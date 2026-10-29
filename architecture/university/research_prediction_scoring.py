"""Score shadow/forward research predictions against realized paper closes (PAPER_ONLY).

Predictions are logged on trades with composite_weight=0; this module records HIT/MISS
after CLOSE without retroactively changing gates or weights.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OUTCOMES_REL = Path("reports") / "grok" / "PAPER" / "research_prediction_outcomes.jsonl"
SCORECARD_REL = Path("reports") / "grok" / "PAPER" / "research_hypothesis_scorecard.json"
SCHEMA_OUTCOME = "ahos.research_prediction_outcome.v1"
SCHEMA_SCORECARD = "ahos.research_hypothesis_scorecard.v1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _outcome_key(row: dict[str, Any]) -> str:
    return "|".join(
        (
            str(row.get("closed_at") or ""),
            str(row.get("symbol") or ""),
            str(row.get("hypothesis_id") or ""),
            str(row.get("verdict") or ""),
        )
    )


def _label_outcome(side: str, pnl: float, predicted: str) -> tuple[str, str]:
    pred = str(predicted or "UNKNOWN").upper()
    if pred in ("UNKNOWN", "NEUTRAL"):
        return "SKIPPED", "no_direction_to_score"
    trade_side = str(side or "").upper()
    if pred not in ("LONG", "SHORT"):
        return "SKIPPED", "invalid_predicted_direction"
    aligned = pred == trade_side
    if not aligned:
        return "SKIPPED", "prediction_not_aligned_with_executed_side"
    if trade_side == "LONG":
        return ("HIT", "long_trade_positive_pnl") if pnl > 0 else ("MISS", "long_trade_non_positive_pnl")
    if trade_side == "SHORT":
        return ("HIT", "short_trade_positive_pnl") if pnl > 0 else ("MISS", "short_trade_non_positive_pnl")
    return "SKIPPED", "unknown_side"


def outcomes_from_close_row(close: dict[str, Any]) -> list[dict[str, Any]]:
    """Build outcome rows for one CLOSE event (may append multiple hypotheses)."""
    preds_doc = close.get("research_predictions")
    if not isinstance(preds_doc, dict):
        eb = close.get("entry_brain")
        if isinstance(eb, dict):
            preds_doc = eb.get("research_predictions")
    if not isinstance(preds_doc, dict):
        return []
    preds = preds_doc.get("predictions")
    if not isinstance(preds, list):
        return []
    side = str(close.get("side") or "")
    pnl = float(close.get("realized_pnl_usd") or 0.0)
    symbol = str(close.get("symbol") or "")
    desk = str(close.get("desk") or preds_doc.get("desk") or "")
    closed_at = str(close.get("closed_at") or close.get("ts") or "")
    out: list[dict[str, Any]] = []
    for p in preds:
        if not isinstance(p, dict):
            continue
        hid = str(p.get("hypothesis_id") or "")
        if not hid:
            continue
        pred_dir = str(p.get("predicted_direction") or "UNKNOWN")
        label, reason = _label_outcome(side, pnl, pred_dir)
        out.append(
            {
                "schema": SCHEMA_OUTCOME,
                "recorded_at": _utc_now(),
                "closed_at": closed_at,
                "symbol": symbol,
                "desk": desk,
                "side": side,
                "realized_pnl_usd": round(pnl, 6),
                "hypothesis_id": hid,
                "verdict": p.get("verdict"),
                "predicted_direction": pred_dir,
                "predicted_score": p.get("predicted_score"),
                "composite_weight_was": float(p.get("composite_weight") or 0.0),
                "outcome_label": label,
                "outcome_reason": reason,
                "direction_aligned_with_trade": pred_dir == side,
                "paper_only": True,
                "promotion_authority": False,
            }
        )
    return out


def _load_outcome_keys(path: Path) -> set[str]:
    keys: set[str] = set()
    if not path.is_file():
        return keys
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            keys.add(_outcome_key(row))
    return keys


def append_close_outcomes(root: Path, close_row: dict[str, Any]) -> list[dict[str, Any]]:
    """Append outcome rows for this close; idempotent on (closed_at, symbol, hypothesis)."""
    root = Path(root)
    path = root / OUTCOMES_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = _load_outcome_keys(path)
    written: list[dict[str, Any]] = []
    with path.open("a", encoding="utf-8") as fh:
        for row in outcomes_from_close_row(close_row):
            if _outcome_key(row) in existing:
                continue
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            existing.add(_outcome_key(row))
            written.append(row)
    return written


def load_all_outcomes(root: Path) -> list[dict[str, Any]]:
    path = Path(root) / OUTCOMES_REL
    rows: list[dict[str, Any]] = []
    if not path.is_file():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict) and row.get("schema") == SCHEMA_OUTCOME:
            rows.append(row)
    return rows


def build_hypothesis_scorecard(root: Path) -> dict[str, Any]:
    rows = load_all_outcomes(root)
    by_hyp: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "hypothesis_id": "",
            "verdicts": set(),
            "scored": 0,
            "hits": 0,
            "misses": 0,
            "skipped": 0,
            "hit_rate": None,
            "mean_pnl_usd_when_aligned": None,
            "pnl_samples": [],
            "last_outcome_at": None,
        }
    )
    for r in rows:
        hid = str(r.get("hypothesis_id") or "")
        if not hid:
            continue
        cell = by_hyp[hid]
        cell["hypothesis_id"] = hid
        if r.get("verdict"):
            cell["verdicts"].add(str(r["verdict"]))
        label = str(r.get("outcome_label") or "")
        if label == "HIT":
            cell["hits"] += 1
            cell["scored"] += 1
            cell["pnl_samples"].append(float(r.get("realized_pnl_usd") or 0))
        elif label == "MISS":
            cell["misses"] += 1
            cell["scored"] += 1
            cell["pnl_samples"].append(float(r.get("realized_pnl_usd") or 0))
        elif label == "SKIPPED":
            cell["skipped"] += 1
        ts = r.get("closed_at") or r.get("recorded_at")
        if ts and (cell["last_outcome_at"] is None or str(ts) > str(cell["last_outcome_at"])):
            cell["last_outcome_at"] = ts
    hypotheses: list[dict[str, Any]] = []
    for hid in sorted(by_hyp):
        cell = by_hyp[hid]
        n = int(cell["scored"])
        hit_rate = round(cell["hits"] / n, 4) if n else None
        pnls = cell["pnl_samples"]
        mean_pnl = round(sum(pnls) / len(pnls), 6) if pnls else None
        hypotheses.append(
            {
                "hypothesis_id": hid,
                "verdicts": sorted(cell["verdicts"]),
                "scored_closes": n,
                "hits": cell["hits"],
                "misses": cell["misses"],
                "skipped": cell["skipped"],
                "hit_rate": hit_rate,
                "mean_pnl_usd_when_scored": mean_pnl,
                "last_outcome_at": cell["last_outcome_at"],
                "composite_weight_policy": "zero_until_PASS_STATS_and_SURVIVED",
                "paper_only": True,
            }
        )
    return {
        "schema": SCHEMA_SCORECARD,
        "generated_at": _utc_now(),
        "paper_only": True,
        "outcomes_total": len(rows),
        "hypotheses": hypotheses,
        "honesty_note": (
            "Shadow/forward predictions are scored against executed paper closes only; "
            "hit_rate does not prove edge and does not enable promotion or composite weight."
        ),
    }


def export_research_hypothesis_scorecard(root: Path) -> dict[str, Any]:
    root = Path(root)
    doc = build_hypothesis_scorecard(root)
    out = root / SCORECARD_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc


def backfill_outcomes_from_log(root: Path) -> int:
    """Scan paper_trades.jsonl for CLOSE rows with research_predictions; append missing outcomes."""
    root = Path(root)
    log = root / "reports" / "grok" / "PAPER" / "paper_trades.jsonl"
    if not log.is_file():
        return 0
    n = 0
    for line in log.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("event") != "CLOSE":
            continue
        n += len(append_close_outcomes(root, row))
    export_research_hypothesis_scorecard(root)
    return n
