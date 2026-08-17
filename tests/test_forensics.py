"""Wave-26: on-chain forensics -- techniques harvested from OSS, math verified.

These statistics are the reusable half of the Solana rug-detection ecosystem.
The code in those projects mostly is not reusable (TypeScript, or Python
wrappers around paid APIs that break the $0 floor and the sanctions
constraint), but Gini, coefficient of variation and round-number clustering
are public mathematics.

Because we reimplemented rather than copied, these tests do the job a license
cannot: they prove the math is actually right, by checking it against values
that can be derived by hand.
"""
from __future__ import annotations

import json
import sqlite3

import pytest

from architecture.intel.forensics import (
    ForensicsAnalyzer, ForensicsReport, FORENSICS_VERSION,
    gini_coefficient, coefficient_of_variation, round_number_share,
    parse_top_accounts,
    GINI_EXTREME, GINI_HIGH, MIN_HOLDERS_FOR_GINI, MIN_WALLETS_FOR_CV,
)


# --------------------------------------------------------- gini, verified --

def test_perfect_equality_is_zero():
    """Hand-checkable anchor: ten identical holders => Gini 0."""
    assert gini_coefficient([10.0] * 10) == pytest.approx(0.0, abs=1e-9)


def test_near_total_concentration_approaches_one():
    g = gini_coefficient([1_000_000.0] + [1.0] * 19)
    assert g > 0.9


def test_gini_is_scale_invariant():
    """Doubling every balance changes nothing about inequality."""
    a = gini_coefficient([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    b = gini_coefficient([2.0, 4.0, 6.0, 8.0, 10.0, 12.0])
    assert a == pytest.approx(b)


def test_gini_is_order_independent():
    vals = [5.0, 1.0, 9.0, 3.0, 7.0, 2.0]
    assert gini_coefficient(vals) == pytest.approx(gini_coefficient(sorted(vals)))


def test_gini_stays_in_the_unit_interval():
    for vals in ([1.0] * 8, [100.0] + [0.0] * 9, [3.0, 1.0, 4.0, 1.0, 5.0, 9.0]):
        g = gini_coefficient(vals)
        assert g is None or 0.0 <= g <= 1.0


def test_too_few_holders_is_none_not_zero():
    """The bug this prevents: reading 'unmeasured' as 'perfectly equal'."""
    assert gini_coefficient([1.0, 2.0]) is None
    assert gini_coefficient([]) is None
    assert len([1.0, 2.0]) < MIN_HOLDERS_FOR_GINI


def test_zero_total_supply_is_none():
    assert gini_coefficient([0.0] * 10) is None


def test_negative_balances_are_discarded_not_trusted():
    assert gini_coefficient([-5.0, -1.0]) is None


# ------------------------------------------------- coordination detection --

def test_identical_wallet_behaviour_has_zero_variation():
    """Bots are uniform. That uniformity is the fingerprint."""
    assert coefficient_of_variation([7.0] * 8) == pytest.approx(0.0)


def test_organic_behaviour_has_high_variation():
    cv = coefficient_of_variation([5, 120, 8, 300, 17, 64, 9, 201])
    assert cv > 0.5


def test_cv_needs_enough_wallets():
    assert coefficient_of_variation([1.0, 1.0]) is None
    assert len([1.0, 1.0]) < MIN_WALLETS_FOR_CV


def test_cv_with_zero_mean_is_none():
    assert coefficient_of_variation([0.0] * 8) is None


# ------------------------------------------------------ automation pattern --

def test_all_round_amounts_are_flagged():
    assert round_number_share([1.0, 0.5, 2.0, 1.0, 0.1, 0.5, 1.0, 2.0]) == 1.0


def test_organic_amounts_are_not_flagged():
    share = round_number_share(
        [0.3271, 1.8823, 0.0917, 2.4419, 0.7734, 1.1265, 0.4408, 3.2231])
    assert share < 0.2


def test_round_share_needs_a_minimum_sample():
    assert round_number_share([1.0, 1.0]) is None


# ------------------------------------------------------------- end to end --

def test_a_manipulated_token_is_labelled_manipulated():
    r = ForensicsAnalyzer().analyze(
        "RUG",
        holder_balances=[1_000_000.0] + [5.0] * 20,
        wallet_txn_counts=[7.0] * 10,
        buy_amounts=[1.0, 0.5, 1.0, 2.0, 0.5, 1.0, 0.1, 2.0])
    assert r.label == "MANIPULATED"
    assert r.coordination_suspected and r.bot_pattern_suspected
    assert r.risk_penalty == 50.0     # capped


def test_a_healthy_token_is_clean():
    r = ForensicsAnalyzer().analyze(
        "GOOD",
        holder_balances=[100, 95, 88, 80, 76, 70, 65, 60, 55, 50, 45, 40],
        wallet_txn_counts=[3, 17, 8, 42, 5, 23, 11, 31],
        buy_amounts=[0.3271, 1.8823, 0.0917, 2.4419, 0.7734, 1.1265, 0.4408, 3.2231])
    assert r.label == "CLEAN"
    assert r.risk_penalty == 0.0
    assert not r.warnings


def test_no_evidence_yields_unknown_never_clean():
    """The core discipline: unmeasured must never read as safe."""
    r = ForensicsAnalyzer().analyze("GHOST")
    assert r.label == "UNKNOWN"
    assert r.is_known is False
    assert r.risk_penalty == 0.0
    assert r.unknowns


def test_partial_evidence_still_produces_a_judgement():
    r = ForensicsAnalyzer().analyze(
        "PARTIAL", holder_balances=[1_000_000.0] + [1.0] * 19)
    assert r.label in ("MANIPULATED", "SUSPICIOUS")
    assert r.coordination_cv is None       # not measured
    assert r.round_number_share is None    # not measured


def test_penalty_is_bounded():
    r = ForensicsAnalyzer().analyze(
        "MAX",
        holder_balances=[10**9] + [1.0] * 30,
        wallet_txn_counts=[5.0] * 20,
        buy_amounts=[1.0] * 20)
    assert 0.0 <= r.risk_penalty <= 50.0


def test_shares_are_derived_from_the_balances():
    r = ForensicsAnalyzer().analyze("S", holder_balances=[50.0] + [5.0] * 10)
    assert r.top1_share_pct == pytest.approx(50.0)
    assert r.holder_count == 11


def test_report_is_serialisable():
    r = ForensicsAnalyzer().analyze("X", holder_balances=[1.0] * 10)
    assert json.loads(json.dumps(r.to_dict(), ensure_ascii=False))["version"] \
        == FORENSICS_VERSION


def test_reasons_and_warnings_are_persian():
    r = ForensicsAnalyzer().analyze(
        "P", holder_balances=[1_000_000.0] + [1.0] * 19)
    joined = " ".join(r.warnings + r.reasons + r.unknowns)
    assert any("\u0600" <= ch <= "\u06FF" for ch in joined)


# ----------------------------------------------------------------- parsing --

@pytest.mark.parametrize("payload,expected", [
    ([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]),
    ([{"amount": 5}, {"amount": 7}], [5.0, 7.0]),
    ([{"uiAmount": 2.5}], [2.5]),
    ([{"balance": "9"}], [9.0]),
    ({"accounts": [1, 2]}, [1.0, 2.0]),
    ({"value": [{"amount": 4}]}, [4.0]),
])
def test_top_accounts_parsing_tolerates_schema_drift(payload, expected):
    assert parse_top_accounts(json.dumps(payload)) == expected


def test_unparseable_holder_payload_yields_nothing_not_garbage():
    for junk in (None, "", "{not json", "[]", 12345):
        assert parse_top_accounts(junk) == []


def test_nested_ui_amount_is_extracted():
    payload = [{"amount": {"uiAmount": 3.5}}]
    assert parse_top_accounts(json.dumps(payload)) == [3.5]


# -------------------------------------------------------------- store I/O --

@pytest.fixture
def db():
    c = sqlite3.connect(":memory:")
    c.execute("""CREATE TABLE holder_snapshot(
        id INTEGER PRIMARY KEY, token_id TEXT, ts REAL, source TEXT,
        top_accounts_json TEXT, top10_share REAL, top20_share REAL,
        error_state TEXT, raw_ref TEXT)""")
    return c


def test_store_reads_the_newest_clean_snapshot(db):
    db.execute("INSERT INTO holder_snapshot(token_id,ts,top_accounts_json)"
               " VALUES('T',1,?)", (json.dumps([1.0] * 10),))
    db.execute("INSERT INTO holder_snapshot(token_id,ts,top_accounts_json)"
               " VALUES('T',2,?)", (json.dumps([1_000_000.0] + [1.0] * 19),))
    r = ForensicsAnalyzer().analyze_from_store(db, "T", symbol="TOK")
    assert r.gini > 0.9      # newest row wins, not the earlier equal one


def test_store_skips_error_rows(db):
    """Honest error rows exist by design; they must never be read as data."""
    db.execute("INSERT INTO holder_snapshot(token_id,ts,top_accounts_json)"
               " VALUES('T',1,?)", (json.dumps([1.0] * 10),))
    db.execute("INSERT INTO holder_snapshot(token_id,ts,top_accounts_json,error_state)"
               " VALUES('T',9,?,'rpc_refused')", (json.dumps([]),))
    r = ForensicsAnalyzer().analyze_from_store(db, "T")
    assert r.holder_count == 10


def test_store_with_no_snapshot_is_unknown(db):
    r = ForensicsAnalyzer().analyze_from_store(db, "MISSING")
    assert r.label == "UNKNOWN"
    assert any("نمونه‌برداری" in u for u in r.unknowns)


def test_store_missing_table_degrades_to_unknown():
    r = ForensicsAnalyzer().analyze_from_store(sqlite3.connect(":memory:"), "T")
    assert r.label == "UNKNOWN"


def test_store_access_is_read_only(db):
    db.execute("INSERT INTO holder_snapshot(token_id,ts,top_accounts_json)"
               " VALUES('T',1,?)", (json.dumps([1.0] * 10),))
    before = db.execute("SELECT COUNT(*) FROM holder_snapshot").fetchone()[0]
    ForensicsAnalyzer().analyze_from_store(db, "T")
    assert db.execute("SELECT COUNT(*) FROM holder_snapshot").fetchone()[0] == before
