#!/usr/bin/env python3
"""AHOS paper position ledger — DETERMINISTIC ONLY (Wave-7 directive §17).

Law:
  - Append-only. No UPDATE/DELETE paths exist in this module by construction.
  - Only the deterministic command layer calls log_buy; AI providers are never
    on this path (Intent LEDGER_MUTATING_INTENTS gate enforced by caller + test).
  - An entry with unresolved token is REFUSED (None returned) — never store a
    guess. UNKNOWN market value stays UNKNOWN (NULL), never fabricated.
  - Valuation uses ONLY rows from discovery tables (same store link), else NULL.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS position_ledger (
  entry_id      TEXT PRIMARY KEY,
  created_utc   TEXT NOT NULL,
  intent_rule   TEXT NOT NULL,        -- parser rule id (evidence trail)
  token_chain   TEXT NOT NULL,
  token_address TEXT NOT NULL,
  side          TEXT NOT NULL,        -- BUY only for now (SELL logging lands with sell-flow design)
  amount_value  REAL NOT NULL,        -- in amount_currency units (IRT canonical for fiat)
  amount_currency TEXT NOT NULL,      -- IRT | USD | ETH | BTC | SOL | USDT
  note          TEXT,
  raw_text      TEXT,                 -- normalized user text (provenance)
  meta_json     TEXT
);
CREATE INDEX IF NOT EXISTS idx_ledger_token ON position_ledger(token_chain, token_address);
"""


def open_ledger(path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def _entry_id(chain: str, address: str, amount: float, cur: str, ts: float) -> str:
    return hashlib.sha256(f"{chain}:{address}:{amount}:{cur}:{ts}".encode()).hexdigest()[:16]


def log_buy(conn: sqlite3.Connection, *, token: dict, amount_value: float,
            amount_currency: str, intent_rule: str, raw_text: str,
            note: str | None = None, now: float | None = None) -> str | None:
    """Returns entry_id, or None when the entry is REFUSED (unresolved/invalid)."""
    ts = time.time() if now is None else now
    address = (token or {}).get("address")
    chain = (token or {}).get("chain")
    if not address or not chain:
        return None                                  # never store guesses
    if not isinstance(amount_value, (int, float)) or amount_value <= 0:
        return None
    eid = _entry_id(chain, str(address).lower(), float(amount_value), amount_currency, ts)
    conn.execute(
        """INSERT INTO position_ledger(entry_id,created_utc,intent_rule,token_chain,token_address,
                                      side,amount_value,amount_currency,note,raw_text,meta_json)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (eid, datetime.fromtimestamp(ts, timezone.utc).isoformat(timespec="seconds"),
         intent_rule, chain, str(address), "BUY", float(amount_value), amount_currency,
         note, raw_text, json.dumps({"source": "telegram_deterministic"})))
    conn.commit()
    return eid


def positions_for_token(conn: sqlite3.Connection, chain: str, address: str) -> list[dict]:
    rows = conn.execute(
        """SELECT * FROM position_ledger WHERE token_chain=? AND token_address=? ORDER BY created_utc""",
        (chain, str(address))).fetchall()
    return [dict(r) for r in rows]


def latest_observed_value(discovery_conn: sqlite3.Connection, token_id: str) -> dict:
    """Value evidence from E-01 observations only. UNKNOWN (None) when no price row exists."""
    r = discovery_conn.execute(
        """SELECT price_usd, retrieved_ts FROM discovery_observations
           WHERE token_id=? AND price_usd IS NOT NULL AND error_state IS NULL
           ORDER BY retrieved_ts DESC LIMIT 1""", (token_id,)).fetchone()
    if not r:
        return {"price_usd": None, "as_of_ts": None, "state": "UNKNOWN"}
    return {"price_usd": r["price_usd"], "as_of_ts": r["retrieved_ts"], "state": "OBSERVED"}
