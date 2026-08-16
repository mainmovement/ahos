-- ============================================================================
-- AHOS PostgreSQL Schema v1.1-FINAL
-- Supersedes: v1.0 (129 lines, verified PASS in AHOS_PHASE_1_PRODUCTION_VERIFICATION_REPORT)
-- Change: additive only (dataset versioning columns, extra CHECKs) — no table removed,
--         no Phase-1 architecture break (Rule #1 preserved)
-- Security: no secrets stored in any table. All monetary values NUMERIC, guarded.
-- ============================================================================

-- ---------- 1. market_data (independent base) ----------
CREATE TABLE IF NOT EXISTS market_data (
    id              BIGSERIAL PRIMARY KEY,
    symbol          TEXT        NOT NULL,
    timeframe       TEXT        NOT NULL DEFAULT '1h'
                    CHECK (timeframe IN ('1m','5m','15m','1h','4h','1d')),
    ts              TIMESTAMPTZ NOT NULL,
    open            NUMERIC(20,8) NOT NULL CHECK (open > 0),
    high            NUMERIC(20,8) NOT NULL CHECK (high >= low),
    low             NUMERIC(20,8) NOT NULL CHECK (low <= high),
    close           NUMERIC(20,8) NOT NULL CHECK (close >= low AND close <= high),
    volume          NUMERIC(24,8) NOT NULL CHECK (volume >= 0),
    source          TEXT        NOT NULL CHECK (source IN ('LBank','Bybit','Manual_CSV')),
    dataset_version TEXT        NOT NULL,           -- e.g. v1.0-phase1a-2026-08-09
    checksum_sha256 TEXT,                            -- per-SCHEMA.md versioning
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (symbol, timeframe, ts, source)           -- dedupe gate
);
CREATE INDEX IF NOT EXISTS idx_md_symbol_time ON market_data (symbol, ts);
CREATE INDEX IF NOT EXISTS idx_md_source_time ON market_data (source, ts);

-- ---------- 2. agent_registry (independent reference) ----------
CREATE TABLE IF NOT EXISTS agent_registry (
    agent_id        TEXT PRIMARY KEY,                -- AGENT-01 .. AGENT-10
    agent_name      TEXT NOT NULL,
    agent_group     TEXT NOT NULL CHECK (agent_group IN ('DATA','EXEC','COMMS','SUPERVISORY','AUDIT')),
    enabled         BOOLEAN NOT NULL DEFAULT TRUE,
    registered_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------- 3. trade_decisions (FK -> agent_registry) ----------
CREATE TABLE IF NOT EXISTS trade_decisions (
    id              BIGSERIAL PRIMARY KEY,
    signal_id       TEXT NOT NULL UNIQUE,
    agent_id        TEXT NOT NULL REFERENCES agent_registry(agent_id) ON DELETE RESTRICT,
    ts              TIMESTAMPTZ NOT NULL DEFAULT now(),
    symbol          TEXT NOT NULL,
    decision        TEXT NOT NULL CHECK (decision IN ('LONG','SHORT','NO_TRADE')),
    confidence_score NUMERIC(5,4) CHECK (confidence_score BETWEEN 0 AND 1),
    entry_price     NUMERIC(20,8) CHECK (entry_price > 0),
    stop_loss       NUMERIC(20,8) CHECK (stop_loss > 0),
    take_profit     NUMERIC(20,8) CHECK (take_profit > 0),
    position_size   NUMERIC(24,8) CHECK (position_size >= 0),
    leverage        NUMERIC(4,1) NOT NULL CHECK (leverage <= 10.0),
    risk_percent    NUMERIC(4,2) NOT NULL CHECK (risk_percent <= 2.0),
    reason          TEXT NOT NULL,                    -- mandatory explanation, never null
    execution_status TEXT NOT NULL DEFAULT 'PENDING'
                    CHECK (execution_status IN ('PENDING','PAPER','EXECUTED','REJECTED','CANCELLED')),
    dataset_version TEXT
);
CREATE INDEX IF NOT EXISTS idx_td_symbol_time ON trade_decisions (symbol, ts);
CREATE INDEX IF NOT EXISTS idx_td_agent_time  ON trade_decisions (agent_id, ts);

-- ---------- 4. position_monitoring (independent) ----------
CREATE TABLE IF NOT EXISTS position_monitoring (
    id              BIGSERIAL PRIMARY KEY,
    decision_id     BIGINT REFERENCES trade_decisions(id) ON DELETE RESTRICT,
    symbol          TEXT NOT NULL,
    side            TEXT NOT NULL CHECK (side IN ('LONG','SHORT')),
    entry_price     NUMERIC(20,8) NOT NULL CHECK (entry_price > 0),
    quantity        NUMERIC(24,8) NOT NULL CHECK (quantity > 0),
    unrealized_pnl  NUMERIC(20,8),
    risk_status     TEXT NOT NULL DEFAULT 'OK'
                    CHECK (risk_status IN ('OK','WARNING','SL_NEAR','TP_NEAR','LIQUIDATION_RISK')),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_pos_symbol_status ON position_monitoring (symbol, risk_status);

-- ---------- 5. evolution_memory (independent — Phase 3 learning layer) ----------
CREATE TABLE IF NOT EXISTS evolution_memory (
    id              BIGSERIAL PRIMARY KEY,
    decision_id     BIGINT REFERENCES trade_decisions(id) ON DELETE RESTRICT,
    regime          TEXT CHECK (regime IN ('BULL','BEAR','SIDEWAYS','HIGH_VOL','LOW_VOL')),
    outcome         TEXT CHECK (outcome IN ('WIN','LOSS','BREAKEVEN')),
    pattern_notes   TEXT,
    applied_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_evolution_applied ON evolution_memory (applied_at);

-- ---------- 6. telegram_audit (independent) ----------
CREATE TABLE IF NOT EXISTS telegram_audit (
    id              BIGSERIAL PRIMARY KEY,
    ts              TIMESTAMPTZ NOT NULL DEFAULT now(),
    chat_id         BIGINT NOT NULL,
    command         TEXT NOT NULL,                    -- token/chat never logged beyond id
    agent_response  TEXT,
    risk_level      TEXT CHECK (risk_level IN ('LOW','HIGH')),
    approved        BOOLEAN,
    verified        BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS idx_telegram_audit_time ON telegram_audit (ts);

-- ---------- 7. agent_audit_trail (independent, references agent) ----------
CREATE TABLE IF NOT EXISTS agent_audit_trail (
    id              BIGSERIAL PRIMARY KEY,
    ts              TIMESTAMPTZ NOT NULL DEFAULT now(),
    agent_id        TEXT NOT NULL REFERENCES agent_registry(agent_id) ON DELETE RESTRICT,
    action          TEXT NOT NULL,
    reason          TEXT NOT NULL,
    result          TEXT,
    verified_by_agent_10 BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS idx_audit_agent_time ON agent_audit_trail (agent_id, ts);

-- ---------- 8. model_parameter_history (roll-back capable) ----------
CREATE TABLE IF NOT EXISTS model_parameter_history (
    id              BIGSERIAL PRIMARY KEY,
    ts              TIMESTAMPTZ NOT NULL DEFAULT now(),
    parameter_key   TEXT NOT NULL,
    previous_value  TEXT NOT NULL,
    new_value       TEXT NOT NULL,
    change_reason   TEXT NOT NULL,
    evidence_ref    TEXT,                             -- backtest/OOS/WF/MC report reference
    rollback_script_path TEXT NOT NULL,               -- mandatory per Phase-3 framework
    approved_by_agent_10  BOOLEAN NOT NULL DEFAULT FALSE,
    approved_by_human     BOOLEAN NOT NULL DEFAULT FALSE,
    applied        BOOLEAN NOT NULL DEFAULT FALSE,
    rolled_back    BOOLEAN NOT NULL DEFAULT FALSE
);

-- ---------- Seed: 10-agent registry (frozen mapping) ----------
INSERT INTO agent_registry (agent_id, agent_name, agent_group) VALUES
 ('AGENT-01','DataFetch','DATA'), ('AGENT-02','StrategyEngine','DATA'),
 ('AGENT-03','Execution','EXEC'), ('AGENT-04','Security','EXEC'),
 ('AGENT-05','Telegram','COMMS'), ('AGENT-06','Report','COMMS'),
 ('AGENT-07','LeadEngineer','SUPERVISORY'), ('AGENT-08','RiskManager','SUPERVISORY'),
 ('AGENT-09','QualityAssurance','SUPERVISORY'), ('AGENT-10','FinalAuditor','AUDIT')
ON CONFLICT (agent_id) DO NOTHING;
