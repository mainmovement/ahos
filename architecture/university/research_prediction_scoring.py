"""Score shadow/forward research predictions against realized paper closes (PAPER_ONLY).

Executes-side scoring (legacy) plus counterfactual scoring vs the same price horizon
(entry→exit return), independent of which side we traded. Composite weight stays 0.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OUTCOMES_REL = Path("reports") / "grok" / "PAPER" / "research_prediction_outcomes.jsonl"
SCORECARD_REL = Path("reports") / "grok" / "PAPER" / "research_hypothesis_scorecard.json"
M57_WEEKLY_REL = Path("reports") / "grok" / "M57" / "weekly_research_shadow_scorecard.json"
SCHEMA_OUTCOME = "ahos.research_prediction_outcome.v2"
SCHEMA_SCORECARD = "ahos.research_hypothesis_scorecard.v2"
SCHEMA_M57_WEEKLY = "ahos.m57.weekly_research_shadow_scorecard.v1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _iso_week() -> str:
    return datetime.now(timezone.utc).strftime("%G-W%V")


def _parse_ts(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        if ts.endswith("Z"):
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def _horizon_seconds(close: dict[str, Any]) -> float | None:
    a = _parse_ts(str(close.get("opened_at") or ""))
    b = _parse_ts(str(close.get("closed_at") or close.get("ts") or ""))
    if not a or not b:
        return None
    return max(0.0, (b - a).total_seconds())


def _price_return_pct(close: dict[str, Any]) -> float | None:
    entry = close.get("entry_price")
    exit_px = close.get("fill_price") if close.get("fill_price") is not None else close.get("quote_price")
    if entry is None or exit_px is None:
        return None
    ep = float(entry)
    if ep == 0:
        return None
    return (float(exit_px) - ep) / ep


def _outcome_key(row: dict[str, Any]) -> str:
    return "|".join(
        (
            str(row.get("closed_at") or ""),
            str(row.get("symbol") or ""),
            str(row.get("hypothesis_id") or ""),
            str(row.get("verdict") or ""),
        )
    )


def _label_executed_side(side: str, pnl: float, predicted: str) -> tuple[str, str]:
    pred = str(predicted or "UNKNOWN").upper()
    if pred in ("UNKNOWN", "NEUTRAL"):
        return "SKIPPED", "no_direction_to_score"
    trade_side = str(side or "").upper()
    if pred not in ("LONG", "SHORT"):
        return "SKIPPED", "invalid_predicted_direction"
    if pred != trade_side:
        return "SKIPPED", "prediction_not_aligned_with_executed_side"
    if trade_side == "LONG":
        return ("HIT", "long_trade_positive_pnl") if pnl > 0 else ("MISS", "long_trade_non_positive_pnl")
    return ("HIT", "short_trade_positive_pnl") if pnl > 0 else ("MISS", "short_trade_non_positive_pnl")


def _label_counterfactual(predicted: str, price_return_pct: float | None) -> tuple[str, str]:
    pred = str(predicted or "UNKNOWN").upper()
    if price_return_pct is None:
        return "SKIPPED", "missing_price_horizon"
    if pred in ("UNKNOWN", "NEUTRAL"):
        return "SKIPPED", "no_direction_to_score"
    if pred == "LONG":
        return ("HIT", "price_up_over_horizon") if price_return_pct > 0 else ("MISS", "price_not_up_over_horizon")
    if pred == "SHORT":
        return ("HIT", "price_down_over_horizon") if price_return_pct < 0 else ("MISS", "price_not_down_over_horizon")
    return "SKIPPED", "invalid_predicted_direction"


def outcomes_from_close_row(close: dict[str, Any]) -> list[dict[str, Any]]:
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
    ret = _price_return_pct(close)
    horizon_s = _horizon_seconds(close)
    out: list[dict[str, Any]] = []
    for p in preds:
        if not isinstance(p, dict):
            continue
        hid = str(p.get("hypothesis_id") or "")
        if not hid:
            continue
        pred_dir = str(p.get("predicted_direction") or "UNKNOWN")
        ex_label, ex_reason = _label_executed_side(side, pnl, pred_dir)
        cf_label, cf_reason = _label_counterfactual(pred_dir, ret)
        out.append(
            {
                "schema": SCHEMA_OUTCOME,
                "recorded_at": _utc_now(),
                "closed_at": closed_at,
                "symbol": symbol,
                "desk": desk,
                "executed_side": side,
                "realized_pnl_usd": round(pnl, 6),
                "price_return_pct": round(ret, 8) if ret is not None else None,
                "horizon_seconds": round(horizon_s, 1) if horizon_s is not None else None,
                "hypothesis_id": hid,
                "verdict": p.get("verdict"),
                "predicted_direction": pred_dir,
                "predicted_score": p.get("predicted_score"),
                "composite_weight_was": float(p.get("composite_weight") or 0.0),
                "outcome_label": cf_label,
                "outcome_reason": cf_reason,
                "outcome_label_executed": ex_label,
                "outcome_reason_executed": ex_reason,
                "outcome_label_counterfactual": cf_label,
                "outcome_reason_counterfactual": cf_reason,
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
        if isinstance(row, dict) and str(row.get("schema", "")).startswith("ahos.research_prediction_outcome"):
            rows.append(row)
    return rows


def _aggregate_hypothesis(rows: list[dict[str, Any]], label_field: str) -> dict[str, dict[str, Any]]:
    by_hyp: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "hypothesis_id": "",
            "verdicts": set(),
            "scored": 0,
            "hits": 0,
            "misses": 0,
            "skipped": 0,
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
        label = str(r.get(label_field) or r.get("outcome_label") or "")
        if label == "HIT":
            cell["hits"] += 1
            cell["scored"] += 1
        elif label == "MISS":
            cell["misses"] += 1
            cell["scored"] += 1
        elif label == "SKIPPED":
            cell["skipped"] += 1
        ts = r.get("closed_at") or r.get("recorded_at")
        if ts and (cell["last_outcome_at"] is None or str(ts) > str(cell["last_outcome_at"])):
            cell["last_outcome_at"] = ts
    return by_hyp


def build_hypothesis_scorecard(root: Path) -> dict[str, Any]:
    rows = load_all_outcomes(root)
    cf = _aggregate_hypothesis(rows, "outcome_label_counterfactual")
    ex = _aggregate_hypothesis(rows, "outcome_label_executed")
    hypotheses: list[dict[str, Any]] = []
    for hid in sorted(set(cf.keys()) | set(ex.keys())):
        c = cf.get(hid) or {}
        e = ex.get(hid) or {}
        n_cf = int(c.get("scored") or 0)
        n_ex = int(e.get("scored") or 0)
        hypotheses.append(
            {
                "hypothesis_id": hid,
                "verdicts": sorted((c.get("verdicts") or set()) | (e.get("verdicts") or set())),
                "counterfactual_scored_closes": n_cf,
                "counterfactual_hits": c.get("hits", 0),
                "counterfactual_misses": c.get("misses", 0),
                "counterfactual_skipped": c.get("skipped", 0),
                "counterfactual_hit_rate": round(c["hits"] / n_cf, 4) if n_cf else None,
                "executed_side_scored_closes": n_ex,
                "executed_side_hits": e.get("hits", 0),
                "executed_side_misses": e.get("misses", 0),
                "executed_side_skipped": e.get("skipped", 0),
                "executed_side_hit_rate": round(e["hits"] / n_ex, 4) if n_ex else None,
                "scored_closes": n_cf,
                "hits": c.get("hits", 0),
                "misses": c.get("misses", 0),
                "skipped": c.get("skipped", 0),
                "hit_rate": round(c["hits"] / n_cf, 4) if n_cf else None,
                "last_outcome_at": c.get("last_outcome_at") or e.get("last_outcome_at"),
                "composite_weight_policy": "zero_until_PASS_STATS_and_SURVIVED",
                "primary_metric": "counterfactual_price_horizon",
                "paper_only": True,
            }
        )
    return {
        "schema": SCHEMA_SCORECARD,
        "generated_at": _utc_now(),
        "iso_week": _iso_week(),
        "paper_only": True,
        "outcomes_total": len(rows),
        "hypotheses": hypotheses,
        "honesty_note": (
            "Primary hit_rate is counterfactual vs entry→exit price return on the same horizon, "
            "whether or not the desk traded that direction. Does not prove edge or enable promotion."
        ),
    }


def export_research_hypothesis_scorecard(root: Path) -> dict[str, Any]:
    root = Path(root)
    doc = build_hypothesis_scorecard(root)
    out = root / SCORECARD_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc


def export_weekly_shadow_scorecard_to_m57(root: Path) -> dict[str, Any]:
    """Weekly M57 teaching journal attachment for shadow hypothesis calibration."""
    root = Path(root)
    scorecard = export_research_hypothesis_scorecard(root)
    doc = {
        "schema": SCHEMA_M57_WEEKLY,
        "iso_week": _iso_week(),
        "generated_at": _utc_now(),
        "paper_only": True,
        "scorecard_path": str(SCORECARD_REL.as_posix()).replace("\\", "/"),
        "outcomes_path": str(OUTCOMES_REL.as_posix()).replace("\\", "/"),
        "hypotheses_tracked": len(scorecard.get("hypotheses") or []),
        "outcomes_total": scorecard.get("outcomes_total"),
        "hypotheses": scorecard.get("hypotheses") or [],
        "honesty_note": scorecard.get("honesty_note"),
        "teaching_module_fa": "U-108: کالیبراسیون فرضیه‌های سایهٔ دانشگاه روی افق قیمت واقعی (وزن صفر در composite)",
    }
    out = root / M57_WEEKLY_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        from architecture.learning.teaching_shadow_scorecard_m65 import refresh_teaching_journal_with_shadow_scorecard

        refresh_teaching_journal_with_shadow_scorecard(root, doc)
    except Exception:
        pass
    return doc


def backfill_outcomes_from_log(root: Path) -> int:
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
    export_weekly_shadow_scorecard_to_m57(root)
    return n
