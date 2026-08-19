# Current architecture map

## 1. Scope and architectural reality

This map describes the executable checkout at `c77597899dce60d192abe94cb017279089b065f7`, not the union of historical phase reports. AHOS is not one process graph. It contains four principal graphs:

1. the canonical opportunity runtime;
2. the frozen Lane-A observation/research path;
3. the conversational Telegram path;
4. several isolated governance, control-plane, paper-research, n8n, PostgreSQL, and agent designs.

The first three share SQLite files and selected domain modules but do not form a single transactional system. The fourth group is mostly isolated or host-gated.

## 2. Canonical runtime graph

Primary entry point: `python -m architecture.runtime` (`architecture/runtime/__main__.py`).

```text
architecture.runtime.__main__
  -> ApplicationLifecycleManager
     -> StartupValidator / health / runtime lifecycle ledger
  -> ProductionScheduler
     -> scheduler_runs / scheduler_locks / scheduler_heartbeats
  -> CollectorEngine
     -> architecture.providers.registry.ProviderRouter
     -> DexScreener + GeckoTerminal discovery adapters
     -> production_observations / provider_failure_events in e01_discovery.sqlite
  -> OpportunityPipelineOrchestrator
     -> normalized candidate
     -> materialize_evidence
     -> IntelligenceEngine
        -> SecurityIntelligence
        -> composed WhaleIntelligence
        -> FeatureExtractor -> RiskEngine -> OpportunityCalculator -> ExplanationEngine
     -> OpportunityScorer
     -> optional ScoreLedger in ahos_local.sqlite
     -> ExitabilityAnalyzer + ViralityTracker + WhaleTracker
     -> CognitivePanel -> DecisionAdvisor
     -> AlertEngine
     -> optional Telegram adapter / announcement memory
     -> optional canonical paper-position review
  -> TelegramBotRunner.process_pending_updates
  -> OperationalMetricsTracker
```

Important boundaries:

- The collector/pipeline path uses `architecture/providers/*`; it does not use `discovery/pal.py`.
- `architecture/intelligence/*` accepts `EvidenceBundle`, not raw provider payloads. This boundary is statically enforced by `scripts/validate_imports.py`.
- `ScoreLedger` is explicitly injected. Ad-hoc pipeline construction does not persist predictions, preventing accidental calibration contamination.
- Runtime startup injects a ledger and resolves its source to `sandbox` unless the operator explicitly selects `local`.
- Alerts and `ENTER` vocabulary are advisory. No exchange SDK, wallet signing, transaction, or order-placement path was found.

### Runtime execution modes

| Mode | Command | Actual behavior | Status |
|---|---|---|---|
| Single cycle | `python -m architecture.runtime --single-cycle` | one scheduler cycle: provider collection, scoring, vetting, Telegram update poll | `IMPLEMENTED`, `REQUIRES_EXTERNAL_SERVICE` |
| Daemon | `--daemon` | repeated scoring cycle only | `IMPLEMENTED` |
| Observation daemon | `--daemon --observation-cycle` | scoring plus frozen Lane-A observation/outcome materialization | `IMPLEMENTED`, externally dependent |
| Provider probe | `--probe-providers` | read-only reachability classification; writes a report | `IMPLEMENTED`, externally dependent |
| Windows launcher | `start_ahos.ps1` / `.bat` | observation daemon with source `local` | statically verified, `REQUIRES_USER_ACTION` |

## 3. Frozen Lane-A observation/research graph

```text
architecture.runtime.observation_loop.ObservationRuntime
  -> runtime safety gate
     -> architecture.security.assert_safe_environment
     -> scripts.freeze_lane_a.verify (36 pinned files)
  -> discovery.observe_active.run_observe_active
     -> discovery.pal.PAL
        -> config/providers.yaml
        -> keyless/optional provider clients, rate/cache/breaker envelopes
     -> discovery.observations / discovery/schema_sqlite.sql
        -> raw_payloads
        -> tokens / pairs / discovery_observations
        -> observation_state / lifecycle_events / gap_register
  -> discovery.materialize.materialize_outcomes
     -> feature_vector / outcome_label
  -> operational metrics
```

Research consumes frozen/manifested data through `research/*`, `strategy_lab/*`, and the versioned `paper_trading/*` engines. This lane is intentionally separate from the opportunity runtime's `production_observations`. Both families currently write tables into `data/e01_discovery.sqlite`; schema ownership is therefore shared even though code ownership is separate.

Status: `IMPLEMENTED`, `EXPERIMENTAL`, `REQUIRES_EXTERNAL_SERVICE`. The mechanics are extensively tested. This audit's generated store contained zero discovery rows, so live data accumulation is not currently proven.

## 4. Telegram graphs

### 4.1 Standalone bot

Entry point: `python run_bot.py`.

```text
run_bot.py
  -> .env loader
  -> preflight
  -> ProductionTelegramAdapter long-poll
  -> TelegramSecurityGate
  -> TelegramBotRunner
  -> TelegramDomainService
     -> intents / Persian NLU / response contracts
     -> provider-backed token lookup and deterministic scoring
     -> paper buy-statement ledger
     -> on-demand hindsight/exit advice
     -> optional LiveCouncil for explicit AI-assisted analysis
  -> data/telegram_offset.json
```

`--console` is an offline REPL; `--preflight` performs a live Telegram `getMe` when a token is present.

### 4.2 Telegram inside canonical runtime

`architecture.runtime.__main__` builds the same adapter, gate, runner, and domain service, then polls pending updates once per scheduler cycle. Unlike `run_bot.py`, this embedded path calls `poll_updates()` without a persisted/advanced offset, so a real Telegram backlog can be returned repeatedly. It also uses the adapter for proactive vetted alerts.

### 4.3 Security boundary

- Token values are loaded from environment and exception text is scrubbed.
- HTML-controlled fields are escaped in the integrated announcement path.
- Empty `TELEGRAM_ALLOWED_CHAT_IDS` means **open access**, not deny-by-default. This is a deployment blocker for a private single-user bot.
- `ProductionTelegramAdapter.poll_updates()` swallows every exception and returns an empty list, so `run_bot.py`'s outer network-error/backoff branch cannot observe ordinary poll failures.
- `send_message()` also converts failures to `{"ok": false}`; pipeline callers do not inspect that result and increment delivery counts/record announcements anyway. Delivery metrics can therefore be false-positive.
- Live Telegram operation was not executed during this audit.

Status: domain behavior `IMPLEMENTED`; network delivery/poll accounting `BROKEN`; authorization default `BROKEN` for a private deployment expectation.

## 5. Persistence and schema lineage

| Store/artifact | Schema owners | Runtime writers | Audit state | Ownership status |
|---|---|---|---|---|
| `data/e01_discovery.sqlite` | `discovery/schema_sqlite.sql`; `CollectorEngine` adds two production tables | frozen observation poller, outcome materializer, production collector | 17 tables, 0 rows, integrity OK | `PARTIALLY_IMPLEMENTED`; shared ownership needs migration ledger |
| `data/paper_trading.sqlite` | `paper_trading/schema{,_v2,_v3}.sql`; bootstrap | versioned paper engines; canonical monitor reads it for tracked tokens | 19 tables, 0 rows, integrity OK | intentional versioned research store |
| `data/ahos_local.sqlite` | bootstrap plus runtime scheduler/metrics/lifecycle/score and Telegram position DDL | scheduler, metrics, lifecycle, score ledger, Telegram paper log | 9 tables, 20 contaminated control rows | operational store; test/import isolation is `BROKEN` |
| `data/ahos_knowledge.sqlite` | `architecture/knowledge/store.py` via bootstrap | knowledge claim store | 2 tables, 0 rows | `IMPLEMENTED` structure, empty evidence |
| `database/schema_v1_2.sql`, `schema_v1_3.sql` | PostgreSQL twin of discovery | no delivered Python runtime writer | not executed | `ORPHAN`, target migration assets |
| `database/postgresql_schema.sql` | separate target-domain schema | n8n target workflows by design | not executed | `SCAFFOLD`, not equivalent to SQLite canonical stores |
| Research CSVs/manifests | `engine/acquire_3yr.py`, `engine/data_audit.py` | acquisition scripts | 12 outputs hash/row/time match | tracked evidence; provenance/replay limitations remain |

All four SQLite files are ignored runtime state, not tracked source. All have `PRAGMA user_version=0`; schema evolution is inferred from idempotent DDL rather than an explicit migration version.

## 6. Subsystem integration map

“Tests” lists representative evidence, not every test module.

| Subsystem | Files / entry points | Inbound -> outbound | Tests / schemas / config | Reality status |
|---|---|---|---|---|
| Runtime lifecycle | `architecture/runtime/{__main__,lifecycle,logging,metrics,observation_loop}.py` | launchers/Docker -> scheduler, collector, pipeline, Telegram | runtime/lifecycle/hardening/phase tests; local SQLite DDL | `IMPLEMENTED`, external operation unproven |
| Scheduling | `architecture/scheduling/{engine,watchdog}.py` | runtime -> task callbacks, heartbeat/lock tables | scheduler phase/fault/hardening tests | `IMPLEMENTED`; no Windows service supervisor |
| Market discovery (runtime) | `architecture/collector/engine.py`, `architecture/providers/*` | runtime -> HTTP adapters -> production observations | provider/collector/E2E/failure tests | `IMPLEMENTED`, `REQUIRES_EXTERNAL_SERVICE` |
| Observation discovery (Lane A) | `discovery/*`, `config/providers.yaml` | observation loop/CLIs -> PAL -> discovery schema | discovery, observation, E-01, failure tests; 36-file hash freeze | `IMPLEMENTED`, `EXPERIMENTAL`, external data required |
| Evidence | `architecture/intelligence/evidence.py`, adapters | normalized candidate -> immutable evidence bundle | architecture, feature-boundary, security tests | `IMPLEMENTED` |
| Features/risk/scoring/explanations | `architecture/{features,risk,scoring,explanations}/*` | Evidence only -> report | deep matrices, integration, invariant tests; weights config | `IMPLEMENTED` |
| Security intelligence | `architecture/security/*`, `intelligence/engine.py` | evidence -> findings/vetoes -> risk/score | hardening/intelligence/provider tests | `IMPLEMENTED`; live source quality external |
| Whale intelligence | `architecture/intelligence/whales.py`; `architecture/intel/whales.py` | evidence-composed engine plus specialist vetting context | whale, exitability, integration tests | both implemented; overlapping semantics require reconciliation |
| Specialist intelligence | `architecture/intel/{exitability,forensics,news,viral,whales}.py` | candidate/report -> panel/advisor/council context | focused unit tests | `IMPLEMENTED` with some external inputs absent |
| Decision/advice | `architecture/decision/advisor.py` | score + specialist reports + panel -> ENTER/WAIT/AVOID advice | advisor, pipeline vetting, sizing tests | `IMPLEMENTED`, advisory-only |
| Knowledge/cognitive panel | `architecture/knowledge/*`, team YAML | candidate/report/calibration -> 42 deterministic lenses -> panel | panel, lenses, teams, coverage tests; knowledge DB | `IMPLEMENTED`; registry breadth exceeds executed coverage |
| AI council | `architecture/ai/*`, `config/ai_council_providers.yaml` | explicit Telegram intent -> provider chat APIs -> advisory verdict | 24 focused live-council tests using injected clients | `PARTIALLY_IMPLEMENTED`, external/local service required |
| AI provider router contract | `architecture/provider_router.py`, `config/ai_provider_registry.yaml` | tests/control-plane design only | `test_runtime_w11.py` | `ORPHAN`; not used by LiveCouncil |
| Legacy Telegram AI PAL | `telegram_ai/providers.py`, `telegram_ai/ai_providers.yaml` | tests only | `test_telegram_ai.py` | `ORPHAN`, `DUPLICATE` |
| Prediction ledger/calibration | `architecture/learning/{score_ledger,calibration}.py`, calibration CLI | runtime scores + Lane-A outcomes -> source-isolated descriptive calibration | 58 focused tests; local score table | code `IMPLEMENTED`; empirical capability `INSUFFICIENT_DATA` |
| Paper positions (canonical) | `architecture/positions/{manager,monitor}.py` | optional manager callers -> runtime monitor -> advice/alerts | manager/monitor/ledger tests; local DDL in module | `IMPLEMENTED`, empty store |
| Paper research engines | `paper_trading/{engine,engine_v2,engine_v3,...}` | CLIs/research -> discovery RO -> versioned paper store | v1/v2/v3/v3.2 tests; 3 SQL schemas | `EXPERIMENTAL`, deliberately versioned |
| Telegram paper log | `telegram_ai/positions.py` | Persian buy statement -> `position_ledger` -> on-demand advice | Telegram/position schema tests | `IMPLEMENTED`; not canonical allocation store |
| Research | `research/*`, `strategy_lab/*`, acquisition/audit scripts | manifested CSV/SQLite -> baseline/backtest reports | baseline, strategy, wave tests | `IMPLEMENTED`, `EXPERIMENTAL`; no current outcome evidence |
| Telegram domain | `telegram_ai/*`, `run_bot.py` | user/update -> intents/scoring/AI/health -> response | extensive NLU/service/adapter tests | `IMPLEMENTED`; live connectivity/user setup required |
| Registry | `architecture/registry.py`, `config/agent_registry.yaml` | standalone registry/control-plane design | matrix/runtime tests | `PARTIALLY_IMPLEMENTED`; YAML claims are historically stale |
| Control plane | `architecture/control_plane.py`, `config/control_plane.yaml` | direct callers/tests -> injected probes -> control ledger | W11 + soak tests | `ORPHAN`, simulated/injected; no production entry point |
| Evolution/learning governance | `architecture/evolution/{engine,hindsight}.py`, proposal contract | explicit service call; hindsight used by Telegram | evolution/hindsight tests | hindsight `IMPLEMENTED`; self-evolution `SCAFFOLD` |
| Update/self-repair | `engine/{update_manager,health_manager}.py` | manual CLI/tests; health read by some operational responses | health/update tests | `PARTIALLY_IMPLEMENTED`; no autonomous repair/update |
| n8n | `n8n/workflows/*.json`, setup docs | manual import -> Postgres/Telegram/Execute Command | 6/6 static validator | `ORPHAN`, external credentials/import/mounts required |
| Docker/Compose | root compose; `deployment/Dockerfile`; four deployment compose profiles | Docker -> runtime/bot/n8n/target infra | static config tests only | `BROKEN` packaging risk; runtime unproven |
| Windows | installer, PS/batch launchers, Windows compose/runbooks | operator -> venv/bootstrap/runtime | static and subprocess-on-Linux tests | `PARTIALLY_IMPLEMENTED`, native execution required |
| Security/hygiene | `architecture/security/*`, secret/import gates, `.gitignore` | runtime/tests -> veto/redaction/scans | security/zero-money/import tests | code strong; Docker context and Telegram default are RED |
| Evidence/reporting | `scripts/{record_test_run,evidence_common,system_state_snapshot,...}` | explicit CLI -> reports | evidence/static tests | `IMPLEMENTED`; reports are point-in-time only |
| OSS intelligence | spec, agent registry AG-25, one metadata report | manual GitHub metadata audit -> candidate record | `test_oss_*` largely validates schema/spec | `SCAFFOLD`; no automated sandbox pipeline |

## 7. Configuration map and precedence

| Configuration | Consumer | Finding |
|---|---|---|
| `.env` / `.env.example` | native runtime and bot | ignored secret file; two simple loaders overlap; blank chat allowlist opens bot access |
| `config/providers.yaml` | frozen discovery PAL | active only in Lane-A observation path |
| hardcoded provider set in `architecture/providers/registry.py` | canonical runtime collector | separate from `config/providers.yaml`; no single provider inventory |
| `config/ai_council_providers.yaml` | active `architecture.ai` LiveCouncil | canonical current chat transport registry |
| `config/ai_provider_registry.yaml` | isolated AI router | not connected to LiveCouncil |
| `telegram_ai/ai_providers.yaml` | legacy AIPAL | tests only |
| `config/agent_registry.yaml` | control plane/tests/docs | internally machine-readable but not synchronized with current integration/evidence |
| `config/control_plane.yaml` | isolated control plane | target infrastructure assumptions, not canonical runtime wiring |
| `requirements*.txt` | installers/Docker | 8 core and 3 optional lower bounds; no lock/checksums/packaging metadata |

## 8. Documentation cross-reference by subsystem

| Subsystem group | Current/canonical or operational docs | Historical/design docs retained |
|---|---|---|
| Overall runtime/architecture | `README.md`, `ARCHITECTURE.md`, `docs/canonical/{CANONICAL_STATUS,ARCHITECTURE,DATA_MODEL}.md` | root phase/reality/readiness reports; `reports/PHASE_STATE.md` |
| Discovery/providers/provenance | `docs/canonical/{DISCOVERY,PROVIDERS}.md`, Windows provider-probe steps | E-01 experiment reports, provider comparison/probe reports, issue-register entries |
| Evidence/intelligence/security/risk/scoring | canonical architecture/security docs and score/security design docs | phase-21/22 reports and mission/design records |
| Research/paper/calibration | `docs/canonical/RESEARCH.md`, strategy specs, soak/calibration instructions | `research/reports`, `research/experiments`, wave/paper phase reports |
| Telegram/alerts/positions | `docs/canonical/TELEGRAM.md`, `docs/TELEGRAM_TEST_PROCEDURE.md`, `run_bot.py` usage | earlier Telegram phase reports and source patches |
| Scheduling/runtime/operations | `QUICKSTART.md`, `INSTALLATION.md`, `docs/RUNBOOK_OPERATIONS.md`, local activation/soak protocols | phase-7/month-1/operational gate reports |
| Windows | Windows quickstart/deployment guide/operator runbook and activation checklist | phase-13/17/18/19 reports |
| Docker/n8n/PostgreSQL | root compose comments, `docs/n8n_setup_guide.md`, deployment file headers | target orchestration comparisons/designs |
| AI/Local AI/council/knowledge | canonical status/knowledge map, council/provider configs | `docs/architecture/*`, phase-22 intelligence reports |
| Agents/control/evolution/autonomy | governance/master directive, `docs/AGENT_MODE_OPERATIONAL_DIRECTIVE_FA.md` | agent matrix, OSS/self-repair/update designs and phase reports |
| Evidence/test/security | `SECURITY.md`, `CONTRIBUTING.md`, canonical status validation record | dated test/audit/readiness artifacts |
| Documentation/history | `docs/DOCUMENT_CLASSIFICATION.md` | `docs/archive`, `docs/history/source-patches`, `docs/history/snapshots` |

This cross-reference is an index, not proof. The drift report identifies where a current-looking document has weaker evidence than its wording.

## 9. Disconnected and external graphs

- n8n workflows are not automatically imported. Workflows 01–03 need PostgreSQL nodes, while the canonical root compose has no PostgreSQL. Workflows 10–12 execute commands under `/opt/ahos`, but delivered n8n services do not mount the repository there.
- PostgreSQL schemas and target compose profiles are not consumed by the canonical Python runtime.
- Temporal, Prometheus, and Grafana exist only in the target compose design.
- `architecture/control_plane.ControlPlane` has no production launcher and all current probes are injected by callers.
- `SelfEvolutionEngine` advances an in-memory proposal; it does not inspect a repository, edit code, run tests, use Git, deploy, monitor, or execute rollback.
- Ollama is a configured HTTP endpoint. No model installation, model presence, hardware benchmark, embedding, RAG, or vector-store path exists.

## 10. Architectural conclusion

The best-supported architecture is a conservative, deterministic, paper-only opportunity intelligence runtime with a separate frozen observation experiment. It should be preserved. The next engineering phase should reduce parallel configuration/schema/runtime ownership and prove the delivered host paths; it should not replace the repository wholesale or add another agent framework.
