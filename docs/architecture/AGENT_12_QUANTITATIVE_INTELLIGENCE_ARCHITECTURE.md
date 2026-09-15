# Agent Organization Quantitative Intelligence Architecture

```text
DOCUMENT_ID      = AGENT_12_QUANTITATIVE_INTELLIGENCE_ARCHITECTURE
MISSION_ID       = TASK-20260914-013
VERSION          = 0.1.0
STATUS           = PROPOSED / READ_ONLY_QUANTITATIVE_INTELLIGENCE_ARCHITECTURE
AUTHORITY        = NONE CREATED
RUNTIME_EFFECT   = NONE
AHOS_EFFECT      = NONE
AGENT_ID         = AGENT-12 (agent.org.12-quant-backtesting — documentary)
DIRECT_COMMANDER = MASTER ORCHESTRATOR
PARENT           = MASTER ORCHESTRATOR
```

This document is a **design and architecture artifact** produced by AGENT-12 under explicit activation for TASK-20260914-013. It does not implement a quant engine, adopt governance, grant authority, modify AHOS, connect providers, execute backtests from this repository, or promote knowledge. Facts cite repository evidence with explicit classification labels (`[IMPLEMENTED]`, `[DOCUMENTED]`, `[PARTIALLY_IMPLEMENTED]`, `[PROPOSED]`, `[UNKNOWN]`). Architectural recommendations are labeled `[PROPOSED]`.

**Critical honesty constraint:**

```text
OBSERVATION             ≠ FEATURE
FEATURE                 ≠ SIGNAL
SIGNAL                  ≠ PREDICTION
PREDICTION              ≠ OUTCOME
OUTCOME                 ≠ KNOWLEDGE
BACKTEST                ≠ FUTURE PROOF
SIMULATION              ≠ EXECUTION
CORRELATION             ≠ CAUSATION
STATISTICAL SIGNIFICANCE ≠ PRACTICAL SIGNIFICANCE
MODEL CONFIDENCE        ≠ REAL-WORLD SAFETY
HIGH SHARPE             ≠ ROBUST STRATEGY
PROFITABILITY           ≠ VALIDITY
REPEATABILITY           ≠ CAUSALITY
SAMPLE SIZE             ≠ EVIDENCE QUALITY
NO DETECTED EFFECT      ≠ NO EFFECT
UNKNOWN                 ≠ ZERO
MISSING DATA            ≠ ZERO
DATA AVAILABILITY       ≠ DATA QUALITY
SURVIVORSHIP            ≠ REPRESENTATIVENESS
HISTORICAL STABILITY    ≠ FUTURE STABILITY
PARAMETER FIT           ≠ GENERALIZATION
OUT-OF-SAMPLE           ≠ IMMUNE TO OVERFITTING
P-VALUE                 ≠ TRUTH
EXPECTED VALUE          ≠ SAFETY
PROBABILITY ESTIMATE    ≠ FACT
SCENARIO                ≠ PREDICTION
STRESS TEST             ≠ GUARANTEE
QUANT VALIDATION        ≠ GOVERNANCE ACCEPTANCE
QUANT VALIDATION        ≠ PRODUCTION ADMISSION
```

**Additional invariants (Agent-12 derived):**

```text
VECTOR SCREEN           ≠ CAUSAL BACKTEST
REGISTRY ENTRY          ≠ VALIDATED STRATEGY
CALIBRATION HARNESS     ≠ CALIBRATED SYSTEM
INSUFFICIENT_DATA       ≠ FAILURE (often correct early state)
NEGATIVE RESULT         ≠ WASTED WORK
FEATURE DEFINITION      ≠ FEATURE AVAILABILITY AT DECISION TIME
PRE-REGISTERED CELL     ≠ INDEPENDENT HYPOTHESIS (multiplicity remains)
OPPORTUNITY DETECTION   ≠ PORTFOLIO OPTIMIZATION
SECURITY VETO CLEAR     ≠ SAFE TO TRADE
CROSS-ASSET OOS PASS    ≠ UNIVERSAL EDGE
```

---

## 1. Executive Summary

`[VERIFIED]` **Two repositories, two quant postures:**

| Repository | Quant posture |
| --- | --- |
| **AHOS** (`G:\robat\ahos`) | Substantial **implemented** quant research stack: causal backtest engines, strategy lab with fixed gates, feature store with machine-enforced leakage laws (L1–L4), pre-registered search-space cells, calibration harness (read-only), paper-trading simulation tests. **Zero accepted strategies** (0/8+ testable hypotheses REJECTED). Live calibration measurement blocked on outcome accrual (`0 joined_pairs` reported). |
| **Agent Organization** (`G:\robat\ahos-agent-org`) | **No quant runtime.** Slice 1 logical roles (`agent.scoring-science`, `agent.paper-trading`, `agent.calibration`) are inspect-only registry entries. Slice 2B provides generic `ExperimentPlan` / `ExperimentRun` epistemic types — not domain quant contracts. Research worker cannot execute backtests. |

**Central architectural question:**

> What quantitative claims can AHOS legitimately make, under what data, methodology, uncertainty, validation, and failure conditions?

**Agent-12 role:** Own **backtest/study validity**, **statistical use of upstream features**, **performance measurement design**, **leakage defense**, and **quantitative evidence lineage** — while **not** owning feature semantics (07–09), security verdicts (10), risk framing (11), epistemic promotion (05), or methodology authority (06).

**Minimum defensible quant core for launch:** Point-in-time feature joins + pre-registered opportunity evaluation + read-only calibration + negative-result registry + explicit quant→epistemic handoff. Full event-driven DEX microstructure backtesting and ML model registry are **future excellence**, not launch blockers for an evidence-first opportunity intelligence platform.

**Launch blockers (quant-relevant):** (1) insufficient local calibration pairs, (2) no unified quant governance bridge between AHOS strategy lab and org epistemic TCB, (3) survivorship/point-in-time universe gaps for token discovery research, (4) dual paper/backtest ledger surfaces not reconciled.

**Operating baseline:** Agent-12 operated per P1/P2/P3 for this mission. `BASELINE_PROPAGATION = BASELINE_NOT_PROPAGATED` — not claimed adopted org-wide.

---

## 2. Repository Forensics

### 2.1 Agent Organization (`G:\robat\ahos-agent-org`)

| Path | Finding | Classification |
| --- | --- | --- |
| `ahos_org/registry.py` | Logical roles: `agent.scoring-science`, `agent.paper-trading`, `agent.calibration` — inspect-only, no prod scoring | `[IMPLEMENTED]` registry only |
| `ahos_org/policy.py` | Global denies: `trading.live`, `provider.connect`, `credentials.access`, `ahos.*` | `[IMPLEMENTED]` `[TESTED]` |
| `agent_org/epistemic.py` | `ResearchMission`, `ExperimentPlan`, `ExperimentRun`, `Hypothesis`, promotion gates | `[IMPLEMENTED]` `[TESTED]` |
| `research_worker/` | Bounded analyst; `execution_requested: False`; no statistical computation | `[IMPLEMENTED]` |
| `docs/architecture/AGENT_05..11_*.md` | Peer architecture inputs — design only | `[DOCUMENTED]` |
| `docs/architecture/AGENT_12_*` | Did not exist before this mission | `[NONE]` → now `[DOCUMENTED]` |

**No backtest engine, feature store, metrics library, or quant tests** in agent-org.

### 2.2 AHOS (`G:\robat\ahos`) — read-only inspection

#### Backtesting engines

| Module | Capability | Causality strictness |
| --- | --- | --- |
| `engine/ahos_backtest.py` | Frozen baseline v1.0; signal@close t → entry@open t+1; fees, slippage, DD cap, MC, WFA | **Strict** — pytest-proven no look-ahead |
| `strategy_lab/lab_engine.py` | Generic causal backtester for registered hypothesis generators | **Strict** — prefix-causality tests |
| `strategy_lab/vector_engine.py` | Fast parameter grid sweep | **Weaker** — same-bar price for entry/exit checks |
| `engine/event_backtest.py` | Discrete-event DEX sim: AMM slippage, latency, partial fills | **Event-ordered** — pool liquidity fallback when ≤0 |
| `strategy_lab/validation_engine.py` | Purged K-fold + embargo, rolling WFA, OOS efficiency, MC permutation | `[IMPLEMENTED]` |
| `strategy_lab/run_lab.py` | Full battery: Train 70%/OOS 30%, WFA, MC(1000), stress 2× costs, registry | `[IMPLEMENTED]` |

#### Feature / signal / model surfaces

| Surface | Location | Notes |
| --- | --- | --- |
| Discovery feature store | `discovery/feature_store.py` | fs_v0.1/v0.2; L1–L4 leakage laws; architecture tests |
| Scoring feature extractor | `architecture/features/extractor.py` | Rule-based; feeds `OpportunityCalculator` |
| Strategy registry | `strategy_lab/registry.json` | H1–H12: all TESTED → REJECTED or DATA-BLOCKED |
| Search-space registry | `research/SEARCH_SPACE_REGISTRY.json` | Pre-registered B1/B2 cells; evaluation via `baseline_stats.py` |
| ML model registry | — | **Absent by design** — rule-based / grid-sweep only |

#### Calibration

| Component | Status |
| --- | --- |
| `architecture/learning/calibration.py` | `[IMPLEMENTED]` — no-peeking join, pre-declared bands, read-only |
| `architecture/learning/score_ledger.py` | `[IMPLEMENTED]` — append-only predictions |
| `scripts/calibration_report.py` | `[IMPLEMENTED]` |
| Live measurement | `[PARTIALLY_IMPLEMENTED]` — M-GAP-008 OPEN; operator evidence: 0 joined_pairs |

#### Data / reproducibility

| Artifact | Mechanism |
| --- | --- |
| `research/data/MANIFEST.json` | sha256-pinned BinanceVision 3.6y datasets |
| `database/postgresql_schema.sql` | `dataset_version` column on market tables |
| Baseline validation data | ~83-day LBank CSVs (separate from 3.6y lab data) |

#### Empirical outcomes (verified)

- `reports/BACKTEST_REPORT_EXACT.md`: Frozen baseline v1.0 **no edge** on available data; live gate CLOSED.
- `research/reports/RESEARCH_FINDINGS_v2.0.md`: **0/8 accepted** strategy lab candidates; process working as designed.
- H6 BTC anomaly noted but **REJECTED** for cross-asset instability and train-window failure.

### 2.3 Forensic gaps (`CAPABILITY_GAP`)

| Gap | Reason |
| --- | --- |
| Live production DB contents | Not accessed — credentials/production forbidden |
| 72-hour soak runtime state | Not disturbed — mission constraint |
| Full on-chain historical archive | Not verified — Agent 09 flags indexer vs archive node tension |
| Telegram/n8n live paths | Not activated |

---

## 3. Current Quantitative Capabilities

### 3.1 Classification matrix

| Capability | AHOS | Agent Org | Launch relevance |
| --- | --- | --- | --- |
| Causal bar backtest | `[IMPLEMENTED]` | `[NONE]` | Research path exists in AHOS |
| Strategy lab gate battery | `[IMPLEMENTED]` | `[NONE]` | Strong internal discipline |
| Feature store + L1–L4 | `[IMPLEMENTED]` | `[NONE]` | **Core for opportunity eval** |
| Pre-registered search cells | `[IMPLEMENTED]` | `[NONE]` | Multiplicity partial defense |
| Calibration harness | `[IMPLEMENTED]` | `[NONE]` | **Launch-critical when pairs accrue** |
| Calibration measurement | `[PARTIAL]` | `[NONE]` | **Launch blocker** |
| Point-in-time token universe | `[DOCUMENTED]` plan only | `[NONE]` | **Launch blocker for broad backtest claims** |
| Survivorship controls | `[DOCUMENTED]` OSS plan | `[NONE]` | High-risk for token research |
| ML model registry / training | `[NONE]` by design | `[NONE]` | Deferred (Agent 13) |
| Org quant TCB types | `[NONE]` | `[PROPOSED]` | Integration gap |
| Independent quant verification | `[SELF-TEST ONLY]` | `[NONE]` | Agent 16 not engaged |
| Paper trading sim | `[IMPLEMENTED]` tests | logical role only | Dual-ledger tension |

### 3.2 What AHOS can legitimately claim today

| Claim type | Legitimate? | Evidence |
| --- | --- | --- |
| "Engine is deterministic and no-look-ahead on tested paths" | **Yes** (bounded) | `tests/test_ahos.py`, `tests/test_strategy_lab.py` |
| "Frozen baseline v1.0 has no demonstrated edge on audited data" | **Yes** | `BACKTEST_REPORT_EXACT.md` |
| "No strategy candidate passed full lab gates" | **Yes** | `registry.json`, `RESEARCH_FINDINGS_v2.0.md` |
| "Feature store enforces L1–L4 on tested fixtures" | **Yes** (unit scope) | `tests/test_feature_store_boundaries.py` |
| "Scoring is calibrated" | **No** | 0 joined_pairs; harness untested on live cohort |
| "Backtest proves future performance" | **No** | Explicitly contradicted by own reports |
| "H6/H10 BTC OOS results are production-ready strategies" | **No** | REJECTED for instability / sample / cross-asset |

---

## 4. Quantitative Epistemology

### 4.1 Quantitative truth pipeline

```text
RAW OBSERVATION
        ↓  [Agent 07: DataArtifact, quality, lineage]
DATA VALIDATION
        ↓  [cutoff_policy, quarantine, conflict resolution]
POINT-IN-TIME DATASET
        ↓  [InformationCutoff(T), universe_definition]
FEATURE / TRANSFORMATION
        ↓  [Feature Registry; FEATURE_VERSION ≠ MODEL_VERSION]
SIGNAL
        ↓  [Signal Registry; threshold + validity window]
HYPOTHESIS / MODEL
        ↓  [Model Registry; deterministic / statistical / ML]
PREDICTION
        ↓  [timestamp, uncertainty, provenance]
DECISION-SIMULATION
        ↓  [cost matrix explicit; no silent promotion]
SIMULATED EXECUTION
        ↓  [fees, slippage, latency, partial fills]
OBSERVED OUTCOME
        ↓  [label horizon closed; no peeking]
PERFORMANCE ANALYSIS
        ↓  [metrics suite by objective]
FAILURE ANALYSIS
        ↓  [failure taxonomy]
REPLICATION
        ↓  [same input/version/method ≈ same result]
GENERALIZATION TEST
        ↓  [time/asset/chain/venue/regime matrix]
EPISTEMIC ASSESSMENT
        ↓  [Agent 05 ONLY — quant stops here]
```

### 4.2 Transition contracts (summary)

| Transition | Input contract | Output contract | Authority boundary |
| --- | --- | --- | --- |
| Observation → Feature | Raw rows + `as_of` + schema version | Feature vector rows with `availability_ts` | Agent 07 semantics; Agent 12 validates cutoff use |
| Feature → Signal | Feature vector + rule/threshold spec | Signal event with validity window | Agent 08/09 own market/on-chain signal defs; Agent 12 owns eval validity |
| Signal → Prediction | Signal + model spec | Scored prediction + uncertainty | Agent 13 for ML training; Agent 12 for eval protocol |
| Prediction → Simulated execution | Prediction + sim assumptions | Fill log + equity path | Agent 12; not Agent 11 risk decision |
| Outcome → Performance | Closed labels + sim log | Metric bundle + CI | Agent 12 produces; Agent 05 classifies epistemic status |
| Performance → Knowledge | QuantFinding + MethodologyAssessment | **None automatic** | Agent 05 promotion gate only |

### 4.3 Quant ↔ Epistemic handoff (Agent 05)

```text
Agent-12 produces:
  "Observed out-of-sample precision = X (95% CI [a,b]), n=N, under protocol P,
   with leakage attestation L, research lineage R."

Agent-05 determines:
  "What epistemic status can legitimately be assigned to that result?"
  (OBSERVATION / EVIDENCE / HYPOTHESIS SUPPORT — never auto-Knowledge)
```

**Non-collapse rule:** A profitable backtest is **at most** a bounded simulation result until independently replicated, methodology-approved, and epistemically promoted through TCB gates.

---

## 5. Backtesting Architecture

### 5.1 Design layers

| Layer | Purpose | AHOS current | Target |
| --- | --- | --- | --- |
| **L0 — Vector screen** | Fast hypothesis pruning | `vector_engine.py` | Keep; label as `SCREENING_ONLY` |
| **L1 — Causal bar engine** | Regime/strategy validation | `ahos_backtest.py`, `lab_engine.py` | Primary for majors |
| **L2 — Event microstructure** | DEX token fills | `event_backtest.py` | Required for token opportunity sim |
| **L3 — Opportunity event study** | Detection metrics, not portfolio | `baseline_stats.py` + search cells | **Primary for AHOS product** |
| **L4 — Paper path** | Forward sim without live exec | paper trading tests | Unify ledgers |

### 5.2 Historical replay requirements

`[PROPOSED]` Unified replay bus supporting:

| Data type | Timestamp semantics | AHOS status |
| --- | --- | --- |
| Candles (1h/5m) | bar close vs availability | `[IMPLEMENTED]` majors |
| Trades / ticks | exchange event time + ingest delay | `[PARTIAL]` |
| Order book snapshots | snapshot time + depth | H8 DATA-BLOCKED |
| Liquidity states | pool reserves at block/time | `[PARTIAL]` event_backtest |
| Token lifecycle | pair_created, delist, rug | `[PARTIAL]` — no PIT universe |
| On-chain events | block time + finality lag | `[PROPOSED]` Agent 09 |
| Security observations | report time vs effective time | `[PROPOSED]` Agent 10 |
| Social/news | post time vs ingest; edited/deleted | `[DEFERRED]` registry-only |

### 5.3 Event-driven simulation

**Event ordering rules** `[PROPOSED]`:

```text
PRIMARY_SORT:   effective_decision_time (UTC normalized)
SECONDARY_SORT: causal_priority (market before fill, fill before PnL mark)
TIE_BREAK:      source_id lexicographic (deterministic, documented)
```

**Event anomaly handling:**

| Anomaly | Behavior |
| --- | --- |
| Missing events | Gap register entry; feature NULL; sim may skip or conservative fill |
| Delayed events | Apply `availability_ts`; never retroactive signal |
| Duplicated events | Dedup by `(source, id, type)`; log conflict |
| Stale events | Expire per validity window |
| Out-of-order ingest | Reorder by `effective_time`; flag `INGEST_REORDER` |
| Simultaneous events | Deterministic tie-break; document sensitivity |

### 5.4 Execution simulation minimum model

Must model (where applicable):

- spread, slippage, market impact, latency, partial fills, failed fills
- liquidity exhaustion, fees, gas/network costs, MEV assumptions (bounded scenarios)
- position limits, exit constraints

**Never assume:** `SIGNAL → INSTANT FILL`

AHOS implements subsets: `ahos_backtest.py` (fixed fee+slippage), `event_backtest.py` (AMM + latency). `[PROPOSED]` explicit assumption registry per backtest run documenting what was **not** modeled.

---

## 6. Point-in-Time Architecture

### 6.1 InformationCutoff(T)

`[PROPOSED]` canonical function:

```text
InformationCutoff(T) → {
  decision_time: T,
  allowed_observation_end: T - ingestion_lag_policy,
  allowed_chain_block: finality_adjusted(T),
  allowed_label_end: T (labels strictly FUTURE of T),
  provider_trust_window: per-provider publication delay table,
  feature_compute_as_of: T,
  security_effective_cutoff: min(report_time, T),
  universe_membership_as_of: snapshot_id(U, T)
}
```

Every object consumed at decision time must prove:

```text
AVAILABLE_AT <= DECISION_TIME
```

AHOS partial implementation: feature store L1/L3 (`retrieved_ts <= as_of`, `availability_ts <= as_of_ts`); calibration no-peeking (`resolved_ts > scored_ts`).

### 6.2 Delay classes

| Class | Examples | Handling |
| --- | --- | --- |
| Provider publication delay | API backfill, revised candles | Prefer `retrieved_ts`; flag `BACKFILL_DETECTED` |
| Ingestion delay | Collector lag | `availability_ts` on features |
| Chain finality | reorgs | `as_of_block` + confirmation depth (Agent 09) |
| Indexer delay | holder snapshots | block/time pin + staleness flag |
| Social post edits | deleted tweets | point-in-time archive or invalidate |
| Retrospective labels | rug tagged post-hoc | **Forbidden** as decision-time inputs |
| DB corrections | updated metadata | versioned snapshots; no silent rewrite |

### 6.3 Proof artifacts

`[PROPOSED]` Each `QuantExperiment` carries `pit_attestation`:

```text
pit_attestation: {
  cutoff_policy_id,
  cutoff_policy_hash,
  universe_snapshot_id,
  feature_set_version,
  label_horizon_definition,
  leakage_scan_result: PASS | FAIL | UNKNOWN,
  attested_by: agent_id,
  attested_at: timestamp
}
```

---

## 7. Dataset Architecture

### 7.1 Reproducible dataset identity

`[PROPOSED]` `DatasetIdentity`:

```text
dataset_id              # stable logical name
dataset_version         # semver or content hash
source_version          # provider export version
schema_version
feature_version         # fs_v0.1 etc.
label_version
universe_definition     # hash of inclusion rules
cutoff_policy           # InformationCutoff policy id
sampling_policy
filter_policy
timezone                # UTC enforced
missing_data_policy
content_address         # sha256 manifest (AHOS: MANIFEST.json pattern)
```

AHOS `[IMPLEMENTED]`: `research/data/MANIFEST.json`, Postgres `dataset_version`, feature set versions in SQLite.

**Gap:** No immutable point-in-time **token universe snapshots** for discovery research.

### 7.2 Immutability policy

| Tier | Policy |
| --- | --- |
| Raw provider dumps | Content-addressed, append-only |
| Derived feature tables | Versioned recompute; old versions retained |
| Experiment inputs | Pin manifest hash at experiment start |
| Labels | Separate table; no import from features (L2 enforced) |

---

## 8. Feature Registry

### 8.1 Formal record

`[PROPOSED]` extends AHOS `feature_definitions` + Agent 07 `Feature`:

```text
feature_id
name
definition
formula
formula_version
formula_hash          # sha256(canonical formula text)
source_dependencies
time_window
lookback
availability_lag
normalization
missing_data_policy
units
range
owner                 # Agent 07 / 08 / 09 / 12 joint
status                # DEFINED → IMPL-TESTED → BACKFILLED → RESEARCH → PROMOTED
leakage_risk_class
pit_required: bool
```

**Invariants:**

```text
FEATURE_VERSION ≠ MODEL_VERSION
FEATURE DEFINITION MUST BE IMMUTABLE FOR A GIVEN EXPERIMENT
```

AHOS `[IMPLEMENTED]`: registry in SQLite + `D_FEATURE_STORE_SCHEMA.md`; formula hashing `[PROPOSED]` for org bridge.

### 8.2 Registry ownership (unresolved)

| Option | Pros | Cons |
| --- | --- | --- |
| AHOS git + SQLite | Already implemented | Org TCB cannot attest independently |
| Org TCB sidecar | Epistemic audit | Sync burden |
| Joint canonical in docs + hash pins | Simple | Not machine-enforced |

**Status:** `[HUMAN_DECISION_REQUIRED]` — see §25.

---

## 9. Signal Registry

### 9.1 Signal taxonomy

| Class | Definition | Example |
| --- | --- | --- |
| **OBSERVATION** | Raw or normalized measurement | liquidity_usd_t |
| **DERIVED_METRIC** | Deterministic transform | liquidity_growth_1h |
| **SIGNAL** | Rule-fired indicator with threshold | buy_sell_imbalance > 0.15 |
| **ALERT** | Actionable notification candidate | "volume shock detected" |
| **PREDICTION** | Forward claim with horizon | "+50% in 24h probability" |

### 9.2 Signal record

```text
signal_id, signal_version, class, definition, threshold,
feature_dependencies[], timestamp, provenance,
confidence/uncertainty, validity_window, known_limitations,
decision_eligible: false  # ALWAYS false at registry level
```

**Rule:** A signal must never silently become a decision. Decision-simulation is a separate explicit stage with cost matrix and authority gate.

---

## 10. Model Registry

### 10.1 Scope

Supports:

- deterministic rules (AHOS primary today)
- statistical models
- ML models (Agent 13 lifecycle)
- ensembles
- LLM-derived hypotheses (non-evidence until validated)
- regime-specific models

### 10.2 Model record

```text
model_id, model_version,
training_data, training_cutoff,
features[], hyperparameters, random_seed,
code_version, environment,
objective, validation_protocol,
known_failures[], calibration_ref,
deployment_status: IDEA | RESEARCH | EXPERIMENTAL | REPLICATED | ...
```

AHOS today: strategy candidates H1–H12 as **hypothesis generators**, not trained models — `[IMPLEMENTED]` as rule registry, not ML registry.

**No model validated merely by training performance.**

---

## 11. Validation Architecture

### 11.1 Split strategies

| Method | When valid | When invalid (crypto) |
| --- | --- | --- |
| Random K-fold | IID data (rare) | Time-series, regime-dependent |
| Chronological split | Default for markets | Needs embargo if labels overlap |
| Walk-forward | `[IMPLEMENTED]` AHOS | Requires sufficient windows |
| Purged K-fold + embargo | `[IMPLEMENTED]` validation_engine | Required for overlapping labels |
| Rolling / expanding windows | Regime drift detection | Window size is a researcher DoF |
| Grouped splits (by token) | Cross-asset generalization | Prevents token leakage |
| Cross-chain / cross-venue | Robustness | `[PROPOSED]` |
| Regime-conditioned | H10/H12 attempts | Regime definition is itself a hypothesis |

### 11.2 Dependencies invalidating random K-fold

```text
TIME DEPENDENCE — mandatory embargo
CROSS-ASSET DEPENDENCE — group by asset
CROSS-VENUE DEPENDENCE — group by venue
CROSS-CHAIN DEPENDENCE — group by chain
REGIME DEPENDENCE — regime labels are not free metadata
```

### 11.3 AHOS strategy lab gates (reference)

Fixed gates in `run_lab.py`: OOS PF>1.3, expectancy>0, OOS DD<15%, MC>70% positive, WFA ≥60% profitable windows, stress 2× costs PF>1.1, ≥30 OOS trades, cross-asset stability. **These are strategy-promotion gates, not opportunity-detection gates** — separate metric suites required (§15).

---

## 12. Leakage Taxonomy

### 12.1 Formal taxonomy

| ID | Leakage class | Crypto example | Detection | Severity |
| --- | --- | --- | --- | --- |
| LK-01 | Look-ahead price | future close in signal | prefix-causality test | CRITICAL |
| LK-02 | Survivorship | winners-only token set | PIT universe diff | CRITICAL |
| LK-03 | Selection bias | filter on future outcome | pre-register filters | HIGH |
| LK-04 | Universe leakage | train/test token overlap improper | grouped split audit | HIGH |
| LK-05 | Delisting leakage | exclude dead tokens using end-state | PIT membership | CRITICAL |
| LK-06 | Rug hindsight | label from post-rug knowledge | effective_time audit | CRITICAL |
| LK-07 | Post-launch labeling | "scam" tag applied retroactively | security cutoff | CRITICAL |
| LK-08 | Future security info | audit published after T used at T | Agent 10 cutoff | HIGH |
| LK-09 | Future liquidity | depth after pump used at entry | availability_ts | HIGH |
| LK-10 | Future social engagement | viral post counted before posted | ingest vs post time | MED |
| LK-11 | Whale behavior leakage | labeled whale wallet post-hoc | PIT holder graph | HIGH |
| LK-12 | Reorg artifacts | pre-reorg state | finality policy | MED |
| LK-13 | Timestamp inconsistency | mixed UTC/local | normalization audit | MED |
| LK-14 | Provider backfill | revised historical candles | retrieved_ts policy | HIGH |
| LK-15 | Missing universe | inactive tokens vanish | gap register | HIGH |
| LK-16 | Fake historical liquidity | interpolated depth | NULL not zero | HIGH |
| LK-17 | Impossible fills | fill beyond pool depth | event_backtest guards | HIGH |
| LK-18 | Regime leakage | classify regime using full sample | causal regime labels | HIGH |
| LK-19 | Test-set tuning | tweak after OOS view | lineage + locked tests | CRITICAL |
| LK-20 | Label horizon overlap | train labels bleed into test | purged CV | HIGH |

AHOS `[IMPLEMENTED]` defenses: LK-01 (lab tests), LK-01/03 partial (L1–L4), LK-19 partial (hypothesis re-id rule), calibration no-peeking.

**Major gaps:** LK-02, LK-05, LK-06, LK-07, LK-11 — token discovery research.

---

## 13. Statistical Validity

### 13.1 Required practices

- Confidence intervals (Wilson CI in `baseline_stats.py` — `[IMPLEMENTED]`)
- Bootstrap / block bootstrap for dependent series `[PROPOSED]`
- Multiple testing correction when scanning search cells `[PARTIAL]` — pre-registration helps, not sufficient
- Effect size + practical significance alongside p-values
- Power / sample adequacy (`MIN_N=200`, `MIN_POSITIVES=20` — `[IMPLEMENTED]`)
- Report `INSUFFICIENT_DATA` as first-class outcome

### 13.2 Researcher degrees of freedom — winner suspicion

> How many strategies must fail before the surviving winner becomes suspicious?

`[PROPOSED]` Report **effective trial count** `M_eff` from `ResearchLineage`:

```text
M_eff ≈ (# hypotheses) × (# parameter grids) × (# universes) × (# metrics cherry-picked)
```

If `M_eff > 20` and one winner survives uncorrected, apply:

- Bonferroni / Benjamini-Hochberg on primary metric
- Holdout not used in any prior decision
- Require replication on fresh time window

AHOS partial defense: hypothesis cards before run, frozen params after first OOS, search-space pre-registration, batch-2 raised bar (OOS PF>1.5).

---

## 14. Calibration

### 14.1 Architecture layers

```text
MODEL SCORE → MODEL PROBABILITY → CALIBRATED PROBABILITY → EMPIRICAL FREQUENCY
```

AHOS `[IMPLEMENTED]` harness measures empirical frequency by score band; **does not tune weights**.

### 14.2 Methods

| Method | Use |
| --- | --- |
| Reliability diagrams | Primary visualization |
| Brier score / ECE | `[IMPLEMENTED]` in extended tests |
| Isotonic / Platt | `[PROPOSED]` — Agent 13 + governance approval |
| Regime-specific calibration | Segment by RV regime, chain, liquidity class |
| Temporal recalibration | Scheduled; triggers drift alarm |

### 14.3 Coordination with Calibration role

Slice 1 `agent.calibration` (inspect-only) vs AHOS runtime harness vs future Agent dedicated to calibration governance — **three surfaces**. Agent-12 owns **measurement protocol**; weight changes require human-reviewed `improvement_proposal_v1` flow in AHOS.

---

## 15. Performance Metrics

### 15.1 By research objective

| Objective | Primary metrics | Secondary |
| --- | --- | --- |
| **Opportunity detection** | precision, recall, PR-AUC, precision@K, time-to-detection, false alarm rate | calibration, coverage |
| **Portfolio strategy** | CAGR, Sharpe, Sortino, Calmar, max DD, turnover | MC stress, WFA stability |
| **Liquidity survival** | sellability rate, time-to-exit, slippage at size | pool depth at entry/exit |
| **Security asymmetry** | conditional precision on veto-clear subset | false safe rate |
| **Cost-sensitive alert** | expected cost under explicit matrix | missed opportunity cost |

### 15.2 Metric suites (AHOS `QuantMetricsEngine`)

`[IMPLEMENTED]`: Sharpe, Sortino, Calmar, Omega, VaR/CVaR, max DD, Kelly, tear-sheet.

**Do not reduce opportunity detection to profit-only.**

### 15.3 Imbalanced crypto opportunity datasets

Prefer **PR-AUC**, **precision@K**, **calibrated probability**, **base-rate-adjusted lift** over raw accuracy or ROC-AUC alone.

---

## 16. Robustness

### 16.1 Robustness matrix

Every candidate insight tested against:

```text
TIME | ASSET | CHAIN | VENUE | REGIME | LIQUIDITY | PARAMETER | DATA SOURCE | EXEC ASSUMPTION
```

AHOS `[PARTIAL]`: cross-asset in strategy lab gates; H6/H10 show BTC-only effects correctly rejected.

### 16.2 Ablation

`[PROPOSED]` Required before promotion:

- feature group ablation
- data source ablation
- signal component ablation
- security / on-chain / market input ablation

Ask: *Does this component contribute, or is it decorative complexity?*

### 16.3 Baseline models

Every sophisticated model requires:

- naive baseline (base rate)
- random baseline
- simple rule baseline
- buy-and-hold where applicable

AHOS `[PARTIAL]`: implicit base rate in `baseline_stats.py`; not formalized as Model Registry entries.

---

## 17. Stress Testing

### 17.1 Scenarios

| Scenario | Variable stressed |
| --- | --- |
| Price gap | gap at open vs stop |
| Liquidity collapse | pool depth → 0 |
| Spread expansion | 2×–10× spread |
| Latency increase | 500ms → 5s |
| Missing providers | single-source failure |
| Stale data | aged `availability_ts` |
| Chain outage | no new blocks |
| Provider disagreement | conflicting prices |
| Sudden volatility | RV shock |
| Rug event | instant -90% |
| Execution failure | fill reject rate |
| Security downgrade | veto flips post-entry |

AHOS `[IMPLEMENTED]`: stress 2× costs in strategy lab. `[PROPOSED]` expanded scenario registry with explicit non-guarantee labeling.

---

## 18. Research Lineage

### 18.1 ResearchLineage object

```text
ResearchLineage {
  lineage_id,
  root_hypothesis_id,
  experiment_ids[],
  variants_attempted: int,
  datasets_used[],
  models_used[],
  parameter_search_budget,
  model_search_budget,
  test_sets_touched[],      # track reuse
  selection_events[],       # when a result influenced next step
  final_selected_result_id,
  multiplicity_adjustment_method
}
```

**Purpose:** Answer: *How many attempts were tried before this result was selected?*

AHOS `[PARTIAL]`: `registry.json`, experiment logs, hypothesis cards — not unified lineage object.

### 18.2 Experiment tracking

`[PROPOSED]`:

```text
Experiment ID, Hypothesis ID, Research Lineage,
Parameter Search Budget, Model Search Budget, Test Reuse Tracking
```

---

## 19. Quantitative Failure Memory

### 19.1 Failure taxonomy

| Class | Example in AHOS evidence |
| --- | --- |
| DATA_LEAKAGE | Prevented by L1–L4 tests |
| OVERFITTING | H6 train PF 0.35 vs OOS 3.13 BTC |
| REGIME_FAILURE | H1 trend decay 2025+ |
| LIQUIDITY_FAILURE | H9 stress PF 0.93 at 2× costs |
| EXECUTION_FAILURE | `[PROPOSED]` formal tracking |
| CALIBRATION_FAILURE | 0 joined_pairs — not yet measurable |
| LABEL_FAILURE | `[PROPOSED]` |
| SELECTION_BIAS | `[RISK]` without PIT universe |
| SURVIVORSHIP_BIAS | `[DOCUMENTED]` gap |
| TIMESTAMP_FAILURE | `[PROPOSED]` golden tests |
| PROVIDER_FAILURE | funding coverage ends 2026-07-31 |
| MODEL_FAILURE | H11 zero-signal falsification |
| ASSUMPTION_FAILURE | event_backtest $10k pool fallback |
| REPLICATION_FAILURE | `[PROPOSED]` |
| GENERALIZATION_FAILURE | H10 BTC-only after refinement |

**Negative results are first-class artifacts.** AHOS `[IMPLEMENTED]`: REJECTED registry entries, findings report. `[PROPOSED]`: org TCB `FailureRecord` linked to Agent 05/06 memory.

---

## 20. Quantitative Finding Contract

`[PROPOSED]` `QuantitativeFinding` — **design only, not implemented**:

```text
QuantitativeFinding {
  finding_id,
  finding_type: OBSERVED_RESULT | STATISTICAL_INFERENCE | SIMULATION_OUTCOME,
  statement,                          # precise, bounded
  metric_name, metric_value,
  uncertainty: { ci_lower, ci_upper, method },
  methodology_ref,
  experiment_id,
  dataset_identity_ref,
  feature_versions[], model_version,
  replication_status: NOT_ATTEMPTED | REPLICATED | FAILED_REPLICATION,
  known_limitations[],
  epistemic_status: UNASSIGNED,       # Agent 05 fills
  promotion_eligible: false           # default
}
```

---

## 21. QuantExperiment Contract

`[PROPOSED]` extends Slice 2B `ExperimentPlan` + Agent 06 methodology:

```text
QuantExperiment {
  experiment_id,
  research_question,
  hypothesis_id,
  preregistration_hash,              # before data peek
  study_type: BACKTEST | EVENT_STUDY | CALIBRATION | ABLATION | STRESS,
  dataset_identity,
  information_cutoff_policy,
  feature_registry_snapshot,
  model_registry_snapshot,
  parameter_budget,
  validation_plan: { splits, embargo, metrics_primary, metrics_secondary },
  stopping_rules,
  cost_matrix_ref,                   # explicit
  result: QuantitativeFinding | null,
  failure_analysis,
  replication_protocol,
  reviewer_status: PENDING | PASS | FAIL,
  lineage_id
}
```

**Coordination:** Agent 06 owns methodology defensibility review; Agent 12 owns what the experiment shows.

---

## 22. QuantConflict

`[PROPOSED]` explicit conflict object — **do not average contradictory evidence**:

```text
QuantConflict {
  conflict_id,
  subject,                           # token, strategy, feature, regime
  side_a: { source, finding_id, metric, direction },
  side_b: { source, finding_id, metric, direction },
  conflict_type: MODEL_DISAGREEMENT | BACKTEST_DISAGREEMENT | DATA_PROVIDER_DISAGREEMENT | REGIME_DISAGREEMENT,
  resolution_status: OPEN | EXPLAINED | UNRESOLVED,
  proposed_resolution,
  owner_agent
}
```

Examples from AHOS forensics:

- BACKTEST_A (83d LBank) vs BACKTEST_B (3.6y BinanceVision) — different data, not contradictory engines
- H6 OOS BTC positive vs ETH/SOL negative — **REGIME_DISAGREEMENT / CROSS_ASSET**
- Vector engine vs lab engine causality — **METHODOLOGY_DISAGREEMENT**

---

## 23. Cross-Agent Boundaries

| Agent | Agent-12 receives | Agent-12 produces | Agent-12 must NOT |
| --- | --- | --- | --- |
| **05 Epistemic** | promotion rules, ladder | QuantitativeFinding for review | self-promote to Knowledge |
| **06 Methodology** | study design requirements, leakage checklist | experiment results, lineage | override methodology authority |
| **07 Data** | DataArtifact, quality, lineage, NOT_FIT | data sufficiency requests | bypass quarantine |
| **08 Market** | MarketFeatureDefinition, regimes | backtest validity, eval metrics | redefine CMI features |
| **09 On-Chain** | PIT on-chain features | leakage attestation on use | own decoder semantics |
| **10 Security** | SecurityAssessment context | label validity warnings | emit security verdicts |
| **11 Risk** | scenarios, constraints | drawdown/tail/stress distributions | convert to risk decisions |
| **13 AI/ML** | trained model artifacts | validation protocol, holdout rules | own training lifecycle |

**Interface fields (all cross-agent payloads):** inputs, outputs, timestamps, provenance, versioning, uncertainty, conflicts, failure behavior, authority boundary.

---

## 24. Contradiction Register

| ID | Source | Conflict | Why it matters | Blocker? | Proposed resolution | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CR-01 | Agent 08 CMI-C02 vs Slice 1 | `agent.scoring-science` vs Agents 08+12 feature/model ownership | Duplicate scoring paths | HIGH-RISK | Plane map: CMI defines features, 12 validates use, 13 trains ML | Human + Agent 04 | UNRESOLVED |
| CR-02 | Agent 09 OCI-C10 vs 06/07/12 | Feature cutoff ownership | ML leakage if wrong owner | HIGH-RISK | Joint cutoff policy in InformationCutoff(T) | Agent 12+09+07 | UNRESOLVED |
| CR-03 | Agent 09 OCI-C04 vs 08 | Pool feature duplication | Conflicting quant inputs | IMPORTANT | Canonical pool feature registry | Agent 08+09 | UNRESOLVED |
| CR-04 | Agent 11 RI-C11 vs 12 | VaR/backtest metrics as "risk truth" | Authority collapse | HIGH-RISK | Quant produces; Risk interprets | Agent 11+12 | DOCUMENTED |
| CR-05 | Agent 11 RI-C09 vs Slice 1 | `agent.paper-trading` vs risk limits | Paper path without risk frame | IMPORTANT | Explicit paper sim ≠ risk approval | Agent 11+12 | UNRESOLVED |
| CR-06 | Agent 07 HD-12 vs 12 | Feature registry location TCB vs git | Reproducibility attestation | IMPORTANT | Hash-pinned dual write | Human | UNRESOLVED |
| CR-07 | AHOS dual data horizons | 83d LBank vs 3.6y BinanceVision | Incomparable backtest claims | IMPORTANT | Unified dataset identity per experiment | AHOS eng | UNRESOLVED |
| CR-08 | AHOS vector vs lab engine | Different causality strictness | False confidence from vector screen | HIGH-RISK | Label vector as SCREENING_ONLY | Agent 12 | PROPOSED |
| CR-09 | AHOS calibration vs org role | Runtime harness vs org inspect role | Governance gap | IMPORTANT | Bridge QuantFinding to TCB | Agent 12+05 | UNRESOLVED |
| CR-10 | Agent 06 vs 05 | Methodology vs epistemic thin boundary | Strong methods blocked epistemically | NON-BLOCKING | MethodologyAssessment handoff schema | Agent 06+05 | UNRESOLVED |
| CR-11 | Agent 10 vs 12 | Security calibration mention vs quant calibration | Term collision | NON-BLOCKING | Namespace: security_score_calibration vs opportunity_calibration | Agent 10+12 | PROPOSED |
| CR-12 | Dual-19 | Plane A vs Plane D role IDs | Authorization mapping | HIGH-RISK | Agent 04 governance mission | Agent 04 | UNRESOLVED |

---

## 25. Human Decision Register

| ID | Decision | Why agent cannot decide |
| --- | --- | --- |
| HD-Q01 | Feature registry canonical location (TCB vs AHOS git vs dual hash) | Org governance + operational ownership |
| HD-Q02 | Whether locked/hidden evaluation sets are required at launch vs Phase 3 | Product risk appetite |
| HD-Q03 | Minimum calibration joined_pairs threshold for "score trustworthy" user messaging | Product/legal framing |
| HD-Q04 | Promotion of any REJECTED-but-interesting lead (H10 BTC) to new research priority | Resource allocation |
| HD-Q05 | Unification of paper trading ledger surfaces | Cross-system product decision |
| HD-Q06 | ML model introduction timeline (Agent 13) vs rule-only launch | Strategic scope |

**Not inflated:** Technical leakage rules, metric definitions, and pipeline stage contracts are Agent-12 delegable design work.

---

## 26. Minimum Viable Quant Engine

**Smallest defensible core** — not the full architecture.

| Component | Class | Why |
| --- | --- | --- |
| Point-in-time feature compute + L1–L4 | **MUST_HAVE_FOR_FIRST_RUN** | Already in AHOS; core honesty |
| Pre-registered opportunity event study (`baseline_stats` + search cells) | **MUST_HAVE_FOR_FIRST_RUN** | Matches product (detection ≠ portfolio) |
| Score ledger + calibration harness (read-only) | **MUST_HAVE_FOR_FIRST_RUN** | Converts scores to measurable claims |
| Negative result registry | **MUST_HAVE_FOR_FIRST_RUN** | Prevents repeated failure |
| Causal bar backtest for majors | **SHOULD_HAVE** | Exists; needed for strategy research track |
| QuantExperiment / Lineage schema in org TCB | **SHOULD_HAVE** | Bridge AHOS ↔ org epistemics |
| Strategy lab full gate battery | **SHOULD_HAVE** | Exists; not required for opportunity-only launch |
| Event-driven DEX backtester | **LATER** | Partial; needed for token sim depth |
| Vector screening engine | **SHOULD_HAVE** | Keep labeled SCREENING_ONLY |
| ML model registry | **LATER** | Agent 13 |
| Survivorship PIT universe | **MUST_HAVE_FOR_FIRST_RUN** (token claims) | Gap — blocker for broad token backtest marketing |
| Locked hidden test sets | **LATER** | Phase 3 maturity |
| Full regime robustness matrix | **LATER** | Phase 3 |
| Monte Carlo scenario library | **RESEARCH_ONLY** | Exists for strategies |
| Institutional HFT microstructure | **NOT_NEEDED** | Wrong product tier |

---

## 27. Launch Blockers

### Launch blockers (quant-relevant)

| # | Blocker | Evidence |
| --- | --- | --- |
| 1 | **Calibration unmeasured on live local pairs** | M-GAP-008; 0 joined_pairs |
| 2 | **No PIT token universe / survivorship control** | OSS plan only; LK-02/05 open |
| 3 | **Org↔AHOS quant epistemic bridge missing** | No QuantFinding in TCB |
| 4 | **Dual paper/backtest ledger reconciliation** | Phase 0 audit note |

**Count: 4**

### Future excellence (NOT launch blockers)

- Full event-driven token microstructure parity with live execution
- ML model registry + Agent 13 pipeline
- Hidden evaluation sets / researcher DoF budget enforcement in code
- Cross-chain robustness automation
- Institutional-grade order book backtests (H8 blocked on data anyway)
- CI green on GitHub (M-GAP-004)

---

## 28. Backlog / Deferred Work

| # | Item | Priority |
| --- | --- | --- |
| 1 | InformationCutoff(T) policy document + golden tests | HIGH |
| 2 | Unified DatasetIdentity across AHOS surfaces | HIGH |
| 3 | ResearchLineage object + test reuse tracking | HIGH |
| 4 | QuantConflict handler | MED |
| 5 | Formal SCREENING_ONLY wrapper for vector_engine | MED |
| 6 | Expanded stress scenario registry | MED |
| 7 | Block bootstrap for dependent returns | MED |
| 8 | Ablation protocol template | MED |
| 9 | Cross-agent feature formula_hash standard | MED |
| 10 | Replication protocol with tolerance bands | MED |
| 11 | Opportunity-detection metric dashboard (non-PnL) | HIGH |
| 12 | Joint Agent 12+09 on-chain PIT feature spec | HIGH |
| 13 | Golden datasets spec (§47 mission) | MED |
| 14 | Cost matrix registry per research context | MED |
| 15 | LLM hypothesis quarantine workflow | LOW |

**Count: 15**

---

## 29. Build → Integrate → Verify Matrix

| Component | Build | Integrate | Independent Verify | Acceptance Gate | Blocker? |
| --- | --- | --- | --- | --- | --- |
| PIT feature store (AHOS) | DONE | In discovery pipeline | Agent 16 replay fixtures | L1–L4 tests pass | No |
| Opportunity event study | DONE | Search cells + baseline_stats | Agent 16 cell replay | Pre-registered eval only | No |
| Calibration harness | DONE | Score ledger + outcomes | Agent 16 join audit | joined_pairs ≥ MIN_N | **Yes** (measurement) |
| Strategy lab gates | DONE | run_lab pipeline | Agent 16 battery replay | Documented REJECT/ACCEPT | No |
| Causal backtest engine | DONE | Strategy research | Existing pytest + Agent 16 | Determinism + no lookahead | No |
| QuantExperiment schema | NOT STARTED | TCB + AHOS experiment logs | Agent 16 schema validation | Round-trip experiment | **Yes** (bridge) |
| ResearchLineage | NOT STARTED | Registry + logs | Agent 19 adversarial DoF audit | M_eff reported | No (launch) |
| PIT token universe | NOT STARTED | Discovery DB | Agent 16 survivorship test | No LK-02 on fixture | **Yes** |
| InformationCutoff policy | NOT STARTED | All research paths | Golden timestamp tests | 100% pit_attestation | Partial |
| Org quant role runtime | NOT STARTED | Slice 1 authorize inspect | Agent 16 deny tests | No prod scoring | No |
| Vector engine labeling | NOT STARTED | vector_engine wrapper | Agent 19 causality compare | Cannot promote without L1 | No |
| Paper ledger unification | NOT STARTED | Lane A + TS gateway | Agent 16 ledger diff | Single source of truth | **Yes** |
| Hidden holdout sets | NOT STARTED | Phase 3 | Agent 19 gaming audit | Zero test reuse violations | No (launch) |

---

## 30. Independent Verification Plan

**Agent-12 builds ≠ independent verification.**

| Verification | Verifier | Method |
| --- | --- | --- |
| Leakage law enforcement | Agent 16 | Replay golden fixtures with injected future data |
| Backtest determinism | Agent 16 | Re-run `run_validation.py` / experiment logs; hash compare |
| Calibration no-peeking | Agent 16 | Adversarial join order tests |
| Search cell pre-registration | Agent 19 | Git timestamp vs first eval timestamp |
| Researcher DoF / p-hacking | Agent 19 | Lineage audit; count effective trials |
| Survivorship bias | Agent 16 | PIT universe fixture with delisted tokens |
| Vector vs causal divergence | Agent 19 | Same hypothesis both engines; document delta |
| Cross-agent boundary violations | Agent 19 | Attempt quant→decision shortcut; must fail closed |
| Metric calculation correctness | Agent 16 | Golden tear-sheet vectors |

**Current status:** `[NOT PERFORMED]` — no Agent 16/19 mission evidence in repository.

---

## 31. Delivery Roadmap

```text
PHASE 0 — DOCUMENTED CONTRACTS          ← THIS DOCUMENT + cross-agent IDs
PHASE 1 — MINIMUM EMPIRICAL ENGINE      ← PIT features + event study + calibration accrual
PHASE 2 — REPRODUCIBLE BACKTESTING      ← DatasetIdentity + QuantExperiment + lineage
PHASE 3 — ROBUSTNESS / CALIBRATION      ← Regime matrix + multiplicity + hidden holdouts
PHASE 4 — PAPER-TRADING VALIDATION      ← Unified ledger + forward sim vs backtest
PHASE 5 — PRODUCTION CANDIDATE          ← Governance promotion + Agent 05 acceptance
```

**Parallelizable:**

- Phase 0 contracts ∥ AHOS calibration accrual (time-dependent)
- Phase 2 dataset identity ∥ Phase 3 golden tests design
- Agent 12+09 on-chain PIT spec ∥ opportunity metrics dashboard

**First useful product release does NOT require Phase 5** — requires Phase 0–1 with honest INSUFFICIENT_DATA states.

---

## 32. Anti-Loop / Stopping Condition

### WHAT MUST BE DONE NOW

1. Accept this architecture as Phase 0 contract baseline
2. Accrue calibration joined_pairs under local evidence source (time-dependent)
3. Define PIT token universe snapshot policy (blocks token backtest claims)
4. Design QuantExperiment bridge schema (org TCB ↔ AHOS logs)

### WHAT CAN WAIT

- ML model registry (Agent 13)
- Hidden evaluation sets
- Full microstructure parity
- Cross-chain robustness automation

### WHAT SHOULD BE BACKLOGGED

- See §28 (15 items)

### TRUE BLOCKERS

- 4 launch blockers in §27

### NOT BLOCKERS

- Zero accepted strategies (correct scientific outcome)
- No ML pipeline (by design)
- No GitHub CI (M-GAP-004)
- Baseline not propagated org-wide
- Dual-19 unresolved

**Stop condition met:** forensics complete, state classified, architecture specified, boundaries defined, contradictions recorded, MVP/launch separated, BIV matrix defined, IV requirements identified, human decisions listed.

---

## 33. Final Classification

| Area | Status |
| --- | --- |
| Agent-12 architecture document | `[DOCUMENTED]` |
| AHOS causal backtest | `[IMPLEMENTED]` `[TESTED]` |
| AHOS strategy lab | `[IMPLEMENTED]` `[TESTED]` — 0 ACCEPTED |
| AHOS feature store PIT | `[IMPLEMENTED]` `[TESTED]` — bounded scope |
| AHOS calibration harness | `[IMPLEMENTED]` — measurement `[PARTIAL]` |
| AHOS vector backtest | `[IMPLEMENTED]` — causality `[WEAKER]` |
| AHOS event backtest | `[PARTIALLY_IMPLEMENTED]` |
| AHOS survivorship / PIT universe | `[PLANNED]` / `[DOCUMENTED]` |
| Org quant runtime | `[NONE]` |
| Org QuantExperiment / QuantFinding | `[PROPOSED]` |
| Cross-agent quant integration | `[PROPOSED]` |
| Independent verification | `[NOT PERFORMED]` |
| Agent 05–11 peer inputs | `[DOCUMENTED]` — used as inputs not truth |
| Operating baseline adoption org-wide | `[NOT PROPAGATED]` |

---

## Appendix A — Opportunity Detection vs Portfolio Optimization

| Dimension | Opportunity detection | Portfolio optimization |
| --- | --- | --- |
| Unit of eval | Event / alert / token-time | Portfolio path |
| Primary metrics | precision@K, time-to-detection, lift | Sharpe, DD, turnover |
| Horizon | Fixed event horizon (+50% @ 24h) | Continuous |
| Capital allocation | Often out of scope early | Central |
| Failure mode | false alarm storm | drawdown breach |
| AHOS fit | **Primary** — discovery + scoring | Secondary — strategy lab track |

---

## Appendix B — Label Design

| Label type | Decision-time available? | Use |
| --- | --- | --- |
| future return @ H | **No** — outcome only | Supervised eval |
| MFE / MAE | **No** | Exit research |
| time-to-event | **No** | Survival analysis |
| liquidity survival | **No** | Sellability studies |
| rug event | **No** unless PIT security feed | Classification |
| opportunity persistence | **No** | Regime eval |

**Rule:** `LABEL ≠ KNOWLEDGE` at decision time.

---

## Appendix C — Golden Test Vectors (spec only)

Future golden datasets for: timestamp correctness, leakage detection, slippage, fees, partial fills, missing data, duplicate events, ordering, reorg, liquidity collapse, calibration bins, metric calculations. **Not implemented in this mission.**

---

## Appendix D — Performance Governance Levels (non-final)

```text
IDEA → RESEARCH → EXPERIMENTAL → REPLICATED → ROBUST → PROVISIONALLY_ACCEPTED → PRODUCTION_CANDIDATE
```

Dependencies on Agents 04/05/06/16/19 — **policy not finalized here.**

Explicit separation:

```text
QUANT VALIDATION ≠ GOVERNANCE ACCEPTANCE ≠ PRODUCTION ADMISSION
```

---

```text
MISSION_STATUS = QUANTITATIVE_INTELLIGENCE_ARCHITECTURE_ANALYSIS_COMPLETE_WITH_GAPS
AGENT_ID = AGENT-12
DIRECT_COMMANDER = MASTER ORCHESTRATOR
LIFECYCLE_STATUS = IDLE / DORMANT / WAITING_FOR_NEW_COMMAND
DUAL_19 = UNRESOLVED
AGENT_ONE = NOT IMPLEMENTED / FUTURE_NON_AUTHORITY_ROOT
AHOS_IMPACT = NONE
CODE_CHANGES = NONE
RUNTIME_CHANGES = NONE
GOVERNANCE_CHANGES = NONE
COMMIT = NONE
PUSH = NONE
OPERATING_BASELINE_USED = YES
BASELINE_PROPAGATION_CLAIM = NOT_MADE
INDEPENDENT_VERIFICATION = NOT_PERFORMED — NO AGENT_16/19 MISSION EVIDENCE IN REPOSITORY
LAUNCH_BLOCKERS = 4
NON_BLOCKING_BACKLOG = 15
CAPABILITY_GAPS = LIVE_PRODUCTION_DB; SOAK_RUNTIME_STATE; FULL_ON_CHAIN_ARCHIVE; TELEGRAM_N8N_LIVE_PATHS
HUMAN_DECISIONS_REQUIRED = HD-Q01 Feature registry canonical location; HD-Q02 Locked eval sets at launch vs Phase 3; HD-Q03 Calibration joined_pairs threshold for user messaging; HD-Q04 REJECTED lead prioritization; HD-Q05 Paper ledger unification; HD-Q06 ML introduction timeline
UNVERIFIED_CLAIMS = AHOS production calibration state beyond committed reports; full on-chain PIT reproducibility; org-wide baseline adoption; independent verification of any quant path
RECOMMENDED_NEXT_MISSION = STATE ONLY — Integrate QuantExperiment schema into agent_org TCB and mirror AHOS experiment logs; OR joint Agent-12+09 on-chain PIT feature registry; OR Agent-16 independent verification of AHOS leakage golden fixtures — DO NOT EXECUTE
```
