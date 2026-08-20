# AHOS CANONICAL — PROVIDERS (PAL matrix, live ground truth)
Detail: discovery/providers.yaml (binding registry) · docs/mission_v1_1/G (matrix) · probe evidence (wave-5).

## Reachability (LIVE VERIFIED from sandbox 2026-08-11; IRAN = UNKNOWN until user-side probe)
OK: DexScreener (profiles/boosts/tokens-v1) · GeckoTerminal (networks/new_pools/pool-detail) · RugCheck ·
DefiLlama · Solana RPC (mainnet-beta, publicnode) · EVM publicnode (ETH/BSC/Base) · GitHub API ·
CoinTelegraph RSS · TheBlock RSS.
FAILED/DEGRADED: GoPlus (timeout×3) · LlamaRPC (521) · Ankr (key now required) · Cloudflare-ETH (-32046) ·
CryptoPanic (404 — endpoint changed) · CoinDesk RSS (308 chain, usable).

## Architecture-side adapters (Month 2 — additive to the PAL matrix)
`architecture/providers/` implements the unified provider layer over the PAL matrix:
DexScreener, GeckoTerminal, GoPlus, RugCheck (keyless) · CoinGecko (keyless) ·
ChainExplorer/Blockscout (keyless, 4 EVM chains) · **CoinMarketCap** (keyed free
tier — inert NO_KEY until `COINMARKETCAP_API_KEY`, fills market cap/FDV/volume
only, last in the `ProviderCollector` merge) · **pump.fun** (keyless Solana
launchpad discovery feed, discovery-only) · DEXTools (inert until
`DEXTOOLS_API_KEY`). Every adapter emits normalized envelopes with the full
NO_KEY/AUTH_REQUIRED/RATE_LIMIT/DOWN/ERROR/UNSUPPORTED vocabulary (M-GAP-016)
and never fabricates fields. Live reachability of CMC/pump.fun is still
fixture-verified only (M-GAP-007 pending host egress).

## Social Intelligence sources (W41 — `architecture/intel/social.py`)
Not market-data providers. Social is evidence, never a buy signal. Live claim is NONE for every row.

| Source | Status | Notes |
|---|---|---|
| RSS/news | IMPLEMENTED | wraps `architecture/intel/news.py`; unreachable → UNKNOWN |
| GitHub public API | IMPLEMENTED | official API only; no transport ⇒ no live claim |
| Reddit | AUTH_REQUIRED | no unauthenticated JSON; no scraping |
| X/Twitter | COST_BLOCKED | paid API; $0 ceiling |
| Telegram channels | OUT_OF_POLICY | ToS-gray user-session harvest; Telegram remains UX (`telegram_ai`) |
| Instagram / TikTok / public web crawl | OUT_OF_POLICY | no official free research API |
| YouTube Data API | AUTH_REQUIRED | key-gated; no scraping |

DEXTools remains in `architecture/providers/adapters.py` (inert until `DEXTOOLS_API_KEY`).

## Rules
Free-first ordered chains per capability; paid tier never a hard dependency; envelope contract
(provider/endpoint/chain/capability/freshness/ratelimit/availability/confidence/dual-ts/error_state);
token-bucket budgets (conservative vs documented); breaker with cooldown; TTL cache; raw payload archived
before parse; every probe/failure recorded (no silent DOWN). User-side probe script: engine/pal_probe.py
(same method; IRAN columns filled only from real Iran runs).
**Rate/breaker sync law (Month 2):** architecture adapters/breakers must never be
more aggressive than the frozen PAL contract for the same provider — enforced by
`tests/test_provider_yaml_sync.py`.
