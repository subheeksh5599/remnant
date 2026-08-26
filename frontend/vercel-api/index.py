"""Vercel serverless entrypoint for the REMNANT backend.

The FastAPI app lives in the `remnant` package. Storage runs in memory mode on
serverless (Vercel FS is read-only). The site starts EMPTY — no seeded corpus.
Only real community data imported through the website appears (per instance;
the durable deployment persists it). The clearly-labeled synthetic corpus is
available ONLY via the explicit 'Load demonstration corpus' control in the UI.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

os.environ.setdefault("STORAGE_PATH", ":memory:")
os.environ.setdefault("VERCEL", "1")

from remnant.app import app  # noqa: E402

# Vercel looks for a top-level `app` ASGI export — FastAPI's is already that.