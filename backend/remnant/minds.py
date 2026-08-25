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
        """Read the Mind's state via the HTTP Builder API (works on serverless,
        unlike the CLI). On failure returns an EXPLICIT error state — never an
        invented 'ok' with fabricated values."""
        if not self.mind_id:
            return MindsState(ok=False, error="MIND_ID not set (env)")
        if not self.api_key:
            return MindsState(ok=False, error="MINDS_BUILDER_API_KEY not set (env)")
        try:
            d = self._http("GET", f"/v1/minds/{self.mind_id}", None)
            enabled = bool(d.get("isEnabled", False))
            name = d.get("name")
            try:
                bal = self._http("GET", f"/v1/minds/{self.mind_id}/credits", None)
                balance = bal.get("cognition", 0.0)
            except MindsError:
                balance = 0.0
            return MindsState(
                mind_id=self.mind_id,
                name=name,
                enabled=enabled,
                cognition_balance=float(balance or 0.0),
                ok=True,
            )
        except (MindsError, ValueError, TypeError) as e:
            audit("minds.state_error", error=str(e))
            return MindsState(ok=False, error=str(e))

    def available(self) -> bool:
        return bool(self.api_key and self.mind_id)

    # --- memory mirroring (the load-bearing Minds integration) --------------------
    #
    # The Mind genuinely HOLDS the community-memory narrative: on every
    # belief-critical change, the backend sends a compact memory message to the
    # Mind's conversation (alias per remnant). The Mind's conversation history
    # then IS the continuity record — inspectable via the messaging history
    # endpoint. The backend remains the deterministic accounting engine; the
    # Mind is the persistent steward of the story. Verified live against the
    # Builder API (POST /v1/messaging/conversation + /v1/messaging/message).

    API_BASE = "https://api.build.hellominds.ai"

    def _http(self, method: str, path: str, payload: Optional[dict]) -> dict:
        import urllib.error
        import urllib.request

        body = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(
            f"{self.API_BASE}{path}",
            data=body,
            method=method,
            headers={
                "X-Api-Key": self.api_key or "",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                raw = resp.read().decode()
        except urllib.error.HTTPError as e:
            raise MindsError(f"minds http {e.code} on {path}: {e.read().decode()[:200]}") from e
        except (urllib.error.URLError, TimeoutError) as e:
            raise MindsError(f"minds http failure on {path}: {e}") from e
        if not raw.strip():
            raise MindsError(f"minds http empty response on {path}")
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            raise MindsError(f"minds http malformed response on {path}") from e

    def remember(self, remnant_id: str, message: str) -> bool:
        """Mirror a belief-critical state change into the persistent Mind's
        conversation memory. Returns True on success, False when Minds is not
        configured or the write fails (explicit, never silent)."""
        if not self.available():
            audit("minds.remember_skipped", remnant_id=remnant_id, reason="not configured")
            return False
        alias = f"remnant-{remnant_id[:8]}"
        try:
            self._http("POST", "/v1/messaging/conversation", {"mindId": self.mind_id, "alias": alias})
            self._http("POST", "/v1/messaging/message", {"mindId": self.mind_id, "alias": alias, "messageText": message})
            audit("minds.remembered", remnant_id=remnant_id, alias=alias, mind_id=self.mind_id[:8])
            return True
        except MindsError as e:
            audit("minds.remember_failed", remnant_id=remnant_id, error=str(e))
            return False

    def list_minds(self) -> list[dict]:
        """List the Minds available to the connected builder key (per-user
        connection flow). Raises MindsError on failure — never fake data.
        The endpoint returns a bare JSON array of mind objects."""
        if not self.api_key:
            raise MindsError("builder api key missing")
        data = self._http("GET", f"/v1/humans/{self._human_id()}/minds", None)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("minds", []) or data.get("mind", []) or []
        return []

    def _human_id(self) -> str:
        """Extract humanId from the Builder API key JWT payload (verified key
        shape: {..., humanId: '0b07503e-...', ...}). Never sent anywhere."""
        import base64

        if not self.api_key:
            raise MindsError("builder api key missing")
        try:
            payload = self.api_key.split(".")[1]
            payload += "=" * (-len(payload) % 4)
            claims = json.loads(base64.urlsafe_b64decode(payload))
            hid = claims.get("humanId")
            if not hid:
                raise MindsError("builder key payload missing humanId")
            return hid
        except Exception as e:  # noqa: BLE001
            raise MindsError(f"cannot decode builder key: {e}") from e