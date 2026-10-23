#!/usr/bin/env python3
"""Paper position lifecycle contracts for a future Lane B canonical-only entry bridge.

TEST-ONLY. Does not implement the bridge. Uses temporary DBs and synthetic
observations only. Characterizes CURRENT frozen consumer behavior:

  * v3 open-position discoverability query
  * settlement + bankroll reclaim when the harness can isolate entry scan
  * missing ALLOCATE / missing ENTRY monitor effects
  * token_id uniqueness fail-closed
  * exclusion by paper_exit_v2 / paper_exit_v3 FULL / TRADE invalidation
  * absence of a public canonical-only paper_trade_v2 entry API

Does not claim OPERATOR_READY, live-runtime VERIFIED, or profitability.
"""
from __future__ import annotations

import inspect
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_paper_trading_v3 import (  # reuse established fixtures (no duplication)
    T0,
    add_obs,
    mk_discovery,
    mk_paper,
    mk_trade,
)

from paper_trading import bankroll, engine_v2 as ev2, engine_v3, entry_rules, ledger

# Exact open-position filter used by engine_v3.run_cycle_v3 (consumer contract).
OPEN_V3_SQL = """
SELECT t.trade_id FROM paper_trade_v2 t
 WHERE t.trade_id NOT IN (SELECT trade_id FROM paper_exit_v3 WHERE exit_kind='FULL')
   AND t.trade_id NOT IN (SELECT trade_id FROM paper_exit_v2)
   AND t.trade_id NOT IN (SELECT ref_id FROM invalidation WHERE scope='TRADE')
"""


def _open_ids(conn: sqlite3.Connection) -> set[str]:
    return {r[0] for r in conn.execute(OPEN_V3_SQL).fetchall()}


def _insert_trade_row(
    conn,
    *,
    token_id: str,
    tid: str | None = None,
    qty: float = 2.0,
    price: float = 1.0,
    alloc: float = 2.0,
    chain: str = "solana",
    security_class: str = "MEDIUM_RISK",
    entry_ts: float = T0,
    sell_tax=None,
):
    """Schema-complete paper_trade_v2 + decision_snapshot_v2 only (no allocate/monitor)."""
    sid = ev2._snap_v2(
        conn,
        token_id=token_id,
        chain=chain,
        address="0x" + token_id,
        symbol=token_id,
        cohort="NEW_LAUNCH",
        discovered_ts=entry_ts - 3600,
        decision_ts=entry_ts,
        features={"as_of": entry_ts, "price_usd": price, "liquidity_usd": 1e6},
        security={
            "verdict": "PASS_WITH_UNKNOWN",
            "taxes": {
                "buy_tax_bps": None,
                "sell_tax_bps": sell_tax,
                "transfer_tax_bps": None,
            },
            "checks": [],
        },
        decision="QUALIFIED_ENTRY",
        reason="lifecycle-contract",
        cfg=entry_rules.BANKROLL_V2,
    )
    assert sid is not None
    trade_id = tid or f"trade-{token_id}"
    conn.execute(
        """INSERT INTO paper_trade_v2(trade_id,strategy_version,snapshot_id,token_id,chain,
               address,symbol,cohort,discovered_ts,entry_decision_ts,entry_ts,
               entry_price_observed,bankroll_before,amount_allocated,qty,fee_entry_usd,
               entry_slippage_bps,entry_price_exec,liq_at_entry,expected_exit_liquidity_usd,
               buy_tax_bps,sell_tax_bps,transfer_tax_bps,cost_completeness,security_class,
               execution_class,opportunity_class,exit_rule_version,monitoring_horizon_ts,
               created_utc)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            trade_id,
            "PT-BANKROLL-v2",
            sid,
            token_id,
            chain,
            "0x" + token_id,
            token_id,
            "NEW_LAUNCH",
            entry_ts - 3600,
            entry_ts,
            entry_ts,
            price,
            20.0,
            alloc,
            qty,
            0.02,
            25.0,
            price,
            1e6,
            1e6,
            None,
            sell_tax,
            None,
            "PARTIAL(taxes UNKNOWN)" if sell_tax is None else "FULL",
            security_class,
            "EXECUTABLE_OK",
            "MEDIUM",
            "PT-X3-v1",
            entry_ts + 48 * 3600,
            "2026-08-12T00:00:00+00:00",
        ),
    )
    conn.commit()
    return trade_id


def _assert_entry_scan_isolated(st: dict) -> None:
    """mk_discovery seeds schema only — no tokens/observation_state ⇒ no new entries."""
    assert st["scanned"] == 0
    assert st["entries"] == 0


# ------------------------------------------------------------------ 1. discoverability
def test_complete_position_discoverable_by_v3_open_query(tmp_path):
    conn = mk_paper(tmp_path)
    tid = mk_trade(conn, token_id="LC1", qty=2.0, price=1.0, alloc=2.0)
    assert tid in _open_ids(conn)
    assert (
        conn.execute(
            "SELECT COUNT(*) FROM portfolio_ledger WHERE event='ALLOCATE' AND trade_id=?",
            (tid,),
        ).fetchone()[0]
        == 1
    )
    assert (
        conn.execute(
            "SELECT COUNT(*) FROM monitor_event WHERE trade_id=? AND event='ENTRY'",
            (tid,),
        ).fetchone()[0]
        == 1
    )
    conn.close()


# ------------------------------------------------------------------ 2. exit + conservation
def test_monitor_settles_and_reclaims_with_isolated_entry_scan(tmp_path):
    """Fresh synthetic obs + empty candidate set → FULL TOTAL_LOSS; cash conserved."""
    disc = mk_discovery(tmp_path)
    conn = mk_paper(tmp_path)
    tid = mk_trade(
        conn, token_id="LC2", qty=2.0, price=0.075, alloc=2.0, chain="ethereum"
    )
    cash_after_alloc = bankroll.cash_now(conn)
    assert cash_after_alloc == pytest.approx(18.0)
    conn.close()

    add_obs(tmp_path, disc, "LC2", T0 + 30, price=0.075, liq=1e6)
    st = engine_v3.run_cycle_v3(
        str(tmp_path / "paper.sqlite"), str(disc), now=T0 + 60, pal=None
    )
    _assert_entry_scan_isolated(st)
    assert st["trapped"] == 1 and st["exits"] == 1

    p = sqlite3.connect(str(tmp_path / "paper.sqlite"))
    p.row_factory = sqlite3.Row
    x = p.execute("SELECT * FROM paper_exit_v3 WHERE trade_id=?", (tid,)).fetchone()
    assert x["exit_kind"] == "FULL"
    assert x["exit_reason"] == "TOTAL_LOSS"
    assert x["net_proceeds_usd"] == pytest.approx(0.0)
    assert x["capital_loss_usd"] == pytest.approx(2.0)
    assert tid not in _open_ids(p)
    cash = p.execute(
        "SELECT cash_after FROM portfolio_ledger ORDER BY id DESC LIMIT 1"
    ).fetchone()[0]
    # reclaim(0) + LOSS_RECOGNIZED: cash remains 18.0 (allocated capital written off)
    assert cash == pytest.approx(18.0)
    reclaim = p.execute(
        "SELECT amount FROM portfolio_ledger WHERE event='RECLAIM' AND trade_id=?",
        (tid,),
    ).fetchone()
    assert reclaim is not None and reclaim[0] == pytest.approx(0.0)
    assert (
        p.execute(
            "SELECT COUNT(*) FROM portfolio_ledger WHERE event='LOSS_RECOGNIZED' "
            "AND trade_id=?",
            (tid,),
        ).fetchone()[0]
        == 1
    )
    p.close()


# ------------------------------------------------------------------ 3. missing ALLOCATE
def test_missing_allocate_still_discoverable_breaks_naive_conservation(tmp_path):
    """Open query does not require ALLOCATE; cash vs amount_allocated diverge."""
    conn = mk_paper(tmp_path)
    tid = _insert_trade_row(conn, token_id="LC3", alloc=2.0)
    assert tid in _open_ids(conn)
    assert (
        conn.execute(
            "SELECT COUNT(*) FROM portfolio_ledger WHERE event='ALLOCATE' AND trade_id=?",
            (tid,),
        ).fetchone()[0]
        == 0
    )
    cash = bankroll.cash_now(conn)
    allocated_on_row = conn.execute(
        "SELECT amount_allocated FROM paper_trade_v2 WHERE trade_id=?", (tid,)
    ).fetchone()[0]
    assert cash == pytest.approx(bankroll.BANKROLL_START_USD)
    assert allocated_on_row == pytest.approx(2.0)
    # Demonstrated inconsistent bookkeeping if amount_allocated is trusted without ALLOCATE
    assert cash + allocated_on_row != pytest.approx(bankroll.BANKROLL_START_USD)
    conn.close()


# ------------------------------------------------------------------ 4. missing ENTRY monitor
def test_missing_entry_monitor_still_discoverable(tmp_path):
    """Open query does not require ENTRY monitor_event; omission alone does not hide the row."""
    conn = mk_paper(tmp_path)
    tid = _insert_trade_row(conn, token_id="LC4", alloc=2.0)
    bankroll.allocate(conn, T0, tid, 2.0, "alloc without ENTRY monitor")
    conn.commit()
    assert (
        conn.execute(
            "SELECT COUNT(*) FROM monitor_event WHERE trade_id=? AND event='ENTRY'",
            (tid,),
        ).fetchone()[0]
        == 0
    )
    assert tid in _open_ids(conn)
    conn.close()


# ------------------------------------------------------------------ 5. duplicate token_id
def test_duplicate_token_id_fails_closed_without_corrupting_first(tmp_path):
    conn = mk_paper(tmp_path)
    tid = mk_trade(conn, token_id="LC5", qty=2.0, price=1.0, alloc=2.0)
    cash_before = bankroll.cash_now(conn)
    row_before = dict(
        conn.execute("SELECT * FROM paper_trade_v2 WHERE trade_id=?", (tid,)).fetchone()
    )

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """INSERT INTO paper_trade_v2(trade_id,strategy_version,snapshot_id,token_id,chain,
                   address,symbol,cohort,discovered_ts,entry_decision_ts,entry_ts,
                   entry_price_observed,bankroll_before,amount_allocated,qty,fee_entry_usd,
                   entry_slippage_bps,entry_price_exec,liq_at_entry,expected_exit_liquidity_usd,
                   buy_tax_bps,sell_tax_bps,transfer_tax_bps,cost_completeness,security_class,
                   execution_class,opportunity_class,exit_rule_version,monitoring_horizon_ts,
                   created_utc)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                "trade-LC5-dup",
                "PT-BANKROLL-v2",
                "fake-snapshot-not-used",
                "LC5",  # duplicate token_id
                "solana",
                "0xLC5",
                "LC5",
                "NEW_LAUNCH",
                T0 - 3600,
                T0,
                T0,
                1.0,
                20.0,
                2.0,
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
    conn.rollback()

    assert bankroll.cash_now(conn) == pytest.approx(cash_before)
    row_after = dict(
        conn.execute("SELECT * FROM paper_trade_v2 WHERE trade_id=?", (tid,)).fetchone()
    )
    assert row_after == row_before
    assert (
        conn.execute("SELECT COUNT(*) FROM paper_trade_v2 WHERE token_id='LC5'").fetchone()[0]
        == 1
    )
    # Second QUALIFIED snapshot for same token also fail-closed via _snap_v2
    assert (
        ev2._snap_v2(
            conn,
            token_id="LC5",
            chain="solana",
            address="0xLC5",
            symbol="LC5",
            cohort="NEW_LAUNCH",
            discovered_ts=T0,
            decision_ts=T0 + 1,
            features={},
            security={"verdict": "PASS_WITH_UNKNOWN", "taxes": {}, "checks": []},
            decision="QUALIFIED_ENTRY",
            reason="dup",
            cfg=entry_rules.BANKROLL_V2,
        )
        is None
    )
    conn.close()


# ------------------------------------------------------------------ 6. exclusion records
def test_exit_v2_full_v3_and_invalidation_exclude_from_open_query(tmp_path):
    conn = mk_paper(tmp_path)
    t_v2 = mk_trade(conn, token_id="EXV2", alloc=1.0)
    t_v3 = mk_trade(conn, token_id="EXV3", alloc=1.0)
    t_inv = mk_trade(conn, token_id="EXINV", alloc=1.0)
    assert {t_v2, t_v3, t_inv} <= _open_ids(conn)

    conn.execute(
        """INSERT INTO paper_exit_v2(trade_id,exit_ts,exit_reason,qty_sold,closed_utc)
           VALUES (?,?,?,?,?)""",
        (t_v2, T0 + 10, "TEST_CLOSE", 2.0, "2026-08-12T00:00:10+00:00"),
    )
    conn.execute(
        """INSERT INTO paper_exit_v3(exit_id,trade_id,exit_seq,exit_kind,exit_ts,exit_reason,
               rule_version,qty_sold,qty_remaining_after,requested_notional_usd,
               executable_notional_usd,allocated_retired_usd,closed_utc)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            "x3-full-exv3",
            t_v3,
            1,
            "FULL",
            T0 + 10,
            "TEST_FULL",
            "PT-X3-v2",
            2.0,
            0.0,
            2.0,
            2.0,
            1.0,
            "2026-08-12T00:00:10+00:00",
        ),
    )
    ledger.invalidate(conn, "TRADE", t_inv, "lifecycle-contract invalidation")
    conn.commit()

    open_ids = _open_ids(conn)
    assert t_v2 not in open_ids
    assert t_v3 not in open_ids
    assert t_inv not in open_ids
    conn.close()


# ------------------------------------------------------------------ 7. bridge API boundary
def test_no_public_canonical_only_v2_entry_api_private_helpers_stay_private():
    """Naming/inspect convention: no public insert_paper_trade_v2; private helpers underscored."""
    public_v3 = {
        name
        for name, obj in inspect.getmembers(engine_v3, inspect.isfunction)
        if not name.startswith("_") and obj.__module__ == engine_v3.__name__
    }
    public_v2 = {
        name
        for name, obj in inspect.getmembers(ev2, inspect.isfunction)
        if not name.startswith("_") and obj.__module__ == ev2.__name__
    }
    public_bankroll = {
        name
        for name, obj in inspect.getmembers(bankroll, inspect.isfunction)
        if not name.startswith("_") and obj.__module__ == bankroll.__name__
    }

    assert "run_cycle_v3" in public_v3
    assert "insert_paper_trade_v2" not in public_v3
    assert "open_canonical_paper_trade" not in public_v3
    assert "_monitor_position" not in public_v3
    assert "_settle" not in public_v3
    assert hasattr(engine_v3, "_monitor_position") and hasattr(engine_v3, "_settle")

    assert "insert_paper_trade_v2" not in public_v2
    assert "_snap_v2" not in public_v2
    assert hasattr(ev2, "_snap_v2")

    assert "allocate" in public_bankroll
    assert "open_trade_v2" not in public_bankroll

    # ledger.open_trade writes paper_trade (v1), not paper_trade_v2
    src = inspect.getsource(ledger.open_trade)
    assert "INSERT INTO paper_trade(" in src
    assert "paper_trade_v2" not in src
