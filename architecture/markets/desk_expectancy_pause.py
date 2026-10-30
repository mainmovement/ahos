"""Pause a paper desk whose own closes have a negative expectancy. Shadow scoring stays."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OUT_REL = Path("reports") / "grok" / "PAPER" / "desk_pause.json"
MIN_CLOSES = 20


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def assess(closes: list[dict[str, Any]]) -> dict[str, Any]:
    cells: dict[str, list[float]] = {}
    for row in closes:
        pnl = row.get("realized_pnl_usd")
        if not isinstance(pnl, (int, float)) or isinstance(pnl, bool):
            continue
        desk = str(row.get("desk") or "UNKNOWN")
        cells.setdefault(desk, []).append(float(pnl))
    rows = []
    for desk in sorted(cells):
        sample = cells[desk]
        net = round(sum(sample), 4)
        expectancy = round(net / len(sample), 6)
        pause = len(sample) >= MIN_CLOSES and expectancy < 0
        rows.append({
            "desk": desk,
            "closes": len(sample),
            "net_pnl_usd": net,
            "expectancy_usd": expectancy,
            "paused": pause,
            "shadow": pause,
        })
    carrying = [row["desk"] for row in rows if row["net_pnl_usd"] > 0 and not row["paused"]]
    return {
        "schema": "ahos.desk_pause.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "min_closes": MIN_CLOSES,
        "desks": rows,
        "paused_desks": [row["desk"] for row in rows if row["paused"]],
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
