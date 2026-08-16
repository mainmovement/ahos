# E. DISCOVERY FEATURE EXPANSION PLAN — Wave-6 (Part V mapping) — 2026-08-11
# Marks: EXISTS / PARTIAL / MISSING / MOCK / LIVE VERIFIED / UNKNOWN

## Current coverage vs Part V matrix
| Family | Feature | Wave | State |
|---|---|---|---|
| MARKET | liquidity_usd_t, growth_1h/6h, volume_growth_1h, volume_acceleration, buy_sell_imbalance_1h, price_change_1h/6h/24h, volatility_1h, liquidity_to_volume_24h, max_drawdown_since_first_seen, token_age_hours, boost_active | 5 | EXISTS (fs_v0.1, leak-proof) |
| MARKET | liquidity_stability (rolling CV of L over window), txn_acceleration (5m txn slope), market_cap_change, unique buyers/sellers(via proxies only — true uniques need RPC tx-level data) | 6 | reg. fs_v0.2 (stability/txn-acc/mcap now; uniques REGISTERED-ONLY) |
| HOLDER | top_holder_concentration (top10/top20 share), top20_net_flow_1h (whale-flow seed) | 6 | fs_v0.2 — **code IMPLEMENTED; source BLOCKED: getTokenLargestAccounts rejected on 5/5 free public SOL RPCs (429/403/401/timeout, probe 2026-08-11 → doc I §1, R-13 family). Features emit only from real snapshot rows; currently honestly absent.** |
| HOLDER | holder_growth (total count), holder_survival | — | MISSING-by-platform: free RPC cannot count holders (getProgramAccounts cost-blocked publicly) → UNKNOWN documented, never faked |
| ON-CHAIN | deployer-linked wallets, funding relationships, wallet age | 7+ | ARCHITECTURE (doc I) — needs tx-history (indexer/paid page APIs): PARTIAL via RPC signatures (slow) |
| WHALE | accumulation/distribution from top-account deltas (top20 flow), first-entry, coordinated timing | 6-7 | fs_v0.2 seeds (top20 net-flow) + doc I |
| SOCIAL | velocity/unique-authors/engagement | 7 | INTERFACES ONLY (doc J); no paid social API (X $200/mo blocked) |

## fs_v0.2 additions (this wave — code + tests)
1. `liquidity_stability` = 1 − CV(L, last 12 obs) (needs ≥12 pts) — anti-spike depth quality
2. `txn_acceleration` = last 5m txns / mean(prev 12×5m) — mirrors volume_acceleration on counts
3. `top_holder_concentration` = Σ top-10 share from holder_snapshot (RPC)
4. `top20_net_flow_1h` = signed % change of top-20 sum vs snapshot ≥1h earlier (whale proxy seed)
5. `mcap_change_1h` = mc_t/mc_{t−1h}−1 (provider-supplied mc series)

## Hard rules for every expansion
Registry ⇄ computed-set equality (D-doc law) · leakage tests per new feature · missing→absent (never 0-fill) ·
feasibility must be probe-verified before CLAIMING a feature (holder_count = the warning case).
