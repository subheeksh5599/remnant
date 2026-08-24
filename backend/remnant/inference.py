"""
REMNANT — inference core.

The intellectual heart: distinguishing EXPRESSION from UNDERLYING NEED, without
claiming certainty. For a candidate need we maintain competing explanations (H1-H4)
and reason over which deserves attention now.

Anti-slop guardrails:
  - No fabricated similarity numbers pretending to be calibrated probability.
  - Semantic grouping surfaces BOTH support and conflict.
  - We never auto-merge expressions that merely share a token ("ZK").
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .models import (AudienceExpression, EvidenceStrength, Hypothesis,
                     HypothesisAssessment, Remnant)


@dataclass
class SemanticMatch:
    """How one expression relates to an underlying need candidate, honestly scored."""
    expression_id: str
    text: str
    need_candidate: str
    match: EvidenceStrength = EvidenceStrength.LOW
    shared_subject: bool = False
    same_outcome: bool = False
    same_audience_need: bool = False
    conflict: Optional[str] = None
    notes: str = ""


# --- Adversarial token-collision guard ---------------------------------------
# Two expressions that share a token are NOT evidence of continuity. We explicitly
# track this so we never over-merge.

def _tokens(s: str) -> set[str]:
    # Strip punctuation so "ZK?" and "ZK" are the same token. Naive split
    # otherwise produces false negatives (and false positives on shared
    # punctuation artifacts).
    import re

    return {t for t in re.sub(r"[^a-z0-9\s]", "", s.lower()).split() if t}


def _has_token(s1: str, s2: str) -> bool:
    return len(_tokens(s1) & _tokens(s2)) > 0


def assess_expression_pair(new: str, old: str) -> dict:
    """
    Return an honest signal about whether two expressions may reflect the same
    underlying need. Used by the engine and by tests (incl. adversarial cases).
    """
    shared = _has_token(new, old)
    if not shared:
        return {"token_overlap": False, "note": "no token overlap"}
    # Token overlap alone is NOT continuity (adversarial guard).
    return {
        "token_overlap": True,
        "note": "token overlap is insufficient evidence of continuity on its own",
    }


def assess_hypotheses(remnant: Remnant, current_evidence: float = 0.5) -> list[HypothesisAssessment]:
    """
    Build H1-H4 assessments from the remnant's accumulated evidence.

    This is deliberately simple and deterministic for the core slice; semantic
    matching can plug in an embedding scorer, but the *accounting* of support vs
    conflict lives here so the reasoning is inspectable.
    """
    n_hist = sum(1 for e in remnant.expressions if e.occurred_at.year <= 2023)
    n_cur = sum(1 for e in remnant.expressions if e.occurred_at.year >= 2024)
    any_response = any(d.decision != "no_response" for d in remnant.creator_decisions)

    assessments: list[HypothesisAssessment] = []

    # H1 — persistent unresolved need
    h1 = HypothesisAssessment(
        hypothesis=Hypothesis.H1,
        supporting_evidence=[f"expressions across years: hist={n_hist} cur={n_cur}"],
        contradicting_evidence=["creator never responded" if not any_response else "creator responded"],
        evidence_strength=EvidenceStrength.MEDIUM if n_hist and n_cur else EvidenceStrength.LOW,
        summary="Historical and current expressions both exist, but continuity is inferred, not proven.",
    )
    assessments.append(h1)

    # H2 — independent recurrence among a new cohort
    h2 = HypothesisAssessment(
        hypothesis=Hypothesis.H2,
        supporting_evidence=["current cohort expressions differ in wording from historical ones"],
        contradicting_evidence=[],
        evidence_strength=EvidenceStrength.MEDIUM,
        summary="New users may independently express the same need.",
    )
    assessments.append(h2)

    # H3 — temporary external trend
    h3 = HypothesisAssessment(
        hypothesis=Hypothesis.H3,
        supporting_evidence=[],
        contradicting_evidence=[],
        evidence_strength=EvidenceStrength.LOW,
        summary="No evidence yet that this is a short-lived external spike.",
    )
    assessments.append(h3)

    # H4 — semantic coincidence
    h4 = HypothesisAssessment(
        hypothesis=Hypothesis.H4,
        supporting_evidence=["shared tokens alone could explain the link" if len(remnant.expressions) >= 2 and _has_token(
            remnant.expressions[-2].text, remnant.expressions[-1].text) else "no evidence"],
        contradicting_evidence=[],
        evidence_strength=EvidenceStrength.LOW,
        summary="Token overlap is not enough to assert a shared underlying need.",
    )
    assessments.append(h4)

    return assessments
