# FINAL TRUTH AUDIT

**Date:** 2026-08-27  
**Branch tip:** `cursor/ahos-cleanup-alignment-4bde` (PR #19)  
**PR:** https://github.com/mainmovement/ahos/pull/19  
**Classification:** `INTEGRATION_READY` (agent-host verified) — **NOT** `OPERATOR_READY` / `PRODUCTION_READY`  
**Next phase:** Operator laptop verification + outcome accrual + soak (see backlog)

---

## INTEGRATION_READY acceptance (this pass)

| Criterion | Required | Result |
|---|---|---|
| Discovery provider LIVE SUCCESS (tokens>0) on a verified host | Yes | **PASS** — dexscreener + geckoterminal (`reports/provider_probe_LIVE_VERIFIED_agent_host.json`) |
| Pipeline collect → score → persist (`local` ledger) | Yes | **PASS** — single-cycle candidates scored+persisted |
| Narrative wired into scoring path | Yes | **PASS** — code + unit + live DERIVED atoms |
| Market/tokenomics/catalyst layers IMPLEMENTED+TESTED | Yes | **PASS** — Lane B intel modules |
| Scoring semantic contract documented | Yes | **PASS** — `docs/contracts/scoring_contract_v1.json` |
| Lane-A freeze intact | Yes | **PASS** — 36 files |
| Full offline test suite green | Yes | *re-run at end of pass* |
| Telegram live E2E | No (→ OPERATOR) | NOT VERIFIED |
| 7-day soak | No (→ OPERATOR) | NOT VERIFIED |
| Calibration validated | No (→ data) | `CALIBRATION_READY_BUT_DATA_REQUIRED` (0 outcome pairs) |
| n8n operational | No | JSON VALID only |
| Operator Windows laptop egress | Residual | USER ACTION (re-run probe) |

---

## Capability matrix

| Capability | Code | Tests | Runtime | External | Status | Evidence |
|---|---|---|---|---|---|---|
| Discovery providers | Y | Y | LIVE on agent host | Laptop residual | LIVE_VERIFIED (agent) / BLOCKED_EXTERNAL (laptop until OA-3) | probe JSON |
| Evidence accrual (score ledger) | Y | Y | LOCAL rows exist | Outcomes sparse | LOCALLY_VERIFIED | ledger census |
| Observation poller (Lane-A active set) | Y | Y | tracked=0 this cycle | Needs seeded actives | IMPLEMENTED | single-cycle log |
| Narrative feed-through | Y | Y | LIVE DERIVED | — | LIVE_VERIFIED (agent) | intel atoms JSON |
| Market structure | Y | Y | LIVE DERIVED | — | IMPLEMENTED + TESTED | `intel/market_structure.py` |
| Tokenomics | Y | Y | LIVE DERIVED | Unlock UNKNOWN | IMPLEMENTED + TESTED | never fabricates vesting |
| Catalysts | Y | Y | LIVE FOUND when headlines match | — | IMPLEMENTED + TESTED | provenance required |
| Holder / smart-money depth | Partial | Partial | — | RPC limits | PARTIAL | existing holders/whales |
| Development activity | N | N | — | — | NOT_IMPLEMENTED | P5 |
| Opportunity scoring | Y | Y | LIVE | — | LOCALLY_VERIFIED + LIVE path | |
| Security veto | Y | Y | Unit | Live contract partial | LOCALLY_VERIFIED | authoritative |
| Scoring contract Py↔TS | Y | Y | — | Numeric parity NOT claimed | IMPLEMENTED | contract v1 |
| Calibration | Engine Y | Y | INSUFFICIENT_DATA | Need outcome labels | CALIBRATION_READY_BUT_DATA_REQUIRED | calibration JSON |
| Telegram W57 | Y | Y | Unit | Live token | LOCALLY_VERIFIED | OA-1 |
| n8n | JSON Y | validate Y | Live NOT | Owner | JSON VALID ≠ OPERATIONAL | |
| 7-day soak | Protocol Y | — | Not run | Owner | PROTOCOL ONLY | |
| CI | Absent | — | — | workflows perm | NOT PRESENT | |

---

## Forbidden claims (remain FALSE unless noted)

| Claim | Status |
|---|---|
| Production Ready | FALSE |
| Live Provider Verified (operator laptop) | FALSE — agent host TRUE |
| Telegram E2E Verified | FALSE |
| n8n Operational | FALSE |
| 7-Day Soak Passed | FALSE |
| Calibration Validated | FALSE |
| CI Active | FALSE |
| Automatic AI Model Routing | FALSE |

---

## Gate results (end of integration pass)

| Gate | Result |
|---|---|
| `npm run typecheck` | PASS |
| `.venv/bin/pytest tests/ -q` | **1399 passed**, 0 failed |
| `python3 scripts/freeze_lane_a.py` | OK (36 files) |
| `python3 tests/validate_n8n.py` | 6/6 PASS (JSON only) |
| `--probe-providers` (agent host) | LIVE SUCCESS: dexscreener, geckoterminal |
| `--single-cycle --evidence-source local` | candidates scored + persisted |
| Live intel atoms | narrative/mstruct/tokenomics/catalyst DERIVED |
| `scripts/calibration_report.py` | INSUFFICIENT_DATA (0 outcome pairs) |