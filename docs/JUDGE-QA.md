# REMNANT — Judge Q&A prep

Written answers to the questions a probing judge is most likely to ask. Every
answer is honest, grounded in the code, and never overclaims. If an answer starts
with "I don't know" that is the correct answer — this product's credibility IS
its uncertainty handling.

---

## 1. "Isn't this just clustering comments / a sentiment tool?"

No. The primitive is a **time-aware hypothesis** about an unresolved need. A
clustering tool groups text; it does not:
- preserve the *creator's response* (or silence) as part of the record,
- maintain four **competing explanations** (H1 persistent need / H2 new cohort /
  H3 trend / H4 coincidence) with evidence for AND against each,
- plan a **pre-registered, numeric experiment** and update belief only from the
  observed number crossing the threshold.

Clustering answers "what did people write?" REMNANT answers "what need might still
be unresolved, which explanation is most supported, and what's the cheapest way to
know more?" Those are different jobs.

## 2. "How do you know it's the same demand returning?"

I don't — and the product says so. The demo's strongest line is: *"We cannot
reliably distinguish H1 (persistent need) from H2 (new cohort) yet."* That
ambiguity is a **feature**, not a weakness. The experiment exists precisely to
disambiguate, and even after a CLEARED verdict the belief text still says:
"This is a belief, not a fact."

## 3. "The 0.067 observed value — is that real data?"

Honest answer: in the demo run it comes from the **clearly-labeled synthetic
demonstration corpus** (labeled `SYNTHETIC DEMONSTRATION CORPUS` in the script
output and everywhere it appears). The real product path ingests a **real measured
number** (creator-provided / real public data) with full provenance. We never
present synthetic data as real — the label is mandatory in this repo.

## 4. "Why not just search old comments / a feature-request board?"

Three reasons:
1. **Demand that disappears is not demand that died.** Search only finds what's
   still visible; REMNANT preserves the *unresolved state* even when no one is
   asking.
2. **Language changes.** "Can you make a beginner ZK tutorial?" (2022) and
   "How do I start building with zero knowledge?" (2026) share almost no keywords,
   yet may be the same underlying need. Token overlap is explicitly NOT treated as
   continuity (adversarial guard: `How do I learn ZK?` vs `ZK badge is broken`
   never auto-merge).
3. **A feature-request board tells you what people asked; REMNANT tells you what
   to test next**, and only when the evidence justifies it — including the
   credible "DON'T ACT" conclusion.

## 5. "Aren't you just calling a database 'the Mind'?"

The local store is a durable backing so state survives restart. The **conceptual
center is the persistent Minds agent**: the long-term interpretation, hypothesis
continuity, experiment decisions, autonomous follow-up, and cumulative reasoning
are the Mind's job (backend/remnant/minds.py drives the Minds Builder surface).
`docs/architecture.md` states the honest split — the store is the durable
backing, the Mind is the steward.

## 6. "What does REMNANT do that an LLM with a prompt can't?"

An LLM with a prompt doesn't:
- keep a **pre-registered numeric threshold** that cannot be moved after observing
  (the experiment module rejects a second outcome recording),
- maintain **evidence accounting** per hypothesis (support/contradict lists that
  are inspectable, not hidden in prose),
- produce a **deterministic crossing verdict** (`0.067 >= 0.040 -> CLEARED`) that
  is the same every time,
- **remember across sessions** with a fresh store handle replaying the full chain.

The LLM writes the reasoning; the deterministic core owns the accounting. That
split is what makes claims checkable.

## 7. "Where's the actual autonomous follow-up?"

The Mind Activity log + the autonomous detection path. REMNANT's loop is: review
dormant remnants → compare current evidence → detect possible continuity → check
creator response history → determine unresolved → recommend a pre-registered
experiment. It does not wait to be asked "what are people asking for?" — the
demo shows it proactively surfacing the need and proposing the experiment.

## 8. "Why should I trust the beliefs?"

Because the product is designed to be **probable**:
- evidence strength is qualitative (low/medium/high), never a fake "91%",
- contradicting evidence is surfaced, never suppressed,
- "I don't know" and "evidence is inconclusive" are valid outputs,
- every verdict is deterministic and reproducible,
- provenance is retained through the entire lifecycle (tested).

## 9. "What would you do with real data?"

Ingest a real community export (real comments / Discord / GitHub with timestamps),
run the same pipeline, and every number gets a real source link. The pipeline is
data-agnostic; the labels change from SYNTHETIC to real provenance.

## 10. "Is this a hackathon toy, or does it scale?"

The primitive — unresolved-need hypothesis + competing explanations + experiment —
scales from a single creator's comments to communities, open-source projects,
education, and eventual "persistent digital institution" memory. The hackathon
build is one flawless vertical slice of that. Viability is the mechanism, not the
feature count.