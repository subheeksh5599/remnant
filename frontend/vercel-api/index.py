"""Vercel serverless entrypoint for the REMNANT backend.

The FastAPI app lives in the `remnant` package. Storage runs in memory mode on
serverless (Vercel FS is read-only). Serverless ASGI runtimes do NOT reliably
run Starlette's lifespan, so the labeled synthetic corpus is seeded HERE at
import time (per instance), not in the app lifespan.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

os.environ.setdefault("STORAGE_PATH", ":memory:")
os.environ.setdefault("VERCEL", "1")

from remnant.app import store  # noqa: E402
from remnant.scripts_loader import build_demo_corpus  # noqa: E402

# Seed per instance at cold start (idempotent — skips existing titles).
try:
    if store.memory_mode and len(store.all()) == 0:
        build_demo_corpus(store)
except Exception:  # noqa: BLE001 — never block startup
    pass

from remnant.app import app  # noqa: E402

# Vercel looks for a top-level `app` ASGI export — FastAPI's is already that.