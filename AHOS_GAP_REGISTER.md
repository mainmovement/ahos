# AHOS Production Gap Register

**Created:** 2026-08-18 (Month 1 Operational Gate phase) · **Supersedes:** AHOS_REALITY_AUDIT_v2.md §5 (informal list)
**Ordering (strict):** 1 Safety · 2 Data integrity · 3 Scheduler reliability · 4 Persistence ·
5 Provider reliability · 6 Observability · 7 Performance · 8 UX
**Status legend:** OPEN · MITIGATED (control exists, residual risk documented) · CLOSED (evidence-linked)

| GAP ID | Discovered | Priority tier | Evidence | Subsystem | Reproducibility | Mitigation | Owner / action | Acceptance criterion | Status |
|---|---|---|---|---|---|---|---|---|---|
| M-GAP-001 | 2026-08-18 (audit) | 4 Persistence | watchdog probe created empty SQLite files on missing stores (violated read-only contract) | architecture/scheduling/watchdog.py | deterministic: probe nonexistent path → file appeared | read-only URI connections (`file:...?mode=ro`); regression `tests/test_soak_snapshot.py::test_snapshot_missing_stores_report_no_data_never_fabricated` | — (fixed in-session) | probe leaves filesystem unchanged | **CLOSED** |
| M-GAP-002 | 2026-08-18 (soak pilot, live) | 5 Provider reliability / 6 Observability | daemon log 14:18–14:24 UTC: providers TLS-blocked, 7 cycles logged only `candidates=0` at INFO; zero durable records; breaker state in-memory only (died with process) | architecture/collector/engine.py | sandbox egress blocks api.dexscreener.com / api.geckoterminal.com (TLS EOF); any network-dead host reproduces | FIXED same session: `provider_failure_events` table (durable FETCH_ERROR + BREAKER_OPEN_SKIP rows) + WARN logs; tests `test_collector_failure_visibility.py` (3); matrix scenario 29; live verification: 6 events recorded in first 3 post-fix cycles | — (fixed in-session; soak restart documented) | a provider outage is distinguishable from an honest empty market from committed stores alone | **CLOSED** (post-fix soak evidence continues to accrue) |
| M-GAP-003 | 2026-08-18 (audit v2 carry-over) | 3 Scheduler reliability | no soak evidence ≥ 7 days exists anywhere in repo history | whole system | run protocol | AHOS_MONTH1_SOAK_PROTOCOL.md active (sandbox pilot running; VPS window required for gate) | USER: VPS provision; then 168h window per protocol §3 | protocol §7 criteria with snapshots committed | **OPEN** (pilot accruing) |
| M-GAP-004 | 2026-08-18 (audit v2 carry-over) | 6 Observability | CI absent — GitHub App lacks `workflows` permission; remote push of ci.yml rejected 2026-08-18 | CI | any push touching `.github/workflows/*` | local gate (`scripts/validate_imports.py` + `pytest tests/ -q`) substitutes only when a committed `reports/*_run_*.json` artifact exists; ci.yml preserved untracked | USER: grant App `workflows` permission | PR shows green CI run | **OPEN** (blocked on owner) |
| M-GAP-005 | 2026-08-18 | 4 Persistence | SQLite in rollback-journal mode (no WAL); single-writer; fsync behavior under long uptime unobserved | data stores | soak duration | monitor integrity + write latency across soak; WAL switch is a post-soak reviewed change (not mid-soak) | engineer: evaluate WAL after gate | integrity_check=ok in every snapshot; no write-loss incidents | **OPEN** (monitoring) |
| M-GAP-006 | 2026-08-18 | 3 Scheduler reliability | drift detection measures wall-step since process start, not absolute NTP offset (a host booted with wrong clock shows 0 drift) | architecture/scheduling/engine.py | set wrong clock before process start | documented limitation; systemd-timesyncd on VPS keeps host clock sane; absolute-offset check = post-soak option (needs trusted time source) | VPS: enable NTP sync; revisit post-gate | host NTP active; no unexplained ABORTED_DRIFT storms | **MITIGATED** |
| M-GAP-007 | 2026-08-18 (pilot) | 5 Provider reliability | sandbox pilot cannot exercise live provider paths (egress-blocked) → provider *availability* unproven here; C1 evidence in pilot = failure-side only | providers | sandbox network policy | VPS soak exercises live paths; failure/UNKNOWN discipline already proven offline (matrix 28/28) | USER: VPS soak | protocol C-criteria met on live-provider host | **OPEN** |
| M-GAP-008 | 2026-08-18 (audit v2 carry-over) | 2 Data integrity | scoring calibration unvalidated on accumulated real observations | architecture/scoring | needs ≥ 8 weeks observation history | Month 3 roadmap gate (calibration harness) | engineer (Month 3) | calibration report on historical data | **OPEN** (by design, Month 3) |
| M-GAP-009 | 2026-08-18 (audit v2 carry-over) | 1 Safety-adjacent (operational) | Telegram never run live (token rotation pending) — alerts unverified end-to-end | telegram_ai | needs real token | Month 4; user blocker ① | USER: token rotation | live transcript archived | **OPEN** (blocked on user) |
| M-GAP-010 | 2026-08-18 (audit v2 carry-over; drill 2026-08-18) | 4 Persistence | originally: no SQLite backup/rotation strategy on any host | `scripts/sqlite_backup_restore.py`, `tests/test_sqlite_backup_restore.py`, `reports/backup_restore_drill.json` | `python scripts/sqlite_backup_restore.py drill` (synthetic + 4 AHOS stores) | Online Backup API + restore verification (source/backup/restored sha256, row counts, `integrity_check`) | residual: 7 consecutive nightly backups + cron on a persistent host; restore onto a fresh host | tool + one executed restore drill + regression test committed; 7-night host series still required for original Month-1 acceptance | **MITIGATED** |
| M-GAP-011 | 2026-08-18 (audit v2 carry-over) | 5 Provider reliability | missing adapters: CoinMarketCap, Launchpads; ChainExplorer has no keyless instance for bsc/avalanche/solana (honest UNSUPPORTED) | architecture/providers | import registry | Month 2 roadmap | engineer (Month 2) | adapters + live probe evidence | **OPEN** (Month 2) |
| M-GAP-012 | 2026-08-18 (audit v2 carry-over) | 6 Observability | watchdog is local-only; no off-box alerting path | deployment | VPS only | journald + free uptime monitor on ahos-watchdog unit failures (protocol §1 item 3) | USER/ops at VPS install | off-box alert received in drill | **OPEN** |

**Safety tier (1) — zero open gaps in the matrix/static-scan sense.** D-series criteria are
pinned by `reports/month1_failure_matrix.json` (committed) + `tests/test_month1_failure_matrix.py`.
No trading/wallet/execution surface exists in the scanned runtime packages. Live-trading env veto
and Lane-A freeze veto are exercised by that matrix. That is **not** a production-ready claim.

---

## Evidence classification (do not collapse these)

### Committed evidence (in git; may be cited as repository evidence)

| Item | Path |
|---|---|
| Controlled-failure matrix machine record | `reports/month1_failure_matrix.json` |
| Soak snapshot file (pilot window, not 168h) | `reports/soak_snapshot_20260818T142806Z.json` |
| Soak pilot log | `reports/soak_pilot_log_20260818T1431Z.jsonl` |
| Backup/restore drill (hashes, counts, integrity) | `reports/backup_restore_drill.json` |
| Backup/restore implementation + tests | `scripts/sqlite_backup_restore.py`, `tests/test_sqlite_backup_restore.py` |
| `provider_failure_events` schema/writer/tests | `architecture/collector/engine.py`, `tests/test_collector_failure_visibility.py` |
| Command-run artifacts (command + UTC + SHA + exit) | `reports/validate_imports_run_*.json`, `reports/pytest_run_*.json` |

A PASS/GREEN verdict in this register is allowed only when one of the rows above is the
evidence link. Markdown prose without an artifact is not evidence.

### Runtime observation (happened in a session; not repository evidence unless snapshotted)

- Sandbox soak daemon cycles described in `AHOS_MONTH1_OPERATIONAL_GATE.md` (hours, not days).
- Live TLS-blocked provider failures that motivated M-GAP-002 (only the table + tests + soak
  snapshot counts are committed; the daemon log itself is not in git).
- Any pytest/validate count written only in a narrative report and not in `reports/*_run_*.json`.

### Unproven (must not be labeled PASS)

- 168 consecutive hours on a persistent host (M-GAP-003).
- Provider **success** paths from a host with working market-data egress (M-GAP-007).
- 7 consecutive nightly backups + cron on a persistent host; restore to a fresh host (M-GAP-010 residual).
- Live Telegram (M-GAP-009), scoring calibration on real history (M-GAP-008), off-box watchdog (M-GAP-012).
- GitHub Actions green run (M-GAP-004).
- Protocol §6 deliberate recovery events (kill -9 / SIGTERM / 20-min pause) on the soak host.
- Any readiness percentage or “production ready / READY_FOR_DEPLOYMENT” sentence in older reports.
