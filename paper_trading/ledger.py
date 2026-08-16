#!/usr/bin/env python3
"""Paper Trading Lab — append-only ledger. The lab writes ONLY to its own store.

Guarantees:
  - discovery store is opened READ-ONLY (uri mode=ro) — Track A cannot be contaminated.
  - every table carries UPDATE/DELETE-abort triggers (schema v1); history is never rewritten.
  - every row carries created_utc + evidence refs; integrity problems go to `invalidation`.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
DEFAULT_STORE = Path(__file__).resolve().parents[1] / "data" / "paper_trading.sqlite"


def utc(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).isoformat(timespec="seconds")


def open_paper(path: str | Path = DEFAULT_STORE) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_PATH.read_text())
    return conn


def open_discovery_ro(path: str | Path) -> sqlite3.Connection:
    """STRUCTURAL isolation: discovery DB is read-only for the lab, always."""
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _sha(*parts) -> str:
    return hashlib.sha256(":".join(str(p) for p in parts).encode()).hexdigest()[:24]


def seed_strategy(conn: sqlite3.Connection, card: dict, exit_card: dict, cost_card: dict) -> None:
    conn.execute(
        """INSERT OR IGNORE INTO strategy_version(version,created_utc,hypothesis,entry_rules_json,
           exit_rules_json,cost_json,failure_criteria,success_criteria,status_note)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (card["version"], card["created"], card["hypothesis"],
         json.dumps({k: v for k, v in card.items() if k not in ("exit_rules", "cost_model")}, sort_keys=True),
         json.dumps(exit_card, sort_keys=True), json.dumps(cost_card, sort_keys=True),
         card["failure_criteria"], card["success_criteria"], "registered; constants locked"))


def record_snapshot(conn, *, token_id, chain, address, symbol, discovered_ts, decision_ts,
                    features, security, rule_version, decision, reason) -> str | None:
    sid = _sha(token_id, decision_ts, rule_version)
    try:
        conn.execute(
            """INSERT INTO decision_snapshot(snapshot_id,token_id,chain,address,symbol,discovered_ts,
                   decision_ts,features_json,security_json,rule_version,decision,reason,created_utc)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (sid, token_id, chain, address, symbol, discovered_ts, decision_ts,
             json.dumps(features, sort_keys=True, default=str),
             json.dumps(security, sort_keys=True, default=str),
             rule_version, decision, reason, utc(time.time())))
        conn.commit()
        return sid
    except sqlite3.IntegrityError:      # token already decided — dedupe law, not an error
        return None


def open_trade(conn, *, strategy_version, snapshot_id, token_id, chain, address, symbol,
               discovered_ts, entry_decision_ts, entry_ts, entry_price_observed,
               fee_bps, entry_slippage_bps, entry_price_exec, notional_usd, qty, fee_entry_usd,
               liq_at_entry, exit_rule_version, monitoring_horizon_ts) -> str | None:
    tid = _sha("TRADE", token_id, entry_ts, strategy_version)
    try:
        conn.execute(
            """INSERT INTO paper_trade(trade_id,strategy_version,snapshot_id,token_id,chain,address,
                   symbol,discovered_ts,entry_decision_ts,entry_ts,entry_price_observed,fee_bps,
                   entry_slippage_bps,entry_price_exec,notional_usd,qty,fee_entry_usd,liq_at_entry,
                   exit_rule_version,monitoring_horizon_ts,created_utc)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (tid, strategy_version, snapshot_id, token_id, chain, address, symbol, discovered_ts,
             entry_decision_ts, entry_ts, entry_price_observed, fee_bps, entry_slippage_bps,
             entry_price_exec, notional_usd, qty, fee_entry_usd, liq_at_entry, exit_rule_version,
             monitoring_horizon_ts, utc(time.time())))
        conn.commit()
        return tid
    except sqlite3.IntegrityError:
        return None


def monitor(conn, trade_id: str, ts: float, obs_ts: float | None, price, liq, vol,
            event: str, detail: str = "") -> None:
    conn.execute(
        """INSERT OR IGNORE INTO monitor_event(trade_id,ts,obs_ts,price_usd,liquidity_usd,volume_24h,event,detail)
           VALUES (?,?,?,?,?,?,?,?)""", (trade_id, ts, obs_ts, price, liq, vol, event, detail))
    conn.commit()


def close_trade(conn, *, trade_id, exit_ts, exit_reason, exit_obs_ts, exit_price_observed,
                exit_slippage_bps, exit_price_exec, pnl, fee_exit_usd,
                mfe_pct, mae_pct, hold_hours) -> bool:
    try:
        conn.execute(
            """INSERT INTO paper_exit(trade_id,exit_ts,exit_reason,exit_obs_ts,exit_price_observed,
                   exit_slippage_bps,exit_price_exec,gross_pnl_usd,slippage_usd,fee_exit_usd,
                   cost_total_usd,net_pnl_usd,mfe_pct,mae_pct,hold_hours,closed_utc)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (trade_id, exit_ts, exit_reason, exit_obs_ts, exit_price_observed, exit_slippage_bps,
             exit_price_exec, pnl["gross_pnl_usd"], pnl["slippage_usd"], fee_exit_usd,
             pnl["cost_total_usd"], pnl["net_pnl_usd"], mfe_pct, mae_pct, hold_hours,
             utc(time.time())))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def invalidate(conn, scope: str, ref_id: str, reason: str) -> None:
    conn.execute("INSERT INTO invalidation(scope,ref_id,reason,created_utc) VALUES (?,?,?,?)",
                 (scope, ref_id, reason, utc(time.time())))
    conn.commit()


def open_trades(conn) -> list[sqlite3.Row]:
    return conn.execute(
        """SELECT t.* FROM paper_trade t LEFT JOIN paper_exit x ON x.trade_id=t.trade_id
           WHERE x.trade_id IS NULL
           AND t.trade_id NOT IN (SELECT ref_id FROM invalidation WHERE scope='TRADE')""").fetchall()
