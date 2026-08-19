"""Tests for AHOS QuantStats-style Institutional Metrics Engine (OSS-003)."""

from __future__ import annotations

import numpy as np
import pytest

from research.quant_metrics import QuantMetricsEngine


def test_sharpe_and_sortino_positive_returns():
    # Synthetic steadily rising returns with low volatility
    equity = [100.0, 102.0, 104.0, 103.5, 106.0, 108.0, 107.5, 110.0, 112.0]
    returns = QuantMetricsEngine.returns_from_equity(equity)
    sharpe = QuantMetricsEngine.sharpe_ratio(returns)
    sortino = QuantMetricsEngine.sortino_ratio(returns)

    assert sharpe > 2.0
    assert sortino > sharpe  # Sortino should be higher since downside volatility is low


def test_max_drawdown_and_duration():
    # Synthetic equity curve with a known 20% drawdown
    equity = [100.0, 120.0, 96.0, 100.0, 130.0]  # Peak 120 -> trough 96 = -20%
    max_dd, duration = QuantMetricsEngine.max_drawdown_and_duration(equity)

    assert pytest.approx(max_dd, 0.01) == -0.20
    assert duration >= 1


def test_var_and_cvar():
    np.random.seed(42)
    # Standard normal returns
    returns = np.random.normal(0.001, 0.02, 1000)
    var95, cvar95 = QuantMetricsEngine.var_cvar(returns, alpha=0.95)

    assert var95 > 0.0
    assert cvar95 >= var95  # CVaR is always greater than or equal to VaR


def test_win_rate_and_kelly():
    trades = [0.10, -0.05, 0.08, -0.04, 0.12, -0.05, 0.06]
    win_rate, payoff, pf = QuantMetricsEngine.win_rate_payoff_profit_factor(trades)
    kelly = QuantMetricsEngine.kelly_fraction(win_rate, payoff)

    assert win_rate > 0.50
    assert payoff > 1.0
    assert pf > 1.5
    assert kelly > 0.0


def test_full_tearsheet_generation():
    equity = np.cumprod(1.0 + np.random.normal(0.002, 0.01, 200)) * 1000.0
    trades = [0.05, -0.02, 0.03, -0.01, 0.04, 0.02, -0.02]
    sheet = QuantMetricsEngine.generate_tearsheet(equity, trades)

    required_keys = [
        "initial_equity",
        "final_equity",
        "total_return_pct",
        "annualized_sharpe",
        "annualized_sortino",
        "calmar_ratio",
        "max_drawdown_pct",
        "var_95_pct",
        "cvar_95_pct",
        "profit_factor",
        "kelly_fraction",
    ]
    for k in required_keys:
        assert k in sheet
