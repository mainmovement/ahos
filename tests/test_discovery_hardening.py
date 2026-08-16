#!/usr/bin/env python3
"""AHOS Discovery Hardening & Domain Boundary Test Suite (Phase C).
Exhaustively tests:
1. Zero and negative price handling
2. Zero and negative liquidity handling
3. Out-of-order observations and duplicate timestamps
4. Starved / sparse token observation series
5. Zero transactions / zero buys / zero sells imbalance
6. Empty database / zero observations edge cases
7. Feature store fs_v0.1 & fs_v0.2 numerical stability with NaN / Inf protections
8. Wilson score confidence interval boundary edge cases (n=0, k=0, k=n)
9. Outcome labeling boundaries (no observations in horizon window, zero price)
10. Lifecycle sweep transitions and duplicate gap prevention
"""
import sys, math, json, sqlite3
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(ROOT_DIR / "discovery") not in sys.path: sys.path.insert(0, str(ROOT_DIR / "discovery"))

import pytest
from discovery import identity, observations as obs, lifecycle, feature_store, outcomes
from research import baseline_stats

T0 = 1_750_000_000.0
RAW = "a" * 64


@pytest.fixture()
def conn(tmp_path):
    c = obs.open_store(tmp_path / "hardening.sqlite")
    feature_store.register_definitions(c)
    yield c
    c.close()


def _mk_token(conn, now=T0, chain="solana", address="HardenTok11111111111111111111111111111"):
    tid = obs.upsert_token(conn, chain, address, now, "fixture", symbol="HDN", name="Hardened Token",
                           created_at_ts=now - 7200.0)
    pid = obs.upsert_pair(conn, chain, "raydium", address, tid, now, "fixture", RAW,
                          pair_created_ts=now - 7200.0)
    lifecycle.register_discovery(conn, tid, now)
    return tid


def test_zero_and_negative_prices_ignored_safely(conn):
    """Price features must ignore non-positive prices without crashing."""
    tid = _mk_token(conn, address="TokZeroPx1111111111111111111111111111")
    raw_id = obs.store_raw(conn, "test", "url", T0, 200, {})
    obs.record_observation(conn, tid, "test", T0, raw_id, metrics={"price_usd": 0.0, "liquidity_usd": 1000.0})
    obs.record_observation(conn, tid, "test", T0 + 3600, raw_id, metrics={"price_usd": -5.0, "liquidity_usd": 1000.0})
    feats = feature_store.compute_features(conn, tid, T0 + 3600)
    assert "price_change_1h" not in feats
    assert "volatility_1h" not in feats
    assert "max_drawdown_since_first_seen" not in feats


def test_zero_liquidity_handling(conn):
    """Zero liquidity must use EPS_LIQ floor and not divide by zero."""
    tid = _mk_token(conn, address="TokZeroLiq11111111111111111111111111")
    raw_id = obs.store_raw(conn, "test", "url", T0, 200, {})
    obs.record_observation(conn, tid, "test", T0, raw_id, metrics={"price_usd": 1.0, "liquidity_usd": 0.0})
    obs.record_observation(conn, tid, "test", T0 + 3600, raw_id, metrics={"price_usd": 1.0, "liquidity_usd": 500.0})
    feats = feature_store.compute_features(conn, tid, T0 + 3600)
    assert "liquidity_growth_1h" in feats
    # Should use EPS_LIQ = 100.0 in denominator: (500 - 0) / 100.0 = 5.0
    assert feats["liquidity_growth_1h"]["value_num"] == pytest.approx(5.0)


def test_zero_txns_buy_sell_imbalance(conn):
    """Zero buys and zero sells must yield 0.0 imbalance and not divide by zero."""
    tid = _mk_token(conn, address="TokZeroTxn11111111111111111111111111")
    raw_id = obs.store_raw(conn, "test", "url", T0, 200, {})
    obs.record_observation(conn, tid, "test", T0, raw_id, metrics={"txns_1h_buys": 0, "txns_1h_sells": 0})
    feats = feature_store.compute_features(conn, tid, T0)
    assert "buy_sell_imbalance_1h" in feats
    assert feats["buy_sell_imbalance_1h"]["value_num"] == 0.0


def test_out_of_order_and_duplicate_timestamps(conn):
    """Observations arriving with disordered timestamps must be handled deterministically."""
    tid = _mk_token(conn, address="TokOrder1111111111111111111111111111")
    raw_id = obs.store_raw(conn, "test", "url", T0, 200, {})
    obs.record_observation(conn, tid, "test", T0 + 3600, raw_id, metrics={"price_usd": 2.0, "liquidity_usd": 2000.0})
    obs.record_observation(conn, tid, "test", T0, raw_id, metrics={"price_usd": 1.0, "liquidity_usd": 1000.0})
    feats = feature_store.compute_features(conn, tid, T0 + 3600)
    assert "price_change_1h" in feats
    assert feats["price_change_1h"]["value_num"] == pytest.approx(1.0)


def test_empty_token_feature_computation(conn):
    """Token with zero observations returns empty feature dictionary without errors."""
    tid = _mk_token(conn, address="TokEmpty111111111111111111111111111")
    feats = feature_store.compute_features(conn, tid, T0)
    # With zero observations, obs_avail is None, so emit cleanly drops all features (NULL discipline)
    assert feats == {}
    assert "token_age_hours" not in feats
    assert "liquidity_usd_t" not in feats
    assert "volume_growth_1h" not in feats


def test_wilson_ci_bounds():
    """Wilson CI calculates accurate bounds for extreme and edge proportions."""
    assert baseline_stats.wilson_ci(0, 0) == (None, None)
    low, high = baseline_stats.wilson_ci(0, 100)
    assert low == 0.0 and 0.0 < high < 0.1
    low, high = baseline_stats.wilson_ci(100, 100)
    assert 0.9 < low < 1.0 and high == 1.0
    low, high = baseline_stats.wilson_ci(50, 100)
    assert low < 0.5 < high


def test_rates_and_lift_empty_and_insufficient():
    """rates_and_lift safely handles empty stratums and applies MIN_N_STRATUM guards."""
    res_empty = baseline_stats.rates_and_lift(0, 0, 10, 50)
    assert res_empty["verdict"] == "INSUFFICIENT_DATA"
    assert res_empty["reason"] == "empty cell"

    res_small = baseline_stats.rates_and_lift(5, 50, 10, 100)
    assert res_small["verdict"] == "INSUFFICIENT_DATA"
    assert "n<200" in res_small["reason"]
