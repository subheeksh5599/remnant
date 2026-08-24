# REMNANT — Architecture (as actually built)

## The two-layer split

```
audience expressions (comments, discord, github, …)
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ BACKEND (deterministic — Python, no LLM inside the math)     │
│  inference.py   expression-vs-need, H1–H4 evidence accounting│
│  experiments.py pre-registered threshold, crossing verdict   │
│  belief.py      belief reconstruction from the persisted     │
│                 chain (deterministic, reproducible)          │
│  observatory.py autonomous background loop (cooldown,        │
│                 action provenance, approval-required recs)   │
│  store.py       atomic durable JSON (survives restart)       │
└───────────────────────────────┬─────────────────────────────┘
                                │ memory mirroring
                                ▼
┌─────────────────────────────────────────────────────────────┐
│ PERSISTENT MINDS AGENT (the community-memory steward)        │
│  conversation per remnant; every belief-critical change is   │
│  mirrored via POST /v1/messaging/message (verified live).    │
│  The Mind's history IS the continuity record.                │
└─────────────────────────────────────────────────────────────┘
```

## What each layer owns (the honest split)

| Concern | Owner | Why |
|---|---|---|
| H1–H4 evidence accounting | Backend (deterministic) | reproducible, probe-proof, no LLM variance |
| Pre-registered threshold + verdict | Backend (deterministic) | `0.067 >= 0.040 -> CLEARED` is identical every run |
| Belief reconstruction from chain | Backend (deterministic) | replayable after restart |
| Autonomous observation | Backend (observatory thread) | interval + cooldown + provenance; recommends, never executes externally without approval |
| The community-memory NARRATIVE | Persistent Mind | conversation history holds the story across sessions; inspectable |
| Durability/restart survival | Store (atomic JSON) | local backing; recovered from corruption |

**Remove the Mind:** the deterministic core still runs (tests, store, belief), but
the product loses its persistent narrative memory — the "remembers what communities
left behind" claim stops being true, and `/api/v1/mind` reports `available=false`.
The Mind is not decorative; it is one of two load-bearing halves.

**Remove the backend:** there is no product — no ingestion, no accounting, no
experiments, no observatory. The Mind alone is a chat.

## Configuration

Centralized in `config.py`, validated at startup (fail fast). All secrets env-only.
See `docs/DEPLOY.md` for the env table.

## Failure semantics

- Minds unavailable → `remember()` returns False, audit `minds.remember_failed`,
  `/api/v1/mind` reports `available=false`. Never silent, never substituted.
- Store corrupt → recovery via `.lastgood` / backups (audit `store.corrupt`).
- API errors → consistent `{error: {code, message, request_id}}` schema.