-- AHOS Paper Trading Lab — schema v1 (Wave-7 Track B). Separate store: data/paper_trading.sqlite.
-- ISOLATION LAW: this store is the ONLY store the lab writes. Discovery store is opened READ-ONLY.
-- APPEND-ONLY LAW: every table is write-once; UPDATE/DELETE are blocked by triggers.
-- Event-sourced lifecycle: DISCOVERED (snapshot) → QUALIFIED (decision) → PAPER_ENTRY (paper_trade)
--   → MONITORING (monitor_events) → EXIT (paper_exit) → POST_TRADE_ANALYSIS (reports). No rewrites.

CREATE TABLE IF NOT EXISTS strategy_version (
  version         TEXT PRIMARY KEY,      -- e.g. PT-BASELINE-v1 (entry) + exit/cost refs inside json
  created_utc     TEXT NOT NULL,
  hypothesis      TEXT NOT NULL,
  entry_rules_json TEXT NOT NULL,
  exit_rules_json  TEXT NOT NULL,
  cost_json        TEXT NOT NULL,
  failure_criteria TEXT NOT NULL,
  success_criteria TEXT NOT NULL,
  status_note      TEXT NOT NULL         -- factual state notes only; versioning replaces mutation
);

CREATE TABLE IF NOT EXISTS decision_snapshot (
  snapshot_id    TEXT PRIMARY KEY,       -- sha of (token_id, decision_ts, rule_version)
  token_id       TEXT NOT NULL UNIQUE,   -- ONE decision per token (dedupe + determinism)
  chain          TEXT,
  address        TEXT,
  symbol         TEXT,
  discovered_ts  REAL NOT NULL,          -- first_seen_ts from discovery (unchanged, cited)
  decision_ts    REAL NOT NULL,          -- wall clock of the decision
  features_json  TEXT NOT NULL,          -- ONLY observations with retrieved_ts <= decision_ts
  security_json  TEXT NOT NULL,          -- checks + verdict evaluated at decision_ts (never future)
  rule_version   TEXT NOT NULL,
  decision       TEXT NOT NULL,          -- QUALIFIED_ENTRY | NOT_QUALIFIED
  reason         TEXT NOT NULL,
  created_utc    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS paper_trade (
  trade_id        TEXT PRIMARY KEY,
  strategy_version TEXT NOT NULL,
  snapshot_id     TEXT NOT NULL UNIQUE REFERENCES decision_snapshot(snapshot_id),
  token_id        TEXT NOT NULL UNIQUE,  -- one paper trade per token, ever
  chain TEXT, address TEXT, symbol TEXT,
  discovered_ts   REAL NOT NULL,
  entry_decision_ts REAL NOT NULL,
  entry_ts        REAL NOT NULL,         -- observation ts used as entry reference
  entry_price_observed REAL NOT NULL,
  fee_bps          REAL NOT NULL,
  entry_slippage_bps REAL NOT NULL,
  entry_price_exec  REAL NOT NULL,       -- observed * (1 + slip)  (buy)
  notional_usd   REAL NOT NULL,
  qty            REAL NOT NULL,          -- (notional - fee_entry) / entry_price_exec
  fee_entry_usd  REAL NOT NULL,
  liq_at_entry   REAL,                   -- NULL allowed → recorded UNKNOWN, never fabricated
  exit_rule_version TEXT NOT NULL,
  monitoring_horizon_ts REAL NOT NULL,
  created_utc    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS monitor_event (    -- append-only observation events while OPEN
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  trade_id  TEXT NOT NULL REFERENCES paper_trade(trade_id),
  ts        REAL NOT NULL,                   -- event wall-clock assessed
  obs_ts    REAL,                            -- underlying observation ts (NULL if none)
  price_usd REAL, liquidity_usd REAL, volume_24h REAL,
  event     TEXT NOT NULL,                   -- OBSERVED | NO_NEW_DATA | SECURITY_REVIEW | ...
  detail    TEXT,
  UNIQUE(trade_id, obs_ts, event)
);

CREATE TABLE IF NOT EXISTS paper_exit (       -- at most one exit per trade
  trade_id     TEXT PRIMARY KEY REFERENCES paper_trade(trade_id),
  exit_ts      REAL NOT NULL,
  exit_reason  TEXT NOT NULL,                -- TAKE_PROFIT|STOP_LOSS|TIME_EXIT|LIQUIDITY_COLLAPSE|SECURITY_EVENT|INVALID_*
  exit_obs_ts  REAL,
  exit_price_observed REAL,
  exit_slippage_bps REAL,
  exit_price_exec REAL,
  gross_pnl_usd REAL,                        -- price movement only
  slippage_usd   REAL,                       -- adverse slippage, both legs
  fee_exit_usd   REAL,
  cost_total_usd REAL,                       -- fee_entry + fee_exit
  net_pnl_usd    REAL,                       -- gross - slippage - costs (fees)
  mfe_pct REAL, mae_pct REAL,
  hold_hours REAL,
  closed_utc   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS invalidation (     -- integrity evidence; trades are never edited
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  scope TEXT NOT NULL,                       -- TRADE | SNAPSHOT | EXPERIMENT
  ref_id TEXT NOT NULL,
  reason TEXT NOT NULL,
  created_utc TEXT NOT NULL
);

-- append-only enforcement (construction, not convention)
CREATE TRIGGER IF NOT EXISTS pt_no_update_trade  BEFORE UPDATE ON paper_trade       BEGIN SELECT RAISE(ABORT,'append-only: paper_trade'); END;
CREATE TRIGGER IF NOT EXISTS pt_no_delete_trade  BEFORE DELETE ON paper_trade       BEGIN SELECT RAISE(ABORT,'append-only: paper_trade'); END;
CREATE TRIGGER IF NOT EXISTS pt_no_update_snap   BEFORE UPDATE ON decision_snapshot BEGIN SELECT RAISE(ABORT,'append-only: decision_snapshot'); END;
CREATE TRIGGER IF NOT EXISTS pt_no_delete_snap   BEFORE DELETE ON decision_snapshot BEGIN SELECT RAISE(ABORT,'append-only: decision_snapshot'); END;
CREATE TRIGGER IF NOT EXISTS pt_no_update_exit   BEFORE UPDATE ON paper_exit        BEGIN SELECT RAISE(ABORT,'append-only: paper_exit'); END;
CREATE TRIGGER IF NOT EXISTS pt_no_delete_exit   BEFORE DELETE ON paper_exit        BEGIN SELECT RAISE(ABORT,'append-only: paper_exit'); END;
CREATE TRIGGER IF NOT EXISTS pt_no_update_mon    BEFORE UPDATE ON monitor_event     BEGIN SELECT RAISE(ABORT,'append-only: monitor_event'); END;
CREATE TRIGGER IF NOT EXISTS pt_no_delete_mon    BEFORE DELETE ON monitor_event     BEGIN SELECT RAISE(ABORT,'append-only: monitor_event'); END;
CREATE TRIGGER IF NOT EXISTS pt_no_update_inv    BEFORE UPDATE ON invalidation      BEGIN SELECT RAISE(ABORT,'append-only: invalidation'); END;
CREATE TRIGGER IF NOT EXISTS pt_no_delete_inv    BEFORE DELETE ON invalidation      BEGIN SELECT RAISE(ABORT,'append-only: invalidation'); END;
CREATE TRIGGER IF NOT EXISTS pt_no_update_strat  BEFORE UPDATE ON strategy_version  BEGIN SELECT RAISE(ABORT,'append-only: strategy_version'); END;
CREATE TRIGGER IF NOT EXISTS pt_no_delete_strat  BEFORE DELETE ON strategy_version  BEGIN SELECT RAISE(ABORT,'append-only: strategy_version'); END;
