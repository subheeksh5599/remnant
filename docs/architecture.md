# REMNANT — Architecture (as actually built)

## The two-layer split

```
raw audience expressions (comments, discord, github, youtube import, …)
        │
        ▼  DISCOVERY ENGINE (inference.py) — deterministic, auditable
        │   transparent concept glossary + token overlap + collision guard
        │   → candidate link (same need / candidate / insufficient / different)
        ▼
┌─────────────────────────────────────────────────────────────┐
│ BACKEND (deterministic — Python, no LLM inside the math)     │
│  inference.py    discovery + H1–H4 evidence accounting       │
│  experiments.py  pre-registered threshold, crossing verdict  │
│                 (creator overrides: metric/threshold/        │
│                  population/window recorded as defined_by_creator) │
│  belief.py       belief reconstruction from the persisted    │
│                 chain (deterministic, reproducible)          │
│  observatory.py  autonomous background loop (durable deploys │
│                 only; interval + cooldown + provenance +     │
│                 approval boundaries)                         │
│  store.py        atomic durable JSON (survives restart)      │
└───────────────────────────────┬─────────────────────────────┘
                                │ memory mirroring (write)
                                │ recovery (read)
                                ▼
┌─────────────────────────────────────────────────────────────┐
│ PERSISTENT MINDS AGENT (the community-memory steward)        │
│  per-remnant conversation; belief-critical changes mirrored  │
│  via POST /v1/messaging/message (verified live).             │
│  GET /v1/messaging/histories/{alias} → recover_context()     │
│  reconstructs the narrative even when the store is empty.    │
└─────────────────────────────────────────────────────────────┘
```

## What each layer owns (the honest split)

| Concern | Owner | Why |
|---|---|---|
| Matching expressions to needs (discovery) | Backend — deterministic concept glossary | auditable, no LLM variance; candidate ≠ merge |
| H1–H4 evidence accounting | Backend (deterministic) | reproducible, probe-proof |
| Pre-registered threshold + verdict | Backend (deterministic) | `0.067 >= 0.040 -> CLEARED` is identical every run |
| Belief reconstruction from chain | Backend (deterministic) | replayable after restart |
| Autonomous observation | Backend (observatory thread — durable deploys only) | interval + cooldown + provenance; recommends, never executes externally without approval |
| The community-memory NARRATIVE | Persistent Mind | conversation history holds the story across sessions; recoverable via /api/v1/minds/recover/{rid} |
| Durability/restart survival | Store (atomic JSON) | local backing; recovered from corruption |

**Remove the Mind:** the deterministic core still runs (tests, store, belief), but
the product loses its persistent narrative memory AND the recover path — the
"remembers what communities left behind" claim stops being true, and `/api/v1/mind`
reports `available=false`. The Mind is not decorative; it is one of two load-bearing
halves.

**Remove the backend:** there is no product — no discovery, no accounting, no
experiments, no observatory. The Mind alone is a chat.

## Discovery pipeline (P0.2, as built)

1. Raw expressions are ingested ONE AT A TIME — no grouping hints.
2. Each is offered to every remnant's evidence via the matcher (concept glossary
   + token overlap + collision guard).
3. Best link ≥ candidate → attach with the matcher evidence recorded in
   `discovered_links` (supporting / conflicting / uncertainty / confidence).
4. No link → create a new candidate remnant.
5. The demo corpus uses THIS path — the 2022→2026 ZK grouping is discovered,
   never pre-encoded (verified by tests).

## Autonomous observatory (durable deploys only)

Serverless (Vercel) cannot keep a background thread alive — the observatory only
runs when `/api/v1/observatory/run` is called. The durable backend (systemd on the
VPS) starts the observatory in the app lifespan at a configurable interval
(`REMNANT_OBSERVATORY_INTERVAL_S`), with cooldown+idempotency and an approval
boundary (it recommends; it never executes consequential external actions).
Deploy script: `deploy/durable-observatory.sh` (idempotent, isolated to
`/opt/remnant-durable`, stops before start so the operator pastes the Minds env).

## Configuration

Centralized in `config.py`, validated at startup (fail fast). All secrets env-only.
See `docs/DEPLOY.md` for the env table.

## Failure semantics

- Minds unavailable → `remember()` returns False, audit `minds.remember_failed`,
  `/api/v1/mind` reports `available=false`. Never silent, never substituted.
- Store corrupt → recovery via `.lastgood` / backups (audit `store.corrupt`).
- API errors → consistent `{error: {code, message, request_id}}` schema.