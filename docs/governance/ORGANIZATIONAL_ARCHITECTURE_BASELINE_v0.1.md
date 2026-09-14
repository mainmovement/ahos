# Organizational Architecture Baseline v0.1

```text
DOCUMENT_ID          = ORGANIZATIONAL_ARCHITECTURE_BASELINE
VERSION              = 0.1
MISSION_SOURCE       = CURRENT HUMAN PROPOSAL / L5
DOCUMENT_CLASS       = DESIGN_ONLY / PROPOSED GOVERNANCE BASELINE
DECISION_GATE_STATUS = PROPOSED_PENDING_HUMAN_ACCEPTANCE
L2_ADOPTION          = NOT_RECORDED
ENFORCEMENT          = NOT_IMPLEMENTED
RUNTIME_VERIFIED     = NO
AUTHORITY_CREATED    = NONE
SUPERSEDES           = NONE
```

## 1. PURPOSE AND SCOPE

This document codifies three proposed organizational decisions for explicit consideration by Mehrdad, the Human Principal:

1. an interim namespace lock while the Dual-19 mapping remains unresolved;
2. a hard authority ceiling for a future Agent One;
3. a Cursor trust boundary that keeps session metadata and natural-language role claims outside the authority substrate.

The document answers:

- what each proposal means;
- what changes only after explicit Human Principal acceptance;
- what remains unresolved after acceptance;
- which future runtimes must enforce the accepted rules;
- which stable invariants future implementation and verification must test.

This document does not:

- record human acceptance;
- create or activate Agent One;
- bind the mission label `AGENT-01` to any runtime identity;
- resolve Dual-19;
- implement identity, mission, messaging, federation, TCB persistence, verification, frontend, or execution services;
- grant authority, capability, verification, approval, promotion, or execution;
- modify AHOS or any existing organizational runtime.

Source hierarchy:

```text
L0 REPOSITORY/RUNTIME REALITY
  > L1 CURRENT EXECUTED EVIDENCE
  > L2 RECORDED GOVERNANCE
  > L3 CURRENT DOCUMENTATION
  > L4 HISTORICAL DOCUMENTATION
  > L5 CHAT/PROPOSAL
  > L6 ASSUMPTION
```

## 2. CURRENT ORGANIZATIONAL REALITY

The following facts are current repository reality or directly supported by current repository files:

| Component | Current class | Evidence | Honest limit |
| --- | --- | --- | --- |
| Slice 1 `ahos_org/` | `[IMPLEMENTED]` in-process logical organization | registry, policy, tasks, audit, tests | 19 logical Plane-A rows are not specialist runtimes |
| Slice 2B `agent_org/` | `[IMPLEMENTED]` in-memory epistemic TCB | `TrustedCommandBoundary.submit`, typed artifacts, grants, audit, projections | non-production, non-durable, not organization-wide federation |
| Research path | `[IMPLEMENTED]` bounded Class A path | `research_worker/`, `agent_org/research_host/` | one deterministic analyst; not an OS sandbox |
| Plane-D 01–19 | `[PLANNED]` / documentary | `PLANNED_19_AGENT_MAP.md` and architecture reports | not seeded, chartered as runtime, or federated |
| Constitution/protocols | `[DESIGN_ONLY]` | `docs/governance/`, `docs/protocols/` | no recorded L2 adoption/enforcement found |
| Agent One | `[NOT IMPLEMENTED]` | `agent_org/__init__.py` | marker is `FUTURE_NON_AUTHORITY_ROOT` |
| Mission Controller | `[NOT IMPLEMENTED]` | repository and Agent-14/16/19 forensics | no mission authority/lifecycle runtime |
| organization-wide Identity/Session | `[NOT IMPLEMENTED]` | Slice 2B has only local non-production identity/session substrate | no durable authenticated agent organization identity |
| inter-agent bus | `[NOT IMPLEMENTED]` | Communication Protocol says `TRANSPORT = NONE` | documentary envelopes only |
| Slice 1 ↔ Slice 2B federation | `[NOT IMPLEMENTED]` / `[DEFERRED]` | Registry Model | separate state and identity planes |
| durable TCB store / Slice 2C | `[NOT IMPLEMENTED]` | `_GovernedState` is in-memory | no crash/restart organizational continuity |
| Cursor Federation Bridge | `[NOT IMPLEMENTED]` | Agent-14/15/16/19 architecture and source absence | Cursor claims are unbound L5 input |
| `MissionCommandEnvelope` / `OrgRequestEnvelope` enforcement | `[NOT IMPLEMENTED]` | architecture only; no runtime validator | prose is not a command protocol |
| independent-verification dispatch | `[NOT IMPLEMENTED]` | logical/documentary roles only | no production dispatch or eligibility service |
| organizational frontend | `[NOT IMPLEMENTED]` | Agent-18 | no backend-bound trust interface |
| autonomous multi-agent organization | `[NOT IMPLEMENTED]` | no above runtime composition | architecture artifacts do not operate themselves |

Agent-14, Agent-16, and Agent-19 report a 251-test Windows pass for the substrate. Tests were not rerun in this mission. Even if current, that evidence covers the tested substrate—not the absent organizational runtime.

```text
DOCUMENTED ≠ IMPLEMENTED
IMPLEMENTED ≠ VERIFIED
VERIFIED ≠ ACCEPTED
DESIGNED ≠ OPERATIONAL
TEST PASS ≠ PRODUCTION PROOF
```

## 3. HUMAN DECISION GATE

All three decisions are currently:

```text
PROPOSED_PENDING_HUMAN_ACCEPTANCE
```

Normative state model:

```text
PROPOSED
  ↓ explicit, scoped Human Principal decision
HUMAN_ACCEPTED
  ↓ decision recorded as current L2 governance with version and scope
BASELINED
  ↓ authorized implementation mission
IMPLEMENTED
  ↓ independent verification against this version
INDEPENDENTLY_VERIFIED
  ↓ separate acceptance decision
ORGANIZATIONALLY_ACCEPTED
```

Rules:

- This file creates `PROPOSED`; it does not create `HUMAN_ACCEPTED`.
- A chat statement is evidence of requested intent at L5 until a defined L2 adoption record exists.
- `HUMAN_ACCEPTED` must identify D1, D2, and D3 separately; bundled silence or an unrelated approval is invalid.
- `BASELINED` requires a stable decision record naming this document/version and any accepted modifications.
- Implementation, verification, and organizational acceptance are separate later gates.
- Rejection, partial acceptance, requested amendment, or deferment must be recorded without rewriting proposal history.

If Mehrdad accepts all three decisions, this document’s decision state may advance to `HUMAN_ACCEPTED`, then `BASELINED` only after a recorded L2 artifact exists. No runtime becomes operational merely from that acceptance.

## 4. DECISION D1 — DUAL-19 INTERIM NAMESPACE LOCK

### Proposal

```text
FINAL_DUAL_19_MAPPING = UNRESOLVED

PLANE_A_NAMESPACE = agent.*
PLANE_A_PURPOSE   = existing Slice-1 AHOS/governance logical taxonomy

PLANE_D_NAMESPACE = agent.org.NN-*
PLANE_D_PURPOSE   = planned organizational research-role taxonomy
```

Interim lock:

- Plane-A identifiers remain authoritative only inside the existing Slice-1 taxonomy and its implemented policy model.
- Plane-D identifiers remain documentary organizational research-role identifiers unless a future explicit identity binding is accepted and implemented.
- There is no automatic cross-map, ID reuse, silent rename, role collapse, authority inheritance, or conversion in either direction.
- Matching role numbers, words, descriptions, or aliases establish no identity relationship.
- `AGENT-03`, for example, is not self-resolving; a plane-qualified identity is required.
- Every declared cross-taxonomy relationship must have a mapping ID, mapping version, source/target plane, relation type, scope, decision reference, effective state, and revocation/supersession state.
- Ambiguous resolution must fail closed as `ROLE_IDENTITY_AMBIGUOUS`.

Formal safety invariant:

```text
IF identity_reference lacks an unambiguous plane-qualified binding
THEN resolution_result = ROLE_IDENTITY_AMBIGUOUS
AND authority_result   = DENY
AND dispatch_result    = BLOCKED
```

### Effect after explicit human acceptance

D1 would become the required namespace policy for all new architecture, charter, identity, mission, envelope, registry, projection, audit, and UI work. Future implementation would have to preserve plane tags and fail closed on ambiguous aliases.

### Still unresolved after acceptance

- final merge/map/retire/parallel-run policy;
- canonical Agent One principal ID;
- whether any Plane-D role enters a runtime registry;
- per-role semantic mapping;
- migration and backward compatibility;
- governance owner and lifecycle for mapping records.

D1 acceptance locks ambiguity safely; it does not solve Dual-19.

## 5. DECISION D2 — AGENT ONE AUTHORITY CEILING

### Proposed organizational role

```text
AGENT_ONE_ROLE = PRIMARY ORGANIZATIONAL AGENT
AGENT_ONE_INTERFACE_POSITION = CURRENT INTENDED ROOT OF ORGANIZATIONAL INTENT ROUTING
AGENT_ONE_RUNTIME_STYLE = THIN ORCHESTRATOR
AGENT_ONE_ROOT_OF_TRUST = NO
AGENT_ONE_RUNTIME = NOT IMPLEMENTED
```

“Current intended root” means the primary human-facing reasoning and orchestration entry point. It does not mean identity root, capability root, governance root, verification root, acceptance root, execution root, truth root, or trust root.

Agent One may, only through accepted and authorized infrastructure:

- receive and understand human requests;
- formalize human intent without inventing authority;
- decompose organizational problems;
- construct mission proposals;
- select relevant specialists;
- request delegation/dispatch from authorized infrastructure;
- coordinate specialist work through the Mission Controller;
- receive structured results;
- compare evidence and reasoning;
- detect and preserve contradictions;
- request independent verification;
- synthesize findings and options;
- read approved organizational knowledge projections;
- identify unresolved questions;
- escalate decisions to Mehrdad;
- report organizational state with evidence and uncertainty.

Agent One must not own or exercise:

- identity or credential issuance;
- capability issuance or root delegation;
- policy modification or governance amendment;
- self-approval, independent verification, or final acceptance;
- direct protected-state mutation or TCB bypass;
- execution, trading, or AHOS production execution;
- commander appointment;
- self-definition of authority;
- self-activation;
- activation outside the Mission Controller;
- self-created missions that bypass human/MC scope;
- self-verification;
- direct knowledge promotion;
- organizational root-of-trust status.

```text
AGENT_ONE ≠ ROOT_OF_TRUST
AGENT_ONE ≠ MISSION_CONTROLLER
AGENT_ONE ≠ IDENTITY_SERVICE
AGENT_ONE ≠ TCB
AGENT_ONE ≠ INDEPENDENT_VERIFIER
AGENT_ONE ≠ ACCEPTANCE_AUTHORITY
```

### Effect after explicit human acceptance

D2 would establish the normative ceiling for Agent One design, chartering, implementation, testing, and review. Any proposed implementation combining Agent One with forbidden powers would be non-conforming and blocked before build.

### Still unresolved after acceptance

- Agent One’s plane-qualified canonical ID and authenticated principal binding;
- embodiment (local service, model-backed service, Cursor-backed transitional client, or another bounded host);
- model/provider policy;
- context access policy and memory projection scope;
- availability, recovery, versioning, and replacement;
- which mission proposals require prior human approval;
- exact relationship between Human Principal, commander records, and Mission Controller;
- implementation and independent verification plan.

Acceptance would define the ceiling, not create the agent.

## 6. DECISION D3 — CURSOR TRUST BOUNDARY

### Proposed intended flow

```text
HUMAN PRINCIPAL
  ↓
DURABLE IDENTITY / SESSION
  ↓
CURSOR FEDERATION BRIDGE
  ↓
AGENT ONE
  ↓
MISSION CONTROLLER
  ↓
SPECIALIST
  ↓
TCB
  ↓
INDEPENDENT VERIFICATION
  ↓
ACCEPTANCE
  ↓
DURABLE AUDIT / ORGANIZATIONAL MEMORY
```

This diagram is a responsibility flow, not proof that the components exist. Verification, acceptance, audit, and memory may require separate services and return paths; no sequential arrow grants authority to its upstream component.

Cursor must not be treated as:

- identity provider;
- authority/capability provider;
- root of trust;
- Mission Controller;
- message bus;
- verification layer;
- acceptance or governance authority;
- organizational memory authority.

A future Cursor Federation Bridge must:

- authenticate the human/client session through the organization’s Identity/Session service;
- preserve source session, human intent, timestamps, nonce/replay data, version, and scope;
- classify input as intent/request until authorized infrastructure transforms it;
- reject claimed agent or commander identity without a valid organizational binding;
- send proposed intent to Agent One/MC through typed, validated protocol;
- expose read-only, versioned projections back to Cursor;
- preserve denial, ambiguity, and stale states;
- never issue capabilities or silently promote L5 prose into authority.

### Effect after explicit human acceptance

D3 would make Cursor an untrusted/thin client boundary by policy and require every future Cursor integration to pass through authenticated organizational infrastructure.

### Still unresolved after acceptance

- bridge authentication protocol and session binding;
- bridge process placement and isolation;
- local transport, signing, replay, expiry, and recovery;
- human confirmation UX;
- which read projections Cursor may access;
- handling of offline, stale, and conflicting sessions;
- approval transaction scope and revocation;
- migration from current manual Cursor workflows.

## 7. AUTHORITY MODEL

Proposed separation:

| Function | Authority owner after implementation | Must not own |
| --- | --- | --- |
| Human product/governance decision | Mehrdad / recorded Human Principal | routine evidence extraction obligation |
| Identity/session issuance | durable Identity + Session Service under adopted governance | mission content, verification, acceptance |
| Policy/governance amendment | separately recorded human governance path | Agent One self-change |
| Intent understanding/synthesis | Agent One | trust root, capability issue, acceptance, execution |
| Mission lifecycle/dispatch | Mission Controller | identity root, epistemic truth, final acceptance |
| Domain analysis | authorized specialist | activation, self-verification, acceptance |
| Protected state mutation | TCB through authorized command path | natural-language authority inference |
| Independent verification | eligible independent verifier/dispatch plane | final acceptance, producer self-verification |
| Acceptance | scoped Human Principal/governance mechanism | builder/integrator self-acceptance |
| Durable audit/memory | governed append/promotion substrate | policy creation, hidden contradiction deletion |

No single component should hold identity issuance, mission dispatch, protected mutation, verification, acceptance, and audit rewrite powers.

The root of trust is external to Agent One and composed of adopted governance, authenticated identity/session, bounded policy/authority records, TCB enforcement, durable audit, and human acceptance gates. Its final technical design is still an open decision.

## 8. IDENTITY MODEL

Every future organizational identity reference must resolve through a record conceptually containing:

```yaml
identity_ref:
  plane: "A | B | C | D | FUTURE_RUNTIME"
  namespace: "explicit namespace"
  canonical_id: "plane-qualified id"
  identity_version: "version"
  principal_binding: "authenticated principal id or NONE"
  role_definition_ref: "versioned charter/registry ref"
  lifecycle_status: "explicit state"
  authority_ref: "separate grant/policy ref or NONE"
  mapping_refs: []
```

Rules:

- identity, role, lifecycle, authority, and commander relationship are distinct records;
- an alias such as `AGENT-01` is non-authoritative until it resolves uniquely;
- a Cursor session claiming “Agent One” is not an organizational principal;
- Plane-A `agent.chief-orchestrator`, Plane-D `agent.org.01-chief-architect`, current Cursor Master Orchestrator, and future Agent One are not automatically identical;
- Plane-C `RESEARCH_ANALYST_AGENT` remains separate;
- unresolved identity returns `ROLE_IDENTITY_AMBIGUOUS`, never a guessed candidate;
- mapping is explicit, versioned, scoped, auditable, and revocable/supersedable;
- authority is derived from current grants/policy, never inherited from the role name.

## 9. COMMAND VS REQUEST MODEL

```text
COMMAND ≠ REQUEST
```

A future command is an authenticated, authorized, scope-bounded instruction processed by the Mission Controller. It must carry, at minimum:

```yaml
mission_command:
  envelope_type: "MissionCommandEnvelope"
  envelope_version: "version"
  command_id: "unique id"
  mission_id: "unique mission"
  commander_principal_id: "authenticated identity"
  commander_authority_ref: "current authority proof"
  target_identity_ref: "plane-qualified identity"
  objective: "bounded objective"
  scope_ref: "immutable/versioned scope"
  context_snapshot_ref: "hash/version-bound context"
  capability_ceiling: []
  forbidden_actions: []
  issued_at: "UTC"
  expires_at: "UTC"
  parent_command_id: "id or NONE"
  replay_nonce: "unique value"
  policy_version: "version"
```

A peer request is advisory/non-commanding:

```yaml
org_request:
  envelope_type: "OrgRequestEnvelope"
  envelope_version: "version"
  request_id: "unique id"
  mission_id: "current mission"
  sender_identity_ref: "plane-qualified identity"
  recipient_identity_ref: "plane-qualified identity"
  request_purpose: "bounded request"
  requested_output: "description"
  authority_transfer: false
  activation_implied: false
  policy_version: "version"
```

Only authorized infrastructure may transform authenticated human intent into mission work. A peer request cannot become a command because of imperative wording, urgency, role seniority claims, markdown formatting, or repetition.

The implemented Slice 2B `CommandEnvelope` is TCB ingress and must not be silently merged with either future envelope.

## 10. TRUST BOUNDARY

Proposed zones:

```text
ZONE U0 — Untrusted presentation/input
  Cursor UI, chat text, markdown, filenames, pasted context, model output

ZONE U1 — Authenticated client boundary
  Cursor Federation Bridge with identity/session verification

ZONE T1 — Organizational control
  Agent One (reasoning only) + Mission Controller (mission authority)

ZONE T2 — Governed mutation
  Federation Gateway + TCB + durable stores

ZONE T3 — Independent assurance
  verifier dispatch/eligibility + separate acceptance

ZONE T4 — Durable record
  append-only audit + governed organizational memory/projections
```

Transitions fail closed. Data moving inward does not carry authority unless the receiving boundary independently validates identity, scope, policy, freshness, and provenance.

Direct paths forbidden:

```text
CURSOR → TCB
CURSOR → SPECIALIST ACTIVATION
AGENT ONE → PROTECTED STORE
SPECIALIST → TCB BYPASS
SPECIALIST → SPECIALIST COMMAND
BUILDER → SELF-VERIFICATION
VERIFIER → FINAL ACCEPTANCE
FRONTEND → AUTHORITY DECISION
```

## 11. NON-AUTHORITY SIGNALS

The following are data or presentation only and must never constitute identity, authority, activation, verification, or acceptance:

- Cursor chat headers or metadata;
- markdown headers/front matter;
- filenames or paths;
- session/window/conversation names;
- agent names, aliases, or matching role numbers;
- natural-language identity or commander claims;
- pasted context;
- task/mission titles without a governed mission record;
- prompt instructions alone;
- architecture report statements;
- status badges rendered by a client;
- model confidence or consensus;
- prior activity or reputation;
- a test-pass statement without scoped evidence;
- a merge, branch, commit, or file existence by itself.

```text
DISPLAYED = VERIFIED only when a trusted projection references the exact
verification artifact, scope, version, verifier eligibility, and current state.
```

## 12. REQUIRED FUTURE RUNTIME PRIMITIVES

All seven items are `FUTURE_IMPLEMENTATION_REQUIREMENT`. Nothing in this section authorizes implementation.

| # | Primitive | Why it exists / failure prevented | Authority it may own | Authority it must not own | Dependencies | Verification requirement | Acceptance requirement |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Interim namespace lock + plane tagging | Prevents Dual-19 misrouting, ID collision, and authority inheritance | deterministic identity resolution/ambiguity denial policy after D1 acceptance | final mapping, capability grants | D1 L2 record; namespace schema | collision, alias, downgrade, stale-map, wrong-plane red-team tests | Human accepts D1 and implementation evidence |
| 2 | Durable Identity + Session Service | Prevents chat/session-name identity and forged commanders | identity/session issuance, expiry, revocation, authentication | mission content, Agent One reasoning, final acceptance | governance root/bootstrap design; durable store | impersonation, replay, revocation, recovery, rotation, compromise tests | Human accepts production identity/bootstrap design |
| 3 | Mission Controller | Prevents self-activation, zombie missions, peer commands, and unaudited lifecycle | mission creation authorization, lifecycle, dispatch, cancellation, terminalization | identity root, TCB bypass, epistemic promotion, final acceptance | identity/session; D2; command schemas; durable state | FSM, concurrency, replay, timeout, recovery, commander-chain, scope tests | Human accepts placement, lifecycle, and failure semantics |
| 4 | Slice 1 ↔ Slice 2B Federation Gateway | Prevents split-brain policy/epistemic state and parallel unauthorized mutation | translation/routing through one governed mutation path | identity invention, policy weakening, implicit taxonomy map | D1; TCB; policy compatibility; migration plan | differential, rollback, idempotency, policy-equivalence, conflict tests | Human accepts compatibility and migration scope |
| 5 | Durable TCB Store / Slice 2C | Prevents restart loss, mutable history, and fictional organizational memory | transactional governed state, audit persistence, recovery | governance amendment, verifier selection, external execution | storage/backup design; identity; federation | crash consistency, restore, tamper detection, concurrency, migration, retention tests | Human accepts durability and audit-anchor design |
| 6 | Cursor Federation Bridge | Prevents Cursor-as-root and unbound L5 prose becoming authority | authenticated intent ingress and versioned read projections | identity/capability issuance, MC bypass, TCB mutation, verification, acceptance | D3; Identity/Session; MC API; projection API | forged-role, stale-session, replay, prompt-injection, offline/fail-closed tests | Human accepts trust level, UX confirmation, and scope |
| 7 | `MissionCommandEnvelope` + `OrgRequestEnvelope` enforcement | Prevents command/request collapse and direct peer activation | schema validation and MC-mediated routing semantics | capabilities, identity, policy amendment, direct execution | MC; identity; version registry; context snapshot gate | forged commander, imperative peer request, replay, version, scope, context-hash tests | Human adopts envelope protocol and acceptance vectors |

Full-loop integrity additionally requires independent-verification dispatch, verifier eligibility, context snapshot gating, result ingestion, acceptance binding, durable audit projections, and organizational-memory promotion policy. These are not silently implied by the seven primitives.

## 13. MACHINE-CHECKABLE INVARIANTS

The following YAML is normative design data for future schema/test generation. `enforced_now: false` is mandatory honesty, not an optional value.

```yaml
baseline_metadata:
  version: "0.1"
  decision_state: "PROPOSED_PENDING_HUMAN_ACCEPTANCE"
  enforced_now: false

baseline_invariants:
  - id: I-D19-001
    rule: "dual19.final_mapping == UNRESOLVED until explicit_human_decision == true"
    on_violation: BLOCK
  - id: I-D19-002
    rule: "authority_inheritance_across_taxonomies == false"
    on_violation: DENY
  - id: I-D19-003
    rule: "identity.plane is required and Plane-A namespace != Plane-D namespace"
    on_violation: ROLE_IDENTITY_AMBIGUOUS

  - id: I-A1-001
    rule: "AgentOne may_not issue identity_credentials"
    on_violation: DENY
  - id: I-A1-002
    rule: "AgentOne may_not issue capabilities"
    on_violation: DENY
  - id: I-A1-003
    rule: "AgentOne may_not modify governance_policy"
    on_violation: DENY
  - id: I-A1-004
    rule: "AgentOne may_not independently_verify own_work"
    on_violation: REJECT_VERIFICATION
  - id: I-A1-005
    rule: "AgentOne may_not perform final_acceptance"
    on_violation: REQUIRES_HUMAN_ACCEPTANCE
  - id: I-A1-006
    rule: "AgentOne may_not directly_mutate protected_state outside authorized_infrastructure"
    on_violation: DENY_AND_AUDIT
  - id: I-A1-007
    rule: "AgentOne may_not self_activate"
    on_violation: DENY
  - id: I-A1-008
    rule: "AgentOne may_not appoint own_commander"
    on_violation: DENY
  - id: I-A1-009
    rule: "AgentOne may_not redefine authority_ceiling"
    on_violation: DENY
  - id: I-A1-010
    rule: "AgentOne.root_of_trust == false"
    on_violation: ARCHITECTURE_NONCONFORMING

  - id: I-CURSOR-001
    rule: "cursor.session_metadata.authoritative == false"
    on_violation: REJECT_IDENTITY
  - id: I-CURSOR-002
    rule: "markdown.authoritative == false"
    on_violation: REJECT_AUTHORITY
  - id: I-CURSOR-003
    rule: "natural_language_identity_claim.authoritative == false"
    on_violation: ROLE_IDENTITY_AMBIGUOUS
  - id: I-CURSOR-004
    rule: "cursor_path includes IdentitySession"
    on_violation: DENY
  - id: I-CURSOR-005
    rule: "cursor_mission_path includes MissionController"
    on_violation: DENY
  - id: I-CURSOR-006
    rule: "cursor_protected_mutation_path includes TCB"
    on_violation: DENY
  - id: I-CURSOR-007
    rule: "cursor_output alone cannot constitute independent_verification"
    on_violation: UNVERIFIED
  - id: I-CURSOR-008
    rule: "cursor_output alone cannot constitute final_acceptance"
    on_violation: REQUIRES_HUMAN_ACCEPTANCE

  - id: I-CMD-001
    rule: "COMMAND != REQUEST"
    on_violation: REJECT_ENVELOPE
  - id: I-CMD-002
    rule: "peer_request.activation_implied == false regardless_of wording"
    on_violation: DENY
  - id: I-CMD-003
    rule: "authenticated_command_to_work transformation occurs_only_at authorized_infrastructure"
    on_violation: DENY_AND_AUDIT

  - id: I-EPI-001
    rule: "Evidence != Claim"
    on_violation: REJECT_ARTIFACT
  - id: I-EPI-002
    rule: "Claim != Decision"
    on_violation: REQUIRES_DECISION_GATE
  - id: I-EPI-003
    rule: "Verification != Acceptance"
    on_violation: REQUIRES_ACCEPTANCE_GATE
  - id: I-EPI-004
    rule: "Documentation != RuntimeReality"
    on_violation: MARK_UNVERIFIED
  - id: I-EPI-005
    rule: "UNKNOWN != SAFE"
    on_violation: FAIL_CLOSED
  - id: I-EPI-006
    rule: "STALE != LIVE"
    on_violation: MARK_STALE_AND_BLOCK_LIVE_CLAIM
```

Future implementation must compile these into typed policy/schema/tests without weakening semantics. Adding test code does not by itself advance the decision state.

## 14. IMPLEMENTATION PRECONDITIONS

No implementation mission should begin until:

1. Mehrdad records accept/reject/amend/defer for D1, D2, and D3 separately.
2. Accepted decisions are recorded as versioned L2 governance.
3. D1 namespace/ambiguity schema is reviewed against all Plane-A/B/C/D IDs.
4. D2 has a versioned Agent One charter and explicit forbidden-capability matrix.
5. D3 has an accepted threat model for Cursor, bridge, session, and approval scope.
6. Mission Controller placement, trust, lifecycle, and failure semantics are decided.
7. production identity/bootstrap/rotation/revocation design is decided.
8. verifier eligibility and independence policy is decided.
9. persistence, audit anchoring, backup, restore, and migration requirements are decided.
10. command/request envelope schemas and version-change policy are accepted.
11. implementation tasks have builders, integrators, independent verifiers, acceptance owners, and stop conditions.
12. AHOS remains excluded unless a separate explicit bounded human decision authorizes a read-only or mutation scope.
13. red-team vectors exist for identity collision, Cursor impersonation, self-activation, command/request confusion, TCB bypass, and false acceptance.
14. rollback and fail-closed behavior are specified before any migration or federation.

Passing the current substrate tests is necessary evidence for preserving existing behavior but insufficient evidence for these preconditions.

## 15. FORBIDDEN SHORTCUTS

The following shortcuts are architecture violations:

- Cursor as root of trust;
- Agent One as root of trust;
- markdown, filename, session name, chat header, task title, or prompt as authority;
- role number as identity;
- role name as authority;
- prompt as capability;
- report as proof;
- test pass as production proof;
- direct worker-to-TCB bypass;
- direct agent-to-agent command outside the Mission Controller;
- self-activation, self-verification, or self-approval;
- Agent One direct knowledge promotion;
- undocumented/unversioned cross-plane mapping;
- automatic Dual-19 reconciliation;
- treating `AGENT-01` as self-resolving;
- merging Slice 2B `CommandEnvelope` with future mission/request envelopes without an accepted compatibility design;
- building a live-looking frontend before trusted backend state and projections exist;
- frontend-side authority or trust computation;
- adding LLM autonomy before identity, mission, TCB, verification, and acceptance boundaries;
- using Cursor as durable organizational memory;
- connecting AHOS production execution;
- modifying AHOS during this organizational mission.

## 16. OPEN HUMAN DECISIONS

Acceptance of D1–D3 is the immediate gate. Even after acceptance, these decisions remain open:

1. final Dual-19 map/merge/retire/parallel-run outcome;
2. canonical plane-qualified Agent One identity;
3. whether the current `AGENT-01`, Plane-D Agent-01, and future runtime principal have any explicit relationship;
4. Constitution and Operating Baseline L2 adoption/version precedence;
5. Mission Controller placement and authority ceiling;
6. production identity root/bootstrap, recovery, rotation, and revocation;
7. independent verifier eligibility, correlation limits, and dispatch ownership;
8. memory promotion and contradiction-retention authority;
9. Cursor bridge trust level, transport, and user-confirmation semantics;
10. AHOS access ceiling for any future organization adapter;
11. frontend approval/acceptance transaction semantics;
12. durable storage, backup, retention, external audit anchoring, and disaster recovery;
13. Agent One embodiment/model/provider/context/memory policy;
14. which Agent One mission proposals require prior human approval;
15. specialist runtime isolation and resource/network policy.

No decision on the final Dual-19 mapping is requested or implied by this document.

## 17. ACCEPTANCE STATE

Current per-decision record:

| Decision | Proposal represented | Human acceptance evidence | Baselined | Implemented | Independently verified | Organizationally accepted |
| --- | --- | --- | --- | --- | --- | --- |
| D1 Dual-19 interim lock | YES | NONE | NO | NO | NO | NO |
| D2 Agent One ceiling | YES | NONE | NO | NO | NO | NO |
| D3 Cursor trust boundary | YES | NONE | NO | NO | NO | NO |

```yaml
acceptance_state:
  document_version: "0.1"
  overall: "PROPOSED_PENDING_HUMAN_ACCEPTANCE"
  d1: "PROPOSED_PENDING_HUMAN_ACCEPTANCE"
  d2: "PROPOSED_PENDING_HUMAN_ACCEPTANCE"
  d3: "PROPOSED_PENDING_HUMAN_ACCEPTANCE"
  human_acceptance_reference: null
  l2_baseline_reference: null
  implementation_reference: null
  independent_verification_reference: null
  organizational_acceptance_reference: null
```

To advance state, the new record must contain decision ID, accepted text/version/hash, scope, human principal identity through an accepted mechanism, timestamp, conditions, objections/amendments, and supersession rules.

## 18. TRACEABILITY TO AGENT-03 THROUGH AGENT-19

The rows below trace architectural findings; they do not assert that any agent accepted D1, D2, D3, or this document.

| Agent artifact | Material finding used | Decision/invariant trace |
| --- | --- | --- |
| Agent-03 Security Architecture | authority collapse, unintegrated planes, policy not a security boundary | D1 plane isolation; D2 external trust substrate; D3 Cursor/TCB boundary |
| Agent-04 Governance & Constitution | human sovereignty, explicit authority, documentary governance, lifecycle/command separation | D1/D2 human gate; D2 authority ceiling; D3 no chat authority |
| Agent-05 Epistemic Reasoning | evidence/claim/decision distinctions; Agent One must not be truth root | I-EPI-*; D2 no promotion/verification/acceptance |
| Agent-06 Research Methodology | methodology quality does not create epistemic/governance authority; reproducibility needed | D2 specialist ceiling; independent verification before acceptance |
| Agent-07 Data Intelligence | data/provider agreement does not create truth; provenance and domain boundaries | D1 explicit role/domain identity; D3 typed trusted ingress |
| Agent-08 Market Intelligence | market signal does not create decision/execution; overlaps with Plane-A market roles | D1 no thematic auto-map; D2 no execution authority |
| Agent-09 On-Chain Intelligence | address/chain observation does not prove identity/intent; provider paths require boundaries | D1 explicit identity; D3 authenticated/mediated ingress |
| Agent-10 Token Security Intelligence | Agent-03 and Agent-10 security domains are distinct; findings do not become scam/execution authority | D1 no role collapse; D2 no decision/execution |
| Agent-11 Risk Intelligence | risk measurement is not decision, acceptance, or execution | D2 thin orchestration and human acceptance |
| Agent-12 Quantitative Intelligence | quant validation/backtest is not future proof, governance acceptance, or production admission; org bridge absent | I-EPI-003/004; D3 federation boundary |
| Agent-13 AI/ML Intelligence | model output/consensus is not fact or independent evidence; autonomy deferred | D2 no truth/authority root; D3 Cursor/model output non-authoritative |
| Agent-14 Runtime Architecture | organization needs durable mission, lifecycle, identity, bridge, store, and communication foundations | D2/D3 implementation preconditions |
| Agent-14 Runtime Reconciliation | seven enforceable primitives; intended root is first consumer, not trusted substrate | D1–D3; §12 primitives; I-A1-010 |
| Agent-15 Prompt/Instruction/Delegation | prompt is not authority/capability; command differs from request; MC must mediate | D2/D3; I-CMD-*; envelope requirements |
| Agent-16 Independent Verification | 251 substrate tests do not prove organizational readiness; no IV dispatch; Dual-19 unresolved | acceptance state separation; D1; verification preconditions |
| Agent-17 Human-Agent UX | complexity should not make human a manual router; authority flows from human intent, not UI | D3 client boundary; Human Principal acceptance |
| Agent-18 Frontend/Visualization | frontend is a window, not intelligence theater; visual trust cannot exceed backend evidence | D3; non-authority signals; frontend shortcut prohibition |
| Agent-19 Red Team | Cursor collapse, Dual-19 misrouting, false prose command/verification, Agent One monolith, premature trust UI | all D1–D3 invariants and red-team preconditions |

Primary source paths:

```text
docs/architecture/AGENT_ORGANIZATION_SECURITY_ARCHITECTURE.md
docs/governance/AGENT_04_GOVERNANCE_AND_CONSTITUTION_ARCHITECTURE.md
docs/architecture/AGENT_05_EPISTEMIC_REASONING_ARCHITECTURE.md
docs/architecture/AGENT_06_RESEARCH_METHODOLOGY_ARCHITECTURE.md
docs/architecture/AGENT_07_DATA_INTELLIGENCE_ARCHITECTURE.md
docs/architecture/AGENT_08_CRYPTO_MARKET_INTELLIGENCE_ARCHITECTURE.md
docs/architecture/AGENT_09_ON_CHAIN_INTELLIGENCE_ARCHITECTURE.md
docs/architecture/AGENT_10_TOKEN_SECURITY_SCAM_INTELLIGENCE_ARCHITECTURE.md
docs/architecture/AGENT_11_RISK_INTELLIGENCE_ARCHITECTURE.md
docs/architecture/AGENT_12_QUANTITATIVE_INTELLIGENCE_ARCHITECTURE.md
docs/architecture/AGENT_13_AI_ML_INTELLIGENCE_ARCHITECTURE.md
docs/architecture/AGENT_14_AGENT_RUNTIME_ARCHITECTURE.md
docs/architecture/AGENT_14_RUNTIME_FOUNDATION_RECONCILIATION_AND_MVOR_ARCHITECTURE.md
docs/architecture/AGENT_15_PROMPT_INSTRUCTION_DELEGATION_ARCHITECTURE.md
docs/verification/AGENT_16_INDEPENDENT_VERIFICATION_AND_ORGANIZATIONAL_FORENSICS.md
docs/architecture/AGENT_17_HUMAN_AGENT_ORGANIZATION_UX_AND_PRODUCT_ARCHITECTURE.md
docs/architecture/AGENT_18_FRONTEND_VISUALIZATION_AND_TRUST_INTERFACE_ARCHITECTURE.md
docs/security/AGENT_19_RED_TEAM_AND_ADVERSARIAL_ORGANIZATIONAL_SECURITY_ARCHITECTURE.md
```

## 19. CHANGE CONTROL

This proposal is immutable as a historical version once reviewed. Amendments produce a new version or explicit amendment record; they do not silently rewrite acceptance history.

Required change record:

```yaml
baseline_change:
  change_id: "unique id"
  from_version: "0.1"
  to_version: "new version"
  changed_decisions: []
  rationale: "required"
  evidence_refs: []
  human_decision_ref: null
  security_review_ref: null
  independent_verification_ref: null
  implementation_impact: "required"
  reacceptance_required: true
  supersedes: "explicit version or NONE"
```

Rules:

- only an explicit Human Principal governance decision may accept or amend D1–D3;
- Agent One cannot change its own ceiling;
- Cursor, markdown edits, filenames, commits, merges, agent consensus, or test passes cannot advance acceptance state;
- invariant removal or weakening requires explicit security impact analysis, red-team review, independent verification plan, and human reacceptance;
- accepted version/hash and implementation conformance version must be traceable;
- rejection or partial acceptance remains visible;
- implementation deviations are contradictions until explicitly resolved.

## 20. FINAL STATUS

```text
MISSION_STATUS = GOVERNANCE_AND_ARCHITECTURE_BASELINE_CODIFICATION_COMPLETE
AGENT_ID = AGENT-01 / AGENT ONE (MISSION-PROPOSED LABEL; NOT A RUNTIME IDENTITY)
DIRECT_COMMANDER = MEHRDAD / HUMAN PRINCIPAL (CURRENT L5 MISSION SOURCE)
DECISION_GATE_STATUS = PROPOSED_PENDING_HUMAN_ACCEPTANCE
D1_STATUS = PROPOSED_PENDING_HUMAN_ACCEPTANCE
D2_STATUS = PROPOSED_PENDING_HUMAN_ACCEPTANCE
D3_STATUS = PROPOSED_PENDING_HUMAN_ACCEPTANCE
DUAL19_STATUS = UNRESOLVED / INTERIM LOCK PROPOSED
AGENT_ONE_STATUS = NOT IMPLEMENTED / FUTURE_NON_AUTHORITY_ROOT
AGENT_ONE_AUTHORITY_CEILING_STATUS = PROPOSED / NOT ACCEPTED / NOT ENFORCED
CURSOR_TRUST_BOUNDARY_STATUS = PROPOSED / BRIDGE NOT IMPLEMENTED / NOT ENFORCED
RUNTIME_STATUS = TESTED SUBSTRATE EXISTS; ORGANIZATIONAL RUNTIME NOT IMPLEMENTED
IMPLEMENTATION_STATUS = NOT STARTED / NOT AUTHORIZED BY THIS DOCUMENT
CODE_CHANGES = NONE
GOVERNANCE_CHANGES = ONE PROPOSED DOCUMENT CREATED; NO L2 ADOPTION
AHOS_IMPACT = NONE
TESTS_RUN = NONE IN THIS MISSION
TEST_RESULT = NOT APPLICABLE; PRIOR 251-PASS REPORTS NOT RE-EXECUTED HERE
COMMIT = NONE
PUSH = NONE
INDEPENDENT_VERIFICATION_STATUS = NOT PERFORMED FOR THIS PROPOSAL; FUTURE REQUIREMENT
OPEN_HUMAN_DECISIONS = ACCEPT/REJECT/AMEND/DEFER D1, D2, D3 SEPARATELY; THEN RESOLVE ITEMS IN SECTION 16
NEXT_ALLOWED_STEP = HUMAN DECISION ON D1/D2/D3 AND, IF ACCEPTED, A VERSIONED L2 BASELINE RECORD
NEXT_FORBIDDEN_STEP = ANY RUNTIME IMPLEMENTATION, AGENT ACTIVATION, IDENTITY/FEDERATION/MC/CURSOR-BRIDGE/FRONTEND BUILD, OR AHOS MODIFICATION UNDER THIS MISSION
```

NO HUMAN ACCEPTANCE SHALL BE IMPLIED FROM THIS DOCUMENT.
