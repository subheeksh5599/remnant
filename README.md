<div align="center">

<img src="docs/remnant-banner.png" alt="REMNANT — the Mind that remembers what communities leave behind" width="100%" />

&nbsp;

[![Live demo](https://img.shields.io/badge/●_live-remnant--two.vercel.app-34d399)](https://remnant-two.vercel.app)
[![Tests](https://img.shields.io/badge/tests-62%20passing-3fb950)](backend/tests)
[![Track](https://img.shields.io/badge/Creative%20Minds%20Jam%20%231-Track%201-5C6B7A)](https://www.animocabrands.com/minds)
[![License: MIT](https://img.shields.io/badge/license-MIT-34d399.svg)](LICENSE)
![Real data](https://img.shields.io/badge/real%20data-only%20imports%2C%20no%20seeds-34d399)
![Minds](https://img.shields.io/badge/Minds-persistent%20memory-f4b728)

### The Mind that remembers what communities leave behind.

Every community produces thousands of audience expressions — YouTube comments, GitHub issues, Discord messages, support tickets. Almost all quietly disappear into the conversation. REMNANT is the layer that remembers them: a **persistent Minds agent** that discovers **candidate recurring needs** across years, holds the **competing explanations** for why they keep appearing, tests them with **pre-registered experiments**, and updates its beliefs from **measured outcomes** — never from vibes.

</div>

---

## Table of contents

- [See it in one command](#-see-it-in-one-command)
- [The one rule — never fake certainty](#the-one-rule--never-fake-certainty)
- [What REMNANT does](#what-remnant-does)
  - [Cross-language discovery — the money-shot](#1--cross-language-discovery--the-money-shot)
  - [Competing explanations H1–H4](#2--competing-explanations-h1h4)
  - [Pre-registered experiments](#3--pre-registered-experiments)
  - [Persistent Minds memory + recovery](#4--persistent-minds-memory--recovery)
  - [Autonomous observatory](#5--autonomous-observatory)
  - [Real-data imports, from the website](#6--real-data-imports-from-the-website)
- [Architecture](#architecture)
- [Safety, enforced in code](#safety-enforced-in-code)
- [Engineering decisions & the hard problems](#engineering-decisions--the-hard-problems)
- [What's real vs pending — the honesty table](#whats-real-vs-pending--the-honesty-table)
- [Tests](#tests)
- [Run it locally](#run-it-locally)
- [Configuration](#configuration)
- [Deploy](#deploy)
- [Project layout](#project-layout)
- [Tech stack · Credits · Roadmap](#tech-stack)

---

## ▶ See it in one command

The full belief lifecycle on one remnant, through the API — this is real output from the local durable backend, from the labeled synthetic demo corpus (real data imports work through the exact same code path):

```console
$ python -m pytest tests/ -q
62 passed

$ python
>>> from fastapi.testclient import TestClient
>>> from remnant.app import app
>>> c = TestClient(app)
>>> c.post("/api/v1/demo/load")          # labeled synthetic corpus → discovered, not pre-encoded
>>> rid = c.get("/api/v1/remnants").json()[0]["remnant_id"]
>>> c.post(f"/api/v1/remnants/{rid}/experiments").json()["threshold_value"]
0.04
>>> c.post(f"/api/v1/remnants/{rid}/experiments/{eid}/outcome",
...        json={"observed_value": 0.067}).json()["resolution_state"]
'candidate → revisited'
```

That verdict — **`observed 0.067 >= pre-registered 0.040 → CLEARED`** — is arithmetic, not opinion. The threshold was locked *before* the observation existed. And the same experiment's outcome was mirrored into the Minds agent's conversation, where a fresh session could read it back — that is the product in two lines.

---

## The one rule — never fake certainty

A candidate is a candidate; a fact is a fact. **REMNANT never presents a discovery as proven continuity.** The matcher's output for its own benchmark pair — a 2022 "Can you make a beginner ZK tutorial?" and a 2026 "How do I start building with zero knowledge?" — is `candidate / medium`, with supporting evidence, conflicting evidence, and explicit uncertainty, *never* a merged remnant and *never* a claim of continuity. Belief moves only through a crossed threshold, and the H1–H4 panel keeps the alternatives alive even after a verdict.

This is enforced in three places:

1. **The matcher is deterministic and auditable.** A curated concept glossary (`zero_knowledge ↔ zk`, `on_ramp ↔ "new to"`) produces decisions you can inspect line-by-line. It cannot hallucinate, and it cannot "feel" — it conservatively candidates and lets the experiment decide.
2. **The demo corpus is labeled SYNTHETIC and only appears when a developer asks for it.** The website starts empty. Real imported data is labeled real. The two are never mixed.
3. **`insufficient_evidence` is a real verdict.** When the relationship genuinely cannot be established, the system says so — it is not a failure state, it is the honest answer, and an adversarial pair in the Safety lab demonstrates it live.

### The resolution states

| | State | Meaning |
|:--:|---|---|
| 🔵 | **candidate** | Discovery linked evidence into a possible need — plausible, unproven |
| ⚪ | **insufficient_evidence** | Not enough signal to link at all — refused to guess |
| 🟡 | **unresolved / dormant / under_experiment** | Held, waiting, or being measured |
| 🟢 | **fulfilled / validated** | Creator adopted the need, or an experiment supported it |
| 🔴 | **rejected / disproven** | Creator declined, or an experiment killed the hypothesis |
| ↻ | **revisited** | New evidence or a cleared experiment reopened it |

The transition map is a guarded state machine: a terminal `fulfilled` remnant cannot be silently moved, and every transition is logged with a reason.

---

## What REMNANT does

Six capabilities, each with the mechanism behind it. All live at [remnant-two.vercel.app](https://remnant-two.vercel.app).

### 1 · Cross-language discovery — the money-shot

The core object is the **remnant**: a time-aware hypothesis about an unresolved community need, with its evidence, its competing explanations, and its full transition log. Remnants are formed by the **discovery engine** — a deterministic concept-glossary matcher that links expressions across years and vocabularies:

```
"Can you make a beginner ZK tutorial?"   (2022)
"How do I start building with zero knowledge?"   (2026)
        ↓  shared concepts: zero_knowledge + on_ramp
candidate / medium — supporting + conflicting + uncertainty
        ↓  never auto-merged; H1–H4 held separately
```

The 2022→2026 relationship in the demo corpus is **discovered by the engine, not encoded by the corpus**: the loader ingests a flat list of raw expressions one at a time, and grouping is the matcher's decision, recorded as `discovered_links` with the evidence that produced it.

### 2 · Competing explanations H1–H4

Every remnant holds four hypotheses about *why* the need keeps appearing:

| | Hypothesis | What it claims |
|:--:|---|---|
| H1 | **Persistent need** | The same community genuinely wants it, still |
| H2 | **New cohort** | A different audience keeps discovering the gap |
| H3 | **Temporary trend** | One wave of interest, no lasting need |
| H4 | **Semantic coincidence** | The words overlap; the needs do not |

Each carries `supporting_evidence` and `contradicting_evidence` as append-only strings. **Contradicting evidence is never suppressed** — it is the machine's guard against self-deception. After a CLEARED experiment, H1 moves medium → high with the verdict appended to its evidence; H2, H3 and H4 stay alive with honest lower confidence, because a single experiment cannot close them.

### 3 · Pre-registered experiments

The experiment planner proposes the smallest decisive test for a remnant, with defaults the creator can override (metric, threshold, target population, duration). The threshold is **locked at plan time** — recorded, immutable, and displayed before any observation:

```
Experiment 7d5c148f
  hypothesis: the beginner-ZK need is alive in the current audience
  metric:     comment-to-view ratio
  threshold:  0.04 gte   (failure band < 0.02)
  status:     planned
```

Observing `0.067` produces `CLEARED` deterministically (`0.067 >= 0.040`); the state machine moves `candidate → revisited`, H1 is updated, the Minds mirror fires, and the audit ring records transitions, verdicts and request IDs. Duplicate outcomes are **rejected with 409** — evidence is immutable.

### 4 · Persistent Minds memory + recovery

The Mind is not decorative: **every belief-critical change is mirrored into the Minds agent's conversation** as a structured `[memory]` line — a new audience expression, an experiment outcome, an autonomous observatory action. The recovery path, `recover_context()`, reads those lines back and reconstructs what the agent knew — verified live against a Minds agent: a message written through the deployed site, read back from the agent's conversation in a fresh session, including the agent's own reply.

> **Honest boundary:** Minds holds the *narrative*; the *accounting* — H1–H4 math, verdicts, belief reconstruction — is deterministic Python in the backend. This split is documented in `docs/architecture.md` and is deliberate: the arithmetic must be reproducible by anyone.

### 5 · Autonomous observatory

A background thread (durable deployment) revisits dormant and revisited remnants on a configurable interval, applies the recency test, and **surfaces candidates without any page load** — recording each pass as an audited action:

```
observatory.pass  →  remnant 76f052c5… revisited, fresh 2026 evidence
  action: recommend_follow_up
  audit_id: 4fbaa5d8…
```

Verified on the durable deployment: with the UI untouched and no API calls, the observer surfaced a remnant and wrote audit entries. On serverless (Vercel) the observatory fires via `/observatory/run` on page load — an honest, labeled difference, because a serverless function cannot own a background thread.

### 6 · Real-data imports, from the website

The site starts **empty**. Real evidence enters only through explicit import, from the website itself:

- **YouTube** — paste a video URL → real comments fetched via yt-dlp (no API key). The demo-canonical source is a 2020 Fireship Node.js guide: **901 real comments spanning 2020–2026**, including a 2023 "should I learn Node or React first?" — the same beginner need, different words, six years apart.
- **GitHub** — paste `owner/repo` → real open issues + comments from the GitHub API (foundry-rs/foundry yields real reporter names, dates and issue URLs).
- **Discord** — paste an export (JSON array, CSV, or lines).

Every expression carries `source.kind`, `source_id`, `author`, `occurred_at`, and a clickable `url` — provenance as a first-class field, displayed in the UI and surfaced as *REAL* vs *SYNTHETIC* everywhere. An imported comment never becomes "synthetic" and the labeled corpus never becomes "real".

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  MINDS (persistent narrative/cognitive memory)               │
│  • conversation mirror: [memory] <expression|outcome|action> │
│  • recover_context() reads the narrative back                │
│  • per-user Connect-your-Mind via Builder key                │
└───────────────▲───────────────────────────────▲──────────────┘
                │ mirror                        │ recover
┌───────────────┴───────────────────────────────┴──────────────┐
│  BACKEND (deterministic accountant — no LLM in the math)     │
│  discovery: concept-glossary matcher (inference.py)          │
│  accounting: H1–H4 + verdicts + belief rebuild (experiments) │
│  memory: Store (durable JSON file or :memory: serverless)    │
│  autonomy: Observatory (interval thread · audit ring)        │
│  evidence in: import/github · import/youtube · import/discord│
└──────────────────────────────────────────────────────────────┘
```

**The scan logic is written once.** The matcher, verdicts and state machine live in the `remnant` Python package; the API is a thin shell over them; the frontend is a thin shell over the API. A rule fixed in `inference.py` or `experiments.py` is fixed everywhere, and the test suite pins it.

### Component by component

| Module | Responsibility |
|---|---|
| **`remnant/inference.py`** | The concept glossary, `analyze_relationship`, `assess_hypotheses`, `discover_for_expression` — all deterministic, auditable |
| **`remnant/models.py`** | `Remnant` (hypothesis + evidence + transitions), `AudienceExpression` (provenance), `ResolutionState`, `Experiment` (creator overrides) |
| **`remnant/experiments.py`** | `plan_experiment` (locked threshold), `apply_observed_outcome` (CLEARED / DISPROVEN / UNCERTAIN branches + beliefs) |
| **`remnant/store.py`** | Durable JSON store with atomic persist, prefix-id resolution (serverless-safe), `:memory:` mode |
| **`remnant/ingest.py`** | Real-data importers (GitHub API, yt-dlp, Discord paste) with conservative link scoring |
| **`remnant/minds.py`** | Minds Builder client — HTTP-only (serverless-safe), `remember()`, `recover_context()`, per-user clients |
| **`remnant/observatory.py`** | The autonomous observer — interval thread, cooldowns, audited actions |
| **`remnant/app.py`** | FastAPI app + audit ring + request IDs (see [endpoints](#configuration)) |
| **`remnant/scripts_loader.py`** | The labeled synthetic corpus — ingested through discovery, never pre-encoded |

**Frontend** (`frontend/` — React + Vite, minimal editorial design):

| Route | Responsibility |
|---|---|
| **`/`** | Landing — the pitch, Track 1 framing |
| **`/dashboard`** | Mind status, system health, remnant summary |
| **`/remnants`** | All remnants — id, title, state, first/last detected, relevance, evidence strength |
| **`/remnants/:rid`** | The full record: discovery evidence, H1–H4, experiments + verdict, belief, provenance |
| **`/mind`** | Mind status, Ask-the-Mind (6 questions, prefix-id), persistence proof + Recover-from-Mind |
| **`/import`** | The only data entrance — YouTube / GitHub / Discord |
| **`/system`** | Health, evidence states, audit trail, storage mode |
| **`/lab`** | Adversarial semantic presets + demo controls (clearly labeled) |

---

## Safety, enforced in code

Every claim in this README maps to a mechanism, not a promise:

| Claim | How it's enforced |
|---|---|
| Nothing fake is ever presented as real | Real imports are labeled REAL by source; the corpus is labeled SYNTHETIC in history + UI; the download-only "Load demonstration corpus" control is the only way it appears |
| A discovery is never presented as proven | The matcher returns `candidate / medium` with supporting + conflicting + uncertainty; `insufficient_evidence` is a real verdict; the Lab demonstrates the collision guard |
| Verdicts are not opinions | `apply_observed_outcome` is arithmetic against the locked threshold; duplicate outcomes → 409; thresholds immutable after plan |
| State can't be silently corrupted | Guarded `transition_to` map; terminal states are terminal; every transition logged with reason + request id |
| The Mind can't be faked | `MindsError` propagation — when the Minds API is unconfigured/unreachable, the UI shows an explicit error state, never a fake "online" |
| Serverless ephemerality isn't hidden | `storage_mode: memory` in health + UI badge + reconnect note "no disk — honest" |
| Data provenance is first-class | `source.kind/source_id/author/url/occurred_at` on every expression, displayed and clickable |

---

## Engineering decisions & the hard problems

A few calls I'm glad I made, and the traps that taught me something.

- **The matcher is a curated glossary, not an embedding model.** Cross-language need discovery ("zero knowledge" vs "zk") without an LLM inside the accounting means every link decision is inspectable and reproducible — the trade-off is that the machine can't reason beyond its lexicon, which is precisely why candidates go to experiments rather than conclusions. A laplacian cannot hallucinate; it also cannot be clever. That boundary is the product's honesty, not its weakness.

- **The store resolves 8-character prefixes, because serverless re-seeds ids.** The UI invites "first 8 chars" — on Vercel each cold instance mints new full ids, so the backend resolves unique prefixes on any instance rather than 404ing the user's pasted prefix. Ambiguous prefixes return *None*, never a guess.

- **The corpus is ingested through discovery, not constructed around the answer.** The demo's 2022→2026 arc exists only because the engine links the expressions itself — the loader takes a flat list of raw evidence. If the matcher can't establish the link honestly, the demo shows `insufficient_evidence`. The story is the output of the machine.

- **The experiment threshold is locked before the observation exists.** Plan-time recording + immutability + 409-on-duplicate means the demo can't be accused of moving goalposts — the number on screen at plan time is the number used at verdict time.

- **Large-corpus over-clustering was a real bug, and the fix is conservative.** A 900-comment YouTube import collapsed into one giant remnant because generic intent words ("learn", "get", "start") matched everywhere. The discovery scorer now requires a topic-specific concept or ≥2 meaningful shared tokens to link — singletons stay singletons, genuine recurrences group. The failure mode was found by testing, not by luck.

- **On serverless, the observatory cannot own a thread — so we say so.** The durable deployment runs the interval observer; Vercel fires it on `/observatory/run` (page load). Both are real; the difference is labeled in the UI (`storage_mode: memory`) and in the honesty table. A background thread is a claim we only make where we can genuinely deliver it.

---

## What's real vs pending — the honesty table

| Capability | Status |
|---|---|
| **Cross-language discovery** (concept glossary) | **Real** — deterministic, tested, adversarially paired in the Lab |
| **H1–H4 accounting + belief reconstruction** | **Real** — deterministic, tested |
| **Pre-registered experiments** (locked threshold, creator overrides) | **Real** — tested (immutability, 409 duplicates) |
| **Deterministic verdicts** (`0.067 ≥ 0.040 → CLEARED`) | **Real** — arithmetic by construction, tested (CLEARED / DISPROVEN / UNCERTAIN) |
| **Guarded state machine** (candidate → revisited, terminal states) | **Real** — tested (invalid transitions rejected) |
| **Minds memory mirroring** | **Real — verified live** against a Minds agent (message written via the deployed site, read back in a fresh session) |
| **Minds recovery** (`/minds/recover/{rid}`) | **Real — verified live** |
| **Autonomous observatory** (no page load) | **Real on the durable deployment** — verified (action surfaced + audit ids); on Vercel it fires via `/observatory/run` and the UI says so |
| **Store survives process restart + belief replay** | **Real on the durable backend**; serverless honestly reports `storage_mode: memory` |
| **Real-data imports** (YouTube / GitHub / Discord from the website) | **Real** — live fetch at click time, full provenance; YouTube needs the yt-dlp extra (works on the durable backend, honest error on serverless) |
| **Real community data in the live demo** | **Real when you import it** — the site starts empty; the 901-comment Fireship + foundry imports are the demonstrated sources |
| **Synthetic demo corpus** | **Clearly labeled SYNTHETIC** — only via the explicit "Load demonstration corpus" control |
| **Observatory *acting through* the Mind autonomously** | **Not claimed** — the observatory runs in the backend; the Mind holds the narrative |
| **Reading a creator's private community without their export** | **Not claimed** — evidence in, evidence out through explicit imports |

---

## Tests

**62 tests** — pure-python, no network, run in seconds:

```bash
cd backend && source .venv/bin/activate
python -m pytest tests/ -q        # 62 passed
```

| Suite | Tests | Covers |
|---|--:|---|
| `test_core.py` | 16 | store persistence + prefix resolution, remnant transitions, experiment math |
| `test_discovery.py` | 7 | cross-language candidate discovery, collision guard, insufficient evidence, corpus groups without pre-encoding |
| `test_final_gate.py` | 14 | all three verdict branches, duplicates 409, threshold immutability, creator overrides, invalid transitions, Minds-failure, restart persistence |
| `test_production.py` | 25 | the full API surface, connect flow (401/422), adversarial endpoints, audit ring, recovery |

CI is not yet wired — `pytest` is the gate (documented, honest). What is exercised by hand rather than automated: the live Minds mirror/recovery, the yt-dlp YouTube fetch, and the observatory interval on a running deployment — each verified live and detailed in the honesty table.

---

## Run it locally

**Prerequisites:** Python 3.12+, Node 18+ (frontend only).

```bash
# Backend
cd backend
uv venv .venv && source .venv/bin/activate
uv pip install -e .                        # optional: uv pip install -e ".[importers]" for yt-dlp
python -m pytest tests/ -q                 # 62 passing
python -m uvicorn remnant.app:app --port 8000

# Frontend
cd frontend && npm install && npm run dev  # http://localhost:5173

# Real data — from the website (Import data page), or:
python -m scripts.import_github foundry-rs/foundry --limit 8
```

The frontend proxies `/api` to the backend at `:8000`. Without Minds env vars the Mind panel shows an honest "not configured" state instead of a fake online status.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `STORAGE_PATH` | `data/remnant.db` | Durable JSON store path; `:memory:` = serverless mode (honestly reported in `/health` + UI) |
| `MINDS_BUILDER_API_KEY` | — | Builder key for the env-configured Mind (set via CLI, never committed) |
| `MIND_ID` | — | Default Mind id (Wake) used when no creator connects their own |
| `REMNANT_OBSERVATORY_INTERVAL_S` | 600 | Observer tick on the durable deployment |
| `REMNANT_OBSERVATORY_COOLDOWN_S` | 3600 | Min interval between passes for the same remnant |

## Deploy

| | |
|---|---|
| **Web app + API** | **[remnant-two.vercel.app](https://remnant-two.vercel.app)** — Vercel, memory mode, Minds env configured live |
| **Durable backend** | `deploy/durable-observatory.sh` — idempotent, isolated to `/opt/remnant-durable`, real background observatory + durable store |

The Vercel deployment runs `storage_mode: memory` (read-only FS) and the UI says so. The durable deployment is where the observatory interval and restart-survival claims are genuinely true — full instructions in [DEPLOY.md](DEPLOY.md).

## Project layout

```
backend/
  remnant/           the package — inference · experiments · store · ingest · minds · observatory · app
  scripts/           import_github.py · import_youtube.py (CLI form of the same importers)
  tests/             62 tests (core · discovery · final gate · production)
frontend/
  vercel-api/        serverless ASGI entrypoint (memory mode, no seed)
  src/               React + Vite — pages · components · lib/api.ts
    pages/           Landing · Dashboard · Remnants · RemnantDetail · Import · Mind · System · Lab
docs/                architecture.md · DEPLOY.md · RUNOFSHOW.md (demo script)
deploy/              durable-observatory.sh
```

## Tech stack

- **Backend:** Python 3.12 · FastAPI · pydantic v2 · uvicorn — deterministic, no LLM inside the math.
- **Frontend:** React 19 · TypeScript (strict) · Vite — minimalist editorial design system.
- **Memory:** Minds by Animoca Brands — persistent narrative memory with recovery; per-user connect via Builder key.
- **Data:** yt-dlp (YouTube comments) · GitHub REST API · Discord exports — all with provenance.
- **Hosting:** Vercel (live demo, memory mode) · durable backend for the observatory.

## Credits

- Built for **Creative Minds Jam #1 — Track 1: Audience Growth & Engagement**, on **Minds by Animoca Brands**.
- The demo-canonical real corpus: a 2020 Fireship *Node.js Beginner's Guide* comment section (901 real comments) and `foundry-rs/foundry` issues, both imported live with provenance.
- The persistent Mind: configured as an env-connected Minds agent, verified live through mirror + recovery.

## Roadmap

Tracked as [GitHub issues](https://github.com/subheeksh5599/remnant/issues) — contributions welcome.

- **Durable observatory on shared infrastructure** — the observatory interval on a long-lived box (script ready; VPS deployment is the remaining step).
- **Timed re-observation rules** — dormant remnants revisited on a schedule with per-need cooldowns.
- **Minds as co-pilot** — the Mind not only mirrors, but proposes (read → propose → confirm as part of the memory loop).
- **More importers** — Telegram exports, email digests, CSV from any tool.
- **Experiment battery** — multi-experiment runs per remnant with a board of outcomes.

## License

MIT — see [LICENSE](LICENSE). Built to be probed: read the honesty table, run the tests, import your own community's data, and watch what REMNANT discovers.