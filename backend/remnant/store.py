"""
REMNANT — durable store.

Lightweight JSON persistence for the core slice (no heavy DB dependency so it
runs cleanly on constrained hardware). The CONCEPTUAL center of continuity is the
persistent Mind, not this file — this store is the local durable backing so state
survives restart. The Mind mirrors and owns the long-term interpretation.
"""

from __future__ import annotations

import json
import os
import threading
from typing import Optional

from .models import Remnant


class Store:
    def __init__(self, path: str = "./data/remnant.db"):
        self.path = path
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self._remnants: dict[str, Remnant] = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                for rid, data in raw.items():
                    self._remnants[rid] = Remnant.model_validate(data)
            except (json.JSONDecodeError, KeyError, ValueError):
                self._remnants = {}

    def _persist(self) -> None:
        # Caller already holds self._lock (upsert/delete take it, then call here).
        data = {rid: r.model_dump(mode="json") for rid, r in self._remnants.items()}
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def upsert(self, remnant: Remnant) -> Remnant:
        with self._lock:
            self._remnants[remnant.remnant_id] = remnant
            self._persist()
            return remnant

    def get(self, remnant_id: str) -> Optional[Remnant]:
        with self._lock:
            return self._remnants.get(remnant_id)

    def all(self) -> list[Remnant]:
        with self._lock:
            return sorted(
                self._remnants.values(),
                key=lambda r: r.created_at,
            )

    def delete(self, remnant_id: str) -> bool:
        with self._lock:
            existed = self._remnants.pop(remnant_id, None) is not None
            if existed:
                self._persist()
            return existed
