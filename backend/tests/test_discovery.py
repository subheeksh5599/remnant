"""
REMNANT — discovery-engine tests (P0.2 + matcher upgrade).

Covers: cross-language candidate discovery (the benchmark pair), the collision
guard, candidate states, creator-defined experiments, and the claim that the
demo corpus does NOT encode grouping.
"""

import tempfile
import os

import pytest

from remnant.inference import analyze_relationship, discover_for_expression
from remnant.models import ResolutionState
from remnant.store import Store
from remnant.scripts_loader import ingest_evidence_through_discovery


# --- cross-language matcher ---------------------------------------------------

def test_cross_language_pair_is_candidate():
    """THE benchmark: 'beginner ZK tutorial' vs 'start building with zero
    knowledge' must become a CANDIDATE (concept discovery) — never merged,
    never dismissed."""
    r = analyze_relationship(
        "Can you make a beginner ZK tutorial?",
        "How do I start building with zero knowledge?",
    )
    assert r["relationship"] == "candidate"
    assert "zero_knowledge" in r["shared_concepts"]
    assert r["supporting"]  # evidence for the link
    assert r["uncertainty"]  # limits stated
    # NEVER a merge: candidate is not same_need, and no auto-attach happens here.


def test_collision_guard_still_holds():
    r = analyze_relationship("How do I learn ZK?", "ZK badge for my profile looks broken")
    assert r["relationship"] == "different_need"
    assert r["confidence"] == "high"


def test_cross_language_same_subject_different_need():
    """Same subject concept (zero_knowledge) but a merch ask is NOT a link
    to the ZK need — the discovery must not over-link on one concept."""
    r = analyze_relationship("I want to learn zero knowledge proofs", "Can we get merch pls")
    # zero_knowledge concept on A; merch concept on B — no shared subject
    assert r["relationship"] in ("insufficient_evidence", "different_need")


def test_discover_returns_best_link():
    from remnant.models import AudienceExpression, Source
    from datetime import datetime, timezone

    existing = [
        AudienceExpression(text="Can you make a beginner ZK tutorial?",
                           source=Source(kind="yt", source_id="1"),
                           occurred_at=datetime(2022, 6, 1, tzinfo=timezone.utc)),
    ]
    link = discover_for_expression("How do I start building with zero knowledge?", existing)
    assert link is not None
    assert link["relationship"] in ("candidate", "same_need")
    assert "zero_knowledge" in link["shared_concepts"]


# --- discovery pass-through (P0.2) ---------------------------------------------

def test_corpus_discovery_groups_without_preencoding():
    """Ingest the raw evidence one-at-a-time; the engine must discover the
    ZK group (across the dormant gap) and NOT glue merch/app into it."""
    with tempfile.TemporaryDirectory() as d:
        s = Store(os.path.join(d, "t.db"))
        ingest_evidence_through_discovery(s)
        remnants = s.all()
        assert len(remnants) >= 3  # ZK + app + merch discovered separately
        zk = next((r for r in remnants if "zero knowledge" in r.underlying_need_hypothesis.lower()
                   or "zk" in r.title.lower() and "beginner" in r.title.lower()), None)
        assert zk is not None
        # the 2022->2026 arc lives in ONE remnant (discovered, not encoded)
        years = sorted({e.occurred_at.year for e in zk.expressions})
        assert 2022 in years and 2026 in years
        assert len(zk.expressions) == 5  # the five ZK expressions
        assert zk.resolution_state == ResolutionState.CANDIDATE
        assert zk.discovered_links  # matcher evidence recorded


def test_corpus_contrast_states_from_creator_decisions():
    with tempfile.TemporaryDirectory() as d:
        s = Store(os.path.join(d, "t.db"))
        ingest_evidence_through_discovery(s)
        states = {r.resolution_state for r in s.all()}
        assert ResolutionState.FULFILLED in states  # mobile app adopted
        assert ResolutionState.REJECTED in states  # merch rejected


# --- creator-defined experiment (P2) ---------------------------------------------

def test_creator_defined_experiment_overrides():
    from remnant.models import Remnant, AudienceExpression, Source
    from remnant.experiments import plan_experiment
    from datetime import datetime, timezone

    r = Remnant(title="T", underlying_need_hypothesis="need")
    r.expressions.append(AudienceExpression(
        text="x", source=Source(kind="yt", source_id="1"),
        occurred_at=datetime(2022, 1, 1, tzinfo=timezone.utc)))
    exp = plan_experiment(r, threshold=0.10, target_population="new developers", measurement_window="7d")
    assert exp.threshold_value == 0.10
    assert exp.target_population == "new developers"
    assert exp.measurement_window == "7d"
    assert exp.defined_by_creator is True
    # default still works
    exp2 = plan_experiment(r)
    assert exp2.threshold_value == 0.04
    assert exp2.defined_by_creator is False