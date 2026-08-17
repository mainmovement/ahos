"""Wave-25: the self-improvement loop -- "what if I had bought token X on day Y?"

The value of a learning loop is entirely determined by whether it learns the
TRUE outcome. A loop trained on displayed chart prices teaches the system to
chase tokens it can never sell. So the load-bearing test in this file is
`test_pump_into_a_dead_pool_is_a_trap_not_a_win`: a 5x on paper that cannot be
exited must be recorded as a failure.

Second load-bearing rule: hindsight may judge a decision, never justify it.
Every result carries the OUT_OF_SAMPLE label.
"""
from __future__ import annotations

import sqlite3

import pytest

from architecture.evolution.hindsight import (
    HindsightEngine, HindsightResult, VERDICTS, HINDSIGHT_VERSION,
    OUT_OF_SAMPLE_NOTE, MIN_OBSERVATIONS, DEAD_LIQUIDITY_USD,
)

T0 = 1_000_000.0
LATER = T0 + 100 * 3600


@pytest.fixture
def db():
    c = sqlite3.connect(":memory:")
    c.execute("""CREATE TABLE discovery_observations(
        obs_id INTEGER PRIMARY KEY, token_id TEXT, retrieved_ts REAL,
        price_usd REAL, liquidity_usd REAL, error_state TEXT)""")
    c.execute("""CREATE TABLE opportunity_rank(
        as_of_ts REAL, token_id TEXT, rank INTEGER, bullets_json TEXT,
        risks_json TEXT, invalidation_json TEXT, engine_version TEXT)""")
    c.execute("""CREATE TABLE tokens(
        token_id TEXT PRIMARY KEY, chain_id TEXT, address TEXT,
        symbol TEXT, name TEXT)""")
    return c


def seed(db, token_id, path, entry_price=1.0, entry_liq=50_000.0, t0=T0):
    """path = [(hours_after, price, liquidity), ...]"""
    db.execute("INSERT INTO discovery_observations"
               "(token_id,retrieved_ts,price_usd,liquidity_usd) VALUES(?,?,?,?)",
               (token_id, t0, entry_price, entry_liq))
    for h, p, l in path:
        db.execute("INSERT INTO discovery_observations"
                   "(token_id,retrieved_ts,price_usd,liquidity_usd) VALUES(?,?,?,?)",
                   (token_id, t0 + h * 3600, p, l))
    return db


# ----------------------------------------------------------- core verdicts --

def test_a_real_winner_is_recorded_as_a_win(db):
    seed(db, "W", [(1, 1.2, 50_000), (2, 1.8, 48_000), (3, 2.4, 45_000)])
    r = HindsightEngine(db).review_pick("W", T0, symbol="ALPHA", now=LATER)
    assert r.verdict == "WOULD_HAVE_WON"
    assert r.rule_exit_reason == "TAKE_PROFIT"
    assert r.max_favorable_pct == pytest.approx(140.0)


def test_a_dump_is_recorded_as_a_loss_not_as_flat(db):
    """A token that ticked +0% then fell 60% did not 'do fine'."""
    seed(db, "L", [(1, 0.9, 50_000), (2, 0.6, 48_000), (3, 0.4, 45_000)])
    r = HindsightEngine(db).review_pick("L", T0, symbol="DUMP", now=LATER)
    assert r.verdict == "WOULD_HAVE_LOST"
    assert r.rule_exit_reason == "STOP_LOSS"


def test_a_genuinely_flat_token_is_flat(db):
    seed(db, "F", [(1, 1.02, 50_000), (2, 0.98, 50_000), (3, 1.05, 50_000)])
    r = HindsightEngine(db).review_pick("F", T0, symbol="MEH", now=LATER)
    assert r.verdict == "WOULD_HAVE_BEEN_FLAT"
    assert r.rule_exit_reason == "TIME_EXIT"


def test_pump_into_a_dead_pool_is_a_trap_not_a_win(db):
    """THE test. 5x on the chart, $900 pool -- the money never comes out."""
    seed(db, "T", [(1, 2.0, 850), (2, 4.0, 800), (3, 5.0, 700), (4, 3.0, 600)],
         entry_liq=900.0)
    r = HindsightEngine(db).review_pick("T", T0, symbol="TRAP",
                                        position_usd=1000.0, now=LATER)
    assert r.verdict == "WOULD_HAVE_BEEN_TRAPPED"
    assert r.displayed_peak_multiple == pytest.approx(5.0)
    # The honest number must be dramatically below the chart number.
    assert r.realizable_peak_multiple < 1.0
    assert "خروج" in r.lesson


def test_the_display_reality_gap_is_surfaced_explicitly(db):
    seed(db, "T", [(1, 2.0, 850), (2, 4.0, 800), (3, 5.0, 700)], entry_liq=900.0)
    r = HindsightEngine(db).review_pick("T", T0, position_usd=1000.0, now=LATER)
    assert any("شکاف نمایش/واقعیت" in x for x in r.reasons)


def test_liquidity_collapse_outranks_price_in_the_exit_replay(db):
    """EXIT_V1 priority: a collapsing pool fires before take-profit."""
    # Price is well past take-profit, but the pool has collapsed to $100.
    seed(db, "C", [(1, 1.9, 100.0), (2, 2.5, 100.0), (3, 3.0, 100.0)])
    r = HindsightEngine(db).review_pick("C", T0, now=LATER)
    assert r.rule_exit_reason == "LIQUIDITY_COLLAPSE"


# ------------------------------------------------------ unknown is a verdict --

def test_thin_history_is_insufficient_data_not_a_zero(db):
    seed(db, "S", [(1, 1.1, 50_000)])
    r = HindsightEngine(db).review_pick("S", T0, symbol="THIN", now=LATER)
    assert r.verdict == "INSUFFICIENT_DATA"
    assert r.is_known is False
    assert r.observation_count < MIN_OBSERVATIONS
    # It must blame observation coverage, not the market.
    assert "رصد" in r.lesson


def test_missing_entry_price_is_not_guessed(db):
    r = HindsightEngine(db).review_pick("GHOST", T0, now=LATER)
    assert r.verdict == "INSUFFICIENT_DATA"
    assert r.entry_price is None
    assert any("قیمت مرجع" in u for u in r.unknowns)


def test_error_rows_are_excluded_never_treated_as_price_zero(db):
    seed(db, "E", [(1, 1.2, 50_000), (2, 1.8, 50_000), (3, 2.4, 50_000)])
    db.execute("INSERT INTO discovery_observations"
               "(token_id,retrieved_ts,price_usd,liquidity_usd,error_state)"
               " VALUES(?,?,?,?,?)", ("E", T0 + 4 * 3600, None, None, "timeout"))
    r = HindsightEngine(db).review_pick("E", T0, now=LATER)
    assert r.observation_count == 3
    assert r.trough_price > 0


def test_entry_reference_never_looks_into_the_future(db):
    """Using a post-decision price as the entry would fake the whole result."""
    seed(db, "P", [(1, 5.0, 50_000), (2, 6.0, 50_000), (3, 7.0, 50_000)],
         entry_price=1.0)
    r = HindsightEngine(db).review_pick("P", T0, now=LATER)
    assert r.entry_price == 1.0


def test_observations_before_the_decision_are_not_part_of_the_outcome(db):
    db.execute("INSERT INTO discovery_observations"
               "(token_id,retrieved_ts,price_usd,liquidity_usd) VALUES(?,?,?,?)",
               ("B", T0 - 7200, 99.0, 50_000))
    seed(db, "B", [(1, 1.1, 50_000), (2, 1.2, 50_000), (3, 1.3, 50_000)])
    r = HindsightEngine(db).review_pick("B", T0, now=LATER)
    assert r.peak_price == pytest.approx(1.3)  # 99.0 must not appear


def test_horizon_bounds_the_review_window(db):
    seed(db, "H", [(1, 1.1, 50_000), (2, 1.2, 50_000),
                   (3, 1.3, 50_000), (80, 99.0, 50_000)])
    r = HindsightEngine(db).review_pick("H", T0, horizon_hours=48.0, now=LATER)
    assert r.peak_price == pytest.approx(1.3)  # the 80h moonshot is out of scope


# ------------------------------------------------------------- aggregation --

def test_aggregate_counts_and_rates(db):
    e = HindsightEngine(db)
    seed(db, "W", [(1, 1.2, 50_000), (2, 1.8, 48_000), (3, 2.4, 45_000)])
    seed(db, "L", [(1, 0.9, 50_000), (2, 0.6, 48_000), (3, 0.4, 45_000)])
    seed(db, "S", [(1, 1.1, 50_000)])
    rs = [e.review_pick("W", T0, now=LATER),
          e.review_pick("L", T0, now=LATER),
          e.review_pick("S", T0, now=LATER)]
    agg = e.aggregate(rs)
    assert agg["reviewed"] == 3 and agg["judgeable"] == 2
    assert agg["counts"]["WOULD_HAVE_WON"] == 1
    assert agg["counts"]["WOULD_HAVE_LOST"] == 1
    assert agg["counts"]["INSUFFICIENT_DATA"] == 1
    assert agg["hit_rate"] == pytest.approx(0.5)


def test_poor_coverage_is_reported_as_the_priority_finding(db):
    """If most picks can't be judged, the bug is observation -- not scoring."""
    e = HindsightEngine(db)
    for t in ("A", "B", "C"):
        seed(db, t, [(1, 1.1, 50_000)])
    rs = [e.review_pick(t, T0, now=LATER) for t in ("A", "B", "C")]
    agg = e.aggregate(rs)
    assert agg["judgeable"] == 0
    assert "پوشش رصد" in agg["priority_finding"]


def test_high_trap_rate_recommends_tightening_liquidity(db):
    e = HindsightEngine(db)
    for t in ("T1", "T2"):
        seed(db, t, [(1, 2.0, 300), (2, 4.0, 250), (3, 5.0, 200)], entry_liq=400.0)
    rs = [e.review_pick(t, T0, position_usd=1000.0, now=LATER) for t in ("T1", "T2")]
    agg = e.aggregate(rs)
    assert agg["trap_rate"] == 1.0
    assert "نقدینگی" in agg["priority_finding"]


def test_aggregate_on_empty_input_does_not_divide_by_zero(db):
    agg = HindsightEngine(db).aggregate([])
    assert agg["reviewed"] == 0
    assert agg["hit_rate"] is None and agg["trap_rate"] is None


# --------------------------------------------------------------- batch/api --

def test_review_recent_picks_only_judges_matured_picks(db):
    """A pick from 10 minutes ago cannot be graded on a 48h horizon."""
    db.execute("INSERT INTO tokens(token_id,symbol) VALUES('W','ALPHA')")
    seed(db, "W", [(1, 1.2, 50_000), (2, 1.8, 48_000), (3, 2.4, 45_000)])
    db.execute("INSERT INTO opportunity_rank(as_of_ts,token_id,rank) VALUES(?,?,?)",
               (T0, "W", 1))
    db.execute("INSERT INTO opportunity_rank(as_of_ts,token_id,rank) VALUES(?,?,?)",
               (LATER - 600, "W", 1))  # too fresh
    out = HindsightEngine(db).review_recent_picks(horizon_hours=48.0, now=LATER)
    assert len(out) == 1
    assert out[0].symbol == "ALPHA"


def test_missing_tables_degrade_to_empty_not_crash():
    bare = sqlite3.connect(":memory:")
    e = HindsightEngine(bare)
    assert e.review_recent_picks() == []
    assert e.review_pick("X", T0).verdict == "INSUFFICIENT_DATA"


# ------------------------------------------------------------------- laws --

def test_every_result_is_labelled_out_of_sample(db):
    seed(db, "W", [(1, 1.2, 50_000), (2, 1.8, 48_000), (3, 2.4, 45_000)])
    r = HindsightEngine(db).review_pick("W", T0, now=LATER)
    assert r.review_label == OUT_OF_SAMPLE_NOTE
    assert "هرگز" in r.review_label  # 'never' justify
    assert r.version == HINDSIGHT_VERSION


def test_report_carries_the_out_of_sample_label(db):
    e = HindsightEngine(db)
    seed(db, "W", [(1, 1.2, 50_000), (2, 1.8, 48_000), (3, 2.4, 45_000)])
    txt = e.report_persian([e.review_pick("W", T0, now=LATER)])
    assert OUT_OF_SAMPLE_NOTE in txt
    assert "بازبینی انتخاب‌های گذشته" in txt


def test_empty_report_is_still_honest(db):
    txt = HindsightEngine(db).report_persian([])
    assert "قابل بازبینی وجود ندارد" in txt
    assert OUT_OF_SAMPLE_NOTE in txt


def test_verdict_is_always_from_the_locked_vocabulary(db):
    e = HindsightEngine(db)
    seed(db, "W", [(1, 1.2, 50_000), (2, 1.8, 48_000), (3, 2.4, 45_000)])
    seed(db, "S", [(1, 1.1, 50_000)])
    for t in ("W", "S", "GHOST"):
        assert e.review_pick(t, T0, now=LATER).verdict in VERDICTS


def test_result_is_json_serialisable(db):
    import json
    seed(db, "W", [(1, 1.2, 50_000), (2, 1.8, 48_000), (3, 2.4, 45_000)])
    r = HindsightEngine(db).review_pick("W", T0, now=LATER)
    assert json.loads(json.dumps(r.to_dict(), ensure_ascii=False))["verdict"] == r.verdict


def test_engine_never_writes_to_the_discovery_store(db):
    """Hindsight is read-only over discovery. Learning must not mutate evidence."""
    seed(db, "W", [(1, 1.2, 50_000), (2, 1.8, 48_000), (3, 2.4, 45_000)])
    before = db.execute("SELECT COUNT(*) FROM discovery_observations").fetchone()[0]
    e = HindsightEngine(db)
    e.review_pick("W", T0, now=LATER)
    e.review_recent_picks(now=LATER)
    after = db.execute("SELECT COUNT(*) FROM discovery_observations").fetchone()[0]
    assert before == after
