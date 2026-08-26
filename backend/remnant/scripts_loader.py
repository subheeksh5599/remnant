"""
REMNANT — demo corpus loader (CLEARLY LABELED SYNTHETIC).

P0.2: the corpus does NOT encode which expressions belong together. It is a
flat list of raw evidence; the DISCOVERY ENGINE (inference.discover_for_expression)
decides which expressions link into which remnant, using the transparent concept
glossary. The 2022→2026 relationship is DISCOVERED by REMNANT, not pre-encoded.
Every record is marked synthetic; the honesty label travels with the data.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .inference import assess_hypotheses, discover_for_expression, link_evidence_line
from .models import (AudienceExpression, CreatorDecision, Remnant,
                     ResolutionState, Source)

CORPUS_LABEL = "SYNTHETIC DEMONSTRATION CORPUS — not real audience data"

# Flat raw evidence in ingestion order (2022 → 2023 → 2026). NO grouping hints.
# The discovery engine must figure out that e.g. the ZK expressions belong
# together ACROSS the dormant gap, using the concept glossary alone.
_RAW_EVIDENCE: list[dict] = [
    # --- the money-shot arc: beginner ZK education ---
    {"text": "Can you make a beginner ZK tutorial?",
     "source": Source(kind="youtube_comment", source_id="yt-2022-01"), "at": "2022-06-01T00:00:00Z",
     "author": "viewer_alan", "url": "https://youtube.com/watch?v=DEMO"},
    {"text": "How do I even start learning ZK?",
     "source": Source(kind="discord", source_id="dc-2022-02"), "at": "2022-11-19T00:00:00Z",
     "author": "discord_ben", "url": "https://discord.gg/DEMO"},
    {"text": "Could you make something for people completely new to ZK?",
     "source": Source(kind="youtube_comment", source_id="yt-2023-03"), "at": "2023-03-14T00:00:00Z",
     "author": "viewer_chen", "url": "https://youtube.com/watch?v=DEMO"},
    # dormant gap (2024-2025: no strong matches)
    {"text": "How do I start building with zero knowledge?",
     "source": Source(kind="github_discussion", source_id="gh-2026-01"), "at": "2026-02-03T00:00:00Z",
     "author": "dev_dana", "url": "https://github.com/DEMO/discussions/1"},
    {"text": "I don't know where to begin with ZK — is there a path?",
     "source": Source(kind="discord", source_id="dc-2026-02"), "at": "2026-07-22T00:00:00Z",
     "author": "discord_erin", "url": "https://discord.gg/DEMO"},
    # --- the fulfilled contrast: mobile app (creator adopted) ---
    {"text": "Any chance of a mobile app?",
     "source": Source(kind="youtube_comment", source_id="yt-2021-04"), "at": "2021-08-01T00:00:00Z",
     "author": "viewer_frank", "url": "https://youtube.com/watch?v=DEMO2"},
    {"text": "Please make an app for your community",
     "source": Source(kind="twitter", source_id="tw-2022-09"), "at": "2022-09-12T00:00:00Z",
     "author": "tw_gina", "url": "https://twitter.com/DEMO"},
    # --- the rejected contrast: merch (creator said never) ---
    {"text": "Merch when?",
     "source": Source(kind="twitter", source_id="tw-2023-01"), "at": "2023-01-20T00:00:00Z",
     "author": "tw_hao", "url": "https://twitter.com/DEMO"},
    {"text": "I'd buy a hoodie",
     "source": Source(kind="discord", source_id="dc-2023-02"), "at": "2023-05-05T00:00:00Z",
     "author": "discord_ian", "url": "https://discord.gg/DEMO"},
    {"text": "Can we get merch pls",
     "source": Source(kind="youtube_comment", source_id="yt-2026-03"), "at": "2026-06-11T00:00:00Z",
     "author": "viewer_jules", "url": "https://youtube.com/watch?v=DEMO2"},
]


def _dt(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def _make_expression(ev: dict) -> AudienceExpression:
    return AudienceExpression(
        text=ev["text"],
        source=ev["source"],
        occurred_at=_dt(ev["at"]),
        author=ev.get("author"),
        url=ev.get("url"),
    )


def ingest_evidence_through_discovery(store) -> list[dict]:
    """Ingest the raw evidence ONE EXPRESSION AT A TIME. For each expression:
      - offer it to every existing remnant's expressions via the discovery engine
      - if a candidate link (same_need/candidate) exists, attach it there and
        record the matcher evidence in discovered_links
      - otherwise create a NEW remnant (candidate need)
    Returns a log of what was discovered (remnant title, expression, link verdict).
    """
    discovery_log: list[dict] = []
    new_remnant_titles: list[str] = []
    for ev in _RAW_EVIDENCE:
        expr = _make_expression(ev)

        # Offer to all remnants that have evidence (skip terminal ones).
        best_link = None
        target = None
        best_score = 0
        for remnant in store.all():
            if not remnant.expressions:
                continue
            if remnant.resolution_state in (ResolutionState.FULFILLED, ResolutionState.REJECTED):
                continue
            link = discover_for_expression(expr.text, remnant.expressions)
            if link is None:
                continue
            score = _score(link)
            if score > best_score:
                best_score = score
                best_link = link
                target = remnant
        # Only attach when the matcher argues for a link (candidate or same_need).
        # insufficient_evidence (score 1) means "cannot establish" → new remnant.
        if target is not None and best_link is not None and best_score >= 2:
            # Link it — but keep the evidence + uncertainty on the record.
            target.expressions.append(expr)
            link["expression_id"] = expr.expression_id
            link["text"] = expr.text[:120]
            target.discovered_links.append(link)
            target.history.append(f"{CORPUS_LABEL} · {link_evidence_line(link)}")
            target.assessments = assess_hypotheses(target)
            if target.resolution_state == ResolutionState.UNRESOLVED:
                target.transition_to(ResolutionState.CANDIDATE, "discovered link across expressions")
            target.touch()
            store.upsert(target)
            discovery_log.append({
                "action": "linked",
                "remnant": target.title,
                "expression": expr.text[:80],
                "verdict": best_link["relationship"],
                "evidence": link_evidence_line(best_link),
            })
        else:
            # No candidate link anywhere: it starts its own candidate remnant.
            title = expr.text[:60].rstrip("?.") or "Discovered need"
            r = Remnant(
                title=title,
                underlying_need_hypothesis=expr.text,
                resolution_state=ResolutionState.CANDIDATE,
            )
            r.expressions.append(expr)
            r.assessments = assess_hypotheses(r)
            r.history.append(CORPUS_LABEL)
            r.history.append("candidate need — no link to existing evidence; created by discovery")
            r.touch()
            store.upsert(r)
            new_remnant_titles.append(title)
            discovery_log.append({
                "action": "created",
                "remnant": title,
                "expression": expr.text[:80],
                "verdict": "new_candidate",
                "evidence": "no candidate link to existing expressions",
            })

    # Apply the contrast states for the demo story (creator decisions, not inference).
    for remnant in store.all():
        title_norm = remnant.title.rstrip("?.").strip()
        if title_norm in ("Any chance of a mobile app", "Please make an app for your community"):
            remnant.creator_decisions.append(CreatorDecision(
                decision="adopted", reason="shipped the community app in 2023",
                decided_at=_dt("2023-01-10T00:00:00Z"),
            ))
            remnant.transition_to(ResolutionState.FULFILLED, "creator adopted the mobile app")
            remnant.touch()
            store.upsert(remnant)
        elif title_norm in ("Merch when", "I'd buy a hoodie", "Can we get merch pls"):
            remnant.creator_decisions.append(CreatorDecision(
                decision="rejected", reason="we are a protocol, not a merch brand — never making this",
                decided_at=_dt("2026-07-01T00:00:00Z"),
            ))
            remnant.transition_to(ResolutionState.REJECTED, "creator rejected merch permanently")
            remnant.touch()
            store.upsert(remnant)
    return discovery_log


def _score(link: dict) -> int:
    return {"same_need": 3, "candidate": 2, "insufficient_evidence": 1, "different_need": 0}.get(
        link.get("relationship"), 0
    )


def build_demo_corpus(store) -> list[str]:
    """Load the synthetic 2022-2026 demo arc into the store via the discovery
    engine. Returns remnant ids. Idempotent: skipped if the corpus is present."""
    if any("SYNTHETIC DEMONSTRATION CORPUS" in h for r in store.all() for h in r.history):
        return [r.remnant_id for r in store.all()]
    ingest_evidence_through_discovery(store)
    return [r.remnant_id for r in store.all()]