# REMNANT

**“The Mind that remembers what communities leave behind.”**

REMNANT is a persistent Minds agent that remembers unresolved audience needs across
time, preserves uncertainty about why they recur or disappear, and autonomously runs
small experiments to discover which needs are actually worth acting on now.

Built for **Creative Minds Jam #1: Hong Kong** (Minds by Animoca Brands).
**Track fit:** **Track 1 — Audience growth & engagement** (retain the audience; don't lose
them to a forgotten need) with a strong Track 3 (community) resonance.

## ▶ See it in one command

```bash
git clone https://github.com/subheeksh5599/remnant.git && cd remnant

# backend + tests
cd backend
uv sync
source .venv/bin/activate
python -m pytest tests/ -q        # 36 tests, all pass
python -m scripts.demo            # the full money-shot arc (labeled synthetic)

# frontend
cd ../frontend
npm install && npm run build      # production build
```

---

## The problem

Creators receive enormous amounts of audience input — requests, questions, feature
ideas, complaints, recurring problems. Most of it disappears into historical
conversation. People leave. Platforms change. Vocabulary changes. A creator may
remember that "people used to ask for something" but loses the context, persistence,
history, and unresolved state.

## The core idea

A **REMNANT** is a persistent, time-aware hypothesis about an unresolved audience
need — *not a note, not a saved comment*. It preserves:

- the underlying need candidate (expression ≠ need; the exact words vs what people want)
- historical expressions with full provenance (source, timestamp)
- the creator's responses (or silence)
- **competing explanations** — H1 persistent need · H2 new cohort · H3 temporary trend · H4 semantic coincidence
- evidence for and against each hypothesis
- experiments and their real observed outcomes
- belief updates and the Mind's history

REMNANT never claims: *"This is definitely the same demand returning."* It says:
"Current evidence supports revisiting this need — we cannot yet distinguish H1 from H2.
Here is the smallest experiment that can."

**The product is a decision-under-uncertainty engine, not a certainty engine.**

## Why persistence matters (the demo proof)

1. Audience expresses a need (2022).
2. REMNANT records it; the creator never responds → dormant/unresolved.
3. Years later, new audience members express the same underlying need in different
   words (2026).
4. The Mind detects *possible* continuity, holds H1 vs H2 honestly.
5. It plans the smallest experiment; the outcome updates belief.
6. A fresh session still knows the full history → **continuity demonstrated, not claimed.**

## How the Minds agent is used

Two layers, deliberately split:

1. **The persistent Mind holds the community-memory narrative — and can give it back.** On every
   belief-critical change (an audience expression ingested, an experiment outcome
   recorded, an autonomous observatory action), the backend mirrors a compact
   memory message into the Mind's conversation (`backend/remnant/minds.py` →
   `POST /v1/messaging/message`, verified live). The Mind's conversation history
   IS the continuity record: it remembers that the need existed, what evidence
   arrived, what was tested, what the number said, and what the belief became.
   It is not write-only: `/api/v1/minds/recover/{rid}` reads the conversation
   back and reconstructs what the agent knew about a need, even if the local
   store is empty (verified live). Recovery is honest about its boundary: the
   Mind returns the *narrative*; the *structured accounting* (thresholds,
   verdicts, H1–H4 state) lives in the backend store.
2. **The backend owns the deterministic accounting** — the H1–H4 evidence
   accounting, the pre-registered threshold, the crossing verdict, and the belief
   update are pure arithmetic in Python (no LLM inside the math), so they are
   reproducible and probe-proof. **The discovery engine** (`inference.py`) links
   expressions to needs via a transparent concept glossary + token overlap —
   deterministic, auditable, and capable of *candidate* cross-language discovery
   ("beginner ZK tutorial" ↔ "start building with zero knowledge") without an
   LLM and without auto-merging.

The local store is a durable backing so state survives restart; the Mind is the
persistent steward of the story, not a database relabeled as "AI." The Minds
surface is live-gated: with `MINDS_BUILDER_API_KEY` + `MIND_ID` set, memory
mirroring is on (verified); without them, `/api/v1/mind` reports `available=false`
explicitly and the product still runs on the deterministic core + store. Honest
split documented in `docs/architecture.md`.

## How uncertainty is handled

- Four competing hypotheses are maintained for every potentially recurring need.
- Evidence strength is **qualitative** (low/medium/high), never a fake calibrated "91%".
- Contradicting evidence is surfaced, never suppressed (anti-confirmation-bias).
- The Mind can conclude **DON'T ACT** — that is a strong, credible result.
- Adversarial guard: shared tokens are **not** treated as continuity
  (`How do I learn ZK?` vs `ZK badge is broken` must never auto-merge).

## How experiments work

Prediction ≠ observation. Before a major intervention the Mind proposes the smallest
experiment that maximises information gain while minimising creator effort and
audience risk, with success/failure thresholds set **before** the result. Only real
observed outcomes update beliefs.

## How provenance works

Every important conclusion is traceable:

```
source → observation → interpretation → hypothesis → recommendation
       → experiment → outcome → belief update
```

Every expression carries source kind, id, and timestamp. Nothing is fabricated;
synthetic demo data is labeled `SYNTHETIC DEMONSTRATION CORPUS`.

## Data sources

- Preferred: real creator-provided comments, real public data, real community exports.
- Demo: `backend/scripts/demo.py` builds a **clearly labeled synthetic** 2022→2026 arc
  to demonstrate the temporal workflow. It is never presented as real audience data.

## Architecture

```
backend/remnant/
  models.py        core domain: Remnant, Expression, Hypothesis H1-H4, Experiment
  inference.py     expression-vs-need distinction, adversarial token guard, H1-H4 accounting
  experiments.py   smallest-experiment planner + belief update from real outcomes
  store.py         durable JSON backing (survives restart)
  minds.py         Minds Builder integration (persistent agent state)
  app.py           FastAPI: /api/remnants, expressions, decisions, experiments, /api/mind
frontend/
  src/App.tsx      archive-style UI: remnants, register, detail, provenance, experiments, mind
```

## Run it

```bash
# backend
cd backend
uv sync
source .venv/bin/activate
python -m uvicorn remnant.app:app --port 8000

# demo scenario (synthetic, clearly labeled)
python -m scripts.demo

# tests
python -m pytest tests/ -q

# frontend
cd frontend
npm install
npm run dev   # http://localhost:5173 (proxies /api -> :8000)
```

## Deployment

**Live:** https://remnant-two.vercel.app (Creative Minds Jam #1 submission build)

Single Vercel project: Vite static frontend + Python (FastAPI) serverless function at
`/api/*`. Serverless FS is read-only, so the deployed API runs in **memory mode**
(`STORAGE_PATH=:memory:`): the labeled synthetic demo corpus seeds at cold start, and
`/api/v1/health` honestly reports `storage_mode: memory`. The durable deployment
(VPS, systemd, JSON store + backups + corruption recovery) is the production-grade
path documented in `docs/DEPLOY.md`.

- Frontend: `scripts/vercel-build.sh` stages `deploy/dist` (static) + root `api/` (function).
- API: `api/index.py` entrypoint; rewrites route `/api/*` → function, everything else → SPA.
- Deploy: `npx vercel deploy --prod --yes` (alias `remnant-two`).

## Honesty table

| Area | Status |
|------|--------|
| Core domain + inference + experiments + store | **Real — tested** (36 tests passing) |
| Competing-hypothesis accounting (H1-H4) | **Real — tested** |
| Adversarial token-collision guard | **Real — tested** |
| Experiment planner + belief update | **Real — tested** |
| Persistence across sessions (store) | **Real — tested** |
| Minds Builder memory mirroring + recovery (to/from the persistent Mind's conversation) | **Real — verified live** (written + read back via recover; needs env to run) |
| Cross-language discovery engine (concept glossary) | **Real — tested** (candidate, never auto-merge; adversarial guard) |
| Demo corpus | **Synthetic, labeled** — and NOT pre-encoded: the discovery engine decides the grouping |
| Real community data ingestion | **Real — `scripts/import_youtube.py`** imported 226 real comments (public video, full provenance) into the dev store; live site runs on labeled synthetic + whatever a visitor ingests |
| Frontend UI | Real — builds clean, rendered in browser |
| Full live Minds loop (autonomous follow-up executed THROUGH the Mind) | **Not claimed** — the observatory runs in the backend; the Mind holds the memory narrative (recoverable), the backend does the deterministic accounting |

## Limitations

- Semantic grouping in the core slice uses token-aware, evidence-accounted matching,
  not embeddings; the *accounting* is deterministic and inspectable, which is the
  defensible part. Embeddings can plug in behind the same interface.
- H1-vs-H2 ambiguity is inherent to the problem; the product treats it as the feature.
- This is a vertical slice, not a platform: one undeniable mechanism, demonstrated
  flawlessly, rather than ten shallow features.

## Future directions

Creator community memory → unresolved-need intelligence → experiment engine →
creator-product validation → long-term audience relationship infrastructure.

---

*REMNANT is not an archive. It is a persistent, autonomous memory of unresolved
audience need.*