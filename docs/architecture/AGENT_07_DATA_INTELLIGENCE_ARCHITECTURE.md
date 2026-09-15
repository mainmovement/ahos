# Agent Organization Data Intelligence Architecture

```text
DOCUMENT_ID      = AGENT_07_DATA_INTELLIGENCE_ARCHITECTURE
MISSION_ID       = TASK-20260914-007
VERSION          = 0.1.0
STATUS           = PROPOSED / READ_ONLY_DATA_INTELLIGENCE_ARCHITECTURE
AUTHORITY        = NONE CREATED
RUNTIME_EFFECT   = NONE
AHOS_EFFECT      = NONE
AGENT_ID         = AGENT-07 (agent.org.07-data-intelligence — documentary)
DIRECT_COMMANDER = MASTER ORCHESTRATOR
PARENT           = MASTER ORCHESTRATOR
```

This document is a **design and architecture artifact** produced by AGENT-07 under explicit activation for TASK-20260914-007. It does not implement a data platform, adopt governance, grant authority, modify AHOS, connect providers, or promote knowledge. Facts cite repository evidence with explicit classification labels (`[IMPLEMENTED]`, `[DOCUMENTED]`, `[PROPOSED]`, `[UNKNOWN]`). Architectural recommendations are labeled `[PROPOSED]`.

**Critical honesty constraint:**

```text
DATA                    ≠ EVIDENCE
DATA QUALITY            ≠ TRUTH
DATA VALIDITY           ≠ SOURCE RELIABILITY
SOURCE RELIABILITY      ≠ EVIDENCE STRENGTH
DATA COMPLETENESS       ≠ CORRECTNESS
FRESHNESS               ≠ ACCURACY
SCHEMA VALIDITY         ≠ SEMANTIC VALIDITY
AVAILABILITY            ≠ TRUSTWORTHINESS
CONSISTENCY             ≠ TRUTH
MULTIPLE PROVIDERS      ≠ INDEPENDENT CONFIRMATION
DATA AGREEMENT          ≠ REALITY
DATA ABSENCE            ≠ REAL-WORLD ABSENCE
MODEL INPUT VALIDITY    ≠ MODEL OUTPUT VALIDITY
DATA QUALITY SCORE      ≠ DECISION CONFIDENCE
QUALITY-PASS            ≠ TRUTH
```

---

## 1. Executive Summary

`[VERIFIED]` The AHOS Agent Organization contains a **partial data-intelligence foundation** in Slice 2B (`agent_org/epistemic.py`, `[IMPLEMENTED]` `[TESTED]`): typed `Source` (origin registration with locator and content hash), `Evidence` (dual timestamps, freshness policy, assurance scalar, verification status, supersession), and universal `Provenance` + `lineage` on epistemic artifacts. These encode **epistemic warrant structure**, not a general data quality platform.

`[VERIFIED]` Slice 1 globally denies `provider.connect` and related production capabilities (`ahos_org/policy.py`, `[IMPLEMENTED]` `[TESTED]`). Logical role `agent.provider-data` exists in the registry but **cannot connect to providers** (`[IMPLEMENTED]` registry description).

`[VERIFIED]` No runtime `DataArtifact`, `DataQualityAssessment`, `DataLineage`, `DataContract`, provider registry, reconciliation engine, or data observability layer exists in this repository today.

`[VERIFIED]` Peer architecture documents define boundaries: Agent-03 (security), Agent-04 (governance), Agent-05 (epistemic), Agent-06 (research methodology). Agent-06 explicitly recommended Agent-07 for data quality schema coordination.

**Central architectural question:** How should the organization understand, validate, characterize, govern, reconcile, preserve, trace, and evaluate data before allowing that data to support research, epistemic reasoning, prediction, scoring, decision-making, or future execution?

**Primary data-intelligence objective:** prevent **data authority collapse** — where syntactic validity, provider availability, freshness labels, quality scores, or multi-provider agreement silently become truth, evidence strength, or decision confidence.

**Current data-intelligence posture:** `[PARTIALLY_VERIFIED]` — strong provenance and freshness contracts on epistemic `Source`/`Evidence`; no structured data quality dimensions, provider independence model, reconciliation rules, data contracts, or fitness-for-purpose gates in code.

**Dual-19 status:** `[VERIFIED]` `[CONFLICT / UNRESOLVED]` — Slice 1 Plane A (`agent.*`, including `agent.provider-data`) and planned Plane D (`agent.org.07-data-intelligence`) remain separate taxonomies. This document analyzes data implications only; it does not merge them.

**Agent One:** `NOT_IMPLEMENTED / FUTURE_NON_AUTHORITY_ROOT` — must never become data authority or truth root.

**AHOS:** `[VERIFIED]` Separate product repository. This mission performs read-only boundary analysis only. `AHOS_IMPACT = NONE`.

---

## 2. Agent-07 Identity

| Field | Value |
| --- | --- |
| `AGENT_ID` (mission) | `AGENT-07` |
| Blueprint ID | `agent.org.07-data-intelligence` |
| Provisional name | Data Intelligence Architect |
| Role | Design data intelligence architecture: quality, provenance, semantics, lineage, conflicts, fitness-for-purpose |
| Authority class | `NONE` (design mission only) |
| Capabilities exercised | READ, ANALYZE, PROPOSE (documentation) |
| Forbidden | VERIFY (own conclusions), PROMOTE, EXECUTE, MODIFY runtime, CONNECT providers, ACTIVATE other agents, declare data truthful from quality pass |
| Supervisor | MASTER ORCHESTRATOR → human operator (MEHRDAD) |
| Source of truth | **Not** AGENT-07. Repository L0/L1 + governance L2/L3 only. |

AGENT-07 is **not** Agent One, **not** the Master Orchestrator, **not** a data engineer implementing pipelines, **not** a provider operator, **not** an epistemic authority, **not** a verifier of its own deliverables, and **not** authorized to convert quality-pass into truth or evidence.

---

## 3. Command Chain

```text
MEHRDAD
  → MASTER ORCHESTRATOR
    → AGENT-07 (this mission)
```

- Direct commander: **MASTER ORCHESTRATOR**
- Parent: **MASTER ORCHESTRATOR**
- Reporting line: **MASTER ORCHESTRATOR**
- Agent-03, Agent-04, Agent-05, Agent-06 are **peer specialists**, not commanders.
- No subordinate agents created or activated by this mission.
- No modification of reporting line.

---

## 4. Lifecycle

### 4.1 Activation rule

Creating, registering, or naming an agent does **not** activate it. TASK-20260914-007 is the explicit activation command for this mission.

### 4.2 Mission lifecycle

```text
REGISTERED / IDLE / DORMANT
  → [explicit activation: TASK-20260914-007]
  → RUNNING (data intelligence architecture analysis)
  → COMPLETED (this deliverable)
  → IDLE / DORMANT / WAITING_FOR_NEW_COMMAND
```

### 4.3 Terminal states

Supported: `COMPLETED`, `FAILED`, `TIMEOUT`, `CANCELLED`, `BLOCKED`, `SUSPENDED`, `QUARANTINED`.

After termination: `LIFECYCLE_STATUS = IDLE / DORMANT / WAITING_FOR_NEW_COMMAND`.

Recommendations in this document are **not** commands. AGENT-07 does not auto-continue to Agent-08 or any future mission.

---

## 5. Data Intelligence Role

### 5.1 Scope

AGENT-07 owns **architectural design** for:

- Data meaning, origin, transformations, and uncertainty
- Multi-dimensional quality characterization (not scalar collapse)
- Provenance and lineage traceability
- Provider identity, dependency, and contextual reliability
- Semantic and temporal integrity requirements
- Conflict, gap, anomaly, and duplication representation
- Fitness-for-purpose and readiness levels
- Data-to-decision trace requirements
- Coordination boundaries with security, governance, epistemic, and research domains

### 5.2 Out of scope

- Implementing data pipelines, provider adapters, or storage
- Connecting to external providers or AHOS production
- Granting governance authority or approving provider admission
- Assigning epistemic status or promoting knowledge
- Defining research methodology (Agent-06) or security controls (Agent-03)
- Declaring any dataset "true" because it passes quality checks

### 5.3 Distinction from Data Engineering

| Concern | Data Engineer (future runtime) | Data Intelligence Architect (Agent-07) |
| --- | --- | --- |
| Primary question | "How do we move and store data?" | "What must be true about data before it may support reasoning?" |
| Output | Pipelines, schemas, jobs | Contracts, quality models, lineage rules, readiness gates |
| Success metric | Throughput, uptime | Traceability, distinguishability of failure modes |
| Authority | Operational (when granted) | None (design only) |

---

## 6. Core Distinctions

These are **architectural constraints**, not slogans. Violating them is a data-intelligence defect.

| Forbidden equality | Why it fails |
| --- | --- |
| DATA = EVIDENCE | Data is raw or derived material; evidence is a bounded warrant artifact with epistemic role |
| DATA QUALITY = TRUTH | High-quality wrong data remains wrong |
| DATA VALIDITY = SOURCE RELIABILITY | Schema pass does not prove provider honesty |
| SOURCE RELIABILITY = EVIDENCE STRENGTH | Reliable stale source may not support live claims |
| DATA COMPLETENESS = CORRECTNESS | Complete dataset can be uniformly wrong |
| FRESHNESS = ACCURACY | Recent incorrect data is fresh but inaccurate |
| SCHEMA VALIDITY = SEMANTIC VALIDITY | Syntactically valid wrong-units records pass schema |
| AVAILABILITY = TRUSTWORTHINESS | Available manipulated feed is untrustworthy |
| CONSISTENCY = TRUTH | Internally consistent fiction remains fiction |
| MULTIPLE PROVIDERS = INDEPENDENT CONFIRMATION | Shared upstream breaks independence |
| DATA AGREEMENT = REALITY | Colluding or correlated sources can agree on error |
| DATA ABSENCE = REAL-WORLD ABSENCE | Missing observation ≠ zero |
| MODEL INPUT VALIDITY = MODEL OUTPUT VALIDITY | Valid features + flawed model = invalid output |
| DATA QUALITY SCORE = DECISION CONFIDENCE | Decision confidence requires relevance + independence + epistemic review |

`[IMPLEMENTED]` Subset encoded in Slice 2B module docstring: "Stored memory, confidence, recency, and audit inclusion never imply truth."

---

## 7. Data Object Model

Each object below is classified as **conceptual**, **runtime**, or **documentary**. Not all conceptual objects must become runtime entities.

### 7.1 Object catalog

| Object | Meaning | Classification today |
| --- | --- | --- |
| **DataSource** | Abstract origin class (e.g., chain RPC, exchange API, file) | `[PROPOSED]` conceptual |
| **Provider** | Concrete supplier of data with identity, incentives, history | `[PROPOSED]` conceptual |
| **Dataset** | Bounded collection of records sharing contract and provenance | `[PROPOSED]` conceptual |
| **DataArtifact** | Immutable or versioned stored data unit (raw, normalized, derived) | `[PROPOSED]` conceptual |
| **DataRecord** | Single logical record within an artifact | `[PROPOSED]` conceptual |
| **Observation** | Measured value at an event (may overlap epistemic `Observation`) | `[IMPLEMENTED]` epistemic type; data layer `[PROPOSED]` binding |
| **Event** | Something that happened in source domain with event-time | `[PROPOSED]` conceptual |
| **Snapshot** | Point-in-time capture of a dataset or entity state | `[PROPOSED]` conceptual |
| **Stream** | Time-ordered sequence of events/records | `[PROPOSED]` conceptual |
| **Feature** | Computed input variable for analysis/ML | `[PROPOSED]` conceptual |
| **DerivedFeature** | Feature computed from other features or derived data | `[PROPOSED]` conceptual |
| **Transformation** | Documented operation from input artifact(s) to output | `[PROPOSED]` conceptual; partial via `extraction_method` on Evidence |
| **DataQualityAssessment** | Multi-dimensional quality evaluation of an artifact | `[PROPOSED]` conceptual |
| **DataLineage** | Directed acyclic graph of artifact dependencies | `[PROPOSED]` conceptual; partial via `lineage` tuples on artifacts |
| **DataConflict** | Unresolved disagreement between data sources/records | `[PROPOSED]` conceptual; epistemic `ContradictionCase` is separate |
| **DataAnomaly** | Detected deviation from expected pattern | `[PROPOSED]` conceptual |
| **DataGap** | Known missing coverage (distinct from zero) | `[PROPOSED]` conceptual |
| **DataVersion** | Version identifier for artifact content | `[IMPLEMENTED]` partial via `version` int on epistemic artifacts |
| **SchemaVersion** | Version of structural/semantic contract | `[PROPOSED]` conceptual |
| **DataContract** | Producer/consumer agreement on schema, semantics, SLAs | `[PROPOSED]` conceptual |
| **DataPolicy** | Governance rule for data admission, use, retention | `[DOCUMENTED]` Slice 1 deny tokens; `[PROPOSED]` data-specific policies |
| **DataReliabilityProfile** | Contextual historical reliability characterization | `[PROPOSED]` conceptual |
| **Source** (Slice 2B) | Registered origin with locator and hash | `[IMPLEMENTED]` runtime epistemic type |
| **Evidence** (Slice 2B) | Warrant artifact from source with freshness | `[IMPLEMENTED]` runtime epistemic type |

### 7.2 Layer separation

```text
DATA LAYER          →  characteristics, provenance, quality, conflicts
EPISTEMIC LAYER     →  evidence, claims, verification (Agent 05)
METHODOLOGY LAYER   →  whether data meets study requirements (Agent 06)
GOVERNANCE LAYER    →  who may admit providers, override quarantine (Agent 04)
SECURITY LAYER      →  tampering, injection, unauthorized access (Agent 03)
```

Data objects may **inform** evidence creation but must not **collapse into** evidence automatically.

### 7.3 Mapping DataArtifact → Evidence

`[PROPOSED]` Conversion path (never automatic):

```text
DataArtifact + DataQualityAssessment + DataContract compliance
  → eligibility review (purpose-specific)
  → optional human/agent attestation
  → Evidence registration (Agent 05 domain) with explicit extraction_method
```

A quality-pass alone is **insufficient** for evidence registration.

---

## 8. Provider Model

### 8.1 Provider identity `[PROPOSED]`

| Field | Purpose |
| --- | --- |
| `provider_id` | Stable identifier (namespace: `provider.`) |
| `provider_type` | INDEXER, EXCHANGE, AGGREGATOR, RPC, ORACLE, NEWS, SOCIAL, RESEARCH, INTERNAL |
| `ownership` | Legal/operational owner |
| `acquisition_mechanism` | API, RPC, scrape, file drop, manual |
| `endpoint_refs` | Locators (not credentials) |
| `data_domains` | on-chain, market, off-chain, macro, etc. |
| `geographic_coverage` | Regions, chains, markets |
| `update_frequency` | Expected cadence |
| `historical_depth` | Earliest reliable data |
| `known_limitations` | Documented gaps and biases |
| `known_failure_modes` | Outage, lag, restatement, manipulation patterns |
| `incentives` | Business model affecting data honesty |
| `reliability_history_ref` | Link to DataReliabilityProfile |
| `schema_version_refs` | Active contract versions |
| `licensing_constraints` | Usage restrictions |
| `admission_status` | PROPOSED, APPROVED, SUSPENDED, REVOKED |
| `dependency_graph_ref` | Upstream providers this provider depends on |

### 8.2 Provider ≠ Source

- **Provider** supplies data through one or more endpoints.
- **Source** (Slice 2B) is a registered origin instance with locator and content hash at capture time.
- One provider may produce many Source registrations; one Source may aggregate multiple provider inputs (must be documented).

### 8.3 Reputation ≠ current correctness

Historical reliability informs **contextual priors**, not unconditional trust. A previously reliable provider can fail, be compromised, or restate history.

### 8.4 Current repository state

| Item | Status |
| --- | --- |
| `provider.connect` capability | `[IMPLEMENTED]` globally denied |
| `agent.provider-data` logical role | `[IMPLEMENTED]` registry entry; cannot connect |
| Provider registry runtime | `[PROPOSED]` |
| Provider admission workflow | `[PROPOSED]` governance (Agent 04) |

---

## 9. Provenance

### 9.1 Required provenance fields (consequential artifacts)

Where feasible, every consequential data artifact should trace:

| Field | Meaning |
| --- | --- |
| Source / provider identity | Who produced upstream |
| Endpoint / acquisition path | How obtained |
| Acquisition timestamp | When captured |
| Event timestamp | When the underlying event occurred (if applicable) |
| Transformation identity + version | What changed the data |
| Schema version | Contract at capture/transform |
| Parser / tool version | Software that interpreted bytes |
| Agent / operator identity | Who initiated acquisition |
| Predecessor artifact refs | Input artifacts |
| Downstream consumer refs | Who used it (when known) |

### 9.2 Slice 2B provenance (implemented subset)

`[IMPLEMENTED]` `Provenance` dataclass: `creator_principal_id`, `session_id`, `command_id`, `method`, `source_refs`.

`[IMPLEMENTED]` All epistemic artifacts require typed `Provenance` and support `lineage: tuple[str, ...]`.

`[IMPLEMENTED]` TCB enforces provenance match on mutation (`artifact_provenance_mismatch` → deny).

### 9.3 Provenance ≠ correctness

Perfect provenance enables audit and reproduction; it does not prove the captured content matches reality. Provenance answers **where this came from and how it was handled**, not **whether it is true**.

---

## 10. Data Lineage

### 10.1 Canonical lineage chain

```text
SOURCE / PROVIDER
      ↓
ACQUISITION
      ↓
RAW ARTIFACT                    (immutable preferred)
      ↓
NORMALIZATION
      ↓
TRANSFORMATION(S)
      ↓
DERIVED DATA / DATASET
      ↓
FEATURE(S)
      ↓
ANALYSIS INPUT
      ↓
EVIDENCE / RESEARCH RESULT      (epistemic layer — Agent 05)
      ↓
DECISION                        (future decision system)
```

### 10.2 Transition requirements

| Transition | Immutable ref | Version | Timestamp | Transform record | Validation | Owner | Reproducibility |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Source → Raw | Required | Required | Acquisition + event | Minimal (capture params) | Schema + hash | Acquirer | Replay from source if allowed |
| Raw → Normalized | Required | Required | Processing | Required | Contract check | Pipeline | Deterministic transform spec |
| Normalized → Derived | Required | Required | Processing | Required | Semantic + statistical | Pipeline | Full param record |
| Derived → Feature | Required | Required | Feature cutoff time | Required | Leakage check | Feature owner | Definition hash |
| Feature → Analysis | Required | Required | Analysis time | Optional | Method check | Analyst | Analysis script hash |
| Analysis → Evidence | Required | Required | Packaging time | extraction_method | Epistemic gate | Agent 05 path | Linked data refs |

**Rule:** Valid upstream does not auto-validate downstream. Each transition may introduce new failure modes.

### 10.3 Lineage graph properties `[PROPOSED]`

- Directed acyclic graph (cycles indicate error or undocumented feedback)
- Immutable raw nodes preferred
- Supersession edges for restatements (never silent overwrite)
- Uncertainty propagation annotations on edges

---

## 11. Data Quality

### 11.1 Multi-dimensional quality model

Quality is a **vector**, not a scalar, unless a specific downstream use case publishes which dimensions are collapsed and why.

| Dimension | Question |
| --- | --- |
| **Completeness** | Are required fields, records, entities, and time windows present? |
| **Correctness** | Does content match ground truth where verifiable? |
| **Consistency** | Internal and cross-record coherence? |
| **Validity** | Conforms to syntactic rules and ranges? |
| **Uniqueness** | Duplicate-free where identity requires? |
| **Timeliness** | Arrived within expected latency? |
| **Freshness** | Current enough for intended use? |
| **Integrity** | Unchanged since capture (hash/signature)? |
| **Precision** | Resolution adequate for use? |
| **Accuracy** | Closeness to true value (where measurable)? |
| **Coverage** | Geographic, entity, and domain span? |
| **Availability** | Accessible when needed? |
| **Continuity** | Gaps in time series? |
| **Stability** | Schema and distribution stable over window? |
| **Provenance** | Traceable origin and handling? |
| **Semantic validity** | Correct units, identity, timezone, domain meaning? |

### 11.2 DataQualityAssessment `[PROPOSED]`

```text
DataQualityAssessment
  artifact_id
  assessed_at
  assessor_principal_id
  purpose_context          # fitness-for-purpose binding
  dimension_scores         # per-dimension enum or structured rating
  detected_gaps[]          # DataGap refs
  detected_anomalies[]     # DataAnomaly refs
  detected_conflicts[]     # DataConflict refs
  overall_readiness_hint   # NOT truth; readiness only
  limitations              # explicit scope limits
  provenance
```

### 11.3 Implemented partial quality signals

| Signal | Location | Status |
| --- | --- | --- |
| Content hash | Source, Evidence | `[IMPLEMENTED]` |
| Freshness max age + expiry | Evidence | `[IMPLEMENTED]` |
| Evidence STALE state | EvidenceState | `[IMPLEMENTED]` |
| Assurance 0–100 scalar | Evidence | `[IMPLEMENTED]` — **risk of scalar collapse** |
| Verification status | Evidence | `[IMPLEMENTED]` epistemic, not data QA |
| Lineage tuples | All epistemic artifacts | `[IMPLEMENTED]` |

`[PROPOSED]` Agent 05 HD-04 and this document recommend replacing or supplementing scalar `assurance` with explicit quality vectors for data-derived evidence.

---

## 12. Quality vs Truth

### 12.1 Failure modes (dataset can be…)

| State | Example | Architectural response |
| --- | --- | --- |
| Internally consistent but wrong | All records use wrong token decimals consistently | Semantic validation; spot checks against independent source |
| Complete but manipulated | Full wash-traded volume history | Manipulation pattern detection; not completeness praise |
| Fresh but inaccurate | Live price feed with systematic bias | Freshness label + accuracy dimension separate |
| Accurate historically but stale now | Yesterday's liquidity snapshot for live trade | Staleness gate blocks live use |
| Schema-valid but semantically wrong | Price in cents labeled as dollars | Semantic contract beyond JSON schema |
| High-quality technically but irrelevant | Perfect weather data for token scoring | Fitness-for-purpose check |

### 12.2 Anti-pattern: quality-pass → truth

```text
FORBIDDEN CHAIN:
  schema_valid AND freshness=FRESH
    → label TRUTH
    → register Evidence as VERIFIED
    → promote Knowledge
```

**Required chain:**

```text
PERMITTED CHAIN:
  DataQualityAssessment (multi-dim) + purpose context
    → FIT_FOR_PURPOSE evaluation
    → eligibility for Evidence packaging (Agent 05)
    → independent verification (if required)
    → epistemic status assignment (Agent 05)
    → governance promotion (if ever)
```

---

## 13. Data Contracts

### 13.1 DataContract structure `[PROPOSED]`

| Section | Contents |
| --- | --- |
| **Identity** | contract_id, schema_version, effective_dates |
| **Schema** | fields, types, ordering |
| **Semantics** | units, enumerations, entity identity rules |
| **Constraints** | required/optional, ranges, nullability, uniqueness |
| **Temporal** | timestamp conventions (event vs observation vs ingestion) |
| **Producer obligations** | delivery SLA, restatement policy, notification |
| **Consumer expectations** | handling of null, gap, conflict, stale |
| **Failure behavior** | reject, quarantine, partial accept, degrade |
| **Compatibility** | backward/forward rules |

### 13.2 Compatibility analysis

| Change type | Backward compatible? | Forward compatible? | Semantic compatible? |
| --- | --- | --- | --- |
| Add optional field | Often yes | Often yes | If semantics documented |
| Remove field | No | — | — |
| Type widening | Sometimes | — | May break semantics |
| Type narrowing | No | — | — |
| Unit change | No | No | **Never** silent |
| Timestamp semantics change | No | No | Critical for leakage |
| Identity key change | No | No | Breaks dedup and joins |

**Rule:** `schema compatibility ≠ semantic compatibility`.

---

## 14. Schema Evolution

### 14.1 Controls `[PROPOSED]`

1. **Version bump policy** — every material change increments schema_version
2. **Migration record** — transformation from vN to vN+1 with reversible spec where feasible
3. **Dual-read window** — consumers accept N and N+1 during transition
4. **Breaking change gate** — governance approval (Agent 04) for production-impacting breaks
5. **Semantic diff** — human-readable semantic changelog, not only JSON diff
6. **Downstream impact assessment** — features, research, decisions affected
7. **Historical interpretability** — old research readable with old schema version pinned

### 14.2 Restatement vs evolution

Provider **restatement** (correcting past values) is not schema evolution. Restatements require new artifact version with supersession link, never silent overwrite.

---

## 15. Semantic Integrity

### 15.1 Semantic failure catalog

| Failure | Detection | Consequence if undetected |
| --- | --- | --- |
| Wrong units | Unit registry, range sanity | Systematic scale error |
| Wrong decimals | Token metadata cross-check | Orders-of-magnitude error |
| Wrong timezone | UTC normalization audit | Leakage, misaligned events |
| Wrong chain | chain_id validation | Cross-chain contamination |
| Wrong token identity | Address + chain + symbol tuple | Portfolio/analytics corruption |
| Wrong address normalization | Checksum, casing rules | Missed joins, false matches |
| Wrong event type | ABI / schema mapping audit | Misclassified activity |
| Wrong symbol / pair | Canonical pair registry | Price/volume on wrong market |
| Wrong market pair identity | pool_id + fee tier | Liquidity misattribution |
| Wrong timestamp interpretation | event_time vs block_time policy | Causal inversion |
| Wrong currency | Quote asset validation | FX conflation |
| Wrong precision | Significant figures vs storage | Rounding artifacts |

A record can pass JSON Schema validation while failing every semantic check above.

### 15.2 Semantic validation layer `[PROPOSED]`

Sits **above** syntactic validation:

```text
Bytes → Syntax parse → Schema validation → Semantic validation → Quality assessment
```

---

## 16. Temporal Integrity

### 16.1 Timestamp taxonomy

| Timestamp | Meaning |
| --- | --- |
| **Event time** | When the real-world/domain event occurred |
| **Observation time** | When the phenomenon was observable on chain/instrument |
| **Acquisition time** | When this organization captured the data |
| **Ingestion time** | When data entered storage/pipeline |
| **Processing time** | When transform/feature job ran |
| **Verification time** | When quality/epistemic verification occurred |
| **Decision time** | When a decision consumed the data |

All consequential artifacts should record which timestamp types they carry and which govern validity for each use case.

### 16.2 Temporal failure modes

| Failure | Description | Mitigation |
| --- | --- | --- |
| Late events | Arrive after window closed | Watermark policy; revision artifacts |
| Clock skew | Producer clocks disagree | Skew tolerance; NTP audit |
| Out-of-order events | Sequence violations | Reordering buffer; explicit disorder flag |
| Duplicated events | Same event_id replayed | Idempotent keys |
| Future leakage | Future data in historical feature | Point-in-time joins; cutoff enforcement |
| Historical corrections | Provider fixes past | Supersession, not overwrite |
| Backfills | Retroactive gap fill | Mark backfill boundary in lineage |
| Provider restatements | Bulk history rewrite | Version + diff + downstream invalidation |

**Rule:** Preserve temporal truth. Do not silently relabel stale acquisition as current event time.

---

## 17. Freshness / Staleness

### 17.1 Freshness states `[PROPOSED]`

| State | Meaning |
| --- | --- |
| **LIVE** | Streaming or sub-second latency for domain |
| **FRESH** | Within purpose-specific freshness threshold |
| **AGING** | Approaching threshold; usable with caution flag |
| **STALE** | Outside threshold; blocked for live decisions |
| **EXPIRED** | Past hard expiry; archival/historical only |
| **UNKNOWN** | Freshness cannot be determined |

`[IMPLEMENTED]` Slice 2B Evidence: `freshness_max_age_seconds`, `expires_at`, `EvidenceState.STALE`.

### 17.2 Domain-specific thresholds

Freshness thresholds must be **domain-specific** and **decision-specific**:

| Domain | Example FRESH window | Example STALE impact |
| --- | --- | --- |
| Liquid CEX spot price | seconds–minutes | Live scoring blocked |
| DEX pool reserves | block-time aligned | Slippage estimate invalid |
| Daily on-chain metrics | 24h + buffer | Trend analysis OK, execution not |
| Token metadata | days (if verified) | Identity risk if stale |
| News / social | minutes–hours | Event detection vs historical study |

**Rule:** Do not treat stale data as live merely because it remains technically available.

---

## 18. Completeness

### 18.1 Completeness levels

| Level | Question |
| --- | --- |
| **Field** | Required fields present? |
| **Record** | Expected records in batch? |
| **Time window** | Continuous coverage for interval? |
| **Entity** | All entities in population represented? |
| **Provider** | Expected providers contributing? |
| **Dataset** | All constituent artifacts present? |
| **Population** | Sample covers defined universe? |
| **Event stream** | All event types represented? |

### 18.2 Critical gap rule

> `99% complete` may hide the missing `1%` containing the most important events.

Completeness metrics must report **where** incompleteness occurs (time range, entity class, event type), not only a global percentage.

---

## 19. Duplication

### 19.1 Duplication categories

| Type | Description | Dedup caution |
| --- | --- | --- |
| Exact duplicate | Identical bytes/hash | Safe to collapse with same provenance |
| Semantic duplicate | Same meaning, different encoding | Requires identity key agreement |
| Replayed event | Same event_id re-delivered | Idempotent ingestion |
| Provider duplicate | Provider sends twice | Provider-specific dedup key |
| Cross-provider duplicate | Same event via two paths | May be confirmation OR correlated echo |
| Chain event duplication | Log index + tx uniqueness | chain-specific identity |
| Retry duplication | Transport retry artifact | Dedup by request id |

### 19.2 Identity keys `[PROPOSED]`

Identity keys must be **domain-defined** (e.g., `(chain_id, block_number, tx_hash, log_index)` for EVM logs). Never deduplicate merely because two records look similar if they may represent distinct real-world events.

---

## 20. Data Gaps

### 20.1 DataGap representation `[PROPOSED]`

```text
DataGap
  gap_id
  artifact_or_dataset_ref
  missing_description        # what is missing
  expected_coverage          # what should have been present
  time_range                 # if temporal
  entity_scope               # addresses, tokens, markets, etc.
  reason                     # OUTAGE, NOT_YET_BACKFILLED, UNKNOWN, ...
  detection_method
  detected_at
  downstream_impact          # which features/decisions affected
  distinguish_from_zero      # MUST be true
```

**Critical rule:** Missing data must remain distinguishable from zero. Null, absent, and zero are three different states.

---

## 21. Data Anomalies

### 21.1 Anomaly categories

| Category | Examples |
| --- | --- |
| Outlier | Price spike beyond tolerance |
| Impossible value | Negative supply |
| Discontinuity | Level shift without event |
| Sudden provider change | Schema or distribution jump |
| Schema anomaly | Unexpected fields |
| Semantic anomaly | Right schema, wrong units |
| Temporal anomaly | Future timestamp, time travel |
| Duplicate burst | Retry storm |
| Missing burst | Provider partial outage |
| Suspicious manipulation | Wash trade pattern, spoofing |

### 21.2 Handling principle

Do **not** automatically delete anomalies. An anomaly may be:

- Measurement error → quarantine or correct with audit
- Legitimate event → retain and document
- Manipulation → flag, preserve for investigation
- Novel behavior → coordinate with Agent-05 **NOVEL** state (§26)

---

## 22. Data Conflicts

### 22.1 Conflict types

| Conflict | Example |
| --- | --- |
| Provider disagreement | Two prices differ beyond tolerance |
| Timestamp disagreement | Event time differs across sources |
| Token identity disagreement | Symbol collision across chains |
| Price / liquidity / volume disagreement | Metric divergence |
| Event ordering disagreement | Mempool vs confirmed order |
| Historical restatement | Provider A restates, B does not |

### 22.2 Resolution principles

Do **not** automatically apply "majority provider wins."

Resolution must consider:

- Source type and domain semantics
- Provider independence (§23)
- Freshness and provenance quality
- Known failure modes
- Decision impact tier
- Whether conflict is resolvable or must remain **UNRESOLVED**

`[PROPOSED]` DataConflict artifact preserves all sides until explicit resolution or epistemic ContradictionCase (Agent 05) when propositions conflict.

---

## 23. Provider Independence

### 23.1 False independence

Two providers are **NOT** independent merely because:

- Different company names
- Different API endpoints
- Different branding

### 23.2 Shared dependency catalog

| Shared dependency | Effect |
| --- | --- |
| Same upstream exchange | Correlated price errors |
| Same blockchain indexer | Correlated lag/reorg handling |
| Same RPC provider | Correlated node state |
| Same market-data vendor | Same underlying tape |
| Same cached dataset | Echo, not confirmation |
| Same source article | Repost, not corroboration |
| Same oracle network | Correlated feed failure |

### 23.3 Dependency / correlation model `[PROPOSED]`

```text
ProviderDependencyGraph
  provider_id
  upstream_provider_ids[]
  shared_infrastructure_tags[]
  correlation_cluster_id
  independence_claim_allowed   # boolean + evidence
```

Evidence of "two independent sources" requires documented **distinct correlation clusters**, not distinct names.

Aligns with Agent-05 Independence Matrix and Agent-06 correlated error rules.

---

## 24. Source Reliability

### 24.1 Contextual reliability profile `[PROPOSED]`

Dimensions (evaluated per domain and time window):

| Dimension | Meaning |
| --- | --- |
| Historical accuracy | vs audit ground truth when available |
| Uptime | Availability SLA adherence |
| Latency | Delivery timeliness |
| Completeness | Gap frequency |
| Correction rate | Restatement frequency and magnitude |
| Anomaly rate | Detected anomalies per volume |
| Provenance quality | Metadata completeness |
| Independence | Distinct upstream |
| Manipulation exposure | Known attack surface |
| Domain coverage | Breadth vs claim |

### 24.2 Forbidden output

Never produce unconditional `Provider X = trusted`. Instead:

```text
Provider X: RELIABILITY_CONTEXTUAL
  domain: on-chain transfers (chain Y)
  window: 2026-Q1
  accuracy: HIGH (audit sample n=500)
  staleness_incidents: 2
  independence_cluster: cluster-7
  NOT VALID FOR: live MEV-sensitive decisions without fresh stream
```

---

## 25. Data Reconciliation

### 25.1 Reconciliation strategies `[PROPOSED]`

| Strategy | When appropriate | Risk |
| --- | --- | --- |
| Exact agreement | Identity fields should match | False precision |
| Tolerance agreement | Numeric drift within epsilon | Wrong tolerance hides manipulation |
| Weighted reconciliation | Known reliability weights | Weight bias |
| Source-priority | Governance-approved hierarchy | **Requires evidence**; not universal |
| Temporal reconciliation | Align on event-time windows | Window choice bias |
| Semantic reconciliation | Normalize units/identity first | Normalization error |
| Manual review | High-stakes conflict | Cost |
| Unresolved conflict | Preserve all values | Downstream must handle UNKNOWN |

Do **not** create a universal provider hierarchy without human governance decision and evidence (HD-09 in Agent-06 aligns).

---

## 26. Anomaly vs Novelty

| Concept | Meaning | Owner coordination |
| --- | --- | --- |
| **Anomaly** | Deviation from established pattern/model | Agent-07 detection and classification |
| **Novelty** | Unexpected but potentially real new behavior | Agent-05 epistemic **NOVEL** status |

A new market regime may initially look like an anomaly. A novel blockchain event may violate existing assumptions.

**Rule:** Do not automatically clean away novelty. Pipeline default should **flag**, not **delete**, unless quarantine policy (§38) requires isolation.

---

## 27. Transformation Governance

Every material transformation should preserve:

| Element | Purpose |
| --- | --- |
| Input artifact refs | Reproducibility |
| Transformation identity + version | Change tracking |
| Parameters | Replay |
| Execution time | Temporal audit |
| Output artifact ref | Lineage continuation |
| Validation results | Quality gate record |
| Operator / agent identity | Accountability |

Avoid opaque transformations that cannot be reconstructed. `[IMPLEMENTED]` partial: `extraction_method` on Evidence; `[PROPOSED]` full Transformation registry.

---

## 28. Feature Engineering

### 28.1 Feature requirements (future ML/AI)

| Requirement | Rationale |
| --- | --- |
| Feature provenance | Lineage to raw data |
| Feature definition | Human-readable spec |
| Units | Semantic clarity |
| Calculation | Formula or code hash |
| Lookback window | Leakage prevention |
| Timestamp semantics | Which time governs cutoff |
| Leakage risk attestation | Agent-06 coordination |
| Version | Schema + definition version |
| Dependencies | Upstream features/data |
| Training/serving parity | Same definition in both paths |

**Rules:** `feature ≠ evidence`, `feature ≠ truth`. Features are derived inputs; epistemic packaging requires separate Evidence path.

---

## 29. Crypto / Market Data

Architecture-only analysis for AHOS domain context. **Does not modify AHOS.**

### 29.1 Integrity risks

| Risk | Description |
| --- | --- |
| Block timestamps | Miner manipulation, variance |
| Transaction ordering | Mempool vs block finality |
| Chain reorganizations | Reorg invalidates recent "confirmed" data |
| RPC disagreement | Node state divergence |
| Indexer lag | Apparent stale on-chain state |
| Mempool visibility | Partial observation |
| Token decimals | Contract metadata errors |
| Token identity | Multi-chain symbol collisions |
| Pair / pool identity | Factory variants, fee tiers |
| Liquidity calculations | Range, concentration, fake depth |
| Volume calculations | Wash trading inflation |
| Wash trading / spoofing | Manipulation patterns |
| Fake liquidity | Ephemeral depth |
| Stale market feeds | Displayed but old |
| Provider restatements | Historical rewrite |
| Token migrations | Contract upgrades, redirects |
| Wrapped assets | Bridge/depeg semantics |
| Chain-specific semantics | UTXO vs account, finality rules |

### 29.2 Architectural response

- Separate **observed on-chain** from **interpreted metrics**
- Never use single-provider volume as ground truth without independence check
- Treat DEX metrics as manipulation-exposed by default
- Bind all token/pool references to `(chain_id, address, ...)` tuples

---

## 30. On-Chain Data

### 30.1 Identity and finality

| Concept | Requirement |
| --- | --- |
| Block height / hash | Pin observations to canonical block |
| Transaction hash | Primary tx identity |
| Log / event identity | `(tx_hash, log_index)` or chain equivalent |
| Address normalization | Checksum, lowercase policy documented |
| Chain ID | Explicit on every record |
| Contract identity | Proxy vs implementation documented |
| Token mint / address | Not symbol alone |
| Event ordering | Block position + log index |
| Finality assumptions | Confirmations required stated |
| Reorg handling | Invalidate or supersede below depth N |

### 30.2 Observed vs interpreted

```text
OBSERVED ON CHAIN     = raw logs, balances, bytecode (with node caveats)
INTERPRETED           = "transfer", "swap", "liquidity added", USD value
```

Interpretation requires documented decoder version and semantic contract.

---

## 31. Off-Chain Data

### 31.1 Source classes

News, social media, websites, announcements, research reports, APIs, community data.

### 31.2 Integrity concerns

| Concern | Handling |
| --- | --- |
| Source authenticity | Identity verification, official channel registry |
| Timestamps | Publication vs edit vs capture time |
| Reposts | Duplicate content detection |
| Bot-generated content | Bot score; not organic volume |
| Source incentives | Promotional bias flag |
| Manipulation | Coordinated campaigns |
| Deletion / edits | Capture snapshot; note mutability |
| Provenance | Original URL, archive link |

**Rule:** Do not assume social volume = organic demand.

---

## 32. Security Boundary (Agent 03)

| Domain | Owner |
| --- | --- |
| Unauthorized access, malicious data, injection, tampering, isolation | **Agent 03** |
| Data quality and integrity characteristics for intended use | **Agent 07** |

```text
SECURITY INTEGRITY     ≠ SEMANTIC CORRECTNESS
DATA CORRECTNESS       ≠ SECURITY
SECURE PIPELINE        ≠ VALID DATA
VALID DATA             ≠ SECURE PIPELINE
```

A tamper-proof pipeline can still ingest semantically wrong data. Semantically perfect data can arrive via insecure channel (must be quarantined until security review).

Coordinate: quarantine for integrity failure (§38) may be triggered by either security or data-intelligence findings.

---

## 33. Epistemic Boundary (Agent 05)

| Question | Owner |
| --- | --- |
| Data characteristics, provenance, quality, lineage, conflict, reliability | **Agent 07** |
| Epistemic status, evidence interpretation, claim/hypothesis, contradiction, promotion | **Agent 05** |

### 33.1 Forbidden conversions

```text
quality-pass        → evidence          FORBIDDEN (automatic)
high reliability    → truth             FORBIDDEN
data agreement      → knowledge         FORBIDDEN
fresh data          → verified claim    FORBIDDEN
```

### 33.2 Handoff artifact `[PROPOSED]`

```text
DataIntelligenceAssessment
  artifact_id
  readiness_level              # §36
  fit_for_purpose[]            # purpose tags + verdict
  quality_vector               # §11 dimensions
  gaps[], anomalies[], conflicts[]
  provider_independence_summary
  temporal_integrity_attestation
  semantic_integrity_attestation
  limitations
  → input to Evidence packaging / Agent 05 eligibility review
```

Agent-07 proposes assessments; Agent-05 owns Evidence registration and epistemic lifecycle.

---

## 34. Research Methodology Boundary (Agent 06)

| Question | Owner |
| --- | --- |
| Whether data meets methodological requirements of a study | **Joint: Agent 06 defines requirements; Agent 07 assesses supply** |
| Research design, sampling, leakage, reproducibility | **Agent 06** |

Neither silently assumes authority over the other. Methodologically required freshness/completeness that the dataset cannot meet → study blocked at data gate, not patched by methodology waiver.

See §49 for research data requirements template.

---

## 35. Fitness for Purpose

### 35.1 FIT_FOR_PURPOSE `[PROPOSED]`

Formal evaluation: given artifact A and intended use U, is A suitable for U?

| Verdict | Meaning |
| --- | --- |
| **FIT** | Quality vector meets U's minimum dimensions |
| **FIT_WITH_LIMITATIONS** | Usable with documented scope restrictions |
| **NOT_FIT** | One or more blocking dimension failures |
| **UNKNOWN** | Insufficient assessment |

### 35.2 Contextual examples

| Dataset | Exploratory research | Confirmatory research | Live decision |
| --- | --- | --- | --- |
| 70% complete chain history | FIT_WITH_LIMITATIONS | NOT_FIT (unless question scoped) | NOT_FIT |
| Stale DEX snapshot | FIT (historical) | FIT if window matches | NOT_FIT |
| Single-provider social feed | FIT_WITH_LIMITATIONS | NOT_FIT without independence | NOT_FIT |
| Reconciled multi-provider OHLCV (audited) | FIT | FIT_WITH_LIMITATIONS | FIT_WITH_LIMITATIONS |

**Rule:** DATA QUALITY IS CONTEXTUAL. A single global quality score is insufficient.

---

## 36. Data Readiness

### 36.1 Readiness levels `[PROPOSED]`

| Level | Meaning | Required controls | ≠ Truth |
| --- | --- | --- | --- |
| **RAW** | Captured bytes, minimal validation | Hash, acquisition provenance | Yes |
| **STRUCTURED** | Parsed to schema | Schema validation | Yes |
| **VALIDATED** | Semantic + quality dimensions assessed | DataQualityAssessment | Yes |
| **RECONCILED** | Multi-source conflicts addressed or flagged | Reconciliation record | Yes |
| **RESEARCH_READY** | Meets Agent-06 data requirements for stated study | Methodology data checklist | Yes |
| **DECISION_READY** | Meets decision-specific fitness gate | Governance-approved criteria | Yes |
| **PRODUCTION_READY** | Operational SLAs, monitoring, incident playbooks | Agent 04 authorization | **Yes** |

**Rule:** PRODUCTION_READY ≠ TRUE. Readiness is use-case dependent.

### 36.2 Readiness monotonicity

Readiness is **not** automatically monotonic across purposes. A dataset DECISION_READY for trend monitoring may be NOT_FIT for execution pricing.

---

## 37. Data Incident Model

### 37.1 Incident categories

| Category | Examples |
| --- | --- |
| Corruption | Bit rot, truncated file |
| Provider outage | API down |
| Schema break | Unexpected structure |
| Semantic break | Unit change undetected |
| Stale data | Feed stopped updating |
| Identity mismatch | Token collision |
| Missing data | Gap undetected until use |
| Duplication | Inflated metrics |
| Conflicting providers | Unreconciled divergence |
| Manipulation | Suspected wash trading |
| Provenance loss | Missing lineage |
| Transformation failure | Bad derive job |

### 37.2 Incident lifecycle `[PROPOSED]`

```text
DETECT → CONTAIN → ASSESS IMPACT → NOTIFY → QUARANTINE (if needed)
  → RECOVER → REPROCESS → AUDIT → CLOSE
```

| Phase | Actions |
| --- | --- |
| Detection | Observability alerts, anomaly rules, consumer reports |
| Containment | Stop downstream propagation; mark artifacts |
| Impact | List affected features, research, decisions |
| Notification | Agent 04 governance path; human for high tier |
| Quarantine | Isolate suspect artifacts (§38) |
| Recovery | Restore from raw; alternate provider |
| Reprocessing | Replay transforms with fixed logic |
| Audit | Post-incident review; update reliability profile |

---

## 38. Data Quarantine

### 38.1 Quarantine conditions

Mark **QUARANTINED** when:

- Unknown provenance
- Integrity failure (hash mismatch)
- Severe schema mismatch
- Identity mismatch unresolved
- Suspicious manipulation pattern
- Temporal impossibility
- Unexplained severe provider conflict
- Security flag from Agent 03

### 38.2 Quarantine semantics

- Quarantine ≠ deletion
- Preserve original artifact when legally and technically appropriate
- Downstream consumers must fail closed or explicit bypass with governance approval
- Quarantine release requires documented review (Agent 04 governance)

`[IMPLEMENTED]` Mission lifecycle includes `QUARANTINED` terminal state for agents; `[PROPOSED]` data artifact quarantine enum.

---

## 39. Data Retention

### 39.1 Retention classes

| Class | Rationale |
| --- | --- |
| Raw data | Reproducibility, dispute resolution |
| Normalized / derived | Replay without re-fetch |
| Transformations specs | Audit |
| Failed ingestion | Debug, pattern detection |
| Anomalies / conflicts | Investigation |
| Corrections / supersession | Historical interpretability |
| Research datasets | Reproducibility level dependent (Agent 06) |

### 39.2 Principles

- Preserve enough history to reproduce consequential decisions where feasible
- Indefinite retention is **not** always appropriate (cost, legal, PII)
- Retention policy is governance-owned (Agent 04); Agent-07 specifies architectural requirements

---

## 40. Data Versioning

Version these independently:

| Object | Version type |
| --- | --- |
| Raw datasets | Content hash + capture version |
| Schemas | schema_version semver |
| Transformations | transform_id + version |
| Feature definitions | definition_hash |
| Provider snapshots | snapshot_id + provider state |
| Reconciliation rules | rule_set_version |

Historical research must remain interpretable after future schema changes — pin versions in research artifacts (Agent-06 reproducibility matrix).

`[IMPLEMENTED]` Epistemic artifacts carry `version: int` and supersession links on Evidence.

---

## 41. Quality Propagation

### 41.1 Propagation chain

```text
Provider Problem
      ↓
Raw Data Risk
      ↓
Derived Data Risk
      ↓
Feature Risk
      ↓
Evidence Risk              (if unsuitable data packaged)
      ↓
Research Risk
      ↓
Decision Risk
```

### 41.2 Rules

1. Downstream layers **inherit** upstream uncertainty flags
2. Downstream validation **cannot erase** upstream gaps or conflicts without explicit resolution record
3. Transforms may **amplify** errors (aggregation hides outliers)
4. Quality assessment at each layer should reference upstream assessment ids

---

## 42. Data-to-Decision Lineage

### 42.1 Reverse trace (ideal)

```text
DECISION
   ↓
DECISION INPUT MANIFEST
   ↓
FEATURE / ANALYSIS ARTIFACTS
   ↓
DERIVED DATA
   ↓
TRANSFORMATION RECORDS
   ↓
RAW DATA ARTIFACTS
   ↓
SOURCE / PROVIDER REGISTRATIONS
```

### 42.2 Organizational capability target

The organization should eventually answer:

> "Which exact data artifacts contributed to this consequential decision?"

`[PROPOSED]` DecisionInputManifest with content-addressed refs. `[IMPLEMENTED]` partial: TCB audit chain + artifact lineage tuples for epistemic path only.

Architecture only — no runtime decision system in this repository.

---

## 43. AI/ML Data Quality

### 43.1 Risk catalog

| Risk | Mitigation direction |
| --- | --- |
| Garbage-in | Upstream quality gates |
| Distribution shift | Drift monitoring (§47) |
| Training-serving skew | Feature definition parity |
| Leakage | Temporal cutoffs (Agent 06) |
| Label contamination | Label provenance |
| Dataset bias | Population documentation |
| Benchmark contamination | Holdout isolation |
| Stale features | Freshness in serving path |
| Hidden proxy variables | Feature semantic audit |
| Provider changes | Version detection, retrain triggers |

**Rule:** A powerful model does not compensate for bad data. Model capacity ≠ data validity.

---

## 44. Scoring Relationship

Data quality interacts with future scoring systems as:

| Role | Description |
| --- | --- |
| **Gating condition** | Block score if NOT_FIT |
| **Scope limitation** | Score valid only for subset |
| **Confidence modifier** | Widen uncertainty bands |
| **Missingness state** | Explicit UNKNOWN component |
| **MONITOR_ONLY flag** | Score displayed but not actionable |

### 44.1 Forbidden pattern

```text
LOW-QUALITY DATA → HIGH SCORE → HIGH CONFIDENCE   FORBIDDEN
```

Do not prescribe a single formula without evidence. `[PROPOSED]` scoring interface must accept quality vector + readiness level as inputs.

---

## 45. Decision Relationship

```text
DATA QUALITY        ≠ DECISION CONFIDENCE
DECISION RELEVANCE  ≠ DATA QUALITY
```

High decision confidence may arise from multiple independent high-quality sources agreeing **on a relevant proposition** after epistemic review.

A technically high-quality dataset irrelevant to the decision must not increase confidence.

Decision systems should consume:

1. DataIntelligenceAssessment (Agent 07 domain)
2. MethodologyAssessment (Agent 06 domain)
3. Epistemic status (Agent 05 domain)
4. Governance authorization (Agent 04 domain)

---

## 46. Data Observability

### 46.1 Observability dimensions

| Signal | Detects |
| --- | --- |
| Freshness lag | Stale feed |
| Completeness ratio | Gaps (with location) |
| Ingestion latency | Pipeline delay |
| Schema conformance rate | Structural breaks |
| Error rate | Parse/validation failures |
| Anomaly rate | Pattern breaks |
| Provider divergence | Conflicts |
| Coverage breadth | Missing entities/chains |
| Drift metrics | Distribution/schema shift |

### 46.2 System health ≠ data correctness

```text
PIPELINE GREEN + SEMANTICALLY WRONG DATA   = possible
PIPELINE RED + previously valid cache        = stale may still serve (danger)
```

Monitor **data correctness signals** separately from **job success metrics**.

---

## 47. Data Drift

| Drift type | Description |
| --- | --- |
| Schema drift | Fields appear/disappear |
| Distribution drift | Statistical property shift |
| Concept drift | Y|X relationship changes |
| Provider behavior drift | Latency, restatement pattern change |
| Source composition drift | Provider mix changed |
| Market regime drift | Structural market change |

Historical quality does not guarantee future quality. Drift triggers re-assessment, not automatic trust continuation.

---

## 48. Governance Boundary (Agent 04)

| Decision | Owner |
| --- | --- |
| Who may define data policies | **Agent 04** / human governance |
| Who may approve provider admission | **Agent 04** / human governance |
| Who may change data contracts | **Agent 04** with impact review |
| Who may override quarantine | **Agent 04** / human governance |
| Who may authorize production use | **Agent 04** / human governance |

Agent-07 **proposes requirements** only. Does not grant itself governance authority.

Slice 1 `[IMPLEMENTED]` provides policy deny tokens as floor, not complete data governance.

---

## 49. Research Data Requirements

Research plans (Agent 06) should specify data requirements that Agent-07 assesses:

| Requirement | Example specification |
| --- | --- |
| Minimum freshness | "Block-level data ≤ 2 blocks behind head" |
| Minimum completeness | "≥99% blocks in window; gaps documented" |
| Required provenance | "Raw artifact hash + provider id" |
| Provider independence | "≥2 uncorrelated clusters for price" |
| Acceptable missingness | "Gaps <1h acceptable if not in primary outcome window" |
| Temporal resolution | "1-minute bars" |
| Allowed transformations | "Normalize only; no imputation" |
| Identity rules | "Token by (chain_id, address)" |
| Reconciliation policy | "Conflicts >1% → UNRESOLVED, study pauses" |
| Readiness target | "RESEARCH_READY minimum" |

`[IMPLEMENTED]` `ResearchMission.required_evidence` partially captures evidence needs; `[PROPOSED]` structured `data_requirements` block.

---

## 50. Evidence Data Requirements

Before DataArtifact → Evidence conversion (Agent 05):

| Gate | Requirement |
| --- | --- |
| Provenance complete | Source registered, lineage intact |
| Quality assessed | DataQualityAssessment exists for purpose |
| Freshness adequate | For claim time horizon |
| Semantic validation | Passed or limitations documented |
| Conflicts | Resolved or explicitly carried forward |
| Independence | Documented if multi-source |
| Extraction method | Explicit on Evidence |
| Not quarantined | Unless governance exception |

**Rule:** `valid data → evidence` is **not automatic**. Validity is necessary, not sufficient.

`[IMPLEMENTED]` Evidence requires `source_id`, timestamps, `extraction_method`, content hash. `[IMPLEMENTED]` `is_eligible_positive_support()` checks freshness + verification — epistemic gate, not full data QA.

---

## 51. Data Red Team

Adversarial questions the organization must survive:

| # | Question |
| --- | --- |
| 1 | Can stale data pass as live? |
| 2 | Can zero be confused with missing? |
| 3 | Can two providers be falsely treated as independent? |
| 4 | Can duplicate events inflate volume? |
| 5 | Can a token identity collision contaminate analysis? |
| 6 | Can timestamps be shifted to simulate causality? |
| 7 | Can future data leak into historical research? |
| 8 | Can schema-valid but semantically invalid records pass? |
| 9 | Can a provider restatement silently rewrite history? |
| 10 | Can anomalies be deleted instead of investigated? |
| 11 | Can data quality scores hide catastrophic failures in subpopulations? |
| 12 | Can corrupted upstream data produce apparently valid downstream features? |
| 13 | Can quarantine be bypassed via derived artifact without lineage? |
| 14 | Can a green pipeline mask semantic unit error? |
| 15 | Can correlated social reposts simulate independent confirmation? |

Planned executor: `agent.org.19-independent-red-team` (`[PLANNED]`). Agent-07 defines the question set; red team executes adversarial probes.

---

## 52. Failure Taxonomy

### 52.1 Source failures

| Code | Description |
| --- | --- |
| `SRC_OUTAGE` | Provider unavailable |
| `SRC_MANIPULATION` | Suspected intentional distortion |
| `SRC_PROVENANCE_FAILURE` | Incomplete origin metadata |
| `SRC_UPSTREAM_CORRUPTION` | Bad data from upstream of provider |

### 52.2 Transport failures

| Code | Description |
| --- | --- |
| `TRN_TRUNCATION` | Partial payload |
| `TRN_DUPLICATION` | Retry duplicates |
| `TRN_DELAY` | Late arrival |
| `TRN_RETRY_ARTIFACT` | Transport-level duplicate records |

### 52.3 Structural failures

| Code | Description |
| --- | --- |
| `STR_SCHEMA_MISMATCH` | Contract violation |
| `STR_TYPE_MISMATCH` | Wrong type |
| `STR_MALFORMED` | Unparseable |

### 52.4 Semantic failures

| Code | Description |
| --- | --- |
| `SEM_WRONG_UNIT` | Unit error |
| `SEM_WRONG_IDENTITY` | Token/entity mismatch |
| `SEM_WRONG_CHAIN` | Chain mislabel |
| `SEM_WRONG_TIMESTAMP` | Time semantics error |
| `SEM_WRONG_INTERPRETATION` | Decoder error |

### 52.5 Temporal failures

| Code | Description |
| --- | --- |
| `TMP_STALE` | Outside freshness |
| `TMP_FUTURE_LEAKAGE` | Future info in past context |
| `TMP_CLOCK_SKEW` | Inconsistent clocks |
| `TMP_OUT_OF_ORDER` | Sequence violation |

### 52.6 Analytical failures

| Code | Description |
| --- | --- |
| `ANL_LEAKAGE` | Feature leakage |
| `ANL_AGGREGATION_ERROR` | Wrong rollups |
| `ANL_TRANSFORM_ERROR` | Bad derived logic |
| `ANL_FEATURE_CONTAMINATION` | Train/test bleed |

### 52.7 Governance failures

| Code | Description |
| --- | --- |
| `GOV_UNAUTHORIZED_SOURCE` | Unapproved provider |
| `GOV_UNAPPROVED_PROVIDER` | Admission violation |
| `GOV_UNDOCUMENTED_TRANSFORM` | Missing lineage |

Aligns with Agent-06 failure taxonomy where overlapping (e.g., `TEMPORAL_MISMATCH`, `PROVIDER_DISAGREEMENT`).

---

## 53. Data Intelligence Principles

Evaluated constitution (minimum 20):

| # | Principle | Evaluation |
| --- | --- | --- |
| 1 | Never confuse data with truth | **Required** — core distinction |
| 2 | Never erase provenance | **Required** — `[IMPLEMENTED]` on TCB artifacts |
| 3 | Never hide missingness | **Required** — use DataGap |
| 4 | Never silently convert missing into zero | **Required** — three-valued logic |
| 5 | Never treat stale data as live | **Required** — `[IMPLEMENTED]` Evidence STALE |
| 6 | Never assume provider independence | **Required** — dependency graph |
| 7 | Never silently overwrite historical data | **Required** — supersession only |
| 8 | Never erase anomalies merely because inconvenient | **Required** — flag and preserve |
| 9 | Never hide provider disagreement | **Required** — DataConflict |
| 10 | Never treat schema validity as semantic correctness | **Required** — layered validation |
| 11 | Never allow future information into historical evaluation | **Required** — Agent 06 alignment |
| 12 | Preserve lineage for consequential data | **Required** — `[IMPLEMENTED]` partial |
| 13 | Make data fitness-for-purpose explicit | **Required** — FIT_FOR_PURPOSE |
| 14 | Preserve uncertainty | **Required** — quality vectors, not false precision |
| 15 | Preserve data conflicts | **Required** — UNRESOLVED is valid state |
| 16 | Preserve original artifacts where appropriate | **Required** — raw immutability |
| 17 | Do not allow data quality to silently become decision confidence | **Required** — separate channels |
| 18 | Data readiness must be contextual | **Required** — purpose-bound levels |
| 19 | Downstream systems must inherit upstream uncertainty | **Required** — propagation rules |
| 20 | Data correction must remain auditable | **Required** — supersession + incident record |

**Additions proposed:**

| # | Principle | Rationale |
| --- | --- | --- |
| 21 | Never collapse quality dimensions into one score without published justification | Prevents laundering |
| 22 | Never deduplicate without domain identity keys | Prevents event loss |
| 23 | Never conflate observed on-chain with interpreted metrics | Crypto-specific |
| 24 | Quarantine is not deletion | Investigation integrity |

---

## 54. Implemented / Documented / Proposed

| Control | Classification | Evidence |
| --- | --- | --- |
| `Source` registration with hash | `[IMPLEMENTED]` | `agent_org/epistemic.py` |
| `Evidence` with dual timestamps | `[IMPLEMENTED]` | `agent_org/epistemic.py` |
| Freshness policy on Evidence | `[IMPLEMENTED]` | `freshness_max_age_seconds`, `expires_at` |
| Evidence STALE lifecycle | `[IMPLEMENTED]` | `EvidenceState.STALE` |
| Scalar assurance 0–100 | `[IMPLEMENTED]` | `Evidence.assurance` — collapse risk |
| Universal Provenance on artifacts | `[IMPLEMENTED]` | `agent_org/contracts.py` |
| Lineage tuples on artifacts | `[IMPLEMENTED]` | All epistemic dataclasses |
| TCB provenance enforcement | `[IMPLEMENTED]` | `agent_org/tcb.py` |
| Content hash on Source/Evidence | `[IMPLEMENTED]` | Construction validation |
| Evidence supersession | `[IMPLEMENTED]` | `supersedes_evidence_id` |
| `provider.connect` deny | `[IMPLEMENTED]` | `ahos_org/policy.py` |
| `agent.provider-data` logical role | `[IMPLEMENTED]` | `ahos_org/registry.py` |
| Audit hash chain | `[IMPLEMENTED]` | `agent_org/audit.py` |
| L0–L6 hierarchy | `[DOCUMENTED]` | Constitution |
| DATA ≠ EVIDENCE vocabulary | `[DOCUMENTED]` | Constitution, Agent 05 |
| Evidence Protocol reporting | `[DOCUMENTED]` | `AGENT_EVIDENCE_PROTOCOL.md` |
| Agent 05 epistemic boundaries | `[DOCUMENTED]` | `AGENT_05_EPISTEMIC_REASONING_ARCHITECTURE.md` |
| Agent 06 methodology data gates | `[DOCUMENTED]` | `AGENT_06_RESEARCH_METHODOLOGY_ARCHITECTURE.md` |
| Agent 03 security boundaries | `[DOCUMENTED]` | `AGENT_ORGANIZATION_SECURITY_ARCHITECTURE.md` |
| `agent.org.07-data-intelligence` blueprint | `[PLANNED]` | `PLANNED_19_AGENT_MAP.md` |
| DataArtifact / DataQualityAssessment | `[PROPOSED]` | This document |
| Provider registry + dependency graph | `[PROPOSED]` | — |
| DataContract / SchemaVersion | `[PROPOSED]` | — |
| DataGap / DataAnomaly / DataConflict types | `[PROPOSED]` | — |
| DataIntelligenceAssessment handoff | `[PROPOSED]` | — |
| Readiness levels (RAW → PRODUCTION_READY) | `[PROPOSED]` | — |
| FIT_FOR_PURPOSE evaluation | `[PROPOSED]` | — |
| Data observability layer | `[PROPOSED]` | — |
| Reconciliation engine | `[PROPOSED]` | — |
| Quarantine on data artifacts | `[PROPOSED]` | — |
| Quality vector replacing assurance | `[PROPOSED]` | Agent 05 HD-04 related |
| Plane A `agent.provider-data` vs Plane D Agent-07 mapping | `[UNKNOWN]` | Dual-19 unresolved |
| AHOS data pipeline controls | `[UNKNOWN]` | Not audited in this mission (read-only boundary cited from separation policy only) |

Never claim documented rules are enforced unless code or tests demonstrate it.

---

## 55. Required Matrices

### A. Data Quality Matrix

| Dimension | Meaning | Detection | Consequence if failed |
| --- | --- | --- | --- |
| Completeness | Required scope present | Gap detection vs contract | NOT_FIT; DataGap recorded |
| Correctness | Matches verifiable truth | Audit sample, cross-source | Quarantine or conflict |
| Consistency | Internal coherence | Rule checks, joins | Block reconcile |
| Validity | Schema/range pass | Contract validator | Reject at ingest |
| Uniqueness | No illegal duplicates | Identity key dedup | Inflate metrics if missed |
| Timeliness | Arrived on schedule | Latency monitor | Stale downstream |
| Freshness | Current for use | Age vs threshold | STALE; block live use |
| Integrity | Hash unchanged | Hash verify | QUARANTINE |
| Precision | Resolution adequate | Unit/resolution check | Wrong granularity use |
| Accuracy | Close to true value | Ground truth sample | Confidence modifier |
| Coverage | Span of entities/time | Coverage report | Scope limitation |
| Availability | Accessible | Health check | Gap if outage |
| Continuity | No time holes | Time series scan | DataGap |
| Stability | Stable schema/dist | Drift monitor | Re-assess readiness |
| Provenance | Traceable origin | Provenance audit | QUARANTINE if missing |
| Semantic validity | Correct meaning | Semantic validator | Silent error if missed |

### B. Data Readiness Matrix

| Level | Meaning | Required Controls | Allowed Use |
| --- | --- | --- | --- |
| RAW | Captured bytes | Hash, acquisition time, source ref | Archival, re-parse |
| STRUCTURED | Parsed records | Schema validation | Internal exploration |
| VALIDATED | Quality assessed | DataQualityAssessment | Constrained analysis |
| RECONCILED | Conflicts handled | Reconciliation record | Multi-source research |
| RESEARCH_READY | Meets study data spec | Agent-06 checklist pass | Registered research |
| DECISION_READY | Meets decision spec | Fitness gate + governance | Decision input (not auto execute) |
| PRODUCTION_READY | Ops-grade | Monitoring, incidents, approval | Production pipelines (future) |

### C. Provider Independence Matrix (illustrative patterns)

| Provider A | Provider B | Shared Dependency | Independent? | Evidence |
| --- | --- | --- | --- | --- |
| Exchange API A | Exchange API B | Different exchanges | **Partial** | Same market structure risks |
| Indexer X | Indexer Y | Same RPC node | **No** | Shared node state |
| Aggregator M | Aggregator N | Same upstream CEX | **No** | Same tape |
| On-chain node direct | Indexer via node | Same chain data | **Partial** | Interpretation may differ |
| News wire | Social scrape | Same press release | **No** | Repost |
| Agent A prompt | Agent B prompt | Same LLM + source | **No** | Agent 05/06 rule |
| Provider P (approved) | Provider Q (approved) | Documented distinct upstream | **Yes** | With cluster evidence |

### D. Data Incident Matrix

| Incident | Detection | Containment | Impact | Recovery |
| --- | --- | --- | --- | --- |
| Corruption | Hash failure | QUARANTINE artifact | Downstream invalid | Re-fetch raw |
| Provider outage | Health alert | Failover or gap record | Missing window | Backfill |
| Schema break | Validator error | Stop ingest | Pipeline halt | Contract migration |
| Semantic break | Semantic rules | QUARANTINE batch | Wrong analytics | Fix transform, reprocess |
| Stale feed | Freshness alert | Mark STALE | Live decisions blocked | Restore feed |
| Identity mismatch | Registry lookup fail | QUARANTINE | Join corruption | Manual resolution |
| Missing data | Gap detector | DataGap artifact | Sample bias | Backfill or scope change |
| Duplication | Dedup burst | Inflate flags | Volume error | Dedup reprocess |
| Provider conflict | Divergence metric | DataConflict | Unknown ground truth | Reconcile or UNRESOLVED |
| Manipulation | Anomaly detector | Flag + preserve | False signals | Human review |
| Provenance loss | Audit fail | QUARANTINE | Non-auditable | Re-acquire |
| Transform failure | Job error | Stop derive | Stale features | Fix + replay |

### E. Data-to-Decision Matrix

| Data Layer | Validation | Uncertainty Inherited | Downstream Effect |
| --- | --- | --- | --- |
| Raw | Hash, capture provenance | Provider reliability | All upstream |
| Normalized | Schema + semantic | Raw gaps/conflicts | Derived, features |
| Derived | Transform validation | Normalized | Features, analysis |
| Feature | Leakage + freshness | Derived | Model, scores |
| Analysis output | Method check (Agent 06) | Feature + data | Evidence eligibility |
| Evidence | Epistemic gate (Agent 05) | All data layers | Claims, decisions |
| Decision input | Governance + fitness | Full stack | Execution (future) |

### F. Data Object Matrix

| Object | Meaning | Provenance | Versioning | Validation |
| --- | --- | --- | --- | --- |
| Provider | Data supplier identity | Registration record | Admission history | Governance approve |
| DataSource | Abstract origin class | N/A (type) | Type version | Documented |
| Source (2B) | Registered origin instance | `[IMPLEMENTED]` required | `[IMPLEMENTED]` version | Locator + hash |
| DataArtifact | Stored data unit | Full chain | Content hash + version | Schema + semantic |
| Dataset | Collection w/ contract | Aggregate refs | Dataset version | Contract + QA |
| DataRecord | Single record | Parent artifact | Record key | Field validators |
| Transformation | Transform spec | Inputs + operator | Transform version | Replay test |
| DataQualityAssessment | QA result | Assessor + method | Assessment id | Multi-dim rules |
| DataGap | Missing coverage | Detection method | Gap id | N/A (fact) |
| DataAnomaly | Detected deviation | Detector + params | Anomaly id | Review |
| DataConflict | Source disagreement | All sides preserved | Conflict id | Reconciliation |
| Feature | ML/analysis input | Lineage to raw | Definition hash | Leakage + semantic |
| Evidence (2B) | Epistemic warrant | `[IMPLEMENTED]` | `[IMPLEMENTED]` | Epistemic + freshness |
| DataContract | Schema agreement | Authors + approvers | schema_version | Compatibility tests |

---

## 56. Open Questions

1. Should `DataQualityAssessment` be a TCB artifact type or a sidecar store linked to epistemic objects?
2. Should scalar `assurance` on Evidence be deprecated in favor of quality vector references (coordination with Agent 05 HD-04)?
3. What is the mapping between Plane A `agent.provider-data` and Plane D `agent.org.07-data-intelligence` under Dual-19?
4. Should DataConflict automatically spawn epistemic ContradictionCase, or remain data-layer only until claim formation?
5. What minimum provider admission evidence is required before governance approval (Agent 04)?
6. Should readiness levels be enums on DataArtifact or computed views from assessments?
7. How should AHOS data pipelines (future integration) mirror org data contracts without coupling runtimes?
8. What is the default reconciliation strategy for crypto price disagreement (no universal hierarchy without HD-09)?
9. Should quarantine state be propagated automatically to all derived artifacts in lineage graph?
10. How should off-chain mutable sources (social, web) snapshot immutability be guaranteed?
11. What correlation cluster evidence is sufficient to claim provider independence?
12. Should Feature definitions live in TCB, git, or a dedicated feature registry?
13. How do data incidents escalate to governance vs epistemic contradiction workflows?
14. What AHOS on-chain decoders become authoritative when integration is approved?
15. Should NULL, MISSING, and ZERO be typed sentinels in DataContract or application logic only?

---

## 57. Human Decisions Required

| ID | Decision | Status |
| --- | --- | --- |
| **HD-01** | Dual-19 resolution: Plane A `agent.provider-data` vs Plane D Agent-07 ownership | `HUMAN_DECISION_REQUIRED` |
| **HD-02** | Adopt data readiness levels (§36) as organizational vocabulary | `HUMAN_DECISION_REQUIRED` |
| **HD-03** | Adopt FIT_FOR_PURPOSE evaluation model (§35) | `HUMAN_DECISION_REQUIRED` |
| **HD-04** | Quality representation: retain Evidence assurance scalar vs quality vector vs both | `HUMAN_DECISION_REQUIRED` |
| **HD-05** | Provider admission process and minimum evidence for approval | `HUMAN_DECISION_REQUIRED` |
| **HD-06** | Default crypto provider reconciliation strategy when providers disagree | `HUMAN_DECISION_REQUIRED` |
| **HD-07** | Quarantine override authority and audit requirements | `HUMAN_DECISION_REQUIRED` |
| **HD-08** | Data retention policy tiers (raw vs derived vs features) | `HUMAN_DECISION_REQUIRED` |
| **HD-09** | DataIntelligenceAssessment → Evidence packaging handoff schema (with Agent 05) | `HUMAN_DECISION_REQUIRED` |
| **HD-10** | Research data requirements template adoption (with Agent 06) | `HUMAN_DECISION_REQUIRED` |
| **HD-11** | When AHOS integration is allowed: read-only mirror vs mediated contract boundary | `HUMAN_DECISION_REQUIRED` |
| **HD-12** | Adoption of this architecture doc as L2 governance text | `HUMAN_DECISION_REQUIRED` |

---

## 58. Recommended Future Work — STATE ONLY

`RECOMMENDED_NEXT_MISSION = STATE_ONLY — DO NOT EXECUTE`

The following are **recommendations only**. They are not activated missions.

1. **FUTURE_IMPLEMENTATION_REQUIRED:** `DataQualityAssessment` artifact (or sidecar) with multi-dimensional vector.
2. **FUTURE_IMPLEMENTATION_REQUIRED:** Provider registry with dependency/correlation graph.
3. **FUTURE_IMPLEMENTATION_REQUIRED:** DataContract and SchemaVersion types with compatibility tests.
4. **FUTURE_IMPLEMENTATION_REQUIRED:** DataGap, DataAnomaly, DataConflict artifact types.
5. **FUTURE_IMPLEMENTATION_REQUIRED:** DataIntelligenceAssessment handoff schema for Agent 05 Evidence eligibility.
6. **FUTURE_IMPLEMENTATION_REQUIRED:** Research `data_requirements` block coordinated with Agent 06 template.
7. **FUTURE_IMPLEMENTATION_REQUIRED:** Readiness level computation from assessments (purpose-bound).
8. **FUTURE_IMPLEMENTATION_REQUIRED:** Data artifact quarantine state with downstream propagation rules.
9. **FUTURE_IMPLEMENTATION_REQUIRED:** Semantic validation layer above JSON schema for crypto identity tuples.
10. **Recommended documentary agent:** Agent 08 — Crypto Market Intelligence (domain-specific data contracts; coordinate with Agent 07).
11. **Recommended documentary agent:** Agent 09 — On-Chain Intelligence (decoder/finality semantics; coordinate with Agent 07).
12. **Recommended coordination mission:** Agent 05 + Agent 07 joint boundary test cases (quality-pass blocked epistemically, and converse).
13. **Recommended coordination mission:** Agent 06 + Agent 07 research data requirements template alignment.
14. **Recommended verification mission:** Red-team data integrity probes (Agent 19) using §51 question set.

**AGENT-07 does not execute any of the above.**

---

## Document provenance

| Field | Value |
| --- | --- |
| Author | AGENT-07 (Data Intelligence Architect) |
| Task | TASK-20260914-007 |
| Commander | MASTER ORCHESTRATOR |
| Repository | `G:\robat\ahos-agent-org` |
| Code changes | NONE |
| Runtime changes | NONE |
| AHOS impact | NONE |
| Classification | `[PROPOSED]` architecture unless cited `[IMPLEMENTED]` / `[DOCUMENTED]` |

---

*End of AGENT_07_DATA_INTELLIGENCE_ARCHITECTURE.md*
