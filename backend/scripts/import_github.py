"""
REMNANT — real GitHub evidence ingestion (issues + discussions).

Pulls REAL public issues (and their comments) from any GitHub repo via the
public REST API (no auth token required; rate-limited generously) and ingests
them through the SAME discovery pipeline as everything else, with full
provenance: repo, issue number, URL, author, timestamps, and comment ids.

Usage (repo with real user questions):
    uv run python -m scripts.import_github <owner/repo> [--limit N]

Examples:
    uv run python -m scripts.import_github matter-labs/zksync-era --limit 20
    uv run python -m scripts.import_github gitcoinco/grants-stack --limit 20
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from remnant.inference import assess_hypotheses, discover_for_expression
from remnant.models import AudienceExpression, Remnant, ResolutionState, Source
from remnant.store import Store

API = "https://api.github.com"
UA = {"User-Agent": "remnant-demo-importer", "Accept": "application/vnd.github+json"}


def _get(url: str) -> dict | list:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def fetch_issues(repo: str, limit: int = 20) -> list[dict]:
    """Real issues with need-shaped content: open issues that mention how-to or
    beginner-type questions. Falls back to recent issues when the search API is
    rate-limited (unauthenticated: 10 search/min, 60 core/hr)."""
    items: list[dict] = []
    # Try the search API first (finds need-shaped issues).
    q = f"repo:{repo} is:issue is:open in:title how OR beginner OR help OR start OR tutorial OR error"
    try:
        data = _get(f"{API}/search/issues?q={urllib.parse.quote(q)}&per_page={limit}")
        items = data.get("items", [])
    except Exception:
        items = []
    if not items:
        # Fallback: recent issues (any kind). Filter to non-PR issues locally.
        data = _get(f"{API}/repos/{repo}/issues?state=all&per_page={limit}")
        items = [i for i in data if "pull_request" not in i][:limit]
    return items


def fetch_comments(repo: str, issue_number: int) -> list[dict]:
    try:
        return _get(f"{API}/repos/{repo}/issues/{issue_number}/comments")
    except Exception:
        return []


def _iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def ingest_github(store: Store, repo: str, limit: int = 20) -> dict:
    issues = fetch_issues(repo, limit)
    log = []
    for issue in issues:
        title = issue.get("title") or ""
        body = (issue.get("body") or "").strip()
        if not title:
            continue
        number = issue["number"]
        url = issue.get("html_url") or f"{API}/repos/{repo}/issues/{number}"
        author = (issue.get("user") or {}).get("login")
        created = _iso(issue["created_at"])
        # The issue itself is a real audience expression.
        expr = AudienceExpression(
            text=f"{title}. {body[:100]}" if body else title,
            source=Source(kind="github_issue", source_id=f"{repo}#{number}"),
            occurred_at=created,
            author=author,
            url=url,
        )
        target, best_link, best_score = None, None, 0
        for remnant in store.all():
            if not remnant.expressions or remnant.resolution_state in (ResolutionState.FULFILLED, ResolutionState.REJECTED):
                continue
            link = discover_for_expression(expr.text, remnant.expressions)
            if link is None:
                continue
            score = {"same_need": 3, "candidate": 2}.get(link.get("relationship"), 0)
            if score > best_score:
                best_score, best_link, target = score, link, remnant
        if target and best_link and best_score >= 2:
            target.expressions.append(expr)
            best_link["expression_id"] = expr.expression_id
            best_link["text"] = expr.text[:120]
            target.discovered_links.append(best_link)
            target.history.append(f"REAL community evidence (github {repo}) · discovered link")
            target.assessments = assess_hypotheses(target)
            target.touch()
            store.upsert(target)
            log.append({"action": "linked", "issue": f"#{number}", "remnant": target.title[:40], "verdict": best_link["relationship"]})
        else:
            r = Remnant(title=title[:60].rstrip("?.") or "Discovered need",
                        underlying_need_hypothesis=expr.text,
                        resolution_state=ResolutionState.CANDIDATE)
            r.expressions.append(expr)
            r.assessments = assess_hypotheses(r)
            r.history.append(f"REAL community evidence (github {repo})")
            r.touch()
            store.upsert(r)
            log.append({"action": "created", "issue": f"#{number}", "remnant": title[:40], "verdict": "new_candidate"})
        # Real comment replies carry audience discussion.
        comments = fetch_comments(repo, number)
        for c in comments[:3]:
            cexpr = AudienceExpression(
                text=(c.get("body") or "").strip()[:200],
                source=Source(kind="github_comment", source_id=str(c.get("id", ""))),
                occurred_at=_iso(c["created_at"]),
                author=(c.get("user") or {}).get("login"),
                url=c.get("html_url"),
            )
            if not cexpr.text or len(cexpr.text) < 3:
                continue
            l2, t2, s2 = None, None, 0
            for remnant in store.all():
                if not remnant.expressions:
                    continue
                link2 = discover_for_expression(cexpr.text, remnant.expressions)
                if link2 is None:
                    continue
                score2 = {"same_need": 3, "candidate": 2}.get(link2.get("relationship"), 0)
                if score2 > s2:
                    s2, l2, t2 = score2, link2, remnant
            if t2 and l2 and s2 >= 2:
                t2.expressions.append(cexpr)
                l2["expression_id"] = cexpr.expression_id
                t2.discovered_links.append(l2)
                t2.touch()
                store.upsert(t2)
    return {"repo": repo, "issues": len(issues), "log": log}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", help="owner/repo, e.g. matter-labs/zksync-era")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    import urllib.parse  # noqa: F401  (used lazily in fetch_issues)
    store = Store(os.getenv("STORAGE_PATH", "./data/remnant.db"))
    result = ingest_github(store, args.repo, args.limit)
    print(f"imported {result['issues']} real issues from {result['repo']}")
    for entry in result["log"][:10]:
        print(f"  [{entry['action']}] issue {entry['issue']} -> {entry['remnant']} ({entry['verdict']})")
    print(f"store now has {len(store.all())} remnants")