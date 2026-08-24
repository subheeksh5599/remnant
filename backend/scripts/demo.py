"""
REMNANT — demo corpus + scenario (CLEARLY LABELED SYNTHETIC).

This module builds a *synthetic demonstration corpus* for the demo. It is NOT
presented as real audience data. The product's honesty rule is absolute: synthetic
data is labeled as such everywhere it appears, and the real product path uses
creator-provided / real public data instead.

The demo scenario is the money-shot:

  2022-2023  expressions of a beginner-ZK-learning need  -> creates REMNANT #918
  (dormant gap 2024-2025)
  2026       new expressions in different language        -> possible recurrence
  competing hypotheses H1 (persistent need) vs H2 (new cohort) held honestly
  -> plan smallest experiment -> record outcome -> belief update
  -> persistence proof (fresh session still knows the full history)
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from remnant.experiments import apply_observed_outcome, plan_experiment
from remnant.inference import assess_hypotheses
from remnant.models import (AudienceExpression, Remnant, Source)
from remnant.store import Store


def build_demo_remnant() -> Remnant:
    """Build REMNANT #918 with the full 2022 -> 2026 arc."""
    r = Remnant(
        title="Beginner-friendly zero-knowledge education",
        underlying_need_hypothesis=(
            "Beginners want an accessible on-ramp to zero-knowledge development, "
            "expressed across years in changing language."
        ),
    )

    def expr(text: str, year: int, month: int, sid: str, kind: str = "youtube_comment") -> AudienceExpression:
        return AudienceExpression(
            text=text,
            source=Source(kind=kind, source_id=sid),
            occurred_at=datetime(year, month, 1, tzinfo=timezone.utc),
        )

    # Historical arc (2022-2023)
    r.expressions.append(expr("Can you make a beginner ZK tutorial?", 2022, 6, "yt-2022-06"))
    r.expressions.append(expr("How do I even start learning ZK?", 2022, 9, "yt-2022-09"))
    r.expressions.append(expr("Could you make something for people completely new to ZK?", 2023, 3, "yt-2023-03"))

    # Re-emergence in different language (2026)
    r.expressions.append(expr("How do I start building with zero knowledge?", 2026, 2, "yt-2026-02"))
    r.expressions.append(expr("I have no idea where to begin with ZK.", 2026, 4, "discord-2026-04", "discord"))
    r.expressions.append(expr("Is there a beginner-friendly way to learn this?", 2026, 5, "yt-2026-05"))

    r.assessments = assess_hypotheses(r)
    r.history.append("remnant constructed from synthetic demonstration corpus (2022-2026 arc)")
    return r


def run_demo_scenario(store_path: str = "./data/demo.db") -> None:
    """Run the full demo loop, writing state to a durable store so persistence
    across sessions can be demonstrated (restart -> ask -> still knows)."""
    store = Store(store_path)
    r = store.get("demo-918") or build_demo_remnant()
    r.remnant_id = "demo-918"
    r.assessments = assess_hypotheses(r)
    store.upsert(r)

    print("=" * 70)
    print("REMNANT demo scenario (SYNTHETIC DEMONSTRATION CORPUS — not real data)")
    print("=" * 70)
    print(f"\nREMNANT #918: {r.title}")
    print(f"  hypothesis: {r.underlying_need_hypothesis}")
    print(f"  first observed: {r.first_observed().date()}  last: {r.last_observed().date()}")
    print(f"  resolution state: {r.resolution_state.value}")

    print("\n-- competing explanations --")
    for a in r.assessments:
        print(f"  {a.hypothesis.value} [{a.evidence_strength.value}]: {a.summary}")

    print("\n-- the honest position --")
    print("  'We cannot reliably distinguish H1 (persistent need) from H2 (new cohort) yet.'")

    print("\n-- plan smallest experiment --")
    exp = plan_experiment(r)
    r.experiments.append(exp)
    store.upsert(r)
    print(f"  {exp.test}")
    print(f"  success: {exp.success_threshold}")
    print(f"  failure: {exp.failure_condition}")

    print("\n-- record real (demo-observed) outcome --")
    apply_observed_outcome(r, exp, "high response from the target audience segment")
    store.upsert(r)
    print(f"  observed -> '{exp.observed}'")
    print(f"  resolution state: {r.resolution_state.value}")

    print("\n-- persistence proof (fresh store handle = new session) --")
    fresh = Store(store_path)
    loaded = fresh.get("demo-918")
    assert loaded is not None
    print("  fresh session still knows:")
    print(f"    title: {loaded.title}")
    print(f"    expressions: {len(loaded.expressions)} (2022..2026)")
    print(f"    state: {loaded.resolution_state.value}")
    print(f"    experiments: {len(loaded.experiments)}")
    print(f"    history tail: {loaded.history[-2:]}")
    print("\n  The Mind remembered what the conversation had left behind.")

    print("\nSYNTHETIC DEMONSTRATION CORPUS — not real audience data.")


if __name__ == "__main__":
    run_demo_scenario(os.getenv("STORAGE_PATH", "./data/demo.db"))