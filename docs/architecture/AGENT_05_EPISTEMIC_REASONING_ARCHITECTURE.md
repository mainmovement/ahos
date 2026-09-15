# Agent Organization Epistemic Reasoning Architecture

```text
DOCUMENT_ID      = AGENT_05_EPISTEMIC_REASONING_ARCHITECTURE
MISSION_ID       = TASK-20260914-005
VERSION          = 0.1.0
STATUS           = PROPOSED / READ_ONLY_EPISTEMIC_ARCHITECTURE
AUTHORITY        = NONE CREATED
RUNTIME_EFFECT   = NONE
AHOS_EFFECT      = NONE
AGENT_ID         = AGENT-05 (agent.org.05-epistemic-reasoning — documentary)
DIRECT_COMMANDER = MASTER ORCHESTRATOR
PARENT           = MASTER ORCHESTRATOR
```

This document is a **design and architecture artifact** produced by AGENT-05 under explicit activation for TASK-20260914-005. It does not implement epistemic runtime, adopt governance, grant authority, or modify AHOS. Facts cite repository evidence with explicit classification labels (`[IMPLEMENTED]`, `[DOCUMENTED]`, `[PROPOSED]`, `[UNKNOWN]`). Architectural recommendations are labeled `[PROPOSED]`.

---

## 1. Executive Summary

`[VERIFIED]` The AHOS Agent Organization already contains a **substantial epistemic foundation** in Slice 2B (`agent_org/epistemic.py`, `[IMPLEMENTED]` `[TESTED]`): typed artifacts for Source, Evidence, Claim, Hypothesis, Prediction, Observation, KnowledgeCandidate, ContradictionCase, ExperimentPlan/Run, VerificationRecord, Approval, and MemoryRecord; explicit lifecycle state machines; provenance on every artifact; and a TCB-gated knowledge promotion path (D-01/D-04).

`[VERIFIED]` Governance documentation (Constitution, Evidence Protocol, Response Protocol) defines epistemic **vocabulary and reporting discipline** but does **not** enforce multi-agent reasoning in chat (`[DOCUMENTED]` only).

`[VERIFIED]` The planned 19-agent blueprint includes `agent.org.05-epistemic-reasoning` as a specialist role (`[PLANNED]`). This mission activates AGENT-05 as a **documentary design agent**, not as a runtime principal with TCB write access.

**Central architectural question:** How does the organization distinguish reality, observation, evidence, claims, hypotheses, predictions, experiments, results, verification, knowledge candidates, knowledge, uncertainty, contradiction, and ignorance — and prevent silent collapse of these categories?

**Primary epistemic objective:** prevent **epistemic authority collapse** — where inference, documentation, consensus, confidence, or orchestration silently become truth, verification, or execution authority.

**Current epistemic posture:** `[PARTIALLY_VERIFIED]` — strong typed contracts and promotion gates in Slice 2B; weak bridge from Cursor chat agents to TCB artifacts; no durable multi-agent epistemic bus; evidence taxonomy dimensions largely unimplemented as structured metadata.

**Dual-19 status:** `[VERIFIED]` `[CONFLICT / UNRESOLVED]` — Slice 1 Plane A (`agent.*`) and planned Plane D (`agent.org.NN-*`) remain separate taxonomies. This document analyzes epistemic implications only; it does not merge them.

**Agent One:** `NOT_IMPLEMENTED / FUTURE_NON_AUTHORITY_ROOT` — must never become epistemic root of truth.

---

## 2. Agent-05 Identity

| Field | Value |
| --- | --- |
| `AGENT_ID` (mission) | `AGENT-05` |
| Blueprint ID | `agent.org.05-epistemic-reasoning` |
| Provisional name | Epistemic Reasoning Architect |
| Role | Design epistemic architecture; distinguish evidence from claim from knowledge |
| Authority class | `NONE` (design mission only) |
| Capabilities exercised | READ, ANALYZE, PROPOSE (documentation) |
| Forbidden | VERIFY (own conclusions), PROMOTE, EXECUTE, MODIFY runtime, ACTIVATE other agents |
| Supervisor | MASTER ORCHESTRATOR → human operator (MEHRDAD) |
| Source of truth | **Not** AGENT-05. Repository L0/L1 + governance L2/L3 only. |

AGENT-05 is **not** Agent One, **not** the Master Orchestrator, **not** an authority over other agents, **not** a verifier of its own deliverables, and **not** a source of truth.

---

## 3. Command Chain

```text
MEHRDAD
  → MASTER ORCHESTRATOR
    → AGENT-05 (this mission)
```

- Direct commander: **MASTER ORCHESTRATOR**
- Parent: **MASTER ORCHESTRATOR**
- Reporting line: **MASTER ORCHESTRATOR**
- No subordinate agents created or activated by this mission.
- No modification of reporting line.

---

## 4. Lifecycle

### 4.1 Activation rule

Creating, registering, or naming an agent does **not** activate it. TASK-20260914-005 is the explicit activation command for this mission.

### 4.2 Mission lifecycle

```text
REGISTERED / IDLE / DORMANT
  → [explicit activation: TASK-20260914-005]
  → RUNNING (architecture analysis)
  → COMPLETED (this deliverable)
  → IDLE / DORMANT / WAITING_FOR_NEW_COMMAND
```

### 4.3 Terminal states

Supported: `COMPLETED`, `FAILED`, `TIMEOUT`, `CANCELLED`, `BLOCKED`, `SUSPENDED`, `QUARANTINED`.

After termination: `LIFECYCLE_STATUS = IDLE / DORMANT / WAITING_FOR_NEW_COMMAND`.

Recommendations in this document are **not** commands. AGENT-05 does not auto-continue to Agent 06 or any future mission.

---

## 5. Epistemic Foundation

### 5.1 Non-collapse principles (architectural constraints)

These are **forbidden equalities**. Violating them is an epistemic defect, not a stylistic choice:

```text
EVIDENCE        ≠ CLAIM
CLAIM           ≠ TRUTH / FACT
HYPOTHESIS      ≠ FACT
PREDICTION      ≠ OBSERVATION
SIMULATION      ≠ EXECUTION
BACKTEST        ≠ LIVE PROOF
DOCUMENTATION   ≠ EVIDENCE
MODEL OUTPUT    ≠ REALITY
AGENT OPINION   ≠ KNOWLEDGE
CONSENSUS       ≠ TRUTH
RECOMMENDATION  ≠ DECISION
DECISION        ≠ OUTCOME
UNKNOWN         ≠ SAFE
STALE           ≠ LIVE
ABSENCE OF EVIDENCE ≠ EVIDENCE OF ABSENCE
PROVENANCE      ≠ TRUTH
CONFIDENCE      ≠ EPISTEMIC STATUS
MEMORY          ≠ TRUTH
SELF_CHECK      ≠ INDEPENDENT VERIFICATION
```

`[IMPLEMENTED]` Slice 2B module docstring and Constitution §3.2 encode subsets of these. `[DOCUMENTED]` Evidence Protocol and Response Protocol extend to chat reporting.

### 5.2 Source-of-truth hierarchy (L0–L6)

| Level | Meaning | Epistemic use |
| --- | --- | --- |
| **L0** | Actual runtime / repository evidence | Ground truth for "what exists" |
| **L1** | Validated tests / authoritative validation | Ground truth for "what was demonstrated" |
| **L2** | Current governance decisions | Authorization and policy vocabulary |
| **L3** | Current project context / architecture docs | Intent; not proof |
| **L4** | Historical documentation | Context only |
| **L5** | AI / human discussion | Proposals; never execution authority |
| **L6** | Assumption | Must be labeled; never promoted silently |

**Rule:** Never promote L5/L6 to L0/L1 without evidence. A TCB artifact is L1 **only if** its verification/approval state in the store supports that claim.

**Mapping to Slice 2B:** TCB artifacts are **recorded propositions and warrants**, not automatic truth. Their epistemic weight depends on lifecycle state, verification records, freshness, and contradiction linkage — not merely on existence in the store.

### 5.3 Layer separation

```text
COGNITION  ≠  GOVERNANCE  ≠  EXECUTION
EPISTEMIC SYSTEM  →  KNOWLEDGE / EVIDENCE  →  DECISION SYSTEM  →  EXECUTION SYSTEM
```

`[IMPLEMENTED]` Slice 2B TCB denies execution-class operations on protected resources. `[PROPOSED]` Future decision system must consume epistemic objects without inheriting their authority automatically.

---

## 6. Object Model

### 6.1 Core objects

Each object below has a Slice 2B dataclass where noted. Meanings apply organization-wide even when artifacts are report-only (chat agents).

#### Source

**Meaning:** Registered origin from which information is obtained (file, API, human statement, instrument, model output channel).

**Slice 2B:** `Source` with `source_type`, `locator`, `content_hash`, lifecycle (`REGISTERED`, `SUPERSEDED`, `REVOKED`).

#### Observation

**Meaning:** Something directly measured or recorded at an event — distinct from interpretation.

**Slice 2B:** `Observation` bound to `experiment_run_id`, `measured_value`, `observation_method`.

**Note:** Not every observation requires an experiment; chat agents may report observations without TCB registration using Evidence Protocol finding records.

#### Evidence

**Meaning:** A bounded information artifact supporting or challenging a proposition — not the proposition itself.

**Slice 2B:** `Evidence` with dual timestamps (`observation_timestamp`, `retrieval_timestamp`), freshness policy, `assurance` (0–100), `verification_status`, eligibility helper `is_eligible_positive_support()`.

#### Claim

**Meaning:** A proposition asserted about reality, backed by evidence references.

**Slice 2B:** `Claim` requires non-empty `statement` and `evidence_ids`. Lifecycle: `DRAFT` → `SUBMITTED` → `CHALLENGED` / `VERIFIED` / `REJECTED` → `SUPERSEDED`.

**Gap:** Mission model used `PROPOSED` → `SUPPORTED`; Slice 2B uses `SUBMITTED` without `SUPPORTED`. See §12 Claim Governance.

#### Hypothesis

**Meaning:** A testable proposition explicitly not established; must remain distinguishable from fact even under agreement.

**Slice 2B:** Requires `falsification_criteria`. States: `PROPOSED`, `TESTING`, `SUPPORTED`, `REFUTED`, `INCONCLUSIVE`, `SUPERSEDED`.

#### Prediction

**Meaning:** Future-oriented or conditional expectation derived from a hypothesis — not an observation.

**Slice 2B:** Bound to `hypothesis_id`, `expected_observation`, `evaluation_deadline`. States: `PROPOSED`, `CONFIRMED`, `REFUTED`, `EXPIRED`.

#### Experiment

**Meaning:** Controlled attempt to distinguish competing hypotheses.

**Slice 2B:** `ExperimentPlan` (PLANNED) + `ExperimentRun` (outcome, observations). Experiment success ≠ knowledge promotion.

#### Result

**Meaning:** Recorded output of an experiment or process. In Slice 2B, primarily `ExperimentRun.outcome` plus linked `Observation` artifacts.

#### Verification Record

**Meaning:** Structured evaluation of whether a target artifact satisfies defined criteria.

**Slice 2B:** `VerificationRecord` with `verification_kind` ∈ {`INDEPENDENT`, `SELF_CHECK`}, `verifier_principal_id` ≠ `producer_principal_id` for INDEPENDENT.

#### Knowledge Candidate

**Meaning:** Proposition passing defined epistemic requirements but not yet promoted knowledge.

**Slice 2B:** Requires proposition, claims, evidence, verification IDs; tracks `contradiction_ids`.

#### Knowledge

**Meaning:** Governed, verified epistemic state at promotion — represented as `KnowledgeCandidate` in state `PROMOTED` (Slice 2B). There is no separate `Knowledge` dataclass; promotion is a lifecycle state, not a type collapse.

#### Contradiction

**Meaning:** Two or more propositions/artifacts that cannot all be accepted as simultaneously true under stated assumptions/context.

**Slice 2B:** `ContradictionCase` with `left_artifact_id`, `right_artifact_id`, `affects_candidate_ids`, resolution evidence.

#### Uncertainty / Unknown / Novel

**Meaning:** Epistemic **status dimensions**, not artifact types. See §17.

### 6.2 Conceptual flow (not mandatory pipeline)

Primary path:

```text
SOURCE
  ↓
OBSERVATION (optional direct registration)
  ↓
EVIDENCE
  ↓
CLAIM
  ↓
HYPOTHESIS (optional)
  ↓
PREDICTION (optional)
  ↓
EXPERIMENT → RESULT / OBSERVATION
  ↓
VERIFICATION
  ↓
KNOWLEDGE CANDIDATE
  ↓
INDEPENDENT VERIFICATION + APPROVAL + PROMOTE_KNOWLEDGE
  ↓
KNOWLEDGE (PROMOTED candidate)
```

### 6.3 Alternative paths (explicit)

| Path | Description | When valid |
| --- | --- | --- |
| **Direct evidence → claim** | Observation packaged as evidence without hypothesis | Descriptive facts, audits |
| **Evidence → knowledge candidate** | Skips explicit hypothesis when proposition is directly warranted | `[PROPOSED]` policy-defined narrow cases |
| **Hypothesis → experiment → observation** | Bypasses prediction | Exploratory research |
| **Contradiction-first** | Conflict detected before claim completion | Mandatory when sources disagree |
| **Report-only (L5)** | Agent Response Protocol without TCB write | Default for planned 01–19 until granted `epistemic.write` |
| **Negative evidence** | Absence or failed test as warrant | Must not be read as proof of absence |
| **Stale replay** | Historical evidence for historical claims only | Forbidden for live decisions without refresh |

Every path must preserve type boundaries at each hop. Shortcuts may skip **stages**, not **distinctions**.

---

## 7. Evidence Taxonomy

Evidence categories should be modeled as **orthogonal dimensions**, not a single enum. A single artifact may carry multiple tags; collapsing to one label hides critical structure.

### 7.1 Proposed dimension set

| Dimension | Values | Purpose |
| --- | --- | --- |
| **Provenance tier** | PRIMARY, SECONDARY, DERIVED | How close to origin |
| **Support direction** | POSITIVE, NEGATIVE, NEUTRAL | Supports, challenges, or contextual |
| **Directness** | DIRECT, INDIRECT | Measured vs inferred from other evidence |
| **Verification** | UNVERIFIED, SELF_CHECK, INDEPENDENT_PASS, INDEPENDENT_FAIL, INCONCLUSIVE | `[IMPLEMENTED]` partial via `VerificationStatus` on Evidence |
| **Freshness** | CURRENT, STALE, EXPIRED, HISTORICAL | `[IMPLEMENTED]` partial via `EvidenceState`, expiry |
| **Completeness** | COMPLETE, PARTIAL, UNKNOWN_COMPLETENESS | Scope of what was examined |
| **Integrity** | INTACT, CORRUPTED, SUSPECT | Hash/signature/consistency |
| **Independence cluster** | cluster_id + correlation flags | See §21 Correlated Error |
| **Contradiction linkage** | none / contradiction_id | Ties to ContradictionCase |

### 7.2 Category analysis (mission minimum)

| Category | Definition | Orthogonal dimension(s) |
| --- | --- | --- |
| Primary evidence | From original source/instrument | Provenance tier |
| Secondary evidence | Citing or summarizing primary | Provenance tier |
| Derived evidence | Computed/transformed from other evidence | Provenance tier + transformation record |
| Direct evidence | Observes target directly | Directness |
| Indirect evidence | Infers via chain | Directness |
| Positive evidence | Supports a proposition | Support direction |
| Negative evidence | Undermines a proposition | Support direction |
| Absence | No observation where one was expected | Support direction (negative) + **not** proof of absence |
| Stale evidence | Outside freshness policy | Freshness |
| Contradictory evidence | Conflicts with other evidence | Contradiction linkage |
| Incomplete evidence | Partial scope | Completeness |
| Corrupted evidence | Integrity failure | Integrity |
| Unverified evidence | No independent verification | Verification |
| Independently verified | INDEPENDENT PASS on record | Verification |

`[IMPLEMENTED]` Slice 2B: freshness (`EvidenceState.STALE`, `expires_at`, `freshness_max_age_seconds`), verification status on Evidence, supersession/revocation.

`[PROPOSED]` Structured metadata for provenance tier, directness, completeness, integrity, independence cluster — not yet fields on `Evidence`.

### 7.3 Why not a single enum

A piece of evidence can be **primary, direct, positive, stale, and unverified** simultaneously. A scalar enum forces false choices and enables laundering (e.g., labeling derived model output as "primary").

---

## 8. Evidence Quality

### 8.1 Quality dimensions (multi-axis)

Evaluate evidence on **independent dimensions**; do not collapse into one score without publishing the vector:

| Dimension | Question |
| --- | --- |
| Provenance | Where did it originate? Chain intact? |
| Authenticity | Is it genuinely from the claimed source? |
| Integrity | Unchanged since capture? Hash matches? |
| Freshness | Current for the decision context? |
| Completeness | Full scope or sample? |
| Relevance | Bears on the proposition? |
| Specificity | Precise claim or vague gesture? |
| Independence | Uncorrelated with other cited evidence? |
| Reproducibility | Can another agent re-obtain it? |
| Consistency | Aligns with other independent evidence? |
| Context | Domain, assumptions, preconditions stated? |
| Temporal validity | Valid for event-time vs decision-time? |
| Source reliability | Track record, incentives (see §11) |

`[IMPLEMENTED]` Partial: `assurance` int 0–100 on Evidence and MemoryRecord; freshness fields; verification linkage in promotion gate.

### 8.2 Why a single scalar confidence is misleading

1. **Masks failure modes:** High "confidence" with stale or circular evidence hides epistemic risk.
2. **False precision:** Numeric scores imply measurement where only qualitative judgment exists.
3. **Overrides status:** Agents may treat confidence ≥ threshold as VERIFIED without verification record.
4. **Non-composability:** Good provenance + bad freshness cannot be honestly reduced to one number without weights that themselves need governance.
5. **Encourages theatre:** LLM default is to emit confident prose; scalar scores amplify hallucination risk.

**Architecture rule:** `confidence` (if used) is a **reporting annotation** tied to explicit epistemic status and cited evidence IDs — never a substitute for `VerificationRecord` or lifecycle state.

Slice 2B `assurance` is **not** truth; module docstring: "Stored memory, confidence, recency, and audit inclusion never imply truth."

---

## 9. Provenance

### 9.1 Requirements for consequential epistemic objects

Every consequential object should be traceable to:

| Field | Slice 2B |
| --- | --- |
| Source | `Source` artifact or `source_id` on Evidence |
| Acquisition time | `retrieval_timestamp` |
| Observation time | `observation_timestamp` |
| Transformation / derivation | `extraction_method`, `lineage`, `source_refs` in Provenance |
| Agent / principal | `producer_principal_id`, `creator_principal_id` |
| Tool / method | `Provenance.method`, `observation_method` |
| Context | `ResearchMission.constraints`, task scope on command |
| Predecessor objects | `lineage`, `supersedes_*` fields |
| Verification state | `verification_ids`, `verification_status` |

`[IMPLEMENTED]` `Provenance` dataclass: `creator_principal_id`, `session_id`, `command_id`, `method`, `source_refs`.

### 9.2 Provenance ≠ truth

Complete provenance enables **audit and challenge**; it does not establish correctness. A perfectly traced hallucination remains a hallucination.

**Red-team:** Model output with provenance "agent X said so" is **evidence of utterance**, not evidence of world fact.

---

## 10. Temporal Epistemics

### 10.1 Time axes

| Axis | Meaning |
| --- | --- |
| **Event-time** | When the state of the world occurred |
| **Observation-time** | When it was measured |
| **Ingestion-time** | When the org recorded it (`retrieval_timestamp`, `created_at`) |
| **Verification-time** | When verification completed |
| **Decision-time** | When a decision consumes the evidence |

A statement may be **historically correct** and **currently false** for live decision-making.

### 10.2 Temporal classes

| Class | Rule |
| --- | --- |
| **Current** | Within freshness policy for the decision context |
| **Stale** | Outside freshness; may support historical claims only |
| **Historical** | Explicitly archived; cite with time bounds |
| **Future** | Predictions only; never observations |
| **Time-bounded truth** | Knowledge carries `valid_from` / `valid_until` `[PROPOSED]` |

`[IMPLEMENTED]` Evidence expiry and `is_eligible_positive_support(now)`. Promotion gate re-checks freshness at promotion time.

`[PROPOSED]` Explicit decision-time vs event-time fields on claims and knowledge candidates.

### 10.3 Rules

1. Live operational decisions require **current** evidence class or explicit human override with recorded rationale.
2. Stale evidence must not silently support live claims — label `[STALE]` in reports; TCB transitions to `EvidenceState.STALE`.
3. Predictions cannot be re-timestamped after outcomes (`[PROPOSED]` immutability enforcement on prediction content hash).

---

## 11. Source Reliability

Do **not** assume reputable source = always true, or unknown source = always false.

### 11.1 Reliability framework `[PROPOSED]`

Track per source (or source class) a **reliability profile**, not a boolean:

| Factor | Notes |
| --- | --- |
| Historical reliability | Calibration of past claims |
| Context | Domain match (security vs market) |
| Incentives | Manipulation/adversarial risk |
| Independence | Correlation with other sources |
| Corroboration | Independent confirmation count |
| Freshness | Decay of relevance |
| Source type | Instrument, human, model, aggregator |

Reliability informs **prior weight** in analysis; it does **not** bypass verification for promotion.

### 11.2 Source lifecycle

`[IMPLEMENTED]` `SourceState`: `REGISTERED`, `SUPERSEDED`, `REVOKED`. Revoked sources invalidate downstream evidence linkage via governance policy `[PROPOSED]` (not fully automated in Slice 2B).

---

## 12. Claim Governance

### 12.1 Lifecycle comparison

**Mission template:**

```text
PROPOSED → SUPPORTED → CHALLENGED → VERIFIED → REJECTED → SUPERSEDED
```

**Slice 2B implemented:**

```text
DRAFT → SUBMITTED → CHALLENGED → VERIFIED → REJECTED → SUPERSEDED
```

| Issue | Resolution |
| --- | --- |
| Missing `SUPPORTED` | Use `SUBMITTED` + evidence linkage as "supported" structurally; do not treat submission as verification |
| Missing `PROPOSED` | Map to `DRAFT` |
| **Forbidden:** `SUPPORTED → VERIFIED` without verification | `[IMPLEMENTED]` TCB requires independent verification for claim transition to VERIFIED via `__require_independent_verification` |

### 12.2 Rules

1. Every claim requires ≥1 evidence ID at registration.
2. `VERIFIED` requires `VerificationRecord` with `INDEPENDENT` + `PASS`.
3. `CHALLENGED` blocks promotion of dependent knowledge candidates while unresolved.
4. Supersession preserves lineage; do not delete rejected claims.

`[IMPLEMENTED]` Claim state machine in `LEGAL_ARTIFACT_TRANSITIONS`.

---

## 13. Hypothesis Governance

### 13.1 Lifecycle

| Stage | Requirement |
| --- | --- |
| Creation | Explicit statement + falsification criteria |
| Assumptions | Documented separately `[PROPOSED]` structured field |
| Evidence requirements | Defined before `TESTING` |
| Falsification criteria | Mandatory at creation `[IMPLEMENTED]` |
| Experiment design | Linked `ExperimentPlan` |
| Competing hypotheses | Encouraged; `[PROPOSED]` mutual exclusion groups |
| Status | `PROPOSED` → `TESTING` → `SUPPORTED` / `REFUTED` / `INCONCLUSIVE` |
| Rejection | `REFUTED` is terminal except supersession |
| Promotion | Hypothesis `SUPPORTED` ≠ knowledge; requires separate candidate path |

### 13.2 Principle

> A hypothesis must remain distinguishable from a fact even when many agents agree with it.

Agreement elevates **social confidence**, not **epistemic status**. Status changes only via defined transitions and verification artifacts.

---

## 14. Prediction Governance

| Element | Requirement |
| --- | --- |
| Creation | Before outcome known; hash content at creation `[PROPOSED]` |
| Timestamp | `created_at`, `evaluation_deadline` `[IMPLEMENTED]` |
| Horizon | `evaluation_deadline` |
| Target variable | `expected_observation` (string; structured `[PROPOSED]`) |
| Confidence / uncertainty | Separate from prediction state |
| Assumptions | Linked hypothesis + mission constraints |
| Expected outcome | `expected_observation` |
| Actual outcome | Separate observation/evidence artifacts |
| Scoring | `CONFIRMED` / `REFUTED` / `EXPIRED` `[IMPLEMENTED]` |
| Calibration | Aggregate over prediction set `[PROPOSED]` |
| Failure analysis | Required on refutation `[PROPOSED]` |

**Preserved:** prediction ≠ observation; prediction accuracy ≠ truth of underlying explanation (a wrong model can get lucky; a right prediction doesn't prove causality).

---

## 15. Experiment Governance

### 15.1 Experiment model

| Field | Slice 2B |
| --- | --- |
| Research question | Via linked `ResearchMission.question` |
| Hypothesis | `ExperimentPlan.hypothesis_id` |
| Competing hypotheses | `[PROPOSED]` multi-link |
| Variables | `[PROPOSED]` structured |
| Assumptions | `preconditions` |
| Controls | `[PROPOSED]` |
| Expected result | `expected_observations` |
| Actual result | `ExperimentRun.outcome`, `observation_ids` |
| Stopping criteria | `[PROPOSED]` on mission |
| Failure criteria | `failure_class` on run |
| Reproducibility | `reproducibility_requirements` |
| Interpretation | Separate claim artifacts — not embedded in run |

### 15.2 Experiment result ≠ knowledge promotion

Successful experiment creates **results and observations** warranting claims and candidates. Promotion still requires verification, approval, and `PROMOTE_KNOWLEDGE` through TCB.

`[IMPLEMENTED]` Experiment state machine; no auto-promotion link.

---

## 16. Contradiction Intelligence

Major organizational requirement: **do not hide contradictions to achieve consensus**.

### 16.1 Contradiction types

| Type | Example |
| --- | --- |
| Conflicting evidence | Two measurements disagree |
| Conflicting claims | Mutually exclusive statements |
| Conflicting predictions | Same horizon, incompatible forecasts |
| Conflicting agent conclusions | Different interpretations |
| Temporal contradictions | True at T1, false at T2 without supersession |
| Source contradictions | Same source contradicts earlier self |
| Model contradictions | Ensemble disagreement |
| Internal system contradictions | Registry vs blueprint (Dual-19) |

### 16.2 Contradiction states

**Mission requested:** DETECTED, UNRESOLVED, EXPLAINED, RESOLVED, INVALIDATED, SUPERSEDED.

**Slice 2B implemented:** `OPEN`, `UNDER_INVESTIGATION`, `RESOLVED`, `RETAINED_UNCERTAIN`.

| Mapping | Notes |
| --- | --- |
| DETECTED → OPEN | On creation |
| UNRESOLVED → OPEN / UNDER_INVESTIGATION / RETAINED_UNCERTAIN | Active conflict |
| EXPLAINED → RESOLVED with rationale | Partial resolution |
| RESOLVED → RESOLVED | Requires resolution evidence IDs |
| INVALIDATED → `[PROPOSED]` | One side shown inapplicable |
| SUPERSEDED → artifact supersession | Context change |

### 16.3 Promotion firewall

`[IMPLEMENTED]` TCB `__promote` denies promotion when open contradiction affects candidate (`ContradictionState.OPEN`, `UNDER_INVESTIGATION`, `RETAINED_UNCERTAIN`).

### 16.4 Reporting

`[DOCUMENTED]` Evidence Protocol contradiction block. Known org contradiction (Dual-19) must remain visible.

---

## 17. Unknown / Uncertain / Novel

Do **not** collapse into generic `LOW_CONFIDENCE`.

| State | Meaning | Representation |
| --- | --- | --- |
| **KNOWN** | Established under defined conditions | `KnowledgeState.PROMOTED` or verified claim with scope |
| **UNCERTAIN** | Evidence exists; precision/confidence insufficient | Explicit status + cited partial evidence |
| **UNKNOWN** | Insufficient basis to establish proposition | `[UNKNOWN]` token; no fabricated filler |
| **CONTRADICTORY** | Relevant conflict unresolved | Linked `ContradictionCase` |
| **NOVEL** | Outside current ontology/model | Flag for architecture/extension; not UNKNOWN |

`[IMPLEMENTED]` Constitution status taxonomy. `[PROPOSED]` `EpistemicStatus` enum separate from artifact lifecycle and from confidence.

---

## 18. Epistemic Status vs Confidence

**Epistemic status** = governed categorical state of a proposition or artifact (draft, verified, contradicted, unknown, etc.).

**Confidence** = graded belief or assurance annotation, often subjective or model-estimated.

| Scenario | Status | Confidence | Truth |
| --- | --- | --- | --- |
| High-confidence false claim | REJECTED or REFUTED | may have been high | false |
| Low-confidence observation | RECORDED | low | may still be valuable evidence |
| Verified narrow fact | VERIFIED | may be moderate | true within scope |
| Accurate predictor, wrong theory | prediction CONFIRMED | N/A | explanation still hypothesis |

**Rule:** Confidence must not override epistemic status in gates. Promotion checks lifecycle + verification, not assurance alone.

---

## 19. Agent Reasoning

### 19.1 Standard reasoning structure `[PROPOSED]`

Agents should separate layers explicitly in reports (Response Protocol) and `[PROPOSED]` in structured output:

```text
OBSERVATION:     [what was seen — no causal language]
INTERPRETATION:  [meaning assigned — labeled]
INFERENCE:       [derived conclusion — labeled, cites observations]
ASSUMPTION:      [unverified premise — L6, labeled]
CLAIM:           [proposition about reality — cites evidence]
HYPOTHESIS:      [testable, falsifiable — labeled]
PREDICTION:      [future conditional — timestamped]
RECOMMENDATION:  [proposed action — not decision]
UNCERTAINTY:     [what is not known]
CONTRADICTION:   [conflicts detected]
```

### 19.2 Anti-patterns (forbidden)

- Silent conversion of inference → fact
- "I think X" → registered as Evidence
- Recommendation → recorded as Decision
- Model output → Evidence without provenance of acquisition

`[DOCUMENTED]` Response Protocol + Evidence Protocol. `[IMPLEMENTED]` RESEARCH_ANALYST_AGENT narrow JSON (`AgentOutput`) — not full template.

---

## 20. Multi-Agent Consensus

### 20.1 Mechanisms analyzed

| Mechanism | Verdict |
| --- | --- |
| Simple voting | `[PROPOSED]` acceptable for **prioritization**, not truth |
| Weighted voting | Risk of authority laundering unless weights are evidence-backed |
| Evidence-weighted consensus | Preferred for **synthesis** if weights trace to independent evidence |
| Specialist disagreement | Must be preserved; minority reports required |
| Independent reasoning | Required for verification class |
| Correlated errors | Must be detected (§21) |

**Critical principle:** Agreement among multiple agents does **not** automatically create evidence. Ten agents repeating the same unsupported claim ≠ ten independent evidence sources.

`[PROPOSED]` Consensus records as `Recommendation` artifacts, never `Knowledge`.

---

## 21. Correlated Error

Detect when multiple agents share:

| Shared factor | Detection `[PROPOSED]` |
| --- | --- |
| Same source | Provenance `source_refs` overlap |
| Same prompt | Prompt hash in mission provenance |
| Same model | Model ID in principal metadata |
| Same assumption | Explicit assumption registry overlap |
| Same context / memory | Memory lineage overlap |
| Contaminated memory | Unverified memory promoted to semantic store |

**Architecture:** Independence clusters on evidence; promotion requires verifications from **distinct clusters**.

`[IMPLEMENTED]` Partial: independent verification requires distinct `verifier_principal_id` ≠ producer. `[PROPOSED]` Full correlation graph.

---

## 22. Independent Verification

### 22.1 Qualifying independence

| Type | Independent when |
| --- | --- |
| Independent agent | Distinct principal, distinct correlation cluster, no shared prompt chain |
| Independent model | Different model ID + different training cutoff (if applicable) |
| Independent source | Distinct origin, not derived from same primary |
| Independent data path | Separate acquisition instrument/session |
| Independent reasoning | No access to producer's draft reasoning `[PROPOSED]` |
| Independent execution environment | Separate process/host for reproduction |

**Not independent:** Different agent **names** on same model, same prompt, same context.

`[IMPLEMENTED]` `VerificationKind.INDEPENDENT` with producer ≠ verifier; promotion gate checks active verifier principal.

### 22.2 Independence matrix

See §32 Matrices (C).

---

## 23. Epistemic Memory

Connect to future memory systems. Slice 2B `MemoryKind` / `MemoryState`:

| Memory type | Allowed to store | Forbidden |
| --- | --- | --- |
| Episodic | Time-bound events with evidence refs | Unverified speculation as fact |
| Semantic | Promoted knowledge summaries | Hypotheses without label |
| Procedural | Verified methods | Unvalidated shortcuts as "best practice" |
| Failure | Failed experiments, refuted predictions | Silent deletion |
| Hypothesis | Active hypotheses with falsification criteria | Promoted without test |
| Causal | Causal claims with evidence ladder | Correlation → causation unchecked |
| Contradiction | Open and resolved contradiction cases | Suppressed conflicts |
| Self-model | Calibrated capabilities/limitations | Inflated capability claims |

`[IMPLEMENTED]` Memory promotion blocked from equating to truth; TCB denies memory → knowledge shortcuts. States: `CANDIDATE`, `CHALLENGED`, `PROMOTED`, `SUPERSEDED`, `REJECTED`.

**Rule:** unverified speculation → permanent truth memory is **forbidden**.

---

## 24. Learning and Knowledge Promotion

### 24.1 Desired loop

```text
Evidence
  → Hypothesis
  → Experiment
  → Result
  → Verification
  → Knowledge Candidate
  → Independent Verification
  → Human Approval (scoped)
  → PROMOTE_KNOWLEDGE
  → Promotion
```

`[IMPLEMENTED]` TCB promotion gate checks:
- Candidate state `VERIFIED`
- Eligible fresh evidence with independent verification
- Independent verification on candidate
- Active approval bound to `candidate_id` (D-04)
- No unresolved contradictions affecting candidate
- Dedicated `PROMOTE_KNOWLEDGE` command (D-01)

### 24.2 AHOS-adjacent learning (architecture only)

| Loop element | Future AHOS connection `[PROPOSED]` |
| --- | --- |
| Paper trading | Experiment/run artifacts; outcomes as observations |
| Outcome recording | Evidence with event-time |
| Failure analysis | Failure memory + refuted hypotheses |
| Calibration | Prediction scoring over horizons |
| Self-improvement | `[PROPOSED]` governance-gated; not autonomous promotion |

**Do not implement learning in this mission.**

---

## 25. Decision Boundary

```text
EPISTEMIC SYSTEM
        ↓
  KNOWLEDGE / EVIDENCE (warrants)
        ↓
DECISION SYSTEM (authorization, policy, human approval)
        ↓
EXECUTION SYSTEM (tools, trading, deployment)
```

| Principle | Status |
| --- | --- |
| KNOWLEDGE ≠ AUTHORITY | `[IMPLEMENTED]` promotion ≠ execution grant |
| KNOWLEDGE ≠ EXECUTION | `[IMPLEMENTED]` protected resource denies |
| RECOMMENDATION ≠ DECISION | `[DOCUMENTED]` |
| DECISION ≠ OUTCOME | `[DOCUMENTED]` |

Orchestrator coordinates; it does not become source of truth.

---

## 26. AHOS Relationship

Architecture-only analysis of how epistemic architecture could **eventually** support AHOS concepts (no AHOS modification):

| AHOS concept | Epistemic mapping |
| --- | --- |
| Market observations | Source → Observation → Evidence |
| Token evidence | Evidence with chain provenance |
| Security findings | Claims + verification; high manipulation risk sources |
| Liquidity evidence | Time-bounded evidence; stale critical |
| Social/news evidence | Secondary/indirect; independence clustering |
| Claims | Claim artifacts scoped to token/market |
| Hypotheses | Testable strategy/thesis objects |
| Predictions | Price/event predictions with deadlines |
| Paper-trading outcomes | ExperimentRun results (simulation ≠ execution) |
| Failure episodes | Failure memory |
| Learning | Candidate promotion loop — governance gated |
| Calibration | Prediction scoring `[PROPOSED]` |

**AHOS_IMPACT = NONE** for this mission.

---

## 27. Agent Organization Relationship

| Agent / component | Epistemic interaction |
| --- | --- |
| **Agent 03 — Security** | Determines trust in evidence/communication/runtime paths; manipulation risk in source reliability |
| **Agent 04 — Governance** | Authorizes who may create, verify, approve, promote epistemic objects |
| **Research Agent** | Produces bounded outputs; Class A JSON ≠ full epistemic ladder |
| **Independent Verification (16)** | Executes INDEPENDENT verification records |
| **Red Team (19)** | Falsifies claims; raises contradictions |
| **Learning / Memory** | Stores by status; blocks speculation → truth |
| **Master Orchestrator** | Coordinates missions; L5 proposals until L2; not truth root |
| **Future Agent One** | `NOT IMPLEMENTED`; may synthesize and detect contradictions; may not promote or execute |

---

## 28. Failure Modes

| Failure | Detection | Containment | Recovery | Memory |
| --- | --- | --- | --- | --- |
| Hallucination | Provenance gap; no L0 source | Label UNVERIFIED; deny promotion | Independent verification | Failure pattern |
| Source contamination | Provenance chain | Revoke source | Re-acquire | Source reliability downgrade |
| Prompt injection | Anomaly in tool output | Fail closed; quarantine evidence | Red-team review | Incident record |
| Confirmation bias | Cherry-picked evidence IDs | Require negative evidence search | Broaden experiment | Methodology review |
| Selection bias | Sampling metadata | `[PROPOSED]` completeness dimension | Redesign experiment | Hypothesis refutation |
| Survivorship bias | Missing failure records | Mandate failure memory | Audit missing runs | Failure memory |
| Stale evidence | Freshness check | STALE transition; deny live use | Refresh observation | Timestamp audit |
| Duplicate evidence | Hash collision / same source | Deduplicate clusters | Merge with lineage | — |
| Correlated evidence | Cluster analysis | Count as one independent unit | Diversify sources | Cluster registry |
| Circular reasoning | Lineage cycle detection | Block promotion | Restructure warrants | Contradiction case |
| Circular verification | Verifier = producer chain | `[IMPLEMENTED]` producer ≠ verifier | New verifier | Revoke verification |
| Self-confirmation | Self-check only | Deny promotion | Independent verification | — |
| Authority laundering | Role title → action | Capability checks | Deny | Audit |
| Consensus laundering | Vote without evidence | Consensus ≠ proof rule | Evidence-weighted review | Minority report |
| Provenance loss | Missing Provenance fields | Construction validation fail | Re-register | — |
| Context loss | Missing mission link | Scope validation | Re-link | — |
| Temporal confusion | Event vs decision time | Freshness gate | Re-verify at decision-time | — |
| False precision | Numeric confidence theatre | Ban scalar-only gates | Multi-axis quality | — |
| Confidence inflation | Status/confidence mismatch | Separate fields | Status-only gates | Calibration |
| Unsupported causal inference | Causal memory without ladder | `[PROPOSED]` causal gates | Downgrade to hypothesis | — |
| Simulation-to-reality | Backtest labeled live | SIMULATION ≠ EXECUTION labels | Separate artifact types | — |
| Prediction-to-observation | Rewritten prediction | `[PROPOSED]` content hash immutability | Reject artifact | Audit |

---

## 29. Red-Team Model

Adversarial tests the architecture must survive:

| # | Question | Expected answer |
| --- | --- | --- |
| 1 | Can an agent label a hypothesis as verified? | Only via TCB transition with verification record; chat label insufficient |
| 2 | Can repeated unsupported claims become knowledge? | No — promotion gate requires evidence + independent verification + approval |
| 3 | Can one source appear as many independent sources? | Prevented by correlation clustering `[PROPOSED]`; partial via provenance |
| 4 | Can stale evidence support a live decision? | No — `is_eligible_positive_support` fails; report `[STALE]` |
| 5 | Can an agent erase contradictory evidence? | Artifacts immutable versioned; contradiction required visible |
| 6 | Can confidence override epistemic status? | Architecture forbids; `[PROPOSED]` enforce in gates |
| 7 | Can orchestrator convert recommendation into decision? | No without decision system + authority |
| 8 | Can model output become evidence without provenance? | Construction validation requires Provenance |
| 9 | Can a prediction be rewritten after outcome? | `[PROPOSED]` immutability; currently version increment only |
| 10 | Can failed experiments disappear? | FAILED/REFUTED terminal states retained |
| 11 | Can consensus vote override contradictory evidence? | No — promotion blocked on open contradiction |

`[IMPLEMENTED]` Tests in `tests2b/` cover promotion denial, self-verification, contradiction blocking, generic promotion refusal (D-01).

---

## 30. Epistemic Constitutional Principles

Evaluated and refined set:

1. **No claim without provenance.** `[IMPLEMENTED]` construction validation.
2. **No verification without criteria.** `[IMPLEMENTED]` method + evidence on VerificationRecord; `[PROPOSED]` explicit criteria objects.
3. **No promotion without defined gates.** `[IMPLEMENTED]` D-01/D-04 promotion path.
4. **No self-verification for consequential promotion.** `[IMPLEMENTED]` INDEPENDENT kind + producer ≠ verifier.
5. **No consensus-as-proof.** `[DOCUMENTED]` `[PROPOSED]` enforcement at orchestration layer.
6. **No hidden contradiction suppression.** `[IMPLEMENTED]` promotion firewall; `[DOCUMENTED]` reporting protocol.
7. **No silent epistemic status changes.** `[IMPLEMENTED]` TCB audit append on mutation.
8. **No retroactive prediction rewriting.** `[PROPOSED]` content-addressed immutability.
9. **No evidence laundering.** `[PROPOSED]` taxonomy dimensions + correlation clusters.
10. **No undocumented assumptions.** `[DOCUMENTED]` L6 labeling; `[PROPOSED]` assumption registry.
11. **Unknown must remain representable.** `[DOCUMENTED]` `[UNKNOWN]` token.
12. **Uncertainty must remain representable.** Separate from LOW_CONFIDENCE `[PROPOSED]`.
13. **Contradiction must remain representable.** `[IMPLEMENTED]` ContradictionCase.
14. **Knowledge must be scoped and contextual.** `[PROPOSED]` scope fields on candidates.
15. **Epistemic state does not grant authority.** `[IMPLEMENTED]` KNOWLEDGE_PROMOTE ≠ EXECUTION.

---

## 31. Implemented / Documented / Proposed

| Control | Classification | Evidence |
| --- | --- | --- |
| Typed epistemic artifacts | `[IMPLEMENTED]` | `agent_org/epistemic.py` |
| Lifecycle state machines | `[IMPLEMENTED]` | `LEGAL_ARTIFACT_TRANSITIONS` |
| Provenance on artifacts | `[IMPLEMENTED]` | `Provenance` dataclass |
| Evidence freshness / stale | `[IMPLEMENTED]` | `EvidenceState`, eligibility helper |
| Independent verification type | `[IMPLEMENTED]` | `VerificationKind.INDEPENDENT` |
| Knowledge promotion gate | `[IMPLEMENTED]` `[TESTED]` | `tcb.py` `__promote`, D-01/D-04 |
| Contradiction blocking promotion | `[IMPLEMENTED]` `[TESTED]` | `__require_candidate_verification` |
| Memory ≠ truth | `[IMPLEMENTED]` | TCB policy |
| Generic transition ≠ promotion | `[IMPLEMENTED]` | `refuse_generic_knowledge_promotion` |
| L0–L6 hierarchy | `[DOCUMENTED]` | Constitution §4 |
| Evidence Protocol (reporting) | `[DOCUMENTED]` | `AGENT_EVIDENCE_PROTOCOL.md` |
| Response Protocol structure | `[DOCUMENTED]` | `AGENT_RESPONSE_PROTOCOL.md` |
| Multi-agent reasoning enforcement | `[PROPOSED]` | No chat runtime enforcement |
| Evidence taxonomy dimensions | `[PROPOSED]` | Not on Evidence dataclass |
| Correlation cluster detection | `[PROPOSED]` | — |
| Prediction immutability | `[PROPOSED]` | Versioning only today |
| Assumption registry | `[PROPOSED]` | — |
| EpistemicStatus enum (UNKNOWN/NOVEL) | `[PROPOSED]` | — |
| AHOS epistemic integration | `[PROPOSED]` | Not connected |
| Plane A / D identity federation | `[UNKNOWN]` | `DEFERRED_IMPLEMENTATION` |
| Chat agent → TCB bridge | `[PROPOSED]` | — |

Never claim documented rules are enforced unless code or tests demonstrate it.

---

## 32. Required Matrices

### A. Object Matrix

| Object | Meaning | Evidence Required | Can Be False? | Verification | Promotion |
| --- | --- | --- | --- | --- | --- |
| Source | Origin registration | Self (locator/hash) | Yes (wrong locator) | `[PROPOSED]` source validation | No |
| Observation | Direct measurement | Method record | Yes | INDEPENDENT for verified obs | No |
| Evidence | Warrant artifact | Source + timestamps | Yes | INDEPENDENT for promotion use | No |
| Claim | Proposition about reality | ≥1 Evidence | Yes | INDEPENDENT for VERIFIED | No |
| Hypothesis | Testable unsettled prop | Falsification criteria | Yes | Via experiment results | No |
| Prediction | Future expectation | Linked hypothesis | Yes (refuted) | Outcome comparison | No |
| ExperimentPlan | Study design | Hypothesis link | Yes (flawed design) | Peer review `[PROPOSED]` | No |
| ExperimentRun | Execution result | Plan link | Yes (failed run) | Reproduction | No |
| VerificationRecord | Criteria evaluation | Method + evidence | Yes (FAIL) | N/A (is verification) | No |
| KnowledgeCandidate | Pre-promotion knowledge | Claims + evidence + verifications | Yes | INDEPENDENT + no open contradiction | Via PROMOTED state |
| ContradictionCase | Conflict record | Two artifact refs + rationale | N/A | Resolution evidence | No |
| Approval | Human promotion auth | Scoped to candidate | Yes (revoked) | N/A | Enables promotion |
| MemoryRecord | Stored recall | Evidence refs | Yes | Promotion to semantic `[PROPOSED]` gates | Not knowledge auto |

### B. Status Matrix (selected lifecycles)

**Claim**

| Status | Meaning | Allowed Transition | Forbidden Transition |
| --- | --- | --- | --- |
| DRAFT | Unpublished | SUBMITTED, REJECTED | VERIFIED |
| SUBMITTED | Published with evidence | CHALLENGED, VERIFIED*, REJECTED | VERIFIED* without verification |
| CHALLENGED | Disputed | VERIFIED*, REJECTED, SUPERSEDED | VERIFIED* without verification |
| VERIFIED | Independently verified | SUPERSEDED | DRAFT |
| REJECTED | Not accepted | — | VERIFIED |
| SUPERSEDED | Replaced | — | Any |

\*VERIFIED requires independent VerificationRecord (TCB enforced).

**KnowledgeCandidate**

| Status | Meaning | Allowed Transition | Forbidden Transition |
| --- | --- | --- | --- |
| SUBMITTED | Initial | UNDER_REVIEW, REJECTED, DEFERRED | PROMOTED |
| UNDER_REVIEW | Review | CHALLENGED, REJECTED, DEFERRED | PROMOTED |
| VERIFIED | Ready for promotion | CHALLENGED, REJECTED, DEFERRED | PROMOTED via generic transition |
| PROMOTED | Knowledge | SUPERSEDED | Via TRANSITION_ARTIFACT |
| CHALLENGED | Disputed | UNDER_REVIEW, VERIFIED, REJECTED, DEFERRED | PROMOTED |
| REJECTED | Failed | — | PROMOTED |
| DEFERRED | Postponed | UNDER_REVIEW | PROMOTED |

**ContradictionCase**

| Status | Meaning | Allowed Transition | Forbidden Transition |
| --- | --- | --- | --- |
| OPEN | Detected | UNDER_INVESTIGATION, RESOLVED, RETAINED_UNCERTAIN | Silent delete |
| UNDER_INVESTIGATION | Active work | RESOLVED, RETAINED_UNCERTAIN | RESOLVED without rationale |
| RESOLVED | Closed with evidence | — | OPEN without new case |
| RETAINED_UNCERTAIN | Acknowledged unresolved | UNDER_INVESTIGATION, RESOLVED | RESOLVED without record |

### C. Independence Matrix

| Verification Type | Independent? | Why / Why Not |
| --- | --- | --- |
| Same principal self-check | No | Same actor; `SELF_CHECK` only |
| Same model, different prompt | No | Correlated errors |
| Different model, same training data | Partial | Reduced but not full independence |
| Different agent name, same context | No | Correlated errors |
| Distinct principal, distinct source, distinct method | Yes | Meets INDEPENDENT criteria |
| Human verifier vs agent producer | Yes | If active HumanIdentity |
| Reproduction in separate process | Yes | Independent execution environment |
| Verifier shares prompt with producer | No | `[PROPOSED]` correlation detection |
| Slice 2B INDEPENDENT record, distinct principals | Yes | `[IMPLEMENTED]` minimum bar |

### D. Failure Matrix

See §28 (Failure Modes) — full table with Detection, Containment, Recovery, Memory columns.

---

## 33. Open Questions

1. Should `SUPPORTED` be added to `ClaimState` or remain implicit in `SUBMITTED` + evidence?
2. Should `EpistemicStatus` be a first-class field on all propositions or only on reports?
3. How should Plane A and Plane D agent identities map for verification independence?
4. What is the minimum independent verification bar for **non-promotion** claims (chat-only agents)?
5. Should prediction content be content-addressed (immutable hash) at creation?
6. How should negative evidence ("absence") be typed without implying proof of absence?
7. What AHOS observation instruments become authoritative sources when integration is approved?
8. Should assurance (0–100) be deprecated in favor of explicit quality vectors?
9. How do contradiction states map to user-facing Constitution tokens (`[CONTRADICTED]`)?
10. What is the federation model between Slice 1 maturity and Slice 2B knowledge promotion?

---

## 34. Human Decisions Required

| ID | Decision | Status |
| --- | --- | --- |
| **HD-01** | Dual-19 resolution: merge, map, dual-run, or retire Plane A vs Plane D | `HUMAN_DECISION_REQUIRED` |
| **HD-02** | Claim lifecycle vocabulary: adopt SUBMITTED vs add SUPPORTED state | `HUMAN_DECISION_REQUIRED` |
| **HD-03** | Evidence taxonomy: approve orthogonal dimension model vs minimal enum | `HUMAN_DECISION_REQUIRED` |
| **HD-04** | Scalar assurance: retain, restrict, or replace with quality vector | `HUMAN_DECISION_REQUIRED` |
| **HD-05** | Chat agent → TCB artifact bridge: when planned agents may write epistemic objects | `HUMAN_DECISION_REQUIRED` |
| **HD-06** | AHOS epistemic integration boundary (future): read-only vs mediated write | `HUMAN_DECISION_REQUIRED` |
| **HD-07** | Contradiction state alignment: extend Slice 2B vs map documentary states | `HUMAN_DECISION_REQUIRED` |
| **HD-08** | Adoption of this architecture doc as L2 governance text | `HUMAN_DECISION_REQUIRED` |

---

## 35. Recommended Future Work — STATE ONLY

`RECOMMENDED_NEXT_MISSION = STATE_ONLY — DO NOT EXECUTE`

The following are **recommendations only**. They are not activated missions.

1. **FUTURE_IMPLEMENTATION_REQUIRED:** Add orthogonal evidence metadata dimensions to `Evidence` (or sidecar artifacts) without breaking existing tests.
2. **FUTURE_IMPLEMENTATION_REQUIRED:** Correlation cluster ID on evidence and verification for multi-agent deduplication.
3. **FUTURE_IMPLEMENTATION_REQUIRED:** Prediction content-hash immutability at registration.
4. **FUTURE_IMPLEMENTATION_REQUIRED:** Chat-to-TCB adapter for Response Protocol → REGISTER_ARTIFACT (gated by `epistemic.write`).
5. **FUTURE_IMPLEMENTATION_REQUIRED:** Explicit `EpistemicStatus` on knowledge candidates (KNOWN/UNCERTAIN/UNKNOWN/CONTRADICTORY/NOVEL).
6. **Recommended next documentary agent:** Agent 06 — Research Methodology (thin boundary with Agent 05; coordinate with Master Orchestrator).
7. **Recommended verification mission:** Independent red-team of promotion gate assumptions (`tests2b` extension).
8. **Recommended governance mission:** Agent 04 alignment on promotion authority and human approval scopes.

**AGENT-05 does not execute any of the above.**

---

## Document provenance

| Field | Value |
| --- | --- |
| Author | AGENT-05 (Epistemic Reasoning Architect) |
| Task | TASK-20260914-005 |
| Commander | MASTER ORCHESTRATOR |
| Repository | `G:\robat\ahos-agent-org` |
| Code changes | NONE |
| Runtime changes | NONE |
| AHOS impact | NONE |
| Classification | `[PROPOSED]` architecture unless cited `[IMPLEMENTED]` / `[DOCUMENTED]` |

---

*End of AGENT_05_EPISTEMIC_REASONING_ARCHITECTURE.md*
