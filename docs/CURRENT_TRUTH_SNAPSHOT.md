# CURRENT_TRUTH_SNAPSHOT

**Captured:** 2026-08-27T20:27Z (agent host)  
**Phase:** OPERATOR VALIDATION & EVIDENCE ACCRUAL — pre-modify reconcile  
**Law:** Code + executable artifacts > documentation claims.

## Git / PR

| Field | Value |
|-------|--------|
| Branch | `cursor/ahos-cleanup-alignment-4bde` |
| HEAD | `207a169` |
| Working tree | clean |
| PR | https://github.com/mainmovement/ahos/pull/19 — OPEN, MERGEABLE, not draft |
| Base | `main` @ `dff5133` |
| Lane-A freeze | OK (36 files pinned) |

## Classification (honest)

| Level | Status |
|-------|--------|
| DEVELOPMENT_READY | proven earlier |
| INTEGRATION_READY | **YES — agent-host only** |
| OPERATOR_READY | **NOT_VERIFIED** — Windows operator gates not executed |
| PRODUCTION_CANDIDATE / PRODUCTION_READY | **FALSE** |

## Evidence census (agent host DBs)

| Metric | Value |
|--------|------:|
| local predictions | 352 |
| observation_state OBSERVING | 113 |
| discovery_observations | 368 |
| production_observations | 354 |
| outcome_labels | **0** |
| calibration eligible pairs | **0** (`no_matching_label` until T+72h resolve) |
| calibration_status | `INSUFFICIENT_DATA` |

## What is proven vs not

| Claim | State |
|-------|--------|
| Agent-host provider SUCCESS | AGENT_HOST_VERIFIED |
| Prediction→Lane-A bridge | IMPLEMENTED + TEST_VERIFIED + AGENT_HOST_VERIFIED |
| Narrative/intel feed-through | AGENT_HOST_VERIFIED |
| Pytest / typecheck / freeze / n8n JSON | TEST_VERIFIED / STRUCTURAL_VALID |
| Operator Windows probe | OWNER_ACTION_REQUIRED |
| Telegram live E2E | OWNER_ACTION_REQUIRED |
| n8n OPERATIONAL_VALID | OWNER_ACTION_REQUIRED |
| Pre-soak / 72h / 168h soak | NOT_VERIFIED |
| Calibration pairs | INSUFFICIENT_DATA |
| Numeric TS↔Python parity | NOT required / NOT claimed |
| Dev-activity / AG-25 | NOT_IMPLEMENTED (out of this phase scope) |

## Contradictions found

None material between code and canonical docs after R-81: docs correctly say INTEGRATION_READY (agent-host), calibration data required, operator actions open.

## This phase scope (binding)

Build operator validation gates + pre-soak protocol + runnable report generator.  
Do **not** add speculative features.  
Do **not** promote to OPERATOR_READY without Windows artifacts.
