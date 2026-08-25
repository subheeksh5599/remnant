"""
REMNANT — belief reconstruction.

The money-shot's second half: after a reload / fresh session, the Mind must be
able to answer "what do you currently believe about this need?" and REPLAY THE
FULL CHAIN — historical evidence, current evidence, competing hypotheses, the
experiment (pre-registered threshold), the observed number, the verdict, and the
updated belief. Not a summary; the chain, with the numbers.
"""

from __future__ import annotations

from .models import Remnant


def answer_questions(r: Remnant) -> dict:
    """The six 'Ask the Mind' questions, answered deterministically from the
    persisted chain. Every answer cites evidence; none invents certainty."""
    h1 = next((a for a in r.assessments if a.hypothesis.value == "H1"), None)
    completed = [e for e in r.experiments if e.status == "completed"]
    state = r.resolution_state.value

    def _belief_line() -> str:
        return current_belief(r)

    def _why() -> str:
        n_hist = sum(1 for e in r.expressions if e.occurred_at.year <= 2023)
        n_cur = sum(1 for e in r.expressions if e.occurred_at.year >= 2024)
        parts = [
            f"{len(r.expressions)} audience expressions recorded "
            f"({n_hist} historical, {n_cur} current) across {len({e.source.kind for e in r.expressions})} source types",
        ]
        if completed:
            last = completed[-1]
            parts.append(
                f"last experiment observed {last.observed_value} vs pre-registered "
                f"{last.threshold_value} ({last.threshold_operator}) -> {last.outcome}"
            )
        if h1 is not None:
            parts.append(
                f"H1 (persistent unresolved need) currently holds {h1.evidence_strength.value} evidence "
                f"({len(h1.supporting_evidence)} supporting, {len(h1.contradicting_evidence)} conflicting items)"
            )
        return "; ".join(parts)

    def _evidence() -> str:
        lines = []
        for e in r.expressions[-4:]:
            lines.append(f"  - {e.occurred_at.date().isoformat()} [{e.source.kind}] \"{e.text[:90]}\"")
        return "\n".join(lines) if lines else "  - none recorded yet"

    def _contradicts() -> str:
        conflicts = []
        if h1 is not None:
            conflicts += h1.contradicting_evidence
        creator_rejected = [d for d in r.creator_decisions if d.decision == "rejected"]
        if creator_rejected:
            conflicts.append(f"creator explicitly rejected this need: {creator_rejected[-1].reason or 'no reason given'}")
        return "\n".join(f"  - {c}" for c in conflicts) if conflicts else "  - none on record — uncertainty is preserved, not hidden"

    def _next_test() -> str:
        if r.resolution_state.value in ("fulfilled", "rejected", "disproven"):
            return "No test recommended: the need is resolved/closed on the record."
        if completed and completed[-1].crossed_threshold is not None:
            last = completed[-1]
            return (
                f"Recommended: a follow-up probe on the same metric "
                f"({last.metric}, threshold {last.threshold_value} {last.threshold_operator}) "
                f"to confirm the observed signal is stable, or a variant targeting a different segment."
            )
        return "Recommended: plan the smallest pre-registered probe (concrete metric + threshold) and record the observed number."

    def _changed() -> str:
        recent = r.history[-3:]
        return "\n".join(f"  - {h}" for h in recent) if recent else "  - nothing yet"

    return {
        "what_do_you_currently_believe": _belief_line(),
        "why": _why(),
        "what_evidence_supports_this": _evidence(),
        "what_contradicts_it": _contradicts(),
        "what_should_we_test_next": _next_test(),
        "what_changed_since_the_last_experiment": _changed(),
        "resolution_state": state,
    }


def current_belief(remnant: Remnant) -> str:
    """Reconstruct the Mind's current belief with its full evidence chain."""
    if not remnant.expressions:
        return "No evidence has been recorded for this need yet. I don't have a belief."

    lines: list[str] = []

    # 1. Historical evidence
    hist = [e for e in remnant.expressions if e.occurred_at.year <= 2023]
    cur = [e for e in remnant.expressions if e.occurred_at.year >= 2024]
    lines.append(f"Need under consideration: {remnant.title!r}")
    lines.append(f"Hypothesis: {remnant.underlying_need_hypothesis}")
    lines.append("")
    lines.append("PRE-EXPERIMENT EVIDENCE:")
    lines.append(f"  historical expressions ({len(hist)}):")
    for e in hist:
        lines.append(f"    {e.occurred_at.date().isoformat()}  \"{e.text}\"  [{e.source.kind}]")
    lines.append(f"  current expressions ({len(cur)}):")
    for e in cur:
        lines.append(f"    {e.occurred_at.date().isoformat()}  \"{e.text}\"  [{e.source.kind}]")
    lines.append("")

    # 2. Competing hypotheses with current evidence strength
    lines.append("COMPETING EXPLANATIONS (held simultaneously):")
    for a in remnant.assessments:
        lines.append(
            f"  {a.hypothesis.value} [{a.evidence_strength.value}]: {a.summary}"
        )

    # 3. Experiment: pre-registered threshold vs observed number
    lines.append("")
    completed = [e for e in remnant.experiments if e.status == "completed"]
    if completed:
        lines.append("EXPERIMENT (pre-registered, then observed):")
        for e in completed:
            lines.append(f"  test: {e.test}")
            lines.append(f"  metric: {e.metric}")
            lines.append(
                f"  pre-registered threshold: {e.threshold_value:.3f} ({e.threshold_operator})"
            )
            lines.append(
                f"  observed value: {e.observed_value:.3f}"
                if e.observed_value is not None
                else "  observed value: pending"
            )
            lines.append(f"  verdict: {e.outcome}")
    elif remnant.experiments:
        lines.append("")
        lines.append("EXPERIMENT (planned, not yet run):")
        e = remnant.experiments[-1]
        lines.append(f"  test: {e.test}")
        lines.append(f"  metric: {e.metric}")
        lines.append(f"  pre-registered threshold: {e.threshold_value:.3f} ({e.threshold_operator})")
    else:
        lines.append("")
        lines.append("NO EXPERIMENT YET: the smallest pre-registered probe has not been run.")

    # 4. Current belief statement
    lines.append("")
    lines.append("CURRENT BELIEF:")
    h1 = next((a for a in remnant.assessments if a.hypothesis.value == "H1"), None)
    if h1 is None:
        lines.append("  (no hypothesis accounting available)")
    else:
        strength = h1.evidence_strength.value
        last_obs = completed[-1] if completed else None
        if remnant.resolution_state.value == "revisited" and strength == "high" and last_obs is not None:
            lines.append(
                "  The evidence supports revisiting this need. The pre-registered probe "
                f"cleared its threshold (observed {last_obs.observed_value:.3f} >= "
                f"{last_obs.threshold_value:.3f}), so H1 (persistent need) gained "
                "support. This is still a belief, not a fact — H2 (a new cohort) remains "
                "plausible until more evidence disambiguates it."
            )
        elif remnant.resolution_state.value == "disproven" and last_obs is not None:
            lines.append(
                "  The current evidence does not support acting on this need. The probe "
                f"observed {last_obs.observed_value:.3f}, below the pre-registered "
                "failure band; H1 lost support. The need is preserved in memory as "
                "dormant, not deleted — conditions can change."
            )
        elif remnant.resolution_state.value == "uncertain" and last_obs is not None:
            lines.append(
                "  Evidence is inconclusive. The probe observed "
                f"{last_obs.observed_value:.3f}, within the ambiguous band between "
                "failure and success. I recommend one follow-up probe, not a full build."
            )
        else:
            lines.append(
                f"  State: {remnant.resolution_state.value} (H1 evidence: {strength}). "
                "No experiment has yet decided this need."
            )

    # 5. Honest uncertainty
    lines.append("")
    lines.append(
        "UNCERTAINTY: continuity is inferred, never asserted. H1 vs H2 can only be "
        "separated by the observed outcome of a pre-registered experiment, and that "
        "verdict is a belief update, not proof."
    )
    return "\n".join(lines)