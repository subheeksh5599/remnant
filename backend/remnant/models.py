"""
REMNANT — core domain model.

The product's central primitive is the REMNANT: a time-aware hypothesis about an
unresolved audience need. It is NOT a note, NOT a saved comment. It preserves the
underlying need candidate, its historical expressions, the creator's responses,
competing explanations, evidence, experiments, and outcomes.

Intellectual guardrails enforced here:
  - We NEVER claim certainty about "the same demand returning". We keep competing
    hypotheses (H1..H4) with evidence strength for and against each.
  - We NEVER fabricate evidence. Every claim references a source expression with
    provenance.
  - Evidence strength is qualitative (low/medium/high) unless a calibrated numeric
    score with methodology is provided.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EvidenceStrength(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ResolutionState(str, enum.Enum):
    UNRESOLVED = "unresolved"
    DORMANT = "dormant"
    FULFILLED = "fulfilled"
    REJECTED = "rejected"
    PARTIALLY_FULFILLED = "partially_fulfilled"
    REVISITED = "revisited"
    UNDER_EXPERIMENT = "under_experiment"
    VALIDATED = "validated"
    DISPROVEN = "disproven"
    UNCERTAIN = "uncertain"


# --- Competing explanations (the core intellectual move) ----------------------

class Hypothesis(str, enum.Enum):
    H1 = "H1"  # Persistent unresolved need
    H2 = "H2"  # Independent recurrence among a new audience cohort
    H3 = "H3"  # Temporary external trend
    H4 = "H4"  # Semantic similarity without meaningful underlying continuity


class HypothesisAssessment(BaseModel):
    hypothesis: Hypothesis
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)
    evidence_strength: EvidenceStrength = EvidenceStrength.LOW
    summary: str = ""


class Source(BaseModel):
    kind: str  # youtube_comment, discord, github_issue, livestream, email, ...
    source_id: str
    url: Optional[str] = None


class AudienceExpression(BaseModel):
    """The exact words someone used, with full provenance. Never fabricated."""

    expression_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    text: str
    source: Source
    occurred_at: datetime
    audience_segment: Optional[str] = None
    creator_response: Optional[str] = None


class CreatorDecision(BaseModel):
    decision: Literal["adopted", "rejected", "deferred", "no_response"] = "no_response"
    reason: Optional[str] = None
    decided_at: Optional[datetime] = None
    evidence_refs: list[str] = Field(default_factory=list)


class Experiment(BaseModel):
    experiment_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    remnant_id: str
    hypothesis: Hypothesis
    test: str  # the smallest intervention
    prediction: str
    success_threshold: str
    failure_condition: str
    status: Literal["planned", "running", "completed"] = "planned"
    observed: Optional[str] = None
    outcome: Optional[str] = None  # e.g. "high response"
    decided_at: Optional[datetime] = None


class RemnantConfiguration(BaseModel):
    """A Remnant configured in the system."""


class Remnant(BaseModel):
    """A time-aware hypothesis about an unresolved audience need."""

    remnant_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    title: str
    underlying_need_hypothesis: str
    created_at: datetime = Field(default_factory=utcnow)
    expressions: list[AudienceExpression] = Field(default_factory=list)
    creator_decisions: list[CreatorDecision] = Field(default_factory=list)
    assessments: list[HypothesisAssessment] = Field(default_factory=list)
    experiments: list[Experiment] = Field(default_factory=list)
    resolution_state: ResolutionState = ResolutionState.UNRESOLVED
    current_relevance: Literal["low", "medium", "high", "uncertain"] = "uncertain"
    history: list[str] = Field(default_factory=list)  # mind log
    mind_notes: list[str] = Field(default_factory=list)

    def first_observed(self) -> Optional[datetime]:
        if not self.expressions:
            return None
        return min(e.occurred_at for e in self.expressions)

    def last_observed(self) -> Optional[datetime]:
        if not self.expressions:
            return None
        return max(e.occurred_at for e in self.expressions)
