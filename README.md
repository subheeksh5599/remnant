<p align="center">
  <a href="https://github.com/subheeksh5599/remnant"><img src="docs/remnant-banner.png" width="750" alt="REMNANT"></a>
</p>

<p align="center">
    <em>The Mind that remembers what communities leave behind.</em>
</p>

<p align="center">
<a href="https://remnant-two.vercel.app" target="_blank">
    <img src="https://img.shields.io/website/https/remnant-two.vercel.app" alt="Website">
</a>
<a href="https://github.com/subheeksh5599/remnant/actions/workflows/test.yml" target="_blank">
    <img src="https://github.com/subheeksh5599/remnant/actions/workflows/test.yml/badge.svg" alt="Test">
</a>
<a href="https://github.com/subheeksh5599/remnant/tree/main/backend/tests" target="_blank">
    <img src="https://img.shields.io/badge/tests-62%20passing-3E7A5C" alt="Tests">
</a>
<a href="https://opensource.org/licenses/MIT" target="_blank">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
</a>
</p>

---

**Website**: <a href="https://remnant-two.vercel.app/" target="_blank">remnant-two.vercel.app</a>

**Documentation**: <a href="https://github.com/subheeksh5599/remnant/tree/main/docs" target="_blank">docs</a>

**REMNANT Mind**: <a href="https://github.com/subheeksh5599/remnant" target="_blank">Repository</a>

---

REMNANT is a persistent Minds agent that discovers candidate recurring needs across a creator's community, preserves competing explanations about why they recur, and learns from pre-registered experiments which needs are actually worth acting on now.

**[What it is](#what-it-is)** - **[The loop](#the-loop)** - **[Features](#features)** - **[Hard problems](#hard-problems)** - **[Architecture](#architecture)** - **[Honesty](#honesty)** - **[Requirements](#requirements)** - **[Installation](#installation)** - **[Usage](#usage)** - **[Contributors](#contributors)**

## What it is

Every community produces thousands of audience expressions — YouTube comments, GitHub issues, Discord messages, support tickets. Almost all of them quietly disappear into the conversation. REMNANT is the layer that remembers them.

It was built for exactly one question, which is the hardest question in creator economics:

> *"People asked for this in 2022. They're asking again in 2026, in different words. Is this a real recurring need — or a coincidence?"*

REMNANT answers that question by holding **time-aware hypotheses** (called *remnants*) about unresolved community needs. Each remnant tracks the underlying need, the evidence that supports it, the competing explanations for why it keeps appearing, and a pre-registered experiment plan to separate them. Nothing gets decided by vibes: belief changes only through measured outcomes.

<b>REMNANT is one of three entries in Creative Minds Jam #1 — Track 1: Audience Growth & Engagement, built on the Minds by Animoca Brands platform.</b>

## The loop

```
audience expressions (past + present)
        │
        ▼  DISCOVERY ENGINE — concept-glossary matcher, auditable, no LLM
candidate recurring need (H1: persistent · H2: new cohort · H3: trend · H4: coincidence)
        │
        ▼  PRE-REGISTERED EXPERIMENT (locked threshold before any observation)
real-world measurement
        │
        ▼  DETERMINISTIC VERDICT  (observed 0.067 >= threshold 0.040 → CLEARED)
belief update (H1 medium → high) + Minds memory mirror + state transition
        │
        ▼  long-term community memory — and the cycle repeats
```

The core object is the **remnant**: an explicit, honest, time-aware hypothesis with provenance, evidence strength, resolution state, and a full transition log. The demo corpus (clearly labeled synthetic) shows the 2022→2026 arc; real community data is imported through the website (YouTube comments, GitHub issues, Discord exports) and runs through the exact same pipeline.

## Features

- **Cross-language need discovery** — a transparent concept glossary links "Can you make a beginner ZK tutorial?" with "How do I start building with zero knowledge?" (zero shared words) as a *candidate* — never auto-merged, never presented as proven continuity.
- **Competing explanations (H1–H4)** — persistent need, new cohort, temporary trend, semantic coincidence — each with supporting and contradicting evidence; contradicting evidence is never suppressed.
- **Pre-registered experiments** — metric, threshold, target population and duration locked before observation; verdict is arithmetic, not opinion: `observed 0.067 >= pre-registered 0.040 → CLEARED`.
- **Persistent Minds memory with recovery** — every belief-critical change is mirrored into the Minds agent's conversation; a fresh session can recover what the agent knew, even after a store wipe.
- **Autonomous observatory** — a background observer revisits dormant remnants on an interval, surfaces candidates, and records its own audit trail — no page load required on the durable deployment.
- **Provenance-first evidence** — every expression carries its real source, author, URL and timestamp; real data is labeled real, synthetic stays labeled synthetic, and the two are never mixed.
- **Full web app** — landing, dashboard, remnant explorer with belief reconstruction, Ask-the-Mind, System & audit, and a Safety lab with real-data import (YouTube / GitHub / Discord) and an adversarial semantic guard.

## Hard problems

1. **Cross-language discovery without an LLM.** Matching needs across years requires understanding near-synonyms ("zero knowledge" vs "zk"), which naively means embeddings or an LLM inside the accounting. REMNANT uses a curated, deterministic concept glossary so every link decision is inspectable and reproducible. The trade-off is real: the machine never *reasons* — it conservatively produces candidates and lets the experiment decide. A hand-written laplacian cannot hallucinate, but it also cannot be clever; that is the honest boundary.

2. **Serverless persistence vs. "remembers across years".** The public demo runs on Vercel where every cold start throws the store away. The honest architecture: the durable store lives on the deployed backend, while the *Mind* — the narrative memory — is external and persistent by construction. The recovery path reads the belief narrative back from the Minds platform itself (verified live), so even a fully wiped instance can reconstruct what it knew.

3. **Never faking certainty.** The system's whole value is trust, so uncertainty is first-class: `insufficient_evidence` is a real verdict, H1–H4 confidence moves in qualitative steps with appended evidence, and the demo explicitly shows a same-topic pair ("I want to learn zero knowledge proofs" vs "Can we get merch pls") returning *different-need* — proof the guard is not a collapser. Nothing in the product pretends a candidate is a fact.

4. **Large-corpus over-clustering.** A 900-comment YouTube import initially collapsed into one giant remnant because generic intent words ("learn", "get", "start") matched across unrelated comments. The discovery scorer now requires a topic-specific concept or ≥2 meaningful shared tokens to link, so genuine recurrences group while singletons stay singletons — an honest, observable property of the matcher.

## Architecture

The product is deliberately split so a judge can verify each half:

```
┌───────────────────────────────────────────────┐      ┌──────────────────────────────┐
│  MINDS (persistent narrative/cognitive memory) │      │  BACKEND (deterministic)     │
│  • conversation mirror: [memory] ...           │◄────►│  • concept glossary matcher  │
│  • every ingest / outcome / autonomous action  │      │  • H1–H4 accounting          │
│  • recover_context() reads it back             │      │  • verdicts (arithmetic)     │
│  • per-user connect via Builder key            │      │  • belief reconstruction     │
└───────────────────────────────────────────────┘      │  • observatory + audit ring  │
                                                        └──────────────────────────────┘
```

- **Minds** = the persistent identity and memory. It is the agent; the product is *a Minds agent*. If Minds is removed, the product fundamentally stops working.
- **Backend** = the accountant. Deterministic Python; **no LLM inside the arithmetic**. H1–H4 math, verdicts and belief reconstruction are reproducible from the same evidence by anyone.
- **No mock in the middle** — the same code path serves the synthetic demo corpus (labeled) and real imports (labeled real).

## Honesty

The product is built to be probed. Here is exactly what is real, what is labeled, and what is not claimed:

| Claim | Status |
|---|---|
| Minds memory mirroring (every belief-critical change → Minds conversation) | **Real — verified live** against a Minds agent ("Wake"): message written, read back in a fresh session |
| Minds recovery (reconstruct belief from the Mind's conversation) | **Real — verified live** |
| Cross-language discovery (concept glossary) | **Real — deterministic, auditable, no LLM** |
| H1–H4 epistemic accounting + belief reconstruction | **Real — deterministic** |
| Pre-registered experiments with creator overrides | **Real** (defaults autonomous; metric/threshold/segment/window overridable) |
| Deterministic verdicts (`0.067 ≥ 0.040 → CLEARED`) | **Real — arithmetic by construction** |
| Autonomous observatory on the durable deployment (no page load) | **Real** — verified: surfaced a dormant remnant autonomously, audit entries recorded |
| Durable store surviving process restart + belief replay | **Real on the durable backend**; on serverless the UI reports `storage_mode: memory` honestly |
| Website import of real community data (YouTube/GitHub/Discord) | **Real** — live fetch at click time, full provenance; YouTube needs yt-dlp (durable backend), honest error on serverless |
| Synthetic demo corpus | **Clearly labeled SYNTHETIC** everywhere; only appears via the explicit "Load demonstration corpus" button |
| Footage or claim of the observatory *acting through* the Mind autonomously | **Not claimed** — observatory runs in the backend; the Mind holds the narrative |
| "REMNANT can read the creator's private community without their export" | **Not claimed** — evidence in, evidence out through explicit imports |

Backend tests: **62 passing** (`backend/tests/`), including adversarial same-need/collision/insufficient-evidence paths, all three verdict branches, duplicate-outcome rejection, threshold immutability, creator-defined overrides, invalid state transitions, Minds-failure handling, and restart persistence.

## Requirements

**REMNANT requires Python version 3.12 or higher (backend) and Node 18 or higher (frontend).**

> It is recommended to use a [virtual environment](https://docs.python.org/3/library/venv.html) for installing REMNANT, in order to avoid dependency conflicts. You can use your favorite virtual environment management system, like [conda](https://docs.conda.io/en/latest/), [poetry](https://python-poetry.org/), or [uv](https://docs.astral.sh/uv/) for example.

Furthermore, the following software packages need to be installed in your system:

- **Ubuntu**: `sudo apt-get install python3.12 python3.12-venv curl git`
- **Mac OS**: `brew install python@3.12 git curl`
- **Windows**

    > Windows support is currently under development. For the time being, we highly recommend using [Windows Subsystem for Linux](https://learn.microsoft.com/en-us/windows/wsl/install) and then following the Linux instructions.

For the optional **YouTube importer** (real comments): `uv pip install -e ".[importers]"` (yt-dlp). GitHub and Discord importers need nothing extra.

## Installation

You can install REMNANT directly from the repository:

```bash
git clone https://github.com/subheeksh5599/remnant.git
cd remnant/backend
uv venv .venv
uv pip install -e .
```

Then you can run remnant in your python shell, notebook or application as follows:

```python
import uvicorn
from remnant.app import app

uvicorn.run(app, port=8000)
```

... and just like that, you're ready to go! For the frontend, `cd frontend && npm install && npm run dev` (serves the dashboard at `http://localhost:5173`). We support multiple [deployment modes](https://github.com/subheeksh5599/remnant/blob/main/docs/architecture.md) (durable backend with a real observatory interval, or serverless memory mode with the honest `storage_mode: memory` label).

## Usage

For example, [ingest the labeled demo corpus](https://github.com/subheeksh5599/remnant/blob/main/backend/remnant/scripts_loader.py) and let discovery surface the needs:

```python
from fastapi.testclient import TestClient
from remnant.app import app

with TestClient(app) as c:
    c.post("/api/v1/demo/load")   # labeled synthetic corpus, discovered not pre-encoded
    remnants = c.get("/api/v1/remnants").json()
    print([r["title"] for r in remnants])
```

And then run the money-shot — the whole belief lifecycle on one remnant:

```python
rid = remnants[-1]["remnant_id"]
eid = c.post(f"/api/v1/remnants/{rid}/experiments").json()["experiment_id"]
out = c.post(f"/api/v1/remnants/{rid}/experiments/{eid}/outcome",
             json={"observed_value": 0.067}).json()
print(out["resolution_state"])   # -> revisited
```

Real evidence is imported the same way from the website (`Import data` page: YouTube URL, GitHub repo, or Discord paste) — every expression carries its real source, author, URL and timestamp. Please refer to the [documentation](https://github.com/subheeksh5599/remnant/tree/main/docs) to learn more about how to use REMNANT.

## API

All routes under `/api/v1`. The `remnants` endpoints cover the full lifecycle: list/detail, expressions, creator decisions, experiments (plan + outcome), belief reconstruction and `ask`. `import/*` fetches real evidence; `observatory/*` runs and audits autonomous passes; `minds/*` connects a creator's own Mind, reports status, and recovers memory; `demo/*` load/reconnect the clearly-labeled synthetic corpus; `/audit` is the append-only event ring.

## Contributors

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/subheeksh5599"><img src="https://avatars.githubusercontent.com/u/251461028?v=4" width="100px;" alt="Komari Subheeksh"/><br /><sub><b>Komari Subheeksh</b></sub></td>
    </tr>
  </tbody>
</table>
<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

Want to be part of the persistent community-memory revolution? All contributions are welcome! Check out the [contribution guide](https://github.com/subheeksh5599/remnant/blob/main/docs/architecture.md) to learn more about how to develop with and for REMNANT.