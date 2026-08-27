# AHOS — Next Development Backlog

**Date:** 2026-08-27  
**Classification:** `INTEGRATION_READY` (agent-host) — Windows defects fixed; OPERATOR_READY NOT_VERIFIED  
**Law:** No speculative features until Windows operator gates + evidence accrual.

## Active phase (do these, not new P5 features)

| ID | Goal | Owner |
|----|------|-------|
| OV-0 | Follow `docs/WINDOWS_OPERATOR_HANDOFF.md` | OWNER |
| OV-PG | Postgres + DATABASE_URL for G2 | OWNER |
| OV-1 | Run Windows operator_validation_gate | OWNER |
| OV-2 | PRE_SOAK only if `pre_soak_entry_ok` | OWNER |
| OV-3 | ≥72h observation-cycle → joined_pairs (real time) | OWNER |
| OV-4 | Telegram live E2E (required for OPERATOR_READY) | OWNER |
| OV-LA | Decide Lane-A RO URI fix + freeze re-anchor | OWNER |
| OV-5 | Promote OPERATOR_READY only with Windows G1–G11 artifacts | Evidence |

## Deferred (explicit — do not implement now)

Dev-activity collector · AG-25 · deep holder/RPC expansions · numeric TS↔Python parity · cosmetic dashboard · autonomous evolution

## Completed engineering (prior)

P0 narrative · P1 intel analyzers · prediction→Lane-A bridge · scoring contract v1 semantic
