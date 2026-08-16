# IRAN NETWORK RESILIENCE MATRIX (Deliverable E) — 2026-08-11
# Directive §14: filtering/blocking/geo-restriction is a FIRST-CLASS design input.
# Every row: PRIMARY → FALLBACK(+2) → DEGRADED MODE. Sandbox column = LIVE probe evidence
# (reports/pal_probe_20260811_184349_sandbox.json). Iran column = UNKNOWN until user-side probe.

## Data plane (discovery PAL)
| Capability | PRIMARY → fallbacks | Sandbox 2026-08-11 (probe ids) | Degraded mode |
|---|---|---|---|
| discovery_stream | geckoterminal → dexscreener profiles/boosts | OK (PRB-…-001) | none needed yet; cache TTL |
| pair_enrich | dexscreener → geckoterminal | OK (002) | stale-cache + UNKNOWN fields |
| security_sol | rugcheck | OK (003, 421ms) | PASS_WITH_UNKNOWN coverage-capped |
| security_evm | goplus → on-chain heuristics (Phase-3) | **OK again (004, 361ms — upgraded)** | coverage-capped verdicts |
| rpc_sol | mainnet-beta → publicnode | OK ×2 (007, 008) | holder ops still REFUTED (429/403; R-15) |
| rpc_eth/bsc/base | publicnode per chain | OK ×3 (009–011) | LlamaRPC 521 (012), Cloudflare -32046 (013), Ankr key-required (014) — removed/deprioritized |
| narrative_rss | cointelegraph → theblock → **coindesk (NEW, 017 OK)** | OK (005, 006, 017) | narrative features absent anyway (Phase-7) |
| social API | cryptopanic free posts | **DOWN 404 ×2 (016)** — endpoint changed, re-verify pre-Phase-7 | social MVP deferred, fenced in H17/H19 |
| holder RPCs (strategic) | helius "public" 401 (015) — Helius/QuickNode free tiers = user signup | REFUTED free-public | UNKNOWN fields, no fabrication |

## AI plane (AI-PAL)
local ollama (LOCAL_IMMUNE, needs host) → GITHUB_TOKEN models → groq → gemini (likely-filtered in IR;
documented, not assumed) → openrouter-free → **DETERMINISTIC_ONLY (test-pinned, always available)**.

## Control plane
- Telegram Bot API: reachable status from Iran historically volatile (has worked via official
  clients; API endpoints sometimes throttled). Mitigation: n8n/bot on VPS (②) outside IR + user
  interacts via normal Telegram clients. UNKNOWN until ①+② done — honest.
- Payments: $0/month architecture means NO international payment dependency anywhere in the system.

## User-side probe protocol (needs nothing but Python)
```
python3 engine/pal_probe.py --site user-iran     # data plane, no keys required
# then send reports/pal_probe_*.json back — Iran column gets probe ids, UNKNOWNs resolve to facts
```
