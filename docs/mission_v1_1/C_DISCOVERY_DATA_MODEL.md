# C. DISCOVERY DATA MODEL v0.1 — Mission v1.1 — 2026-08-11
# Doctrine: canonical identity first; every observation timestamped twice (source_ts, retrieved_ts);
# missing = NULL/UNKNOWN, never fabricated; raw payloads replayable.

## 1. Canonical Token Identity (STEP 3)
`token_id = sha256(chain_id ‖ ":" ‖ lowercase(contract_address))` — first 16 bytes hex (32 chars).
- chain_id: normalized string from controlled vocabulary: {solana, ethereum, bsc, base, arbitrum, polygon, ton, sui, …} (extensible registry, PAL normalizes provider spellings: "bsc"≡"BNB Chain").
- contract_address: chain-native form stored + lowercase comparison form used in ID (EVM checksum-insensitive; Solana base58 case-sensitive → lowercasing inside ID only for EVM chains; SOL/others use exact bytes).
- Rationale: provider-pair addresses change, token contracts do not; ID must be stable across providers.

Entities:
```
Token(token_id PK, chain_id, address, symbol, name, deployer_address NULL, first_seen_ts,
      created_at_ts NULL, source_first_seen_provider, created_by_tx NULL, meta_json, status)
Pair(pair_id PK = sha256(chain‖dex‖pair_address), token_id FK, chain_id, dex_id, pair_address,
     base_token_id, quote_symbol, pair_created_ts NULL, first_seen_ts, provider, raw_ref)
```
Dedupe: token_id unique; same token discovered by 2 providers → single Token row, provenance rows per provider.

## 2. Discovery Observations (STEP 4)
```
discovery_observation(
  obs_id PK, token_id FK, pair_id FK NULL, provider, capability='discovery_snapshot',
  source_ts NULL, retrieved_ts NOT NULL,            -- dual-time doctrine
  -- normalized numeric fields (NULL = unknown):
  price_usd, liquidity_usd, fdv, market_cap, volume_5m, volume_1h, volume_6h, volume_24h,
  txns_5m_buys, txns_5m_sells, txns_1h_buys, txns_1h_sells, txns_24h_buys, txns_24h_sells,
  price_change_5m, price_change_1h, price_change_6h, price_change_24h,
  pair_age_minutes, boost_amount NULL,
  quality_flags TEXT[],                             -- e.g. {'schema_ok','ts_fresh','complete'}
  error_state NULL,                                 -- populated instead of fake values on failure
  raw_ref NOT NULL                                  -- pointer to raw_payloads blob (sha256-keyed)
)
raw_payloads(payload_sha256 PK, provider, endpoint, retrieved_ts, http_status, payload_jsonb)
```

## 3. PAL normalized envelope (every adapter returns this; Mission §4 fields)
```
{provider_id, endpoint, chain, capability, data_type, freshness_sec,
 rate_limit:{rpm_remaining NULL, budget}, availability: OK|DEGRADED|DOWN,
 confidence: HIGH|MED|LOW (adapter-assessed), source_timestamp, retrieval_timestamp,
 error_state NULL|{kind,message,http_status}, payload:[normalized records]}
```

## 4. Security verdicts + features + scores + outcomes (pointers to D/E/F)
```
security_verdict(token_id, ts, provider, check_key, value, severity, raw_ref)   -- E
feature_vector(token_id, feature_set_version, as_of_ts, availability_ts, key, value_num, value_text, reliability)  -- D
observation_state(token_id, state, entered_ts, meta_json)                        -- F
outcome_label(token_id, horizon, event_class, hit, max_favorable, max_adverse, resolved_ts, entry_price_ts, entry_price)  -- F/STEP8
opportunity_rank(as_of_ts, token_id, rank, score NULL, bullets_json, risks_json, invalidation_json, engine_version)  -- STEP9
```

## 5. Storage plan
- Authoritative relational store: PostgreSQL (schema_v1_2.sql, additive — new tables only, no v1.1 edits).
- Sandbox/CI store: **SQLite adapter with identical DDL core** (engine pattern exists: data/ahos_local.sqlite);
  type mapping documented; tests run on SQLite so CI stays free/self-contained.
- Raw payloads: table `raw_payloads` (jsonb pg / text sqlite). Integrity: sha256 of payload bytes = PK.

## 6. Normalization rules (binding)
- USD numerics: float; prices keep full precision text-parse → float (no rounding at ingest).
- Timestamps: all UTC epoch-seconds at REST boundaries; stored ISO-8601 UTC in sqlite, timestamptz in pg.
- Provider-reported changes (price_change_*) stored as-reported for snapshot consistency; recomputed-from-series variants are separate features (D), never overwriting raw fields.
- `"0 is not NULL"`: a real zero (e.g. sells=0) is data; missing key = NULL.
