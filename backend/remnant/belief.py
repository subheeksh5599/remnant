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