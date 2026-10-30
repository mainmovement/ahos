"""University / research → paper desk signal feed receipt (read-only projection, PAPER_ONLY)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from architecture.markets.paper_trade_gates import effective_desk_notional_mult
from architecture.markets.research_desk_signal import (
    DESK_TO_PIPELINE,
    research_overlay_for_desk,
    research_predictions_for_trade,
)
from architecture.university.research_prediction_scoring import (
    SCORECARD_REL,
    build_hypothesis_scorecard,
)

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
        ev = overlay.get("evidence") if isinstance(overlay.get("evidence"), dict) else {}
        pred = research_predictions_for_trade(root, paper_desk)
        mult, mult_src = effective_desk_notional_mult(root, paper_desk)
        scorecard = build_hypothesis_scorecard(root)
        hyp_scores = {
            h["hypothesis_id"]: h
            for h in (scorecard.get("hypotheses") or [])
            if isinstance(h, dict) and h.get("hypothesis_id")
        }
        shadow_scores = []
        for hid in list(ev.get("shadow_forward_logged") or []):
            h = hyp_scores.get(str(hid))
            if h:
                shadow_scores.append(
                    {
                        "hypothesis_id": hid,
                        "hit_rate": h.get("counterfactual_hit_rate"),
                        "scored_closes": h.get("counterfactual_scored_closes"),
                        "hits": h.get("hits"),
                        "misses": h.get("misses"),
                        "skipped": h.get("skipped"),
                    }
                )
        desks.append(
            {
                "paper_desk": paper_desk,
                "pipeline_desk": pipeline,
                "research_overlay_score": overlay.get("score"),
                "research_overlay_available": overlay.get("available"),
                "research_overlay_composite_weight": ev.get("composite_weight", 0.0),
                "batch_pass_stats_keys": list(ev.get("batch_pass_stats_keys") or []),
                "shadow_forward_hypotheses": list(ev.get("shadow_forward_logged") or []),
                "shadow_forward_predictions": pred.get("predictions") or [],
                "shadow_outcome_scorecard": shadow_scores,
                "weighted_sources": list(ev.get("weighted_sources") or []),
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
        "research_hypothesis_scorecard_path": str(SCORECARD_REL.as_posix()).replace("\\", "/"),
        "honesty_note": (
            "research_overlay composite weight applies only to PASS_STATS + SURVIVED_RED_TEAM. "
            "SHADOW/FORWARD rows are logged on trades with weight 0."
        ),
    }


def export_desk_signal_feed(root: Path) -> dict[str, Any]:
    root = Path(root)
    feed = build_desk_signal_feed(root)
    out = root / FEED_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(feed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return feed
