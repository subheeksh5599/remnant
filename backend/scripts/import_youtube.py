"""
REMNANT — real evidence ingestion (P1).

Pulls REAL public comments from a YouTube video (via yt-dlp, no API key) and
ingests them through the SAME discovery pipeline as everything else, with full
provenance: source kind/permalink, comment id, author, timestamp, and when WE
ingested it. Never relabels synthetic as real; the corpus label is separate.

Usage:
    uv run python -m scripts.import_youtube <video_url>
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

from remnant.inference import assess_hypotheses, discover_for_expression, link_evidence_line
from remnant.models import AudienceExpression, Remnant, ResolutionState, Source
from remnant.store import Store


def fetch_comments(video_url: str) -> list[dict]:
    """Fetch real public comments with yt-dlp. Returns [{text, author, timestamp, id}]."""
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "vid")
        cmd = [
            "yt-dlp", "--skip-download", "--write-comments",
            "--extractor-args", "youtube:comment_sort=newest",
            "--no-playlist", "-o", out, video_url,
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=600)
        info_path = out + ".info.json"
        with open(info_path, "r", encoding="utf-8") as f:
            info = json.load(f)
        comments = []
        for c in info.get("comments", []):
            ts = c.get("timestamp")
            comments.append({
                "text": (c.get("text") or "").strip(),
                "author": c.get("author"),
                "timestamp": datetime.fromtimestamp(ts, tz=timezone.utc) if ts else None,
                "comment_id": c.get("id"),
            })
        return comments, info.get("webpage_url") or video_url, info.get("title") or "video"


def ingest_comments(store: Store, comments: list[dict], video_url: str, video_title: str) -> dict:
    """Ingest real comments through discovery. Each becomes an expression with
    full provenance; the discovery engine decides grouping (never pre-encoded).
    Returns the discovery log."""
    log = []
    for c in comments:
        if not c["text"] or len(c["text"]) < 3:
            continue
        expr = AudienceExpression(
            text=c["text"],
            source=Source(kind="youtube_comment", source_id=c.get("comment_id") or f"yt-{abs(hash(c['text'])) % 999999}"),
            occurred_at=c["timestamp"] or datetime.now(timezone.utc),
            author=c.get("author"),
            url=c["url"] if (c.get("url")) else video_url,
        )
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
            score = {"same_need": 3, "candidate": 2, "insufficient_evidence": 1, "different_need": 0}.get(link["relationship"], 0)
            if score > best_score:
                best_score, best_link, target = score, link, remnant
        if target is not None and best_link is not None and best_score >= 2:
            target.expressions.append(expr)
            best_link["expression_id"] = expr.expression_id
            best_link["text"] = expr.text[:120]
            target.discovered_links.append(best_link)
            target.history.append(f"REAL community evidence (public video {video_title[:40]}) · {link_evidence_line(best_link)}")
            target.assessments = assess_hypotheses(target)
            if target.resolution_state == ResolutionState.UNRESOLVED:
                target.transition_to(ResolutionState.CANDIDATE, "real evidence linked by discovery")
            target.touch()
            store.upsert(target)
            log.append({"action": "linked", "remnant": target.title, "expression": expr.text[:80], "verdict": best_link["relationship"]})
        else:
            title = expr.text[:60].rstrip("?.") or "Discovered need"
            r = Remnant(title=title, underlying_need_hypothesis=expr.text,
                        resolution_state=ResolutionState.CANDIDATE)
            r.expressions.append(expr)
            r.assessments = assess_hypotheses(r)
            r.history.append(f"REAL community evidence (public video {video_title[:40]})")
            r.touch()
            store.upsert(r)
            log.append({"action": "created", "remnant": title, "expression": expr.text[:80], "verdict": "new_candidate"})
    return {"ingested": len(comments), "log": log, "source_url": video_url, "source_title": video_title}


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else None
    if not url:
        print("usage: uv run python -m scripts.import_youtube <video_url>")
        sys.exit(1)
    store = Store(os.getenv("STORAGE_PATH", "./data/remnant.db"))
    comments, resolved_url, title = fetch_comments(url)
    print(f"fetched {len(comments)} real comments from '{title}'")
    result = ingest_comments(store, comments, resolved_url, title)
    print(f"ingested {result['ingested']} (through discovery)")
    for entry in result["log"][:10]:
        print(f"  [{entry['action']}] {entry['expression'][:50]} -> {entry['remnant'][:30]} ({entry['verdict']})")
    print(f"source: {result['source_url']}")