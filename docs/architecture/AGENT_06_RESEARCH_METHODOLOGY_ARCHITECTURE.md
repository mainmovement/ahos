# Agent Organization Research Methodology Architecture

```text
DOCUMENT_ID      = AGENT_06_RESEARCH_METHODOLOGY_ARCHITECTURE
MISSION_ID       = TASK-20260914-006
VERSION          = 0.1.0
STATUS           = PROPOSED / READ_ONLY_METHODOLOGY_ARCHITECTURE
AUTHORITY        = NONE CREATED
RUNTIME_EFFECT   = NONE
AHOS_EFFECT      = NONE
AGENT_ID         = AGENT-06 (agent.org.06-research-methodology — documentary)
DIRECT_COMMANDER = MASTER ORCHESTRATOR
PARENT           = MASTER ORCHESTRATOR
```

This document is a **design and architecture artifact** produced by AGENT-06 under explicit activation for TASK-20260914-006. It does not implement a research engine, adopt governance, grant authority, modify AHOS, or promote knowledge. Facts cite repository evidence with explicit classification labels (`[IMPLEMENTED]`, `[DOCUMENTED]`, `[PROPOSED]`, `[UNKNOWN]`). Architectural recommendations are labeled `[PROPOSED]`.

**Critical honesty constraint:**

```text
METHODOLOGY DOCUMENTATION ≠ METHODOLOGY ENFORCEMENT
RESEARCH QUALITY ≠ EPISTEMIC TRUTH
RESEARCH QUALITY ≠ GOVERNANCE AUTHORITY
SECURITY ≠ METHODOLOGICAL VALIDITY
```

---

## 1. Executive Summary

`[VERIFIED]` The AHOS Agent Organization contains a **partial research methodology foundation** in Slice 2B (`agent_org/epistemic.py`, `[IMPLEMENTED]` `[TESTED]`): typed `ResearchMission`, `ExperimentPlan`, `ExperimentRun`, `Hypothesis` (with mandatory `falsification_criteria`), and related epistemic objects. These encode **structural requirements** for bounded research missions and experiment design but do **not** enforce statistical, causal, ML, or crypto-market methodology.

`[VERIFIED]` A Class A deterministic research agent (`RESEARCH_ANALYST_AGENT`, `research_worker/analyst.py`, `[IMPLEMENTED]`) applies minimal methodological rules: label discipline, explicit contradiction detection via `NOT` prefix pairs, descriptive experiment proposal when observations are missing, and refusal to emit verification or promotion labels. This is **not** a general research methodology engine.

`[VERIFIED]` Governance and epistemic documentation (Constitution, Evidence Protocol, AGENT-05 Epistemic Architecture) define vocabulary for questions, hypotheses, experiments, and evidence separation but do **not** enforce pre-registration, bias controls, reproducibility levels, or confirmatory/exploratory labeling in chat agents (`[DOCUMENTED]` only).

**Central architectural question:** How should the organization investigate questions, formulate hypotheses, design experiments, collect evidence, evaluate competing explanations, control bias, reproduce results, analyze failures, and determine whether a research result is sufficiently trustworthy for **epistemic review** (Agent 05's domain)?

**Primary methodological objective:** prevent **methodology collapse** — where desired outcomes, exploratory pattern-finding, correlation, model performance, or narrative plausibility silently become validated causal knowledge or decision-grade conclusions.

**Current methodology posture:** `[PARTIALLY_VERIFIED]` — strong typed mission/experiment contracts and label discipline in the research worker path; weak enforcement of study design quality, bias mitigation, pre-registration, negative-result retention, and multi-agent independence at the Cursor Control-Plane layer.

**Dual-19 status:** `[VERIFIED]` `[CONFLICT / UNRESOLVED]` — Plane A (`agent.*`) and Plane D (`agent.org.NN-*`) remain separate taxonomies. This document analyzes methodology implications only; it does not merge them.

**Agent One:** `NOT_IMPLEMENTED / FUTURE_NON_AUTHORITY_ROOT` — must never become methodological authority or epistemic root.

**Boundary with Agent 05:** Agent 06 owns **how research was conducted and how strong the method is**. Agent 05 owns **what epistemic status a result should receive**. Methodological strength does not automatically confer epistemic promotion eligibility.

---

## 2. Agent-06 Identity

| Field | Value |
| --- | --- |
| `AGENT_ID` (mission) | `AGENT-06` |
| Blueprint ID | `agent.org.06-research-methodology` |
| Provisional name | Research Methodology Architect |
| Role | Design research methodology architecture; study design, bias control, reproducibility |
| Authority class | `NONE` (design mission only) |
| Capabilities exercised | READ, ANALYZE, PROPOSE (documentation) |
| Forbidden | VERIFY (own conclusions), PROMOTE, EXECUTE, MODIFY runtime, ACTIVATE other agents, grant authority based on research quality |
| Supervisor | MASTER ORCHESTRATOR → human operator (MEHRDAD) |
| Source of truth | **Not** AGENT-06. Repository L0/L1 + governance L2/L3 only. |

AGENT-06 is **not** Agent One, **not** the Master Orchestrator, **not** an epistemic authority, **not** a verifier of its own deliverables, and **not** a source of methodological truth by title.

---

## 3. Command Chain

```text
MEHRDAD
  → MASTER ORCHESTRATOR
    → AGENT-06 (this mission)
```

- Direct commander: **MASTER ORCHESTRATOR**
- Parent: **MASTER ORCHESTRATOR**
- Reporting line: **MASTER ORCHESTRATOR**
- Agent-03, Agent-04, Agent-05 are **peer specialists**, not commanders.
- No subordinate agents created or activated by this mission.
- No modification of reporting line.

---

## 4. Lifecycle

### 4.1 Activation rule

Creating, registering, or naming an agent does **not** activate it. TASK-20260914-006 is the explicit activation command for this mission.

### 4.2 Mission lifecycle

```text
REGISTERED / IDLE / DORMANT
  → [explicit activation: TASK-20260914-006]
  → RUNNING (methodology architecture analysis)
  → COMPLETED (this deliverable)
  → IDLE / DORMANT / WAITING_FOR_NEW_COMMAND
```

### 4.3 Terminal states

Supported: `COMPLETED`, `FAILED`, `TIMEOUT`, `CANCELLED`, `BLOCKED`, `SUSPENDED`, `QUARANTINED`.

After termination: `LIFECYCLE_STATUS = IDLE / DORMANT / WAITING_FOR_NEW_COMMAND`.

Recommendations in this document are **not** commands. AGENT-06 does not auto-continue to Agent 07 or any future mission.

---

## 5. Research Principles

The mission supplied 20 core principles. Each is evaluated for applicability and limitations.

| # | Principle | Applicability | Limitation / nuance |
| --- | --- | --- | --- |
| 1 | Research begins with a clearly defined question | **Required** | Questions can be ill-posed; refinement is iterative |
| 2 | Question must differ from desired answer | **Required** | Motivated reasoning often hides desired outcomes in framing |
| 3 | Hypotheses must be explicit | **Required** | `[IMPLEMENTED]` falsification criteria required on `Hypothesis` in Slice 2B |
| 4 | Competing hypotheses where reasonable | **Required** | Not all hypotheses are equally plausible; document why alternatives were excluded |
| 5 | Assumptions must be explicit | **Required** | `[PROPOSED]` no assumption registry in code today |
| 6 | Evidence must be traceable | **Required** | `[IMPLEMENTED]` provenance on artifacts; chat agents often lack TCB binding |
| 7 | Methods reproducible where feasible | **Conditional** | Not all domains permit Level 4–5 reproducibility; label level achieved |
| 8 | Negative results retained | **Required** | `[PROPOSED]` no enforced failure archive in org runtime |
| 9 | Failed experiments are information | **Required** | `[IMPLEMENTED]` `ExperimentRun` supports `failure_class` |
| 10 | Correlation ≠ causation | **Required** | Observational crypto/market research is predominantly correlational |
| 11 | Prediction accuracy ≠ causal explanation | **Required** | Especially critical for ML and backtests |
| 12 | Statistical significance ≠ practical significance | **Required** | Large samples can detect trivial effects |
| 13 | Lack of significance ≠ no effect | **Required** | Underpowered studies cannot establish absence |
| 14 | Sample selection can distort conclusions | **Required** | Survivorship and convenience sampling dominate crypto datasets |
| 15 | Data leakage invalidates results | **Required** | First-class risk for ML and backtests |
| 16 | Multiple testing creates false discoveries | **Required** | Requires pre-specified primary outcomes or correction |
| 17 | Researcher/agent degrees of freedom create bias | **Required** | Applies to LLM agents (prompt, tool, stopping choices) |
| 18 | Post-hoc explanations ≠ pre-registered hypotheses | **Required** | HARKing is a primary integrity failure mode |
| 19 | Conclusions scoped to tested conditions | **Required** | Generalization requires explicit justification |
| 20 | Methodology must preserve uncertainty | **Required** | `[IMPLEMENTED]` research worker emits `uncertainty_labels` |

**Forbidden methodological equalities:**

```text
DESIRED OUTCOME     ≠ RESEARCH QUESTION
EXPLORATORY FINDING ≠ CONFIRMATORY PROOF
CORRELATION         ≠ CAUSATION
BACKTEST            ≠ LIVE PROOF
SIMULATION          ≠ REAL-WORLD EXECUTION
MODEL PERFORMANCE   ≠ MECHANISTIC TRUTH
P-VALUE             ≠ TRUTH PROBABILITY
HIGH CONFIDENCE     ≠ CAUSAL TRUTH
REPLICATION BY SAME ACTOR ≠ INDEPENDENT REPLICATION
METHODOLOGY QUALITY ≠ EPISTEMIC PROMOTION
```

---

## 6. Research Question Design

### 6.1 Formal research-question model `[PROPOSED]`

A research question is a bounded inquiry artifact, distinct from a decision objective or desired outcome.

| Field | Meaning | Required |
| --- | --- | --- |
| `question_id` | Stable identifier | Yes |
| `objective` | What the study seeks to learn (not what decision-maker wants) | Yes |
| `scope` | Temporal, geographic, asset, and system boundaries | Yes |
| `domain` | e.g., on-chain, market microstructure, agent behavior | Yes |
| `time_horizon` | Observation window and decision relevance window | Yes |
| `population` | Entities the conclusion may generalize to | Yes |
| `unit_of_analysis` | Token, address, transaction, agent run, etc. | Yes |
| `variables` | Independent, dependent, confounders (named) | Yes |
| `constraints` | Legal, technical, data-access, safety | Yes |
| `assumptions` | Explicit L6 assumptions | Yes |
| `decision_relevance` | Which decision (if any) this informs — not the decision itself | Optional |
| `falsifiability` | What observation would refute a positive answer | Yes |
| `measurable_outcomes` | Primary and secondary metrics | Yes |
| `question_type` | Descriptive / comparative / predictive / causal / mechanistic | Yes |
| `encoding_check` | Reviewer attestation that question does not encode desired answer | `[PROPOSED]` |

**Slice 2B mapping:** `ResearchMission.question`, `unknowns`, `constraints`, `required_evidence`, `success_criteria`, `failure_criteria` partially implement this model (`[IMPLEMENTED]`). Gaps: no structured population/unit-of-analysis fields, no explicit decision-relevance separation, no encoding-check workflow.

### 6.2 Distinguishing four concepts

| Concept | Definition | Example (token price rise) |
| --- | --- | --- |
| **Research question** | Testable inquiry about reality | "What factors co-occurred with the price rise in window W?" |
| **Desired outcome** | Preference of stakeholder | "We want to prove organic demand drove the rise" |
| **Hypothesis** | Explicit testable proposition | "H1: Coordinated promotion accounts for >50% of volume spike" |
| **Decision objective** | Action to be taken if evidence sufficient | "Decide whether to flag token for manipulation review" |

A research question must **not** secretly encode the desired answer (e.g., "Why is organic demand the cause of the rise?" presumes causation and desired explanation).

### 6.3 Question quality gates `[PROPOSED]`

- **Clarity:** Can two independent researchers parse the same question?
- **Boundedness:** Are scope and population explicit?
- **Falsifiability:** Is there a conceivable disconfirming observation?
- **Feasibility:** Can required evidence be obtained within budget?
- **Neutrality:** Does framing avoid embedding conclusion?

---

## 7. Hypothesis Design

### 7.1 Hypothesis taxonomy

| Type | Definition | Falsification example |
| --- | --- | --- |
| **Null (H0)** | Default/no-effect or no-difference | Effect size within measurement noise |
| **Alternative (H1)** | Effect or difference of interest | Observed effect beyond threshold |
| **Competing (H2…Hn)** | Plausible alternative explanations | Evidence discriminates against H2 |
| **Directional** | Predicts sign of effect | Opposite sign observed |
| **Non-directional** | Predicts difference without sign | No difference beyond threshold |
| **Causal** | X causes Y under stated conditions | Natural experiment contradicts; confounding explains |
| **Predictive** | Y predictable from X without mechanism | Out-of-sample prediction fails |
| **Mechanistic** | Process P links X to Y | Intermediate step absent |

**Rule:** `Hypothesis ≠ Fact` — even `SUPPORTED` or `TESTING` states in Slice 2B do not equate to knowledge (`[IMPLEMENTED]` lifecycle; epistemic promotion is separate).

### 7.2 Required hypothesis fields `[PROPOSED]` (extends Slice 2B)

Slice 2B `Hypothesis` requires: `statement`, `falsification_criteria`, `supporting_claim_ids` (`[IMPLEMENTED]`).

Recommended additions:

| Field | Purpose |
| --- | --- |
| `hypothesis_class` | null / alternative / competing / exploratory |
| `causal_claim` | boolean — triggers causal inference checklist |
| `assumptions` | Explicit L6 list |
| `evidence_threshold` | What evidence would support/refute |
| `expected_observations` | If true, what should be seen |
| `disconfirming_observations` | If false, what should be seen |
| `primary_outcome` | For confirmatory studies |
| `pre_registered` | boolean + plan hash reference |

### 7.3 Falsification criteria

Falsification criteria must be **observable and prior** to seeing results. Criteria like "if wrong, we'd notice eventually" are insufficient.

Example (competing hypotheses for token price rise):

```text
H1 (organic demand): Unique buyer count rises before price; no wash-trade signature
H2 (wash trading): Volume rises without unique buyer growth; round-trip address patterns
H3 (whale accumulation): Top-holder concentration increases before price
H4 (market-wide beta): Correlated assets move similarly without token-specific signal
H5 (data artifact): Price spike aligns with exchange outage or oracle lag
```

---

## 8. Competing Hypotheses

### 8.1 Requirement

Where reasonable alternatives exist, researchers must **enumerate and discriminate** among them — not adopt the first plausible explanation.

**Methodology rule:** Absence of evidence for H2 is not evidence for H1 unless H2 was actively tested or ruled out by design.

### 8.2 Comparison methods `[PROPOSED]`

| Method | Use |
| --- | --- |
| **Evidence discrimination** | Identify observations that support H1 and contradict H2 |
| **Bayesian / likelihood framing** | Compare relative support (not mandatory framework) |
| **Decision tree of tests** | Sequence experiments to maximally separate hypotheses |
| **Contradiction detection** | `[IMPLEMENTED]` `ContradictionCase`; worker `NOT` prefix heuristic |
| **Ablation / negative controls** | Remove suspected cause; outcome should change if causal |

### 8.3 Documentation requirement

Research plans must include a **competing-hypothesis section** with:

- List of alternatives considered
- Reason alternatives were included or excluded
- Discriminating evidence or experiments planned
- Residual ambiguity if discrimination incomplete

---

## 9. Research Plan

### 9.1 Standard research plan template `[PROPOSED]`

Every non-trivial research effort should produce a plan artifact before confirmatory execution:

| Section | Content |
| --- | --- |
| Research question | Formal question model (§6) |
| Motivation | Why this question matters (not desired answer) |
| Scope | Boundaries |
| Hypotheses | H0, H1, H2… with falsification criteria |
| Competing hypotheses | §8 |
| Assumptions | Explicit L6 |
| Required evidence | Types, sources, freshness |
| Data sources | Provenance, access method, limitations |
| Methodology | Study type (§10) |
| Experiment design | Controls, splits, stopping rules |
| Analysis plan | Primary outcome, statistical tests, multiplicity handling |
| Success / failure criteria | Linked to mission fields |
| Stopping conditions | §25 |
| Expected limitations | Known blind spots |
| Reproducibility requirements | Target level (§19) |
| Reporting structure | Deliverables, negative results |
| Research mode | EXPLORATORY or CONFIRMATORY (§24) |
| Pre-registration reference | If confirmatory (§23) |

**Slice 2B mapping:** `ResearchMission` + `ExperimentPlan` cover subsets (`[IMPLEMENTED]`). No unified plan document type or pre-registration hash in code.

### 9.2 Plan review gate `[PROPOSED]`

Confirmatory research should not execute until **method review** passes (§31). Exploratory research may proceed with lighter plan but must be labeled.

---

## 10. Experiment Design

### 10.1 Study types

| Type | Definition | Legitimate conclusions | Org status |
| --- | --- | --- | --- |
| **Controlled experiment** | Randomized or matched manipulation | Causal claims (with assumptions) | `[PROPOSED]` |
| **Observational study** | No manipulation; observe co-variation | Associative; causal requires extra methods | `[PROPOSED]` |
| **Natural experiment** | Exogenous shock creates quasi-random variation | Causal (local) if assumptions hold | `[PROPOSED]` |
| **Simulation** | Model-generated data | Model behavior only; not reality proof | `[DOCUMENTED]` SIMULATION ≠ EXECUTION |
| **Backtest** | Historical strategy replay | Historical fit only; not live proof | `[DOCUMENTED]` |
| **A/B test** | Randomized comparison | Causal for tested intervention | `[PROPOSED]` |
| **Longitudinal** | Same units over time | Temporal patterns; watch for drift | `[PROPOSED]` |
| **Cross-sectional** | Snapshot across units | Associations; confounding risk | `[PROPOSED]` |
| **Comparative** | Compare groups or methods | Relative performance under stated conditions | `[PROPOSED]` |

### 10.2 Critical distinctions

```text
SIMULATION        ≠ REAL-WORLD OBSERVATION
REAL-WORLD OBS    ≠ REAL-WORLD EXECUTION (trading, deployment)
BACKTEST          ≠ LIVE PROOF
IN-SAMPLE FIT     ≠ OUT-OF-SAMPLE GENERALIZATION
```

The research worker proposes **descriptive inspection only** — no external execution (`[IMPLEMENTED]` `execution_requested: False`).

### 10.3 Experiment artifact model (Slice 2B)

`ExperimentPlan`: `method`, `preconditions`, `expected_observations`, `reproducibility_requirements` (`[IMPLEMENTED]`).

`ExperimentRun`: `outcome`, `failure_class` (`[IMPLEMENTED]`).

Gaps: no train/test split metadata, no control group reference, no randomization record, no study-type enum.

---

## 11. Causal Inference

### 11.1 Methodology for correlation vs causation

Causal claims require **explicit causal inference design**, not correlation alone.

| Tool / concept | Role |
| --- | --- |
| **Confounders** | Common causes of X and Y — must be measured or blocked |
| **Mediators** | X → M → Y; intervening mechanism |
| **Colliders** | Conditioning opens spurious paths |
| **Selection bias** | Sample not representative of target population |
| **Reverse causality** | Y causes X, not X causes Y |
| **Temporal precedence** | Cause must precede effect in time |
| **Counterfactual reasoning** | What would Y be if X had differed? |
| **Causal graphs (DAGs)** | `[PROPOSED]` document assumed structure |
| **Natural experiments** | Exogenous variation |
| **Randomized experiments** | Gold standard when feasible |

### 11.2 Causal claim ladder `[PROPOSED]`

| Level | Claim type | Minimum requirement |
| --- | --- | --- |
| L0 | Descriptive | Observation only |
| L1 | Associative | Controlled comparison or regression with confounders named |
| L2 | Predictive | Out-of-sample prediction under fixed protocol |
| L3 | Quasi-causal | Natural experiment + sensitivity analysis |
| L4 | Causal (interventional) | Randomized or validated instrumental design |

Epistemic promotion of causal knowledge (Agent 05) should require explicit causal ladder level ≥ declared minimum.

### 11.3 Crypto-specific causal caution

Market manipulation, regime change, and latent liquidity conditions make naive causal claims especially fragile (§18).

---

## 12. Observational Research

When controlled experiments are impossible (most crypto/market intelligence):

### 12.1 Required documentation

- Confounding variables named
- Selection mechanism for sample
- Missing data pattern
- Survivorship handling
- Measurement error sources
- Temporal drift / regime labels
- Hidden variable acknowledgment

### 12.2 Legitimate conclusions from observational evidence

| Allowed | Not allowed without extra design |
| --- | --- |
| "X and Y co-occur in sample S under conditions C" | "X causes Y" |
| "H2 is less consistent with data than H1" | "H1 is proven" |
| "Effect estimate Ê with stated assumptions" | "Effect is practically significant" |
| "Prediction fails out-of-sample" | "No effect exists" (underpowered) |

### 12.3 Mitigation strategies `[PROPOSED]`

- Propensity scoring / matching (when assumptions stated)
- Difference-in-differences (with parallel trends check)
- Instrumental variables (with validity argument)
- Sensitivity analysis for unmeasured confounding
- Pre-specified robustness checks

---

## 13. Data Collection

### 13.1 Data collection requirements `[PROPOSED]`

| Requirement | Purpose | Org status |
| --- | --- | --- |
| Source provenance | Trace origin | `[IMPLEMENTED]` `Source`, evidence provenance |
| Acquisition timestamp | When data was retrieved | `[IMPLEMENTED]` `retrieval_timestamp` on Evidence |
| Event timestamp | When event occurred | `[IMPLEMENTED]` `observation_timestamp` |
| Sampling method | How units selected | `[PROPOSED]` |
| Population definition | Generalization target | `[PROPOSED]` |
| Inclusion / exclusion criteria | Reproducible sample | `[PROPOSED]` |
| Missing data handling | Document imputation or exclusion | `[PROPOSED]` |
| Duplicate handling | Dedup rules | `[PROPOSED]` |
| Corrupted data policy | Quarantine vs repair | `[PROPOSED]` |
| Outlier policy | Pre-specified vs post-hoc | `[PROPOSED]` |
| Schema / version | Data contract | `[PROPOSED]` |
| Transformation history | Lineage of derived features | `[PROPOSED]` |
| Raw evidence preservation | Immutable raw where feasible | `[PROPOSED]` |

**Principle:** Preserve raw evidence where appropriate; transformations are claims requiring their own warrants.

---

## 14. Data Leakage

Data leakage is a **first-class research risk** — especially for ML, backtests, and time-series crypto research.

### 14.1 Leakage types

| Type | Description | Control |
| --- | --- | --- |
| **Future information in past analysis** | Look-ahead bias | Temporal splits; point-in-time features |
| **Target leakage** | Label derived from features | Separate label generation pipeline |
| **Train/test contamination** | Test data influences training | Strict split discipline |
| **Survivorship leakage** | Universe conditioned on future survival | Point-in-time universe |
| **Feature leakage** | Post-outcome data in features | Feature timestamp audit |
| **Duplicate observations** | Same event counted multiple times | Dedup + cluster-aware CV |
| **Provider disagreement leakage** | Choosing provider after seeing outcome | Pre-specify provider hierarchy |

### 14.2 Leakage checklist `[PROPOSED]` (required for ML/backtest plans)

- [ ] Features available at decision time T for prediction at T
- [ ] Label defined without future feature information
- [ ] Train/val/test splits respect time ordering
- [ ] Hyperparameter tuning uses validation only
- [ ] Final test set touched once
- [ ] Universe includes delisted/failed assets where relevant
- [ ] No post-outcome filtering

**Org status:** `[PROPOSED]` — not enforced in `ExperimentPlan` or research worker.

---

## 15. Sampling Bias

### 15.1 Bias catalog (methodological)

| Bias | Description | Mitigation |
| --- | --- | --- |
| **Selection bias** | Non-random sample | Define sampling frame; weighting |
| **Convenience sampling** | Easy data ≠ target population | Document limits; avoid over-generalization |
| **Survivorship bias** | Only survivors observed | Include failures, delists, rugs |
| **Publication bias** | Positive results over-reported | Mandate negative result registry |
| **Winner's curse** | Extreme performers regress | Holdout validation; shrinkage |
| **MNAR missing data** | Missingness depends on unobserved value | Sensitivity analysis |
| **Non-response** | Subset responds | Compare responders vs non-responders |
| **Dataset construction bias** | Cleaning choices encode outcome | Pre-specify cleaning |

### 15.2 Generalization statement `[PROPOSED]`

Every research report must state:

```text
POPULATION STUDIED: ...
POPULATION CONCLUSION MAY GENERALIZE TO: ...
POPULATION CONCLUSION MAY NOT GENERALIZE TO: ...
```

---

## 16. Statistical Reasoning

This architecture does **not** prescribe a single statistical framework. It requires **explicit reasoning** about:

| Dimension | Requirement |
| --- | --- |
| Effect size | Report magnitude, not only significance |
| Uncertainty intervals | Prefer intervals over point estimates |
| Variance | Document instability |
| Sample size | Justify power or label underpowered |
| Statistical significance | Not truth probability |
| Practical significance | Domain-specific thresholds |
| Multiple comparisons | Pre-specify primary; correct or preregister secondary |
| False discovery | Control FDR or family-wise error where many tests |
| Statistical power | Report for null results |
| Calibration | For probabilistic predictions |
| Robustness | Sensitivity to assumptions |

**Forbidden:**

```text
P-VALUE = TRUTH PROBABILITY
HIGH CONFIDENCE = CAUSAL TRUTH
NON-SIGNIFICANT = NO EFFECT (without power analysis)
```

---

## 17. Machine Learning Research

### 17.1 ML methodology requirements `[PROPOSED]`

| Control | Requirement |
| --- | --- |
| Train/validation/test separation | Strict; temporal for time series |
| Temporal splits | Mandatory for sequential crypto data |
| Cross-validation | Nested if hyperparameter tuning |
| Leakage controls | §14 checklist |
| Baseline models | Simple baselines mandatory (random, naive, linear) |
| Ablation | Remove components to test claims |
| Hyperparameter selection | Validation set only |
| Model drift | Monitor post-deployment (future) |
| Calibration | Reliability diagrams for probabilistic outputs |
| Out-of-distribution behavior | Test on held-out regimes |
| Reproducibility | Seeds, data snapshots, environment spec |
| Benchmark contamination | Do not tune on test benchmarks |

**Principle:** `MODEL PERFORMANCE ≠ EXPLANATION TRUTH` — a high AUC does not validate a mechanistic hypothesis.

### 17.2 Reporting minimum `[PROPOSED]`

- Data split diagram
- Baseline comparison table
- Primary metric (pre-specified)
- Confidence intervals or bootstrap
- Failure cases / error analysis
- Leakage attestation

---

## 18. Crypto / Market Research

Methodology only — **no AHOS modification, no live credentials, no trading**.

### 18.1 Domain-specific risks

| Risk | Methodological response |
| --- | --- |
| Market regime changes | Label regimes; test across regimes |
| Token lifecycle | Include pre-launch, launch, maturity, decline |
| Liquidity changes | Normalize by depth; flag illiquid periods |
| Manipulation / wash trading | Competing hypothesis H2; on-chain heuristics |
| Fake volume | Cross-exchange comparison; unique participant metrics |
| Address clustering | Document clustering assumptions |
| Survivorship bias | Include delisted tokens in historical universe |
| Rug pulls | Failure class in outcome taxonomy |
| Oracle / data quality | Provider disagreement protocol |
| Latency | Timestamp alignment rules |
| Chain reorganizations | Reorg-aware confirmation depth |
| Provider disagreement | Pre-specified reconciliation hierarchy |
| Historical data gaps | Missingness model; no silent interpolation |

### 18.2 Timestamp alignment `[PROPOSED]`

All multi-source crypto research must document:

- Clock source (block time vs ingestion time)
- Alignment window (e.g., nearest prior block)
- Handling of delayed indexing

### 18.3 Manipulation-aware research

Price or volume anomalies require **competing hypotheses** (§8) before narrative assignment. Methodology must not default to "organic" or "manipulation" without discrimination tests.

---

## 19. Reproducibility

### 19.1 Reproducibility levels (evaluated scale)

| Level | Name | Requirement | Appropriate for |
| --- | --- | --- | --- |
| **0** | Narrative-only | Text description | Brainstorming only |
| **1** | Source-identifiable | Sources named with locators | Early exploration |
| **2** | Data-reconstructable | Data + schema sufficient to rebuild dataset | Most observational studies |
| **3** | Method-replayable | Code/scripts + data → same analysis | ML/backtests |
| **4** | Environment-reproducible | Pinned deps, seeds, container spec | High-stakes confirmatory |
| **5** | Independently replicated | Different team/process confirms | Rare; gold standard |

**Evaluation:** This scale is **appropriate** with the caveat that not every question requires Level 5. Research plans must declare **target level** and **achieved level** honestly.

**Slice 2B:** `ExperimentPlan.reproducibility_requirements` tuple (`[IMPLEMENTED]`) — free-text only, no level enum.

### 19.2 Honesty rule

Claiming Level 3 without archived analysis code is a methodology integrity violation.

---

## 20. Replication

### 20.1 Terminology

| Term | Meaning |
| --- | --- |
| **Repeatability** | Same team, same setup → similar results |
| **Reproducibility** | Different team, same data + method → similar results |
| **Replicability** | New data collection, same method → consistent findings |
| **Independent confirmation** | Distinct principals, sources, methods → convergent result |

### 20.2 When replication is required `[PROPOSED]`

- Confirmatory claims with decision impact
- Surprising or high-magnitude effects
- Single-source crypto/market claims
- ML results near baseline
- Any claim proposed for epistemic promotion at high assurance

### 20.3 False independence

Independent replication must **not**:

- Reuse the same contaminated source without audit
- Share the same LLM prompt and context (correlated errors)
- Be performed by the same principal with a different label

Aligns with Agent 05 Independence Matrix (`[DOCUMENTED]` in AGENT-05 architecture).

### 20.4 Replication sufficient for trust `[PROPOSED]`

A conclusion may be labeled **methodologically replicated** when:

1. Pre-registered plan matched (or deviations documented)
2. Independent principal executed replication
3. Primary outcome directionally consistent within pre-specified tolerance
4. No unresolved leakage or confounding flagged in either study

Epistemic promotion remains Agent 05 + governance gates.

---

## 21. Negative Results

### 21.1 Principle

> A system that remembers only successful experiments will systematically corrupt its own learning.

### 21.2 Required handling `[PROPOSED]`

| Result type | Handling |
| --- | --- |
| Failed experiment | `ExperimentRun` with `failure_class`; retain in store |
| Null result | Report effect size + CI; power statement |
| Contradictory finding | `ContradictionCase`; do not delete prior |
| Inconclusive study | Terminal state INCONCLUSIVE on hypothesis |
| Failed prediction | Refute or mark INCONCLUSIVE |
| Failed replication | Publish failure; downgrade confidence |

**Org status:** `[IMPLEMENTED]` terminal states exist; `[PROPOSED]` no org-wide negative-result registry or search index.

### 21.3 Failure retention architecture `[PROPOSED]`

- Immutable experiment run records
- Failure taxonomy (§37)
- Periodic audit: "missing expected runs" detection
- No deletion of failed runs from TCB store

---

## 22. Research Integrity

Safeguards against integrity failures:

| Failure mode | Detection | Mitigation |
| --- | --- | --- |
| Cherry-picking | Compare pre-reg vs reported outcomes | Pre-registration hash |
| P-hacking | Multiplicity audit | Primary outcome pre-specification |
| HARKing | Plan timestamp vs result timestamp | Pre-registration |
| Outcome-driven methodology | Method changes after data seen | Immutable plan versions |
| Selective reporting | Deliverable vs plan diff | Required reporting template |
| Deleting failed experiments | Audit gap detection | Append-only store |
| Changing hypotheses post-hoc | Hypothesis version lineage | `[IMPLEMENTED]` versioning |
| Rewriting predictions | Content hash at creation | `[PROPOSED]` (Agent 05) |
| Changing evaluation criteria | Criteria linked to plan ID | Plan binding |

**Principle:** Research history should be **immutable or auditable** where appropriate (`[IMPLEMENTED]` TCB audit append; `[PROPOSED]` plan immutability).

---

## 23. Pre-registration

### 23.1 When to pre-register `[PROPOSED]`

| Mode | Pre-registration |
| --- | --- |
| **Confirmatory** | Required before data analysis |
| **Exploratory** | Optional; if absent, findings labeled exploratory |
| **High-stakes decision research** | Required |
| **ML benchmark claims** | Required for primary metric |

### 23.2 Pre-registration contents

- Hypotheses (primary)
- Primary outcome measure
- Analysis plan
- Stopping criteria
- Success/failure criteria
- Exclusion rules
- Multiplicity handling

### 23.3 Distinction

```text
PRE-REGISTERED PLAN  ≠  FINAL REPORT (deviations must be documented)
EXPLORATORY RESEARCH ≠  CONFIRMATORY PROOF
```

**Org status:** `[PROPOSED]` — no pre-registration store or hash in repository.

---

## 24. Exploratory vs Confirmatory Research

### 24.1 Definitions

| Mode | Purpose | Labeling |
| --- | --- | --- |
| **Exploratory** | Discover patterns; generate hypotheses | `RESEARCH_MODE=EXPLORATORY` |
| **Confirmatory** | Test pre-defined hypotheses | `RESEARCH_MODE=CONFIRMATORY` |

Exploratory research is **valuable** but must not be relabeled confirmatory after seeing results.

### 24.2 Transition rules `[PROPOSED]`

```text
Exploratory finding
  → new hypothesis registered
  → new confirmatory plan pre-registered
  → new data collection (preferred) or held-out confirmatory split
  → confirmatory execution
```

**Rule:** Same dataset cannot serve exploratory discovery and confirmatory test without held-out confirmation split (risk of double dipping).

---

## 25. Stopping Rules

### 25.1 Stopping causes

| Cause | Action |
| --- | --- |
| Sufficient evidence | Stop; report with uncertainty |
| Falsification | Stop; record refutation |
| Resource exhaustion | Stop; label INCONCLUSIVE if underpowered |
| Time limit | Stop; document partial evidence |
| Safety issue | Stop immediately; escalate |
| Contradiction | Pause; resolve or retain uncertain |
| Diminishing returns | Stop; VoI assessment (§28) |
| Insufficient data | Stop or extend with new plan |
| Irreproducibility | Stop; investigate before continuing |

### 25.2 Endless loop prevention `[PROPOSED]`

- Mission `expires_at` (`[IMPLEMENTED]` on `ResearchMission`)
- Max experiment count in worker constraints (`[IMPLEMENTED]`)
- Commander-approved extension required past expiry
- VoI gate before continuation

---

## 26. Research Resource Budget

### 26.1 Budget dimensions `[PROPOSED]`

| Resource | Examples |
| --- | --- |
| Time | Wall clock, human review |
| Compute | CPU/GPU hours |
| Data | Storage, API quota |
| API calls | External providers (future) |
| Agent calls | LLM tokens, subagent launches |
| Human attention | Review, verification |
| External verification | Third-party audit |

### 26.2 Proportionality principle

> Research effort should be proportional to decision importance, uncertainty, and downside risk.

**Examples:**

- Low-stakes exploratory question → Level 1–2 reproducibility, no replication
- High-stakes trading signal claim → Level 3–4, independent replication, pre-registration

**Org status:** `[PROPOSED]` — no resource manager implemented (mission forbids implementation).

---

## 27. Research Prioritization

### 27.1 Priority factors `[PROPOSED]`

| Factor | Weight guidance |
| --- | --- |
| Decision impact | Higher impact → higher priority |
| Uncertainty | High uncertainty on important question → priority |
| Reversibility | Irreversible decisions need more research |
| Potential downside | Tail risk elevates priority |
| Information gain | Expected reduction in decision uncertainty |
| Novelty | Novel claims need stronger method, not automatic priority |
| Cost | Low-cost high-VoI research first |
| Urgency | Time-bound decisions |

### 27.2 Anti-pattern

Do **not** reduce all priorities to a single opaque score without tradeoff documentation. Multi-criteria framing with explicit tradeoffs is required.

---

## 28. Value of Information (VoI)

### 28.1 Concept

VoI asks: **Will additional research materially change the decision or reduce important uncertainty?**

| VoI assessment | Action |
| --- | --- |
| High VoI | Continue or expand research |
| Low VoI | Stop; decide with current evidence |
| Negative VoI | Stop; research adds noise or delay |

### 28.2 Distinction

```text
MORE INFORMATION  ≠  BETTER INFORMATION
```

Better information targets the highest-uncertainty decision lever. More data on a settled sub-question wastes budget.

### 28.3 VoI checklist `[PROPOSED]`

- What decision depends on this research?
- What would change if result is A vs B?
- Is uncertainty on the critical lever?
- Is cheaper evidence available?

---

## 29. Research Agent Methodology

### 29.1 Methodological contract for future Research Agents `[PROPOSED]`

Every research agent report must be able to state:

| Field | Required |
| --- | --- |
| Question | Bounded research question |
| Scope | Explicit boundaries |
| Assumptions | L6 list |
| Hypotheses | With falsification criteria |
| Competing hypotheses | Where reasonable |
| Evidence requested / obtained | With provenance |
| Methodology | Study type |
| Findings | Scoped to conditions |
| Contradictions | Open conflicts |
| Limitations | Methodological |
| Uncertainty | Preserved |
| Reproducibility level | Target and achieved |
| Recommended next research step | Not a command |

### 29.2 Forbidden silent claims

Research agents must **NOT** silently claim:

- Verification
- Authority
- Production truth
- Knowledge promotion
- Causal proof from correlation
- Replication without independence

**RESEARCH_ANALYST_AGENT** enforces subset via fixed interpreter rules (`[IMPLEMENTED]`): never emits `VERIFIED`, `PROMOTED`, `AUTHORIZED`, etc.

### 29.3 Gap

Cursor Control-Plane specialist agents (including this mission) operate at L5 with **no runtime binding** to the research worker contract unless explicitly routed through the host.

---

## 30. Multi-Agent Research

### 30.1 Patterns

| Pattern | Description | Independence caution |
| --- | --- | --- |
| Independent research | Separate agents, separate plans | Must not share prompt/source |
| Specialist decomposition | Domain experts on sub-questions | Coordinate via orchestrator, not merge blindly |
| Parallel research | Same question, different methods | True independence requires diverse methods/sources |
| Evidence pooling | Combine findings | Correlation cluster detection required |
| Blind review | Reviewer unaware of producer hypothesis | `[PROPOSED]` |
| Adversarial review | Red team seeks falsification | §32 |
| Replication | Independent rerun | §20 |

### 30.2 Correlated error rule

> Different agents using the same prompt and same source are **NOT** necessarily independent researchers.

Aligns with Agent 05 Independence Matrix.

### 30.3 Source overlap documentation `[PROPOSED]`

Multi-agent studies must document shared sources and adjust independence claims accordingly.

---

## 31. Research Review

### 31.1 Review pipeline `[PROPOSED]`

```text
Research Plan
      ↓
Method Review        ← Agent 06 domain (methodology quality)
      ↓
Research Execution
      ↓
Result Review        ← methodology + completeness
      ↓
Independent Challenge ← QA / Red Team (Agent 16/19)
      ↓
Replication (where required)
      ↓
Epistemic Evaluation ← Agent 05 domain (epistemic status)
      ↓
Governance / Decision ← Agent 04 / human (authority)
```

**Critical rule:** Do **not** collapse methodological review and epistemic verification into one step.

### 31.2 Method review criteria

- Question neutrality
- Hypothesis explicitness
- Competing hypotheses
- Study design appropriateness
- Leakage controls (if ML/backtest)
- Sampling frame
- Pre-registration (if confirmatory)
- Stopping rules
- Reproducibility target
- Resource proportionality

### 31.3 Outcomes

| Outcome | Meaning |
| --- | --- |
| APPROVED | May proceed to execution |
| REVISE | Plan amendment required |
| REJECT | Fatal methodological flaw |
| DEFER | Insufficient information to review |

Method review approval does **not** grant epistemic promotion or governance authority.

---

## 32. Red-Team Research

### 32.1 Red-team mandate

Red-team researchers **seek failure**, not consensus. They attempt to falsify:

- Assumptions
- Data quality
- Methodology
- Causal claims
- Model performance claims
- Replication claims
- Generalization scope

### 32.2 Red-team outputs `[PROPOSED]`

| Output | Description |
| --- | --- |
| Falsification attempt record | What was tried |
| Failure found | If successful falsification |
| Residual risk | If falsification failed |
| Recommended mitigation | Not automatic fix |

**Planned role:** `agent.org.19-independent-red-team` (`[PLANNED]`). Distinct from QA verification (`agent.org.16`) — red team is adversarial; QA is procedural.

### 32.3 Integration

Red-team review should occur **before** epistemic evaluation on high-stakes claims.

---

## 33. Research Quality Levels

### 33.1 Maturity model (proposed)

| Level | Name | Meaning | ≠ Truth |
| --- | --- | --- | --- |
| **RQ0** | INFORMAL | Unstructured narrative | Yes |
| **RQ1** | STRUCTURED | Question + hypotheses documented | Yes |
| **RQ2** | REPRODUCIBLE | Level 2–3 reproducibility achieved | Yes |
| **RQ3** | INDEPENDENTLY REVIEWED | Method + result review passed | Yes |
| **RQ4** | REPLICATED | Independent replication succeeded | Yes |
| **RQ5** | HIGH-METHODOLOGY-CONFIDENCE | RQ4 + pre-registration + bias controls | Yes |

**Evaluation:** Names are **appropriate** if "HIGH-CONFIDENCE" is renamed to **HIGH-METHODOLOGY-CONFIDENCE** to avoid confusion with epistemic confidence (Agent 05).

### 33.2 Mapping to epistemic review

| RQ Level | Typical epistemic input (Agent 05) |
| --- | --- |
| RQ0–1 | Hypothesis or claim draft only |
| RQ2 | Candidate with reproducible warrants |
| RQ3–4 | Eligible for independent verification |
| RQ5 | Strong methodological warrant bundle — still requires promotion gates |

**Maturity ≠ truth.** RQ5 does not bypass D-01/D-04 promotion gates.

---

## 34. Epistemic Boundary (Agent 05)

| Question | Owner |
| --- | --- |
| What epistemic status should a result have? | **Agent 05** |
| What research methodology produced the result and how strong was it? | **Agent 06** |

### 34.1 Handoff artifact `[PROPOSED]`

```text
MethodologyAssessment
  research_id
  rq_level
  reproducibility_level
  research_mode (exploratory/confirmatory)
  leakage_attestation
  competing_hypotheses_considered
  negative_results_retained
  limitations
  method_review_status
  red_team_status
  → input to EpistemicEvaluation (Agent 05)
```

Neither agent automatically controls the other. Low methodology quality should **block** epistemic promotion regardless of narrative plausibility.

---

## 35. Governance Boundary (Agent 04)

| Domain | Owner |
| --- | --- |
| Authority, approval, delegation | **Agent 04** |
| Research method | **Agent 06** |

Agent 06 does **NOT** grant itself authority based on research quality. Methodological approval ≠ governance approval ≠ execution authority.

Research missions may specify `authority_capabilities` and `authority_resources` on `ResearchMission` (`[IMPLEMENTED]`) but methodology design does not expand those grants.

---

## 36. Security Boundary (Agent 03)

| Domain | Owner |
| --- | --- |
| Environment security, injection, isolation, evidence tampering | **Agent 03** |
| Methodological validity | **Agent 06** |

```text
SECURITY        ≠ METHODOLOGICAL CORRECTNESS
SECURE SYSTEM   ≠ VALID RESEARCH
VALID RESEARCH  ≠ SECURE SYSTEM
```

A secure research run can still use biased sampling. A methodologically sound plan can still execute in an insecure environment. Both reviews are required where applicable.

---

## 37. Research Failure Taxonomy

| Failure class | Description | Typical detection |
| --- | --- | --- |
| `BAD_QUESTION` | Ill-posed or encoded desired answer | Method review |
| `BAD_HYPOTHESIS` | Non-falsifiable or vague | Plan review |
| `INSUFFICIENT_EVIDENCE` | Data inadequate for claim | Result review |
| `BIASED_SAMPLE` | Non-representative selection | Sampling audit |
| `DATA_LEAKAGE` | Future info in analysis | Leakage checklist |
| `CONFOUNDING` | Uncontrolled common cause | Causal review |
| `MEASUREMENT_ERROR` | Instrument bias | Replication |
| `STATISTICAL_ERROR` | Wrong test / misinterpretation | Stats review |
| `IMPLEMENTATION_ERROR` | Code bug in analysis | Reproduction |
| `REPLICATION_FAILURE` | Independent rerun disagrees | Replication |
| `SOURCE_CONTAMINATION` | Bad or poisoned source | Provenance audit |
| `METHODOLOGY_DRIFT` | Plan deviates undeclared | Plan vs report diff |
| `POST_HOC_REASONING` | HARKing | Pre-reg comparison |
| `CHERRY_PICKING` | Selective evidence | Full evidence audit |
| `FALSE_INDEPENDENCE` | Correlated "independent" agents | Independence matrix |
| `TEMPORAL_MISMATCH` | Misaligned timestamps | Data audit |
| `PROVIDER_DISAGREEMENT` | Unreconciled sources | Source protocol |
| `MODEL_OVERFITTING` | In-sample fit only | OOS test |
| `DISTRIBUTION_SHIFT` | Train ≠ deploy regime | Regime testing |

**Slice 2B:** `ExperimentRun.failure_class` accepts string (`[IMPLEMENTED]`); taxonomy not enumerated in code.

---

## 38. Research Integrity Principles (Methodology Constitution)

Evaluated minimum set:

1. **Never hide failed experiments.** `[PROPOSED]` enforcement; `[IMPLEMENTED]` terminal states.
2. **Never rewrite predictions after outcomes.** `[PROPOSED]` content hash immutability.
3. **Never silently change evaluation criteria after seeing results.** `[PROPOSED]` plan binding.
4. **Never convert exploratory findings into confirmatory proof.** `[PROPOSED]` mode labeling.
5. **Never claim causality from correlation alone.** `[DOCUMENTED]` Constitution; `[PROPOSED]` causal ladder.
6. **Never ignore competing hypotheses without justification.** `[PROPOSED]` plan requirement.
7. **Never hide uncertainty.** `[IMPLEMENTED]` worker uncertainty labels; `[DOCUMENTED]` protocols.
8. **Never hide methodological limitations.** `[PROPOSED]` required report section.
9. **Never claim replication without independent replication.** `[DOCUMENTED]` Agent 05 independence rules.
10. **Never treat model consensus as evidence.** `[DOCUMENTED]` CONSENSUS ≠ TRUTH.
11. **Never use future information in historical evaluation.** `[PROPOSED]` leakage controls.
12. **Preserve research provenance.** `[IMPLEMENTED]` TCB provenance + audit.
13. **Preserve negative results.** `[PROPOSED]` registry.
14. **Distinguish discovery from confirmation.** `[PROPOSED]` mode + transition rules.
15. **Scope conclusions to tested conditions.** `[DOCUMENTED]` `[PROPOSED]` generalization block.

---

## 39. Implemented / Documented / Proposed

| Control | Classification | Evidence |
| --- | --- | --- |
| `ResearchMission` bounded fields | `[IMPLEMENTED]` | `agent_org/epistemic.py` |
| `ExperimentPlan` / `ExperimentRun` | `[IMPLEMENTED]` | `agent_org/epistemic.py` |
| Hypothesis falsification criteria required | `[IMPLEMENTED]` | Construction validation |
| Experiment reproducibility requirements field | `[IMPLEMENTED]` | `ExperimentPlan` |
| Mission expiry / success / failure criteria | `[IMPLEMENTED]` | `ResearchMission` |
| Research worker label discipline | `[IMPLEMENTED]` | `research_worker/analyst.py` |
| Worker contradiction heuristic | `[IMPLEMENTED]` | `NOT` prefix pairs |
| Worker descriptive experiment proposal | `[IMPLEMENTED]` | `_experiments()` |
| Worker uncertainty labels | `[IMPLEMENTED]` | `uncertainty_labels` output |
| No verification/promotion from worker | `[IMPLEMENTED]` | Interpreter rules |
| IPC reproducibility_requirements validation | `[IMPLEMENTED]` | `research_worker/protocol.py` |
| TCB audit append on mutation | `[IMPLEMENTED]` | `agent_org/tcb.py` |
| L0–L6 hierarchy | `[DOCUMENTED]` | Constitution |
| Evidence Protocol reporting | `[DOCUMENTED]` | `AGENT_EVIDENCE_PROTOCOL.md` |
| SIMULATION ≠ EXECUTION | `[DOCUMENTED]` | Constitution, Agent 05 |
| CORRELATION ≠ CAUSATION (vocabulary) | `[DOCUMENTED]` | Mission principles, Constitution |
| Research plan template | `[PROPOSED]` | This document |
| Pre-registration store | `[PROPOSED]` | — |
| Exploratory/confirmatory mode enum | `[PROPOSED]` | — |
| Reproducibility level enum | `[PROPOSED]` | — |
| Leakage checklist enforcement | `[PROPOSED]` | — |
| Method review gate | `[PROPOSED]` | — |
| Negative result registry | `[PROPOSED]` | — |
| Causal ladder metadata | `[PROPOSED]` | — |
| ML split / backtest controls | `[PROPOSED]` | — |
| Crypto timestamp alignment protocol | `[PROPOSED]` | — |
| Multi-agent independence enforcement | `[PROPOSED]` | — |
| MethodologyAssessment handoff to Agent 05 | `[PROPOSED]` | — |
| Chat agent methodology contract | `[PROPOSED]` | No runtime enforcement |
| Plane A / D methodology role mapping | `[UNKNOWN]` | Dual-19 unresolved |

Never claim documented rules are enforced unless code or tests demonstrate it.

---

## 40. Required Matrices

### A. Research Lifecycle Matrix

| Stage | Required Inputs | Output | Review | Failure Conditions |
| --- | --- | --- | --- | --- |
| **Question formulation** | Decision context, unknowns, constraints | Research question artifact | Method review (neutrality) | Encoded desired answer; unfalsifiable |
| **Plan authoring** | Question, hypotheses, competing H, assumptions | Research plan | Method review | Missing competing H; no stopping rules |
| **Pre-registration** (confirmatory) | Frozen plan hash | Registration record | Registration audit | Post-hoc registration |
| **Data acquisition** | Plan, source contracts | Sourced dataset + provenance | Data QA | Contaminated source; temporal mismatch |
| **Experiment design** | Hypothesis, study type | ExperimentPlan | Method review | Leakage; no control/baseline |
| **Execution** | Approved plan, budget | ExperimentRun, observations | Runtime monitor | Safety stop; budget exceeded |
| **Analysis** | Pre-specified analysis plan | Results + uncertainty | Result review | P-hacking; criteria change |
| **Reporting** | All above | Research report + limitations | Completeness review | Selective reporting |
| **Independent challenge** | Report | Red-team / QA findings | Adversarial review | Unresolved fatal flaw |
| **Replication** (if required) | Original plan + data/method | Replication report | Independence check | False independence |
| **Epistemic handoff** | MethodologyAssessment | Package for Agent 05 | Epistemic evaluation | RQ level insufficient for claim type |
| **Archive** | All artifacts | Immutable history | Audit | Missing negative results |

### B. Methodology Quality Matrix

| Dimension | Weak | Moderate | Strong | Evidence |
| --- | --- | --- | --- | --- |
| Question clarity | Vague intent | Bounded question | Formal model + falsifiability | Plan document |
| Hypothesis quality | Implicit | Explicit H1 | H0 + competing H + criteria | Hypothesis artifacts |
| Study design | Narrative only | Structured observational | RCT / natural experiment / validated ML protocol | ExperimentPlan |
| Bias control | Unacknowledged | Named biases | Mitigations + residual risk | Bias matrix (§C) |
| Data provenance | Unknown source | Named source | Full lineage + timestamps | Source/Evidence records |
| Leakage control | None | Partial checklist | Audited temporal splits | ML/backtest audit |
| Statistical rigor | p-value only | Effect size + CI | Power + multiplicity control | Analysis report |
| Reproducibility | Level 0–1 | Level 2–3 | Level 4–5 | Repro matrix (§D) |
| Integrity | Post-hoc story | Documented plan | Pre-registered confirmatory | Registration hash |
| Independence | Same agent/source | Different agent | Independent principal + method | Replication record |

### C. Bias Matrix

| Bias | Detection | Mitigation | Residual Risk |
| --- | --- | --- | --- |
| Selection bias | Compare sample vs population | Define frame; weighting | Unobserved selection |
| Survivorship bias | Missing delists/failures | Point-in-time universe | Incomplete history |
| Confirmation bias | Cherry-picked evidence IDs | Require disconfirming search | Motivated interpretation |
| Publication bias | Only positive studies visible | Negative result registry | File drawer remains |
| Look-ahead / leakage | Feature timestamp audit | Temporal splits | Hidden feature paths |
| Multiple testing | Count of tests vs pre-spec | FDR / primary outcome | Researcher degrees of freedom |
| LLM prompt bias | Shared prompt across "independent" agents | Diverse prompts/methods | Correlated model errors |
| Convenience sampling | Data source audit | Document non-generalization | Wrong population inference |
| Regime change | Structural break tests | Regime labeling | Unlabeled shifts |
| Wash trading (crypto) | Volume vs unique users | Competing H2 tests | Sophisticated manipulation |

### D. Reproducibility Matrix

| Level | Requirement | Evidence |
| --- | --- | --- |
| 0 — Narrative | Written summary | Report text |
| 1 — Source-identifiable | Named locators | Source records |
| 2 — Data-reconstructable | Data + schema + selection rules | Dataset snapshot |
| 3 — Method-replayable | Analysis code + seeds + data | Replay log |
| 4 — Environment-reproducible | Pinned deps + container | Environment spec hash |
| 5 — Independently replicated | Independent team replication | Second replication report |

### E. Research-vs-Epistemic Boundary Matrix

| Activity | Agent 06 | Agent 05 | Independent Verifier | Governance |
| --- | --- | --- | --- | --- |
| Question design quality | **Owns** | Advises on falsifiability | — | — |
| Study / experiment design | **Owns** | — | Reviews if assigned | — |
| Pre-registration policy | **Owns** | — | — | Adopts if L2 |
| Bias / leakage controls | **Owns** | — | Audits | — |
| Reproducibility level | **Assesses** | Records in warrant | Confirms replay | — |
| Method review approval | **Recommends** | — | May co-review | Does not approve |
| Claim / hypothesis typing | Advises | **Owns** lifecycle | — | — |
| Evidence eligibility | Advises on collection | **Owns** freshness/eligibility | Verifies | — |
| Contradiction typing | Methodological source | **Owns** ContradictionCase | Investigates | — |
| Epistemic status assignment | **Must not** | **Owns** | Inputs verification | — |
| Knowledge promotion | **Must not** | Gates candidate | Independent verify | Human approval |
| Research authority grants | **Must not** | **Must not** | — | **Owns** |
| Red-team methodology attack | Defines scope | Receives findings | **Executes** (Agent 19) | — |
| Negative result retention policy | **Owns** | Uses in promotion | Audits completeness | — |

---

## 41. Open Questions

1. Should `ResearchMission` gain structured fields for population, unit_of_analysis, and research_mode enum?
2. Should pre-registration be a first-class TCB artifact with content hash, or a sidecar document store?
3. What minimum RQ level is required for each epistemic promotion tier (coordination with Agent 05)?
4. How should exploratory research from Cursor chat agents be labeled when no TCB mission exists?
5. Should `ExperimentRun.failure_class` use a closed enum from §37 taxonomy?
6. What is the default reproducibility level target for Class A research worker outputs?
7. How should crypto provider disagreement be reconciled methodologically (hierarchy vs aggregate)?
8. Should causal ladder level be metadata on `Hypothesis` or on `KnowledgeCandidate`?
9. How do Plane A research-adjacent roles (reality-forensics, scoring-science) map to Agent 06 methodology ownership under Dual-19?
10. Should methodology review be automated (lint-like) or human/specialist-only for confirmatory research?
11. What is the handoff format from RESEARCH_ANALYST_AGENT output to MethodologyAssessment?
12. Should backtests performed outside this org (future AHOS) require mirrored methodology metadata?

---

## 42. Human Decisions Required

| ID | Decision | Status |
| --- | --- | --- |
| **HD-01** | Dual-19 resolution: impact on methodology role ownership (Plane A vs Plane D) | `HUMAN_DECISION_REQUIRED` |
| **HD-02** | Adopt RQ maturity model (§33) as organizational vocabulary | `HUMAN_DECISION_REQUIRED` |
| **HD-03** | Pre-registration policy: mandatory for confirmatory research or optional | `HUMAN_DECISION_REQUIRED` |
| **HD-04** | Minimum reproducibility level by research class (exploratory vs confirmatory vs ML) | `HUMAN_DECISION_REQUIRED` |
| **HD-05** | Method review gate: who performs it (Agent 06 documentary vs Agent 16 vs human) | `HUMAN_DECISION_REQUIRED` |
| **HD-06** | Failure taxonomy: adopt closed enum in `ExperimentRun.failure_class` | `HUMAN_DECISION_REQUIRED` |
| **HD-07** | Exploratory→confirmatory transition: require fresh data vs allow held-out split | `HUMAN_DECISION_REQUIRED` |
| **HD-08** | MethodologyAssessment handoff schema to Agent 05 epistemic evaluation | `HUMAN_DECISION_REQUIRED` |
| **HD-09** | Crypto data provider reconciliation hierarchy (when providers disagree) | `HUMAN_DECISION_REQUIRED` |
| **HD-10** | Adoption of this architecture doc as L2 governance text | `HUMAN_DECISION_REQUIRED` |
| **HD-11** | Resource budget defaults by decision impact tier | `HUMAN_DECISION_REQUIRED` |

---

## 43. Recommended Future Work — STATE ONLY

`RECOMMENDED_NEXT_MISSION = STATE_ONLY — DO NOT EXECUTE`

The following are **recommendations only**. They are not activated missions.

1. **FUTURE_IMPLEMENTATION_REQUIRED:** Add `research_mode`, `reproducibility_level`, and `rq_level` metadata to `ResearchMission` or sidecar artifacts.
2. **FUTURE_IMPLEMENTATION_REQUIRED:** Pre-registration artifact with content hash and plan binding.
3. **FUTURE_IMPLEMENTATION_REQUIRED:** Closed `failure_class` enum aligned with §37 taxonomy.
4. **FUTURE_IMPLEMENTATION_REQUIRED:** MethodologyAssessment schema for Agent 05 handoff.
5. **FUTURE_IMPLEMENTATION_REQUIRED:** Leakage checklist attestation field on `ExperimentPlan` for ML/backtest studies.
6. **FUTURE_IMPLEMENTATION_REQUIRED:** Negative result registry and audit for missing experiment runs.
7. **Recommended documentary agent:** Agent 07 — Data Intelligence (data quality schema; coordinate with Agent 06 sampling/provenance).
8. **Recommended documentary agent:** Agent 12 — Quant / Backtesting (extend §17/§18 with domain-specific controls).
9. **Recommended verification mission:** Red-team methodology audit of RESEARCH_ANALYST_AGENT rules vs this architecture.
10. **Recommended coordination mission:** Agent 05 + Agent 06 joint boundary test cases (methodology strong but epistemically blocked, and converse).

**AGENT-06 does not execute any of the above.**

---

## Document provenance

| Field | Value |
| --- | --- |
| Author | AGENT-06 (Research Methodology Architect) |
| Task | TASK-20260914-006 |
| Commander | MASTER ORCHESTRATOR |
| Repository | `G:\robat\ahos-agent-org` |
| Code changes | NONE |
| Runtime changes | NONE |
| AHOS impact | NONE |
| Classification | `[PROPOSED]` architecture unless cited `[IMPLEMENTED]` / `[DOCUMENTED]` |

---

*End of AGENT_06_RESEARCH_METHODOLOGY_ARCHITECTURE.md*
