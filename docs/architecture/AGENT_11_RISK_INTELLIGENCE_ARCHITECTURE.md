# Agent Organization Risk Intelligence Architecture

```text
DOCUMENT_ID      = AGENT_11_RISK_INTELLIGENCE_ARCHITECTURE
MISSION_ID       = TASK-20260914-011
VERSION          = 0.1.0
STATUS           = PROPOSED / READ_ONLY_RISK_INTELLIGENCE_ARCHITECTURE
AUTHORITY        = NONE CREATED
RUNTIME_EFFECT   = NONE
AHOS_EFFECT      = NONE
AGENT_ID         = AGENT-11 (agent.org.11-risk-intelligence — documentary)
DIRECT_COMMANDER = MASTER ORCHESTRATOR
PARENT           = MASTER ORCHESTRATOR
```

This document is a **design and architecture artifact** produced by AGENT-11 under explicit activation for TASK-20260914-011. It does not implement a risk engine, adopt governance, grant authority, modify AHOS, connect providers, compute live risk scores, or promote knowledge. Facts cite repository evidence with explicit classification labels (`[IMPLEMENTED]`, `[DOCUMENTED]`, `[PROPOSED]`, `[UNKNOWN]`). Architectural recommendations are labeled `[PROPOSED]`.

**Critical honesty constraint:**

```text
RISK                    ≠ SECURITY
RISK                    ≠ DANGER LABEL
RISK                    ≠ EVIDENCE
RISK                    ≠ CLAIM
RISK                    ≠ HYPOTHESIS
RISK                    ≠ PREDICTION
RISK                    ≠ OBSERVATION
RISK                    ≠ DECISION
RISK                    ≠ EXECUTION
RISK SCORE              ≠ TRUTH
RISK SCORE              ≠ EXPECTED RETURN
RISK SCORE              ≠ GUARANTEED OUTCOME
LOW OBSERVED RISK       ≠ NO RISK
UNKNOWN                 ≠ LOW RISK
NO DETECTED RISK        ≠ SAFE
VOLATILITY              ≠ RISK
LIQUIDITY               ≠ EXITABILITY
DIVERSIFICATION         ≠ INDEPENDENCE
HISTORICAL STABILITY    ≠ FUTURE STABILITY
MODEL CONFIDENCE        ≠ REAL-WORLD SAFETY
SIMULATION              ≠ EXECUTION
BACKTEST                ≠ FUTURE PROOF
HIGH LIQUIDITY          ≠ LOW RISK
HIGH MARKET CAP         ≠ LOW RISK
MANY HOLDERS            ≠ LOW RISK
HIGH SCORE              ≠ LOW RISK
EXPECTED VALUE          ≠ SAFETY
PROBABILITY ESTIMATE    ≠ FACT
SCENARIO                ≠ PREDICTION
STRESS TEST             ≠ GUARANTEE
DIVERSIFICATION         ≠ HEDGING
CORRELATION             ≠ CAUSATION
```

---

## 1. Executive Summary

`[VERIFIED]` The AHOS Agent Organization contains **zero implemented Risk Intelligence runtime**. No `RiskFactor`, `RiskAssessment`, `RiskVector`, `RiskScenario`, or risk aggregation engine exists in Slice 1 (`ahos_org/`) or Slice 2B (`agent_org/`). The only risk-related implemented artifact is Slice 1 organizational `RiskLevel` on task records (`ahos_org/models.py`, `ahos_org/tasks.py`) — a **mission governance label**, not financial or portfolio risk intelligence.

`[VERIFIED]` Peer architecture documents (Agents 07–10) already define **upstream producer boundaries** and explicitly defer loss framing, exposure quantification, scenario analysis, and portfolio risk limits to Agent 11. Agent 05 defines epistemic non-collapse principles that Risk Intelligence must inherit. Agent 03 defines authority-collapse as the primary security failure mode that risk architecture must not replicate.

`[VERIFIED]` The planned 19-agent blueprint lists `agent.org.11-risk-intelligence` as `Risk identification and framing` with status `PLANNED` (`docs/agents/PLANNED_19_AGENT_MAP.md`). It is **not seeded** in Slice 1 `CANONICAL_AGENT_IDS`.

**Central architectural question:** How should the organization represent **what can go wrong**, **how badly**, **under what uncertainty**, **over what horizon**, **with what dependencies and tail exposure** — without collapsing multidimensional risk into a decision shortcut?

**Primary risk-intelligence objective:** prevent **risk authority collapse** — where risk scores, risk labels, scenario outputs, or risk agent synthesis silently become trade approval, rejection, execution gates, or epistemic truth.

**Current risk-intelligence posture:** `[UNVERIFIED]` at runtime — architectural boundaries are `[PARTIALLY_VERIFIED]` via peer documents; no risk domain code, tests, or TCB artifact types exist.

**Dual-19 status:** `[VERIFIED]` `[CONFLICT / UNRESOLVED]` — Slice 1 Plane A (`agent.*`, including thematic overlap with `agent.scoring-science`, `agent.paper-trading`) and planned Plane D (`agent.org.11-risk-intelligence`) remain separate taxonomies. This document analyzes implications only; it does **not** merge them.

**Agent One:** `NOT_IMPLEMENTED / FUTURE_NON_AUTHORITY_ROOT` — must never become risk authority or decision root.

**AHOS:** `[VERIFIED]` Separate product repository. This mission performs read-only boundary analysis only. `AHOS_IMPACT = NONE`.

---

## 2. Agent-11 Identity

| Field | Value |
| --- | --- |
| `AGENT_ID` (mission) | `AGENT-11` |
| Blueprint ID | `agent.org.11-risk-intelligence` |
| Provisional name | Risk Intelligence Architect |
| Role | Design risk intelligence architecture: identification, characterization, scenario framing, dependency analysis, uncertainty preservation |
| Authority class | `NONE` (design mission only) |
| Capabilities exercised | READ, ANALYZE, PROPOSE (documentation) |
| Forbidden | APPROVE/REJECT trades, EXECUTE, PROMOTE, VERIFY (own conclusions), MODIFY runtime/TCB, ACTIVATE other agents, emit BUY/SELL, set risk limits as enforced policy, connect providers, access credentials/wallets |
| Supervisor | MASTER ORCHESTRATOR → human operator |
| Source of truth | **Not** AGENT-11. Repository L0/L1 + governance L2/L3 only. |

AGENT-11 is **not** Agent One, **not** the Master Orchestrator, **not** Agent 03 (organizational security), **not** Agent 10 (token security intelligence producer), **not** Agent 05 (epistemic promotion), **not** Agent 12 (quant/backtesting), **not** Agent 13 (AI/ML), and **not** authorized to convert risk assessments into decisions or execution.

---

## 3. Command Chain

```text
MEHRDAD
  → MASTER ORCHESTRATOR
    → AGENT-11 (this mission)
```

- Direct commander: **MASTER ORCHESTRATOR**
- Parent: **MASTER ORCHESTRATOR**
- Reporting line: **MASTER ORCHESTRATOR**
- Agents 03–10, 05–06 are **peer specialists**, not commanders.
- No subordinate agents created or activated by this mission.

---

## 4. Lifecycle

### 4.1 Activation rule

Creating, registering, or naming an agent does **not** activate it. TASK-20260914-011 is the explicit activation command for this mission.

### 4.2 Mission lifecycle

```text
REGISTERED / IDLE / DORMANT
  → [explicit activation: TASK-20260914-011]
  → RUNNING (risk intelligence architecture analysis)
  → COMPLETED (this deliverable)
  → IDLE / DORMANT / WAITING_FOR_NEW_COMMAND
```

### 4.3 Terminal states

Supported: `COMPLETED`, `FAILED`, `TIMEOUT`, `CANCELLED`, `BLOCKED`, `SUSPENDED`, `QUARANTINED`.

After termination: `LIFECYCLE_STATUS = IDLE / DORMANT / WAITING_FOR_NEW_COMMAND`.

Recommendations in this document are **not** commands. AGENT-11 does not auto-continue to Agent 12 or any future mission.

---

## 5. What Is Risk Intelligence?

### 5.1 Definition

**Risk Intelligence (RI)** is the bounded architectural domain responsible for transforming **quality-qualified observations and assessments from upstream intelligence domains** into **explicitly labeled risk characterizations** — exposure structures, severity framings, uncertainty-preserving scenario sets, dependency graphs, and conflict records — while preserving epistemic separation from evidence, security verdicts, market signals, predictions, decisions, and execution.

Risk Intelligence answers:

> Given what we observe and what we do not know, **what adverse outcomes are plausible**, **how severe could they be**, **under what assumptions**, **over what horizon**, **with what dependencies**, and **what must remain UNKNOWN**?

Risk Intelligence does **not** answer:

> Should we buy, sell, hold, approve, reject, or execute?

### 5.2 Risk Intelligence ≠ Risk Score

`[REJECTED]` as sole architecture: `risk_score = 73`.

A scalar score may exist as a **derived summary** under strict governance, but it is **never** the canonical risk representation. The canonical representation is a **multidimensional, time-stamped, provenance-linked structure** that survives audit, red-team attack, and regime change without hiding tail risk or UNKNOWN dimensions.

### 5.3 Fundamental vs derived dimensions

| Dimension | Class | Notes |
| --- | --- | --- |
| **Exposure** | Fundamental | What is at stake (direct/indirect/hidden) |
| **Severity** | Fundamental | Magnitude of harm if realized |
| **Uncertainty** | Fundamental | Epistemic + aleatoric + model + data components |
| **Timing / horizon** | Fundamental | When harm may materialize; validity window |
| **Reversibility** | Fundamental | Can loss be recovered? |
| **Detectability** | Fundamental | Can we see it coming? |
| **Dependency / contagion** | Fundamental | What else fails if this fails? |
| **Probability** | Derived (conditional) | Only when evidence supports responsible estimation |
| **Confidence** | Derived (meta) | Strength of assessment itself — not probability of event |
| **Liquidity / exitability** | Derived from observations | Never equated with nominal liquidity |
| **Concentration** | Derived | From holdings, providers, infrastructure |
| **Tail risk** | Derived + structural | Fat-tail, jump, cascade properties |
| **Model risk** | Derived | From model metadata and disagreement |
| **Data risk** | Derived | From data quality conditions |
| **Scalar risk score** | Derived summary | Optional; never canonical |

---

## 6. Non-Collapse Principles (Architectural Invariants)

These are **forbidden equalities**. Violating them is a risk-intelligence defect, not a presentation choice. They extend Agent 05 epistemic invariants and Agent 07–10 domain invariants.

```text
RISK ASSESSMENT     ≠ DECISION
RISK RECOMMENDATION ≠ TRADE APPROVAL
RISK LIMIT PROPOSAL ≠ ENFORCED LIMIT (without governance)
SCENARIO            ≠ PREDICTION
STRESS TEST RESULT  ≠ GUARANTEE
LOW RISK LABEL      ≠ SAFE TO ACT
UNKNOWN DIMENSION   ≠ ZERO RISK CONTRIBUTION
MISSING DATA        ≠ LOW RISK
CONFLICT RESOLVED   ≠ TRUTH (without epistemic resolution)
AGGREGATED SCORE    ≠ COMPARABLE ACROSS CONTEXTS (without proof)
```

`[IMPLEMENTED]` Slice 2B: "Stored memory, confidence, recency, and audit inclusion never imply truth." Risk Intelligence must treat this as binding on any future risk artifacts stored in or derived from TCB.

---

## 7. Risk Taxonomy

### A. Market Risk `[PROPOSED]`

| Sub-type | Description | Upstream |
| --- | --- | --- |
| Price risk | Adverse price movement vs reference | Agent 08 |
| Volatility risk | Realized/implied vol regime | Agent 08 |
| Regime risk | Structural market state change | Agent 08 |
| Gap risk | Discontinuous price moves | Agent 08 |
| Momentum reversal | Trend failure | Agent 08 |
| Mean-reversion failure | Expected reversion absent | Agent 08 |
| Correlation breakdown | Diversification illusion | Agent 08 + Agent 11 graph |
| Cross-venue divergence | Same asset, divergent venues | Agent 08 |
| Market-wide shock | Systemic price dislocation | Agent 08 + Agent 11 systemic |

**Boundary:** Agent 08 owns market **observation and interpretation**. Agent 11 owns **loss framing** from those observations. `STRONG SIGNAL ≠ LOW RISK` (Agent 08 §34).

### B. Liquidity Risk `[PROPOSED]` — MAJOR SECTION

| Sub-type | Description |
| --- | --- |
| Insufficient depth | Order book / pool depth inadequate for size |
| Slippage | Execution price deviation |
| Price impact | Market move caused by own trade |
| Liquidity withdrawal | LP removal, pool drain |
| Fragmented liquidity | Split across venues/routes |
| Fake liquidity | Spoofing, wash, flash LP |
| Asymmetric liquidity | Easy entry, hard exit |
| Exit liquidity | Ability to unwind position |
| Time-to-liquidate | Horizon to exit at acceptable cost |
| Liquidation cascade | Forced selling chain reaction |

**Critical invariant:** `LIQUIDITY ≠ EXITABILITY`

Nominal TVL, volume, or "high liquidity" labels from Agent 08 **do not** authorize low exit-risk conclusions. Agent 11 must evaluate: executable depth at size, route diversity, LP control (Agent 09/10), security restrictions (Agent 10), and time-to-exit under stress.

### C. Security Risk `[PROPOSED]`

Consumes Agent 10 outputs **without** taking over security authority.

| Input from Agent 10 | Risk framing by Agent 11 |
| --- | --- |
| Privilege / upgradeability findings | Capital loss, frozen asset, arbitrary mint risk |
| Honeypot hypothesis (SUPPORTED) | Exit impossibility, total loss scenario |
| Blacklist/whitelist capability | Selective trading restriction risk |
| Malicious trading logic | Hidden tax, transfer block risk |
| LP control by owner | Rug / liquidity removal risk |

**Invariant:** Agent 10 finding is **preserved verbatim**. Agent 11 adds **exposure × severity × scenario** — never rewrites `SUPPORTED HONEYPOT HYPOTHESIS` into `LOW RISK`.

### D. On-Chain Risk `[PROPOSED]`

Consumes Agent 09 outputs:

| Observation (Agent 09) | Risk dimension (Agent 11) |
| --- | --- |
| Holder concentration | Single-actor dump / governance capture |
| Deployer exposure | Insider sell, rug pathway |
| Whale behavior | Coordinated exit, cascade trigger |
| Bridge dependency | Bridge failure, wrapped asset depeg |
| Chain instability / reorg | Finality uncertainty, state rollback |
| Smart-contract dependency | Composability failure cascade |
| Wallet clustering uncertainty | Hidden concentration risk |

**Invariant:** `Observation ≠ quantified risk` (Agent 09 §46).

### E. Data Risk `[PROPOSED]`

Consumes Agent 07 quality characterizations:

| Data condition | Risk arising |
| --- | --- |
| Stale data | Assessment validity decay; wrong regime inference |
| Missing data | UNKNOWN propagation; false confidence if imputed |
| Biased data | Systematic underestimation of tail |
| Provider disagreement | Epistemic + model risk amplification |
| Corrupted data | False safe / false danger |
| Low coverage | Survivorship, selection bias in risk estimates |
| Look-ahead leakage | Inflated backtest-derived risk metrics (Agent 12 boundary) |
| Timestamp mismatch | Wrong causal ordering in scenario trees |
| Identity mismatch | Wrong asset risk attribution |
| Provenance weakness | Unauditable risk lineage |

**Boundary:** Agent 07 answers "Is data suitable?" Agent 11 answers "What risk arises from unsuitability?"

### F. Model Risk `[PROPOSED]`

| Sub-type | Description |
| --- | --- |
| Misspecification | Wrong functional form |
| Overfitting / underfitting | Generalization failure |
| Calibration failure | Confidence ≠ frequency |
| Distribution shift | Training ≠ deployment |
| Concept drift | Feature-outcome relationship change |
| Hidden assumptions | Unstated priors in risk models |
| Unstable features | Small input change → large risk change |
| Adversarial conditions | Manipulation of model inputs |
| False confidence | High score, low real safety |
| Correlated model errors | Ensemble illusion of independence |

**Boundary:** Agent 13 owns model intelligence. Agent 11 owns **risk interface** — how model conditions translate to loss scenarios and uncertainty budgets.

### G. Operational Risk `[PROPOSED]`

| Sub-type | Examples |
| --- | --- |
| Service failure | Worker crash, host unavailable |
| Data store corruption | TCB/store integrity |
| Message loss | IPC/orchestration gap |
| Stale cache | Risk assessment served from expired state |
| Misconfiguration | Wrong thresholds, wrong asset ID |
| Policy error | Incorrect capability grant |
| Deployment error | Version skew |
| Monitoring failure | Undetected escalation |

Relevant to org runtime (Agent 03, Agent 14) and future AHOS integration — not live trading today.

### H. Counterparty / Dependency Risk `[PROPOSED]`

Provider outage, API dependency, oracle failure, bridge operator risk, centralized infra (RPC, indexer), external service SLA — overlaps Agent 07 provider model and Agent 11 dependency graph.

### I. Execution Risk `[PROPOSED]` — ARCHITECTURAL ONLY

Latency, slippage, partial fills, failed transactions, gas spikes, MEV, sandwiching, route failure — **forbidden to implement** in this repository today. Architecturally documented for future governed execution plane. `SIMULATION ≠ EXECUTION`.

### J. Systemic / Contagion Risk `[PROPOSED]` — MAJOR SECTION

Shared liquidity pools, chains, stablecoins, market makers, contract libraries, providers, narratives, wallets, counterparties.

**Principle:** Apparent diversification may conceal **common-cause exposure**. Three agents agreeing from one provider is **not** three independent risk confirmations.

`[PROPOSED]` `RiskDependencyGraph` — see §19.

### K. Tail Risk `[PROPOSED]` — MAJOR SECTION

Black swans, fat tails, jump risk, discontinuities, regime breaks, extreme drawdowns, liquidity evaporation, cascading failures, ruin scenarios, nonlinear loss.

**Architectural rule:** Tail risk must **never** be fully absorbed into a mean-variance or average score without explicit separate representation. A small probability of catastrophic loss must remain visible.

---

## 8. Risk Representation

### 8.1 Representation options analyzed

| Option | Benefits | Failure modes |
| --- | --- | --- |
| **A. Scalar score** | Simple UI, fast sort | Hides dimensions, tail, conflict, UNKNOWN |
| **B. Risk vector** | Multidimensional, auditable | Comparison harder; needs governance |
| **C. Scenario set** | Tail-aware, narrative clarity | Combinatorial explosion |
| **D. Risk graph** | Contagion, dependency | Complexity, validation burden |
| **E. Hybrid** | Best of B+C+D | Implementation cost |

### 8.2 Recommendation `[PROPOSED]`

Adopt **Option E — Hybrid** as canonical architecture:

1. **`RiskVector`** — mandatory core: typed dimensions with value, uncertainty band, freshness, provenance refs.
2. **`RiskScenarioSet`** — mandatory for material assessments: named scenarios with triggers, mechanisms, impacts, falsification conditions.
3. **`RiskDependencyGraph`** — mandatory when ≥2 assets/providers/chains involved.
4. **Optional scalar `summary_index`** — explicitly labeled derived, with precision policy (§23), never used alone for decisions.

### 8.3 RiskVector conceptual schema `[PROPOSED]`

```text
RiskVector
  assessment_id
  subject_ref              # token, portfolio slice, mission, provider
  observation_cutoff       # point-in-time block/time
  assessment_timestamp
  validity_interval        # [valid_from, valid_until]
  dimensions[]             # RiskDimensionEntry
  conflicts[]              # RiskConflict refs
  unknown_dimensions[]     # explicit UNKNOWN list
  dependency_graph_ref
  scenario_set_ref
  provenance               # upstream artifact lineage
  formula_version
  producer_agent_id        # AGENT-11 runtime future
  epistemic_status         # not PROMOTED knowledge
  summary_index            # OPTIONAL derived scalar
  summary_index_precision  # e.g. "ordinal band HIGH" not "73.42%"
```

### 8.4 Missing and incomparable risks

- **Missing dimension:** record as `UNKNOWN`, not imputed zero.
- **Incomparable risks:** use `INCOMPARABLE` flag; no forced ranking without explicit commensurability proof.
- **Sparse evidence:** widen uncertainty bands; reduce precision; forbid false decimals.

---

## 9. Probability vs Uncertainty (Mandatory Deep Section)

### 9.1 Distinctions

| Concept | Meaning | Owned by |
| --- | --- | --- |
| **Probability** | Estimated likelihood of event E | Agent 11 (when justified) |
| **Confidence** | Belief in the assessment/calibration | Meta-uncertainty on assessment |
| **Evidence strength** | Warrant quality for claims | Agent 05 / Agent 07 |
| **Epistemic uncertainty** | Lack of knowledge | Explicit dimension |
| **Aleatoric uncertainty** | Inherent randomness | Scenario spread |
| **Model uncertainty** | Structural/model error | Model risk layer |
| **Data uncertainty** | Input quality gaps | Data risk layer |
| **Scenario uncertainty** | Which scenario applies | Regime / structural |
| **Irreducible uncertainty** | Cannot be eliminated | Must remain labeled |

### 9.2 Forbidden collapse

`confidence = probability` is **forbidden** unless formally defined with calibration evidence and governance approval.

### 9.3 Behavior when probability cannot be estimated

When evidence is insufficient:

1. Emit **severity + exposure + scenario** without point probability.
2. Use **ordinal bands** (NEGLIGIBLE / MATERIAL / SEVERE / CATASTROPHIC) with explicit criteria.
3. Preserve **UNKNOWN** on probability dimension.
4. Escalate to human review when severity is CATASTROPHIC or irreversibility is HIGH regardless of probability.
5. **Never** substitute `P = 0.5` or "medium" as default.

---

## 10. Severity Framework

| Severity class | Criteria (conceptual) |
| --- | --- |
| NEGLIGIBLE | De minimis financial/operational impact |
| MINOR | Recoverable loss, short recovery |
| MATERIAL | Significant drawdown or operational disruption |
| SEVERE | Large capital loss, long recovery, structural damage |
| CATASTROPHIC | Ruin, total loss, irreversible harm, systemic trigger |

**Dimensions of severity** (multidimensional, not single number):

- Financial loss (absolute and %)
- Drawdown depth and duration
- Probability of ruin (when estimable)
- Liquidity-adjusted loss (cost to exit under stress)
- Operational impact
- Systemic contagion potential
- Reversibility (see §13)
- Second/third-order effects

**Rule:** Expected value averaging must not erase CATASTROPHIC tail in summary views.

---

## 11. Exposure

### 11.1 Exposure types

| Type | Description |
| --- | --- |
| Direct | Capital in asset |
| Indirect | Via derivative, LP share, bridge wrapper |
| Hidden | Correlated book, same owner wallets |
| Correlated | Statistical co-movement |
| Common-cause | Shared provider, chain, LP |
| Temporal | Exposure window (event-bound) |
| Concentration | % of portfolio / liquidity |
| Dependency | Reliance on external service |
| Liquidity | Size relative to executable depth |
| Model | Reliance on specific model/feature |

### 11.2 Why `number of assets ≠ diversification`

N assets sharing: same chain, same stablecoin quote, same LP owner, same indexer, same narrative, same market maker — may have **near-unity effective exposure**. Agent 11 must compute **effective independence** via dependency graph, not asset count.

---

## 12. Time Horizon — Risk(t)

Every assessment must include:

| Field | Purpose |
| --- | --- |
| `observation_time` | When upstream data observed |
| `assessment_time` | When risk computed |
| `market_state_time` | Price/chain state reference |
| `validity_interval` | When assessment expires |
| `event_horizon` | When harm may materialize |

Horizon classes: instantaneous, intraday, event-window, medium-term, long-term structural.

`Risk(t)` is **not stationary**. Regime change invalidates historical `Risk(t-Δ)`.

---

## 13. Reversibility

| Class | Examples |
| --- | --- |
| Easily reversible | Temporary slippage, short vol spike |
| Partially reversible | Drawdown with recovery path |
| Difficult to reverse | Deep drawdown, reputational harm |
| Effectively irreversible | Exploit total loss, frozen token, key compromise |

Reversibility interacts with severity: **high severity + irreversible** triggers strongest escalation even at low probability.

---

## 14. Detectability

| Class | Description |
| --- | --- |
| Observable before event | Warning signals exist |
| Detectable during event | Real-time only |
| Detectable after event | Forensic only |
| Fundamentally difficult | Hidden privilege, novel exploit |

Low detectability + high severity → higher monitoring burden and human review triggers.

---

## 15. Risk Lead Time

Every material risk should characterize (when known):

- Detection lead time
- Escalation lead time
- Mitigation lead time
- Recovery time

**Contrast:** High severity + minutes lead time ≠ high severity + weeks lead time. Architecture must represent both.

---

## 16. Liquidity and Exit Risk (Major Section)

### 16.1 Nominal vs executable liquidity

| Metric | Source | Risk use |
| --- | --- | --- |
| Nominal TVL / volume | Agent 08 | Context only |
| Executable depth at size | Agent 08 + stress | Exit cost estimate |
| LP ownership / control | Agent 09/10 | Withdrawal risk |
| Route diversity | Agent 08 | Single-path failure |
| Security sell restrictions | Agent 10 | Hard exit block |
| Time-to-exit under stress | Agent 11 scenario | Primary exit risk output |

### 16.2 Rejected shortcut

`liquidity high → exit safe` is **architecturally rejected**.

Required checks before low exit-risk label:

1. Executable depth at **stated position size**
2. LP concentration and owner privileges
3. Security transfer restrictions
4. Stress scenario (§18) liquidity shock
5. Cross-venue fragmentation

---

## 17. Scenario Intelligence

### 17.1 Scenario ≠ Prediction

Scenarios are **conditional narratives** for planning and stress — not forecasts.

### 17.2 Scenario structure `[PROPOSED]`

```text
RiskScenario
  scenario_id
  name                     # e.g. "LP rug partial exit"
  tier                     # BASE | ADVERSE | SEVERE | EXTREME | STRUCTURAL_FAILURE | NOVEL
  trigger                  # what initiates
  assumptions[]            # explicit
  exposure_ref
  mechanism                # causal pathway
  impact                   # severity framing
  duration
  recovery
  probability_estimate     # OPTIONAL — only if justified
  confidence_in_scenario   # meta
  falsification_condition  # what would refute
  upstream_artifact_refs[]
  validity_interval
```

### 17.3 Scenario trees

Conditional branches: IF trigger A THEN scenario B ELSE scenario C. Novel/unknown scenario tier mandatory for black-swan class.

---

## 18. Stress Testing (Conceptual Design)

### 18.1 Stress catalog

| Stress | Domains affected |
| --- | --- |
| Price shock (-30%, -50%, -90%) | Market, liquidity |
| Liquidity shock (50% depth removal) | Liquidity, exit |
| Volume collapse | Market, detection |
| Volatility explosion | Market, execution (future) |
| Provider outage | Data, all downstream |
| Chain outage / reorg | On-chain, finality |
| Security incident (exploit) | Security, total loss |
| Oracle failure | Counterparty, price |
| Stablecoin depeg | Systemic, correlation |
| Market-wide crash | Systemic, contagion |
| Correlated asset crash | Concentration |
| Model failure | Model risk |
| Data corruption | Data risk, all |
| Execution failure (future) | Execution |

### 18.2 Simultaneous failure rule

Architecture **must** support **compound stress** — e.g. price shock + liquidity withdrawal + provider outage. Single-factor-only stress tests are insufficient for tail analysis.

`[PROPOSED]` `StressTest` + `StressTestResult` objects with versioned assumptions — see §47.

---

## 19. Correlation and Contagion (Major Section)

### 19.1 Correlation types

| Type | Description |
| --- | --- |
| Statistical correlation | Co-movement in returns |
| Structural correlation | Shared architecture |
| Causal dependency | A failure causes B |
| Common provider | Same data source |
| Common chain | Same L1/L2 |
| Common liquidity | Same pool/MM |
| Common wallet | Same controller |
| Common narrative | Reflexive selling |
| Common infrastructure | RPC, indexer, cloud |

**Invariant:** `CORRELATION ≠ CAUSATION`

### 19.2 RiskDependencyGraph `[PROPOSED]`

```text
RiskDependencyGraph
  nodes[]                  # assets, providers, chains, wallets, models
  edges[]
    type                   # PROVIDES_DATA | SHARES_LIQUIDITY | CONTROLS | CORRELATES | ...
    strength               # qualitative or bounded numeric
    evidence_refs[]
    independence_claim     # PROVEN | ASSUMED | UNKNOWN
  common_cause_clusters[]
```

Used for: contagion scenarios, false diversification detection, provider concentration limits (conceptual).

---

## 20. Concentration Risk

| Concentration type | Detection source |
| --- | --- |
| Token / wallet | Agent 09 |
| Liquidity / LP | Agent 08, 09, 10 |
| Chain | Portfolio + dependency graph |
| Provider / data source | Agent 07 |
| Model / feature | Agent 13 |
| Infrastructure | Agent 03, 14 |
| Narrative / sector | Agent 08 (weak signal) |

Hidden concentration: same beneficial owner across wallets; same indexer backing "independent" APIs.

---

## 21. Conflicting Risk Signals

### 21.1 No automatic averaging

Examples requiring `RiskConflict`:

| Signal A | Signal B | Required behavior |
| --- | --- | --- |
| Market risk LOW | Security risk HIGH | Preserve both; no net score |
| Liquidity HIGH | Exitability UNKNOWN | Conflict; no "liquid" label |
| Data quality HIGH | Model confidence LOW | Separate dimensions |
| Historical vol LOW | Structural fragility HIGH | Scenario emphasis |

### 21.2 RiskConflict vs Contradiction (see §49)

`RiskConflict` — orthogonal risk dimensions in tension.

`ContradictionCase` (Agent 05) — incompatible truth claims about same proposition.

They may co-occur but **must not merge** into one object type.

---

## 22. Risk Aggregation

| Option | When meaningful | When dangerous |
| --- | --- | --- |
| Weighted score | Commensurate dimensions, explicit weights, governance | Heterogeneous risks, UNKNOWN dims |
| Risk vector | Always (canonical) | None if complete |
| Scenario distribution | Tail-aware decisions | False precision in probabilities |
| Risk graph | Systemic analysis | Over-graphing sparse evidence |
| Hybrid | Production-grade | Complexity |

**Rule:** Aggregation requires **commensurability proof** or explicit ordinal-only merge. Default: **no aggregation** across domains — present **RiskProfile** with side-by-side vectors and conflicts.

---

## 23. False Precision

Forbidden without evidence: `73.42% risk`.

Rules `[PROPOSED]`:

- Significant digits capped by evidence quality
- Confidence intervals mandatory for numeric probability
- Qualitative bands when N < threshold or high model uncertainty
- UNKNOWN dimensions exclude from numeric aggregate
- Sparse evidence → widen bands, not point estimates

Agent 07 flagged `Evidence.assurance` 0–100 as **scalar collapse risk** — Risk Intelligence must not replicate this pattern on risk outputs.

---

## 24. Risk Budgets (Conceptual Only)

Exposure limits, concentration limits, drawdown limits, liquidity limits, uncertainty budgets, model-risk budgets, dependency budgets, provider concentration limits, operational risk budgets.

**Agent 11 designs measurement inputs.** **Governance/human** owns limit adoption and enforcement. **Do not implement limits** in this mission.

---

## 25. Risk Appetite vs Measurement vs Policy vs Decision

| Concept | Owner (future) |
| --- | --- |
| Risk measurement | Agent 11 (analytics) |
| Risk appetite | Human / governance (L2) |
| Risk policy | Agent 04 + human |
| Risk limits | Governance + enforcement runtime |
| Decision | Human / future governed decision plane — **not** Agent 11 |

---

## 26. Risk vs Opportunity

```text
Opportunity ≠ Return
Opportunity ≠ Low Risk
High Opportunity + High Risk = legitimate state
```

Architecture must prevent upside attractiveness from suppressing risk dimensions in composite "opportunity scores."

---

## 27. Expected Value

EV analysis permitted as **one scenario output** when probability justified.

**Rejected shortcut:** `positive EV → safe`

Must accompany: tail scenarios, ruin probability (if estimable), liquidity-adjusted exit, model uncertainty, asymmetric payoff disclosure.

---

## 28. Drawdown and Ruin

Analyze: max drawdown, expected drawdown, conditional drawdown, recovery time, probability of ruin, path dependency, sequence risk.

Identical average returns → different risk profiles via path. Agent 12 quant outputs feed Agent 11 interpretation; Agent 11 does not own backtest execution.

---

## 29. Path Dependency

Liquidation cascades, compounding losses, sequential provider failures, margin-like mechanisms, sequential model failures — require **path-aware scenarios**, not terminal-state-only analysis.

---

## 30. Regime Change

Market, liquidity, volatility, narrative, regulatory, model regimes. `P(risk | regime)` may shift discontinuously.

Historical estimates **invalidate** on regime transition unless re-validated. `[PROPOSED]` `RiskInvalidation` on regime change events (§50).

---

## 31. Model Risk Layer

Dedicated interface to Agent 13:

- Model disagreement → widen uncertainty
- Calibration metadata → confidence vs probability separation
- Drift signals → assessment expiry
- Adversarial robustness → stress test inputs
- Ensemble correlation → false independence flag

**Forbidden:** `AI confidence → risk truth`

---

## 32. Data Risk Interface (Agent 07)

| Agent 07 | Agent 11 |
| --- | --- |
| Data quality vector | Risk from quality gaps |
| Provider identity | Provider concentration risk |
| Freshness / staleness | Assessment TTL / invalidation |
| Reconciliation status | Confidence in risk inputs |
| Fitness-for-purpose | Whether risk calc permitted |

Handoff `[PROPOSED]`: `DataQualityAssessment` → `DataRiskCharacterization` with explicit UNKNOWN propagation rules (§43).

---

## 33. Market Risk Interface (Agent 08)

| Agent 08 | Agent 11 |
| --- | --- |
| MarketSignal, LiquidityAssessment | Market + liquidity risk dimensions |
| Regime label | Regime-conditional scenarios |
| Anomaly flags | Elevated tail scenarios |

**Invariant:** Market interpretation must not silently become risk verdict. CMI supplies **inputs**; RI produces **loss framing**.

---

## 34. On-Chain Risk Interface (Agent 09)

| Agent 09 | Agent 11 |
| --- | --- |
| OnChainObservation, concentration metrics | Concentration + contagion risk |
| Finality / reorg labels | Timing + validity risk |
| Bridge facts | Dependency + depeg scenarios |

Never rewrite on-chain observations.

---

## 35. Security Risk Interface (Agent 10)

| Agent 10 | Agent 11 |
| --- | --- |
| SecurityFinding, SecurityAssessment | Capital loss, exit block scenarios |
| Honeypot hypothesis status | Irreversible loss tier |
| SecurityConflict | May map to RiskConflict + epistemic Contradiction |

Example: Agent 10 `SUPPORTED HONEYPOT HYPOTHESIS` → Agent 11 `CATASTROPHIC EXIT / CAPITAL-LOSS RISK` — **without** altering security finding.

---

## 36. Epistemic Interface (Agent 05)

Risk assessments are **not** promoted knowledge by default.

Must preserve: evidence provenance, uncertainty, contradictions, hypothesis status, verification status, freshness.

Risk must not replace epistemology. Future risk artifacts may reference `Evidence`, `Claim`, `Hypothesis`, `ContradictionCase` — not substitute for them.

---

## 37. Research Methodology Interface (Agent 06)

- Risk hypotheses researched under Agent 06 methodology
- Stress test design requires falsification criteria
- Negative results preserved
- Scenario assumptions documented
- Leakage attestation for any historical risk metrics

---

## 38. Future Quant Interface (Agent 12)

**Agent 11 → Quant:** risk scenarios, constraints, feature risk flags, leakage warnings.

**Quant → Agent 11:** backtest distributions, drawdown paths, model outputs — interpreted as **inputs with model risk**, not ground truth.

Agent 11 does **not** absorb: backtesting, portfolio optimization, statistical modeling, execution algorithms.

---

## 39. AI/ML Interface (Agent 13)

Model outputs consumed with: disagreement vectors, calibration status, drift flags, adversarial test results.

Risk interface defines **loss-relevant interpretation** — not model training or selection.

---

## 40. QA / Verification Interface (Agent 16)

Future verification targets:

- Risk calculation golden vectors
- Scenario invariant checks
- Stress test reproducibility
- UNKNOWN propagation behavior
- Conflict non-averaging
- Aggregation commensurability rules
- Numerical stability
- Point-in-time correctness
- Staleness expiry behavior

---

## 41. Red Team Interface (Agent 19)

Attack surfaces:

- Risk underestimation
- False diversification
- Hidden correlation
- False precision
- Missing tail risk
- Stale data treated as live
- Optimistic scenario omission
- Model blindness
- Liquidity illusion
- Security-risk suppression
- Correlated model failure
- Scalar score gaming
- UNKNOWN → LOW imputation

---

## 42. Risk Propagation

```text
Data Condition (Agent 07)
  → Market / OnChain / Security Observation (Agents 08–10)
  → Risk Factor identification (Agent 11)
  → Risk Scenario construction (Agent 11)
  → Risk Assessment / RiskVector (Agent 11)
  → Risk Aggregation / RiskProfile (Agent 11 — optional, governed)
  → Decision Input (human / future decision plane)
  → [STOP — Agent 11 does not cross]
  → Decision
  → Execution (forbidden today)
```

**Propagation MUST STOP** before Decision. No automatic edge from `RiskAssessment` to `ALLOW`/`DENY` trade.

---

## 43. UNKNOWN Propagation (Mandatory)

| Upstream | Forbidden | Required |
| --- | --- | --- |
| Liquidity = UNKNOWN | Liquidity Risk = LOW | Exit risk = UNKNOWN or CONFLICT |
| Security = UNKNOWN | Security Risk = LOW | Capital loss scenario = UNKNOWN tier |
| Provider = UNKNOWN | Data risk = LOW | Assessment validity shortened |
| Probability inestimable | P = 0.5 default | Ordinal severity only |
| Missing dimension | Impute 0 | List in `unknown_dimensions[]` |

Default: **fail closed on actionability**, not fail closed on **analysis** — analysis may proceed with explicit UNKNOWNs.

---

## 44. Stale Risk

Risk assessments decay via:

- TTL / validity_interval expiry
- Freshness policy (inherit from Agent 07)
- Event invalidation (§50)
- Regime invalidation (§30)
- Provider invalidation
- Model version change

Stale assessment ≠ current assessment. Must be labeled `STALE` or `SUPERSEDED`.

---

## 45. Point-in-Time Correctness

Every `RiskAssessment` preserves:

- observation timestamp
- assessment timestamp
- market state timestamp
- block height (where applicable)
- data cutoff
- model version
- feature version
- scenario version
- validity interval

Look-ahead contamination forbidden — coordinated with Agent 06/12 leakage rules.

---

## 46. Risk Versioning

Immutable/versioned: risk definitions, formulas, models, thresholds, scenario definitions, aggregation methods.

Historical assessments reproducible from version pins + input artifact hashes.

---

## 47. Risk Object Model (Conceptual — Not Implemented)

| Object | Purpose | Authority | Lifecycle highlights |
| --- | --- | --- | --- |
| **RiskFactor** | Named risk driver | Agent 11 analytic | DETECTED → CHARACTERIZED |
| **RiskExposure** | What is at stake | Agent 11 | Tied to subject_ref |
| **RiskObservation** | Risk-relevant observed fact | Often upstream; RI may derive | Links to 08–10 |
| **RiskScenario** | Conditional outcome narrative | Agent 11 | Versioned; falsifiable |
| **RiskAssessment** | Point-in-time evaluation | Agent 11 | ACTIVE → EXPIRED/SUPERSEDED |
| **RiskConflict** | Non-averagable tension | Agent 11 | OPEN until resolved or retained |
| **RiskDependency** | Edge in dependency graph | Agent 11 | Evidence-linked |
| **RiskEvent** | Invalidation trigger | System / Agent 11 | Causes EXPIRED/ESCALATED |
| **StressTest** | Defined shock specification | Agent 11 design | Versioned |
| **StressTestResult** | Outcome under shock | Agent 11 | Linked to assessment |
| **RiskVector** | Multidimensional representation | Agent 11 | Canonical output |
| **RiskDistribution** | Scenario probability spread | Agent 11 | Optional |
| **RiskLimit** | Proposed bound | Governance — not Agent 11 enforce |
| **RiskBudget** | Allocated risk capacity | Governance | Conceptual |
| **RiskProfile** | Portfolio/subject aggregate | Agent 11 | Conflicts preserved |
| **RiskAssessmentVersion** | Immutable snapshot | Agent 11 | Audit |
| **RiskInvalidation** | Why assessment died | Agent 11 / events | Audit |
| **RiskIncident** | Realized loss event | Human/post-hoc | Feedback loop |
| **RiskMitigationProposal** | Suggested reduction | Agent 11 PROPOSE only | Not enforcement |

All objects: provenance, uncertainty, timestamps, freshness, evidence linkage — **none** imply decision authority.

---

## 48. Risk Lifecycle

`[PROPOSED]` lifecycle (alternatives considered: simpler 3-state — rejected as insufficient for audit):

```text
DETECTED
  → CHARACTERIZED
  → ASSESSED
  → CHALLENGED (Red Team / contradiction)
  → STRESSED (stress test applied)
  → VALIDATED / UNVALIDATED (Agent 16)
  → ACTIVE | EXPIRED | SUPERSEDED | REFUTED
```

Terminal states require reason + timestamp. REFUTED requires epistemic linkage if claim-level refutation.

---

## 49. RiskConflict vs Epistemic Contradiction

| | RiskConflict | ContradictionCase (Agent 05) |
| --- | --- | --- |
| **Nature** | Orthogonal dimensions in tension | Incompatible truth claims |
| **Example** | Low market risk + high security risk | Evidence A vs B on same claim |
| **Resolution** | Present both; decision layer weighs | Epistemic investigation |
| **Object merge** | **Forbidden** | Separate types |

Cross-link allowed: same incident may spawn both.

---

## 50. Risk Events (Invalidation)

| Event | Effect |
| --- | --- |
| Liquidity withdrawal | Invalidate liquidity/exit assessments |
| Ownership change | Invalidate concentration/security |
| Contract upgrade | Invalidate security-dependent risk |
| Exploit | Catastrophic realization; post-hoc incident |
| Chain reorg | Invalidate on-chain-timestamped assessments |
| Provider outage | Data risk escalation; expiry |
| Market crash | Regime invalidation |
| Stablecoin depeg | Systemic scenario activation |

`[PROPOSED]` event-driven subscription model for assessment expiry — not implemented.

---

## 51. Common-Cause Failure (Mandatory Expert Section)

**Question:** What if Agent 07 → Agent 08, Agent 07 → Agent 09, Agent 07 → Agent 11 all consume the same flawed provider?

**Answer:** Apparent agent independence is **false**. Architecture must track:

```text
Correlation of Information  ≠  Correlation of Markets  ≠  Correlation of Models
```

`[PROPOSED]` `InformationDependencyGraph` — provider/upstream lineage on every risk input. Red Team (Agent 19) must attack "three agents agree" consensus.

---

## 52. Independence Forms

| Independence | Meaning |
| --- | --- |
| Data | Different raw observations |
| Provider | Different upstream suppliers |
| Model | Different model families |
| Agent | Different evidence paths |
| Methodology | Different inference methods |
| Temporal | Non-overlapping sample windows |

`three agents agree` ≠ independent confirmation without path analysis.

---

## 53. Risk of the AI Council Itself

Multi-agent system risks:

- Correlated hallucination
- Common prompt bias
- Common source bias
- Authority cascade (orchestrator → truth)
- Consensus illusion
- Confirmation bias
- Automation bias
- Model monoculture
- Hidden shared dependencies

The council is a **risk-bearing system**. Agent 11 should assess **meta-risk** on synthesized orchestrator outputs — without claiming orchestrator outputs as ground truth.

---

## 54. Human Oversight (Architectural Triggers)

Human intervention should be **architecturally suggested** (not implemented) when:

- CATASTROPHIC severity
- High uncertainty + material exposure
- Novel risk tier (NOVEL scenario)
- Unresolved RiskConflict on material subject
- Irreversible exposure
- Model disagreement above threshold
- Provider disagreement
- Tail event in stress test
- Scalar summary conflicts with vector tail

---

## 55. Risk Communication

Communicate: known, unknown, plausible outcomes, why it matters, probability (if justified), severity, uncertainty, horizon, evidence, assumptions, invalidation conditions.

Avoid: alarmism, false reassurance, precision without warrant.

---

## 56. Risk Explanation Checklist

Future risk report must answer:

1. What is the risk?
2. What causes it?
3. What evidence supports it?
4. What is uncertain?
5. Potential impact?
6. Time horizon?
7. Reversibility?
8. Detectability?
9. Dependencies?
10. Invalidation conditions?
11. Worsening scenarios?
12. What should authorized layers consider?

---

## 57. Risk Scoring — Critical Forensics

| Approach | Benefits | Failure modes | Governance risk |
| --- | --- | --- | --- |
| Scalar score | UI simplicity | Tail hiding, gaming | **High** — decision collapse |
| Vector | Auditability | Complexity | Low if no auto-decision |
| Ordinal class | Honest uncertainty | Less granularity | Low |
| P × Severity | Intuitive | False precision in P | Medium |
| Expected shortfall | Tail aware | Model dependent | Medium |
| Scenario loss | Narrative + tail | Many scenarios | Low |
| Distributional | Complete | Data hungry | Medium |
| Hybrid | Best practice | Implementation cost | Low with gates |

### Conclusion `[PROPOSED]` — not adopted governance

**Canonical:** RiskVector + RiskScenarioSet + optional ordinal `summary_band`.

**Optional derived scalar:** permitted only with: precision policy, explicit "NOT FOR DECISION" label, tail disclosed separately, conflicts not averaged.

**Rejected as canonical:** single 0–100 `risk_score` driving any automated gate.

---

## 58. Risk Thresholds

Thresholds for **classification and escalation** may exist; they must **never** silently map to BUY/SELL.

`[PROPOSED]` hysteresis, confidence bounds, uncertainty bands, event-triggered overrides — all require human governance adoption.

---

## 59. Paper-Only Boundary

`[VERIFIED]` AHOS org is paper-only; live trading globally denied (`ahos_org/policy.py`).

Risk Intelligence: **ANALYTICAL / NON-EXECUTING**.

Future execution transition requires separate L2 governance — not inferable from this document.

---

## 60. Decision Boundary

### Agent-11 MAY

- Identify and characterize risks
- Compare scenarios
- Quantify where justified
- Preserve uncertainty and conflicts
- Identify dependencies and tail risks
- Challenge assumptions
- Propose mitigations (PROPOSE class)

### Agent-11 MUST NOT

- Approve/reject trades
- Execute trades
- Issue BUY/SELL
- Promote knowledge
- Verify own assessments as independent truth
- Change policy or grant authority
- Activate agents
- Bypass TCB
- Access credentials, wallets, live trading

---

## 61. Authority Collapse Analysis

### 61.1 Dangerous chain

```text
Risk Score → Decision → Execution
```

**Prevention architecture:**

1. No code path from `RiskAssessment` to trade execution
2. Scalar summary forbidden as sole decision input
3. Decision plane separate principal class from risk analyst
4. Human gate on material exposure
5. Audit trail: risk artifact IDs ≠ decision artifact IDs
6. Master Orchestrator synthesis ≠ automatic decision

### 61.2 Secondary collapse

```text
Risk Agent → Risk Policy → Risk Limit → Trade Rejection
```

Policy and limits owned by **governance (Agent 04 + human)** — not Agent 11. Agent 11 supplies **measurement**; enforcement runtime is separate bounded component with its own authorization.

---

## 62. Dual-19 Conflict

`DUAL_19 = UNRESOLVED` — preserved.

| Plane | Relevant IDs | Ambiguity |
| --- | --- | --- |
| A (Slice 1) | `agent.scoring-science`, `agent.paper-trading` | Thematic overlap with risk/scoring |
| D (Blueprint) | `agent.org.11-risk-intelligence` | Not in CANONICAL_AGENT_IDS |
| D overlap note | 08–12 market/chain/risk/quant | Documented in PLANNED_19_AGENT_MAP |

Agent 11 identity is **Plane D documentary** until human L2 maps to Plane A or federates identity (DEFERRED).

**Not resolved in this mission.**

---

## 63. Agent One

`AGENT_ONE = NOT IMPLEMENTED / FUTURE_NON_AUTHORITY_ROOT`

Future Agent One may: request risk assessments, compare with other reports, detect contradictions, synthesize recommendations.

Agent One must **not**: treat risk score as truth, auto-execute on risk threshold, override risk UNKNOWNs, become risk authority.

---

## 64. Master Orchestrator Boundary

Master Orchestrator may request, compare, synthesize, recommend next missions.

Must **not** become technical source of truth because it synthesizes. Risk Intelligence remains evidence-bearing analysis with provenance — orchestrator output is **L5/L3 synthesis**, not L0.

---

## 65. Security Against Risk Manipulation

Threats:

- Optimistic input manipulation
- Selective evidence (omit adverse scenarios)
- Score/threshold gaming
- Provider manipulation
- Model manipulation
- False diversification
- Hidden correlation
- Stale risk suppression
- Uncertainty suppression

Mitigations `[PROPOSED]`: provenance on all inputs, conflict preservation, Red Team, independent verification, version pinning, UNKNOWN fail-closed on actionability.

---

## 66. Failure Modes

| Mode | Description |
| --- | --- |
| Underestimation | Tail ignored |
| Overestimation | Paralysis, false alarms |
| False precision | Decimal scores without warrant |
| Missing tail | Average-score collapse |
| Stale assessment | Live decision on expired risk |
| Correlated errors | Common provider undetected |
| Hidden exposure | Dependency graph incomplete |
| Wrong identity | Risk on wrong token |
| Wrong timestamp | Look-ahead / stale mix |
| Wrong scenario | Mis-specified mechanism |
| Model drift | Historical risk invalid |
| Provider failure | Silent degradation |
| Data poisoning | Adverse input |
| Scenario omission | Black swan excluded |
| Aggregation distortion | Incommensurate merge |
| Uncertainty collapse | UNKNOWN → zero |
| Authority collapse | Risk → decision |

---

## 67. Adversarial Risk Cases (Conceptual)

| # | Case | Expected architectural behavior |
| --- | --- | --- |
| 1 | High liquidity + malicious contract | HIGH security/capital risk; CONFLICT with liquidity; no net "safe" |
| 2 | Low liquidity + honest contract | HIGH exit risk; security not conflated with exit |
| 3 | High volatility + strong fundamentals | Separate vol vs structural; scenario tree |
| 4 | Low volatility + hidden structural fragility | Stress test reveals tail; do not trust vol alone |
| 5 | Multiple providers, same wrong data | Information dependency exposed; single effective source |
| 6 | Three agents, one source | Meta-risk flag; not triple confirmation |
| 7 | High EV + catastrophic tail | Tail scenario mandatory; EV not sufficient |
| 8 | Unknown security + attractive market | CONFLICT; actionability UNKNOWN |
| 9 | Stable history + regime shift | Regime invalidation; historical risk STALE |
| 10 | Diversified assets, same LP | Dependency graph shows concentration |
| 11 | Strong model confidence + distribution shift | Model risk HIGH; confidence ≠ safety |
| 12 | Low measured risk + missing data | UNKNOWN propagation; no LOW label |
| 13 | High market score + severe exit risk | RiskConflict preserved |
| 14 | High security confidence + unknown ops dependency | Separate dimensions |
| 15 | High liquidity + LP controlled by one actor | Exit risk ELEVATED despite nominal liquidity |

---

## 68. Risk Matrices (Conceptual)

### Matrix A — Risk Type × Evidence Type

| | Direct observation | Derived metric | Hypothesis | Model output | UNKNOWN |
| --- | --- | --- | --- | --- | --- |
| Market | Price, vol | Beta, corr | Regime shift | Forecast | Gap |
| Liquidity | Depth | TVL | Fake LP | Impact model | Exit time |
| Security | Bytecode | Heuristic | Honeypot | Classifier | Privilege |
| On-chain | Tx | Holder % | Cluster | Graph ML | Identity |
| Data | Record | Quality score | Bias | Imputation | Missing |
| Model | Backtest | CV error | Drift | Ensemble | Structure |
| Operational | Log | Uptime | Failure mode | — | Blast radius |
| Systemic | Event | Correlation | Contagion | Network | Hidden link |
| Tail | Historical extrema | VaR/ES* | Black swan | Sim | Novel |

*VaR/ES as quant outputs (Agent 12) — not sole risk metric.

### Matrix B — Risk Type × Agent Owner

| Risk type | Primary producer | Risk framer | Verifier |
| --- | --- | --- | --- |
| Data | 07 | 11 | 16 |
| Market | 08 | 11 | 16 |
| On-chain | 09 | 11 | 16 |
| Security | 10 | 11 | 16 |
| Model | 13 | 11 | 16 |
| Quant path | 12 | 11 | 16 |
| Operational | 03/14 | 11 | 16 |
| Systemic/tail | 11 (synthesis) | 11 | 16/19 |

### Matrix C — Risk Type × Uncertainty

Rows: market, liquidity, security, … Columns: epistemic, aleatoric, model, data, irreducible — each cell: typical dominant uncertainty type.

### Matrix D — Risk Type × Time Horizon

Instantaneous (execution/MEV future), intraday (vol/gap), event-window (unlock), medium (trend), long (structural/regulatory).

### Matrix E — Risk Type × Severity

Maps which risk types most often reach CATASTROPHIC (security exploit, systemic depeg, total loss).

### Matrix F — Risk Type × Detectability

Security privilege often low detectability; market vol higher; data staleness medium.

### Matrix G — Risk Type × Reversibility

Slippage reversible; exploit irreversible.

### Matrix H — Risk Type × Dependency

Systemic/contagion highest dependency degree; idiosyncratic market lower.

### Matrix I — Risk Type × Decision Boundary

All types: Agent 11 stops at assessment; none authorize execution.

### Matrix J — Risk Type × Verification Requirement

Tail/systemic/security: mandatory Red Team + independent verification before high-stakes human decision.

---

## 69. Contradiction Analysis (Architectural)

| ID | Conflict | Source | Why it matters | Status | Proposed resolution | Human? |
| --- | --- | --- | --- | --- | --- | --- |
| **RI-C01** | Agent 08 §34 says Agent 11 owns "risk decisions" | This mission §60 forbids decisions | Wording collapse | `UNRESOLVED` | Agent 11 owns **framing** not **decisions** | Yes |
| **RI-C02** | Slice 1 `RiskLevel` on tasks vs financial RI | `ahos_org/tasks.py` vs Plane D 11 | Name collision | `UNRESOLVED` | Rename or namespace (`org_task_risk` vs `portfolio_risk`) | Yes |
| **RI-C03** | `agent.scoring-science` vs `agent.org.11` | Registry vs blueprint | Scoring may absorb risk | `UNRESOLVED` | Explicit plane mapping | Yes |
| **RI-C04** | Scalar `Evidence.assurance` vs vector risk | Agent 07, epistemic.py | False precision heritage | `UNRESOLVED` | Vector-only risk handoff | Yes |
| **RI-C05** | Agent 10 "Agent 11 probability" | Agent 10 §42 handoff table | Implies RI owns security probability | `PARTIALLY RESOLVED` | Joint: 10=capability, 11=exposure×scenario | No |
| **RI-C06** | CMI "exitability verdict" vs RI ownership | Agent 08 LiquidityAssessment | Domain leak | `UNRESOLVED` | CMI: depth facts; RI: exit risk verdict | Yes |
| **RI-C07** | RiskConflict vs ContradictionCase merge pressure | Agent 05 vs this doc | Object model collision | `UNRESOLVED` | Separate types, cross-link | Yes |
| **RI-C08** | Orchestrator synthesis → decision | Agent 03 authority collapse | Chat governance gap | `UNRESOLVED` | Explicit synthesis artifact type | Yes |
| **RI-C09** | Paper-trading role vs RI limits | Slice 1 registry | Execution path confusion | `UNRESOLVED` | Paper sim ≠ risk enforcement | Yes |
| **RI-C10** | HD-12 quarantine authority (Agent 10) | Agent 10 | Who blocks actionability | `UNRESOLVED` | Governance owns quarantine policy | Yes |
| **RI-C11** | VaR/quant metrics as "risk truth" | Industry habit vs org doctrine | Quant collapse | `UNRESOLVED` | Agent 12 produces; Agent 11 interprets | No |
| **RI-C12** | Dual-19 identity for Agent 11 | Registry model | Authorization ambiguity | `UNRESOLVED` | Deferred federation | Yes |

---

## 70. Human Decisions Required

Prioritized `[PROPOSED]` — **not adopted**:

| Priority | ID | Decision | Options |
| --- | --- | --- | --- |
| P0 | HD-01 | Canonical risk representation | Vector+scenario hybrid vs scalar-only |
| P0 | HD-02 | Risk-to-decision boundary enforcement | Code deny tokens vs policy-only |
| P0 | HD-03 | Dual-19 mapping for Agent 11 | Plane D only vs map to Slice 1 role |
| P1 | HD-04 | Scalar summary policy | Forbidden vs ordinal band vs gated numeric |
| P1 | HD-05 | UNKNOWN propagation rules | Formal spec adoption |
| P1 | HD-06 | RiskConflict vs ContradictionCase | Separate vs unified with tags |
| P1 | HD-07 | Tail risk mandatory disclosure | Always separate scenario vs optional |
| P1 | HD-08 | Aggregation commensurability | When merge allowed |
| P2 | HD-09 | Risk appetite owner | Human-only vs governance board |
| P2 | HD-10 | Stress test governance | Required scenarios catalog |
| P2 | HD-11 | Provider independence proof | Required for multi-source confirmation |
| P2 | HD-12 | Quarantine/actionability authority | TSI / RI / human |
| P2 | HD-13 | Human escalation triggers | Threshold adoption |
| P2 | HD-14 | Future Agent One risk consumption | Read-only vs recommend |
| P2 | HD-15 | AHOS integration boundary | Mediated artifact exchange |
| P3 | HD-16 | TCB artifact types for risk | Extend epistemic.py vs separate module |
| P3 | HD-17 | Risk limit enforcement plane | Future runtime owner |

Label: **ARCHITECTURAL RECOMMENDATION** unless future L2 record states **ADOPTED DECISION**.

---

## 71. Future Mission Map (STATE ONLY — DO NOT EXECUTE)

1. **Agent-12 — Quant Intelligence Architecture** (backtest → risk interpretation boundary)
2. **Agent-13 — AI/ML Intelligence Architecture** (model risk interface)
3. **Agent-16 — Risk Golden Vectors** (verification specs)
4. **Agent-19 — Risk Red Team** (adversarial cases §67 implementation)
5. **Agent-05 + Agent-11 — Epistemic/Risk Boundary** (Contradiction vs RiskConflict)
6. **Agent-07 + Agent-11 — Data/Risk Boundary** (formal handoff schema)
7. **Agent-08 + Agent-11 — Market/Risk Boundary** (resolve RI-C01, RI-C06)
8. **Agent-09 + Agent-11 — On-Chain/Risk Boundary**
9. **Agent-10 + Agent-11 — Security/Risk Boundary**
10. **Risk Object Schema Design** (TCB extension proposal)
11. **Stress-Test Governance Design**
12. **Risk Dependency Graph Design**
13. **Information Dependency / Common-Cause Model**

---

## 72. Implementation Status Forensic Summary

| Component | Status | Evidence |
| --- | --- | --- |
| Risk Intelligence runtime | `[UNKNOWN]` / not present | No module in repo |
| RiskVector / RiskAssessment types | `[PLANNED]` | This document |
| Slice 1 `RiskLevel` (task governance) | `[IMPLEMENTED]` | `ahos_org/models.py` |
| Global trading deny | `[IMPLEMENTED]` `[TESTED]` | `ahos_org/policy.py` |
| Epistemic core | `[IMPLEMENTED]` `[TESTED]` | `agent_org/epistemic.py` |
| Agent 07–10 upstream boundaries | `[DOCUMENTED]` | Peer architecture docs |
| Agent 11 blueprint row | `[PLANNED]` | `PLANNED_19_AGENT_MAP.md` |
| Dual-19 resolution | `[CONTRADICTED]` / unresolved | `AGENT_REGISTRY_MODEL.md` |
| Agent One | `[DOCUMENTED]` not implemented | `AGENT_ONE_STATUS` |
| AHOS connection | `[BLOCKED]` | Policy deny |
| This architecture document | `[PROPOSED]` | TASK-20260914-011 deliverable |

---

## 73. Mission Closeout

```text
MISSION_STATUS = RISK_INTELLIGENCE_ARCHITECTURE_ANALYSIS_COMPLETE_WITH_GAPS
AGENT_ID = AGENT-11
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
RECOMMENDED_NEXT_MISSION = STATE ONLY — DO NOT EXECUTE
```

**Gaps explicitly retained:** no runtime validation; Dual-19 unresolved; RI-C01/C06 wording conflicts with peer docs; scalar assurance heritage; quarantine authority; TCB type extension undecided; full test suite not re-run this mission.

---

*End of AGENT_11_RISK_INTELLIGENCE_ARCHITECTURE.md*
