# AHOS — DATA SOURCE MATRIX v1.0 (free-first, Iran-resilient, provider-independent)
# Verified facts marked V; assumptions marked A(SSUME) → must be probed at integration time.
# Every source passes through Provider Abstraction Layer (PAL) with fallback chain + cache + backoff.

| Source | Purpose | Cost | Key? | Rate budget (V=Documented/A=Assume) | Iran net risk | Fallback | Quality note |
|---|---|---|---|---|---|---|---|
| DexScreener API (api.dexscreener.com) | new pairs, liquidity, vol, txns, boosts | FREE | None (V) | ~300 req/min (A) | LOW-MED (A) | GeckoTerminal | Aggregated DEX state; strong coverage Solana/EVM |
| GeckoTerminal (CoinGecko) | new pools per network, OHLCV pools | FREE | None (V) | ~30 req/min (A) | MED (A) | DexScreener | Slower but independent pipeline |
| GoPlus Security API | honeypot, tax, owner, blacklist, proxy | FREE | None (V) | daily-qty limits (A) | MED (A) | RugCheck (SOL) / Honeypot.is | Industry-standard risk flags |
| RugCheck.xyz | Solana token risk, LP lock, authorities | FREE | None (A) | modest (A) | MED | GoPlus | Solana-first depth |
| Honeypot.is | EVM honeypot sim | FREE unofficial (A) | None | strict (A) | MED | GoPlus | Secondary opinion only |
| BinanceVision CDN | majors 1h klines/funding/OI/metrics | FREE | None (V) | file-based (V) | LOW (V) — proven from sandbox | LBank CCXT (V) | primary historical research source; in use |
| Binance public API | live majors data | FREE | None for market (V) | weight-based (V) | HIGH (V — 451 from IR) | LBank API (V) | via VPS only |
| LBank API | live + research OHLCV | FREE | public ok (V) | ~1000 candles/req (V) | LOW (V) | Binance via VPS | current live-venue candidate |
| Public RPC — Solana (ankr public / official) | holders, deployer tx, program data | FREE | None/optional (A) | strict public caps (A) | MED | Helius/QuickNode free tiers (signup-risk for IR) | holder snapshots feasible per-token |
| Public RPC — EVM (llamarpc/ankr/cloudflare-eth) | same for ETH/BSC | FREE | None (V) | strict (A) | MED | full-node on VPS later | blockscout/explorer APIs as fallback |
| DefiLlama | chain TVL/liquidity context | FREE | None (V) | generous (V) | LOW-MED (A) | — | context only, not signal |
| CryptoPanic (free tier) | news velocity | FREE w/ key (V) | signup key | ~1000/day (A) | LOW-MED | RSS news feeds | good-enough news velocity |
| RSS feeds (CoinTelegraph, CoinDesk, TheBlock…) | narrative/news MVP | FREE | None (V) | poll 15–30min (A) | MED (some filtered → VPS) | CryptoPanic | MVP narrative signal |
| GitHub API | dev activity per project repos | FREE | optional token (V) | 60/h anon, 5000/h token (V) | LOW (V) | — | solid dev-activity proxy |
| Reddit JSON | community momentum | FREE w/ OAuth (V) | app key | 100 req/min (V) | MED | RSS of subreddits | secondary |
| X/Twitter API | social momentum | **PAID ($200/mo basic) — COST-BLOCKED (V)** | key | — | — | RSS bridges/nitter (unreliable, A) | **excluded until revenue; documented** |
| Telegram public channels (Telethon) | project-channel velocity | FREE w/ user account (A) | api_id/hash | per-account (A) | MED (MTProto proxy needed, IR) | channel RSS mirrors | ToS gray zone — advisory data only |
| Santiment/Glassnode/Arkham/Nansen | smart-money/whale labels | PAID — COST-BLOCKED (V) | — | — | — | self-built whale heuristics (M6) | excluded at current budget |

## Provider Abstraction Layer contract (PAL v1)
providers.yaml: per-purpose ordered chain [{name, base_url, key_env, rate, timeout, breaker}] —
every call returns (data, provenance{provider, fetched_at, latency, status}); UNKNOWN stays UNKNOWN;
no fabrication. Voyeur rule: PAL never silently substitutes fields across providers (schema-normalized).

## Acquisition policy for early tokens (E-01 collection)
Discovery poll every 5 min (new pairs, Solana+Base+BSC+ETH); snapshot at detection: liquidity/volume/
price/age/security flags/holders(if available within 5-min budget); re-snapshot at +15m/+1h/+4h/+12h/
+24h/+72h/+7d → outcome labels computed from price series (% move, max drawdown within horizon).
Estimated request budget: ~50 new pairs/day × ~10 snapshots ≈ 1,200 calls/day — well within free tiers.
