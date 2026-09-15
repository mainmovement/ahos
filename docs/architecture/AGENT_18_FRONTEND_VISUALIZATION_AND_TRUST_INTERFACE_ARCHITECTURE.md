# AGENT-18 — Frontend, Visualization, Information Architecture & Trust-Interface Architecture

```text
DOCUMENT_ID      = AGENT_18_FRONTEND_VISUALIZATION_AND_TRUST_INTERFACE_ARCHITECTURE
MISSION_ID       = TASK-20260914-018 (Frontend Visualization & Trust-Interface Architecture)
VERSION          = 1.0.0
STATUS           = FRONTEND_VISUALIZATION_AND_TRUST_INTERFACE_ARCHITECTURE_ANALYSIS_COMPLETE_WITH_GAPS
AGENT_ID         = AGENT-18
DIRECT_COMMANDER = AGENT-01 / AGENT ONE
AUTHORITY        = READ_ONLY_ARCHITECTURE_ANALYSIS
CODE_CHANGES     = NONE (this document is the mandated mission deliverable)
AHOS_EFFECT      = NONE
RUNTIME_EFFECT   = NONE
```

This document is a **read-only architecture artifact** produced by AGENT-18. It converts Agent-17's cognitive UX model into a **technical frontend, visualization, and trust-interface architecture** for the AHOS Agent Organization control plane. It does **not** implement UI, components, CSS, runtime, API, or governance changes.

Facts cite repository evidence with explicit classification labels. Recommendations are labeled `[PROPOSED]`.

---

## 1. Executive Verdict

**The Agent Organization has zero organizational frontend runtime today.** Mehrdad interacts through Cursor chat and markdown artifacts. The intended product — a trustworthy, inspectable, Persian-first interface to Agent One and the organizational substrate — is architecturally specified by Agent-17 and bound to Slice 2B epistemic types, but **not experienceable as software**.

| Question | Verdict |
| --- | --- |
| Does an organizational frontend exist? | **NO** — `[VERIFIED]` no `package.json`, no React/Vue/HTML UI, no org-specific web app in `ahos-agent-org` |
| Is frontend architecture specified? | **YES (this document)** — prior to this mission: **NO** dedicated frontend architecture artifact |
| Can the frontend be built honestly today? | **PARTIALLY** — manual/CURRENT mode + read-only projection viewer over in-memory TCB is possible; live org UI requires MC + Agent One |
| Should frontend create organizational truth? | **NEVER** — hard invariant |
| Should UI imply live agents when runtime absent? | **NEVER** — no-fake-live-system policy |
| Is Persian-first required? | **YES** — inherited from Agent-17 + AHOS product precedent |
| Org frontend = AHOS frontend? | **NO** — separate product shell with explicit integration boundary |

**Central design thesis:**

```text
The frontend is a window into organizational reality — not a theater of intelligence.
Visual polish must never exceed backend-established authority.
Every trust signal must trace to an authoritative source, version, and timestamp.
```

**Classification:** `FRONTEND ARCHITECTURE COMPLETE — IMPLEMENTATION ABSENT — RUNTIME UI NOT STARTED`

---

## 2. Mission Scope

### 2.1 Inspected (read-only)

| Repository | Path | Mode |
| --- | --- | --- |
| Agent Organization | `G:\robat\ahos-agent-org` | Primary — docs, code, tests, projections |
| AHOS | `G:\robat\ahos` | Secondary — bilingual UX, dashboard, evidence patterns |

### 2.2 Input artifacts (challenged, not blindly trusted)

- **Agent-17** Human–Agent Organization UX & Product Architecture (primary UX input)
- Agent-16 Independent Verification & Organizational Forensics
- Agent-14 Agent Runtime Architecture
- Agent-15 Prompt/Instruction/Delegation Architecture
- Agent-05 Epistemic Reasoning Architecture (via Slice 2B code)
- Governance: Constitution, Registry Model, Operating Baseline
- Protocol pack: Communication, Evidence, Response, Supervision, Escalation, Update
- Slice 2B: `agent_org/epistemic.py`, `projections.py`, `contracts.py`, `audit.py`, `commands.py`
- Slice 1: `ahos_org/models.py`, registry, task FSM
- AHOS: `CommandCenter.tsx`, `01/src/lib/format.ts`, 3D platform `app-shell.tsx`

### 2.3 Not performed

- No code, UI, CSS, React, package installs, AHOS modifications, runtime activation, commit, push
- Test re-execution deferred; Agent-16 L1 evidence (251 tests) accepted for substrate claims

### 2.4 Deliverable boundary

| Layer | Owner | Status after this mission |
| --- | --- | --- |
| UX principles & interaction model | Agent-17 | `[COMPLETE]` |
| Visualization & trust-interface architecture | Agent-18 | `[COMPLETE]` (this document) |
| Design system implementation | Future engineering | `[ABSENT]` |
| Frontend implementation | Future engineering | `[ABSENT]` |
| Backend API / BFF | Future Agent-14 Phase 1+ | `[ABSENT]` |
| Organizational runtime | Future MC + Agent One | `[ABSENT]` |

---

## 3. Current Reality

### 3.1 Actual human interaction path

```text
MEHRDAD (Human Principal)
   ↓ natural language intent (unbound — no runtime mission record)
CURSOR CONTROL-PLANE (L5 — external, not repo-enforced)
   ↓ manual session open per "agent"
SPECIALIST CURSOR WORKER (acting as AGENT-NN — no commander chain)
   ↓ markdown report / chat output
MEHRDAD (manual read, copy, reconcile, next prompt)
```

`[VERIFIED]` per Agent-16 §5; Agent-17 §3.1.

### 3.2 Frontend-specific current state

| Element | Status | Evidence |
| --- | --- | --- |
| Organizational web/desktop UI | `[NOT IMPLEMENTED]` | No frontend package manifest in `ahos-agent-org` |
| Agent One interface | `[NOT IMPLEMENTED]` | No service loop; `agent_org/__init__.py` marker only |
| Mission Controller UI binding | `[NOT IMPLEMENTED]` | No MC in repository |
| Read projections API | `[NOT IMPLEMENTED]` | `ReadOnlyProjections` exists in-process only |
| Real-time event stream to UI | `[NOT IMPLEMENTED]` | Audit ledger in-memory; no transport |
| Org i18n layer | `[NOT IMPLEMENTED]` | No org-specific locale files |
| CURRENT mode banner spec | `[PROPOSED]` | Agent-17 §31.1 |

### 3.3 What exists that frontend may eventually bind to

| Substrate | Status | Frontend relevance |
| --- | --- | --- |
| Slice 2B epistemic artifacts (14+ types) | `[IMPLEMENTED]` `[TESTED]` | Canonical data contracts for trust UI |
| Slice 2B `ReadOnlyProjections` | `[IMPLEMENTED]` | Prototype read-model API surface |
| Slice 2B `AuditEvent` hash chain | `[IMPLEMENTED]` in-memory | Expert-mode audit explorer source |
| Slice 1 `TaskState` FSM | `[IMPLEMENTED]` `[TESTED]` | Partial mission lifecycle vocabulary |
| Slice 1 registry (19 logical roles) | `[IMPLEMENTED]` | Agent card registry plane A data |
| Research worker path | `[IMPLEMENTED]` | One specialist lifecycle pattern |
| Communication protocol envelopes | `[DESIGN_ONLY]` `TRANSPORT = NONE` | Future Layer B message inspector |

### 3.4 Canonical organizational identity (non-negotiable)

```text
AGENT_ONE_ORGANIZATIONAL_ROLE = CURRENT_INTENDED_ROOT / PRIMARY_ORGANIZATIONAL_AGENT
AGENT_ONE_RUNTIME             = NOT_IMPLEMENTED
DIRECT_COMMANDER              = AGENT-01 / AGENT ONE
```

Historical terms (Master Orchestrator, Chief Orchestrator, Cursor Master Orchestrator, Future Agent One) are `[SUPERSEDED]` for organizational framing where applicable.

```text
ORGANIZATIONAL_FRONTEND_RUNTIME = NOT_IMPLEMENTED
FRONTEND_ARCHITECTURE_STATUS    = SPECIFIED (this document)
TRUST_UI_STATUS                 = NOT_IMPLEMENTED
REAL_TIME_UI_STATUS             = NOT IMPLEMENTED
```

---

## 4. Agent-17 Input Assessment

Agent-17 deliverable: **`[VERIFIED]` as primary UX input — materially complete and internally consistent.**

### 4.1 What Agent-17 provides (consumed, not summarized)

| Agent-17 artifact | Agent-18 conversion |
| --- | --- |
| Layer A/B two-layer interface | Routing model + layout architecture (§9) |
| Orthogonal status dimensions | `StatusDimensionBundle` technical model (§7) |
| Drill-down Levels 0–7 | URL/state encoding + inspector panels (§10) |
| Command vs Request UX classes | Semantic action contract (§21) |
| Epistemic display vocabulary | Bound to Slice 2B enums (§6) |
| Contradiction first-class UX | ContradictionCard + graph decision (§24, §26) |
| No fake live org (P7/P8) | No-Fake-Live-System policy (§39) |
| Persian-first requirement | RTL/i18n technical architecture (§34) |
| MVOU feature set | Minimum Viable Organizational Frontend (§50) |
| UX threat model §29 | Extended frontend threat model (§45) |

### 4.2 Agent-17 gaps Agent-18 must fill

1. **Visual encoding specification** — Agent-17 forbids patterns; Agent-18 defines semantic visual language (§32).
2. **Data contracts for UI consumption** — Agent-17 references types; Agent-18 defines projection DTOs (§11).
3. **Real-time transport selection** — Agent-17 mentions async missions; Agent-18 evaluates SSE/polling/WebSocket (§14).
4. **State management architecture** — not specified in Agent-17; specified here (§41).
5. **Trusted rendering policies** — security-critical; specified here (§20).
6. **Graph visualization suitability analysis** — Agent-17 mentions DAG; Agent-18 evaluates per graph type (§26).
7. **Frontend observability** — not in Agent-17 scope (§43).
8. **Testing architecture for UI** — Agent-19 handoff requires test categories (§46).

### 4.3 Agent-17 corrections required

| Issue | Status | Agent-18 stance |
| --- | --- | --- |
| Code marker `AGENT_ONE_STATUS = FUTURE_NON_AUTHORITY_ROOT` | `[CONFIRMED]` — organizational vs runtime conflation | Frontend labels must separate **role** from **runtime**; code comment fix is governance mission |
| Slice 1 TaskState lacks VERIFICATION/ACCEPTANCE | `[CONFIRMED]` | Frontend composes overlay dimensions; does not pretend TaskState is complete |
| Dual-19 unresolved | `[CONFIRMED]` | Every agent reference shows plane label; standing contradiction badge |

**AGENT_17_INPUT_STATUS = COMPLETE — CONSUMED AND EXTENDED**
**AGENT_17_CORRECTIONS_REQUIRED = NONE IN THIS DOCUMENT — governance/code missions remain**

**NEW_CROSS_AGENT_DISCOVERIES (Agent-18):** 5

1. **`ReadOnlyProjections` is the seed of an honest read-model API** — frontend should never bypass it to mutate stores.
2. **AHOS "ROOTS LIVE" pulsing indicator is an anti-pattern for org UI** — `[VERIFIED]` in AHOS `app-shell.tsx`; org frontend must not copy uncritically.
3. **Evidence `assurance` field (0–100) must never become a user-facing confidence meter** — `[VERIFIED]` in `epistemic.py`; internal warrant only.
4. **Slice 2B `VerificationKind.INDEPENDENT` enforces producer ≠ verifier in code** — UI must surface this distinction; backend already validates.
5. **No acceptance record type exists separate from `Approval`** — acceptance UI binds to `Approval` artifact with scoped action; no invented AcceptRecord enum.

---

## 5. Frontend Truth Boundary

### 5.1 Hard invariant

> **The frontend never creates organizational truth.**

The frontend is a **read-and-intent** surface. It may:

- Display authoritative projections (state, evidence, claims, missions, agents, verification records, audit events, proposals, approvals, failures)
- Collect **human intent** and emit **intent envelopes** to authorized ingress
- Show **staleness**, **unknown**, and **capability gap** honestly
- Label **PLANNED**, **SIMULATION**, and **MANUAL MODE** explicitly

The frontend must **never** independently decide or visually imply:

- Authorization, capability, verification, acceptance, canonical truth
- Agent authority, mission completion, policy validity
- Inter-agent message delivery, Agent One runtime presence, MC operation

### 5.2 Authority illusion prevention rules

| UI element | May show | Must not imply |
| --- | --- | --- |
| Green badge | Lifecycle phase reached | Verified, accepted, trusted, correct |
| Agent avatar active | UI session open | Runtime agent authorized and executing |
| Progress bar | Defined sub-step completion | Mission success or verification pass |
| "Approve" button clicked | Intent submitted | Command executed and accepted by TCB |
| Cached projection | Last known authoritative state | Current live state without freshness label |
| Markdown report rendered | Untrusted agent output | Safe HTML or executable content |

### 5.3 Mode honesty (CURRENT vs FUTURE)

```text
┌─────────────────────────────────────────────────────────────┐
│ CURRENT: MANUAL CONTROL PLANE — CURSOR MEDIATED             │
│ Organizational runtime NOT OPERATIONAL                      │
└─────────────────────────────────────────────────────────────┘
```

Future/simulation surfaces require watermark: **`SIMULATION — NOT AUTHORITATIVE`**.

`[PROPOSED]` banner text (Persian): `حالت فعلی: کنترل دستی از طریق Cursor — سازمان خودکار نیست`

---

## 6. UI Semantic State Taxonomy

Epistemic and lifecycle states must be **visually and semantically non-interchangeable**. Color alone is forbidden as the sole channel.

### 6.1 Taxonomy dimensions

Each displayed state belongs to exactly one **semantic class**:

| Class | Meaning | Visual family | Example tokens |
| --- | --- | --- | --- |
| **EPISTEMIC** | What is known about truth | Diamond + text label | KNOWN, UNCERTAIN, UNKNOWN, CONTRADICTORY, NOVEL |
| **LIFECYCLE** | Process phase | Circle outline + phase text | PROPOSED, RUNNING, COMPLETED |
| **AUTHORIZATION** | Governance grant | Shield icon + scope ref | AUTHORIZED, REQUIRES_REVIEW, DENIED |
| **VERIFICATION** | Independent check result | Check-in-box (qualified) | UNVERIFIED, PASS, FAIL, INCONCLUSIVE |
| **ACCEPTANCE** | Human/governance gate | Stamp icon | PENDING, ACCEPTED, REJECTED, DEFERRED |
| **FRESHNESS** | Temporal validity | Clock + age | LIVE, FRESH, STALE, UNKNOWN, OFFLINE |
| **CAPABILITY** | What system can do | wrench/lock | AVAILABLE, PLANNED, NOT_IMPLEMENTED, GAP |
| **SEVERITY** | Human attention urgency | Triangle (not color-only) | CRITICAL, HIGH, MEDIUM, LOW, INFO |

### 6.2 Forbidden visual equivalences

```text
UNKNOWN           ≠ VERIFIED          (different shape + explicit "UNKNOWN" text)
PROPOSED          ≠ ACCEPTED          (draft watermark vs stamp)
ACTIVE            ≠ AUTHORIZED        (activity pulse vs shield)
AGENT COMPLETED   ≠ RESULT VERIFIED   (lifecycle vs verification class)
MODEL OUTPUT      ≠ FACT              (source badge "AGENT OUTPUT")
SELF_CHECK PASS   ≠ INDEPENDENT PASS  (qualifier mandatory)
REGISTERED        ≠ OPERATIONAL       (maturity level display)
PLANNED           ≠ LIVE              (watermark + capability class)
```

### 6.3 Epistemic posture mapping (organization summaries)

From Agent-17 §11.2, bound to Slice 2B evidence graph:

| Posture | Backend derivation (simplified) | UI treatment |
| --- | --- | --- |
| KNOWN | Evidence VALID + verification PASS + no OPEN contradiction | Neutral epistemic badge; still show provenance link |
| UNCERTAIN | Partial evidence or INCONCLUSIVE verification | List explicit gaps |
| UNKNOWN | No evidence or UNVERIFIED | Prominent UNKNOWN — never empty silence |
| CONTRADICTORY | ContradictionCase OPEN or RETAINED_UNCERTAIN | ContradictionCard required |
| NOVEL | New claim, no memory match | NOVEL badge + "not in organizational memory" |

### 6.4 Binding to Slice 2B enums (implemented)

Frontend DTOs must map 1:1 to repository enums — no UI-only aliases that collapse meaning:

```text
EvidenceState          → lifecycle + freshness derivation
VerificationStatus     → verification dimension
VerificationKind       → INDEPENDENT | SELF_CHECK (never collapse)
ClaimState             → claim lifecycle
ContradictionState     → contradiction lifecycle
KnowledgeState         → candidate lifecycle (PROMOTED ≠ truth)
MemoryState            → memory lifecycle (PROMOTED ≠ truth)
ApprovalState          → acceptance/approval lifecycle
TaskState              → mission lifecycle (partial)
ResearchMissionState   → research mission lifecycle
```

---

## 7. Orthogonal Status Model

### 7.1 Core principle

**Never collapse orthogonal dimensions into `status = green/red`.**

Each entity carries a `StatusDimensionBundle`:

```typescript
// [PROPOSED] conceptual TypeScript — not implemented
interface StatusDimensionBundle {
  entity_id: string;
  entity_type: EntityType;
  schema_version: number;
  projection_version: number;
  as_of: ISO8601;
  freshness: FreshnessState;
  dimensions: {
    lifecycle?: DimensionValue;
    authorization?: DimensionValue;
    verification?: DimensionValue;
    acceptance?: DimensionValue;
    evidence?: DimensionValue;
    epistemic?: DimensionValue;
    capability?: DimensionValue;
  };
  source_refs: SourceRef[];  // authoritative backend pointers
}
```

### 7.2 Example: composed mission state (valid and required)

```text
Mission MISSION-042:
  lifecycle:     ACTIVE
  agent:         COMPLETED (Agent-16)
  evidence:      PARTIALLY_SUPPORTED
  verification:  PENDING
  acceptance:    NOT_STARTED
  freshness:     FRESH (updated 2m ago)
```

UI renders **five separate badges** + freshness clock — never a single "75% complete" bar unless sub-steps have defensible semantics.

### 7.3 Agent lifecycle states (UI vocabulary)

Maps Agent-17 §9.1 + Agent-14 lifecycle design:

```text
REGISTERED | IDLE | DORMANT | WAITING_FOR_COMMAND
ACTIVATION_REQUESTED | AUTHORIZED | ACTIVE | COMPLETED
FAILED | TIMEOUT | CANCELLED | BLOCKED | SUSPENDED | QUARANTINED
```

`[DOCUMENTED_ONLY]` — no full agent lifecycle FSM in code; research worker has process-level lifecycle only.

**Critical separations in UI:**

| Display | Must NOT visually imply |
| --- | --- |
| ACTIVE (working) | AUTHORIZED (governance grant) |
| AUTHORIZED | TRUSTED (epistemic) |
| TRUSTED | CORRECT (truth) |
| REGISTERED (registry row) | OPERATIONAL (can execute) |

Slice 1 seeds all 19 roles at `MaturityLevel.REGISTERED` (0) — below `MINIMUM_MATURITY_FOR_ALLOW` (2). UI must show maturity explicitly.

### 7.4 Mission lifecycle states (composed)

**Lifecycle dimension** (maps partially to `TaskState` / `ResearchMissionState`):

```text
DRAFT | PLANNING | PROPOSED | AUTHORIZED | ACTIVE | WAITING
BLOCKED | VERIFICATION | ACCEPTANCE | COMPLETE | FAILED | CANCELLED | REJECTED
```

Overlay dimensions (not in TaskState — must be separate):

```text
evidence_status:     NONE | PARTIAL | SUFFICIENT | STALE | CONTRADICTED
verification_status: NOT_REQUESTED | PENDING | PASS | FAIL | INCONCLUSIVE
acceptance_status:   NOT_REQUIRED | PENDING | ACCEPTED | REJECTED | DEFERRED
```

### 7.5 Evidence, claim, verification, acceptance, change proposal states

**Evidence** — bind to `EvidenceState` + `verification_status` + freshness:

```text
REGISTERED | VALID | STALE | SUPERSEDED | REVOKED
+ verification: UNVERIFIED | PASS | FAIL | INCONCLUSIVE
+ freshness: computed from retrieval_timestamp, expires_at, freshness_max_age_seconds
```

**Claim** — bind to `ClaimState`:

```text
DRAFT | SUBMITTED | CHALLENGED | VERIFIED | REJECTED | SUPERSEDED
```

Note: `ClaimState.VERIFIED` ≠ organizational acceptance — verification dimension still required.

**Verification** — bind to `VerificationRecord`:

```text
status: UNVERIFIED | PASS | FAIL | INCONCLUSIVE
kind:   INDEPENDENT | SELF_CHECK
```

**Acceptance** — bind to `Approval` artifact + human decision record:

```text
NOT_REQUIRED | PENDING | ACCEPTED | REJECTED | DEFERRED | EXPIRED | REVOKED
```

**Change proposal** — `[PROPOSED]` (no dedicated type in Slice 2B):

```text
DETECTED | PROPOSED | IMPACT_ANALYSIS | AWAITING_APPROVAL
APPROVED | REJECTED | IMPLEMENTING | VERIFYING | ACCEPTED | SUPERSEDED
```

---

## 8. Information Architecture

### 8.1 Design principle

**Progressive disclosure over navigation sprawl.** Not every concept becomes top-level nav. Agent-17 §36: conversation-first, not 19-agent admin console.

### 8.2 Primary navigation (Layer A — default)

| Surface | Route `[PROPOSED]` | Purpose | Layer |
| --- | --- | --- | --- |
| **Agent One Home** | `/` | What is happening? What needs me? | A |
| **Conversation** | `/conversation` | Primary Agent One dialogue | A |
| **Decision Inbox** | `/decisions` | Human gates only — no noise | A |
| **Missions** | `/missions` | Active/pending mission list | A |
| **System Status** | `/status` | CURRENT mode, capability honesty | A |

### 8.3 Secondary navigation (Layer B — organizational transparency)

| Surface | Route `[PROPOSED]` | Access |
| --- | --- | --- |
| Mission Detail | `/missions/:id` | From home/missions |
| Agent Detail | `/agents/:id` | Drill-down only |
| Evidence Explorer | `/evidence` | Expert/curious path |
| Contradictions | `/contradictions` | Standing + mission-scoped |
| Verification | `/verification` | IV pipeline visibility |
| Organizational Map | `/org` | Self-model, capabilities |
| Memory | `/memory` | Post-MVP |
| Changes | `/changes` | Change propagation tracker |
| Audit | `/audit` | Expert mode entry |
| Capabilities | `/capabilities` | Gap registry |

### 8.4 Contextual drill-down (not top-level)

- Claims, hypotheses, predictions, observations — accessed via Evidence Explorer lineage
- Raw events, envelope hashes, instruction stack layers — Expert Mode panels
- Agent roster full grid — Expert Mode; default is summary count only
- AHOS product surfaces — separate app shell; never merged nav without HD-17-04

### 8.5 Modal/panel patterns

| Pattern | Use |
| --- | --- |
| **Right inspector panel** | Mission/evidence/agent detail without losing conversation context |
| **Approval modal** | Multi-step WHAT/WHY/WHO/IMPACT/RISK — never one-click confirm |
| **Capability gap panel** | Inline when action blocked |
| **Contradiction drawer** | Side-by-side positions with evidence refs |
| **Context banner** | Stale context, Dual-19, CURRENT mode — persistent when relevant |

### 8.6 Expert-only views

- Raw audit event stream with hash chain verification UI
- Mission DAG graph (when scale permits)
- Inter-agent message inspector (when transport exists)
- TCB command ingress log
- Schema/version mismatch diagnostics
- Frontend client observability dashboard

---

## 9. Two-Layer Interface

### 9.1 Layer A — Cognitive / Human Interface

Answers in ≤1 screen without specialist IDs:

```text
What did I ask?
What is happening?
What did the organization learn?
What needs me?
```

**Layout `[PROPOSED]`:** Conversation-first desktop — conversation left (60%), contextual panel right (40%, collapsible). Mobile: conversation + Decision Inbox; Layer B via deep links.

**Density modes:** Calm (default) | Standard | Expert — affects field visibility, not authority.

### 9.2 Layer B — Organizational Transparency

Answers audit questions:

```text
Which mission? Which agents? Which evidence? Which claims?
Which contradictions? Which verification? Which audit events?
Which source? Which context version?
```

### 9.3 A → B transition without context loss

```text
Layer A summary card
  → [Inspect mission] preserves conversation scroll + opens inspector
  → [View evidence] deep-links with breadcrumb: Home > Mission-042 > evidence.abc
  → [Back to summary] restores Layer A focus + highlights what changed
```

**State preservation:** URL encodes drill path; conversation state in session store; inspector stack is push/pop navigation.

---

## 10. Drill-Down Architecture

### 10.1 Progressive levels (Agent-17 §4.4 — technical binding)

| Level | Question | Default surfacing | Route segment |
| --- | --- | --- | --- |
| **0** | What is happening? | Phase summary, pending decisions | `/` |
| **1** | Why? | Intent, constraints, blockers | `/missions/:id#intent` |
| **2** | Which agents? | Delegation roles, not prompts | `/missions/:id/agents` |
| **3** | Which evidence? | Evidence IDs, sources, freshness | `/missions/:id/evidence` |
| **4** | Which claims? | Claim/hypothesis objects | `/evidence/:id/claims` |
| **5** | Which verification? | Verification records, kind | `/verification/:id` |
| **6** | Which artifacts? | File paths, test refs (L0/L1) | `/evidence/:id/source` |
| **7** | Which audit/event? | Audit chain, envelope IDs | `/audit/:eventId` |

Level 0 must never require Level 2+ for a status question.

### 10.2 Routing model `[PROPOSED]`

```text
/                                    → Agent One Home
/conversation                        → Agent One dialogue
/decisions                           → Decision Inbox
/decisions/:id                       → Approval detail
/missions                            → Mission list
/missions/:missionId                 → Mission detail (composed status)
/missions/:missionId/agents          → Level 2
/missions/:missionId/evidence        → Level 3
/agents/:agentId                     → Agent card detail
/evidence/:evidenceId                → Evidence explorer entry
/evidence/:evidenceId/lineage        → Provenance chain
/contradictions/:contradictionId     → Contradiction detail
/audit                               → Audit explorer
/audit/:eventId                      → Level 7
/expert                              → Expert mode hub
/status                              → System mode + capabilities
/settings                            → Locale, density, motion, a11y
```

### 10.3 URL/state encoding

- Entity IDs in path (stable, shareable): `mission.20260914-018`, `evidence.abc123`
- Inspector depth via hash or nested path — not query-string-only (SR accessibility)
- `?as_of=` optional for historical projection snapshot (expert)
- `?plane=A|D|Research` when Dual-19 requires explicit plane context

### 10.4 Breadcrumbs

```text
خانه ← ماموریت MISSION-042 ← شواهد evidence.abc ← منبع source.def
(Home ← Mission ← Evidence ← Source)
```

Machine IDs remain LTR within RTL breadcrumb.

### 10.5 Permissions (future)

Frontend hides action buttons based on **authoritative capability projection** — never client-side authorization alone. Read paths may be wider than write paths. Expert mode may require explicit toggle + session flag.

### 10.6 Stale data handling on drill-down

If projection `as_of` exceeds freshness SLA while user drills:

```text
⚠ PROJECTION STALE — last updated 14m ago
[Refresh] [View anyway with STALE watermark]
```

Never silently upgrade stale to live appearance.

---

## 11. Frontend Data Contracts

Conceptual read-model DTOs aligned with Slice 2B — **no invented fields contradicting epistemic model**.

### 11.1 Common fields (all projections)

```text
identity          — stable ID with namespace prefix
version           — artifact/task version (int ≥ 1)
schema_version    — projection schema version
status_dimensions — StatusDimensionBundle
timestamps        — created_at, updated_at (UTC ISO8601)
provenance        — creator_principal_id, command_id, method, source_refs
mission_binding   — mission_id | null
agent_binding     — principal_id | null
verification_state— orthogonal dimension
acceptance_state  — orthogonal dimension
staleness         — FreshnessState + as_of + ttl_hint
plane             — A | D | Research | Human (for agents)
```

### 11.2 Entity contracts

**AgentProjection**

```text
agent_id, display_name, role_label, plane, commander_id
lifecycle_state, maturity_level, governance_status
capabilities: CapabilityStatus (grants + delegations — read-only)
current_mission_id | null
authority_summary (scoped — not implied full org authority)
last_activity_at | null
known_limitations: string[]
current_context_ref | null
verification_status (of last major output — not agent trustworthiness)
```

**MissionProjection**

```text
mission_id, title, objective, constraints[]
commander_id, context_version, context_hash
lifecycle + evidence + verification + acceptance dimensions
agents: AgentParticipation[] (role, state — not peer command arrows)
blockers[], capability_gaps[], pending_human_decisions[]
contradiction_ids[], evidence_ids[]
parent_mission_id | null, child_mission_ids[]
last_meaningful_update_at
```

**EvidenceProjection** — maps `Evidence` dataclass:

```text
evidence_id, source_id, producer_principal_id
content_ref, content_hash, extraction_method
validity_status (EvidenceState), verification_status
retrieval_timestamp, observation_timestamp, expires_at
freshness_max_age_seconds, assurance (internal — expert only by default)
supersedes_evidence_id | null, lineage[]
linked_claim_ids[], verification_ids[]
```

**ClaimProjection** — maps `Claim`:

```text
claim_id, statement, evidence_ids[], verification_ids[]
lifecycle_state (ClaimState), producer_principal_id
```

**ContradictionProjection** — maps `ContradictionCase`:

```text
contradiction_id, left_artifact_id, right_artifact_id, rationale
lifecycle_state (ContradictionState)
affects_candidate_ids[], resolution_evidence_ids[]
conflict_type [PROPOSED], severity [PROPOSED], required_action [PROPOSED]
```

**VerificationProjection** — maps `VerificationRecord`:

```text
verification_id, target_artifact_id
producer_principal_id, verifier_principal_id
verification_kind (INDEPENDENT | SELF_CHECK)
status (VerificationStatus), method, evidence_ids[]
independence_warning: bool (computed: same principal or SELF_CHECK)
```

**AcceptanceProjection** — maps `Approval`:

```text
approval_id, approver_principal_id, action, resource_id, capability_id
task_id | null, candidate_id | null
issued_at, expires_at, lifecycle_state (ApprovalState)
is_active (computed with now)
```

**AuditEventProjection** — maps `AuditEvent`:

```text
event_id, timestamp, actor_principal, command_id, operation, result
previous_state, resulting_state, payload_hash, event_hash, previous_event_hash
correlation_id, causation_id, policy_version
```

**CapabilityProjection**

```text
capability_id, status: AVAILABLE | PLANNED | NOT_IMPLEMENTED | DENIED
evidence_refs[], impact_description
```

**OrganizationStateProjection**

```text
mode: CURRENT_MANUAL | OPERATIONAL | DEGRADED | OFFLINE
substrate_maturity: SUBSTRATE-1..N
active_missions_count, pending_decisions_count
open_contradictions_count, launch_blockers_count
capability_gaps[], standing_contradictions[] (Dual-19)
projection_as_of, backend_version, frontend_min_backend_version
```

**ContextSnapshotProjection** `[PLANNED]`

```text
context_id, version, hash, assembled_at, source_count
stale_flags[], conflict_flags[], recommendation
```

### 11.3 Write-side intent envelopes (not direct mutation)

```text
UserIntentEnvelope {
  intent_id, intent_class: VIEW | PROPOSE | REQUEST | COMMAND | APPROVE
  actor_principal_id, session_id, timestamp
  natural_language | structured_payload
  target_mission_id | null
  client_version
}
```

Frontend sends intent; backend returns `CommandResult` with `ACCEPTED | DENIED | REQUIRES_REVIEW`.

---

## 12. Backend Boundary

### 12.1 Layer classification

| Element | Status | Evidence |
| --- | --- | --- |
| Slice 2B TCB + stores | `[EXISTS]` in-process | `agent_org/tcb.py` |
| ReadOnlyProjections | `[EXISTS]` | `agent_org/projections.py` |
| Audit hash chain | `[EXISTS]` in-memory | `agent_org/audit.py` |
| HTTP/IPC API for projections | `[ABSENT]` | No server entry point |
| BFF (Backend-for-Frontend) | `[PROPOSED]` | Agent-14 local service |
| Mission Controller | `[ABSENT]` | Agent-16 confirmed |
| Agent One service | `[ABSENT]` | No service loop |
| Message bus | `[ABSENT]` | `TRANSPORT = NONE` |
| Cursor federation bridge | `[ABSENT]` | Agent-14 Phase 1 |
| Durable persistence | `[ABSENT]` | In-memory only |
| Slice 1 ↔ 2B federation | `[ABSENT]` | Registry model DEFERRED |
| Event stream transport | `[ABSENT]` | No WebSocket/SSE server |

### 12.2 Target architecture `[PROPOSED]`

```text
┌─────────────────────────────────────────────────────────────┐
│  Frontend (local web app — Windows-first)                   │
│  Read: projections + event stream                           │
│  Write: UserIntentEnvelope only                             │
└───────────────────────────┬─────────────────────────────────┘
                            │ localhost HTTP + SSE (recommended)
┌───────────────────────────▼─────────────────────────────────┐
│  Org API / BFF `[PROPOSED]`                                  │
│  - Aggregates read projections                              │
│  - Validates intent schema                                  │
│  - Never bypasses TCB for mutations                         │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌─────────────────┐
│ Agent One     │   │ Mission       │   │ TCB             │
│ Service       │   │ Controller    │   │ (Slice 2B/2C)   │
│ `[ABSENT]`    │   │ `[ABSENT]`    │   │ `[EXISTS]` mem  │
└───────────────┘   └───────────────┘   └─────────────────┘
                            │
                    ┌───────▼───────┐
                    │ Durable Store │
                    │ `[ABSENT]`    │
                    └───────────────┘
```

### 12.3 Frontend mutation prohibition

Frontend **must not**:

- Call TCB `CommandIngress` directly without authenticated local boundary
- Write to SQLite, filesystem governance docs, or git
- Mutate AHOS product state
- Simulate `CommandResult.ACCEPTED` without backend confirmation

---

## 13. Read/Write Separation

### 13.1 CQRS-like separation (recommended where runtime exists)

**Read path:** Frontend consumes immutable **read projections** versioned with `as_of` timestamp.

**Write path:**

```text
USER INTENT → Intent Validator → Authorized Command → TCB/MC → CommandResult → Event → Projection refresh
```

Not:

```text
BUTTON → optimistic "Done" → local state mutation
```

### 13.2 Where separation is necessary

| Scenario | Separation required |
| --- | --- |
| Mission approval | YES — await authoritative state transition |
| Knowledge promotion | YES — TCB gate D-01/D-04 |
| Authority delegation | YES — grant store write |
| Verification recording | YES — producer≠verifier enforced in backend |
| Acceptance | YES — Approval artifact creation |
| Status display | YES — projection read only |
| Conversation scroll position | NO — local UI state only |
| Inspector panel open/closed | NO — local UI state |
| Locale/density preference | NO — local preference store |

### 13.3 Where CQRS may be overengineering (initially)

- Single-user local-first MVP with synchronous command round-trip — simple request/response may suffice before full event sourcing UI
- Static CURRENT mode documentation viewer before MC exists — read-only markdown + manual mode banner

### 13.4 Optimistic UI policy

**Strong warning:** Do not use optimistic UI for authority-bound actions.

Allowed optimistic patterns:

- Typing indicator for Agent One response **only when backend stream confirms processing**
- UI pending state: `REQUESTED` — not `DONE`

```text
User clicks APPROVE → UI shows "Approval requested…" (REQUESTED)
Backend CommandResult ACCEPTED → UI shows "Authorized" (AUTHORIZED)
Backend DENIED → UI shows denial reason — revert any pending indicator
```

---

## 14. Real-Time Architecture

### 14.1 Requirements

- Windows-first, local-first, single-user initially
- Low cost, no mandatory cloud
- Offline resilience, reconnect, multi-tab coherence
- Event ordering, deduplication, staleness visibility
- Org status is low-frequency relative to trading dashboards

### 14.2 Option evaluation

| Transport | Pros | Cons | Verdict |
| --- | --- | --- | --- |
| **WebSocket** | Bidirectional, low latency | More complex reconnect/auth; overkill for read-heavy MVP | Phase 2+ for Agent One streaming dialogue |
| **Server-Sent Events (SSE)** | Simple unidirectional push; HTTP-friendly; auto-reconnect in browsers | One-way; limited IE (irrelevant for modern) | **Primary recommendation `[PROPOSED]`** for mission/event updates |
| **Polling** | Trivial; works offline fallback | Latency; waste; misses ordering guarantees | **Fallback** when SSE unavailable |
| **Event streams (file tail)** | Matches audit JSONL pattern | Not browser-native | Expert mode / local dev only |
| **Push notifications** | Mobile re-engagement | Requires OS integration; Telegram `[PLANNED]` not assumed | Post-MVP |

### 14.3 Recommended architecture `[PROPOSED]`

```text
Primary:   SSE /org/events?since=cursor — mission, agent, verification, decision events
Fallback:  Poll /org/projections/snapshot?as_of= — every 30s when SSE down
Reconnect: Last-Event-ID header + cursor dedup on client
Multi-tab: BroadcastChannel or localStorage leader election for single SSE connection
Offline:   Show OFFLINE banner; cache last snapshot with STALE watermark; queue intents locally (NOT auto-send)
```

### 14.4 Event delivery guarantees (UI assumptions)

- **At-least-once** delivery — client must dedupe by `event_id`
- **Partial ordering** per aggregate (mission_id, agent_id) — UI reconciles
- **No silent gap** — heartbeat every 30s; missing heartbeat → DEGRADED

---

## 15. Event Model

### 15.1 Conceptual organizational events

| Event | Source authority | Display impact |
| --- | --- | --- |
| `MISSION_CREATED` | MC | Add to mission list |
| `MISSION_ACTIVATION_REQUESTED` | MC/Lifecycle | Show pending authorization |
| `MISSION_STARTED` | MC | Lifecycle → ACTIVE |
| `AGENT_ACTIVATED` | Lifecycle Controller | Agent lifecycle badge |
| `AGENT_COMPLETED` | Lifecycle Controller | Agent COMPLETED — not verification |
| `AGENT_FAILED` | Lifecycle Controller | Failure card with typed reason |
| `EVIDENCE_RECEIVED` | TCB/ingestion | Evidence explorer update |
| `CLAIM_CREATED` | TCB | Claim linkage in mission |
| `CONTRADICTION_DETECTED` | TCB | Contradiction badge + inbox if severe |
| `VERIFICATION_REQUESTED` | MC/IV plane | Verification PENDING |
| `VERIFICATION_COMPLETED` | TCB | Verification dimension update |
| `ACCEPTANCE_REQUESTED` | MC/Agent One | Decision Inbox item |
| `ACCEPTANCE_COMPLETED` | TCB (Approval) | Acceptance stamp |
| `CAPABILITY_GAP_DETECTED` | Agent One/MC | Capability gap card |
| `CONTEXT_UPDATED` | Context gate | Context banner refresh |
| `CONTEXT_STALE` | Context gate | Stale context warning |
| `CHANGE_PROPOSED` | Governance | Changes tracker |
| `CHANGE_ACCEPTED` | Governance | Memory/governance update |
| `CHANGE_REJECTED` | Human | Terminal with reason |
| `AGENT_QUARANTINED` | Security path | Quarantine badge + blocked actions |
| `MISSION_BLOCKED` | MC | Blocker surfaced in home |

### 15.2 Event envelope (conceptual)

```text
event_id          — unique, idempotency key
event_type        — from catalog above
aggregate_type    — mission | agent | evidence | ...
aggregate_id      — stable ID
sequence          — monotonic per aggregate (when available)
occurred_at       — UTC
recorded_at       — UTC (may differ — show both in expert mode)
authority         — service that emitted (MC, TCB, Agent One)
schema_version    — event schema version
payload           — typed, minimal
causation_id      — upstream command/event
correlation_id    — mission/session scope
```

### 15.3 Event arrival ≠ canonical state

UI maintains:

```text
projected_state  — derived from events + snapshot
last_event_id    — cursor
last_snapshot_at — authoritative checkpoint
```

On conflict: **snapshot wins** for display; event flagged `CONFLICT` in expert mode.

---

## 16. Eventual Consistency

### 16.1 Scenarios and UI response

| Scenario | UI behavior |
| --- | --- |
| Event arrives late | Apply with "late update" indicator; refresh affected badges |
| Event arrives twice | Dedupe by `event_id` — no double animation/alert |
| Event out of order | Reconcile per aggregate; show brief "reconciling…" if needed |
| Event references unknown object | Show orphan event in expert audit; placeholder "unknown entity" in standard mode |
| Event conflicts with projection | Prefer snapshot; flag conflict; never silently merge |
| Event belongs to stale mission | Ignore for Layer A; show in audit with "superseded mission" label |
| Event references superseded context | Show with context version mismatch banner |

### 16.2 Impossible state prevention

UI validation layer (client-side **display guard** — not authority):

```typescript
// [PROPOSED] display guard — rejects rendering impossible composites
function validateDisplayBundle(bundle: StatusDimensionBundle): DisplayGuardResult {
  if (bundle.dimensions.acceptance === 'ACCEPTED' &&
      bundle.dimensions.verification === 'UNVERIFIED' &&
      bundle.requirements?.verification_required) {
    return { render: true, warnings: ['ACCEPTANCE_WITHOUT_VERIFICATION'] };
  }
  // ... additional rules
}
```

Warnings render as explicit UI alerts — not silent correction.

---

## 17. Staleness

### 17.1 Freshness state machine

```text
LIVE      — SSE connected; projection age < 5s
FRESH     — projection age < SLA (configurable per entity type)
STALE     — projection age ≥ SLA
UNKNOWN   — no timestamp or clock skew detected
OFFLINE   — backend unreachable
DEGRADED  — partial connectivity; polling fallback active
```

### 17.2 SLA hints by entity type `[PROPOSED]`

| Entity | FRESH threshold | STALE treatment |
| --- | --- | --- |
| Agent lifecycle | 30s | Muted pulse; "last seen Xm ago" |
| Mission status | 60s | Stale badge on mission card |
| Verification | 5m | Never show as "current verification" |
| Context snapshot | 1h | Context refresh recommendation |
| Organization snapshot | 2m | Home panel stale overlay |
| Audit events | append-only | Events never "stale" — timestamps always shown |

### 17.3 Visual treatment

Stale ≠ offline. Stale uses **clock icon + age text** — not red error color. Offline uses **explicit OFFLINE banner** with last cached snapshot labeled STALE.

---

## 18. Local-First Architecture

### 18.1 Environment constraints

```text
OS:           Windows-first
Deployment:   Local service + browser (localhost)
Cost:         Free-first — no mandatory cloud/VPS
Users:        Single human principal initially (Mehrdad)
Network:      Localhost primary; optional future remote read-only
```

### 18.2 Component topology `[PROPOSED]`

```text
Browser (http://127.0.0.1:PORT)
  ↔ Org Local Service (Python — MC + API + SSE)
      ↔ SQLite (durable state — Phase 1+)
      ↔ TCB process boundary (Phase 1 end goal)
```

Frontend static assets may be served by same local service or embedded WebView — no cloud CDN required.

### 18.3 Offline mode

| State | Behavior |
| --- | --- |
| Backend down | OFFLINE banner; read last cached projections with STALE |
| Intent while offline | Queue locally with `QUEUED_OFFLINE` — **do not** show as executed |
| Reconnect | Replay SSE from cursor; refresh snapshot; flush intent queue with user confirm |
| Cache invalidation | Version bump on `schema_version` or `backend_version` mismatch |

### 18.4 Local cache architecture

```text
IndexedDB or SQLite WASM `[PROPOSED choice: IndexedDB for snapshots, avoid WASM initially]`
  - projection_snapshots keyed by entity_id + version
  - event_cursor
  - pending_intents (offline queue)
  - user_preferences (locale, density, reduced_motion)
```

Cache is **display cache only** — never authoritative.

### 18.5 Safe fallback

When API schema mismatch:

```text
Frontend version X requires backend ≥ Y
Current backend: Z
[View read-only cached data] [Download diagnostic bundle]
```

Never guess unknown fields — render `UNKNOWN_FIELD` in expert mode only.

---

## 19. Frontend Security

### 19.1 Threat surface summary

The org frontend handles **untrusted agent output**, **high-authority actions**, and **localhost API exposure** on a Windows workstation.

### 19.2 Authentication & session `[PROPOSED]`

Initial single-user local:

```text
Local service binds 127.0.0.1 only (not 0.0.0.0) by default
Session: short-lived token issued by local service on browser open
Human principal: principal.human.mehrad (or configured id)
No password initially — OS user boundary + localhost binding
Future: optional PIN/biometric for approval actions
```

### 19.3 CSRF / clickjacking

- SameSite=Strict cookies for session
- `X-Frame-Options: DENY` or CSP `frame-ancestors 'none'`
- Approval modals require explicit focus trap — no iframe embedding

### 19.4 XSS / injection (critical)

Agent output is **untrusted data**:

- No `dangerouslySetInnerHTML` on agent content
- No `eval`, no dynamic script from messages
- Markdown → sanitized subset only (§20)
- URLs validated; `javascript:` blocked
- SVG from agents: disallow or sanitize aggressively

### 19.5 CSP `[PROPOSED]`

```text
default-src 'self';
script-src 'self';
style-src 'self' 'unsafe-inline';  /* minimize inline over time */
img-src 'self' data: blob:;
connect-src 'self' http://127.0.0.1:* ws://127.0.0.1:*;
frame-ancestors 'none';
base-uri 'self';
form-action 'self';
```

### 19.6 Token storage

- Session token: `httpOnly` cookie preferred over localStorage
- Never store TCB credentials or AHOS secrets in browser storage
- Approval intents: memory-only until submitted

### 19.7 Local API exposure

| Risk | Mitigation |
| --- | --- |
| Localhost accessible to other users on machine | Bind 127.0.0.1; optional auth token |
| Malicious browser extension reading DOM | Minimize secret display; short sessions |
| Another app calling localhost API | CSRF token + Origin check |
| Agent output prompt injection via displayed content | Sanitize; separate system prompts from rendered content; "untrusted content" banner |

### 19.8 IPC (future desktop shell)

If Electron/Tauri wrapper added: use contextIsolation, disable nodeIntegration in renderer, preload script allowlist only.

---

## 20. Trusted Rendering

### 20.1 Policy matrix

| Content type | Renderer | Trust level | Notes |
| --- | --- | --- | --- |
| User input | Plain text / controlled input | Trusted source | Still length-limited |
| Agent One structured output | JSON schema validated → components | Semi-trusted | Schema-bound rendering only |
| Agent markdown reports | Sanitized Markdown → React | **Untrusted** | No raw HTML pass-through |
| Code blocks | Syntax highlighter, static | Untrusted | No execution |
| JSON evidence | Pretty-print, collapsible | Untrusted | No `__proto__` tricks in display |
| Logs | Monospace, escaped | Untrusted | |
| File paths | `<code dir=ltr>` escaped | Untrusted | Click → confirm before open |
| URLs | Allowlist scheme http/https; rel=noopener | Untrusted | Confirm external navigation |
| Git hashes, IDs | LTR monospace | Trusted format | |
| Evidence text | Escaped + optional Markdown subset | Untrusted | |
| External provider data | Same as evidence | Untrusted | AHOS adapter boundary |
| SVG | Prefer disallow; if needed: DOMPurify SVG profile | Untrusted | No scripts/events |

### 20.2 Markdown safe subset `[PROPOSED]`

Allowed: paragraphs, headings, lists, blockquote, code fence, tables (simple), links (sanitized href), emphasis.

Forbidden: raw HTML, images from arbitrary URLs (initially), iframes, script-like attributes, data URIs in links.

Library candidates (implementation phase): `react-markdown` + `rehype-sanitize` with strict schema.

### 20.3 Prevent agent output → executable UI

```text
Agent JSON payload
  → JSON Schema validation
  → Component registry map (type → pre-approved React component)
  → Unknown type → JSON tree fallback (never dynamic component load)
```

No `new Function`, no `import()` from agent strings.

### 20.4 Bidirectional text (RTL/LTR)

Evidence may contain mixed scripts. Use Unicode bidi isolation (`\u2068`, `\u2069`) around LTR technical tokens in RTL paragraphs to prevent spoofing.

---

## 21. Command UX Boundary

### 21.1 Semantic action classes

| Class | Authority level | UI pattern |
| --- | --- | --- |
| **VIEW** | Read projection | No side effects; no confirm |
| **PROPOSE** | Agent One drafts | Draft badge; creates proposal record only |
| **REQUEST** | Human asks | Neutral input; not yet formalized |
| **COMMAND** | Human-approved, MC-bound | Scope hash, expiry, command ID displayed |
| **APPROVE** | Human L2 decision | Multi-field approval modal |
| **EXECUTE** | Runtime activation | Separate confirm after APPROVE — never merged |

### 21.2 Semantic action contract `[PROPOSED]`

```typescript
interface SemanticAction {
  action_id: string;
  action_class: 'VIEW' | 'PROPOSE' | 'REQUEST' | 'COMMAND' | 'APPROVE' | 'EXECUTE';
  label: LocalizedString;
  target_entity: EntityRef;
  required_confirmations: ConfirmationStep[];
  scope_preview: ScopePreview | null;
  reversibility: 'REVERSIBLE' | 'PARTIAL' | 'IRREVERSIBLE';
  expiry: ISO8601 | null;
  backend_endpoint: string;  // intent ingress — not direct DB
  optimistic_allowed: false;  // always false for APPROVE/COMMAND/EXECUTE
}
```

### 21.3 Dangerous pattern elimination

```text
❌ Single "Run" button: APPROVE + EXECUTE + side effects
✅ Step 1: Review proposal → Step 2: APPROVE (scope hash) → Step 3: EXECUTE (if separate activation)
```

Button labels must use action class vocabulary — Persian: `پیشنهاد`, `درخواست`, `تایید`, `اجرا`, `مشاهده`.

---

## 22. Approval UI

### 22.1 Approval categories (from Agent-17 §23)

Policy changes, authority changes, production changes, credential access, live execution, organizational structural changes, irreversible operations, Agent One constitutional changes, knowledge promotion, consequential mission activation.

### 22.2 Approval surface required fields

Every approval modal displays:

```text
WHAT          — scoped action in plain language
WHY           — rationale + mission link
WHO REQUESTED — principal_id + plane
MISSION       — mission_id + constraints
IMPACT        — affected resources, agents, artifacts
RISK          — RiskLevel + typed risks
EVIDENCE      — linked evidence IDs (clickable)
VERIFICATION  — current verification status of subject
REVERSIBILITY — REVERSIBLE | PARTIAL | IRREVERSIBLE + rollback plan if any
EXPIRY        — approval.expires_at countdown
```

### 22.3 Approval UX rules

- **Never** equivalent to blind confirmation — require scroll-through for IRREVERSIBLE
- Typed confirmation for STOP ORGANIZATION, quarantine, production paths
- Show `Approval` artifact fields that will be created on confirm
- On submit: `REQUESTED` → await `CommandResult` → `ACTIVE` or `DENIED`
- Expired approval: visually distinct from never-requested

### 22.4 Knowledge promotion approval (Slice 2B D-01/D-04)

Separate from mission approve. Must show:

```text
Candidate ID, proposition, evidence chain, open contradictions
Promotion ≠ truth — organizational memory only
```

---

## 23. Decision Inbox

### 23.1 Purpose

Surface **only** items requiring Mehrdad — anti-noise.

### 23.2 Inbox item types

```text
APPROVAL_REQUIRED
CONFLICT_UNRESOLVED (ContradictionCase OPEN + severity ≥ threshold)
CAPABILITY_GAP (blocks requested mission)
HIGH_RISK_CHANGE
POLICY_AMENDMENT
VERIFICATION_FAILURE
QUARANTINE_DECISION
ACCEPTANCE_PENDING
MISSION_ACTIVATION (consequential)
```

### 23.3 Excluded from inbox (digest optional)

- Routine specialist progress ticks
- Self-check verifications
- Informational mission updates
- NO_ACTION_REQUIRED (valid empty state — prominent)

### 23.4 Inbox item structure

```text
DecisionItem {
  item_id, item_type, severity, created_at, expires_at | null
  title, summary, mission_id, entity_refs[]
  recommended_actions: SemanticAction[]
  evidence_refs[], contradiction_refs[]
  ack_required: bool
}
```

### 23.5 Priority & cap

Max 3 items in Layer A home; rest queued with count badge. Sort: CRITICAL → expiry → created_at.

---

## 24. Contradiction Visualization

### 24.1 Conceptual model (first-class)

```text
CONTRADICTION
├── Position A
│   ├── artifact_ref (claim/evidence/candidate)
│   ├── producer_principal
│   └── supporting_evidence[]
├── Position B
│   ├── artifact_ref
│   ├── producer_principal
│   └── supporting_evidence[]
├── Conflict Type [PROPOSED]: INTERPRETATION | SCOPE | TEMPORAL | IDENTITY | METHODOLOGY
├── Severity: CRITICAL | HIGH | MEDIUM | LOW
├── Verification Status (orthogonal)
├── Resolution Status (ContradictionState)
└── Required Action (PROPOSAL — not auto-executed)
```

### 24.2 Visual layout `[PROPOSED]`

**Split panel** (not pie chart):

```text
┌──────────────────────┬──────────────────────┐
│ Position A           │ Position B           │
│ Agent-08             │ Agent-11             │
│ claim.x / evidence.a │ claim.y / evidence.b │
│ [View lineage]       │ [View lineage]       │
└──────────────────────┴──────────────────────┘
Conflict: IDENTITY · Severity: HIGH · State: OPEN
Independent verification: REQUIRED
[Approve reconciliation mission] [Defer] [Override with reason]
```

### 24.3 Forbidden representations

```text
❌ Agent A = 70% vs Agent B = 30%
❌ Averaged compromise text
❌ Hidden contradiction behind "consensus summary"
✅ RETAINED_UNCERTAIN as valid terminal display
```

### 24.4 Standing contradiction: Dual-19

Persistent org-level badge until HD-16-02 resolved:

```text
⚠ STANDING CONTRADICTION: Dual-19 registry planes (A vs D)
```

---

## 25. Evidence Visualization

### 25.1 Evidence explorer structure

```text
Source (source_id, locator, content_hash)
  ↓
Evidence (validity, freshness, verification)
  ↓
Claims (ClaimState)
  ↓
Hypotheses / Predictions
  ↓
Experiments / Observations
  ↓
VerificationRecords (kind + status)
  ↓
Acceptance (Approval)
```

**No implied causal arrows** unless `lineage[]` or explicit link exists — use solid vs dashed connectors.

### 25.2 Evidence card fields

```text
evidence_id · type badge · EvidenceState · verification_status
source_id · producer · retrieval_timestamp · expires_at
freshness: FRESH|STALE · assurance (expert-only label)
content_ref (link) · content_hash (copy) · extraction_method
supersedes · lineage · linked claims/contradictions
```

### 25.3 Provenance display

Always show:

```text
creator_principal_id · command_id · method · source_refs[]
```

Click any ID → Level 7 audit drill if available.

### 25.4 Support eligibility

Surface backend rule from `Evidence.is_eligible_positive_support()` result — do not recompute trust client-side as authority.

---

## 26. Graph Architecture

Graphs are **optional accelerators**, not default truth surfaces.

### 26.1 Evaluation matrix

| Graph type | Purpose | User question | Scale | Verdict |
| --- | --- | --- | --- | --- |
| **Command tree** | Show delegation authority | Who commanded whom? | ≤20 nodes MVP | **List + tree view toggle** — graph Phase 2 |
| **Mission DAG** | Parallel mission structure | What depends on what? | ≤30 nodes | **Useful** — table fallback required |
| **Evidence lineage** | Provenance chain | Where did this come from? | ≤50 nodes | **Useful** — vertical timeline primary |
| **Contradiction graph** | Related conflicts | What conflicts cluster? | Low count | **Optional** — split panel primary |
| **Organizational memory** | Supersession chain | What replaced what? | Grows over time | **Timeline + table** over force graph |
| **Dependency graph** | Capability/blockers | What blocks launch? | ~12 blockers | **Checklist primary** — graph optional |

### 26.2 Graph interaction requirements

- Keyboard navigable nodes
- Textual adjacency list always available (accessibility)
- No physics simulation by default (reduced motion)
- Node labels: role + ID — not prompt excerpts
- Edge types visually distinct: **command** (solid) vs **evidence** (dashed) vs **knowledge** (dotted)

### 26.3 Failure modes

| Failure | Mitigation |
| --- | --- |
| Hairball at 19 agents | Default hidden; summary count only |
| Misread peer edge as command | Edge legend + type labels |
| Animated layout implies live activity | Static layout default; no force "breathing" |
| Color-only node status | Shape + text (§32) |

### 26.4 Alternative representations (preferred for MVP)

- **Tables** for agent roster, audit events, verification queue
- **Timelines** for mission history, evidence freshness
- **Stacked status bars** for orthogonal dimensions
- **Split panels** for contradictions

---

## 27. Organizational Map

### 27.1 Purpose

Show organizational self-model — who exists, who is active, command relationships — without misleading authority.

### 27.2 Structure

```text
Agent One (PRIMARY_ORGANIZATIONAL_AGENT — runtime NOT_IMPLEMENTED labeled)
  ↓ command edges (solid)
Specialists (plane-labeled)
  ↔ knowledge edges (dotted) — NOT command
  ↔ mission participation (temporary, dashed, time-bounded)
  ↔ peer requests (dash-dot, labeled REQUEST not COMMAND)
```

### 27.3 Current honest map (CURRENT mode)

```text
Mehrdad (Human Principal)
  ↓ manual (Cursor)
Cursor Sessions (acting as AGENT-NN — no runtime binding)
  ↓ markdown artifacts
Mehrdad

Agent One node: PRESENT as intended root — labeled RUNTIME NOT IMPLEMENTED
19 logical roles: REGISTERED maturity 0 — not operational grid
```

### 27.4 Dual-19 display

Never unified "19 agents" without disclaimer:

```text
Plane A: 19 seeded logical roles
Plane D: 19 blueprint roles (not seeded)
Research: RESEARCH_ANALYST_AGENT
Standing contradiction: UNRESOLVED
```

---

## 28. Agent Card

### 28.1 Canonical Agent Card fields

```text
Agent ID · Role · Plane (A|D|Research)
Commander · Lifecycle state · Maturity level
Capabilities (grants) vs Authority (delegations) — separate sections
Current mission · Last activity
Verification status (of outputs — not agent morality)
Known limitations · Current context ref
Governance status · Capability gaps affecting this agent
```

### 28.2 Separations (mandatory sections)

```text
CAPABILITY        — what agent could do if authorized (registry/policy)
AUTHORITY         — current grants + delegations (CapabilityStatus projection)
CURRENT AUTH      — active approval scopes
AVAILABILITY      — runtime: IDLE|ACTIVE|DORMANT|NOT_IMPLEMENTED
```

### 28.3 Default vs expert

**Calm mode:** "Security specialist" — hide AGENT-08 unless expanded.

**Expert mode:** `agent.security · Plane A · Maturity REGISTERED · Lifecycle IDLE`

---

## 29. Mission Card

### 29.1 Canonical fields

```text
Mission ID · Title · Objective · Constraints
Commander · Phase (lifecycle dimension)
Composed status bar (lifecycle | evidence | verification | acceptance)
Agents (count + roles) · Blockers · Capability gaps
Contradictions (count + link) · Evidence (count + link)
Pending human decisions · Last meaningful update
Context version · Parent/child mission links
```

### 29.2 Progress display rules

**No percentage bar** unless percentage maps to defined checklist:

```text
✓ Allowed: "3/5 deliverables submitted" (if deliverables[] defined)
✗ Forbidden: "73% complete" (semantic meaning absent)
```

### 29.3 Mission card states overlay example

```text
┌─────────────────────────────────────────────────┐
│ MISSION-042 · Autonomy Readiness Assessment     │
│ Lifecycle: ACTIVE │ Evidence: PARTIAL           │
│ Verification: PENDING │ Acceptance: NOT_STARTED │
│ ⏱ Updated 3m ago (FRESH)                         │
│ ⚠ 1 open contradiction · 1 decision required    │
└─────────────────────────────────────────────────┘
```

---

## 30. Agent One Home

### 30.1 Primary screen answers

```text
What is happening?
What needs me?
What changed?
What is blocked?
What is uncertain?
What did the organization learn?
What should I know now?
```

### 30.2 Layout zones `[PROPOSED]`

```text
┌─ CURRENT MODE BANNER ─────────────────────────────┐
├─ ORG SNAPSHOT (calm) ─────────────────────────────┤
│  Active missions: N · Decisions pending: N        │
│  Open contradictions: N · Capability gaps: N      │
├─ DECISION INBOX (max 3) ──────────────────────────┤
├─ AGENT ONE SUMMARY (Layer A prose + structured) ──┤
├─ RECENT CHANGES (since last visit) ───────────────┤
└─ NOTHING NEEDS ATTENTION (valid prominent state) ─┘
```

### 30.3 Anti-patterns on home

```text
❌ 19-agent live grid with pulsing online dots
❌ Fake message bus traffic ticker
❌ "All systems operational" when MC absent
✅ "SUBSTRATE-1 — NOT OPERATIONAL" honest label
✅ "Nothing needs your attention" when true
```

---

## 31. Expert Mode

### 31.1 Purpose

Advanced audit, debugging, governance review — **without weakening authority boundaries**.

### 31.2 Exposed surfaces

- Raw `AuditEvent` stream with hash chain verify button
- Mission DAG graph
- Agent graph with plane labels
- Evidence lineage graph
- TCB command results log
- Context version diff (when gate exists)
- Message envelope inspector (when bus exists)
- Verification artifacts with producer/verifier IDs
- Schema/version diagnostics
- Unknown/orphan events

### 31.3 Expert mode gates

- Explicit toggle — not default
- IRREVERSIBLE actions still require full approval flow
- Expert view does not grant extra backend permissions
- Watermark: `EXPERT VIEW — AUDIT PURPOSE`

---

## 32. Visual Language

### 32.1 Design principles

```text
REALITY > VISUAL POLISH
TRUST > WOW EFFECT
SEMANTIC CORRECTNESS > ANIMATION
EVIDENCE > BADGES
SHAPE + TEXT + ICON > COLOR ALONE
```

### 32.2 Semantic dimensions → visual encoding

| Dimension | Shape/icon | Color role (secondary) |
| --- | --- | --- |
| Epistemic KNOWN | Diamond outline | Neutral slate |
| Epistemic UNKNOWN | Dashed diamond | Muted gray |
| Epistemic CONTRADICTORY | Split diamond | Amber accent (not sole channel) |
| Lifecycle PROPOSED | Dotted circle | Blue-gray |
| Lifecycle ACTIVE | Solid circle (no pulse in calm mode) | Blue |
| Lifecycle COMPLETED | Circle check | Gray (not green "success") |
| Authorization | Shield | Purple-gray |
| Verification INDEPENDENT PASS | Check in box + "INDEPENDENT" | Teal |
| Verification SELF_CHECK | Check in box + "SELF_CHECK" | Muted |
| Acceptance ACCEPTED | Stamp | Green only with "ACCEPTED" text |
| Freshness STALE | Clock | Amber |
| Capability NOT_IMPLEMENTED | Lock | Gray |
| Severity CRITICAL | Triangle + text | Red accent + icon |

### 32.3 Forbidden mappings

```text
green ≠ good (epistemic)
red ≠ bad agent (may be honest failure report)
pulsing dot ≠ live agent
animated graph ≠ active organization
```

### 32.4 Typography `[PROPOSED]`

- Persian: Vazirmatn or similar — readable at 16px base
- English/technical: Inter or system-ui
- IDs/code: JetBrains Mono, always `dir=ltr`

---

## 33. Accessibility

### 33.1 Target

WCAG 2.2 AA — Agent-17 §28.2 adopted.

### 33.2 Requirements

| Requirement | Implementation |
| --- | --- |
| Color not sole channel | Shape + text on every status badge |
| Keyboard navigation | All actions reachable; visible focus rings |
| Screen readers | `aria-live="polite"` for decision alerts; dimensions announced separately |
| Reduced motion | `prefers-reduced-motion`: disable non-essential animation |
| High contrast | Token set with ≥4.5:1 body text |
| Graphs | Adjacency list alternative always present |
| Tables | Sortable headers; caption + scope |
| Focus management | Approval modal trap; restore focus on close |
| Touch targets | ≥44px for approval buttons |

### 33.3 Status announcement pattern

```text
"Mission Autonomy Readiness. Lifecycle: Active. Verification: Pending. Acceptance: Not started."
```

Not: "Mission active, green badge."

---

## 34. Persian / RTL Architecture

### 34.1 Policy

Persian-primary UI chrome; English technical identifiers preserved; bilingual toggle `[PROPOSED]`.

### 34.2 Technical requirements

```text
html[dir=rtl][lang=fa] default
Locale files: fa.json (primary), en.json (secondary)
next-intl or react-i18next [PROPOSED at implementation]
```

### 34.3 Do-not-translate list (LTR enclaves)

```text
AGENT-18 · MISSION-042 · mission.20260914-018
agent.security · agent.org.05-epistemic-reasoning
File paths · Git hashes · Evidence IDs · Test names
URLs · JSON keys · ISO8601 timestamps (display layer may add Jalali)
```

### 34.4 Mixed content handling

```html
<!-- [PROPOSED] pattern -->
<p dir="rtl">وضعیت ماموریت: <bdi dir="ltr">MISSION-042</bdi> — در انتظار تایید (<bdi dir="ltr">PENDING_ACCEPTANCE</bdi>)</p>
<pre dir="ltr"><code>...</code></pre>
```

### 34.5 Numerals

Latin numerals for precision (AHOS convention) — `[VERIFIED]` in AHOS `01/src/lib/format.ts`.

### 34.6 Jalali timestamps `[PROPOSED]`

Display: Jalali + hover ISO8601 UTC. Storage/transmission: always UTC ISO8601.

### 34.7 Persian UX terminology (from Agent-17 §27.5)

```text
ماموریت · شواهد · تناقض · تایید · تایید مستقل · خلاء توانایی
پیشنهاد · دستور · بدون اقدام لازم
```

---

## 35. AHOS Integration Boundary

### 35.1 Product separation (hard)

```text
Agent Organization ≠ AHOS
Org frontend ≠ AHOS product frontend
```

Separate app shell or nav section:

```text
[ Organization ]  |  [ AHOS Intelligence ]
```

`[PROPOSED]` — requires HD-17-04 human decision.

### 35.2 Integration adapter (future)

```text
Agent One / Org Frontend
  ↓ read-only AHOS Integration Adapter
  ↓ (no direct DB/trading/credentials)
AHOS authoritative APIs / projections
```

Frontend **must not** directly mutate AHOS. Status: `[NOT IMPLEMENTED]`.

### 35.3 What org UI may eventually show from AHOS

- Read-only product health summary (if adapter exists)
- Cross-links to AHOS evidence for domain missions
- Shared locale/format utilities (library-level, not merged nav)

### 35.4 What org UI must never assume from AHOS

- AHOS agent roster (AG-01..AG-25) ≠ org agent roster
- AHOS "ROOTS LIVE" status ≠ org operational status
- AHOS paper trading state ≠ org mission state

---

## 36. AHOS Visual Compatibility

### 36.1 AHOS patterns inspected

| Pattern | Location | Reusable for org? |
| --- | --- | --- |
| Persian/EN locale formatting | `01/src/lib/format.ts` | **YES** — adapt for org tokens |
| RTL in modals | `MasterVisionModal.tsx` `dir=rtl` | **YES** |
| Dark dashboard shell | `app-shell.tsx`, `CommandCenter.tsx` | **PARTIAL** — calm org UI may be lighter |
| Evidence-before-decision ticker | AHOS app-shell | **YES** — epistemic slogans |
| Score tone good/mid/bad | `format.ts scoreTone` | **NO** for org epistemic — misleading |
| Pulsing "ROOTS LIVE" | `app-shell.tsx` | **NO** — violates no-fake-live |
| 3D void scene | AHOS platform | **NO** for primary org UI |
| Token cards | AHOS product | **NO** — domain-specific |
| Paper trading actions | AHOS | **NO** — wrong product |

### 36.2 Principles to adopt

- Persian-first with LTR technical enclaves
- Evidence-before-decision messaging
- Local-first, $0 budget posture in copy
- Typed failure states (not generic errors)

### 36.3 Principles to reject for org UI

- Confidence percentages as primary signal
- Live pulsing indicators without backend basis
- Trading-specific visual metaphors
- Implied operational status from aesthetic polish

---

## 37. 3D / Immersive Visualization

### 37.1 Verdict

**3D is not appropriate as primary representation** for evidence, verification, authorization, approval, or security events.

### 37.2 Possible future uses (ambient only)

| Use | Appropriate? | Notes |
| --- | --- | --- |
| Organizational overview ambient background | Marginal | Must not carry status information |
| Mission landscape | Phase 3+ optional | Table remains canonical |
| System health particle effects | **NO** | Implies liveness |
| Expert mode graph 3D | **NO** | Accessibility failure |

### 37.3 Rule

Critical information remains **2D, precise, accessible, textual**. Any 3D is decorative, disable-able, and never sole channel.

---

## 38. Animation Governance

### 38.1 Classification

| Animation | Class | Policy |
| --- | --- | --- |
| Mission phase transition | Useful | Subtle cross-fade; respect reduced-motion |
| New contradiction alert | Useful | Single attention pulse — then static |
| Verification pending | Useful | Subtle ellipsis or static "Pending" |
| Critical security event | Useful | Controlled alert banner — no shake |
| Fake "AI thinking" loop | **Dangerous** | **Forbidden** unless backend confirms processing |
| Pulsing online indicators | **Misleading** | **Forbidden** without runtime |
| Force-directed graph churn | Decorative | Off by default |
| Count-up numbers | Decorative | Forbidden for epistemic scores |

### 38.2 Rule

**Do not simulate activity to make the system feel alive.** Animation encodes **state change**, not **existence**.

---

## 39. No-Fake-Live-System Policy

### 39.1 Hard rules (when runtime absent)

```text
DO NOT SHOW LIVE AGENTS
DO NOT SHOW LIVE MISSION PROGRESS
DO NOT SHOW FAKE ONLINE STATUS
DO NOT SHOW FAKE MESSAGE FLOW
DO NOT SHOW FAKE VERIFICATION
DO NOT SHOW FAKE AGENT ONE TYPING
```

### 39.2 CURRENT mode requirements

- Persistent banner: manual Cursor control plane
- Agent One runtime labeled NOT IMPLEMENTED — role vs runtime separated
- Inter-agent comm: "NOT AVAILABLE" — not simulated threads from filenames
- Demo/preview: watermark SIMULATION

### 39.3 AHOS anti-pattern callout

AHOS `app-shell.tsx` shows pulsing green "ROOTS LIVE" — `[VERIFIED]`. Org frontend **must not** copy this pattern without live backend subscription.

---

## 40. Design System Architecture

Conceptual primitives — **not implemented**.

### 40.1 Core primitives

| Primitive | Semantic meaning | Constraints |
| --- | --- | --- |
| **StatusBadge** | Single orthogonal dimension value | Requires dimension prop; never generic "status" |
| **StatusStack** | Multiple StatusBadges | Order: lifecycle, auth, verification, acceptance, freshness |
| **EvidenceCard** | Evidence projection display | Shows provenance link; stale watermark |
| **MissionCard** | Composed mission summary | No fake progress % |
| **AgentCard** | Agent projection | Plane + maturity mandatory |
| **VerificationCard** | VerificationRecord | INDEPENDENT vs SELF_CHECK qualifier |
| **ContradictionCard** | Split panel positions | No averaging |
| **DecisionCard** | Inbox item | Severity + expiry |
| **CapabilityGapCard** | Missing capability | NOT_IMPLEMENTED honest label |
| **Timeline** | Event/history display | UTC + optional Jalali |
| **EventRow** | Audit/event inspector | Hash copy button |
| **GraphView** | Optional graph | Requires ListView sibling |
| **TableView** | Accessible tabular data | Primary for audit |
| **Inspector** | Layer B drill panel | Preserves Layer A context |
| **CommandBar** | Intent input | Class labeled REQUEST |
| **ApprovalModal** | Multi-step approval | §22 fields mandatory |
| **ContextBanner** | Stale/conflict/mode alerts | Non-dismissable for CURRENT mode |
| **FreshnessIndicator** | LIVE/FRESH/STALE/OFFLINE | Clock icon + text |
| **ModeBanner** | CURRENT / SIMULATION | Top of shell |
| **UntrustedContent** | Wrapper for agent output | Sanitized render path |

### 40.2 Token categories `[PROPOSED]`

```text
color.semantic.*     — dimension-specific (not good/bad)
space.*              — 4px grid
typography.fa.*      — Persian scale
typography.mono.*    — IDs/code
motion.reduced       — media query overrides
elevation.*          — minimal — calm UI
```

### 40.3 Composition rules

- Every card accepts `source_refs[]` for traceability
- Every actionable component declares `action_class`
- PLANNED features use `CapabilityBadge(PLANNED)`

---

## 41. State Management

### 41.1 Architectural approach `[PROPOSED]`

```text
Server state (authoritative projections)
  → TanStack Query (or equivalent) — cache keyed by entity_id + version
  → SSE event reducer invalidates/refetches selective queries

Local UI state
  → React useState/useReducer — panel open, scroll, locale, density

Event stream state
  → Event log buffer (ring buffer, max 1000) for expert mode
  → Dedupe by event_id

Immutable snapshots
  → Store as_of snapshots for comparison (expert time-travel lite)
```

### 41.2 Cache invalidation rules

| Event type | Invalidation scope |
| --- | --- |
| `MISSION_*` | mission detail + home snapshot + inbox |
| `AGENT_*` | agent detail + mission agents list |
| `EVIDENCE_*` | evidence + linked mission |
| `VERIFICATION_*` | verification + target artifact + mission |
| `CONTRADICTION_*` | contradiction registry + home |
| Heartbeat miss | Mark all FRESH → STALE |

### 41.3 Optimistic updates

**Forbidden** for: APPROVE, COMMAND, EXECUTE, delegation, promotion.

**Allowed** for: UI toggles, inspector expand, conversation draft text (local only).

Pending state pattern:

```text
dispatch({ type: 'INTENT_SUBMITTED', intent_id, action_class })
// UI shows REQUESTED — not DONE
on CommandResult → resolve or reject with reason
```

### 41.4 Multi-tab coherence

`BroadcastChannel('org-ui')` syncs: event cursor, invalidation signals, pending intent resolution — avoid duplicate SSE connections.

---

## 42. Error / Recovery Architecture

### 42.1 Failure taxonomy (frontend handling)

| Failure | UI response |
| --- | --- |
| Backend unavailable | OFFLINE banner; cached STALE snapshot |
| Stale connection | DEGRADED; switch to polling |
| Message lost (SSE gap) | Detect via sequence gap → full snapshot refresh |
| Duplicate event | Silent dedupe |
| Out-of-order event | Reconcile; expert flag if unresolved |
| Schema mismatch | Block writes; expert diagnostic; read-only cache |
| Unknown event type | Log in expert; ignore in standard mode |
| Authorization failure | Show denial reason; no retry without new intent |
| Session expiry | Re-auth prompt; preserve read cache |
| Context mismatch | Banner with version diff link |
| Mission deleted/superseded | Redirect to parent; show superseded label |
| Verification changed | Refresh verification dimension; notify if user viewing stale |

### 42.2 Recovery principle

**Never silently recover into false state.** Every recovery path labels data freshness and authority status.

### 42.3 Error display structure

```text
WHAT FAILED · WHAT STILL WORKS · WHAT IS TRUSTWORTHY · WHAT TO DO NEXT
```

Forbidden: "Something went wrong."

---

## 43. Frontend Observability

### 43.1 Client-side metrics (frontend health — not org health)

```text
render_failures
api_latency_p50/p95
sse_connected bool
sse_last_event_age
event_lag_ms (occurred_at vs displayed_at)
projection_stale_count
schema_mismatch_count
authorization_errors
connection_state: LIVE|DEGRADED|OFFLINE
client_version
backend_version (from OrganizationStateProjection)
cache_hit_rate
```

### 43.2 Diagnostic bundle `[PROPOSED]`

Expert export: client version, backend version, last 50 events, connection state, pending intents — **no secrets**.

### 43.3 Separation

```text
Frontend health OK + Organization NOT OPERATIONAL = valid honest state
```

Never conflate "UI loaded" with "org autonomous."

---

## 44. Version Compatibility

### 44.1 Version axes

```text
frontend_version
backend_api_version
event_schema_version
projection_schema_version
context_version
organization_schema_version (registry/planes)
epistemic_artifact_schema (Slice 2B — implicit in dataclasses)
```

### 44.2 Compatibility policy `[PROPOSED]`

| Scenario | Behavior |
| --- | --- |
| Frontend newer, backend older | Graceful degrade; hide unknown features |
| Backend newer, frontend older | Unknown fields ignored in display; warn in expert |
| Event schema bump | SSE reconnect with negotiation header |
| Breaking API change | Block writes; read-only until frontend update |

### 44.3 Feature flags

Backend-driven flags for: SIMULATION mode, expert graph, AHOS adapter — never client-only enable of authority features.

### 44.4 Schema negotiation

```text
GET /org/capabilities → { api_version, features[], min_frontend_version }
```

Frontend refuses write paths if `frontend_version < min_frontend_version` for mutating features.

---

## 45. Threat Model

| # | Threat | Impact | Mitigation | Backend dependency | Frontend responsibility | Verification |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | UI spoofing | False trust | CSP, no inline scripts, signed bundles | Optional bundle hash | Strict CSP, SRI | Agent-19 red team |
| 2 | Stale state displayed as live | Wrong decisions | FreshnessIndicator mandatory | Projection timestamps | SLA rendering | Golden STALE states |
| 3 | Authority illusion | Unauthorized action | Separate auth badges | CapabilityStatus projection | Never infer auth from UI role | State machine tests |
| 4 | Fake verification badge | False confidence | VerificationCard kind qualifier | VerificationRecord | INDEPENDENT vs SELF_CHECK | Contract tests |
| 5 | Fake progress | Premature acceptance | No % without semantics | MC mission model | Composed status only | Visual regression |
| 6 | XSS | Code execution | Sanitized rendering | N/A | Trusted rendering §20 | Security tests |
| 7 | Malicious Markdown | XSS/UX spoof | Markdown subset | N/A | react-markdown + sanitize | Injection fixtures |
| 8 | Poisoned agent output | Prompt/UI injection | UntrustedContent wrapper | Schema validation | Component registry only | Red team payloads |
| 9 | Prompt injection via display | User misled | Untrusted banners | N/A | Separate styling for agent content | Manual review |
| 10 | Local API exposure | Local privilege escalation | 127.0.0.1 bind + token | Service config | Origin checks | Pen test localhost |
| 11 | Token theft | Session hijack | httpOnly cookie | Session issuance | No localStorage secrets | Security audit |
| 12 | Browser storage compromise | Cached data leak | Minimal cache; no secrets | N/A | Encrypt optional PII-free | Storage inspection |
| 13 | Clickjacking | Tricked approval | X-Frame-Options DENY | N/A | Frame denial | Header test |
| 14 | Event replay | Stale UI update | event_id dedupe + sequence | Event authority | Client dedupe | Failure injection |
| 15 | Schema confusion | Misrendered authority | schema_version display | Version headers | Strict parsing | Contract tests |
| 16 | Privilege escalation via UI | Hidden admin actions | Action class enforcement | TCB deny | Hide buttons without projection grant | Authz UI tests |
| 17 | Hidden execution | Approve runs code | Separate EXECUTE step | MC/TCB | Multi-step approval | E2E approval |
| 18 | Misleading animation | False liveness | Animation governance §38 | Runtime truth | No fake pulse | Visual audit |
| 19 | Fake consensus visualization | Averaged truth | ContradictionCard | ContradictionCase | No averaging UI | Golden CONTRADICTORY |
| 20 | Unauthorized approval | Governance bypass | Approval links to Approval artifact | TCB CREATE_APPROVAL | Await CommandResult | Integration tests |

---

## 46. Testing Architecture

Testing design only — **not implemented**.

### 46.1 Unit tests

- Semantic UI components render correct dimension labels
- StatusStack ordering and forbidden collapse detection
- FreshnessIndicator SLA transitions
- Display guard impossible state warnings
- RTL/LTR mixed content rendering
- Sanitizer: Markdown fixtures → no script execution

### 46.2 Contract tests

- Projection DTOs ↔ Slice 2B dataclass field parity
- Event envelope schema ↔ UI reducer expectations
- API `/org/capabilities` version negotiation

### 46.3 Integration tests

- Frontend ↔ local Org API read paths
- Intent submission → CommandResult → UI state update
- SSE reconnect + dedupe

### 46.4 State-machine tests

- Mission/agent/evidence composed states — golden matrices
- Illegal composite detection (ACCEPTANCE without required VERIFICATION)

### 46.5 Security tests

- XSS injection corpus through Markdown renderer
- SVG/script payload rejection
- CSRF token validation on mutating routes
- Clickjacking header presence

### 46.6 Accessibility tests

- axe-core WCAG 2.2 AA on key routes
- Screen reader announcement snapshots for StatusStack
- Keyboard-only approval flow
- Reduced motion: no essential info in animation only

### 46.7 Visual regression

Only for semantically meaningful states:

```text
UNKNOWN | UNVERIFIED | VERIFIED+INDEPENDENT | CONTRADICTORY
BLOCKED | CAPABILITY_GAP | HUMAN_DECISION_REQUIRED | QUARANTINED
STALE | OFFLINE | CURRENT_MODE | SIMULATION
```

Not for decorative layout churn.

### 46.8 E2E tests (when runtime exists)

```text
Human → Agent One conversation → mission proposal → approve → specialist → evidence → verification → acceptance
```

### 46.9 Failure injection tests

- Disconnect backend mid-approval
- Duplicate SSE events
- Out-of-order mission events
- Schema version mismatch
- Expired approval attempt

### 46.10 Golden UI states

Maintain screenshot/story fixtures for each epistemic/lifecycle combination in §46.7 — Agent-19 attack baseline.

---

## 47. Backend Gap Transparency

### 47.1 Hard invariant

```text
Backend NOT_IMPLEMENTED → Frontend labels NOT_IMPLEMENTED
Backend UNKNOWN         → Frontend labels UNKNOWN
Backend VERIFICATION_PENDING → Frontend never labels TRUSTED
```

### 47.2 Capability gap display

When user requests unavailable capability, render CapabilityGapCard:

```text
Requested: Mission Controller
Current: NOT IMPLEMENTED
Evidence: Agent-16 §4.2
Impact: Autonomous execution cannot proceed
Alternative: Document-only READ_ONLY mission via Cursor (manual)
```

### 47.3 Launch blocker surfacing

Org home may show count (12 — Agent-16) with link to read-only blocker list — not hidden behind polished dashboard.

---

## 48. Agent-19 Red-Team Handoff

### 48.1 Attack surfaces for Agent-19

| Surface | Attack vector |
| --- | --- |
| UI authority illusion | Render fake AUTHORIZED without grant |
| State spoofing | Inject localStorage projection override |
| Trust signaling | Add green VERIFIED badge via devtools |
| Data injection | Malicious Markdown/SVG/URL in agent report |
| Command UI | Single button crossing APPROVE+EXECUTE |
| Approval UI | Skip scope hash display |
| Evidence visualization | Imply causal link without lineage |
| Event handling | Replay old SSE events |
| Frontend/backend boundary | Call TCB directly from browser console |
| Stale as live | Freeze freshness clock |
| Fake consensus | Collapse contradiction to average |
| Mode confusion | Hide CURRENT banner |
| RTL spoofing | Bidi override in evidence text |

### 48.2 Adversarial test cases (document only)

```text
fake_verified_badge_on_agent_completion
fake_agent_identity_in_delegation_tree
fake_command_origin_principal
spoofed_mission_status_ACTIVE_when_PROPOSED
spoofed_commander_agent_one_when_cursor_session
spoofed_approval_without_approval_artifact
malicious_markdown_script_injection
malicious_svg_onload
malicious_javascript_url_in_evidence_link
stale_verification_displayed_as_current
replayed_sse_event
future_dated_event
out_of_order_lifecycle_transition_display
unauthorized_action_button_without_capability_projection
hidden_execute_in_approve_modal
```

### 48.3 Expected red-team outcome

Document failures as `UI_DEFECT` with severity — not silent fixes. Frontend architecture assumes hostile agent output and careless rendering.

**AGENT_18_TO_AGENT_19_HANDOFF = COMPLETE — RED TEAM MAY ATTACK SPECIFIED SURFACES**

---

## 49. Agent One Handoff

When Agent One runtime is implemented, it will require from the frontend:

| Capability | Frontend deliverable |
| --- | --- |
| Human intent input | CommandBar + REQUEST/PROPOSE class labeling |
| Mission proposal display | MissionCard in PROPOSED state + approval actions |
| Approval surfaces | ApprovalModal bound to Approval artifact creation |
| Status synthesis | Agent One Home + composed StatusStacks |
| Uncertainty display | UNKNOWN/UNCERTAIN epistemic badges — no false confidence |
| Contradiction surfacing | ContradictionCard + inbox integration |
| Verification visibility | VerificationCard with INDEPENDENT qualifier |
| Decision inbox | Filtered DecisionItems only |
| Organizational memory | MemoryRecord cards — PROMOTED ≠ truth label |
| Capability gaps | Honest NOT_IMPLEMENTED cards |
| Change proposals | Changes tracker UI |
| Audit drill-down | Level 0–7 inspector paths |

Agent One must **not** rely on frontend for authority decisions — only for intent collection and projection display.

**Frontend does not implement Agent One — it interfaces to Agent One service.**

---

## 50. Minimum Viable Organizational Frontend (MVOF)

Derived from Agent-17 MVOU + runtime dependencies — smallest **credible** product.

### 50.1 Prerequisites (runtime — block MVOF honest live mode)

1. Mission Controller (durable) — `[ABSENT]`
2. Cursor Federation Bridge — `[ABSENT]`
3. MissionCommandEnvelope validator — `[PROPOSED]` in docs only
4. Agent One service (minimal) — `[ABSENT]`
5. Result ingestion pipeline — `[ABSENT]`
6. Org API exposing ReadOnlyProjections — `[ABSENT]`

### 50.2 Phase 0 — Honest CURRENT mode (may precede MC)

`[PROPOSED]` — only mode honest today:

```text
✓ CURRENT mode banner (manual Cursor)
✓ Static org status from documented reality (SUBSTRATE-1)
✓ Capability gap registry (read-only from Agent-16 blockers)
✓ Dual-19 standing contradiction display
✓ Governance doc viewer (read-only, untrusted render path)
✓ Persian/English locale shell
✓ System status page (what is NOT implemented)
✗ Fake Agent One conversation
✗ Fake mission progress
```

### 50.3 Phase 1 — MVOF (after Agent-14 Phase 1 verified)

```text
✓ Agent One conversation surface (bound to service)
✓ Mission proposal → approve/reject/edit
✓ One specialist delegation status
✓ Composed mission status dimensions
✓ Evidence ref display (IDs + classification + links)
✓ Decision Inbox (approvals + acceptance)
✓ SSE mission/event updates
✓ Basic Agent/Mission cards
```

### 50.4 Explicit MVOF exclusions

- Full 19-agent roster management UI
- Message bus visualization
- Organizational memory browser
- Mission/evidence graphs (table/timeline only)
- AHOS integration UI
- Telegram/mobile push
- 3D/immersive environments

---

## 51. Advanced Future Frontend

After SUBSTRATE-4+ and core runtime verified:

| Feature | Dependency |
| --- | --- |
| Live mission DAG visualization | MC + graph projection API |
| Inter-agent message inspector | Message bus transport |
| Epistemic graph navigator | Full artifact graph index |
| Memory browser with supersession | Memory runtime |
| Change propagation map | Governance change pipeline |
| Capability map | Unified registry federation |
| Performance history | Performance MemoryKind runtime |
| Independent Verification Console | IV dispatch plane |
| Audit Explorer with time-travel | Durable audit + snapshots |
| Expert instruction stack layer view | Instruction stack runtime |
| Bilingual report export (PDF/md) | Export service |
| Simulation/rehearsal mode | Mock MC + watermark |

All labeled PLANNED until runtime evidenced.

---

## 52. Open Questions

1. **Stack selection:** React+TypeScript (AHOS-aligned) vs alternative — `[PROPOSED]` React for reuse of i18n/format patterns.
2. **Desktop shell:** Browser-only localhost vs Tauri/Electron wrapper for Windows — defer until Phase 1.
3. **Agent One streaming:** WebSocket for token stream vs SSE + polling for structured blocks — depends on Agent One service design (HD-16-04).
4. **Acceptance granularity UI:** Per-mission vs per-artifact vs per-claim — inherits HD from Agent-17 §39.
5. **Simulation mode:** Allow rehearse future UX against mock MC? — HD-17-03.
6. **Graph library:** dagre/static layout vs force — prefer static for a11y.
7. **Offline intent queue:** Auto-send on reconnect vs require user confirm — recommend **confirm**.
8. **Jalali default:** Always show or toggle — recommend hover ISO + optional Jalali primary.
9. **Shared component package with AHOS:** Monorepo shared `@ahos/ui-tokens` vs fork — product separation favors fork with documented compatibility.
10. **Frontend test runner in org repo:** Separate `frontend/` package when implementation starts — not in this mission.

---

## 53. Human Decisions Required

| ID | Decision | Frontend impact |
| --- | --- | --- |
| HD-16-01 | AGENT-01 = AGENT ONE canonical identity | Labels, home copy, commander display |
| HD-16-02 | Resolve Dual-19 | Org map, agent cards, roster UI |
| HD-16-03 | Legitimate agent contact channel | Message inspector design |
| HD-16-04 | Agent One runtime principal id | Agent One card binding |
| HD-16-06 | Operating Baseline v1 L2 adoption | Approval semantics enforcement display |
| HD-16-07 | Verifier independence rules | VerificationCard qualifiers |
| HD-17-01 | Persian-primary org UX | Default locale |
| HD-17-02 | Conversation-first vs dashboard-first | Layout priority |
| HD-17-03 | Simulation/preview mode | Watermark + feature flag |
| HD-17-04 | Separate org app vs AHOS nav | App shell architecture |
| **HD-18-01** | Approve Phase 0 CURRENT mode UI before MC | Early honest UI without fake live |
| **HD-18-02** | SSE vs WebSocket as primary transport | Real-time architecture |
| **HD-18-03** | Localhost-only vs optional LAN access | Security model |

---

## 54. Architectural Dependencies

Ordered dependencies for frontend **implementation** (not this document):

```text
1. Human decisions HD-16-01/02/04, HD-17-01/02/04, HD-18-01
2. Agent-14 Phase 1: MC + durable store + federation bridge
3. Org API exposing ReadOnlyProjections + intent ingress
4. Agent One minimal service loop
5. Result ingestion + MissionCommandEnvelope
6. IV dispatch runtime (verification UI beyond manual)
7. Context pack gate (context banner)
8. Message bus (Layer B message inspector)
9. Slice 1 ↔ 2B federation (unified agent projections)
10. L2 governance adoption (approval enforcement)
11. Frontend implementation team (consumes this architecture)
12. Agent-19 red team on implemented UI
```

**Frontend Phase 1 (live) cannot precede MC + Org API** without violating no-fake-live policy.

**Frontend Phase 0 (CURRENT mode)** may proceed as honest manual-mode shell.

---

## 55. Verification Requirements

| Claim | Verification method | Status |
| --- | --- | --- |
| No org frontend exists | Repo search — no package.json | `[VERIFIED]` |
| Epistemic types match UI contracts | Crosswalk to `epistemic.py` | `[VERIFIED]` |
| ReadOnlyProjections exists as read seed | Source read | `[VERIFIED]` |
| Agent-17 UX consumed | Cross-reference §4 | `[VERIFIED]` |
| AHOS RTL patterns exist | Spot-check `01/src/lib/format.ts` | `[VERIFIED]` |
| AHOS live pulse anti-pattern | Spot-check `app-shell.tsx` | `[VERIFIED]` |
| No MC/Agent One runtime | Agent-16 + source | `[VERIFIED]` |
| 251 tests prove UI readiness | **NO** — tests prove substrate only | `[VERIFIED]` |

**Recommended verifier:** Agent-19 red team on §45 threat model + golden UI states.

---

## 56. Recommended Next Mission

**STATE ONLY — DO NOT EXECUTE**

```text
PRIMARY:   AGENT-14 PHASE 1 — MC + durable store + Org API projections endpoint
           — prerequisite for honest live frontend beyond Phase 0

PARALLEL:  GOVERNANCE MISSION — HD-16-01/02/05/06 identity + baseline adoption

PARALLEL:  AGENT-19 RED TEAM — review this architecture + Agent-17 UX threat model

SEQUENCED: FRONTEND PHASE 0 — CURRENT mode shell (honest manual banner, no fake live)
           — after HD-18-01 approval

SEQUENCED: AGENT ONE MINIMAL SERVICE + MVOF UI — after Phase 1 runtime verified

DO NOT:    Build polished 19-agent dashboard before MC exists
DO NOT:    Copy AHOS "ROOTS LIVE" pattern into org UI
DO NOT:    Implement optimistic approval UX
```

---

## Appendix A — Evidence Classification Key

```text
VERIFIED · PARTIALLY_VERIFIED · DOCUMENTED_ONLY · PROPOSED
PLANNED · UNVERIFIED · UNKNOWN · BLOCKED · SUPERSEDED
```

Runtime capabilities explicitly **NOT IMPLEMENTED** (independently confirmed):

```text
Agent One runtime · Mission Controller · Message Bus · Lifecycle Controller
Organizational frontend · Org API · Real-time UI transport · Context Gate
Inter-agent communication · IV dispatch · Cursor federation bridge
Organizational UX runtime · Durable persistence · Slice 1↔2B federation
```

---

## Appendix B — Slice 1 TaskState → Mission Lifecycle UI Mapping

| TaskState | Mission lifecycle (UI) | Overlays required |
| --- | --- | --- |
| PROPOSED | Planning | evidence/verification/acceptance separate |
| AUTHORIZED | Planning (approved) | same |
| RUNNING | Active | same |
| BLOCKED | Blocked | show blocker refs |
| COMPLETED | Complete (lifecycle only) | verification + acceptance NOT implied |
| FAILED | Failed | partial results if any |
| CANCELLED | Cancelled | terminal |
| REJECTED | Rejected | reason required |

---

## Appendix C — Technology Recommendations Summary `[PROPOSED]`

| Concern | Recommendation | Rationale |
| --- | --- | --- |
| UI framework | React + TypeScript | AHOS precedent; component ecosystem |
| Server state | TanStack Query | Projection cache + invalidation |
| Routing | React Router or Next.js app router | Deep linking §10 |
| Styling | CSS modules or Tailwind | Match team preference at implementation |
| i18n | next-intl or react-i18next | FA/EN with RTL |
| Markdown | react-markdown + rehype-sanitize | Trusted rendering |
| Real-time | SSE primary, polling fallback | §14 |
| Local API | Python (same service as MC) | Agent-14 alignment |
| Charts/graphs | dagre + SVG (static layout) | Accessibility |
| Testing | Vitest + Playwright + axe | §46 |

**None of the above is implemented or committed — architecture recommendation only.**

---

```text
MISSION_STATUS = FRONTEND_VISUALIZATION_AND_TRUST_INTERFACE_ARCHITECTURE_ANALYSIS_COMPLETE_WITH_GAPS
AGENT_ID = AGENT-18
DIRECT_COMMANDER = AGENT-01 / AGENT ONE
LIFECYCLE_STATUS = IDLE / DORMANT / WAITING_FOR_NEW_COMMAND
AGENT_ONE_STATUS = PRIMARY_ORGANIZATIONAL_AGENT / CURRENT_INTENDED_ROOT
AGENT_ONE_RUNTIME_STATUS = NOT_IMPLEMENTED
DUAL_19 = UNRESOLVED
ORGANIZATIONAL_FRONTEND_RUNTIME = NOT_IMPLEMENTED
FRONTEND_ARCHITECTURE_STATUS = SPECIFIED — ARCHITECTURE DOCUMENT COMPLETE
TRUST_UI_STATUS = NOT_IMPLEMENTED — DESIGN SPECIFIED IN §5–§20, §32, §45–§47
REAL_TIME_UI_STATUS = NOT_IMPLEMENTED — SSE+POLLING DESIGN SPECIFIED IN §14–§16
AHOS_IMPACT = NONE
CODE_CHANGES = NONE
FRONTEND_CHANGES = NONE
RUNTIME_CHANGES = NONE
DATABASE_CHANGES = NONE
GOVERNANCE_CHANGES = NONE
COMMIT = NONE
PUSH = NONE
LAUNCH_BLOCKERS = 12
NON_BLOCKING_GAPS = 24
HUMAN_DECISIONS_REQUIRED = HD-16-01; HD-16-02; HD-16-03; HD-16-04; HD-16-06; HD-16-07; HD-17-01; HD-17-02; HD-17-03; HD-17-04; HD-18-01; HD-18-02; HD-18-03
CAPABILITY_GAPS = Mission Controller; Agent One runtime; Org API/BFF; Message bus; Agent lifecycle FSM; Durable persistence; Slice 1↔2B federation; Context sync gate; Instruction stack enforcement; IV dispatch; Cursor federation bridge; Organizational memory runtime; Domain runtime adapters; Organizational frontend package; Real-time event transport; SSE/WebSocket server; Intent ingress endpoint; Result ingestion pipeline; Bilingual org i18n implementation; Expert mode audit API; AHOS integration adapter; Simulation/mock MC; Frontend test harness; Unified agent projection federation
AGENT_17_INPUT_STATUS = COMPLETE — CONSUMED AND EXTENDED INTO TECHNICAL ARCHITECTURE
AGENT_17_CORRECTIONS_REQUIRED = NONE IN THIS DOCUMENT — code marker AGENT_ONE_STATUS comment separation remains governance mission (HD-16-01)
AGENT_18_TO_AGENT_19_HANDOFF = COMPLETE — §48 adversarial surfaces and test cases specified
NEW_CROSS_AGENT_DISCOVERIES = 5
RECOMMENDED_NEXT_MISSION = STATE ONLY — AGENT-14 PHASE 1 + PARALLEL AGENT-19 RED TEAM REVIEW OF THIS ARCHITECTURE + SEQUENCED FRONTEND PHASE 0 AFTER HD-18-01 — DO NOT EXECUTE
```

---

