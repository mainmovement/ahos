-- AHOS Paper Trading Lab — schema v3 (Wave-8 CONTINUATION directive). ADDITIVE ONLY.
-- v1/v2 tables stay immutable. Realizable-value truth + partial exits + autonomous
-- decision evidence + learning loop. Same append-only law (UPDATE/DELETE triggers).

-- §2/§3: every monitor pass records DISPLAYED vs REALIZABLE per open position.
CREATE TABLE IF NOT EXISTS realizable_snapshot (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  trade_id TEXT NOT NULL,
  ts REAL NOT NULL,                 -- decision time (cycle now)
  obs_ts REAL,                      -- observation time the snapshot is priced on (≤ ts)
  qty_remaining REAL NOT NULL,
  price_observed REAL,
  liquidity_usd REAL,
  displayed_value_usd REAL,         -- qty*price (the number a naive UI would show)
  max_executable_notional_usd REAL, -- liquidity-absorption cap (impact ≤ EXIT_IMPACT_CAP_BPS)
  requested_exit_notional_usd REAL, -- what we would WANT to sell now (= displayed)
  executable_exit_notional_usd REAL,-- what can ACTUALLY be sold within impact cap
  exit_slippage_bps REAL,
  exit_fee_usd REAL,
  sell_tax_usd REAL,                -- NULL when provider tax UNKNOWN (never zero-filled)
  gas_cost_usd REAL,                -- PT-REALIZABLE-v1 MODEL constant per chain (NOT live)
  realizable_value_usd REAL,        -- after slip+fee+tax(known)+gas; floored at 0
  unexited_displayed_usd REAL,      -- displayed - executable notional (still only DISPLAYED truth)
  route_status TEXT NOT NULL,       -- EXECUTABLE_FULL|EXECUTABLE_PARTIAL|UNEXITABLE_HONEYPOT|
                                    -- UNEXITABLE_NO_PRICE|UNEXITABLE_NO_LIQUIDITY|SECURITY_RECHECK_CRITICAL
  model_version TEXT NOT NULL,      -- PT-REALIZABLE-v1
  detail TEXT,
  created_utc TEXT NOT NULL
);

-- §7: partial exits. A trade may have many PARTIAL rows + at most one closing FULL row.
CREATE TABLE IF NOT EXISTS paper_exit_v3 (
  exit_id TEXT PRIMARY KEY,
  trade_id TEXT NOT NULL REFERENCES paper_trade_v2(trade_id),
  exit_seq INTEGER NOT NULL,        -- 1..n within trade
  exit_kind TEXT NOT NULL,          -- PARTIAL | FULL (FULL closes the position)
  exit_ts REAL NOT NULL,
  exit_reason TEXT NOT NULL,        -- TAKE_PROFIT|STOP_LOSS|TIME_EXIT|EXIT_RISK|SECURITY_EVENT|
                                    -- LIQUIDITY_COLLAPSE|DIVERGENCE_PROFIT_LOCK|DECAY_PROFIT_LOCK|
                                    -- TRAPPED|TOTAL_LOSS (+ *_PARTIAL variants)
  rule_version TEXT NOT NULL,       -- PT-X3-v1 (owner-mandated management upgrade, forward-only)
  exit_obs_ts REAL,
  exit_price_observed REAL,
  qty_sold REAL NOT NULL,
  qty_remaining_after REAL NOT NULL,
  requested_notional_usd REAL NOT NULL,   -- what the exit decision asked to sell
  executable_notional_usd REAL NOT NULL,  -- what liquidity allowed within impact cap
  gross_proceeds_usd REAL,          -- executable*(1-slip)
  exit_fee_usd REAL,
  exit_slippage_usd REAL,
  sell_tax_usd REAL,                -- NULL when UNKNOWN
  gas_cost_usd REAL,
  net_proceeds_usd REAL,            -- gross - fee - tax(known) - gas  (= RECLAIM to cash)
  allocated_retired_usd REAL NOT NULL,    -- proportional allocated basis retired by this chunk
  realized_pnl_usd REAL,            -- net_proceeds - allocated_retired (this chunk)
  capital_loss_usd REAL,            -- >=0 on trapped/loss closes
  displayed_value_pre_usd REAL,     -- honesty pair: what the position LOOKED like
  realizable_value_pre_usd REAL,    -- vs what was realistically recoverable
  hold_hours REAL,
  closed_utc TEXT NOT NULL
);

-- §5/§12: every autonomous decision (incl. HOLD) is evidence-logged with categorical factors.
CREATE TABLE IF NOT EXISTS position_decision_event (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  trade_id TEXT NOT NULL,
  ts REAL NOT NULL,
  action TEXT NOT NULL,             -- HOLD|PARTIAL_EXIT|FULL_EXIT|RISK_EXIT|TRAPPED|TOTAL_LOSS|INVALID|NO_DATA
  reason TEXT NOT NULL,
  rule_version TEXT NOT NULL,
  momentum_class TEXT,              -- IMPROVING|FLAT|DETERIORATING|UNKNOWN (observed data only)
  continuation_prob TEXT,           -- NOT_ESTIMABLE (no-probability law) — recorded, never guessed
  reversal_prob TEXT,               -- NOT_ESTIMABLE (no-probability law)
  security_risk TEXT,               -- §N classification at decision time
  exitability TEXT,                 -- route_status from realizable snapshot
  realizable_value_usd REAL,
  displayed_value_usd REAL,
  execution_cost_usd REAL,          -- fee+slip+tax(known)+gas of the considered exit
  liquidity_risk TEXT,              -- OK|THIN|COLLAPSED|UNKNOWN
  news_risk TEXT,                   -- UNAVAILABLE_NO_FEED (documented, never fabricated)
  scam_risk TEXT,                   -- §N classification / escalation state
  opportunity_cost TEXT,            -- CASH_CONSTRAINED|CASH_AVAILABLE|NOT_APPLICABLE
  evidence_json TEXT,
  created_utc TEXT NOT NULL
);

-- §10: one structured lesson per CLOSED trade. Questions answered from evidence; UNKNOWN stays UNKNOWN.
CREATE TABLE IF NOT EXISTS post_trade_lesson (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  trade_id TEXT NOT NULL,
  closed_ts REAL NOT NULL,
  outcome_class TEXT NOT NULL,      -- PROFIT|LOSS|RUG|HONEYPOT|TRAPPED|TOTAL_LOSS|INVALIDATED
  answers_json TEXT NOT NULL,       -- §10 question set, evidence-backed or explicit UNKNOWN
  lesson TEXT NOT NULL,
  hypothesis TEXT NOT NULL,         -- testable, registered separately — rules NOT silently modified
  evidence TEXT NOT NULL,
  proposed_improvement TEXT NOT NULL,
  model_versions TEXT NOT NULL,     -- entry/exit/cost/realizable versions in force
  created_utc TEXT NOT NULL
);

-- §11: learning counters — recomputed from tables each cycle, snapshot appended for audit.
CREATE TABLE IF NOT EXISTS learning_stats_snapshot (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts REAL NOT NULL,
  stats_json TEXT NOT NULL,         -- full §11 counter block (see lessons.learning_stats)
  created_utc TEXT NOT NULL
);

CREATE TRIGGER IF NOT EXISTS rs3_no_update  BEFORE UPDATE ON realizable_snapshot      BEGIN SELECT RAISE(ABORT,'append-only: realizable_snapshot'); END;
CREATE TRIGGER IF NOT EXISTS rs3_no_delete  BEFORE DELETE ON realizable_snapshot      BEGIN SELECT RAISE(ABORT,'append-only: realizable_snapshot'); END;
CREATE TRIGGER IF NOT EXISTS px3_no_update  BEFORE UPDATE ON paper_exit_v3            BEGIN SELECT RAISE(ABORT,'append-only: paper_exit_v3'); END;
CREATE TRIGGER IF NOT EXISTS px3_no_delete  BEFORE DELETE ON paper_exit_v3            BEGIN SELECT RAISE(ABORT,'append-only: paper_exit_v3'); END;
CREATE TRIGGER IF NOT EXISTS pde_no_update  BEFORE UPDATE ON position_decision_event  BEGIN SELECT RAISE(ABORT,'append-only: position_decision_event'); END;
CREATE TRIGGER IF NOT EXISTS pde_no_delete  BEFORE DELETE ON position_decision_event  BEGIN SELECT RAISE(ABORT,'append-only: position_decision_event'); END;
CREATE TRIGGER IF NOT EXISTS ptl3_no_update BEFORE UPDATE ON post_trade_lesson        BEGIN SELECT RAISE(ABORT,'append-only: post_trade_lesson'); END;
CREATE TRIGGER IF NOT EXISTS ptl3_no_delete BEFORE DELETE ON post_trade_lesson        BEGIN SELECT RAISE(ABORT,'append-only: post_trade_lesson'); END;
CREATE TRIGGER IF NOT EXISTS lss_no_update  BEFORE UPDATE ON learning_stats_snapshot  BEGIN SELECT RAISE(ABORT,'append-only: learning_stats_snapshot'); END;
CREATE TRIGGER IF NOT EXISTS lss_no_delete  BEFORE DELETE ON learning_stats_snapshot  BEGIN SELECT RAISE(ABORT,'append-only: learning_stats_snapshot'); END;
