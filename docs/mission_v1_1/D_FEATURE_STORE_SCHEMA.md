# D. FEATURE STORE SCHEMA v0.1 — Mission v1.1 §10 — 2026-08-11
# LAW: no "PUMP SCORE" yet. Features first, each with definition/formula/source/timestamps/
# missing-behavior/reliability/validation-status. Leakage prevention is machine-enforced.

## 1. Feature registry (feature_definitions)
| key | definition (formula) | source fields | missing behavior | reliability | status |
|---|---|---|---|---|---|
| liquidity_usd_t | liquidity at t | obs.liquidity_usd | skip point | HIGH | DEFINED |
| liquidity_growth_1h | (L_t − L_{t−1h})/max(L_{t−1h}, ε), ε=$100 floor | obs series | FEATURE=NULL | HIGH | DEFINED |
| liquidity_growth_6h | same over 6h | obs series | NULL | HIGH | DEFINED |
| volume_growth_1h | V_1h_t / V_1h_{t−1h} (log-ratio if prev>0 else NULL) | obs.volume_* | NULL | MED | DEFINED |
| buy_sell_imbalance_1h | (b−s)/max(b+s,1) in 1h | obs.txns_1h_* | NULL | HIGH | DEFINED |
| volume_acceleration | V_5m_t / mean(V_5m last 12 obs) | obs series | NULL (needs ≥12 pts) | MED | DEFINED |
| liquidity_to_volume_24h | L / max(V24,1) (depth adequacy) | obs | NULL | MED | DEFINED |
| token_age_hours | (as_of − pair_created_ts)/3600 | pair_created_ts | NULL if created unknown | HIGH | DEFINED |
| price_change_1h / 6h / 24h | from obs series (recomputed, not provider field) | obs.price_usd | NULL | HIGH | DEFINED |
| max_drawdown_since_first_seen | 1 − min(price)/max(price) window | obs.price_usd | NULL | HIGH | DEFINED |
| volatility_1h | stdev of 5m log returns (60m window) | obs.price_usd | NULL (<12 pts) | MED | DEFINED |
| holder_growth_1h | holders_t − holders_{t−1h} — **DEFERRED** | RPC snapshot (Phase-3) | UNKNOWN | LOW (not live) | REGISTERED-ONLY |
| whale_net_flow_1h | Σ whale buys − sells — **DEFERRED** | RPC+labels (Phase-3) | UNKNOWN | LOW | REGISTERED-ONLY |
| social_velocity / narrative_velocity | mentions/h + unique-authors ratio — **DEFERRED** (Phase-7) | RSS/CryptoPanic† | UNKNOWN | LOW | REGISTERED-ONLY |
| security_all_hard_veto_clear | 1 if no veto TRUE & ≥1 check OK else 0/NULL | security_verdict | NULL if no checks | HIGH | DEFINED |
| top_holder_concentration | top10/share — **DEFERRED** (Phase-3 RPC) | UNKNOWN | LOW | REGISTERED-ONLY |
| boost_active | latest boost_amount > 0 (DexScreener) | obs.boost_amount | NULL when provider lacks field | MED | DEFINED |
| market_regime | BTC 1h RV 3-state (reuses H12 machinery, read-only) | research/data majors | NULL | HIGH | REGISTERED-ONLY (wire lands with regime adapter; excluded from fs_v0.1 compute set — registry ⇄ computed-set equality enforced) |
† CryptoPanic endpoint 404 at probe — registry entry marked UNVERIFIED-PROVIDER until re-probe.

## 2. Storage rows
```
feature_vector(token_id, feature_set_version, as_of_ts, availability_ts, key, value_num, value_text,
               reliability, computed_by)  PK(token_id, feature_set_version, as_of_ts, key)
```
- `feature_set_version` = `fs_v0.1` (semver; definitions table is versioned with it).
- Every vector row carries both timestamps (Mission §12 hard requirement).

## 3. Missing-data behavior (uniform)
Feature cannot be computed from data with availability_ts ≤ as_of_ts ⇒ **row absent + gap_register entry**
(analytics read NULL; nothing imputed; "0 is not NULL" applies here too).

## 4. Leakage prevention (machine-enforced — the core guarantee)
```
RULE L1: compute_features(token_id, as_of) selects observations ONLY WHERE retrieved_ts <= as_of
         (retrieved = availability proxy; source_ts may be earlier, never later-trusted).
RULE L2: outcome labels are stored ONLY in outcome_label table; feature computation code has
         no import path to outcome_label (dependency-direction enforced by architecture test:
         tests/test_discovery.py::test_feature_store_has_no_outcome_import).
RULE L3: every emitted feature row asserts availability_ts <= its own as_of_ts (DB CHECK + unit test).
RULE L4: research joins ALWAYS use as_of/availability from feature_vector (review checklist; Quant role).
```
Tests: synthetic future-injection fixture (observation with retrieved_ts > as_of must never affect output;
determinism: same inputs → same features byte-identical).

## 5. Validation status ladder (feature promotion)
DEFINED → IMPL-TESTED (unit) → BACKFILLED-OBSERVED (computed on real collected series) →
RESEARCH-ASSOCIATED (event study) → PROMOTED (score-eligible via lab H-registration).
Only DEFINED exists this wave; nothing above is claimed.
