"""M56 Arena Skill Multi-Strategy Paper Tournament.
Evaluates competing paper strategies (Trend-Following, Mean-Reversion, Regime-HMM, Multi-TF Confluence)
on out-of-sample / replay returns using Deflated Sharpe Ratio (DSR), Max Drawdown, and Brier calibration.
Strictly PAPER_ONLY = True and auto_promote = False (winning a paper tournament never promotes to live).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

PAPER_ONLY: bool = True
AUTO_PROMOTE: bool = False


@dataclass(frozen=True, slots=True)
class StrategyScore:
    strategy_id: str
    title: str
    family: str
    sample_trades: int
    raw_sharpe: float
    deflated_sharpe: float
    max_drawdown_pct: float
    brier_score: float
    win_rate_pct: float
    composite_rank_score: float
    eligible_for_shadow: bool
    paper_only: bool = True
    auto_promote: bool = False


def compute_sharpe_and_dsr(returns: Sequence[float], *, num_trials: int = 4) -> tuple[float, float]:
    """Compute annualized Sharpe and Deflated Sharpe Ratio (haircut for multiple testing)."""
    n = len(returns)
    if n < 2:
        return 0.0, 0.0
    mean_r = sum(returns) / n
    var_r = sum((r - mean_r) ** 2 for r in returns) / (n - 1)
    std_r = math.sqrt(var_r) if var_r > 1e-12 else 0.0
    if std_r <= 0.0:
        return 0.0, 0.0
    raw_sr = (mean_r / std_r) * math.sqrt(252.0)
    # Multiple-testing haircut proportional to sqrt(2 * ln(num_trials))
    haircut = math.sqrt(2.0 * math.log(max(2, num_trials))) * 0.35
    dsr = raw_sr - haircut
    return round(raw_sr, 4), round(dsr, 4)


def compute_max_drawdown_pct(returns: Sequence[float]) -> float:
    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        equity *= 1.0 + float(r)
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak * 100.0 if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
    return round(max_dd, 4)


def compute_brier(probs: Sequence[float], outcomes: Sequence[int]) -> float:
    if not probs or len(probs) != len(outcomes):
        return 0.25
    total = sum((float(p) - float(o)) ** 2 for p, o in zip(probs, outcomes))
    return round(total / len(probs), 4)


def default_tournament_strategies() -> list[dict[str, Any]]:
    return [
        {
            "strategy_id": "strat-regime-hmm-v2",
            "title": "Forward-Filtered Regime HMM + ATR Stop (M24)",
            "family": "Regime-HMM",
            "returns": [0.0042, 0.0031, -0.0015, 0.0050, 0.0028, -0.0011, 0.0039, 0.0044, -0.0009, 0.0036, 0.0029, 0.0041],
            "probs": [0.68, 0.64, 0.42, 0.72, 0.61, 0.39, 0.66, 0.70, 0.45, 0.65, 0.62, 0.69],
            "outcomes": [1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1],
        },
        {
            "strategy_id": "strat-multi-tf-confluence",
            "title": "Multi-Timeframe Confluence (H4/H1/M15 + Two-Source Filter)",
            "family": "Multi-TF Confluence",
            "returns": [0.0035, 0.0022, -0.0018, 0.0041, 0.0019, -0.0014, 0.0030, 0.0033, -0.0012, 0.0027, 0.0024, 0.0031],
            "probs": [0.63, 0.59, 0.44, 0.67, 0.58, 0.41, 0.62, 0.64, 0.47, 0.60, 0.59, 0.63],
            "outcomes": [1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1],
        },
        {
            "strategy_id": "strat-trend-donchian-ema",
            "title": "Donchian Breakout + EMA(50/200) Trend Follower",
            "family": "Trend-Following",
            "returns": [0.0060, -0.0032, -0.0028, 0.0075, 0.0012, -0.0025, 0.0055, -0.0019, 0.0048, 0.0015, -0.0021, 0.0052],
            "probs": [0.61, 0.52, 0.48, 0.65, 0.55, 0.46, 0.60, 0.51, 0.59, 0.54, 0.49, 0.62],
            "outcomes": [1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1],
        },
        {
            "strategy_id": "strat-mean-reversion-bb",
            "title": "Bollinger-RSI Mean Reversion (Range Regime Only)",
            "family": "Mean-Reversion",
            "returns": [0.0021, 0.0018, -0.0045, 0.0024, -0.0038, 0.0019, 0.0022, -0.0031, 0.0017, 0.0020, -0.0029, 0.0015],
            "probs": [0.57, 0.56, 0.58, 0.59, 0.54, 0.55, 0.58, 0.52, 0.56, 0.57, 0.53, 0.55],
            "outcomes": [1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1],
        },
    ]


def run_strategy_tournament(
    strategies: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run the M56 paper strategy tournament and rank contenders without auto-promotion."""
    rows = strategies if strategies is not None else default_tournament_strategies()
    num_trials = max(2, len(rows))
    scored: list[StrategyScore] = []

    for item in rows:
        sid = str(item.get("strategy_id") or "unknown")
        title = str(item.get("title") or sid)
        family = str(item.get("family") or "quant")
        rets = [float(x) for x in (item.get("returns") or ())]
        probs = [float(x) for x in (item.get("probs") or ())]
        outcomes = [int(x) for x in (item.get("outcomes") or ())]

        raw_sr, dsr = compute_sharpe_and_dsr(rets, num_trials=num_trials)
        mdd = compute_max_drawdown_pct(rets)
        brier = compute_brier(probs, outcomes)
        wins = sum(1 for r in rets if r > 0)
        win_rate = round((wins / len(rets)) * 100.0, 2) if rets else 0.0

        # Composite score rewards high DSR, low drawdown, and low Brier calibration error
        composite = round(dsr * 10.0 - mdd * 2.5 + (0.25 - brier) * 40.0, 4)
        eligible = dsr > 1.0 and mdd <= 5.0 and brier <= 0.22

        scored.append(
            StrategyScore(
                strategy_id=sid,
                title=title,
                family=family,
                sample_trades=len(rets),
                raw_sharpe=raw_sr,
                deflated_sharpe=dsr,
                max_drawdown_pct=mdd,
                brier_score=brier,
                win_rate_pct=win_rate,
                composite_rank_score=composite,
                eligible_for_shadow=eligible,
                paper_only=True,
                auto_promote=False,
            )
        )

    scored.sort(key=lambda s: s.composite_rank_score, reverse=True)
    leader = scored[0] if scored else None

    return {
        "schema": "ahos.strategy_tournament.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "execution_mode": "PAPER_ONLY",
        "real_trading": False,
        "auto_promote": False,
        "contenders_count": len(scored),
        "leader_id": leader.strategy_id if leader else None,
        "leader_title": leader.title if leader else None,
        "leader_dsr": leader.deflated_sharpe if leader else None,
        "leader_brier": leader.brier_score if leader else None,
        "leaderboard": [
            {
                "rank": idx,
                "strategy_id": s.strategy_id,
                "title": s.title,
                "family": s.family,
                "sample_trades": s.sample_trades,
                "raw_sharpe": s.raw_sharpe,
                "deflated_sharpe": s.deflated_sharpe,
                "max_drawdown_pct": s.max_drawdown_pct,
                "brier_score": s.brier_score,
                "win_rate_pct": s.win_rate_pct,
                "composite_rank_score": s.composite_rank_score,
                "eligible_for_shadow": s.eligible_for_shadow,
                "paper_only": s.paper_only,
                "auto_promote": s.auto_promote,
            }
            for idx, s in enumerate(scored, start=1)
        ],
    }
