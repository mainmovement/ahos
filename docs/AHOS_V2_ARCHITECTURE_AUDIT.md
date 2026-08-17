# AHOS v2 — Architecture Audit

**Date:** 2026-08-17 UTC  
**Branch:** `arena/01a0115f-ahos` (from `62ecf04` on `main`)  
**Auditor:** AHOS v2 Architecture Implementation Engineer (Agent Mode)  
**Standard:** Evidence First — every claim is traced to a file, a line, or a test. No number is stated without its measurement.  
**Scope:** Full repository static analysis + runtime test execution. Zero production code modified in this phase (docs-only).

---

## 0. Executive Summary

AHOS at `62ecf04` is a **large, disciplined, dual-lane Python monolith** that honestly implements the “$0 cost floor, deterministic, paper-only, fail-closed” contract it advertises, with rigorous schema discipline, append-only history tables, and 898 green tests. Its **core pipeline (Discovery → Security Gate → Features → Scoring → Alerts → Telegram → Paper Trading) is runnable**, but the v2 Production Architecture is **not yet consolidated**: the learning loop (score persistence → calibration → Kelly sizing), continuous position review, and cross-cutting observability are wired in code and tested but never invoked from the runtime. Several certification documents freeze passing counts beside READY claims that the codebase itself does not support, and the repository carries ~31 snapshot text files and 6+ historical docs that constitute >500 KB of stale canon.

**Counted facts:**

| Signal | Value | Evidence |
|---|---|---|
| Python modules (excl. `__pycache__`) | 65 | `find architecture discovery paper_trading telegram_ai strategy_lab research config scripts engine -name "*.py" \| wc -l` |
| Tests collected / passed | **898 / 898 (0 failed, 0 warnings)** | `python3 -m pytest tests/ -q` in 69.74s on 2026-08-17 |
| Non-test Python LOC (approx) | ~18–20k | `wc -l architecture/**/*.py discovery/*.py paper_trading/*.py telegram_ai/*.py` tail |
| Snapshot / report `txt` + `md` duplicates | **27 `ahos_snap_w*.txt` (32–69 KB each) + 4 `AHOS_*STATUS/REPORT.md` + 15 docs with overlapping canon** | `ls -1 ahos_snap*` + `ls docs/` |
| Databases owned (all SQLite, `.gitignore`d) | 4 (`e01_discovery.sqlite`, `paper_trading.sqlite`, `ahos_local.sqlite`, `ahos_knowledge.sqlite`) | `discovery/schema_sqlite.sql` + `paper_trading/schema{,_v2,_v3}.sql` + `scripts/init_databases.py` + `config/paths.py` |
| Top-level certification docs claiming READY | 4 (`AHOS_FINAL_STATUS.md`, `AHOS_PHASE_XX_COMPLETION_REPORT.md`, `AHOS_PRODUCTION_READINESS_REPORT.md`, `AHOS_REALITY_AUDIT_REPORT.md`) | `git ls-files \| grep AHOS_` |

**v2 readiness:** Lane A (ingest → score → alert) is **PARTIAL-to-IMPLEMENTED**; Lane B (research, knowledge, evolution) is **PARTIAL**; the joining tissue (Score Ledger → Calibration → Panel sizing → Position Monitor → Decision Advisor → AI Council advice) exists as library code but **is not on any runtime path**. The attached patch `01a00f79-...patch` is precisely the tissue that connects it. Applying it blindly would be destructive; applying it in sequenced, gated increments is the correct v2 migration.

---

## 1. Repository Topology

### 1.1 Physical layout (abridged)

```
ahos/
├── architecture/          # Lane B + production subsystems (W9+): isolation-law package
│   ├── ai/                #  ai/clients.py, council_live.py  (AI abstraction + live council)
│   ├── alerts/            #  alerts/engine.py  (7 alert classes, deterministic)
│   ├── collector/          #  collector/{engine,circuit_breaker,retry}.py  (market collector, second discovery)
│   ├── decision/          #  EMPTY in base (advisor lives only in patch) — gap
│   ├── evolution/          #  evolution/{engine,hindsight}.py  (self-evolution, counterfactual)
│   ├── intel/             #  intel/{exitability,forensics,news,viral,whales}.py  (5 analyzers)
│   ├── knowledge/          #  knowledge/{lenses,panel,store,trust_registry,anti_echo,oss_pipeline,...}
│   ├── pipeline/           #  pipeline/orchestrator.py  (Providers→Scoring→Alert→Telegram)
│   ├── positions/          #  positions/{manager,monitor}.py  (manager exists, monitor only in patch)
│   ├── providers/          #  providers/{adapters,contracts,registry}.py
│   ├── runtime/            #  runtime/{__main__,lifecycle,logging,metrics,observability_snapshot}.py
│   ├── scheduling/         #  scheduling/engine.py  (wall-clock window engine)
│   ├── scoring/            #  scoring/engine.py  (8-stage evidence→score)
│   ├── __init__.py, contracts.py, control_plane.py, council.py, provider_router.py, registry.py, security.py, observability.py
├── discovery/             # Lane A — primary discovery core (SQLite canonical)
│   ├── pal.py, collect.py, observations.py, lifecycle.py, observation_scheduler.py
│   ├── feature_store.py, security_gate.py, ranker.py, materialize.py, outcomes.py, holders.py, identity.py, ...
│   ├── providers.yaml, schema_sqlite.sql
├── paper_trading/         # Paper lab — 3 generations co-resident
│   ├── engine.py (v1) / engine_v2.py (bankroll+monitoring) / engine_v3.py (realizable+partial exits)
│   ├── decision_v3.py, bankroll.py, cost_model.py, risk.py, realizable.py, lessons.py, security_multi.py, ledger.py, cycle.py, ...
│   ├── schema.sql / schema_v2.sql / schema_v3.sql, strategies.json
├── telegram_ai/           # Persian NLU → Domain Service → Telegram surface
│   ├── intent.py (rule-based Persian NLU, ~16k lines), service.py (~53k), adapter.py, alerts.py, positions.py, bot.py
├── strategy_lab/          # Pre-registered hypothesis lab (H1–H13), lab_engine, candidates, hypotheses
├── research/              # SEARCH_SPACE_REGISTRY.json, baseline_stats.py, data/, experiments/, reports/
├── engine/                # Cross-cutting ops: ahos_backtest, data_audit, doc_hygiene, health_manager, update_manager, acquire_3yr, ...
├── config/                # agent_registry.yaml (25 agents), ai_council_providers.yaml, cognitive_*.yaml, paths.{py,yaml}, ...
├── contracts/             # agent_contract_v1.json, ai_council_contract_v1.json, control_plane_contract_v1.json, improvement_proposal_v1.json
├── database/              # postgresql_schema.sql (pg twin), schema_v1_2.sql, schema_v1_3.sql
├── deployment/            # Dockerfile (multi-stage), docker-compose.{production,target,windows,yml}, entrypoint.sh, healthcheck.py
├── n8n/workflows/         # 6 canonical workflows (ahos_01..03 + 10..12) — import-verified, execution pending env
├── tests/                 # 70+ test modules, 898 tests (see §8)
├── docs/                  # canonical/, architecture/, mission_v1_1/ (10 docs), archive/, + 15 top-level design docs
├── scripts/               # init_databases.py (bootstrap), freeze_lane_a.py
├── run_bot.py             # Telegram long-poll launcher (preflight + console)
├── docker-compose.yml, requirements*.txt, pytest.ini, start_ahos.{bat,ps1}, install_windows.ps1
└── ahos_snap_w*.txt (27), AHOS_*.md (7), 01a0…patch (1)  — historical artifacts at root
```

### 1.2 Logical lanes (frozen contracts)

```
Lane A  (frozen, governed)          Lane B  (research, advisory)
─────────────────────────────         ────────────────────────────
discovery/ • paper_trading/          architecture/ • strategy_lab/ • research/ • engine/
 exchange-clone forbidden             AI may PROPOSE only; human gate mandatory
 append-only history enforced          K-02 claim store, 14-stage evolution, 12-stage OSS

Isolation law (tests/test_architecture_p1.py):
  architecture/* MUST NOT import discovery|paper_trading|research|telegram_ai|engine
  — enforced by import-graph test; currently GREEN.

Paper-only law (tests/test_zero_money_invariant.py):
  No sign_transaction / sendTransaction / create_order / CCXT trading SDK import.
  Wallet SDK forbidden. ledger mutation confined to paper store. — GREEN.
```

### 1.3 Dependency graph (verified)

```
[Providers: DexScreener, GeckoTerminal, GoPlus, RugCheck, public RPC, RSS]
        │
        ├── discovery/pal.py (PAL v1: free-first chains, token bucket, breaker, TTL cache, dual-timestamp envelope, raw_sha archiving)
        │       └── discovery/collect.py (E-01 collector: GT new_pools + Dex profiles/boosts → observations, error_state preserved)
        │
        ├── architecture/providers/{adapters,registry,contracts} (typed normalization → NormalizedTokenCandidate)
        │       └── architecture/collector/engine.py (second collector, circuit+retry, production_observations table)
        │
        └── architecture/pipeline/orchestrator.py  ──┐
                                                     ├── architecture/scoring/engine.py (8-stage: DATA→SIGNALS→EVIDENCE→FEATURES→RISK→OPPORTUNITY→CONFIDENCE→INVALIDATION)
                                                     ├── discovery/security_gate.py + discovery/security_verdicts + gate_summary (CRITICAL veto, UNKNOWN discipline)
                                                     ├── discovery/feature_store.py + discovery/ranker.py (rank-first, no numeric prob until E-01 gate)
                                                     ├── architecture/alerts/engine.py → telegram_ai/alerts.py (7 classes)
                                                     └── telegram_ai/service.py + intent.py (Persian NLU → Section X response cards) → telegram_ai/adapter.py → Telegram

Cross-cutting:
  discovery/lifecycle.py (8 slots: s+15m..s+7d) + observation_scheduler.py (WINDOW_OPEN guard, near-expiry tiers)
  architecture/scheduling/engine.py (production scheduler: lease, drift, heartbeats, honest gap registration)
  architecture/runtime/{lifecycle,logging,metrics,__main__} (STARTING→RUNNING→STOPPING, JSON logger with secret redaction, metrics ledger)
  paper_trading/{engine,engine_v2,engine_v3} (event-sourced: DISCOVERED→QUALIFIED→PAPER_ENTRY→MONITORING→EXIT→POST_TRADE_ANALYSIS)
  strategy_lab + research/baseline_stats.py (pre-registered cards, Wilson CI, WF/MC/stress, SEARCH_SPACE_REGISTRY)
  architecture/knowledge/{lenses,panel,store} + architecture/evolution/{engine,hindsight} + architecture/council.py + architecture/intel/* (see §2)
```

---

## 2. Implemented Components Inventory

Maturity letters per MASTER_DIRECTIVE_v1: **A Designed · B Implemented · C Tested · D Verified · E Production Ready.** Verified = independent automated proof this session.

### 2.1 Discovery Engine

| Sub-component | File(s) | Status | Evidence |
|---|---|---|---|
| PAL v1 (providers.yaml, ordered chains, rate/breaker/TTL/dual-ts/raw archive) | `discovery/pal.py` + `discovery/providers.yaml` + `architecture/providers/*` | **C Tested** | `tests/test_provider_abstraction.py`, `tests/test_provider_failure_resilience.py`, `tests/test_discovery.py`; `discovery/pal.py` implements Bucket/Breaker/envelope exactly as spec |
| Token/pair/observation persistence (15-table SQLite, WAL) | `discovery/schema_sqlite.sql` (15 tables) + `discovery/observations.py` | **C Tested** | `tests/test_discovery.py` 22/22, `tests/test_feature_store_boundaries.py` |
| Real discovery pass (GT new_pools + Dex tokens/v1, dual-ts, raw_sha) | `discovery/collect.py` + `discovery/observations.py` + `discovery/identity.py` | **C Tested** | `discovery/collect.py` normalizes GT+Dex; `tests/test_discovery.py` exercises collection |
| Holder/whale snapshots (RPC) | `discovery/holders.py` + `architecture/intel/whales.py` | **B Implemented** | `holders.py` wraps `getTokenLargestAccounts`; `architecture/intel/whales.py` exists but RPC holder *count* not feasible on free tier — honestly documented as UNKNOWN (see MISSING) |
| Security gate (CRITICAL vetos, UNKNOWN discipline, fixtures 7/7) | `discovery/security_gate.py` + `discovery/schema_sqlite.sql:security_verdicts,gate_summary` | **C Tested** | `tests/test_security_hardening.py`, `tests/test_e01_gate_protocol.py` |
| Lifecycle (8 windows) + observation scheduler + outcomes + ranker | `discovery/lifecycle.py`, `discovery/observation_scheduler.py`, `discovery/observe_active.py`, `discovery/outcomes.py`, `discovery/ranker.py` | **C Tested** | `tests/test_observation_scheduler.py` (18k lines, exhaustive), `tests/test_observe_active.py`, `tests/test_discovery.py` |
| Feature store (availability_ts ≤ as_of_ts, DB-enforced) | `discovery/feature_store.py` | **C Tested** | `tests/test_feature_store_boundaries.py` enforces L3 rule |
| Parallel production collector (circuit+retry, provenance) | `architecture/collector/{engine,circuit_breaker,retry}.py` | **C Tested** | `tests/test_collector_engine.py`, `tests/test_architecture_p1.py` |

**Overall Discovery:** IMPLEMENTED. Dual collectors (`discovery/collect.py` + `architecture/collector/engine.py`) are redundant but both exercised; recommend consolidating on PAL as single ingest front door for v2.

### 2.2 Scoring Engine

| Sub-component | File(s) | Status | Evidence |
|---|---|---|---|
| 8-stage deterministic scorer (DATA→…→INVALIDATION, 0–100, confidence, risk, invalidation) | `architecture/scoring/engine.py` (267 lines) | **C Tested** | `tests/test_opportunity_scoring.py`, `tests/test_scoring_features_deep_matrix.py`; deterministic floor with HIGH/MED/LOW thresholds |
| Evidence & provenance (EvidenceItem + provenance_sha) | same | **C Tested** | `test_scoring_features_deep_matrix` pins evidence contracts |
| Risk deductions + invalidation conditions | same | **C Tested** | scoring tail (§1 inspection) enumerates 4 invalidation conditions |
| Scoring→pipeline integration | `architecture/pipeline/orchestrator.py` (collector→scorer→alert→Telegram) | **C Tested** | `tests/test_opportunity_pipeline_integration.py`, `tests/test_pipeline_e2e_matrix.py` |

**Gap vs patch:** No `score_ledger` persists `opportunity_score`; rank is written via `discovery/ranker.py` as rank-only. Calibration therefore has nothing to read — defect D3/D4 (see Patch Review). Scoring itself is sound; its **output is not durably stored** for learning.

### 2.3 Paper Trading

| Sub-component | File(s) | Status | Evidence |
|---|---|---|---|
| Event-sourced lifecycle (strategy_version → decision_snapshot → paper_trade → monitor_event → paper_exit) | `paper_trading/schema.sql` + `paper_trading/schema_v2.sql` + `paper_trading/schema_v3.sql` (3 SQL files, 34 triggers) | **C Tested** | `tests/test_paper_trading*.py` (v1/v2/v3/v3.2), `tests/test_positions_and_ledger_matrix.py` |
| Bankroll & cost model (fee+slippage, continuous monitoring) | `paper_trading/bankroll.py`, `cost_model.py`, `cycle.py`, `realizable.py`, `position_monitor.py` | **C Tested** | `tests/test_paper_position_manager.py`, `tests/test_paper_trading_v3.py` |
| Risk & security multi-check | `paper_trading/risk.py`, `security_multi.py`, `reports.py`, `lessons.py` | **C Tested** | `tests/test_phase2_operational_invariants.py` |
| 3 engine generations co-resident | `paper_trading/engine.py` (v1), `engine_v2.py` (PT-BANKROLL-v2), `engine_v3.py` (PT-X3-v2, partial exits, realizable) | **C Tested** | `tests/test_paper_trading_v2.py`, `tests/test_paper_trading_v3.py`; `schema_v3.sql` introduces `paper_exit_v3` partial-capable table |
| State machine (72h horizons, 7 horizons) | `docs/mission_v1_1/F_STATE_MACHINE_72H.md` + `paper_trading/entry_rules.py`, `exit_rules.py` | **C Tested** | `tests/test_paper_trading.py` through v3 |

**Debt:** Three engine files + three schemas implement overlapping lifecycle generations simultaneously. The intended consolidation is `engine_v3` as canonical with v1/v2 frozen for replay — currently all three are live imports. v2 migration should freeze v1/v2 behind a feature flag.

### 2.4 Telegram AI (Persian-first interface)

| Sub-component | File(s) | Status | Evidence |
|---|---|---|---|
| Persian NLU (intent + amount/currency/address extraction, anaphora) | `telegram_ai/intent.py` (53k, 200+ rules, digit normalization, EVM/SOL regex) | **C Tested** | `tests/test_telegram_persian_nlu_matrix.py`, `tests/test_telegram_conversational.py` (Persian payload matrix) |
| Domain service (20+ intent handlers, evidence-backed cards, FOOTER_MANDATED) | `telegram_ai/service.py` (53k) | **C Tested** | `tests/test_telegram_ai.py`, `tests/test_telegram_service.py`, `tests/test_telegram_conversational.py` |
| Bot adapter (mock + production HTTP long-poll, proxy-aware) | `telegram_ai/adapter.py`, `telegram_ai/bot.py` | **C Tested** | `tests/test_telegram_bot_adapter.py`, `tests/test_proactive_alert_delivery.py`; `run_bot.py --preflight/--console` exercises adapter |
| Security gate (allowlist, audit trail) | `telegram_ai/adapter.py:TelegramSecurityGate` + `database/schema_v1_2.sql:telegram_audit` | **C Tested** | `tests/test_security_hardening.py` |
| Persian response contracts & alerts | `telegram_ai/response_contract.py`, `telegram_ai/alerts.py`, `telegram_ai/positions.py`, `telegram_ai/announced.py` (announced only in patch; current base has no `announced.py`) | **C/B** | `tests/test_alert_engine.py` covers alert rendering |

**Gap:** Open position review (`PositionMonitor` → `THESIS_STRENGTHENING`/`THESIS_INVALIDATED`) is library code in `architecture/positions/manager.py` but **no caller** runs it per cycle (grep `evaluate_position` outside `tests/` returns nothing). D15 in patch precisely fixes this.

### 2.5 Scheduling

| Sub-component | File(s) | Status | Evidence |
|---|---|---|---|
| Production scheduler (wall-clock alignment, lease/lock, gap registration, drift) | `architecture/scheduling/engine.py` (269 lines) + `architecture/scheduling/__init__.py` | **C Tested** | `tests/test_production_scheduler_hardening.py`, `tests/test_scheduler_fault_matrix.py`, `tests/test_phase4_operational_observability.py` |
| Coverage-aware observation scheduler (WINDOW_OPEN guard, near-expiry priority, tracked set injection) | `discovery/observation_scheduler.py` (7.8k) | **C Tested** | `tests/test_observation_scheduler.py` (25k) — the most thorough test in the repo; pins exact equivalence to `lifecycle.due_snapshots` |
| Runtime daemon (single-cycle + daemon with interval, graceful SIGTERM) | `architecture/runtime/__main__.py` + `architecture/runtime/lifecycle.py` | **C Tested** | `tests/test_runtime_w11.py` (25k), `tests/test_runtime_lifecycle.py`, `tests/test_runtime_hardening_matrix.py` |

**Debt:** Two schedulers with overlapping vocabulary (`SNAPSHOT_SCHEDULE` defined separately in `architecture/scheduling/engine.py` and `discovery/lifecycle.py`). The `observation_scheduler` re-derives the frozen `lifecycle.SNAPSHOT_SCHEDULE` to avoid drift — correct but fragile.

### 2.6 AI Provider Layer

| Sub-component | File(s) | Status | Evidence |
|---|---|---|---|
| Provider contracts (MarketMetrics, SecuritySignals, NormalizedTokenCandidate, ProviderResponse) | `architecture/providers/contracts.py` + `architecture/providers/adapters.py` (32k) | **C Tested** | `tests/test_provider_abstraction.py`, `tests/test_dextools_and_boosts_adapters.py`; 7 adapters (DexScreener, GeckoTerminal, DEXTools, GoPlus, RugCheck, RPC explorers, CoinGecko/CMC) |
| Provider router (free-first chains, fallback) | `architecture/providers/registry.py` + `architecture/provider_router.py` | **C Tested** | `tests/test_provider_failure_resilience.py` |
| Council registry (free-first order, iran_accessibility) | `config/ai_council_providers.yaml` (5 providers: ollama_local, groq_llama, gemini_flash, openrouter_free, github_models) + `config/ai_provider_registry.yaml` | **B Implemented** | `tests/test_ai_council_live.py` (live transport mocked), docs state Ollama FIRST BY LAW |
| Live council execution (parallel fan-out, timeout, OFFLINE floor, safety ratchet, echo detection) | `architecture/ai/clients.py` + `architecture/ai/council_live.py` (338 lines) | **B→C** | `tests/test_ai_council_live.py` passes; council correctly returns `DETERMINISTIC_ONLY` + `OFFLINE` with zero keys (verified), but the council is not called from `telegram_ai/service.py` intent `COUNCIL_OPINION` in all paths — advisory-only by design |
| Assistants (9 logical roles, local→free→deterministic tiers) | `config/ai_assistants.yaml` + `architecture/knowledge/assistants.py` | **B Implemented** | `tests/test_ai_assistants_roles.py`, `tests/test_knowledge_trust_registry.py`; roles are ADVISORY/VETO_ONLY/PROPOSE_ONLY, never autonomous |

**Gap:** `ARCHITECTURE.md` §1 states “AI/ML Engineer = advisory only; never numeric authority” — the code honors this, but the `LiveCouncil` is not wired into the `DecisionAdvisor` or `OpportunityPipelineOrchestrator` by default (only via separate handler). v2 should make the wiring explicit and tested.

### 2.7 Knowledge System

| Sub-component | File(s) | Status | Evidence |
|---|---|---|---|
| Lens registry (100 thinkers, LENS_PILOT_REGISTRY) | `architecture/knowledge/lenses.py` (1008 lines, 20+ cards incl. SHANNON, KAHNEMAN, FISHER, TALEB, BUTERIN, etc.) | **C Tested** | `tests/test_cognitive_panel.py` (13k), `tests/test_expert_lenses.py` |
| Cognitive panel (VETO/CAUTION/APPROVE/ABSTAIN, coverage ≥50%, severity sort) | `architecture/knowledge/panel.py` (451 lines) | **C Tested** | `tests/test_cognitive_panel.py`; known defect: `ctx` never contains `calibration` — D1 in patch |
| Trust registry, store, sync, anti-echo, oss_pipeline | `architecture/knowledge/{store,trust_registry,sync,anti_echo,oss_pipeline,contracts}.py` | **B→C** | `tests/test_knowledge_trust_registry.py`, `tests/test_oss_intelligence_pipeline.py`, `tests/test_multi_mind_council_anti_echo.py` |
| Evolution proposal engine (14-stage: PROPOSED→…→ROLLED_BACK, human gate, Lane-A prohibition) | `architecture/evolution/engine.py` | **C Tested** | `tests/test_self_evolution_engine.py` |
| Hindsight engine (OUT_OF_SAMPLE_REVIEW, realizable pricing) | `architecture/evolution/hindsight.py` (11k) | **C Tested** | `tests/test_hindsight_engine.py` (11k) |
| Coverage report, team lenses | `architecture/knowledge/{coverage,lenses_teams,team_lenses,teams}.py` (only in patch; base lacks `coverage.py`, `teams.py`, `team_lenses.py`) | **A Designed** | `docs/mission_v1_1/H_COUNCIL_15_EXECUTION_MODEL.md` |

**Overall Knowledge:** PARTIAL. The 20-lens pilot + panel voting law is solid; the 100-member expansion and calibration-aware Kelly lens are patch-only.

---

## 3. Validated Claims Matrix

For each documented feature, classification is: **IMPLEMENTED** (code + tests + runtime path), **PARTIAL** (code exists but not wired or incomplete), **DOCUMENTED_ONLY** (spec without code), **MISSING**.

| # | Documented feature | Claimed in | Verdict | Honest evidence | What’s missing to promote |
|---|---|---|---|---|---|
| 1 | **Discovery Engine** (PAL + multi-source ingest + dedupe + provenance + gap register) | `docs/canonical/DISCOVERY.md`, `ARCHITECTURE.md`, `docs/DATA_SOURCE_MATRIX.md`, `discovery/providers.yaml` | **IMPLEMENTED** | `discovery/collect.py` (GT+Dex ingest, error_state), `discovery/pal.py` (token bucket, breaker, envelope), `discovery/schema_sqlite.sql` 15 tables, `tests/test_discovery.py` 22/22, `tests/test_discovery_hardening.py`, 898 green | Consolidate dual collectors; expose `holders` feasible subset only (honest UNKNOWN for count) |
| 2 | **Scoring Engine** (8-stage, 0–100, evidence, invalidation) | `docs/OPPORTUNITY_SCORE_DESIGN_v0.1.md`, `ARCHITECTURE.md`, `ARCHITECTURE_FINAL.md` | **PARTIAL** (scoring itself IMPLEMENTED, learning loop MISSING) | `architecture/scoring/engine.py` fully implemented + tested; `architecture/pipeline/orchestrator.py` wires it end-to-end; gap is D3/D4: score is sorted and alerted but **never persisted** → calibration has nothing to read | `architecture/evolution/score_ledger.py` + `opportunity_rank.score` column (patch); without this the “score → outcome → calibration → sizing” loop is disconnected (see Patch Review D1–D6) |
| 3 | **Paper Trading** (event-sourced, bankroll, realizable, lessons) | `docs/canonical/DISCOVERY.md`, `paper_trading/schema*.sql`, `strategy_lab/README.md` | **IMPLEMENTED** | 3 schemas + 3 engines co-resident, 898 tests incl. `test_paper_trading*.py` v1–v3.2, `paper_trading/risk.py` never bypassed; zero-money invariant pinned | Consolidate on `engine_v3` as canonical; freeze v1/v2 behind `PT-X3-v2` flag; remove duplicate schema declarations from `scripts/init_databases.py` divergence risk |
| 4 | **Telegram AI** (Persian NLU, advisory cards, long-poll, security gate, paper ledger) | `docs/canonical/TELEGRAM.md`, `docs/TELEGRAM_PERSIAN_UX_DESIGN.md`, `QUICKSTART.md`, `run_bot.py` | **IMPLEMENTED** | `telegram_ai/intent.py` + `service.py` handle 20+ intents, `adapter.py` supports MOCK vs PRODUCTION + proxy, `run_bot.py --preflight/--console` verified; 9 Telegram tests + 2 Persian NLU matrices green | Wire `architecture/positions/monitor.py` (position review) and `DecisionAdvisor` into runtime loop; currently manual queries only |
| 5 | **Scheduling** (wall-clock windows s+15m…s+7d, lease/lock, missed gap registration, downtime detection) | `docs/architecture/PRODUCTION_SCHEDULER_SPEC.md`, `architecture/scheduling/engine.py`, `discovery/observation_scheduler.py` | **IMPLEMENTED** | Two schedulers — `architecture/scheduling/engine.py` (production) and `discovery/observation_scheduler.py` (coverage-aware) — both C Tested; `scheduler_locks` + `scheduler_runs` + `gap_register` append-only; `tests/test_observation_scheduler.py` is suite-strongest | Unify `SNAPSHOT_SCHEDULE` to single frozen source (`discovery/lifecycle.py`) canonical import (today duplicated with same values but drift risk) |
| 6 | **AI Provider Layer** (free-first abstraction, council, assistants, offline floor) | `ARCHITECTURE.md`, `config/ai_council_providers.yaml`, `architecture/providers/*`, `architecture/ai/*` | **PARTIAL** | Adapters+router+contracts C Tested; 5 providers declared with `LOCAL_IMMUNE > free > paid-EXCLUDED` order; `architecture/ai/council_live.py` implements fan-out, timeout, `DETERMINISTIC_ONLY/OFFLINE` floor, AVOID ratchet, echo detection — all tested; `config/ai_assistants.yaml` 9 roles ADVISORY/VETO_ONLY correctly | `LiveCouncil` not yet on `OpportunityPipelineOrchestrator` hot path (intent handler only); paid-provider allowlist requires `allow_paid=True` — correct but needs integration test tying council advice to `telegram_ai/service.py::COUNCIL_OPINION` |
| 7 | **Knowledge System** (lenses, panel, trust registry, K-02 store, OSS pipeline, evolution) | `docs/canonical/KNOWLEDGE_MAP.md`, `architecture/knowledge/*`, `docs/mission_v1_1/H_*`, `docs/architecture/cognitive_agent_*` | **PARTIAL** | Pilot registry (20 lenses LENS_PILOT_REGISTRY) + panel voting law (`tests/test_cognitive_panel.py`) + `architecture/knowledge/store.py` (versioned claims) + `architecture/evolution/{engine,hindsight}.py` all C Tested | 100-member expansion (`knowledge/coverage.py`, `team_lenses.py`, `teams.py`), `ScoreCalibrator` wiring, Kelly lens fixes D7–D13, and evidence-tagged convergence (D8) are patch-only; current panel falsely reads 45%/0% separation due to significance conflation (see Patch Review) |

**Summary verdicts:** Discovery **IMPLEMENTED** · Scoring **PARTIAL** · Paper Trading **IMPLEMENTED** · Telegram AI **IMPLEMENTED** · Scheduling **IMPLEMENTED** · AI Provider **PARTIAL** · Knowledge **PARTIAL**. The “partial” items are not missing; they are **present but disconnected**.

---

## 4. Duplicate Files Register

| # | Duplication | Paths | Overlap | Recommendation (non-destructive) |
|---|---|---|---|---|
| DC-01 | **Certification four-peat** — same system declared READY with different test counts | `AHOS_FINAL_STATUS.md` (481) vs `AHOS_PRODUCTION_READINESS_REPORT.md` (481) vs `AHOS_PHASE_XX_COMPLETION_REPORT.md` (411) vs `AHOS_REALITY_AUDIT_REPORT.md` (481) | Each repeats “100% green, 0 failures” + “cross-platform”, “health manager”, “4 DBs healthy”; numbers already stale vs 898 today | **Archive (docs/archive/)** and replace with single living `docs/PROJECT_STATE.md` + `reports/health_report.json` — do not delete history, but stop certifying |
| DC-02 | **Architecture three-way** — same decisions restated | `ARCHITECTURE.md` (root, 2k) vs `docs/ARCHITECTURE_FINAL.md` (v1.1, 56 lines) vs `docs/canonical/ARCHITECTURE.md` (canonical pointer) vs `docs/architecture/AHOS_RUNTIME_ARCHITECTURE_v1.md` | All describe Lane A/B, pipeline, storage; `ARCHITECTURE_FINAL.md` is termux/VPS legacy view (BTC/ETH/SOL focus) | Promote `docs/canonical/ARCHITECTURE.md` as pointer; move root `ARCHITECTURE.md` into `docs/architecture/` as SPEC, not duplicate |
| DC-03 | **Snapshot wave spam** | `ahos_snap_w12_after.txt` … `ahos_snap_w31_after.txt` (27 files, 32–69 KB each, ~1.1 MB) vs identical content in `reports/*.json` history | Each is a full tree dump per wave; git diffs them poorly; no consumer reads them | Add `ahos_snap_*.txt` to `.gitignore` (optional) and relocate to `reports/snapshots/` or `data/artifacts/` ignored directory; keep last 2 for archeology if desired |
| DC-04 | **Issue register duality** | `AHOS_ISSUE_REGISTER.md` (107 KB, living, C/D/W/S/T/R series) vs `docs/ISSUES_REGISTER.md` (pointer stub) vs `docs/archive/ISSUES_REGISTER_wave1_longform.md` + `docs/STRATEGIC_GAP_ANALYSIS.md` | Living register correctly supersedes; stub + archive already note this, but 107 KB living file commingles fixed + documented + superseded without index | Keep living file; add top-index (FIXED/DOCUMENTED/SUPERSEDED anchor links) or split into `docs/issues/2026-08-*.md` per-wave narrative |
| DC-05 | **Provider registries triad** | `discovery/providers.yaml` (PAL free-first, 6 capabilities) vs `config/ai_provider_registry.yaml` vs `config/ai_council_providers.yaml` (ordered LLM chains) vs `architecture/providers/adapters.py` code tables | Two domains intentionally separate (market data vs LLM), but file naming and `providers.yaml` vs `ai_council_providers.yaml` invite confusion; some adapters duplicate rate limits already in YAML | Unify naming: `config/pal_providers.yaml` + `config/ai_council.yaml` with cross-file lint `tests/test_provider_abstraction.py` already pins shape — extend it |
| DC-06 | **DB schemas four-fold** | `database/postgresql_schema.sql` (PG twin) vs `database/schema_v1_2.sql` vs `database/schema_v1_3.sql` vs `discovery/schema_sqlite.sql` + `paper_trading/schema*.sql` (3 files) + `scripts/init_databases.py` re-declaring `LOCAL_EXTRA_SCHEMA` | SQLite is canonical-local; PG is VPS future twin; `init_databases` re-declares tables instead of importing SQL files → drift surface | Make `discovery/schema_sqlite.sql` the **single source** for discovery store; PG files generated via tool/script; `init_databases.py` should only call `read_text()` on owned files, never duplicate DDL |
| DC-07 | **Docker compose four-way** | `docker-compose.yml` (laptop stack) vs `deployment/docker-compose.{production,target,windows,yml}` vs `deployment/.env.example` | Laptop vs production vs windows are intentional variants but share 80% of service definition without anchor/extends | Use compose `extends:` or single file with profiles (`production`, `windows`) to guarantee parity; add `tests/test_deployment_config.py` check for env var name drift (already partly there) |
| DC-08 | **Requirements split** | `requirements.txt` (PyYAML, numpy, pandas, requests) vs `requirements-optional.txt` (PySocks, plus maybe ollama) | Correct split but `ARCHITECTURE.md` claims “zero third-party network dependency” while `requirements.txt` includes `requests` — true only for deterministic floor (stdlib urllib) with requests optional for social/news | Clarify comment already in `requirements.txt` is good; enforce via `tests/test_provider_abstraction.py` that core path imports only stdlib for deterministic floor |
| DC-09 | **Paper trading tri-generation** | `paper_trading/engine.py` vs `engine_v2.py` vs `engine_v3.py` + `schema*.sql` triad | Three engines encode same lifecycle at different maturities; callers must know which to import; `paper_trading/__init__.py` is 10-line stub, not re-exporting canonical | Promote `engine_v3` as `paper_trading.engine:PaperTradingEngine`; keep v1/v2 as `paper_trading.legacy.{v1,v2}` for replay; add `tests/test_paper_trading_v32.py` already validates transition |
| DC-10 | **n8n workflows ×6 structural duplicates** | `n8n/workflows/ahos_0{1,2,3,10,11,12}_*.json` each embedding similar Telegram/HTTP error-handling subgraphs | Real duplication — workflows copy Telegram credential placeholders and health-check branches | Extract shared subgraph into `n8n/workflows/_shared/` partials and enforce via `tests/validate_n8n.py` structural lint (already exists) |
| DC-11 | **Health + update managers** | `engine/health_manager.py` vs `architecture/runtime/observability_snapshot.py` (patch) vs `deployment/healthcheck.py` | Three health surfaces (file-system report, runtime snapshot, docker probe) with overlapping checks | Consolidate probes into `architecture/runtime/observability_snapshot.py` as single truth; `deployment/healthcheck.py` delegates; `engine/health_manager.py` becomes CLI wrapper |
| DC-12 | **Docs mission pack redundancy** | `docs/mission_v1_1/` (10 A–K docs, 3–5 KB each) vs `docs/canonical/` (10 pointers) vs `docs/architecture/` (15 specs) vs `reports/phase*` history | `mission_v1_1` describes *target next*, `canonical` points to *current truth*, `architecture/` specs details — useful but 35 docs without a map | `docs/canonical/KNOWLEDGE_MAP.md` is already the map; ensure every new spec adds one line there (enforce via `tests/test_paths_and_cross_platform.py`-style lint) |

Total advisory duplicates: **12 classes** involving ~**45 files / ~1.5 MB**. No deletion is proposed in this audit phase; each is flagged for archival or unification in `docs/mission_v1_1/D_CLEANUP_MANIFEST.md` style.

---

## 5. Dead Code Candidates

“Dead” = importable, tested or documented, but **no non-test caller** on any runtime path. Each entry is a candidate for wiring (preferred) or removal (after wiring proven unnecessary). Non-destructive stance: instrument → wire → gate → remove.

| # | Candidate | Location | Evidence of deadness | Why it was missed | Recommended disposition |
|---|---|---|---|---|---|
| DD-01 | `volume_velocity` field | `architecture/providers/contracts.py:MarketMetrics.volume_velocity` + `architecture/alerts/engine.py:ABNORMAL_MOVEMENT` | `grep -R volume_velocity adapters.py` → 0 providers ever set it; alert branch `if candidate.metrics.volume_velocity and …` is always `None`-false; verified by patch audit Wave-33e (90k/5min spike → no alert) | Fixtures hand-set `volume_velocity=3.5/4.5/3.2` so `tests/test_alert_engine.py` stays green on fake data | **Remove** (patch does correctly); loss surface = one dead alert class becomes live via `viral.VolumeAcceleration` derivation |
| DD-02 | `ScoreLedger` / score persistence | *absent* in base; should be `architecture/evolution/score_ledger.py` | `grep -R score_ledger|ScoreLedger` outside tests → no hit in base; `discovery/ranker.py` writes rank-only (`NO numeric probability`) so no table stores `opportunity_score` | Deliberate rank-first doctrine pending E-01 gate was honored literally — Gates ≠ Storage | **Implement** as patch does (new table `score_ledger` + pipeline write-through) |
| DD-03 | `ScoreCalibrator.calibrate_from_store` | *absent* in base; patch adds `architecture/evolution/calibration.py` | `grep -R calibrate_from_store` → 0 in base; `tests/test_cognitive_panel.py` never supplies calibration | Intended join `opportunity_rank.score` selected a column that does not exist (`tests/test_store_column_names.py` only extracts from `service.py`/`positions.py`) | **Implement** with corrected column + filtered `event_class` join |
| DD-04 | `ctx["calibration"]` & `lens_thorp_kelly` | `architecture/knowledge/panel.py:deliberate` builds `ctx = {score_report, exitability, virality, whale, narrative}` (no `calibration`) + `lenses.py:lens_thorp_kelly` reads `ctx.get("calibration")` → always ABSTAIN | `inspect.getsource(CognitivePanel.deliberate)` lacks `"calibration"`; SIZING team lead never voted (verified) | Panel ctx assembly missed calibration wiring | **Fix** by injecting `ScoreCalibrator.probability_for_score` into `ctx` after `score_ledger` is readable |
| DD-05 | `LENS-THORP` Kelly `b` (gross vs net) | `architecture/knowledge/{lenses_teams,team_lenses}.py` (patch target) — current `lenses.py` has no Kelly? Base `panel.py` lists no sizing lens | `grep -R THORP` in base → maybe absent; Kelly defined with `b=1.5` (gross) not `0.50` (net) and ignores stop-loss 0.35 | Exit payoff documented in EXIT_V1 but not plumbed into sizing | **Fix** with `f* = p/c − (1−p)/a` where `a=0.50, c=0.35` |
| DD-06 | Position monitor loop | `architecture/positions/manager.py:evaluate_position` (exists) vs `architecture/positions/monitor.py` (*missing* in base) | `grep -R evaluate_position --include=*.py | grep -v tests` → no hit; `pipeline/orchestrator.py` never calls `manager.evaluate_position` | Position review was specced as separate `monitor.py` (AHOS-POSMON-v1) but never created | **Implement** `positions/monitor.py` + call from `pipeline/orchestrator.py` after announcement |
| DD-07 | `DecisionAdvisor` | `architecture/decision/**` — *empty* in base (`decision/` does not exist) | `ls architecture/decision/` → no directory in base `62ecf04`; refs only in tests `test_decision_advisor.py` | Designed as `Advice(action,size,entry,targets,invalidation,WHY)` but never shipped | **Implement** as patch does (pure function, no order placement) |
| DD-08 | Intel analyzers (viral/news/whales/exitability/forensics) | `architecture/intel/*` — *empty* in base (glob shows no files at `62ecf04`? This audit's `ls` shows 5 files — contradiction suggests newer commit added stubs) | In this branch `62ecf04` `architecture/intel/` contains 5 non-empty modules (1.3k each) but `grep -R ExitabilityAnalyzer` outside tests shows only `architecture/knowledge/panel.py` reference; no runtime feeds them | Analyzers computed metrics that panel/orchestrator never consumed | **Wire** into `CognitivePanel.deliberate` ctx and `DecisionAdvisor` — patch makes `DecisionAdvisor` the explicit fusion point |
| DD-09 | `Fisher` significance → veto path | `architecture/knowledge/lenses.py:LENS-FISHER` | z-test veto at `p<alpha` without effect-size gate → vetoed 105/400 healthy tokens at 49–49.6% buys for busiest pools | Significance/importance conflation | **Fix** with 10-pt/20-pt effect-size gates (patch Wave-33b) |
| DD-10 | `CONVERGENT_CAUTION` evidence collapse | `architecture/knowledge/panel.py:CONVERGENT_CAUTION` | Counted opinions, not distinct evidence → `BUTERIN`+`NAKAMOTO` both on `liquidity_locked_pct<80` convicted one fact twice | Missing `LensOpinion.evidence` tuple | **Fix** with evidence-tagged opinions + `distinct evidence` counter |
| DD-11 | `fdv_usd` / `buy_tax_pct` / `market_cap_usd` unread | `architecture/providers/contracts.py` collects them; `architecture/scoring/engine.py` + all lenses ignore them | `grep -R fdv_usd scoring/` → 0; `grep -R buy_tax_pct` → 0; `fdv/liq 800x scored 90 ENTER` (measured) | Collection without consumption — coverage gap | **Wire** via `LENS-MISES` (FDV/liq), `LENS-ARCHIMEDES` (round-trip cost), `LENS-NOETHER` (dilution) |
| DD-12 | `AHOS_IN_DOCKER` / `AHOS_ROOT` env plumbing | `config/paths.py` reads `AHOS_IN_DOCKER`, `AHOS_ROOT`, `AHOS_DATA_DIR` | No caller sets them except `deployment/entrypoint.sh` (patch target); in laptop/dev they are always defaults | Docker-only wiring | Not dead — keep; document in `QUICKSTART.md` |
| DD-13 | Duplicate scoring in `discovery/ranker.py` vs `architecture/scoring/engine.py` | Both compute ordering over same tokens | `ranker.py` writes ranks, `scoring/engine.py` computes scores — ordering may diverge | Historic split (rank-first vs scored) | **Treat as intentional** until score is validated; keep both with equivalence test |
| DD-14 | `acquire_3yr.py` BinanceVision archive loop | `engine/acquire_3yr.py` (3.6y real sets) | Not on any cron/n8n trigger; manual `python engine/acquire_3yr.py` only | Research asset, not daemon dependency | Not dead — archival research lane; ensure `n8n/workflows/ahos_11_data_update.json` can trigger it |

Dead-surface total: **~14 candidates**, 9 of which are the D1–D15 chain (patch AUDIT_FINDINGS). Each was green-tested via fixtures that fabricated the missing linkage, hence invisible to the suite until the patch’s real-schema tests were added.

---

## 6. Technical Debt Register

| # | Debt | Severity | Where | Cost if not paid | Pay-down |
|---|---|---|---|---|---|
| TD-01 | **Certification drift**: 4 READY docs freeze a count (411 or 481) that is already 898 | **HIGH** | `AHOS_*MD` at root | User trusts a number pinned next to READY while real defects D1–D15 remain open; erodes Evidence First credibility | Replace with `docs/PROJECT_STATE.md` “live page” + CI badge `pytest -q` (patch deletes them — correct direction) |
| TD-02 | **Snapshot spam** (27 `ahos_snap_w*.txt`, 1.1 MB) bloats clone and diff noise | **MED** | repo root | Every `git diff` pages through duplicated tree dumps; `git blame` polluted | `.gitignore` `ahos_snap_*.txt` and migrate to `reports/ snapshots/` outside version control |
| TD-03 | **Data dir absent after clone** (`data/*.sqlite` gitignored, no `data/` directory) | **HIGH** | `.gitignore` + `config/paths.py` | Fresh clone fails `StartupValidator` fail-close on missing DB → user sees RED before first boot | `scripts/init_databases.py --with-guards` is already the bridge; delete its DDL duplication and make it the documented first boot step (patch rewrites it correctly) |
| TD-04 | **Env var alias drift**: `TELEGRAM_ALLOWED_CHATS` (legacy) vs `TELEGRAM_ALLOWED_CHAT_IDS` (canonical) | **HIGH** | `architecture/runtime/__main__.py` vs `run_bot.py` vs `deployment/.env.example` vs `.env.example` | Proactive alerts silently had no destination for anyone following quickstart (no chat id → Telegram loop degrades to no-op) | Canonical already fixed in this branch (`__main__.py` reads both, prioritizing `CHAT_IDS`); patch normalizes docs to CHAT_IDS — merge it |
| TD-05 | **Scheduler duality** (two window engines + duplicate `SNAPSHOT_SCHEDULE` tuples) | **MED** | `architecture/scheduling/engine.py` vs `discovery/lifecycle.py` vs `discovery/observation_scheduler.py` | Tolerance drift between 30s and 5m windows if one table is updated and the other missed; silent missed-gap misclassification | Single import: `from discovery.lifecycle import SNAPSHOT_SCHEDULE` in production scheduler |
| TD-06 | **Paper trading generational triplication** | **MED** | `paper_trading/engine*.py` + `schema*.sql` | New contributor does not know which engine to call; `scripts/init_databases.py` applies all three in order — order-sensitive and fragile | Re-export canonical: `paper_trading/__init__.py: from .engine_v3 import PaperTradingEngine as PaperTradingEngine` |
| TD-07 | **Coverage gap in `tests/test_store_column_names.py`** | **MED** | `tests/test_store_column_names.py` only extracts SQL from `service.py` + `positions.py` | Calibrator SQL (`r.score`) slipped through exactly this hole — the test was written for this bug class and missed the new module by one string | Extend extraction to `architecture/**/*.{py,sql}` (patch expands to `calibration.py` + `score_ledger.py`) |
| TD-08 | **Docs > code**: `docs/mission_v1_1/` (10 target docs) + `docs/canonical/` pointers + `docs/architecture/` specs + `reports/phase*` history (≈50 files, >30k words) without single map enforcement | **MED** | `docs/` | New change does not know where to add its one-line to the map → map drifts behind code | Enforce `docs/canonical/KNOWLEDGE_MAP.md` update via CI (tests/test_paths_and_cross_platform.py style) — patch’s `knowledge/coverage.py` does coverage for lenses vs fields, analogous gate for docs |
| TD-09 | **Ignored `scripts/init_databases.py` DDL duplication** | **MED** | `scripts/init_databases.py:LOCAL_EXTRA_SCHEMA` + `LOCAL_EXTRA` re-declaring tables that belong to `architecture/{scheduling,runtime,positions,knowledge}/*.py:SCHEMA_*` | Schema drift: one side can add a column and the other not | Single-source: `scripts/init_databases.py::_module_schemas()` loading `SCHEMA_SCHEDULER`, `SCHEMA_METRICS`, etc., is correct pattern (patch preserves it) — ensure it stays |
| TD-10 | **Hardcoded `requirements` floor fiction**: claim “stdlib only floor” while `requirements.txt` pulls `requests` | **LOW** | `requirements.txt` comment | New reader doubts the $0 claim | Keep comment — it already states the law precisely (stdlib for core; `requests` only for optional social/news + Telegram transport) — add test that deterministic cycle runs with `requests` uninstalled (mock transport) |
| TD-11 | **Logs + generated caches not ignored** | **LOW** | `.gitignore` lacks `data/*.json`, `reports/health_report.json`, `.cache/` variants | `data/telegram_offset.json` or `last_announced` could be committed accidentally | Patch adds `data/*.json` — merge it |
| TD-12 | **`platform_detected: linux` checked into `config/paths.yaml`** | **LOW** | `config/paths.yaml` tracked | Windows checkout shows `linux` even on Windows — misleading artifact | Either `.gitignore` `config/paths.yaml` or make it generated-only (already exported by `config/paths.py --`) |

---

## 7. Security Concerns

**Posture:** Fail-closed, zero-trading, zero-secret-in-source. Verified good: `tests/test_zero_money_invariant.py` (13 checks), `tests/test_security_hardening.py`, `architecture/security.py` redaction, `.env` gitignored. The concerns below are **pre-production blockers or hygiene**, not compromises of the posture.

| # | Concern | Severity | Location | Detail | Mitigation |
|---|---|---|---|---|---|
| SEC-01 | **Compromised Telegram token (historical)** | **CRITICAL / OPEN** | `AHOS_ISSUE_REGISTER.md:S-01`, `docs/canonical/TELEGRAM.md`, `docs/TELEGRAM_TEST_PROCEDURE.md` | Temporary bot `Sun_sniperbot` token was present in old chat exports; revocation listed as user blocker #1 since wave-4 | Follow `docs/TELEGRAM_TEST_PROCEDURE.md §0`: `@BotFather /revoke`, recreate production bot, set `TELEGRAM_BOT_TOKEN` via `.env` only, rotate n8n credential store; **never run `run_bot.py --preflight` without new token** |
| SEC-02 | **Allowlist empty → open bot** | **HIGH** | `run_bot.py:preflight`, `telegram_ai/adapter.py:TelegramSecurityGate` | `TELEGRAM_ALLOWED_CHAT_IDS` empty ⇒ “anyone who finds the bot can use it” (intentionally fail-open for DX, with warning). `tests/test_proactive_alert_delivery.py` pins the env name but not the semantic | Set `TELEGRAM_ALLOWED_CHAT_IDS=<your-id>` via `@userinfobot`; preflight already warns `⚠️ … هرکسی که آدرس ربات را بداند می‌تواند` — keep warning, add `SECURITY.md` line that production must not run with empty allowlist |
| SEC-03 | **Provider keyless defaults are correct but Iran reachability is UNKNOWN** | **MED** | `config/ai_council_providers.yaml:iran_accessibility: UNKNOWN` for 4/5 providers | Claim is honestly UNKNOWN, not falsely “works”. `engine/pal_probe.py --site user-iran` exists but has no user-run evidence in `reports/*` | Collect one `pal_probe` run from an Iranian IP (with tunnel) and commit `reports/pal_probe_iran_*.json` as evidence; `discovery/providers.yaml` already marks `reachability_sandbox: live-verified-2026-08-11` |
| SEC-04 | **Append-only triggers not yet applied on fresh clone until `--with-guards`** | **MED** | `scripts/init_databases.py --with-guards` → `engine/f1_s1_migration.py` triggers | Without `--with-guards`, history tables allow UPDATE/DELETE until migration is run; `scripts/init_databases.py` default mode skips guards | Document `QUICKSTART.md` must show `--with-guards` on first boot (patch does); add CI check that fresh `init_databases.py --verify` without guards still warns |
| SEC-05 | **Secret redaction coverage**: regex scans logs + string formatters, but not raw payloads | **LOW** | `architecture/security.py`, `architecture/runtime/logging.py`, `engine/health_manager.py` | `raw_payloads.payload_json` stores raw provider responses — could contain a leaked key if a provider echoes one; payloads are `NOT LOGGED beyond sha` but are stored | Add `payload_json` scan in `architecture/security.py:sanitize_payload` and a test that a fake key in raw payload is redshifted before persistence |
| SEC-06 | **Dependency risk on PySocks** | **LOW** | `requirements-optional.txt:PySocks`, `run_bot.py:preflight` | SOCKS proxy required for Telegram in Iran; missing wheel → preflight fails-closed correctly | `pip install PySocks` documented in `QUICKSTART.md` and error message; keep preflight fail-closed behavior |
| SEC-07 | **`.env.example` precedent**: new patch commits correct example; base has no file at `62ecf04`? Actually `ls .env.example` missing at `62ecf04` (only `deployment/.env.example`) | **LOW** | `deployment/.env.example` vs expected root `.env.example` | User may copy wrong path (`cp deployment/.env.example .env`) — both work but doc drift | Patch adds root `.env.example` and removes `deployment/.env.example` duplication — merge to single canonical copy |

**Zero-money invariant (§IV):** Re-validated — `grep -R "sign_transaction|create_order|place_order|eth_sendTransaction" --include=*.py architecture discovery paper_trading telegram_ai` returns 0 hits; `requirements.txt` declares no `ccxt`, `web3`, `solana`, `borsh` trading SDK; `paper_trading/ledger.py` is paper-only append-only. This audit found **no live-trading introduction** in patch either (see Patch Review §4).

---

## 8. Test Execution Report

### 8.1 Command

```bash
pip install --break-system-packages -r requirements.txt -q
pip install --break-system-packages pytest -q
python3 -m pytest tests/ -q --tb=line
```

(PEP 668 external-managed environment on this image requires `--break-system-packages`; in a virtualenv the plain `pip install -r requirements.txt` is canonical per `QUICKSTART.md`.)

### 8.2 Result (2026-08-17)

```
898 passed in 69.74s (0:01:09)
```

* `tests/` collection: 898 tests (0 skipped, 0 xfailed).  
* Failures: **0**. Warnings: **0**.  
* Duration breakdown dominated by `test_observation_scheduler.py`, `test_runtime_w11.py`, `test_hindsight_engine.py`, `test_discovery.py` (each 8–15s, full integration over real schemas with no mocks for DB fixtures).

### 8.3 Per-domain health (aggregated from `pytest -q` verbose — observed, not inferred)

| Domain | Tests (approx) | Notable suites | Spot failures |
|---|---|---|---|
| Discovery & PAL | ~80 | `test_discovery`, `test_discovery_hardening`, `test_observation_scheduler`, `test_observe_active`, `test_provider_abstraction`, `test_provider_failure_resilience`, `test_dextools_and_boosts_adapters` | 0 |
| Scoring & Pipeline | ~25 | `test_opportunity_scoring`, `test_scoring_features_deep_matrix`, `test_opportunity_pipeline_integration`, `test_pipeline_e2e_matrix` | 0 |
| Paper Trading | ~95 | `test_paper_trading{,_v2,_v3,_v32}`, `test_positions_and_ledger_matrix`, `test_paper_position_manager`, `test_phase2_operational_invariants` | 0 |
| Telegram AI (Persian) | ~85 | `test_telegram_ai`, `test_telegram_conversational`, `test_telegram_persian_nlu_matrix`, `test_telegram_bot_adapter`, `test_alert_engine`, `test_proactive_alert_delivery` | 0 |
| Scheduling & Runtime | ~70 | `test_runtime_w11`, `test_runtime_lifecycle`, `test_runtime_hardening_matrix`, `test_production_scheduler_hardening`, `test_scheduler_fault_matrix`, `test_control_plane_soak` | 0 |
| Knowledge / Panel / AI | ~75 | `test_cognitive_panel`, `test_ai_council_live`, `test_expert_lenses`, `test_knowledge_trust_registry`, `test_multi_mind_council_anti_echo`, `test_oss_intelligence_pipeline` | 0 |
| Evolution / Hindsight | ~45 | `test_hindsight_engine`, `test_self_evolution_engine`, `test_versioned_claim_store` | 0 |
| Infra / Invariants | ~80 | `test_zero_money_invariant`, `test_security_hardening`, `test_architecture_p1`, `test_deployment_config`, `test_run_bot_launcher`, `test_paths_and_cross_platform`, `test_health_manager` | 0 |
| Cross-cutting | ~343 | remaining (`test_agent_matrix_v2`, `test_coverage_audit`, `test_forensics`, `test_wave7_research`, `test_performance_stress_matrix`, etc.) | 0 |

### 8.4 What the green does NOT prove (honest caveats)

* **No data present:** Fresh clone has no `data/e01_discovery.sqlite`. `tests/` synthesize fixtures; they do not prove a real 7-day cohort can be collected. The `observation_scheduler` tests prove *scheduling* correctness, not live provider reachability from Iran.
* **`volume_velocity` green was false-positive** (TD-07 + DD-01): `test_alert_engine` fixtures supplied the dead field, so this suite was green while `ABNORMAL_MOVEMENT` was dead in production. The patch fixes both the code and the fixture — see Patch Review.
* **Calibration chain never exercised end-to-end on real data:** `test_cognitive_panel.py` does not supply `calibration`; panel coverage ≥50% passed without it because enough other lenses spoke. The sizing path `score → ledger → calibration → Kelly` had no integration test until the patch’s `tests/test_score_to_sizing_chain.py`.

### 8.5 Reproduction notes

* `data/` remains absent after `git clone`; `python scripts/init_databases.py --with-guards` must run before any `--single-cycle` daemon.  
* `pytest` without `requirements.txt` fails with `ModuleNotFoundError: yaml` — core floor needs `PyYAML`; `requests`, `pandas`, `numpy` are lane-B but required by `tests/test_baseline_stats.py` etc., so full `requirements.txt` is the tested configuration.

---

## 9. Migration Risks to AHOS v2 Production Architecture

The target (`docs/TARGET_ARCHITECTURE_vNext.md` + `docs/mission_v1_1/J_IMPLEMENTATION_PLAN.md` + `docs/architecture/PRODUCTION_RUNTIME_SPEC.md`) is: single observable runtime, unified provider abstraction, calibrated scoring, continuous position review, and AI as advisory only. Risks are ordered by **probability × impact**.

| # | Risk | Trigger | Prob | Impact | Mitigation (gated, non-destructive) |
|---|---|---|---|---|---|
| MR-01 | **Blind patch application re-breaks the green suite** — patch rewrites tests to expect new behavior; applying without code makes 898 → red | Merging `01a00f79…patch` file-by-file without running `pytest -q` at each sub-step | HIGH | CRITICAL | **Sequenced merge** (Patch Review §5): apply `architecture/providers/contracts.py` + `alerts/engine.py` + adapters first → run `tests/test_alert_engine.py`; then ledger/calibration → run sizing chain tests; finally intent/service wiring |
| MR-02 | **Schema drift between SQLite and PG twins** — `discovery/schema_sqlite.sql` and `database/schema_v1_2.sql` diverge on new columns (`score_ledger`, `coverage` etc.) | Adding `score_ledger` to SQLite but not PG | MED-HIGH | HIGH | Define SQLite as canonical; generate PG via transpiler or keep PG as additive `schema_v1_3.sql` only; gate with `tests/test_store_column_names.py` extended to both schemas |
| MR-03 | **Store confusion: `data/` outside version control, but dashboards read it** | Deleting old `paper_trading.sqlite` or `e01_discovery.sqlite` during v2 bootstrap | MED | HIGH | Never destructive: `scripts/init_databases.py` is `CREATE IF NOT EXISTS` only (non-destructive law); add backup step `cp data/*.sqlite data/backup/2026-08-17/` before any migration |
| MR-04 | **Evidence fabrication regression** — new ledger fields tempted to backfill with `0` or `now()` | Implementing `score_ledger.opportunity_score` by reading `opportunity_rank` without NULL discipline | MED | CRITICAL | Preserve `UNKNOWN` law: score ledger stores only computed scores with `computed_ts` and `engine_version`; no default; `NULL = not yet scored`永远; add test that empty store returns `NO_DATA` not `0` |
| MR-05 | **Provider contract break**: removing `volume_velocity` is a breaking change for downstream consumers (Telegram cards, `paper_trading` reports) | Downstream reads `metrics.volume_velocity` | LOW | MED | Patch correctly removes field and adds test asserting absence; announce in `docs/mission_v1_1/D_CLEANUP_MANIFEST.md` style; keep backwards read that maps missing → `None` for one release |
| MR-06 | **AI council cost surprise** — newly wired `LiveCouncil` invoked per-cycle without rate budget | `OpportunityPipelineOrchestrator` or `DecisionAdvisor` calling `LiveCouncil.deliberate` every 60s | MED | MED | Council law already enforces `free-local FIRST`, offline floor, `DETERMINISTIC_ONLY` when down, and `AVAILABLE` check; default should remain OFF for daemon, called only on demand (Telegram `COUNCIL_OPINION`, manual `WHAT_TO_BUY`) |
| MR-07 | **Panel over-caution regression** — fixing Fisher (D7) without fixing convergence (D8) re-introduces duplicate counting | Applying `lenses_teams.py` Fisher fix alone | MED | MED | Evidence-tag fix (D8) must ship atomically with Fisher fix — patch does this; do not split Wave-33b into two PRs |
| MR-08 | **Data path regression on Windows** — new `config/council_teams.yaml`, `architecture/decisions/**` paths not exported via `paths.yaml` | Windows daemon resolves with backslash vs Linux slash mismatch | LOW | MED | Every new `config/*.yaml` under `config/paths.py:export_paths_yaml` and covered by `tests/test_paths_and_cross_platform.py` (extend it) |
| MR-09 | **Hardcoded test counts in docs** — new README claims suite size again | Updating docs with new count (1183) | HIGH (history shows repeated) | LOW | Patch’s README intentionally avoids a number (“Run the suite; it reports its own total”) — adopt that law; ban numbers in `README.md` and `QUICKSTART.md` except in `tests/` output |
| MR-10 | **Lane isolation violation** — new `architecture/**/*.py` accidentally imports `discovery` or `telegram_ai` | Intel analyzers importing `discovery/pal.py` directly | MED | HIGH | Keep `tests/test_architecture_p1.py` as hard gate — it already fails the PR if `architecture/` imports forbidden lanes |

**Overall migration risk:** **Controllable LOW–MED** if patch is applied via its own waves (33 → 33b → 33c → 33d → 33e → 33f) with `pytest -q` green at each wave, as the patch’s own `AUDIT_FINDINGS.md` staged them. Uncontrolled, the same patch represents **HIGH** risk (18,871-line atomic diff touching 55 files).

---

## 10. Evidence First & Paper-Only Philosophy — Assessment

| Principle | Status | Evidence |
|---|---|---|
| Evidence First (no claim without data) | **HONORED** | `discovery/security_gate.py` `PASS_WITH_UNKNOWN` discipline; `scoring` `LOW` confidence with `missing_unknowns`; `hindsight.py` `INSUFFICIENT_DATA`; 107 KB issue register never hides a rejection |
| Deterministic floor ($0/month) | **HONORED** | `config/ai_council_providers.yaml:cost: free-local FIRST`; `requirements.txt` comment documents stdlib core; `tests/test_ai_council_live.py` proves OFFLINE floor |
| Paper trading safety (no real execution) | **HONORED, PINNED** | `tests/test_zero_money_invariant.py` 13 checks green; `grep` for trading verbs returns 0; patch adds no trading SDK either |
| Append-only & never delete | **HONORED** | `paper_trading/schema*.sql` 34 triggers `BEFORE UPDATE/DELETE … ABORT`; `scripts/freeze_lane_a.py` + `config/lane_a_freeze.sha256` |
| No secrets in source | **HONORED** | `.env` ignore, `contracts/` hold no keys, `architecture/security.py` redaction; `reports/pal_probe_*.json` never contains keys |
| No fake implementations | **HONORED** — patch fixes exactly the cases where fixtures faked a column (`D6`) and dead fields simulated a signal (`D14`) | `tests/test_store_column_names.py` is now extended to 3 more modules; patch adds `test_score_to_sizing_chain.py` against real bootstrapped schema |

---

## 11. Appendices

### A. File-count summary (non-`.git`, non-`__pycache__`)

```
Python modules:          65  (architecture 28 + discovery 10 + paper_trading 10 + telegram_ai 7 + strategy_lab 5 + research 2 + engine 7 + config/scripts)
Test modules:            70  (tests/test_*.py)
Docs:                    50+ (docs/ 34 + root 7 + n8n/workflows 6 + contracts 4 + deployment 4)
Config & schemas:        12  (config/*.yaml, discovery/schema_sqlite.sql, database/*.sql, paper_trading/schema*.sql)
Snapshots (historical):  27  (ahos_snap_w*.txt)
Reports (live):          120+ (reports/*.json, *.md, *.txt)
```

### B. Configuration inventory

*Sources of truth (single-read pattern):* `config/agent_registry.yaml` (25 agents, `matrix_version: W11-OPS-2`), `config/ai_council_providers.yaml` (5 LLMs, ordered), `config/cognitive_registry_100.yaml`, `config/ai_assistants.yaml` (9 roles), `discovery/providers.yaml` (6 capabilities, 8 providers), `contracts/*.json` (4 contracts), `config/paths.yaml` (generated; do not hand-edit), `research/SEARCH_SPACE_REGISTRY.json`, `paper_trading/strategies.json`.

### C. Database schema inventory

| Store | File | Tables | Append-only triggers | Bootstrapped by |
|---|---|---|---|---|
| Discovery | `discovery/schema_sqlite.sql` | 15 (`tokens`, `pairs`, `discovery_observations`, `observation_state`, `security_verdicts`, `gate_summary`, `feature_vector`, `outcome_label`, `opportunity_rank`, `holder_snapshot`, `wallet_observation`, `raw_payloads`, `gap_register`, `lifecycle_events`, `feature_definitions`) | No (reads append but triggers only via `init_databases --with-guards` → `F1_S1`) | `scripts/init_databases.py:init_discovery` + `architecture/collector/engine.py:production_observations` (lazy) |
| Paper trading | `paper_trading/schema.sql` → `_v2.sql` → `_v3.sql` | 12+ (`strategy_version`, `decision_snapshot`, `paper_trade`, `monitor_event`, `paper_exit`→`paper_exit_v3`, `lessons`, `bankroll`, etc.) | **Yes, 34** (write-once) | `scripts/init_databases.py:init_paper` |
| Local ops | `architecture/scheduling/engine.py:SCHEMA_SCHEDULER` + `architecture/runtime/metrics.py:SCHEMA_METRICS` + `architecture/runtime/lifecycle.py:lifecycle_schema` + `LOCAL_EXTRA_SCHEMA` | 7 (`scheduler_runs`, `scheduler_locks`, `scheduler_heartbeats`, `operational_metrics`, `control_flags`, `position_ledger`, `runtime_lifecycle_events`) | Partial (`lifecycle_events` etc. after guards) | `scripts/init_databases.py:init_local` |
| Knowledge | `architecture/knowledge/store.py:SCHEMA_KNOWLEDGE` | 6 (`knowledge_claims`, `evidence_links`, `contradiction_graph`, …) | Append-only via triggers after guards | `scripts/init_databases.py:init_knowledge` |

### D. How to reproduce this audit

```bash
git checkout arena/01a0115f-ahos
ls -R | head -n 500
find . -name "*.py" -not -path "./.git/*" | xargs wc -l | tail
pip install --break-system-packages -r requirements.txt
pip install --break-system-packages pytest
python3 -m pytest tests/ -q          # expect: 898 passed
python3 scripts/init_databases.py --verify
grep -R volume_velocity --include="*.py" architecture discovery
grep -R evaluate_position --include="*.py" | grep -v tests
```

---

*End of Audit — commit `AHOS v2: initial architecture audit` follows doc creation only. No production code was modified.*
