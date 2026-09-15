# Agent-01 Organizational Federation Architecture

```text
DOCUMENT_ID          = AGENT_01_ORGANIZATIONAL_FEDERATION_ARCHITECTURE
VERSION              = 0.1.0
STATUS               = DESIGN_ONLY / NOT_RUNTIME_CONNECTED
DECISION_BASIS       = ORGANIZATIONAL_ARCHITECTURE_BASELINE_v0.1
DECISION_GATE        = PROPOSED_PENDING_HUMAN_ACCEPTANCE
DUAL19_STATUS        = UNRESOLVED
AGENT_ONE_RUNTIME    = NOT_IMPLEMENTED / FUTURE_NON_AUTHORITY_ROOT
AUTHORITY_CREATED    = NONE
RUNTIME_EFFECT       = NONE
AHOS_EFFECT          = NONE
```

## Executive Answer

The smallest technically honest architecture is not a flat 19-agent council and not a generic message bus. It is a local, durable, fail-closed **hierarchical coordination substrate** that first proves one bounded chain:

```text
Human Principal
  → authenticated intent
  → thin Agent One
  → durable Mission Controller
  → one accepted Direct Commander
  → one Specialist
  → structured Result/Evidence
  → independent Verification
  → scoped Acceptance
  → durable Audit/Memory projection
  → Agent One synthesis
  → Human Principal
```

The minimum substrate combines the seven primitives from Agent-14 reconciliation with: a versioned relationship registry, durable command/request/result routing inside the Mission Controller, independent-verifier dispatch, acceptance binding, and governed audit/memory projection.

No authoritative commander mapping for the 19 Plane-D roles can be derived today. Existing Agent-03–14 documents name `MASTER_ORCHESTRATOR`; Agent-15–19 documents name `AGENT-01 / AGENT ONE`; no accepted L2 identity binding or subordinate tree exists. Inventing domain commanders would violate Dual-19 and identity invariants. Therefore this architecture defines the enforceable model and leaves every unresolved commander edge `ACTIVATION_BLOCKED`.

## A. Canonical Organizational Hierarchy

### Target hierarchy

```text
MEHRDAD / HUMAN PRINCIPAL
          │ human intent + governance/acceptance authority
          ▼
AGENT ONE — thin reasoning/orchestration client
          │ proposed mission/selection; no identity or execution authority
          ▼
MISSION CONTROLLER — authoritative mission/lifecycle/routing boundary
          │
          ├── DIRECT COMMANDER A ── specialists ── subordinates
          ├── DIRECT COMMANDER B ── specialists ── subordinates
          └── DIRECT COMMANDER C ── specialists ── subordinates

ORTHOGONAL SERVICES:
Identity/Session · Policy/Authority · Federation Gateway · TCB
Independent Verification · Acceptance · Audit · Organizational Memory
```

The A/B/C labels are slots, not assigned identities. This document does not invent their membership.

### Current hierarchy

```text
Human → Cursor sessions → documentary personas → markdown → Human
```

There is no enforced organizational hierarchy. Existing commander statements are documentary and conflict across generations of architecture reports.

### Hierarchy invariants

1. Every `ACTIVE` agent has exactly one current `COMMANDER_OF` incoming edge.
2. A missing, multiple, expired, ambiguous, or unaccepted commander edge blocks activation.
3. Commander relationships are versioned records, not fields inferred from names.
4. The Human Principal commands Agent One through an accepted identity/session path.
5. Agent One proposes/routs through the Mission Controller; it does not directly activate agents.
6. A commander may command only identities and mission classes explicitly within its authority ceiling.
7. No hierarchy edge implies verification, supervision, peer, knowledge, or resource-modification authority.

## B. Direct Commander Model

Canonical relationship:

```yaml
CommanderRelationship:
  relationship_id: string
  relationship_version: integer
  commander_identity_ref: plane-qualified identity
  subordinate_identity_ref: plane-qualified identity
  allowed_mission_classes: [string]
  capability_ceiling_refs: [string]
  resource_ceiling_refs: [string]
  effective_from: UTC timestamp
  effective_until: UTC timestamp or null
  governance_decision_ref: string
  lifecycle_state: PROPOSED | ACCEPTED | ACTIVE | SUSPENDED | REVOKED | SUPERSEDED
  audit_ref: string
```

Validation:

- exactly one active commander per active subordinate;
- commander and subordinate cannot be the same principal;
- relationship cannot cross taxonomy planes without an accepted mapping/binding;
- child ceilings must be subsets of commander ceilings;
- no relationship may appoint Agent One’s commander or alter Agent One’s authority ceiling;
- only the Mission Controller may use an active relationship to authorize activation;
- revocation blocks new commands and triggers mission review, not silent reassignment.

The Direct Commander owns bounded mission assignment, progress/revision requests, subordinate escalation intake, and result receipt. It does not own identity, unrestricted capability issuance, independent verification, final acceptance, or protected-state mutation.

## C. Supervision Model

Supervision is a separate edge:

```yaml
SupervisionRelationship:
  supervisor_identity_ref: plane-qualified identity
  subject_identity_ref: plane-qualified identity
  visibility_scope:
    missions: boolean
    tasks: boolean
    blockers: boolean
    contradictions: boolean
    verification_status: boolean
    quality_indicators: boolean
    evidence_content: NONE | METADATA | SCOPED_CONTENT
  command_authority: false
  verification_authority: false
  resource_access_refs: [string]
  governance_decision_ref: string
```

A supervisor may observe only its granted projection. It may flag overdue work, blockers, failures, contradictions, or escalation needs. It cannot activate, cancel, widen scope, view unrelated evidence, change identity, modify authority, or claim independent verification unless a distinct relationship grants that power.

Commander dashboards are read projections from Mission Controller/Audit state; they are not direct database access.

## D. Peer Request Model

Peer collaboration uses `OrgRequestEnvelope`, never `MissionCommandEnvelope`.

Minimum contract:

```yaml
OrgRequestEnvelope:
  schema_version: string
  request_id: string
  requesting_identity_ref: plane-qualified identity
  target_identity_ref: plane-qualified identity
  commander_context_ref: string
  mission_id: string
  task_id: string
  request_type: INFORMATION | ANALYSIS | REVIEW | EVIDENCE | METHOD_CRITIQUE | CHALLENGE
  objective: string
  required_output_contract_ref: string
  evidence_requirements: [string]
  budget_ref: string or null
  deadline: UTC timestamp or null
  authority_context_ref: string
  provenance_refs: [string]
  created_at: UTC timestamp
  expires_at: UTC timestamp
  status: PROPOSED | POLICY_ALLOWED | DELIVERED | ACKNOWLEDGED | COMPLETED | DECLINED | EXPIRED | BLOCKED
  activation_implied: false
  authority_transfer: false
```

Reconciliation:

- Slice 2B `CommandEnvelope` remains the TCB mutation ingress.
- `MissionCommandEnvelope` is superior-to-subordinate mission instruction validated by the Mission Controller.
- `OrgRequestEnvelope` is a lateral request and cannot activate or transfer authority.
- Communication Protocol envelopes are documentary predecessors; a future protocol version may carry these typed bodies.
- The Mission Controller validates peer policy, mission scope, target lifecycle, budget, expiry, and evidence permissions before delivery.

An imperative sentence in a peer request remains a request. If the target is inactive, the request is queued/blocked or returned to the target’s commander; it does not activate the target.

## E. Mission Routing

Mission path:

```text
HumanIntentRecord
  → Agent One formalization
  → MissionProposal
  → required Human decision (when consequential)
  → Mission Controller authorization
  → MissionRecord
  → commander selection from accepted relationship registry
  → MissionCommandEnvelope
  → subordinate activation
```

MissionRecord minimum:

```yaml
MissionRecord:
  mission_id: string
  mission_version: integer
  parent_mission_id: string or null
  objective: string
  mission_class: string
  human_intent_ref: string
  owner_identity_ref: string
  direct_commander_ref: string
  risk_level: LOW | MEDIUM | HIGH | CRITICAL
  scope_ref: string
  capability_ceiling_refs: [string]
  protected_resource_refs: [string]
  context_snapshot_ref: string
  evidence_standard_ref: string
  result_contract_ref: string
  verifier_profile_ref: string or null
  acceptance_policy_ref: string
  state: PROPOSED | AUTHORIZATION_REQUIRED | AUTHORIZED | DISPATCHED | ACTIVE | BLOCKED | RESULT_SUBMITTED | VERIFYING | ACCEPTANCE_PENDING | ACCEPTED | REJECTED | REVISION_REQUIRED | FAILED | CANCELLED | COMPLETED
  timestamps: object
  audit_refs: [string]
```

Agent One can propose and monitor missions. Mission identity, authorization, lifecycle, and dispatch are owned by the Mission Controller.

## F. Task Routing

Each mission decomposes into versioned tasks:

```yaml
TaskRecord:
  task_id: string
  mission_id: string
  parent_task_id: string or null
  owner_identity_ref: string
  assigned_identity_ref: string
  commander_relationship_ref: string
  objective: string
  inputs: [artifact reference]
  expected_output_contract_ref: string
  evidence_requirements: [string]
  capability_scope_refs: [string]
  resource_scope_refs: [string]
  dependencies: [task id]
  deadline: UTC timestamp or null
  state: PROPOSED | AUTHORIZED | READY | ACTIVE | BLOCKED | RESULT_SUBMITTED | FAILED | CANCELLED | COMPLETED
```

Mission Controller creates/authorizes task routing; commanders may propose decomposition within mission scope. A task cannot widen mission scope or authority. Dependency-ready tasks may run in parallel; mutation, decision, or evidence dependencies remain sequential.

## G. Result Routing

Canonical return path:

```text
Subordinate
  → MissionResultEnvelope
  → Direct Commander structural/scope review
  → Mission Controller result ingestion/deduplication
  → Agent One comparison/contradiction detection
  → Independent Verification dispatch when required
  → Acceptance gate
  → TCB-governed audit/memory update
  → Agent One synthesis
  → Human Principal
```

Minimum result:

```yaml
MissionResultEnvelope:
  schema_version: string
  result_id: string
  mission_id: string
  task_id: string
  producer_identity_ref: string
  producer_version_ref: string
  commander_relationship_ref: string
  scope_status: IN_SCOPE | PARTIAL | OUT_OF_SCOPE
  status: RESULT_SUBMITTED | BLOCKED | FAILED
  findings: [typed finding reference]
  evidence_refs: [string]
  claim_refs: [string]
  contradiction_refs: [string]
  unknowns: [string]
  limitations: [string]
  validation_performed: [string]
  validation_not_performed: [string]
  recommended_next_action: string
  context_snapshot_ref: string
  produced_at: UTC timestamp
  signature_or_attestation_ref: string
```

A commander can return malformed/out-of-scope work for revision but cannot label it independently verified or accepted. Mission Controller deduplicates results and records late/expired submissions without promoting them.

## H. Knowledge Mesh

The Command Tree carries authority; the Knowledge Mesh carries typed information references.

Allowed mesh payload classes:

- Source/Evidence;
- Observation;
- Claim;
- Hypothesis;
- Prediction;
- Contradiction;
- Research finding;
- Methodological criticism;
- Verification result;
- accepted knowledge/memory projection reference.

Knowledge edge:

```yaml
KnowledgeRelationship:
  sender_identity_ref: string
  receiver_identity_ref: string
  allowed_artifact_types: [string]
  mission_scope_required: boolean
  content_access: METADATA | SCOPED_CONTENT
  provenance_required: true
  authority_transfer: false
  commander_change: false
```

Mesh messages carry artifact IDs and immutable/versioned context, not flattened prose presented as truth. Receiving evidence gives no command authority, capability, acceptance power, or permission to mutate the source.

## I. Contradiction Routing

```text
THESIS
  + ANTI-THESIS
  + EVIDENCE FOR
  + EVIDENCE AGAINST
  + SOURCE QUALITY
  + INDEPENDENCE ANALYSIS
  → ContradictionCase
  → targeted VerificationRequest
  → RESOLVED | RETAINED_UNCERTAIN | UNRESOLVED
```

Contradiction record:

```yaml
OrganizationalContradiction:
  contradiction_id: string
  mission_id: string
  affected_task_ids: [string]
  position_refs: [string]
  evidence_for_refs: [string]
  evidence_against_refs: [string]
  source_independence_assessment: string
  materiality: LOW | MEDIUM | HIGH | CRITICAL
  owner_identity_ref: string
  verifier_profile_ref: string
  state: OPEN | INVESTIGATING | RESOLVED | RETAINED_UNCERTAIN
  resolution_evidence_refs: [string]
  resolution_scope: string or null
```

Agent One detects and routes contradictions but cannot resolve them by vote, confidence, seniority, or narrative preference. Material unresolved contradictions remain visible to acceptance and memory gates.

## J. Verification Routing

Distinct review classes:

| Review | Producer may perform? | Commander may perform? | Counts as independent? | Can accept? |
| --- | --- | --- | --- | --- |
| `SELF_CHECK` | YES | N/A | NO | NO |
| `PEER_REVIEW` | NO/peer | possible | NO by default | NO |
| `SUPERVISORY_REVIEW` | NO | YES | NO by default | NO |
| `INDEPENDENT_VERIFICATION` | NO | only if independence profile proves eligibility | YES when profile passes | NO |
| `FINAL_ACCEPTANCE` | NO | only if separately authorized acceptance owner | not verification | YES for scoped result |

VerificationRequest:

```yaml
VerificationRequest:
  verification_request_id: string
  mission_id: string
  target_result_id: string
  target_claim_refs: [string]
  acceptance_criteria_ref: string
  required_profile_ref: string
  forbidden_verifier_refs: [string]
  independence_dimensions: [IDENTITY, MODEL, CONTEXT, DATA, METHOD, ENVIRONMENT]
  requested_by_identity_ref: string
  status: REQUESTED | DISPATCHED | PASS | FAIL | INCONCLUSIVE | BLOCKED
```

Mission Controller/verification dispatch selects from eligible profiles. Agent One may request verification and consume projections; it cannot choose a dependent verifier to manufacture independence, write the verification result, or accept its own synthesis.

## K. Organizational Memory

Durable memory entry must preserve:

```yaml
OrganizationalMemoryEntry:
  memory_id: string
  memory_kind: MISSION | EVIDENCE | DECISION | OUTCOME | FAILURE | PERFORMANCE | GOVERNANCE
  source_refs: [string]
  author_identity_ref: string
  mission_id: string
  task_id: string
  created_at: UTC timestamp
  epistemic_type: string
  evidence_refs: [string]
  reasoning_status: string
  verification_refs: [string]
  contradiction_refs: [string]
  acceptance_ref: string or null
  lifecycle_state: CANDIDATE | ACCEPTED | INVALIDATED | EXPIRED | SUPERSEDED
  revision: integer
  supersedes: string or null
  valid_from: UTC timestamp
  expires_at: UTC timestamp or null
  audit_refs: [string]
```

Only TCB-governed paths write canonical memory. Mission logs are not truth. Documentation, sent, received, understood, implemented, verified, accepted, outcome, invalidated, and superseded remain separate states. Agent One reads projections and maintains ephemeral working context only.

## L. Change Propagation

```text
DISCOVERY
  → CHANGE PROPOSAL
  → IMPACT ANALYSIS
  → AFFECTED IDENTITY/ARTIFACT DISCOVERY
  → OWNER IDENTIFICATION
  → HUMAN/GOVERNANCE DECISION
  → MISSION CREATION
  → IMPLEMENTATION
  → INDEPENDENT VERIFICATION
  → ACCEPTANCE
  → CANONICAL MEMORY UPDATE
  → TARGETED VERSIONED PROPAGATION
```

Change notices include changed artifact/version, old/new semantics, affected identities, required re-acknowledgment/revalidation, effective time, expiry/supersession, rollback, and evidence references.

No arbitrary broadcast to all 19. Mission Controller computes recipients from versioned dependency, relationship, capability, and context references. Delivery does not prove receipt; receipt does not prove understanding; understanding does not prove enforcement.

## M. Agent Lifecycle

Target lifecycle:

```text
REGISTERED
  → IDLE / DORMANT / WAITING_FOR_COMMAND
  → ACTIVATION_REQUESTED
  → AUTHORIZED
  → ACTIVE
  → RESULT_SUBMITTED
  → VERIFYING | REVISION_REQUIRED | REJECTED
  → ACCEPTANCE_PENDING
  → ACCEPTED
  → COMPLETED
  → IDLE / DORMANT
```

Failure side states: `BLOCKED`, `FAILED`, `CANCELLED`, `TIMED_OUT`, `SUSPENDED`, `QUARANTINED`, `RECOVERY_REQUIRED`.

Activation requires:

1. authenticated active identity;
2. one accepted active direct commander;
3. valid mission and task;
4. valid `MissionCommandEnvelope` from that commander through MC;
5. valid authority/capability/resource context;
6. current context snapshot;
7. non-expired, non-replayed command.

No self-activation, self-task, self-appointment, unauthorized mission, stale mission reactivation, or authority inference from `ACTIVE`. Reactivation uses a new mission/command identity or explicitly governed recovery transition.

## N. Capability Registry

Canonical registry view:

```yaml
AgentCapabilityRecord:
  identity_ref: string
  role_ref: string
  taxonomy_plane: string
  direct_commander_relationship_ref: string or null
  supervision_relationship_refs: [string]
  peer_relationship_refs: [string]
  knowledge_relationship_refs: [string]
  capabilities: [string]
  prohibited_capabilities: [string]
  input_contract_refs: [string]
  output_contract_refs: [string]
  allowed_mission_classes: [string]
  verification_eligibility_profile_refs: [string]
  authority_ceiling_ref: string
  protected_resource_policy_refs: [string]
  communication_policy_ref: string
  maturity: string
  lifecycle_state: string
  record_version: integer
  governance_decision_ref: string
```

Current Plane-D runtime capabilities are empty. Architecture reports exercising READ/ANALYZE/PROPOSE do not self-issue runtime grants. Missing commander, charter, capability record, or plane binding blocks activation.

## O. Authority Boundaries

- Human Principal: product direction, L2 governance, consequential acceptance.
- Identity/Session: authentication, session lifecycle; not mission content.
- Agent One: intent formalization, decomposition, coordination, synthesis; not trust/authority root.
- Mission Controller: mission/task/lifecycle/routing; not identity root, TCB, verifier, or acceptor.
- Direct Commander: bounded subordinate command/revision/escalation; not unrestricted supervisor/verifier.
- Specialist: scoped work and results; no self-activation/acceptance.
- Federation Gateway: translation and single governed routing; no policy weakening or implicit mapping.
- TCB: protected mutation/epistemic gates; not mission reasoning.
- Verification Plane: eligible independent checks; not acceptance.
- Acceptance: scoped decision; not evidence fabrication.
- Audit/Memory: durable trace/projections; not hidden policy or authority.
- Cursor: client/federation surface only.

Agent One cannot become a monolith. Separate services may run locally, but their interfaces, principals, policy checks, audit records, and failure boundaries remain distinct.

## P. Cursor Federation Boundary

Target:

```text
Cursor client
  → Federation Bridge
  → Identity/Session validation
  → Agent One intent interface
  → Mission Controller
  → Command Tree
  → Federation Gateway/TCB
  → Verification/Audit projections
```

Cursor headers, session names, prompts, markdown, tool output, and claimed roles are untrusted inputs. The bridge authenticates, validates schema/version/replay/expiry, binds human intent, submits to accepted APIs, and returns read-only projections. It cannot issue identity/capabilities, activate directly, verify, accept, write memory, or bypass MC/TCB.

This boundary is design-only and absent today.

## Q. Dual19 Handling

```text
DUAL19_STATUS = UNRESOLVED
```

Plane A `agent.*` and Plane D `agent.org.NN-*` remain separate. Every graph node/edge carries `plane`. Matching number/name/domain creates no relationship.

Interim design behavior:

- ambiguous alias → `ROLE_IDENTITY_AMBIGUOUS`;
- no accepted cross-plane binding → no command/supervision/verification edge;
- Plane-D runtime activation → blocked until explicit identity/charter/capability/commander records;
- mapping records are explicit, versioned, scoped, auditable, revocable, and human-governed;
- no automatic conversion, role collapse, or authority inheritance.

## R. Human Escalation

Escalate to Mehrdad for:

- D1/D2/D3 acceptance;
- commander-tree assignments and mapping decisions;
- authority/policy/identity changes;
- unresolved critical contradictions;
- verifier independence conflicts;
- acceptance of high-risk/consequential outcomes;
- protected resource or AHOS scope;
- irreversible migration, recovery exceptions, or security control weakening.

Escalation payload includes mission/task, decision requested, evidence, options, risks, contradiction status, deadline, safe default, and what remains blocked.

The human is not the routine message router or evidence-copy service. Infrastructure collects technical evidence; the human exercises legitimate governance judgment.

## S. Failure and Recovery

Fail-closed cases:

- ambiguous/multiple commander;
- unknown/expired/revoked identity, capability, mission, task, context, or mapping;
- replay/duplicate command/request/result;
- peer request disguised as command;
- lifecycle transition without MC;
- result after expiry or from wrong producer;
- verifier independence failure;
- contradiction affecting acceptance;
- audit/store corruption;
- bridge/MC/TCB unavailable;
- stale projection presented as live.

Recovery:

1. stop dispatch/mutation for affected scope;
2. preserve evidence and durable audit;
3. mark `RECOVERY_REQUIRED` or `BLOCKED`;
4. revoke/expire unsafe authority;
5. restore from verified checkpoint;
6. reconcile command, mission, TCB, audit, and projection heads;
7. independently verify recovery;
8. obtain required acceptance before resuming.

No automatic fail-open, silent replay, hidden reassignment, or loss of contradictions.

## T. Auditability

The durable audit must answer without Cursor transcript archaeology:

- who authenticated;
- who commanded whom;
- which commander relationship/version applied;
- which mission/task/context/policy versions applied;
- which capabilities/resources were requested and derived;
- what command/request/result was delivered, acknowledged, expired, denied, or replayed;
- what evidence and contradictions existed;
- who verified, with what independence profile and environment;
- who accepted which exact scope;
- what entered memory and what later invalidated/superseded it;
- how failures/recovery changed state.

Audit is append-only/tamper-evident, externally anchorable, queryable through read-only projections, and transactionally aligned with state. Agent One and frontend cannot rewrite audit.

## Progressive Federation Sequence

| Phase | Deliverable | Honest claim after acceptance and verification |
| --- | --- | --- |
| 0 | architecture, graph, contracts, D1/D2/D3 and commander decisions | design baseline only |
| 1 | namespace resolver, durable Identity/Session, Mission Controller core, durable mission/audit store, envelope validators | authenticated missions can exist; no Agent One/specialist runtime claim |
| 2 | thin Agent One service + Cursor Federation Bridge + result ingestion | human intent can produce governed mission proposals/commands; no federation claim yet |
| 3 | one accepted Direct Commander → one Specialist path, federation gateway, bounded worker adapter | one hierarchical path operates; not 19 agents |
| 4 | independent verification dispatch, acceptance binding, durable TCB/memory projection, recovery | one end-to-end verified/accepted path |
| 5 | controlled additional commanders/specialists and knowledge/contradiction mesh | bounded multi-agent pilot |
| 6 | accepted per-agent records and full 19-role expansion | full federation only if runtime evidence proves every required path |

Every phase follows:

```text
BUILD → INTEGRATE → TEST → FAILURE ANALYSIS
→ INDEPENDENT VERIFICATION → ACCEPT / REJECT / REWORK
```

## Current Blockers

1. D1/D2/D3 remain `PROPOSED_PENDING_HUMAN_ACCEPTANCE`.
2. Dual-19 final mapping is unresolved.
3. Agent One canonical runtime identity and charter are unresolved.
4. No authoritative direct commander mapping exists.
5. No durable organization identity/session or Mission Controller.
6. No federation gateway, durable TCB store, or Cursor bridge.
7. No runtime command/request/result transport.
8. No independent-verification dispatch/eligibility service.
9. No organization-wide acceptance binding, durable memory, or recovery.
10. No specialist runtime records/charters/capability grants for Plane D.

## Reality Report

### 1. WHAT EXISTS TODAY

- Slice 1 logical registry/policy/tasks/audit;
- Slice 2B in-memory TCB/identity/grants/epistemic artifacts/projections;
- one bounded research analyst path;
- protocol, governance, and Agent-03–19 architecture artifacts;
- substrate tests reported passing by prior verification missions.

### 2. WHAT EXISTS ONLY AS DESIGN

- this hierarchy, command tree, commander/supervision/peer/knowledge relations;
- Mission Controller, MissionCommandEnvelope, OrgRequestEnvelope, result routing;
- federation, Agent One service, Cursor bridge, verification dispatch, acceptance/memory architecture.

### 3. WHAT IS PARTIALLY IMPLEMENTED

- task state machines (not mission/agent lifecycle);
- identity/session/grants (non-production Slice 2B only);
- TCB mutation and epistemic verification artifacts (in-memory, not org-wide);
- audit/projections (not durable/external);
- research result ingestion for one bounded path (not general federation).

### 4. WHAT IS MISSING

All blockers listed above, plus accepted hierarchy edges and durable transport/recovery.

### 5. WHAT CAN BE SAFELY IMPLEMENTED NOW

Without D1/D2/D3 acceptance, only non-runtime design artifacts, schema prototypes, and isolated test vectors that cannot be mistaken for authority. Runtime Phase 1 requires an explicit human gate and separate implementation mission.

### 6. WHAT REQUIRES HUMAN DECISION

- D1/D2/D3;
- authoritative commander edges;
- Agent One identity/charter;
- identity/bootstrap and MC placement;
- verifier eligibility;
- acceptance/memory authority;
- persistence/audit and AHOS access ceiling.

### 7. WHAT REQUIRES INDEPENDENT VERIFICATION

Every implemented phase, identity/authority enforcement, lifecycle/routing, federation equivalence, TCB durability, verifier independence, recovery, Cursor boundary, and no-bypass invariants.

### 8. WHAT MUST NOT BE IMPLEMENTED YET

- full 19-agent runtime;
- arbitrary commander tree;
- LLM autonomy/self-improvement;
- frontend implying live authority;
- AHOS integration/execution;
- any MC/identity/federation/Agent One runtime before the human decision and scoped implementation mission.

## Final Status

```text
ORGANIZATIONAL_MODEL = HIERARCHICAL COMMAND TREE + ORTHOGONAL KNOWLEDGE MESH
COMMAND_TREE = DESIGNED / COMMANDER MEMBERSHIP UNRESOLVED
AGENT_ONE_ROLE = THIN PRIMARY INTENT ORCHESTRATOR / NOT ROOT OF TRUST
DIRECT_COMMANDER_MODEL = DESIGNED / NO AUTHORITATIVE EDGES ACCEPTED
SUPERVISION_MODEL = DESIGNED / SEPARATE FROM COMMAND AND VERIFICATION
REQUEST_MODEL = OrgRequestEnvelope DESIGN_ONLY / NOT ENFORCED
MISSION_MODEL = MISSION-CENTRIC / MISSION CONTROLLER NOT IMPLEMENTED
RESULT_MODEL = MissionResultEnvelope DESIGN_ONLY / NOT ENFORCED
KNOWLEDGE_MESH = DESIGN_ONLY / AUTHORITY-ORTHOGONAL
VERIFICATION_MODEL = DESIGNED / DISPATCH RUNTIME ABSENT
MEMORY_MODEL = DESIGNED / DURABLE CANONICAL MEMORY ABSENT
CHANGE_PROPAGATION = TARGETED, VERSIONED, AUTHORIZED / NOT ENFORCED
CURRENT_REALITY = TESTED SUBSTRATE + DOCUMENTARY SESSIONS; NO FEDERATED ORGANIZATION
IMPLEMENTATION_GAPS = IDENTITY, MC, COMMANDER MAP, ENVELOPES, FEDERATION, DURABILITY, IV, ACCEPTANCE, RECOVERY
HUMAN_DECISIONS_REQUIRED = D1/D2/D3 + COMMANDER TREE + AGENT ONE IDENTITY + TRUST/ACCEPTANCE POLICIES
NEXT_SAFE_IMPLEMENTATION_STEP = HUMAN DECISION, THEN SEPARATE PHASE-1 IMPLEMENTATION MISSION
DUAL19_STATUS = UNRESOLVED
RUNTIME_CHANGES = NONE
AHOS_IMPACT = NONE
```
