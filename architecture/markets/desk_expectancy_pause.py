"""Pause a paper desk whose own closes have a negative expectancy. Shadow scoring stays."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OUT_REL = Path("reports") / "grok" / "PAPER" / "desk_pause.json"
MIN_CLOSES = 20
EARLY_CLOSES = 10


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def assess(closes: list[dict[str, Any]]) -> dict[str, Any]:
    cells: dict[str, list[dict[str, Any]]] = {}
    for row in closes:
        pnl = row.get("realized_pnl_usd")
        if not isinstance(pnl, (int, float)) or isinstance(pnl, bool):
            continue
        desk = str(row.get("desk") or "UNKNOWN")
        cells.setdefault(desk, []).append(row)
    rows = []
    for desk in sorted(cells):
        sample = cells[desk]
        net = round(sum(float(row["realized_pnl_usd"]) for row in sample), 4)
        expectancy = round(net / len(sample), 6)
        fees = [
            float(row["fees_usd"])
            for row in sample
            if isinstance(row.get("fees_usd"), (int, float)) and not isinstance(row.get("fees_usd"), bool)
        ]
        mean_fee = round(sum(fees) / len(fees), 6) if fees else None
        pause = len(sample) >= MIN_CLOSES and expectancy < 0
        early = (
            not pause
            and len(sample) >= EARLY_CLOSES
            and mean_fee is not None
            and expectancy < (-2.0 * mean_fee)
        )
        rows.append({
            "desk": desk,
            "closes": len(sample),
            "net_pnl_usd": net,
            "expectancy_usd": expectancy,
            "mean_fee_usd": mean_fee,
            "paused": pause,
            "shadow": pause,
            "size_factor": 0.5 if early else 1.0,
            "early_warning": early,
        })
    carrying = [row["desk"] for row in rows if row["net_pnl_usd"] > 0 and not row["paused"]]
    return {
        "schema": "ahos.desk_pause.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "min_closes": MIN_CLOSES,
        "early_closes": EARLY_CLOSES,
        "desks": rows,
        "paused_desks": [row["desk"] for row in rows if row["paused"]],
        "early_warning_desks": [row["desk"] for row in rows if row["early_warning"]],
        "carrying_desks": carrying,
        "applied_to_live_weights": False,
        "decides": False,
    }


def export_pause(root: Path, closes: list[dict[str, Any]]) -> dict[str, Any]:
    doc = assess(closes)
    path = Path(root) / OUT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    return doc


def paused_desk_names(closes: list[dict[str, Any]]) -> set[str]:
    return set(assess(closes)["paused_desks"])


def early_warning_factors(closes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Half size for a desk with at least 10 closes whose mean loss is worse than twice its own fee."""
    out: dict[str, dict[str, Any]] = {}
    for row in assess(closes)["desks"]:
        if row["size_factor"] != 0.5:
            continue
        out[row["desk"]] = {
            "size_factor": 0.5,
            "rule": "EXPECTANCY_LT_2X_FEE",
            "closes": row["closes"],
            "expectancy_usd": row["expectancy_usd"],
            "mean_fee_usd": row["mean_fee_usd"],
            "applied_to_live_weights": False,
        }
    return out
