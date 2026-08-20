# AHOS Production Gap Register

**Created:** 2026-08-18 (Month 1 Operational Gate phase) · **Supersedes:** AHOS_REALITY_AUDIT_v2.md §5 (informal list)
**Ordering (strict):** 1 Safety · 2 Data integrity · 3 Scheduler reliability · 4 Persistence ·
5 Provider reliability · 6 Observability · 7 Performance · 8 UX
**Status legend:** OPEN · MITIGATED (control exists, residual risk documented) · CLOSED (evidence-linked)
**Phase-8 class (this mission):** PROVEN · MITIGATED · OPEN · BLOCKED — never PASS without an artifact.

| GAP ID | Discovered | Priority tier | Evidence | Subsystem | Reproducibility | Mitigation | Owner / action | Acceptance criterion | Status |
|---|---|---|---|---|---|---|---|---|---|
| M-GAP-001 | 2026-08-18 (audit) | 4 Persistence | watchdog probe created empty SQLite files on missing stores (violated read-only contract) | architecture/scheduling/watchdog.py | deterministic: probe nonexistent path → file appeared | read-only URI connections (`file:...?mode=ro`); regression `tests/test_soak_snapshot.py::test_snapshot_missing_stores_report_no_data_never_fabricated` | — (fixed in-session) | probe leaves filesystem unchanged | **CLOSED** |
| M-GAP-002 | 2026-08-18 (soak pilot, live) | 5 Provider reliability / 6 Observability | daemon log 14:18–14:24 UTC: providers TLS-blocked, 7 cycles logged only `candidates=0` at INFO; zero durable records; breaker state in-memory only (died with process) | architecture/collector/engine.py | sandbox egress blocks api.dexscreener.com / api.geckoterminal.com (TLS EOF); any network-dead host reproduces | FIXED same session: `provider_failure_events` table (durable FETCH_ERROR + BREAKER_OPEN_SKIP rows) + WARN logs; tests `test_collector_failure_visibility.py` (3); matrix scenario 29; live verification: 6 events recorded in first 3 post-fix cycles | — (fixed in-session; soak restart documented) | a provider outage is distinguishable from an honest empty market from committed stores alone | **CLOSED** (post-fix soak evidence continues to accrue) |
| M-GAP-003 | 2026-08-18 (audit v2 carry-over; retargeted local) | 3 Scheduler reliability | no soak evidence ≥ 7 days exists anywhere in repo history | whole system | run `AHOS_LOCAL_SOAK_PROTOCOL.md` on the laptop | local daemon + snapshots; VPS is **not** required | USER: keep laptop awake 168h per local protocol | local protocol §10 criteria with committed laptop snapshots | **OPEN** |
| M-GAP-004 | 2026-08-18 (audit v2 carry-over) | 6 Observability | CI absent — GitHub App lacks `workflows` permission | CI | optional infrastructure | **optional** for local-laptop operation; local `reports/pytest_run.json` + `validate_imports_run.json` are the gate | none required for local soak | (optional) PR shows green CI run | **OPEN** — re-verified 2026-08-20: push of `.github/workflows/ci.yml` still rejected (`refusing to allow a GitHub App to create or update workflow ... without workflows permission`). Workflow drafted (untracked in working tree, Phase-7 precedent) ready to commit the moment the App is granted `workflows` permission. |
| M-GAP-005 | 2026-08-18 | 4 Persistence | SQLite in rollback-journal mode (no WAL); single-writer; fsync behavior under long uptime unobserved | data stores | soak duration | monitor integrity + write latency across soak; WAL switch is a post-soak reviewed change (not mid-soak) | engineer: evaluate WAL after gate | integrity_check=ok in every snapshot; no write-loss incidents | **OPEN** (monitoring) |
| M-GAP-006 | 2026-08-18 | 3 Scheduler reliability | drift detection measures wall-step since process start, not absolute NTP offset (a host booted with wrong clock shows 0 drift) | architecture/scheduling/engine.py | set wrong clock before process start | documented limitation; laptop OS automatic time sync (local soak protocol §1) | USER: leave OS time sync on | host clock sane; no unexplained ABORTED_DRIFT storms | **MITIGATED** |
| M-GAP-007 | 2026-08-18 (pilot) | 5 Provider reliability | live probe ERROR TLS EOF, `token_count=0` — success path unproven. Re-probed 2026-08-18 (Phase 11): 2 discovery providers `TLS_ERROR`, 4 non-discovery `UNSUPPORTED`, **0 SUCCESS** from this host | providers | host egress | failure/UNKNOWN discipline proven offline (matrix); success requires working **local** egress | USER: run `python -m architecture.runtime --probe-providers` on the laptop (command now exists — M-GAP-016) | at least one provider `status=SUCCESS` with `token_count>0` in a committed probe artifact | **OPEN** (blocked on laptop egress) |
| M-GAP-008 | 2026-08-18 (audit v2 carry-over) | 2 Data integrity | scoring calibration unvalidated on accumulated real observations | architecture/scoring | needs ≥ 8 weeks observation history | Month 3 roadmap gate (calibration harness) | engineer (Month 3) | calibration report on historical data | **OPEN** (measurement pending data accrual) — **2026-08-20:** Month-3 calibration surface completed in the canonical harness (`architecture/learning/calibration.py`, schema v3→v4): confidence-bucket segmentation (HIGH/MED/LOW + UNKNOWN bucket, ordering/inversion verdicts), chain segmentation, **provider segmentation (new — `source_provider` now stamped on every prediction at scoring time and persisted in the ledger with an idempotent additive migration; UNKNOWN bucket for legacy rows)**, continuous outcomes per band (mean/median max_favorable, mean max_adverse), Brier (normalized-score diagnostic, explicitly not a probability claim), ECE, Spearman rank (score vs hit, score vs max_favorable), evidence-coverage census, extreme-record provenance, honest dimension-availability (regime/opportunity-type NOT_PERSISTED_AT_PREDICTION_TIME — opportunity-type has no concept in the scoring contract and is not invented), outcome-provenance block (frozen Lane-A labeler identity), multi-horizon `run_many` + CLI `--all-horizons`, schema/guards intact. 21+4 new tests; runtime: CLI artifacts (honest INSUFFICIENT_DATA — 0 `local` pairs) + stamp path runtime-verified. Measurement itself still blocked on ≥ real evidence accrual. |
| M-GAP-014 | 2026-08-18 (Phase 11 audit) | 2 Data integrity | **outcome labels were never produced at runtime** — `discovery/materialize.py::materialize_outcomes` (frozen Lane-A labeler) was called only by tests and a manual CLI, never by the daemon. Predictions would accumulate indefinitely against zero labels, so the calibration join returned 0 pairs regardless of uptime: the chain was broken one link after the one Phase 10 fixed | `architecture/runtime/observation_loop.py` | `grep -rn compute_outcomes` showed no runtime caller | observation cycle now calls the frozen materializer after each poll; horizon-closure is still enforced inside Lane-A via `now`; labeling failure is reported in cycle details and never discards collected observations | — (fixed in-session) | a closed horizon produces labels during normal daemon operation | **CLOSED** |
| M-GAP-015 | 2026-08-18 (Phase 11 audit) | 2 Data integrity | **no synthetic/real evidence boundary** — every prediction row was equally eligible for calibration, so a sandbox run, a stray script or a test fixture pointed at the real store would silently become the evidence a calibration number was computed from | `architecture/learning/score_ledger.py`, `calibration.py` | seed a `test` row, run calibration → it was counted | rows are stamped `local\|sandbox\|test\|synthetic`; **only `local` is calibration-eligible**; default is `sandbox` (opt-in, never opt-out); pytest auto-detects to `test`; `source` is part of the `score_id` seed so a fixture cannot suppress a real row via INSERT OR IGNORE; contamination is reported as a headline finding | — (fixed in-session) | test/synthetic rows present in a store contribute 0 pairs and are named in `exclusion_reasons` | **CLOSED** |
| M-GAP-016 | 2026-08-18 (Phase 11 audit) | 6 Observability | **`--probe-providers` did not exist on the runtime entrypoint** although `AHOS_LOCAL_SOAK_PROTOCOL.md` and this register both instructed the operator to run it; the only probe (`system_state_snapshot.py`) covered 2 of 6 providers and reported raw exception class names | `architecture/providers/probe.py` | `python -m architecture.runtime --probe-providers` → unrecognized argument | real command implemented with 9 disjoint statuses (SUCCESS/EMPTY/TLS_ERROR/TIMEOUT/RATE_LIMIT/AUTH_REQUIRED/UNSUPPORTED/ERROR/UNKNOWN); a failure is never rounded up; security-only adapters report UNSUPPORTED instead of a reachability-implying EMPTY; writes a committed JSON artifact | — (fixed in-session) | operator has one command whose artifact settles M-GAP-007 | **CLOSED** (the *command*; the live success itself stays M-GAP-007) |
| M-GAP-013 | 2026-08-18 (post-release audit) | 2 Data integrity | **predictions were never persisted** — the scorer produced a full `OpportunityScoreReport` every cycle and discarded it on return; no table in any store held a score, so outcome labels (frozen Lane-A, already recorded) could never be joined to what the system predicted. The `Prediction` node of the learning loop was structurally MISSING and no calibration statement was computable at all | `architecture/learning/score_ledger.py`, `architecture/learning/calibration.py`, `architecture/pipeline/orchestrator.py` | `grep -rn opportunity_score --include=*.sql .` returned nothing before the fix | append-only `opportunity_score_ledger` (engine version + weights fingerprint + evidence sha + UNKNOWN accounting), written by the pipeline before any outcome is known; calibration harness joins predictions to frozen labels under a no-peeking rule with the project's pre-registered guards | — (implemented in-session) | a prediction survives the cycle that made it, and score-vs-outcome is computable from committed stores | **CLOSED** (infrastructure) — measurement itself stays INSUFFICIENT_DATA until real pairs accrue |
| M-GAP-009 | 2026-08-18 (audit v2 carry-over) | 1 Safety-adjacent (operational) | Telegram never run live (token rotation pending) — alerts unverified end-to-end | telegram_ai | needs real token | Month 4; user blocker ① | USER: token rotation | live transcript archived | **OPEN** (blocked on user) |
| M-GAP-010 | 2026-08-18 (audit v2 carry-over; drill 2026-08-18) | 4 Persistence | originally: no SQLite backup/rotation strategy on any host | `scripts/sqlite_backup_restore.py`, `tests/test_sqlite_backup_restore.py`, `reports/backup_restore_drill.json` | `python scripts/sqlite_backup_restore.py drill` (synthetic + 4 AHOS stores) | Online Backup API + restore verification (source/backup/restored sha256, row counts, `integrity_check`). **Phase 11:** `nightly` subcommand added — takes one verified night and appends to `reports/nightly_backup_series.json`, which counts **distinct UTC dates** (re-running in one evening still reads 1/7, so the series cannot be gamed) | residual: the operator must actually run it on 7 real days; fresh-host restore needs a second machine | tooling + regressions committed; `series_complete=true` requires 7 distinct days of real runs | **MITIGATED** (tooling ready; 7 nights + fresh-host restore = USER-ACTION-REQUIRED) |
| M-GAP-011 | 2026-08-18 (audit v2 carry-over) | 5 Provider reliability | missing adapters: CoinMarketCap, Launchpads; ChainExplorer has no keyless instance for bsc/avalanche/solana (honest UNSUPPORTED) | architecture/providers | import registry | Month 2 roadmap | engineer (Month 2) | adapters + live probe evidence | **OPEN** — **2026-08-20 progress:** CoinMarketCap adapter IMPLEMENTED (inert-until-configured per DEXTools pattern; NO_KEY/AUTH_REQUIRED/RATE_LIMIT/DOWN distinction; discovery UNSUPPORTED; liquidity UNKNOWN; platform-slug matching) + 20 offline tests (`tests/test_coinmarketcap_adapter.py`); registered in `ProviderRouter` + `--probe-providers` map; `.env.example` key slot. Wired into the unified `ProviderCollector` (last in `MARKET_PROVIDER_ORDER`: with a key it fills only UNKNOWN fields; without a key it reports NO_KEY and never emits traffic). Launchpad adapter (pump.fun, keyless Solana discovery feed) IMPLEMENTED + 11 offline tests (`tests/test_pumpfun_adapter.py`); registered in `ProviderRouter` + `--probe-providers`. Live probe evidence still pending host egress (M-GAP-007). Rate/breaker sync with frozen PAL registry CLOSED via `tests/test_provider_yaml_sync.py` + alignment (adapters ≤ PAL rpm; collector breakers ≥ PAL cooldown, ≤ PAL threshold). |
| M-GAP-012 | 2026-08-18 (audit v2 carry-over) | 6 Observability | watchdog is local-only | local watchdog is the **designed** surface for laptop operation | n/a | off-box alerting is **optional**, not an acceptance item | none | local `watchdog --status` during soak | **OPTIONAL** (local architecture) |

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
| Command-run artifacts (command + UTC + SHA + exit) | `reports/validate_imports_run.json`, `reports/pytest_run.json` |
| Score ledger + calibration harness + regressions | `architecture/learning/`, `tests/test_score_ledger_calibration.py` (19) |
| CoinMarketCap adapter (M-GAP-011) + offline tests | `architecture/providers/coinmarketcap.py`, `tests/test_coinmarketcap_adapter.py` (20) |
| Pump.fun launchpad adapter (M-GAP-011) + offline tests | `architecture/providers/pumpfun.py`, `tests/test_pumpfun_adapter.py` (11) |
| PAL rate/breaker sync law (Month 2) + alignment | `tests/test_provider_yaml_sync.py`, `architecture/collector/engine.py::PAL_BREAKER_CONFIGS` |
| Calibration report (honest INSUFFICIENT_DATA on current data) | `reports/calibration_*.json` |
| Month-3 calibration surface (v3): confidence/chain segments, Brier/ECE/Spearman, multi-horizon | `architecture/learning/calibration.py`, `tests/test_calibration_extended.py` (21) |
| System state snapshot (Phase 8) | `reports/system_state_snapshot.json` |
| Reliability challenge (Phase 8) | `reports/reliability_matrix.json`, `reports/reliability_matrix_*.json` |
| Local laptop soak contract | `AHOS_LOCAL_SOAK_PROTOCOL.md` |
| Local production gate | `AHOS_LOCAL_PRODUCTION_GATE_REPORT.md` |

A PASS/GREEN verdict in this register is allowed only when one of the rows above is the
evidence link. Markdown prose without an artifact is not evidence.

### Runtime observation (happened in a session; not repository evidence unless snapshotted)

- Sandbox soak daemon cycles described in `AHOS_MONTH1_OPERATIONAL_GATE.md` (hours, not days).
- Live TLS-blocked provider failures that motivated M-GAP-002 (only the table + tests + soak
  snapshot counts are committed; the daemon log itself is not in git).
- Any pytest/validate count written only in a narrative report and not in `reports/*_run_*.json`.

### Unproven (must not be labeled PASS)

- 168 consecutive hours on the **laptop** with sleep prevented (`AHOS_LOCAL_SOAK_PROTOCOL.md`) — M-GAP-003.
- Provider **success** path on the laptop (`--probe-providers` OK + tokens>0) — M-GAP-007.
- Repeated local nightly backups during that window — M-GAP-010 residual.
- Live Telegram (M-GAP-009), scoring calibration (M-GAP-008).
- **Scoring calibration itself.** M-GAP-013 closed the *infrastructure* hole (predictions
  are now persisted and joinable). It did NOT calibrate anything: the current report is
  `INSUFFICIENT_DATA` with 0 prediction/outcome pairs, because provider egress is blocked
  here and no cohort has accrued. "The harness exists" must never be restated as
  "the score is validated".
- GitHub Actions (M-GAP-004) and off-box watchdog (M-GAP-012) are **optional**, not local-production blockers.
- Deliberate recovery events on the laptop (local protocol §7).
- Any readiness percentage or “production ready / READY_FOR_DEPLOYMENT” sentence in older reports.

---

## Remaining-gap classification (2026-08-20 — after W32 provider expansion + W33 calibration surface)

Classification alphabet: **IMPLEMENTABLE NOW** · **REQUIRES USER ACTION** ·
**REQUIRES EXTERNAL SERVICE** · **REQUIRES CREDENTIAL** ·
**INTENTIONALLY BLOCKED** (governance/safety) · **CLOSED/MITIGATED** (evidence-linked).

| Gap | Classification | What unblocks it |
|---|---|---|
| M-GAP-003 (168h soak) | REQUIRES USER ACTION | laptop/VPS daemon + `AHOS_LOCAL_SOAK_PROTOCOL.md` for 7 real days; snapshots every 6h |
| M-GAP-004 (CI) | REQUIRES EXTERNAL SERVICE | GitHub App `workflows` permission; workflow drafted (untracked `.github/workflows/ci.yml`), ready to commit |
| M-GAP-005 (SQLite WAL) | INTENTIONALLY BLOCKED (post-soak reviewed change) | monitoring exists in soak snapshots (integrity_check per snapshot); WAL switch only after gate review |
| M-GAP-006 (drift vs NTP) | MITIGATED | documented limitation; host OS time sync (user-side) |
| M-GAP-007 (live egress) | REQUIRES USER ACTION | `python -m architecture.runtime --probe-providers` on the laptop → SUCCESS + tokens>0 |
| M-GAP-008 (calibration measurement) | REQUIRES USER ACTION (data accrual) | harness surface IMPLEMENTED (W33); run the laptop daemon with `AHOS_EVIDENCE_SOURCE=local`, then `scripts/calibration_report.py` |
| M-GAP-009 (live Telegram) | REQUIRES CREDENTIAL | BotFather token rotation + admin chat id (user blocker ①) |
| M-GAP-010 (7-night backups) | REQUIRES USER ACTION | 7 distinct nightly `scripts/sqlite_backup_restore.py nightly` runs |
| M-GAP-011 (CMC + launchpads) | CLOSED (adapters) → live probe REQUIRES USER ACTION | adapters implemented + 31 offline tests; live probe rides on M-GAP-007 |
| M-GAP-012 (off-box watchdog) | OPTIONAL (by design) | not an acceptance item for local-laptop operation |

No remaining gap is IMPLEMENTABLE NOW without user action, credentials,
external permission, or data accrual. Next engineering surfaces (Month 3–5:
weight governance via the existing `improvement_proposal_v1` flow, narrative
feed-through, learning engine) are sequenced behind calibration measurement
evidence per ROADMAP_v3.
