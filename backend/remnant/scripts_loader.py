"""
REMNANT — demo corpus loader (CLEARLY LABELED SYNTHETIC).

Shared by the CLI demo (`scripts/demo.py`) and the UI Demo Controls
(`POST /api/v1/demo/load`). Every record is marked synthetic in the remnant
history and the API response; the honesty label travels with the data.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .inference import assess_hypotheses
from .models import (AudienceExpression, CreatorDecision, Remnant,
                     ResolutionState, Source)

CORPUS_LABEL = "SYNTHETIC DEMONSTRATION CORPUS — not real audience data"


def _dt(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def build_demo_corpus(store) -> list[str]:
    """Load the synthetic 2022-2026 demo arc into the store. Returns remnant ids.
    Idempotent: remnants with the same title as an existing record are skipped."""
    created: list[str] = []
    existing_titles = {r.title for r in store.all()}

    def _add(r: Remnant) -> None:
        if r.title in existing_titles:
            return
        existing_titles.add(r.title)
        store.upsert(r)
        created.append(r.remnant_id)

    # --- REMNANT A: beginner ZK education (the money-shot arc) -------------------
    r = Remnant(
        title="Beginner-friendly ZK education",
        underlying_need_hypothesis=(
            "Beginners want an accessible on-ramp to zero-knowledge education "
            "that does not assume prior cryptography background."
        ),
    )
    r.expressions = [
        AudienceExpression(text="Can you make a beginner ZK tutorial?", source=Source(kind="youtube_comment", source_id="yt-2022-01"), occurred_at=_dt("2022-06-01T00:00:00Z")),
        AudienceExpression(text="How do I even start learning ZK?", source=Source(kind="discord", source_id="dc-2022-02"), occurred_at=_dt("2022-11-19T00:00:00Z")),
        AudienceExpression(text="Could you make something for people completely new to ZK?", source=Source(kind="youtube_comment", source_id="yt-2023-03"), occurred_at=_dt("2023-03-14T00:00:00Z")),
        AudienceExpression(text="How do I start building with zero knowledge?", source=Source(kind="github_discussion", source_id="gh-2026-01"), occurred_at=_dt("2026-02-03T00:00:00Z")),
        AudienceExpression(text="I don't know where to begin with ZK — is there a path?", source=Source(kind="discord", source_id="dc-2026-02"), occurred_at=_dt("2026-07-22T00:00:00Z")),
    ]
    r.assessments = assess_hypotheses(r)
    r.history.append(CORPUS_LABEL)
    r.touch()
    _add(r)

    # --- REMNANT B: mobile community app (fulfilled need — for contrast) ---------
    r2 = Remnant(
        title="Community mobile app",
        underlying_need_hypothesis=(
            "The community wants a mobile app for participating while away from desktop."
        ),
    )
    r2.expressions = [
        AudienceExpression(text="Any chance of a mobile app?", source=Source(kind="youtube_comment", source_id="yt-2021-04"), occurred_at=_dt("2021-08-01T00:00:00Z")),
        AudienceExpression(text="Please make an app for your community", source=Source(kind="twitter", source_id="tw-2022-09"), occurred_at=_dt("2022-09-12T00:00:00Z")),
    ]
    r2.creator_decisions.append(CreatorDecision(decision="adopted", reason="shipped the community app in 2023"))
    r2.resolution_state = ResolutionState.FULFILLED
    r2.history.append(CORPUS_LABEL)
    r2.history.append("creator adopted the mobile app — fulfilled")
    r2.touch()
    _add(r2)

    # --- REMNANT C: merch (rejected need — creator said never) --------------------
    r3 = Remnant(
        title="Merch store",
        underlying_need_hypothesis=(
            "The audience wants branded merchandise."
        ),
    )
    r3.expressions = [
        AudienceExpression(text="Merch when?", source=Source(kind="twitter", source_id="tw-2023-01"), occurred_at=_dt("2023-01-20T00:00:00Z")),
        AudienceExpression(text="I'd buy a hoodie", source=Source(kind="discord", source_id="dc-2023-02"), occurred_at=_dt("2023-05-05T00:00:00Z")),
        AudienceExpression(text="Can we get merch pls", source=Source(kind="youtube_comment", source_id="yt-2026-03"), occurred_at=_dt("2026-06-11T00:00:00Z")),
    ]
    r3.creator_decisions.append(CreatorDecision(decision="rejected", reason="we are a protocol, not a merch brand — never making this"))
    r3.resolution_state = ResolutionState.REJECTED
    r3.history.append(CORPUS_LABEL)
    r3.history.append("creator rejected merch permanently — not an unresolved need")
    r3.touch()
    _add(r3)

    return created