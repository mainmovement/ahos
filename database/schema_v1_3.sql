-- AHOS PostgreSQL schema v1.3 — ADDITIVE (holder/whale snapshots; wave-6). Apply after v1.2.
BEGIN;
CREATE TABLE IF NOT EXISTS holder_snapshot (
  id BIGSERIAL PRIMARY KEY,
  token_id TEXT NOT NULL,
  ts DOUBLE PRECISION NOT NULL,
  source TEXT NOT NULL,
  top_accounts_json JSONB,
  top10_share DOUBLE PRECISION, top20_share DOUBLE PRECISION,
  error_state JSONB,
  raw_ref TEXT
);
CREATE TABLE IF NOT EXISTS wallet_observation (
  address TEXT NOT NULL, chain TEXT NOT NULL,
  first_seen_ts DOUBLE PRECISION NOT NULL, last_seen_ts DOUBLE PRECISION NOT NULL,
  evidence_json JSONB, PRIMARY KEY (address, chain)
);
COMMIT;
