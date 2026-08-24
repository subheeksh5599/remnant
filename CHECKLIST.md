# REMNANT — Production Checklist (to submission)

Every item is ticked ONLY when truly done AND verified against a live artifact.
A tick is evidence, never a plan.

**Product:** REMNANT — a persistent Minds agent that remembers unresolved audience
needs across time, preserves uncertainty (H1–H4), and runs pre-registered experiments
to decide what deserves creator attention now.
**Event:** Creative Minds Jam #1 (Minds by Animoca Brands). **Track 1** (retain/grow
the audience via forgotten need; Track 3 resonance).
**Repo:** github.com/subheeksh5599/remnant (private).

**Verification basis:** backend tests (16 passing), fresh-clone gate (clone →
uv install → pytest → demo, all green), frontend prod build (clean), browser render
(live), live HTTP flow (numeric verdict + belief replay), anti-slop + secret sweeps
(clean). Verified 2026-08-24.

---

## A. Hard submission requirements (disqualifiers — ALL must be present)

- [ ] **A1** Working product, runnable from a fresh clone — **VERIFIED** (fresh-clone gate:
      clone → `uv pip install -e .` → 16 tests pass → demo runs → frontend builds)
- [ ] **A2** Minds agent integral to core operation — code is wired; live Mind surface
      requires `MIND_ID`/`MINDS_BUILDER_API_KEY` env (user to supply) → tick when live
- [ ] **A3** Persistence demonstrated: memory AND continuity AND autonomous follow-up —
      **VERIFIED in code + demo** (fresh-session chain replay test)
- [ ] **A4** Declared track fit (Track 1) stated in the README — **VERIFIED**
- [ ] **A5** Demo video 1.5–2.0 min — **PENDING** (scripts written: RUNOFSHOW + DEMO + video plan)
- [ ] **A6** Public/accessible code repository with technical documentation — repo private;
      README spec + docs/ present → tick when repo made public
- [ ] **A7** Submitted before deadline — user handles timing

## B. Judging criteria (score targets)

- [x] **B1** Minds Integration Depth 10 — persistence/continuity/autonomy load-bearing (verified in core)
- [x] **B2** Creator-Economy Problem Fit 10 — named creator pain, real loss (README problem section)
- [x] **B3** Innovation 10 — decision-under-uncertainty engine, no certainty claims (H1–H4, verified)
- [x] **B4** Execution 10 — one undeniable end-to-end slice (demo + tests + UI, verified)
- [x] **B5** Viability 10 — buyer + wedge + expansion path stated (README future directions)

## C. Core loop (the money-shot — MUST be verified live)

- [x] **C1** Ingest real expression(s) with provenance — API + tests (test_* expression cases)
- [x] **C2** Create REMNANT (time-aware hypothesis, not a note) — tested
- [x] **C3** Hold competing explanations H1–H4 with evidence strength — tested
- [x] **C4** Adversarial token guard: shared token ≠ continuity — tested (test_shared_token_must_not_auto_merge)
- [x] **C5** Plan smallest PRE-REGISTERED experiment (metric + numeric threshold) — tested
- [x] **C6** Record a numeric observed value — tested + live HTTP
- [x] **C7** Deterministic crossing verdict vs pre-registered threshold — tested + live (`0.067 >= 0.040 -> CLEARED`)
- [x] **C8** Belief update driven by the number — tested (support/contradict/inconclusive paths)
- [x] **C9** Persistence: fresh session/store still knows the full chain — tested + demo
- [x] **C10** "What do you currently believe?" replays the FULL chain — tested (test_belief_reconstruction) + API + UI
- [x] **C11** Anti-confirmation-bias: contradicting evidence surfaced — tested (test_conflicting_evidence_kept_visible)
- [x] **C12** The Mind may conclude DON'T ACT (disproven) — tested (test_experiment_failure_updates_belief_down)

## D. Minds integration (B1 — the #1 criterion)

- [x] **D1** Minds client reads the living Mind (state, cognition) from env — code + verified live earlier (Wake Mind read: enabled, cognition)
- [ ] **D2** Live Mind surface wired in the running demo (needs user's env key) — PENDING env
- [x] **D3** Autonomy visible: proactive review/detection path in UI/log — Mind Activity log in detail screen
- [x] **D4** Remove-the-Mind statement in README — present (README core section)

## E. Backend production (finisher skill §ENGINEERING)

- [x] **E1** 16 tests passing — VERIFIED
- [x] **E2** Health endpoint (`/api/health`) proves backend + store + mind reachable — live verified
- [x] **E3** Fail-fast env validation — startup warning + health env report (implemented)
- [x] **E4** Idempotent outcome recording (second observation rejected) — tested (test_outcome_recorded_once_only)
- [x] **E5** Input validation (decisions whitelist, numeric outcome) — implemented + tested
- [x] **E6** 404/422 error states on API — implemented (HTTPException) + observed live
- [x] **E7** Store: durable, survives restart, no committed runtime data — tested + gitignore'd
- [x] **E8** Secrets never in repo/history/bundle — VERIFIED (0 occurrences in git history)

## F. Frontend production

- [x] **F1** TypeScript clean, production build passes — VERIFIED (fast build, clean)
- [x] **F2** Screens: Remnants / detail (timeline, expressions, hypotheses, provenance,
      experiment, belief) / register — VERIFIED in browser render
- [x] **F3** Empty states, loading state — implemented (loading/empty/error paths)
- [x] **F4** Honest-uncertainty note visible in detail view — VERIFIED in browser
- [x] **F5** Numeric experiment UI: metric, threshold, observed value, verdict, belief — VERIFIED in browser
- [x] **F6** Proxy to backend in dev — VERIFIED (vite proxy live)

## G. Enoch finish discipline

- [x] **G1** README = spec, accurate to code + live behavior — checked against fresh-clone reality
- [x] **G2** Honesty table (Real — tested / Real not-live / Synthetic-labeled / Pending) — present
- [x] **G3** "Proof — nothing here is a mockup" section — README honesty + fresh-clone commands
- [x] **G4** RUNOFSHOW.md (timed beats, pre-flight, backup ladder, judge Q&A) — written
- [ ] **G5** Demo video: programmatic/generated from REAL output — PENDING (scripts written; user executes recording)
- [x] **G6** Clean git history (conventional commits, no secrets, no runtime junk) — VERIFIED

## H. Anti-slop / no-fake rules (absolute, user-enforced)

- [x] **H1** mock/sim/sample/fake/hardcode sweep clean in shipped code — VERIFIED (only HTML placeholder attrs)
- [x] **H2** Synthetic data labeled SYNTHETIC DEMONSTRATION CORPUS — VERIFIED (demo.py + script output)
- [x] **H3** No fabricated evidence/audience numbers/outcomes — code path (numeric observed value required)
- [x] **H4** Uncertainty explicit; "I don't know" is a valid answer — belief module + JUDGE-QA
- [x] **H5** No usage how-to instructions in the dapp UI — VERIFIED (grep clean)
- [x] **H6** No secrets in git history — VERIFIED (0)

## I. Fresh-clone cloneability (Reality Checker gate) — ALL VERIFIED

- [x] **I1** `git clone` works
- [x] **I2** Backend `uv venv && uv pip install -e .` works from fresh clone
- [x] **I3** Tests pass from fresh clone (16/16)
- [x] **I4** Demo runs from fresh clone (CLEARED verdict ×3)
- [x] **I5** Frontend `npm install && npm run build` works from fresh clone
- [x] **I6** No committed junk (`node_modules`, `dist`, `.venv`, `.env*`, `data/`)
- [x] **I7** README quickstart starts with the clone command

## J. Submission package

- [x] **J1** README final (spec + proof + honesty table)
- [ ] **J2** Demo video (1.5–2 min) — scripts ready (RUNOFSHOW/DEMO); recording PENDING (user)
- [ ] **J3** Screenshot pack (desktop + mobile) — PENDING
- [x] **J4** One winning-theme line woven through docs — present
- [x] **J5** Judge Q&A prep written (docs/JUDGE-QA.md) — VERIFIED
- [ ] **J6** Repo description + topics set — PENDING (one `gh repo edit` when ready)

---

## Remaining to hit 100% (blocked on user / final push)

1. **A2/D2** — run the live Minds surface: set `MIND_ID` + `MINDS_BUILDER_API_KEY` env and
   verify `/api/mind` returns the live Mind (user supplies env).
2. **A5/G5/J2** — the 1.5–2 min demo video (scripts written; record from real run output).
3. **J3** — screenshot pack of the live app.
4. **A6/J6** — make repo public + set description/topics at submission time (user's call).

Everything else is done and verified.