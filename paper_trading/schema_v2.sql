-- AHOS Paper Trading Lab — schema v2 (Wave-8). ADDITIVE to schema v1 (which stays immutable).
-- Event-sourced bankroll + states + scam evidence. Same append-only law (triggers).

CREATE TABLE IF NOT EXISTS portfolio_ledger (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts REAL NOT NULL,
  event TEXT NOT NULL,             -- INIT | ALLOCATE | RECLAIM | LOSS_RECOGNIZED
  trade_id TEXT,
  bankroll_before REAL NOT NULL,
  amount REAL NOT NULL,            -- signed: ALLOCATE/LOSS negative, RECLAIM positive
  cash_after REAL NOT NULL,        -- free cash after this event
  detail TEXT,
  created_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS position_state_event (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  trade_id TEXT NOT NULL,
  ts REAL NOT NULL,
  state TEXT NOT NULL,             -- §M enum; appended, never updated
  reason TEXT NOT NULL,
  created_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scam_assessment (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  token_id TEXT NOT NULL,
  ts REAL NOT NULL,
  classification TEXT NOT NULL,    -- §N enum
  reasons TEXT NOT NULL,           -- JSON list — exactly WHY
  evidence_json TEXT NOT NULL,
  created_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS decision_snapshot_v2 (
  snapshot_id    TEXT PRIMARY KEY,
  token_id       TEXT NOT NULL UNIQUE,   -- one v2 decision per token (v1 law mirrored per version)
  chain TEXT, address TEXT, symbol TEXT,
  cohort         TEXT,
  discovered_ts  REAL NOT NULL,
  decision_ts    REAL NOT NULL,
  features_json  TEXT NOT NULL,
  security_json  TEXT NOT NULL,          -- full multi-source evaluation incl. taxes + classification
  rule_version   TEXT NOT NULL,
  decision       TEXT NOT NULL,          -- QUALIFIED_ENTRY | NOT_QUALIFIED | QUALIFIED_SKIPPED_NO_CASH
  reject_class   TEXT,                   -- security|liquidity|insufficient_data|honeypot|scam|cash|none
  reason         TEXT NOT NULL,
  created_utc    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS paper_trade_v2 (
  trade_id TEXT PRIMARY KEY,
  strategy_version TEXT NOT NULL,   -- PT-BANKROLL-v2
  snapshot_id TEXT NOT NULL UNIQUE REFERENCES decision_snapshot(snapshot_id),
  token_id TEXT NOT NULL UNIQUE,
  chain TEXT, address TEXT, symbol TEXT,
  cohort TEXT NOT NULL,             -- NEW_LAUNCH | EARLY_LAUNCH | ESTABLISHED
  discovered_ts REAL NOT NULL,
  entry_decision_ts REAL NOT NULL,
  entry_ts REAL NOT NULL,
  entry_price_observed REAL NOT NULL,
  bankroll_before REAL NOT NULL,
  amount_allocated REAL NOT NULL,   -- total cash out the door (notional incl. entry fee)
  qty REAL NOT NULL,
  fee_entry_usd REAL NOT NULL,
  entry_slippage_bps REAL NOT NULL,
  entry_price_exec REAL NOT NULL,
  liq_at_entry REAL,
  expected_exit_liquidity_usd REAL, -- model estimate at decision time
  buy_tax_bps REAL, sell_tax_bps REAL, transfer_tax_bps REAL,   -- NULL = UNKNOWN (never assumed 0)
  cost_completeness TEXT NOT NULL,  -- FULL | PARTIAL(taxes UNKNOWN)
  security_class TEXT NOT NULL,     -- §N classification at entry (never 'safe')
  execution_class TEXT NOT NULL,    -- EXECUTABLE_OK | EXECUTABLE_THIN
  opportunity_class TEXT NOT NULL,  -- qualitative band (NO numeric score pre-gate — council rule)
  exit_rule_version TEXT NOT NULL,  -- PT-X2-v2
  monitoring_horizon_ts REAL NOT NULL,
  created_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS paper_exit_v2 (
  trade_id TEXT PRIMARY KEY REFERENCES paper_trade_v2(trade_id),
  exit_ts REAL NOT NULL,
  exit_reason TEXT NOT NULL,        -- incl. EXIT_RISK | TRAPPED | TOTAL_LOSS (§B)
  exit_obs_ts REAL,
  exit_price_observed REAL,
  qty_sold REAL NOT NULL,           -- may be partial==qty in v2 (full exits only)
  gross_proceeds_usd REAL,
  exit_fee_usd REAL,
  exit_slippage_usd REAL,
  sell_tax_usd REAL,                -- NULL when tax UNKNOWN → cost_completeness PARTIAL
  recoverable_value_usd REAL,       -- what would realistically come back
  total_trade_cost_usd REAL,
  realized_pnl_usd REAL,
  realized_pnl_pct REAL,
  capital_loss_usd REAL,            -- allocated - recoverable (>=0 when trapped)
  mfe_pct REAL, mae_pct REAL, hold_hours REAL,
  closed_utc TEXT NOT NULL
);

CREATE TRIGGER IF NOT EXISTS ptl_no_update BEFORE UPDATE ON portfolio_ledger     BEGIN SELECT RAISE(ABORT,'append-only: portfolio_ledger'); END;
CREATE TRIGGER IF NOT EXISTS ptl_no_delete BEFORE DELETE ON portfolio_ledger     BEGIN SELECT RAISE(ABORT,'append-only: portfolio_ledger'); END;
CREATE TRIGGER IF NOT EXISTS pse_no_update BEFORE UPDATE ON position_state_event BEGIN SELECT RAISE(ABORT,'append-only: position_state_event'); END;
CREATE TRIGGER IF NOT EXISTS pse_no_delete BEFORE DELETE ON position_state_event BEGIN SELECT RAISE(ABORT,'append-only: position_state_event'); END;
CREATE TRIGGER IF NOT EXISTS sa_no_update  BEFORE UPDATE ON scam_assessment      BEGIN SELECT RAISE(ABORT,'append-only: scam_assessment'); END;
CREATE TRIGGER IF NOT EXISTS sa_no_delete  BEFORE DELETE ON scam_assessment      BEGIN SELECT RAISE(ABORT,'append-only: scam_assessment'); END;
CREATE TRIGGER IF NOT EXISTS pt2_no_update BEFORE UPDATE ON paper_trade_v2       BEGIN SELECT RAISE(ABORT,'append-only: paper_trade_v2'); END;
CREATE TRIGGER IF NOT EXISTS pt2_no_delete BEFORE DELETE ON paper_trade_v2       BEGIN SELECT RAISE(ABORT,'append-only: paper_trade_v2'); END;
CREATE TRIGGER IF NOT EXISTS px2_no_update BEFORE UPDATE ON paper_exit_v2        BEGIN SELECT RAISE(ABORT,'append-only: paper_exit_v2'); END;
CREATE TRIGGER IF NOT EXISTS px2_no_delete BEFORE DELETE ON paper_exit_v2        BEGIN SELECT RAISE(ABORT,'append-only: paper_exit_v2'); END;
CREATE TRIGGER IF NOT EXISTS ds2_no_update BEFORE UPDATE ON decision_snapshot_v2 BEGIN SELECT RAISE(ABORT,'append-only: decision_snapshot_v2'); END;
CREATE TRIGGER IF NOT EXISTS ds2_no_delete BEFORE DELETE ON decision_snapshot_v2 BEGIN SELECT RAISE(ABORT,'append-only: decision_snapshot_v2'); END;
