# REMNANT — Run of Show (live judging demo)

**Thesis (one line):** "Creators lose unresolved audience needs into the past.
REMNANT is the persistent Mind that remembers them, refuses to fake certainty, and
runs pre-registered experiments to decide what deserves attention now."

**Hard rule:** every number on screen is a real recorded value from a real run, or
the clearly-labeled synthetic demo corpus. Nothing is fabricated. If something
breaks, the backup ladder is built only from real artifacts (below).

## Pre-flight (before you walk up)

- [ ] Backend running: `cd backend && source .venv/bin/activate && python -m uvicorn remnant.app:app --port 8000`
- [ ] Frontend running: `cd frontend && npm run dev` (http://localhost:5173)
- [ ] Health check: `curl http://127.0.0.1:8000/api/health` → ok:true
- [ ] Demo state seeded (fresh `data/demo.db`, one remnant with 2022→2026 arc)
- [ ] Backup tab open: this repo's README "Proof" section (live links)
- [ ] Recorded REAL video ready as last-resort backup
- [ ] Network check: local only (no external dependency needed for the demo)

## Timed beats (target ~1:50)

### 0:00–0:15 — The pain (cold open)
Show the REMNANT home / register view.
Narration: "Creators receive thousands of audience requests. Most disappear into
the past — people leave, platforms change, language changes. The need survives;
the memory of it doesn't."

### 0:15–0:40 — The REMNANT + historical evidence
Open REMNANT #918 (Beginner ZK education). Point at the temporal timeline.
Narration: "This REMNANT was born from 2022–2023 requests — 'Can you make a
beginner ZK tutorial?' — that the creator never answered. Dormant."
Point at the timeline: 2022 ● ● ● → 2023 ● → ○ dormant gap → 2026 ● ● ●.

### 0:40–0:55 — Current evidence (different language)
Scroll to the 2026 expressions.
Narration: "Years later, new audience members ask the same underlying thing in
different words. REMNANT marks this as POSSIBLE CONTINUITY — it does not scream
'reawakened'."
Click "Ask the Mind" → show the competing explanations block:
H1 persistent need [high evidence] · H2 new cohort [medium] · H3 trend [low] · H4
coincidence [low].

### 0:55–1:10 — The honest position + the pre-registered experiment
Narration: "Two explanations remain plausible — a persistent need or a new cohort.
REMNANT refuses to fake certainty. It plans the smallest experiment that can
disambiguate them."
Show the experiment card: one 90-second explainer; metric = comment-to-view ratio
at 48h; **pre-registered threshold 0.040 — set before observing.**

### 1:10–1:30 — The observed number + the verdict (THE money-shot)
Record the observed value 0.067.
Narration: "The explainer runs. Observed: 0.067 comments per view.
0.067 ≥ pre-registered 0.040 → CLEARED."
Point at the deterministic verdict line. Then show the belief update: H1 gains
support, state → revisited.
Narration: "The belief updated from a number — not from a vibe."

### 1:30–1:50 — Persistence: reload the app
Reload the page (fresh session). Click "Ask the Mind: what do you currently believe?"
Narration: "Fresh session. Same question. The Mind replays the ENTIRE chain —
2022 evidence, 2026 evidence, the competing explanations, the pre-registered
threshold, the observed 0.067, the verdict, and the updated belief. And it still
says the honest thing: this is a belief, not a fact — H2 remains plausible."

Closing line: "Your audience changes. Your platforms change. People leave.
REMNANT remembers what was left behind — and runs the experiment to know if it
matters now."

## The one emotional beat (slow down here)

At 1:10–1:30 (the verdict): pause, let the number land. "Observed 0.067 — cleared
the pre-registered 0.040." That single deterministic line is the difference
between "an AI that remembers" and "a system that learns from what happened."
Do not rush it.

## Backup ladder (real artifacts ONLY — no mocks, ever)

1. Backend hiccup → restart uvicorn; demo state is in `data/demo.db`, survives.
2. Frontend hiccup → `npm run dev` restart; or open the README "Proof" section.
3. Everything dies → screen-share the repo: README + CHECKLIST + the demo script
   (`python -m scripts.demo` output pasted — real run output).
4. Last resort → play the recorded REAL demo video.

## Anticipated judge questions (short answers)

- "Isn't this just comment clustering?" → No — the primitive is a time-aware
  hypothesis with competing explanations and pre-registered experiments. Clustering
  doesn't decide what to test; REMNANT does.
- "How do you know it's the same need?" → I don't. H1 vs H2 is held honestly; the
  experiment is the disambiguator, and the verdict is a belief, not a fact.
- "The 0.067 data — is it real?" → In the demo it's the clearly-labeled synthetic
  corpus; the real path ingests a real measured number with provenance.
- "Why not just keyword-search old comments?" → Because demand that disappears is
  not demand that died. Token overlap is explicitly NOT continuity.
- "Where's the Minds integration?" → The Mind is the steward of this memory; the
  backend drives the Minds Builder surface (state, cognition) and the continuity
  thesis is the product. See docs/architecture.md for the honest split.

Full written answers: docs/JUDGE-QA.md