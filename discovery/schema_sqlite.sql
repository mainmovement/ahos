-- AHOS Discovery Core schema v1.2 (SQLite canonical-local; Postgres twin in database/schema_v1_2.sql)
-- All timestamps REAL epoch-seconds UTC. NULL = UNKNOWN (never fabricated). Raw payloads sha256-keyed.
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS raw_payloads (
  payload_sha256 TEXT PRIMARY KEY,
  provider      TEXT NOT NULL,
  endpoint      TEXT NOT NULL,
  retrieved_ts  REAL NOT NULL,
  http_status   INTEGER,
  payload_json  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tokens (
  token_id        TEXT PRIMARY KEY,               -- sha256(chain‖":"‖addr-normalized)[:32]
  chain_id        TEXT NOT NULL,
  address         TEXT NOT NULL,
  symbol          TEXT,
  name            TEXT,
  deployer_address TEXT,                          -- NULL until RPC evidence (Phase-3)
  first_seen_ts   REAL NOT NULL,
  created_at_ts   REAL,                           -- NULL = unknown
  source_first_seen_provider TEXT NOT NULL,
  meta_json       TEXT,
  status          TEXT NOT NULL DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS pairs (
  pair_id       TEXT PRIMARY KEY,                 -- sha256(chain‖dex‖pair_address)[:32]
  token_id      TEXT NOT NULL REFERENCES tokens(token_id),
  chain_id      TEXT NOT NULL,
  dex_id        TEXT,
  pair_address  TEXT NOT NULL,
  base_token_id TEXT,
  quote_symbol  TEXT,
  pair_created_ts REAL,                           -- NULL = unknown
  first_seen_ts REAL NOT NULL,
  provider      TEXT NOT NULL,
  raw_ref       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS discovery_observations (
  obs_id        TEXT PRIMARY KEY,                 -- sha256(token‖pair‖provider‖retrieved‖raw_sha)[:32]
  token_id      TEXT NOT NULL REFERENCES tokens(token_id),
  pair_id       TEXT,
  provider      TEXT NOT NULL,
  capability    TEXT NOT NULL DEFAULT 'discovery_snapshot',
  source_ts     REAL,                             -- provider's own timestamp; NULL if none
  retrieved_ts  REAL NOT NULL,
  price_usd REAL, liquidity_usd REAL, fdv REAL, market_cap REAL,
  volume_5m REAL, volume_1h REAL, volume_6h REAL, volume_24h REAL,
  txns_5m_buys INTEGER, txns_5m_sells INTEGER, txns_1h_buys INTEGER, txns_1h_sells INTEGER,
  txns_24h_buys INTEGER, txns_24h_sells INTEGER,
  price_change_5m REAL, price_change_1h REAL, price_change_6h REAL, price_change_24h REAL,
  pair_age_minutes INTEGER, boost_amount REAL,
  quality_flags TEXT,                             -- JSON array
  error_state   TEXT,                             -- JSON object; populated instead of fake values
  raw_ref       TEXT NOT NULL REFERENCES raw_payloads(payload_sha256)
);
CREATE INDEX IF NOT EXISTS idx_obs_token_ts ON discovery_observations(token_id, retrieved_ts);
CREATE INDEX IF NOT EXISTS idx_obs_retrieved ON discovery_observations(retrieved_ts);

CREATE TABLE IF NOT EXISTS observation_state (
  token_id   TEXT PRIMARY KEY REFERENCES tokens(token_id),
  state      TEXT NOT NULL CHECK (state IN ('DISCOVERED','OBSERVING','DEAD','RESOLVED')),
  entered_ts REAL NOT NULL,
  first_seen_ts REAL NOT NULL,
  last_obs_ts REAL,
  security_flagged INTEGER NOT NULL DEFAULT 0,
  meta_json TEXT
);

CREATE TABLE IF NOT EXISTS lifecycle_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  token_id TEXT NOT NULL, ts REAL NOT NULL,
  from_state TEXT, to_state TEXT NOT NULL, reason TEXT
);

CREATE TABLE IF NOT EXISTS gap_register (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  token_id TEXT NOT NULL, kind TEXT NOT NULL,
  expected_ts REAL, noted_ts REAL NOT NULL, detail TEXT
);

CREATE TABLE IF NOT EXISTS security_verdicts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  token_id TEXT NOT NULL, ts REAL NOT NULL,
  provider TEXT NOT NULL, check_key TEXT NOT NULL,
  value TEXT NOT NULL CHECK (value IN ('TRUE','FALSE','UNKNOWN')),
  severity TEXT NOT NULL CHECK (severity IN ('CRITICAL','HIGH','INFO')),
  raw_ref TEXT
);

CREATE TABLE IF NOT EXISTS gate_summary (
  token_id TEXT NOT NULL, ts REAL NOT NULL,
  verdict TEXT NOT NULL CHECK (verdict IN ('SECURITY_VETO','PASS_WITH_UNKNOWN','PASS')),
  veto_reasons TEXT, coverage REAL NOT NULL, evidence_refs TEXT,
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
  as_of_ts REAL NOT NULL, availability_ts REAL NOT NULL,
  key TEXT NOT NULL, value_num REAL, value_text TEXT,
  reliability TEXT, computed_by TEXT,
  CHECK (availability_ts <= as_of_ts),            -- RULE L3, DB-enforced
  PRIMARY KEY (token_id, feature_set_version, as_of_ts, key)
);

CREATE TABLE IF NOT EXISTS outcome_label (
  token_id TEXT NOT NULL, horizon TEXT NOT NULL, event_class TEXT NOT NULL,
  hit INTEGER, max_favorable REAL, max_adverse REAL,
  entry_price REAL, entry_price_ts REAL, resolved_ts REAL NOT NULL,
  PRIMARY KEY (token_id, horizon, event_class)
);

CREATE TABLE IF NOT EXISTS opportunity_rank (
  as_of_ts REAL NOT NULL, token_id TEXT NOT NULL, rank INTEGER,
  bullets_json TEXT, risks_json TEXT, invalidation_json TEXT, engine_version TEXT,
  PRIMARY KEY (as_of_ts, token_id)
);

-- v1.3 additive (wave-6): holder/whale snapshots (source currently rate-limited — see doc I)
CREATE TABLE IF NOT EXISTS holder_snapshot (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  token_id TEXT NOT NULL,
  ts REAL NOT NULL,
  source TEXT NOT NULL,                 -- rpc:mainnet-beta / rpc:publicnode / ...
  top_accounts_json TEXT,               -- NULL on failure
  top10_share REAL, top20_share REAL,   -- NULL when accounts unavailable
  error_state TEXT,                     -- JSON; present instead of fake values
  raw_ref TEXT
);
CREATE TABLE IF NOT EXISTS wallet_observation (
  address TEXT NOT NULL, chain TEXT NOT NULL,
  first_seen_ts REAL NOT NULL, last_seen_ts REAL NOT NULL,
  evidence_json TEXT, PRIMARY KEY (address, chain)
);
