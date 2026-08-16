#!/usr/bin/env python3
"""Tests for feature_store edge cases and domain boundaries (D-FS-01 hardening).
Enforces:
1. volume_1h > 0 / normal
2. volume_1h = 0 (zero latest volume with non-zero past volume) -> D-FS-01 reproduction
3. previous volume = 0 (zero past volume with non-zero latest volume)
4. previous and latest volume = 0
5. negative/invalid inputs
6. missing/UNKNOWN values according to existing schema semantics
7. numerical stability
8. no mutation of stored observations
"""
import sys, math, json, sqlite3, time
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(ROOT_DIR / "discovery") not in sys.path: sys.path.insert(0, str(ROOT_DIR / "discovery"))

import pytest
from discovery import identity, observations as obs, lifecycle, feature_store

T0 = 1_750_000_000.0
RAW = "a" * 64


@pytest.fixture()
def conn(tmp_path):
    c = obs.open_store(tmp_path / "t.sqlite")
    feature_store.register_definitions(c)
    yield c
    c.close()


def _mk_token(conn, now=T0, chain="solana", address="TokenEdgeTest1111111111111111111111111111"):
    tid = obs.upsert_token(conn, chain, address, now, "fixture", symbol="EDGE", name="Edge Token",
                           created_at_ts=now - 7200.0)
    pid = obs.upsert_pair(conn, chain, "raydium", address, tid, now, "fixture", RAW,
                          pair_created_ts=now - 7200.0)
    lifecycle.register_discovery(conn, tid, now)
    return tid


def _record_obs(conn, tid, ts, vol_1h=1000.0, liq=50000.0, px=1.0, vol_24h=10000.0, buys=50, sells=40):
    raw_id = obs.store_raw(conn, "test_provider", "https://api.test/tok", ts, 200, {"v": vol_1h})
    return obs.record_observation(
        conn, tid, "test_provider", ts, raw_id,
        metrics={
            "price_usd": px,
            "liquidity_usd": liq,
            "volume_1h": vol_1h,
            "volume_24h": vol_24h,
            "txns_1h_buys": buys,
            "txns_1h_sells": sells,
            "boost_amount": 0
        }
    )


def test_volume_growth_1h_normal_positive(conn):
    """Class 1: Normal positive volumes compute valid log-growth."""
    tid = _mk_token(conn, address="TokNormal1111111111111111111111111111")
    _record_obs(conn, tid, T0, vol_1h=100.0)
    _record_obs(conn, tid, T0 + 3600, vol_1h=200.0)
    feats = feature_store.compute_features(conn, tid, T0 + 3600)
    assert "volume_growth_1h" in feats
    assert feats["volume_growth_1h"]["value_num"] == pytest.approx(math.log(2.0))


def test_volume_growth_1h_latest_zero_d_fs_01(conn):
    """Class 2: D-FS-01 reproduction: prev_v1 > 0 but last_v1 == 0.0."""
    tid = _mk_token(conn, address="TokZeroLatest1111111111111111111111111")
    _record_obs(conn, tid, T0, vol_1h=100.0)
    _record_obs(conn, tid, T0 + 3600, vol_1h=0.0)
    # Under unpatched code: math.log(0.0 / 100.0) -> ValueError: math domain error
    feats = feature_store.compute_features(conn, tid, T0 + 3600)
    assert "volume_growth_1h" not in feats


def test_volume_growth_1h_prev_zero(conn):
    """Class 3: prev_v1 == 0.0 and last_v1 > 0."""
    tid = _mk_token(conn, address="TokZeroPrev111111111111111111111111111")
    _record_obs(conn, tid, T0, vol_1h=0.0)
    _record_obs(conn, tid, T0 + 3600, vol_1h=100.0)
    feats = feature_store.compute_features(conn, tid, T0 + 3600)
    assert "volume_growth_1h" not in feats


def test_volume_growth_1h_both_zero(conn):
    """Class 4: both prev_v1 == 0.0 and last_v1 == 0.0."""
    tid = _mk_token(conn, address="TokBothZero111111111111111111111111111")
    _record_obs(conn, tid, T0, vol_1h=0.0)
    _record_obs(conn, tid, T0 + 3600, vol_1h=0.0)
    feats = feature_store.compute_features(conn, tid, T0 + 3600)
    assert "volume_growth_1h" not in feats


def test_missing_and_sparse_observations(conn):
    """Class 6: Single observation only (no past observation 1h ago)."""
    tid = _mk_token(conn, address="TokSingle11111111111111111111111111111")
    _record_obs(conn, tid, T0, vol_1h=100.0)
    feats = feature_store.compute_features(conn, tid, T0)
    assert "volume_growth_1h" not in feats
    assert "liquidity_growth_1h" not in feats
    assert "price_change_1h" not in feats
    assert feats["liquidity_usd_t"]["value_num"] == 50000.0


def test_numerical_stability(conn):
    """Class 7: Very small and large float values."""
    tid = _mk_token(conn, address="TokNumStab1111111111111111111111111111")
    _record_obs(conn, tid, T0, vol_1h=1e-6, liq=1e-6, px=1e-8)
    _record_obs(conn, tid, T0 + 3600, vol_1h=1e6, liq=1e9, px=100.0)
    feats = feature_store.compute_features(conn, tid, T0 + 3600)
    assert math.isfinite(feats["volume_growth_1h"]["value_num"])
    assert math.isfinite(feats["liquidity_growth_1h"]["value_num"])
    assert math.isfinite(feats["price_change_1h"]["value_num"])


def test_no_mutation_of_stored_observations(conn):
    """Class 8: feature computation is strictly read-only and does not mutate obs rows."""
    tid = _mk_token(conn, address="TokNoMut111111111111111111111111111111")
    _record_obs(conn, tid, T0, vol_1h=100.0, liq=10000.0)
    _record_obs(conn, tid, T0 + 3600, vol_1h=0.0, liq=12000.0)

    rows_before = conn.execute("SELECT * FROM discovery_observations WHERE token_id=?", (tid,)).fetchall()
    before_tuples = [tuple(r) for r in rows_before]

    # Try compute_features (which fails under unpatched, or succeeds under patched)
    try:
        feature_store.compute_features(conn, tid, T0 + 3600)
    except Exception:
        pass

    rows_after = conn.execute("SELECT * FROM discovery_observations WHERE token_id=?", (tid,)).fetchall()
    after_tuples = [tuple(r) for r in rows_after]
    assert before_tuples == after_tuples
