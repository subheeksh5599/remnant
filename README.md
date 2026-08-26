<p align="center">
  <a href="https://remnant-two.vercel.app"><img src="docs/remnant-banner.png" width="750" alt="REMNANT"></a>
</p>

<p align="center">
    <em>The Mind that remembers what communities leave behind.</em>
</p>

<p align="center">
<a href="https://remnant-two.vercel.app" target="_blank">
    <img src="https://img.shields.io/badge/live-demo-7A5C3E" alt="Live demo">
</a>
<a href="https://github.com/subheeksh5599/remnant/actions" target="_blank">
    <img src="https://img.shields.io/badge/tests-61%20passing-3E7A5C" alt="Tests">
</a>
<a href="https://www.animocabrands.com/minds" target="_blank">
    <img src="https://img.shields.io/badge/Track-1%20Audience%20growth%20and%20engagement-5C6B7A" alt="Track">
</a>
<a href="https://opensource.org/licenses/MIT" target="_blank">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
</a>
</p>

---

**Website**: <a href="https://remnant-two.vercel.app" target="_blank">remnant-two.vercel.app</a>

**Documentation**: <a href="https://github.com/subheeksh5599/remnant/blob/main/docs/architecture.md" target="_blank">docs/architecture.md</a>

**Repository**: <a href="https://github.com/subheeksh5599/remnant" target="_blank">github.com/subheeksh5599/remnant</a>

---

REMNANT is a persistent Minds agent that discovers *candidate recurring needs* in a creator's community, holds competing explanations about why they recur, tests them with pre-registered experiments, and learns from the measured outcome. Built for **Creative Minds Jam #1: Hong Kong** — **Track 1: Audience growth & engagement**.

**[Features](#features) - **[Requirements](#requirements) - **[Installation](#installation) - **[Usage](#usage) - **[API](#api) - **[Architecture](#architecture) - **[Honesty](#honesty)**

## Features

- **Cross-language need discovery** — a transparent concept glossary + token overlap links "beginner ZK tutorial" (2022) to "start building with zero knowledge" (2026) as a *candidate*, never a merge. Deterministic and auditable; no LLM inside the math.
- **Competing hypotheses (H1–H4)** — persistent need · new cohort · temporary trend · semantic coincidence. Evidence strength is qualitative (low/medium/high); contradicting evidence is surfaced, never suppressed.
- **Pre-registered experiments** — metric, threshold, population and window are locked *before* observing. The verdict is pure arithmetic: `observed 0.067 >= threshold 0.040 → CLEARED`. Creator-defined overrides are supported and recorded.
- **Persistent Minds memory — with recovery** — every belief-critical change is mirrored into the persistent Mind's conversation, and `/api/v1/minds/recover/{rid}` reads it back, so a later session can recover what the agent knew even if the local store is empty.
- **Autonomous observatory** — on durable deployments a background thread revisits dormant/revisited remnants on an interval (cooldown + action provenance + approval boundaries), with zero page loads required.
- **Provenance-first evidence** — every expression carries source kind, id, URL, author, occurred-at and ingested-at. Real and synthetic are never mixed without labels.
- **Full provenance UI** — remnant detail, discovery evidence, H1–H4 panel, belief reconstruction, audit trail with request IDs, semantic-safety lab.

## Requirements

**Backend**: Python 3.12+, `uv` (or pip). No external model/API keys required for the deterministic core.

**Frontend**: Node 18+, npm.

**Minds (optional, recommended)**: a `MINDS_BUILDER_API_KEY` and `MIND_ID` from the [Minds Builder](https://www.animocabrands.com/minds). Without them the product runs fully on the deterministic core + store; `/api/v1/mind` reports `available=false` honestly.

> It is recommended to use a virtual environment. The test suite (61 tests) runs against a clean install.

## Installation

```bash
git clone https://github.com/subheeksh5599/remnant.git && cd remnant

# backend
cd backend
uv venv .venv
uv pip install -e .
source .venv/bin/activate
python -m pytest tests/ -q        # 61 tests, all pass
python -m uvicorn remnant.app:app --port 8000

# frontend (new terminal)
cd frontend
npm install
npm run dev                      # http://localhost:5173 (proxies /api -> :8000)
```

And just like that, you're ready to go. Load the synthetic demo corpus (clearly labeled) through **Demo Controls** on the Safety Lab page — the system discovers the groupings itself.

## Usage

```python
from fastapi.testclient import TestClient
from remnant.app import app

with TestClient(app) as c:
    # 1. ingest raw community evidence (REMNANT discovers the need)
    r = c.post("/api/v1/remnants", json={
        "title": "Beginner ZK education",
        "underlying_need_hypothesis": "Beginners want an accessible on-ramp to zero-knowledge education.",
    }).json()
    rid = r["remnant_id"]

    c.post(f"/api/v1/remnants/{rid}/expressions", json={
        "text": "Can you make a beginner ZK tutorial?",
        "source_kind": "youtube_comment", "source_id": "yt-2022-01",
        "occurred_at": "2022-06-01T00:00:00Z",
    })

    # 2. plan a pre-registered experiment (or override it)
    exp = c.post(f"/api/v1/remnants/{rid}/experiments").json()

    # 3. record the observation — the verdict is deterministic
    out = c.post(f"/api/v1/remnants/{rid}/experiments/{exp['experiment_id']}/outcome",
                 json={"observed_value": 0.067}).json()
    # out: observed 0.067 >= pre-registered 0.040 -> CLEARED, state -> revisited

    # 4. ask the Mind what it believes
    belief = c.get(f"/api/v1/remnants/{rid}/belief").json()["belief"]
```

The adversarial semantic test (`POST /api/v1/adversarial/analyze`) shows the system refusing to merge a fault report with a need, and accepting a candidate cross-language link — both with supporting, conflicting and uncertainty evidence lines.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/remnants` | list remnants |
| POST | `/api/v1/remnants` | register a need hypothesis |
| GET | `/api/v1/remnants/{rid}` | full remnant: expressions, discoveries, H1–H4, experiments, decisions |
| POST | `/api/v1/remnants/{rid}/expressions` | ingest evidence (provenance: source, author, url, timestamps) |
| POST | `/api/v1/remnants/{rid}/decisions` | creator decision (adopted / rejected / deferred) |
| POST | `/api/v1/remnants/{rid}/experiments` | plan experiment (autonomous or creator-defined: metric, threshold, population, window) |
| POST | `/api/v1/remnants/{rid}/experiments/{eid}/outcome` | record observation → deterministic verdict (409 on duplicate) |
| GET | `/api/v1/remnants/{rid}/belief` | ask the Mind: reconstructed belief + uncertainty |
| GET | `/api/v1/remnants/{rid}/provenance` | traceable evidence chain |
| GET | `/api/v1/mind` | Minds status (explicit error when unconfigured) |
| GET | `/api/v1/minds/status` | memory steward: user-connected, env-configured, or none |
| GET | `/api/v1/minds/recover/{rid}` | recover narrative from the persistent Mind's conversation |
| POST | `/api/v1/minds/connect` | connect a visitor's own Minds agent (validated against the Builder API) |
| GET | `/api/v1/observatory/actions` | autonomous observatory action log (with audit IDs) |
| POST | `/api/v1/adversarial/analyze` | cross-language semantic safety test |
| GET | `/api/v1/audit` | audit trail: mutations, transitions, experiments, outcomes, request IDs |
| GET | `/api/v1/health` | health + storage mode (memory vs durable, reported honestly) |
| POST | `/api/v1/demo/load` | load labeled synthetic corpus through the discovery engine (idempotent) |

## Architecture

```
backend/remnant/
  models.py        domain: Remnant, Expression, Experiment, H1–H4, discovery lifecycle
  inference.py     discovery engine: concept glossary + token overlap + collision guard
  experiments.py   pre-registered experiment planner + deterministic belief update
  observatory.py   autonomous background loop (durable deploys; cooldown + provenance)
  belief.py        belief reconstruction from the persisted chain
  store.py         atomic durable JSON (survives restart)
  minds.py         Minds Builder: memory mirroring + recovery
  app.py           FastAPI surface
frontend/
  src/pages/       Landing · Dashboard · Remnants · RemnantDetail · Mind · System · Lab
  src/components/  Shell · Footer · Reveal
  src/lib/api.ts   typed API client (mirrors the domain model)
scripts/
  vercel-build.sh          stages the Vercel deploy (static + python function)
  import_youtube.py        real public YouTube evidence → discovery pipeline
deploy/
  durable-observatory.sh   one-shot durable VPS deploy (isolated, idempotent)
```

Details in [`docs/architecture.md`](https://github.com/subheeksh5599/remnant/blob/main/docs/architecture.md) — including the honest ownership split (Mind = narrative + recovery; backend = deterministic accounting).

## Deployment

**Live demo:** <a href="https://remnant-two.vercel.app" target="_blank">remnant-two.vercel.app</a>

Single Vercel project: Vite static frontend + FastAPI python function at `/api/*`. Serverless FS is read-only, so the deployed API runs in **memory mode** (`STORAGE_PATH=:memory:`): the labeled synthetic corpus seeds at cold start, and `/api/v1/health` reports `storage_mode: memory`. The durable deployment — real JSON store, observatory background thread, systemd — is one command via `deploy/durable-observatory.sh`.

## Honesty

| Area | Status |
|------|--------|
| Core domain + inference + experiments + store | **Real — tested** (61 tests) |
| Cross-language discovery engine (concept glossary) | **Real — tested** (candidate, never auto-merge; adversarial guard) |
| H1–H4 accounting + deterministic verdicts | **Real — tested** (CLEARED / DISPROVEN / UNCERTAIN paths) |
| Persistence across restart | **Real — tested** (store survives process restart) |
| Minds memory mirroring + recovery | **Real — verified live** (written + read back via recover; needs env to run) |
| Autonomous observatory (durable deploys) | **Real — verified** (background thread, no page load, audit provenance) |
| Demo corpus | **Synthetic, labeled** — and NOT pre-encoded: the discovery engine decides the grouping |
| Real community data ingestion | **Real — `scripts/import_youtube.py`** (226 real public comments, full provenance) |
| Frontend UI | **Real** — builds clean, rendered in browser |
| Full live Minds loop (actions executed THROUGH the Mind) | **Not claimed** — the observatory runs in the backend; the Mind holds the narrative, the backend does the accounting |

## Contributing

This is a Creative Minds Jam #1 submission. The code is structured as a vertical slice: one mechanism — *candidate recurring need → competing hypotheses → pre-registered experiment → measured verdict → persistent belief* — demonstrated completely rather than ten shallow features. PRs are welcome for anything that deepens that slice: embeddings behind the same interface, real community connectors, creator notification surfaces, or sharper hypotheses.

---

*REMNANT is not an archive. It is a persistent, autonomous memory of unresolved audience need.*