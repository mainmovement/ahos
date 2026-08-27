# CURRENT_TRUTH_SNAPSHOT

**Captured:** 2026-08-27 (agent host)  
**Phase:** RELEASE / TRANSFER CONTROL — merge audit; Windows run NOT simulated  
**Law:** Code + executable artifacts > documentation claims.

## Git / PR

| Field | Value |
|-------|--------|
| Branch | `cursor/ahos-cleanup-alignment-4bde` |
| HEAD | `e73a92e` |
| PR | https://github.com/mainmovement/ahos/pull/19 — OPEN |
| Base | `main` |
| Lane-A freeze | OK (36 files pinned; no frozen sources changed vs main) |
| Merge audit | `docs/MERGE_READINESS_AUDIT.md` |

## Classification (honest)

| Level | Status |
|-------|--------|
| DEVELOPMENT_READY | proven earlier |
| INTEGRATION_READY | **YES — agent-host only** |
| OPERATOR_READY | **NOT_VERIFIED** — no Windows gate JSON |
| PRODUCTION_CANDIDATE / PRODUCTION_READY | **FALSE** |
| MERGE_READY (transfer) | see `docs/MERGE_READINESS_AUDIT.md` after gates |

## Evidence census (agent host DBs)

| Metric | Value |
|--------|------:|
| local predictions | 352 |
| observation_state OBSERVING | 113 |
| discovery_observations | ≥368 |
| production_observations | 354 |
| outcome_labels | **0** |
| calibration eligible pairs | **0** |
| calibration_status | `CALIBRATION_READY_BUT_DATA_REQUIRED` |

## What is proven vs not

| Claim | State |
|-------|--------|
| Agent-host provider SUCCESS | AGENT_HOST LIVE_VERIFIED (prior JSON) |
| Windows operator gates | NOT_VERIFIED |
| Telegram live E2E | OWNER_ACTION_REQUIRED |
| n8n OPERATIONAL | NOT_VERIFIED (structural only) |
| Pre-soak / 72h / 168h soak | NOT_VERIFIED |
| Lane-A Windows RO URI gap | BLOCKED pending freeze re-anchor |
| AG-25 / speculative features | NOT_IMPLEMENTED / DEFERRED |

## This phase scope (binding)

Freeze PR for safe Windows transfer. Do **not** invent Windows PASS. Do **not** promote OPERATOR_READY.
