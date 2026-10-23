#!/usr/bin/env python3
"""Isolated characterization of paper-lifecycle failure modes (PAPER_ONLY tmp DBs).

NOT a bridge. Does not authorize Lane A edits, freeze amendments, or fixes.
Exposes current behavior; a failing characterization is evidence, not a prod patch.

Isolation: every DB path is under pytest tmp_path; open_paper is always called with
an explicit path (never DEFAULT_STORE).
"""
from __future__ import annotations

import inspect
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_paper_trading_v3 import (  # noqa: E402
    T0,
    add_obs,
    mk_discovery,
    mk_paper,
    mk_trade,
)

from paper_trading import bankroll, engine_v2 as ev2, engine_v3, entry_rules, ledger

OPEN_SQL = """
SELECT t.trade_id FROM paper_trade_v2 t
 WHERE t.trade_id NOT IN (SELECT trade_id FROM paper_exit_v3 WHERE exit_kind='FULL')
   AND t.trade_id NOT IN (SELECT trade_id FROM paper_exit_v2)
   AND t.trade_id NOT IN (SELECT ref_id FROM invalidation WHERE scope='TRADE')
"""


def _trade_row_sql(tid: str, token_id: str, sid: str, alloc: float = 2.0):
    return (
        """INSERT INTO paper_trade_v2(trade_id,strategy_version,snapshot_id,token_id,chain,
               address,symbol,cohort,discovered_ts,entry_decision_ts,entry_ts,
               entry_price_observed,bankroll_before,amount_allocated,qty,fee_entry_usd,
               entry_slippage_bps,entry_price_exec,liq_at_entry,expected_exit_liquidity_usd,
               buy_tax_bps,sell_tax_bps,transfer_tax_bps,cost_completeness,security_class,
               execution_class,opportunity_class,exit_rule_version,monitoring_horizon_ts,
               created_utc)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            tid,
            "PT-BANKROLL-v2",
            sid,
            token_id,
            "solana",
            "0x" + token_id,
            token_id,
            "NEW_LAUNCH",
            T0 - 3600,
            T0,
            T0,
            1.0,
            20.0,
            alloc,
            2.0,
            0.02,
            25.0,
            1.0,
            1e6,
            1e6,
            None,
            None,
            None,
            "PARTIAL(taxes UNKNOWN)",
            "MEDIUM_RISK",
            "EXECUTABLE_OK",
            "MEDIUM",
            "PT-X3-v1",
            T0 + 48 * 3600,
            "2026-08-12T00:00:00+00:00",
        ),
    )


def _snap(conn, token_id: str):
    return ev2._snap_v2(
        conn,
        token_id=token_id,
        chain="solana",
        address="0x" + token_id,
        symbol=token_id,
        cohort="NEW_LAUNCH",
        discovered_ts=T0 - 3600,
        decision_ts=T0,
        features={"as_of": T0},
        security={"verdict": "PASS_WITH_UNKNOWN", "taxes": {}, "checks": []},
        decision="QUALIFIED_ENTRY",
        reason="failure-characterization",
        cfg=entry_rules.BANKROLL_V2,
    )


# ------------------------------------------------------------------ A
def test_A_allocate_false_and_engine_ignores_return_allows_trade_without_allocate(tmp_path):
    """allocate(False) is detectable; v3 entry path does not check it; mimic commit order."""
    assert bankroll.allocate.__doc__ is not None or True
    conn = mk_paper(tmp_path)
    # Drain cash so next allocate fails
    assert bankroll.allocate(conn, T0, "drain", 20.0, "drain all") is True
    assert bankroll.cash_now(conn) == pytest.approx(0.0)
    assert bankroll.allocate(conn, T0, "too-much", 1.0, "should fail") is False

    sid = _snap(conn, "FA1")
    assert sid is not None
    tid = "trade-FA1"
    sql, params = _trade_row_sql(tid, "FA1", sid)
    conn.execute(sql, params)  # pending until a later commit
    # Mimic engine_v3: ignore allocate return, then state_event (commits)
    ignored = bankroll.allocate(conn, T0, tid, 2.0, "engine-style unchecked")
    assert ignored is False
    bankroll.state_event(conn, tid, T0, "OPEN", "mimic unchecked allocate path")

    other = sqlite3.connect(str(tmp_path / "paper.sqlite"))
    other.row_factory = sqlite3.Row
    assert other.execute("SELECT 1 FROM paper_trade_v2 WHERE trade_id=?", (tid,)).fetchone()
    assert (
        other.execute(
            "SELECT COUNT(*) FROM portfolio_ledger WHERE event='ALLOCATE' AND trade_id=?",
            (tid,),
        ).fetchone()[0]
        == 0
    )
    assert tid in {r[0] for r in other.execute(OPEN_SQL)}
    other.close()

    src = inspect.getsource(engine_v3.run_cycle_v3)
    # Caller does not branch on allocate() return (characterization of production source)
    assert "bankroll.allocate(" in src
    assert "if not bankroll.allocate" not in src
    assert "if bankroll.allocate" not in src
    conn.close()


# ------------------------------------------------------------------ B
def test_B_duplicate_allocate_same_trade_is_not_prevented(tmp_path):
    conn = mk_paper(tmp_path)
    tid = mk_trade(conn, token_id="FB1", alloc=2.0)
    cash_after_first = bankroll.cash_now(conn)
    assert cash_after_first == pytest.approx(18.0)
    n1 = conn.execute(
        "SELECT COUNT(*) FROM portfolio_ledger WHERE event='ALLOCATE' AND trade_id=?",
        (tid,),
    ).fetchone()[0]
    assert n1 == 1
    assert bankroll.allocate(conn, T0 + 1, tid, 2.0, "second allocate") is True
    n2 = conn.execute(
        "SELECT COUNT(*) FROM portfolio_ledger WHERE event='ALLOCATE' AND trade_id=?",
        (tid,),
    ).fetchone()[0]
    assert n2 == 2
    assert bankroll.cash_now(conn) == pytest.approx(16.0)
    conn.close()


# ------------------------------------------------------------------ C
def test_C_missing_entry_discoverable_and_public_monitor_can_append_entry(tmp_path):
    conn = mk_paper(tmp_path)
    sid = _snap(conn, "FC1")
    tid = "trade-FC1"
    sql, params = _trade_row_sql(tid, "FC1", sid)
    conn.execute(sql, params)
    assert bankroll.allocate(conn, T0, tid, 2.0, "alloc") is True
    conn.commit()
    assert (
        conn.execute(
            "SELECT COUNT(*) FROM monitor_event WHERE trade_id=? AND event='ENTRY'",
            (tid,),
        ).fetchone()[0]
        == 0
    )
    assert tid in {r[0] for r in conn.execute(OPEN_SQL)}
    # Public API can append ENTRY without opening another trade
    ledger.monitor(conn, tid, T0 + 1, T0 + 1, 1.0, 1e6, 1000.0, "ENTRY", "repair-char")
    assert (
        conn.execute(
            "SELECT COUNT(*) FROM monitor_event WHERE trade_id=? AND event='ENTRY'",
            (tid,),
        ).fetchone()[0]
        == 1
    )
    assert (
        conn.execute("SELECT COUNT(*) FROM paper_trade_v2 WHERE token_id='FC1'").fetchone()[0]
        == 1
    )
    conn.close()


# ------------------------------------------------------------------ D
def test_D_orphan_snapshot_has_no_public_recovery_completer(tmp_path):
    conn = mk_paper(tmp_path)
    sid = _snap(conn, "FD1")
    assert sid is not None
    assert (
        conn.execute(
            "SELECT COUNT(*) FROM paper_trade_v2 WHERE token_id='FD1'"
        ).fetchone()[0]
        == 0
    )
    # Permanent uniqueness: second snap fails closed
    assert _snap(conn, "FD1") is None
    public_v3 = {
        n
        for n, o in inspect.getmembers(engine_v3, inspect.isfunction)
        if not n.startswith("_") and o.__module__ == engine_v3.__name__
    }
    assert "open_canonical_paper_position" not in public_v3
    assert "complete_orphan_snapshot" not in public_v3
    assert "insert_paper_trade_v2" not in public_v3
    conn.close()


# ------------------------------------------------------------------ E
def test_E_repeated_reclaim_after_full_exit_is_not_prevented(tmp_path):
    disc = mk_discovery(tmp_path)
    conn = mk_paper(tmp_path)
    tid = mk_trade(
        conn, token_id="FE1", qty=2.0, price=0.075, alloc=2.0, chain="ethereum"
    )
    conn.close()
    add_obs(tmp_path, disc, "FE1", T0 + 30, price=0.075, liq=1e6)
    st = engine_v3.run_cycle_v3(
        str(tmp_path / "paper.sqlite"), str(disc), now=T0 + 60, pal=None
    )
    assert st["scanned"] == 0 and st["entries"] == 0
    assert st["exits"] == 1
    p = sqlite3.connect(str(tmp_path / "paper.sqlite"))
    p.row_factory = sqlite3.Row
    assert p.execute(
        "SELECT COUNT(*) FROM paper_exit_v3 WHERE trade_id=? AND exit_kind='FULL'",
        (tid,),
    ).fetchone()[0] == 1
    cash_after = bankroll.cash_now(p)
    # Second RECLAIM for same trade is not schema-blocked
    bankroll.reclaim(p, T0 + 90, tid, 1.0, "duplicate reclaim characterization")
    n_reclaim = p.execute(
        "SELECT COUNT(*) FROM portfolio_ledger WHERE event='RECLAIM' AND trade_id=?",
        (tid,),
    ).fetchone()[0]
    assert n_reclaim >= 2
    assert bankroll.cash_now(p) == pytest.approx(cash_after + 1.0)
    p.close()


# ------------------------------------------------------------------ F
def test_F_commit_boundary_trade_pending_until_allocate_or_state_commit(tmp_path):
    path = tmp_path / "paper.sqlite"
    conn = mk_paper(tmp_path)
    sid = _snap(conn, "FF1")  # snap already committed inside _snap_v2
    tid = "trade-FF1"
    sql, params = _trade_row_sql(tid, "FF1", sid)
    conn.execute(sql, params)  # not committed

    peek = sqlite3.connect(str(path))
    assert peek.execute("SELECT 1 FROM decision_snapshot_v2 WHERE token_id='FF1'").fetchone()
    assert peek.execute("SELECT 1 FROM paper_trade_v2 WHERE trade_id=?", (tid,)).fetchone() is None
    peek.close()

    assert bankroll.allocate(conn, T0, tid, 2.0, "boundary") is True  # commits trade+alloc

    peek2 = sqlite3.connect(str(path))
    assert peek2.execute("SELECT 1 FROM paper_trade_v2 WHERE trade_id=?", (tid,)).fetchone()
    assert (
        peek2.execute(
            "SELECT COUNT(*) FROM portfolio_ledger WHERE event='ALLOCATE' AND trade_id=?",
            (tid,),
        ).fetchone()[0]
        == 1
    )
    peek2.close()
    conn.close()


# ------------------------------------------------------------------ G
def test_G_no_public_monitor_only_api_and_run_cycle_v3_contains_entry_scan(tmp_path):
    public = {
        n
        for n, o in inspect.getmembers(engine_v3, inspect.isfunction)
        if not n.startswith("_") and o.__module__ == engine_v3.__name__
    }
    assert "run_cycle_v3" in public
    assert "run_monitor_v3" not in public
    src = inspect.getsource(engine_v3.run_cycle_v3)
    assert "FROM tokens t JOIN observation_state" in src
    assert "paper_exit_v3 WHERE exit_kind='FULL'" in src
    # Entry scan appears before open_rows block in source text order
    assert src.index("FROM tokens t JOIN observation_state") < src.index(
        "paper_exit_v3 WHERE exit_kind='FULL'"
    )
    # Empty-candidate isolation still holds for this harness
    disc = mk_discovery(tmp_path)
    conn = mk_paper(tmp_path)
    mk_trade(conn, token_id="FG1", alloc=1.0)
    conn.close()
    st = engine_v3.run_cycle_v3(
        str(tmp_path / "paper.sqlite"), str(disc), now=T0 + 60, pal=None
    )
    assert st["scanned"] == 0 and st["entries"] == 0
