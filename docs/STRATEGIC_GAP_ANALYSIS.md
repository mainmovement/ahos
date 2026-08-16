# AHOS — STRATEGIC GAP ANALYSIS (Step §23 of Mission Correction v1.0) — 2026-08-11
# CURRENT SYSTEM vs INTENDED SYSTEM. Basis: all existing docs read; H1–H13 evidence reviewed.

## CURRENT SYSTEM (what exists — maturity letters enforced)
| Block | Exists? | Maturity | Notes |
|---|---|---|---|
| Causal backtest engine + risk caps | ✔ | D | ahos_backtest.py; DD-stop enforced & proven |
| Data acquisition + governance (checksum/dedupe/gap/OHLC) | ✔ | D | engine/acquire_3yr.py; BinanceVision; 3.6y×3 + 6.6y BTC |
| Strategy research lab (hypothesis cards, registry, gates) | ✔ | D | 13 cards, 0 accepted — honest outcome |
| Statistical battery (OOS/WF/MC/stress) | ✔ | D | seeded, reproducible, multiplicity guards |
| PostgreSQL schema (8 tables) | ✔ | C (B pending live boot) | market-scoped, no token/discovery tables yet |
| n8n workflows (6) | ✔ | C | control + research; import smoke-check pending VPS |
| Telegram control plane (auth/kill/gate) | ✔ | C (simulated) | REAL send pending token rotation (user) |
| Telegram PERSIAN UX / NLP position entry | ✘ | A | designed in this wave |
| Early-token DISCOVERY engine | ✘ | — | does not exist |
| Security-veto engine (honeypot/contract) | ✘ | — | does not exist |
| Whale/wallet intelligence | ✘ | — | does not exist |
| Social/narrative engine (free-tier reality) | ✘ | — | design constrained by cost |
| Opportunity scoring engine | ✘ | A | v0.1 design in this wave; weights UNVALIDATED by law |
| Position monitoring (paper) | partial | B | DB tables ready-ish; no ingestion of user positions |
| Evolution layer | ✘ | A | gated behind evidence by design |

## INTENDED SYSTEM (target vNext; see TARGET_ARCHITECTURE_vNext.md)
Data Sources → Discovery → Normalization → **Security (VETO)** → On-chain → Whale →
Social/Narrative → Microstructure → Tokenomics → Catalyst → **Opportunity Score** → Risk →
Research/Backtest → Decision → Persian Telegram → User  ┃  Position→Monitoring→Alerts (parallel loop)

## GAPS (ranked by mission criticality)
1. **Discovery sources integration** — DexScreener/GeckoTerminal free APIs (no key) — build first.
2. **Security veto layer** — GoPlus/RugCheck free APIs; hard-veto logic; UNKNOWN-field discipline.
3. **Event-outcome capture (E-01 paper study)** — the missing dataset for ANY score validation.
4. **Persistence for tokens/events/scores** — schema extension v1.2 (additive, no Phase-1 break).
5. **Persian NLP position intake** — parser + confirmation flow.
6. **Whale intelligence** — public RPC + holder snapshots (cost/feasibility constraints documented).
7. **Narrative engine** — free sources only; X active-search API is cost-blocked (recorded).

## WHAT IS EXPERIMENTALLY VALIDATED (vs theoretical)
Validated: data governance, causal backtesting, risk caps, gate discipline, telegram protocol logic (sim).
Theoretical-only: every new product layer above. Opportunity weights are FORBIDDEN until E-01 outcome data exists.

## KEY RISKS (new mission)
- Early tokens = manipulated markets: wash volume, fake holders → security/manipulation features are
  first-class; "attention ≠ organic demand" is an enforced rule.
- Free API rate limits (300/min DexScreener, 30/min GT) → provider abstraction + cache + backoff.
- Iran network variance → all calls through provider layer with fallback chain; VPS for engine.
