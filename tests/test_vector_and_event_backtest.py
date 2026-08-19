"""Tests for AHOS Vectorized and Event-Driven Backtesting Engines (OSS-004)."""

from __future__ import annotations

import numpy as np
import pytest

from engine.event_backtest import EventDrivenBacktester
from strategy_lab.vector_engine import VectorBacktestEngine


def test_vector_parameter_grid_sweep():
    np.random.seed(42)
    n = 200
    prices = 100.0 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, n)))
    scores = np.random.uniform(30.0, 95.0, n)

    results = VectorBacktestEngine.run_parameter_grid_sweep(
        prices=prices,
        scores=scores,
        score_thresholds=[70.0, 80.0],
        stop_loss_pcts=[0.05, 0.10],
        take_profit_pcts=[0.15, 0.25],
    )

    assert len(results) == 8  # 2 * 2 * 2 combos
    # Ensure all return required fields
    for r in results:
        assert "annualized_sharpe" in r
        assert "max_drawdown_pct" in r
        assert "param_entry_thresh" in r


def test_event_driven_amm_slippage():
    tester = EventDrivenBacktester(initial_capital_usd=1000.0)

    # 1. Buy order with constant-product price impact
    fill_buy, slip_buy = tester.calculate_amm_slippage_price(
        spot_price=10.0,
        trade_usd=1000.0,
        pool_liquidity_usd=10000.0,
        is_buy=True,
    )
    # Price impact should make fill_price higher than spot
    assert fill_buy > 10.0
    assert slip_buy > 0.05

    # 2. Sell order
    fill_sell, slip_sell = tester.calculate_amm_slippage_price(
        spot_price=10.0,
        trade_usd=1000.0,
        pool_liquidity_usd=10000.0,
        is_buy=False,
    )
    assert fill_sell < 10.0


def test_event_driven_causal_simulation():
    tester = EventDrivenBacktester(initial_capital_usd=1000.0)

    # Push sequence of ticks and signals
    tester.push_event(
        10.0,
        "SIGNAL_ENTRY",
        {
            "token_id": "TEST_TOKEN",
            "spot_price": 10.0,
            "pool_liquidity_usd": 50000.0,
        },
    )
    tester.push_event(
        15.0,
        "MARKET_TICK",
        {
            "token_id": "TEST_TOKEN",
            "spot_price": 12.0,
            "pool_liquidity_usd": 50000.0,
        },
    )
    tester.push_event(
        20.0,
        "MARKET_TICK",
        {
            "token_id": "TEST_TOKEN",
            "spot_price": 13.0,
            "pool_liquidity_usd": 50000.0,
        },  # triggers take-profit
    )

    results = tester.run_simulation()

    assert "annualized_sharpe" in results
    assert len(results["trade_log"]) == 1
    trade = results["trade_log"][0]
    assert trade["token_id"] == "TEST_TOKEN"
    assert trade["net_profit_usd"] > 0
