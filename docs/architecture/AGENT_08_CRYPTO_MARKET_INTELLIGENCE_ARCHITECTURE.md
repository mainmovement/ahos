# Agent Organization Crypto Market Intelligence Architecture

```text
DOCUMENT_ID      = AGENT_08_CRYPTO_MARKET_INTELLIGENCE_ARCHITECTURE
MISSION_ID       = TASK-20260914-008
VERSION          = 0.1.0
STATUS           = PROPOSED / READ_ONLY_MARKET_INTELLIGENCE_ARCHITECTURE
AUTHORITY        = NONE CREATED
RUNTIME_EFFECT   = NONE
AHOS_EFFECT      = NONE
AGENT_ID         = AGENT-08 (agent.org.08-crypto-market-intelligence — documentary)
DIRECT_COMMANDER = MASTER ORCHESTRATOR
PARENT           = MASTER ORCHESTRATOR
DUAL_19          = UNRESOLVED
AGENT_ONE        = NOT_IMPLEMENTED / FUTURE_NON_AUTHORITY_ROOT
```

This document is a **design and architecture artifact** produced by AGENT-08 under explicit activation for TASK-20260914-008. It does not implement market intelligence runtime, adopt governance, grant authority, modify AHOS, connect providers or exchanges, or promote knowledge. Facts cite repository evidence with explicit classification labels (`[IMPLEMENTED]`, `[DOCUMENTED]`, `[PROPOSED]`, `[UNKNOWN]`). Architectural recommendations are labeled `[PROPOSED]`.

**Critical honesty constraint:**

```text
MARKET OBSERVATION          ≠ MARKET TRUTH
PRICE MOVE                  ≠ OPPORTUNITY
VOLUME SPIKE                ≠ DEMAND
BUY PRESSURE                ≠ FUTURE PRICE INCREASE
LIQUIDITY EXISTS            ≠ LIQUIDITY IS ACCESSIBLE
LIQUIDITY EXISTS            ≠ LIQUIDITY IS STABLE
LIQUIDITY EXISTS            ≠ LIQUIDITY IS EXITABLE
HIGH VOLUME                 ≠ HEALTHY MARKET
WHALE ACTIVITY              ≠ BULLISHNESS
MOMENTUM OBSERVED           ≠ MOMENTUM EXPLANATION
MOMENTUM OBSERVED           ≠ MOMENTUM PREDICTION
CORRELATION                 ≠ CAUSATION
MARKET SIGNAL               ≠ EVIDENCE
MARKET INTELLIGENCE         ≠ TRUTH
MODEL OUTPUT                ≠ MARKET FACT
STRONG SIGNAL               ≠ LOW RISK
SIGNAL                      ≠ DECISION
BACKTEST RESULT             ≠ LIVE MARKET TRUTH
ANOMALY DETECTED            ≠ MANIPULATION PROVEN
ATTENTION                   ≠ DEMAND
SENTIMENT                   ≠ BUYING
SOCIAL VOLUME               ≠ FUNDAMENTAL VALUE
NARRATIVE                   ≠ TRUTH
MULTIPLE VENUES             ≠ AUTOMATIC INDEPENDENT CONFIRMATION
CURRENT_TIMESTAMP           ≠ EVENT_TIMESTAMP
RECENT                      ≠ LIVE
```

---

## 1. Executive Summary

`[VERIFIED]` The AHOS Agent Organization contains **no implemented Crypto Market Intelligence layer** in code. There are no market-specific datatypes, signal engines, regime classifiers, liquidity assessors, or provider integrations in `ahos_org/`, `agent_org/`, or `research_worker/`. Market intelligence today exists only as a **planned specialist role** (`agent.org.08-crypto-market-intelligence`, `[PLANNED]`) in `PLANNED_19_AGENT_MAP.md`.

`[VERIFIED]` Foundational **upstream dependencies are partially documented** by peer architecture missions: Agent-07 (data quality, provenance, provider independence), Agent-05 (epistemic ladder), Agent-06 (research methodology), Agent-03 (security), Agent-04 (governance). Slice 2B (`agent_org/epistemic.py`, `[IMPLEMENTED]` `[TESTED]`) provides generic `Observation`, `Evidence`, `Hypothesis`, `Prediction`, and `ContradictionCase` types — not market-domain semantics.

`[VERIFIED]` Slice 1 (`ahos_org/registry.py`) contains **thematically overlapping logical roles** — `agent.paper-trading`, `agent.scoring-science`, `agent.provider-data` — but none implement market interpretation. All canonical agents are at `MaturityLevel.REGISTERED` (below execution allow threshold). `provider.connect` and `trading.live` are globally denied (`[IMPLEMENTED]` `ahos_org/policy.py`).

**Central architectural question:** What does the market appear to be doing? What do we actually observe? What market phenomena can legitimately be inferred from those observations? What should remain UNKNOWN? How should market observations become intelligence without silently becoming Evidence, Truth, Decision, or Execution authority?

**Primary market-intelligence objective:** prevent **market authority collapse** — where price moves, volume spikes, momentum labels, regime tags, opportunity scores, or model outputs silently become truth, evidence, buy signals, or execution triggers.

**Current market-intelligence posture:** `[DOCUMENTED]` blueprint only; `[PROPOSED]` peer boundaries; `[IMPLEMENTED]` generic epistemic and deny-policy substrate. **No market intelligence runtime.**

**Dual-19 status:** `[VERIFIED]` `[CONFLICT / UNRESOLVED]` — Plane A (`agent.paper-trading`, `agent.scoring-science`, `agent.provider-data`) and Plane D (`agent.org.08-crypto-market-intelligence`) remain separate taxonomies. This document analyzes compatibility only; it does not merge them.

**Agent One:** `NOT_IMPLEMENTED / FUTURE_NON_AUTHORITY_ROOT` — must never become market truth root or execution authority.

**AHOS:** `[VERIFIED]` Separate product repository with market-related pipelines (read-only boundary citation). This mission performs no AHOS modification. `AHOS_IMPACT = NONE`.

---

## 2. Mission Scope

### 2.1 In scope (this mission)

- Repository forensics and architecture design for Crypto Market Intelligence
- Taxonomies for observations, signals, regimes, liquidity, anomalies, threats
- Boundary definitions with Agents 03–07 and future 09–13, 16, 19
- Object model proposals (conceptual only)
- Contradiction analysis across existing docs and code
- Required matrices, human decisions, implementation gaps

### 2.2 Out of scope (explicit prohibitions)

- AHOS modification; Lane A/B modification; live trading; provider connections
- Runtime service implementation; trading algorithms; autonomous execution
- Agent activation or creation; governance adoption; commits or pushes
- Resolving Dual-19; granting Agent 08 decision authority
- Claiming any market intelligence capability is implemented or verified

---

## 3. Identity and Lifecycle

### 3.1 Agent-08 identity

| Field | Value |
| --- | --- |
| `AGENT_ID` (mission) | `AGENT-08` |
| Blueprint ID | `agent.org.08-crypto-market-intelligence` |
| Provisional name | Crypto Market Intelligence Architect |
| Role | Design market intelligence architecture: observation taxonomy, signal discipline, regime/liquidity/anomaly models, cross-venue reasoning |
| Authority class | `NONE` (design mission only) |
| Capabilities exercised | READ, ANALYZE, PROPOSE (documentation) |
| Forbidden | VERIFY (own conclusions), PROMOTE, EXECUTE, MODIFY runtime, CONNECT providers/exchanges, ACTIVATE other agents, emit buy/sell decisions |
| Supervisor | MASTER ORCHESTRATOR → human operator (MEHRDAD) |
| Source of truth | **Not** AGENT-08. Repository L0/L1 + governance L2/L3 only. |

AGENT-08 is **not** Agent One, **not** the Master Orchestrator, **not** a quant trader, **not** a data engineer, **not** an epistemic authority, **not** a risk approver, and **not** authorized to convert market signals into decisions or execution.

### 3.2 Command chain

```text
MEHRDAD
  → MASTER ORCHESTRATOR
    → AGENT-08 (this mission)
```

- Direct commander: **MASTER ORCHESTRATOR**
- No subordinate agents created or activated
- Peer specialists (03–07, future 09–19) are not commanders

### 3.3 Lifecycle

```text
ACTIVATION_REQUESTED → AUTHORIZED → ACTIVE
  (TASK-20260914-008)
  → COMPLETED (this deliverable)
  → IDLE / DORMANT / WAITING_FOR_NEW_COMMAND
```

Recommendations in this document are **not** commands. AGENT-08 does not auto-continue to Agent-09 or any future mission.

---

## 4. Existing Repository State

### 4.1 Implementation inventory

| Component | Path | Market relevance | Status |
| --- | --- | --- | --- |
| Slice 1 registry | `ahos_org/registry.py` | `agent.paper-trading`, `agent.scoring-science`, `agent.provider-data` | `[IMPLEMENTED]` logical roles only |
| Global deny policy | `ahos_org/policy.py` | `provider.connect`, `trading.live` denied | `[IMPLEMENTED]` `[TESTED]` |
| Epistemic core | `agent_org/epistemic.py` | Generic Observation/Evidence/Hypothesis | `[IMPLEMENTED]` no market domain |
| Research analyst | `research_worker/analyst.py` | Label discipline; no market analytics | `[IMPLEMENTED]` Class A only |
| Planned Agent 08 | `PLANNED_19_AGENT_MAP.md` | Blueprint row | `[PLANNED]` |
| Agent 07 architecture | `AGENT_07_DATA_INTELLIGENCE_ARCHITECTURE.md` | Upstream data boundary | `[DOCUMENTED]` |
| Agent 05/06 architecture | respective docs | Epistemic/methodology boundaries | `[DOCUMENTED]` |
| Market signal engine | — | — | `[PROPOSED]` none |
| Regime classifier | — | — | `[PROPOSED]` none |
| Liquidity assessor | — | — | `[PROPOSED]` none |
| DEX/CEX adapters | — | — | `[PROPOSED]` none |
| Market feature registry | — | — | `[PROPOSED]` none |
| Cross-venue reconciler | — | — | `[PROPOSED]` none |

### 4.2 Honesty classification

```text
DOCUMENTED ≠ IMPLEMENTED
IMPLEMENTED ≠ VERIFIED (for market intelligence — nothing to verify)
VERIFIED ≠ PRODUCTION_READY
```

### 4.3 Dual-19 compatibility (not resolution)

| Plane A (Slice 1) | Plane D (Blueprint) | Overlap theme | Resolution |
| --- | --- | --- | --- |
| `agent.paper-trading` | `agent.org.08-crypto-market-intelligence` | Market analysis | `UNRESOLVED` |
| `agent.scoring-science` | `agent.org.08` + `agent.org.12-quant-backtesting` | Scoring/signals | `UNRESOLVED` |
| `agent.provider-data` | `agent.org.07-data-intelligence` | Data supply | `UNRESOLVED` (Agent 07 domain) |
| `agent.reality-forensics` | `agent.org.08` / `agent.org.09` | Reconstructing claims | `UNRESOLVED` |

`[PROPOSED]` compatibility rule: Agent 08 owns **market meaning derivation**; Plane A roles remain logical policy placeholders until human L2 mapping.

---

## 5. Definition of Crypto Market Intelligence

### 5.1 Architectural definition

**Crypto Market Intelligence (CMI)** is the bounded architectural domain responsible for transforming **data-quality-qualified market observations** into **explicitly labeled market interpretations, signals, hypotheses, and assessments** — while preserving uncertainty, provenance, temporal semantics, and epistemic separation from evidence, truth, risk approval, and execution.

CMI answers: **"What market meaning can legitimately be derived from suitable data?"**

CMI does **not** answer: **"Should we trade?"** or **"Is this true?"**

### 5.2 Purpose

- Structure market observations across CEX, DEX, and cross-venue contexts
- Derive metrics and signals with documented formulas and failure modes
- Classify regimes, momentum, liquidity, and anomalies as **assessments**, not facts
- Surface opportunity **and** danger hypotheses without decision authority
- Propagate data-quality and provider limitations from Agent 07
- Produce intelligence artifacts eligible for epistemic packaging (Agent 05), not automatic evidence

### 5.3 Scope

**In scope:** spot/perp prices, volume, order flow (where available), liquidity, funding/OI (derivatives), cross-venue divergence, temporal alignment, manipulation **hypotheses**, narrative boundary interfaces.

**Out of scope:** on-chain wallet semantics (Agent 09), token contract security (Agent 10), portfolio risk limits (Agent 11), backtest execution (Agent 12), model training (Agent 13), order placement, wallet operations, live provider connections (denied globally).

### 5.4 Inputs

| Input | Source owner | Required metadata |
| --- | --- | --- |
| Raw/normalized market records | Agent 07 data layer (future) | Provider, venue, symbol, event_time, ingestion_time |
| DataQualityAssessment | Agent 07 | Quality vector, gaps, conflicts, readiness |
| Provider independence summary | Agent 07 | Correlation clusters |
| Security flags (market-relevant) | Agent 03 / 10 | Quarantine, tampering suspicion |
| Research question context | Agent 06 | Purpose binding, falsification criteria |
| On-chain intelligence (future) | Agent 09 | Separate domain; fusion boundary only |

### 5.5 Transformations (permitted)

```text
Raw Observation → Normalized Observation → Derived Metric
  → Market Signal → Market Interpretation → Market Hypothesis
  → Market Intelligence Assessment
```

Each step requires: transform identity, version, input refs, timestamp semantics, uncertainty propagation.

### 5.6 Outputs

| Output | Epistemic class | Decision authority |
| --- | --- | --- |
| MarketObservation | Observation-tier | None |
| MarketMetric / MarketSignal | Derived interpretation | None |
| MarketRegimeAssessment | Labeled assessment + confidence | None |
| MarketAnomaly | Detected deviation | None |
| MarketHypothesis | Testable proposition | None |
| MarketIntelligenceAssessment | Synthesis artifact | None |
| MarketConflict | Explicit disagreement record | None |
| Evidence Candidate pointer | Handoff to Agent 05 | None (Agent 05 owns Evidence) |

### 5.7 Uncertainty and limitations

- All outputs carry explicit uncertainty dimensions (see §27)
- UNKNOWN is a first-class state (see §41)
- Staleness, missingness, and provider disagreement propagate downstream
- Regime and momentum labels are **model outputs**, not ground truth

### 5.8 Consumers (future, non-authoritative)

| Consumer | May use CMI for | Must not assume |
| --- | --- | --- |
| Agent 05 | Evidence packaging eligibility | Signal = verified claim |
| Agent 06 | Hypothesis test design | Pattern = causal proof |
| Agent 11 | Risk context | Strong signal = low risk |
| Agent 12 | Feature/signal definitions | Backtest parity = live truth |
| Agent 13 | Labeled features + uncertainty | Clean features = truth |
| Agent 16 | Verification targets | Metric correctness without tests |
| Agent 19 | Adversarial probes | Architecture = enforcement |
| Human operator | Situational awareness | Intelligence = trade command |

### 5.9 Prohibited interpretations

CMI must never silently imply:

- Buy/sell/hold decisions
- Guaranteed profit opportunity
- Manipulation proof from anomaly alone
- Regime certainty from single model
- Cross-venue agreement as independent confirmation without cluster evidence
- Social sentiment as organic demand
- Price increase as fundamental value confirmation

### 5.10 Governance boundary

CMI operates under `[PROPOSED]` design authority only. Production use requires: Agent 07 data readiness, Agent 04 governance admission, Agent 16 verification, explicit human L2 adoption. CMI has **zero** direct path to execution.

### 5.11 Distinctions from adjacent domains

| Domain | Question | CMI boundary |
| --- | --- | --- |
| Market data | What bytes/records exist? | Agent 07 upstream |
| Market analytics | What numbers were computed? | CMI owns formulas + semantics |
| Technical analysis | Pattern labels from charts | CMI treats as **interpretation**, not evidence |
| Quant signals | Statistical model outputs | Agent 12 owns model lifecycle; CMI supplies features |
| Trading strategy | When/how to act | Forbidden for Agent 08 |
| Risk intelligence | What can go wrong financially? | Agent 11 owns risk framing |
| On-chain intelligence | What happened on ledger? | Agent 09; fusion requires explicit boundary |
| Token security | Is token contract safe? | Agent 10; market activity ≠ security clearance |
| Prediction | Future outcome claim | CMI may propose Prediction candidates; Agent 05 owns lifecycle |
| Decision | Authorized action choice | Canonical decision authority (future); not Agent 08 |
| Execution | Order/wallet operations | Globally denied |

---

## 6. Architectural Principles

### 6.1 Non-collapse principles

```text
OBSERVATION       ≠ INTERPRETATION
INTERPRETATION    ≠ HYPOTHESIS
HYPOTHESIS        ≠ PREDICTION
PREDICTION        ≠ EVIDENCE
EVIDENCE          ≠ KNOWLEDGE
KNOWLEDGE         ≠ DECISION
DECISION          ≠ EXECUTION
```

### 6.2 Layer separation

```text
DATA LAYER (Agent 07)           → suitability, provenance, quality
MARKET INTELLIGENCE (Agent 08)  → market meaning, signals, assessments
EPISTEMIC LAYER (Agent 05)      → evidence, claims, promotion gates
METHODOLOGY (Agent 06)          → study validity
RISK (Agent 11)                 → loss/exposure framing
SECURITY (Agent 03/10)            → integrity, scam/manipulation analysis
DECISION (future canonical)     → authorized action
EXECUTION (future, governed)    → orders, wallets — separately governed
```

### 6.3 Fail-closed rules

- If Agent 07 marks data NOT_FIT or STALE for purpose → CMI must not emit live-grade signals without explicit degraded-mode labeling
- If provider conflict UNRESOLVED → cross-venue intelligence defaults to UNKNOWN or CONFLICT, not average
- If security quarantine active → market intelligence on affected instruments blocked or flagged
- Missing event_time → no momentum/regime claims on affected window

### 6.4 No silent feature engineering

Prohibited without documented transform record:

- Silent imputation, hidden normalization, undocumented smoothing
- Look-ahead bias, future-data contamination, survivorship bias
- Hidden provider substitution, unit changes without version bump

Aligns with Agent 06 leakage controls and Agent 07 lineage requirements.

---

## 7. Market Observation Model

### 7.1 Three-tier observation classification

| Tier | Definition | Examples |
| --- | --- | --- |
| **OBSERVABLE** | Directly recorded from provider/venue with documented semantics | Last trade price, bid, ask, pool reserves, funding rate |
| **INFERRED** | Computed from observables with explicit formula | Returns, volume imbalance, effective spread, price impact estimate |
| **UNKNOWN** | Not available, ambiguous, or data-quality blocked | True aggressive buy volume when only aggregate tape exists |

Every metric must declare its tier. INFERRED metrics must cite input observables and transform version.

### 7.2 Observation binding requirements

Each market observation record `[PROPOSED]`:

```text
observation_id
instrument_ref          # chain_id, venue, pair/pool, quote/base
event_timestamp         # when market event occurred
observation_timestamp   # when captured (Slice 2B dual-time pattern)
ingestion_timestamp
provider_id
venue_type              # CEX | DEX | AGGREGATOR | ORACLE
raw_value + units
normalization_version
data_quality_ref        # Agent 07 assessment id
tier                    # OBSERVABLE | INFERRED | UNKNOWN
limitations[]
provenance
```

---

## 8. Market Data Boundary

### 8.1 Agent 07 vs Agent 08 split

| Question | Owner |
| --- | --- |
| Is the data suitable and trustworthy enough for this use? | **Agent 07** |
| What market meaning can legitimately be derived from that data? | **Agent 08** |

Agent 08 **must not override** Agent 07 findings. If data is stale, incomplete, contradictory, corrupted, or semantically ambiguous, CMI propagates that limitation on every downstream artifact.

### 8.2 Minimum data gate for CMI processing `[PROPOSED]`

| CMI operation | Minimum Agent 07 readiness |
| --- | --- |
| Exploratory metric computation | STRUCTURED + quality vector |
| Published MarketSignal | VALIDATED for declared purpose |
| Cross-venue intelligence | RECONCILED or explicit UNRESOLVED conflict |
| Regime assessment (live context) | FIT or FIT_WITH_LIMITATIONS + freshness pass |
| Decision-adjacent intelligence handoff | RESEARCH_READY minimum; DECISION_READY for operational consumers |

### 8.3 Forbidden chain

```text
FORBIDDEN:
  schema_valid AND freshness=FRESH
    → MarketSignal=BUY
    → Evidence
    → Decision
    → Execution
```

---

## 9. Price Intelligence

### 9.1 Price observation taxonomy

| Concept | Tier | Notes |
| --- | --- | --- |
| Spot last price | OBSERVABLE | Venue-specific; not universal "the price" |
| Mark/index price (perps) | OBSERVABLE | Provider-defined methodology |
| OHLC (open/high/low/close) | INFERRED/OBSERVABLE | Depends on bar construction rules |
| Price change / return | INFERRED | Requires window and compounding convention |
| Log return | INFERRED | Formula version required |
| Percentage movement | INFERRED | Base price and window explicit |
| Relative movement (vs BTC/ETH/index) | INFERRED | Benchmark instrument ref required |
| Realized volatility | INFERRED | Window, annualization factor documented |
| Implied volatility | INFERRED/UNKNOWN | Requires options surface; often unavailable in crypto |
| Drawdown / recovery | INFERRED | Path-dependent; peak definition matters |
| Price gap | INFERRED | Requires continuous series assumption |

### 9.2 Price failure modes

| Failure | Detection | CMI response |
| --- | --- | --- |
| Stale quote displayed as live | Freshness vs event_time delta | STALE label; block momentum |
| Wrong decimal normalization | Semantic validator (Agent 07) | QUARANTINE upstream; no signals |
| Index vs last divergence | Cross-field check | Emit MarketConflict |
| Flash wick vs sustained move | Time persistence rules | Separate spike vs trend signals |
| Oracle vs DEX divergence | Cross-venue compare | UNKNOWN or manipulation hypothesis tier |

---

## 10. Volume Intelligence

### 10.1 Volume taxonomy

| Concept | Tier | Notes |
| --- | --- | --- |
| Traded volume (base/quote) | OBSERVABLE | Venue reporting semantics vary |
| Buy/sell volume | INFERRED/OBSERVABLE | Often unavailable; tier must be honest |
| Volume imbalance | INFERRED | Definition: (buy-sell)/(buy+sell) or proxy |
| Volume acceleration | INFERRED | Second derivative; noise-sensitive |
| Abnormal volume | INFERRED | Requires baseline model + false-positive rate |
| Volume concentration | INFERRED | Top-N trades/wallets share when data exists |
| Volume/price divergence | INFERRED | Joint signal; not automatic reversal proof |

### 10.2 Volume prohibitions

```text
VOLUME SPIKE ≠ DEMAND
HIGH VOLUME ≠ HEALTHY MARKET
VOLUME ↑ + PRICE ↑ ≠ ORGANIC ACCUMULATION (without independent checks)
```

Wash trading and fake volume require manipulation hypothesis pathway (§20), not volume praise.

---

## 11. Liquidity Intelligence

### 11.1 Liquidity distinction model

```text
LIQUIDITY EXISTS        = reserves/depth observable at snapshot
LIQUIDITY ACCESSIBLE    = achievable fill at stated size/slippage for actor class
LIQUIDITY STABLE        = persistence over time window
LIQUIDITY EXITABLE      = ability to exit position without catastrophic impact
```

Each layer is a separate assessment with separate confidence.

### 11.2 Liquidity taxonomy

| Concept | Tier | CEX | DEX |
| --- | --- | --- | --- |
| Displayed depth | OBSERVABLE | Order book levels | Pool reserves / CL ranges |
| Effective liquidity | INFERRED | Impact simulation | AMM curve simulation |
| Bid/ask spread | OBSERVABLE/INFERRED | Top of book | Effective spread via small trade |
| Slippage estimate | INFERRED | Book walk / historical | x*y=k or CL math |
| Market impact | INFERRED | Size-dependent | Route-dependent |
| Liquidity concentration | INFERRED | Top levels % | Pool share / LP concentration |
| Liquidity fragmentation | INFERRED | Cross-venue | Multi-pool routing |
| Liquidity withdrawal | INFERRED | Depth delta events | LP remove events |
| Liquidity spoofing | INFERRED/HYPOTHESIS | Fleeting large orders | Less common; MEV-adjacent |

### 11.3 Exit liquidity assessment `[PROPOSED]`

```text
LiquidityAssessment
  instrument_ref
  assessed_at
  snapshot_refs[]
  size_bands[]              # e.g., 1k, 10k, 100k USD notional
  estimated_slippage_by_band
  exitability_verdict       # EXITABLE | CONSTRAINED | THIN | UNKNOWN
  stability_window
  concentration_flags[]
  limitations               # e.g., single pool, bridge risk not included
  confidence_vector
```

---

## 12. Order Flow Intelligence

Available primarily on CEX and some aggregated feeds; often **UNKNOWN** on DEX without specialized reconstruction.

| Concept | Tier | Availability |
| --- | --- | --- |
| Order imbalance | INFERRED | CEX L2 history |
| Trade imbalance | INFERRED | Aggressor side when tagged |
| Aggressive buy/sell | INFERRED/OBSERVABLE | Requires trade flags |
| Maker/taker behavior | INFERRED | Fee tier + order type |
| Spread dynamics | INFERRED | Time series |
| Depth imbalance | INFERRED | Bid vs ask depth |
| Trade intensity | INFERRED | Trades per second |
| Cancellation behavior | INFERRED | CEX only; manipulation signal input |
| Execution pressure | INFERRED | Composite; document formula |

When order flow is UNKNOWN, CMI must not infer demand from price alone without labeled proxy limitations.

---

## 13. Market Regimes

### 13.1 Regime framework `[PROPOSED]`

Possible regime labels (non-exhaustive): `TRENDING`, `RANGING`, `BREAKOUT`, `BREAKDOWN`, `HIGH_VOLATILITY`, `LOW_VOLATILITY`, `LIQUIDITY_EXPANSION`, `LIQUIDITY_CONTRACTION`, `PANIC`, `EUPHORIA`, `ACCUMULATION_HYPOTHESIS`, `DISTRIBUTION_HYPOTHESIS`, `FRAGMENTED`, `STRESSED`, `ILLIQUID`, `ANOMALOUS`, `UNKNOWN`, `STALE`.

**Rule:** Regime label ≠ fact. It is a **model assignment** with evidence bundle.

### 13.2 Regime assessment structure

```text
MarketRegimeAssessment
  regime_label
  model_id + version
  evidence_bundle[]         # metrics supporting label
  confidence                # structured, not single hidden scalar
  uncertainty
  conflicting_indicators[]  # e.g., trend metric vs range metric
  transition_detected       # bool + from/to if true
  valid_from / valid_until
  freshness
  epistemic_status          # INTERPRETATION | HYPOTHESIS — never FACT
```

### 13.3 Regime states of knowledge

| State | Meaning |
| --- | --- |
| **Regime evidence** | Observable metrics fed to classifier |
| **Regime confidence** | Model posterior or heuristic score with calibration disclaimer |
| **Regime uncertainty** | Ambiguity, conflicting indicators, low sample |
| **Unknown regime** | Insufficient data or model abstention |
| **Stale regime** | Assessment older than validity window |
| **Conflicting regimes** | Multiple models disagree — preserve all (§29) |

---

## 14. Momentum

### 14.1 Momentum taxonomy

| Horizon | Examples | Tier |
| --- | --- | --- |
| Short-term | 1m–1h ROC, microstructure impulse | INFERRED |
| Medium-term | 4h–1d trend slope | INFERRED |
| Long-term | 7d–30d trend | INFERRED |
| Acceleration | Δ(momentum) | INFERRED |
| Deceleration | Momentum peak detection | INFERRED |
| Trend persistence | Hurst proxy, ADX-like | INFERRED |
| Reversal pattern | Divergence flags | INFERRED/HYPOTHESIS |
| Mean reversion signal | Z-score vs window | INFERRED |
| Breakout / false breakout | Level breach + failure | INFERRED/HYPOTHESIS |
| Momentum exhaustion | Volume divergence + deceleration | HYPOTHESIS |

### 14.2 Momentum separation

```text
MOMENTUM OBSERVED     = metric values over window W
MOMENTUM EXPLANATION  = narrative or causal story (hypothesis tier)
MOMENTUM PREDICTION   = forward expectation (Prediction object, Agent 05 path)
```

---

## 15. Volatility

| Metric | Definition notes | Failure modes |
| --- | --- | --- |
| Realized vol | Window, annualization, sampling freq | Gap-filled series bias |
| Parkinson/Garman-Klass | OHLC estimators | Bad ticks distort |
| Implied vol | Options-derived | Often N/A in crypto spot |
| Vol compression/expansion | Regime input | Lagging after shock |
| Vol-of-vol | Second-order | High variance estimator |

Volatility expansion is **not** automatically opportunity; may indicate stress (§23).

---

## 16. DEX Intelligence

### 16.1 AMM observation model

| Event | Observable | Inferred |
| --- | --- | --- |
| Pool creation | Factory event | New market hypothesis |
| Liquidity add/remove | Mint/burn amounts | LP behavior trend |
| Swap | Amounts in/out | Price impact, route |
| Pool migration | Contract events | Liquidity fragmentation |
| Concentrated liquidity (CL) | Tick ranges | Effective depth varies by price |

### 16.2 DEX-specific semantics

- **Price** on DEX is path-dependent (trade size, route, fees)
- **Liquidity** is curve-state, not order book
- **Volume** may include wash routing across pools
- **Aggregator behavior** introduces synthetic prices not tied to single pool

### 16.3 DEX vs CEX semantic differences

| Dimension | CEX | DEX |
| --- | --- | --- |
| Price discovery | Central limit order book | AMM curve + external arb |
| Depth | Visible orders (spoofable) | Reserves (ruggable) |
| Finality | Exchange internal | Chain confirmation + reorg |
| Identity | Account-based | Pool/tx hash |
| Funding/OI | Perps native | Often off-chain perp venues |

Cross-venue comparison requires **semantic normalization contract** (Agent 07 DataContract + CMI feature governance §31).

---

## 17. CEX Intelligence

| Data class | Typical source | Provider-specific? |
| --- | --- | --- |
| Order book L2 | Exchange API | Yes |
| Trades tape | Exchange API | Yes |
| Funding rate | Perp exchange | Yes |
| Open interest | Exchange | Yes |
| Liquidations | Exchange / aggregator | Often partial |
| Mark/index | Exchange | Yes — methodology varies |
| Futures basis | Derived from spot+perp | Requires aligned timestamps |
| Spot/futures divergence | Cross-instrument | INFERRED |

CMI must document provider-specific fields in Provider Dependency Matrix (Matrix C).

---

## 18. Cross-Venue Intelligence

### 18.1 Cross-venue phenomena

| Phenomenon | Meaning | Risk |
| --- | --- | --- |
| Price divergence | Same asset, different venues | Stale quote fake arb |
| Liquidity fragmentation | Depth split | Exit path unclear |
| Cross-venue spread | Arbitrage band | Latency-sensitive |
| Synchronized moves | Correlated updates | Shared upstream, not independence |
| Provider disagreement | Numeric conflict | No silent averaging |

### 18.2 Critical rule

```text
MULTIPLE VENUES ≠ AUTOMATIC INDEPENDENT CONFIRMATION
```

Coordinate with Agent 07 §23 Provider Independence. Confirmation requires distinct `correlation_cluster_id` evidence.

### 18.3 Cross-venue assessment `[PROPOSED]`

```text
CrossVenueAssessment
  instrument_cluster_ref
  venue_observations[]
  divergence_metrics
  independence_summary_ref
  arbitrage_feasibility    # HYPOTHESIS tier — fees, latency, capital not ignored
  conflict_state           # RESOLVED | UNRESOLVED | UNKNOWN
```

---

## 19. Market Anomalies

### 19.1 Anomaly classes

| Class | Detection basis | Default tier |
| --- | --- | --- |
| Abnormal volume | Baseline z-score / robust median | INFERRED |
| Abnormal volatility | Vol spike vs regime | INFERRED |
| Abnormal spread | Spread vs historical | INFERRED |
| Liquidity withdrawal | Depth drop rate | INFERRED |
| Abnormal trade size | Tail trade cluster | INFERRED |
| Unusual price movement | Jump detection | INFERRED |
| Order-book imbalance spike | Depth ratio | INFERRED |
| Provider disagreement | Reconciliation delta | OBSERVABLE/INFERRED |
| Timestamp anomaly | event_time > ingestion_time violations | OBSERVABLE |
| Market-data discontinuity | Gap / duplicate bar | OBSERVABLE |
| Manipulation hypothesis | Pattern suite | HYPOTHESIS |

### 19.2 Anomaly rule

```text
ANOMALY DETECTED ≠ MANIPULATION PROVEN
```

Anomalies trigger investigation pathways, not automatic security verdicts.

---

## 20. Manipulation Intelligence

### 20.1 Hypothesis classes (non-exhaustive)

Pump, dump, wash trading, spoofing, layering, liquidity bait, coordinated trading, fake volume, price manipulation, oracle manipulation, cross-venue manipulation.

### 20.2 Observation → hypothesis pipeline

```text
OBSERVATION → ANOMALY → HYPOTHESIS → TEST → POSSIBLE CONFIRMATION / REFUTATION
```

| Stage | Owner emphasis |
| --- | --- |
| Observation/Anomaly | Agent 08 + Agent 07 data |
| Hypothesis formulation | Agent 08 proposes; Agent 06 designs test |
| Security substantiation | Agent 10 / 03 where contract/integrity involved |
| Epistemic promotion | Agent 05 only |

### 20.3 Manipulation detection architecture `[PROPOSED]`

- Pattern library with known false-positive rates
- Multi-signal fusion requires explicit conflict handling
- Never auto-block trading from manipulation hypothesis alone (decision layer)

---

## 21. Narrative/Sentiment Boundary

### 21.1 Permitted interaction

CMI may **reference** off-chain narrative/sentiment as **context** with separate provenance:

- News headlines, social volume, community activity, attention metrics

### 21.2 Forbidden equalities

```text
ATTENTION ≠ DEMAND
SENTIMENT ≠ BUYING
SOCIAL VOLUME ≠ FUNDAMENTAL VALUE
NARRATIVE ≠ TRUTH
```

### 21.3 Interface model `[PROPOSED]`

```text
NarrativeContextAttachment
  market_intelligence_id
  narrative_source_refs[]     # Agent 07 off-chain data classes
  attachment_type             # CONTEXT_ONLY — never merged into price signal score silently
  temporal_alignment          # narrative lead/lag vs price move
  limitations
```

Future dedicated narrative intelligence layer must not collapse into CMI price/volume signals without explicit fusion contract and human L2 approval.

---

## 22. Market Opportunity Signals

### 22.1 Opportunity indicators (hypothesis-tier, not decisions)

| Indicator | Meaning | Not equivalent to |
| --- | --- | --- |
| Unusual momentum | ROC vs baseline | BUY |
| Liquidity improvement | Depth/slippage better | Safe to size up |
| Volume expansion | Activity surge | Organic demand |
| Price/volume divergence | Joint pattern | Reversal certainty |
| Cross-venue inefficiency | Divergence band | Executable arb profit |
| Volatility compression | Squeeze setup | Directional certainty |
| Breakout structure | Level breach | Successful breakout |
| Emerging demand hypothesis | Composite story | Verified accumulation |

### 22.2 Two-sided model

Architecture must emit **POTENTIAL_OPPORTUNITY** and **POTENTIAL_DANGER** with equal structural weight. No forced positive-only scoring.

```text
SIGNAL ≠ DECISION
```

---

## 23. Market Threat Intelligence

### 23.1 Threat taxonomy

| Threat | Signal inputs | Default severity framing |
| --- | --- | --- |
| Thin liquidity | LiquidityAssessment | Exit risk |
| Sudden liquidity withdrawal | Depth delta | Rug/adverse selection hypothesis |
| Fake volume | Volume anomaly + uniqueness | Signal corruption |
| Wash trading | Trade pattern hypothesis | Metric untrustworthiness |
| Spoofing | Fleeting depth | False liquidity |
| Extreme volatility | Vol regime | Slippage/gap risk |
| Price gaps | Discontinuous series | Stop/run risk |
| Oracle divergence | Cross-source price | Liquidation/manipulation |
| Venue outage | Feed gap | Stale intelligence |
| Stale market data | Freshness fail | False signals |
| Market fragmentation | Cross-venue spread | Execution uncertainty |
| Manipulation (hypothesis) | Anomaly suite | Investigation required |
| Correlated collapse | Beta spike | Systemic stress |
| Liquidation cascade | OI + funding + vol | Perp-specific |

Threats feed **Agent 11 Risk** and security review; CMI does not authorize defensive actions.

---

## 24. Temporal Intelligence

### 24.1 Timestamp classes

| Timestamp | Meaning |
| --- | --- |
| **event_time** | When the market event occurred |
| **observation_time** | When provider/sensor recorded it |
| **ingestion_time** | When org pipeline received it |
| **processing_time** | When CMI computed derived metrics |
| **decision_time** | When downstream decision evaluated (future) |

### 24.2 Critical rules

```text
CURRENT_TIMESTAMP ≠ EVENT_TIMESTAMP
RECENT ≠ LIVE
```

### 24.3 Temporal failure modes

| Failure | Handling |
| --- | --- |
| Stale quotes | STALE flag; block live-grade signals |
| Delayed provider updates | Latency metric; widen uncertainty |
| Out-of-order events | Reorder buffer or invalidate window |
| Duplicate events | Dedup; volume double-count guard |
| Missing intervals | DataGap propagation from Agent 07 |
| Clock skew | Skew detector; quarantine if severe |

Coordinate with Agent 07 temporal integrity and Agent 06 leakage prevention.

---

## 25. Provenance and Lineage

### 25.1 Market intelligence lineage chain

```text
Provider
  ↓
Raw Observation
  ↓
Normalized Observation
  ↓
Derived Metric
  ↓
Market Signal
  ↓
Market Interpretation
  ↓
Market Intelligence Assessment
  ↓
Evidence Candidate (Agent 05 — not automatic)
```

### 25.2 Slice 2B alignment

`[IMPLEMENTED]` `Provenance` + `lineage` tuples on epistemic artifacts provide partial pattern. `[PROPOSED]` CMI artifacts should use compatible provenance fields and link to Agent 07 `DataArtifact` refs where applicable.

### 25.3 Lineage rules

1. Every transform is versioned and reproducible in specification
2. Supersession preferred over silent overwrite
3. Downstream inherits upstream uncertainty flags
4. Valid upstream does not auto-validate downstream interpretation

---

## 26. Market Intelligence Object Model

Conceptual objects only — **not implemented**.

### 26.1 Object catalog

| Object | Identity | Key fields | Forbidden transitions |
| --- | --- | --- | --- |
| **MarketObservation** | `observation_id` | instrument, event_time, value, tier, provider_ref | → Evidence without Agent 05 |
| **MarketMetric** | `metric_id` | formula_hash, inputs[], window, value | → Decision |
| **MarketSignal** | `signal_id` | signal_type, strength_vector, quality_ref | → Execution |
| **MarketRegimeAssessment** | `regime_id` | label, model, confidence, conflicts | → FACT status |
| **LiquidityAssessment** | `liq_id` | size_bands, exitability, stability | → "safe to trade" |
| **MarketAnomaly** | `anomaly_id` | class, detector, false_positive_prior | → Manipulation proven |
| **MarketHypothesis** | `mh_id` | statement, falsification, linked signals | → Knowledge |
| **MarketIntelligenceAssessment** | `mia_id` | synthesis, opportunity/danger flags | → Decision |
| **MarketConflict** | `conflict_id` | sides[], magnitude, unresolved | → Silent average |
| **MarketSnapshot** | `snapshot_id` | multi-metric point-in-time bundle | → Live without freshness |
| **MarketEvent** | `event_id` | typed market occurrence | → Causal claim without test |

### 26.2 Universal object requirements `[PROPOSED]`

Every object carries: `identity`, `created_at`, `source_refs`, `provenance`, `confidence`, `uncertainty`, `dependencies[]`, `validity_window`, `freshness`, `lifecycle_state`, `epistemic_status`, `intended_consumers[]`, `data_quality_ref`, `limitations[]`.

### 26.3 Epistemic status enum `[PROPOSED]`

`RAW`, `OBSERVED`, `NORMALIZED`, `DERIVED`, `INTERPRETED`, `HYPOTHESIZED`, `TESTED`, `SUPPORTED`, `CONTRADICTED`, `STALE`, `INVALID`, `RETIRED`.

**Mapping note:** Align with but do not merge silently into Slice 2B `HypothesisState`, `EvidenceState`, or Agent 07 readiness enums — explicit compatibility table in §43.

---

## 27. Signal Quality

### 27.1 Multidimensional quality model

Do **not** reduce to one number unless purpose-specific collapse is documented and reversible.

| Dimension | Question |
| --- | --- |
| Data quality | Agent 07 vector pass-through |
| Freshness | event_time vs now |
| Temporal alignment | Cross-series sync quality |
| Source reliability | Provider contextual profile |
| Provider independence | Cluster diversity |
| Calculation integrity | Transform verified? |
| Sample sufficiency | Enough bars/trades? |
| Regime stability | Label volatility |
| Uncertainty | Explicit bounds |
| Contradiction | Conflicting sub-signals |
| Reproducibility | Same inputs → same output |
| Sensitivity | Parameter stability |
| Robustness | Outlier resistance |

### 27.2 Signal quality artifact `[PROPOSED]`

```text
MarketSignalQuality
  signal_id
  dimension_scores{}        # structured, not hidden scalar
  blocking_failures[]
  degradations[]
  overall_actionability_hint  # MONITOR | RESEARCH_ONLY | NOT_ACTIONABLE — NOT buy/sell
```

---

## 28. Signal Lifecycle

### 28.1 Proposed lifecycle states

```text
RAW → OBSERVED → NORMALIZED → DERIVED → DETECTED → INTERPRETED
  → HYPOTHESIZED → TESTED → SUPPORTED | CONTRADICTED
  → STALE | INVALID | RETIRED
```

### 28.2 Compatibility with Slice 2B

| CMI lifecycle | Slice 2B analog | Compatible? |
| --- | --- | --- |
| OBSERVED | Observation.RECORDED | Partial — CMI adds market semantics |
| HYPOTHESIZED | Hypothesis.PROPOSED | Yes — handoff possible |
| TESTED | ExperimentRun | Via Agent 06 |
| SUPPORTED | Hypothesis.SUPPORTED | Agent 05 owns — not automatic |
| CONTRADICTED | ContradictionCase.OPEN | Separate objects; link required |
| STALE | EvidenceState.STALE | Analogous freshness concept |

Do not merge enums without human L2 decision (HD-04).

---

## 29. Conflict Intelligence

### 29.1 Multi-domain conflict example

| Domain | Says | CMI handling |
| --- | --- | --- |
| Price | Bullish breakout | Record signal |
| Volume | Weak participation | MarketConflict |
| Liquidity | Deteriorating | Threat flag |
| On-chain (Agent 09) | Accumulation | Cross-domain conflict object |
| Social | Euphoric | Narrative attachment only |
| Security (Agent 10) | Honeypot risk | Blocking context for consumers |

**Do not force consensus.** Emit `MarketConflict` with investigation requirements.

### 29.2 Conflict resolution states

`OPEN`, `UNDER_INVESTIGATION`, `PARTIALLY_RESOLVED`, `UNRESOLVED`, `RETAINED_UNCERTAIN`.

Link to Agent 05 `ContradictionCase` when propositional conflict exists; keep data-layer conflicts in CMI when no claim yet formed.

---

## 30. Provider Disagreement

Coordinate with Agent 07 §25 Reconciliation.

| Step | Action |
| --- | --- |
| Detection | Divergence metric vs tolerance |
| Magnitude | Absolute/relative; per field semantics |
| Semantic compatibility | Same instrument/units/window |
| Timestamp alignment | event_time sync quality |
| Independence check | Shared cluster → not vote tally |
| Reconciliation | Strategy per HD-06 (human decision) |
| Unresolved | Preserve all values; downstream UNKNOWN |
| Fallback | Never assume majority provider correct |

---

## 31. Feature Governance

Every market feature (returns, vol, momentum, spread, depth, imbalance, funding, OI, price impact) requires:

| Attribute | Required |
| --- | --- |
| definition | Plain language + formula |
| formula | Versioned, hashable |
| units | Explicit |
| source | Provider/venue classes |
| timestamp semantics | event vs bar close |
| missing-data behavior | FAIL | NULL | FORWARD_FILL (documented) |
| validity range | Sanity bounds |
| transformation history | Lineage |
| version | semver or content hash |
| known failure modes | Documented |

`[PROPOSED]` `MarketFeatureDefinition` registry coordinated with Agent 12 (quant) and Agent 13 (ML).

---

## 32. Prediction Boundary

| Stage | CMI role |
| --- | --- |
| Observation | Owns |
| Interpretation | Owns |
| Hypothesis | Proposes MarketHypothesis |
| Prediction | Proposes candidate with mandatory fields |

Prediction must include: `prediction_target`, `prediction_time`, `horizon`, `information_cutoff`, `expected_outcome`, `falsification_criterion`, `provenance`.

Agent 05 owns `Prediction` lifecycle. No retroactive rewrite of predictions.

---

## 33. Epistemic Boundary (Agent 05)

| Agent 08 may propose | Agent 08 must NOT |
| --- | --- |
| Observation-tier market records | Promote to Knowledge |
| Interpretation-tier signals | Register Evidence unilaterally |
| Hypothesis-tier manipulation stories | Mark VERIFIED |
| Prediction candidates | Override contradiction blocks |

```text
Agent 08: market interpretation
Agent 05: epistemic classification
```

Handoff: `MarketIntelligenceAssessment` → eligibility review → optional `Evidence` registration with `extraction_method` documenting market derivation path.

---

## 34. Risk Boundary (Agent 11)

```text
Market Signal ≠ Risk Signal
STRONG SIGNAL ≠ LOW RISK
```

CMI supplies context (liquidity, vol, threats). Agent 11 owns loss framing, exposure limits, and risk decisions. A bullish momentum signal with thin liquidity must surface as **conflict**, not net bullish score.

---

## 35. Security Boundary (Agent 03 / 10)

CMI is security-aware but not security-authoritative:

- Suspicious liquidity behavior → anomaly + referral
- Honeypot-related trading patterns → flag for Agent 10
- Transfer restriction symptoms in market data → do not interpret as normal vol

Agent 08 must not replace Token Security analysis. Security finding can **invalidate** market signal actionability without deleting observations.

---

## 36. On-Chain Boundary (Agent 09)

| Observation domain | Example | Relationship |
| --- | --- | --- |
| Market (Agent 08) | Price up on DEX | Observable |
| On-chain (Agent 09) | Whale wallet accumulation | Observable |
| Fusion | "Price up because accumulation" | **Hypothesis** — neither domain auto-explains the other |

`[PROPOSED]` `CrossDomainMarketFusion` artifact requires: both domain refs, temporal alignment, independence check, explicit fusion rule version, and UNKNOWN default when alignment insufficient.

---

## 37. Quant Boundary (Agent 12)

| Concern | Owner |
| --- | --- |
| Feature definitions for research | Joint — CMI semantics, Agent 12 statistical use |
| Backtest execution | Agent 12 |
| Live signal generation | Future runtime — not Agent 08 execution |
| Statistical model validity | Agent 12 + Agent 06 |

```text
BACKTEST RESULT ≠ LIVE MARKET TRUTH
```

CMI features fed to backtests must carry leakage annotations and cutoff times.

---

## 38. AI/ML Boundary (Agent 13)

CMI may expose to ML:

- Validated features with provenance
- Observations with uncertainty and missingness
- Regime context labels (as features, not labels of truth)
- Explicit bias/leakage warnings

Never provide silently cleaned or fabricated "ground truth" market labels.

---

## 39. QA Boundary (Agent 16)

Verification requirements for:

- Market metric formulas (golden tests)
- Timestamp semantics compliance
- Regime classifier reproducibility
- Liquidity simulation correctness
- Anomaly detector false-positive baselines
- Cross-provider reconciliation logic

Agent 16 verifies; Agent 08 designs verifiable specifications.

---

## 40. Red-Team Boundary (Agent 19)

Adversarial questions CMI architecture must survive:

1. Can fake volume create a false momentum signal?
2. Can stale prices create fake arbitrage signals?
3. Can one provider dominate regime classification undetected?
4. Can correlated providers appear independent in cross-venue confirmation?
5. Can liquidity metrics be gamed via spoofing or flash LP?
6. Can regime classification be manipulated by wash trading?
7. Can a missing event produce a false trend (gap fill imputation)?
8. Can an anomalous market be mistaken for opportunity?
9. Can a strong market signal survive a catastrophic security finding without conflict surfacing?
10. Can narrative context silently boost signal scores?

Agent 19 probes; architecture must fail closed or expose conflicts.

---

## 41. Unknown Handling

Explicit UNKNOWN states required for:

| Condition | UNKNOWN manifestation |
| --- | --- |
| Missing data | Metric = UNKNOWN; not zero |
| Insufficient history | Regime = UNKNOWN |
| Conflicting providers | CrossVenue = UNRESOLVED |
| Ambiguous semantics | QUARANTINE or UNKNOWN tier |
| Unreliable source | Propagate Agent 07 flag |
| Regime uncertainty | Multi-model disagree → preserve |
| Insufficient liquidity data | Exitability = UNKNOWN |
| Insufficient statistical power | Signal = NOT_DETECTED vs false negative documented |

**Never convert UNKNOWN into neutral-positive assumptions.**

---

## 42. Failure Taxonomy

| Failure class | Examples | Detection |
| --- | --- | --- |
| Data failure | Stale, gap, corrupt | Agent 07 gates |
| Semantic failure | Wrong pair, decimals | Semantic validator |
| Temporal failure | Look-ahead, misaligned bars | Timestamp audit |
| Provider failure | Outage, restatement | Health monitors |
| Calculation failure | Formula bug | Golden tests |
| Interpretation failure | Overclaim from metric | Epistemic review |
| Model failure | Regime misfire | Backtest + live monitor |
| Regime failure | Label churn | Stability metric |
| Manipulation failure | False manipulation flag | Human review |
| Reconciliation failure | Wrong merge | Conflict preserved |
| Provenance failure | Broken lineage | Lineage audit |
| Epistemic boundary failure | Signal → decision collapse | Red team / governance |

---

## 43. Readiness Model

### 43.1 CMI readiness levels `[PROPOSED]`

| Level | Meaning |
| --- | --- |
| CONCEPT | Idea only |
| DOCUMENTED | Architecture/spec exists |
| PROTOTYPE | Non-production code |
| TESTABLE | Golden tests defined |
| VERIFIED | Independent verification passed |
| RESEARCH_READY | Usable for bounded studies |
| PAPER_READY | Paper-trading context only |
| PRODUCTION_CANDIDATE | Ops prerequisites met — still ≠ truth |

### 43.2 Mapping to Agent 07 readiness

| Agent 07 | CMI dependency |
| --- | --- |
| RAW | No CMI outputs |
| STRUCTURED | Internal metrics only |
| VALIDATED | Signal emission allowed (degraded) |
| RECONCILED | Cross-venue intelligence |
| RESEARCH_READY | Hypothesis-grade assessments |
| DECISION_READY | Handoff to decision consumers (not execute) |
| PRODUCTION_READY | Operational monitoring required |

### 43.3 Mapping to Slice 1 maturity

| MaturityLevel | Slice 1 | CMI relevance |
| --- | --- | --- |
| REGISTERED (0) | All canonical agents today | No execution allow |
| IMPLEMENTED (2+) | Required for ALLOW | CMI runtime would need separate maturity tracking |

Current CMI posture: **CONCEPT → DOCUMENTED** (this document only).

---

## 44. Observability

Future observability requirements `[PROPOSED]`:

| Metric | Purpose |
| --- | --- |
| signal_latency | processing_time - event_time |
| provider_latency | ingestion - event_time |
| stale_rate | % signals past freshness |
| missing_rate | UNKNOWN frequency |
| disagreement_rate | cross-provider conflicts |
| anomaly_rate | detector throughput |
| false_positive_rate | calibrated on labeled samples |
| false_negative_rate | red-team scenarios |
| regime_instability | label flip frequency |
| signal_decay | predictive power over horizon |
| feature_drift | distribution shift |
| provider_drift | Schema/semantic changes |

---

## 45. Incident Management

### 45.1 Incident classes

| Class | Example |
| --- | --- |
| Stale market intelligence | Live dashboard using expired regime |
| False opportunity | Signal fired on wash volume |
| False danger | Liquidity scare from spoofing |
| Provider divergence | Unreconciled price conflict |
| Data poisoning | Bad tick propagated |
| Manipulation-induced signal | Pump pattern misfire |
| Calculation regression | Formula deploy bug |
| Timestamp corruption | Clock skew batch |
| Regime misclassification | Trend labeled range |
| Model drift | Feature distribution shift |

### 45.2 Quarantine / escalation principles

1. Contain: stop downstream propagation of affected artifacts
2. Preserve: retain inputs for forensics
3. Notify: Agent 04 governance path; human for high tier
4. Quarantine: mark signals INVALID; link incident id
5. Recover: replay from raw with fixed transform
6. Audit: post-incident review; update feature failure modes

---

## 46. Data → Intelligence → Evidence

### 46.1 Formal boundary model

```text
DATA
  ↓  [Agent 07: quality, provenance, fitness]
DATA QUALITY ASSESSMENT
  ↓  [Agent 08: only if fit for declared purpose]
MARKET OBSERVATION
  ↓  [Agent 08: metrics, alignment, transforms]
MARKET ANALYSIS
  ↓  [Agent 08: signals, regimes, assessments]
MARKET INTELLIGENCE
  ↓  [Agent 05: epistemic evaluation]
EPISTEMIC EVALUATION
  ↓  [Agent 05 + verification + governance]
EVIDENCE CANDIDATE
```

| Layer | Responsibility owner |
| --- | --- |
| DATA | Agent 07 (+ providers future) |
| DATA QUALITY ASSESSMENT | Agent 07 |
| MARKET OBSERVATION | Agent 08 |
| MARKET ANALYSIS | Agent 08 |
| MARKET INTELLIGENCE | Agent 08 |
| EPISTEMIC EVALUATION | Agent 05 |
| EVIDENCE CANDIDATE | Agent 05 (Evidence registration) |

---

## 47. Intelligence → Risk → Decision

### 47.1 Formal model

```text
MARKET INTELLIGENCE (Agent 08)
        +
ON-CHAIN INTELLIGENCE (Agent 09)
        +
SECURITY INTELLIGENCE (Agent 10)
        +
RISK INTELLIGENCE (Agent 11)
        +
EPISTEMIC EVALUATION (Agent 05)
        ↓
CANONICAL DECISION AUTHORITY (future — Slice 1 agent.canonical-decision-auditor is logical auditor only today)
        ↓
EXECUTION (separately governed — globally denied today)
```

```text
NO SINGLE SPECIALIST OWNS THE FINAL TRUTH.
NO SINGLE SPECIALIST OWNS THE FINAL DECISION.
```

Agent 08 has **ZERO** direct decision authority and **ZERO** execution path.

---

## 48. Contradictions

| CONTRADICTION_ID | LOCATION | SOURCE_A | SOURCE_B | CONFLICT | IMPACT | CURRENT_STATUS | RECOMMENDED_HUMAN_DECISION |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **CMI-C01** | Registry planes | Slice 1 `agent.paper-trading` | Plane D `agent.org.08-crypto-market-intelligence` | Both claim market analysis domain | Role duplication, unclear ownership | `UNRESOLVED` | Approve mapping table or split responsibilities (paper vs intelligence) |
| **CMI-C02** | Registry planes | Slice 1 `agent.scoring-science` | Plane D Agent 08 + Agent 12 | Scoring vs market signals vs quant | Signal ownership blur | `UNRESOLVED` | Define scoring input contract; assign model lifecycle to Agent 12 |
| **CMI-C03** | Registry model | `agent.provider-data` (Plane A) | `agent.org.07-data-intelligence` (Plane D) | Data supply ownership | Market intel depends on unresolved data plane | `UNRESOLVED` | Resolve Dual-19 data plane first (HD-01 Agent 07) |
| **CMI-C04** | Epistemic types | Slice 2B `Observation` (experiment-bound) | CMI `MarketObservation` (continuous feed) | Same word, different binding | Schema collision if merged naively | `UNRESOLVED` | Namespace separation or subtype enum |
| **CMI-C05** | Assurance scalar | `Evidence.assurance` 0–100 | Agent 07 quality vector + CMI signal quality | Scalar collapse risk | Market signal strength could mimic epistemic assurance | `UNRESOLVED` | Adopt vector-only handoff (HD-03/HD-04) |
| **CMI-C06** | Research worker | Deterministic analyst observations | CMI continuous market observations | Different observation pipelines | Inconsistent epistemic binding | `UNRESOLVED` | Define when research worker consumes CMI artifacts |
| **CMI-C07** | Agent 06 vs 08 | Methodology requires causal caution | Market intel may emit predictive signals | Correlation-heavy outputs vs causal claims | Overinterpretation risk | `PARTIALLY_DOCUMENTED` | Require hypothesis tier for predictive market outputs |
| **CMI-C08** | Agent 07 §29 crypto | "Never use single-provider volume as ground truth" | Future CMI volume signals | Operational tension | Volume-based signals without multi-source | `DOCUMENTED` | Enforce multi-source or UNKNOWN for volume signals |
| **CMI-C09** | Global deny | `provider.connect` denied | Any future market data ingestion | Data must come from somewhere | Blocks all live CMI until governed exception | `IMPLEMENTED` | Human-governed mediated ingest architecture (not direct connect) |
| **CMI-C10** | AHOS separation | AHOS has market pipelines (external) | Org CMI architecture (this repo) | Two systems, unclear federation | Duplicate or divergent market semantics | `UNKNOWN` | Define read-only mirror contract when integration approved |
| **CMI-C11** | Chief orchestrator | Slice 1 `agent.chief-orchestrator` | Agent One definition | Three "top" orchestration names | Authority confusion | `UNRESOLVED` | Maintain Agent One as NOT_IMPLEMENTED; no CMI subordination |
| **CMI-C12** | Planned map dependency | "04,05,16,19 before 08–13" | TASK-20260914-008 executed now | Dependency order vs parallel design | Design ahead of enforcement | `ACKNOWLEDGED` | Allow design missions; block production until dependencies verified |

Do not silently resolve any row.

---

## 49. Required Matrices

### Matrix A — Market Intelligence Object Matrix

| Object | Input | Output | Evidence Status | Authority | Risk |
| --- | --- | --- | --- | --- | --- |
| MarketObservation | Agent 07 qualified data | Normalized observation record | Not evidence | None | Low if labeled OBSERVABLE |
| MarketMetric | Observations | Derived numeric | Not evidence | None | Medium — formula error |
| MarketSignal | Metrics | Typed signal + quality vector | Candidate input only | None | High if collapsed to decision |
| MarketRegimeAssessment | Metrics + models | Regime label + conflicts | Interpretation | None | High — stale regime |
| LiquidityAssessment | Depth/reserves | Exitability verdict | Interpretation | None | High — exit risk |
| MarketAnomaly | Metrics | Anomaly record | Not evidence | None | Medium — false positive |
| MarketHypothesis | Signals/anomalies | Testable statement | Hypothesis tier | None | High — narrative bias |
| MarketIntelligenceAssessment | Sub-artifacts | Synthesis | Handoff to Agent 05 | None | High |
| MarketConflict | Diverging sub-signals | Conflict record | Not evidence | None | Medium — ignored conflict |
| MarketSnapshot | Multi-metric | Point-in-time bundle | Context | None | Medium — stale snapshot |
| MarketEvent | Feeds | Typed event | Observation | None | Low |

### Matrix B — Market Signal Matrix

| Signal | Observable | Inferred | Required Data | Failure Modes | Tests |
| --- | --- | --- | --- | --- | --- |
| Return (1h) | OHLC | Yes | Aligned bars, decimals | Gap, stale, wrong window | Golden series |
| Volume spike | Volume | Yes | Baseline window | Wash trade, duplicate | Injected wash pattern |
| Momentum ROC | Price series | Yes | Sufficient history | Missing bars → false ROC | Missingness |
| Bid-ask spread | BBO | Partial | L2 top | Spoofed tight spread | Spoof simulation |
| Depth imbalance | L2 | Yes | Snapshot | Fleeting depth | Time persistence |
| Funding extreme | Funding | Observable | Perp venue | Wrong instrument mapping | Symbol map |
| OI surge | OI | Observable | Exchange API | Restatement | Provider disagreement |
| DEX price impact | Reserves | Yes | Pool state + fee | Low liquidity illusion | Size sweep |
| Cross-venue arb | Multi-venue prices | Yes | Synced timestamps | Stale arb | Latency injection |
| Regime trend | Multi-metric | Yes | Model params | Label churn | Regime stability |
| Wash hypothesis | Trades | Yes | Trade IDs | False positive | Labeled dataset |
| Vol compression | Realized vol | Yes | Window | Post-shock lag | Shock window |

### Matrix C — Provider Dependency Matrix

| Intelligence | Provider | Dependency | Independence | Failure |
| --- | --- | --- | --- | --- |
| Spot price | CEX API A | Exchange matching engine | Partial — single venue | Outage, halt |
| Spot price | Aggregator M | Upstream CEX feeds | No — shared tape | Same stale upstream |
| DEX mid price | Pool RPC | Node + pool | Partial | Reorg, wrong pool |
| Index price | Exchange index | Constituent markets | Partial | Constituent gap |
| Social volume | Social API | Single vendor | No | Bot inflation |
| On-chain swap vol | Indexer | RPC provider | No if shared node | Index lag |
| Funding | Perp venue | Internal mark | Partial | Mark manipulation |
| News sentiment | Wire + scrape | Same article | No | Repost |
| Cross-venue confirm | A + B | If same aggregator | **No** | False confirmation |
| Regime model | Internal | All input providers | Inherited | Cascading |

### Matrix D — Market Conflict Matrix

| Conflict | Possible Cause | Required Investigation | Default Status |
| --- | --- | --- | --- |
| Price up, volume weak | Manipulation, low participation | Trade uniqueness, venue depth | UNRESOLVED |
| Price up, liquidity down | Rug setup, LP exit | LP events, exit sim | POTENTIAL_DANGER |
| CEX up, DEX flat | Lag, different pair, stale | Timestamp align, pair map | UNRESOLVED |
| Momentum bullish, regime ranging | Model disagreement | Multi-model bundle | CONFLICT |
| Market bullish, security dangerous | Honeypot, scam | Agent 10 review | BLOCK actionability |
| Social euphoric, on-chain distributing | Narrative lag | Cross-domain fusion test | HYPOTHESIS |
| Provider A > B price | Stale, different quote | Freshness + semantics | DATA CONFLICT |
| High vol, tight spread | Book artifact | Spoof check | ANOMALY |

### Matrix E — Market Readiness Matrix

| Capability | Documented | Implemented | Tested | Verified | Production |
| --- | --- | --- | --- | --- | --- |
| Market observation model | Yes (this doc) | No | No | No | No |
| Price/volume metrics | Yes | No | No | No | No |
| Liquidity assessment | Yes | No | No | No | No |
| Regime framework | Yes | No | No | No | No |
| DEX intelligence semantics | Yes | No | No | No | No |
| CEX order flow | Yes | No | No | No | No |
| Cross-venue reconciliation | Partial (Agent 07) | No | No | No | No |
| Anomaly detection | Yes | No | No | No | No |
| Manipulation hypotheses | Yes | No | No | No | No |
| Feature registry | Yes | No | No | No | No |
| Signal quality model | Yes | No | No | No | No |
| Epistemic handoff | Partial (Agent 05/07) | No | No | No | No |
| Observability | Yes | No | No | No | No |
| Incident model | Yes | No | No | No | No |

### Matrix F — Agent Boundary Matrix

| Agent | Owns | Consumes | Produces | Must Not Override |
| --- | --- | --- | --- | --- |
| 03 Security | Integrity, access, tamper | CMI artifacts for review | Security flags | Data quality verdicts (07) |
| 04 Governance | Policy, admission | Architecture proposals | L2 decisions | Technical market meaning |
| 05 Epistemic | Evidence, claims, promotion | CMI assessments | Epistemic status | Market interpretation |
| 06 Methodology | Study design, bias control | CMI hypotheses | Method requirements | Data fitness (07) |
| 07 Data Intelligence | Data quality, provenance | Raw provider data | DataQualityAssessment | Market signals |
| **08 Market Intelligence** | **Market meaning, signals** | **Agent 07 qualified data** | **MarketIntelligenceAssessment** | **Agent 07 QA, Agent 05 epistemic** |
| 09 On-Chain | Ledger observations | Chain data | On-chain intel | Market price narrative |
| 10 Token Security | Scam/contract risk | Market + chain | Security verdict | Market opportunity |
| 11 Risk | Loss/exposure framing | CMI + others | Risk assessment | Signal direction |
| 12 Quant | Models, backtests | CMI features | Quant signals | Feature semantics (08) |
| 13 AI/ML | Model lifecycle | CMI features | Predictions | Ground truth |
| 16 QA | Verification | CMI specs | Test results | Architecture |
| 19 Red Team | Adversarial review | CMI claims | Findings | Governance |

### Matrix G — Market Failure Matrix

| Failure | Detection | Impact | Quarantine | Recovery |
| --- | --- | --- | --- | --- |
| Stale price signal | Freshness monitor | False momentum | INVALID signal | Refresh + replay |
| Wash volume signal | Trade pattern | False opportunity | Flag hypothesis | Multi-source vol |
| Formula regression | Golden test fail | Wrong metrics | Stop derive | Fix version + replay |
| Regime label churn | Stability metric | Decision noise | STALE regime | Retrain/recalibrate |
| Cross-venue fake arb | Latency check | False arb | UNRESOLVED | Sync audit |
| Liquidity overestimate | Exit sim fail | Exit trap | Downgrade exitability | Recompute depth |
| Timestamp inversion | Temporal validator | Look-ahead | QUARANTINE batch | Reorder/fix clock |
| Provider restatement | Version detect | Historical signal invalid | Supersede artifacts | Reprocess raw |
| Security conflict ignored | Boundary test | Unsafe action | Block actionability | Force MarketConflict |
| Scalar quality collapse | Schema audit | Overconfidence | Reject scalar | Use vector |

### Matrix H — Data-to-Decision Lineage Matrix

| Layer | Input | Transformation | Output | Authority |
| --- | --- | --- | --- | --- |
| Provider | External feed | Acquisition | Raw bytes | None |
| Data (07) | Raw | QA + normalize | DataArtifact + QA | None |
| Observation (08) | DataArtifact | Bind instrument/time | MarketObservation | None |
| Analysis (08) | Observations | Metrics/signals | MarketSignal | None |
| Intelligence (08) | Signals | Synthesis | MarketIntelligenceAssessment | None |
| Epistemic (05) | MIA + context | Evidence packaging | Evidence | None |
| Risk (11) | Intel + evidence | Framing | RiskAssessment | None |
| Decision (future) | Multi-domain | Authorization | Decision record | Human/governed |
| Execution (future) | Decision | Order placement | Trades | Denied today |

---

## 50. Human Decisions

| ID | Human Decision Required | Why It Matters | Recommended Options | Risk |
| --- | --- | --- | --- | --- |
| **HD-01** | Dual-19: map Plane A market roles (`paper-trading`, `scoring-science`) to Plane D Agent 08 | Prevents duplicate ownership | A) Merge B) Split duties C) Defer | Authority collapse |
| **HD-02** | Adopt CMI readiness levels (§43) as org vocabulary | Enables consistent status reporting | Adopt / Modify / Reject | Misleading maturity claims |
| **HD-03** | Market feature registry location (git vs TCB vs sidecar) | Reproducibility and governance | TCB / Git / Hybrid | Untraceable features |
| **HD-04** | CMI lifecycle enum vs Slice 2B enum mapping | Prevents silent enum merge | Separate / Mapped / Unified | Epistemic confusion |
| **HD-05** | Minimum Agent 07 readiness for live-grade MarketSignal | Fail-closed vs progress | VALIDATED / RECONCILED / RESEARCH_READY only | Stale signal trades |
| **HD-06** | Default cross-venue price reconciliation strategy | No universal hierarchy exists | Unresolved preserve / Weighted / Human tier | False arb |
| **HD-07** | When volume signals require multi-provider confirmation | Wash trading exposure | Always / Above threshold / Never single-source | Fake volume signals |
| **HD-08** | Regime model disagreement presentation | Consensus illusion | Show all / Primary+alternates / Abstain | Wrong regime actions |
| **HD-09** | MarketIntelligenceAssessment → Evidence handoff schema (with Agent 05) | Epistemic boundary | Joint schema / MIA as attachment only | Signal = evidence |
| **HD-10** | Narrative context attachment rules | Sentiment collapse | Context-only / Forbidden until layer exists | Narrative bias |
| **HD-11** | AHOS market data federation model (read-only mirror) | External vs org semantics | Mirror / Mediated contract / Isolated | Divergent truth |
| **HD-12** | Adoption of this document as L2 governance text | Architectural force | Adopt / Partial / Reject | Design-only drift |
| **HD-13** | Manipulation hypothesis auto-action policy | Safety vs false positive | Never auto / Flag only / Escalate | Wrong blocks |
| **HD-14** | Paper-trading role relationship to CMI outputs | Slice 1 overlap | Consumer of CMI / Separate path | Duplicate analytics |

---

## 51. Implementation Gaps

| Gap | Priority | Dependency |
| --- | --- | --- |
| No market datatypes in code | High | Agent 07 data artifacts |
| No feature registry | High | HD-03 |
| No signal engine | High | Data ingest (governed) |
| No regime/liquidity runtime | Medium | Feature registry |
| No cross-venue reconciler | High | Agent 07 reconciliation |
| No CMI↔Epistemic handoff schema | High | Agent 05 HD-09 |
| No golden tests for metrics | High | Agent 16 |
| No observability layer | Medium | Runtime existence |
| No incident/quarantine on signals | Medium | Agent 04 governance |
| Plane A/D mapping unresolved | High | HD-01 |
| Provider connect denied — no ingest path | Blocking | Governance-mediated ingest design |
| AHOS federation undefined | Medium | HD-11 |
| Research worker market integration undefined | Low | HD-14, CMI-C06 |

---

## 52. Recommended Future Missions — STATE ONLY

`RECOMMENDED_NEXT_MISSION = STATE_ONLY — DO NOT EXECUTE`

1. **Agent 09 — On-Chain Intelligence Architecture** (cross-domain fusion boundary with CMI).
2. **Agent 10 — Token Security / Scam Intelligence Architecture** (market-security conflict model).
3. **Agent 07 + 08 joint mission:** DataIntelligenceAssessment → MarketObservation binding schema.
4. **Agent 05 + 08 joint mission:** MarketIntelligenceAssessment → Evidence eligibility test cases.
5. **Agent 12 — Quant / Backtesting Architecture** (feature leakage and backtest boundary).
6. **FUTURE_IMPLEMENTATION_REQUIRED:** MarketFeatureDefinition registry with formula hashes.
7. **FUTURE_IMPLEMENTATION_REQUIRED:** Golden test suite for core metrics (returns, vol, impact).
8. **FUTURE_IMPLEMENTATION_REQUIRED:** CrossVenueAssessment with UNRESOLVED default.
9. **FUTURE_IMPLEMENTATION_REQUIRED:** Regime multi-model disagreement preservation.
10. **FUTURE_IMPLEMENTATION_REQUIRED:** Market incident + signal INVALID propagation.
11. **Red-team mission (Agent 19):** CMI §40 adversarial question battery.
12. **Human L2 session:** Resolve HD-01 Dual-19 market role mapping.

**AGENT-08 does not execute any of the above.**

---

## 53. Final Assessment

The AHOS Agent Organization has **mature upstream architectural discipline** (Agents 03–07, Slice 2B epistemic core, global production denies) but **zero implemented Crypto Market Intelligence runtime**. The highest-risk future failure mode is not missing indicators — it is **market authority collapse**, where observational market metrics silently become trading truth.

This architecture establishes:

1. A strict **Agent 07 → Agent 08 → Agent 05** pipeline with no shortcut to decision or execution.
2. Comprehensive **observation taxonomies** with OBSERVABLE / INFERRED / UNKNOWN discipline.
3. **Two-sided** opportunity and danger intelligence without positive bias.
4. **Cross-venue and provider independence** rules aligned with Agent 07.
5. **Explicit conflict preservation** across price, volume, liquidity, on-chain, social, and security domains.
6. **Dual-19 unresolved** compatibility analysis without merge.
7. Eight required matrices, twelve contradictions, and fourteen human decisions requiring L2 resolution before production candidacy.

**CMI maturity today:** `DOCUMENTED` only. **Next honest step:** resolve HD-01/HD-05 and implement Agent 07 data artifacts before any market signal code.

---

## Document provenance

| Field | Value |
| --- | --- |
| Author | AGENT-08 (Crypto Market Intelligence Architect) |
| Task | TASK-20260914-008 |
| Commander | MASTER ORCHESTRATOR |
| Repository | `G:\robat\ahos-agent-org` |
| Code changes | NONE |
| Runtime changes | NONE |
| AHOS impact | NONE |
| Classification | `[PROPOSED]` architecture unless cited `[IMPLEMENTED]` / `[DOCUMENTED]` |

---

*End of AGENT_08_CRYPTO_MARKET_INTELLIGENCE_ARCHITECTURE.md*
