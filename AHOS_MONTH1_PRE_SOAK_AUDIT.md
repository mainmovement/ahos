# AHOS Month 1 — Pre-Soak Readiness Audit

**Date:** 2026-08-18 · **Auditor:** Production Reliability Engineer (Arena Agent)
**Baseline:** `arena/01a013f8-ahos` @ Phase-7 commit (+ Month-1 work this session), `main @ 95f5e14`
**Method:** Direct inspection with file:line evidence + executed commands. No architecture was
modified to make this audit pass. One legitimate defect found during audit was fixed and is
flagged as such (§17).

---

## 0. Executed Verification Commands (this session, post Month-1 tooling)

| # | Command | Result |
|---|---|---|
| V1 | `python scripts/validate_imports.py` | **PASS** — imports/evidence-boundary/Lane-A freeze/secrets all clean |
| V2 | `pytest tests/ -q` | **972 passed / 0 failed** (95.9s) |
| V3 | `python scripts/month1_failure_matrix.py` | **27/27 PASS** (report §2 of `AHOS_CONTROLLED_FAILURE_TEST_REPORT.md`) |
| V4 | `pytest tests/test_month1_failure_matrix.py tests/test_soak_snapshot.py tests/test_scheduler_phase7.py -q` | **19 passed** (matrix pinned as CI regression) |

## 1–16. Readiness Checklist

| # | Item | Evidence (file:line / command) | Result | Risk | Required action |
|---|---|---|---|---|---|
| 1 | Scheduler entrypoint | `architecture/runtime/__main__.py:35-45` (`--daemon --interval-sec N --observation-cycle`); daemon loop `:178-182` runs lease-locked `execute_scheduled_cycle("DAEMON_CYCLE")` | **PASS** | Single-process; restart policy is systemd's job | none |
| 2 | Lease/lock mechanism | `architecture/scheduling/engine.py` `scheduler_locks` table + `acquire_lease`/`release_lease`; takeover on expiry; proven by matrix S4/S5 (SIGKILL holder → SKIPPED_LOCKED while live → takeover after expiry) | **PASS** | Lease duration 300s default: a crashed holder blocks its schedule-name up to 5 min (by design, visible) | none |
| 3 | Heartbeat watchdog | `architecture/scheduling/watchdog.py` (OK/STALE/NO_HEARTBEATS, exit 0/2/3); systemd timer `deployment/ahos-watchdog.timer` (5 min) | **PASS** | Watchdog is local-only; needs journald/uptime monitor on VPS for off-box alerting | VPS: uptime monitor on `ahos-watchdog` unit failures |
| 4 | State persistence | SQLite: `scheduler_runs`, `scheduler_heartbeats`, `runtime_operational_metrics` (local); `production_observations` + E-01 tables (discovery). Matrix P-series: restart continuity, PK dup rejection, interrupted-write rollback | **PASS** | Single-writer SQLite; WAL not enabled | monitor long-term fsync behavior in soak (gap register M-GAP-005) |
| 5 | Restart behavior | systemd `Restart=always` + `RestartSec=15` + crash-loop guard (`StartLimitBurst=5`/600s); graceful SIGTERM/SIGINT handling `__main__.py:96-104` | **PASS** | Unit never booted on a real VPS yet | VPS boot transcript during soak |
| 6 | Crash recovery | Matrix S5 (crashed lease holder), S9-10 (watchdog), P1 (restart continuity); missed-window audit registers gaps without backfill | **PASS** | none observed in fault injection | confirm with real kill during soak (protocol §6) |
| 7 | Wall-clock drift protection | `engine.py::check_clock_drift` (Phase-7 real implementation: wall-vs-monotonic divergence; pre-2023 sanity floor). Matrix S7: +600s → 600.0s, −3600s → 3600.0s measured | **PASS** | Detects steps since process start, not absolute NTP offset | acceptable (documented limitation M-GAP-006) |
| 8 | Provider failure handling | Fail-closed envelopes `DOWN/ERROR/NO_KEY/UNSUPPORTED` across adapters; 3-state circuit breakers `architecture/collector/circuit_breaker.py`; matrix P-series 8/8 PASS | **PASS** | none | none |
| 9 | UNKNOWN/UNSUPPORTED discipline | `contracts.py` None-sentinel + `identify_unknowns()`; matrix P6/P7/P8: 30 UNKNOWN fields tracked; unsupported chains never fabricate | **PASS** | none | none |
| 10 | Circuit breakers | `architecture/collector/engine.py:186-194` `get_provider_health()` exposes breaker state/failures; tests `test_provider_failure_resilience.py` green | **PASS** | breaker states not yet in soak snapshots | included in snapshot tool via metrics (see protocol) |
| 11 | Logging | `architecture/runtime/logging.py` structured logger w/ run_id; secrets redaction `architecture/security/hygiene.py` (scan of 2,115 files clean, V1) | **PASS** | logs go to journald only | VPS: set up log persistence check |
| 12 | systemd service/timer | `deployment/ahos-runtime.service`, `ahos-watchdog.service`, `ahos-watchdog.timer` — reviewed: restart policy, hardening (NoNewPrivileges/ProtectSystem/PrivateTmp), no secrets in unit | **PASS** | paths assume `/opt/ahos` + `ahos` user | document install commands in protocol (done) |
| 13 | Configuration & environment | `config/paths.py` (env override `AHOS_DATA_DIR`); Telegram strictly optional (`__main__.py:67-71`: no token → MockTelegramAdapter, no network); forbidden live-trading vars veto (`hygiene.py:62-73`) | **PASS** | none | none |
| 14 | Data directories | `config/paths.py:56-70` auto-creates `data/`; `scripts/init_databases.py` idempotent bootstrap (CREATE IF NOT EXISTS, append-only guards, zero fabrication — header docstring) | **PASS** | none | run bootstrap before soak start (done, §protocol) |
| 15 | Permissions | No secrets in any service unit; `.gitignore` excludes `*.sqlite`, `.env*`; secrets scan clean (V1); DB files are the only writable state | **PASS** | VPS file ownership `ahos:ahos` to be set at install | install checklist in protocol |
| 16 | External dependencies | `requirements.txt`: PyYAML/numpy/pandas/requests/urllib3/PySocks/pytest(+timeout). Runtime core stdlib-first (urllib). Zero paid SDKs. venv installs clean (re-created this session) | **PASS** | none | none |

## 17. Defect Found & Fixed During Audit (flagged, not hidden)

**M-GAP-001 (fixed):** `architecture/scheduling/watchdog.py` opened probes with plain
`sqlite3.connect()`, which **creates an empty DB file** when the store is missing — contradicting
the module's read-only contract. Fixed: read-only URI connections (`file:...?mode=ro`).
Regression-pinned by `tests/test_soak_snapshot.py::test_snapshot_missing_stores_report_no_data_never_fabricated`
(asserts no file is created). System behavior unchanged otherwise.

## 18. Decision

**Phase 1: PASS** — all 16 readiness items hold with evidence; 972-test suite green;
27/27 controlled-failure scenarios green after honest iteration (see failure-test report §"iteration log").

Soak start is authorized under `AHOS_MONTH1_SOAK_PROTOCOL.md`.
