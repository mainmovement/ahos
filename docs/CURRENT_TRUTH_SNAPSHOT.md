# CURRENT_TRUTH_SNAPSHOT

**Captured:** 2026-08-27 (agent host)  
**Phase:** OPERATOR VALIDATION — Windows-blocking defects fixed; Windows run NOT simulated  
**Law:** Code + executable artifacts > documentation claims.

## Git / PR

| Field | Value |
|-------|--------|
| Branch | `cursor/ahos-cleanup-alignment-4bde` |
| HEAD | (see `git rev-parse HEAD` after push) |
| PR | https://github.com/mainmovement/ahos/pull/19 — OPEN, MERGEABLE, not draft |
| Base | `main` |
| Lane-A freeze | OK (36 files pinned) |

## Classification (honest)

| Level | Status |
|-------|--------|
| DEVELOPMENT_READY | proven earlier |
| INTEGRATION_READY | **YES — agent-host only** |
| OPERATOR_READY | **NOT_VERIFIED** — no Windows gate JSON yet |
| PRODUCTION_CANDIDATE / PRODUCTION_READY | **FALSE** |

## Evidence census (agent host DBs)

| Metric | Value |
|--------|------:|
| local predictions | 352 |
| observation_state OBSERVING | 113 |
| discovery_observations | 379 |
| production_observations | 354 |
| outcome_labels | **0** |
| calibration eligible pairs | **0** |
| calibration_status | `INSUFFICIENT_DATA` / `CALIBRATION_READY_BUT_DATA_REQUIRED` |

## What is proven vs not

| Claim | State |
|-------|--------|
| Agent-host provider SUCCESS | AGENT_HOST_VERIFIED (prior) |
| Windows-safe SQLite RO URI (Lane B/scripts) | TEST_VERIFIED |
| Operator gate Windows defects fixed | TEST_VERIFIED (npm.cmd, HTTPError, handoff commands) |
| Operator Windows probe | **NOT_VERIFIED** / OWNER_ACTION |
| Telegram live E2E | OWNER_ACTION_REQUIRED |
| n8n OPERATIONAL_VALID | OWNER_ACTION_REQUIRED |
| Pre-soak / 72h / 168h soak | NOT_VERIFIED |
| Lane-A RO URI on Windows (`observe_active`, `paper_trading/ledger`) | **REMAINING GAP** (frozen; not patched) |

## This phase scope (binding)

Fix real Windows operator-blocking defects; keep readiness honest.  
Do **not** promote to OPERATOR_READY without Windows artifacts.  
Do **not** fabricate calibration pairs or simulate Windows PASS.
