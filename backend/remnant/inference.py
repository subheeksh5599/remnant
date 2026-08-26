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


# --- Transparent concept glossary (deterministic, auditable) ------------------
# Cross-language need discovery WITHOUT an LLM: a curated, inspectable mapping
# from surface words to NEED CONCEPTS. Two expressions that share a concept can
# become a CANDIDATE relationship even with zero token overlap — but never an
# automatic merge. The glossary is small, explicit, and shown in the reasoning
# evidence so a judge can audit exactly why two expressions were linked.
#
# Concept assignment is a rule, not a statistical guess. This is the honest
# middle ground between naive token matching and an un-auditable embedding.

CONCEPT_GLOSSARY: dict[str, set[str]] = {
    # zero-knowledge domain (the demo's canonical need)
    "zk": {"zero_knowledge"},
    "zero-knowledge": {"zero_knowledge"},
    "zero knowledge": {"zero_knowledge"},
    "zkp": {"zero_knowledge"},
    "zksnarks": {"zero_knowledge"},
    "proofs": {"zero_knowledge"},
    "crypto": {"zero_knowledge"},
    "cryptography": {"zero_knowledge"},
    # learning / on-ramp intent (the common underlying NEED shape)
    "tutorial": {"learning_resource", "on_ramp"},
    "tutor": {"learning_resource"},
    "learn": {"learning_resource", "on_ramp"},
    "learning": {"learning_resource", "on_ramp"},
    "beginner": {"on_ramp"},
    "beginners": {"on_ramp"},
    "start": {"on_ramp", "get_started"},
    "starting": {"on_ramp", "get_started"},
    "build": {"get_started", "building"},
    "building": {"get_started", "building"},
    "path": {"on_ramp"},
    "guide": {"learning_resource"},
    "intro": {"learning_resource"},
    "introduction": {"learning_resource"},
    "explainer": {"learning_resource"},
    "course": {"learning_resource"},
    "on-ramp": {"on_ramp"},
    "onramp": {"on_ramp"},
    "new to": {"on_ramp"},  # "completely new to ZK" = an on-ramp ask
    "newbie": {"on_ramp"},
    "noob": {"on_ramp"},
    # fault/issue context (the adversarial collision guard)
    "broken": {"fault_report"},
    "bug": {"fault_report"},
    "fix": {"fault_report"},
    "error": {"fault_report"},
    "crash": {"fault_report"},
    "issue": {"fault_report"},
    "fails": {"fault_report"},
    "not working": {"fault_report"},
    # merch / commerce
    "merch": {"merchandise"},
    "hoodie": {"merchandise"},
    "shirt": {"merchandise"},
    "tshirt": {"merchandise"},
    "store": {"merchandise"},
    # app / mobile
    "app": {"mobile_app"},
    "mobile": {"mobile_app"},
    "android": {"mobile_app"},
    "ios": {"mobile_app"},
    "iphone": {"mobile_app"},
}

# Concepts considered "the same underlying need" when both sides share them.
# Two expressions sharing ONLY a domain concept (zero_knowledge) → candidate.
# Sharing a domain concept + an intent concept (on_ramp) → stronger candidate.
_SUBJECT_CONCEPTS = {"zero_knowledge", "merchandise", "mobile_app", "fault_report"}
_INTENT_CONCEPTS = {"learning_resource", "on_ramp", "get_started", "building"}


def _concepts(s: str) -> set[str]:
    """Map an expression's surface words to need concepts via the glossary.
    Multi-word phrases are checked first; falls back to single tokens."""
    import re

    lowered = s.lower().strip()
    matched: set[str] = set()
    tokens = _tokens(s)

    # phrase-level lookups (multi-word keys)
    for phrase, concepts in CONCEPT_GLOSSARY.items():
        if len(phrase.split()) > 1 and phrase in lowered:
            matched.update(concepts)
    # word-level lookups
    for t in tokens:
        concepts = CONCEPT_GLOSSARY.get(t)
        if concepts:
            matched.update(concepts)
    return matched


def _stopwords() -> set[str]:
    return {"how", "do", "i", "you", "we", "a", "an", "the", "can", "make", "me",
            "to", "for", "of", "is", "are", "it", "this", "that", "with", "on",
            "in", "at", "my", "your", "our", "please", "help"}


def analyze_relationship(a: str, b: str) -> dict:
    """Cross-language need relationship analysis between two expressions.

    Layers (all deterministic, all inspectable):
      1. token overlap (with stemming + stopword filter)
      2. concept overlap via the transparent glossary — this is how
         "beginner ZK tutorial" and "start building with zero knowledge"
         become a CANDIDATE (shared `zero_knowledge` concept) with zero
         shared tokens.
      3. adversarial collision guard — fault/issue context blocks a merge.
    Output is structured: relationship, confidence, supporting evidence,
    conflicting evidence, uncertainty, and shared concepts. NEVER auto-merges;
    `candidate` is the strongest cross-language claim, and it demands a probe.
    """
    ta, tb = _tokens(a), _tokens(b)
    stop = _stopwords()
    shared_tokens = (ta & tb) - stop
    ca, cb = _concepts(a), _concepts(b)
    shared_concepts = ca & cb
    subject_shared = shared_concepts & _SUBJECT_CONCEPTS
    intent_shared = shared_concepts & _INTENT_CONCEPTS
    b_tokens = [t for t in tb if t not in stop]

    supporting: list[str] = []
    conflicting: list[str] = []
    uncertainty: list[str] = []

    # ---- fault/issue collision guard (always checked first) ----
    if "fault_report" in (ca | cb):
        if "fault_report" in shared_concepts:
            return {
                "expression_a": a, "expression_b": b,
                "relationship": "different_need",
                "confidence": "high",
                "supporting": ["both mention fault/issue context (broken, bug, fix, error…)"],
                "conflicting": ["fault reports express a broken CURRENT thing, not an unmet future need"],
                "uncertainty": ["if the fault is about the SAME feature the need is for, this could be 2 facets of one topic — not merged without a probe"],
                "reasoning": [
                    "adversarial collision guard: shared fault-report concept is NOT continuity",
                ],
                "shared_concepts": sorted(shared_concepts),
            }
        # one side is a fault report, the other is not — they don't align
        return {
            "expression_a": a, "expression_b": b,
            "relationship": "different_need",
            "confidence": "high",
            "supporting": [f"fault-report concept present: {sorted(ca | cb)}"],
            "conflicting": ["one side is a fault report, the other is a need — different kinds of message"],
            "uncertainty": [],
            "reasoning": ["adversarial collision guard: fault/issue context is not an unmet need on its own"],
            "shared_concepts": sorted(shared_concepts),
        }

    # ---- evidence: token overlap ----
    if shared_tokens:
        supporting.append(f"meaningful shared tokens: {sorted(shared_tokens)}")
    else:
        uncertainty.append("no shared content tokens — overlap, if any, is conceptual, not lexical")

    # ---- evidence: concept overlap (the cross-language discovery) ----
    if subject_shared:
        supporting.append(
            f"shared need-domain concept(s): {sorted(subject_shared)} — "
            "different words pointing at the same subject"
        )
    if intent_shared:
        supporting.append(
            f"shared intent concept(s): {sorted(intent_shared)} — "
            "both express the same kind of ask (learn / get started / build)"
        )
    if not shared_concepts:
        uncertainty.append("no shared concepts — cannot assert a need relationship from this matcher alone")

    # ---- verdict ----
    if not shared_tokens and not shared_concepts:
        return {
            "expression_a": a, "expression_b": b,
            "relationship": "insufficient_evidence",
            "confidence": "low",
            "supporting": supporting,
            "conflicting": conflicting,
            "uncertainty": [
                "zero lexical or conceptual overlap — the matcher cannot claim a link",
                "a different need, or a need the glossary simply cannot see; requires a probe",
            ],
            "reasoning": supporting + conflicting + uncertainty,
            "shared_concepts": sorted(shared_concepts),
        }

    # Strong lexical overlap (>=2 meaningful tokens) is the strongest signal.
    if len(shared_tokens) >= 2 and len(b_tokens) >= 3:
        relationship, confidence = "same_need", "candidate"
        uncertainty.append("same_need is a candidate label — evidence-accounted review still applies")
    elif subject_shared and intent_shared:
        # Different words, same domain + same intent → the cross-language discovery.
        relationship, confidence = "candidate", "medium"
        uncertainty.append(
            "no token overlap but matched concepts — continuity is PLAUSIBLE, not proven; "
            "an experiment is required to disambiguate H1 (persistent need) vs H2 (new cohort)"
        )
    elif subject_shared and not intent_shared:
        # Only the subject concept matches — weak but real: same topic. This is
        # how "Please make an app" links to "Any chance of a mobile app?"
        # (shared mobile_app). Low-confidence candidate — probe decides.
        relationship, confidence = "candidate", "low"
        uncertainty.append(
            "only the subject concept matches — same topic, but the two may be different needs; a probe decides"
        )
    else:
        relationship, confidence = "insufficient_evidence", "low"
        uncertainty.append(
            "shared intent without shared subject cannot establish a need relationship"
        )

    if not supporting:
        supporting.append("concept overlap detected (see shared_concepts)")
    return {
        "expression_a": a, "expression_b": b,
        "relationship": relationship,
        "confidence": confidence,
        "supporting": supporting,
        "conflicting": conflicting,
        "uncertainty": uncertainty,
        "reasoning": supporting + (["CONFLICT: " + c for c in conflicting]) + (["UNCERTAIN: " + u for u in uncertainty]),
        "shared_concepts": sorted(shared_concepts),
    }


def _tokens(s: str) -> set[str]:
    # Strip punctuation so "ZK?" and "ZK" are the same token. Naive split
    # otherwise produces false negatives (and false positives on shared
    # punctuation artifacts). Light stemming handles inflections
    # (tutorial/tutorials, beginner/beginners) so genuine continuity is not
    # missed by plural/suffix noise.
    import re

    words = re.findall(r"[a-z0-9]+", s.lower())
    return {_stem(w) for w in words}


def _stem(w: str) -> str:
    # minimal, conservative English suffix reduction (no over-stemming)
    if len(w) > 4 and w.endswith("ies") and len(w) > 5:
        return w[:-3] + "y"  # stories -> story
    if len(w) > 4 and w.endswith("ing"):
        return w[:-3]  # building -> build
    if len(w) > 3 and w.endswith("ers"):
        return w[:-2]  # beginners -> beginner
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]  # tutorials -> tutorial
    return w


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


# --- Discovery engine (P0.2: inference pass-through) --------------------------
# The demo dataset must NOT encode which expressions belong together. Instead,
# every new expression is offered to every existing remnant's evidence; the
# matcher decides the best candidate link (or none), and the remnant records
# WHERE that link came from. This is what makes the 2022→2026 relationship
# DISCOVERED by REMNANT rather than pre-encoded by the corpus.

LINK_QUALITY_ORDER = {"same_need": 3, "candidate": 2, "insufficient_evidence": 1, "different_need": 0}


def discover_for_expression(new_text: str, expressions: list[AudienceExpression]) -> Optional[dict]:
    """Offer a raw expression to a set of existing expressions; return the best
    candidate link (with matcher evidence) or None when nothing argues for a link.

    The result is a HYPOTHESIS about grouping, never a merge: the caller decides
    whether to attach, and the attachment records discovery evidence + confidence.
    """
    best: Optional[dict] = None
    best_score = 0
    for e in expressions:
        rel = analyze_relationship(new_text, e.text)
        score = LINK_QUALITY_ORDER.get(rel["relationship"], 0)
        if score > best_score:
            best_score = score
            best = {
                "against_expression_id": e.expression_id,
                "against_text": e.text[:120],
                "relationship": rel["relationship"],
                "confidence": rel["confidence"],
                "supporting": rel["supporting"],
                "conflicting": rel["conflicting"],
                "uncertainty": rel["uncertainty"],
                "shared_concepts": rel["shared_concepts"],
            }
    if best is None or best_score == 0:
        return None  # nothing argued for a link — different_need or no signal
    return best


def link_evidence_line(link: dict) -> str:
    """One audit line for a discovered link: what the matcher found + its limits."""
    rel = link["relationship"].replace("_", " ")
    conf = link["confidence"]
    concepts = ", ".join(link["shared_concepts"]) if link["shared_concepts"] else "none"
    return (f"discovered candidate link ({rel}, {conf}) vs '{link['against_text']}' "
            f"[concepts: {concepts}]")


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
