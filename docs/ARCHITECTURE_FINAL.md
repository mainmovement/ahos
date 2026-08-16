# AHOS — FINAL ARCHITECTURE (v1.1) — 2026-08-10
# Consolidates: TRADING_INTELLIGENCE_PLAN, PHASE_0_REDTEAM, Phase-1 verification reports,
# Phase-2/3 frameworks. Phase-1 foundation is preserved; changes are additive or documented
# corrections (see ISSUES_REGISTER). No rewrite of the frozen core.

## 1. System overview
Poco F3 (Termux) = controller + Telegram client + backup. VPS (docker-compose) = engine:
[Postgres] + [n8n]. Python engine module holds strategy/risk/validation logic (also embeddable
in n8n Code nodes). Exchange access is CCXT-config-swappable (lbank|bybit). Capital: $10–15,
micro mode (leverage hard 2x). Mode default: PAPER; LIVE requires every gate open + human.

Data flow:
exchange OHLCV → W1 ingest+integrity (hourly) → market_data (dedupe UPSERT)
→ W2 kill-check → strategy eval (frozen v1.0) → risk gate → PAPER record + Telegram
(LIVE only after gates → human /approve → execution node (currently DISABLED))
→ trade_decisions / agent_audit_trail / telegram_audit (full audit chain)

## 2. Unified phase map (canonical)
| Canonical | Old labels | Content | Status |
|---|---|---|---|
| P0 Setup | Plan-Phase 0 | architecture, scorecard, env templates | DONE |
| P1 Foundation | Plan-Phase 1 / AHOS Phase 1 | schema, ingest, integrity, artifacts | DONE (artifacts rebuilt) |
| P2 Validation | Plan-Phase 2/3 | backtest + OOS + WF + MC on real data | PARTIAL → **REBUILD REQUIRED** (baseline failed gates on 83d; 3yr data absent) |
| P3 Paper+Control | Plan-Phase 4 | n8n live paper loop + Telegram bot + DB | ENGINE READY — activate after env setup (token/chat-id) |
| P4 Evolution | AHOS Phase 3–5 / Plan-Phase 5–7 | learning memory, NL interface, scale — all human-gated | DESIGNED, OFF, activates only after P2/P3 pass |

## 3. Data governance
- Real data only; canonical sets: BTC 1997 (clean, gaps registered), ETH/SOL 2000.
- Versioning: dataset_version + sha256 checksums (SCHEMA.md v1.0 preserved).
- Removed-row registry in engine/run_validation.py; no interpolation ever.
- 48-symbol universe corrected to 45 verified candidates (ISSUES_REGISTER D2); live artery = BTC/ETH/SOL.

## 4. Strategy & risk (frozen values)
- Signal: EMA20 trend + volume >1.2×SMA20 + ATR14 bracket 1.5/2.0 + 72h time stop, both-sided,
  entry next-open, same-candle SL priority. Costs: 0.055% fee + 0.02% slippage per side.
- Risk: 2% equity/trade, 2x leverage (micro), 3 max positions, 10% daily-loss halt 24h,
  20% DD full stop, min-notional guard pending exchange verification.
- CURRENT STATUS: fails edge gates on real data (PF<1). Redesign mandate: new hypothesis →
  full P2 battery on 3-year data. No tuning on the current OOS window (untouched law).

## 5. Security architecture
- Secrets only in .env (+n8n credential store), never in repo/JSON/logs/telegram.
- Exchange key: trade-only, withdrawal disabled, IP whitelist where supported.
- Kill switch: 3 enforcement points (bot flag file/SQLite, agent_audit_trail row, n8n kill-check node).
- Telegram: admin chat-id gate before any mutating command; attempts audited.
- n8n: basic-auth + encryption key + loopback-only port (reverse proxy in front).

## 6. Recovery & operations
- Postgres volume persists; n8n volume persists; restart=unless-stopped.
- On restart: pipeline re-reads market_data; decisions reconcile via execution_status.
- Backups: pg_dump nightly (cron in runbook) + CSV snapshots retained.
- CI gate before any delivery: engine/run_all_checks.sh (4 checks must be green).

## 7. What is NOT in this architecture (honest exclusions)
- No auto-learning online; no whale/on-chain feeds (data source unverified); no $1M claims;
  no live execution wiring (node shipped disabled); no web UI (Telegram is the interface).
