"""The day's loss causes and one shadow fix each. The live book is not edited."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from architecture.university.learning_loop import loss_cause

REPORT_REL = Path("reports") / "grok" / "PAPER" / "daily_diagnosis.json"

_CAUSE_ORDER = ("FEE_DRAG", "BAD_DATA", "NEWS_TRAP", "WRONG_FAMILY", "BAD_TIMING", "REGIME", "UNKNOWN")
_FIX = {
    "FEE_DRAG": "Leave the 2x fee gate where it is. Shadow: drop the day's fee-drag closes from the replay.",
    "BAD_DATA": "A CONFLICT witness stays untradable. Shadow: drop the day's bad-data closes from the replay.",
    "NEWS_TRAP": "News stays at weight 0. Shadow: drop the day's news-trap closes from the replay.",
    "WRONG_FAMILY": "Leave that family's weight in shadow until DSR and PBO pass.",
    "BAD_TIMING": "Leave the time stop where it is. Shadow: replay the same closes with the existing time stop only.",
    "REGIME": "Leave the regime size haircut where it is. Do not add another live haircut.",
    "UNKNOWN": "No fix. The cause is not identified.",
}


def _day(row: dict[str, Any]) -> str:
    return str(row.get("closed_at") or "")[:10]


def diagnose_day(closes: list[dict[str, Any]], day: str) -> dict[str, Any]:
    losses = [row for row in closes if _day(row) == day and float(row.get("realized_pnl_usd") or 0) <= 0]
    counts = {cause: 0 for cause in _CAUSE_ORDER}
    for row in losses:
        cause = loss_cause(row)
        if cause in counts:
            counts[cause] += 1
    ranked = sorted((cause for cause in _CAUSE_ORDER if counts[cause] > 0), key=lambda cause: (-counts[cause], _CAUSE_ORDER.index(cause)))
    top = ranked[:3]
    chosen = top[0] if top else None
    fixes = [
        {"cause": cause, "n": counts[cause], "fix_proposal": _FIX[cause], "fix_status": "NO_FIX" if cause == "UNKNOWN" else "SHADOW"}
        for cause in top
    ]
    return {
        "schema": "ahos.daily_diagnosis.v1",
        "paper_only": True,
        "day": day,
        "loss_count": len(losses),
        "causes": counts,
        "primary_cause": chosen,
        "top_causes": fixes,
        "fix_proposal": _FIX.get(chosen) if chosen else "No losing close on this day.",
        "fix_status": "SHADOW" if chosen and chosen != "UNKNOWN" else "NO_FIX",
        "applied_to_live": False,
    }


def shadow_test(closes: list[dict[str, Any]], day: str) -> dict[str, Any]:
    """Replay the day's closes with the proposed cause removed. Live pnl is not changed."""
    report = diagnose_day(closes, day)
    cause = report["primary_cause"]
    day_rows = [row for row in closes if _day(row) == day]
    live = round(sum(float(row.get("realized_pnl_usd") or 0) for row in day_rows), 4)
    if cause is None or report["fix_status"] != "SHADOW":
        shadow = live
    else:
        shadow = round(sum(
            float(row.get("realized_pnl_usd") or 0)
            for row in day_rows
            if loss_cause(row) != cause
        ), 4)
    report["live_pnl_usd"] = live
    report["shadow_pnl_usd"] = shadow
    report["shadow_minus_live_usd"] = round(shadow - live, 4)
    for fix in report["top_causes"]:
        if fix["fix_status"] != "SHADOW":
            fix["shadow_minus_live_usd"] = 0.0
            continue
        without = round(sum(
            float(row.get("realized_pnl_usd") or 0)
            for row in day_rows
            if loss_cause(row) != fix["cause"]
        ), 4)
        fix["shadow_minus_live_usd"] = round(without - live, 4)
        fix["applied_to_live"] = False
    report["applied_to_live"] = False
    return report


def export_daily(root: Path, closes: list[dict[str, Any]], day: str) -> dict[str, Any]:
    doc = shadow_test(closes, day)
    path = Path(root) / REPORT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return doc
