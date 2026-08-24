"""
REMNANT — structured logging + request correlation.

Every request gets a correlation id (request_id) that flows through logs, error
responses, and audit entries. Logs are JSON lines for machine parsing in a
deployed environment.
"""

from __future__ import annotations

import json
import logging
import sys
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for k in ("request_id", "mind_id", "remnant_id", "experiment_id", "event"):
            v = getattr(record, k, None)
            if v is not None:
                payload[k] = v
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def setup_logging(level: str = "INFO") -> logging.Logger:
    root = logging.getLogger("remnant")
    if root.handlers:
        return root
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(level.upper())
    return root


log = setup_logging()


def audit(event: str, **fields) -> None:
    """Write an audit-trail log line (experiments, belief updates, actions)."""
    log.info("audit", extra={"event": event, **fields})


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach a correlation id to every request/response and log it."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        start = time.monotonic()
        request.state.request_id = request_id
        try:
            response = await call_next(request)
        except Exception:
            log.error("unhandled exception", extra={"request_id": request_id})
            raise
        duration_ms = (time.monotonic() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        log.info(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round(duration_ms, 1),
            },
        )
        return response