"""Why a paper desk's expectancy is negative. Shadow only.

The split is pre-registered. Fees are the logged fees. Timing is a TIME_STOP
or MAX_HOLD close. An entry cause is news, the wrong family, or bad data.
Anything else on a loss is an exit. A win stays a win. Nothing here changes
a live weight.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from architecture.learning.walk_forward import deflated_sharpe, pbo_cscv, sharpe
from architecture.university.learning_loop import loss_cause

OUT_REL = Path("reports") / "grok" / "PAPER" / "edge_decomposition.json"
TIMING = {"TIME_STOP", "MAX_HOLD"}
ENTRY = {"NEWS_TRAP", "WRONG_FAMILY", "BAD_DATA"}
DSR_MIN = 0.95
PBO_MAX = 0.5
MIN_OOS = 30


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _pnl(row: dict[str, Any]) -> float:
    return float(row.get("realized_pnl_usd") or 0)


def _fee(row: dict[str, Any]) -> float:
    value = row.get("fees_usd")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0.0
    return float(value)


def bucket(row: dict[str, Any]) -> str:
    cause = loss_cause(row)
    if cause == "WIN":
        return "WIN"
    if cause == "FEE_DRAG":
        return "FEES"
    if cause == "BAD_TIMING" or str(row.get("reason") or "") in TIMING:
        return "TIMING"
    if cause in ENTRY:
        return "ENTRIES"
    return "EXITS"


def decompose(closes: list[dict[str, Any]]) -> dict[str, Any]:
    """Per desk: net, expectancy, and the dollar sum of each bucket."""
    cells: dict[str, list[dict[str, Any]]] = {}
    for row in closes:
        if isinstance(row.get("realized_pnl_usd"), bool) or not isinstance(row.get("realized_pnl_usd"), (int, float)):
            continue
        cells.setdefault(str(row.get("desk") or "UNKNOWN"), []).append(row)
    desks = []
    for desk in sorted(cells):
        sample = cells[desk]
        sums = {"WIN": 0.0, "FEES": 0.0, "ENTRIES": 0.0, "EXITS": 0.0, "TIMING": 0.0}
        counts = {key: 0 for key in sums}
        fees = 0.0
        for row in sample:
            name = bucket(row)
            sums[name] += _pnl(row)
            counts[name] += 1
            fees += _fee(row)
        net = sum(_pnl(row) for row in sample)
        negative = {key: round(sums[key], 4) for key in ("FEES", "ENTRIES", "EXITS", "TIMING") if sums[key] < 0}
        dominant = min(negative, key=negative.get) if negative else None
        desks.append({
            "desk": desk,
            "closes": len(sample),
            "net_usd": round(net, 4),
            "expectancy_usd": round(net / len(sample), 6),
            "fees_usd": round(fees, 4),
            "bucket_usd": {key: round(value, 4) for key, value in sums.items()},
            "bucket_n": counts,
            "dominant_negative": dominant,
        })
    return {"desks": desks}


def _cause_name(name: str) -> str:
    return {"FEES": "FEE_DRAG", "TIMING": "BAD_TIMING", "ENTRIES": "ENTRY_CAUSES", "EXITS": "EXITS"}.get(name, name)


def shadow_dominant(closes: list[dict[str, Any]]) -> dict[str, Any]:
    """Pick the worst in-sample bucket, then score dropping it on the later 40 percent.

    EXITS is not a single logged cause, so that bucket is not a drop rule.
    The result is never applied. A missing red-team file keeps it in shadow
    even when the out-of-sample number is positive.
    """
    ordered = sorted(
        (row for row in closes if isinstance(row.get("realized_pnl_usd"), (int, float)) and not isinstance(row.get("realized_pnl_usd"), bool)),
        key=lambda row: str(row.get("closed_at") or ""),
    )
    split = int(len(ordered) * 0.6)
    train, later = ordered[:split], ordered[split:]
    train_doc = decompose(train)
    ranked = [row for row in train_doc["desks"] if row["dominant_negative"] in ("FEES", "TIMING", "ENTRIES")]
    choice = min(ranked, key=lambda row: row["bucket_usd"][row["dominant_negative"]]) if ranked else None
    rule = _cause_name(choice["dominant_negative"]) if choice else None

    def keep(row: dict[str, Any]) -> bool:
        if rule is None:
            return True
        if rule == "FEE_DRAG":
            return loss_cause(row) != "FEE_DRAG"
        if rule == "BAD_TIMING":
            return loss_cause(row) != "BAD_TIMING"
        if rule == "ENTRY_CAUSES":
            return loss_cause(row) not in ENTRY
        return True

    kept = [row for row in later if keep(row)]
    base = [_pnl(row) for row in later]
    oos = [_pnl(row) for row in kept]
    base_mean = sum(base) / len(base) if base else None
    oos_mean = sum(oos) / len(oos) if oos else None
    trials = [sharpe(base), sharpe(oos)] if len(oos) >= 2 else []
    dsr = deflated_sharpe(oos, 2, trials) if trials else None
    blocks = _blocks(later, keep, 8)
    pbo = pbo_cscv(blocks, 8) if blocks else None
    stats_pass = (
        dsr is not None and dsr > DSR_MIN
        and pbo is not None and pbo < PBO_MAX
        and len(oos) >= MIN_OOS
        and oos_mean is not None and oos_mean > 0
    )
    # Deleting an already-labeled loss is not a rule that can be traded next time.
    # The DSR and PBO above stay as measurements of that deletion. They are not a pass.
    reasons = ["POST_HOC_CAUSE_DROP", "RED_TEAM_ABSENT"]
    if not stats_pass:
        reasons.insert(0, "PASS_STATS_ABSENT")
    stats_pass = False
    return {
        "schema": "ahos.edge_shadow.v1",
        "paper_only": True,
        "rule": rule,
        "chosen_on": "first_60_percent",
        "scored_on": "last_40_percent",
        "oos_closes": len(later),
        "oos_kept": len(kept),
        "oos_expectancy_usd": None if base_mean is None else round(base_mean, 6),
        "shadow_expectancy_usd": None if oos_mean is None else round(oos_mean, 6),
        "dsr": dsr,
        "pbo": pbo,
        "pass_stats": stats_pass,
        "red_team": None,
        "decision": "KEEP_SHADOW",
        "applied_to_live_weights": False,
        "reasons": reasons,
    }


def _blocks(later: list[dict[str, Any]], keep, n: int) -> list[list[float]] | None:
    if len(later) < n:
        return None
    size = len(later) / n
    all_blocks = []
    kept_blocks = []
    for i in range(n):
        chunk = later[int(i * size):int((i + 1) * size)]
        all_blocks.append(sum(_pnl(row) for row in chunk))
        kept_blocks.append(sum(_pnl(row) for row in chunk if keep(row)))
    return [all_blocks, kept_blocks]


def export_edge(root: Path, closes: list[dict[str, Any]]) -> dict[str, Any]:
    doc = {
        "schema": "ahos.edge_decomposition.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "live_switch": False,
        "decides": False,
        "applied_to_live_weights": False,
        **decompose(closes),
        "shadow": shadow_dominant(closes),
    }
    path = Path(root) / OUT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return doc
