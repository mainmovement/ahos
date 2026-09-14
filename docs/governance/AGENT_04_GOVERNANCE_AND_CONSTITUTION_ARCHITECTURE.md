# Agent Organization — Governance & Constitution Architecture

```text
DOCUMENT_ID      = AGENT_04_GOVERNANCE_AND_CONSTITUTION_ARCHITECTURE
MISSION_ID       = TASK-20260914-004
VERSION          = 0.1.0
STATUS           = PROPOSED / READ_ONLY_GOVERNANCE_ARCHITECTURE
AUTHORITY        = NONE CREATED
ENFORCEMENT      = NOT_IMPLEMENTED
RUNTIME_EFFECT   = NONE
AHOS_EFFECT      = NONE
AGENT_ID         = AGENT-04 (agent.org.04-governance-constitution — documentary)
DIRECT_COMMANDER = MASTER ORCHESTRATOR
LIFECYCLE        = IDLE / DORMANT / WAITING_FOR_NEW_COMMAND (post-mission)
DUAL_19          = UNRESOLVED
AGENT_ONE        = NOT_IMPLEMENTED / FUTURE_NON_AUTHORITY_ROOT
```

This document is a **governance and constitutional architecture artifact**. It does not implement controls, adopt governance, grant authority, or modify runtime behavior. Facts cite repository evidence with explicit status labels. Proposals are labeled `[PROPOSED]`.

**Critical honesty constraint:**

```text
DOCUMENTED CONTROL ≠ ENFORCED CONTROL
POLICY ≠ SECURITY BOUNDARY
DOCUMENTATION ≠ PROOF
AGENT EXISTENCE ≠ AGENT ACTIVATION
AGENT ACTIVATION ≠ AGENT AUTHORITY
AGENT AUTHORITY ≠ EXECUTION AUTHORITY
```

---

## 1. Executive Summary

`[VERIFIED]` The AHOS Agent Organization (`ahos-agent-org`) is an independent control-plane workspace with three implemented but **separate** foundations:

1. **Slice 1** (`ahos_org/`) — in-process logical registry (19 canonical roles), fail-closed symbolic authorization, task state machine, audit hash chain.
2. **Slice 2B** (`agent_org/`) — in-memory Trusted Command Boundary (TCB), epistemic artifact model, scoped grants/delegation (max depth 3), non-production session stub.
3. **Research path** (`research_worker/` + `agent_org/research_host/`) — one bounded Class A deterministic analyst with process isolation and JSON IPC firewalls.

`[VERIFIED]` Governance today is predominantly **documentary** (Constitution v0.1.0, protocols, planned maps) with **partial in-process enforcement** in Slice 1 and Slice 2B. The Cursor Control-Plane (Human Principal → Master Orchestrator → specialist agents in chat) operates at L5 with **no runtime binding** to Slice 1/2B authorization.

`[VERIFIED]` **Dual-19** remains unresolved: Plane A (`agent.*` in `ahos_org/registry.py`) and Plane D (`agent.org.NN-*` in `PLANNED_19_AGENT_MAP.md`) are competing taxonomies. This report records the conflict; it does not merge, rename, or select a canonical taxonomy.

`[VERIFIED]` **Agent One** is not implemented (`AGENT_ONE_STATUS = FUTURE_NON_AUTHORITY_ROOT`). Slice 1 contains a logical `agent.chief-orchestrator` role — this is **not** Agent One and must not be silently merged.

**Primary governance objective:** ensure authority remains **bounded, auditable, separated, revocable, and subordinate to the human principal** (Mehrdad), preventing any agent — including the Master Orchestrator or a future Agent One — from becoming sovereign through technical capability, documentation, or orchestration convenience.

**Current governance posture:** `[PARTIALLY_VERIFIED]` — strong constitutional vocabulary and fail-closed policy design; weak enforcement of lifecycle, activation, command authenticity, and inter-plane federation at the Cursor Control-Plane layer.

**This document's class:** `[PROPOSED]` architectural recommendations requiring human adoption (L2) before they become organizational law. Code denies in L0 remain stronger until explicitly changed through governed code paths.

---

## 2. Agent-04 Identity

| Field | Value |
| --- | --- |
| `AGENT_ID` | `AGENT-04` |
| Documentary plane-D ID | `agent.org.04-governance-constitution` |
| Role | Governance & Constitution Architect |
| Mission | TASK-20260914-004 — constitutional and governance system design |
| Direct commander | MASTER ORCHESTRATOR |
| Parent | MASTER ORCHESTRATOR |
| Human principal | MEHRDAD |
| Authority class (this mission) | READ, ANALYZE, PROPOSE only |
| Forbidden (this mission) | APPROVE, PROMOTE, EXECUTE, MODIFY runtime, DELEGATE, implement Agent One |
| Lifecycle (post-mission) | IDLE / DORMANT / WAITING_FOR_NEW_COMMAND |
| Activation rule | Explicit command from direct commander only; registration ≠ activation |

Agent-04 is a **design specialist**, not a governance authority, not Agent One, not the Master Orchestrator, and not the owner of truth.

---

## 3. Command Chain

### 3.1 Current chain (Cursor Control-Plane)

```text
MEHRDAD (Human Principal — ultimate sovereignty)
    ↓
MASTER ORCHESTRATOR (coordination layer — L5 operational, not constitutional sovereign)
    ↓
SPECIALIST AGENTS (e.g., AGENT-03 Security, AGENT-04 Governance, future 01–19)
```

`[VERIFIED]` This chain exists in chat/worker launch practice. `[UNVERIFIED]` as runtime-enforced identity binding.

### 3.2 Relationship types (must not be collapsed)

| Relationship | Class | Authority type | Current enforcement |
| --- | --- | --- | --- |
| Human Principal → any agent | Sovereignty | Ultimate command, override, revocation | `[DOCUMENTED]` Constitution §3.1; `[NOT_IMPLEMENTED]` as authenticated command channel |
| Master Orchestrator → specialist | Command (delegated) | Task formalization, specialist selection, coordination | `[L5]` chat activation only |
| Specialist → Master Orchestrator | Reporting | Informational | `[DESIGN_ONLY]` response protocol |
| Specialist → specialist (peer) | Advisory / review | No command authority by default | `[PROPOSED]` |
| Independent verifier → producer | Verification-only | Challenge, verify, reject evidence — not command | `[DESIGN_ONLY]` supervision protocol |
| Commander → subordinate | Command | Scoped mission activation within delegated ceiling | `[PROPOSED]` — no mission controller runtime |
| Parent → child | Lineage / accountability | Parent owns reporting chain; parent ≠ automatic approver | `[PROPOSED]` — charter field not in `AgentRecord` |
| Coordinator (orchestrator) | Coordination | May synthesize; may not approve or execute | `[DESIGN_ONLY]` Constitution §3.1, Agent One definition |

### 3.3 Forbidden command-chain mutations

`[PROPOSED]` constitutional prohibitions:

- No agent may appoint itself commander.
- No subordinate may appoint another commander without human authorization.
- No peer may activate another peer without commander authorization.
- No specialist may change its own reporting line.
- No orchestrator may become constitutional sovereign by title or convenience.

---

## 4. Lifecycle Governance

### 4.1 Agent lifecycle states (proposed unified model)

Slice 1 uses `GovernanceStatus`: `REGISTERED`, `ACTIVE`, `SUSPENDED`, `RETIRED`.  
Slice 2B uses `IdentityStatus`: `ACTIVE`, `SUSPENDED`, `REVOKED`.  
Cursor Control-Plane uses mission-text lifecycle (this mission).

`[PROPOSED]` unified lifecycle vocabulary (not yet implemented as a single FSM):

```text
REGISTERED
    ↓
IDLE / AVAILABLE / DORMANT
    ↓
ACTIVATION_REQUESTED
    ↓
AUTHORIZED
    ↓
ACTIVE
    ↓
COMPLETED | FAILED | TIMEOUT | CANCELLED
    ↓
IDLE / DORMANT

Side states (from any non-terminal):
    BLOCKED — missing input/authority; may return to ACTIVATION_REQUESTED or IDLE
    SUSPENDED — policy/incident hold; requires supervisor restore
    QUARANTINED — suspected compromise; stronger review than SUSPENDED
    RETIRED — terminal; no reactivation without new registration
```

### 4.2 Critical lifecycle principles

```text
Agent existence ≠ Agent activation
Agent activation ≠ Agent authority
Agent authority ≠ Execution authority
Mission completion ≠ Automatic next mission
Conversation alive ≠ Mission alive
```

`[VERIFIED]` Slice 1 seeds 19 canonical agents at `MaturityLevel.REGISTERED` with `enabled=True`. Registration does **not** mean operational specialists exist (`AGENT_REGISTRY_MODEL.md`).

`[VERIFIED]` Slice 1 `MINIMUM_MATURITY_FOR_ALLOW = 2` (IMPLEMENTED) prevents REGISTERED agents from receiving ALLOW for execution-class actions.

### 4.3 Transition authorization matrix

| Transition | Initiator | Authorizer | Preconditions | Audit required |
| --- | --- | --- | --- | --- |
| → REGISTERED | Human / governance | Human | Unique ID, role, commander, authority ceiling defined | Registration event |
| REGISTERED → IDLE | System | — | Valid registration | — |
| IDLE → ACTIVATION_REQUESTED | Commander | — | Valid mission ID + scope; agent not quarantined/retired | Activation request |
| ACTIVATION_REQUESTED → AUTHORIZED | — | Commander + mission controller; human if HIGH/CRITICAL risk | Scope within authority ceiling; grants derivable | Authorization decision |
| AUTHORIZED → ACTIVE | Agent / controller | — | Explicit start signal | Activation timestamp |
| ACTIVE → COMPLETED | Agent (result) | Commander acceptance (informational) | Scope satisfied or explicitly closed | Result + deactivation |
| ACTIVE → FAILED | Agent / controller | — | Failure recorded | Failure event |
| ACTIVE → TIMEOUT | Controller | — | Timeout in mission spec | Timeout event |
| ACTIVE → CANCELLED | Commander or Human | Human if in-progress external effect | Cancellation token | Cancel event |
| * → BLOCKED | Agent / controller | — | Missing dependency documented | Blocker record |
| * → SUSPENDED | Human / supervisor | Human | Incident or policy trigger | Suspend event |
| * → QUARANTINED | Security supervisor | Human + security review | Suspected compromise class | Quarantine record |
| QUARANTINED → ACTIVE | — | Human + security review (stronger than normal) | Root cause addressed | Reactivation audit |
| COMPLETED/FAILED → ACTIVE | Commander only | Mission controller + human if repeated failure | **New** mission ID + **new** scope | **Prohibited:** old mission resurrection |
| * → RETIRED | Human | Human | No pending missions | Retirement record |

`[IMPLEMENTED]` partial: Slice 1 `AgentRegistry.disable()` sets `governance_status=SUSPENDED`, `enabled=False`.  
`[NOT_IMPLEMENTED]`: QUARANTINED state, activation FSM, mission controller, timeout enforcement at org runtime.

### 4.4 Terminal state rules

After COMPLETED, FAILED, TIMEOUT, CANCELLED, RETIRED:

```text
LIFECYCLE_STATUS = IDLE / DORMANT / WAITING_FOR_NEW_COMMAND
```

No automatic continuation. No self-reactivation. No peer activation. Next mission requires new explicit command, new Task/Mission ID, new scope, explicit activation.

---

## 5. Human Sovereignty

### 5.1 Ultimate human authority

`[DOCUMENTED]` Constitution §3.1: Mehrdad (human principal) holds ultimate sovereignty over the Agent Organization.

| Power | Holder | Agent may not assume |
| --- | --- | --- |
| Constitutional adoption / amendment | Human | Agents may propose only |
| AHOS production access | Human explicit decision | Never by agent inference |
| Agent creation / retirement | Human | No self-creation as authority |
| Authority grant / revocation | Human (+ governed code) | No self-grant |
| Emergency override | Human | Fail-closed until human acts |
| Mission cancellation | Human or commander (human for external effect) | No agent veto of human cancel |
| Quarantine / restore | Human (+ security review for restore) | No self-clearance |
| Dual-19 resolution | Human | `[UNRESOLVED]` — HUMAN_DECISION_REQUIRED |
| Agent One operationalization | Human | `[UNRESOLVED]` — multiple questions open |

### 5.2 Human message ≠ automatic authority

```text
HUMAN MESSAGE (L5) ≠ AUTOMATIC AUTHORITY GRANT (L2)
CHAT ACTIVATION ≠ RUNTIME AUTHORIZATION
```

A human or commander message in Cursor/chat is **evidence of intent** until recorded as L2 governance decision or reflected in L0 code/configuration through governed change control.

### 5.3 Emergency intervention

`[PROPOSED]`:

- Human may suspend, quarantine, revoke, or cancel **any** agent or mission at any time.
- Emergency constitutional amendment (see §13) requires human initiation; agents may not invoke emergency paths autonomously.
- Emergency override is **logged** but logging does not substitute for post-incident human review.

### 5.4 Accountability

Humans remain accountable for decisions they approve. Agents produce recommendations and evidence; they do not absorb human accountability through synthesis or automation.

---

## 6. Authority Model

### 6.1 Separated concepts (non-negotiable)

These are **distinct** and must not be treated as synonyms:

| Concept | Definition | Collapse risk |
| --- | --- | --- |
| **Identity** | Stable principal/agent ID in a registry plane | Identity forgery → unauthorized commands |
| **Role** | Organizational function label | Role title ≠ authority (Constitution §6) |
| **Capability** | Token permitting a class of operation on a resource | Capability ≠ approval |
| **Authority** | Derived right to cause a governed state transition | Authority ≠ execution |
| **Activation** | Permission to begin work on a scoped mission | Activation ≠ standing authority |
| **Command** | Directed instruction with scope, ID, and issuer | Command ≠ chat message unless bound |
| **Approval** | Binding acceptance of a consequential transition | Approval ≠ recommendation |
| **Verification** | Independent assessment of evidence/result | Verification ≠ promotion |
| **Promotion** | Elevation of knowledge/policy/agent maturity | Promotion ≠ truth |
| **Execution** | Causing external or protected state change | Execution requires separate gate |

### 6.2 Authority classes (Constitution vocabulary)

```text
READ      ANALYZE     PROPOSE     REQUEST     VERIFY
APPROVE   PROMOTE     EXECUTE     MODIFY      DELEGATE
```

Default for planned 01–19 specialists until chartered and granted:

```text
AUTHORITY_CLASS = NONE beyond READ, ANALYZE, PROPOSE, REQUEST
Forbidden: APPROVE, PROMOTE, EXECUTE (external), MODIFY (AHOS/protected), DELEGATE
VERIFY: only if independently assigned; never final self-verification
```

### 6.3 Plane mapping (do not merge silently)

| Concept | Slice 1 (`ahos_org`) | Slice 2B (`agent_org`) | Cursor Control-Plane |
| --- | --- | --- | --- |
| Identity | `agent.*` in `AgentRecord` | `principal.*` in TCB | Chat agent names (unbound) |
| Capability | string tokens in policy | `Capability` enum | Tool access (IDE-level) |
| Authorization | `GovernanceEngine.authorize` | `TrustedCommandBoundary.submit` | None |
| Task scope | `TaskRecord` | TCB task scope | Mission text |
| Maturity | `MaturityLevel` 0–5 | Not mapped | Not enforced |

`DEFERRED_IMPLEMENTATION`: unified authority model across planes (`AGENT_REGISTRY_MODEL.md`).

### 6.4 Minimum Necessary Authority (constitutional principle)

`[PROPOSED]`:

- Authority must be **explicit, bounded, revocable, time/scoped, auditable, non-self-expandable**.
- Grants expire (`[IMPLEMENTED]` in Slice 2B `CapabilityGrant.expires_at`).
- Delegation attenuates (`[IMPLEMENTED]` `MAX_DELEGATION_DEPTH = 3`).
- No agent receives standing APPROVE/PROMOTE/EXECUTE without human-governed grant.

---

## 7. Chain of Command

### 7.1 Definitions

| Term | Meaning |
| --- | --- |
| **Parent** | Lineage owner for accountability; receives escalations by default |
| **Commander** | May issue activation commands within delegated ceiling |
| **Reporting line** | Information flow path; not automatically bidirectional command |
| **Subordinate** | Agent under a commander's activation authority |
| **Peer** | Same commander level; no default command over each other |
| **Coordinator** | Master Orchestrator / future Agent One — synthesizes, does not sovereignly decide |
| **Reviewer** | Independent assessment; no command authority |
| **Independent verifier** | Verification-only; cannot approve or execute |

### 7.2 Master Orchestrator position

The Master Orchestrator is **coordinator**, not constitutional sovereign:

**MAY:** understand requests, formalize tasks, select specialists, create recommendations, coordinate analysis, compare results, detect contradictions, request independent verification, synthesize results, report to Mehrdad.

**MUST NOT automatically become:** source of truth, unilateral verifier, unilateral approver, unrestricted executor, constitutional sovereign, production authority.

`[VERIFIED]` Slice 1 `agent.chief-orchestrator` has only `orchestrate.plan`, `task.propose`, `task.inspect`, `policy.inspect` — no approve/promote/execute tokens.

### 7.3 Anti-collapse rule

No single component may simultaneously be:

```text
source of truth + commander + verifier + approver + executor + policy modifier
```

This is the primary **authority collapse** risk (also analyzed in Agent 03 security architecture as context, not binding governance).

---

## 8. Mission Governance

### 8.1 Mission identity requirements

Every mission must have:

```text
MISSION_ID / TASK_ID     — unique, non-reusable for new scope
EXPLICIT_COMMAND         — from authorized commander or human
SCOPE                    — bounded deliverables and exclusions
CONSTRAINTS              — forbidden actions, planes, resources
TIMEOUT                  — optional but recommended
AUTHORITY_BOUNDARY       — max authority class for this mission
ACTIVATION_RECORD        — who authorized, when
```

### 8.2 Mission lifecycle (aligned with Slice 1 tasks)

`[IMPLEMENTED]` Slice 1 `TaskState`: PROPOSED → AUTHORIZED → RUNNING → {COMPLETED, FAILED, BLOCKED, CANCELLED, REJECTED}.

`[PROPOSED]` binding Cursor missions to Slice 1/2B task records when runtime federation exists.

### 8.3 Mission resurrection prohibition

```text
No agent may continue an old mission merely because the conversation or process remains alive.
```

Rules:

- COMPLETED/FAILED/CANCELLED missions are **closed**.
- Retry requires new mission ID, explicit reactivation, and review if repeated failure.
- `[PROPOSED]` mission controller rejects `TASK_ID` reuse across distinct scopes.

### 8.4 Risk-based human gates

`[IMPLEMENTED]` Slice 1: `RiskLevel.HIGH` or `CRITICAL`, or `resource.requires_human_approval`, yields `AuthzDecision.REQUIRES_REVIEW` unless `task.human_approved`.

---

## 9. Delegation Governance

### 9.1 Default principle

```text
No authority may be delegated beyond the authority actually possessed.
DELEGATE ≠ AUTHORITY (Constitution §6)
```

### 9.2 Explicit answers

| Question | Answer | Status |
| --- | --- | --- |
| Who can delegate? | Principals/agents with active `AUTHORITY_DELEGATE` grant | `[IMPLEMENTED]` Slice 2B; `[NOT_IMPLEMENTED]` Slice 1 |
| Who can receive? | Registered principals with attenuated subset of delegator's grant | `[IMPLEMENTED]` Slice 2B |
| Recursive delegation? | Yes, max depth 3 | `[IMPLEMENTED]` `MAX_DELEGATION_DEPTH = 3` |
| Delegate beyond possession? | **PROHIBITED** | `[IMPLEMENTED]` attenuation logic |
| Delegate approval authority? | **CONDITIONALLY_ALLOWED** — only if delegator holds `APPROVAL_ISSUE` and attenuation preserves approval binding rules | `[PROPOSED]` human policy for consequential approvals |
| Delegate promotion authority? | **PROHIBITED by default**; **REQUIRES_HUMAN** if ever allowed | `[IMPLEMENTED]` research path denies `KNOWLEDGE_PROMOTE` |
| Delegate execution authority? | **PROHIBITED** — `EXECUTION` globally denied in TCB policy | `[IMPLEMENTED]` |
| Subordinate appoint commander? | **PROHIBITED** | `[PROPOSED]` |
| Peer activate peer? | **PROHIBITED** without commander authorization | `[PROPOSED]` |
| Master Orchestrator delegate to specialists? | **CONDITIONALLY_ALLOWED** — mission-scoped task assignment only, not standing authority | `[L5]` today; `[PROPOSED]` runtime binding |

### 9.3 Delegation chain audit requirements

`[PROPOSED]`: every delegation records `parent_grant_id`, `delegation_depth`, `issued_by`, `expires_at`, `policy_version`. Revocation cascades or explicit child revoke required (`[IMPLEMENTED]` `REVOKE_GRANT` in TCB).

---

## 10. Approval Governance

### 10.1 Separated concepts

| Concept | Meaning | May self-apply for consequential transitions? |
| --- | --- | --- |
| Recommendation | Non-binding proposal | Yes (output) |
| Review | Assessment without binding effect | No — reviewer ≠ producer for final review |
| Approval | Binding authorization for state change | **No** (default) |
| Authorization | Permission to act within scope | **No** for self-activation |
| Verification | Evidence/result checking | **No** as final independent verification |
| Promotion | Elevation to trusted/knowledge/production | **No** |

### 10.2 Default constitutional principle

```text
No self-approval for consequential state transitions.
```

Consequential transitions include: activation, delegation, approval issuance, knowledge promotion, policy change, constitutional change, agent maturity increase, AHOS access, production configuration change.

### 10.3 Self-action matrix

| Action | Propose | Verify (self) | Approve (self) | Promote (self) |
| --- | --- | --- | --- | --- |
| Own analysis result | ALLOWED | ALLOWED as SELF_CHECK only | **PROHIBITED** | **PROHIBITED** |
| Own mission completion | ALLOWED | **PROHIBITED** as independent | **PROHIBITED** | N/A |
| Own knowledge candidate | ALLOWED | **PROHIBITED** as independent | **PROHIBITED** | **PROHIBITED** |
| Own agent maturity | **PROHIBITED** | **PROHIBITED** | **PROHIBITED** | **PROHIBITED** |

`[IMPLEMENTED]` Slice 2B: `VerificationKind.SELF_CHECK` vs `INDEPENDENT`; D-04 candidate-bound approval; promotion only via `PROMOTE_KNOWLEDGE` command after gate.

### 10.4 Separation of duties requirements

`[PROPOSED]` minimum SoD for operational maturity:

- Producer ≠ independent verifier (final)
- Verifier ≠ approver (same person/agent instance)
- Approver ≠ executor (for external/protected resources)
- Commander ≠ independent verifier (same mission)

---

## 11. Verification Governance

### 11.1 Principles

```text
Reviewer ≠ Commander
Verifier ≠ Executor
Security reviewer ≠ Governance authority
Recommendation ≠ Approval
SELF_ASSESSMENT ≠ INDEPENDENT VERIFICATION
```

### 11.2 Verification types

| Type | Purpose | Default agent |
| --- | --- | --- |
| Independent verification | Validate evidence/claims | Human or assigned verifier (e.g., planned 16, 19) |
| Red-team review | Adversarial challenge | `agent.red-team` (Slice 1 logical) / planned 19 |
| Security review | Threat/control analysis | Agent 03 class; not governance approval |
| Governance review | Constitutional/policy consistency | Agent 04 class; not security enforcement |
| Evidence verification | Source/integrity check | Evidence protocol + TCB artifacts |
| Production readiness | Pre-production gate | Human + multi-reviewer |

### 11.3 Verification does not imply promotion

`[IMPLEMENTED]` TCB separates `CREATE_VERIFICATION` from `PROMOTE_KNOWLEDGE`. Verification PASS is necessary but not sufficient for promotion (approval gate D-04).

---

## 12. Promotion Governance

### 12.1 Promotion targets

| Target | Evidence required | Independent verification | Human approval | Governance approval | Security review |
| --- | --- | --- | --- | --- | --- |
| KnowledgeCandidate → Knowledge (PROMOTED) | Yes — lineage | Yes | **REQUIRES_HUMAN** for production-facing | Yes | If security-relevant |
| Policy change | Impact analysis | Yes | **REQUIRES_HUMAN** | Yes | Recommended |
| Agent maturity increase | Tests + charter | Yes | **REQUIRES_HUMAN** | Yes | If authority expands |
| Authority increase | Justification | Yes | **REQUIRES_HUMAN** | Yes | Yes |
| Production configuration | Soak/test evidence | Yes | **REQUIRES_HUMAN** | Yes | Yes |

### 12.2 Silent promotion prohibition

```text
MERGE ≠ GOVERNANCE APPROVAL
TEST PASS ≠ PRODUCTION PROOF
DOCUMENTATION ≠ PROMOTED KNOWLEDGE
```

`[IMPLEMENTED]` Only `CommandType.PROMOTE_KNOWLEDGE` through TCB after promotion gate (`agent_org/epistemic.py`).

### 12.3 Memory ≠ truth

`[IMPLEMENTED]` `[TESTED]` TCB denies memory promotion to truth. Stored memory, confidence, recency, audit inclusion never imply truth.

---

## 13. Constitutional Change Control

### 13.1 Current status

`[DOCUMENTED]` `AGENT_ORGANIZATION_CONSTITUTION.md` v0.1.0: `STATUS = DESIGN_ONLY`, `ENFORCEMENT = NOT_IMPLEMENTED`, `AUTHORITY = PROPOSED_GOVERNANCE_TEXT`.

Until human records adoption as L2, Constitution is **L3 proposed governance text**. Code denies (L0/L2 in policy modules) beat markdown.

### 13.2 Change process (proposed)

| Stage | Actor | Action |
| --- | --- | --- |
| Propose | Any agent or human | Draft amendment with version bump, rationale, impact |
| Review | Independent governance reviewer (not proposer) | Constitutional consistency check |
| Security review | Security architect class | Boundary impact if authority/security affected |
| Approve | **Human principal** | Record L2 adoption decision |
| Implement | Human-authorized code/docs change | Separate commit/PR with audit |
| Effective date | Explicit in amendment | No retroactive authority |
| Supersession | Prior version marked SUPERSEDED | Immutable history preserved |

### 13.3 Critical principle

```text
The Constitution must not be changeable merely because an agent has enough technical access to modify its files.
```

`[IMPLEMENTED]` Slice 2B globally denies `Capability.POLICY_MODIFY` and `Operation.UPDATE_POLICY` on protected paths.  
`[NOT_IMPLEMENTED]` Git/protected-branch enforcement for constitution files.

### 13.4 Emergency amendment

`[PROPOSED]`:

- Initiation: **human only**
- Scope: minimal temporary measure with expiry
- Post-incident: full review and ratification or rollback within fixed window
- Agents may **not** invoke emergency amendment autonomously

### 13.5 Versioning and rollback

- Semantic version on Constitution and protocols
- `SUPERSEDES` / `SUPERSEDED_BY` linkage
- Rollback requires human approval; rollback is not silent

---

## 14. Governance of Governance

### 14.1 Meta-problem

Who governs the governors?

| Governor | Reviewer | Escalation |
| --- | --- | --- |
| Master Orchestrator | Human principal; planned independent agents | Mehrdad |
| Future Agent One | Human principal; governance + security reviewers | Mehrdad — **UNRESOLVED** operational rules |
| Governance agents (04 class) | Independent peer + human | Contradiction escalation |
| Security agents (03 class) | Red team + human | Not governance override |
| Approval mechanisms | Audit + human spot check | Constitutional amendment |
| Delegation mechanisms | Authority chain audit | Revocation |

### 14.2 Authority collapse detection

`[PROPOSED]` standing audit questions:

1. Does any component both produce and finally verify the same artifact?
2. Does any component both approve and execute the same transition?
3. Does any component modify policy and benefit from that modification?
4. Does orchestration convenience bypass human gates?

Agent 03 security architecture provides complementary threat analysis; it does not supersede this governance document.

---

## 15. Master Orchestrator Governance

### 15.1 Current model

```text
MEHRDAD → MASTER ORCHESTRATOR → SPECIALIST
```

Operating layer: Cursor Control-Plane (L5). Not runtime-bound to Slice 1/2B.

### 15.2 Permitted functions

| Function | Status |
| --- | --- |
| Understand human requests | `[L5]` operational |
| Formalize tasks / mission IDs | `[L5]` operational |
| Select specialists | `[L5]` operational |
| Create recommendations | `[L5]` operational |
| Coordinate parallel analysis | `[L5]` operational |
| Compare and detect contradictions | `[L5]` operational |
| Request independent verification | `[L5]` operational |
| Synthesize results for human | `[L5]` operational |
| Report to Mehrdad | `[L5]` operational |

### 15.3 Prohibited automatic elevation

| Prohibited role | Reason |
| --- | --- |
| Source of truth | Epistemic ownership must stay in evidence/TCB/human |
| Unilateral verifier | SoD violation |
| Unilateral approver | Human/governance gate required |
| Unrestricted executor | Execution globally denied |
| Constitutional sovereign | Human principal reserved |
| Production authority | AHOS isolation |

### 15.4 Relationship to `agent.chief-orchestrator`

`[VERIFIED]` Slice 1 logical role ≠ Master Orchestrator runtime ≠ Agent One. Three names; **do not merge silently**. `HUMAN_DECISION_REQUIRED` for future mapping.

---

## 16. Agent One Future Governance

```text
AGENT_ONE = NOT_IMPLEMENTED / FUTURE_NON_AUTHORITY_ROOT
```

Constitutional questions **unresolved** — require human decisions before operationalization:

| Question | Status |
| --- | --- |
| May Agent One coordinate? | `[PROPOSED]` yes, bounded — like Master Orchestrator++ |
| May Agent One delegate? | `UNRESOLVED` — if yes, attenuation + human ceiling required |
| May Agent One approve? | `[DOCUMENTED]` no by title (Constitution §3.1) |
| May Agent One verify? | `UNRESOLVED` — likely no as final independent verifier of own orchestration |
| May Agent One promote? | `[DOCUMENTED]` no |
| May Agent One modify governance? | `[DOCUMENTED]` no |
| May Agent One access AHOS? | `[DOCUMENTED]` no unless future human authorization |
| May Agent One access credentials? | `[DOCUMENTED]` no |
| May Agent One execute? | `[DOCUMENTED]` no |
| May Agent One create/modify agents? | `UNRESOLVED` — registration vs activation governance required |

**Do not implement Agent One under this analysis.**

---

## 17. Agent Creation

### 17.1 Constitutional requirements for new agents

Every new agent requires:

```text
AGENT_ID                  — unique within target plane
ROLE                      — organizational function (not authority)
COMMANDER                 — who may activate
PARENT                    — reporting lineage
REPORTING_LINE            — explicit chain to human principal
CAPABILITY_SET            — allowed tokens (minimum necessary)
AUTHORITY_CEILING         — max authority class
LIFECYCLE_STATE           — initial REGISTERED/IDLE
MISSION_SCOPE             — none until activation
ALLOWED_TOOLS             — explicit enumeration
PROHIBITED_ACTIONS        — explicit enumeration
VERIFICATION_REQUIREMENTS — independent review rules
RETIREMENT/REVOCATION     — who may retire/revoke
```

### 17.2 Registration vs activation vs authority

```text
Registration  — row in registry / identity store; no mission authority
Activation    — commander-authorized begin-work for scoped mission
Authority     — derived grants for specific governed transitions
```

`[IMPLEMENTED]` Slice 1: `register()` vs maturity gates vs `GovernanceEngine.authorize`.  
`[IMPLEMENTED]` Slice 2B: `REGISTER_AGENT` vs session/grant derivation.  
`[NOT_IMPLEMENTED]` Cursor agent launch binding to either plane.

### 17.3 Dual-19 creation rule

New agents must declare plane: A (`agent.*`), B (`principal.*`), C (research), or D (`agent.org.*` documentary). Plane D agents are **not registry facts** until human approves seeding.

---

## 18. Suspension / Quarantine / Revocation

### 18.1 Triggers

| Trigger | Typical response |
| --- | --- |
| Policy violation | SUSPEND → review |
| Authority escalation attempt | QUARANTINE → security review |
| Prompt injection | QUARANTINE → sanitize + review |
| Evidence manipulation | QUARANTINE → audit chain review |
| Unauthorized delegation | REVOKE grants + SUSPEND |
| Self-activation | QUARANTINE → governance review |
| Repeated failures | SUSPEND → human reactivation approval |
| Security compromise | QUARANTINE → human + security clearance |
| Contradictory behavior | SUSPEND → investigation |
| Integrity failure | QUARANTINE → audit |

### 18.2 Authority matrix

| Action | Human | Commander | Master Orchestrator | Security agent | Governance agent | Agent self |
| --- | --- | --- | --- | --- |
| Suspend | ALLOWED | CONDITIONALLY_ALLOWED (subordinate) | PROPOSE only | PROPOSE | PROPOSE | PROHIBITED |
| Quarantine | ALLOWED | PROHIBITED | PROPOSE only | PROPOSE (escalate) | PROPOSE | PROHIBITED |
| Revoke grants | ALLOWED | PROHIBITED | PROHIBITED | PROPOSE | PROPOSE | PROHIBITED |
| Retire | ALLOWED | PROHIBITED | PROPOSE | PROPOSE | PROPOSE | PROHIBITED |
| Restore from SUSPEND | ALLOWED | CONDITIONALLY_ALLOWED | PROHIBITED | ADVISORY | ADVISORY | PROHIBITED |
| Restore from QUARANTINE | ALLOWED ( + security review) | PROHIBITED | PROHIBITED | ADVISORY | ADVISORY | PROHIBITED |

`[IMPLEMENTED]` Slice 1 `AgentRegistry.disable()`.  
`[IMPLEMENTED]` Slice 2B grant/session revocation.  
`[NOT_IMPLEMENTED]` QUARANTINED state, automated incident response.

---

## 19. Conflict Resolution

### 19.1 Principle

```text
Conflict ≠ automatic authority for the strongest agent.
```

Escalate; do not arbitrate by capability, eloquence, or orchestration position.

### 19.2 Conflict handling matrix

| Conflict type | First response | Escalation | Final arbiter |
| --- | --- | --- | --- |
| Specialist vs specialist | Document both positions; detect contradiction | Independent verifier | Human |
| Specialist vs Master Orchestrator | Orchestrator must not override by rank | Independent verifier | Human |
| Security vs governance | Separate reports; no merge | Joint human review | Human |
| Governance vs execution | Fail-closed on execution | Human policy decision | Human |
| Verifier vs commander | Verifier does not command | Escalate evidence dispute | Human |
| Evidence vs policy | Policy cannot invent evidence | Amend policy or gather evidence | Human |
| Old policy vs new policy | L0/L2 code wins until governed change | Constitutional change control | Human |
| Plane A vs Plane D taxonomy | **Do not merge** | Record DUAL_19 | **HUMAN_DECISION_REQUIRED** |

`[DOCUMENTED]` Evidence protocol: silent resolution forbidden.

---

## 20. Evidence Governance

### 20.1 Non-collapse rules

```text
evidence ≠ decision
evidence ≠ authority
evidence ≠ approval
claim ≠ truth
recommendation ≠ authorization
verification ≠ execution
documentation ≠ proof
```

### 20.2 Source-of-truth hierarchy (authority/evaluation)

```text
L0 — Actual runtime / repository reality
L1 — Validated tests and authoritative validation evidence
L2 — Current governance decisions (incl. policy code)
L3 — Current architecture / project documentation
L4 — Historical documentation
L5 — Chat / discussion / human proposals
L6 — Agent assumptions
```

Conflict default: `L0 > L1 > L2 > L3 > L4 > L5 > L6`  
Exception: fail-closed deny in L0/L2 code cannot be loosened by L3/L5 alone.

### 20.3 Epistemic ladder (Slice 2B — separate, map don't merge)

```text
Evidence ≠ Claim ≠ Hypothesis ≠ Prediction ≠ Observation ≠ Decision ≠ Outcome
```

TCB artifact is L1 **only if** verification/approval state in store supports it.

---

## 21. Security Boundary

Governance and security are **separate layers**:

| Layer | Defines | Must not |
| --- | --- | --- |
| **Governance** | What SHOULD be allowed; authority rules; human sovereignty | Implement technical enforcement alone |
| **Security** | How unauthorized behavior is prevented/detected | Become governance authority |
| **Runtime** | What is actually permitted at enforcement points | Silently expand authority |

Agent 03 (`AGENT_ORGANIZATION_SECURITY_ARCHITECTURE.md`) analyzed threats and controls. This document treats it as **relevant context**, not automatic L2 authority.

`[VERIFIED]` Both documents agree: `DOCUMENTED CONTROL ≠ ENFORCED CONTROL`, `POLICY ≠ SECURITY BOUNDARY`.

---

## 22. Communication Governance

`[VERIFIED]` No inter-agent message bus exists. Communication protocol envelopes are **DESIGN_ONLY**.

### 22.1 Command authenticity requirements (future implementation)

| Requirement | Purpose |
| --- | --- |
| Command source binding | Prove issuer identity |
| Command scope binding | Tie to mission/task ID |
| Task/mission binding | Prevent scope creep |
| Replay prevention | `[IMPLEMENTED]` TCB duplicate command ID |
| Stale command rejection | `[IMPLEMENTED]` `COMMAND_MAX_AGE = 5 minutes` in Slice 2B |
| Cancellation tokens | Explicit mission cancel |
| Authorization expiry | Grant lifetime bounds |
| Delegation chain provenance | Audit attenuation |
| Reporting identity | Sender cannot spoof commander |

`[PROPOSED]` Cursor Control-Plane missions should eventually produce signed/bound activation records federated to Slice 1/2B.

---

## 23. Auditability

### 23.1 Principle

```text
Audit record ≠ governance authority
```

An audit log records what happened; it does not authorize what happened.

### 23.2 Required durable audit events

| Event | Slice 1 | Slice 2B | Cursor plane |
| --- | --- | --- | --- |
| Command | Partial (authz) | `[IMPLEMENTED]` | `[NOT_IMPLEMENTED]` |
| Activation | Agent register/update | Identity register | `[NOT_IMPLEMENTED]` |
| Delegation | — | `[IMPLEMENTED]` | — |
| Approval | — | `[IMPLEMENTED]` | — |
| Verification | — | `[IMPLEMENTED]` | — |
| Promotion | — | `[IMPLEMENTED]` | — |
| Suspension | `[IMPLEMENTED]` disable | Revoke | — |
| Constitutional change | — | — | `[PROPOSED]` git + L2 record |

`[IMPLEMENTED]` Hash-chain audit in both planes (in-memory; tamper detection in tests).

`[PROPOSED]` Durable external anchoring for production.

---

## 24. Least Authority

Constitutional principle: **Minimum Necessary Authority**.

Implementation expectations:

- Default deny (`[IMPLEMENTED]` both planes)
- Task-scoped grants (`[IMPLEMENTED]` Slice 2B)
- Maturity gates (`[IMPLEMENTED]` Slice 1)
- Global deny lists for AHOS/credentials/trading (`[IMPLEMENTED]`)
- Time-bounded commands and grants (`[IMPLEMENTED]` Slice 2B)
- No standing external execution (`[IMPLEMENTED]` deny)
- Periodic authority review (`[PROPOSED]`)

---

## 25. Anti-Patterns

| Anti-pattern | Description | Mitigation |
| --- | --- | --- |
| Self-authorization | Agent grants itself authority | Fail-closed; human grant only |
| Self-promotion | Agent elevates own knowledge/maturity | TCB promotion gate; human approval |
| Self-verification | Final verification of own output | Independent verifier required |
| Self-activation | Agent starts without commander | Mission controller; explicit command |
| Peer activation | Peer starts peer without commander | Prohibited |
| Authority laundering | Delegation obscures origin | Delegation chain audit |
| Recursive uncontrolled delegation | Unlimited depth/breadth | Max depth 3; attenuation |
| Commander spoofing | False issuer identity | Command authenticity binding |
| Stale command reuse | Old mission command replayed | Expiry + replay detection |
| Mission resurrection | Continue closed mission | New ID required |
| Constitutional bypass | Markdown overrides code denies | L0/L2 precedence |
| Undocumented authority | Implied powers from role | Explicit authority ceiling |
| Policy-as-authority | Policy text grants execution | Separate approval/activation |
| Role-as-authority | Title implies powers | Capability tokens |
| Capability-as-authority | Token implies approval | Separate approval gate |
| Documentation-as-enforcement | Doc change = operational change | Implemented vs documented matrix |
| Orchestrator authority collapse | MO becomes sovereign | SoD rules §15 |
| Agent One authority collapse | Future root becomes sovereign | Unresolved questions §16 |
| Dual-19 silent merge | Pick taxonomy without human | DUAL_19 = UNRESOLVED |
| Chat-as-command | L5 message becomes L2 | Explicit adoption path |
| Merge-as-approval | Git merge promotes governance | Separate promotion governance |

---

## 26. Decision Matrix

Legend: **A** = ALLOWED, **C** = CONDITIONALLY_ALLOWED, **P** = PROHIBITED, **H** = REQUIRES_HUMAN, **V** = REQUIRES_INDEPENDENT_VERIFICATION, **U** = UNRESOLVED

| Action | Agent | Commander | Master Orchestrator | Human | Independent Verifier |
| --- | --- | --- | --- | --- | --- |
| Propose mission | A | A | A | A | C (recommend only) |
| Activate agent | P | C (subordinates) | C (select+request) | H | P |
| Assign task | P | C (within scope) | C (coordinate) | H | P |
| Delegate authority | P | C (if granted) | U | H | P |
| Approve result | P | C (non-consequential) | P | H | P |
| Verify result | C (not own, final) | C (not own mission) | C (not own synthesis) | A | A (independent) |
| Promote knowledge | P | P | P | H + V | V |
| Change policy | P | P | P | H + V | V |
| Change Constitution | P | P | P | H + V | V |
| Suspend agent | P | C (subordinate) | P (propose) | A | P |
| Quarantine agent | P | P | P (propose) | H | P (escalate) |
| Retire agent | P | P | P (propose) | H | P |
| Modify AHOS production | P | P | P | H | V |

**Conditional notes:**

- Commander activation/delegation requires prior human-authorized ceiling.
- Master Orchestrator "assign task" = coordination/request, not runtime authorization until bound.
- Independent verifier verifies; does not approve or command unless separately granted.

---

## 27. Implemented / Documented / Proposed Matrix

| Control | IMPLEMENTED | DOCUMENTED | PROPOSED | UNKNOWN |
| --- | --- | --- | --- | --- |
| Human sovereignty principle | — | Constitution §3.1 | Emergency override detail | — |
| Fail-closed authorization | Slice 1 + 2B | Constitution | — | — |
| Global AHOS/credential/trading deny | Slice 1 + 2B | Constitution | — | — |
| 19-role Slice 1 registry | `ahos_org/registry.py` | Registry model | — | — |
| Planned 19 blueprint | — | PLANNED_19_AGENT_MAP | — | — |
| Dual-19 resolution | — | — | — | **UNRESOLVED** |
| Agent lifecycle FSM (unified) | Partial (task + identity states) | This mission | Full activation FSM | — |
| Agent activation governance | Maturity gate only | Mission text | Commander binding | — |
| Mission resurrection prevention | Terminal task states | Protocols | Mission controller | — |
| Delegation max depth 3 | Slice 2B | — | Cross-plane | — |
| Self-approval prohibition | TCB promotion/approval gates | Constitution | Full SoD | — |
| Independent verification | TCB types | Supervision protocol | 19-agent service | — |
| Knowledge promotion gate | Slice 2B epistemic | Constitution | — | — |
| Constitutional change control | Policy modify denied | Constitution adoption § | Full amendment process | — |
| Master Orchestrator bounds | Chief orchestrator tokens | Constitution | Cursor binding | — |
| Agent One governance | Status constant | Constitution §19 | Operational rules | Most questions |
| Agent creation requirements | Partial AgentRecord | Charter template | Full contract | — |
| Quarantine state | — | Agent 03 doc | This doc | — |
| Conflict escalation | Contradiction in TCB | Evidence protocol | Full service | — |
| Command authenticity | TCB replay/expiry | Comm protocol | Cursor federation | — |
| Audit hash chain | Both planes | — | Durable anchor | — |
| Inter-agent message bus | — | Comm protocol | — | Deferred |
| Identity federation A↔B | — | Registry model | — | Deferred |
| Constitution enforcement in code | Deny policy modify | — | Status taxonomy in code | — |
| Cursor control-plane binding | — | — | All §15 binding | — |

---

## 28. Open Constitutional Questions

1. **Dual-19 resolution** — Which taxonomy is canonical? Mapping table A↔D? Retire either list? → `HUMAN_DECISION_REQUIRED`
2. **Agent One operational charter** — All questions in §16 → `HUMAN_DECISION_REQUIRED`
3. **Master Orchestrator ↔ `agent.chief-orchestrator` ↔ Agent One** — naming and authority mapping → `HUMAN_DECISION_REQUIRED`
4. **Constitution adoption** — When does v0.1.0 become L2? → `HUMAN_DECISION_REQUIRED`
5. **Cursor-to-runtime federation** — How do chat missions bind to Slice 1/2B tasks? → `FUTURE_MISSION_REQUIRED`
6. **Quarantine authority model** — Who may quarantine vs suspend in production org? → `HUMAN_DECISION_REQUIRED`
7. **Approval delegation policy** — May approval authority ever be delegated? → `HUMAN_DECISION_REQUIRED`
8. **Agent maturity promotion criteria** — What evidence promotes REGISTERED → OPERATIONALLY_TRUSTED? → `HUMAN_DECISION_REQUIRED`
9. **Independent verifier assignment** — Service vs ad-hoc human? → `FUTURE_MISSION_REQUIRED`
10. **Emergency constitutional amendment** — Threshold and expiry rules → `HUMAN_DECISION_REQUIRED`
11. **AHOS read access for org agents** — Any bounded read for analysis? → `HUMAN_DECISION_REQUIRED`
12. **Plane D charter issuance process** — Who authorizes blueprint → operational? → `HUMAN_DECISION_REQUIRED`
13. **Governance agent self-review** — How Agent 04 class avoids reviewing its own constitutional changes as final? → `HUMAN_DECISION_REQUIRED`
14. **Incident restore from QUARANTINED** — Evidence bar for reactivation → `HUMAN_DECISION_REQUIRED`
15. **Unified registry** — Single ID namespace or permanent federation? → `HUMAN_DECISION_REQUIRED`

---

## 29. Human Decisions Required

Decisions that **cannot** be safely made by Agent-04 or any specialist agent alone:

1. Adopt `AGENT_ORGANIZATION_CONSTITUTION.md` v0.1.0 (or amended version) as L2 governance
2. Resolve **DUAL_19** — select, merge, or federate Plane A and Plane D taxonomies
3. Define Agent One operational bounds before any implementation
4. Map Master Orchestrator to runtime identity (or explicitly keep L5-only)
5. Authorize constitution file protection mechanism (branch rules, signing)
6. Define quarantine vs suspend authority for production operations
7. Set agent maturity promotion criteria and evidence bars
8. Decide bounded AHOS read access policy for research/analysis agents
9. Approve Plane D specialist charter issuance order (dependencies in planned map)
10. Ratify approval delegation policy (default deny recommended)
11. Choose independent verification service model
12. Approve emergency amendment procedure
13. Decide unified vs federated registry architecture
14. Authorize any governance runtime implementation mission (separate from this design)
15. Accept or reject this document's `[PROPOSED]` recommendations for organizational adoption

---

## 30. Recommended Future Work — STATE ONLY

`RECOMMENDED_NEXT_MISSION = STATE_ONLY — DO NOT EXECUTE`

The following are **recommendations only**. Agent-04 must not execute them.

| # | Recommended mission | Purpose | Prerequisite |
| --- | --- | --- | --- |
| 1 | Human adoption session for Constitution v0.1.0 | Establish L2 governance baseline | Mehrdad review |
| 2 | Dual-19 resolution mission | Human decision on taxonomy | #1 |
| 3 | Identity federation design (A↔B↔Cursor) | Close registry split | #2 or explicit federate decision |
| 4 | Mission controller specification | Enforce activation/resurrection rules | #3 |
| 5 | Command authenticity / activation binding spec | Bind Cursor missions to runtime | #4 |
| 6 | Independent verification service design | Operationalize SoD | #1 |
| 7 | Quarantine/incident governance specification | QUARANTINED state + restore | Agent 03 + #1 |
| 8 | Constitutional amendment tooling design | Protected change path | #1, #5 |
| 9 | Agent One charter draft (non-implementing) | Resolve §16 questions | #1, #2 |
| 10 | Implemented vs enforced governance gap audit | Close DOCUMENTED vs IMPLEMENTED gaps | #1 |
| 11 | Agent 05+ charter template rollout | Per planned map dependencies | #2 |
| 12 | Governance enforcement runtime mission (separate) | Code only after human authorization | #1–#5 |

---

## Appendix A — Proposed Constitutional Model (Evaluated)

Requested model:

```text
Human Principal
      ↓
Constitution
      ↓
Governance Authority
      ↓
Command Authority
      ↓
Agent Identity
      ↓
Role
      ↓
Capability
      ↓
Mission Scope
      ↓
Activation
      ↓
Execution Boundary
      ↓
Evidence / Result
      ↓
Independent Verification
      ↓
Approval / Promotion
```

### Evaluation

**Assessment:** Mostly correct with **one ordering refinement** and **explicit parallel branches**.

1. **Human Principal → Constitution** — Correct. Constitution derives legitimacy from human adoption, not from agents.

2. **Constitution → Governance Authority** — Correct. Governance authority is delegated, bounded, revocable.

3. **Governance Authority → Command Authority** — Correct with nuance: command authority is a **subset** of governance, not peer to it.

4. **Agent Identity before Role** — Correct. Identity is stable; role is assignable.

5. **Role before Capability** — Correct as documentation order; enforcement must use **capability tokens**, not role names.

6. **Capability before Mission Scope** — **Refinement proposed:** Mission scope should **attenuate** capability, not follow it linearly. Effective authority = capability ∩ mission scope ∩ grant ∩ maturity.

7. **Activation before Execution Boundary** — Correct. Activation is necessary; not sufficient.

8. **Evidence before Independent Verification before Approval/Promotion** — Correct epistemic ordering.

**Proposed revision:**

```text
Human Principal
      ↓
Constitution (L2 when adopted)
      ↓
Governance Authority (human-delegated)
      ↓
Command Authority (mission-scoped)
      ↓
Agent Identity
      ↓
Role (non-authoritative label)
      ↓
Capability Ceiling (max possible)
      ↓
Mission Scope (attenuation)
      ↓
Activation (time-bounded)
      ↓
Effective Authority = Capability ∩ Scope ∩ Grant ∩ Maturity
      ↓
Execution Boundary (separate gate — default DENY)
      ↓
Evidence / Result (non-authoritative)
      ↓
Independent Verification
      ↓
Approval / Promotion (human for consequential)
```

**Parallel enforcement branch (not subordinate to documentation):**

```text
Security Controls → Runtime Enforcement → Audit
```

Governance defines SHOULD; security defines prevention/detection; runtime enforces IS.

---

## Appendix B — Dual-19 Record

```text
DUAL_19 = UNRESOLVED

Plane A: ahos_org/registry.py — 19 canonical agent.* roles [IMPLEMENTED]
Plane D: docs/agents/PLANNED_19_AGENT_MAP.md — 19 agent.org.NN-* roles [PLANNED]

This document does NOT:
  - merge the taxonomies
  - select one as canonical
  - rename either list
  - seed Plane D into code

Action required: HUMAN_DECISION_REQUIRED
```

---

## Appendix C — Mission Completion Record

```text
MISSION_ID       = TASK-20260914-004
MISSION_STATUS   = GOVERNANCE_AND_CONSTITUTION_ANALYSIS_COMPLETE_WITH_GAPS
AGENT_ID         = AGENT-04
DIRECT_COMMANDER = MASTER ORCHESTRATOR
LIFECYCLE_STATUS = IDLE / DORMANT / WAITING_FOR_NEW_COMMAND
DUAL_19          = UNRESOLVED
AGENT_ONE        = NOT_IMPLEMENTED / FUTURE_NON_AUTHORITY_ROOT
AHOS_IMPACT      = NONE
CODE_CHANGES     = NONE
RUNTIME_CHANGES  = NONE
GOVERNANCE_CHANGES = NONE (recommendations only — not adopted)
COMMIT           = NONE
PUSH             = NONE
DELIVERABLE      = this document
```

---

*End of AGENT-04 Governance & Constitution Architecture v0.1.0*
