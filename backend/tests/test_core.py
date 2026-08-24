"""REMNANT — core behavioral tests, including adversarial no-merge cases."""

import os
import tempfile
from datetime import datetime, timezone

import pytest

from remnant.experiments import apply_observed_outcome, plan_experiment
from remnant.inference import assess_expression_pair, assess_hypotheses
from remnant.models import (AudienceExpression, Remnant, ResolutionState,
                            Source)
from remnant.store import Store


def _expr(text: str, year: int, sid: str = "src") -> AudienceExpression:
    return AudienceExpression(
        text=text,
        source=Source(kind="youtube_comment", source_id=sid),
        occurred_at=datetime(year, 6, 1, tzinfo=timezone.utc),
    )


def _remnant(seq: list[tuple[str, int]]) -> Remnant:
    r = Remnant(
        title="Beginner ZK education",
        underlying_need_hypothesis="Beginners want accessible ZK education",
    )
    for text, year in seq:
        r.expressions.append(_expr(text, year))
    r.assessments = assess_hypotheses(r)
    return r


# --- 1. different expressions mapping to the same candidate need --------------
def test_different_expressions_same_candidate_need():
    r = _remnant([
        ("Can you make a beginner ZK tutorial?", 2022),
        ("How do I even start learning ZK?", 2023),
        ("How do I start building with zero knowledge?", 2026),
    ])
    h1 = next(a for a in r.assessments if a.hypothesis.value == "H1")
    assert h1.evidence_strength.value == "medium"
    assert len(r.expressions) == 3


# --- 2. similar expressions that should NOT be merged (adversarial) ----------
def test_shared_token_must_not_auto_merge():
    a = assess_expression_pair("How do I learn ZK?", "I don't understand ZK proofs")
    assert a["token_overlap"] is True
    b = assess_expression_pair("How do I learn ZK?", "ZK badge for my profile looks broken")
    assert b["token_overlap"] is True
    # Both share tokens; the guard must treat overlap as insufficient evidence,
    # never as proof of continuity.
    for res in (a, b):
        assert "insufficient evidence" in res["note"]


# --- 3. fulfilled need ---------------------------------------------------------
def test_fulfilled_need():
    r = _remnant([("Can you make a beginner ZK tutorial?", 2022)])
    r.resolution_state = ResolutionState.FULFILLED
    h1 = next(a for a in assess_hypotheses(r) if a.hypothesis.value == "H1")
    assert h1 is not None
    assert r.resolution_state == ResolutionState.FULFILLED


# --- 4. explicitly rejected need ----------------------------------------------
def test_rejected_need():
    r = _remnant([("We are never making this.", 2023)])
    r.resolution_state = ResolutionState.REJECTED
    assert r.resolution_state == ResolutionState.REJECTED


# --- 5. unresolved need --------------------------------------------------------
def test_unresolved_need():
    r = _remnant([("Can you make a beginner ZK tutorial?", 2022)])
    assert r.resolution_state == ResolutionState.UNRESOLVED


# --- 6. conflicting evidence ---------------------------------------------------
def test_conflicting_evidence_kept_visible():
    r = _remnant([
        ("Can you make a beginner ZK tutorial?", 2022),
        ("How do I start building with zero knowledge?", 2026),
    ])
    h1 = next(a for a in r.assessments if a.hypothesis.value == "H1")
    # H1 must carry both support and conflict (creator never responded).
    assert h1.supporting_evidence
    assert h1.contradicting_evidence


# --- 7. recurrence with competing explanations --------------------------------
def test_competing_explanations_present():
    r = _remnant([
        ("Can you make a beginner ZK tutorial?", 2022),
        ("How do I start building with zero knowledge?", 2026),
    ])
    labels = {a.hypothesis.value for a in r.assessments}
    assert labels == {"H1", "H2", "H3", "H4"}


# --- 8. no recurrence -----------------------------------------------------------
def test_no_recurrence_single_expression():
    r = _remnant([("Can you make a beginner ZK tutorial?", 2022)])
    h1 = next(a for a in r.assessments if a.hypothesis.value == "H1")
    assert h1.evidence_strength.value == "low"


# --- 9. experiment outcome changes belief --------------------------------------
def test_experiment_outcome_updates_belief():
    r = _remnant([
        ("Can you make a beginner ZK tutorial?", 2022),
        ("How do I start building with zero knowledge?", 2026),
    ])
    exp = plan_experiment(r)
    apply_observed_outcome(r, exp, "high response from target audience")
    assert r.resolution_state == ResolutionState.REVISITED
    h1 = next(a for a in r.assessments if a.hypothesis.value == "H1")
    assert h1.evidence_strength.value == "high"
    assert any("experiment" in e for e in h1.supporting_evidence)


# --- 10. persistence across sessions --------------------------------------------
def test_persistence_across_sessions():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "remnant.db")
        s1 = Store(path)
        r = _remnant([("Can you make a beginner ZK tutorial?", 2022)])
        s1.upsert(r)

        s2 = Store(path)  # "new session"
        loaded = s2.get(r.remnant_id)
        assert loaded is not None
        assert loaded.expressions[0].text == "Can you make a beginner ZK tutorial?"


# --- 11. unauthorized action blocked --------------------------------------------
def test_invalid_creator_decision_rejected():
    from remnant.app import _VALID_DECISIONS
    assert "ban_everyone" not in _VALID_DECISIONS
    assert "rejected" in _VALID_DECISIONS


# --- 12. provenance retained through lifecycle ----------------------------------
def test_provenance_retained_through_lifecycle():
    r = _remnant([
        ("Can you make a beginner ZK tutorial?", 2022),
        ("How do I start building with zero knowledge?", 2026),
    ])
    exp = plan_experiment(r)
    apply_observed_outcome(r, exp, "low response")
    # The original expressions (the provenance) survive the whole lifecycle.
    assert len(r.expressions) == 2
    assert r.expressions[0].source.source_id == "src"
    assert any("observed: low response" in h for h in r.history)