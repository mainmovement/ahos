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

### Addendum 2026-09-28 (2) — soak-evidence recorder would have recorded a spurious FAIL (M-GAP-034)

| Gap | Classification | What changed |
|---|---|---|
| M-GAP-034 (soak pre-registration records the wrong verdict for the full suite) | **CLOSED** (fix + regression test + doc) | `scripts/record_test_run.py` defaulted `--timeout` to 1800s, but `AHOS_LOCAL_SOAK_PROTOCOL.md:81` instructs the operator to record `pytest tests/ -q` as pre-soak evidence, and that suite runs **3672s** (measured this session). Following the protocol verbatim would kill the run at the halfway mark and persist `timed_out: true, verdict: FAIL` — the wrong evidence shape to enter a 168h soak with. The default now resolves by command class: 7200s for pytest-class commands, 1800s otherwise, reusing the same `"pytest" in joined` predicate `default_out_path` already used. `--timeout` still overrides. Regression test `test_record_test_run_default_timeout_scales_for_pytest`; CLI smoke-tested end to end (it also correctly records `working_tree_clean: false` when the tree is dirty). |
| — (why it was hidden) | note | This defect was unreachable before M-GAP-033: the suite died at collection, so it never ran long enough to hit the timeout. Fixing the encoding defect exposed it. Two defects in the same local-evidence path, found in sequence — which is the reason the soak host is now the highest-yield place to look. |

**Repository reality — governed push #3 (2026-09-28).** Fast-forward `577f822..36fd9a7` → `origin/ahos`, no force. Two commits: `3020382` (this reality-map entry for push #2) and `36fd9a7` `fix(evidence): scale the recorder's default timeout for pytest-class commands`. All four checks verified: local HEAD `36fd9a739c33bf7b1d29fa16b5113d120f5253d2`, remote `refs/heads/ahos` identical, upstream `origin/ahos` tracked, divergence `0 0`. Changeset was `scripts/record_test_run.py` + `tests/test_sqlite_backup_restore.py` + the soak-protocol note; the three `.cursor` working-tree items again excluded. Gates: IMPORTS OK, EVIDENCE-BOUNDARY OK, **LANE-A FREEZE OK (36 files)**, SECRETS OK. No `main` push, no force-push, no merge, no release, no live trading, no governance or maturity change.

### Addendum 2026-09-28 (3) — three control-plane surfaces, two of them test-only (M-GAP-035)

| Gap | Classification | What changed |
|---|---|---|
| M-GAP-035 (the production daemon consults no control plane at all; two candidate planes are test-only) | **OPEN** (architecture finding, reframes area 2) | Import-graph verification, not a code change. The repository has three control-plane-ish surfaces and only one is live: (1) `architecture/runtime/` — the production daemon, **live**, imported by `deployment/healthcheck.py`, `scripts/init_databases.py`, `scripts/local_activation_report.py`, `scripts/month1_failure_matrix.py`; (2) `architecture/control_plane.py` — the W11 START/STOP/STATUS/SAFE_HALT/RESUME engine with the `orchestrated` gate at `:228-230`, **no non-test importer** (referenced only by `tests/test_control_plane_soak.py` and `tests/test_runtime_w11.py`); (3) `ahos_org/` — the maturity + `GovernanceEngine.authorize` plane, **imported only by itself** (`governance ↔ registry ↔ organization`), zero external importers. The daemon `architecture/runtime/__main__.py` imports **neither** (2) nor (3): it wires lifecycle, observation loop, collector, score ledger, scheduler, pipeline orchestrator, and telegram — and `grep ahos_org architecture/runtime/` returns nothing. |
| — (why this matters) | note | The taxonomy map already records `orchestrated: 0` for every agent and "No orchestrator runtime exists (orchestrated=0/25)" (`docs/governance/agent_taxonomy_map.json:32-33,143`), and `control_plane.py:230` already says `"implemented but orchestrated=false (not wired to runtime yet)"`. So the fact is documented; **the new part is the count and the disjointness.** M-GAP-028's maturity gate is necessary but not sufficient: even if all 19 anchors were advanced to `IMPLEMENTED`, no production call site would consult them, because none exists. Bootability is a wiring gap *behind* a maturity gate, and the two candidate planes do not reference each other either (`control_plane.py` reads `config/agent_registry.yaml` and `config/control_plane.yaml`; it does not import `ahos_org`). |
| — (why the orphan scanner missed it) | note | `scripts/validate_imports.py` counts a test import as a reference, so `control_plane.py` is "referenced" and never appeared in the M-GAP-030/M-GAP-031 orphan list. Its 10 orphans are modules with **no** importer of any kind. `control_plane.py` has no *production* importer — a different and sharper condition the scanner does not distinguish. Worth noting for the scanner's own taxonomy: "no importer at all" and "no production importer" are different dispositions. |
| — (what is NOT concluded) | note | This is not evidence that either test-only plane is broken or should be deleted. Both have substantial test coverage (W11 soak tests, 19 taxonomy-map tests, the maturity-gate test). It is evidence that the wiring step between them and the daemon has not been written, and that picking which plane is canonical is an architecture decision, not an autonomous one. |

Action taken: none. No file was modified or deleted. Recorded because it changes the priority order of the six mission areas: area 2 (control-plane bootability) has a concrete, evidence-producing next step that requires no owner input — but it is a *wiring* task, not a maturity task, and the choice of which plane to wire should be reviewed before code is written.

### Addendum 2026-09-28 (4) — the soak pre-registration gate is unpassable on a warm host (M-GAP-036, M-GAP-037)

Third and fourth defects found in the same local-evidence pipeline, again all invisible to Linux CI. Theme: the soak evidence path was written against a clean Linux checkout and never exercised on the warm Windows soak host, because until M-GAP-033 the suite could not even be collected there.

| Gap | Classification | What changed |
|---|---|---|
| M-GAP-036 (recorder could not launch the documented relative-path command on Windows) | **CLOSED** (fix + 2 regression tests) | `scripts/record_test_run.py` spawned the child with `cwd=ROOT` but a *relative* executable. Windows `CreateProcess` does not search the `cwd=` parameter for the executable, so the exact form the soak protocol and `AHOS_WINDOWS_OPERATOR_RUNBOOK.md:64` document — `.venv/Scripts/python.exe …` — died with `FileNotFoundError: [WinError 2]` and the recorder **crashed, recording nothing**. Reproduced in isolation: identical `subprocess.run` with a relative path fails, with an absolute path succeeds. Fixed by anchoring a path-containing first element against `ROOT` before spawning (bare names still go to PATH). The artifact now also carries `command_resolved` so what actually ran is transparent. `record_run` additionally catches `OSError` and records it as `exit_code: 127` with a `LAUNCH FAILED` stderr — an evidence recorder that crashes on a launch failure records no evidence at all. |
| M-GAP-037 (`validate_imports.py` fails on every warm host, so the soak pre-registration gate cannot pass) | **OPEN** (enforcing-control policy decision — deliberately NOT changed autonomously) | `AHOS_LOCAL_SOAK_PROTOCOL.md:79` lists `scripts/validate_imports.py` as a pre-soak gate, and line 81 asks for it to be recorded as evidence. Recorded it for real: **exit code 1, `verdict: FAIL`, 44 FAIL lines — every single one `build artifact present: __pycache__/…` or `.pytest_cache/`. Zero substantive violations.** These are gitignored (`git status` never lists them) and are produced by the unavoidable act of running Python. CI passes because it checks out a clean tree; the operator's own soak host cannot, because it has run Python. So the gate is unpassable in exactly the context it exists for. The correct semantics is "the *committed* tree must not contain artifacts" — which `git` already answers — rather than "the working tree must be artifact-free". **Not fixed:** `AGENTS.md` names `scripts/validate_imports.py` as an enforcing control and the safety section forbids weakening tests, so changing its artifact check needs human review. Candidate approaches, in order of how much they change the control: (a) ignore gitignored paths in the artifact scan; (b) add a flag such as `--allow-gitignored-artifacts` and have the soak protocol pass it; (c) leave the validator alone and restate the protocol to evaluate `validate_imports` on a fresh clone. (a) is the most principled; (c) is the smallest. |

Verified end to end after the fix: `record_test_run.py --out reports/validate_imports_run.json -- .venv/Scripts/python.exe scripts/validate_imports.py` ran in 71.5s at `e112d01` and produced a well-formed artifact with `command_resolved` anchored — the documented invocation now works on Windows. The resulting `reports/validate_imports_run.json` was deliberately **not** committed: it is a local pipeline probe whose `FAIL` verdict is entirely the M-GAP-037 artifact condition, and committing it without that context would read as a real validation failure.

**Follow-up — the same probe exposed an append-only violation, now mechanically prevented.** `--out reports/validate_imports_run.json` silently **overwrote a committed evidence receipt**: the artifact at that path is a 2026-08-20 Linux `PASS` run on `b039fb0`, and my probe replaced it with today's Windows `FAIL`. History was intact (the commit never staged it) and the working-tree file was restored via `git checkout HEAD --`, but the failure mode is real: `AGENTS.md` requires evidence receipts be recorded "without overwriting history" and the soak protocol commits `reports/` and says "never overwritten", yet the recorder's `--out` happily clobbered a tracked file. `default_out_path` already appends a UTC timestamp, so collisions only happen through an explicit `--out`. Fixed by making an existing target refuse with exit 3 unless `--force` is passed — the rule is now enforced by the tool rather than by operator care. Verified from the CLI against the real receipt: it refuses and the 2026-08-20 run survives. Two regression tests cover both branches.

**Repository reality — governed pushes #4 and #5 (2026-09-28).** Both fast-forwards to `origin/ahos`, no force.

- Push #4: `e112d01..77984ce` — `fix(evidence): anchor the recorder's relative executable so it launches on Windows` (M-GAP-036). Changeset `scripts/record_test_run.py` + `tests/test_sqlite_backup_restore.py` + this register.
- Push #5: `77984ce..e97ea90` — `fix(evidence): refuse to overwrite an existing artifact unless --force is passed`. Same two code files plus this register.

Final state, all four checks verified: local HEAD `e97ea903584545bbb6a6c828162d29d99c4511dd`, remote `refs/heads/ahos` identical, upstream `origin/ahos` tracked, divergence `0 0`. Working tree holds only the three pre-existing `.cursor` items (not mine, not committed) plus one deliberately untracked probe artifact `reports/validate_imports_run_20260928T045640Z.json` — uncommitted because its `FAIL` verdict is entirely the M-GAP-037 gitignored-artifact condition and would read as a real validation failure without that context. Gates across both: IMPORTS OK, EVIDENCE-BOUNDARY OK, **LANE-A FREEZE OK (36 files)**, SECRETS OK; `tests/test_sqlite_backup_restore.py` 10 passed. No `main` push, no force-push, no merge, no release, no live trading, no governance or maturity change.

**Session tally (2026-09-28):** 5 governed pushes, 4 defects found in the local soak-evidence pipeline. M-GAP-033 (collection blocked), M-GAP-034 (timeout), M-GAP-036 (Windows launch) are CLOSED with regression tests; M-GAP-037 (validator fails on every warm host) is OPEN as an enforcing-control policy decision. One structural finding, M-GAP-035 (three control-plane surfaces, two test-only, the daemon consults none), recorded without code change because the choice of which plane is canonical needs review. All four were unreachable before today: M-GAP-033 unblocked the suite, and the other three were behind it.

### Addendum 2026-09-28 (5) — role H substrate is live: first real OSS Tier-1 evidence (M-GAP-031 progress)

| Gap | Classification | What changed |
|---|---|---|
| M-GAP-031 (role-H substrate `engine/oss_audit` is an unreferenced orphan) | **PARTIALLY CLOSED** (substrate exercised for real) | M-GAP-035's reassessment ranked area 1 (Agent H / GitHub-OSS Intelligence) the most doable next action, and verification confirmed why: `engine/oss_audit.py` is unauthenticated public-metadata-only, needs **no credentials and no owner input**, and is fail-closed by design — RATE LAW (hard cap 20 repos, sleeps between calls), FAILURE LAW (API error → record `UNVERIFIED — <reason>`, nothing fabricated), TIER LAW (Tier-1 registers candidates only, never a final verdict), and PART O law (NO clone / install / execute). Ran it against a 10-repo candidate set spanning the lanes AHOS cares about: orchestration, replay, agent runtime, multi-agent, memory, evaluation, observability, metrics. **9/10 reached `T1_METADATA`.** |
| — (the honest failures) | evidence | `opentelemetry/opentelemetry-python` → `UNVERIFIED — API error: HTTP Error 404: Not Found` (the repo has since moved to `open-telemetry/`); `microsoft/autogen` → `T1_METADATA` but `STALE_OR_SLOW` (>30 days since push). Both are exactly what the tool is supposed to record, and both are decision-relevant: the 404 says the candidate list needs a refresh pass, and the stale flag says autogen should not be treated as actively maintained without Tier-2 evidence. |

Artifact committed: `reports/oss_capability_audit_20260928T051552Z.json` (probe_set `M0ROLEH-20260928`), 5599 bytes, zero non-ASCII bytes, valid UTF-8 and valid JSON. Committed deliberately, unlike the transient pytest/validator probes excluded from earlier commits — this is the actual mission artifact for role H, produced by running the tool M-GAP-031 identifies as that role's only substrate. Committing it is what converts an orphan from "unreferenced" to "exercised with evidence on record".

**What this does NOT do:** Tier-1 registers candidates only. It assigns no verdict, ranks nothing, and confers no authority on AG-25 — which remains `PLANNED`. Evidence that a public repo is active is not evidence that AHOS should adopt it; Tier-2/3 (host/owner-gated) are still required before any dependency decision. This is `UNKNOWN > fabricated` operating as designed: the 404 is recorded as UNKNOWN, not silently dropped or guessed.

**Ranked reassessment of the six areas** (by how much of the next action is doable now, without owner input or external credentials):

1. **Area 1 — Agent H / GitHub-OSS Intelligence.** Doable now, demonstrated above. Next step: a candidate-refresh pass (fix the `open-telemetry/` path, add lanes AHOS actually lacks) then Tier-1 sweeps at a cadence. No credentials.
2. **Area 2 — control-plane bootability.** Evidence pipeline fixed this session (M-GAP-033/034/036). The remaining step is *wiring* the daemon to one control plane (M-GAP-035) — blocked on an architecture decision about which plane is canonical, not on code ability.
3. **Area 5 — local dashboard.** `app/` is a real Next.js surface (`api/`, `layout.tsx`, `page.tsx`). Doable but needs a design decision about what the dashboard must show; no external blocker.
4. **Area 6 — n8n automation.** 6 workflows exist (`n8n/workflows/ahos_01..12`) plus `docs/n8n_setup_guide.md`. Migration depends on the external n8n instance, so it is owner/externally gated.
5. **Area 3 — skill discovery and acquisition.** `architecture/cognitive/` has the pieces (`capability.py`, `contracts.py`, `evaluation.py`, `novelty.py`, `evolution_gate.py`) but no skill-acquisition substrate. Needs design.
6. **Area 4 — ACI cognitive runtime.** Extensive `architecture/cognitive/` surface, but `AGENTS.md` forbids uncontrolled self-evolution and `evolution_gate.py` is the guardrail. Sensitive by construction; doable work is limited to gate-hardening and does not belong in an autonomous pass.

Separately flagged, not acted on: **137 of 1648 tracked files (8.3%) sit in four root directories that appear unrelated to AHOS** — `01/` (37), `advanced-3d-audiovisual-website/` (33), `advanced-3d-audiovisual-website (1)/` (60), `درخت کاملتر immersive-3d-audiovisual-website/` (7). They look like unrelated audiovisual-website projects committed into the repo root. Not deleted and not modified — the mission forbids deleting anything classified as orphan without live-use verification, and `AGENTS.md` forbids destroying data. This row is the flag; disposition is the owner's.

### Addendum 2026-09-28 (6) — M3 reconciliation: M-GAP-035 reclassified, two constitutional contradictions recorded (M-GAP-038, M-GAP-039)

M3 (PROJECT CONSTITUTIONAL AND KNOWLEDGE RECONCILIATION) performed read-only. Full reconciliation
model, source inventory, decision provenance/supersession table (14 decisions), minimum
composition-root path, and organizational memory model:
`docs/governance/M3_CONSTITUTIONAL_AND_KNOWLEDGE_RECONCILIATION.md`. **No code was modified, no
component renamed, deleted, merged, or migrated** — per M3's binding non-goals.

| Gap | Classification | What changed |
|---|---|---|
| M-GAP-035 (three control-plane surfaces, two test-only, the daemon consults none) | **OPEN, REFRAMED** | My own framing was materially imprecise. `ahos_org/__init__.py` declares *"an independent organizational control plane. It is not an AHOS runtime, not a trading system, and not an AGI"*, and `SLICE_2A` §0 declares its TCB/epistemic core is *"not: an AHOS implementation or integration; … an agent runtime, Agent One, or a 19-agent council."* These are **not three competing planes for one system** — they are one AHOS plane plus a self-declared-independent organizational layer (the MVOR/AGI-research direction). The register's phrase "the choice of which plane is canonical" rested on a category error. The accurate residual gap is a **composition-root ambiguity** between `python -m architecture.runtime --daemon` and `ControlPlane().start()`: two documented ways to "run AHOS", no integration, no recorded precedence. **Verified live:** `ControlPlane().start()` boots to `SAFE_HALT` (`run-c4ccb36c02e23b0a`) over 8 components and reads the `AG-*` namespace — it fabricates nothing and works as documented. Also corrected: the daemon's non-use is substantially *by design* (`orchestrated=0 by design this wave`), not oversight. |
| M-GAP-038 (the doctrine-registry enforcement glob does not cover `MASTER_DIRECTIVE_W43.md`) | **OPEN** (constitutional loophole — human decision required) | `tests/test_master_directive.py` globs `CANON.glob("MASTER_DIRECTIVE_v*.md")` for the "no orphan doctrine files" and sha-registration laws. `MASTER_DIRECTIVE_W43.md` does not match `v*`, so **the registry law never applies to it** — despite the name, despite self-describing as the main command, and despite carrying operational doctrine ("برای هر تغییر معمول مهندسی از کاربر اجازه نگیر. اما مرزهای Governance و Safety را نشکن"). `DOC_TRUTH_MAP.md:11` treats it as a wave directive ("living, not registry ACTIVE"), which is a description, not an enforcement. This is a **loophole in a CI-enforced constitutional law**, and the law v1 itself establishes ("every version file on disk must be listed"). Resolution needs a human: either widen the glob to `MASTER_DIRECTIVE_*.md` (which would force W43 registration or removal) or rename W43 so it cannot be mistaken for unregistered doctrine. **Not fixed — M3 forbids changing constitutional governance, and this is exactly that.** |
| M-GAP-039 (`PROJECT_STATE.md` is stale despite claiming to be always-current) | **OPEN** (doc defect — autonomously fixable) | `docs/canonical/PROJECT_STATE.md` self-describes as an "always-current pointer" but is pinned to "Wave-7 · 2026-08-11" while the register tracks 2026-09-28 and `DOC_TRUTH_MAP.md` references W43/W44. Its pointer (→ `reports/PHASE_STATE.md`) is correct; its content is not. Cheap fix: collapse to a pointer-only state with a single honest line. |

Contradictions recorded, not merged (per M3: "Do not silently merge conflicting taxonomies or
decisions"): (1) M-GAP-038 above; (2) M-GAP-039 above; (3) two live unmapped agent namespaces at
the runtime seam — `control_plane.py` reads `AG-*` from `config/agent_registry.yaml` while
`ahos_org` defines 19 `CANONICAL_AGENT_IDS`, and the M2 taxonomy map recorded the collision
without connecting them at the code seam; (4) M-GAP-037, carried. Also reaffirmed as a
*coexistence*, not a contradiction: the four simultaneously-true Agent-One statements
(intended root / FUTURE_NON_AUTHORITY_ROOT / no wiring / maturity 0) — `AGENT_14` §3.

**M3's methodological precedent found inside the repo:** `ADR_ACI_001` ("dual authority with an
explicit conflict record (chosen)") and `AGENT_14`'s L0–L5 evidence doctrine with
`[VERIFIED]`/`[PROPOSED]` labels. M3's memory model (AUTHORITY + PROVENANCE + TEMPORAL VERSIONING
+ SUPERSESSION + REALITY VERIFICATION + CONTRADICTION DETECTION + DECISION HISTORY) is those two
patterns generalized. The exemplar matters: it is already an *accepted* pattern in this repo, so
M3 is not a new mechanism — it is the existing one applied to the whole corpus.

**What M3 does NOT claim:** no AGI/ACI achievement (a continuing research objective), no
constitutional change, no maturity change, no Lane-A change, no new authority granted, no runtime
effect. The reconciliation document's header states `AUTHORITY = NONE CREATED` and
`RUNTIME_EFFECT = NONE`.

**Verification of C.3.1 against source** (the most consequential new finding): both glob sites in
`tests/test_master_directive.py` — line 61 (`test_required_invariants_and_protocol_shape`) and
line 90 (`test_no_orphan_files_and_sha_match`) — glob `CANON.glob("MASTER_DIRECTIVE_v*.md")`.
`MASTER_DIRECTIVE_W43.md` matches neither, so W43 escapes **both** the non-weakenable-invariants
check and the orphan/disk-vs-registry check. `docs/canonical/` holds exactly two directive files
(`MASTER_DIRECTIVE_v1.md`, `MASTER_DIRECTIVE_W43.md`); the registry's `directives` array lists
only v1, while its own `law` field states "every version file on disk must be listed." The
loophole is real and it is in a CI-enforced law.

**Repository reality — governed push #6 (2026-09-28).** Fast-forward `8dbd1ec..21d8104` →
`origin/ahos`, no force. One commit: `21d8104` `docs(governance): M3 constitutional and knowledge
reconciliation`. Changeset was `docs/governance/M3_CONSTITUTIONAL_AND_KNOWLEDGE_RECONCILIATION.md`
(new), `AHOS_GAP_REGISTER.md`, `docs/DOC_TRUTH_MAP.md` — documentation only, no code, no control-
plane component touched. All four checks verified: local HEAD
`21d810407ec0e8e6a45128a001122dc47610e94b`, remote `refs/heads/ahos` identical, upstream
`origin/ahos` tracked, divergence `0 0`. The three pre-existing `.cursor` working-tree items and
the untracked `reports/validate_imports_run_20260928T045640Z.json` probe were again excluded.
Gates: IMPORTS FAIL is the known M-GAP-037 gitignored-artifact condition with zero substantive
violations (the only non-artifact output is the unchanged 10-record dead-code candidate list);
**LANE-A FREEZE OK (36 files)**; `tests/test_master_directive.py` + `tests/test_agent_taxonomy_map.py`
25 passed. No `main` push, no force-push, no merge, no release, no live trading, no governance or
maturity change.

---

### Addendum 2026-09-28 (7) — M4: M-GAP-038 RESOLVED by declaring the second authority class and pinning it (additively)

**M-GAP-038 status: OPEN → RESOLVED (declaration + mechanical pin; no constitutional change).**

M3 described this as "the doctrine-registry enforcement glob does not cover
`MASTER_DIRECTIVE_W43.md`" and "a loophole in a CI-enforced constitutional law". **That framing is
corrected by the M4 trace: the glob's substance is right and the defect is elsewhere — the
constitution operates two classes of master directive but declares, pins, and enforces only one.**

The decisive simulation (widening the glob to `MASTER_DIRECTIVE_*.md`, as the obvious fix) would
have failed the constitutional suite: `MASTER_DIRECTIVE_W43.md` is missing **5/5** required
non-weakening invariants and **12/12** required protocol steps, and the orphan check reports it
on-disk-only. W43 is **not an unregistered doctrine version** — it is a **wave-scoped operational
directive**, a different class of authority. The registry schema (`version` numeric, ACTIVE = `max`)
has no slot for it: registering it would either break `max()` or demote v1 to SUPERSEDED, which
v1's own R-42 change law forbids and which W43's content never asks for. W43's own text is
wave-scoped ("هدف این موج" — the goal of *this wave*, plus a 13-point Definition of Done for that
wave) and substantively **consistent with** v1 (`UNKNOWN > fabricated`, `PAPER_ONLY`, `NO REAL
TRADING`, `NO WALLET SIGNING`, and an explicit order not to break Governance/Safety boundaries).

The real defect, and what M4 closed: W43 is the **operationally governing** directive
(`DOC_TRUTH_MAP.md` section A) yet its sha256 was pinned **nowhere** as an integrity pin — v1's
sha is pinned in three places, W43's in zero. It could have drifted silently with nothing to notice.
That is exactly the failure mode v1's registry was built to prevent, applied to the other class.
Its exclusion from the registry also *looked accidental*, because the introducing commit
(`5ccb0c0`, owner, 2026-08-21, message "register Master Directive") touched only `README.md`,
`MASTER_DIRECTIVE_W43.md`, `news.ts`, `page.tsx` — never the registry, the test, or the issue
register. A future reader could not tell "correctly excluded" from "registration was forgotten".

**Resolution adopted (option 5 of 5 considered) — strictly additive, fully reversible.** A new
declaration classifies both classes exhaustively and a new test pins it:

- `docs/governance/M4_WAVE_DIRECTIVE_DECLARATION.md` — declares CLASS A (permanent doctrine,
  `MASTER_DIRECTIVE_v{n}.md`, registry-enforced, R-42 change law) and CLASS B (wave operational
  directive, `MASTER_DIRECTIVE_<WAVE>.md`, **not in the registry by declaration, not omission**,
  never supersedes or demotes Class A; where the two could be read to conflict, **Class A
  prevails**). It grants **no authority** and has **`RUNTIME_EFFECT = NONE`** — it declares a
  classification `DOC_TRUTH_MAP.md` already made and pins it.
- `tests/test_wave_directive_declaration.py` — 5 additive pins: (1) the Class A / Class B partition
  on disk is exhaustive and matches the declaration; (2) Class B files are absent from the registry
  (declared, not accidental); (3) each Class B file's sha256 is pinned — W43 =
  `87627c0a61142fdfd0fcedeabbddf54f9f618f6c5851d162ccfaa749e2d2b4fd` — so silent drift is now a
  test failure; (4) Class B files must not claim ACTIVE or supersession; (5) the Class A registry
  still has exactly one ACTIVE = highest version, re-asserted untouched.

**No existing pin weakened, no registry change, no rename, no deletion, no test modification, no
code change.** `tests/test_master_directive.py` is untouched; the registry is untouched; W43 is
untouched. `tests/test_wave_directive_declaration.py` + `tests/test_master_directive.py` together:
**10 passed**. The additive claim is itself test-pinned — the 5 existing master-directive pins
still pass against the unchanged suite.

| M-GAP-038 (`MASTER_DIRECTIVE_W43.md` is not covered by doctrine-registry enforcement) | **RESOLVED (declaration + pin)** — the *description* changed, not the law | M3's "loophole" framing was too strong. The `MASTER_DIRECTIVE_v*.md` glob is **correct** — v1's change law and the registry schema are written in terms of `MASTER_DIRECTIVE_v{n}`. W43 is a **second, undeclared class of authority** (wave operational), and the `DOCUMENTED ≠ ENFORCED` gap was that the constitution never named, pinned, or enforced it. Closed additively: the partition is now exhaustive and each Class B file's sha256 is pinned, so the operationally governing directive has the same tamper evidence v1 always had. Two disposition options remain human-gated (below). |

**Remaining human-gated (carried, not resolved by M4):**

| Item | Class | Why it stays human-gated |
|---|---|---|
| Add a `wave_directives` key to `master_directive_registry.json` (schema 1 → 2) | **DECISION REQUIRED** | The cleanest model, but it changes the registry schema, which is constitutional enforcement. AGENTS.md forbids weakening tests and the owner must ratify; needs an R-series entry. |
| Rename `MASTER_DIRECTIVE_W43.md` so it cannot be mistaken for doctrine | **DECISION REQUIRED** | Breaks 9 referencing files; disposition of an operationally governing document is owner review under `docs/canonical/GOVERNANCE.md` (autonomous deletion prohibited). M4 deliberately did neither. |
| M-GAP-037 (`validate_imports.py` FAIL is 100% gitignored build artifacts) | **OPEN** (enforcing-control policy decision) | Carried unchanged. Confirmed again at M4: 44 FAIL lines, all `__pycache__/` or `.pytest_cache/` — gitignored (`.gitignore:1`), produced by running Python, invisible to CI. IMPORTS / EVIDENCE-BOUNDARY / LANE-A FREEZE / SECRETS all OK; the 10 dead-code candidates are unchanged from the prior baseline. |
| M-GAP-039 (`PROJECT_STATE.md` stale) | **OPEN** (autonomously fixable) | Still open; see next-mission note. |

