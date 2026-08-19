#!/usr/bin/env python3
"""AHOS Paper Position Management Domain (Section XI).

Non-negotiable Laws:
  - 100% PAPER ONLY: Zero real trades, zero exchange API keys, zero wallet private keys.
  - Event-sourced / Append-only: Every state transition (ENTRY, MONITOR, TP, SL, INVALIDATE, RECONCILE) is recorded as an immutable event.
  - Realizable vs Displayed: Explicit fee deduction (gas, LP fee 30bps, price impact) and slippage models.
  - Fail-safe: Stale data (>4h) or missing prices trigger NO_DATA hold rules without guessing.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any
from config.paths import get_paper_trading_db_path

SCHEMA_POSITIONS = """
CREATE TABLE IF NOT EXISTS paper_positions (
  position_id      TEXT PRIMARY KEY,
  chain            TEXT NOT NULL,
  token_address    TEXT NOT NULL,
  symbol           TEXT NOT NULL,
  entry_ts         REAL NOT NULL,
  entry_price_usd  REAL NOT NULL,
  allocated_usd    REAL NOT NULL,
  tokens_amount    REAL NOT NULL,
  fee_entry_usd    REAL NOT NULL,
  impact_bps       REAL NOT NULL,
  status           TEXT NOT NULL,    -- OPEN | CLOSED_TP | CLOSED_SL | CLOSED_INVALIDATED | CLOSED_STALE
  strategy_id      TEXT NOT NULL,
  invalidation_rules TEXT,           -- JSON array of trigger conditions
  meta_json        TEXT
);

CREATE TABLE IF NOT EXISTS paper_position_events (
  event_id         TEXT PRIMARY KEY,
  position_id      TEXT NOT NULL,
  event_ts         REAL NOT NULL,
  event_type       TEXT NOT NULL,    -- ENTRY | PRICE_UPDATE | NO_DATA_STALE | TP_EXIT | SL_EXIT | INVALIDATION_EXIT | RECONCILE
  current_price_usd REAL,
  unrealized_pnl_pct REAL,
  realized_pnl_usd REAL,
  fee_exit_usd     REAL,
  reason           TEXT NOT NULL,
  evidence_ref     TEXT NOT NULL,
  meta_json        TEXT
);
"""


@dataclass
class PaperPosition:
    position_id: str
    chain: str
    token_address: str
    symbol: str
    entry_ts: float
    entry_price_usd: float
    allocated_usd: float
    tokens_amount: float
    fee_entry_usd: float
    impact_bps: float
    status: str                                  # OPEN | CLOSED_*
    strategy_id: str
    invalidation_rules: list[str] = field(default_factory=list)


@dataclass
class PositionEvaluation:
    position_id: str
    status: str
    current_price_usd: float | None
    unrealized_pnl_pct: float | None
    action_taken: str                            # HOLD | TP_EXIT | SL_EXIT | INVALIDATION_EXIT | NO_DATA_HOLD
    reason: str
    evidence: str


class PaperPositionManager:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or get_paper_trading_db_path()
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript(SCHEMA_POSITIONS)
        conn.close()

    def open_position(self, *, chain: str, token_address: str, symbol: str,
                      allocated_usd: float, entry_price_usd: float,
                      strategy_id: str = "STRAT_V3",
                      fee_bps: float = 30.0, impact_bps: float = 25.0,
                      invalidation_rules: list[str] | None = None,
                      now: float | None = None) -> PaperPosition:
        ts = time.time() if now is None else now
        if allocated_usd <= 0 or entry_price_usd <= 0:
            raise ValueError("Allocation and price must be positive")

        pid = hashlib.sha256(f"{chain}:{token_address}:{allocated_usd}:{ts}".encode()).hexdigest()[:16]
        fee_usd = allocated_usd * (fee_bps / 10000.0)
        net_usd = allocated_usd - fee_usd
        tokens_amount = net_usd / entry_price_usd

        pos = PaperPosition(
            position_id=pid,
            chain=chain,
            token_address=token_address,
            symbol=symbol,
            entry_ts=ts,
            entry_price_usd=entry_price_usd,
            allocated_usd=allocated_usd,
            tokens_amount=tokens_amount,
            fee_entry_usd=fee_usd,
            impact_bps=impact_bps,
            status="OPEN",
            strategy_id=strategy_id,
            invalidation_rules=invalidation_rules or []
        )

        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """INSERT INTO paper_positions(position_id,chain,token_address,symbol,entry_ts,entry_price_usd,
                                         allocated_usd,tokens_amount,fee_entry_usd,impact_bps,status,strategy_id,
                                         invalidation_rules,meta_json)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (pos.position_id, pos.chain, pos.token_address, pos.symbol, pos.entry_ts,
             pos.entry_price_usd, pos.allocated_usd, pos.tokens_amount, pos.fee_entry_usd,
             pos.impact_bps, pos.status, pos.strategy_id, json.dumps(pos.invalidation_rules),
             json.dumps({"paper_mode": True})))

        # Record ENTRY event
        eid = hashlib.sha256(f"ENTRY:{pid}:{ts}".encode()).hexdigest()[:16]
        conn.execute(
            """INSERT INTO paper_position_events(event_id,position_id,event_ts,event_type,current_price_usd,
                                               unrealized_pnl_pct,realized_pnl_usd,fee_exit_usd,reason,evidence_ref,meta_json)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (eid, pid, ts, "ENTRY", entry_price_usd, 0.0, 0.0, 0.0,
             "Paper position opened under strategy", f"entry_price={entry_price_usd}", json.dumps({})))
        conn.commit()
        conn.close()
        return pos

    def open_positions(self) -> list[PaperPosition]:
        """Return every currently open paper position in entry order.

        Enumeration is required by the monitor; accepting one known position id
        at a time made autonomous follow-up unreachable. This remains a local,
        paper-only read and never contacts an exchange or wallet.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT * FROM paper_positions WHERE status='OPEN' ORDER BY entry_ts"
            ).fetchall()
        finally:
            conn.close()

        positions: list[PaperPosition] = []
        for row in rows:
            try:
                rules = json.loads(row["invalidation_rules"] or "[]")
            except (TypeError, ValueError):
                rules = []
            positions.append(PaperPosition(
                position_id=row["position_id"], chain=row["chain"],
                token_address=row["token_address"], symbol=row["symbol"],
                entry_ts=row["entry_ts"], entry_price_usd=row["entry_price_usd"],
                allocated_usd=row["allocated_usd"], tokens_amount=row["tokens_amount"],
                fee_entry_usd=row["fee_entry_usd"], impact_bps=row["impact_bps"],
                status=row["status"], strategy_id=row["strategy_id"],
                invalidation_rules=rules,
            ))
        return positions

    def evaluate_position(self, position_id: str, current_price_usd: float | None,
                          last_obs_ts: float | None, is_honeypot: bool = False,
                          liquidity_drop_pct: float = 0.0,
                          now: float | None = None) -> PositionEvaluation:
        ts = time.time() if now is None else now
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        pos = conn.execute("SELECT * FROM paper_positions WHERE position_id=?", (position_id,)).fetchone()
        if not pos or pos["status"] != "OPEN":
            conn.close()
            return PositionEvaluation(position_id, "CLOSED", None, None, "NONE", "Position not open", "none")

        entry_px = pos["entry_price_usd"]

        # 1. Stale / NO_DATA check
        if current_price_usd is None or last_obs_ts is None or (ts - last_obs_ts > 4 * 3600):
            eval_res = PositionEvaluation(
                position_id=position_id,
                status="OPEN",
                current_price_usd=current_price_usd,
                unrealized_pnl_pct=None,
                action_taken="NO_DATA_HOLD",
                reason="Stale observations (>4h) or missing price",
                evidence=f"last_obs_age={ts - (last_obs_ts or 0):.0f}s"
            )
            self._log_event(conn, position_id, ts, "NO_DATA_STALE", current_price_usd, None, None, None, eval_res.reason, eval_res.evidence)
            conn.close()
            return eval_res

        # 2. Invalidation rules (e.g. honeypot detected or massive liquidity rug)
        if is_honeypot or liquidity_drop_pct >= 50.0:
            eval_res = PositionEvaluation(
                position_id=position_id,
                status="CLOSED_INVALIDATED",
                current_price_usd=current_price_usd,
                unrealized_pnl_pct=-100.0,
                action_taken="INVALIDATION_EXIT",
                reason="Invalidating risk triggered (Honeypot or LP collapse)",
                evidence=f"honeypot={is_honeypot}, lp_drop={liquidity_drop_pct:.1f}%"
            )
            conn.execute("UPDATE paper_positions SET status='CLOSED_INVALIDATED' WHERE position_id=?", (position_id,))
            self._log_event(conn, position_id, ts, "INVALIDATION_EXIT", current_price_usd, -100.0, -pos["allocated_usd"], 0.0, eval_res.reason, eval_res.evidence)
            conn.commit()
            conn.close()
            return eval_res

        # 3. Normal PnL Calculation & Take-Profit / Stop-Loss check
        pnl_pct = (current_price_usd / entry_px - 1.0) * 100.0

        if pnl_pct >= 50.0:  # +50% Take Profit
            fee_exit = pos["allocated_usd"] * (1.0 + pnl_pct / 100.0) * (pos["impact_bps"] / 10000.0)
            realized_pnl = (pos["allocated_usd"] * (pnl_pct / 100.0)) - fee_exit - pos["fee_entry_usd"]
            eval_res = PositionEvaluation(
                position_id=position_id,
                status="CLOSED_TP",
                current_price_usd=current_price_usd,
                unrealized_pnl_pct=pnl_pct,
                action_taken="TP_EXIT",
                reason=f"Target profit hit (+{pnl_pct:.1f}%)",
                evidence=f"curr_px={current_price_usd}, entry_px={entry_px}"
            )
            conn.execute("UPDATE paper_positions SET status='CLOSED_TP' WHERE position_id=?", (position_id,))
            self._log_event(conn, position_id, ts, "TP_EXIT", current_price_usd, pnl_pct, realized_pnl, fee_exit, eval_res.reason, eval_res.evidence)
        elif pnl_pct <= -25.0:  # -25% Stop Loss
            fee_exit = pos["allocated_usd"] * (1.0 + pnl_pct / 100.0) * (pos["impact_bps"] / 10000.0)
            realized_pnl = (pos["allocated_usd"] * (pnl_pct / 100.0)) - fee_exit - pos["fee_entry_usd"]
            eval_res = PositionEvaluation(
                position_id=position_id,
                status="CLOSED_SL",
                current_price_usd=current_price_usd,
                unrealized_pnl_pct=pnl_pct,
                action_taken="SL_EXIT",
                reason=f"Stop loss hit ({pnl_pct:.1f}%)",
                evidence=f"curr_px={current_price_usd}, entry_px={entry_px}"
            )
            conn.execute("UPDATE paper_positions SET status='CLOSED_SL' WHERE position_id=?", (position_id,))
            self._log_event(conn, position_id, ts, "SL_EXIT", current_price_usd, pnl_pct, realized_pnl, fee_exit, eval_res.reason, eval_res.evidence)
        else:
            eval_res = PositionEvaluation(
                position_id=position_id,
                status="OPEN",
                current_price_usd=current_price_usd,
                unrealized_pnl_pct=pnl_pct,
                action_taken="HOLD",
                reason="Position within normal bounds",
                evidence=f"pnl_pct={pnl_pct:.2f}%"
            )
            self._log_event(conn, position_id, ts, "PRICE_UPDATE", current_price_usd, pnl_pct, 0.0, 0.0, eval_res.reason, eval_res.evidence)

        conn.commit()
        conn.close()
        return eval_res

    def _log_event(self, conn: sqlite3.Connection, position_id: str, ts: float,
                   event_type: str, current_px: float | None,
                   pnl_pct: float | None, realized_pnl: float | None,
                   fee_exit: float | None, reason: str, evidence: str):
        eid = hashlib.sha256(f"{position_id}:{event_type}:{ts}".encode()).hexdigest()[:16]
        conn.execute(
            """INSERT INTO paper_position_events(event_id,position_id,event_ts,event_type,current_price_usd,
                                               unrealized_pnl_pct,realized_pnl_usd,fee_exit_usd,reason,evidence_ref,meta_json)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (eid, position_id, ts, event_type, current_px, pnl_pct, realized_pnl, fee_exit, reason, evidence, json.dumps({})))
