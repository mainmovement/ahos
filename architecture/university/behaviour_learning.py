"""Weekly learning reports. None of them write a live weight. PAPER_ONLY.

Agents answer a held-out case from the fields they are allowed to see.
A decayed hit rate proposes a shadow multiplier. Calibration uses the
existing log-odds rescaling and keeps it off the entry path unless the
out-of-sample Brier score improves, and even then it is not applied.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from architecture.learning.calibration import brier_score, log_odds_recalibrate
from architecture.university.learning_loop import family_outcomes, loss_cause

EXAM_REL = Path("reports") / "grok" / "PAPER" / "weekly_agent_exam.json"
RELIABILITY_REL = Path("reports") / "grok" / "PAPER" / "reliability_shadow.json"
CALIBRATION_REL = Path("reports") / "grok" / "PAPER" / "calibration_weekly.json"
INTELLIGENCE_REL = Path("reports") / "grok" / "PAPER" / "intelligence_metric.json"
DECAY = 0.97
MIN_RELIABILITY_N = 30
ALPHAS = (0.5, 0.75, 1.0, 1.25)

# What each agent may use. AG-18 sees only earlier cases on the same desk.
AGENT_SCOPE = ("AG-33", "AG-04", "AG-08", "AG-09", "AG-19", "AG-18")


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write(root: Path, rel: Path, doc: dict[str, Any]) -> dict[str, Any]:
    path = Path(root) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    return doc


def _answer(agent: str, row: dict[str, Any], prior: list[dict[str, Any]]) -> str:
    cause_row = row
    if agent == "AG-33":
        return "NEWS_TRAP" if "news" in family_outcomes(cause_row)["wrong"] else "ABSTAIN"
    if agent == "AG-04":
        others = [name for name in family_outcomes(cause_row)["wrong"] if name != "news"]
        return "WRONG_FAMILY" if others else "ABSTAIN"
    if agent == "AG-08":
        pnl = float(row.get("realized_pnl_usd") or 0)
        fees = float(row.get("fees_usd") or 0)
        if pnl <= 0 and fees > 0 and pnl + fees >= 0:
            return "FEE_DRAG"
        brain = row.get("entry_brain") if isinstance(row.get("entry_brain"), dict) else {}
        regime = brain.get("regime") if isinstance(brain.get("regime"), dict) else {}
        mult = regime.get("size_mult")
        if isinstance(mult, (int, float)) and not isinstance(mult, bool) and float(mult) < 1 and pnl <= 0:
            return "REGIME"
        return "ABSTAIN"
    if agent == "AG-09":
        reason = str(row.get("reason") or "")
        witness = row.get("witness") if isinstance(row.get("witness"), dict) else {}
        if reason.startswith("WITNESS") or witness.get("verdict") == "CONFLICT":
            return "BAD_DATA"
        return "ABSTAIN"
    if agent == "AG-19":
        if str(row.get("reason") or "") in ("TIME_STOP", "MAX_HOLD"):
            return "BAD_TIMING"
        return "ABSTAIN"
    if agent == "AG-18":
        desk = row.get("desk")
        earlier = [loss_cause(item) for item in prior if item.get("desk") == desk and float(item.get("realized_pnl_usd") or 0) <= 0]
        earlier = [item for item in earlier if item != "WIN"]
        if not earlier:
            return "ABSTAIN"
        return max(set(earlier), key=earlier.count)
    return "ABSTAIN"


def weekly_exam(closes: list[dict[str, Any]]) -> dict[str, Any]:
    """Score each agent on losses. The current row's cause is not an input to AG-18."""
    ordered = sorted(closes, key=lambda row: str(row.get("closed_at") or ""))
    losses = [row for row in ordered if float(row.get("realized_pnl_usd") or 0) <= 0]
    scores = []
    for agent in AGENT_SCOPE:
        correct = 0
        for index, row in enumerate(losses):
            predicted = _answer(agent, row, losses[:index])
            if predicted == loss_cause(row):
                correct += 1
        n = len(losses)
        scores.append({
            "agent_id": agent,
            "n": n,
            "correct": correct,
            "accuracy": round(correct / n, 4) if n else None,
            "applied_to_live_weights": False,
        })
    return {
        "schema": "ahos.weekly_agent_exam.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "loss_cases": len(losses),
        "scores": scores,
        "decides": False,
        "applied_to_live_weights": False,
    }


def _regime_name(row: dict[str, Any]) -> str:
    brain = row.get("entry_brain") if isinstance(row.get("entry_brain"), dict) else {}
    regime = brain.get("regime") if isinstance(brain.get("regime"), dict) else {}
    name = regime.get("regime") or regime.get("name")
    return str(name) if name else "UNKNOWN"


def reliability_shadow(closes: list[dict[str, Any]]) -> dict[str, Any]:
    """Beta counts with decay, per desk, regime, and family. The multiplier stays shadow."""
    cells: dict[tuple[str, str, str], list[float]] = {}
    counts: dict[tuple[str, str, str], int] = {}
    ordered = sorted(closes, key=lambda row: str(row.get("closed_at") or ""))
    for row in ordered:
        outcomes = family_outcomes(row)
        desk = str(row.get("desk") or "UNKNOWN")
        regime = _regime_name(row)
        seen = set(outcomes["right"]) | set(outcomes["wrong"])
        for family in seen:
            key = (desk, regime, family)
            alpha, beta = cells.get(key, [1.0, 1.0])
            hit = family in outcomes["right"]
            cells[key] = [DECAY * alpha + (1.0 if hit else 0.0), DECAY * beta + (0.0 if hit else 1.0)]
            counts[key] = counts.get(key, 0) + 1
    rows = []
    for key, (alpha, beta) in sorted(cells.items()):
        n = counts[key]
        mean = alpha / (alpha + beta) if alpha + beta else None
        candidate = None
        if n >= MIN_RELIABILITY_N and mean is not None:
            candidate = round(max(0.5, min(1.5, 0.5 + mean)), 4)
        rows.append({
            "desk": key[0],
            "regime": key[1],
            "family": key[2],
            "n": n,
            "posterior_mean": None if mean is None else round(mean, 4),
            "candidate_multiplier": candidate,
            "status": "SHADOW",
            "reason": "INSUFFICIENT_SAMPLE" if n < MIN_RELIABILITY_N else "AWAITING_DSR_PBO",
            "dsr": None,
            "pbo": None,
            "red_team": None,
            "applied_to_live_weights": False,
        })
    return {
        "schema": "ahos.reliability_shadow.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "decay": DECAY,
        "rows": rows,
        "decides": False,
        "applied_to_live_weights": False,
    }


def _confidence(row: dict[str, Any]) -> float | None:
    brain = row.get("entry_brain") if isinstance(row.get("entry_brain"), dict) else {}
    raw = brain.get("composite")
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raw = row.get("exit_composite")
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return None
    return max(0.0, min(1.0, abs(float(raw))))


def calibration_weekly(closes: list[dict[str, Any]]) -> dict[str, Any]:
    """Brier and a reliability curve per desk. Recalibration is kept if the last 40 percent improves."""
    by_desk: dict[str, dict[str, Any]] = {}
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in sorted(closes, key=lambda item: str(item.get("closed_at") or "")):
        prob = _confidence(row)
        if prob is None:
            continue
        grouped.setdefault(str(row.get("desk") or "UNKNOWN"), []).append(row)
    for desk, rows in grouped.items():
        probs = [float(_confidence(row)) for row in rows]
        outcomes = [1.0 if float(row.get("realized_pnl_usd") or 0) > 0 else 0.0 for row in rows]
        bins = []
        for lo in (0.0, 0.2, 0.4, 0.6, 0.8):
            chosen = [(p, y) for p, y in zip(probs, outcomes) if lo <= p < lo + 0.2 or (lo == 0.8 and p == 1.0)]
            if lo == 0.8:
                chosen = [(p, y) for p, y in zip(probs, outcomes) if p >= 0.8]
            else:
                chosen = [(p, y) for p, y in zip(probs, outcomes) if lo <= p < lo + 0.2]
            bins.append({
                "lo": lo,
                "n": len(chosen),
                "mean_confidence": round(sum(p for p, _y in chosen) / len(chosen), 4) if chosen else None,
                "hit_rate": round(sum(y for _p, y in chosen) / len(chosen), 4) if chosen else None,
            })
        split = int(len(probs) * 0.6)
        train_p, train_y = probs[:split], outcomes[:split]
        test_p, test_y = probs[split:], outcomes[split:]
        base = brier_score(test_p, test_y)
        chosen_alpha = 1.0
        best_train = brier_score(train_p, train_y)
        if train_p and best_train is not None:
            for alpha in ALPHAS:
                train_brier = brier_score(log_odds_recalibrate(train_p, alpha), train_y)
                if train_brier is not None and train_brier < best_train:
                    best_train = train_brier
                    chosen_alpha = alpha
        held = brier_score(log_odds_recalibrate(test_p, chosen_alpha), test_y) if test_p else None
        improved = held is not None and base is not None and held < base and chosen_alpha != 1.0 and len(test_p) >= 8
        if len(test_p) < 8:
            cal_status = "INSUFFICIENT_HOLDOUT"
        elif improved:
            cal_status = "OOS_IMPROVED_NOT_APPLIED"
        else:
            cal_status = "NO_OOS_IMPROVEMENT"
        by_desk[desk] = {
            "n": len(probs),
            "brier": None if brier_score(probs, outcomes) is None else round(float(brier_score(probs, outcomes)), 4),
            "reliability": bins,
            "oos_brier": None if base is None else round(base, 4),
            "oos_brier_recalibrated": None if held is None else round(held, 4),
            "alpha": chosen_alpha if improved else 1.0,
            "status": cal_status,
            "applied_to_entry": False,
        }
    return {
        "schema": "ahos.calibration_weekly.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "by_desk": by_desk,
        "decides": False,
        "applied_to_live_weights": False,
    }


def _week(row: dict[str, Any]) -> str:
    raw = str(row.get("closed_at") or "")
    try:
        moment = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return ""
    year, week, _day = moment.isocalendar()
    return f"{year}-W{week:02d}"


def _week_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    pnl = [float(row.get("realized_pnl_usd") or 0) for row in rows]
    n = len(pnl)
    wins = [x for x in pnl if x > 0]
    losses = [x for x in pnl if x <= 0]
    explained = sum(1 for row in rows if isinstance(row.get("kian_explain_fa"), str) and row["kian_explain_fa"].strip())
    probs, outcomes = [], []
    for row in rows:
        prob = _confidence(row)
        if prob is None:
            continue
        probs.append(prob)
        outcomes.append(1.0 if float(row.get("realized_pnl_usd") or 0) > 0 else 0.0)
    brier = brier_score(probs, outcomes)
    return {
        "n": n,
        "win_rate": round(len(wins) / n, 4) if n else None,
        "profit_factor": round(sum(wins) / -sum(losses), 4) if losses and sum(losses) < 0 else None,
        "expectancy_usd": round(sum(pnl) / n, 4) if n else None,
        "brier": None if brier is None else round(brier, 4),
        "explained_pct": round(explained / n, 4) if n else None,
    }


def intelligence_metric(closes: list[dict[str, Any]]) -> dict[str, Any]:
    """Week over week. A missing prior week is not a rise. A lower Brier is the better calibration."""
    buckets: dict[str, list[dict[str, Any]]] = {}
    for row in closes:
        key = _week(row)
        if key:
            buckets.setdefault(key, []).append(row)
    weeks = sorted(buckets)
    series = [{"week": key, **_week_metrics(buckets[key])} for key in weeks]
    status = "NO_PRIOR_WEEK"
    reasons: list[str] = []
    if len(series) >= 2:
        prev, cur = series[-2], series[-1]
        if prev["n"] < 5 or cur["n"] < 5:
            status = "INSUFFICIENT_SAMPLE"
            reasons.append(f"weeks need at least 5 closes; {prev['week']} has {prev['n']}, {cur['week']} has {cur['n']}")
        else:
            higher = ("win_rate", "profit_factor", "expectancy_usd", "explained_pct")
            for name in higher:
                left, right = prev.get(name), cur.get(name)
                if left is None or right is None:
                    reasons.append(f"{name} is missing on {prev['week']} or {cur['week']}")
                elif float(right) < float(left):
                    reasons.append(f"{name} {prev['week']}={left} {cur['week']}={right}")
            if prev.get("brier") is not None and cur.get("brier") is not None and float(cur["brier"]) > float(prev["brier"]):
                reasons.append(f"brier {prev['week']}={prev['brier']} {cur['week']}={cur['brier']}")
            status = "TREND_UP" if not reasons else "TREND_NOT_UP"
    return {
        "schema": "ahos.intelligence_metric.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "weeks": series[-8:],
        "status": status,
        "reasons": reasons,
        "decides": False,
        "applied_to_live_weights": False,
    }


def publish_learning(root: Path, closes: list[dict[str, Any]]) -> dict[str, Any]:
    exam = _write(root, EXAM_REL, weekly_exam(closes))
    reliability = _write(root, RELIABILITY_REL, reliability_shadow(closes))
    calibration = _write(root, CALIBRATION_REL, calibration_weekly(closes))
    metric = _write(root, INTELLIGENCE_REL, intelligence_metric(closes))
    return {
        "exam_agents": len(exam["scores"]),
        "reliability_rows": len(reliability["rows"]),
        "calibration_desks": len(calibration["by_desk"]),
        "intelligence_status": metric["status"],
        "applied_to_live_weights": False,
    }
