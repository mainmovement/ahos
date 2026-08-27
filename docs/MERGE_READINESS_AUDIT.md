# AHOS — Merge Readiness / Transfer Control Audit

**Captured:** 2026-08-27 (agent-host)  
**Scope:** PR #19 freeze for GitHub → Windows transfer  
**Law:** Repository evidence only. MERGE_READY ≠ OPERATOR_READY.

| Field | Value |
|-------|--------|
| Branch | `cursor/ahos-cleanup-alignment-4bde` |
| HEAD | pinned at end of this pass (see git tip) |
| PR | https://github.com/mainmovement/ahos/pull/19 |
| Base | `main` |
| Classification | `INTEGRATION_READY` (agent-host) |
| `OPERATOR_READY` | **NOT_VERIFIED** |
| Windows gate artifact | **absent** |

---

## Claim → evidence map (selected)

| Claim | Status | Evidence |
|-------|--------|----------|
| Integration on agent-host | IMPLEMENTED + TEST_VERIFIED (+ prior LIVE provider) | pytest, freeze, prior provider JSON labeled `agent_host` |
| Operator Windows gates | NOT_VERIFIED | no `reports/operator_validation_report_windows_*` |
| Telegram live E2E | OWNER_ACTION_REQUIRED | no BotFather transcript |
| n8n operational | NOT_VERIFIED | structural only (`validate_n8n.py`) |
| Calibration pairs | NOT_VERIFIED / data-required | outcome_labels=0 |
| Soak | NOT_VERIFIED | pre-soak entry blocked until Windows G1–G10 |
| AG-25 / holders / speculative AI | NOT_IMPLEMENTED / DEFERRED | backlog |
| Lane-A freeze integrity | TEST_VERIFIED | `scripts/freeze_lane_a.py` OK; no frozen files in PR vs main |
| Lane-A Windows RO URI | BLOCKED (governance) | frozen `observe_active.py` / `paper_trading/ledger.py` still naive URI |
| PAPER_ONLY / live-trade veto | TEST_VERIFIED | `assert_safe_environment` + security tests |
| Secrets in tree | TEST_VERIFIED (scan) | `.env` gitignored; no committed `.env` |

---

## Truth hierarchy (canonical)

1. Executable artifacts + tests (`reports/*` with platform provenance, pytest, freeze)
2. `docs/CURRENT_TRUTH_SNAPSHOT.md` + `docs/FINAL_TRUTH_AUDIT.md`
3. `docs/WINDOWS_OPERATOR_HANDOFF.md` / operator protocols
4. `docs/DOC_TRUTH_MAP.md` (authority vs superseded)
5. Historical root reports (`AHOS_FINAL_STATUS.md` etc.) — **SUPERSEDED**, not current readiness

---

## Windows handoff audit

Commands in `docs/WINDOWS_OPERATOR_HANDOFF.md` checked against repo:

- modules/scripts/flags exist (`architecture.runtime`, `init_databases`, gate runner)
- no `pip install -e .`
- no canonical `AHOS_DB_PATH=ahos.db`
- Postgres `DATABASE_URL` explicit for G2
- PowerShell syntax; repo-relative paths (no `/workspace`)

Remaining transfer risks (owner): real Windows execution, Postgres availability, Telegram token, elapsed T+72h.

---

## MERGE vs OPERATOR

| Decision surface | Meaning |
|------------------|---------|
| **MERGE_READY** | Safe canonical GitHub revision for Windows clone/pull |
| **OPERATOR_READY** | Requires Windows gate JSON + G11 — **not claimed** |

Post-merge sequence: clone → handoff → Windows validation → pre-soak → ≥72h → calibration → soak → evidence-based promotion.

---

## Explicit non-claims

OPERATOR_READY · PRODUCTION_CANDIDATE · PRODUCTION_READY · Windows provider verified · Telegram E2E · n8n operational · soak passed · calibration validated
