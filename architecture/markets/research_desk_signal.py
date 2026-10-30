"""M57 research overlay: weighted composite only for PASS_STATS + SURVIVED_RED_TEAM.

SHADOW_FORWARD / FORWARD_TEST hypotheses are logged per trade (direction only) with composite weight 0.
PAPER_ONLY — not promotion authority.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from architecture.markets import signal_brain as sb
from architecture.learning.strategy_switch import RED_REL

DESK_TO_PIPELINE = {
    "CRYPTO": "CRYPTO_UNIVERSE_DESK",
    "CRYPTO_FUTURES": "CRYPTO_UNIVERSE_DESK",
    "PB_TOKEN": "CRYPTO_UNIVERSE_DESK",
    "GOLD": "GOLD_DESK",
    "OIL": "OIL_DESK",
    "US_EQUITIES": "US_EQUITIES_DESK",
    "EU_EQUITIES": "EU_EQUITIES_DESK",
    "ASIA_EQUITIES": "ASIA_EQUITIES_DESK",
    "FOREX": "FOREX_DESK",
}

_HYP_DESKS: dict[str, list[str]] = {
    "H14": ["CRYPTO_UNIVERSE_DESK"],
    "H15": ["CRYPTO_UNIVERSE_DESK"],
    "H16": ["US_EQUITIES_DESK"],
    "H17": ["OIL_DESK"],
    "H18": list(DESK_TO_PIPELINE.values()),
    "H19": list(DESK_TO_PIPELINE.values()),
    "H20": list(DESK_TO_PIPELINE.values()),
    "H21": ["CRYPTO_UNIVERSE_DESK"],
    "H22": list(DESK_TO_PIPELINE.values()),
}

_SHADOW_VERDICTS = frozenset({"SHADOW_FORWARD_TEST", "FORWARD_TEST"})

PREDICTIONS_SCHEMA = "ahos.research_predictions.v1"


def _read_switch(root: Path) -> dict[str, Any]:
    path = root / "reports" / "grok" / "PAPER" / "strategy_switch.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"active": {}, "version": 0}


def _hypothesis_from_strategy_id(strategy_id: str) -> str | None:
    for part in str(strategy_id).split("-"):
        if part.startswith("H") and len(part) > 1 and part[1:].isdigit():
            return part
    return None


def _red_team_verdict(root: Path, strategy_id: str) -> str | None:
    try:
        red = json.loads((root / RED_REL).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    row = next((r for r in red.get("reports") or [] if r.get("strategy_id") == strategy_id), None)
    if not isinstance(row, dict):
        return None
    return str(row.get("verdict") or "") or None


def _direction_from_metric(metric: float | None) -> str:
    if metric is None:
        return "UNKNOWN"
    if metric > 0.01:
        return "LONG"
    if metric < -0.01:
        return "SHORT"
    return "NEUTRAL"


def _batch_weighted_overlay(
    root: Path, pipe: str
) -> tuple[float | None, list[str], list[dict[str, Any]]]:
    """Only PASS_STATS + SURVIVED_RED_TEAM affect research_overlay composite score."""
    contrib = 0.0
    weight_sum = 0.0
    keys: list[str] = []
    rows: list[dict[str, Any]] = []
    m28 = root / "reports" / "grok" / "M28"
    if not m28.is_dir():
        return None, keys, rows
    for path in sorted(m28.glob("batch*_research.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for cand in doc.get("candidates") or []:
            if not isinstance(cand, dict) or cand.get("gate") != "PASS_STATS":
                continue
            sid = str(cand.get("strategy_id") or "")
            if _red_team_verdict(root, sid) != "SURVIVED_RED_TEAM":
                continue
            hid = _hypothesis_from_strategy_id(sid)
            if not hid or pipe not in (_HYP_DESKS.get(hid) or []):
                continue
            metric = cand.get("oos_sharpe")
            if metric is None:
                metric = cand.get("deflated_sharpe")
            if metric is None:
                continue
            f = float(metric)
            w = min(1.0, abs(f))
            if w <= 0:
                continue
            weight_sum += w
            contrib += f * w
            keys.append(sid)
            rows.append(
                {
                    "strategy_id": sid,
                    "batch_file": path.name,
                    "metric": round(f, 4),
                    "gate": "PASS_STATS",
                    "red_team": "SURVIVED_RED_TEAM",
                    "composite_weight_applied": True,
                    "paper_only": True,
                }
            )
    if weight_sum <= 0:
        return None, keys, rows
    score = max(-1.0, min(1.0, contrib / weight_sum))
    return score, keys, rows


def _registry_shadow_predictions(root: Path, pipe: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    path = root / "strategy_lab" / "registry.json"
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return out
    candidates = doc.get("candidates") if isinstance(doc.get("candidates"), dict) else {}
    for hid, row in candidates.items():
        if not isinstance(row, dict):
            continue
        hid_s = str(hid)
        if pipe not in (_HYP_DESKS.get(hid_s) or []):
            continue
        verdict = str(row.get("verdict") or "")
        if verdict not in _SHADOW_VERDICTS:
            continue
        detail = row.get("detail") if isinstance(row.get("detail"), dict) else {}
        metrics: list[float] = []
        for v in detail.values():
            if isinstance(v, dict) and v.get("oos_sharpe") is not None:
                metrics.append(float(v["oos_sharpe"]))
        mean = sum(metrics) / len(metrics) if metrics else None
        out.append(
            {
                "hypothesis_id": hid_s,
                "verdict": verdict,
                "predicted_direction": _direction_from_metric(mean),
                "predicted_score": round(mean, 4) if mean is not None else None,
                "composite_weight": 0.0,
                "outcome_scoring": "deferred_vs_realized_trade",
                "evidence": row.get("evidence"),
                "note": detail.get("reason") if mean is None and isinstance(detail, dict) else None,
                "paper_only": True,
            }
        )
    return out


def research_predictions_for_trade(root: Path, desk: str) -> dict[str, Any]:
    """Shadow/forward hypotheses logged on each trade; zero composite weight."""
    pipe = DESK_TO_PIPELINE.get(desk)
    if not pipe:
        return {"schema": PREDICTIONS_SCHEMA, "desk": desk, "predictions": [], "paper_only": True}
    preds = _registry_shadow_predictions(root, pipe)
    sw = _read_switch(root)
    for key, w in (sw.get("active") or {}).items():
        if not isinstance(w, (int, float)):
            continue
        raw = str(key)
        hid = raw.split(":", 1)[0] if ":" in raw else raw
        if not hid.startswith("H") or pipe not in (_HYP_DESKS.get(hid) or []):
            continue
        preds.append(
            {
                "hypothesis_id": hid,
                "verdict": "STRATEGY_SWITCH_ACTIVE",
                "predicted_direction": _direction_from_metric(float(w)),
                "predicted_score": round(float(w), 4),
                "composite_weight": 0.0,
                "outcome_scoring": "deferred_vs_realized_trade",
                "switch_key": raw,
                "paper_only": True,
            }
        )
    return {
        "schema": PREDICTIONS_SCHEMA,
        "desk": desk,
        "pipeline_desk": pipe,
        "predictions": preds,
        "paper_only": True,
        "honesty_note": "Shadow/forward rows never change composite or notional; scored later against outcomes.",
    }


def _finite_metric(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if not math.isfinite(number):
        return None
    return number


def advisory_vote_score(predictions: list[dict[str, Any]]) -> float | None:
    """Mean of existing numeric predicted scores, clamped to [-1, 1].

    Direction-only rows (predicted_score None) are skipped. This never invents a score.
    """
    nums: list[float] = []
    for row in predictions:
        if not isinstance(row, dict):
            continue
        metric = _finite_metric(row.get("predicted_score"))
        if metric is None:
            continue
        nums.append(metric)
    if not nums:
        return None
    mean = sum(nums) / len(nums)
    return round(max(-1.0, min(1.0, mean)), 4)


def research_overlay_for_desk(root: Path, desk: str) -> dict[str, Any]:
    pipe = DESK_TO_PIPELINE.get(desk)
    if not pipe:
        return sb._sig("research_overlay", None, {"desk": desk, "reason": "unknown_desk"}, "research_overlay", "M57")
    score, batch_keys, batch_rows = _batch_weighted_overlay(root, pipe)
    shadow = _registry_shadow_predictions(root, pipe)
    sw = _read_switch(root)
    preds = research_predictions_for_trade(root, desk).get("predictions") or []
    promoted = score is not None
    advisory = None if promoted else advisory_vote_score(preds)
    return sb._sig(
        "research_overlay",
        score,
        {
            "pipeline_desk": pipe,
            "switch_version": sw.get("version"),
            "weighted_sources": ["batch_pass_stats_survived"] if batch_rows else [],
            "batch_pass_stats_keys": batch_keys,
            "batch_pass_stats": batch_rows[:8],
            "shadow_forward_logged": [p["hypothesis_id"] for p in shadow],
            "advisory_vote_score": advisory,
            "advisory_sources": [p.get("hypothesis_id") for p in preds if _finite_metric(p.get("predicted_score")) is not None] if not promoted else [],
            "vote_authority": "PASS_STATS+SURVIVED_RED_TEAM" if promoted else ("ADVISORY_ONLY" if advisory is not None else "UNAVAILABLE"),
            "composite_weight": 0.05 if promoted else 0.0,
            "paper_only": True,
            "not_promotion": True,
        },
        "batch_pass_stats+red_team" if promoted else "advisory_shadow_or_switch",
        "M57",
    )


def append_research_signal(root: Path, desk: str, signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    overlay = research_overlay_for_desk(root, desk)
    return signals + [overlay]
