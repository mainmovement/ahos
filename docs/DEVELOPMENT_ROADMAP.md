# AHOS — DEVELOPMENT ROADMAP (Mission vNext) — 2026-08-11
# Exit criteria per phase are measurable. Lab law and maturity letters apply throughout.

## PHASE 1 — Architecture stabilization (DONE)
Exit met: frozen base + schema v1.1 + audit trail + CI 6-stage green.

## PHASE 2 — Multi-source token discovery (CURRENT)
Build: PAL (providers.yaml) · discovery collectors (DexScreener+GT) · schema v1.2 migration
Exit: 72h continuous discovery log with provenance + dedupe proof + integrity PASS on stored raw payloads.

## PHASE 3 — On-chain + security intelligence
Build: GoPlus/RugCheck adapters · veto registry · holder/concentration snapshots (RPC budgeted)
Exit: every discovered token gets security verdict row; UNKNOWN discipline proven by tests;
veto fixtures (known scam patterns) pass: 100% veto rate on synthetic-fixture list (documented as fixtures).

## PHASE 4 — Opportunity scoring + scientific validation
Build: E-01 collector (≥8 weeks in background) · score engine v0.1 (rank-first) · outcome labeler
Exit: outcome dataset ≥ ~1,500 events (order-of-magnitude target, reported exactly); ranking-quality
study train-only; NO numeric probabilities before calibration pass.

## PHASE 5 — n8n automation
Build: workflows 20 (discovery) / 21 (scoring+security) / 22 (monitoring) with error+kill+audit paths
Exit: structural validation + live import smoke-check (needs VPS — user blocker).

## PHASE 6 — Telegram Persian interface
Build: engine/ux_fa.py templates · NLP intake with confirmation · 6 message classes
Exit: harness Tests A–J REAL (needs token rotation — user blocker) + Persian payload fixtures green.

## PHASE 7 — Paper-position monitoring
Build: positions lifecycle, P/L tracking, alert levels; STRICTLY paper bookkeeping
Exit: 2-week paper run vs recorded alerts; variance documented. (No live trading — separately gated.)

## PHASE 8 — Evolution / continuous research
Build: learning loops over E-01 datasets; score-version rollbacks; quarterly regime review
Exit: every change versioned+batteried; adverse-drift kill conditions defined a priori.

## Paralleled user blockers (open today)
1. Token rotation + admin chat id (unlocks REAL telegram tests)
2. VPS (unlocks n8n live smoke + Iran-resilient provider access + 24/7 discovery)
