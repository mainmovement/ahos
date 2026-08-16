#!/usr/bin/env python3
"""Paper Trading Lab — virtual bankroll ledger (Wave-8 §A). $20.00 virtual start.
Append-only portfolio_ledger; cash/bankroll always DERIVABLE from the event stream."""
from __future__ import annotations

import json
import sqlite3
import time
from datetime import datetime, timezone

BANKROLL_START_USD = 20.00           # locked experiment constant (Wave-8 directive §A)
SCHEMA_V2 = __file__.replace("bankroll.py", "schema_v2.sql")


def ensure_v2_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(open(SCHEMA_V2).read())


def _utc(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).isoformat(timespec="seconds")


def cash_now(conn: sqlite3.Connection) -> float:
    r = conn.execute("SELECT cash_after FROM portfolio_ledger ORDER BY id DESC LIMIT 1").fetchone()
    return r[0] if r else 0.0


def init_bankroll(conn: sqlite3.Connection, ts: float) -> None:
    if conn.execute("SELECT COUNT(*) FROM portfolio_ledger").fetchone()[0] == 0:
        conn.execute(
            """INSERT INTO portfolio_ledger(ts,event,trade_id,bankroll_before,amount,cash_after,detail,created_utc)
               VALUES (?,?,?,?,?,?,?,?)""",
            (ts, "INIT", None, 0.0, BANKROLL_START_USD, BANKROLL_START_USD,
             "wave-8 experiment start: virtual $20.00 (PAPER ONLY)", _utc(ts)))
        conn.commit()


def allocate(conn: sqlite3.Connection, ts: float, trade_id: str, amount: float, detail: str) -> bool:
    c = cash_now(conn)
    if amount > c + 1e-12:
        return False
    conn.execute(
        """INSERT INTO portfolio_ledger(ts,event,trade_id,bankroll_before,amount,cash_after,detail,created_utc)
           VALUES (?,?,?,?,?,?,?,?)""", (ts, "ALLOCATE", trade_id, c, -amount, c - amount, detail, _utc(ts)))
    conn.commit()
    return True


def reclaim(conn: sqlite3.Connection, ts: float, trade_id: str, proceeds: float, detail: str) -> None:
    c = cash_now(conn)
    conn.execute(
        """INSERT INTO portfolio_ledger(ts,event,trade_id,bankroll_before,amount,cash_after,detail,created_utc)
           VALUES (?,?,?,?,?,?,?,?)""", (ts, "RECLAIM", trade_id, c, proceeds, c + proceeds, detail, _utc(ts)))
    conn.commit()


def recognize_loss(conn: sqlite3.Connection, ts: float, trade_id: str, detail: str) -> None:
    """Trapped/total-loss bookkeeping event (no cash movement — the cash left at ALLOCATE)."""
    c = cash_now(conn)
    conn.execute(
        """INSERT INTO portfolio_ledger(ts,event,trade_id,bankroll_before,amount,cash_after,detail,created_utc)
           VALUES (?,?,?,?,?,?,?,?)""", (ts, "LOSS_RECOGNIZED", trade_id, c, 0.0, c, detail, _utc(ts)))
    conn.commit()


def state_event(conn: sqlite3.Connection, trade_id: str, ts: float, state: str, reason: str) -> None:
    conn.execute(
        "INSERT INTO position_state_event(trade_id,ts,state,reason,created_utc) VALUES (?,?,?,?,?)",
        (trade_id, ts, state, reason, _utc(ts)))
    conn.commit()


def current_states(conn: sqlite3.Connection) -> dict[str, str]:
    rows = conn.execute(
        """SELECT trade_id, state FROM position_state_event
           WHERE id IN (SELECT MAX(id) FROM position_state_event GROUP BY trade_id)""").fetchall()
    return {r[0]: r[1] for r in rows}
