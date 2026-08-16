# AHOS CANONICAL — DATA MODEL (current truth)
Sources of truth: `discovery/schema_sqlite.sql` (canonical local) · `database/postgresql_schema.sql` v1.1 (legacy core)
· `database/schema_v1_2.sql` (pg twin, additive). Full field rationale: docs/mission_v1_1/C.

## v1.1 (legacy, frozen) — market_data · agent_registry · trade_decisions (PAPER) · agent_audit_trail ·
## model_parameter_history · kill Switch flags etc. (8 tables; in use by engine/n8n design)

## v1.2 (discovery core, additive)
raw_payloads(sha256 PK, provider, endpoint, retrieved_ts, http_status, payload)
tokens(token_id PK, chain_id, address, symbol, name, deployer?, first_seen_ts, created_at_ts?, src_provider, meta, status)
pairs(pair_id PK, token_id FK, chain, dex, pair_address, quote, pair_created_ts?, first_seen_ts, provider, raw_ref)
discovery_observations(obs_id PK, token_id, pair_id, provider, source_ts?, retrieved_ts, 20 metric fields NULL-able,
  quality_flags, error_state?, raw_ref)            — "0 real, NULL unknown" law
observation_state · lifecycle_events · gap_register — 72h machine with audit trail
security_verdicts(check rows TRUE/FALSE/UNKNOWN) · gate_summary(verdict, coverage, refs)
feature_definitions(versioned registry) · feature_vector(as_of_ts+availability_ts; CHECK avail<=as_of)
outcome_label(horizon×class grid; entry-window honest) · opportunity_rank(snapshot per as_of)

## Rules
NULL=UNKNOWN (never fabricated) · dual timestamps everywhere · raw payload sha256 before normalization ·
additive-only migrations (destructive change = architect+council sign-off) · scope/scoping notes on restricted series.
