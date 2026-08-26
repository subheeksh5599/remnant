"""
REMNANT — experiment planner and belief update.

The Mind chooses the SMALLEST experiment that maximises information gain while
minimising creator effort and audience risk. Success/failure thresholds are
PRE-REGISTERED before any observation. Beliefs update ONLY from a numeric
observed value crossing (or failing) the pre-registered threshold — never from
a vibe word. There is no post-hoc threshold moving.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from .models import (EvidenceStrength, Experiment, Hypothesis, Remnant,
                     ResolutionState)


def plan_experiment(
    remnant: Remnant,
    hypothesis: Hypothesis = Hypothesis.H1,
    metric: Optional[str] = None,
    threshold: Optional[float] = None,
    target_population: Optional[str] = None,
    measurement_window: Optional[str] = None,
) -> Experiment:
    """Design a concrete, pre-registered, numeric validation experiment.

    Autonomous by default. P2: the creator may OVERRIDE any of metric, threshold,
    target population, or measurement window — the override is recorded on the
    experiment (defined_by_creator=True) so nobody mistakes it for the default.
    'Concrete' means: a named deliverable, an exact measurement, a pre-registered
    numeric threshold. The creator must be able to run it and read one number.
    """
    if not remnant.expressions:
        raise ValueError("cannot plan an experiment with no expressions")

    defined_by_creator = any(
        v is not None for v in (metric, threshold, target_population, measurement_window)
    )

    # Defaults (autonomous planner). Threshold rationale (pre-registered, never
    # tuned after the fact):
    #   >= 0.04 (4%)      -> need is currently active (H1 gains support)
    #   <  0.02 (2%)      -> evidence does not support acting now
    #   in between        -> inconclusive; run a follow-up probe
    segment = target_population or "beginner/curious segment"
    window = measurement_window or "48h"
    test = (
        "Publish one 90-second explainer ('{need}') to the {segment} on the "
        "creator's main channel, using the request's own framing."
    ).format(need=remnant.underlying_need_hypothesis, segment=segment)
    metric_final = metric or f"comment-to-view ratio (comments / views, measured {window} after publish)"
    threshold_final = 0.04 if threshold is None else threshold
    prediction = (
        f"If the need is currently active, the explainer clears the pre-registered "
        f"threshold of {threshold_final} comments/view; if dormant, it stays below "
        f"{threshold_final / 2:.2f}."
    )

    return Experiment(
        remnant_id=remnant.remnant_id,
        hypothesis=hypothesis,
        test=test,
        metric=metric_final,
        threshold_value=threshold_final,  # PRE-REGISTERED, never adjusted after observing
        threshold_operator="gte",
        prediction=prediction,
        success_threshold=f"observed metric >= {threshold_final}",
        failure_condition=f"observed metric < {threshold_final / 2:.2f}; do not act on the need now",
        target_population=segment,
        measurement_window=window,
        defined_by_creator=defined_by_creator,
    )


def crossing_verdict(exp: Experiment, observed_value: float) -> bool:
    """Deterministic verdict: does the observed number cross the pre-registered
    threshold? gte -> observed >= threshold. lte -> observed <= threshold."""
    if exp.threshold_operator == "gte":
        return observed_value >= exp.threshold_value
    return observed_value <= exp.threshold_value


def apply_observed_outcome(
    remnant: Remnant,
    experiment: Experiment,
    observed_value: float,
) -> None:
    """Record the numeric outcome and update beliefs FROM THE NUMBER.

    The observed value is a real measurement (or, in the labeled demo corpus, a
    demo number). The verdict is computed against the pre-registered threshold —
    never keyword-matched, never a vibe word.
    """
    if experiment.status == "completed":
        raise ValueError("experiment already completed; outcomes are recorded once")

    # The remnant must own the experiment in its persistent list.
    if not any(e.experiment_id == experiment.experiment_id for e in remnant.experiments):
        remnant.experiments.append(experiment)

    experiment.status = "completed"
    experiment.observed_value = observed_value
    experiment.crossed_threshold = crossing_verdict(experiment, observed_value)
    experiment.decided_at = datetime.now(timezone.utc)

    verdict = "CLEARED" if experiment.crossed_threshold else "FAILED"
    exp_note = (
        f"observed {observed_value:.3f} {'>=' if experiment.threshold_operator == 'gte' else '<='} "
        f"pre-registered {experiment.threshold_value:.3f} -> {verdict}"
    )
    experiment.outcome = exp_note

    # Belief update, driven by the number + verdict, with the 2%-4% inconclusive band.
    from .models import ResolutionState as RS

    if experiment.crossed_threshold:
        if remnant.resolution_state in (
            RS.UNRESOLVED,
            RS.DORMANT,
            RS.UNCERTAIN,
            RS.UNDER_EXPERIMENT,
        ):
            remnant.transition_to(RS.REVISITED, f"experiment {experiment.experiment_id} CLEARED threshold")
        for a in remnant.assessments:
            if a.hypothesis.value == "H1":
                a.evidence_strength = EvidenceStrength.HIGH
                a.supporting_evidence.append(f"experiment {experiment.experiment_id}: {exp_note}")
    elif observed_value < 0.02:
        # Clear failure: the need is not currently active. Any pre-experiment state
        # (unresolved/dormant/uncertain/under-experiment/revisited) gives way.
        if remnant.resolution_state in (
            RS.UNRESOLVED,
            RS.DORMANT,
            RS.UNCERTAIN,
            RS.UNDER_EXPERIMENT,
            RS.REVISITED,
        ):
            remnant.transition_to(RS.DISPROVEN, f"experiment {experiment.experiment_id} below failure band")
        for a in remnant.assessments:
            if a.hypothesis.value == "H1":
                a.contradicting_evidence.append(f"experiment {experiment.experiment_id}: {exp_note}")
                a.evidence_strength = EvidenceStrength.LOW
    else:
        # Inconclusive band (0.02-0.04): hold beliefs, recommend a follow-up probe.
        if remnant.resolution_state in (
            RS.UNRESOLVED,
            RS.DORMANT,
            RS.UNDER_EXPERIMENT,
        ):
            remnant.transition_to(RS.UNCERTAIN, f"experiment {experiment.experiment_id} inconclusive band")
        for a in remnant.assessments:
            if a.hypothesis.value == "H1":
                a.supporting_evidence.append(
                    f"experiment {experiment.experiment_id}: inconclusive ({exp_note})"
                )

    remnant.history.append(
        f"experiment {experiment.experiment_id}: {exp_note}"
    )