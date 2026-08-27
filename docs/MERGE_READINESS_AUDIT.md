# AHOS — Merge Readiness / Transfer Control Audit

**Captured:** 2026-08-27 (agent-host)  
**Scope:** PR #19 freeze for GitHub → Windows transfer  
**Law:** Repository evidence only. **MERGE_READY ≠ OPERATOR_READY**.

| Field | Value |
|-------|--------|
| Branch | `cursor/ahos-cleanup-alignment-4bde` |
| HEAD | `d8f18db` |
| PR | https://github.com/mainmovement/ahos/pull/19 |
| Base | `main` |
| Classification | `INTEGRATION_READY` (agent-host) |
| `OPERATOR_READY` | **NOT_VERIFIED** |
| Windows gate artifact | **absent** |

---

## MERGE DECISION

### **MERGE_READY**

Safe as a canonical GitHub revision for Windows clone/pull.

Does **not** mean Windows verified, Telegram live, n8n operational, soak complete, or calibration validated.

---

## Gates run this pass (agent-host)

| Gate | Result |
|------|--------|
| pytest | **1417 passed** |
| `npm run typecheck` | PASS |
| Lane-A freeze | PASS (36 files; **0 frozen sources changed vs main**) |
| n8n structural | PASS 6/6 |
| security / config / operator-gate / paths / lifecycle / scoring contract | PASS (targeted + full suite) |

---

## Claim → evidence map

| Claim | Status | Evidence |
|-------|--------|----------|
| Integration on agent-host | IMPLEMENTED + TEST_VERIFIED | suite + freeze |
| Agent-host live providers | LIVE_VERIFIED (prior) | `reports/provider_probe_*agent_host*` |
| Operator Windows gates | NOT_VERIFIED | no windows JSON |
| Telegram live E2E | OWNER_ACTION_REQUIRED | no transcript |
| n8n operational | NOT_VERIFIED | structural only |
| Calibration pairs | NOT_VERIFIED | outcome_labels=0 |
| Soak | NOT_VERIFIED | blocked until Windows G1–G10 |
| PAPER_ONLY / live-trade veto | TEST_VERIFIED | `assert_safe_environment` reads `AHOS_PAPER_ONLY` |
| Lane-A Windows RO URI | BLOCKED (governance) | frozen files unchanged; gap documented |
| AG-25 / speculative | NOT_IMPLEMENTED / DEFERRED | backlog |
| Secrets committed | NOT present | `.env` gitignored; no `.env` in tree |

---

## Truth hierarchy

1. Artifacts + tests with platform provenance  
2. `docs/CURRENT_TRUTH_SNAPSHOT.md` + `docs/FINAL_TRUTH_AUDIT.md`  
3. Operator handoff / protocols  
4. `docs/DOC_TRUTH_MAP.md`  
5. Superseded historical READY docs (bannered)

---

## Windows handoff

`docs/WINDOWS_OPERATOR_HANDOFF.md` commands verified against modules/flags; no `-e` install; no fake `AHOS_DB_PATH`; Postgres explicit.

---

## Post-merge human sequence

1. Human merge PR #19  
2. Windows clone/pull  
3. Handoff → Windows Operator Validation  
4. Pre-soak only if `pre_soak_entry_ok`  
5. Real T+72h → labels → calibration → soak  
6. Evidence-based readiness promotion only

---

## Explicit non-claims

OPERATOR_READY · PRODUCTION_* · Windows verified · Telegram E2E · n8n ops · soak · calibration validated
