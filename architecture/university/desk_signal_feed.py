"""University / research → paper desk signal feed receipt (read-only projection, PAPER_ONLY)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from architecture.markets.paper_trade_gates import effective_desk_notional_mult
from architecture.markets.research_desk_signal import DESK_TO_PIPELINE, research_overlay_for_desk

FEED_REL = Path("reports") / "grok" / "PAPER" / "desk_signal_feed.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_switch(root: Path) -> dict[str, Any]:
    path = root / "reports" / "grok" / "PAPER" / "strategy_switch.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 0, "active": {}}


def build_desk_signal_feed(root: Path) -> dict[str, Any]:
    root = Path(root)
    sw = _read_switch(root)
    active = sw.get("active") if isinstance(sw.get("active"), dict) else {}
    desks: list[dict[str, Any]] = []
    for paper_desk, pipeline in sorted(DESK_TO_PIPELINE.items()):
        overlay = research_overlay_for_desk(root, paper_desk)
        mult, mult_src = effective_desk_notional_mult(root, paper_desk)
        keys = list((overlay.get("evidence") or {}).get("active_keys") or [])
        batch_keys = list((overlay.get("evidence") or {}).get("batch_pass_stats_keys") or [])
        desks.append(
            {
                "paper_desk": paper_desk,
                "pipeline_desk": pipeline,
                "research_overlay_score": overlay.get("score"),
                "research_overlay_available": overlay.get("available"),
                "strategy_switch_active_keys": keys,
                "batch_pass_stats_keys": batch_keys,
                "overlay_sources": list((overlay.get("evidence") or {}).get("overlay_sources") or []),
                "notional_mult": mult,
                "notional_mult_source": mult_src,
                "paper_only": True,
            }
        )
    return {
        "schema": "ahos.desk_signal_feed.v1",
        "generated_at": _utc_now(),
        "paper_only": True,
        "strategy_switch_version": sw.get("version"),
        "strategy_switch_active_count": len(active),
        "desks": desks,
        "honesty_note": (
            "Feed documents what the paper trader may read (research_overlay signal + size policy). "
            "It does not promote strategies or override security/canonical authority."
        ),
    }


def export_desk_signal_feed(root: Path) -> dict[str, Any]:
    root = Path(root)
    feed = build_desk_signal_feed(root)
    out = root / FEED_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(feed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return feed
