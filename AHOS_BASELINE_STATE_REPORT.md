# AHOS Baseline State Report (Phase 8 / post-merge)

**Generated:** 2026-08-18T15:24:57Z  
**Rule:** no readiness percentages; no capability is “verified” without a path or artifact.

## Post-merge baseline (Phase 1)

| Check | Evidence | Result |
|---|---|---|
| PR #5 merged | `gh pr view 5` → `state=MERGED`, `mergedAt=2026-08-18T15:21:51Z`, merge commit `e92bbb5525fa46f99565401622acab1a04a115db` | MERGED |
| Current `origin/main` SHA | `git ls-remote origin refs/heads/main` / `git rev-parse origin/main` | `e92bbb5525fa46f99565401622acab1a04a115db` |
| Working branch | `git rev-parse --abbrev-ref HEAD` | `arena/01a01560-ahos` at same SHA as `main` before this Phase-8 change-set |
| Lane-A freeze | `python scripts/freeze_lane_a.py` → `Lane-A integrity OK (36 files pinned)`; `reports/system_state_snapshot.json` `lane_a.ok=true` | INTACT |
| Evidence artifacts (pre-Phase-8, on `e92bbb5`) | `reports/pytest_run.json`, `reports/validate_imports_run.json`, `reports/backup_restore_drill.json` | PRESENT |

Repository cleanliness at snapshot time: `git.working_tree_clean=false` in `reports/system_state_snapshot.json` because this change-set was in progress. That is recorded, not hidden.

## Current architecture state

Operational surface (not redesigned in Phase 8):

| Layer | Location | Role |
|---|---|---|
| Runtime daemon | `architecture/runtime/__main__.py` | `--daemon --interval-sec 60 --observation-cycle` |
| Scheduler / leases / drift | `architecture/scheduling/engine.py` | `scheduler_runs`, `scheduler_locks`, `scheduler_heartbeats` |
| Watchdog | `architecture/scheduling/watchdog.py` | read-only; OK / STALE / NO_HEARTBEATS |
| Collector + failure events | `architecture/collector/engine.py` | `provider_failure_events` |
| Providers | `architecture/providers/` | fail-closed envelopes; no exchange SDK |
| Scoring | `architecture/scoring/` | paper/observation scoring only |
| Persistence bootstrap | `scripts/init_databases.py` | four SQLite stores under `data/` (gitignored) |
| systemd | `deployment/ahos-runtime.service`, `ahos-watchdog.service`, `ahos-watchdog.timer` | units exist; **not installed on this host** |
| Soak snapshot | `scripts/soak_snapshot.py` | read-only |
| Backup/restore | `scripts/sqlite_backup_restore.py` | Online Backup API |
| System state (Phase 8) | `scripts/system_state_snapshot.py` | this baseline’s live snapshot |
| Reliability challenge (Phase 8) | `scripts/reliability_challenge.py` | 7 mapped fault tests |

Lane-A (`discovery/*`, `paper_trading/*` schemas) is frozen. Phase 8 does not touch it.

## Verified capabilities

Verified = code path + test and/or committed machine artifact.

| Capability | Evidence |
|---|---|
| Import / freeze / secrets gate | `reports/validate_imports_run.json` (on `3c7476d`, still valid until Phase-8 re-run) |
| Pytest suite | `reports/pytest_run.json` (`988 passed` on `3c7476d`) |
| Controlled failure matrix (28) | `reports/month1_failure_matrix.json`; re-executed inside `reports/reliability_matrix.json` `matrix_total=28` `matrix_passed=28` |
| Process-kill lease recovery | `reports/reliability_matrix.json` challenge `process_kill_recovery` PASS |
| Interrupted-write rollback | same file, `database_interruption_recovery` PASS |
| Provider outage durable/visible | same file, `provider_outage_visibility` PASS; schema `architecture/collector/engine.py` `provider_failure_events` |
| Clock-step measurement | same file, `clock_anomaly_handling` PASS (`forward=600.0s backward=3600.0s`) |
| Duplicate PK rejection | same file, `duplicate_event_protection` PASS |
| Missing-heartbeat fail-closed | same file, `missing_heartbeat_behavior` PASS (`NO_HEARTBEATS`) |
| Backup/restore drill (tool + one run) | `reports/backup_restore_drill.json`; challenge `backup_restore_correctness` PASS |
| Lane-A hash pin | `config/lane_a_freeze.sha256` + freeze CLI |
| No execution surface (static) | matrix `no_execution_surface` `hits=0` in reliability run stdout |

## Unverified capabilities

| Capability | Why unverified | Evidence of absence |
|---|---|---|
| 168h continuous soak | this host has `watchdog.status=NO_HEARTBEATS`, `scheduler.runs_in_window=0` | `reports/system_state_snapshot.json` |
| Provider **success** path | live probe TLS EOF, `token_count=0` | same file `provider_probe` |
| GitHub Actions | no checks on PRs; App `workflows` permission missing (M-GAP-004) | `gh pr checks 5` → `no checks reported` |
| Live Telegram | no token; no live transcript in repo | M-GAP-009; `.env.example` token empty |
| Scoring calibration | no ≥8 weeks observation history | `stores.e01_discovery.row_total=0` |
| 7-night backup series / fresh-host restore | one in-repo drill only | `reports/backup_restore_drill.json` `unproven` |
| Off-box watchdog alert | local probe only; no VPS / uptime monitor | `deployment/ahos-watchdog.service` comments |
| systemd actually running | units shipped, not installed here | snapshot `NO_HEARTBEATS` |

## Evidence inventory

| Artifact | SHA recorded inside | Notes |
|---|---|---|
| `reports/system_state_snapshot.json` | `e92bbb5…` | Phase 8; watchdog NO_HEARTBEATS; provider ERROR |
| `reports/reliability_matrix.json` | `e92bbb5…` | 7/7 PASS |
| `reports/reliability_matrix_20260818T152457Z.json` | same payload | stamped copy |
| `reports/backup_restore_drill.json` | `3c7476d` / refreshed | M-GAP-010 tool evidence |
| `reports/pytest_run.json` | `3c7476d` | superseded after Phase-8 pytest re-run |
| `reports/validate_imports_run.json` | `3c7476d` | same |
| `reports/month1_failure_matrix.json` | earlier session | 28/28 |
| `reports/soak_snapshot_20260818T142806Z.json` | soak **pilot** | hours, not 168h |
| `reports/soak_pilot_log_20260818T1431Z.jsonl` | soak **pilot** | runtime observation archived |
