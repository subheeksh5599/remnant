"""
REMNANT — experiment planner and belief update.

The Mind chooses the SMALLEST experiment that maximises information gain while
minimising creator effort and audience risk. It must never change the success/
failure criteria after observing the result. Belief updates happen only from
real observed outcomes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from .models import (EvidenceStrength, Experiment, Hypothesis, Remnant,
                     ResolutionState)


def plan_experiment(
    remnant: Remnant,
    hypothesis: Hypothesis = Hypothesis.H1,
) -> Experiment:
    """Design a low-cost validation experiment for a candidate need."""
    if not remnant.expressions:
        raise ValueError("cannot plan an experiment with no expressions")

    test = (
        f"Publish a short explainer / probe addressing: '{remnant.underlying_need_hypothesis}' "
        f"to the relevant audience segment, and measure engagement."
    )
    return Experiment(
        remnant_id=remnant.remnant_id,
        hypothesis=hypothesis,
        test=test,
        prediction="Moderate response expected if the need is currently active.",
        success_threshold="Response above baseline on the target audience segment.",
        failure_condition="Response at or below baseline; evidence does not support acting now.",
    )


def apply_observed_outcome(
    remnant: Remnant,
    experiment: Experiment,
    observed: str,
) -> None:
    """Record an honest outcome and update the remnant's state and belief.

    This is the "learn from what actually happened" step. Only real observations
    update beliefs — never a prediction pretending to be a fact.
    """
    experiment.status = "completed"
    experiment.observed = observed
    experiment.outcome = observed
    experiment.decided_at = datetime.now(timezone.utc)

    # Update resolution state based on real outcome.
    lo = observed.lower()
    if any(k in lo for k in ("high", "strong", "positive", "above baseline")):
        if remnant.resolution_state in (ResolutionState.UNRESOLVED, ResolutionState.DORMANT,
                                        ResolutionState.UNCERTAIN, ResolutionState.UNDER_EXPERIMENT):
            remnant.resolution_state = ResolutionState.REVISITED
        # evidence for H1 strengthened
        for a in remnant.assessments:
            if a.hypothesis.value == "H1":
                a.evidence_strength = EvidenceStrength.HIGH
                a.supporting_evidence.append(f"experiment {experiment.experiment_id}: {observed}")
    elif any(k in lo for k in ("low", "below baseline", "weak", "negative")):
        if remnant.resolution_state in (ResolutionState.REVISITED, ResolutionState.UNCERTAIN,
                                        ResolutionState.UNDER_EXPERIMENT):
            remnant.resolution_state = ResolutionState.DISPROVEN
        for a in remnant.assessments:
            if a.hypothesis.value == "H1":
                a.contradicting_evidence.append(f"experiment {experiment.experiment_id}: {observed}")
                a.evidence_strength = EvidenceStrength.LOW

    remnant.history.append(
        f"experiment {experiment.experiment_id} -> observed: {observed}"
    )
