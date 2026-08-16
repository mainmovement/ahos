# AHOS CANONICAL — PROVIDERS (PAL matrix, live ground truth)
Detail: discovery/providers.yaml (binding registry) · docs/mission_v1_1/G (matrix) · probe evidence (wave-5).

## Reachability (LIVE VERIFIED from sandbox 2026-08-11; IRAN = UNKNOWN until user-side probe)
OK: DexScreener (profiles/boosts/tokens-v1) · GeckoTerminal (networks/new_pools/pool-detail) · RugCheck ·
DefiLlama · Solana RPC (mainnet-beta, publicnode) · EVM publicnode (ETH/BSC/Base) · GitHub API ·
CoinTelegraph RSS · TheBlock RSS.
FAILED/DEGRADED: GoPlus (timeout×3) · LlamaRPC (521) · Ankr (key now required) · Cloudflare-ETH (-32046) ·
CryptoPanic (404 — endpoint changed) · CoinDesk RSS (308 chain, usable).

## Rules
Free-first ordered chains per capability; paid tier never a hard dependency; envelope contract
(provider/endpoint/chain/capability/freshness/ratelimit/availability/confidence/dual-ts/error_state);
token-bucket budgets (conservative vs documented); breaker with cooldown; TTL cache; raw payload archived
before parse; every probe/failure recorded (no silent DOWN). User-side probe script: engine/pal_probe.py
(same method; IRAN columns filled only from real Iran runs).
