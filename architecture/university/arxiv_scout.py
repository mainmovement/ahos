"""Research-institute scout: REAL arXiv q-fin papers (export.arxiv.org Atom API, free, 1 request / 3 s).

Each paper is stored with id, title, authors, published date and abstract snippet, and linked to the
pre-registered strategy_lab hypothesis it motivated. Nothing here claims a paper "validated" anything:
validation only comes from walk_forward OOS tests.
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

API = "https://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom"}
OUT_REL = Path("reports") / "grok" / "M44" / "arxiv_scout.json"
# hypothesis id -> arXiv search query (q-fin / econ). Queries are fixed before any backtest result exists.
QUERIES = {
    "H14": 'all:bitcoin AND all:exchange AND (all:inflow OR all:inflows OR all:"on-chain")',
    "H15": 'all:stablecoin AND all:bitcoin AND all:price',
    "H16": 'all:FOMC AND (all:drift OR all:announcement) AND all:returns',
    "H17": 'all:oil AND all:inventory AND (all:EIA OR all:announcement OR all:news)',
    "H18": 'all:"time series momentum"',
    "H19": 'all:"probability calibration" AND all:trading',
    "H20": 'all:"hierarchical risk parity"',
    "H21": 'all:"funding rate" AND all:perpetual',
    "H22": 'all:"news sentiment" AND all:returns',
    "RECENT_QFIN_TR": "cat:q-fin.TR",
    "RECENT_QFIN_PM": "cat:q-fin.PM",
}


def _fetch(query: str, n: int) -> list[dict[str, Any]]:
    url = f"{API}?{urllib.parse.urlencode({'search_query': query, 'max_results': n, 'sortBy': 'submittedDate' if query.startswith('cat:') else 'relevance'})}"
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "AHOS research scout"}), timeout=60) as r:
        root = ET.fromstring(r.read())
    out = []
    for e in root.findall("a:entry", NS):
        aid = (e.findtext("a:id", "", NS) or "").rsplit("/", 1)[-1]
        out.append({"arxiv_id": aid, "url": f"https://arxiv.org/abs/{aid}",
                    "title": re.sub(r"\s+", " ", e.findtext("a:title", "", NS)).strip(),
                    "authors": [a.findtext("a:name", "", NS) for a in e.findall("a:author", NS)][:6],
                    "published": (e.findtext("a:published", "", NS) or "")[:10],
                    "categories": [c.get("term") for c in e.findall("a:category", NS)],
                    "abstract_snippet": re.sub(r"\s+", " ", e.findtext("a:summary", "", NS)).strip()[:420]})
    return out


def scout(root: Path | None = None, per_query: int = 5, pause_s: float = 3.2) -> dict[str, Any]:
    results, errors = {}, {}
    for hid, q in QUERIES.items():
        try:
            got = _fetch(q, 25 if not hid.startswith("RECENT") else 10)
            # relevance guard: finance/economics/statistics categories only
            results[hid] = [p for p in got if any(c.startswith(("q-fin", "econ", "stat")) for c in p["categories"])][:per_query]
        except Exception as exc:
            errors[hid] = repr(exc)[:160]
            results[hid] = []
        time.sleep(pause_s)
    snap = {"schema": "ahos.arxiv_scout.v1", "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": API, "queries": QUERIES, "papers_by_hypothesis": results, "errors": errors,
            "paper_count": sum(len(v) for v in results.values()),
            "honesty_note": "Papers motivate hypotheses only; acceptance requires walk-forward OOS evidence."}
    if root is not None:
        p = Path(root) / OUT_REL
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap
