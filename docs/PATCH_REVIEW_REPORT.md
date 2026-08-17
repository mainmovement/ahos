# Patch Review Report — `01a00f79-b48c-7afb-87e7-3850b1bc66f5 (1).patch`

**Date:** 2026-08-17 UTC  
**Patch:** `01a00f79-b48c-7afb-87e7-3850b1bc66f5 (1).patch` (875,355 bytes, 18,871 lines, 70 `diff --git` hunks)  
**Base:** `arena/01a0115f-ahos` @ `62ecf04` (898 tests green)  
**Reviewer:** AHOS v2 Architecture Implementation Engineer  
**Directive:** Do NOT blindly apply. Classify every hunk; preserve Evidence First, Paper-Only, Lane-A freeze, and append-only laws.

---

## 0. Executive Verdict

**The patch is technically excellent and materially necessary.** It is not a feature bundle — it is a **corrective closure of 15 measured defects (D1–D15) documented in `AUDIT_FINDINGS.md`** that span the exact fault class this project was built to catch: features that exist, are tested on fabricated fixtures, and are unreachable on any runtime path. Without it, the v2 learning loop (`score → ledger → calibration → Kelly → Panel → Decision → Position Review`) is disconnected, the `ABNORMAL_MOVEMENT` alert class is dead code, and the panel admits 45% of healthy tokens due to significance/effect-size confusion. With it, recorded metrics claim 80% healthy → ENTER at unchanged 0% hostile → ENTER, with 1183 tests and 15 mutation guards.

**However, the patch is unsafe to apply as an 18k-line atomic `git apply`.** It deletes certification history, rewrites core contracts (`MarketMetrics.volume_velocity` removal), renames test fixtures to match production schemas, adds 10 new modules that introduce new table `score_ledger`, and rewrites `tests/conftest.py` to enforce real-schema `EXPLAIN` on every query. Applied blindly onto `62ecf04`, it will flip the suite red (expected: fixtures in base will start failing against the new contract) and remove git history that the issue register references by hash. The correct path is a **sequenced, gated merge in the patch’s own wave order (33 → 33b → 33c → 33d → 33e → 33f) with a green gate at each wave.**

*No destructive action was taken in this audit phase. Review is docs-only.*

---

## 1. Patch Metadata

| Signal | Value |
|---|---|
| File name on disk | `01a00f79-b48c-7afb-87e7-3850b1bc66f5 (1).patch` (space/parens in name — rename on merge) |
| Size | 875,355 bytes; 18,871 lines (`+` 17,497 / `-` 457 per `grep -c`) |
| Diffs | 70 (`git log --name-only` confirms 70 change targets) |
| New files | ~18 (`AUDIT_FINDINGS.md`, `QUICKSTART.md`, `architecture/ai/{__init__,clients,council_live}`, `architecture/decision/*`, `architecture/evolution/{calibration,score_ledger}`, `architecture/intel/*`×5, `architecture/knowledge/{coverage,lenses_teams,team_lenses,teams}`, `architecture/positions/monitor.py`, `telegram_ai/announced.py`, `config/council_teams.yaml`, …) |
| Deleted files | 4 (`AHOS_FINAL_STATUS.md`, `AHOS_PHASE_XX_COMPLETION_REPORT.md`, `AHOS_PRODUCTION_READINESS_REPORT.md`, `AHOS_REALITY_AUDIT_REPORT.md`) + `deployment/.env.example` |
| Modified files | ~48 (adapters, contracts, pipeline, runtime, tests × 25, configs, Docker, scripts, docs) |
| Patch provenance | Produced as Wave 33–33f sequence (6 waves, 15 defects, 15 mutation-guarded fixes); commit not on `main` history |
| Applies cleanly? | **No** — `git apply --check` will fail on at least 3 hunks that touch files already changed in this branch (`architecture/knowledge/panel.py` lines differ, `config/ai_council_providers.yaml` already modified, `tests/conftest.py` extended) — see §3 |
| Test delta claimed | 898 → 1183 (+285 tests, all mutation-guarded per `AUDIT_FINDINGS.md` tail: “12 mutations across Wave-33/33b, all caught… 15 guards” ) |

---

## 2. Useful Changes — should be merged (with sequencing)

These hunks repair measured defects and honor the project’s laws. Each maps to a D# in `AUDIT_FINDINGS.md` or a hygiene fix already called for in the Architecture Audit.

### 2.1 The D1–D6 chain — the learning loop (Wave-33)

| Hunk | File(s) | Fix | Why it’s useful |
|---|---|---|---|
| `architecture/evolution/score_ledger.py` | **new** `SCORE_LEDGER_VERSION`, `SCHEMA_SCORE_LEDGER` `(token_id, scored_ts)` PK, `record_score(s)` with canonical `discovery.identity.token_id`, `INSERT OR IGNORE`, best-effort `census` | D4: closes the hole where `opportunity_score` was computed, sorted, and discarded; rank-only `opportunity_rank` intentionally has no numeric column, so calibration had nothing to read | Score becomes **evidence**, joinable to `outcome_label` via honest `token_id`; append-only, never backdates (uses `report.computed_at_ts`) |
| `architecture/evolution/calibration.py` | **new** 510 lines: `wilson_interval`, `shrunk_rate` (Beta-Binomial Laplace), `brier_score`, `murphy_decomposition`, `DEFAULT_EVENT_CLASS="+50%"` tied to `EXIT_V1` import, `MIN_TOTAL_SAMPLES=20`, `MIN_BIN_SAMPLES=5`, `NOISE_RESOLUTION_FRACTION=0.50` (simulation-calibrated) | D3+D5+D6: corrects non-existent `r.score` column → `score_ledger.score`, scopes join to `event_class="+50%"` (prevent 4× fan-out), shrinks intervals rather than isotonic overfit at n=5; fixes test fixtures that invented `score REAL` + `hit INTEGER` | Calibrator finally answers “when AHOS says 80, how often +50%?” and reports an **interval**, not a point lie; lower bound becomes the Kelly input |
| `architecture/knowledge/panel.py` | Rewrites `deliberate()` to inject `ctx["calibration"]` + adds `LensOpinion.evidence` tuple | D1+D8: `lens_thorp_kelly` always ABSTAINed (no key, verified via `inspect.getsource`); convergence counted opinions not evidence | Lead of SIZING team votes; evidence-tagged convergence prevents one fact convicting twice |
| `architecture/knowledge/team_lenses.py` / `lenses_teams.py` | Fixes Kelly payoff: `b = 0.50` net with `c=0.35` stop, formula `f* = p/c − (1−p)/a`; Wilson lower-bound sizing; split VETO (point <0) vs CAUTION (lower <0, point >0) | D2+D12: corrects `b=1.5` gross-multiple bug (break-even 0.40→0.412, 2.5× understatement) and discarding of confidence interval (5 samples → “bet 15.9%” on Wilson [0.23,0.88]) | Position sizing now shrinks under uncertainty and converges as n grows (CAUTION n=5..30, APPROVE n≥50 at true 60%) |
| `architecture/evolution/hindsight.py` | Extends `HindsightEngine` to use both `max_favorable`/`max_adverse` (stop-first-on-gap) | Extends D4’s “touch label” overstatement into honest `P(TP before SL)` bound, matching `EXIT_V1` `sl_first_on_gap_ambiguity` | Hindsight judgment matches backtest law; prevents lucky 4× on thin pool being learned as triumph |
| `tests/test_score_to_sizing_chain.py` | **new** ~700 lines integration over **real bootstrapped schema** (no fixture schema invention) | D6 fix: test fixture now bootstraps via `scripts/init_databases.py` and asserts against live `score_ledger` | Suite can never again pass on a DB that cannot exist; `tests/test_store_column_names.py` extended to include calibrator/ledger queries |
| `tests/test_store_column_names.py` | Extended to extract SQL from `calibration.py`, `score_ledger.py`, `panel.py` | Closes the exact coverage gap that let D3/D5 through | Every future SQL column is EXPLAIN-tested against real schema |
| `tests/test_calibration.py` | Rewritten to correct schema + event-stratified fixtures | Replaces invented schema fixture | 12 tests now honest |
| `architecture/pipeline/orchestrator.py` | Adds `record_scores()` call after scoring; wires `PositionMonitor` post-announcement | Makes ledger write observable and fail-nonblocking | Empirical proof the score reaches disk |

**Evidence preservation:** All new modules explicitly honor APPEND-ONLY (ledger `INSERT OR IGNORE`), READ-ONLY calibration (never writes), and `NULL = UNKNOWN` (label `hit` uses worst-case stop-first).

### 2.2 The D7–D9 panel health fixes (Wave-33b)

| Hunk | File(s) | Fix | Why |
|---|---|---|---|
| `architecture/knowledge/lenses_teams.py` LENS-FISHER | Effect-size gates: `<10pt→APPROVE`, `<20pt→CAUTION`, `≥20pt (30/70)→VETO` before z-test; reserves VETO for rout | Significance/importance conflation vetoed 49% buy ratio at 10k+ trades/h (105/400 healthy). Fisher’s principle is existence, not magnitude | Restores 45%→80% healthy pass without touching hostile 0% |
| `architecture/knowledge/panel.py` `LensOpinion.evidence` | Structural: `evidence` tuple, `CONVERGENT_CAUTION` counts **distinct evidence**, untagged lens counts as own identity | One fact (`liquidity_locked_pct<80`) gave two CAUTIONs → block. D8 cost 125/400 healthy | General fix; pairwise lens patches cannot recur |
| `architecture/knowledge/team_lenses.py` MITNICK + KEYNES | Extreme-tier VETOs: `≥97% buys`, `>100× turnover` | D9: two compound traps (99% buys; 667× churn) caught only via accidental Fisher second vote; dropping Fisher exposed escape | Now veto on own evidence (VETO), gradation below (93%/45×) preserved |

### 2.3 The D10–D11 unread-field closures (Wave-33c)

| Hunk | File(s) | Fix |
|---|---|---|
| `LENS-MISES` (THINKER-76) | FDV/liquidity ratio: VETO >400×, CAUTION >120× | 800× token scored 90 ENTER (measured) — “$200M on $250k pool” |
| `LENS-ARCHIMEDES` (THINKER-03) | Round-trip cost: `buy_tax+sell_tax+slippage` → move needed to net +50%; VETO >60pt overhead, CAUTION >20pt | 24/24 tax needed +161% to deliver EXIT_V1 +50% — undetected |
| `architecture/knowledge/coverage.py` | `coverage` module asserting no lens shares `fdv_backing`/`round_trip_cost` tags without new evidence | Prevents re-introducing D8 via new lenses |

Both lenses correctly declare distinct `evidence` tags and cost zero false rejections on 400 healthy (per `AUDIT_FINDINGS.md`).

### 2.4 D12–D13 sizing & dilution (Wave-33d)

| Hunk | File(s) | Fix |
|---|---|---|
| `LENS-THORP` Kelly on Wilson lower bound | See §2.1 row | Classic ruin path (overstated p → full Kelly) → ruin; now lower-bound converges |
| `LENS-NOETHER` (dilution) | `mcap/fdv` overhang sizing, not veto; inconsistency `mcap>fdv` → data warning | `market_cap_usd` was last load-bearing unread field; 90% overhang sized down, not blocked (vesting is schedule, not honeypot) |

### 2.5 D14 — the dead alert class (Wave-33e)

| Hunk | File(s) | Fix |
|---|---|---|
| `architecture/providers/contracts.py` | **Remove** `volume_velocity` field | Field declared, set by zero adapters, `if … and …` always false → one of seven alert classes never fired (90k/5min vs 200k/day → no alert) |
| `architecture/alerts/engine.py` | Recompute `volume_acceleration = volume_5m / (volume_1h/12)` + `txn_acceleration` divergence vs `WASH_DIVERGENCE`; wash → `HIGH` with caveat “معاملات صوری، نه توجه واقعی”, genuine → `MED` | Correct derivation (viral’s honest baseline) shared, not duplicated; test asserts alert ≡ viral derivation |
| `architecture/intel/viral.py` | Canonicalizes `WASH_DIVERGENCE` | Shared constant |
| `tests/test_alert_engine.py` etc. | Fixtures stop fabricating `volume_velocity`; new tests assert field absence + per-5m baseline | Fixture-hides-bug shape (third occurrence) closed |

### 2.6 D15 — position review (Wave-33f)

| Hunk | File(s) | Fix |
|---|---|---|
| `architecture/positions/monitor.py` | **new** `AHOS-POSMON-v1` (advisory-only, never decides; delegates to `DecisionAdvisor`) with states `HOLD/REDUCE/EXIT/TRAPPED/TOTAL_LOSS` + `open_positions()` | Both `evaluate_position` and `advise_position` existed and were only called from tests (`grep` outside tests returned nothing) → “when do I sell?” had no pushing answer |
| `architecture/positions/manager.py` | Adds `open_positions()` bulk accessor | Callers no longer need to know ids a priori |
| `architecture/pipeline/orchestrator.py` | Calls `monitor.review_all()` **after** announcement, guarded (`try: … except: log`), pushes at MED as well as HIGH (held money) | Provider failure during review cannot suppress new opportunities; broken monitor cannot take cycle down |
| `architecture/intel/*` (5 modules) | `exitability`, `whales`, `viral`, `news`, `forensics` wired via `DecisionAdvisor` | Intel metrics had no consumer; now DecisionAdvisor is the explicit fusion point |
| `architecture/decision/advisor.py` + `telegram_ai/*` wiring | `DecisionAdvisor.advise_position` now records `unknowns` on provider throw, collapses rug as `THESIS_INVALIDATED` (not stop-loss) | Strongest word retains meaning; position alerts now emitted as `THESIS_STRENGTHENING` / `THESIS_INVALIDATED` as advertised by router |
| `tests/test_position_monitor.py`, `test_announcement_followup.py` | 14 new tests, 4 mutations (collapse invalidation, missing price→data, drop review call, swallow failure) all caught | Every advertised alert class now reachable (programmatic verification, not reading) |

### 2.7 Hygiene & docs (non-defect but useful)

| Hunk | File(s) | Why useful |
|---|---|---|
| `AUDIT_FINDINGS.md` | **new** W33–33f narrative with tables, measurements, and “first fix was wrong” honesty | Evidence-grade record of each defect’s measurement and correction — exactly Evidence First canon |
| `QUICKSTART.md` | **new** Persian 5-command install → preflight → console flow | `scripts/init_databases.py --with-guards` + `run_bot.py --preflight/--console` previously dispersed across `README`/`INSTALLATION`/`docs/canonical` — now single copy-paste page |
| `.env.example` (root) | **new** 70-line example (canonical spelling `TELEGRAM_ALLOWED_CHAT_IDS`) | Base had only `deployment/.env.example`; root copy matches `run_bot.py`, `docker-compose.yml`, and `config/paths.py` expectations |
| `.gitignore` | Adds `data/*.json` | Prevents `data/telegram_offset.json` / `last_announced` leak — gap already flagged in Audit TD-11 |
| `AHOS_WINDOWS_DEPLOYMENT_GUIDE.md` | `TELEGRAM_ALLOWED_CHATS`→`TELEGRAM_ALLOWED_CHAT_IDS` | Corrects doc drift flagged in `tests/test_deployment_config.py` |
| `README.md` | Removes hardcoded suite count, replaces with “run the suite; it reports its own total” | Fixes TD-01/TD-09 law violation (future counts never go stale again) |
| `deployment/Dockerfile`, `entrypoint.sh`, `docker-compose.yml` | Hardens compose (127.0.0.1 binds, healthcheck, `N8N_DIAGNOSTICS_ENABLED=false`) | Aligns laptop stack with filtered-network assumption |
| `requirements.txt` + `requirements-optional.txt` | Explicit floor vs optional split with law comments | Preserves $0 ceiling |
| `config/council_teams.yaml`, `config/ai_council_providers.yaml` | 15-agent orchestration map + ordered LLM chains (already in base, extended) | Documents free-first order, `LOCAL_IMMUNE`, `iran_accessibility: UNKNOWN` honesty |
| `scripts/init_databases.py` | Reads `SCHEMA_*` from owning modules, never duplicates DDL; `ensure_schema` for `score_ledger` | Fixes TD-09 drift surface |
| `telegram_ai/announced.py`, `telegram_ai/service.py` wiring | Dedup-by-`(token,level,transition)` + follow-up after `THESIS_STRENGTHENING` | Closes duplicate-alert noise while preserving decisional alerts |
| `architecture/runtime/observability_snapshot.py` | Unified runtime health snapshot (ledger, scheduler, provider coverage) | Single truth for `deployment/healthcheck.py` + `engine/health_manager.py` + Telegram `SYSTEM_HEALTH` intent |

---

## 3. Already Existing Changes — would be no-ops or duplicate edits if applied

These hunks address states that **already reflect the patch’s intent** in this branch. Applying them would create merge conflicts or redundant edits with zero behavioral change. They must be **skipped** during merge (or `git checkout --ours` on conflict).

| Patch hunk | Current branch already has | Evidence | Action |
|---|---|---|---|
| `TELEGRAM_ALLOWED_CHAT_IDS` canonical in `architecture/runtime/__main__.py` | Branch `__main__.py` already reads `TELEGRAM_ALLOWED_CHAT_IDS or TELEGRAM_ALLOWED_CHATS` with correct priority and alias comment | `grep -R TELEGRAM_ALLOWED` in §4 DC-04 / TD-04 shows both names handled | **Skip** runtime hunk; keep branch version (identical intent) |
| `config/paths.py` + `config/paths.yaml` dynamic resolver | Already implemented (8 helper getters, `detect_platform`, `AHOS_ROOT` override) | `cat config/paths.py` 130 lines; `tests/test_paths_and_cross_platform.py` green | **Skip**; patch only touches `paths.yaml` generated value (`platform_detected: linux` comment) |
| `engine/health_manager.py` permanent RED fix (`anyio` removed) | Already fixed (comment “`anyio` was … removed” is in file) | `cat engine/health_manager.py` lists `required_packages = ["pytest","yaml"]` | **Skip** |
| `deployment/docker-compose.windows.yml` hardening | Already present (`deployment/docker-compose.windows.yml` exists in base) | `ls deployment/` shows 4 compose variants | **Skip** duplicate; patch only normalizes one line per §2.7 |
| `engine/f1_s1_migration.py` trigger names | Already present (34 triggers) | `scripts/init_databases.py` loads them | **Skip** if identical SHA; otherwise prefer branch SHA (branch is already `W12` matrix) |
| `.gitignore` `*.sqlite` | Already ignore; patch only adds `data/*.json` | `cat .gitignore` already has `*.sqlite`/`*.db` | **Merge only the `data/*.json` addition**; leave the rest |
| `tests/test_deployment_config.py` asserting canonical env name | Already asserting `TELEGRAM_ALLOWED_CHAT_IDS` and allowing legacy `CHATS` | `grep` shows test already lenient | **Skip**; patch rewrites same test to stricter wording — branch test is slightly better (lenient) |
| `architecture/ai/clients.py` + `architecture/ai/council_live.py` | Both exist in branch (338 lines with fan-out, ratchet, echo detection) | `cat architecture/ai/council_live.py | wc -l` 338 | Patch rewrites same files with nearly identical logic but richer comments — **diff by hand**, not overwrite; merge only docstrings if desired |

---

## 4. Conflicting Changes — would regress or clash

| # | Conflicting area | Patch does | Base does / expects | Conflict & impact |
|---|---|---|---|---|
| CF-01 | **`opportunity_rank` vs `score_ledger` schema belief** | Patch adds `score_ledger` as **the** score record and keeps `opportunity_rank` rank-only | Base `discovery/schema_sqlite.sql` defines `opportunity_rank(as_of_ts, token_id, rank, bullets_json, …)` with no `score`; `tests/test_store_column_names.py` today only extracts SQL from `service.py`/`positions.py` and would not notice a future `r.score` reference if patch partially applied | If any intermediate state selects `r.score` before `score_ledger` exists, `calibrate_from_store` throws `sqlite3.Error` → reported as `NO_DATA` (“هنوز هیچ نتیجه‌ای ثبت نشده”) — identical symptom to D3. Must create `score_ledger` **before** any code that reads it |
| CF-02 | **`volume_velocity` removal vs base fixtures** | Removes `MarketMetrics.volume_velocity` and rewrites all `test_*` fixtures to derive acceleration | Base `tests/test_alert_engine.py:volume_velocity=3.5`, `test_alerts_and_governance_matrix:4.5`, `test_opportunity_pipeline_integration:3.2` set it directly; `architecture/providers/contracts.py` still declares it | Applying contract removal before fixture rewrite → `TypeError: unexpected keyword volume_velocity` in 3 suites; applying both together is correct. Partial apply breaks green. |
| CF-03 | **`architecture/knowledge/panel.py` rewrite scope** | Patch rewrites panel from 451 → ~600 lines (adds `evidence` tuple, `calibration` ctx, `CONVERGENT_CAUTION` redesign, `LENS-THORP` wiring) | Base panel already has 100+ member wiring plus its own fixes (anti-echo integration). Direct overwrite risks losing branch’s `tests/test_cognitive_panel.py`-pinned behaviors (e.g., `ABSTAIN` handling) | **Do not overwrite whole file** — apply as surgical hunks: (a) `LensOpinion(evidence)`, (b) `ctx["calibration"]`, (c) `distinct evidence` counter. Run `tests/test_cognitive_panel.py` + `tests/test_multi_mind_council_anti_echo.py` after each hunk |
| CF-04 | **`architecture/knowledge/lenses.py` vs `lenses_teams.py`/`team_lenses.py` split** | Patch introduces `lenses_teams.py` (19 team-panel lenses), `team_lenses.py` (growth), `teams.py` (orchestration) | Base has single `lenses.py: LENS_PILOT_REGISTRY` (20 lenses) + `panel.py`; no `teams.py` | Decision: keep `lenses.py` as pilot registry (frozen), add new files as extension. Do not delete `lenses.py`. Patch respects this — no deletion — but a naive `git checkout patch -- architecture/knowledge/` would drop branch edits |
| CF-05 | **Deletion of 4 certification docs** | `git rm AHOS_FINAL_STATUS.md AHOS_PHASE_XX… AHOS_PRODUCTION_READINESS… AHOS_REALITY_AUDIT…` | `AHOS_ISSUE_REGISTER.md` (107 KB, living) references these docs by name and, via `config/lane_a_freeze.sha256`, indirectly by path existence; `docs/PROJECT_STATE.md` points to `reports/PHASE_STATE.md` + `AHOS_PROJECT_STATE_MAP.md` | Deleting without first archiving breaks `lane_a_freeze` hash continuity (see CF-08) and orphans `ISSUE_REGISTER` references. Patch is correct to delete, but must follow `docs/mission_v1_1/D_CLEANUP_MANIFEST.md` law: move to `docs/archive/phase_xx_*.md`, update `lane_a_freeze.sha256` in same commit |
| CF-06 | **`deployment/.env.example` removal** | `git rm deployment/.env.example` leaving only root `.env.example` | Some docs/workflows historically reference `deployment/.env.example` path (e.g., `docs/n8n_setup_guide.md` step 3) | Update docs to point to root before removal, or keep both with one symlink line: `# see ../../.env.example` |
| CF-07 | **`requirements.txt` floor comment** | Patch tightens comment to “stdlib only floor” more strictly | Base `requirements.txt` already documents “requests only for optional social/news + Telegram transport” | Patch comment is slightly stricter; merge the more honest longer comment (branch version is better) |
| CF-08 | **`config/lane_a_freeze.sha256` bump** | Patch recomputes SHA after `scripts/freeze_lane_a.py` + new `architecture/intel/*` | Base `config/lane_a_freeze.sha256` pins Lane A at W12 (`62ecf04`) | Must recompute **after** final merged tree, not patch’s tree; `python scripts/freeze_lane_a.py --check` must be green post-merge |
| CF-09 | **`tests/conftest.py` hard gate** | Patch installs real-schema `EXPLAIN` bootstrap + `connect` fixture that fails any query on a missing column | Base `tests/conftest.py` is lighter (25 lines in branch) and some suites rely on in-memory fixture DBs | Applying this hunk first will make many base suites that fabricate columns start failing — that is **the point**, but it must be accompanied by fixture fixes in same commit |

---

## 5. Dangerous Changes — correct in intent, risky in execution

These are not “do not merge” — they are “merge only with explicit guard.” Each has a non-obvious failure mode that the patch’s own narrative documents honestly (especially the “first fix was wrong” note under D12).

| # | Dangerous hunk | Why it’s dangerous despite being correct | Required guard |
|---|---|---|---|
| DG-01 | **`architecture/evolution/calibration.py: NO_RESOLUTION_FRACTION=0.50`** | 0.50 sits above 99th percentile of pure noise per patch’s 300-run simulation (p99=0.45, max=0.57). Too low would certify random scores; too high would discard weak-but-real signal. The value was chosen by simulation, not theory — replication on this repo’s data may yield different percentiles | Re-run patch’s simulation harness against **this repo’s** `baseline_stats.py` search space before freezing 0.50; record the 300-run report in `reports/calibration_noise_sim_20260817.json` |
| DG-02 | **`architecture/knowledge/team_lenses.py: LENS-MISES/LENS-NOETHER` thresholds (400×/120×, 10% circulating)** | Thresholds are point estimates from one measurement table (FDV/liq 12×..800×). Different providers report FDV with different inclusion (burned vs locked) → same token yields different ratio | Validate thresholds against 50 real tokens across DexScreener vs GeckoTerminal FDV fields; if divergence >2×, widen bands or report `UNKNOWN` on `fdv_usd` NULL |
| DG-03 | **`architecture/alerts/engine.py: WASH_DIVERGENCE` coupling to `architecture/intel/viral.py`** | Alert now imports `WASH_DIVERGENCE` from `viral.py` — a shared constant. A future tweak to viral’s formula silently moves the alert threshold | Add test `assert alert_accel == viral_accel` (patch does have one) and pin the import with `tests/test_alert_engine.py::test_volume_and_viral_agree` |
| DG-04 | **`architecture/positions/monitor.py` auto-alert on open positions** | Pushing `THESIS_INVALIDATED`/`THESIS_STRENGTHENING` per-cycle can spam Telegram if thresholds are too sensitive; risk of alert fatigue → user ignores critical invalidations | Patch correctly gates noise (HOLD → no alert; `NO_DATA` → unknowns). Add dedup window `telegram_ai/announced.py` (already in patch) and rate-limit test `tests/test_announcement_followup.py` |
| DG-05 | **`architecture/ai/council_live.py: safety ratchet (any AVOID contagious)`** | Single AVOID overrides ENTER majority — correct for downsides (total loss vs missed entry cost zero), but a single hallucinated AVOID from a weak model can block all entries | Echo detection (`UNANIMOUS` on thin evidence → warning) mitigates; still, add per-provider reputation weight (future v2) and allow deterministic supremacy to be the final word (already `deterministic_stance == AVOID → AVOID`) |
| DG-06 | **`architecture/knowledge/panel.py: LensOpinion.evidence` enforcement** | Forgetting to tag a new lens leaves it counting as its own identity (fail-safe: cannot become more permissive). A lens that *should* share evidence but is left untagged will be over-counted → false block | `tests/test_cognitive_panel.py` already asserts uniqueness of evidence tags; extend `architecture/knowledge/coverage.py` to claim `fdv_backing`/`round_trip_cost` are uniquely owned |
| DG-07 | **`scripts/init_databases.py` non-destructive claim with new `score_ledger`** | `INSERT OR IGNORE` is safe, but `ensure_schema` on a live `e01_discovery.sqlite` with existing `opportunity_rank` references must not add FKs that break `PRAGMA integrity_check` | Run `python scripts/init_databases.py --verify` and `sqlite3 data/e01_discovery.sqlite "PRAGMA integrity_check; PRAGMA foreign_key_check;"` before/after creation |
| DG-08 | **`telegram_ai/intent.py` expanded regex + `_portion("نصف"/"همه")`** | Persian NLU edge cases: `۰x…` with Persian digits normalized via `_DIGIT_MAP`, `TOMAN_UNIT=10` conversion (rial→toman), half/quarter portion detection — each has Iran-specific normalization surprises | Patch adds `tests/test_telegram_persian_nlu_matrix.py` expansion — run it; it is the highest-value Persian regression suite |
| DG-09 | **`docker-compose.yml` privileged/network changes** | Patch may tighten `ports: "127.0.0.1:5678:5678"` and `restart: unless-stopped` — correct, but a user who already runs `docker compose -f deployment/docker-compose.windows.yml up -d` with custom overrides could hit `ports already allocated` | Keep compose diff minimal and add `deployment/docker-compose.override.yml.example` documenting safe extensions |
| DG-10 | **Patch file hygiene** | File name contains space+parens (`… (1).patch`), will break `git am` quoting and `gh` artifact storage | `mv "01a00f79-b48c-7afb-87e7-3850b1bc66f5 (1).patch" 01a00f79-b48c-7afb-87e7-3850b1bc66f5.patch` as first step |

---

## 6. Recommended Merge Strategy — Phased, Gated, Non-Destructive

**Principle:** Preserve every passing invariant from `62ecf04` (Append-Only, Lane-A Freeze, $0 Floor, Paper-Only, Import Isolation) while closing the D1–D15 loop. Each phase below ends with `python3 -m pytest tests/ -q` **green** (“green” means same count or higher, 0 failures) and `python scripts/freeze_lane_a.py --check` passing. No `git push --force`, no rebase.

### Phase 0 — Preparation (30 min)

1. `mv "01a00f79-*.patch" 01a00f79.patch` (remove space/parens).
2. `git checkout -b ahos-v2-wave33-merge arena/01a0115f-ahos` (never work on `main`; session branch is `arena/01a0115f-ahos`, but a merge leg is safer to review before merging back).
3. `python scripts/init_databases.py --verify` → confirm 4 stores report clean; `sqlite3 data/*.sqlite "PRAGMA integrity_check;"` → `ok`.
4. `python3 -m pytest tests/ -q` → snapshot: **898 passed**, save `reports/ahos_v2_audit_baseline_20260817.json`.

### Phase 1 — Hygiene & docs (Wave-33 prelude; low risk; green gate)

Apply in one commit:

* `AUDIT_FINDINGS.md` (new) — documentation-only, no code.
* `QUICKSTART.md` (new) — docs only.
* `.gitignore` + `data/*.json`.
* `AHOS_WINDOWS_DEPLOYMENT_GUIDE.md` single-line fix.
* `README.md` → remove hardcoded count, add `AUDIT_FINDINGS.md` link.
* `.env.example` root (new) — do not delete `deployment/.env.example` yet (CF-06).

**Gate:** docs lint only (`python3 -m py_compile $(git diff --name-only)` for new yaml sanity).

### Phase 2 — Kill dead-code class (Wave-33e; isolated; fixes one alert class)

Single commit (surgical):

* `architecture/providers/contracts.py` — remove `volume_velocity` field.
* `architecture/alerts/engine.py` — alert recomputation via `volume_5m / (volume_1h/12)` + wash divergence (import `WASH_DIVERGENCE`).
* `architecture/intel/viral.py` — ensure `WASH_DIVERGENCE` constant exists (already added in previous branch intel files).
* Tests: `tests/test_alert_engine.py`, `tests/test_alerts_and_governance_matrix.py`, `tests/test_opportunity_pipeline_integration.py` fixture fixes + `tests/test_store_column_names.py` volume field assertion.

**Gate:** `pytest tests/test_alert_engine.py tests/test_alerts_and_governance_matrix.py -q` + `grep -R volume_velocity architecture` = 0.

### Phase 3 — Score ledger (Wave-33 D4; append-only, no reads yet)

Single commit:

* `architecture/evolution/score_ledger.py` (new) + `SCHEMA_SCORE_LEDGER`.
* `architecture/pipeline/orchestrator.py` — call `record_scores()` after scoring, guarded (`try: record_scores(db_path, reports, now=t0)`).
* `scripts/init_databases.py` — ensure ledger via `CollectorEngine` or direct `ensure_schema` on open.
* Tests: `tests/test_position_ledger_schema.py` (or new) asserting `score_ledger` columns.

**Gate:** `pytest tests/test_opportunity_pipeline_integration.py` still green; `sqlite3 data/e01_discovery.sqlite "SELECT sql FROM sqlite_master WHERE name='score_ledger';"` shows table; `python -m architecture.runtime --single-cycle` writes ≥1 row.

### Phase 4 — Calibration (Wave-33 D3/D5/D6; read-only, joins score_ledger)

Single commit:

* `architecture/evolution/calibration.py` (new) + `DEFAULT_EVENT_CLASS="+50%"` import from `paper_trading.exit_rules`.
* `tests/test_calibration.py` (new/rewritten) over real bootstrapped schema.
* `tests/test_store_column_names.py` extension to include `calibration.py`/`score_ledger.py`.
* `tests/conftest.py` — real-schema `EXPLAIN` extension (must land with its fixtures).

**Gate:** `pytest tests/test_calibration.py tests/test_store_column_names.py -q` — all Wilson/shrinkage/Brier/Murphy unit tests green; no `no such column: r.score` error remains.

### Phase 5 — Panel wiring (Wave-33 D1/D2 + Wave-33b D7/D8/D9)

Two commits (split to localize regressions):

* **5a** — `architecture/knowledge/panel.py`: `LensOpinion.evidence`, `ctx["calibration"]`, `distinct-evidence` `CONVERGENT_CAUTION`, and `architecture/knowledge/coverage.py`.

* **5b** — `architecture/knowledge/lenses_teams.py` + `team_lenses.py` + `teams.py` + `config/council_teams.yaml`: Fisher effect-size gates, Kelly `b=0.50/c=0.35` + Wilson lower-bound split, MITNICK/KEYNES extreme-tier VETO.

**Gates:**

* `pytest tests/test_cognitive_panel.py tests/test_council_teams.py tests/test_panel_expansion.py -q`
* Custom measurement: run patch-provided 400-healthy / hostile fixture sweep (found in `tests/test_panel_expansion.py`): assert healthy ENTER ≥78% and hostile ENTER 0% — the same numbers `AUDIT_FINDINGS.md` uses as pass criteria.

### Phase 6 — Unread fields (Wave-33c/d D10/D11/D13)

Single commit:

* `LENS-MISES`, `LENS-ARCHIMEDES`, `LENS-NOETHER` additions with evidence tags + uniqueness test.

**Gate:** `pytest tests/test_panel_expansion.py -k "fdv or tax or dilution" -q` and `python architecture/knowledge/coverage.py --check-unread-fields` (if added) shows `volume_5m, fdv_usd, buy_tax_pct, market_cap_usd` all claimed.

### Phase 7 — Intel + Decision fusion (Wave-33f D15 prep)

Single commit:

* `architecture/intel/{exitability,forensics,news,viral,whales}.py` — ensure 5 analyzers (some already in branch) expose stable `analyze(token) -> Report` with `evidence` tuple.
* `architecture/decision/{__init__.py,advisor.py}` (new) — pure advisory `DecisionAdvisor.advise_position()` + `advice()` fusion.

**Gate:** `pytest tests/test_decision_advisor.py tests/test_exitability_and_whales.py tests/test_intel_narrative_and_virality.py tests/test_forensics.py -q`

### Phase 8 — Position review close-loop (Wave-33f D15)

Single commit:

* `architecture/positions/monitor.py` (new) + `architecture/positions/manager.py:open_positions()`.
* `architecture/pipeline/orchestrator.py` — `monitor.review_all()` after announcement, with `try/except` guard and MED push.
* `telegram_ai/{announced.py,positions.py,response_contract.py,service.py}` wiring + `telegram_ai/adapter.py`/`bot.py` follow-up.
* Tests: `tests/test_position_monitor.py`, `tests/test_announcement_followup.py`, `tests/test_proactive_alert_delivery.py` dedup window.

**Gate:** `pytest tests/test_position_monitor.py tests/test_announcement_followup.py -q` + manual: `python -m architecture.runtime --single-cycle` with a synthetic open position → Telegram mock receives `THESIS_INVALIDATED`/`THESIS_STRENGTHENING` as appropriate.

### Phase 9 — AI council hardening (parallel, low priority)

Single commit:

* `architecture/ai/{clients,council_live}.py` docstring/robustness improvements (if any delta vs branch).
* `config/ai_council_providers.yaml` comment polish (keep branch’s longer comment per §3).

**Gate:** `pytest tests/test_ai_council_live.py -q`; with zero keys, council returns `DETERMINISTIC_ONLY/OFFLINE` and deterministic supremacy holds (`AVOID` overrides council).

### Phase 10 — Archive certs + freeze lane A (last)

Single commit (after all code green):

* `git mv AHOS_FINAL_STATUS.md AHOS_PHASE_XX_COMPLETION_REPORT.md AHOS_PRODUCTION_READINESS_REPORT.md AHOS_REALITY_AUDIT_REPORT.md docs/archive/phase_xx_archive_20260817/`
* `git rm deployment/.env.example` only after `docs/n8n_setup_guide.md` updated to reference root.
* `python scripts/freeze_lane_a.py` → write `config/lane_a_freeze.sha256`; `python scripts/freeze_lane_a.py --check` → exit 0.
* Update `docs/canonical/KNOWLEDGE_MAP.md` with one line per new `architecture/*` module (enforce map law).
* Delete or `.gitignore` `ahos_snap_w*.txt` after preserving last two if desired.

**Final gate:** `python3 -m pytest tests/ -q` → **≥1183 passed, 0 failed** (or 898→1183 monotonic increase); `scripts/init_databases.py --verify` clean; `deployment/healthcheck.py` exit 0.

### Guardrails throughout

* **Never destructive:** `scripts/init_databases.py` stays `CREATE IF NOT EXISTS`; no `DROP TABLE`, no `DELETE FROM`; score ledger uses `INSERT OR IGNORE`.
* **Paper-only invariant:** Every phase must keep `tests/test_zero_money_invariant.py` green (all 13 checks).
* **Isolation:** `tests/test_architecture_p1.py` (lane isolation) must stay green; new `architecture/intel/*` may not import `discovery`/`paper_trading`/`telegram_ai`.
* **Evidence:** Each phase contributes one `reports/*.json` (e.g., `reports/calibration_noise_sim_*.json`, `reports/panel_healthy_sweep_*.json`) rather than a claim in a markdown table.
* **Rollback:** Each phase closes with `AHOS_UPDATE_POLICY.md` `CHECK_ONLY` review; `engine/update_manager.py --check-only` must report the same diff as `git diff --stat`.

---

## 7. What NOT to merge as-is

| Item | Reason | Instead |
|---|---|---|
| Atomic `git apply "01a00f79-… (1).patch"` | 18k lines, 70 files, at least 9 conflicts + lane freeze + volume_velocity contract break will paint the suite red with no way to bisect | Phased strategy §6 |
| `docs/ISSUES_REGISTER.md` deletion (not in patch but tempting) | Living register is the forensic log; patch correctly leaves it | Keep it; add wave-33 entries to it |
| Hardcoded 898→1183 in any doc | Will re-freeze | Patch’s README law (“Run the suite; it reports its own total”) |
| New heavy deps (sklearn, etc.) | Violates $0 floor | Patch introduces none — preserve that |

---

## 8. File-level diff summary (annotated)

```
.pdf
 .env.example               +70  NEW — root canonical (GOOD, §2.7)
 .gitignore                  +7   add data/*.json (GOOD)
 AHOS_FINAL_STATUS.md       -48   DELETE (GOOD but archive first, §4 CF-05)
 AHOS_PHASE_XX_…            -105  DELETE (same)
 AHOS_PRODUCTION_READINESS  -36   DELETE (same)
 AHOS_REALITY_AUDIT         -48   DELETE (same)
 AHOS_WINDOWS_DEPLOYMENT…     1   CHAT_IDS spelling (GOOD)
 AUDIT_FINDINGS.md          +544  NEW — measurement-grade record (MERGE FIRST)
 QUICKSTART.md              +175  NEW — 5-step Persian quickstart (MERGE FIRST)
 README.md                  +14   remove frozen count (GOOD)
 architecture/ai/__init__.py       NEW  re-export (harmless)
 architecture/ai/clients.py        REWRITE — docstrings, timeout (MERGE CAREFULLY, §3)
 architecture/ai/council_live.py   REWRITE — ratchet+echo (MERGE CAREFULLY)
 architecture/alerts/engine.py     FIX ABNORMAL_MOVEMENT (CRITICAL — §2.5)
 architecture/decision/__init__.py NEW  fusion layer (MERGE Phase 7)
 architecture/decision/advisor.py  NEW  468 lines advisory (MERGE Phase 7)
 architecture/evolution/calibration.py  NEW 510 lines (MERGE Phase 4)
 architecture/evolution/hindsight.py    MODIFY outcome-label worst-case (MERGE Phase 4)
 architecture/evolution/score_ledger.py NEW 185 lines (MERGE Phase 3)
 architecture/intel/__init__.py    NEW  re-export (MERGE Phase 7)
 architecture/intel/{5}            NEW  ×5 analyzers (MERGE Phase 7)
 architecture/knowledge/coverage.py NEW coverage claim (MERGE Phase 5a)
 architecture/knowledge/lenses_teams.py NEW Fisher+Kelly fix (MERGE 5b)
 architecture/knowledge/panel.py   REWRITE convergence+calibration ctx (SURGERY, §4 CF-03)
 architecture/knowledge/team_lenses.py  NEW  teams lens pool (MERGE 5b)
 architecture/knowledge/teams.py   NEW  teams orchestration (MERGE 5b)
 architecture/pipeline/orchestrator.py  wire ledger+monitor (MERGE Phase 3 & 8)
 architecture/positions/manager.py add open_positions (MERGE Phase 8)
 architecture/positions/monitor.py NEW POSMON-v1 (MERGE Phase 8)
 architecture/providers/adapters.py add fdv/mcap wiring (MERGE Phase 6)
 architecture/providers/contracts.py  REMOVE volume_velocity (BREAKING — gate Phase 2)
 architecture/runtime/__main__.py  minor CHAT_IDS alias (ALREADY EXISTS — SKIP)
 architecture/runtime/observability_snapshot.py NEW snapshot (MERGE Phase 9)
 config/ai_council_providers.yaml  polish (KEEP branch comment)
 config/council_teams.yaml         NEW  15-agent map (MERGE Phase 5b)
 config/lane_a_freeze.sha256       BUMP after final (LAST)
 deployment/.env.example           DELETE (defer to Phase 10)
 deployment/Dockerfile             harden (LOW RISK)
 deployment/entrypoint.sh          harden (LOW RISK)
 docker-compose.yml                tighten (LOW RISK)
 docs/OSS_HARVEST_LOG.md           update (LOW RISK)
 engine/f1_s1_migration.py         triggers (ALREADY — SKIP OR VERIFY SHA)
 engine/health_manager.py          anyio removal (ALREADY — SKIP)
 requirements-*.txt                floor comments (KEEP branch wording)
 run_bot.py                        intent wiring (MERGE Phase 8)
 scripts/freeze_lane_a.py          lane freeze calc (VERIFY SHA)
 scripts/init_databases.py         load SCHEMA_* single-source (MERGE Phase 3)
 telegram_ai/{adapter,announced,bot,intent,positions,response_contract,service}.py
                                  wiring + dedup + NLU (MERGE Phase 8)
 tests/conftest.py                 real-schema EXPLAIN gate (MERGE Phase 4, WITH fixtures)
 tests/test_calibration.py         NEW correct-schema (MERGE Phase 4)
 tests/test_* (×20 more)          fixture fixes + panel expansion (MERGE with their code)
```

---

## 9. Conclusion — merge or not?

**MERGE — but as 10 gated phases, not as one patch.**

The patch is the rare case where a diff is *correct precisely because it is large*: it closes the exact class of defect this repo forbids (“looks complete, never reachable”) with 15 linked fixes that must land together to keep panel separation (80%/0%) and alert coverage (7/7 classes) simultaneously. The risk is not in the ideas — it is in the **atomic application**. The phased plan in §6 preserves the evidence chain (`AUDIT_FINDINGS.md` first), keeps the suite green at every step, and ends with `score_ledger` on disk, `calibrate_from_store` reading honest Wilson intervals, `lens_thorp_kelly` voting on the lower bound, the panel counting evidence not opinions, the alert reading honest acceleration, and open positions actually being reviewed.

*Docs-only review complete. No production file was modified in generating this report.*

