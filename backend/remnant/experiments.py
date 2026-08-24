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

from .models import (EvidenceStrength, Experiment, Hypothesis, Remnant,
                     ResolutionState)


def plan_experiment(
    remnant: Remnant,
    hypothesis: Hypothesis = Hypothesis.H1,
) -> Experiment:
    """Design a concrete, pre-registered, numeric validation experiment.

    'Concrete' means: a named deliverable, an exact measurement, a pre-registered
    numeric threshold. The creator must be able to run it and read one number.
    """
    if not remnant.expressions:
        raise ValueError("cannot plan an experiment with no expressions")

    # The smallest provable slice: one 90-second explainer addressing the need,
    # published to the relevant segment. The metric is the 48h comment-to-view
    # ratio (comments/views) — a number, not a feeling.
    #
    # Threshold rationale (pre-registered, not tuned after the fact):
    #   >= 0.04 (4%)      -> need is currently active (H1 gains support)
    #   <  0.02 (2%)      -> evidence does not support acting now
    #   in between        -> inconclusive; run a follow-up probe
    test = (
        "Publish one 90-second explainer ('{need}') to the beginner/curious "
        "segment on the creator's main channel, using the request's own framing."
    ).format(need=remnant.underlying_need_hypothesis)
    metric = "comment-to-view ratio (comments / views, measured 48h after publish)"
    prediction = (
        "If the need is currently active, the explainer clears the pre-registered "
        "threshold of 0.04 comments/view; if dormant, it stays below 0.02."
    )

    return Experiment(
        remnant_id=remnant.remnant_id,
        hypothesis=hypothesis,
        test=test,
        metric=metric,
        threshold_value=0.04,  # PRE-REGISTERED, never adjusted after observing
        threshold_operator="gte",
        prediction=prediction,
        success_threshold="observed comment-to-view ratio >= 0.04 (4%)",
        failure_condition="observed ratio < 0.02 (2%); do not act on the need now",
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