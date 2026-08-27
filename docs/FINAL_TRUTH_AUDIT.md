# FINAL TRUTH AUDIT

**Date:** 2026-08-27  
**Branch tip:** `cursor/ahos-cleanup-alignment-4bde` (PR #19)  
**PR:** https://github.com/mainmovement/ahos/pull/19  
**Classification:** `INTEGRATION_READY` (agent-host) — **NOT** `OPERATOR_READY` / `PRODUCTION_READY`  
**Calibration:** `CALIBRATION_READY_BUT_DATA_REQUIRED` (lifecycle bridged; await T+72h labels)

---

## Capability matrix (selected)

| Capability | Status | Evidence |
|---|---|---|
| Discovery LIVE (agent host) | AGENT_HOST_VERIFIED | probe JSON SUCCESS |
| Score ledger `local` preds | LOCALLY_VERIFIED | census > 0 |
| Lane-A observation registration | IMPLEMENTED + TEST_VERIFIED + AGENT_HOST_VERIFIED | bridge + backfill → OBSERVING=101 |
| Outcome labels | INSUFFICIENT_DATA | 0 until T+72h RESOLVED |
| Calibration pairs | INSUFFICIENT_DATA | join ready; no labels yet |
| Narrative / mstruct / tokenomics / catalyst | AGENT_HOST_VERIFIED | live DERIVED atoms |
| Scoring contract v1 | TEST_VERIFIED | semantic; numeric parity NOT required |
| Dev-activity / AG-25 | NOT_IMPLEMENTED | deferred (not speculative this pass) |
| Telegram live E2E | OWNER_ACTION_REQUIRED | protocol: `docs/TELEGRAM_OPERATOR_E2E_PROTOCOL.md` |
| n8n operational | OWNER_ACTION_REQUIRED | `docs/N8N_OPERATIONAL_PROCEDURE.md` |
| Operator Windows probe | OWNER_ACTION_REQUIRED | OA-3 |
| 7-day soak | OWNER_ACTION_REQUIRED | OA-5 |
| CI | EXTERNALLY_BLOCKED | OA-7 |

---

## Prediction lifecycle (this pass)

Root cause of 348 preds / 0 pairs: Lane-B never seeded Lane-A `observation_state`.

Fix (Lane B only): `architecture/learning/prediction_lifecycle.py` + orchestrator hook + backfill script.

After backfill on agent host: `OBSERVING=101`, `discovery_observations=354`, `outcome_labels=0` (honest).

Canonical doc: `docs/CALIBRATION_LIFECYCLE.md`

---

## Gate results

| Gate | Result |
|---|---|
| typecheck | *re-run at end* |
| pytest | *re-run at end* |
| Lane-A freeze | OK (36) — no Lane-A source edits |
| n8n validate | 6/6 JSON |
| calibration_report | INSUFFICIENT_DATA |

---

## Highest proven classification

**`INTEGRATION_READY`** (agent-host).

Not promoted to OPERATOR_READY: Windows live probe, Telegram E2E, soak, and calibration pairs with guards unmet.
