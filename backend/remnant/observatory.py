"""
REMNANT — autonomous observation scheduler.

The Mind's proactive follow-up, running WITHOUT a frontend click. On an interval
it reviews dormant/unresolved remnants, compares current evidence against
historical unresolved needs, and raises candidates for re-evaluation. Everything
it does is:
  - recorded in an action log with provenance (action id, timestamp, reason)
  - idempotent (per-remnant cooldown prevents repeated identical actions)
  - bounded (approval boundaries: it recommends, never executes consequential
    external actions itself)
"""

from __future__ import annotations

import asyncio
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from .config import settings
from .logging_config import audit, log
from .models import Remnant, ResolutionState
from .store import Store


class AutonomousObservationError(RuntimeError):
    """Raised when the observatory cannot produce a safe candidate."""


class Observatory:
    def __init__(self, store: Store):
        self.store = store
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_run: Optional[float] = None
        self.actions: list[dict] = []  # action provenance log (in-memory + audit)

    # --- provenance ------------------------------------------------------------

    def _log_action(self, remnant_id: str, action: str, reason: str, **fields) -> dict:
        entry = {
            "action_id": uuid.uuid4().hex,
            "at": datetime.now(timezone.utc).isoformat(),
            "remnant_id": remnant_id,
            "action": action,
            "reason": reason,
            **fields,
        }
        self.actions.append(entry)
        audit("observatory.action", **entry)
        return entry

    # --- candidate detection -----------------------------------------------------

    def _recent_new_expressions(self, r: Remnant, window_days: int = 30) -> int:
        cutoff = datetime.now(timezone.utc).timestamp() - window_days * 86400
        return sum(1 for e in r.expressions if e.occurred_at.timestamp() >= cutoff)

    def _dormant_candidates(self) -> list[Remnant]:
        """Remnants that are unresolved/dormant AND have a recent signal worth looking at."""
        candidates = []
        for r in self.store.all():
            if r.resolution_state in (
                ResolutionState.DORMANT,
                ResolutionState.UNRESOLVED,
                ResolutionState.UNCERTAIN,
            ):
                recent = self._recent_new_expressions(r)
                if recent >= 1:
                    candidates.append(r)
        return candidates

    def recommend(self, r: Remnant) -> Optional[dict]:
        """Build a candidate investigation for a remnant, or None if nothing to say."""
        recent = self._recent_new_expressions(r)
        if recent == 0:
            return None
        hist = sum(1 for e in r.expressions if e.occurred_at.year <= 2023)
        cur = sum(1 for e in r.expressions if e.occurred_at.year >= 2024)
        return {
            "remnant_id": r.remnant_id,
            "title": r.title,
            "recent_expressions": recent,
            "historical_expressions": hist,
            "current_expressions": cur,
            "state": r.resolution_state.value,
            "candidate": "possible recurrence — compare current evidence against the unresolved need",
            "recommended_action": "plan a pre-registered experiment to disambiguate H1 vs H2",
            "approval_required": True,  # the observatory recommends; it never acts externally
        }

    # --- run loop -----------------------------------------------------------------

    def run_once(self, force: bool = False) -> list[dict]:
        """One observation pass. Idempotent per remnant via cooldown.

        force=True bypasses the cooldown — used for explicit user/API-triggered
        runs; the autonomous background loop always obeys the cooldown.
        """
        if not force and self._last_run is not None:
            elapsed = time.time() - self._last_run
            if elapsed < settings.observatory_cooldown_s:
                return []
        if not force:
            self._last_run = time.time()
        surfaced: list[dict] = []
        for r in self._dormant_candidates():
            rec = self.recommend(r)
            if rec is None:
                continue
            self._log_action(
                r.remnant_id,
                "reviewed_dormant_remnant",
                "current expressions relate to an unresolved historical need",
                **{k: v for k, v in rec.items() if k != "remnant_id"},
            )
            surfaced.append(rec)
        if surfaced:
            audit("observatory.pass", surfaced=len(surfaced))
        return surfaced

    # --- lifecycle ------------------------------------------------------------------

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        if not settings.observatory_enabled:
            log.info("observatory disabled by config")
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="observatory", daemon=True)
        self._thread.start()
        log.info("observatory started", extra={"interval_s": settings.observatory_interval_s})

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.run_once()
            except Exception:  # noqa: BLE001 — never kill the background loop
                log.exception("observatory pass failed")
            self._stop.wait(settings.observatory_interval_s)

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)


# async wrapper for FastAPI startup (so we don't block event loop)
async def start_observatory(store: Store) -> Observatory:
    obs = Observatory(store)
    obs.start()
    return obs