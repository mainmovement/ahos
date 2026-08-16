#!/usr/bin/env python3
"""Wave-7 tests — baseline_stats.evaluate_conjunction + discovery.materialize.
Fixture cohorts only; live cohorts get their own reports. All constants stay locked."""
import sys, sqlite3
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(ROOT_DIR / "research") not in sys.path: sys.path.insert(0, str(ROOT_DIR / "research"))

import pytest
from discovery import observations as obs, lifecycle, feature_store, materialize  # noqa: E402
import baseline_stats as bs  # noqa: E402

T0 = 1_750_000_000.0


def _mk_token(conn, i, lg, va, hit, state="RESOLVED"):
    """Token with a two-key frozen feature vector at the exact join point."""
    tid = obs.upsert_token(conn, "solana", f"Mint{i:040d}", T0, "fixture")
    lifecycle.register_discovery(conn, tid, T0)
    for key, val in (("liquidity_growth_1h", lg), ("volume_acceleration", va)):
        conn.execute(
            """INSERT INTO feature_vector(token_id,feature_set_version,as_of_ts,availability_ts,key,value_num)
               VALUES (?,?,?,?,?,?)""",
            (tid, "fs_v0.2", T0 + bs.JOIN_OFFSET, T0 + bs.JOIN_OFFSET - 60, key, val))
    conn.execute("UPDATE observation_state SET state=? WHERE token_id=?", (state, tid))
    conn.execute(
        """INSERT INTO outcome_label(token_id,horizon,event_class,hit,max_favorable,max_adverse,
                                   entry_price,entry_price_ts,resolved_ts)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (tid, "24h", "+50%", hit, 1.6 if hit else 1.05, -0.2, 1.0, T0, T0 + 86400))
    return tid


# ---------------------------------------------------------------- conjunction cells
def test_conjunction_selects_only_tokens_satisfying_all_clauses(tmp_path):
    conn = obs.open_store(tmp_path / "c.sqlite")
    # 12 tokens: 6 high-lg, of those only 3 also high-va; hits planted ONLY in the 3 full matches
    for i in range(12):
        high_lg = i % 2 == 0
        high_va = i % 4 == 0
        _mk_token(conn, i, lg=0.15 if high_lg else 0.01,
                  va=2.5 if high_va else 0.8, hit=1 if (high_lg and high_va and i < 8) else 0)
    conn.commit()
    clauses = [{"key": "liquidity_growth_1h", "op": ">", "value": 0.10},
               {"key": "volume_acceleration", "op": ">=", "value": 2.0}]
    r = bs.evaluate_conjunction(conn, clauses, "24h", "+50%")
    assert r["n_conditioned"] == 3            # i ∈ {0,4,8}: i%2==0 AND i%4==0 → exactly 3 tokens
    assert r["pos_conditioned"] == 2          # hits planted only for i<8 among full matches
    assert r["rate_conditioned"] > r["rate_baseline"]
    assert r["n_baseline"] == 12
    assert r["verdict"] == "INSUFFICIENT_DATA"  # guards fire below MIN_N/MIN_POS — honest by construction
    assert r["condition"]["conjunction"] == clauses
    conn.close()


def test_conjunction_range_same_key_twice(tmp_path):
    conn = obs.open_store(tmp_path / "r.sqlite")
    for i in range(6):
        _mk_token(conn, i, lg=[0.05, 0.12, 0.30, 0.45, 0.60, 0.11][i], va=1.0, hit=0)
    conn.commit()
    r = bs.evaluate_conjunction(conn, [{"key": "liquidity_growth_1h", "op": ">=", "value": 0.30},
                                       {"key": "liquidity_growth_1h", "op": "<", "value": 0.50}],
                                "24h", "+50%")
    assert r["n_conditioned"] == 2            # lg in [0.30, 0.50): indices 2 and 3
    conn.close()


def test_conjunction_unresolved_tokens_excluded(tmp_path):
    conn = obs.open_store(tmp_path / "u.sqlite")
    _mk_token(conn, 0, lg=0.2, va=3.0, hit=1, state="OBSERVING")   # not resolved → must not join
    for i in range(1, 4):
        _mk_token(conn, i, lg=0.2, va=3.0, hit=0)
    conn.commit()
    r = bs.evaluate_conjunction(conn, [{"key": "liquidity_growth_1h", "op": ">", "value": 0.10}],
                                "24h", "+50%")
    assert r["n_conditioned"] == 3 and r["n_baseline"] == 3
    conn.close()


@pytest.mark.parametrize("bad", [
    {"key": "x'; DROP TABLE tokens;--", "op": ">", "value": 1.0},
    {"key": "liquidity_growth_1h", "op": "LIKE", "value": 1.0},
    {"key": "liquidity_growth_1h", "op": ">", "value": "sql-injection"},
    {"key": "", "op": ">", "value": 1.0},
])
def test_conjunction_clause_validation_rejects_injection(tmp_path, bad):
    conn = obs.open_store(tmp_path / "v.sqlite")
    with pytest.raises(ValueError):
        bs.evaluate_conjunction(conn, [bad], "24h", "+50%")
    conn.close()


# ---------------------------------------------------------------- batch materializer
def _obs_token_with_series(conn, i, n_obs=20, dt=300.0):
    """Real observation rows so fs_v0.2 features are computable (VOL_WINDOW=12 for stability)."""
    tid = obs.upsert_token(conn, "solana", f"Ser{i:040d}", T0, "fixture")
    lifecycle.register_discovery(conn, tid, T0)
    raw = obs.store_raw(conn, "fixture", f"fx://{i}", T0 + 1, 200, {"i": i})
    for k in range(n_obs):
        ts = T0 + k * dt
        obs.record_observation(conn, tid, "fixture", ts, raw, pair=f"P{i}",
                               metrics={"price_usd": 1.0 * (1 + 0.001 * k),
                                        "liquidity_usd": 50_000.0 + 10 * k,
                                        "market_cap": 1_000_000.0 + 100 * k,
                                        "volume_5m": 900.0 + k, "volume_1h": 12_000.0,
                                        "volume_24h": 250_000.0,
                                        "txns_5m_buys": 40 + k, "txns_5m_sells": 20,
                                        "txns_1h_buys": 400, "txns_1h_sells": 200})
    return tid


def test_materialize_features_frozen_asof_idempotent(tmp_path):
    conn = obs.open_store(tmp_path / "m.sqlite")
    for i in range(3):
        _obs_token_with_series(conn, i)
    conn.commit()
    rep1 = materialize.materialize_features(conn, now=T0 + 4000.0)
    assert rep1["features_tokens"] == 3 and rep1["features_rows"] > 0
    n1 = conn.execute("SELECT COUNT(*) c FROM feature_vector").fetchone()["c"]
    asofs = {r["as_of_ts"] for r in conn.execute("SELECT DISTINCT as_of_ts FROM feature_vector")}
    assert asofs == {T0 + 3600.0}                       # exact join point, nothing else
    avails = conn.execute("SELECT MAX(availability_ts) m FROM feature_vector").fetchone()["m"]
    assert avails <= T0 + 3600.0                        # L3: no future availability
    rep2 = materialize.materialize_features(conn, now=T0 + 4000.0)
    n2 = conn.execute("SELECT COUNT(*) c FROM feature_vector").fetchone()["c"]
    assert n2 == n1 and rep2["features_tokens"] == 3    # idempotent upsert
    conn.close()


def test_materialize_features_skips_immature(tmp_path):
    conn = obs.open_store(tmp_path / "mi.sqlite")
    _obs_token_with_series(conn, 0)
    late = obs.upsert_token(conn, "solana", "L" + "9" * 39, T0 + 7000, "fixture")
    lifecycle.register_discovery(conn, late, T0 + 7000)   # as_of = T0+10600 > now
    conn.commit()
    rep = materialize.materialize_features(conn, now=T0 + 4000.0)
    assert rep["features_tokens"] == 1 and rep["features_immature_skipped"] == 1
    got = {r["token_id"] for r in conn.execute("SELECT DISTINCT token_id FROM feature_vector")}
    assert late not in got
    conn.close()


def test_materialize_outcomes_respects_resolution_and_horizon_closure(tmp_path):
    conn = obs.open_store(tmp_path / "mo.sqlite")
    done = _obs_token_with_series(conn, 0, n_obs=500, dt=200.0)   # spans T0..T0+100000 (>24h)
    open_ = _obs_token_with_series(conn, 1, n_obs=500, dt=200.0)
    conn.execute("UPDATE observation_state SET state='RESOLVED' WHERE token_id=?", (done,))
    conn.commit()
    rep = materialize.materialize_outcomes(conn, now=T0 + 90_000.0)   # 24h+ closed, 72h/7d not
    assert rep["outcome_tokens_resolved"] == 1
    rows = conn.execute("SELECT horizon, event_class, hit FROM outcome_label WHERE token_id=?",
                        (done,)).fetchall()
    horizons = {r["horizon"] for r in rows}
    assert horizons == {"15m", "1h", "4h", "12h", "24h"}            # 72h/7d horizon-closure law
    assert conn.execute("SELECT COUNT(*) c FROM outcome_label WHERE token_id=?",
                        (open_,)).fetchone()["c"] == 0              # never label unresolved
    conn.close()
