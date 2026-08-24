# REMNANT — Production Checklist (to submission)

Every item is ticked ONLY when truly done AND verified against a live artifact.
A tick is evidence, never a plan.

**Product:** REMNANT — a persistent Minds agent that remembers unresolved audience
needs across time, preserves uncertainty (H1–H4), and runs pre-registered experiments
to decide what deserves creator attention now.
**Event:** Creative Minds Jam #1 (Minds by Animoca Brands). **Track 1** (retain/grow
the audience via forgotten need; Track 3 resonance).
**Repo:** github.com/subheeksh5599/remnant (private).

---

## A. Hard submission requirements (disqualifiers — ALL must be present)

- [ ] **A1** Working product, runnable from a fresh clone (backend + frontend + demo)
- [ ] **A2** Minds agent integral to core operation — removing it breaks the product
- [ ] **A3** Persistence demonstrated: memory AND continuity AND autonomous follow-up
- [ ] **A4** Declared track fit (Track 1) stated in the README
- [ ] **A5** Demo video 1.5–2.0 min (timed, not estimated)
- [ ] **A6** Public/accessible code repository with technical documentation
- [ ] **A7** Submitted before deadline (user handles timing)

## B. Judging criteria (score targets)

- [ ] **B1** Minds Integration Depth 10 — persistence/continuity/autonomy load-bearing
- [ ] **B2** Creator-Economy Problem Fit 10 — named creator pain, real loss
- [ ] **B3** Innovation 10 — no certainty claims; decision-under-uncertainty engine
- [ ] **B4** Execution 10 — one undeniable end-to-end slice, demo-ready
- [ ] **B5** Viability 10 — buyer + wedge + expansion path stated

## C. Core loop (the money-shot — MUST be verified live)

- [ ] **C1** Ingest real expression(s) with provenance (source, timestamp)
- [ ] **C2** Create REMNANT (time-aware hypothesis, not a note)
- [ ] **C3** Hold competing explanations H1–H4 with evidence strength
- [ ] **C4** Adversarial token guard: shared token ≠ continuity
- [ ] **C5** Plan smallest PRE-REGISTERED experiment (metric + numeric threshold set
      before observing; never moved after)
- [ ] **C6** Record a numeric observed value (not a vibe word)
- [ ] **C7** Deterministic crossing verdict vs pre-registered threshold
- [ ] **C8** Belief update driven by the number (support/contradict/inconclusive)
- [ ] **C9** Persistence: fresh session/store still knows the full chain
- [ ] **C10** "What do you currently believe?" replays the FULL chain with numbers
- [ ] **C11** Anti-confirmation-bias: contradicting evidence surfaced, never suppressed
- [ ] **C12** The Mind may conclude DON'T ACT (disproven state) — credible, not eager

## D. Minds integration (B1 — the #1 criterion)

- [ ] **D1** Minds client reads the living Mind (state, cognition) from env
- [ ] **D2** Mind concept = steward of community memory, not a DB relabeled "AI"
- [ ] **D3** Autonomy visible: proactive review/detection path in the UI/log
- [ ] **D4** Remove-the-Mind statement in README ("what breaks if Minds is removed")

## E. Backend production (finisher skill §ENGINEERING)

- [ ] **E1** 16+ tests passing (inference, experiment, belief, persistence, adversarial)
- [ ] **E2** Health endpoint (`/api/health`) proves backend + store + mind reachable
- [ ] **E3** Fail-fast env validation (missing MIND_ID/KEY = clear error, not silent)
- [ ] **E4** Idempotent outcome recording (second observation rejected)
- [ ] **E5** Input validation (decisions whitelist, numeric outcome)
- [ ] **E6** 404/422 error states on API
- [ ] **E7** Store: durable, survives restart, no committed runtime data
- [ ] **E8** Secrets never in repo/history/bundle (env-only)

## F. Frontend production

- [ ] **F1** TypeScript clean, production build passes
- [ ] **F2** Screens: Remnants / detail (timeline, expressions, hypotheses, provenance,
      experiment, belief) / register
- [ ] **F3** Empty states, loading state, error handling (API down)
- [ ] **F4** Honest-uncertainty note visible in detail view
- [ ] **F5** Numeric experiment UI: metric, pre-registered threshold, observed value,
      crossing verdict, belief panel
- [ ] **F6** Proxy to backend in dev

## G. Enoch finish discipline

- [ ] **G1** README = spec, accurate to code + live behavior
- [ ] **G2** Honesty table (Real — tested / Real not-live / Synthetic-labeled / Pending)
- [ ] **G3** "Proof — nothing here is a mockup" section with live links/commands
- [ ] **G4** demo script (docs/RUNOFSHOW.md, timed beats, pre-flight, backup ladder of
      REAL artifacts, anticipated judge questions with answers)
- [ ] **G5** Demo video: programmatic/generated from REAL output where possible, else
      scripted live recording — never improvised; 1.5–2 min
- [ ] **G6** Clean git history (conventional commits, no secrets, no runtime junk)

## H. Anti-slop / no-fake rules (absolute, user-enforced)

- [ ] **H1** `grep -rniE "mock|simul|sample|fake|dummy|hardcod|placeholder"` clean in
      shipped code (allowed: explicitly-labeled synthetic demo corpus in scripts/)
- [ ] **H2** Synthetic data labeled SYNTHETIC DEMONSTRATION CORPUS everywhere it appears
- [ ] **H3** No fabricated evidence/audience numbers/outcomes
- [ ] **H4** Uncertainty explicit; "I don't know" is a valid answer
- [ ] **H5** No usage how-to instructions in the dapp UI (`grep -rni "how to|step 1"`)
- [ ] **H6** No secrets in git history (`git log --all -p | grep -c <key>` == 0)

## I. Fresh-clone cloneability (Reality Checker gate)

- [ ] **I1** `git clone <repo> /tmp/xxx` — clone works
- [ ] **I2** Backend: `uv venv && uv pip install -e ".[dev]"` — works
- [ ] **I3** Tests: `python -m pytest tests/ -q` — all pass from fresh clone
- [ ] **I4** Demo: `python -m scripts.demo` — runs end-to-end
- [ ] **I5** Frontend: `npm install && npm run build` — builds
- [ ] **I6** No committed junk (`node_modules`, `dist`, `.venv`, `.env*`, `data/`)
- [ ] **I7** README quickstart starts with the clone command

## J. Submission package

- [ ] **J1** README final (spec + proof + honesty table)
- [ ] **J2** Demo video (1.5–2 min) + short fallback (docs/DEMO.md)
- [ ] **J3** Screenshot pack (desktop + mobile) of live app
- [ ] **J4** One winning-theme line woven through submission text
- [ ] **J5** Judge Q&A prep written (docs/JUDGE-QA.md)
- [ ] **J6** Repo description + topics set