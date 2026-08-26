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
    # Discovery lifecycle: a need that REMNANT *discovered* vs one the creator
    # *confirmed*. The distinction is explicit so nobody mistakes a hypothesis
    # for a fact.
    CANDIDATE = "candidate"  # discovered by inference; unconfirmed by the creator
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"  # matcher cannot yet claim a link
    UNRESOLVED = "unresolved"
    DORMANT = "dormant"
    FULFILLED = "fulfilled"
    REJECTED = "rejected"
    PARTIALLY_FULFILLED = "partially_fulfilled"
    REVISITED = "revisited"
    UNDER_EXPERIMENT = "under_experiment"
    VALIDATED = "validated"  # creator confirmed the need (adopted)
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
    author: Optional[str] = None  # public-facing username when legitimately available
    audience_segment: Optional[str] = None
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    url: Optional[str] = None  # direct link to the evidence, when known
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
    test: str  # the smallest intervention (concrete: what exactly is published, where, to whom)
    metric: str  # exactly what is measured (e.g. comment-to-view ratio at 48h)
    threshold_value: float = 0.0  # pre-registered numeric threshold
    threshold_operator: Literal["gte", "lte"] = "gte"  # success = observed crosses this
    prediction: str
    success_threshold: str = ""
    failure_condition: str = ""
    status: Literal["planned", "running", "completed"] = "planned"
    observed_value: Optional[float] = None  # the real number, never a vibe word
    crossed_threshold: Optional[bool] = None  # deterministic verdict vs the pre-registered number
    outcome: Optional[str] = None  # human summary of the verdict
    decided_at: Optional[datetime] = None
    # Creator-defined controls (P2): when set, these OVERRIDE the planner defaults.
    target_population: Optional[str] = None  # audience segment the probe reaches
    measurement_window: Optional[str] = None  # e.g. "48h", "7d"
    defined_by_creator: bool = False  # True when the creator supplied any override


class RemnantConfiguration(BaseModel):
    """A Remnant configured in the system."""


class Remnant(BaseModel):
    """A time-aware hypothesis about an unresolved audience need."""

    schema_version: int = 2  # v2: discovery lifecycle (candidate/insufficient_evidence) + discovered_links
    remnant_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    title: str
    underlying_need_hypothesis: str
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    expressions: list[AudienceExpression] = Field(default_factory=list)
    creator_decisions: list[CreatorDecision] = Field(default_factory=list)
    assessments: list[HypothesisAssessment] = Field(default_factory=list)
    experiments: list[Experiment] = Field(default_factory=list)
    resolution_state: ResolutionState = ResolutionState.UNRESOLVED
    current_relevance: Literal["low", "medium", "high", "uncertain"] = "uncertain"
    history: list[str] = Field(default_factory=list)  # mind log
    mind_notes: list[str] = Field(default_factory=list)
    state_transitions: list[dict] = Field(default_factory=list)  # state-change audit
    discovered_links: list[dict] = Field(default_factory=list)  # P0.2: matcher evidence for each link

    # --- state transition guard -------------------------------------------------
    _ALLOWED_TRANSITIONS: dict[str, set[str]] = {
        "candidate": {"unresolved", "dormant", "fulfilled", "rejected", "revisited", "uncertain",
                      "under_experiment", "disproven", "insufficient_evidence", "validated"},
        "insufficient_evidence": {"candidate", "unresolved", "dormant", "revisited", "uncertain", "disproven"},
        "unresolved": {"dormant", "fulfilled", "rejected", "revisited", "uncertain", "under_experiment", "disproven", "validated"},
        "dormant": {"unresolved", "fulfilled", "rejected", "revisited", "uncertain", "under_experiment", "disproven"},
        "under_experiment": {"revisited", "disproven", "uncertain", "fulfilled", "rejected", "validated"},
        "uncertain": {"revisited", "disproven", "fulfilled", "rejected", "under_experiment"},
        "revisited": {"fulfilled", "rejected", "disproven", "uncertain", "validated"},
        "fulfilled": set(),
        "rejected": set(),
        "disproven": {"revisited", "dormant", "uncertain"},
        "partially_fulfilled": {"fulfilled", "rejected"},
        "validated": {"fulfilled", "rejected"},
    }

    @classmethod
    def _tickle(cls) -> None:
        """Touch the class so the transition map is materialized before use."""

    def touch(self) -> None:
        self.updated_at = utcnow()

    def transition_to(self, new_state: ResolutionState, reason: str) -> bool:
        """Guard every state change; record the transition in the audit trail.

        Returns True if the transition was applied, False if it is not allowed.
        """
        current = self.resolution_state.value
        allowed = self._ALLOWED_TRANSITIONS.get(current, set())
        if new_state.value not in allowed:
            return False
        self.state_transitions.append(
            {
                "from": current,
                "to": new_state.value,
                "reason": reason,
                "at": utcnow().isoformat(),
            }
        )
        self.resolution_state = new_state
        self.touch()
        return True

    def first_observed(self) -> Optional[datetime]:
        if not self.expressions:
            return None
        return min(e.occurred_at for e in self.expressions)

    def last_observed(self) -> Optional[datetime]:
        if not self.expressions:
            return None
        return max(e.occurred_at for e in self.expressions)
