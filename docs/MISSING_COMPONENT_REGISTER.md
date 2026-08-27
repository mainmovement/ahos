# AHOS — MISSING COMPONENT REGISTER (post-gap-analysis) — 2026-08-11
#
> **HISTORICAL (2026-08-27).** Status letters below are a 2026-08-11 design snapshot.  
> Many rows (M1–M5, M8–M12) are now implemented in code — see  
> `docs/CANONICAL_IMPLEMENTATION_MATRIX.md` and `AHOS_GAP_REGISTER.md`.  
> Do not treat “A Designed” rows as current missing-work truth.

# Status letters: A Designed · B Implemented · C Tested · D Verified · E Production Ready
| # | Component | Status | Blocked by | Priority |
|---|---|---|---|---|
| M1 | Provider abstraction layer (registry, fallback chain, rate budget, circuit breaker) | A→B this wave (spec) | — | P0 |
| M2 | Discovery engine (DexScreener + GeckoTerminal collectors, dedupe, provenance) | A | M1 | P0 |
| M3 | Token persistence schema v1.2 (tokens/discoveries/features/security_checks/scores/positions/alerts) | A | — | P0 |
| M4 | Security veto engine (GoPlus + RugCheck adapters; UNKNOWN discipline; hard-veto list) | A | M3 | P0 |
| M5 | Event-outcome collector E-01 (paper labels at 7 horizons) | A | M2,M3 | P0 |
| M6 | Whale/wallet intelligence (holder snapshots via public RPC + RPC adapter with Iran fallback) | A | M1 | P1 |
| M7 | Narrative engine MVP (RSS + CryptoPanic free + TG public channels metadata; X cost-blocked documented) | A | M1 | P1 |
| M8 | Opportunity score engine v0.1 (deterministic, explainable; weights locked until E-01 evidence) | A | M5 | P1 |
| M9 | Persian NLP position intake ("من X تومان خریدم" → confirmation → position row) | A | M3 | P1 |
| M10 | Position monitoring loop (watch → alert levels 🟢🟡🟠🔴) | A | M8,M9 | P2 |
| M11 | n8n workflows 20/21/22 (discovery/scoring/monitoring) | A | M2,M8 | P2 |
| M12 | AI abstraction layer (free-tier providers + local fallback; advisory only) | A | — | P3 |
| M13 | REAL telegram/n8n live verification | C-design | **user: token rotation + VPS** | P0-blocker |
| M14 | Live execution | — | gated: ≥1 validated mechanism + human auth | BLOCKED by law |

## Hard blockers requiring user action (unchanged, still #1/#2 of ops queue)
1. Revoke+recreate Telegram bot token; set TELEGRAM_BOT_TOKEN + TELEGRAM_ADMIN_CHAT_ID.
2. VPS provisioning (engine host; also solves Iran-network reachability for providers).
