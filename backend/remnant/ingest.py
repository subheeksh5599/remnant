"""
REMNANT — real community data import (shared by scripts + HTTP endpoints).

Fetch REAL evidence from public sources and run it through the SAME discovery
pipeline as everything else. Provenance is first-class: source kind, id, url,
author, and timestamps travel with every expression. Never relabels synthetic
as real — imported data is REAL by construction and labeled as such.

Sources:
  github  -- public GitHub issues + comments (REST API, no key)
  youtube -- public YouTube video comments (yt-dlp, no key)
  discord -- exported messages (JSON/CSV/paste)
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Optional

from .inference import assess_hypotheses, discover_for_expression
from .models import AudienceExpression, Remnant, ResolutionState, Source
from .store import Store

GH_API = "https://api.github.com"
UA = {"User-Agent": "remnant-importer", "Accept": "application/vnd.github+json"}


def _get_json(url: str, timeout: int = 30) -> dict | list:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _best_link(store: Store, text: str):
    """Discovery: best candidate remnant for an expression (or None).

    Deliberately conservative: an expression only links when it shares a
    TOPIC-SPECIFIC subject concept (zero_knowledge / mobile_app / merchandise /
    fault_report) or >=2 meaningful tokens with an existing remnant. Generic
    intent words alone (learn/get/start) are NOT enough — otherwise one
    imported corpus collapses every comment into one remnant (a real failure
    observed with a 900-comment import).
    """
    best, target, score = None, None, 0
    for remnant in store.all():
        if not remnant.expressions or remnant.resolution_state in (ResolutionState.FULFILLED, ResolutionState.REJECTED):
            continue
        s = _link_strength(text, remnant.expressions)
        if s > score:
            score, target = s, remnant
    if target is None or score < 2:
        return (None, None, 0)
    # build the evidence record using the standard matcher against the best remnant
    from .inference import discover_for_expression
    link = discover_for_expression(text, target.expressions) if target else None
    return (target, link, score)


def _link_strength(text: str, expressions) -> int:
    """0 = no link, 2 = candidate (concept or 2+ tokens), 3 = strong same_need."""
    from .inference import _concepts, _tokens, _SUBJECT_CONCEPTS

    subjects = set()
    strong = 0
    for e in expressions[:24]:
        shared = _concepts(text) & _concepts(e.text)
        if shared & _SUBJECT_CONCEPTS:
            subjects |= shared & _SUBJECT_CONCEPTS
            strong = max(strong, 2)
        meaningful = len((_tokens(text) & _tokens(e.text)) - _STOP)
        if meaningful >= 2:
            strong = max(strong, 3)
        if strong >= 3:
            break
    return strong if subjects or strong else 0


_SUBJECT_CONCEPTS = {"zero_knowledge", "merchandise", "mobile_app", "fault_report"}
_STOP = {"how", "do", "i", "you", "we", "a", "an", "the", "can", "make", "me",
         "to", "for", "of", "is", "are", "it", "this", "that", "with", "on",
         "in", "at", "my", "your", "our", "please", "help", "start", "get",
         "learn", "building", "new", "vid", "video", "app", "please"}


def _attach(store: Store, remnant: Remnant, expr: AudienceExpression, link: dict, provenance_label: str) -> None:
    remnant.expressions.append(expr)
    link["expression_id"] = expr.expression_id
    link["text"] = expr.text[:120]
    remnant.discovered_links.append(link)
    if provenance_label not in "".join(remnant.history):
        remnant.history.append(provenance_label)
    remnant.assessments = assess_hypotheses(remnant)
    remnant.touch()
    store.upsert(remnant)


def _create(store: Store, expr: AudienceExpression, provenance_label: str) -> Remnant:
    r = Remnant(
        title=expr.text[:60].rstrip("?.") or "Discovered need",
        underlying_need_hypothesis=expr.text,
        resolution_state=ResolutionState.CANDIDATE,
    )
    r.expressions.append(expr)
    r.assessments = assess_hypotheses(r)
    r.history.append(provenance_label)
    r.touch()
    store.upsert(r)
    return r


# --- GitHub ---------------------------------------------------------------------

def import_github(store: Store, repo: str, limit: int = 20) -> dict:
    repo = repo.strip().strip("/")
    if "/" not in repo:
        raise ValueError("repo must be owner/repo, e.g. foundry-rs/foundry")
    items: list[dict] = []
    # 1) Need-shaped issues first (search API: issues only, never PRs).
    q1 = f"repo:{repo} is:issue is:open in:title how OR beginner OR help OR start OR tutorial OR please OR error OR question"
    try:
        items = (_get_json(f"{GH_API}/search/issues?q={urllib.parse.quote(q1)}&per_page={limit}") or {}).get("items", [])
    except Exception:
        items = []
    # 2) Fallback: ANY open issue (still never a PR).
    if not items:
        try:
            q2 = f"repo:{repo} is:issue is:open"
            items = (_get_json(f"{GH_API}/search/issues?q={urllib.parse.quote(q2)}&per_page={limit}") or {}).get("items", [])
        except Exception:
            items = []
    # 3) Last resort: recent core API issues, filtered to non-PRs.
    if not items:
        try:
            data = _get_json(f"{GH_API}/repos/{repo}/issues?state=all&per_page={min(limit * 3, 100)}")
            items = [i for i in data if "pull_request" not in i][:limit]
        except Exception as e:
            raise ValueError(f"could not reach GitHub for {repo}: {e}") from e
    if not items:
        raise ValueError(f"no issues found for {repo}")

    log: list[dict] = []
    for issue in items:
        title = (issue.get("title") or "").strip()
        if not title:
            continue
        body = (issue.get("body") or "").strip()
        number = issue["number"]
        url = issue.get("html_url") or f"{GH_API}/repos/{repo}/issues/{number}"
        author = (issue.get("user") or {}).get("login")
        expr = AudienceExpression(
            text=f"{title} — {body[:140]}" if body else title,
            source=Source(kind="github_issue", source_id=f"{repo}#{number}"),
            occurred_at=_iso(issue["created_at"]),
            author=author,
            url=url,
        )
        label = f"REAL community evidence — github {repo}"
        target, link, score = _best_link(store, expr.text)
        if target and link and score >= 2:
            _attach(store, target, expr, link, label)
            log.append({"action": "linked", "issue": f"#{number}", "remnant": target.title[:45], "verdict": link["relationship"]})
        else:
            r = _create(store, expr, label)
            log.append({"action": "created", "issue": f"#{number}", "remnant": r.title[:45], "verdict": "new_candidate"})
        try:
            comments = _get_json(f"{GH_API}/repos/{repo}/issues/{number}/comments")
            for c in comments[:3]:
                cexpr = AudienceExpression(
                    text=(c.get("body") or "").strip()[:200],
                    source=Source(kind="github_comment", source_id=str(c.get("id", ""))),
                    occurred_at=_iso(c["created_at"]),
                    author=(c.get("user") or {}).get("login"),
                    url=c.get("html_url"),
                )
                if len(cexpr.text) < 3:
                    continue
                ctarget, clink, cscore = _best_link(store, cexpr.text)
                if ctarget and clink and cscore >= 2:
                    _attach(store, ctarget, cexpr, clink, f"REAL community evidence — github {repo} (comment)")
                else:
                    _create(store, cexpr, f"REAL community evidence — github {repo} (comment)")
        except Exception:
            pass
    return {"source": "github", "repo": repo, "items": len(items), "log": log[:limit]}


# --- YouTube --------------------------------------------------------------------

def import_youtube(store: Store, url: str, max_comments: int = 60) -> dict:
    """Fetch REAL public video comments with yt-dlp (no API key) if available.
    Raises a clear error when yt-dlp is not installed / the fetch fails."""
    try:
        import yt_dlp  # heavy; only needed for this path
    except ImportError as e:
        raise ValueError("yt-dlp is not installed on this instance — YouTube import needs the durable backend (add yt-dlp to backend deps)") from e

    opts = {
        "skip_download": True,
        "getcomments": True,
        "max_comments": max_comments,
        "quiet": True,
        "no_warnings": True,
        "extractor_args": {"youtube": {"comment_sort": ["newest"]}},
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        raise ValueError(f"could not fetch YouTube comments: {e}") from e

    title = (info or {}).get("title") or "video"
    comments = (info or {}).get("comments") or []
    if not comments:
        return {"source": "youtube", "video": title, "items": 0, "log": [], "note": "no comments found (or comments disabled)"}

    log: list[dict] = []
    for c in comments:
        text = (c.get("text") or "").strip()
        if len(text) < 3:
            continue
        ts = c.get("timestamp")
        expr = AudienceExpression(
            text=text[:200],
            source=Source(kind="youtube_comment", source_id=str(c.get("id") or f"yt-{abs(hash(text)) % 999999}")),
            occurred_at=datetime.fromtimestamp(ts, tz=timezone.utc) if ts else datetime.now(timezone.utc),
            author=c.get("author"),
            url=c.get("url") or url,
        )
        label = f"REAL community evidence — YouTube '{title[:40]}'"
        target, link, score = _best_link(store, expr.text)
        if target and link and score >= 2:
            _attach(store, target, expr, link, label)
            log.append({"action": "linked", "comment": text[:50], "remnant": target.title[:45], "verdict": link["relationship"]})
        else:
            r = _create(store, expr, label)
            log.append({"action": "created", "comment": text[:50], "remnant": r.title[:45], "verdict": "new_candidate"})
    return {"source": "youtube", "video": title, "items": len(comments), "log": log[:max_comments]}


# --- Discord (exported messages) --------------------------------------------------

def import_discord(store: Store, raw: str) -> dict:
    """Ingest EXPORTED Discord messages (JSON array, CSV, or pasted lines)."""
    parsed: list[dict] = []
    raw = raw.strip()
    if not raw:
        raise ValueError("empty input — paste exported messages or a JSON/CSV export")
    if raw.startswith("[") or raw.startswith("{"):
        data = json.loads(raw)
        if isinstance(data, dict):
            data = data.get("messages") or data.get("channel", {}).get("messages") or []
        for m in data:
            if not isinstance(m, dict):
                continue
            parsed.append({
                "text": str(m.get("content") or m.get("text") or ""),
                "author": m.get("author") if isinstance(m.get("author"), str) else (m.get("author") or {}).get("username") if isinstance(m.get("author"), dict) else m.get("username"),
                "ts": m.get("timestamp") or m.get("created_at"),
            })
    else:
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            parsed.append({"text": line, "author": None, "ts": None})

    log: list[dict] = []
    for m in parsed:
        text = m["text"].strip()
        if len(text) < 3:
            continue
        ts = None
        if m.get("ts"):
            try:
                ts = _iso(str(m["ts"])[:26])
            except Exception:
                ts = None
        expr = AudienceExpression(
            text=text[:200],
            source=Source(kind="discord_message", source_id=f"dc-{abs(hash(text)) % 999999}"),
            occurred_at=ts or datetime.now(timezone.utc),
            author=m.get("author"),
        )
        label = "REAL community evidence — Discord export"
        target, link, score = _best_link(store, expr.text)
        if target and link and score >= 2:
            _attach(store, target, expr, link, label)
            log.append({"action": "linked", "message": text[:50], "remnant": target.title[:45], "verdict": link["relationship"]})
        else:
            r = _create(store, expr, label)
            log.append({"action": "created", "message": text[:50], "remnant": r.title[:45], "verdict": "new_candidate"})
    if not log:
        raise ValueError("no usable messages in the input")
    return {"source": "discord", "items": len(parsed), "log": log[:50]}