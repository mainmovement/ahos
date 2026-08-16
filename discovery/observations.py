#!/usr/bin/env python3
"""AHOS STEP 4 — Timestamped discovery observations + canonical store (SQLite).
Every observation: dual timestamps (source_ts from provider if disclosed; retrieved_ts always),
provenance (provider + raw payload sha256), NULL for unknown, error_state instead of fabrication.
Store API is pure/deterministic given inputs (clock injectable).
"""
from __future__ import annotations
import json, sqlite3, hashlib, time
from pathlib import Path
from . import identity

SCHEMA = (Path(__file__).resolve().parent / "schema_sqlite.sql").read_text(encoding="utf-8")


def open_store(path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


# ---------------- raw payloads ----------------
def store_raw(conn, provider: str, endpoint: str, retrieved_ts: float,
              http_status: int | None, payload) -> str:
    body = payload if isinstance(payload, (bytes, bytearray)) else json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
    sha = hashlib.sha256(body).hexdigest()
    conn.execute(
        "INSERT OR IGNORE INTO raw_payloads(payload_sha256,provider,endpoint,retrieved_ts,http_status,payload_json)"
        " VALUES (?,?,?,?,?,?)",
        (sha, provider, endpoint, retrieved_ts, http_status, body.decode("utf-8", "replace")))
    return sha


# ---------------- tokens / pairs ----------------
def upsert_token(conn, chain_id: str, address: str, first_seen_ts: float, provider: str,
                 symbol=None, name=None, created_at_ts=None, deployer=None, meta=None) -> str:
    tid = identity.token_id(chain_id, address)
    chain_norm = identity.normalize_chain(chain_id)
    conn.execute(
        """INSERT INTO tokens(token_id,chain_id,address,symbol,name,deployer_address,first_seen_ts,
                              created_at_ts,source_first_seen_provider,meta_json,status)
           VALUES (?,?,?,?,?,?,?,?,?,?,'active')
           ON CONFLICT(token_id) DO UPDATE SET
             symbol       = COALESCE(tokens.symbol, excluded.symbol),
             name         = COALESCE(tokens.name, excluded.name),
             created_at_ts= COALESCE(tokens.created_at_ts, excluded.created_at_ts),
             meta_json    = COALESCE(tokens.meta_json, excluded.meta_json)""",
        (tid, chain_norm, address, symbol, name, deployer, first_seen_ts,
         created_at_ts, provider, json.dumps(meta, ensure_ascii=False) if meta else None))
    return tid


def upsert_pair(conn, chain_id: str, dex_id: str, pair_address: str, tok_id: str,
                first_seen_ts: float, provider: str, raw_ref: str,
                quote_symbol=None, pair_created_ts=None, base_token_id=None) -> str:
    pid = identity.pair_id(chain_id, dex_id or "unknown", pair_address)
    chain_norm = identity.normalize_chain(chain_id)
    conn.execute(
        """INSERT INTO pairs(pair_id,token_id,chain_id,dex_id,pair_address,base_token_id,quote_symbol,
                             pair_created_ts,first_seen_ts,provider,raw_ref)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(pair_id) DO UPDATE SET
             pair_created_ts = COALESCE(pairs.pair_created_ts, excluded.pair_created_ts)""",
        (pid, tok_id, chain_norm, (dex_id or "unknown").lower(), pair_address, base_token_id,
         quote_symbol, pair_created_ts, first_seen_ts, provider, raw_ref))
    return pid


# ---------------- observation ----------------
OBS_FIELDS = ["price_usd", "liquidity_usd", "fdv", "market_cap",
              "volume_5m", "volume_1h", "volume_6h", "volume_24h",
              "txns_5m_buys", "txns_5m_sells", "txns_1h_buys", "txns_1h_sells",
              "txns_24h_buys", "txns_24h_sells",
              "price_change_5m", "price_change_1h", "price_change_6h", "price_change_24h",
              "pair_age_minutes", "boost_amount"]


def record_observation(conn, tok_id: str, provider: str, retrieved_ts: float, raw_ref: str,
                       pair: str | None = None, source_ts: float | None = None,
                       metrics: dict | None = None, error_state: dict | None = None) -> str:
    """Insert one observation. Metrics missing → NULL. error_state carries failures; never fake values."""
    metrics = metrics or {}
    flags = []
    if error_state is None:
        present = [f for f in OBS_FIELDS if metrics.get(f) is not None]
        flags.append("schema_ok")
        if len(present) >= 12:
            flags.append("complete")
        if source_ts is not None and retrieved_ts - source_ts <= 300:
            flags.append("ts_fresh")
    oid = identity.obs_id(tok_id, pair, provider, retrieved_ts, raw_ref)
    cols = ["obs_id", "token_id", "pair_id", "provider", "source_ts", "retrieved_ts",
            *OBS_FIELDS, "quality_flags", "error_state", "raw_ref"]
    vals = [oid, tok_id, pair, provider, source_ts, retrieved_ts,
            *[metrics.get(f) for f in OBS_FIELDS],
            json.dumps(flags), json.dumps(error_state) if error_state else None, raw_ref]
    conn.execute(
        f"INSERT OR IGNORE INTO discovery_observations({','.join(cols)}) VALUES ({','.join('?'*len(cols))})",
        vals)
    return oid


# ---------------- f64 helpers for adapters ----------------
def f(x):
    """Parse provider numeric-or-string → float; None/garbage → None (NULL = UNKNOWN)."""
    if x is None or x == "":
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v


def i(x):
    v = f(x)
    return int(v) if v is not None else None


def ms_to_ts(ms):
    v = f(ms)
    return (v / 1000.0) if v is not None else None
