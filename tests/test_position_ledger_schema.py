"""The buy-logging path, tested against a real bootstrapped database.

Why this file exists
--------------------
«۵ میلیون تومان خریدم» -- log a buy, then track it -- is one of the most
central things the user asked for. On a clean install it crashed:

    OperationalError: no such column: token_chain

Two modules declared `position_ledger` with incompatible shapes:
scripts/init_databases.py used (id, chain, address, amount) while
telegram_ai/positions.py -- the only module that actually reads or writes the
table -- uses (entry_id, token_chain, token_address, amount_value). Both used
CREATE TABLE IF NOT EXISTS, so whichever ran first won silently and the other's
queries failed at runtime.

The existing tests all passed because they build ledgers in throwaway temp
files via open_ledger(), which creates the correct shape. Nothing exercised the
combination a real user hits: run the documented bootstrap, then send a
message. So these tests bootstrap the way the quickstart says to, and only then
talk to the service.
"""
from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

from telegram_ai.positions import open_ledger, log_buy, positions_for_token

# The legacy shape that used to be created by the bootstrap script.
LEGACY_DDL = """
CREATE TABLE position_ledger (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  ts            REAL NOT NULL,
  chain         TEXT,
  address       TEXT,
  symbol        TEXT,
  side          TEXT NOT NULL,
  amount        REAL,
  currency      TEXT,
  price_usd     REAL,
  note          TEXT,
  evidence_json TEXT
);
"""

TOKEN = {"chain": "solana",
         "address": "So11111111111111111111111111111111111111112",
         "symbol": "TSTX"}


def _log_a_buy(conn) -> str | None:
    return log_buy(conn, token=TOKEN, amount_value=5_000_000,
                   amount_currency="تومان", intent_rule="R-TEST",
                   raw_text="۵ میلیون تومان خریدم")


# ------------------------------------------------- single-owner invariant --

def test_bootstrap_script_does_not_declare_position_ledger():
    """One owner per table. The bootstrap script must not redeclare a table
    that telegram_ai/positions.py owns -- that is exactly how the two shapes
    diverged, and the same rule already applies to production_observations."""
    src = (ROOT / "scripts" / "init_databases.py").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS position_ledger" not in src, (
        "init_databases.py redeclares position_ledger; telegram_ai/positions.py "
        "owns it")


def test_positions_module_is_the_sole_declarer():
    hits = []
    for path in ROOT.rglob("*.py"):
        if any(part in path.parts for part in (".venv", "__pycache__", "tests")):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "CREATE TABLE IF NOT EXISTS position_ledger" in text:
            hits.append(str(path.relative_to(ROOT)))
    assert hits == ["telegram_ai/positions.py"], \
        f"position_ledger must have exactly one declarer, found: {hits}"


# ------------------------------------------- the real end-to-end scenario --

def test_bootstrap_then_log_a_buy(tmp_path):
    """The exact sequence a new user performs: run the documented bootstrap,
    then log a purchase. This is what used to crash."""
    import os
    env = dict(os.environ, AHOS_DATA_DIR=str(tmp_path / "data"))
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "init_databases.py"), "--with-guards"],
        cwd=str(ROOT), capture_output=True, text=True, timeout=300, env=env)
    assert result.returncode == 0, f"bootstrap failed:\n{result.stderr[-1500:]}"

    ledger = tmp_path / "data" / "ahos_local.sqlite"
    assert ledger.exists(), "bootstrap did not create the local store"

    conn = open_ledger(ledger)
    try:
        entry_id = _log_a_buy(conn)
        conn.commit()
        assert entry_id, "logging a buy returned no entry id"
        rows = positions_for_token(conn, TOKEN["chain"], TOKEN["address"])
        assert len(rows) == 1
        assert rows[0]["amount_value"] == 5_000_000
    finally:
        conn.close()


# ------------------------------------------------ upgrading a broken install --

def test_legacy_table_is_migrated_not_lost(tmp_path):
    """Users who already bootstrapped have the wrong table. Opening the ledger
    must repair that -- and must archive the old table rather than drop it."""
    db = tmp_path / "ahos_local.sqlite"
    raw = sqlite3.connect(db)
    raw.executescript(LEGACY_DDL)
    raw.commit()
    raw.close()

    conn = open_ledger(db)
    try:
        assert _log_a_buy(conn), "buy still fails after opening a legacy ledger"
        conn.commit()
        names = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name LIKE 'position_ledger%'")}
    finally:
        conn.close()

    assert "position_ledger" in names
    archived = [n for n in names if n.startswith("position_ledger_legacy_")]
    assert archived, "the legacy table was dropped instead of archived"


def test_opening_a_correct_ledger_twice_is_a_noop(tmp_path):
    """The repair must not fire on a healthy database, or every open would
    archive a table and the ledger would churn."""
    db = tmp_path / "ahos_local.sqlite"
    conn = open_ledger(db)
    _log_a_buy(conn)
    conn.commit()
    conn.close()

    conn = open_ledger(db)
    try:
        names = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name LIKE 'position_ledger%'")}
        assert names == {"position_ledger"}, f"unexpected churn: {names}"
        assert len(positions_for_token(conn, TOKEN["chain"], TOKEN["address"])) == 1, \
            "reopening the ledger lost the logged position"
    finally:
        conn.close()
