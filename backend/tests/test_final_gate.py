"""
REMNANT — final P1 verification matrix (the acceptance suite).

Covers every item on the pre-submission checklist that has a deterministic
answer, including the adversarial pairs, all three verdict paths, immutability,
duplicate rejection, creator overrides, invalid transitions, and Minds-failure.
"""

import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from remnant.app import app
from remnant.experiments import apply_observed_outcome, plan_experiment
from remnant.inference import analyze_relationship
from remnant.models import (AudienceExpression, Remnant, ResolutionState,
                            Source)
from remnant.store import Store
from datetime import datetime, timezone


@pytest.fixture()
def durable_store():
    with tempfile.TemporaryDirectory() as d:
        yield Store(os.path.join(d, "t.db"))


def _remnant(state: ResolutionState = ResolutionState.CANDIDATE, n_expr: int = 3) -> Remnant:
    r = Remnant(title="Need", underlying_need_hypothesis="need text")
    for i in range(n_expr):
        r.expressions.append(AudienceExpression(
            text=f"expression {i}", source=Source(kind="yt", source_id=str(i)),
            occurred_at=datetime(2022 + i, 1, 1, tzinfo=timezone.utc)))
    from remnant.inference import assess_hypotheses
    r.assessments = assess_hypotheses(r)
    r.resolution_state = state
    return r


# --- adversarial matrix (P1) ----------------------------------------------------

def test_same_need_different_words():
    r = analyze_relationship("Can you make a beginner ZK tutorial?", "How do I start building with zero knowledge?")
    assert r["relationship"] == "candidate"
    assert "zero_knowledge" in r["shared_concepts"]


def test_similar_but_different():
    r = analyze_relationship("How do I learn ZK?", "ZK badge for my profile looks broken")
    assert r["relationship"] == "different_need"
    assert r["confidence"] == "high"


def test_insufficient_evidence_path():
    r = analyze_relationship("Merch restock when?", "Add dark mode to the dashboard?")
    assert r["relationship"] == "insufficient_evidence"


# --- verdict paths (P1) ----------------------------------------------------------

def _run(remnant, value):
    e = plan_experiment(remnant)
    remnant.experiments.append(e)
    apply_observed_outcome(remnant, e, observed_value=value)
    return remnant, e


def test_cleared_path():
    r, e = _run(_remnant(), 0.067)
    assert e.crossed_threshold is True
    assert "CLEARED" in e.outcome
    assert r.resolution_state == ResolutionState.REVISITED
    h1 = [a for a in r.assessments if a.hypothesis.value == "H1"][0]
    assert h1.evidence_strength.value == "high"


def test_disproven_path():
    r, e = _run(_remnant(), 0.015)
    assert e.crossed_threshold is False
    assert r.resolution_state == ResolutionState.DISPROVEN
    h1 = [a for a in r.assessments if a.hypothesis.value == "H1"][0]
    assert h1.evidence_strength.value == "low"


def test_uncertain_path():
    r, e = _run(_remnant(), 0.03)  # between failure (0.02) and success (0.04)
    assert e.crossed_threshold is False
    assert r.resolution_state == ResolutionState.UNCERTAIN


def test_threshold_immutability():
    r, e = _run(_remnant(), 0.067)
    threshold_before = e.threshold_value
    plan = plan_experiment(r)
    # planning a NEW experiment never touches the completed one
    assert e.status == "completed"
    assert e.threshold_value == threshold_before


def test_duplicate_outcome_rejected():
    r, e = _run(_remnant(), 0.067)
    with pytest.raises(ValueError):
        apply_observed_outcome(r, e, observed_value=0.05)


# --- API-level (P1): through the real app ---------------------------------------

def test_api_duplicate_outcome_409():
    with TestClient(app) as c:
        # clean isolated app instance data: the durable path uses the real store;
        # rely on the app store existing (corpus may preexist) — the invariant
        # below holds regardless of what's in there.
        rs = c.get("/api/v1/remnants").json()
        if not rs:
            c.post("/api/v1/demo/load")
            rs = c.get("/api/v1/remnants").json()
        rid = [x for x in rs if len(x["expressions"]) >= 2][0]["remnant_id"]
        exp = c.post(f"/api/v1/remnants/{rid}/experiments", json={}).json()
        ok = c.post(f"/api/v1/remnants/{rid}/experiments/{exp['experiment_id']}/outcome",
                    json={"observed_value": 0.067})
        assert ok.status_code == 200
        dup = c.post(f"/api/v1/remnants/{rid}/experiments/{exp['experiment_id']}/outcome",
                     json={"observed_value": 0.067})
        assert dup.status_code == 409


def test_api_creator_defined_experiment():
    with TestClient(app) as c:
        rs = c.get("/api/v1/remnants").json()
        if not rs:
            c.post("/api/v1/demo/load")
            rs = c.get("/api/v1/remnants").json()
        rid = rs[0]["remnant_id"]
        exp = c.post(f"/api/v1/remnants/{rid}/experiments",
                     json={"threshold": 0.10, "target_population": "devs", "measurement_window": "7d"}).json()
        assert exp["threshold_value"] == 0.10
        assert exp["target_population"] == "devs"
        assert exp["measurement_window"] == "7d"
        assert exp["defined_by_creator"] is True


def test_invalid_state_transition_rejected():
    r = _remnant(ResolutionState.FULFILLED)  # terminal — no transitions allowed
    before = len(r.state_transitions)
    ok = r.transition_to(ResolutionState.REVISITED, "illegal")
    assert ok is False  # rejected, not applied
    assert r.resolution_state == ResolutionState.FULFILLED
    assert len(r.state_transitions) == before  # no audit trail pollution


def test_minds_unavailable_is_explicit(monkeypatch):
    monkeypatch.delenv("MINDS_BUILDER_API_KEY", raising=False)
    monkeypatch.delenv("MIND_ID", raising=False)
    with TestClient(app) as c:
        m = c.get("/api/v1/mind").json()
        assert m["ok"] is False
        assert "MINDS_BUILDER_API_KEY" in (m.get("error") or "") or "MIND_ID" in (m.get("error") or "")


def test_persistence_after_restart():
    """Store reload from disk is a real restart (new Store instance)."""
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "t.db")
        s1 = Store(path)
        r = _remnant()
        s1.upsert(r)
        s2 = Store(path)  # fresh instance = process restart
        assert s2.get(r.remnant_id) is not None
        assert s2.get(r.remnant_id).title == r.title