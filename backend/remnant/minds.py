"""
REMNANT — Minds integration.

The persistent Minds agent is the conceptual center of continuity. This module
wraps the Minds Builder API surface we can drive (list/show minds, conversation
memory, cognition balance) so the product's long-term memory is anchored to the
Mind, not just to the local store.

The Mind owns:
  - long-term interpretation (memory mirrored into Mind conversations)
  - autonomous follow-up (proactive checks)
  - experiment decisions (recommendations grounded in memory)
  - cumulative reasoning

We never store credentials here; the Builder API key comes from the environment.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MindsState:
    mind_id: Optional[str] = None
    name: Optional[str] = None
    enabled: bool = False
    cognition_balance: float = 0.0
    ok: bool = False
    error: Optional[str] = None


class MindsClient:
    """Thin, honest wrapper over the Minds Builder CLI (JSON-first stdout)."""

    def __init__(self, mind_id: Optional[str] = None, api_key: Optional[str] = None):
        self.mind_id = mind_id or os.getenv("MIND_ID")
        self.api_key = api_key or os.getenv("MINDS_BUILDER_API_KEY")
        self._base = ["npx", "-y", "@animocabrands/minds-cli@latest"]

    def _run(self, args: list[str]) -> dict:
        env = dict(os.environ)
        if self.api_key:
            env["MINDS_BUILDER_API_KEY"] = self.api_key
        proc = subprocess.run(
            self._base + args,
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
        # CLI prints one JSON object on stdout; diagnostics go to stderr.
        out = proc.stdout
        start = out.find("{")
        if start == -1:
            return {"ok": False, "error": out.strip() or proc.stderr.strip()}
        try:
            return json.loads(out[start:])
        except json.JSONDecodeError:
            return {"ok": False, "error": out.strip() or proc.stderr.strip()}

    def state(self) -> MindsState:
        """Read-only health/memory surface of the Mind."""
        if not self.mind_id:
            return MindsState(ok=False, error="MIND_ID not set (env)")
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
        except Exception as e:  # noqa: BLE001
            return MindsState(ok=False, error=str(e))

    def available(self) -> bool:
        return bool(self.api_key and self.mind_id)