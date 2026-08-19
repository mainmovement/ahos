"""Every SQL column a module reads must exist in the schema it reads from.

Why this file exists
--------------------
`_get_candidate_from_store` selected `t.chain` and `p.dex`. The real columns
are `chain_id` and `dex_id`. The whole call sat inside `except Exception: pass`,
so the error never surfaced -- the method silently fell through to its
"unknown token" fallback. Every single token lookup returned:

    📊 تحلیل فرصت — UNKNOWN (Unknown Token)   🎯 فرصت: 0/100

with liquidity, volume and buy pressure all reported as "not observed", while
that exact data sat in the database one row away. The headline feature of the
product -- «این توکن رو بررسی کن» -- was answering from an empty object.

The existing tests missed it because they construct candidates directly rather
than loading them through the store, so the broken query was never executed
against a real schema.

These tests run each production query against the real bootstrapped schema. A
query that names a column that does not exist fails loudly here instead of
being swallowed at runtime.
"""
from __future__ import annotations

import ast
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def real_schema(tmp_path_factory):
    """A database created by the project's own bootstrap, not by hand."""
    data_dir = tmp_path_factory.mktemp("schema") / "data"
    env = dict(__import__("os").environ, AHOS_DATA_DIR=str(data_dir))
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "init_databases.py"), "--with-guards"],
        cwd=str(ROOT), capture_output=True, text=True, timeout=300, env=env)
    assert result.returncode == 0, f"bootstrap failed:\n{result.stderr[-1500:]}"
    db = data_dir / "e01_discovery.sqlite"
    assert db.exists()
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


def _columns(conn, table: str) -> set[str]:
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}


# ------------------------------------------------- the specific regression --

def test_tokens_table_has_no_bare_chain_column(real_schema):
    """Pins the fact that made the bug possible."""
    cols = _columns(real_schema, "tokens")
    assert "chain_id" in cols
    assert "chain" not in cols, \
        "if a bare `chain` column is ever added, revisit the service queries"


def test_pairs_table_uses_dex_id(real_schema):
    cols = _columns(real_schema, "pairs")
    assert "dex_id" in cols
    assert "dex" not in cols


def test_service_does_not_select_the_nonexistent_columns():
    src = (ROOT / "telegram_ai" / "service.py").read_text(encoding="utf-8")
    assert "t.chain," not in src, "service selects t.chain; the column is chain_id"
    assert "p.dex," not in src, "service selects p.dex; the column is dex_id"
    assert 'r["chain"]' not in src
    assert 'r["dex"]' not in src


# ------------------------------- every service query, against a real schema --

def _service_queries() -> list[str]:
    """Extract SQL string literals from the Telegram service."""
    src = (ROOT / "telegram_ai" / "service.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            text = node.value.strip()
            if re.match(r"(?is)^\s*select\b", text) and "FROM" in text.upper():
                out.append(text)
    return out


def test_the_service_actually_contains_queries_to_check():
    assert len(_service_queries()) >= 3, "extraction found nothing; test is vacuous"


def test_every_service_select_parses_against_the_real_schema(real_schema):
    """EXPLAIN validates table and column names without running the query.

    This is the guard that would have caught the bug: a wrong column name is a
    hard error here, not a silent fallback.
    """
    failures = []
    for sql in _service_queries():
        probe = re.sub(r"\?", "NULL", sql)
        try:
            real_schema.execute("EXPLAIN " + probe)
        except sqlite3.Error as exc:
            failures.append(f"{exc}  <<  {' '.join(sql.split())[:110]}")
    assert not failures, "service queries reference unknown tables/columns:\n" + \
        "\n".join(failures)


def test_every_positions_query_parses(real_schema, tmp_path):
    """positions.py spans two stores: the ledger and the discovery database.

    Each query is validated against whichever store owns its table, so a typo
    in either one is caught. Checking against a single connection would make
    half the queries fail for the wrong reason.
    """
    from telegram_ai.positions import open_ledger
    ledger = open_ledger(tmp_path / "ledger.sqlite")
    src = (ROOT / "telegram_ai" / "positions.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    failures = []
    checked = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            text = node.value.strip()
            if not (re.match(r"(?is)^\s*select\b", text) and "FROM" in text.upper()):
                continue
            conn = real_schema if "discovery_observations" in text else ledger
            checked += 1
            try:
                conn.execute("EXPLAIN " + re.sub(r"\?", "NULL", text))
            except sqlite3.Error as exc:
                failures.append(f"{exc}  <<  {' '.join(text.split())[:110]}")
    ledger.close()
    assert checked >= 2, "extraction found too few queries; test is vacuous"
    assert not failures, "\n".join(failures)


# ------------------------------------------- the behaviour the bug destroyed --

def test_a_stored_token_is_loaded_with_its_real_metrics(tmp_path):
    """End to end: a token with data in the store must not come back UNKNOWN."""
    import time
    from telegram_ai.service import TelegramDomainService

    now = time.time()
    addr = "So11111111111111111111111111111111111111112"
    token_id = f"solana:{addr}"
    db = tmp_path / "disco.sqlite"

    conn = sqlite3.connect(db)
    conn.executescript("""
        CREATE TABLE tokens(token_id TEXT PRIMARY KEY, chain_id TEXT, address TEXT,
          symbol TEXT, name TEXT, deployer_address TEXT, first_seen_ts REAL,
          created_at_ts REAL, source_first_seen_provider TEXT, meta_json TEXT,
          status TEXT);
        CREATE TABLE pairs(pair_id TEXT PRIMARY KEY, token_id TEXT, chain_id TEXT,
          dex_id TEXT, pair_address TEXT, base_token_id TEXT, quote_symbol TEXT,
          pair_created_ts REAL, first_seen_ts REAL, provider TEXT, raw_ref TEXT);
        CREATE TABLE discovery_observations(obs_id TEXT PRIMARY KEY, token_id TEXT,
          provider TEXT, retrieved_ts REAL, price_usd REAL, liquidity_usd REAL,
          volume_1h REAL, volume_24h REAL, txns_1h_buys INT, txns_1h_sells INT,
          error_state TEXT, raw_ref TEXT);
    """)
    conn.execute("INSERT INTO tokens VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                 (token_id, "solana", addr, "ALPHA", "Alpha", None, now, now,
                  "dexscreener", None, "ACTIVE"))
    conn.execute("INSERT INTO pairs VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                 ("p1", token_id, "solana", "raydium", "PAIR", None, "SOL",
                  now, now, "dexscreener", "r"))
    conn.execute("INSERT INTO discovery_observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                 ("o1", token_id, "dexscreener", now, 1.0, 90000.0, 70000.0,
                  800000.0, 800, 400, None, "r"))
    conn.commit()
    conn.close()

    out = TelegramDomainService(discovery_db_path=str(db)).handle_message(
        f"این توکن رو بررسی کن {addr}", {})

    assert "UNKNOWN" not in out["text"], \
        "token with full data in the store came back as UNKNOWN"
    assert "ALPHA" in out["text"]
    assert "90,000" in out["text"], "liquidity present in the store was not reported"
    cand = out.get("candidate")
    assert cand is not None
    assert cand.source_provider != "ad_hoc_query", \
        "fell through to the fallback despite the token being in the store"
    assert cand.metrics.liquidity_usd == 90000.0
    assert cand.chain == "solana"
    assert cand.dex_id == "raydium"


def test_a_token_absent_from_the_store_still_degrades_gracefully(tmp_path):
    """The fallback is correct behaviour when the token genuinely is unknown."""
    from telegram_ai.service import TelegramDomainService
    db = tmp_path / "empty.sqlite"
    conn = sqlite3.connect(db)
    conn.executescript("""
        CREATE TABLE tokens(token_id TEXT PRIMARY KEY, chain_id TEXT, address TEXT,
          symbol TEXT, name TEXT, source_first_seen_provider TEXT);
        CREATE TABLE pairs(pair_id TEXT PRIMARY KEY, token_id TEXT, dex_id TEXT,
          pair_address TEXT, pair_created_ts REAL);
        CREATE TABLE discovery_observations(obs_id TEXT PRIMARY KEY, token_id TEXT,
          retrieved_ts REAL, price_usd REAL, liquidity_usd REAL, error_state TEXT);
    """)
    conn.commit()
    conn.close()

    out = TelegramDomainService(discovery_db_path=str(db)).handle_message(
        "این توکن رو بررسی کن So11111111111111111111111111111111111111112", {})
    assert out["status"] == "OK"
    assert out["candidate"].source_provider == "ad_hoc_query"
