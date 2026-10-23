"""Tests for M56 Arena Skill Multi-Strategy Paper Tournament."""
from __future__ import annotations

from architecture.learning.strategy_tournament import (
    AUTO_PROMOTE,
    PAPER_ONLY,
    compute_max_drawdown_pct,
    compute_sharpe_and_dsr,
    run_strategy_tournament,
)


def test_m56_tournament_ranks_strategies_without_auto_promotion() -> None:
    assert PAPER_ONLY is True
    assert AUTO_PROMOTE is False
    res = run_strategy_tournament()
    assert res["paper_only"] is True
    assert res["auto_promote"] is False
    assert res["contenders_count"] == 4
    assert res["leader_id"] == "strat-regime-hmm-v2"
    assert res["leader_dsr"] > 1.0
    board = res["leaderboard"]
    assert board[0]["rank"] == 1
    assert all(row["auto_promote"] is False and row["paper_only"] is True for row in board)


def test_dsr_haircut_and_max_drawdown_math() -> None:
    raw_sr, dsr = compute_sharpe_and_dsr([0.01, 0.008, -0.002, 0.011, 0.009, 0.007], num_trials=6)
    assert raw_sr > dsr
    dd = compute_max_drawdown_pct([0.10, -0.05, -0.05, 0.02])
    assert dd > 9.0
