# G. PROVIDER MATRIX v1 — Mission v1.1 §5 — 2026-08-11
# Freshness of reachability: LIVE VERIFIED from sandbox 2026-08-11 (probes in A.2/A.3).
# Iran-network column: UNKNOWN until user-side probe (engine/pal_probe.py ships so user can run it).
# Cost ceiling: $0/month — Tier-4 (paid) never a hard dependency.

Legend: ✅ LIVE VERIFIED (sandbox) · ⚠️ degraded/changed · ❌ failed probe · 🚫 cost-blocked · ❔ unprobed

## Capability: DISCOVERY (new tokens/pairs)
| Tier | Provider | Endpoint(s) | Sandbox | Iran | Rate budget | Fallback |
|---|---|---|---|---|---|---|
| 1 Free | GeckoTerminal | /api/v2/networks/{chain}/new_pools | ✅ 92–106ms | ❔ | ~30 rpm (doc; conservative 25) | Tier-2 |
| 1 Free | DexScreener | /token-profiles/latest/v1 · /token-boosts/latest/v1 | ✅ 75–77ms | ❔ | ~300 rpm (doc; conservative 120) | Tier-2 |
| 2 Free | DexScreener | /tokens/v1/{chain}/{addr} (pair detail/enrich) | ✅ 89ms | ❔ | as above | GT pool detail ✅ |
| 2 Free | GeckoTerminal | /networks/{chain}/pools/{addr}?include=base_token | ✅ 494ms | ❔ | ~30 rpm | DEX tokens/v1 |
| 3 Self-host | full-node/indexer on VPS | — | not built | ❔ | — | — |
| 4 Paid | DEXTools/CMC APIs | — | 🚫 excluded ($) | — | — | never required |

## Capability: SECURITY
| Tier | Provider | Sandbox | Notes |
|---|---|---|---|
| 1 Free | RugCheck /v1/tokens/{mint}/report (SOL) | ✅ 436ms | primary for SOL |
| 1 Free | GoPlus /api/v1/*token_security* | ❌ timeout ×3 | adapter present, DEGRADED; EVM needed for eth/bsc/base |
| 2 Free | Honeypot.is (EVM, unofficial) | ❔ | second-opinion only |
| 3 Self | on-chain RT checks via RPC (mint/freeze authority direct) | ✅ RPC verified | fallback heuristics, limited scope |
| 4 Paid | Chainalysis/TRM etc. | 🚫 | never |

## Capability: ON-CHAIN / HOLDERS (Phase-3 scope, RPC verified now)
| Tier | Provider | Result |
|---|---|---|
| 1 Free | Solana mainnet-beta + solana-rpc.publicnode | ✅ getSlot 142–165ms |
| 1 Free | publicnode EVM ETH/BSC/Base | ✅ eth_blockNumber 137–148ms |
| 2 Free | llamarpc | ❌ 521 (dropped until re-probe) |
| 2 Free | cloudflare-eth | ⚠️ -32046 | 
| 2 Free | ankr public | ⚠️ now requires API key → reclassify Tier-4-free-key |
| 4 Paid-key | Helius/QuickNode free tiers (signup) | ❔ (signup risk for IR users — documented) |

## Capability: NARRATIVE / CONTEXT (Phase-7 scope)
| Provider | Result | Disposition |
|---|---|---|
| CoinTelegraph RSS | ✅ 74ms valid XML | primary |
| TheBlock RSS | ✅ 84ms valid XML | primary |
| CoinDesk RSS | ⚠️ 308 chain | secondary (follow-redirect) |
| CryptoPanic free/dev | ❌ 404 ×2 | endpoint changed — re-verify before Phase-7 |
| GitHub API | ✅ 53ms (60/h anon; token raises to 5000/h) |
| DefiLlama | ✅ 174ms | context (chain TVL), not signal |
| X/Twitter | 🚫 $200/mo — cost-blocked (unchanged) | documented |

## Capability: MARKET-CAP / METADATA ENRICHMENT (Month-2 scope)
| Provider | Endpoint(s) | Verified | Notes |
|---|---|---|---|
| CoinGecko | /api/v3/coins/{platform}/contract/{address} | ✅ 2026-08-11 | keyless; market cap / FDV / volume; liquidity stays UNKNOWN |
| CoinMarketCap | pro-api /v2/cryptocurrency/info?address= + /quotes/latest?id= | ❔ fixture-verified only (M-GAP-011 adapter, 2026-08-20) | free tier needs key → inert NO_KEY until COINMARKETCAP_API_KEY (DEXTools pattern); market cap / FDV / volume / price-change / social links; discovery UNSUPPORTED; liquidity stays UNKNOWN |
| DEXTools | public-api.dextools.io (paid) | 🚫 cost-blocked | inert NO_KEY until DEXTOOLS_API_KEY; audit/score capability only |

## Rate/breaker sync law (Month 2 — ROADMAP_v3 §2)
`discovery/providers.yaml` is the frozen PAL contract (Lane-A). The architecture
adapters must never be more aggressive than it: request rate ≤ PAL's most
conservative rpm budget for the same provider_id; breaker opens no later
(`failure_threshold ≤`) and recovers no sooner (`recovery_timeout_sec ≥
cooldown_sec`). Enforced by `tests/test_provider_yaml_sync.py` (2026-08-20).

## PAL mechanics implemented (this wave, code)
- providers.yaml ordered chains per capability; envelope fields per Mission §4 exactly
  (provider_id/endpoint/chain/capability/data_type/freshness/rate_limit/availability/confidence/
  source_timestamp/retrieval_timestamp/error_state).
- Token-bucket rate limiter per provider + circuit breaker (open after N consecutive failures, half-open probe).
- Cache: GET memoization with TTL per capability (discovery 120s; security 600s) — protects free budgets.
- Every response → raw_payloads (sha256) before normalization; parse failures produce error_state, never silent.
