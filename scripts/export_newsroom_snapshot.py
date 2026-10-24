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

from architecture.markets.news_desk import build_nightly_news_brief_fa


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    """Stage 3: the newsroom is built ONLY from live, registry-verified feeds (no hand-written stories)."""
    import os
    from architecture.markets.news_desk import build_live_newsroom
    from architecture.markets import news_registry as nr
    host = os.environ.get("AHOS_HOST_ID", "laptop" if os.name == "nt" else "box")
    reg_path = ROOT / nr.OUT_REL
    if "--verify" in sys.argv or not reg_path.is_file():
        nr.verify(ROOT, host)
    now_iso = _utc_now()
    live = build_live_newsroom(ROOT, host)
    out_dir = ROOT / "reports" / "grok" / "M18"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": now_iso, "paper_only": True, "host": host,
        "stats": {k: live[k] for k in ("feeds_used", "feed_errors", "items_24h", "clusters", "corroborated")},
        "newsCenter": {"kind": "newsCenter", "executionMode": "PAPER_ONLY", "realTrading": False,
                       "source": f"reports/grok/M18/newsroom_snapshot.json (live RSS, {live['feeds_used']} verified feeds, host={host})",
                       "generatedAt": now_iso, "demo": False, "staleAfterMinutes": 60, "items": live["center_items"]},
        "newsroomStories": live["stories"],
        "rssClusters": live["rss_clusters"],
        "nightlyBriefFa": build_nightly_news_brief_fa(live["stories"]),
    }
    out_path = out_dir / "newsroom_snapshot.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path} feeds={live['feeds_used']} items24h={live['items_24h']} clusters={live['clusters']} corroborated={live['corroborated']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
