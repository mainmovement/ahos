-- AHOS PostgreSQL schema v1.2 — ADDITIVE migration over v1.1 (no v1.1 object altered/dropped)
-- Discovery Core tables (twin of discovery/schema_sqlite.sql). Apply: psql -f schema_v1_2.sql
BEGIN;

CREATE TABLE IF NOT EXISTS raw_payloads (
  payload_sha256 TEXT PRIMARY KEY,
  provider      TEXT NOT NULL,
  endpoint      TEXT NOT NULL,
  retrieved_ts  DOUBLE PRECISION NOT NULL,
  http_status   INTEGER,
  payload_json  JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS tokens (
  token_id        TEXT PRIMARY KEY,
  chain_id        TEXT NOT NULL,
  address         TEXT NOT NULL,
  symbol          TEXT,
  name            TEXT,
  deployer_address TEXT,
  first_seen_ts   DOUBLE PRECISION NOT NULL,
  created_at_ts   DOUBLE PRECISION,
  source_first_seen_provider TEXT NOT NULL,
  meta_json       JSONB,
  status          TEXT NOT NULL DEFAULT 'active',
  UNIQUE (chain_id, address)
);

CREATE TABLE IF NOT EXISTS pairs (
  pair_id       TEXT PRIMARY KEY,
  token_id      TEXT NOT NULL REFERENCES tokens(token_id),
  chain_id      TEXT NOT NULL,
  dex_id        TEXT,
  pair_address  TEXT NOT NULL,
  base_token_id TEXT,
  quote_symbol  TEXT,
  pair_created_ts DOUBLE PRECISION,
  first_seen_ts DOUBLE PRECISION NOT NULL,
  provider      TEXT NOT NULL,
  raw_ref       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS discovery_observations (
  obs_id        TEXT PRIMARY KEY,
  token_id      TEXT NOT NULL REFERENCES tokens(token_id),
  pair_id       TEXT,
  provider      TEXT NOT NULL,
  capability    TEXT NOT NULL DEFAULT 'discovery_snapshot',
  source_ts     DOUBLE PRECISION,
  retrieved_ts  DOUBLE PRECISION NOT NULL,
  price_usd DOUBLE PRECISION, liquidity_usd DOUBLE PRECISION, fdv DOUBLE PRECISION, market_cap DOUBLE PRECISION,
  volume_5m DOUBLE PRECISION, volume_1h DOUBLE PRECISION, volume_6h DOUBLE PRECISION, volume_24h DOUBLE PRECISION,
  txns_5m_buys INTEGER, txns_5m_sells INTEGER, txns_1h_buys INTEGER, txns_1h_sells INTEGER,
  txns_24h_buys INTEGER, txns_24h_sells INTEGER,
  price_change_5m DOUBLE PRECISION, price_change_1h DOUBLE PRECISION, price_change_6h DOUBLE PRECISION, price_change_24h DOUBLE PRECISION,
  pair_age_minutes INTEGER, boost_amount DOUBLE PRECISION,
  quality_flags JSONB, error_state JSONB,
  raw_ref       TEXT NOT NULL REFERENCES raw_payloads(payload_sha256)
);
CREATE INDEX IF NOT EXISTS idx_obs_token_ts ON discovery_observations(token_id, retrieved_ts);
CREATE INDEX IF NOT EXISTS idx_obs_retrieved ON discovery_observations(retrieved_ts);

CREATE TABLE IF NOT EXISTS observation_state (
  token_id   TEXT PRIMARY KEY REFERENCES tokens(token_id),
  state      TEXT NOT NULL CHECK (state IN ('DISCOVERED','OBSERVING','DEAD','RESOLVED')),
  entered_ts DOUBLE PRECISION NOT NULL,
  first_seen_ts DOUBLE PRECISION NOT NULL,
  last_obs_ts DOUBLE PRECISION,
  security_flagged INTEGER NOT NULL DEFAULT 0,
  meta_json  JSONB
);

CREATE TABLE IF NOT EXISTS lifecycle_events (
  id BIGSERIAL PRIMARY KEY,
  token_id TEXT NOT NULL, ts DOUBLE PRECISION NOT NULL,
  from_state TEXT, to_state TEXT NOT NULL, reason TEXT
);

CREATE TABLE IF NOT EXISTS gap_register (
  id BIGSERIAL PRIMARY KEY,
  token_id TEXT NOT NULL, kind TEXT NOT NULL,
  expected_ts DOUBLE PRECISION, noted_ts DOUBLE PRECISION NOT NULL, detail TEXT
);

CREATE TABLE IF NOT EXISTS security_verdicts (
  id BIGSERIAL PRIMARY KEY,
  token_id TEXT NOT NULL, ts DOUBLE PRECISION NOT NULL,
  provider TEXT NOT NULL, check_key TEXT NOT NULL,
  value TEXT NOT NULL CHECK (value IN ('TRUE','FALSE','UNKNOWN')),
  severity TEXT NOT NULL CHECK (severity IN ('CRITICAL','HIGH','INFO')),
  raw_ref TEXT
);

CREATE TABLE IF NOT EXISTS gate_summary (
  token_id TEXT NOT NULL, ts DOUBLE PRECISION NOT NULL,
  verdict TEXT NOT NULL CHECK (verdict IN ('SECURITY_VETO','PASS_WITH_UNKNOWN','PASS')),
  veto_reasons JSONB, coverage DOUBLE PRECISION NOT NULL, evidence_refs JSONB,
  PRIMARY KEY (token_id, ts)
);

CREATE TABLE IF NOT EXISTS feature_definitions (
  key TEXT NOT NULL, feature_set_version TEXT NOT NULL,
  definition TEXT NOT NULL, formula TEXT NOT NULL, source_fields TEXT NOT NULL,
  missing_behavior TEXT NOT NULL, reliability TEXT NOT NULL, status TEXT NOT NULL,
  PRIMARY KEY (key, feature_set_version)
);

CREATE TABLE IF NOT EXISTS feature_vector (
  token_id TEXT NOT NULL, feature_set_version TEXT NOT NULL,
  as_of_ts DOUBLE PRECISION NOT NULL, availability_ts DOUBLE PRECISION NOT NULL,
  key TEXT NOT NULL, value_num DOUBLE PRECISION, value_text TEXT,
  reliability TEXT, computed_by TEXT,
  CHECK (availability_ts <= as_of_ts),
  PRIMARY KEY (token_id, feature_set_version, as_of_ts, key)
);

CREATE TABLE IF NOT EXISTS outcome_label (
  token_id TEXT NOT NULL, horizon TEXT NOT NULL, event_class TEXT NOT NULL,
  hit INTEGER, max_favorable DOUBLE PRECISION, max_adverse DOUBLE PRECISION,
  entry_price DOUBLE PRECISION, entry_price_ts DOUBLE PRECISION,
  resolved_ts DOUBLE PRECISION NOT NULL,
  PRIMARY KEY (token_id, horizon, event_class)
);

CREATE TABLE IF NOT EXISTS opportunity_rank (
  as_of_ts DOUBLE PRECISION NOT NULL, token_id TEXT NOT NULL, rank INTEGER,
  bullets_json JSONB, risks_json JSONB, invalidation_json JSONB, engine_version TEXT,
  PRIMARY KEY (as_of_ts, token_id)
);

COMMIT;
