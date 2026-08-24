# REMNANT — Deployment

Production configuration notes. REMNANT is a two-part app (FastAPI backend +
Vite/React frontend). This doc covers running it for real, not just in dev.

## Environment (all secrets env-only, never in the repo)

| Var | Required | Meaning |
|-----|----------|---------|
| `MINDS_BUILDER_API_KEY` | for live Mind | Minds Builder API key (created in the Builder console, shown once) |
| `MIND_ID` | for live Mind | the persistent Mind's UUID |
| `STORAGE_PATH` | no (default `./data/remnant.db`) | where the durable store lives |
| `REMNANT_REQUIRE_AUTH` | no (default false) | true = require `Authorization: Bearer <token>` |
| `REMNANT_API_TOKEN` | if auth on | the bearer token |
| `REMNANT_CORS_ORIGINS` | no | comma-separated allowed origins (default localhost:5173) |
| `REMNANT_OBSERVATORY` | no | autonomous background loop on/off (default on) |
| `REMNANT_OBSERVATORY_INTERVAL_S` | no | observatory scan interval (min 30) |
| `REMNANT_OBSERVATORY_COOLDOWN_S` | no | per-pass cooldown for autonomous runs |
| `REMNANT_LOG_LEVEL` | no | INFO/DEBUG/WARNING |
| `VITE_API_BASE` | production frontend | if the backend is NOT same-origin, set this at build time |

## Backend

```bash
cd backend
uv venv .venv && uv pip install -e .
source .venv/bin/activate
python -m uvicorn remnant.app:app --host 0.0.0.0 --port 8000
```

- Health: `GET /api/v1/health` · Readiness: `GET /api/v1/readyz` · Liveness: `GET /api/v1/livez`
- OpenAPI docs: `/api/v1/docs` (served when not auth-gated)
- All routes are namespaced under `/api/v1`; legacy `/api/*` aliases exist for
  backward compatibility with early docs/scripts.
- Logs are JSON lines with a `request_id` per request; audit events
  (`experiment.outcome`, `observatory.action`, `store.corrupt`, …) are structured.
- Secrets: read from env only; the Minds CLI key is passed via env, never
  embedded, never exposed to the frontend (the browser only ever talks to /api/v1,
  which never forwards Minds credentials).

## Frontend

```bash
cd frontend
npm install
npm run build        # static output in dist/
```

- Serve `dist/` behind a reverse proxy (nginx/Caddy) that routes `/api` to the
  backend on the same origin — then no `VITE_API_BASE` is needed.
- If the backend is on a different origin: build with
  `VITE_API_BASE=https://backend.example.com npm run build` and configure CORS
  (`REMNANT_CORS_ORIGINS`) to the frontend origin.

## No-localhost rule

The dev proxy (`vite.config.ts` → `127.0.0.1:8000`) is dev-only. In production the
frontend must reach the backend via the configured `VITE_API_BASE` or the
same-origin reverse proxy — never a hardcoded localhost. grep check:
`grep -rn "127.0.0.1\|localhost" frontend/src` must return only the dev proxy config.

## Security notes

- `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
  `Referrer-Policy: no-referrer` are set on every response.
- CORS is allow-listed from `REMNANT_CORS_ORIGINS`, never `*` by default.
- External URLs in evidence are stored as metadata only — the backend never
  fetches them (anti-SSRF).
- Community text is stored as untrusted data (prompt-injection boundary): it is
  never executed as a tool call; test `test_prompt_injection_text_is_untrusted_data`
  proves an "ignore previous instructions" comment is treated as data.
- Auth: `REMNANT_REQUIRE_AUTH=true` + `REMNANT_API_TOKEN` gates all routes with
  `Authorization: Bearer`.

## Restart recovery

The store writes atomically (temp + rename), keeps a `.lastgood` snapshot and
rotating `.bak` files, and recovers from corruption on load (logged as
`store.corrupt`). The observatory (autonomous loop) is a daemon thread; it stops
cleanly on shutdown. State survives process restart by design.