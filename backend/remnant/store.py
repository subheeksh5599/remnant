"""
REMNANT — durable store.

Lightweight JSON persistence for the core slice. Hardened for production:
  - atomic writes (temp file + rename, so a crash mid-write never corrupts state)
  - corrupted-file recovery (falls back to the last good backup, never silently
    serves empty state as if it were the real state)
  - export / import / backup so state can be moved, migrated, or restored
  - thread-safe (single lock; writes are serialized)

The CONCEPTUAL center of continuity is the persistent Mind, not this file — this
store is the local durable backing so state survives restart.
"""

from __future__ import annotations

import json
import os
import shutil
import threading
import time
from typing import Optional

from .logging_config import audit
from .models import Remnant

_BACKUP_KEEP = 3


class Store:
    def __init__(self, path: str = "./data/remnant.db"):
        self.path = path
        self._lock = threading.RLock()  # reentrant: upsert -> _persist_atomic
        self._memory_mode = path == ":memory:"
        if not self._memory_mode:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self._last_good: Optional[dict] = None  # last successfully serialized state
        self._remnants: dict[str, Remnant] = {}
        self._load()

    # --- load / recovery -------------------------------------------------------

    def _load(self) -> None:
        if self._memory_mode:
            self._remnants = {}
            return
        if not os.path.exists(self.path):
            self._remnants = {}
            return
        raw = self._read_with_recovery()
        if raw is None:
            self._remnants = {}
            return
        for rid, data in raw.items():
            try:
                self._remnants[rid] = Remnant.model_validate(data)
            except (KeyError, ValueError, TypeError):
                audit("store.load_skipped", remnant_id=rid, reason="invalid record")

    def _read_with_recovery(self) -> Optional[dict]:
        """Read the store, recovering from corruption via backups or the last
        good in-memory state. Never silently serves empty state."""
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if not isinstance(raw, dict):
                raise ValueError("store root must be a dict")
            self._last_good = raw
            return raw
        except (json.JSONDecodeError, ValueError, OSError):
            audit("store.corrupt", path=self.path, action="falling back")
            # First fallback: the always-maintained lastgood snapshot.
            lastgood = self.path + ".lastgood"
            try:
                with open(lastgood, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                if isinstance(raw, dict):
                    self._last_good = raw
                    return raw
            except (json.JSONDecodeError, OSError):
                pass
            backups = sorted(self._backup_paths(), reverse=True)
            for b in backups:
                try:
                    with open(b, "r", encoding="utf-8") as f:
                        raw = json.load(f)
                    if isinstance(raw, dict):
                        self._last_good = raw
                        return raw
                except (json.JSONDecodeError, OSError):
                    continue
            # last resort: the last successfully serialized in-memory state
            if self._last_good is not None:
                return self._last_good
            return None

    def _backup_paths(self) -> list[str]:
        base = self.path
        return [f"{base}.{i}.bak" for i in range(1, _BACKUP_KEEP + 1)]

    # --- atomic persistence ------------------------------------------------------

    def _persist_atomic(self) -> None:
        # Memory mode (serverless: read-only FS): no file writes; state lives
        # for the lifetime of the instance, honestly reported as such.
        if self._memory_mode:
            self._last_good = {rid: r.model_dump(mode="json") for rid, r in self._remnants.items()}
            return
        # Serialize first (so we know it's valid), then write to a temp file,
        # fsync, then rename over the real path. A crash at any point leaves
        # either the old file or the new one — never a truncated/partial file.
        data = {rid: r.model_dump(mode="json") for rid, r in self._remnants.items()}
        serialized = json.dumps(data, indent=2)  # validates serializability
        self._last_good = json.loads(serialized)
        # Always maintain a lastgood snapshot (written before the main file, so
        # recovery has a fallback even for the very first write).
        lastgood = self.path + ".lastgood"
        with open(lastgood, "w", encoding="utf-8") as f:
            f.write(serialized)
            f.flush()
            os.fsync(f.fileno())
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(serialized)
            f.flush()
            os.fsync(f.fileno())
        # rotate backups (only when a prior file exists)
        paths = self._backup_paths()
        if os.path.exists(self.path):
            shutil.copy2(self.path, paths[0])
            for older, newer in zip(paths, paths[1:]):
                if os.path.exists(older):
                    shutil.copy2(older, newer)
        os.replace(tmp, self.path)

    # --- public API --------------------------------------------------------------

    def upsert(self, remnant: Remnant) -> Remnant:
        with self._lock:
            self._remnants[remnant.remnant_id] = remnant
            self._persist_atomic()
            return remnant

    def get(self, remnant_id: str) -> Optional[Remnant]:
        with self._lock:
            exact = self._remnants.get(remnant_id)
            if exact is not None:
                return exact
            # Prefix-tolerant: the UI invites "first 8 chars" and serverless
            # instances re-seed with fresh ids, so a stable prefix must resolve
            # on ANY instance. Only a UNIQUE prefix resolves — ambiguous ones
            # return None (not a guess).
            if len(remnant_id) >= 8:
                matches = [r for r in self._remnants.values() if r.remnant_id.startswith(remnant_id)]
                if len(matches) == 1:
                    return matches[0]
            return None

    def all(self) -> list[Remnant]:
        with self._lock:
            return sorted(self._remnants.values(), key=lambda r: r.created_at)

    def delete(self, remnant_id: str) -> bool:
        with self._lock:
            existed = self._remnants.pop(remnant_id, None) is not None
            if existed:
                self._persist_atomic()
            return existed

    # --- export / import / backup --------------------------------------------------

    def export(self, out_path: str) -> int:
        """Export all state to a portable JSON file. Returns record count."""
        with self._lock:
            data = {rid: r.model_dump(mode="json") for rid, r in self._remnants.items()}
        if not self._memory_mode:
            tmp = out_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp, out_path)
        return len(data)

    def import_records(self, in_path: str, replace: bool = False) -> int:
        """Import records from a JSON export. replace=True clears existing first."""
        if not os.path.exists(in_path) and not self._memory_mode:
            raise FileNotFoundError(in_path)
        if self._memory_mode:
            raise ValueError("memory mode: import from file requires a writable store")
        with open(in_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict):
            raise ValueError("import file must be a dict of remnant records")
        loaded: dict[str, Remnant] = {}
        for rid, data in raw.items():
            loaded[rid] = Remnant.model_validate(data)
        with self._lock:
            if replace:
                self._remnants = loaded
            else:
                self._remnants.update(loaded)
            self._persist_atomic()
        return len(loaded)

    def backup(self) -> str:
        """Snapshot current state to a timestamped backup file."""
        if self._memory_mode:
            return ":memory:"
        ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        out = f"{self.path}.{ts}.snapshot"
        self.export(out)
        return out

    @property
    def memory_mode(self) -> bool:
        return self._memory_mode