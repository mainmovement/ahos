#!/usr/bin/env python3
"""M42 — the single hash-chained ledger and the nightly reconcile over it.

Owner acceptance (OWNER_DIRECTIVE_MISSION_PLAN.md:407, vision M42):
  * tampering breaks the chain;
  * the paper reconcile has 0 differences;
  * the per-broker concentration test passes (each broker <= 40%).

What is under test, by section:

  A. the ledger's shared evidence surface -- ``record``/``evidence``/``halt``/
     ``clear_halt``/``halted`` -- which is what makes it ONE ledger rather than
     a mission log plus a separate audit trail;
  B. the paper-store anchor (``architecture/markets/paper_anchor.py``) -- the
     bridge that binds the frozen Lane A store into that one chain without
     writing to it;
  C. treasury surveillance (``architecture/treasury/surveillance.py``) -- the
     two §7.0 checks that can stop the system;
  D. the reconcile driver (``architecture/treasury/reconcile.py``) -- every
     leg, the verdict order, and the HALT protocol;
  E. the three named acceptance criteria, as named tests;
  F. the authority laws -- the treasury is an observer, not an authority.

Offline self-tests: tmp ledgers and tmp sqlite stores only. ``data/`` is never
opened (the driver's paper leg is repointed at a tmp store), no price feed or
broker API is contacted, and Lane A is never opened for write.
"""
from __future__ import annotations

import ast
import json
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.markets.judge import BROKEN_CHAIN, CLEAN, DISCREPANCY  # noqa: E402
from architecture.markets.judge import judge_paper_ledger  # noqa: E402
from architecture.markets.paper_anchor import (  # noqa: E402
    ANCHORED_CLEAN, ANCHORED_MISMATCH, UNANCHORED, anchor_store, open_store_ro,
    verify_anchor,
)
from architecture.mission.ledger import (  # noqa: E402
    KIND_ANCHOR, KIND_DECISION, KIND_HALT, KIND_HALT_CLEARED, KIND_RECONCILE, KIND_STATE,
    EVIDENCE_KINDS, LedgerError, LedgerTamperError, MissionLedger,
    SecretRejectedError, _sha, canonical_json,
)
from architecture.treasury.reconcile import (  # noqa: E402
    HALTED, UNKNOWN, Finding, ReconcileReport, StatementTrade, check_statement,
    run_reconcile, write_reconcile_report,
)
from architecture.treasury.surveillance import (  # noqa: E402
    ARMED, BREACH, DEPEG, UNMEASURED, WITHIN_LIMIT, BrokerExposure,
    StableQuote, concentration_check, depeg_check, exposures_from_registry,
)

AG = "engineering:m42-test"

#: Vision §7.0: "each broker <= 40%".
LIMIT_SHARE = 0.40


# ------------------------------------------------------------ fixtures ---

@pytest.fixture()
def led(tmp_path):
    """A fresh single ledger on a tmp path. data/ is never touched."""
    return MissionLedger(tmp_path / "m42.jsonl")


def _store(tmp_path, name="store.sqlite", rows=()):
    """A tmp append-only store, built to be anchored. Never Lane A."""
    p = tmp_path / name
    conn = sqlite3.connect(p)
    conn.execute("CREATE TABLE t (id INTEGER, v TEXT)")
    for i, v in rows:
        conn.execute("INSERT INTO t VALUES (?, ?)", (i, v))
    conn.commit()
    conn.close()
    return p


def _open(store):
    return open_store_ro(store)


def _anchor(led, store):
    with _open(store) as conn:
        return anchor_store(led, conn, store="paper_trading.sqlite")


def _verify(led, store):
    with _open(store) as conn:
        return verify_anchor(led, conn, store="paper_trading.sqlite")


def _cp(cycle, *, bankroll=10000.0, equity=None, cumulative=0.0, closed=0,
         price=None, position=None, exit_event=None, realized=None, bps=10.0):
    """One paper checkpoint in the exact form the M42 judge requires."""
    return {
        "paper_only": True,
        "cycle": cycle,
        "bankroll_usd": bankroll,
        "equity_usd": bankroll if equity is None else equity,
        "cumulative_realized_pnl_usd": cumulative,
        "closed_trades": closed,
        "round_trip_bps": bps,
        "price_usd": price,
        "position": position,
        "exit": exit_event,
        "realized_pnl_usd": realized,
    }


def _flat_track(led, mission="M42-TEST-PAPER", cycles=3, bankroll=10000.0):
    """A minimal paper track the judge scores CLEAN: flat, priced every cycle."""
    led.start(mission, phase="paper", task="m42-selftest", agent=AG)
    for i in range(1, cycles + 1):
        led.checkpoint(mission, _cp(i, bankroll=bankroll, price=2000.0 + i))
    return mission


def _closing_track(led, mission="M42-TEST-PAPER", bankroll=10000.0):
    """A paper track that opens and settles one position, judge-clean.

    The close re-derives from the *recorded* open position and the *recorded*
    price, which is the double-entry law the judge enforces; the numbers below
    are computed, not chosen, so the track is honest by construction.
    """
    led.start(mission, phase="paper", task="m42-selftest", agent=AG)
    qty, entry, bps = 2.0, 2000.0, 10.0
    notional = qty * entry
    led.checkpoint(mission, _cp(1, bankroll=bankroll, price=entry))
    led.checkpoint(mission, _cp(2, bankroll=bankroll, price=entry,
                                position={"qty_oz": qty, "notional_usd": notional,
                                          "entry_ts": "cycle-2"}))
    exit_price = 2010.0
    realized = qty * exit_price * (1.0 - bps / 2.0 / 10_000.0) - notional
    led.checkpoint(mission, _cp(3, bankroll=bankroll, price=exit_price,
                                exit_event={"reason": "target"},
                                realized=realized,
                                equity=bankroll + realized,
                                cumulative=realized, closed=1))
    return mission


def _quotes(*prices, base=1.0):
    return tuple(StableQuote(f"feed-{i}", base + p, observed_at=1000.0 + i)
                 for i, p in enumerate(prices))


def _t(ref, qty, entry, exit_, notional, fee, net=None, broker="A"):
    return StatementTrade(external_ref=ref, qty=qty, entry_price_exec=entry,
                          exit_price_exec=exit_, notional_usd=notional,
                          fee_total_usd=fee, net_pnl_usd=net, broker_id=broker)


@pytest.fixture()
def paper_leg(monkeypatch, tmp_path, led):
    """Repoint the reconcile's paper leg at a tmp store and bind it.

    The driver resolves the real paper store through ``config.paths``; a
    self-test must not bind the live store to a throwaway ledger, so the two
    entry points are swapped for tmp-store equivalents. Nothing else changes:
    the driver still calls ``verify_paper_anchor`` then ``anchor_paper_store``,
    which is the binding path under test.
    """
    store = _store(tmp_path)
    _anchor(led, store)

    # The lambdas must reach for the module-level helpers by name; a local
    # def of the same name would shadow them and recurse into itself, which
    # run_reconcile would report as an anchor failure rather than a test error.
    import architecture.treasury.reconcile as rec
    monkeypatch.setattr(rec, "verify_paper_anchor",
                        lambda *a, **k: _verify(led, store))
    monkeypatch.setattr(rec, "anchor_paper_store",
                        lambda *a, **k: _anchor(led, store))
    return store


# =============================================== A. the ledger surface ====

class TestLedgerEvidenceSurface:
    """``record()`` is the single ledger's shared surface: one chain, and the
    evidence rows that can stop the system sit on it rather than beside it."""

    def test_record_appends_to_the_same_chain(self, led):
        led.start("M1", phase="p", task="t", agent=AG)
        row = led.record(KIND_RECONCILE, {"verdict": CLEAN, "paper_only": True})
        assert row["seq"] == 1 and row["prev_hash"] != "0" * 64
        assert row["kind"] == KIND_RECONCILE and row["authority"] == "NONE"
        assert led.verify()["verdict"] == "CHAIN_INTACT"
        assert led.evidence() == [row]          # STATE is not evidence
        assert led.evidence(KIND_ANCHOR) == []
        # the mission history and the evidence share one chain, not two files
        assert len(led.entries()) == 2

    def test_unknown_kind_rejected(self, led):
        with pytest.raises(LedgerError, match="unknown evidence kind"):
            led.record("BUY", {"qty": 1})
        with pytest.raises(LedgerError, match="STATE rows"):
            led.record(KIND_STATE, {"x": 1})

    def test_payload_must_be_a_mapping_and_json(self, led):
        with pytest.raises(LedgerError, match="must be a mapping"):
            led.record(KIND_ANCHOR, [1, 2])
        with pytest.raises(LedgerError, match="JSON-serialisable"):
            led.record(KIND_ANCHOR, {"bad": object()})

    def test_private_payload_keys_rejected(self, led):
        with pytest.raises(LedgerError, match="must not be private"):
            led.record(KIND_ANCHOR, {"_hidden": 1})

    def test_oversized_text_is_truncated_and_structures_rejected(self, led):
        # a long text value is truncated, not rejected -- the message is kept
        row = led.record(KIND_RECONCILE, {"k": "x" * 5000})
        assert row["payload"]["k"].endswith("...[TRUNCATED]")
        # a structure larger than the checkpoint budget cannot be carried at all
        huge = {f"key_{i}": i for i in range(8000)}
        with pytest.raises(LedgerError, match="too large"):
            led.record(KIND_ANCHOR, huge)
        rows = led.entries()
        assert len(rows) == 1 and rows[0]["kind"] == KIND_RECONCILE,             "the truncated record stands; the rejected one wrote nothing"

    def test_long_text_is_truncated_not_dropped(self, led):
        row = led.record(KIND_RECONCILE, {"k": "x" * 5000})
        assert row["payload"]["k"].endswith("...[TRUNCATED]")

    def test_secrets_never_reach_the_chain(self, led):
        led.strict = True
        with pytest.raises(SecretRejectedError):
            led.record(KIND_RECONCILE,
                       {"note": "sk-proj-abc123def456ghi789jkl012mno345"})
        assert len(led.entries()) == 0, "a rejected record wrote nothing"

    def test_head_hash_and_verify_agree(self, led):
        led.record(KIND_ANCHOR, {"root_hash": "a" * 64})
        assert led.head_hash() == led.verify()["head_hash"]


class TestHaltProtocol:
    """A HALT is on the chain, cannot be dropped, and is lifted only by an
    entry naming its own hash with a written reason."""

    def test_halt_then_halted(self, led):
        row = led.halt("m42:depeg:USDT", reason="peg beyond 0.5%")
        assert row["kind"] == KIND_HALT
        halted, entry = led.halted()
        assert halted and entry["entry_hash"] == row["entry_hash"]
        assert entry["payload"]["source"] == "m42:depeg:USDT"

    def test_no_halt_is_not_halted(self, led):
        led.record(KIND_ANCHOR, {"root_hash": "a" * 64})
        assert led.halted() == (False, None)

    def test_clear_halt_needs_the_halt_own_hash(self, led):
        row = led.halt("m42:chain", reason="broken chain")
        with pytest.raises(LedgerError, match="entry_hash of the HALT"):
            led.clear_halt("not-a-hash")
        led.clear_halt(row["entry_hash"], note="owner reviewed the break")
        halted, entry = led.halted()
        assert not halted and entry is None

    def test_a_clear_cannot_be_replayed_against_a_later_halt(self, led):
        first = led.halt("m42:depeg:USDT", reason="peg broke")
        second = led.halt("m42:chain", reason="chain broke")
        led.clear_halt(first["entry_hash"], note="peg recovered")
        halted, entry = led.halted()
        assert halted, "releasing the earlier halt must not release the later one"
        assert entry["entry_hash"] == second["entry_hash"]

    def test_a_clear_is_not_itself_cleared_by_a_later_clear(self, led):
        row = led.halt("m42:depeg:USDT", reason="peg broke")
        led.clear_halt(row["entry_hash"], note="one")
        led.clear_halt(row["entry_hash"], note="two")
        assert led.halted() == (False, None)

    def test_tamper_reads_as_halted_fail_closed(self, led):
        row = led.halt("m42:depeg:USDT", reason="peg broke")
        lines = led.path.read_text(encoding="utf-8").splitlines()
        rec = json.loads(lines[-1])
        rec["payload"]["reason"] = "nothing happened"
        lines[-1] = json.dumps(rec, sort_keys=True, separators=(",", ":"))
        led.path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        halted, entry = led.halted()
        assert halted, "an unverifiable chain cannot be shown to be un-halted"
        assert entry["reason"].startswith("chain unverifiable")
        with pytest.raises(LedgerTamperError):
            led.verify()


# ================================================= B. the store anchor ====

class TestPaperStoreAnchor:
    """Lane A is frozen and cannot carry a ``prev_hash`` column; the anchor is
    the one-way bridge that makes it a branch of the single chain."""

    def test_anchor_then_clean(self, led, tmp_path):
        store = _store(tmp_path, rows=[(1, "a"), (2, "b")])
        fp = _anchor(led, store)
        assert sum(fp.tables.values()) == 2 and len(fp.root_hash) == 64
        v = _verify(led, store)
        assert v.state == ANCHORED_CLEAN and v.clean
        assert led.evidence(KIND_ANCHOR)[0]["payload"]["root_hash"] == fp.root_hash

    def test_unanchored_is_not_clean(self, led, tmp_path):
        store = _store(tmp_path, rows=[(1, "a")])
        v = _verify(led, store)
        assert v.state == UNANCHORED
        assert not v.clean and v.anchor_hash is None

    def test_appended_rows_leave_the_anchor_clean(self, led, tmp_path):
        """The anchor binds a row-count prefix, so append-only growth is silent
        and stays clean: this is the asymmetry that makes the store's own
        append-only guarantee useful to the chain."""
        store = _store(tmp_path, rows=[(1, "a")])
        _anchor(led, store)
        conn = sqlite3.connect(store)
        conn.execute("INSERT INTO t VALUES (2, 'b')")
        conn.execute("INSERT INTO t VALUES (3, 'c')")
        conn.commit()
        conn.close()
        v = _verify(led, store)
        assert v.state == ANCHORED_CLEAN
        assert v.extensions == (), "row growth is not a new table"

    def test_a_table_added_since_is_reported_as_an_extension(self, led, tmp_path):
        store = _store(tmp_path, rows=[(1, "a")])
        _anchor(led, store)
        conn = sqlite3.connect(store)
        conn.execute("CREATE TABLE u (id INTEGER)")
        conn.commit()
        conn.close()
        v = _verify(led, store)
        assert v.state == ANCHORED_CLEAN
        assert v.extensions == ("u",)

    def test_an_edited_row_breaks_the_anchor(self, led, tmp_path):
        store = _store(tmp_path, rows=[(1, "a"), (2, "b")])
        _anchor(led, store)
        conn = sqlite3.connect(store)
        conn.execute("UPDATE t SET v='X' WHERE id=1")
        conn.commit()
        conn.close()
        v = _verify(led, store)
        assert v.state == ANCHORED_MISMATCH
        assert any("root hash mismatch" in f for f in v.findings),             "the row count is unchanged; the digest is what an edit moves"

    def test_a_deleted_row_breaks_the_anchor(self, led, tmp_path):
        store = _store(tmp_path, rows=[(1, "a"), (2, "b")])
        _anchor(led, store)
        conn = sqlite3.connect(store)
        conn.execute("DELETE FROM t WHERE id=1")
        conn.commit()
        conn.close()
        assert _verify(led, store).state == ANCHORED_MISMATCH

    def test_a_dropped_table_breaks_the_anchor(self, led, tmp_path):
        store = _store(tmp_path, rows=[(1, "a")])
        _anchor(led, store)
        conn = sqlite3.connect(store)
        conn.execute("ALTER TABLE t RENAME TO t_renamed")
        conn.commit()
        conn.close()
        v = _verify(led, store)
        assert v.state == ANCHORED_MISMATCH
        assert any("no longer exists" in f for f in v.findings)

    def test_the_store_is_opened_read_only(self, tmp_path):
        store = _store(tmp_path, rows=[(1, "a")])
        conn = open_store_ro(store)
        try:
            with pytest.raises(sqlite3.OperationalError):
                conn.execute("INSERT INTO t VALUES (2, 'b')")
            with pytest.raises(sqlite3.OperationalError):
                conn.execute("UPDATE t SET v='X'")
        finally:
            conn.close()

    def test_a_tampered_chain_is_reported_as_a_mismatch(self, led, tmp_path):
        store = _store(tmp_path, rows=[(1, "a")])
        _anchor(led, store)
        lines = led.path.read_text(encoding="utf-8").splitlines()
        rec = json.loads(lines[-1])
        rec["payload"]["root_hash"] = "f" * 64
        lines[-1] = json.dumps(rec, sort_keys=True, separators=(",", ":"))
        led.path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        assert _verify(led, store).state == ANCHORED_MISMATCH


# ============================================ C. treasury surveillance ====

class TestBrokerConcentration:
    """Vision §7.0: each broker <= 40% of the exposure placed."""

    def test_within_limit(self):
        v = concentration_check({"A": 100.0, "B": 100.0, "C": 100.0})
        assert v.state == WITHIN_LIMIT and v.allowed
        assert v.worst_broker == "A"           # ties break on sorted order
        assert max(v.shares.values()) == pytest.approx(100 / 3)

    def test_exactly_40_is_allowed(self):
        # the law is "<= 40%", not "< 40%": three brokers at 40/40/20 pass
        v = concentration_check({"A": 40.0, "B": 40.0, "C": 20.0},
                                limit_share=LIMIT_SHARE)
        assert v.state == WITHIN_LIMIT
        assert max(v.shares.values()) == pytest.approx(40.0)

    def test_breach(self):
        v = concentration_check({"A": 60.0, "B": 40.0})
        assert v.state == BREACH and not v.allowed
        assert any("A" in f and "60.00%" in f for f in v.findings)
        assert not any("B" in f for f in v.findings), \
            "B is exactly at the limit and must not be reported"

    def test_breach_just_over_the_line(self):
        v = concentration_check({"A": 40.01, "B": 59.99})
        assert v.state == BREACH

    def test_unmeasured_when_nothing_supplied(self):
        assert concentration_check(None).state == UNMEASURED
        assert concentration_check({}).state == UNMEASURED

    def test_unmeasured_when_the_base_is_not_positive(self):
        v = concentration_check({"A": 0.0, "B": 0.0})
        assert v.state == UNMEASURED, "a zero base makes every share unevaluable"

    def test_an_undeclared_broker_is_reported_not_assumed(self):
        v = concentration_check([BrokerExposure("A", 100.0, eligible=False),
                                 BrokerExposure("B", 100.0),
                                 BrokerExposure("C", 100.0)])
        assert v.state == WITHIN_LIMIT,             "the limit is a separate gate from eligibility"
        assert any("not declared ELIGIBLE" in f for f in v.findings)

    def test_an_explicit_denominator_is_used(self):
        v = concentration_check({"A": 30.0}, total_exposure_usd=300.0)
        assert v.shares["A"] == pytest.approx(10.0)

    def test_empty_registry_gives_no_exposures(self, tmp_path):
        p = tmp_path / "brokers.yaml"
        p.write_text("brokers: []\n", encoding="utf-8")
        assert exposures_from_registry({"brokers": []}) == []
        assert exposures_from_registry({}) == []
        # a row without a declared exposure is skipped, never assumed
        assert exposures_from_registry(
            {"brokers": [{"broker_id": "A"}, {"broker_id": "B", "exposure_usd": 1}]}) == [
            BrokerExposure("B", 1.0)]


class TestUsdtDepeg:
    """Vision §7.0: a USDT deviation beyond 0.5% halts, and the owner's
    two-source law applies to the peg as it does to every other price."""

    def test_armed_within_the_band(self):
        v = depeg_check(_quotes(0.0, 0.0002))
        assert v.state == ARMED and v.allowed
        assert v.deviation_pct < 0.5

    def test_depeg_beyond_the_threshold(self):
        v = depeg_check(_quotes(-0.007, -0.005))     # mean 0.994 -> 0.6% away
        assert v.state == DEPEG and not v.allowed
        assert v.deviation_pct > 0.5
        assert any("HALT" in f for f in v.findings)

    def test_one_quote_certifies_nothing(self):
        v = depeg_check(_quotes(0.0))
        assert v.state == UNMEASURED
        assert any("two-source law" in f for f in v.findings)

    def test_no_quote_is_unmeasured(self):
        assert depeg_check(()).state == UNMEASURED

    def test_two_disagreeing_quotes_are_unmeasured(self):
        v = depeg_check(_quotes(0.0, 0.05))          # ~5% apart
        assert v.state == UNMEASURED
        assert any("disagree" in f for f in v.findings)

    def test_a_quote_from_the_same_provider_is_deduped(self):
        q = (StableQuote("dup", 1.0, observed_at=1.0),
             StableQuote("dup", 1.0001, observed_at=2.0))
        assert depeg_check(q).state == UNMEASURED

    def test_a_non_positive_quote_is_dropped(self):
        v = depeg_check((StableQuote("a", 0.0, 1.0), StableQuote("b", 1.0, 2.0)))
        assert v.state == UNMEASURED

    @pytest.mark.parametrize("exposures", [None, {}])
    def test_findings_are_a_tuple_of_strings(self, exposures):
        """Regression: the single-string ``findings=(...)`` constructions were
        parenthesised strings, not 1-tuples, so a caller iterating them read
        one *character* per finding and the recorded chain filled with noise."""
        v = concentration_check(exposures)
        assert isinstance(v.findings, tuple) and v.findings
        assert all(isinstance(f, str) for f in v.findings)

    def test_an_unreachable_feed_is_not_a_depeg(self):
        """Regression: an unmeasured peg used to raise ``R-DEPEG``, which made
        it indistinguishable from a peg that broke -- a watchdog keying on that
        code would page on a network blip. The gap now carries its own code."""
        v = depeg_check(())
        assert v.state == UNMEASURED
        assert not any("HALT" in f for f in v.findings)


# ============================================ D. the reconcile driver ====

class TestReconcileDriver:
    """Every leg, worst-first verdicts, and the HALT that a mismatch sounds."""

    def test_clean_reconcile_records_and_halts_nothing(self, led, paper_leg):
        m = _closing_track(led)
        report = run_reconcile(
            led, mission_id=m,
            statement={"counterparty": "tmp", "trades": [],
                       "exposures": {"A": 100.0, "B": 100.0, "C": 100.0}},
            depeg_quotes=_quotes(0.0, 0.0001),
            agent=AG)
        assert report.verdict == CLEAN and report.clean
        assert not report.halt_recorded
        assert led.evidence(KIND_RECONCILE)
        halted, _ = led.halted()
        assert not halted

    def test_paper_reconcile_finds_the_difference(self, led, paper_leg):
        m = _closing_track(led)
        report = run_reconcile(led, mission_id=m, record=False)
        assert report.verdict == CLEAN
        # now flatter the equity in the final checkpoint: the judge must catch
        # a number the track itself wrote
        lines = led.path.read_text(encoding="utf-8").splitlines()
        rec = json.loads(lines[-1])
        rec["state"]["CHECKPOINT"]["equity_usd"] = 12345.0
        lines[-1] = json.dumps(rec, sort_keys=True, separators=(",", ":"))
        led.path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        with pytest.raises(LedgerTamperError):
            led.verify()
        bad = run_reconcile(led, mission_id=m, record=False)
        assert bad.verdict == BROKEN_CHAIN

    def test_a_judge_discrepancy_is_a_discrepancy(self, led, paper_leg):
        m = _closing_track(led)
        lines = led.path.read_text(encoding="utf-8").splitlines()
        rec = json.loads(lines[-1])
        rec["state"]["CHECKPOINT"]["cumulative_realized_pnl_usd"] = 999.0
        # recompute this entry's own hash so the chain stays intact and the
        # break is *only* the track's claim -- the judge, not the chain, fires
        body = {k: v for k, v in rec.items() if k != "entry_hash"}
        rec["entry_hash"] = _sha(canonical_json(body))
        lines[-1] = json.dumps(rec, sort_keys=True, separators=(",", ":"))
        led.path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        assert led.verify()["verdict"] == "CHAIN_INTACT"
        assert judge_paper_ledger(led, m).verdict == DISCREPANCY
        report = run_reconcile(led, mission_id=m, record=False)
        assert report.verdict == DISCREPANCY
        assert any(f.code == "R-PAPER" for f in report.findings)

    def test_concentration_breach_halts(self, led, paper_leg):
        m = _flat_track(led)
        report = run_reconcile(
            led, mission_id=m,
            statement={"counterparty": "tmp", "trades": [],
                       "exposures": {"only-broker": 100.0}},
            agent=AG)
        assert report.verdict == DISCREPANCY
        assert any(f.code == "R-CONCENTRATION" for f in report.findings)
        assert report.halt_recorded
        halted, entry = led.halted()
        assert halted and entry["payload"]["source"] == "m42:concentration"

    def test_depeg_breach_halts(self, led, paper_leg):
        m = _flat_track(led)
        report = run_reconcile(led, mission_id=m, agent=AG,
                               depeg_quotes=_quotes(-0.007, -0.005))
        assert report.verdict == DISCREPANCY
        assert any(f.code == "R-DEPEG" for f in report.findings)
        halted, entry = led.halted()
        assert halted and entry["payload"]["source"] == "m42:depeg:USDT"

    def test_counterparty_arithmetic_is_a_discrepancy(self, led, paper_leg):
        m = _flat_track(led)
        trade = _t("F1", 2.0, 2000.0, 2010.0, 4000.0, 2.0, net=1_000_000.0)
        report = run_reconcile(
            led, mission_id=m,
            statement={"counterparty": "tmp", "trades": [trade],
                       "exposures": {"A": 4000.0, "B": 4000.0}},
            agent=AG)
        assert report.verdict == DISCREPANCY
        assert any(f.code == "R-ARITHMETIC" for f in report.findings)

    def test_counterparty_arithmetic_passes_when_it_re_derives(self):
        trade = _t("F1", 2.0, 2000.0, 2010.0, 4000.0, 2.0,
                   net=2.0 * (2010.0 - 2000.0) - 2.0)
        findings, conc = check_statement(
            [trade], exposures={"A": 4000.0, "B": 4000.0, "C": 4000.0})
        assert findings == [] and conc.state == WITHIN_LIMIT

    def test_an_open_fill_has_no_pnl_to_check(self):
        findings, _ = check_statement(
            [_t("F1", 2.0, 2000.0, None, 4000.0, 1.0)],
            exposures={"A": 4000.0, "B": 4000.0, "C": 4000.0})
        assert findings == [],             "an open fill has no PnL identity to check and nothing else to say"

    def test_an_unreadable_statement_halts_rather_than_crashing(self, led, paper_leg):
        """Vision §11.0 lists a broker API anomaly among the halt triggers, so a
        statement that cannot be read must produce a verdict and a recorded stop
        -- not a traceback a watchdog would read as a crash."""
        m = _flat_track(led)
        report = run_reconcile(
            led, mission_id=m,
            statement={"counterparty": "tmp", "trades": [
                {"external_ref": "F1", "qty": "not-a-number"}]},
            agent=AG)
        assert report.verdict == DISCREPANCY
        assert any(f.code == "R-COUNTERPARTY" and "could not be read" in f.detail
                   for f in report.findings)
        halted, entry = led.halted()
        assert halted and entry["payload"]["source"] == "m42:counterparty"

    def test_a_statement_object_that_raises_halts_too(self, led, paper_leg):
        """The same law holds for a real adapter object as for a dict: an
        adapter whose ``statement()`` raises is reported, not propagated."""
        class BrokenAdapter:
            def statement(self):
                raise ConnectionError("broker unreachable")

        m = _flat_track(led)
        report = run_reconcile(led, mission_id=m, agent=AG,
                               statement=BrokenAdapter())
        assert report.verdict == DISCREPANCY
        assert any("broker unreachable" in f.detail for f in report.findings)
        assert report.halt_recorded

    def test_an_empty_statement_is_unmeasured_not_clean(self, led, paper_leg):
        m = _flat_track(led)
        report = run_reconcile(led, mission_id=m, agent=AG,
                               statement={"counterparty": "tmp", "trades": []})
        assert report.verdict == UNKNOWN, "an unmeasured leg is not certified"
        assert any(f.code == "R-COUNTERPARTY" for f in report.findings)
        assert not report.halt_recorded, "an unmeasured limit is not an emergency"

    def test_missing_quotes_are_unmeasured_not_clean(self, led, paper_leg):
        m = _flat_track(led)
        report = run_reconcile(led, mission_id=m, agent=AG,
                               statement={"counterparty": "tmp", "trades": [],
                                          "exposures": {"A": 1.0, "B": 1.0, "C": 1.0}},
                               depeg_quotes=())
        assert report.verdict == UNKNOWN
        assert not report.halt_recorded

    def test_a_prior_halt_governs_and_is_not_cleared(self, led, paper_leg):
        led.halt("m42:depeg:USDT", reason="an earlier reconcile sounded this")
        m = _flat_track(led)
        report = run_reconcile(
            led, mission_id=m,
            statement={"counterparty": "tmp", "trades": [],
                       "exposures": {"A": 1.0, "B": 1.0, "C": 1.0}},
            agent=AG)
        assert report.verdict == HALTED
        assert any(f.code == "R-HALTED" for f in report.findings)
        halted, _ = led.halted()
        assert halted, "the reconcile reported the halt and left it standing"
        # one more reconcile cannot lift it; only the owner's clear can
        run_reconcile(led, mission_id=m, agent=AG,
                      statement={"counterparty": "tmp", "trades": [],
                                 "exposures": {"A": 1.0, "B": 1.0, "C": 1.0}})
        assert led.halted()[0]

    def test_dry_run_writes_nothing(self, led, paper_leg):
        m = _flat_track(led)
        run_reconcile(led, mission_id=m, record=False,
                      statement={"counterparty": "tmp", "trades": [],
                                 "exposures": {"only": 100.0}})
        assert led.evidence(KIND_RECONCILE) == []
        assert led.evidence(KIND_HALT) == []
        assert not led.halted()[0]

    def test_the_binding_path_binds_and_stays_renderable(self, led, monkeypatch,
                                                         tmp_path):
        """First run: the store is unanchored, so the reconcile binds it and the
        report must still render -- the binding returns a bare fingerprint, and
        the report renders an AnchorVerdict."""
        store = _store(tmp_path, rows=[(1, "a")])
        import architecture.treasury.reconcile as rec
        monkeypatch.setattr(rec, "verify_paper_anchor", lambda *a, **k: _verify(led, store))
        monkeypatch.setattr(rec, "anchor_paper_store", lambda *a, **k: _anchor(led, store))
        m = _flat_track(led)

        report = run_reconcile(
            led, mission_id=m,
            statement={"counterparty": "tmp", "trades": [],
                       "exposures": {"A": 1.0, "B": 1.0, "C": 1.0}},
            depeg_quotes=_quotes(0.0, 0.0001), agent=AG)

        assert report.verdict == CLEAN
        assert report.anchor is not None and report.anchor.state == ANCHORED_CLEAN
        assert led.evidence(KIND_ANCHOR), "the store was bound to the chain"
        # the regression: the report renders without an AttributeError, and the
        # verdict was actually recorded (not swallowed into an R-RECORD finding)
        assert any(e["kind"] == KIND_RECONCILE for e in led.entries())
        assert not any(f.code == "R-RECORD" for f in report.findings)
        out = tmp_path / "reconcile.md"
        write_reconcile_report(report, out)
        text = out.read_text(encoding="utf-8")
        assert "ANCHORED_CLEAN" in text and "Verdict: CLEAN" in text

    def test_a_record_failure_is_reported_not_silenced(self, led, paper_leg, monkeypatch):
        m = _flat_track(led)

        def boom(*args, **kwargs):
            raise RuntimeError("disk on fire")

        monkeypatch.setattr(MissionLedger, "record", boom)
        report = run_reconcile(
            led, mission_id=m,
            statement={"counterparty": "tmp", "trades": [],
                       "exposures": {"A": 1.0, "B": 1.0, "C": 1.0}}, agent=AG)
        assert any(f.code == "R-RECORD" and "disk on fire" in f.detail
                   for f in report.findings)
        assert not report.recorded

    def test_report_styles_a_discrepancy_honestly(self, led, paper_leg, tmp_path):
        m = _flat_track(led)
        report = run_reconcile(led, mission_id=m, agent=AG,
                               depeg_quotes=_quotes(-0.007, -0.005))
        out = tmp_path / "d.md"
        write_reconcile_report(report, out)
        text = out.read_text(encoding="utf-8")
        assert "**Verdict: DISCREPANCY**" in text
        assert "R-DEPEG" in text and "PAPER_ONLY" in text


# ======================================== E. the acceptance criteria ====

class TestM42Acceptance:
    """The three tests the owner's plan names (line 407)."""

    def test_acceptance_tampering_breaks_the_chain(self, led, paper_leg):
        _closing_track(led)
        assert led.verify()["verdict"] == "CHAIN_INTACT"
        lines = led.path.read_text(encoding="utf-8").splitlines()
        rec = json.loads(lines[-1])
        rec["state"]["CHECKPOINT"]["equity_usd"] = 999_999.0
        lines[-1] = json.dumps(rec, sort_keys=True, separators=(",", ":"))
        led.path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        with pytest.raises(LedgerTamperError):
            led.verify()
        report = run_reconcile(led, mission_id="M42-TEST-PAPER", record=False)
        assert report.verdict == BROKEN_CHAIN, \
            "a rewritten ledger is not evidence at all, let alone a discrepancy"

    def test_acceptance_paper_reconcile_has_zero_differences(self, led, paper_leg):
        m = _closing_track(led)
        report = run_reconcile(
            led, mission_id=m,
            statement={"counterparty": "tmp", "trades": [],
                       "exposures": {"A": 100.0, "B": 100.0, "C": 100.0}},
            depeg_quotes=_quotes(0.0, 0.0001), agent=AG)
        assert report.verdict == CLEAN
        assert report.paper is not None and report.paper.verdict == CLEAN
        assert report.paper.findings == ()
        assert report.anchor is not None and report.anchor.clean
        assert report.concentration is not None and report.concentration.allowed
        assert report.depeg is not None and report.depeg.allowed

    def test_acceptance_per_broker_concentration(self):
        v = concentration_check({"A": 100.0, "B": 100.0, "C": 100.0})
        assert v.state == WITHIN_LIMIT
        assert max(v.shares.values()) <= LIMIT_SHARE * 100.0
        assert concentration_check({"only-broker": 100.0}).state == BREACH
        # the driver wires the same limit into a halt
        assert concentration_check({"A": 41.0, "B": 59.0}).state == BREACH


# ================================================ F. the authority laws ===

class TestAuthorityLaws:
    """The treasury observes and reports; it is not a decision authority, and
    there is one ledger, not two competing chains."""

    def test_no_authority_code_is_imported(self):
        """The M42 reconcile surface may read the ledger and the providers, but
        it must not import the decision, risk, positions or scoring authorities
        -- an observer that imports an authority can be coerced into trusting
        it, and a reconcile that calls a scorer is auditing its own auditor.

        Scoped to the M42 surface itself: ``architecture/markets`` also carries
        M13's gold paper track, which legitimately reads the paper lab's own
        exit rules, and that is not this law's business.
        """
        files = [
            ROOT / "architecture" / "treasury" / "reconcile.py",
            ROOT / "architecture" / "treasury" / "surveillance.py",
            ROOT / "architecture" / "markets" / "paper_anchor.py",
            ROOT / "architecture" / "markets" / "judge.py",
            ROOT / "scripts" / "m42_nightly_reconcile.py",
        ]
        bad_roots = {"discovery", "engine", "telegram_ai"}
        bad_pkgs = {"architecture.decision", "architecture.risk",
                    "architecture.positions", "architecture.scoring"}
        hits = []
        for f in files:
            tree = ast.parse(f.read_text(encoding="utf-8"))
            mods = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    mods.update(a.name for a in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    mods.add(node.module)
            for m in mods:
                if m.split(".")[0] in bad_roots or m in bad_pkgs:
                    hits.append((f.name, m))
        assert hits == [], hits

    def test_there_is_one_chain_not_two(self):
        """Lane A is frozen, so the paper store cannot gain a ``prev_hash``
        column; the anchor is the bridge, and ``paper_trading/ledger.py`` must
        not grow a second hash chain of its own."""
        src = (ROOT / "paper_trading" / "ledger.py").read_text(encoding="utf-8")
        tree = ast.parse(src)
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.Attribute):
                names.add(node.attr)
        assert "prev_hash" not in names and "entry_hash" not in names, \
            "a second chain in the paper lab would split the single ledger"

    def test_every_reconcile_row_declares_paper_only(self, led, paper_leg):
        m = _flat_track(led)
        run_reconcile(led, mission_id=m, agent=AG,
                      statement={"counterparty": "tmp", "trades": [],
                                 "exposures": {"A": 1.0, "B": 1.0, "C": 1.0}})
        rows = led.evidence(KIND_RECONCILE)
        assert rows
        assert all(r["payload"]["paper_only"] is True for r in rows)
        assert all(r["authority"] == "NONE" for r in rows)

    def test_the_evidence_kinds_are_the_shared_surface(self):
        assert EVIDENCE_KINDS == frozenset(
            {KIND_ANCHOR, KIND_RECONCILE, KIND_HALT, KIND_HALT_CLEARED, KIND_DECISION})

    def test_report_type_holds_every_leg(self):
        r = ReconcileReport(CLEAN)
        assert r.verdict == CLEAN and r.clean
        assert r.findings == () and r.notes == ()
        assert not r.recorded and not r.halt_recorded
        f = Finding("R-DEPEG", "peg broke")
        assert (Finding("R-DEPEG", "peg broke") == f)   # stable codes, hashable


# --------------------------------------------------------------- the CLI ---

class TestTheCli:
    """The driver is runnable and its exit codes mean what the docstring says.

    Called in-process rather than through a subprocess: a subprocess would
    re-import the modules fresh and lose the monkeypatched paper leg, which
    would send it at the live store and the live price feeds -- exactly what a
    self-test must not do.
    """

    @pytest.fixture()
    def cli(self):
        import importlib
        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            return importlib.import_module("m42_nightly_reconcile")
        finally:
            sys.path.remove(str(ROOT / "scripts"))

    def test_cli_dry_run_over_a_tmp_ledger(self, led, paper_leg, cli, tmp_path):
        m = _flat_track(led)
        registry = tmp_path / "none.yaml"
        registry.write_text("brokers: []\n", encoding="utf-8")
        out = tmp_path / "dry.md"
        rc = cli.main(["--ledger", str(led.path), "--mission", m,
                       "--no-depeg", "--dry-run",
                       "--broker-registry", str(registry), "--out", str(out)])
        # UNKNOWN, not CLEAN: a leg was requested and could not be measured
        assert rc == 1
        assert not led.evidence(KIND_RECONCILE), "a dry run wrote to the chain"
        assert "Verdict: UNKNOWN" in out.read_text(encoding="utf-8")

    def test_cli_depeg_only_needs_no_ledger(self, cli, monkeypatch):
        """The peg leg stands alone: a soak that only wants the peg should not
        need a ledger to get it."""
        monkeypatch.setattr(cli, "collect_usdt_quotes",
                            lambda **k: list(_quotes(0.0, 0.0001)))
        assert cli.main(["--depeg-only"]) == 0
        monkeypatch.setattr(cli, "collect_usdt_quotes",
                            lambda **k: list(_quotes(-0.007, -0.005)))
        assert cli.main(["--depeg-only"]) == 1

    def test_cli_records_a_live_run(self, led, paper_leg, cli, monkeypatch, tmp_path):
        m = _flat_track(led)
        monkeypatch.setattr(cli, "collect_usdt_quotes",
                            lambda **k: list(_quotes(0.0, 0.0001)))
        registry = tmp_path / "none.yaml"
        registry.write_text("brokers: []\n", encoding="utf-8")
        out = tmp_path / "live.md"
        rc = cli.main(["--ledger", str(led.path), "--mission", m,
                       "--broker-registry", str(registry),
                       "--out", str(out)])
        assert rc == 1                                     # UNKNOWN, honestly
        rows = led.evidence(KIND_RECONCILE)
        assert rows and rows[-1]["payload"]["paper_only"] is True
        assert "**Verdict: UNKNOWN**" in out.read_text(encoding="utf-8")

