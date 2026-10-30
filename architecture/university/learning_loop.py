"""Closed paper trades become university cases. Weight edits stay shadow.

A hit rate can propose a candidate. The live weight changes only when the
same proposal carries PASS_STATS, SURVIVED_RED_TEAM, a deflated Sharpe above
0.95, and a probability of backtest overfitting below 0.5. Missing either
statistic leaves the proposal in shadow.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from architecture.learning.walk_forward import deflated_sharpe, pbo_cscv, sharpe
from architecture.markets.paper_trade_gates import family_vote_signs

CASES_REL = Path("reports") / "grok" / "PAPER" / "university_cases.jsonl"
PROPOSALS_REL = Path("reports") / "grok" / "PAPER" / "weight_proposals.jsonl"
DSR_MIN = 0.95
PBO_MAX = 0.5
MIN_RESOLVED = 30

_CAUSE_ORDER = ("FEE_DRAG", "BAD_DATA", "BAD_TIMING", "NEWS_TRAP", "REGIME", "WRONG_FAMILY", "UNKNOWN")


def _profitable_sign(side: str, win: bool) -> str | None:
    if side not in ("LONG", "SHORT"):
        return None
    if win:
        return side
    return "SHORT" if side == "LONG" else "LONG"


def family_outcomes(close_row: dict[str, Any]) -> dict[str, list[str]]:
    """Families that voted with the profitable direction, and those that voted against it."""
    brain = close_row.get("entry_brain") if isinstance(close_row.get("entry_brain"), dict) else {}
    signals = brain.get("signals") if isinstance(brain.get("signals"), list) else []
    good = _profitable_sign(str(close_row.get("side") or ""), float(close_row.get("realized_pnl_usd") or 0) > 0)
    right: list[str] = []
    wrong: list[str] = []
    for vote in family_vote_signs(signals):
        sign = vote.get("sign")
        if sign not in ("LONG", "SHORT") or good is None:
            continue
        (right if sign == good else wrong).append(str(vote["family"]))
    return {"right": right, "wrong": wrong}


def loss_cause(close_row: dict[str, Any]) -> str:
    """One pre-registered cause. A win is WIN. A loss with no matching rule is UNKNOWN."""
    pnl = float(close_row.get("realized_pnl_usd") or 0)
    if pnl > 0:
        return "WIN"
    fees = float(close_row.get("fees_usd") or 0)
    if fees > 0 and pnl + fees >= 0:
        return "FEE_DRAG"
    reason = str(close_row.get("reason") or "")
    witness = close_row.get("witness") if isinstance(close_row.get("witness"), dict) else {}
    if reason.startswith("WITNESS") or witness.get("verdict") == "CONFLICT":
        return "BAD_DATA"
    if reason in ("TIME_STOP", "MAX_HOLD"):
        return "BAD_TIMING"
    if reason.startswith("PUMP_NEWS") or "news" in family_outcomes(close_row)["wrong"]:
        return "NEWS_TRAP"
    brain = close_row.get("entry_brain") if isinstance(close_row.get("entry_brain"), dict) else {}
    regime = brain.get("regime") if isinstance(brain.get("regime"), dict) else {}
    mult = regime.get("size_mult")
    if isinstance(mult, (int, float)) and not isinstance(mult, bool) and float(mult) < 1:
        return "REGIME"
    if family_outcomes(close_row)["wrong"]:
        return "WRONG_FAMILY"
    return "UNKNOWN"


def university_case(close_row: dict[str, Any]) -> dict[str, Any]:
    outcomes = family_outcomes(close_row)
    return {
        "schema": "ahos.university_case.v1",
        "paper_only": True,
        "symbol": close_row.get("symbol"),
        "desk": close_row.get("desk"),
        "side": close_row.get("side"),
        "closed_at": close_row.get("closed_at"),
        "reason": close_row.get("reason"),
        "realized_pnl_usd": close_row.get("realized_pnl_usd"),
        "outcome": "WIN" if float(close_row.get("realized_pnl_usd") or 0) > 0 else "LOSS",
        "cause": loss_cause(close_row),
        "families_right": outcomes["right"],
        "families_wrong": outcomes["wrong"],
        "applied_to_live_weights": False,
    }


def append_university_case(root: Path, close_row: dict[str, Any]) -> dict[str, Any]:
    case = university_case(close_row)
    path = Path(root) / CASES_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(case) + "\n")
    return case


def propose_from_scorecard(scorecard: dict[str, Any]) -> list[dict[str, Any]]:
    """Per-desk 4h/24h hit rates become shadow proposals. Nothing here is applied."""
    proposals: list[dict[str, Any]] = []
    by_desk = scorecard.get("by_desk") if isinstance(scorecard.get("by_desk"), dict) else {}
    for desk, families in by_desk.items():
        if not isinstance(families, dict):
            continue
        for family, cell in families.items():
            if not isinstance(cell, dict):
                continue
            day = cell.get("24h") if isinstance(cell.get("24h"), dict) else {}
            four = cell.get("4h") if isinstance(cell.get("4h"), dict) else {}
            resolved = int(day.get("hits") or 0) + int(day.get("misses") or 0)
            rate = day.get("hit_rate")
            candidate = None
            if resolved >= MIN_RESOLVED and isinstance(rate, (int, float)):
                candidate = round(max(0.5, min(1.5, 0.5 + float(rate))), 4)
            proposals.append({
                "schema": "ahos.weight_proposal.v1",
                "paper_only": True,
                "desk": desk,
                "family": family,
                "hit_rate_4h": four.get("hit_rate"),
                "hit_rate_24h": rate,
                "resolved_24h": resolved,
                "candidate_multiplier": candidate,
                "status": "SHADOW",
                "gate": "SHADOW",
                "red_team": None,
                "dsr": None,
                "pbo": None,
                "reason": "INSUFFICIENT_SAMPLE" if resolved < MIN_RESOLVED else "AWAITING_DSR_PBO",
                "applied_to_live_weights": False,
            })
    return proposals


def stats_gate(oos_returns: list[float], trial_returns: list[list[float]]) -> dict[str, Any]:
    """DSR and PBO on the supplied out-of-sample paths. A missing number stays SHADOW."""
    trials = [list(path) for path in trial_returns if path]
    n_trials = len(trials)
    trial_sharpes = [sharpe(path) for path in trials]
    dsr = deflated_sharpe(list(oos_returns), n_trials, trial_sharpes) if oos_returns else None
    width = min((len(path) for path in trials), default=0)
    matrix = [path[:width] for path in trials] if width else []
    pbo = pbo_cscv(matrix) if matrix else None
    passed = dsr is not None and dsr > DSR_MIN and pbo is not None and pbo < PBO_MAX
    return {
        "gate": "PASS_STATS" if passed else "SHADOW",
        "dsr": dsr,
        "pbo": pbo,
        "reason": "DSR_AND_PBO_PASSED" if passed else "DSR_OR_PBO_MISSING_OR_FAILED",
    }


def apply_promoted(weights: dict[str, float], proposal: dict[str, Any]) -> dict[str, float]:
    """Copy weights and edit one key only when every promotion field is present and passing."""
    out = dict(weights)
    signal = proposal.get("signal")
    candidate = proposal.get("candidate_weight")
    dsr = proposal.get("dsr")
    pbo = proposal.get("pbo")
    ok = (
        isinstance(signal, str)
        and signal in out
        and isinstance(candidate, (int, float))
        and not isinstance(candidate, bool)
        and proposal.get("gate") == "PASS_STATS"
        and proposal.get("red_team") == "SURVIVED_RED_TEAM"
        and isinstance(dsr, (int, float))
        and not isinstance(dsr, bool)
        and float(dsr) > DSR_MIN
        and isinstance(pbo, (int, float))
        and not isinstance(pbo, bool)
        and float(pbo) < PBO_MAX
    )
    if ok:
        out[signal] = round(float(candidate), 4)
    return out
