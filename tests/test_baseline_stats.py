#!/usr/bin/env python3
"""Tests for research/baseline_stats.py — fixture cohorts only (labeled; live cohorts get their own reports)."""
import sys, json, sqlite3
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(ROOT_DIR / "research") not in sys.path: sys.path.insert(0, str(ROOT_DIR / "research"))

import pytest
from discovery import observations as obs, lifecycle
import baseline_stats as bs

T0 = 1_750_000_000.0


def _cohort(tmp_path, n_tokens=260, lifted=True):
    """Synthetic cohort: when lifted=True, liquidity_growth_1h>0.10 ⇒ ~40% positive rate;
    baseline ≈ 10%. When lifted=False, condition has no effect (≈10% everywhere)."""
    conn = obs.open_store(tmp_path / "c.sqlite")
    for i in range(n_tokens):
        tid = obs.upsert_token(conn, "solana", f"Mint{i:040d}", T0, "fixture")
        lifecycle.register_discovery(conn, tid, T0)
        raw = obs.store_raw(conn, "fixture", f"fx://{i}", T0 + 1, 200, {"i": i})
        # feature row at join point T0+1h (exact join semantics of evaluate_condition)
        cond_hit = (i % 10 < 4) if lifted else (i % 10 < 1)
        lg = 0.15 if i % 5 == 0 else 0.0
        positive = cond_hit if lg > 0.10 else (i % 10 == 1)
        conn.execute(
            """INSERT INTO feature_vector(token_id,feature_set_version,as_of_ts,availability_ts,key,value_num)
               VALUES (?,?,?,?,?,?)""",
            (tid, "fs_v0.1", T0 + bs.JOIN_OFFSET, T0 + bs.JOIN_OFFSET - 60,
             "liquidity_growth_1h", lg))
        conn.execute("UPDATE observation_state SET state='RESOLVED' WHERE token_id=?", (tid,))
        conn.execute(
            """INSERT INTO outcome_label(token_id,horizon,event_class,hit,max_favorable,max_adverse,
                                       entry_price,entry_price_ts,resolved_ts)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (tid, "24h", "+50%", 1 if (positive if lg > 0.10 else cond_hit) else 0,
             1.5, -0.2, 1.0, T0, T0 + 86400))
    conn.commit()
    return conn


def test_lift_detected_on_large_lifted_cohort(tmp_path):
    conn = _cohort(tmp_path, n_tokens=260, lifted=True)
    r = bs.evaluate_condition(conn, "key='liquidity_growth_1h' AND value_num>0.10", "24h", "+50%")
    # conditioned cohort = 52 tokens (i%5==0) → still under MIN_N → verdict must be INSUFFICIENT_DATA,
    # but descriptive lift should exist
    assert r["n_conditioned"] == 52
    assert r["verdict"] == "INSUFFICIENT_DATA"
    assert r["rate_conditioned"] > r["rate_baseline"]


def test_small_sample_refusal(tmp_path):
    conn = obs.open_store(tmp_path / "s.sqlite")
    # 10 tokens only — even a 10/10 hit streak must NOT pass guards
    for i in range(10):
        tid = obs.upsert_token(conn, "solana", f"S{i:040d}", T0, "fixture")
        lifecycle.register_discovery(conn, tid, T0)
        conn.execute("UPDATE observation_state SET state='RESOLVED' WHERE token_id=?", (tid,))
        conn.execute(
            "INSERT INTO feature_vector VALUES (?,?,?,?,?,?,NULL,'HIGH','t')",
            (tid, "fs_v0.1", T0 + bs.JOIN_OFFSET, T0 + bs.JOIN_OFFSET - 60, "liquidity_growth_1h", 0.2))
        conn.execute(
            """INSERT INTO outcome_label VALUES (?,?,?,1,2,-0.1,1,?,?)""",
            (tid, "24h", "+50%", T0, T0 + 86400))
    conn.commit()
    r = bs.evaluate_condition(conn, "key='liquidity_growth_1h' AND value_num>0.10", "24h", "+50%")
    assert r["rate_conditioned"] == 1.0 and r["verdict"] == "INSUFFICIENT_DATA"
    assert "positives<" in r["reason"] or "n<" in r["reason"]


def test_wilson_ci_properties():
    lo, hi = bs.wilson_ci(2, 20)
    assert lo <= 0.1 <= hi and hi > lo
    lo0, hi0 = bs.wilson_ci(0, 0)
    assert lo0 is None and hi0 is None
    lo1, hi1 = bs.wilson_ci(20, 20)
    assert lo1 > 0.5 and hi1 == pytest.approx(1.0, abs=0.05)


def test_search_space_registry(tmp_path):
    reg_path = tmp_path / "reg.json"
    cells = [{"cell_id": "X1", "condition": "k", "horizon": "24h", "event_class": "+50%"}]
    n = bs.register_search_cells(cells, "B-test", str(reg_path))
    assert n == 1
    n = bs.register_search_cells(cells, "B-test2", str(reg_path))
    assert n == 2
    reg = json.loads(reg_path.read_text())
    assert len(reg["batches"]) == 2 and reg["cells"][0]["batch_id"] == "B-test"
