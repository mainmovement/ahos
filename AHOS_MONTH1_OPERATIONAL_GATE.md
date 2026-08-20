# AHOS Month 1 — Operational Gate

**Date opened:** 2026-08-18 · **Classification rule:** `AHOS_MONTH1_SOAK_PROTOCOL.md` §7 (pre-committed)
**Rule honored:** no readiness percentages, no "production ready" language unless evidence supports it.

---

## Classification: **PENDING — SOAK EVIDENCE INCOMPLETE**

The gate accepts exactly PASS / CONDITIONAL PASS / FAIL **after** the 7-day soak window
closes (`AHOS_MONTH1_SOAK_PROTOCOL.md` §7). The window opened 2026-08-18 ~14:18 UTC and requires
168 consecutive hours on a persistent host. Assigning any of the three classifications today
would violate the protocol's own pre-registration rule — so the honest classification is PENDING.

## What Has Been Verified (evidence-linked)

| Area | Evidence | Verdict |
|---|---|---|
| Readiness (16 items) | `AHOS_MONTH1_PRE_SOAK_AUDIT.md` §1–16 (file:line + commands). Checklist inspection — not a soak PASS. | INSPECTION ONLY |
| Controlled failures | Committed machine record `reports/month1_failure_matrix.json` (`total=28`, `passed=28`, `failed=0`). Narrative in `AHOS_CONTROLLED_FAILURE_TEST_REPORT.md` is not a substitute for that file. | PASS (matrix file only) |
| Full regression | Counts live only in `reports/pytest_run.json` and `reports/validate_imports_run.json` (command + timestamp_utc + git.commit_sha + exit_code). Prior narrative “983 passed” / “972 passed” sentences had no artifact and are withdrawn. | SEE ARTIFACT |
| Live pilot | Committed snapshot `reports/soak_snapshot_20260818T142806Z.json` + `reports/soak_pilot_log_20260818T1431Z.jsonll`. Sandbox hours, not the 168h window. | ACCRUING (pilot) |
| Backup/restore drill | `reports/backup_restore_drill.json` + `tests/test_sqlite_backup_restore.py`. One executed drill; not 7 nightly host backups. | MITIGATED |

## What Failed (found & dispositioned)

1. **M-GAP-001** watchdog file-creation side effect → **fixed + regression-pinned** (closed).
2. **M-GAP-002** silent provider outages at collector level (live discovery!) → **fixed same
   session** (durable `provider_failure_events` + WARN logs), fix verified live; matrix extended
   to 28 scenarios. Both defects were found by this gate process — evidence the process works.
3. Initial failure-matrix run 24/27 — all three FAILs were harness-side (documented in report §2);
   no system behavior was changed to pass them.

## What Remains Unproven

- 168-hour continuous operation on a persistent host (M-GAP-003) — pilot is sandbox-hosted; the
  sandbox is a dev container, not the target VPS, and its egress blocks market-data APIs
  (M-GAP-007): provider **availability/success paths** need the VPS; the pilot proves the
  **failure-side** discipline only.
- Live Telegram (M-GAP-009), scoring calibration on real history (M-GAP-008), 7-night host
  backup series + fresh-host restore (M-GAP-010 residual), off-box watchdog alerting (M-GAP-012).
- Deliberate recovery events (kill -9 / SIGTERM / 20-min pause — protocol §6) scheduled for
  pilot days 1/3/5.

## Classification Procedure (at window close)

1. Compute each protocol §7 criterion from committed snapshots + DBs + logs only.
2. Apply the pre-committed classification rule (§7 bottom).
3. Record PASS / CONDITIONAL PASS / FAIL here with per-criterion evidence links; any deviation
   from pre-committed criteria must be flagged as a protocol violation.

## Interim System State (honest)

Operational mechanics (scheduling, leasing, heartbeats, persistence, fail-closed safety,
failure observability) are **fault-injection-proven and pilot-live-proven for hours, not days**.
Provider success paths are **unproven from this host**. Nothing here justifies the phrase
"production ready".
