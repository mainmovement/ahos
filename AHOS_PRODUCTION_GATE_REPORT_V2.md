# AHOS Production Gate Report V2 (Phase 8)

**Date:** 2026-08-18  
**Baseline SHA (post PR #5):** `e92bbb5525fa46f99565401622acab1a04a115db`  
**Classification rule:** evidence only. Protocol soak window (`AHOS_MONTH1_SOAK_PROTOCOL.md` §7) is **not closed**.

---

## 1. Executive verdict

### **NOT_READY**

Fault-injection and backup-restore **tools** are proven in-repo. Continuous operation, provider success, CI, live Telegram, 7-night host backups, and off-box alerting are **not** proven. Assigning `CONDITIONAL_READY` or `PRODUCTION_READY` would violate the pre-committed soak rule and the evidence-discipline rule.

Older “95.5 / READY_FOR_DEPLOYMENT” language in `AHOS_PRODUCTION_READINESS_REPORT.md` remains **non-evidence**.

---

## 2. Verified capabilities

| Capability | Evidence |
|---|---|
| PR #5 on `main` | merge commit `e92bbb5`; `mergedAt=2026-08-18T15:21:51Z` |
| Lane-A freeze (36 files) | `python scripts/freeze_lane_a.py`; `reports/system_state_snapshot.json` `lane_a.ok=true` |
| Reliability challenge 7/7 | `reports/reliability_matrix.json` `result=PASS` `passed=7` `failed=0` |
| Full Month-1 matrix 28/28 (re-run inside challenge) | same file `matrix_total=28` `matrix_passed=28` |
| SQLite backup/restore tool + one drill | `reports/backup_restore_drill.json`; challenge `backup_restore_correctness` |
| Fail-closed provider outage records | `architecture/collector/engine.py` table `provider_failure_events`; challenge `provider_outage_visibility` |
| No order/SDK surface in scanned packages | matrix `no_execution_surface` hits=0 |
| Live probe honesty (failure recorded, not invented OK) | `reports/system_state_snapshot.json` `provider_probe` both `ERROR` TLS EOF |

---

## 3. Evidence index

| File | command | timestamp_utc | git SHA | exit / result |
|---|---|---|---|---|
| `reports/system_state_snapshot.json` | `python scripts/system_state_snapshot.py` | `2026-08-18T15:24:57Z` | `e92bbb5…` | `RECORDED` / 0 |
| `reports/reliability_matrix.json` | `python scripts/reliability_challenge.py` | `2026-08-18T15:24:57Z` | `e92bbb5…` | `PASS` / 0 |
| `reports/reliability_matrix_20260818T152457Z.json` | same | same | same | same |
| `reports/backup_restore_drill.json` | `python scripts/sqlite_backup_restore.py drill` | `2026-08-18T15:09:56Z` | `3c7476d…` | `PASS` |
| `reports/pytest_run.json` | `/home/user/ahos/.venv/bin/python -m pytest tests/ -q` | `2026-08-18T15:30:05Z` | `e92bbb5525fa46f99565401622acab1a04a115db` | `992 passed` / exit 0 |
| `reports/validate_imports_run.json` | `/home/user/ahos/.venv/bin/python -B scripts/validate_imports.py` | `2026-08-18T15:29:52Z` | `e92bbb5525fa46f99565401622acab1a04a115db` | `PASS` / exit 0 |
| `reports/month1_failure_matrix.json` | `python scripts/month1_failure_matrix.py` | `2026-08-18T14:25:17Z` | prior | 28/28 |
| `reports/soak_snapshot_20260818T142806Z.json` | soak **pilot** | `2026-08-18T14:28:06Z` | prior | pilot only |

Each Phase-8 artifact includes `environment.fingerprint_sha256`.

---

## 4. Failure resilience results

From `reports/reliability_matrix.json`:

| # | Challenge | Scenario | Verdict | Evidence string |
|---|---|---|---|---|
| 1 | process_kill_recovery | `crashed_process_recovery` | PASS | `immediate=SKIPPED_LOCKED after_expiry=SUCCESS` |
| 2 | database_interruption_recovery | `interrupted_write` | PASS | `rows=0 integrity=ok` |
| 3 | provider_outage_visibility | `collector_failure_durable_visible` | PASS | `records=0 fetch_errors=2` |
| 4 | clock_anomaly_handling | `clock_step_forward_backward` | PASS | `forward=600.0s backward=3600.0s` |
| 5 | duplicate_event_protection | `duplicate_event_rejected` | PASS | `integrity_error_raised=True` |
| 6 | missing_heartbeat_behavior | `watchdog_fail_closed` | PASS | `status=NO_HEARTBEATS` |
| 7 | backup_restore_correctness | drill | PASS | `stores=1 passed=1 failed=0` |

These are **injected** faults in a workdir. They are not a 168h host soak.

---

## 5. Active risks

| Risk | Classification | Evidence |
|---|---|---|
| No daemon / no heartbeats on this host | operational | snapshot `watchdog.status=NO_HEARTBEATS` |
| Market-data egress blocked (TLS EOF) | M-GAP-007 OPEN | snapshot `provider_probe` |
| CI cannot run on GitHub | M-GAP-004 BLOCKED | `gh pr checks 5` → no checks |
| SQLite WAL / long-uptime fsync unobserved | M-GAP-005 OPEN | no soak series |
| Clock check is relative, not NTP | M-GAP-006 MITIGATED | `engine.py` `check_clock_drift` |
| Backup rotation not scheduled on a host | M-GAP-010 residual | drill `unproven` list |

---

## 6. Remaining blockers

| ID | Phase-8 class | Blocker |
|---|---|---|
| M-GAP-003 | OPEN | 168h soak on a persistent host |
| M-GAP-004 | BLOCKED | GitHub App `workflows` permission |
| M-GAP-007 | OPEN | provider success on a host with working egress |
| M-GAP-008 | OPEN | scoring calibration (≥8 weeks history) |
| M-GAP-009 | BLOCKED | live Telegram token + transcript |
| M-GAP-010 residual | MITIGATED | 7 nightly backups + fresh-host restore |
| M-GAP-012 | OPEN | off-box watchdog alert received |

---

## 7. Production recommendation

1. Do **not** call the system production-ready.
2. Provision the VPS per `AHOS_VPS_MIGRATION_READINESS.md` (prepare only until owner executes).
3. Start the 168h soak (`AHOS_MONTH1_SOAK_PROTOCOL.md` §3) and commit `system_state_snapshot` / `soak_snapshot` on cadence.
4. Re-probe providers on that host; only then can M-GAP-007 move.
5. Owner: grant Actions `workflows` permission; rotate Telegram token if Month-4 is in scope.

**Final classification: `NOT_READY`.**
