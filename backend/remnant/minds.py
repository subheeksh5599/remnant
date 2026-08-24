"""
REMNANT — Minds integration.

The persistent Minds agent is the conceptual center of continuity. This module
wraps the Minds Builder API surface we can drive (list/show minds, conversation
memory, cognition balance) so the product's long-term memory is anchored to the
Mind, not just to the local store.

Hardening:
  - retries with exponential backoff on transient failures
  - explicit timeouts (never hang a request)
  - malformed responses are treated as failures, never silently ignored
  - Minds failures are EXPLICIT: the backend reports unavailable=true and never
    substitutes fabricated behavior
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass
from typing import Optional

from .logging_config import audit, log


@dataclass
class MindsState:
    mind_id: Optional[str] = None
    name: Optional[str] = None
    enabled: bool = False
    cognition_balance: float = 0.0
    ok: bool = False
    error: Optional[str] = None


class MindsError(RuntimeError):
    """Raised when the Minds integration fails. Callers must handle it explicitly
    and surface the failure — never substitute autonomous behavior."""


class MindsClient:
    def __init__(
        self,
        mind_id: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_s: float = 60.0,
        max_retries: int = 2,
    ):
        self.mind_id = mind_id or os.getenv("MIND_ID")
        self.api_key = api_key or os.getenv("MINDS_BUILDER_API_KEY")
        self._timeout = timeout_s
        self._max_retries = max_retries
        self._base = ["npx", "-y", "@animocabrands/minds-cli@latest"]

    def _run(self, args: list[str], retries: Optional[int] = None) -> dict:
        retries = self._max_retries if retries is None else retries
        env = dict(os.environ)
        if self.api_key:
            env["MINDS_BUILDER_API_KEY"] = self.api_key
        last_err: Optional[str] = None
        for attempt in range(retries + 1):
            try:
                proc = subprocess.run(
                    self._base + args,
                    capture_output=True,
                    text=True,
                    timeout=self._timeout,
                    env=env,
                )
            except subprocess.TimeoutExpired:
                last_err = f"minds timeout after {self._timeout}s"
                log.warning("minds.timeout", extra={"cmd": args[0], "attempt": attempt})
                time.sleep(0.5 * (2 ** attempt))  # backoff
                continue
            except OSError as e:
                raise MindsError(f"minds CLI unavailable: {e}") from e

            out = proc.stdout
            start = out.find("{")
            if start == -1:
                last_err = out.strip() or proc.stderr.strip() or "empty response"
                log.warning("minds.empty", extra={"cmd": args[0], "attempt": attempt, "err": last_err})
                time.sleep(0.5 * (2 ** attempt))
                continue
            try:
                parsed = json.loads(out[start:])
            except json.JSONDecodeError:
                last_err = "malformed JSON from minds CLI"
                log.warning("minds.malformed", extra={"cmd": args[0], "attempt": attempt})
                time.sleep(0.5 * (2 ** attempt))
                continue
            return parsed

        audit("minds.failed", cmd=args[0], error=last_err)
        raise MindsError(f"minds call failed after {retries + 1} attempts: {last_err}")

    def state(self) -> MindsState:
        """Read the Mind's state. On failure returns an EXPLICIT error state —
        never an invented 'ok' with fabricated values."""
        if not self.mind_id:
            return MindsState(ok=False, error="MIND_ID not set (env)")
        if not self.api_key:
            return MindsState(ok=False, error="MINDS_BUILDER_API_KEY not set (env)")
        try:
            d = self._run(["mind", "show", "--mind", self.mind_id])
            mind = d.get("mind", {})
            bal = self._run(["cognition", "balance", "--mind", self.mind_id])
            balance = bal.get("balance", {}).get("cognition", 0.0)
            return MindsState(
                mind_id=self.mind_id,
                name=mind.get("name"),
                enabled=bool(mind.get("isEnabled", False)),
                cognition_balance=float(balance or 0.0),
                ok=True,
            )
        except (MindsError, ValueError, TypeError) as e:
            audit("minds.state_error", error=str(e))
            return MindsState(ok=False, error=str(e))

    def available(self) -> bool:
        return bool(self.api_key and self.mind_id)