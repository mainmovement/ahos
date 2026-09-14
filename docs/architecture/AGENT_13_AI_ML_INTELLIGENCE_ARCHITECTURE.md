# Agent Organization AI/ML Intelligence Architecture

```text
DOCUMENT_ID      = AGENT_13_AI_ML_INTELLIGENCE_ARCHITECTURE
MISSION_ID       = TASK-20260914-014
VERSION          = 0.1.0
STATUS           = PROPOSED / READ_ONLY_AI_ML_INTELLIGENCE_ARCHITECTURE
AUTHORITY        = NONE CREATED
RUNTIME_EFFECT   = NONE
AHOS_EFFECT      = NONE
AGENT_ID         = AGENT-13 (agent.org.13-ai-ml-intelligence — documentary)
DIRECT_COMMANDER = MASTER ORCHESTRATOR
PARENT           = MASTER ORCHESTRATOR
```

This document is a **design and architecture artifact** produced by AGENT-13 under explicit activation for TASK-20260914-014. It does not implement ML models, adopt governance, grant authority, modify AHOS, connect providers, train models from this repository, or promote knowledge. Facts cite repository evidence with explicit classification labels (`[IMPLEMENTED]`, `[DOCUMENTED]`, `[PARTIALLY_IMPLEMENTED]`, `[PROPOSED]`, `[PLANNED]`, `[DEFERRED]`, `[UNKNOWN]`, `[BLOCKED]`). Architectural recommendations are labeled `[PROPOSED]`.

**Critical honesty constraint:**

```text
AI                      ≠ INTELLIGENCE
INTELLIGENCE            ≠ KNOWLEDGE
KNOWLEDGE               ≠ TRUTH
TRUTH                   ≠ AUTHORITY
AUTHORITY               ≠ DECISION
DECISION                ≠ EXECUTION
MODEL OUTPUT            ≠ FACT
MODEL CONFIDENCE        ≠ TRUTH
MODEL PROBABILITY       ≠ GUARANTEE
MODEL EXPLANATION       ≠ CAUSAL EXPLANATION
MODEL CONSENSUS         ≠ INDEPENDENT EVIDENCE
MODEL DISAGREEMENT      ≠ NOISE
RETRIEVAL               ≠ TRUTH
SEMANTIC SIMILARITY     ≠ FACTUAL IDENTITY
ANOMALOUS               ≠ DANGEROUS
ANOMALOUS               ≠ OPPORTUNITY
RANK #1                 ≠ BUY
CALIBRATION HARNESS     ≠ CALIBRATED SYSTEM
TRAINED                 ≠ PRODUCTION READY
```

**Additional invariants (Agent-13 derived):**

```text
DETERMINISTIC SCORE     ≠ LEARNED MODEL
LLM STANCE              ≠ DECISION
COGNITIVE PANEL VETO    ≠ SECURITY VERDICT (downgrade-only advisory)
ENSEMBLE AGREEMENT      ≠ INDEPENDENT CONFIRMATION
FEATURE AVAILABLE       ≠ FEATURE VALID FOR ML LABEL
INSUFFICIENT_DATA       ≠ MODEL FAILURE (often correct abstention)
NEGATIVE ML RESULT      ≠ WASTED WORK
OOD STATUS              ≠ AUTOMATIC REJECTION (requires policy)
ABSTAIN                 ≠ ERROR
HALLUCINATED CITATION   ≠ EVIDENCE
GRAPH PROXIMITY         ≠ CAUSALITY
BACKTEST ML PERFORMANCE ≠ POST-DEPLOYMENT ML PERFORMANCE
```

---

## 1. Executive Summary

`[VERIFIED]` **Two repositories, two AI/ML postures:**

| Repository | AI/ML posture |
| --- | --- |
| **AHOS** (`G:\robat\ahos`) | **No traditional ML stack.** Runtime intelligence is **deterministic**: evidence → features → rule-based score → decision advisor. Optional **LLM advisory council** (`architecture/ai/council_live.py`) and **deterministic cognitive panel** (`architecture/knowledge/panel.py`). Lightweight statistical components: NumPy GMM regime classifier, streaming drift detector. Calibration harness and score ledger **implemented**; live measurement **blocked** on outcome accrual (`0 joined_pairs`). Strategy lab: **0/8+ accepted**. No model artifacts (`.pkl`, `.onnx`, etc.). |
| **Agent Organization** (`G:\robat\ahos-agent-org`) | **No AI/ML runtime.** Slice 2B epistemic types (`Prediction`, `ExperimentPlan`, `MemoryRecord`) exist generically — not ML-domain contracts. Research worker is bounded analyst; no training/inference. Planned role `agent.org.13-ai-ml-intelligence` is `[PLANNED]` only. |

**Central architectural question:**

> Where does AI create genuine measurable intelligence for AHOS, where does it create dangerous false confidence, and how can learning occur without silently rewriting reality, governance, evidence, authority, or production behavior?

**Agent-13 role:** Own **model lifecycle design**, **ML epistemology**, **training/inference governance**, **calibration of learned components**, **OOD/drift/failure memory for models**, and **safe learning boundaries** — while **not** owning feature semantics (07–09), security verdicts (10), risk framing (11), quant study validity (12), epistemic promotion (05), or methodology authority (06).

**Minimum defensible AI core for launch:** Preserve and calibrate the **existing deterministic scorer** as the baseline; treat LLM council and cognitive panel as **advisory-only** with explicit downgrade semantics; define **ModelInference contract** and **Model Registry schema** before any trained model enters the path; consume Agent-12's feature store and calibration harness as **validated inputs only**; reject deep learning, RL, and online learning for launch.

**Launch blockers (AI/ML-relevant):** (1) calibration unmeasured — no ground truth to validate any model or score, (2) no ML model registry or promotion gates, (3) no org↔AHOS ML epistemic bridge, (4) PIT token universe / label governance gaps inherited from quant/data domains. **No additional AI-specific launch blocker** beyond these shared infrastructure gaps — AHOS does not need ML to launch; it needs **honest non-ML intelligence with measurable calibration**.

**Operating baseline:** Agent-13 operated per P1/P2/P3 for this mission. `BASELINE_PROPAGATION = BASELINE_NOT_PROPAGATED` — not claimed adopted org-wide.

---

## 2. Repository Forensics

### 2.1 Agent Organization (`G:\robat\ahos-agent-org`)

| Path | Finding | Classification |
| --- | --- | --- |
| `docs/agents/PLANNED_19_AGENT_MAP.md` | `agent.org.13-ai-ml-intelligence` — PLANNED, not seeded in code | `[PLANNED]` |
| `agent_org/epistemic.py` | Generic `Prediction`, `ExperimentPlan`, `ExperimentRun`, `MemoryRecord`, `Hypothesis` | `[IMPLEMENTED]` `[TESTED]` — not ML-specific |
| `research_worker/` | Bounded analyst; `execution_requested: False`; no model code | `[IMPLEMENTED]` |
| `ahos_org/registry.py` | No ML-specific Slice 1 canonical role | `[IMPLEMENTED]` registry only |
| `ahos_org/policy.py` | Global denies: `trading.live`, `provider.connect`, `ahos.*` | `[IMPLEMENTED]` `[TESTED]` |
| `docs/architecture/AGENT_05..12_*.md` | Peer architecture inputs | `[DOCUMENTED]` |
| ML model registry, training pipeline, inference runtime | — | `[NONE]` |

### 2.2 AHOS (`G:\robat\ahos`) — read-only inspection

#### Scoring & deterministic intelligence

| Module | Capability | Classification |
| --- | --- | --- |
| `architecture/scoring/engine.py` | Opportunity scoring 0–100, confidence, risk | `[IMPLEMENTED]` |
| `architecture/scoring/calculator.py` | Score breakdown from features | `[IMPLEMENTED]` |
| `architecture/features/extractor.py` | Rule-based feature vector | `[IMPLEMENTED]` — not ML |
| `architecture/intelligence/engine.py` | Full pipeline: evidence → score | `[IMPLEMENTED]` |
| `architecture/decision/advisor.py` | ENTER/WAIT/AVOID + sizing | `[IMPLEMENTED]` |
| `architecture/decision/authority.py` | Canonical decision brain; council/panel downgrade-only | `[IMPLEMENTED]` |

#### Statistical / lightweight ML-adjacent

| Module | Capability | Classification |
| --- | --- | --- |
| `architecture/intel/regimes.py` | 3-state GMM regime (NumPy EM) | `[IMPLEMENTED]` — post-hoc calibration segmentation |
| `architecture/learning/drift.py` | Streaming mean-shift drift detector | `[IMPLEMENTED]` — not ML library |
| `architecture/security/manipulation_detection.py` | Wash/tax/velocity heuristics | `[IMPLEMENTED]` — rule-based, not ML anomaly model |

#### LLM / council / cognitive

| Module | Capability | Classification |
| --- | --- | --- |
| `architecture/ai/council_live.py` | Multi-provider LLM council, anti-echo | `[IMPLEMENTED]` — advisory-only |
| `architecture/ai/clients.py` | OpenAI-compatible + Anthropic HTTP | `[IMPLEMENTED]` |
| `architecture/ai/router.py` | Ollama → cloud → heuristic floor | `[PARTIALLY_IMPLEMENTED]` — Tier 2 cloud stub |
| `architecture/ai/debate_council.py` | Bull/Bear/Risk debate pattern | `[PARTIALLY_IMPLEMENTED]` — mostly templates |
| `architecture/council.py` | Contract-based advisory council (no network) | `[IMPLEMENTED]` |
| `architecture/knowledge/panel.py` | CognitivePanel — deterministic lens checks | `[IMPLEMENTED]` — explicitly not LLM role-play |
| `architecture/knowledge/lenses.py` | 20 expert lens data cards | `[IMPLEMENTED]` |
| `config/ai_council_providers.yaml` | LLM provider registry | `[IMPLEMENTED]` |
| `config/ai_assistants.yaml` | Logical assistant roles | `[DOCUMENTED]` — YAML loader only |
| `council.ts`, `chat.ts` | TS deterministic council/chat | `[IMPLEMENTED]` — no LLM in chat path |

#### Learning / calibration / evolution

| Module | Capability | Classification |
| --- | --- | --- |
| `architecture/learning/score_ledger.py` | Append-only prediction persistence | `[IMPLEMENTED]` |
| `architecture/learning/calibration.py` | Read-only score-vs-outcome harness | `[IMPLEMENTED]` — measurement `[BLOCKED]` |
| `architecture/learning/prediction_lifecycle.py` | Prediction → observation bridge | `[IMPLEMENTED]` |
| `architecture/evolution/engine.py` | Human-gated improvement proposals | `[IMPLEMENTED]` — no auto-learning |
| `discovery/feature_store.py` | fs_v0.1/v0.2; L1–L4 leakage laws | `[IMPLEMENTED]` `[TESTED]` |

#### Research / strategy lab

| Module | Capability | Classification |
| --- | --- | --- |
| `strategy_lab/` | Causal backtest, gates, registry | `[IMPLEMENTED]` — 0 ACCEPTED |
| `research/baseline_stats.py` | Pre-registered statistical guards | `[IMPLEMENTED]` |
| ML model registry | — | `[NOT IMPLEMENTED]` |

#### Artifacts & dependencies

| Check | Result |
| --- | --- |
| sklearn / PyTorch / TensorFlow / XGBoost imports | **0** in runtime `.py` |
| Serialized models (`.pkl`, `.onnx`, `.pt`, `.gguf`) | **0** files |
| Embeddings / vector DB | **PLANNED** in archived OSS docs only |
| Online learning / auto weight mutation | **Explicitly forbidden** — calibration "does NOT tune anything" |

### 2.3 Forensic gaps (`CAPABILITY_GAP`)

| Gap | Reason |
| --- | --- |
| Live production DB contents | Not accessed — credentials/production forbidden |
| 72-hour soak runtime state | Not disturbed — mission constraint |
| LLM provider live behavior on operator laptop | Not activated — keys/network optional |
| Full embedding/RAG infrastructure | Not implemented — cannot verify |

---

## 3. Current AI/ML Capabilities

### 3.1 Classification matrix

| Capability | AHOS | Agent Org | Launch relevance |
| --- | --- | --- | --- |
| Rule-based opportunity scoring | `[IMPLEMENTED]` | `[NONE]` | **Core product intelligence today** |
| Deterministic cognitive panel | `[IMPLEMENTED]` | `[NONE]` | Advisory downgrade path |
| LLM advisory council | `[IMPLEMENTED]` optional | `[NONE]` | Research/explanation; not decision authority |
| GMM regime classifier | `[IMPLEMENTED]` | `[NONE]` | Segmentation only; not trading signal |
| Streaming drift detector | `[IMPLEMENTED]` | `[NONE]` | Monitoring; not auto-retrain trigger |
| Calibration harness | `[IMPLEMENTED]` | `[NONE]` | **Launch-critical when pairs accrue** |
| Feature store L1–L4 | `[IMPLEMENTED]` | `[NONE]` | **Required ML input foundation** |
| Classical/deep ML training | `[NONE]` | `[NONE]` | Deferred by design |
| Model registry | `[NONE]` | `[NONE]` | **Must exist before any trained model** |
| Embeddings / RAG | `[PLANNED]` archive only | `[NONE]` | Later |
| Online learning | `[DEFERRED]` docs | `[NONE]` | Forbidden for launch |
| Org ML TCB types | `[NONE]` | `[PROPOSED]` | Integration gap |
| Independent ML verification | `[SELF-TEST ONLY]` | `[NONE]` | Agent 16 not engaged |

### 3.2 What AHOS can legitimately claim today

| Claim type | Legitimate? | Evidence |
| --- | --- | --- |
| "Scoring is deterministic and explainable from measured evidence" | **Yes** (bounded) | `architecture/scoring/`, tests |
| "LLM council is advisory-only and cannot override security veto" | **Yes** | `council_live.py`, `authority.py` |
| "Cognitive panel runs offline deterministic checks, not LLM role-play" | **Yes** | `panel.py` docstring, tests |
| "No trained ML model exists in production path" | **Yes** | Forensic scan: 0 artifacts, 0 ML imports |
| "Opportunity score is calibrated" | **No** | 0 joined_pairs; M-GAP-008 OPEN |
| "AI council provides independent confirmation" | **No** | Same evidence packet; echo detection only |
| "Regime classifier predicts future returns" | **No** | Post-hoc segmentation in calibration only |
| "System learns from live results automatically" | **No** | Evolution engine requires human gates |

### 3.3 What AI/ML can safely consume from Agent-12's quantitative foundation

| Asset | Safe to consume now? | Condition |
| --- | --- | --- |
| Feature store L1–L4 outputs at `as_of` | **Yes** (bounded) | Unit-tested fixtures; not broad token universe |
| Pre-registered search cells | **Yes** | For hypothesis design, not auto-promotion |
| `baseline_stats.py` guards (MIN_N=200) | **Yes** | Mandatory for any ML eval report |
| Calibration harness join semantics | **Yes** | Read-only; no weight tuning |
| Strategy lab rejected registry | **Yes** | Negative-result memory; do not re-train on failures without lineage |
| 3.6y BinanceVision OHLCV | **Yes** | Majors research only; not token discovery ML |
| Outcome labels (T+72h) | **No until accrual** | 0 joined_pairs — labels not yet measurable at scale |
| Vector engine screens | **No for ML labels** | Weaker causality — SCREENING_ONLY |
| Cross-asset OOS claims (H6/H10) | **No** | REJECTED — not valid training justification |

### 3.4 What must NOT be consumed until validated

| Asset | Blocker |
| --- | --- |
| Retrospective scam/rug labels | PIT label availability unverified |
| Provider backfilled social/on-chain data | Provider drift + revision risk |
| LLM-generated hypotheses as training labels | No evidence path |
| Paper trading PnL as reward signal | Dual-ledger reconciliation open (Agent-12 CR) |
| Public ranking feedback loops | Endogenous bias (§36) |
| Survivorship-biased token universe | PIT universe not implemented |

---

## 4. AI/ML Epistemology

### 4.1 Intelligence pipeline

```text
RAW DATA
  ↓  (provenance, freshness, quality — Agent 07)
FEATURE
  ↓  (PIT availability, formula version — Agent 07/12)
REPRESENTATION
  ↓  (embedding, aggregation, regime — Agent 13 design)
MODEL INPUT
  ↓  (typed contract, cutoff timestamp)
MODEL OUTPUT
  ↓  (raw logits/scores — not yet calibrated)
PREDICTION
  ↓  (scoped claim with horizon)
CALIBRATED ESTIMATE
  ↓  (reliability diagram, abstention — Agent 12/13)
EMPIRICAL OUTCOME
  ↓  (frozen labeler, no peeking)
MODEL EVALUATION
  ↓  (pre-registered metrics, baselines)
EPISTEMIC ASSESSMENT
  ↓  (promotion/rejection — Agent 05)
```

### 4.2 Epistemic invariants (extended)

```text
RAW PROVIDER JSON           ≠ VALIDATED FEATURE
AGGREGATED FEATURE          ≠ CAUSAL DRIVER
IN-SAMPLE FIT               ≠ GENERALIZATION
HOLDOUT PASS (once)         ≠ ROBUST MODEL
EXPLANATION ARTIFACT        ≠ GROUND TRUTH MECHANISM
HIGH PR-AUC ON RARE EVENT   ≠ SAFE DEPLOYMENT (check FN cost)
LOW ECE ON TRAIN CALIBRATION ≠ LIVE CALIBRATION
SYNTHETIC LABEL             ≠ OBSERVATION
HUMAN ANNOTATION            ≠ KNOWLEDGE (until promoted)
MODEL DISAGREEMENT          ≠ EPISTEMIC CONTRADICTION (until formalized)
```

### 4.3 Relationship to Agent-05 epistemic ladder

Slice 2B types map to ML lifecycle:

| ML artifact | Epistemic type | Default state |
| --- | --- | --- |
| Model hypothesis | `Hypothesis` | PROPOSED |
| Model output at T | `Prediction` | PROPOSED → CONFIRMED/REFUTED |
| Eval report | `ExperimentRun` | Non-promoting |
| Promoted model policy | `KnowledgeCandidate` | Requires TCB gate |
| Model failure record | `MemoryRecord` | FAILURE class |
| Conflicting model claims | `ContradictionCase` | OPEN until resolved |

**Model output never auto-promotes to `Knowledge`.**

---

## 5. AI Role Taxonomy

| Class | Description | Classification | Rationale |
| --- | --- | --- | --- |
| **A. Deterministic intelligence** | Rules, formulas, thresholds (current scorer) | **USEFUL NOW** | Implemented, auditable, baseline for all ML |
| **B. Statistical intelligence** | Regression, Bayesian, time-series (GMM regime) | **USEFUL NOW** (limited) | Regime segmentation exists; not primary signal |
| **C. Classical ML** | Trees, linear models, clustering, anomaly IF | **USEFUL LATER** | Needs labels + registry; start with baselines |
| **D. Deep learning** | Sequence/temporal/graph neural nets | **RESEARCH ONLY** | No evidence of edge over baselines; high ops cost |
| **E. Representation learning** | Embeddings, latent features | **RESEARCH ONLY** | Not implemented; entity resolution risk |
| **F. LLM reasoning** | Hypothesis, synthesis, explanation, challenge | **USEFUL NOW** (bounded) | Implemented advisory council; research + downgrade |
| **G. Multi-agent intelligence** | Council, specialist collaboration | **USEFUL NOW** (bounded) | Cognitive panel + LiveCouncil — advisory only |
| **H. Adaptive learning** | Online updating, drift adaptation | **DANGEROUS NOW** | Forbidden until offline validation pipeline exists |
| **I. Cognitive architecture** | World models, memory, causal self-critique | **RESEARCH ONLY / FUTURE** | AGI/ACI charter direction; not launch |

---

## 6. Model Registry

`[PROPOSED]` Canonical registry — **does not exist today**. Strategy lab has `strategy_lab/registry.json` for hypotheses only.

### 6.1 Tracked fields

```text
model_id
model_version
architecture
training_data_id
training_cutoff
feature_set_version
label_definition_id
objective
loss
hyperparameters
seed
code_version (git SHA)
environment_fingerprint
dependencies_lock
validation_protocol_id
performance_summary (holdout, not train)
calibration_report_id
failure_history[]
drift_history[]
status
promotion_history[]
search_lineage_id
baseline_comparison_id
independence_matrix_id
```

### 6.2 Promotion states (no shortcuts)

```text
MODEL_CREATED
  → MODEL_TRAINED
  → MODEL_EVALUATED
  → MODEL_REPLICATED (Agent 16)
  → MODEL_CALIBRATED
  → MODEL_APPROVED_FOR_RESEARCH
  → MODEL_APPROVED_FOR_PAPER
  → MODEL_PRODUCTION_CANDIDATE
  → (governance) MODEL_PROMOTED
```

**Forbidden transition:** `MODEL_TRAINED → PRODUCTION` without full chain.

### 6.3 Current status

| Component | Status |
| --- | --- |
| AHOS strategy hypothesis registry | `[IMPLEMENTED]` — not ML |
| AHOS AI provider YAML registry | `[IMPLEMENTED]` — inference endpoints, not models |
| ML model registry | `[NOT IMPLEMENTED]` |

---

## 7. Dataset Governance

### 7.1 Dataset identity contract `[PROPOSED]`

Every training/eval dataset must declare:

```text
dataset_id
dataset_version
content_hash
cutoff_timestamp
inclusion_rules
exclusion_rules
label_definition_id
feature_set_version
pit_attestation
synthetic_fraction
provider_manifest
survivorship_policy
correction_policy
```

### 7.2 AHOS existing anchors

| Asset | Governance |
| --- | --- |
| `research/data/MANIFEST.json` | sha256-pinned BinanceVision — `[IMPLEMENTED]` |
| `discovery/feature_store.py` | L1–L4 laws — `[IMPLEMENTED]` |
| `score_ledger` source tagging | `local\|sandbox\|test\|synthetic`; only `local` calibration-eligible — `[IMPLEMENTED]` |
| Unified DatasetIdentity across surfaces | `[NOT IMPLEMENTED]` — Agent-12 CR-07 |

### 7.3 Rules

1. **No secret training on future information** — enforced by PIT joins (§8).
2. **Synthetic/test rows never enter production model training** without explicit quarantine flag.
3. **Label corrections create new label version** — never silently rewrite historical training rows.
4. **Class imbalance must be declared** before metric selection (§13).
5. **Generated labels (LLM)** require quarantine workflow — `[PROPOSED]` Agent-12 backlog item 15.

---

## 8. Point-in-Time ML

For inference at time **T**, every input must satisfy:

```text
availability_ts <= T
retrieved_ts <= T  (for L1 features)
label_observation_ts > T  (labels are outcomes, never inputs)
token_identity_at_T == token_identity_used  (no retrospective merge)
```

### 8.1 Coordination with Agent-12

| Leakage class | Owner | ML-specific note |
| --- | --- | --- |
| L1 future observations | Feature store | ML must not bypass store with ad-hoc joins |
| L2 outcome in features | Architecture test | ML feature pipelines must not import label tables |
| L3 availability | DB CHECK | Model serving must respect `availability_ts` |
| L4 research joins | Join policy | Train/test splits must use PIT feature rows only |

### 8.2 ML-specific PIT risks (beyond L1–L4)

| Risk | Example | Mitigation |
| --- | --- | --- |
| **Future metadata** | Contract verified after launch | PIT contract snapshot at T |
| **Revised token identity** | Merge/split/rebrand | Entity resolution with effective dates |
| **Retrospective scam labels** | Rug labeled weeks later | Label `available_at` separate from event |
| **Provider backfill** | Historical volume revised | Provider version + revision detection |
| **Future liquidity** | Depth at T+24h in feature | Strict observation cutoff |
| **Future social data** | Tweet deleted then archived | Ingestion timestamp ≤ T |

---

## 9. Label Governance

### 9.1 Label vs outcome vs observation vs knowledge

| Type | Definition | Example | ML use |
| --- | --- | --- | --- |
| **Observation** | Measured at T | `liquidity_usd` at retrieval | Feature input |
| **Outcome** | Horizon-closed event | +50% at 24h | Eval target (after close) |
| **Label** | Assigned class on outcome | `opportunity_hit` | Supervised target |
| **Knowledge** | Promoted belief | "Feature X predicts Y in regime Z" | Not automatic from label |

### 9.2 AHOS label surfaces

| Label | Producer | Availability | Classification |
| --- | --- | --- | --- |
| `outcome_label` (Lane-A) | `discovery/outcomes.py` frozen labeler | T+horizon | `[IMPLEMENTED]` |
| Security verdict | Agent-10 domain | At check time | `[IMPLEMENTED]` — not ML label without governance |
| Scam/rug (retrospective) | `[DOCUMENTED]` plans | Often delayed | **Blocked for ML until PIT policy** |
| LLM stance | LiveCouncil | Instant | **Not a label** — advisory metadata only |

### 9.3 Label authority questions

| Question | Policy `[PROPOSED]` |
| --- | --- |
| Who creates labels? | Frozen labeler code + human governance for new definitions |
| What evidence supports label? | Observation chain + labeler version ID |
| When available? | `label_available_at >= outcome_close_ts` |
| Can label be corrected? | Yes → new `label_version`; old rows immutable |
| Does correction rewrite inputs? | **Never** — triggers re-eval, not silent retrain |

---

## 10. Leakage Taxonomy

### 10.1 Unified ML leakage taxonomy

| ID | Class | Description | Detection |
| --- | --- | --- | --- |
| LK-ML-01 | **Temporal leakage** | Future data in features | PIT join audit |
| LK-ML-02 | **Label leakage** | Outcome in input | Architecture import test |
| LK-ML-03 | **Train-test contamination** | Same entity in both splits | Group split by token_id |
| LK-ML-04 | **Survivorship leakage** | Dead tokens excluded from train | PIT universe |
| LK-ML-05 | **Meta leakage** | Hyperparams tuned on test | Locked holdout + lineage |
| LK-ML-06 | **Provider revision leakage** | Backfilled history | Provider version stamp |
| LK-ML-07 | **Human-in-the-loop leakage** | Analyst sees test before split | Pre-registration |
| LK-ML-08 | **Feedback leakage** | Model output affects future labels | Exposure logging |
| LK-ML-09 | **Embedding leakage** | Encoder trained on test corpus | Separate encoder train split |
| LK-ML-10 | **LLM leakage** | Prompt contains future outcome | Prompt audit hash |

Agent-12 L1–L4 map to LK-ML-01/02/03/04 at feature layer. ML adds LK-ML-05 through LK-ML-10.

---

## 11. OOD Detection

### 11.1 Domain status enum `[PROPOSED]`

```text
IN_DOMAIN
EDGE_OF_DOMAIN
OUT_OF_DOMAIN
UNKNOWN_DOMAIN
```

### 11.2 OOD triggers for AHOS

| Signal | Example |
| --- | --- |
| New chain | First Base token when trained on Solana only |
| New token class | LST vs meme vs AI agent token |
| Unusual liquidity | Depth 100× training median |
| Novel volatility regime | Post-hack market |
| New attack pattern | Previously unseen honeypot variant |
| Provider behavior change | Field semantics shift |

### 11.3 Policy

```text
OOD → normal confidence   FORBIDDEN without explicit downgrade policy
OOD → ABSTAIN             PREFERRED default
OOD → alert + deterministic fallback   REQUIRED for production path
```

AHOS today: no explicit OOD contract. Regime classifier returns probabilities but no OOD gate on scorer.

---

## 12. Drift

### 12.1 Drift types

| Type | Definition | AHOS today |
| --- | --- | --- |
| **Data drift** | P(X) changes | `StreamingDriftDetector` `[IMPLEMENTED]` |
| **Concept drift** | P(Y\|X) changes | Not auto-detected |
| **Label drift** | P(Y) changes | Calibration segmentation by band |
| **Regime drift** | Market state shift | GMM regime in calibration reports |
| **Provider drift** | Source semantics change | `[DOCUMENTED]` Agent-07; not ML-integrated |

### 12.2 Response ladder `[PROPOSED]`

```text
DETECT → LOG → SEGMENT EVAL → ALERT → QUARANTINE → OFFLINE RETRAIN PROPOSAL → VALIDATE → PROMOTE
```

**Never:** `DETECT → AUTO RETRAIN → AUTO DEPLOY`

---

## 13. Calibration

### 13.1 AHOS existing harness `[IMPLEMENTED]`

`architecture/learning/calibration.py`:
- Pre-declared score bands (fixed constants)
- No-peeking join
- MIN_N=200 per band (from `baseline_stats.py`)
- Brier, ECE, Spearman — read-only
- Explicitly **does NOT tune weights**

### 13.2 ML calibration requirements `[PROPOSED]`

| Component | Requirement |
| --- | --- |
| Probability outputs | Reliability diagram + ECE on holdout |
| Score outputs | Band hit-rates vs predicted ordering |
| Selective prediction | Coverage vs accuracy tradeoff reported |
| Abstention rate | Tracked as first-class metric |
| Conformal sets | Optional Phase 3 — research track |

### 13.3 Coordination with Agent-12

Agent-12 owns **whether empirical effect exists** in data. Agent-13 owns **whether a model's probabilities mean what they claim**. Both require joined pairs — currently **0** (`M-GAP-008`).

---

## 14. Abstention

### 14.1 Abstention reasons `[PROPOSED]`

```text
INSUFFICIENT_DATA
OUT_OF_DOMAIN
CONFLICTING_EVIDENCE
LOW_CALIBRATION
STALE_INPUT
UNKNOWN
MISSING_CRITICAL_FEATURE
SECURITY_UNRESOLVED
PROVIDER_FAILURE
MODEL_QUARANTINED
```

### 14.2 AHOS partial implementation

| Surface | Abstention behavior |
| --- | --- |
| LiveCouncil | `UNCLEAR` stance respected in prompt |
| CognitivePanel | Lenses return `ABSTAIN` — never guess |
| Scorer | NULL features → reduced confidence paths |
| Decision advisor | `WAIT` action |

**Gap:** No unified `AbstentionRecord` typed contract across scorer, ML, and council.

---

## 15. Model Failure Memory

### 15.1 Failure classes

```text
MODEL_OVERFIT
REGIME_FAILURE
CHAIN_FAILURE
TOKEN_CLASS_FAILURE
LIQUIDITY_FAILURE
DATA_LEAKAGE
LABEL_ERROR
CALIBRATION_FAILURE
OOD_FAILURE
DRIFT_FAILURE
PROVIDER_FAILURE
ADVERSARIAL_FAILURE
EXPLANATION_FAILURE
ENSEMBLE_ECHO_FAILURE
FEEDBACK_LOOP_FAILURE
```

### 15.2 Connection to AHOS evolution engine

`architecture/evolution/engine.py` — human-gated proposals with `is_ai` flag, fail-closed on AI approvers. Model failures should feed `ImprovementProposal` with `research_basis` claim IDs — not auto-mutate weights.

Slice 2B `MemoryRecord` — `[PROPOSED]` store failure class + model_id + evidence.

Strategy lab rejected hypotheses — **existing negative-result memory** (`registry.json` all REJECTED).

---

## 16. Safe Online Learning

### 16.1 Verdict

| Mode | Classification |
| --- | --- |
| Online learning | **NOT JUSTIFIED NOW** |
| Continual learning | **RESEARCH ONLY** |
| Adaptive models (live weight update) | **DANGEROUS NOW** |

### 16.2 Required loop (when eventually justified)

```text
OBSERVATION
  → EPISODE
  → FAILURE ANALYSIS
  → HYPOTHESIS
  → EXPERIMENT
  → OFFLINE TRAINING
  → VALIDATION
  → INDEPENDENT VERIFICATION (Agent 16)
  → PROMOTION (governance)
```

**Forbidden:**

```text
LIVE RESULT → AUTOMATIC MODEL MUTATION → AUTOMATIC PRODUCTION PROMOTION
```

AHOS calibration module explicitly forbids quiet weight editing during measurement.

---

## 17. Self-Improvement

### 17.1 Cognitive loop classification

| Stage | AHOS today | Classification |
| --- | --- | --- |
| PERCEIVE | Collector + providers | `[IMPLEMENTED]` |
| UNDERSTAND | Intelligence engine | `[IMPLEMENTED]` deterministic |
| REMEMBER | Knowledge store, score ledger | `[PARTIAL]` |
| MODEL | Scorer weights (static) | `[IMPLEMENTED]` — not learning |
| REASON | Advisor + panel + council | `[IMPLEMENTED]` advisory |
| HYPOTHESIZE | Evolution proposals, strategy lab | `[IMPLEMENTED]` gated |
| EXPERIMENT | Strategy lab, calibration | `[IMPLEMENTED]` |
| LEARN | Calibration measurement only | `[PARTIAL]` — blocked on data |
| SELF-CRITICIZE | Panel veto, council disagreement | `[IMPLEMENTED]` downgrade |
| PROMOTE / REJECT | TCB + human gates | `[IMPLEMENTED]` org-side types |

**Learning ≠ production mutation** — enforced in evolution engine laws.

---

## 18. AI Council

### 18.1 AHOS implementations

| Council | Type | Independence | Authority |
| --- | --- | --- | --- |
| **CognitivePanel** | Deterministic lenses | High (rule-based, offline) | Downgrade-only |
| **LiveCouncil** | Multi-LLM parallel | **Low** — same packet, correlated training | Downgrade-only |
| **debate_council** | Template bull/bear | N/A — not live LLM | Advisory |
| **council.ts** | UI simulation | N/A | Display only |

### 18.2 Future council roles `[PROPOSED]`

| Role | Function | Independence requirement |
| --- | --- | --- |
| Analyst | Evidence summary | Different method than scorer |
| Critic | Challenge assumptions | Must not share scorer code path |
| Quant | Statistical sanity | Agent-12 methods |
| Security | Veto patterns | Agent-10 rules — not LLM |
| Market | Regime context | Agent-08 data |
| On-chain | Graph facts | Agent-09 observations |
| Methodology | Design critique | Agent-06 |
| Red-team | Adversarial probe | Agent-19 |
| Verifier | Reproducibility | Agent-16 |

### 18.3 Independence rule

Five models sharing same dataset, assumptions, prompt, model family, and feature pipeline **≠ five independent confirmations**. LiveCouncil detects `ECHO_SUSPECTED` on unanimity — correct instinct, insufficient alone.

---

## 19. Model Independence

### 19.1 Conceptual independence matrix `[PROPOSED]`

|  | Model A | Model B |
| --- | --- | --- |
| **MODEL** | architecture family | — |
| **DATA** | training cutoff overlap | shared provider bias |
| **FEATURE** | formula overlap | shared extractor |
| **TRAINING** | seed / HPO correlation | same search cell |
| **PROMPT** | template similarity | shared system prompt |
| **ARCHITECTURE** | correlated errors | ensemble diversity |
| **ERROR** | failure mode overlap | common blind spots |
| **PROVIDER** | same LLM vendor | same API outage |

**Ensemble consensus ≠ independent evidence** unless matrix shows low common-cause coupling.

---

## 20. LLM Governance

### 20.1 Appropriate uses (empirically bounded for AHOS)

| Use | Classification | Evidence |
| --- | --- | --- |
| Research synthesis | **USEFUL NOW** | Research worker path |
| Hypothesis generation | **USEFUL NOW** | Quarantined until tested |
| Document analysis | **USEFUL LATER** | No RAG infra |
| Contradiction discovery | **USEFUL NOW** | With evidence citation requirement |
| Explanation of deterministic outputs | **USEFUL NOW** | Must cite scorer fields |
| Prompt generation | **RESEARCH ONLY** | Injection risk |
| Agent orchestration | **USEFUL NOW** | This org — not AHOS prod |
| Qualitative signal extraction | **USEFUL LATER** | Needs provenance chain |

### 20.2 Dangerous uses (forbidden without new gates)

```text
UNVERIFIED NUMERIC CLAIMS
AUTOMATIC TRADING DECISIONS
SECURITY VERDICTS (SCAM/SAFE)
SOURCE-OF-TRUTH RECONSTRUCTION
UNSUPERVISED GOVERNANCE CHANGES
```

### 20.3 AHOS enforcement today

- `council_live.py`: deterministic verdict wins; security veto absolute
- `panel.py`: explicitly rejects LLM role-play
- `chat.ts`: no LLM — deterministic Persian routing
- `evolution/engine.py`: AI cannot approve proposals

---

## 21. RAG

### 21.1 Verdict

RAG for AHOS: **USEFUL LATER** — not implemented.

### 21.2 Safe RAG design `[PROPOSED]`

| Corpus | Use | Risk |
| --- | --- | --- |
| Project memory | Research assist | Stale/superseded docs |
| Provider documentation | Integration help | Version mismatch |
| Historical experiments | Avoid repeated failure | Selection bias in retrieval |
| Failure memory | Pattern warning | Over-weighting old failures |
| Governance | Policy lookup | Must not override Constitution |

```text
RETRIEVAL ≠ TRUTH
```

Retrieved document status must include: `STALE | SUPERSEDED | WRONG | UNVERIFIED | CONTRADICTORY`.

Every LLM factual claim requires evidence path — numeric claims must bind to AHOS observation IDs or `CAPABILITY_GAP`.

---

## 22. Semantic Memory

### 22.1 Safe embedding uses (future)

| Use | Safe? | Condition |
| --- | --- | --- |
| Similarity search for research docs | Yes | Not ranked as truth |
| Duplicate narrative detection | Yes | Confirm with hash/id |
| Failure case retrieval | Yes | Tag as historical |
| Token identity resolution | **Dangerous** | Embedding ≠ same token |
| News event resolution | **Dangerous** | Requires entity graph + timestamps |

```text
SEMANTIC SIMILARITY ≠ FACTUAL IDENTITY
```

Especially critical for: token identity, entity resolution, social claim resolution.

---

## 23. Graph AI

### 23.1 Future use cases `[PROPOSED]`

Wallet clustering, contract dependency graphs, liquidity networks, narrative propagation graphs, causal hypothesis graphs.

### 23.2 Boundaries (coordinate Agent-09, Agent-11)

```text
GRAPH PROXIMITY ≠ CAUSALITY
SHARED FUNDER ≠ COORDINATED PUMP (without temporal evidence)
```

Graph AI classification: **RESEARCH ONLY** for launch. AHOS has graph-adjacent intel modules (whales, forensics) — rule-based, not GNN.

---

## 24. Anomaly Detection

### 24.1 AHOS today

`architecture/security/manipulation_detection.py` — heuristic wash/tax/velocity flags. **Not** isolation forest / autoencoder.

Marketing/docs mention anomaly detection; runtime is threshold heuristics.

### 24.2 Design `[PROPOSED]`

| Principle | Policy |
| --- | --- |
| Anomaly ≠ dangerous | Require context + regime |
| Anomaly ≠ opportunity | Separate ranking objective |
| Baseline required | Per chain, token class, liquidity tier |
| Uncertainty explicit | Anomaly score ≠ probability of scam |

**Minimum viable:** Extend deterministic thresholds with documented baselines before ML anomaly models.

Classification for ML anomaly: **USEFUL LATER** — after labels and baseline stats exist.

---

## 25. Ranking

### 25.1 AHOS today

Opportunity scorer produces 0–100 rank. Decision advisor maps to ENTER/WAIT/AVOID — **not automatic BUY**.

### 25.2 ML ranking risks

| Risk | Control |
| --- | --- |
| Wrong objective | Separate detection vs actionability ranks |
| Position bias | Log exposure |
| Selection bias | Pre-register evaluation cohort |
| Feedback loops | Model → attention → price → label (§36) |
| Exposure bias | Counterfactual eval where possible |

```text
RANK #1 ≠ BUY
```

Never allow rank alone to authorize trading.

---

## 26. Reinforcement Learning

### 26.1 Verdict: **NOT JUSTIFIED** (launch and near-term)

| Factor | Assessment |
| --- | --- |
| Simulation quality | Event backtest partial; not RL-grade |
| Reward design | High hacking risk (PnL, attention) |
| Non-stationarity | Crypto regime shifts |
| Offline RL | Research track only |
| Exploration risk | Unacceptable in production |

**Classification:** RESEARCH ONLY at earliest — likely **NOT JUSTIFIED** until causal sim + paper ledger unified.

---

## 27. Causal AI

### 27.1 Separation

```text
PREDICTIVE MODEL  → P(Y|X) — ranking, alert
CAUSAL MODEL      → P(Y|do(X)) — intervention claims
```

AHOS strategy lab tests causal hypotheses on bar data — **not** SCM inference on token discovery.

### 27.2 Policy

No causal claim from ML without: identified intervention, confounding analysis, Agent-06 methodology sign-off, Agent-12 quant validation.

Coordinate Agents 05, 06, 12 — Agent-13 supplies model artifacts; does not own causal identification.

---

## 28. Explainability

### 28.1 Distinction

```text
EXPLANATION OF MODEL BEHAVIOR  → legitimate (SHAP, feature contribution)
EXPLANATION OF REALITY         → requires epistemic promotion
```

AHOS scorer already provides breakdown via `calculator.py` — **prefer this over post-hoc ML explainers** for launch path.

### 28.2 ML explainability policy

| Method | Use |
| --- | --- |
| Feature importance | Debug + audit |
| SHAP | Holdout only; not live authority |
| Attention maps (DL) | Research only |
| Counterfactual explanations | Hypothesis generation — not decisions |
| Surrogate models | Must not replace primary model for prod |

---

## 29. Uncertainty

### 29.1 Uncertainty types

| Type | Source | AHOS today |
| --- | --- | --- |
| **Aleatoric** | Irreducible randomness | Not decomposed |
| **Epistemic** | Model/data ignorance | Confidence buckets in scorer |
| **Model** | Architecture limitation | Not formalized |
| **Data** | Missing/stale features | NULL feature handling |
| **Distribution** | OOD / drift | Partial via drift detector |

**Never compress all uncertainty into one number without justification.**

`[PROPOSED]` `UncertaintyBundle` alongside `ModelInference` with typed components.

---

## 30. Adversarial AI

### 30.1 Attack surfaces

| Attack | Vector | Mitigation |
| --- | --- | --- |
| Poisoned training data | Provider manipulation | Dataset hash + anomaly screening |
| Adversarial inputs | Crafted token metadata | Feature bounds + OOD |
| Manipulated social signals | Bot narratives | Agent-10 + not LLM verdict |
| Fake liquidity | Wash trading | manipulation_detection heuristics |
| Prompt injection | Token description → LLM | Untrusted text boundary (§31) |
| Malicious documents | RAG corpus | Signed corpus + quarantine |

Coordinate Agent-03 (org security), Agent-10 (token security), Agent-19 (red team).

---

## 31. Prompt Injection / Agentic AI Security

### 31.1 Boundaries

```text
UNTRUSTED TEXT → MODEL     : sanitize; system prompt isolation; no tool authority
UNTRUSTED TEXT → TOOL CALL : forbidden without human/policy gate
```

External content (websites, social, token metadata, messages) is **potentially hostile**.

AHOS `council_live.py` constrains models to evidence packet — good pattern. Must extend to any future agentic tool use.

**Never:** external content becomes authority instruction because LLM interpreted it.

---

## 32. AI Memory

### 32.1 Memory classes (coordinate AGI/ACI charter)

| Class | Content | Provenance required |
| --- | --- | --- |
| **Episodic** | What happened at T | observation IDs |
| **Semantic** | What is believed | claim + status |
| **Procedural** | How to do X | versioned procedure |
| **Failure** | What failed | failure class + model_id |
| **Hypothesis** | What might be true | experiment link |
| **Causal** | Suspected relationships | methodology tag |
| **Self-model** | Own capabilities/limits | calibration history |

Slice 2B `MemoryRecord` — generic; ML failures map here `[PROPOSED]`.

---

## 33. World Model

### 33.1 Domains (future)

MARKET, TOKEN, CHAIN, LIQUIDITY, SECURITY, ACTORS, NARRATIVES, TIME, REGIMES

### 33.2 Status typing

Each world-model element must declare:

```text
OBSERVED | INFERRED | HYPOTHESIZED | UNKNOWN | CONTRADICTORY
```

```text
WORLD MODEL ≠ REAL WORLD
```

AHOS today: implicit world state in intelligence engine — not explicit typed world model.

**Classification:** RESEARCH ONLY / FUTURE.

---

## 34. Novelty

### 34.1 Novelty states (AGI/ACI alignment)

```text
KNOWN | UNCERTAIN | UNKNOWN | CONTRADICTORY | NOVEL
```

### 34.2 Policy

```text
UNSEEN ≠ IMPORTANT
NOVEL ≠ ACTIONABLE
```

Novelty detection should trigger **heightened abstention**, not automatic excitement. OOD + low data → ABSTAIN.

---

## 35. Cross-Agent Boundaries

| Agent | Owns | Agent-13 does NOT own |
| --- | --- | --- |
| **05 Epistemic** | Promotion, ContradictionCase | Knowledge acceptance |
| **06 Methodology** | Study design, preregistration | Methodology authority |
| **07 Data** | Quality, provenance, PIT data | Feature semantics |
| **08 Market** | Market intelligence features | Regime truth claims |
| **09 On-chain** | Chain observations, graphs | Entity resolution policy |
| **10 Security** | SCAM/SAFE boundary | Security verdicts from ML |
| **11 Risk** | Risk interpretation | Safety from model confidence |
| **12 Quant** | Effect existence, backtest validity | Statistical proof of edge |
| **13 AI/ML** | Model lifecycle, ML epistemology | Everything above |
| **16 Verification** | Independent replay | Self-verification as final |
| **19 Red Team** | Adversarial attack | Own red-team execution |

### 35.1 Handoff contracts

**AI ↔ Quant (Agent-12):**
- Agent-12: "Does the experiment show an empirical effect?"
- Agent-13: "Can a model reliably generalize that effect under PIT constraints?"
- Handoff: `QuantEffectReport` → `MLGeneralizationStudy` — neither replaces the other.

**AI ↔ Risk (Agent-11):**
- Agent-13 may emit probability/uncertainty estimates.
- Agent-11 owns safety framing — **model confidence ≠ safety**.

**AI ↔ Security (Agent-10):**
- ML may flag SUSPICIOUS/ANOMALOUS/UNUSUAL.
- ML must not emit SCAM/SAFE — security domain owns binary verdict.

**AI ↔ Data (Agent-07):**
- Every model eval must include data quality/freshness/missingness/provenance/drift census.

**AI ↔ Verification (Agent-16):**
- Reproducibility, leakage audit, registry integrity, promotion gates.

**AI ↔ Red Team (Agent-19):**
- Leakage, prompt injection, false confidence, feedback loops, poisoned data.

---

## 36. Feedback Loops

### 36.1 Dangerous loops

```text
MODEL → RANKS TOKEN → USER ATTENTION → MARKET MOVEMENT → TRAINING DATA → MODEL
MODEL → SIGNAL → PAPER TRADING → LABEL → MODEL
PUBLIC ALERT → LIQUIDITY CHANGE → FEATURE → SCORE
```

### 36.2 Controls `[PROPOSED]`

| Control | Mechanism |
| --- | --- |
| Exposure logging | Who saw rank at T |
| Holdout cohort | Never shown to users — pure eval |
| Delayed label join | Prevent same-day feedback |
| Attention-aware eval | Segment by publicity |
| Pre-registration | Hypothesis before deployment |

Self-fulfilling signals: backtest performance may not equal post-deployment performance when AHOS attention is material.

---

## 37. Model Lifecycle

```text
ACTIVE → MONITORED → DEGRADED → QUARANTINED → RETIRED
```

| State | Entry condition |
| --- | --- |
| ACTIVE | Passed promotion gates |
| MONITORED | Default after promotion |
| DEGRADED | Calibration drift, rising abstention |
| QUARANTINED | See §38 |
| RETIRED | Superseded or failed permanently |

Do not keep failing models active because they once performed well.

---

## 38. Model Quarantine

### 38.1 Quarantine triggers (fail-closed)

- Severe drift detected
- Calibration collapse (ECE spike)
- Unexplained performance degradation
- Data leakage discovery
- Security compromise of training data
- Unexplained output instability
- Provider corruption affecting features
- Adversarial attack confirmed

Quarantine → **ABSTAIN** all outputs; fall back to deterministic scorer.

---

## 39. Model Promotion

### 39.1 Stages

```text
RESEARCH → EXPERIMENTAL → REPLICATED → CALIBRATED → PAPER → PRODUCTION CANDIDATE
```

Each stage requires:
- Documented eval protocol
- Baseline comparison (§15)
- Search lineage (§16)
- Agent-16 replication (when runtime exists)
- Governance approval for PRODUCTION CANDIDATE+

**Never:** `TRAINED → PRODUCTION`

---

## 40. AI Governance

Coordinate Agent-04. Decisions requiring human/governance/epistemic/quant/verification/red-team:

| Decision | Required authority |
| --- | --- |
| New label definition for ML | Human + Agent-06 + Agent-12 |
| Model promotion to paper path | Agent-16 + Agent-12 + Human |
| Model promotion to production candidate | Full governance + Agent-19 |
| LLM provider addition | Human + security review |
| Online learning enablement | Human — **reject until Phase 4+** |
| Weight change to scorer | Human via improvement_proposal_v1 |
| Constitutional AI policy change | Agent-04 + Human |

Agent-13 does not create constitutional authority.

---

## 41. AGI/ACI Boundary

Long-term direction: Domain-General Cognitive Intelligence.

| Component | Classification |
| --- | --- |
| PERCEIVE (collectors) | **AVAILABLE NOW** |
| UNDERSTAND (deterministic engine) | **AVAILABLE NOW** |
| REMEMBER (knowledge store) | **RESEARCHABLE** |
| MODEL (learned world model) | **FUTURE** |
| REASON (multi-agent council) | **RESEARCHABLE** — bounded today |
| HYPOTHESIZE | **RESEARCHABLE** |
| EXPERIMENT | **AVAILABLE NOW** (strategy lab) |
| LEARN (safe offline) | **RESEARCHABLE** |
| SELF-CRITICIZE (panel/council) | **AVAILABLE NOW** — partial |
| PROMOTE/REJECT | **AVAILABLE NOW** — human-gated |

**No AGI claim without evidence.** Today's architecture is **narrow opportunity intelligence**, not domain-general cognition.

---

## 42. Minimum Viable AI

**Smallest AI/ML capability that genuinely improves AHOS** — empirically, not aspirationally.

| Capability | Class | Why |
| --- | --- | --- |
| Deterministic scorer + breakdown | **MUST_HAVE_FOR_LAUNCH** | Already core; beats unvalidated ML |
| Read-only calibration accrual | **MUST_HAVE_FOR_LAUNCH** | Makes intelligence measurable |
| Abstention contract (unified) | **MUST_HAVE_FOR_LAUNCH** | Correct "I don't know" |
| LLM council (advisory, offline-capable) | **SHOULD_HAVE** | Exists; downgrade-only |
| Cognitive panel | **SHOULD_HAVE** | Exists; deterministic |
| ModelInference + Registry schema (docs/contracts) | **MUST_HAVE_BEFORE_ANY_ML** | Gate for future models |
| Simple baselines (rule, logistic, shallow tree) | **SHOULD_HAVE** before any deep model | Agent-12+13 joint eval |
| Heuristic anomaly flags | **SHOULD_HAVE** | Exists partially |
| ML anomaly classifier | **LATER** | Needs labels |
| Embeddings / RAG | **LATER** | Not implemented |
| Deep learning | **RESEARCH_ONLY** | Complexity liability without edge proof |
| RL | **NOT JUSTIFIED** | Reward hacking risk |
| Online learning | **NOT JUSTIFIED** | Safety |
| Graph neural networks | **RESEARCH_ONLY** | Agent-09 coordination |
| Multi-LLM as independent verification | **NOT JUSTIFIED** | Correlated errors |

---

## 43. Launch Requirements

### 43.1 What AHOS needs to launch (AI/ML perspective)

1. **Keep deterministic intelligence primary** — no ML required for launch
2. **Accrue calibration pairs** — validate scorer before any ML competes with it
3. **Define ModelInference contract** — Phase 0 gate before trained models
4. **Preserve advisory-only LLM/council semantics** — no upgrade path past evidence
5. **Unified abstention** — INSUFFICIENT_DATA is success state early on

### 43.2 What AHOS may eventually need (cognitive platform)

- Model registry + promotion pipeline
- PIT ML dataset governance
- OOD + drift integrated serving
- Safe offline retrain loop
- RAG with provenance
- Graph AI research track
- World model with typed uncertainty
- Multi-agent independence matrix

**Do not block launch on Phase 5–7 items.**

---

## 44. Delivery Roadmap

```text
PHASE 0 — AI CONTRACTS              ← ModelInference, Registry schema, Abstention enum
PHASE 1 — MINIMUM AI INTELLIGENCE   ← Calibrate deterministic scorer; unify abstention
PHASE 2 — MODEL REGISTRY / EVAL     ← Baselines, lineage, replication hooks
PHASE 3 — CALIBRATED LEARNING       ← First classical ML if beats baselines on PIT data
PHASE 4 — CONTROLLED ADAPTATION     ← Drift response; offline retrain proposals
PHASE 5 — COGNITIVE MEMORY          ← Failure memory, hypothesis memory integration
PHASE 6 — MULTI-AGENT COGNITION      ← Independence matrix; structured council
PHASE 7 — DOMAIN-GENERAL RESEARCH   ← World model, RAG, graph AI — AGI/ACI track
```

**Parallelizable:**
- Phase 0 contracts ∥ calibration pair accrual (time-dependent)
- Phase 2 registry schema ∥ Agent-12 QuantExperiment bridge
- Phase 6 council hardening ∥ Phase 3 ML eval (if data ready)
- LLM research assist (org) ∥ AHOS deterministic path

**Not sequential gates** — but Phase 0 must precede any production ML.

---

## 45. Build → Integrate → Verify

| Capability | Build | Integrate | Independent Verify | Acceptance Gate | Blocker? |
| --- | --- | --- | --- | --- | --- |
| Deterministic scorer | DONE | Pipeline | Agent 16 replay | Parity tests | No |
| Score ledger | DONE | Orchestrator | Agent 16 append audit | Rows persist | No |
| Calibration harness | DONE | Ledger + outcomes | Agent 16 no-peek tests | joined_pairs ≥ MIN_N | **Yes** (data) |
| Cognitive panel | DONE | Authority downgrade | Agent 16 veto tests | Never upgrades | No |
| LiveCouncil | DONE | Optional injection | Agent 19 prompt injection | Advisory only | No |
| ModelInference contract | NOT STARTED | N/A | Agent 16 schema | Contract tests | **Yes** (before ML) |
| Model Registry | NOT STARTED | TCB + AHOS | Agent 16 integrity | No orphan models | **Yes** (before ML) |
| PIT ML datasets | NOT STARTED | Feature store | Agent 16 leakage fixtures | LK-ML audit pass | **Yes** |
| Baseline ML models | NOT STARTED | Eval harness | Agent 16 replicate | Beat rule baseline | No (launch) |
| OOD detection | NOT STARTED | Serving path | Agent 19 OOD spoof | ABSTAIN on OOD | No (launch) |
| Unified abstention | NOT STARTED | Scorer+council+ML | Agent 16 contract | Typed abstain reasons | Partial |
| RAG / embeddings | NOT STARTED | — | — | — | No (launch) |
| Online learning | FORBIDDEN | — | — | — | N/A |

---

## 46. Independent Verification

**Agent-13 analysis ≠ independent verification.**

| Verification | Verifier | Method |
| --- | --- | --- |
| Model reproducibility | Agent 16 | Re-run train+eval; hash compare |
| Dataset identity | Agent 16 | Manifest vs actual rows |
| Feature lineage / leakage | Agent 16 | LK-ML fixture injection |
| Calibration honesty | Agent 16 | Adversarial join order |
| LLM prompt injection | Agent 19 | Hostile token metadata |
| False confidence | Agent 19 | OOD + thin evidence packets |
| Feedback loop gaming | Agent 19 | Simulated attention bias |
| Registry integrity | Agent 16 | Promotion without stage skip |
| Baseline superiority claim | Agent 16 | Independent baseline re-run |

**Current status:** `INDEPENDENT_VERIFICATION_RUNTIME = NOT_IMPLEMENTED` — Agent 16/19 exist as `[PLANNED]` blueprint roles only; no verification mission evidence in repository.

---

## 47. Contradiction Register

| ID | Source | Conflict | Impact | Blocker? | Proposed resolution | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CR-13-01 | Agent 12 CR-01 | Scoring-science vs CMI vs ML feature ownership | Duplicate/conflicting model inputs | HIGH-RISK | CMI defines features; 12 validates; 13 trains only on approved feature sets | Human + 04 | UNRESOLVED |
| CR-13-02 | Agent 12 CR-02 | Feature cutoff ownership for ML | Leakage if wrong owner | HIGH-RISK | Joint InformationCutoff(T) policy | 12+09+07+13 | UNRESOLVED |
| CR-13-03 | `panel.py` vs marketing | "100 AI minds" vs deterministic lenses | User false confidence | IMPORTANT | Document as deterministic analysis | 13+17 | PROPOSED |
| CR-13-04 | LiveCouncil vs independence | Multi-LLM as "council" | Echo masquerading as consensus | HIGH-RISK | Independence matrix + ECHO_SUSPECTED gate | 13 | DOCUMENTED |
| CR-13-05 | Agent 10 vs 13 | ML suspicious flag vs SCAM verdict | Authority collapse | HIGH-RISK | ML emits ANOMALY_SCORE; 10 owns verdict | 10+13 | PROPOSED |
| CR-13-06 | Agent 11 vs 13 | Model confidence vs risk safety | False safety | HIGH-RISK | Separate uncertainty bundle; 11 interprets | 11+13 | DOCUMENTED |
| CR-13-07 | Agent 12 CR-09 | Calibration harness vs org TCB | Governance gap | IMPORTANT | MLCalibrationReport → TCB artifact | 12+13+05 | UNRESOLVED |
| CR-13-08 | AHOS docs vs code | Anomaly ML claims vs heuristics | Overstated capability | IMPORTANT | Align docs to heuristic reality | AHOS eng | UNRESOLVED |
| CR-13-09 | Agent 12 HD-Q06 | ML introduction timeline vs rule-only launch | Scope creep | IMPORTANT | Human decision — default rule-only launch | Human | UNRESOLVED |
| CR-13-10 | debate_council vs council_live | Two council patterns | Integration confusion | NON-BLOCKING | Deprecate template debate or wire to LLM | 13 | UNRESOLVED |
| CR-13-11 | Dual-19 | Plane A vs D agent IDs | Authorization mapping | HIGH-RISK | Agent 04 governance | 04 | UNRESOLVED |
| CR-13-12 | Agent 06 vs 05 | Methodology vs epistemic for ML promotion | Promotion blocked | NON-BLOCKING | MethodologyAssessment on ML studies | 06+05 | UNRESOLVED |

---

## 48. Human Decision Register

| ID | Decision | Why agent cannot decide |
| --- | --- | --- |
| HD-AI-01 | Whether launch remains rule-only or first ML model is in scope | Product/strategic scope |
| HD-AI-02 | Minimum calibration joined_pairs before any ML eval is credible | Risk appetite |
| HD-AI-03 | LLM provider allowlist for AHOS (Ollama-only vs cloud) | Security/cost/privacy |
| HD-AI-04 | Whether embeddings/RAG enters product roadmap Phase 2 vs 3 | Resource allocation |
| HD-AI-05 | Promotion of any ML model to paper-trading observation | Governance |
| HD-AI-06 | Unified vs separate Model Registry location (AHOS git vs org TCB) | Operational ownership |
| HD-AI-07 | Acceptable false-negative rate for rare-opportunity ML (class imbalance) | Product ethics/risk |

**Not inflated:** Contract field definitions, abstention enum, leakage taxonomy, and baseline requirements are Agent-13 delegable design work.

---

## 49. Anti-Loop / Stopping Condition

### DO NOW

1. Accept this document as Phase 0 AI/ML contract baseline
2. Preserve deterministic scorer as primary intelligence
3. Accrue calibration pairs (shared with Agent-12 — time-dependent)
4. Define ModelInference + Registry contracts before any ML code

### DO LATER

- Classical ML baselines (after labels)
- OOD serving integration
- RAG / embeddings
- Graph AI
- Multi-agent independence hardening

### BACKLOG (14 items)

1. ModelInference typed contract implementation
2. Model Registry schema + TCB bridge
3. Unified AbstentionRecord
4. ML leakage golden tests (LK-ML-01–10)
5. Baseline comparison harness (rule vs logistic vs shallow tree)
6. Independence matrix for council
7. LLM hallucination evidence-path linter
8. Feedback loop exposure logger
9. Quarantine automation hooks
10. MLCalibrationReport → org TCB artifact
11. debate_council deprecation decision
12. Anomaly heuristic baseline documentation
13. UncertaintyBundle decomposition
14. World model research charter

### RESEARCH ONLY

- Deep learning, GNN, RL, online learning, domain-general world model

### TRUE BLOCKERS

- 4 launch blockers (§50) — shared with quant/data; no additional AI-only blocker

### NON-BLOCKERS

- No ML pipeline (correct for launch)
- No embeddings/RAG
- Zero accepted strategies (scientific integrity)
- LLM council optional/offline-capable
- Baseline not propagated org-wide

**Stop condition met.**

---

## 50. Final Classification

| Area | Status |
| --- | --- |
| Agent-13 architecture document | `[DOCUMENTED]` |
| AHOS deterministic scoring | `[IMPLEMENTED]` `[TESTED]` |
| AHOS LLM council | `[IMPLEMENTED]` — advisory |
| AHOS cognitive panel | `[IMPLEMENTED]` — deterministic |
| AHOS calibration harness | `[IMPLEMENTED]` — measurement `[BLOCKED]` |
| AHOS ML training/inference | `[NONE]` |
| AHOS model registry | `[NONE]` |
| AHOS online learning | `[FORBIDDEN]` by design |
| Org ML runtime | `[NONE]` |
| Org epistemic ML types | `[PROPOSED]` |
| Independent verification | `[NOT IMPLEMENTED]` |
| Agent-13 role in registry | `[PLANNED]` |

---

## Model Output Contract (§8 — Design Only)

`[PROPOSED]` Typed contract — **not implemented**.

```text
ModelInference {
  model_id: str
  model_version: str
  input_dataset_id: str
  input_cutoff: ISO8601
  feature_versions: map[str, str]
  inference_timestamp: ISO8601
  prediction: Any
  probability: float | null
  uncertainty: UncertaintyBundle
  calibration_status: CALIBRATED | UNCALIBRATED | INSUFFICIENT_DATA
  applicability_domain: str
  known_limitations: list[str]
  ood_status: IN_DOMAIN | EDGE_OF_DOMAIN | OUT_OF_DOMAIN | UNKNOWN_DOMAIN
  drift_status: STABLE | WARNING | DRIFT_DETECTED
  provenance: ProvenanceRecord
  experiment_id: str | null
  abstention: AbstentionRecord | null
}
```

---

## Organizational Change Propagation

| Discovery | Affected Domain | Affected Agent | Required Follow-up | Proposed Mission |
| --- | --- | --- | --- | --- |
| No ModelInference contract blocks safe ML | AI governance | 13, 16 | Implement contract + tests | Phase 0 AI contracts mission |
| Calibration 0 pairs blocks all ML validation | Quant + AI | 12, 13 | Accrue local pairs | Shared calibration accrual |
| ML must not emit SCAM/SAFE | Security boundary | 10, 13 | Confirm ANOMALY vs VERDICT split | Agent-10 boundary amendment |
| Feature cutoff joint policy needed | Data + Quant + ML | 07, 09, 12, 13 | InformationCutoff(T) doc | Joint PIT mission |
| QuantExperiment bridge missing | Org epistemic | 05, 12, 13 | Schema design | TCB bridge mission |

```text
COMMUNICATION_CAPABILITY_GAP = YES
```

No evidence that affected agents received these proposals. Master Orchestrator propagation required.

---

## Appendix A — Class Imbalance (§13)

Crypto opportunity detection: extreme rarity of true positives.

| Approach | When |
| --- | --- |
| PR-AUC primary | Imbalanced detection tasks |
| Precision/recall at operating point | Cost-sensitive deployment |
| Cost-sensitive learning | When FN/FP costs asymmetric |
| Focal loss | Research — not default |
| Anomaly detection framing | Unlabeled majority |
| PU learning | If only positive labels reliable |

**Never optimize accuracy alone.** Report calibration on rare class. Agent-11 defines cost matrix; Agent-13 implements metrics.

---

## Appendix B — Baselines (§15)

Every ML model must beat:

1. **Rule-based baseline** — current OpportunityScorer
2. **Simple statistical** — logistic regression on same PIT features
3. **Naive baseline** — majority class / random stratified
4. **Shallow tree** — max depth 3–5, where appropriate

If deep model does not beat logistic on independent holdout: **complexity is liability**.

---

## Appendix C — Model Selection Bias (§16)

Preserve `MODEL_SEARCH_HISTORY`:
- Architectures tried
- Seeds, hyperparameters
- Features added/dropped
- Datasets and label versions
- Test-set access log

Coordinate Agent-12 research-lineage architecture. Locked evaluation sets — `[LATER]`.

Hyperparameter governance: search budgets, pre-registered cells, early stopping with frozen validation fold, reproducible seeds, experiment IDs.

---

## Appendix D — Model Ensembles (§37)

Bagging, boosting, stacking, voting — allowed in research with **error correlation audit**. Ensemble consensus ≠ independent evidence unless independence matrix (§19) shows low coupling.

---

```text
MISSION_STATUS = AI_ML_INTELLIGENCE_ARCHITECTURE_ANALYSIS_COMPLETE_WITH_GAPS
AGENT_ID = AGENT-13
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
INDEPENDENT_VERIFICATION = NOT_IMPLEMENTED (Agent 16/19 planned roles only; no verification mission evidence)
LAUNCH_BLOCKERS = 4 (shared with Agent-12: calibration unmeasured; PIT token universe; org↔AHOS epistemic bridge; dual paper/backtest ledger — no additional AI-only blocker)
NON_BLOCKING_BACKLOG = 14
CAPABILITY_GAPS = YES (live DB, soak state, LLM live behavior, embedding/RAG infra, production label cohort)
HUMAN_DECISIONS_REQUIRED = HD-AI-01 through HD-AI-07 (see §48)
UNVERIFIED_CLAIMS = Live LLM council accuracy; post-deployment scorer calibration; ML generalization on token discovery; anomaly heuristic precision; cross-chain model transfer; any AGI/ACI readiness
NEW_CROSS_AGENT_DISCOVERIES = 5 (see Organizational Change Propagation)
COMMUNICATION_CAPABILITY_GAPS = YES (no runtime to propagate to Agents 05/07/10/12/16)
RECOMMENDED_NEXT_MISSION = STATE ONLY — Phase 0 AI Contracts: define ModelInference + Model Registry schema + AbstentionRecord in agent-org docs/contracts; DO NOT EXECUTE
```
