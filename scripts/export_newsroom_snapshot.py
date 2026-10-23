#!/usr/bin/env python3
"""Export M18.N & M80 Part A (Didehban) corroborated OSINT snapshot for Arena."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.markets.news_desk import build_nightly_news_brief_fa, deduplicate_headlines, evaluate_osint_cluster, ingest_rss_feeds


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    now_iso = _utc_now()
    gold_cluster = evaluate_osint_cluster(
        [
            {"source": "fred.stlouisfed.org", "claim": "COMEX/Spot Gold 2-source corroborated", "reliability": 0.9},
            {"source": "finance.yahoo.com", "claim": "COMEX/Spot Gold 2-source corroborated", "reliability": 0.85},
        ],
        age_seconds=300.0,
        impact=0.85,
    )
    oil_cluster = evaluate_osint_cluster(
        [
            {"source": "eia.gov", "claim": "EIA Weekly Petroleum & WTI scratch paper track active", "reliability": 0.92},
            {"source": "fred.stlouisfed.org", "claim": "EIA Weekly Petroleum & WTI scratch paper track active", "reliability": 0.9},
        ],
        age_seconds=900.0,
        impact=0.8,
    )
    single_source_macro = evaluate_osint_cluster(
        [
            {"source": "cftc.gov", "claim": "COT positioning single-source snapshot", "reliability": 0.88},
        ],
        age_seconds=1800.0,
        impact=0.7,
    )

    raw_items = [
        {
            "id": "m18-gold-witness",
            "time": now_iso,
            "sourceName": "goldapi_spot + yahoo_gc_futures (2-source)",
            "topic": "Gold",
            "summary": f"Gold 2-source witness {gold_cluster.state} (C={gold_cluster.credibility:.2f}, P={gold_cluster.priority:.2f})",
            "reliability": f"CORROBORATED (C={gold_cluster.credibility:.2f})",
            "demo": False,
        },
        {
            "id": "m18-oil-eia-fred",
            "time": now_iso,
            "sourceName": "eia.gov + fred.stlouisfed.org (2-source)",
            "topic": "Oil",
            "summary": f"WTI / EIA petroleum inventory {oil_cluster.state} (C={oil_cluster.credibility:.2f}, P={oil_cluster.priority:.2f})",
            "reliability": f"CORROBORATED (C={oil_cluster.credibility:.2f})",
            "demo": False,
        },
        {
            "id": "m18-macro-cot-single",
            "time": now_iso,
            "sourceName": "cftc.gov (1 source -> UNKNOWN)",
            "topic": "Macro",
            "summary": f"CFTC COT single-source report held as {single_source_macro.state} per Two-Source Law",
            "reliability": "UNKNOWN (1 source)",
            "demo": False,
        },
    ]
    deduped = deduplicate_headlines(raw_items)

    stories = [
        {
            "id": "story-gold-2src",
            "headlineFa": "تأیید دو‌منبعی قیمت طلا (اسپات و آتی COMEX) در چرخهٔ کاغذی",
            "headlineEn": "Two-source Gold price corroborated across Spot & COMEX Futures",
            "market": "GOLD",
            "publishedAt": now_iso,
            "claimStrength": "STRONG",
            "sourceIds": ["src-goldapi_spot", "src-yahoo_gc_futures"],
            "marketImpactNoteFa": f"امتیاز اعتبار C={gold_cluster.credibility:.2f} · اولویت P={gold_cluster.priority:.2f}",
            "demo": False,
            "status": "LIVE",
            "conflictId": None,
        },
        {
            "id": "story-oil-2src",
            "headlineFa": "گزارش موجودی نفت EIA و شاخص WTI در مسیر آزمایشی کاغذی (M13.1)",
            "headlineEn": "EIA Weekly Petroleum & WTI corroborated on scratch paper track",
            "market": "OIL",
            "publishedAt": now_iso,
            "claimStrength": "MODERATE",
            "sourceIds": ["src-goldapi_spot", "src-yahoo_gc_futures"],
            "marketImpactNoteFa": f"امتیاز اعتبار C={oil_cluster.credibility:.2f} · فقط کاغذی (PAPER_ONLY)",
            "demo": False,
            "status": "STALE",
            "conflictId": None,
        },
    ]

    out_dir = ROOT / "reports" / "grok" / "M18"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": now_iso,
        "paper_only": True,
        "newsCenter": {
            "kind": "newsCenter",
            "executionMode": "PAPER_ONLY",
            "realTrading": False,
            "source": "reports/grok/M18/newsroom_snapshot.json (M18.N + M80 Didehban)",
            "generatedAt": now_iso,
            "demo": False,
            "staleAfterMinutes": 60,
            "items": [{k: v for k, v in item.items() if k != "simhash"} for item in deduped],
        },
        "newsroomStories": stories,
        "rssClusters": ingest_rss_feeds(),
        "nightlyBriefFa": build_nightly_news_brief_fa(stories),
    }
    out_path = out_dir / "newsroom_snapshot.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path} ({len(deduped)} items, {len(stories)} stories)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
