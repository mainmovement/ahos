"""Weekly tech scout. Metadata only. PAPER_ONLY.

Code and models pass the license gate only for MIT, Apache-2.0, or BSD.
A model whose float32 weight estimate exceeds 4 GiB is archived. Papers and
lab notes are not code and are not installed. Nothing here clones a
repository, downloads weights, or executes upstream code. A shadow idea is
promoted only when DSR and PBO pass and the red team survived. Otherwise the
ledger archives it with a reason. The live weight is never written.
"""
from __future__ import annotations

import json
import re
import ssl
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

from architecture.university.learning_loop import stats_gate

LEDGER_REL = Path("reports") / "grok" / "RESEARCH" / "tech_scout_ledger.jsonl"
ALLOWED_LICENSES = frozenset({"mit", "apache-2.0", "bsd-2-clause", "bsd-3-clause"})
MAX_AGE_DAYS = 540
MAX_WEIGHT_BYTES = 4 * 1024 ** 3
IMPACT = {
    "risk": 5,
    "data": 4,
    "alpha": 3,
    "reasoning": 3,
    "self_debug": 3,
    "infra": 2,
    "auto_update": 2,
}

# Sources that did not return a parseable feed from this laptop on 2026-10-30.
DROPPED = {
    "ssrn": "HTTP 403",
    "papers_with_code": "HTTP 200 HTML, not the JSON API",
    "stanford_hai": "HTTP 200 HTML, not an RSS feed",
    "github_trending_accept_json": "HTTP 406; the weekly HTML page is used instead",
}

ATOM = {"a": "http://www.w3.org/2005/Atom"}
_ITEM = re.compile(r"<item[\s>].*?</item>", re.S | re.I)
_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.S | re.I)
_DATE = re.compile(r"<pubDate[^>]*>(.*?)</pubDate>", re.S | re.I)
_TAG = re.compile(r"<!\[CDATA\[|\]\]>|<[^>]+>")
_TREND = re.compile(r'<h2[^>]*>\s*<a[^>]+href="/([^"]+)"', re.I)


def _utc(now: datetime | None = None) -> datetime:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now.astimezone(timezone.utc)


def _parse_dt(raw: str | None) -> datetime | None:
    if not raw:
        return None
    raw = str(raw).strip()
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        pass
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return None


def _license_id(value: Any) -> str | None:
    if isinstance(value, dict):
        value = value.get("spdx_id") or value.get("key")
    if not isinstance(value, str) or value in {"", "NOASSERTION"}:
        return None
    return value.strip().lower()


def _fresh(when: datetime | None, now: datetime) -> bool:
    if when is None:
        return False
    return (now - when).days <= MAX_AGE_DAYS


def _row(source: str, domain: str, kind: str, idea: str, **extra: Any) -> dict[str, Any]:
    base = {
        "source": source,
        "domain": domain,
        "kind": kind,
        "idea": idea,
        "license": None,
        "updated": None,
        "size_bytes": None,
        "private": False,
        "upstream_archived": False,
        "url": None,
    }
    base.update(extra)
    return base


def parse_github_search(payload: dict[str, Any], *, domain: str) -> list[dict[str, Any]]:
    rows = []
    for item in (payload.get("items") or []) if isinstance(payload, dict) else []:
        if not isinstance(item, dict) or not item.get("full_name"):
            continue
        rows.append(_row(
            "github", domain, "code", str(item["full_name"]),
            license=_license_id(item.get("license")),
            updated=item.get("pushed_at"),
            private=bool(item.get("private")),
            upstream_archived=bool(item.get("archived")),
            url=item.get("html_url"),
        ))
    return rows


def parse_github_trending(html: str) -> list[dict[str, Any]]:
    rows = []
    seen = set()
    for name in _TREND.findall(html):
        if name.count("/") != 1 or name in seen:
            continue
        seen.add(name)
        rows.append(_row("github_trending", "infra", "code", name, url=f"https://github.com/{name}"))
        if len(rows) == 5:
            break
    return rows


def parse_arxiv(xml: str, *, domain: str) -> list[dict[str, Any]]:
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return []
    rows = []
    for entry in root.findall("a:entry", ATOM):
        title = re.sub(r"\s+", " ", entry.findtext("a:title", "", ATOM)).strip()
        if not title:
            continue
        published = (entry.findtext("a:published", "", ATOM) or "")[:10]
        aid = (entry.findtext("a:id", "", ATOM) or "").rsplit("/", 1)[-1]
        rows.append(_row(
            "arxiv", domain, "paper", title,
            license="NOT_CODE",
            updated=published or None,
            url=f"https://arxiv.org/abs/{aid}" if aid else None,
        ))
    return rows


def parse_lab_rss(xml: str, *, source: str, domain: str) -> list[dict[str, Any]]:
    rows = []
    for block in _ITEM.findall(xml)[:20]:
        title_m = _TITLE.search(block)
        if not title_m:
            continue
        date_m = _DATE.search(block)
        title = re.sub(r"\s+", " ", _TAG.sub("", title_m.group(1))).strip()
        updated = None
        if date_m:
            dt = _parse_dt(date_m.group(1))
            updated = dt.strftime("%Y-%m-%d") if dt else None
        if title:
            rows.append(_row(source, domain, "lab", title, license="NOT_CODE", updated=updated))
    return rows


def weight_bytes(model: dict[str, Any]) -> int | None:
    """Float32 upper bound from the parameter count. Storage totals are not the weight file."""
    safetensors = model.get("safetensors") if isinstance(model, dict) else None
    total = safetensors.get("total") if isinstance(safetensors, dict) else None
    if isinstance(total, int) and not isinstance(total, bool) and total > 0:
        return total * 4
    return None


def parse_hf_model(model: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(model, dict) or not model.get("id"):
        return None
    card = model.get("cardData") if isinstance(model.get("cardData"), dict) else {}
    return _row(
        "huggingface", "reasoning", "model", str(model["id"]),
        license=_license_id(card.get("license") or model.get("license")),
        updated=model.get("lastModified"),
        size_bytes=weight_bytes(model),
        private=bool(model.get("private")),
        url=f"https://huggingface.co/{model['id']}",
    )


def gate(candidate: dict[str, Any], now: datetime) -> tuple[bool, str]:
    """Hard gates. Impact is not applied to a candidate that fails one."""
    if candidate.get("private") or candidate.get("upstream_archived"):
        return False, "UPSTREAM_CLOSED"
    kind = candidate.get("kind")
    if kind in {"code", "model"}:
        if not _license_id(candidate.get("license")) or _license_id(candidate.get("license")) not in ALLOWED_LICENSES:
            return False, "LICENSE"
        if not _fresh(_parse_dt(candidate.get("updated")), now):
            return False, "STALE"
    else:
        if not _fresh(_parse_dt(candidate.get("updated")), now):
            return False, "STALE"
    if kind == "model":
        size = candidate.get("size_bytes")
        if not isinstance(size, int):
            return False, "SIZE_UNKNOWN"
        if size > MAX_WEIGHT_BYTES:
            return False, "TOO_LARGE_FOR_8GB"
    return True, "PASS"


def rank(candidates: list[dict[str, Any]], now: datetime, limit: int = 5) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    kept: list[dict[str, Any]] = []
    archived: list[dict[str, Any]] = []
    for candidate in candidates:
        ok, reason = gate(candidate, now)
        if ok:
            kept.append({**candidate, "impact": IMPACT.get(str(candidate.get("domain")), 0)})
        else:
            archived.append({**candidate, "reason": reason})
    kept.sort(key=lambda row: (row["impact"], str(row.get("updated") or "")), reverse=True)
    return kept[:limit], archived


def negahban_review(candidate: dict[str, Any]) -> dict[str, Any]:
    """Static review. Upstream code is not fetched and not executed."""
    ok, reason = (True, "METADATA_ONLY")
    if candidate.get("kind") in {"code", "model"} and _license_id(candidate.get("license")) not in ALLOWED_LICENSES:
        ok, reason = False, "LICENSE"
    if candidate.get("kind") == "model" and not isinstance(candidate.get("size_bytes"), int):
        ok, reason = False, "SIZE_UNKNOWN"
    return {
        "verdict": "PASS_STATIC" if ok else "ARCHIVE",
        "reason": reason,
        "executed": False,
        "deps_added": [],
        "network_from_candidate": False,
        "pinned_upstream": False,
        "sandboxed_run": False,
    }


def decide(
    candidate: dict[str, Any],
    review: dict[str, Any],
    oos_returns: list[float] | None = None,
    trial_returns: list[list[float]] | None = None,
    red_team: str | None = None,
) -> dict[str, Any]:
    if review.get("verdict") != "PASS_STATIC":
        decision, reason = "ARCHIVE", str(review.get("reason") or "REVIEW_FAILED")
    else:
        gate_doc = stats_gate(list(oos_returns or []), list(trial_returns or []))
        if gate_doc["gate"] == "PASS_STATS" and red_team == "SURVIVED_RED_TEAM":
            decision, reason = "PROMOTE_ELIGIBLE", "PASS_STATS_AND_SURVIVED_RED_TEAM"
        elif gate_doc["dsr"] is None or gate_doc["pbo"] is None:
            decision, reason = "ARCHIVE", "NO_OOS_NUMBER"
        elif gate_doc["gate"] != "PASS_STATS":
            decision, reason = "ARCHIVE", "FAILED_OOS"
        else:
            decision, reason = "ARCHIVE", "RED_TEAM_PENDING"
        review = {**review, "dsr": gate_doc["dsr"], "pbo": gate_doc["pbo"]}
    return {
        "source": candidate.get("source"),
        "idea": candidate.get("idea"),
        "decision": decision,
        "evidence": {
            "reason": reason,
            "domain": candidate.get("domain"),
            "kind": candidate.get("kind"),
            "license": candidate.get("license"),
            "url": candidate.get("url"),
            "hypothesis": "shadow metadata; no live weight; no upstream execution",
            "predicted_score": None,
            "applied_to_live_weights": False,
            "review": review,
        },
    }


def run_week(candidates: list[dict[str, Any]], *, now: datetime | None = None) -> list[dict[str, Any]]:
    moment = _utc(now)
    top, archived = rank(candidates, moment)
    rows = [decide(row, {"verdict": "ARCHIVE", "reason": row["reason"], "executed": False}) for row in archived]
    for candidate in top:
        rows.append(decide(candidate, negahban_review(candidate)))
    return rows


def append_ledger(root: Path, rows: list[dict[str, Any]]) -> Path:
    path = Path(root) / LEDGER_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def _ssl():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _live_get(url: str) -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": "AHOS research scout"})
    try:
        with urllib.request.urlopen(req, timeout=20, context=_ssl()) as resp:
            return resp.read(400_000).decode("utf-8", "replace")
    except Exception:
        return None


def collect_candidates(getter) -> list[dict[str, Any]]:
    """Fetch the sources that answered. A dead feed adds nothing."""
    queries = [
        ("alpha", "https://api.github.com/search/repositories?q=topic:algorithmic-trading&sort=updated&per_page=5"),
        ("alpha", "https://api.github.com/search/repositories?q=topic:quant&sort=updated&per_page=5"),
        ("reasoning", "https://api.github.com/search/repositories?q=topic:llm-agents&sort=updated&per_page=5"),
        ("self_debug", "https://api.github.com/search/repositories?q=topic:self-healing&sort=updated&per_page=5"),
    ]
    rows: list[dict[str, Any]] = []
    for domain, url in queries:
        body = getter(url)
        if body:
            try:
                rows.extend(parse_github_search(json.loads(body), domain=domain))
            except ValueError:
                pass
    trending = getter("https://github.com/trending?since=weekly")
    if trending:
        rows.extend(parse_github_trending(trending))
    for domain, url in (
        ("alpha", "https://export.arxiv.org/api/query?search_query=cat:q-fin.TR&max_results=5&sortBy=submittedDate"),
        ("reasoning", "https://export.arxiv.org/api/query?search_query=cat:cs.AI&max_results=5&sortBy=submittedDate"),
        ("data", "https://export.arxiv.org/api/query?search_query=cat:cs.LG&max_results=5&sortBy=submittedDate"),
    ):
        body = getter(url)
        if body:
            rows.extend(parse_arxiv(body, domain=domain))
    for source, domain, url in (
        ("mit_csail", "reasoning", "https://www.csail.mit.edu/rss.xml"),
        ("mit_news", "reasoning", "https://news.mit.edu/rss/topic/artificial-intelligence2"),
        ("cmu_ml", "data", "https://blog.ml.cmu.edu/feed/"),
    ):
        body = getter(url)
        if body:
            rows.extend(parse_lab_rss(body, source=source, domain=domain))
    listing = getter("https://huggingface.co/api/models?sort=downloads&direction=-1&limit=5")
    if listing:
        try:
            models = json.loads(listing)
        except ValueError:
            models = []
        if isinstance(models, list):
            for model in models[:5]:
                if not isinstance(model, dict) or not model.get("id"):
                    continue
                detail_body = getter(f"https://huggingface.co/api/models/{model['id']}")
                detail = model
                if detail_body:
                    try:
                        parsed = json.loads(detail_body)
                        if isinstance(parsed, dict):
                            detail = parsed
                    except ValueError:
                        pass
                parsed_row = parse_hf_model(detail)
                if parsed_row:
                    rows.append(parsed_row)
    return rows


def run_live(root: Path, getter=None, now: datetime | None = None) -> list[dict[str, Any]]:
    rows = run_week(collect_candidates(getter or _live_get), now=now)
    append_ledger(root, rows)
    return rows
