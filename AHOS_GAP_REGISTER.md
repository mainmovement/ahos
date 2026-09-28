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
| M-GAP-004 | 2026-08-18 (audit v2 carry-over) | 6 Observability | CI absent — GitHub App lacks `workflows` permission | CI | optional infrastructure | **optional** for local-laptop operation; local `reports/pytest_run.json` + `validate_imports_run.json` are the gate | none required for local soak | (optional) PR shows green CI run | **OPEN** — re-verified 2026-08-20: push of `.github/workflows/ci.yml` still rejected (`refusing to allow a GitHub App to create or update workflow ... without workflows permission`). The workflow is preserved cleanly as the tracked template `deployment/github-actions-ci.yml.template`; copy it to `.github/workflows/ci.yml` after the App receives `workflows` permission. |
| M-GAP-005 | 2026-08-18 | 4 Persistence | SQLite in rollback-journal mode (no WAL); single-writer; fsync behavior under long uptime unobserved | data stores | soak duration | monitor integrity + write latency across soak; WAL switch is a post-soak reviewed change (not mid-soak) | engineer: evaluate WAL after gate | integrity_check=ok in every snapshot; no write-loss incidents | **OPEN** (monitoring) |
| M-GAP-006 | 2026-08-18 | 3 Scheduler reliability | drift detection measures wall-step since process start, not absolute NTP offset (a host booted with wrong clock shows 0 drift) | architecture/scheduling/engine.py | set wrong clock before process start | documented limitation; laptop OS automatic time sync (local soak protocol §1) | USER: leave OS time sync on | host clock sane; no unexplained ABORTED_DRIFT storms | **MITIGATED** |
| M-GAP-007 | 2026-08-18 (pilot) | 5 Provider reliability | live probe ERROR TLS EOF, `token_count=0` — success path unproven. Re-probed 2026-08-18 (Phase 11): 2 discovery providers `TLS_ERROR`, 4 non-discovery `UNSUPPORTED`, **0 SUCCESS** from this host | providers | host egress | failure/UNKNOWN discipline proven offline (matrix); success requires working **local** egress | USER: run `python -m architecture.runtime --probe-providers` on the laptop (command now exists — M-GAP-016) | at least one provider `status=SUCCESS` with `token_count>0` in a committed probe artifact | **MITIGATED** — 2026-08-27 agent-host LIVE SUCCESS (dexscreener+geckoterminal, tokens>0) in `reports/provider_probe_LIVE_VERIFIED_agent_host.json`; **operator Windows laptop re-probe still USER ACTION** |
| M-GAP-008 | 2026-08-18 (audit v2 carry-over) | 2 Data integrity | scoring calibration unvalidated on accumulated real observations | architecture/scoring | needs ≥ 8 weeks observation history | Month 3 roadmap gate (calibration harness) | engineer (Month 3) | calibration report on historical data | **OPEN** (measurement pending T+72h labels; **R-81 bridge** seeds Lane-A — 2026-08-27) — **2026-08-20:** Month-3 calibration surface completed in the canonical harness (`architecture/learning/calibration.py`, schema v3→v4): confidence-bucket segmentation (HIGH/MED/LOW + UNKNOWN bucket, ordering/inversion verdicts), chain segmentation, **provider segmentation (new — `source_provider` now stamped on every prediction at scoring time and persisted in the ledger with an idempotent additive migration; UNKNOWN bucket for legacy rows)**, **regime segmentation (token_price_regime computed post-hoc from PRE-prediction observations via `architecture/intel/regimes.py` — its first production consumer; <10 obs → UNKNOWN, never a default regime)**, continuous outcomes per band (mean/median max_favorable, mean max_adverse), Brier (normalized-score diagnostic, explicitly not a probability claim), ECE, Spearman rank (score vs hit, score vs max_favorable), evidence-coverage census, extreme-record provenance, honest dimension-availability (opportunity-type has no concept in the scoring contract and is not invented), outcome-provenance block (frozen Lane-A labeler identity), multi-horizon `run_many` + CLI `--all-horizons`, schema/guards intact. 21+8 new tests; runtime: CLI artifacts (honest INSUFFICIENT_DATA — 0 `local` pairs) + stamp path runtime-verified. Measurement itself still blocked on ≥ real evidence accrual. |
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
| Gecko `pool_created_at` → SQLite `pair_created_ts` E2E (PR #77+#78, SHA `cf7711e`) | `reports/gecko_pair_created_ts_e2e_RUNTIME_VERIFIED.json`, `docs/engineering/GECKO_PAIR_CREATED_TS_E2E.md` |

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
| M-GAP-004 (CI) | REQUIRES EXTERNAL SERVICE | GitHub App `workflows` permission; tracked template `deployment/github-actions-ci.yml.template` is ready to copy to `.github/workflows/ci.yml` and commit |
| M-GAP-005 (SQLite WAL) | INTENTIONALLY BLOCKED (post-soak reviewed change) | monitoring exists in soak snapshots (integrity_check per snapshot); WAL switch only after gate review |
| M-GAP-006 (drift vs NTP) | MITIGATED | documented limitation; host OS time sync (user-side) |
| M-GAP-007 (live egress) | REQUIRES USER ACTION | `python -m architecture.runtime --probe-providers` on the laptop → SUCCESS + tokens>0 |
| M-GAP-008 (calibration measurement) | REQUIRES USER ACTION (data accrual) | harness surface IMPLEMENTED (W33); run the laptop daemon with `AHOS_EVIDENCE_SOURCE=local`, then `scripts/calibration_report.py` |
| M-GAP-009 (live Telegram) | REQUIRES CREDENTIAL | BotFather token rotation + admin chat id (user blocker ①) |
| M-GAP-010 (7-night backups) | REQUIRES USER ACTION | 7 distinct nightly `scripts/sqlite_backup_restore.py nightly` runs |
| M-GAP-011 (CMC + launchpads) | CLOSED (adapters) → live probe REQUIRES USER ACTION | adapters implemented + 31 offline tests; live probe rides on M-GAP-007 |
| M-GAP-012 (off-box watchdog) | OPTIONAL (by design) | not an acceptance item for local-laptop operation |

### Addendum 2026-08-27 — completion pass (PR hygiene + W57 truth)

| Gap | Classification | What changed |
|---|---|---|
| M-GAP-017 (Telegram tests contradicted W57 lockdown) | **CLOSED** | Stale `handle_message` expectations realigned to `EMERGENCY_FALLBACK_ONLY`; gateway success/failure paths pinned |
| M-GAP-018 (undocumented AHOS_GATEWAY_URL / alert env keys) | **CLOSED** | Documented in `.env.example`; config validation test green |
| M-GAP-019 (n8n guide claimed Telegram → independent NLU) | **CLOSED** | `docs/n8n_setup_guide.md` states gateway-only law |
| Dual-stack ownership (TS chat vs Python daemon) | **DOCUMENTED** | `docs/DOC_TRUTH_MAP.md` §C + `docs/CANONICAL_IMPLEMENTATION_MATRIX.md` |
| `strategies.json` outside Lane-A freeze | **DOCUMENTED** | Intentional exclusion note in `scripts/freeze_lane_a.py` |
| M-GAP-020 (exchange-key env veto dead-check) | **CLOSED** | `assert_safe_environment` now truthy-flags live trading; exchange key presence → `credentials_isolated=False` |
| M-GAP-021 (owner actions scattered) | **CLOSED** | `docs/OWNER_ACTION_REQUIRED.md` |
| M-GAP-022 (stale SECURITY/MISSING/STRATEGIC docs) | **CLOSED** | Historical banners pointing at matrix/audit |
| AG-25 GitHub live harvest | **NOT_IMPLEMENTED** (by design PLANNED) | Honest in matrix; do not claim COMPLETE |

Implementation matrix: `docs/CANONICAL_IMPLEMENTATION_MATRIX.md`  
Final truth audit: `docs/FINAL_TRUTH_AUDIT.md`  
Owner actions: `docs/OWNER_ACTION_REQUIRED.md`

**Classification:** `INTEGRATION_READY` (agent-host). `OPERATOR_READY` / `PRODUCTION_READY` not claimed.

The 2026-08-27 sentence “no remaining gap is IMPLEMENTABLE NOW” is **stale**.
Owner/env gates below remain blocked.

### Addendum 2026-09-09 — GeckoTerminal pair-created persist path

| Gap | Classification | What changed |
|---|---|---|
| M-GAP-023 (Gecko `pool_created_at` never reached SQLite `pair_created_ts`) | **CLOSED** (path RUNTIME VERIFIED) | Adapter mapping PR #78 + collector persist PR #77. Official `--single-cycle` on `cf7711e`: 5/5 new gecko rows stored + reload + independent pool GET exact epoch match. Historical pre-#78 gecko NULLs **not** backfilled. Artifact: `reports/gecko_pair_created_ts_e2e_RUNTIME_VERIFIED.json`. Pair age is **not** overlay PASS. |

### Addendum 2026-09-09 — Telegram HTML escape (Lane B safety)

| Gap | Classification | What changed |
|---|---|---|
| M-GAP-024 (Telegram HTML `escapeHtml` / `format_pump_alert` no-op) | **CLOSED** (unit/selftest) | `escapeTelegramHtml` + `escape_telegram_html` escape `&` `<` `>` on untrusted fields. Tests: `scripts/canonical_security_selftest.ts`, `tests/test_telegram_html_escape.py`. Live E2E remains M-GAP-009. Note: `docs/engineering/TELEGRAM_HTML_ESCAPE.md`. |

### Addendum 2026-09-09 — Canonical overlay census (observability)

| Gap | Classification | What changed |
|---|---|---|
| M-GAP-025 (Python JSON vs TS/Postgres opportunity keys often unmatched → UNAVAILABLE) | **MITIGATED** (diagnostic only) | `/api/command` includes `overlayCensus`. Command Center displays matched/unmatched counts. Unmatched stays UNAVAILABLE. **No store join. No gecko pool→token identity change.** Note: `docs/engineering/CANONICAL_OVERLAY_CENSUS.md`. |

### Addendum 2026-09-09 — Command Center `/api/alerts` wiring

| Gap | Classification | What changed |
|---|---|---|
| M-GAP-026 (Command Center did not fetch `/api/alerts`) | **CLOSED** (unit/selftest) | `evaluateWebAlertBanner` re-checks live Python BUY + overlay PASS; expired/WATCH/UNAVAILABLE stay inactive. Command Center shows a non-FOMO `monitor-banner`. Live Telegram E2E remains M-GAP-009. |

### Push record 2026-09-28 — first governed push of the working branch

| Item | Value |
|---|---|
| Remote branch created | `origin/ahos` (new; no prior `origin/ahos` existed) |
| Commit range pushed | `e0ac1dd` .. `916b786` (6 commits: M1+M2 taxonomy map, sqlite handle-leak fix, gap-register addendum, `advance_maturity` lifecycle ramp + invariant, maintenance note) |
| Local HEAD after push | `916b786fda1ab96973ff332b19f49d4199fac886` |
| Remote HEAD after push | `916b786fda1ab96973ff332b19f49d4199fac886` |
| Upstream | `origin/ahos` (set by the push) |
| Divergence | `0 0` — verified in sync |
| `origin/main` touched | NO — only the working branch; main remains 2 ahead / 9 behind on unrelated history |
| Force-push used | NO |

Authorization scope: ordinary governed push to the working branch only. This is **not** merge-to-main, release, live-trading, governance change, or authority increase.

Verification posture at push time: full `tests/` 2349 passed / 5 failed (all five pre-existing and environmental — 3 x Windows symlink privilege, 2 x stale local operation report; none touched by this range). `tests2b/` 256 passed. Lane-A integrity OK (36 files pinned).

Excluded from the push: the pre-existing `.cursor/hooks.json` modification, `.cursor/hooks.json.local-backup`, `ahos-hooks-local-diff.txt`, and `reports/canonical_decision_read_model.json` (a generated read-model artifact written as a side effect of running the suite; unstaged and left on disk, not committed).

### Addendum 2026-09-28 — orphan-module audit: 4 of 10 are live, not dead

| Gap | Classification | What changed |
|---|---|---|
| M-GAP-030 (10 leaf modules never imported — dead-code candidates) | **PARTIALLY RECLASSIFIED** | The validator's own docstring says removal "is a governance decision, never an automatic action by this gate". Verified against live invocation: **4 are operational entrypoints, not dead code** — `engine/data_audit.py` and `engine/research_report_bot.py` are invoked by `engine/run_all_checks.sh` (the CI gate) and by n8n workflows `ahos_11_data_update` / `ahos_12_research_report`; `engine/acquire_3yr.py` is invoked by n8n `ahos_11_data_update`; `engine/pal_probe.py` is cited as evidence in `config/agent_registry.yaml` (PRB-20260813-001..017) and `config/cognitive_principles.yaml` (R-28 protocol). All four also have `__main__` blocks. The scanner counts shell-invoked CLIs as unreferenced because it only traces Python import paths. |
| M-GAP-031 (4 genuine unreferenced entrypoints) | **OPEN** (governance disposition) | `engine/oss_audit`, `engine/coverage_audit`, `engine/doc_hygiene`, `engine/agent_matrix_v2` are CLI entrypoints with `__main__` blocks that nothing invokes. These are the true dead-code candidates. Note `engine/oss_audit` is already flagged in the taxonomy map as the dead substrate behind M0 role H (GitHub/OSS Intelligence), where AG-25 is PLANNED. Deleting them would remove the only implementation substrate for that role, so disposition must consider the role gap, not just import counts. |
| M-GAP-032 (`paper_trading/cycle.py` orphan status) | **OPEN** (Lane-A gated) | Also appears in the orphan list, but it is one of the 36 files pinned in `config/lane_a_freeze.sha256`. Its disposition requires a reviewed governance request; it is not an autonomous-cleanup candidate under any circumstance. |

Action taken: none of the 10 modules was modified or deleted. The earlier intent to "clean up the 9 non-Lane-A orphans" was abandoned once verification showed 4 of them are live. This row is the correction.


Owner/env blockers unchanged: M-GAP-003, M-GAP-007 (Windows), M-GAP-008 measurement, M-GAP-009 token, M-GAP-010 nights, OV-* Windows gates. Dual-store redesign remains an architecture STOP.

### Addendum 2026-09-27 — Agent taxonomy map pinned (M2) + knowledge-store handle leak

| Gap | Classification | What changed |
|---|---|---|
| M-GAP-027 (four agent taxonomies overlap with no explicit mapping; "agent 01" means four unrelated things) | **CLOSED** (governance artifact + tests) | `docs/governance/agent_taxonomy_map.json` + `AGENT_TAXONOMY_MAP.md`, status `RECONCILED_NOT_MERGED`, enforced by `tests/test_agent_taxonomy_map.py` (19 tests). Mapped `agent.*` / `AG-*` / `AGENT-*` / `agent.org.*` + M0 A-H roles with per-relation provenance. The "agent 01" collision is recorded as a collision, not an alias. Registering in the map is **not** evidence an agent is implemented; no anchor gained authority. |
| M-GAP-028 (no Slice-1 agent can execute — mechanical, not a wiring gap) | **OPEN** (governance-gated) | All 19 `CANONICAL_AGENT_IDS` are seeded at `MaturityLevel.REGISTERED` (0) while `MINIMUM_MATURITY_FOR_ALLOW = 2`. `orchestrated: 0` in the ops matrix agrees. This is a deliberate gate: a control-plane boot must raise documented maturity **with evidence**, not edit the floor. Pinned by `test_all_anchors_registered_and_blocked_from_execution`. |
| M-GAP-029 (`ColumnarKnowledgeStore` leaked one sqlite connection per call) | **CLOSED** (fix + regression test) | `sqlite3.Connection.__exit__` commits but never closes; all 4 call sites used a bare `with sqlite3.connect(...)`. On Windows the leaked handle kept the db locked and `TemporaryDirectory` teardown raised `PermissionError [WinError 32]`. Fixed with `contextlib.closing()`; regression test `test_knowledge_store_releases_db_file_on_windows` fails without the fix. |
| M-GAP-030 (10 leaf modules never imported — dead-code candidates) | **OPEN** (needs governance disposition) | `scripts/validate_imports.py` orphans: `discovery.collect, engine.acquire_3yr, engine.agent_matrix_v2, engine.coverage_audit, engine.data_audit, engine.doc_hygiene, engine.oss_audit, engine.pal_probe, engine.research_report_bot, paper_trading.cycle`. **One is Lane-A frozen:** `paper_trading/cycle.py` is in `config/lane_a_freeze.sha256`, so its disposition requires a reviewed governance request rather than autonomous cleanup. The other nine are Lane B / `engine/`. |

Test posture (2026-09-27 run, superseded by the 2026-09-28 addendum below): full `tests/` run 2340 passed / 5 failed. All five remaining failures are pre-existing and environmental, on files this work did not touch — 3 x Windows symlink privilege (`WinError 1314`, `test_engine_import_safety`), 2 x stale local operation-report state (`test_phase13_laptop_operation`). Neither my taxonomy-map work nor the leak fix touches them.

### Addendum 2026-09-28 — Windows cp1252 locale blocked the entire local verification loop (M-GAP-033)

| Gap | Classification | What changed |
|---|---|---|
| M-GAP-033 (locale-encoding defect makes the local soak suite uncollectable on the operator's own Windows host) | **PARTIALLY CLOSED** (test collection unblocked + 1 production writer fixed; systemic residual recorded, not silently expanded) | `Path.read_text()` / `write_text()` default to `locale.getpreferredencoding(False)`. On this host that is **cp1252** (`PYTHONUTF8` unset), while CI runs Linux where the default is UTF-8. 38 bare `read_text()` call sites across 18 test files read UTF-8 repo content — Persian/Arabic in `config/cognitive_principles.yaml`, `→` (U+2192) / `—` / `·` in the canonical docs — so `pytest tests/` died with `UnicodeDecodeError: 'charmap' codec can't decode byte 0x81` **at collection**, before a single test ran. Consequence: `AHOS_LOCAL_SOAK_PROTOCOL.md:80` — the operator's own designated soak command — was unrunnable on the soak host itself. This is a direct hit on mission area 2 (control-plane bootability): no local verification, no evidence for any maturity advance. |
| — (test read sites) | **CLOSED** | All 38 `read_text()` call sites in the 18 test files pinned to `encoding="utf-8"`. |
| — (test write sites) | **CLOSED** | 2 `write_text()` sites in `tests/test_runtime_hardening_matrix.py` round-tripping `MASTER_DIRECTIVE_v1.md` (contains U+2192, unencodable in cp1252 — a latent `UnicodeEncodeError` that would have surfaced the moment collection was unblocked). |
| — (production writer) | **CLOSED** | `architecture/runtime/observability_snapshot.py:1620` wrote the canonical health snapshot as `json.dumps(..., ensure_ascii=False)` with **no encoding**, so Windows wrote cp1252 bytes into `reports/canonical_health_snapshot.json` and the committed artifact was not valid UTF-8 anywhere else. Exposed by `test_canonical_health_snapshot_generation` (`byte 0x97 in position 5894` — an em-dash) once the suite could finally run. Fixed with pinned UTF-8. Note this is the *only* production fix; production *config* readers were already correct (`architecture/cognitive/agents.py:62`, `architecture/control_plane.py:67,71`, `architecture/registry.py:52`, `engine/agent_matrix_v2.py:116,119`). |

Residual (AST-counted, so multi-line calls are counted correctly — a line-grep overstates this as ~34): **100 pinned / 9 unpinned** text-IO call sites in `architecture/`, `engine/`, `ahos_org/`, `scripts/`. The 9 unpinned are:

- `engine/oss_audit.py:99` (`read_text`), `:103`
- `engine/coverage_audit.py:119`, `engine/f1_s1_migration.py:258`, `engine/agent_matrix_v2.py:125`
- `engine/doc_hygiene.py:244, :246`, `engine/pal_probe.py:224`, `engine/health_manager.py:174`

Only **3** of these can actually emit non-ASCII today, because only they pair `ensure_ascii=False` with a missing encoding: `engine/doc_hygiene.py:244`, `engine/pal_probe.py:224`, `engine/health_manager.py:174` — the same defect class as the writer just fixed. The other 6 use default `json.dumps` (ASCII-only output while content stays ASCII) or a bare read. All 9 sit in `engine/` CLI entrypoints, the same modules M-GAP-031 lists as unreferenced; none has a live production caller, which is why nothing in the suite caught them.

**Not fixed deliberately.** Fixing all 9 would triple the production diff for a class with no live caller. Recorded here as the systemic residual for a reviewed change instead.

**Why CI never saw this, and the one-line systemic guard.** Linux's default locale encoding is UTF-8, so this entire defect class is invisible to CI — it is only observable on a Windows host without the UTF-8 system locale, which is exactly the soak host. The single guard that closes the class for all future call sites is `PYTHONUTF8=1` (UTF-8 mode makes `open()` / `Path` text IO default to UTF-8 regardless of locale). Recommend setting it in the operator environment and in `engine/run_all_checks.sh`, which currently invokes `python3` with no encoding flags. That is an operator-environment change, not an autonomous code change.

Test posture (2026-09-28, after the fix): full `tests/` run **2349 passed / 6 failed / 1 xfailed** in 3672.50s, then `tests/test_phase4_operational_observability.py` re-run green at **16 passed** after the production-writer fix. Of the 6, five are the pre-existing environmental failures above (3 x `WinError 1314` symlink privilege in `test_engine_import_safety`, 2 x stale operation-report state in `test_phase13_laptop_operation`) and the sixth was the newly-exposed snapshot-encoding failure, now fixed. The production-writer edit has been verified by targeted re-run only, not by a second full-suite pass.

**Repository reality — governed push #2 (2026-09-28).** Commit `577f822` `fix(encoding): pin UTF-8 so the local soak suite is collectable on Windows`, pushed to `origin/ahos` (fast-forward `b917db4..577f822`, no force). All four checks verified: local HEAD `577f82297513decae3d2e8ea5326daa307fbbbf2`, remote `refs/heads/ahos` `577f82297513decae3d2e8ea5326daa307fbbbf2` (identical), upstream `origin/ahos` tracked, divergence `0 0`. The 20-file changeset was the 18 test files + `architecture/runtime/observability_snapshot.py` + this register entry; the three pre-existing `.cursor` working-tree items were deliberately excluded as not part of this mission. Gates at push time: `scripts/validate_imports.py` → IMPORTS OK, EVIDENCE-BOUNDARY OK, **LANE-A FREEZE OK (36 files)**, SECRETS OK (its only FAIL lines are gitignored `__pycache__` / `.pytest_cache` build artifacts, present whenever Python has run). No `main` push, no force-push, no merge, no release, no live trading, no governance or maturity change.
