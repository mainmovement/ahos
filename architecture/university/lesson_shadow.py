"""Shadow replay of today's two lessons. PAPER_ONLY. Live weights stay put."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from architecture.university.learning_loop import loss_cause

OUT_REL = Path("reports") / "grok" / "PAPER" / "lesson_shadow.json"
RULES = ("NEWS_TRAP", "BAD_TIMING")


def _pnl(row: dict[str, Any]) -> float:
    return float(row.get("realized_pnl_usd") or 0)


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def measure(closes: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(closes, key=lambda row: str(row.get("closed_at") or ""))
    live = [_pnl(row) for row in ordered]
    kept = [_pnl(row) for row in ordered if loss_cause(row) not in RULES]
    dropped = [row for row in ordered if loss_cause(row) in RULES]
    split = int(len(live) * 0.6)
    live_oos = live[split:]
    kept_oos_rows = [row for row in ordered[split:] if loss_cause(row) not in RULES]
    kept_oos = [_pnl(row) for row in kept_oos_rows]
    live_mean = _mean(live)
    shadow_mean = _mean(kept)
    live_oos_mean = _mean(live_oos)
    shadow_oos_mean = _mean(kept_oos)
    return {
        "schema": "ahos.lesson_shadow.v1",
        "paper_only": True,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rules": list(RULES),
        "rule_text": (
            "Shadow skips a close whose cause is a news trap or a timing loss. "
            "The live book is unchanged."
        ),
        "n_live": len(live),
        "n_shadow": len(kept),
        "n_dropped": len(dropped),
        "dropped_by_cause": {cause: sum(1 for row in dropped if loss_cause(row) == cause) for cause in RULES},
        "expectancy_live_usd": live_mean,
        "expectancy_shadow_usd": shadow_mean,
        "delta_expectancy_usd": None if live_mean is None or shadow_mean is None else round(shadow_mean - live_mean, 6),
        "oos_expectancy_live_usd": live_oos_mean,
        "oos_expectancy_shadow_usd": shadow_oos_mean,
        "oos_delta_expectancy_usd": (
            None if live_oos_mean is None or shadow_oos_mean is None else round(shadow_oos_mean - live_oos_mean, 6)
        ),
        "pnl_live_usd": round(sum(live), 4),
        "pnl_shadow_usd": round(sum(kept), 4),
        "applied_to_live_weights": False,
        "decides": False,
    }


def export_lesson_shadow(root: Path, closes: list[dict[str, Any]]) -> dict[str, Any]:
    doc = measure(closes)
    path = Path(root) / OUT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    return doc
