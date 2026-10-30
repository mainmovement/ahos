"""One daily loss cause and one shadow fix. The live book is not edited."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from architecture.university.learning_loop import loss_cause

REPORT_REL = Path("reports") / "grok" / "PAPER" / "daily_diagnosis.json"

_CAUSE_ORDER = ("FEE_DRAG", "WRONG_FAMILY", "BAD_TIMING", "REGIME", "UNKNOWN")
_FIX = {
    "FEE_DRAG": "Leave the 2x fee gate where it is. Shadow: skip the next same-desk open after a fee-drag close.",
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
    chosen = None
    best = 0
    for cause in _CAUSE_ORDER:
        if counts[cause] > best:
            best = counts[cause]
            chosen = cause
    return {
        "schema": "ahos.daily_diagnosis.v1",
        "paper_only": True,
        "day": day,
        "loss_count": len(losses),
        "causes": counts,
        "primary_cause": chosen,
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
    report["applied_to_live"] = False
    return report


def export_daily(root: Path, closes: list[dict[str, Any]], day: str) -> dict[str, Any]:
    doc = shadow_test(closes, day)
    path = Path(root) / REPORT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return doc
