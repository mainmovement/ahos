#!/usr/bin/env python3
"""Wave-8 CONTINUATION tests — realizable truth, autonomous decisions, partial exits,
learning loop. Same laws: exact math, UNKNOWN never fabricated, no look-ahead,
mark-price fiction banned, append-only enforced."""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

import pytest

from paper_trading import bankroll, decision_v3 as dv3, engine_v3, engine_v2 as ev2
from paper_trading import entry_rules, ledger, lessons, realizable as rz, reports

ROOT = Path(__file__).resolve().parents[1]
T0 = 1_800_000_000.0


# ------------------------------------------------------------------ fixtures/helpers
def mk_paper(tmp_path):
    conn = ledger.open_paper(tmp_path / "paper.sqlite")
    bankroll.ensure_v2_schema(conn)
    engine_v3.ensure_v3_schema(conn)
    bankroll.init_bankroll(conn, T0)
    return conn


def mk_discovery(tmp_path):
    path = tmp_path / "disc.sqlite"
    conn = sqlite3.connect(path)
    conn.executescript((ROOT / "discovery" / "schema_sqlite.sql").read_text())
    conn.close()
    return path


def add_obs(tmp_path, disc_path, token_id, ts, price, liq):
    conn = sqlite3.connect(disc_path)
    conn.execute(
        """INSERT INTO discovery_observations(obs_id,token_id,pair_id,provider,retrieved_ts,
               price_usd,liquidity_usd,volume_24h,raw_ref)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (f"obs-{token_id}-{ts}", token_id, "pair-1", "test", ts, price, liq, 1000.0, "raw-x"))
    conn.commit(); conn.close()


def mk_trade(conn, token_id="T1", qty=2.0, price=1.0, alloc=2.0, liq=1e6,
             sell_tax=None, chain="solana", security_class="MEDIUM_RISK", entry_ts=T0):
    sid = ev2._snap_v2(conn, token_id=token_id, chain=chain, address="0x" + token_id,
                       symbol=token_id, cohort="NEW_LAUNCH", discovered_ts=entry_ts - 3600,
                       decision_ts=entry_ts,
                       features={"as_of": entry_ts, "price_usd": price, "liquidity_usd": liq},
                       security={"verdict": "PASS_WITH_UNKNOWN",
                                 "taxes": {"buy_tax_bps": None, "sell_tax_bps": sell_tax,
                                          "transfer_tax_bps": None},
                                 "checks": []},
                       decision="QUALIFIED_ENTRY", reason="test", cfg=entry_rules.BANKROLL_V2)
    tid = f"trade-{token_id}"
    conn.execute(
        """INSERT INTO paper_trade_v2(trade_id,strategy_version,snapshot_id,token_id,chain,
               address,symbol,cohort,discovered_ts,entry_decision_ts,entry_ts,
               entry_price_observed,bankroll_before,amount_allocated,qty,fee_entry_usd,
               entry_slippage_bps,entry_price_exec,liq_at_entry,expected_exit_liquidity_usd,
               buy_tax_bps,sell_tax_bps,transfer_tax_bps,cost_completeness,security_class,
               execution_class,opportunity_class,exit_rule_version,monitoring_horizon_ts,
               created_utc)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (tid, "PT-BANKROLL-v2", sid, token_id, chain, "0x" + token_id, token_id, "NEW_LAUNCH",
         entry_ts - 3600, entry_ts, entry_ts, price, 20.0, alloc, qty, 0.02, 25.0, price, liq, liq,
         None, sell_tax, None, "PARTIAL(taxes UNKNOWN)" if sell_tax is None else "FULL",
         security_class, "EXECUTABLE_OK", "MEDIUM", "PT-X3-v1", entry_ts + 48 * 3600,
         "2026-08-12T00:00:00+00:00"))
    bankroll.allocate(conn, entry_ts, tid, alloc, "test alloc")
    ledger.monitor(conn, tid, entry_ts, entry_ts, price, liq, 1000.0, "ENTRY", "t")
    conn.commit()
    return tid


def decide_kw(**over):
    base = dict(now=T0 + 60, allocated=2.0, qty_remaining=2.0, entry_price_exec=1.0,
                entry_ts=T0, obs_price=1.0, obs_liq=1e6, obs_ts=T0 + 30,
                consec_liq_breaches=0, sec_veto_now=False, escalations=[],
                sell_tax_bps=None, chain="solana", classification="MEDIUM_RISK",
                monitor_peak_price=1.0, monitor_obs_count=2, base_hit=None)
    return base | over


# ------------------------------------------------------------------ PT-REALIZABLE-v1 pure math
def test_partial_cap_math_exact():
    a = rz.assess(qty=100.0, price_obs=1.0, liq_now=100.0, sell_tax_bps=None,
                  chain="bsc", classification="MEDIUM_RISK")
    assert a["route_status"] == "EXECUTABLE_PARTIAL"
    assert a["max_executable_notional_usd"] == pytest.approx(15.0)
    assert a["executable_exit_notional_usd"] == pytest.approx(15.0)
    assert a["exit_slippage_bps"] == pytest.approx(1500.0)
    # gross 15*0.85=12.75; fee 1% on post-slip =0.1275; tax UNKNOWN→None; gas bsc 0.10
    assert a["exit_fee_usd"] == pytest.approx(0.1275)
    assert a["sell_tax_usd"] is None
    assert a["realizable_value_usd"] == pytest.approx(12.75 - 0.1275 - 0.10)
    assert a["displayed_value_usd"] == pytest.approx(100.0)
    assert a["unexited_displayed_usd"] == pytest.approx(85.0)


def test_full_exec_small_position():
    a = rz.assess(qty=2.0, price_obs=1.0, liq_now=21000.0, sell_tax_bps=None,
                  chain="solana", classification="MEDIUM_RISK")
    assert a["route_status"] == "EXECUTABLE_FULL" and a["sellable_full"]
    assert a["exit_slippage_bps"] == pytest.approx(25.0)      # structural floor
    # gross 2*0.9975 = 1.995; fee 0.01995; gas sol 0.02
    assert a["realizable_value_usd"] == pytest.approx(1.995 - 0.01995 - 0.02)


def test_honeypot_realizable_zero():
    a = rz.assess(qty=10.0, price_obs=5.0, liq_now=1e6, sell_tax_bps=None,
                  chain="bsc", classification="CONFIRMED_HONEYPOT")
    assert a["route_status"] == "UNEXITABLE_HONEYPOT"
    assert a["realizable_value_usd"] == 0.0                   # displayed $50 is fiction


def test_unpriceable_states_honest():
    a = rz.assess(qty=10.0, price_obs=None, liq_now=1e6, sell_tax_bps=None,
                  chain="bsc", classification="MEDIUM_RISK")
    assert a["route_status"] == "UNEXITABLE_NO_PRICE"
    b = rz.assess(qty=10.0, price_obs=1.0, liq_now=None, sell_tax_bps=None,
                  chain="bsc", classification="MEDIUM_RISK")
    assert b["route_status"] == "UNEXITABLE_NO_LIQUIDITY"
    assert b["displayed_value_usd"] == pytest.approx(10.0)    # displayed kept, realizable 0
    assert b["realizable_value_usd"] == 0.0


def test_sell_tax_deducted_exact():
    a = rz.assess(qty=2.0, price_obs=1.0, liq_now=21000.0, sell_tax_bps=1000.0,
                  chain="bsc", classification="MEDIUM_RISK")
    gross = 2.0 * 0.9975
    assert a["sell_tax_usd"] == pytest.approx(gross * 0.10)
    assert a["realizable_value_usd"] == pytest.approx(gross - gross * 0.01 - gross * 0.10 - 0.10)


def test_chunk_merge_and_dust():
    # remainder below $0.25 merges to FULL
    a = rz.assess(qty=100.1, price_obs=1.0, liq_now=667.0, sell_tax_bps=None,
                  chain="bsc", classification="MEDIUM_RISK")
    assert rz.executable_chunk(a)["kind"] == "FULL"
    # dust: liq so small the executable chunk is < $0.05
    b = rz.assess(qty=10.0, price_obs=1.0, liq_now=0.2, sell_tax_bps=None,
                  chain="bsc", classification="MEDIUM_RISK")
    assert b["route_status"] == "UNEXITABLE_DUST"


# ------------------------------------------------------------------ PT-X3-v1 decisions (pure)
def test_hold_healthy_position():
    d = dv3.decide(**decide_kw())
    assert d["action"] == "HOLD"


def test_trapped_on_realizable_less_than_10pct():
    # displayed $0.15 on ethereum: gas $0.80 eats everything → TOTAL_LOSS
    d = dv3.decide(**decide_kw(obs_price=0.075, qty_remaining=2.0, chain="ethereum"))
    assert d["action"] == "TOTAL_LOSS"
    assert "realizable" in d["why"]


def test_no_liq_is_no_data_not_trap():
    d = dv3.decide(**decide_kw(obs_liq=None))
    assert d["action"] == "NO_DATA"                            # UNKNOWN never becomes TRAP


def test_divergence_profit_lock_banks_real():
    d = dv3.decide(**decide_kw(obs_price=2.2, obs_liq=1e6, monitor_peak_price=2.1))
    # displayed 4.4 ≥ 3×2=6? no → need bigger
    assert d["action"] == "HOLD"
    d2 = dv3.decide(**decide_kw(obs_price=3.4, obs_liq=1e6, monitor_peak_price=3.5,
                                monitor_obs_count=2))
    assert d2["action"] == "FULL_EXIT" and d2["reason"] == "DIVERGENCE_PROFIT_LOCK"


def test_decay_profit_lock():
    d = dv3.decide(**decide_kw(obs_price=1.6, obs_liq=1e6, monitor_peak_price=2.2,
                               monitor_obs_count=3))
    # realizable ~3.1 ≥ 1.5×2=3 and price 1.6 ≤ 0.85×2.2=1.87
    assert d["action"] == "FULL_EXIT" and d["reason"] == "DECAY_PROFIT_LOCK"


def test_security_flip_risk_exit_while_sellable():
    d = dv3.decide(**decide_kw(classification="CRITICAL_RISK", sec_veto_now=True))
    assert d["action"] == "RISK_EXIT" and d["reason"] == "SECURITY_EVENT"


def test_base_tp_becomes_partial_when_capped():
    hit = {"reason": "TAKE_PROFIT", "detail": "tp"}
    d = dv3.decide(**decide_kw(obs_price=2.0, obs_liq=20.0, base_hit=hit))  # displayed 4 > cap 3
    assert d["action"] == "PARTIAL_EXIT" and d["reason"] == "TAKE_PROFIT"
    assert d["assess"]["executable_exit_notional_usd"] == pytest.approx(3.0)


# ------------------------------------------------------------------ integration: engine_v3
def test_cycle_partial_then_full_close_lesson_and_conservation(tmp_path):
    disc = mk_discovery(tmp_path)
    conn = mk_paper(tmp_path)
    tid = mk_trade(conn, token_id="T1", qty=2.0, price=1.0, alloc=2.0)
    conn.close()
    now1 = T0 + 60
    add_obs(tmp_path, disc, "T1", T0 + 30, price=2.0, liq=20.0)     # TP hit; cap = 3.0 < 4.0
    st1 = engine_v3.run_cycle_v3(str(tmp_path / "paper.sqlite"), str(disc), now=now1, pal=None)
    assert st1["partials"] == 1 and st1["exits"] == 0
    p1 = sqlite3.connect(str(tmp_path / "paper.sqlite")); p1.row_factory = sqlite3.Row
    rows = p1.execute("SELECT * FROM paper_exit_v3 WHERE trade_id=?", (tid,)).fetchall()
    assert len(rows) == 1 and rows[0]["exit_kind"] == "PARTIAL"
    net1 = rows[0]["net_proceeds_usd"]
    # exactness: notional 3.0, slip 1500bps → gross 2.55, fee 0.0255, tax None, gas 0.02
    assert net1 == pytest.approx(2.55 - 0.0255 - 0.02)
    assert rows[0]["qty_sold"] == pytest.approx(1.5)
    assert p1.execute("SELECT cash_after FROM portfolio_ledger ORDER BY id DESC LIMIT 1"
                      ).fetchone()[0] == pytest.approx(18.0 + net1)
    # states: PARTIAL_EXIT logged
    assert p1.execute("SELECT COUNT(*) FROM position_state_event WHERE trade_id=? AND "
                      "state='PARTIAL_EXIT'", (tid,)).fetchone()[0] == 1
    p1.close()

    st2 = engine_v3.run_cycle_v3(str(tmp_path / "paper.sqlite"), str(disc), now=T0 + 120, pal=None)
    assert st2["exits"] == 1 and st2["partials"] == 0
    p2 = sqlite3.connect(str(tmp_path / "paper.sqlite")); p2.row_factory = sqlite3.Row
    rows = p2.execute("SELECT * FROM paper_exit_v3 WHERE trade_id=? ORDER BY exit_seq",
                      (tid,)).fetchall()
    assert len(rows) == 2 and rows[1]["exit_kind"] == "FULL"
    # remainder 0.5@2.0=1.0 notional, slip max(25, 500)=500bps → gross .95, fee .0095, gas .02
    net2 = rows[1]["net_proceeds_usd"]
    assert net2 == pytest.approx(0.95 - 0.0095 - 0.02)
    cash = p2.execute("SELECT cash_after FROM portfolio_ledger ORDER BY id DESC LIMIT 1"
                      ).fetchone()[0]
    realized_total = (net1 + net2) - 2.0
    assert cash == pytest.approx(20.0 + realized_total)         # every dollar accounted
    # lesson recorded with required structure
    les = p2.execute("SELECT * FROM post_trade_lesson WHERE trade_id=?", (tid,)).fetchone()
    assert les is not None and les["outcome_class"] == "PROFIT"
    ans = json.loads(les["answers_json"])
    for key in ("what_we_believed_before_entry", "evidence_missing_at_entry",
                "what_actually_happened", "did_security_miss_anything"):
        assert key in ans
    assert "UNAVAILABLE_NO_FEED" in ans["did_social_news_help_or_mislead"]
    assert les["hypothesis"] and les["lesson"] and les["proposed_improvement"]
    # stats snapshot appended
    assert p2.execute("SELECT COUNT(*) FROM learning_stats_snapshot").fetchone()[0] >= 2
    stats = json.loads(p2.execute("SELECT stats_json FROM learning_stats_snapshot ORDER BY id DESC "
                                  "LIMIT 1").fetchone()[0])
    assert stats["profitable_trades"] == 1 and stats["partial_exits_taken"] == 1
    # final state EXITED_PROFIT
    last = p2.execute("SELECT state FROM position_state_event WHERE trade_id=? ORDER BY id DESC "
                      "LIMIT 1", (tid,)).fetchone()[0]
    assert last == "EXITED_PROFIT"
    p2.close()


def test_total_loss_gas_trap_booked_honestly(tmp_path):
    disc = mk_discovery(tmp_path)
    conn = mk_paper(tmp_path)
    tid = mk_trade(conn, token_id="T2", qty=2.0, price=0.075, alloc=2.0, chain="ethereum")
    conn.close()
    add_obs(tmp_path, disc, "T2", T0 + 30, price=0.075, liq=1e6)     # displayed $0.15 < gas
    st = engine_v3.run_cycle_v3(str(tmp_path / "paper.sqlite"), str(disc), now=T0 + 60, pal=None)
    assert st["trapped"] == 1
    p = sqlite3.connect(str(tmp_path / "paper.sqlite")); p.row_factory = sqlite3.Row
    x = p.execute("SELECT * FROM paper_exit_v3 WHERE trade_id=?", (tid,)).fetchone()
    assert x["exit_reason"] == "TOTAL_LOSS" and x["net_proceeds_usd"] == pytest.approx(0.0)
    assert x["capital_loss_usd"] == pytest.approx(2.0)
    assert p.execute("SELECT cash_after FROM portfolio_ledger ORDER BY id DESC LIMIT 1"
                     ).fetchone()[0] == pytest.approx(18.0)
    les = p.execute("SELECT outcome_class FROM post_trade_lesson WHERE trade_id=?",
                    (tid,)).fetchone()
    assert les[0] == "TOTAL_LOSS"
    p.close()


def test_no_lookahead_future_obs_irrelevant(tmp_path):
    """A future rug/pump may never justify an earlier decision: replaying the same decision
    time with future observations injected must produce IDENTICAL exits."""
    outs = []
    for tag, future in (("a", False), ("b", True)):
        (tmp_path / tag).mkdir(parents=True, exist_ok=True)
        disc = mk_discovery(tmp_path / tag)
        conn = mk_paper(tmp_path / tag)
        tid = mk_trade(conn, token_id="T3", qty=2.0, price=1.0, alloc=2.0)
        conn.close()
        add_obs(tmp_path / tag, disc, "T3", T0 + 30, price=2.0, liq=20.0)
        if future:
            add_obs(tmp_path / tag, disc, "T3", T0 + 99999, price=0.0001, liq=1.0)  # future rug
        st = engine_v3.run_cycle_v3(str(tmp_path / tag / "paper.sqlite"), str(disc),
                                    now=T0 + 60, pal=None)
        outs.append((st["partials"], st["exits"]))
    assert outs[0] == outs[1] == (1, 0)


def test_append_only_v3_tables(tmp_path):
    conn = mk_paper(tmp_path)
    tid = mk_trade(conn, token_id="T4")
    a = rz.assess(qty=2.0, price_obs=1.0, liq_now=1e6, sell_tax_bps=None,
                  chain="solana", classification="MEDIUM_RISK")
    engine_v3.record_realizable(conn, tid, T0 + 1, T0 + 1, 2.0, a)
    engine_v3.record_decision(conn, tid, T0 + 1, "HOLD", "t", "PT-X3-v1", {})
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("UPDATE realizable_snapshot SET realizable_value_usd=999")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("DELETE FROM position_decision_event")
    # exit + lesson rows: settle a FULL exit so triggers have rows to guard
    conn2db = str(conn.execute("PRAGMA database_list").fetchone()[2])
    conn.close()
    disc = mk_discovery(tmp_path)
    add_obs(tmp_path, disc, "T4", T0 + 30, price=0.4, liq=1e6)   # SL -35% → FULL close
    engine_v3.run_cycle_v3(conn2db, str(disc), now=T0 + 60, pal=None)
    conn = sqlite3.connect(conn2db)
    assert conn.execute("SELECT COUNT(*) FROM paper_exit_v3").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM post_trade_lesson").fetchone()[0] == 1
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("UPDATE post_trade_lesson SET lesson='x'")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("DELETE FROM paper_exit_v3")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("DELETE FROM learning_stats_snapshot")
    conn.close()


def test_equity_report_distinguishes_displayed_vs_realizable(tmp_path):
    disc = mk_discovery(tmp_path)
    conn = mk_paper(tmp_path)
    tid = mk_trade(conn, token_id="T5", qty=2.0, price=1.0, alloc=2.0)
    conn.close()
    add_obs(tmp_path, disc, "T5", T0 + 30, price=1.0, liq=1e6)
    engine_v3.run_cycle_v3(str(tmp_path / "paper.sqlite"), str(disc), now=T0 + 60, pal=None)
    eq = reports.experiment_equity(str(tmp_path / "paper.sqlite"))
    assert eq["cash_usd"] == pytest.approx(18.0)
    assert eq["open_displayed_value_usd"] == pytest.approx(2.0)
    assert eq["open_realizable_value_usd"] < eq["open_displayed_value_usd"]
    assert eq["net_equity_realizable_usd"] == pytest.approx(
        eq["cash_usd"] + eq["open_realizable_value_usd"], abs=2e-4)  # fields rounded to 4dp
    assert eq["equity_truth"].startswith("NET_EQUITY_REALIZABLE")
