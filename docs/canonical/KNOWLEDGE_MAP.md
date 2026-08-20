# AHOS — CANONICAL KNOWLEDGE MAP (entry node · v2, Wave-7 2026-08-11)
# This is THE entry point. Read order below; everything else is referenced, never duplicated.
# Human view with rationale: docs/mission_v1_1/W7_H_CANONICAL_KNOWLEDGE_MAP_V2.md

## 1) Orientation (read in order)
0. **Agent Mode living ops:** `docs/AGENT_MODE_OPERATIONAL_DIRECTIVE_FA.md`
   (session start / end protocol; does **not** supersede MASTER_DIRECTIVE_v1)
1. MISSION.md — what AHOS is / non-negotiable laws ($0, PAPER-only, rank-first, probe-id law)
2. PROJECT_STATE.md — live component states (A–E letters), blockers, counters
3. GOVERNANCE.md — review chain, decision logs, hygiene law, register locations

## 2) System (canonical specs)
ARCHITECTURE.md · DATA_MODEL.md · DISCOVERY.md · SECURITY.md · RESEARCH.md · PROVIDERS.md ·
TELEGRAM.md (now incl. Wave-7 AI layer) · AGENT_COUNCIL.md · ROADMAP.md

## 3) Live truth files (root/reports)
AHOS_ISSUE_REGISTER.md (R/F/C/D/W/S/T series) · reports/PHASE_STATE.md (scorecard+phase letters) ·
reports/PROJECT_DOCUMENT_INVENTORY_WAVE7.json (file census vs 194-baseline) ·
research/SEARCH_SPACE_REGISTRY.json (multiplicity budget: B1+B2, H14–H20)

## 4) Authorities by topic (pointers)
- Discovery runtime code: /discovery/ (README order: pal → identity → observations → lifecycle →
  feature_store → security_gate → outcomes → ranker → holders → materialize → collect)
- Telegram/Persian/AI: /telegram_ai/ (intent → providers → positions → alerts) + ai_providers.yaml
- Research engine: /research/ (baseline_stats → strategy_lab) · CI: /engine/run_all_checks.sh
- Probes: engine/pal_probe.py (data plane) · telegram_ai AIPAL.chat (AI plane) → reports/pal_probe_*

## 5) History (evidence, preserved)
research/experiments/ · research/reports/ · reports/ (waves, probes, audits) ·
docs/mission_v1_1/ (wave-5 A–J · wave-6 A–L · wave-7 W7-A…L) · docs/archive/ ·
uploads/_archive_exact_dups_wave7/ (sha-manifested)

## W9 additions (Lane B)
- Wave-9 plan: `docs/mission_v1_1/W9_COGNITIVE_ARCHITECTURE.md` (two-lane law, authority model)
- Cognitive matrix: `docs/architecture/cognitive_principle_matrix.md` + `config/cognitive_principles.yaml`
- Contracts: `contracts/agent_contract_v1.json` · Registry: `config/agent_registry.yaml` + `architecture/` package
- PG parity audit: `docs/architecture/pg_parity_audit_w9.md`

## W10 additions (Lane B, audit-only)
- Readiness audit: `docs/mission_v1_1/W10_ARCHITECTURE_READINESS.md` (24-agent audit, red-team
  register F1–F16, P3 readiness READY_WITH_BLOCKERS, Lane-A integrity proof)
- Cognitive mapping: `docs/architecture/cognitive_agent_mapping_w10.md` (26 DRAFT principles,
  3 UNVERIFIABLE_PROVENANCE exclusions, agent-of-agents chain design — all DRAFT, unregistered)

## W11 additions (Lane B, runtime engine + contracts)
- Runtime engine: `architecture/control_plane.py` (one-start/degrade/halt/resume/idempotency,
  append-only run-ledger) · `architecture/provider_router.py` (free-first, probe-gated, breaker)
  · `architecture/council.py` (advisory council, disagreement protocol, red-team lints)
- Master doc: `docs/mission_v1_1/W11_UNIFIED_RUNTIME_ARCHITECTURE.md` (acceptance answers,
  topology, observability, contradictions)
- Specs: `docs/architecture/{unified_control_plane,single_start_runtime,runtime_dependency_graph,
  orchestration_comparison,ai_council_architecture,cognitive_agent_fabric,
  cognitive_agent_runtime_matrix,F1_RESOLUTION_PLAN}.md`
- Config: `config/control_plane.yaml` · `config/ai_provider_registry.yaml` —
  upgraded `config/cognitive_principles.yaml` (schema v2, 63 principles) and
  `config/agent_registry.yaml` (ops blocks; F2 cycle repaired; acyclic CI-pinned)
- Contracts: `contracts/{control_plane_contract_v1,ai_provider_contract_v1,
  ai_council_contract_v1,improvement_proposal_v1}.json` (+ additive ops-fields in agent_contract_v1)
- Docker target (design-only, not built): `deployment/docker-compose.target.yml`
- Tests: `tests/test_runtime_w11.py` (44) — suite 145 → 191

## W12 additions (Lane B, execution + intelligence) — 2026-08-13
- F1-S1 EXECUTED (owner-authorized W12 PART B): `engine/f1_s1_migration.py` (drill/apply/rollback,
  probe sets W12A-F1S1-{BEFORE,DRILL,APPLY,ENFORCE}) — drill SAFE on copies → apply OK live,
  census data_identical=true; guards now: e01 10 on 5 history tables + ahos_local 2 on
  control_flags + paper 34/17 untouched; live UPDATE-abort probed; t12 cycle ran clean WITH
  guards. Reports: `reports/f1_s1_{drill,apply}_20260813T025708Z.json`. Claims repaired to
  measured truth: CRYPTO-02 back to EXISTING; AG-17 promoted PARTIAL→EXISTS (9/12/3/1).
  Execution record: `docs/architecture/F1_RESOLUTION_PLAN.md` §7 (S2–S5 stay DESIGN-ONLY).
- Runtime architecture: `docs/architecture/AHOS_RUNTIME_ARCHITECTURE_v1.md` (production topology,
  single-start contract, observability stack; infra stays DESIGN-ONLY per PART O).
- AG-25 Open-Source Capability Intelligence registered (PLANNED/ADVISORY; DISCOVERY→PROPOSAL
  only); spec `docs/architecture/OSS_CAPABILITY_DISCOVERY.md`; first read-only audit
  `reports/oss_capability_audit_1.json` (probe W12A-OSS-1): temporalio/sdk-python ⇒ NO_INTEGRATION
  (host-gated), promptfoo + crewAI ⇒ CANDIDATE_HELD_UNVERIFIED.
- Registry/matrix counters refreshed (25 agents; principles EXISTING 24 / PARTIAL 20 / DEFINED 19);
  tests 191 → **198** (`tests/test_f1_s1.py`, 7).

## W12 addendum (directive re-issue — Lane-A t13 + PART J/K/N closure) — 2026-08-13 ~03:30Z
- Lane A t13 executed: collector 68 new tokens, 0 errors (all sources OK, fresh PRB battery);
  paper cycle 11/11 `NO_DATA(STALE_OBSERVATION)`, cash unchanged, 0 closed —
  `research/experiments/e01_collection_t13_20260813.json`, `reports/paper_cycle_20260813_032731.json`,
  `reports/pal_probe_20260813_*_sandbox.json`.
- PART J closed: `engine/agent_matrix_v2.py` (deterministic generator, never hand-edited) →
  `docs/architecture/agent_matrix_v2.md` (25 agents × 16 mandated fields; typed-IO honestly
  queued to contract v2/F3) + `tests/test_agent_matrix_v2.py` (5: freshness/once-coverage/
  16-fields/owner+authority/no-invented-IO).
- PART K closed: `docs/architecture/SELF_EVOLUTION_LOOP.md` — 15-stage owner loop mapped onto
  improvement_proposal_v1 machinery; AI-direct-modify prohibition contract-pinned.
- PART N registered in `AHOS_RUNTIME_ARCHITECTURE_v1.md` §7 (master loop, self-reinforcing in
  observation only); PART C canonical diagram added verbatim §1; PART D chain §3; PART L
  enumeration §4. Tests 198 → **203**.

## W13 additions (MASTER ROADMAP audit-first wave) — 2026-08-13 ~04:0xZ
- Reality audit: `docs/mission_v1_1/W13_REALITY_AUDIT.md` (W12-vs-workspace reconciliation §0;
  all 20 §32 sections measured; G-SCHED + AG-01 + typed-IO/F3 gaps surfaced; §33 priority plan
  with PART-35 justification for the single permitted build).
- Lane A t13+t14 standing cycles: 722 tokens / 924 observations / 0 resolved (NOT YET VALIDATED);
  evidence `research/experiments/e01_collection_t1{3,4}_20260813.json` + cycle/probe reports.
- OSS Tier-1 batch-2: `reports/oss_capability_audit_2.json` (probe W12A-OSS-2; 5 candidates,
  all CANDIDATE_HELD_UNVERIFIED or archived-REJECT by rule).
- AG-25 Tier-1 executor versioned: `engine/oss_audit.py` + `tests/test_oss_audit.py` (5;
  network-free injected fetcher; verdicts never auto-granted; rate cap law). Suite 203 → **208**.
- W13b soak/fault-injection battery: `tests/test_control_plane_soak.py` (8) — single-fault
  property (real config), seeded 64-combo fuzz, 150-op soak, crash+resume, fail-fast storage
  loss, lock flood, history non-rewrite, prober-crash honesty; runtime v1 §3 annex carries the
  evidence summary + the clock-derived run-id design boundary. Suite 208 → **216** (R-37, P24).
- W13c: `docs/mission_v1_1/F12_DECISION_MEMO.md` — observation-starvation measurement (762 tok:
  only 1 with ≥12h span; 826 missed-snapshot rows; consumers read stored series only) + owner
  options O1/O2/O3 for the versioned observability amendment; decisive for the 08-14 gate's
  interpretation (R-38, P25). t16 skipped-with-published-reason (sampling hygiene).
- W13d: `docs/mission_v1_1/E01_GATE_PROTOCOL_v1.md` — PRE-REGISTERED judgment rules (R1–R8) for
  the 08-14 18:00Z gate; sha256 registered (R-39) + CI-pinned (`tests/test_e01_gate_protocol.py`);
  anti-post-result-tuning made structural. Suite 216 → **219** (P26).

## W14 additions (F12-O2 executed + t17 cycle; 2026-08-13 04:30–05:0xZ)
- F12-O2 (owner-approved, strict evidence boundaries): **`discovery/observe_active.py` v1** —
  NEW FILE only; reuses `lifecycle.due_snapshots` + `observations.record_observation/store_raw` +
  `collect.normalize_dex_pairs` + existing PAL dexscreener client; wrong-token hard guard;
  truth-by-`changes()` recording. 14 tests (`tests/test_observe_active.py`; 3 red-team + census).
  Isolation run on live copy (6 rec/14 fail), activation run 2026-08-13T04:30Z epoch
  **1786595433.489443** (14 priced + 26 explicit failure rows; `reports/observe_active_20260813_activation.json`).
- Boundary census SHA-PROVEN pre⇒post: tokens/pairs/lifecycle_events/gap_register/outcome_label/
  gate_summary identical; obs 987→1027 pure appends, every new row ts ≥ activation.
  **PRE_FIX = retrieved_ts < 1786595433.489443 · POST_FIX = ≥** (owner-mandated split; never merge).
- Coverage guardrail: **`engine/coverage_audit.py`** + 4 tests — 5-block invariant bundle
  (collection health / freshness / horizon coverage / gap detection / recovery status) + frozen
  v1 classifier; activation verdict **DEGRADED** (honest, expected to recover over cadence).
- Register R-40 carries the full no-silent-repair disclosure + binding gate-report disclosure
  addendum (collector/poller versions, activation ts, pre/post coverage, missing+stale obs,
  provider/collection failures, coverage by horizon — never one merged metric). P27. Suite **234**.
- **t17 standing cycle (04:39–04:47Z):** collect +67 ingested (tokens table 762→**818** net;
  failure-tolerant dedup), poller run #2 (40 attempted/14 recorded/26 explicit failures —
  `reports/observe_active_20260813_t17.json`), paper cycle (400 scanned, 0 entries [liquidity
  floors + insufficient coverage], 11 monitored ⇒ 11 `NO_DATA`, 0 exits, cash conserved,
  `reports/paper_cycle_20260813_043935.json`), probe battery PRB-20260813 12 OK/5 down-degraded
  (unchanged known set: llamarpc 521, helius-public 401, cryptopanic 404, cloudflare/ankr
  degraded), coverage_audit: **DEGRADED**, fresh share 0.727→**0.746**, gaps 826 total/580 24h
  (static — sweeps register), horizon coverage NULL@0-resolved (honest) — `reports/coverage_audit_20260813_t17.json`.
- **MEASURED LIMITATION (open, PT-STARVATION-LINK):** poller selection = `ORDER BY first_seen_ts`
  × `--max-tokens 40` ⇒ identical 40-token head across activation & t17 runs (overlap 40/40
  tokens; old slots' tolerance windows are past ⇒ head slots permanently uncoverable, queue
  drains only as head tokens hit RESOLVED at t0+72h ≈ 2026-08-14→15). All 11 open PT positions
  rank **235–321** in the due order ⇒ unreached ⇒ NO_DATA streak continues. Remaining salvageable
  slots: **s+24h windows today** — 07:15Z-entry cohort: obs within **06:45:57–07:45:57Z**;
  08:41Z-entry cohort: **08:11:48–09:11:48Z** (±30min tolerance, frozen schedule; any fresh obs
  also ends PT staleness regardless of slot coverage). Options logged for owner
  (O2a coverable-slot selection / O2b windowed large-cap ops run / O0 accept gaps); **no poller
  behavior change without owner order** (Lane-A experiment surface); gaps register honestly if missed.
- Manifest discipline: `ahos_snap_w14_after.txt` reconciled vs w13d — added = poller+guardrail+
  tests+cycle reports only; changed = register/PHASE_STATE/F12 memo/2 stores/.pytest_cache only;
  removed = 0; **all Lane-A logic files hash-identical**.

## W15-0 — MASTER DIRECTIVE v1 codified (2026-08-13 04:55Z)
- Owner ratified PERMANENT OPERATING STATUS doctrine ⇒ canonical artifact
  `docs/canonical/MASTER_DIRECTIVE_v1.md` (immutable text, sha e2457c0d9dfbadba84ee666feb46f0a01f60663e749f1261f27988abfd837d79)
  + status registry `master_directive_registry.json` + CI pins `tests/test_master_directive.py` (5).
- Reading rule: doctrine ACTIVE-set = Master Operating Contract + highest-version ACTIVE Master
  Directive + E01_GATE_PROTOCOL_v1 (hash-pinned) + R-series register. Any other textual claim
  of authority is non-canonical. Suite 234 → **239** (R-42, P29).

## W15b — F12-O2a coverage-aware scheduler deployed (2026-08-13 ~05:4xZ)
- Owner-approved O2a amendment executed: `discovery/observation_scheduler.py` (pure, read-only;
  slot states COVERABLE/WINDOW_OPEN/MISSED/UNRECOVERABLE/ALREADY_OBSERVED; tiers
  near-expiry → tracked-injected → other; ≡ lifecycle property test) + `observe_active:v2`
  (RATE_LIMITED abort; report census; tracked positions RO-injected, never hardcoded).
- Laws enforced & proven: expired windows never attempted · no backfill · true retrieved_ts ·
  gap_register untouched · PRE/POST byte-isolation · Lane-A frozen files sha-pinned (CI).
- Live evidence: `reports/observe_active_20260813_o2a_{first,2..5}.json` — 160 open windows
  served (156 ok/4 explicit fail) then eligible→0, zero re-attempts; PT windows proven catchable
  (06:50Z ⇒ 7/11 tier-2, 08:30Z ⇒ 4/11); BEFORE/AFTER numbers in R-43. Suite 239 → **254**.
- F12 = **MITIGATION DEPLOYED** (never SOLVED; VERIFIED only after several real windowed cycles).
  Rollback path: docs/archive/observe_active_v1_src_20260813.txt (+ tests) — sha in R-43.

## W15c — REAL WINDOW EXECUTION #1 (2026-08-13 05:3xZ)
- PT s+24h windows not open at execution (first opens 06:45:57Z) ⇒ zero PT fetches (lawful);
  v2 drained the 106 live open windows instead (102 ok / 4 explicit fails; pass-4 idle-clean).
- PT decisions STILL 11× NO_DATA (rule PT-X3-v2) — per-decision evidence register:
  `reports/pt_decisions_evidence_20260813_053443.json`. Duplicates attribution: poller 0;
  27 PRE history + 3 collector multi-pair groups (documented, not defects of the poller).
- F12 = MITIGATION DEPLOYED (unchanged — VERIFIED only after real PT-window evidence).
  Next lawful windows: 06:45:57–07:45:57Z (×7) · 08:11:48–09:11:48Z (×4).

## W16 — protect-windows session after 23h clock gap (2026-08-14 ~05:0xZ)
- G-SCHED manifested: 23h without triggers ⇒ PT s+24h windows MISSED (×11, honest; no backfill).
- Lawful drain: 56 legal windows → 23 obs + 33 explicit no_valid_price; digest
  `reports/observe_evidence_20260814_session.json` (56/56 in-window, true timestamps).
- §O 24h PT report delivered late with cause: `reports/pt_x3_v2_24h_report_20260814.md`.
- Gate arithmetic (measured): earliest first_seen 2026-08-11 18:00Z ⇒ resolvable-by-gate 0 ⇒
  lawful expectation at 2026-08-14 18:00Z: INSUFFICIENT_DATA (final word = audited run).
- F12: MITIGATION DEPLOYED (NOT VERIFIED). Next PT chances: s+48h windows today 06:45:57Z/08:11:48Z.

## W17 — E-01 GATE DAY pre-window cycle (2026-08-14 05:1xZ)
- Window discipline held: PT s+48h windows open 06:45:57Z/08:11:48Z later today ⇒ no PT fetch.
- 134 legal windows drained (118 obs + 16 explicit no_valid_price; pass-5 idle-clean); digest
  `reports/observe_evidence_20260814_session2.json`; PT decisions evidence
  `reports/pt_decisions_evidence_20260814_051716.json` (11× NO_DATA, lawful).
- Gate stays 18:00Z — staged, not pulled. F12 = MITIGATION DEPLOYED. NOT YET VALIDATED.

## W18 — E-01 GATE EXECUTION (2026-08-14 18:06–18:2xZ) — INVALID_PROTOCOL + NOT YET VALIDATED
- Gate ran on time per owner order; governance hashes pinned; workspace sha-identical.
- NEW FINDING D-FS-01: discovery/feature_store.py:157 asymmetric zero-volume guard (last_v1 not
  checked) ⇒ ValueError on 24/952 tokens; latent in frozen code; surfaced by live data at gate.
  Write-safety: implicit rollback ⇒ zero mutation; integrity_check ok; freeze held (no gate-day fix).
- Gate results: R1 0/0 (gate metric <200); R2 PRE 987obs/762tok · POST 749/451; horizon coverage
  s+12h=0% / s+48h=0% (G-SCHED; today's K1×7+K2×4 s+48h buried by 05:19Z→18:06Z session gap);
  R4 9/9 INSUFFICIENT_DATA; R5 Track B 0/0 NOT MET. Verdict INVALID_PROTOCOL; data independently
  forces INSUFFICIENT_DATA. E-01 = NOT YET VALIDATED. F12 = MITIGATION DEPLOYED (unchanged).
- Artifacts: R-47 (with sha refs) + reports/e01_gate_* + research/reports/baseline_stats_e01_gate_*;
  Experimental Validation Report reports/e01_experimental_validation_report_20260814.md (fa+en).
- Next: owner-gated minimal fix (guard + red-first test) ⇒ identical frozen gate re-run (idempotent).

## W19 — D-FS-01 Amendment, E-01 Replay, and Production Architecture Build (2026-08-15)
- A-1 minimal fix in `discovery/feature_store.py:157` applied test-first (`tests/test_feature_store_boundaries.py` RED->GREEN); archived pre-fix source `docs/archive/feature_store_v1_src_20260814.txt` (sha `202bbe6d4f6b...`); amended sha `d3086e729f5c...` pinned.
- Frozen E-01 gate replayed: `discovery.materialize` ran with 0 errors (6,745 features, 223 RESOLVED, 729 DEAD, 5,339 gap rows, 1,048 outcomes); R1 52/200 (<200); R2 PRE 987 / POST 749; R4 9/9 INSUFFICIENT_DATA; R5 Track B 0/0 NOT MET. Protocol verdict: **INSUFFICIENT_DATA**. Experiment status: **NOT YET VALIDATED**.
- Production architecture foundations delivered in isolated lane:
  - Provider Abstraction (`architecture/providers/`): BaseMarketProvider, DexScreener, GeckoTerminal, GoPlus, RugCheck, ProviderRouter, explicit UNKNOWN handling.
  - Opportunity Scoring (`architecture/scoring/`): 8-stage pipeline (DATA->SIGNALS->EVIDENCE->FEATURES->RISK->OPPORTUNITY->CONFIDENCE->INVALIDATION), deterministic $0 decision floor, answers 8 canonical questions.
  - Telegram Persian Interface (`telegram_ai/`): NLU parser, Section X response contract formatter, TelegramDomainService, footer «تصمیم نهایی با کاربر است.».
  - Paper Position Manager (`architecture/positions/`): event-sourced position manager, fees, slippage, realizable PnL, invalidation exits, stale observation NO_DATA holds.
  - Alert Engine (`architecture/alerts/`): deterministic alert generator with WHY-law compliance.
  - Production Scheduler (`architecture/scheduling/`, `docs/architecture/PRODUCTION_SCHEDULER_SPEC.md`): wall-clock alignment, leasing locks, clock drift checks.
  - Security & Observability (`architecture/security.py`, `architecture/observability.py`): secret redaction, structured JSON tracing.
- Test Suite: 290 passed (36 new tests added, 0 failures). Governance hashes verified. Manifest `ahos_snap_w19_after.txt`.

## W20 — Phase XX: Production Runtime Layer, Collector, Pipeline, and Test Suite Expansion (2026-08-15)
- Production Runtime Layer (`architecture/runtime/`): `ApplicationLifecycleManager`, `StartupValidator` (governance hash & DB check), `HealthCheckRegistry`, `JsonFormatter` (structured logging with `run_id`).
- Continuous Market Collector (`architecture/collector/`): `CollectorEngine` multi-provider polling (DexScreener, GeckoTerminal, GoPlus, RugCheck) with `CircuitBreaker` (CLOSED/OPEN/HALF_OPEN), `RetryPolicy`, and `CollectedObservationRecord` provenance persistence.
- Production Scheduler Enhancement (`architecture/scheduling/`): heartbeat tracking, downtime detection, and automated `missed:<slot>` honest gap registration in `gap_register`.
- Telegram Production Adapter (`telegram_ai/`): `TelegramBotAdapterInterface`, `MockTelegramAdapter`, `ProductionTelegramAdapter`, `TelegramSecurityGate`, and `TelegramBotRunner`.
- End-to-End Opportunity Pipeline (`architecture/pipeline/`): `OpportunityPipelineOrchestrator` linking Providers -> Normalization -> Evidence -> Features -> Risk -> Opportunity Score -> Alert -> Telegram.
- Deployment Assets (`deployment/`, `docs/architecture/`): `Dockerfile`, `docker-compose.production.yml`, `.env.example` (zero secrets), container `healthcheck.py`, and `PRODUCTION_RUNTIME_SPEC.md`.
- Test Suite: Expanded from 290 to **411 passed tests (121 new tests added, 0 failures)**. Manifest `ahos_snap_w20_after.txt`.

## W21 — Phase XXI: Production Reality Audit, Executable Hardening, and 450 Tests (2026-08-15)
- Independent Reality Audit (`reports/phase21_reality_audit.md`): Verified all 16 subsystems.
- Implemented authoritative runtime CLI entrypoint `architecture/runtime/__main__.py`. Executed `python3 -m architecture.runtime --single-cycle` in bash (13 tokens scored, structured JSON logs, exit 0).
- Implemented real endpoint calls on `GeckoTerminalAdapter.fetch_token_metrics` and `RugCheckSecurityAdapter.fetch_candidate_tokens`.
- Added multi-thread concurrency lease safety in `ProductionScheduler.acquire_lease`.
- Production Readiness Scorecard (`reports/phase21_production_readiness.md`): Overall score **91.81 / 100**.
- Test Suite: Expanded to **450 passed tests (100% green, 0 failures)** across 43 test suites. Manifest `ahos_snap_w21_after.txt`.

## W22 — Phase XXII: Global Intelligence Integration & Multi-Mind Council (2026-08-15)
- K-01 Knowledge & Trust Registry (`architecture/knowledge/trust_registry.py`): 7-rank epistemic hierarchy (`RAW_FACT` to `SPECULATION`), seeded with Shannon, Nakamoto, Kahneman, Mandelbrot, Taleb.
- K-02 Versioned Claim & Evidence Store (`architecture/knowledge/store.py`): Append-only claim versioning, contradiction tracking, epistemic AI-canonical isolation.
- K-03 Expert Lens Library (`architecture/knowledge/lenses.py`): 10 pilot data cards (Shannon, Von Neumann, Mandelbrot, Kahneman, Munger, Taleb, Nakamoto, Finney, Buterin, Marks) with documented failure modes, mental models, citations, and zero persona fabrication.
- K-04 Open Source & GitHub Harvest Pipeline (`architecture/knowledge/oss_pipeline.py`): 12-stage research pipeline enforcing license compatibility and benchmark lift verification over star counts.
- Multi-Mind Council Synthesis (`architecture/council.py`): `synthesize_multi_mind_council` enforcing *Evidence > Consensus*.
- Anti-Echo-Chamber Engine (`architecture/knowledge/anti_echo.py`): Copied reasoning detector, source monoculture detector, and mandatory contrarian slot inversion.
- Controlled Self-Evolution (`architecture/evolution/engine.py`): 14-stage proposal validation with mandatory human approval gates and rollback plans.
- Test Suite: Expanded to **475 passed tests (100% green, 0 failures)** across 48 test suites. Manifest `ahos_snap_w22_after.txt`.

## W24 — Phase XXIV: Operational Activation & Continuous Intelligence Platform (2026-08-15)
- Continuous Execution Daemon (GAP-01): `python3 -m architecture.runtime --daemon` executed live with process persistence, atomic lease locking, and graceful shutdown.
- Knowledge Memory Activation (GAP-06): `KnowledgeSyncBridge` populated 22 empirical claims into `data/ahos_knowledge.sqlite` from E-01 replay outcomes, baseline research, and strategy rejections.
- Operational Observability Layer: `OperationalMetricsTracker` recording live cycle duration, scores, and alerts into `ahos_local.sqlite`.
- Failure Matrix & Resilience: Verified offline network, provider 503, locked DB, and lease recovery.
- Test Suite: Expanded to **481 passed tests (100% green, 0 failures, 0 warnings)** across 49 test suites. Manifest `ahos_snap_w24_after.txt`.

## W25 — Master Agent Mission: Windows 11 Compatibility, Self-Repair & Hardening (2026-08-16)
- Cross-Platform Dynamic Path Resolver (`config/paths.py`, `config/paths.yaml`): Eliminates hardcoded Linux paths.
- Windows One-Click Installers: `install_windows.ps1`, `start_ahos.ps1`, `start_ahos.bat`.
- Self-Repair Health Manager (`engine/health_manager.py`): Diagnostic engine detecting issues and generating `reports/health_report.json` (Status: GREEN).
- Update Governance (`engine/update_manager.py`): Operates in CHECK_ONLY mode; enforces Master Directive hash locks and human approval gates.
- Logical AI Assistant Roles (`config/ai_assistants.yaml`, `architecture/knowledge/assistants.py`): 9 logical assistant roles defined.
- Complete Documentation Suite: `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `INSTALLATION.md`, `ARCHITECTURE.md`, `AHOS_WINDOWS_DEPLOYMENT_GUIDE.md`, `AHOS_SELF_REPAIR_DESIGN.md`, `AHOS_UPDATE_POLICY.md`, `AHOS_FINAL_STATUS.md`.
- Test Suite: Expanded to **493 passed tests (100% green, 0 failures, 0 warnings)** across 53 test suites. Manifest `ahos_snap_w25_after.txt`.

## W26 — Phase 1: Reality-Locked Hardening, 100 Cognitive Minds & NVIDIA NIM (2026-08-16)
- NVIDIA NIM Provider Contract (`config/ai_provider_registry.yaml`): OpenAI-compatible contract pointing to `https://integrate.api.nvidia.com/v1` with model `meta/llama-3.1-70b-instruct` and `key_env: NVIDIA_API_KEY`.
- 100 Unique Cognitive Minds Catalog (`config/cognitive_registry_100.yaml`): Declared all 100 unique thinkers across 8 domains (with John Nash, Ken Thompson, and George Boole replacing duplicate slots).
- Expert Lens Data Cards (Batch 2): Expanded `architecture/knowledge/lenses.py` to 20 instantiated Data Cards (adding Nash, Thompson, Boole, Turing, Gödel, Bayes, Fisher, Pearl, Schneier, Brewer).
- Knowledge Sync Bridge: Populated 32 empirical claims into `data/ahos_knowledge.sqlite`.
- Test Suite: **493 passed tests (100% green, 0 failures, 0 warnings)** across 53 test suites. Manifest `ahos_snap_w26_after.txt`. Zero live trading, zero credential exposure.

## W27 — Phase 2: Forensic Verification & Zero-Regression Operational Hardening (2026-08-16)
- Track B Portfolio Invariant: Verified exact arithmetic balance ($1.8984375 cash + $18.1015625 allocated = $20.0000000 exact sum).
- E-01 Insufficient Data Invariant: Verified $n=52 < 200$, no artificial promotion.
- G-SCHED & Provider Isolation: Proven atomic lease crash recovery and circuit breaker isolation under provider failure.
- NVIDIA NIM Fallback: Verified OpenAI-compatible routing fallback to $0 deterministic floor.
- Test Suite: **500 passed tests (100% green, 0 failures, 0 warnings)** across 54 test suites. Manifest `ahos_snap_w27_after.txt`. Zero live trading, zero credential exposure.

## W28 — Phase 3: Forensic Reconnaissance, System Health NLU & 30 Cognitive Cards (2026-08-16)
- Operational Diagnostics in Telegram (`telegram_ai/service.py`, `intent.py`): Implemented `SYSTEM_HEALTH` intent delivering real-time database, token, and metrics diagnostics with mandatory footer.
- Cognitive Knowledge Expansion: Added Data Cards 21–30 to `architecture/knowledge/lenses.py` (Lovelace, Hopper, Dijkstra, Knuth, Ritchie, Hamilton, Liskov, Lamport, McCarthy, Minsky).
- Knowledge Claims Sync: Synced 30 expert lens claims into `data/ahos_knowledge.sqlite`.
- Test Suite: **505 passed tests (100% green, 0 failures, 0 warnings)** across 55 test suites. Manifest `ahos_snap_w28_after.txt`. Zero live trading, zero credential exposure.

## W29 — Phase 4: Canonical Observability Snapshot & Telegram Operational Plane (2026-08-16)
- Canonical Health Snapshot Engine (`architecture/runtime/observability_snapshot.py`): Outputs `reports/canonical_health_snapshot.json` exposing complete runtime, scheduler, provider, database, and E-01/Track B health.
- Telegram Operational Read-Only Plane: 8 operational query intents (`SCHEDULER_STATUS`, `DATABASE_STATUS`, `PROVIDERS_STATUS`, `OBSERVATION_GAPS_STATUS`, `E01_STATUS`, `PAPER_TRADING_STATUS`, `AI_STATUS`, `LAST_CYCLE_STATUS`).
- Negative Allocation & Accounting Conservation: Verified Track B exact arithmetic balance ($1.8984375 cash + $18.1015625 allocated = $20.0000000).
- Test Suite: **516 passed tests (100% green, 0 failures, 0 warnings)** across 56 test suites. Manifest `ahos_snap_w29_after.txt`. Zero live trading, zero credential exposure.

## W30 — Phase 4: Re-Audit, Test Path Portability & UTF-8 Encoding Hardening (2026-08-16)
- Test Path Portability: Replaced hardcoded `/home/user/ahos` strings across `tests/*.py` with dynamic `Path(__file__).resolve().parents[1]` and `config.paths`.
- Explicit UTF-8 Encoding: Standardized text read/write calls with explicit `encoding="utf-8"` for cross-platform Windows/Linux parity.
- Lane A Hash Integrity: Verified byte-identical hash for `discovery/collect.py` (`974f8650...`), Master Directive v1 (`e2457c0d...`), and E01 Protocol v1 (`16b86b86...`).
- Test Suite: **516 passed tests (100% green, 0 failures, 0 warnings)** across 56 test suites. Manifest `ahos_snap_w30_after.txt`. Zero live trading, zero credential exposure.

## W31 — Master Directive: Engine Tools Path Portability & CI Verification (2026-08-16)
- Engine Tools Portability: Standardized path resolution in `engine/*.py` scripts using `config.paths` and dynamic `ROOT_DIR`.
- CI Script Validation: `engine/run_all_checks.sh` executed and passed all 6 stages completely (Data audit, test_ahos, test_strategy_lab, test_discovery, test_baseline_stats, test_wave7_research, test_telegram_ai, test_paper_trading, dryrun, telegram live test, n8n validation).
- Lane A Hash Integrity: Verified byte-identical hash for `discovery/collect.py` (`974f8650...`), Master Directive v1 (`e2457c0d...`), and E01 Protocol v1 (`16b86b86...`).
- Test Suite: **516 passed tests (100% green, 0 failures, 0 warnings)** across 56 test suites. Manifest `ahos_snap_w31_after.txt`. Zero live trading, zero credential exposure.

## W32 — Month 2: CoinMarketCap + pump.fun launchpad adapters, PAL rate/breaker sync (2026-08-20)
- CoinMarketCap adapter (`architecture/providers/coinmarketcap.py`): keyed free tier, inert NO_KEY
  until `COINMARKETCAP_API_KEY` (DEXTools pattern, zero traffic unconfigured); two-step
  info+quotes lookup → real market cap/FDV/volume/price-change/social; chain-aware platform
  matching; AUTH_REQUIRED/RATE_LIMIT/DOWN distinction; wired into `ProviderCollector` last
  (fills UNKNOWNs only). 20 offline tests.
- pump.fun launchpad adapter (`architecture/providers/pumpfun.py`): keyless Solana launchpad
  discovery feed, discovery-only, Solana-only; missing fields stay UNKNOWN; DOWN/RATE_LIMIT/
  OK-empty distinction. 11 offline tests. Both registered in `ProviderRouter` +
  `--probe-providers`.
- PAL rate/breaker sync law: `tests/test_provider_yaml_sync.py` pins adapters ≤ frozen
  `discovery/providers.yaml` rates (dexscreener 120/geckoterminal 24/goplus ~20/rugcheck 30 rpm)
  and collector breakers (threshold ≤ PAL, recovery ≥ PAL cooldown).
- M-GAP-004 re-verified: `.github/workflows/ci.yml` push still rejected (App lacks `workflows`
  permission); workflow kept untracked, ready when permission is granted.
- Test Suite: **1225 passed (100% green)**; gate artifacts refreshed
  (`reports/pytest_run.json`, `reports/validate_imports_run.json` — PASS, Lane-A frozen).
  Zero live trading, zero credential exposure.

## W33 — Month 3: Score-vs-outcome calibration surface (2026-08-20, M-GAP-008 infra)
- Extended the canonical calibration harness (`architecture/learning/calibration.py`,
  report schema v3 — no parallel analytics subsystem):
  - Confidence-bucket segmentation (HIGH/MED/LOW + UNKNOWN bucket; ordering /
    inversion verdicts pin over/under-confidence) and chain segmentation, with the
    same pre-registered guards as score bands (never more permissive).
  - Continuous outcomes per band: mean/median max_favorable, mean max_adverse,
    mean_score, calibration_delta (rate − mean_score/100 ⇒ per-band over/under-confidence).
  - Diagnostics over the joined cohort: Brier on normalized score (explicitly a
    ranking diagnostic, not a probability claim), base-rate Brier + resolution,
    ECE over pre-declared bands, Spearman rank (score vs hit, score vs max_favorable)
    — pure-stdlib implementations, deterministic.
  - Evidence-coverage census, extreme-record provenance (top/bottom 3 scored rows
    with evidence sha), honest dimension-availability (provider / market_regime /
    opportunity_type NOT_PERSISTED_AT_PREDICTION_TIME — never fabricated).
  - Multi-horizon `run_many` + CLI `--all-horizons` (combined artifact,
    per-horizon provenance); INSUFFICIENT_DATA default unchanged; sample-size
    warnings travel with descriptive metrics.
- Tests: 21 new (`tests/test_calibration_extended.py`: empty/insufficient/valid
  cohorts, bucket aggregation, confidence/chain segments, missing fields, UNKNOWN
  buckets, mixed versions, multi-horizon, determinism, no-fabrication, CLI).
- Runtime: `scripts/calibration_report.py` artifacts committed — honest
  INSUFFICIENT_DATA (0 `local` pairs; real measurement still blocked on data
  accrual per M-GAP-008). Suite 1232 → **1253 passed**; zero live trading.
- Follow-up (same wave): **provider segmentation closed** — `source_provider` is
  now stamped on `OpportunityScoreReport` at scoring time (both `evaluate()` and
  the pipeline's `from_intelligence` path) and persisted in
  `opportunity_score_ledger.source_provider` (idempotent additive migration for
  legacy stores; legacy rows stay NULL → UNKNOWN bucket). Calibration report
  schema v4 adds `provider_segments` (same pre-registered guards) and an
  `outcome_provenance` block (frozen Lane-A labeler identity). Opportunity-type
  remains honestly NOT_PERSISTED — no such concept exists in the scoring
  contract and the harness does not invent one. Suite **1257 passed**.
- **Regime segmentation (schema v5):** token_price_regime computed post-hoc at
  evaluation time from PRE-prediction observations per token (no-peeking:
  `retrieved_ts <= scored_ts`) via the existing
  `architecture/intel/regimes.py` classifier — its first production consumer.
  Fewer than 10 pre-prediction observations ⇒ UNKNOWN bucket (never a default
  regime). `regime_segments` added to the report; dimension_availability
  documents the post-hoc computation honestly. Suite **1261 passed**.
- **Weight-governance acceptance tool (W33d):** `scripts/calibration_diff.py`
  diffs two calibration report artifacts (`ahos.calibration_diff.v1`,
  deterministic) — per-band rate deltas only when both sides are DESCRIPTIVE_OK
  on the same horizon+event_class, monotonicity + diagnostic deltas, full
  provenance of both sides; honest NO_COMPARABLE_BANDS while evidence is
  insufficient, IDENTICAL_DATASETS nulls rate deltas, missing artifact exits 2.
  This is the roadmap's "any weight change ⇒ calibration diff attached to PR"
  acceptance tool. Suite **1269 passed**.
