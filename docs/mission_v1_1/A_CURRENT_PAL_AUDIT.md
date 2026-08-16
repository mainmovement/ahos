# A. CURRENT PAL AUDIT — Mission v1.1, STEP 1 — 2026-08-11
# Status taxonomy: EXISTS · PARTIAL · MISSING · MOCK · LIVE VERIFIED (per directive §21)
# Auditor: council roles 1 (Architect), 8 (Data Eng), 12 (n8n), 14 (Security adversarial)

## A.1 Verdict
| Aspect | State | Evidence |
|---|---|---|
| PAL design (contract, fallback chain, provenance rule) | **EXISTS (design only)** | docs/DATA_SOURCE_MATRIX.md §"PAL v1"; docs/TARGET_ARCHITECTURE_vNext.md invariant 1 |
| PAL code (registry loader, client, breaker, cache) | **MISSING** | `grep -l pal/provider engine/ strategy_lab/` → 0 files (verified 2026-08-11) |
| providers.yaml registry | **MISSING** | no such file in tree (verified by find) |
| Provenance discipline in stored rows | **PARTIAL** | market_data has `source` col (schema v1.1); discovery rows have no persistence yet |
| Rate-limit enforcement | **MISSING** | none implemented anywhere |
| Circuit breaker / graceful degradation | **PARTIAL(design)/MISSING(code)** | dryrun S2 proves alert-path design only for legacy ingest |
| Provider reachability ground truth | **LIVE VERIFIED this wave (sandbox)** | probe table A.2 |

## A.2 LIVE VERIFIED provider probes (sandbox, 2026-08-11 17:3x UTC; Iran-network state = UNKNOWN, separate)
| Provider | Endpoint probed | Result | Latency |
|---|---|---|---|
| DexScreener | /token-profiles/latest/v1 | LIVE VERIFIED 200 (valid JSON payload) | 77ms |
| DexScreener | /token-boosts/latest/v1 | LIVE VERIFIED 200 | 75ms |
| DexScreener | /tokens/v1/solana/{addr} | LIVE VERIFIED 200 (pair detail) | 89ms |
| GeckoTerminal | /api/v2/networks | LIVE VERIFIED 200 | 63ms |
| GeckoTerminal | /api/v2/networks/{solana,eth}/new_pools | LIVE VERIFIED 200 ×2 | 92–106ms |
| GeckoTerminal | pool detail ?include=base_token | LIVE VERIFIED 200 | 494ms |
| RugCheck | /v1/tokens/{mint}/report/summary | LIVE VERIFIED 200 | 436ms |
| DefiLlama | api.llama.fi/protocols | LIVE VERIFIED 200 (8.5MB) | 174ms |
| Solana RPC | getSlot (mainnet-beta + publicnode) | LIVE VERIFIED 200 ×2 | 142–165ms |
| EVM RPC (publicnode) | eth_blockNumber on ETH/BSC/Base | LIVE VERIFIED 200 ×3 | 137–148ms |
| GitHub API | /rate_limit | LIVE VERIFIED 200 (60/h anon) | 53ms |
| CoinTelegraph RSS | /rss | LIVE VERIFIED 200 (valid XML) | 74ms |
| TheBlock RSS | /rss.xml | LIVE VERIFIED 200 | 84ms |

## A.3 FAILED / DEGRADED from sandbox (recorded, not hidden)
| Provider | Result | Disposition |
|---|---|---|
| GoPlus (SOL + EVM token_security) | timeout ×3 (12–15s), http=000 | **UNAVAILABLE from sandbox**; keep as adapter with PAL fallback to RugCheck(SOL)/on-chain heuristics; Iran-state UNKNOWN |
| LlamaRPC eth | HTTP 521 | dropped from chain until re-probe passes |
| Ankr public EVM | 200 but JSON-RPC error "must authenticate" | no longer free-anonymous → reclassify PAID-KEY tier |
| Cloudflare ETH | JSON-RPC -32046 | degraded; publicnode is primary EVM |
| CryptoPanic free + developer endpoints | 404 ×2 | endpoint retired/changed → verify before Phase-7 narrative build; RSS is primary |
| CoinDesk RSS | 308 redirect chain | parseable with follow-redirect; secondary |

## A.4 Audit conclusions (binding for implementation)
1. PAL must be built now as REAL code (STEP 3 prerequisite), not deferred into n8n nodes.
2. Fallback semantics: per-capability ordered chains (discovery: GT primary? NO — both free & verified;
   order by measured latency+rate budget: DexScreener lexical-coverage + GT new_pools as independent second
   source; security: RugCheck(SOL) primary + GoPlus-pending + on-chain fallback heuristics).
3. Every adapter returns normalized envelope (see C §3) — no provider schema leaks into core (Mission §4).
4. Iran-resilience: sandbox probes ≠ Iran probes. All IRAN columns stay UNKNOWN until user-side probe runs
   (script ships: `engine/pal_probe.py`, same method, user-runnable).
