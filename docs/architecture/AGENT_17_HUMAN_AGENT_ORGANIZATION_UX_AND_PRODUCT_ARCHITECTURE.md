# AGENT-17 — Human–Agent Organization UX & Product Architecture

```text
DOCUMENT_ID      = AGENT_17_HUMAN_AGENT_ORGANIZATION_UX_AND_PRODUCT_ARCHITECTURE
MISSION_ID       = TASK-20260914-017 (Human–Agent Organization UX Architecture)
VERSION          = 1.0.0
STATUS           = HUMAN_AGENT_ORGANIZATION_UX_ARCHITECTURE_ANALYSIS_COMPLETE_WITH_GAPS
AGENT_ID         = AGENT-17
DIRECT_COMMANDER = AGENT-01 / AGENT ONE
AUTHORITY        = READ_ONLY_ARCHITECTURE_ANALYSIS
CODE_CHANGES     = NONE (this document is the mandated mission deliverable)
AHOS_EFFECT      = NONE
RUNTIME_EFFECT   = NONE
```

This document is a **read-only architecture artifact** produced by AGENT-17. It designs the **cognitive command interface** between one human principal and an autonomous organizational intelligence system. It does **not** implement UI, frontend, runtime, or governance changes.

Facts cite repository evidence with explicit classification labels. Recommendations are labeled `[PROPOSED]`.

---

## 1. Executive Verdict

**The AHOS Agent Organization has no organizational UX runtime today.** Mehrdad interacts with the organization through **Cursor chat sessions**, manual prompt crafting, and markdown report handoff. The intended product — **one human, one primary agent (Agent One), many specialists working autonomously underneath** — is architecturally specified across Agent-14/15/16 outputs and governance protocols, but **not experienceable as a product**.

| Question | Verdict |
| --- | --- |
| Does an organizational UX exist? | **NO** — `[VERIFIED]` no Agent One interface, no mission dashboard, no unified conversation surface bound to runtime |
| Is the UX architecture specified? | **PARTIALLY** — protocols, epistemic types, delegation design exist as documents; this mission completes the UX/product layer |
| Can Mehrdad talk naturally to Agent One today? | **NO** — Agent One runtime is `[NOT IMPLEMENTED]`; Cursor sessions stand in manually |
| Is the one-conversation model achievable? | **YES (future)** — requires Agent-14 Phase 1 substrate + Agent One service + federation bridge |
| Should UX hide the organization? | **NO** — simple Layer A conversation with optional Layer B audit drill-down |
| Is Persian-first required? | **YES (product requirement)** — AHOS already treats FA/EN as first-class; org UX must inherit that posture |
| AHOS product UX = Org UX? | **NO** — separate products; must not merge prematurely |

**Central design thesis:**

```text
Complexity belongs to the organization, not to the human.
Trust comes from visible evidence, not from polished presentation.
Authority flows from human intent, not from UI appearance.
```

**Classification:** `ARCHITECTURE COMPLETE — IMPLEMENTATION ABSENT — RUNTIME UX NOT STARTED`

---

## 2. Mission Scope

### 2.1 Inspected (read-only)

| Repository | Path | Mode |
| --- | --- | --- |
| Agent Organization | `G:\robat\ahos-agent-org` | Primary subject — docs, code, tests |
| AHOS | `G:\robat\ahos` | Secondary — bilingual UX patterns, product separation |

### 2.2 Input artifacts (challenged, not blindly trusted)

- Agent-16 Independent Verification & Organizational Forensics
- Agent-05 Epistemic Reasoning Architecture
- Agent-14 Agent Runtime Architecture
- Agent-15 Prompt/Instruction/Delegation Architecture
- Governance: Constitution, Registry Model, Operating Baseline
- Protocol pack: Communication, Evidence, Response, Supervision, Escalation, Update
- Slice 2B epistemic implementation (`agent_org/epistemic.py`)
- Slice 1 task/registry models (`ahos_org/`)

### 2.3 Not performed

- No code, UI, CSS, React, AHOS, governance, commit, push, or runtime activation
- No test re-execution (Agent-16 L1 evidence accepted; independent spot-check of source only)

### 2.4 Deliverable boundary

This document defines **UX principles, requirements, interaction models, and information architecture**. It explicitly separates these from **visualization requirements** (Agent-18) and **frontend implementation** (future).

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

`[VERIFIED]` per Agent-16 §5, §24; `[VERIFIED]` no Mission Controller, message bus, Agent One service, or federation bridge in repository.

### 3.2 What exists that UX may eventually bind to

| Substrate | Status | UX relevance |
| --- | --- | --- |
| Slice 1 task FSM (`PROPOSED`→`AUTHORIZED`→`RUNNING`→terminal) | `[IMPLEMENTED]` `[TESTED]` | Mission status vocabulary — not bound to UI |
| Slice 2B epistemic artifacts (12+ types) | `[IMPLEMENTED]` `[TESTED]` | Trust/epistemic display model — no chat bridge |
| Slice 2B `CommandEnvelope` | `[IMPLEMENTED]` | TCB ingress — not human-facing |
| Research worker path | `[IMPLEMENTED]` | One specialist execution pattern |
| Communication protocol envelopes | `[DESIGN_ONLY]` `TRANSPORT = NONE` | Future agent-to-agent transparency spec |
| 251 passing tests | `[VERIFIED]` Agent-16 L1 | Proves substrate — not organizational UX |

### 3.3 Current UX status assessment

```text
CURRENT_UX_STATUS           = MANUAL_CURSOR_ARTIFACT_MEDIATED
ORGANIZATIONAL_UX_RUNTIME   = NOT_IMPLEMENTED
AGENT_ONE_INTERFACE_RUNTIME = NOT_IMPLEMENTED
INTER_AGENT_COMMUNICATION   = NOT_AVAILABLE (Agent-16 confirmed)
DUAL_19                     = UNRESOLVED
```

### 3.4 Agent-16 input status

Agent-16 forensics report: **`[PARTIALLY_VERIFIED]` as input — materially accurate on repository reality.**

| Agent-16 claim | Agent-17 independent check | Status |
| --- | --- | --- |
| No Agent One runtime | `agent_org/__init__.py`: `AGENT_ONE_STATUS = "FUTURE_NON_AUTHORITY_ROOT"`; no service loop | **CONFIRMED** |
| 251 tests | Not re-run (sandbox unavailable); Agent-16 L1 accepted | **ACCEPTED L1** |
| Dual-19 unresolved | `registry.py` vs `PLANNED_19_AGENT_MAP.md` | **CONFIRMED** |
| Inter-agent comm absent | Protocol header `TRANSPORT = NONE` | **CONFIRMED** |
| Human burden HIGH | Observable from Cursor-only workflow | **CONFIRMED** |
| `AGENT_ONE_STATUS` code marker | Historical wording; organizational intent superseded per mission correction | **CONFIRMED — CORRECTION REQUIRED IN CODE COMMENT ONLY (future governance mission)** |

**Agent-16 corrections required:** Code marker and Constitution §3.1 still say "future orchestrator" / `FUTURE_NON_AUTHORITY_ROOT` without separating **organizational role** from **runtime status**. Agent-17 adopts the mission-mandated interpretation; does not repeat the historical error of treating Agent One as non-authority at the organizational layer.

**NEW_CROSS_AGENT_DISCOVERIES (Agent-17):** 4

1. **UX vacuum is itself a governance risk** — without a designed interface, Cursor chat visually collapses proposal/execution/verification (same green bubble aesthetic).
2. **Slice 1 `TaskState` ≠ mission UX states** — task FSM lacks `VERIFICATION`, `ACCEPTANCE`, `WAITING` phases needed for human mental model; UX must compose orthogonal status dimensions.
3. **Agent-05 §1 still says Agent One "must never become epistemic root"** — correct for epistemic authority, but easily misread as "Agent One is not organizational root"; UX must disambiguate **interface root** vs **truth root**.
4. **AHOS bilingual patterns exist** (`fa-IR`, RTL switching in product tree) but **zero org-specific i18n** — org UX inherits requirement without existing implementation.

---

## 4. Future Intended Experience

### 4.1 Target interaction topology

```text
MEHRDAD
   ↓ intent (natural language — Persian or English)
AGENT-01 / AGENT ONE (primary organizational interface — cognitive coordinator)
   ↓ MissionCommandEnvelope (via Mission Controller — PLANNED)
SPECIALIST AGENTS (parallel, bounded)
   ↓ structured results + evidence refs
INDEPENDENT VERIFICATION (Agent-16 plane — PLANNED dispatch)
   ↓ verification records
ACCEPTANCE GATE (human / governance — PLANNED)
   ↓ accepted artifacts → organizational memory
AGENT ONE (synthesis + contradiction surfacing)
   ↓ human-readable report + optional drill-down
MEHRDAD
```

### 4.2 The "one conversation" model

**Layer A — Primary (default):** Mehrdad speaks to Agent One as a single interlocutor. Agent One returns:

- What was understood
- What is proposed (if anything)
- What is happening / happened
- What is unknown or contradictory
- What requires human decision
- What evidence supports conclusions

**Layer B — Organizational transparency (on demand):** Full audit trail:

```text
WHO did WHAT → WHY → under WHICH mission → with WHICH evidence
→ WHAT they concluded → WHO challenged → WHO verified → WHAT remains UNKNOWN
```

Layer B is **optional for routine use** but **mandatory capability** for trust and governance.

### 4.3 Experience qualities (non-negotiable)

| Quality | Meaning |
| --- | --- |
| **Calm default** | Level 0 answers "what is happening?" without agent roster spam |
| **Honest absence** | "Nothing needs your attention" is a valid, prominent state |
| **No fake live org** | PLANNED capabilities labeled PLANNED — never animated as if running |
| **Proposal ≠ execution** | Visual and semantic separation at all times |
| **Evidence-forward trust** | No confidence theatre; epistemic status over percentage |
| **Progressive disclosure** | Drill-down Levels 0–7 (see §4.4) |

### 4.4 Drill-down principle (progressive disclosure)

| Level | User question | Default surfacing |
| --- | --- | --- |
| **0** | What is happening? | Mission phase summary, human decisions pending |
| **1** | Why? | Intent interpretation, constraints, blockers |
| **2** | Which agents? | Delegation graph — roles, not prompts |
| **3** | Which evidence? | Evidence IDs, sources, freshness |
| **4** | Which claims? | Claim/hypothesis objects with state |
| **5** | Which tests? | L1 test refs, verification records |
| **6** | Which source code? | File paths, line refs (L0) |
| **7** | Which audit/event/message? | Audit chain, envelope IDs, timestamps |

Level 0 must never require Level 2+ to answer a status question.

---

## 5. Human Principal Model

Mehrdad is **sovereign human principal** — not an orchestration engine, not a verifier-of-last-resort for routine coordination, not a memory subsystem.

### 5.1 Minimum human capabilities (each requires UX design)

| Capability | Example utterance | Agent One response pattern | Authority class |
| --- | --- | --- | --- |
| **A. Give objective** | "Find out why the org cannot operate autonomously yet." | Formalize → mission proposal → await approval if consequential | Intent → PROPOSE |
| **B. Give constraints** | "Do not modify anything." | Bind constraints to mission envelope; echo back | Constraint → BIND |
| **C. Ask explanation** | "Explain the three most important blockers." | Synthesize from evidence-linked claims; label uncertainty | READ + SYNTHESIZE |
| **D. Approve mission** | "Proceed." | Convert PROPOSAL → AUTHORIZED COMMAND; MC activates | APPROVE |
| **E. Reject** | "Do not implement this." | Terminalize proposal; record rejection reason | REJECT |
| **F. Change priority** | "Security is more important than speed." | Update mission priority vector; re-plan if active | PRIORITY OVERRIDE |
| **G. Ask for evidence** | "Show me what proves this." | Drill to Level 3–6; never prose-only | EVIDENCE REQUEST |
| **H. Ask for contradiction** | "Which agents disagree?" | Surface ContradictionCase objects; UNRESOLVED visible | CONTRADICTION QUERY |
| **I. Ask for status** | "Where are we?" | Level 0 org snapshot; mission phase | STATUS |
| **J. Ask for next action** | "What should happen next?" | Recommendations labeled PROPOSAL; distinguish from auto-execution | RECOMMEND |

### 5.2 Human authority boundary

**Human retains:**

```text
INTENT · PRIORITY · CONSTRAINT · APPROVAL · REJECTION · ESCALATION
OVERRIDE · PAUSE · CANCEL · RESUME · REVIEW · ACCEPTANCE
```

**Organization retains (future automation target):**

```text
Specialist selection · Prompt/instruction assembly · Parallel delegation
Result collection · Contradiction detection · Verification request routing
Memory organization · Routine status tracking · Context pack assembly
Follow-up mission discovery (as proposals)
```

### 5.3 What human should NOT manually do (operational burden elimination targets)

| Activity | Today | Future owner |
| --- | --- | --- |
| Select Agent-07 vs Agent-12 | Manual | Agent One + MC |
| Write per-agent prompts | Manual | Instruction stack + MC |
| Copy/forward reports | Manual | Result ingestion pipeline |
| Reconcile conflicting reports | Manual | Contradiction engine + Agent One synthesis |
| Remember agent domain ownership | Manual | Organizational self-model |
| Track mission IDs | Manual | MC durable store |
| Wake/idle agents | Manual | Lifecycle controller |
| Context synchronization | Manual | Context pack gate |
| Request verification | Manual | IV dispatch plane |
| Construct follow-up missions | Manual | Agent One discovery → PROPOSE |

`[VERIFIED]` all listed manual today per Agent-16 §24.

---

## 6. Agent One UX Model

Agent One is a **cognitive coordinator**, not a chatbot mascot, not a monolith executor.

### 6.1 Canonical identity (organizational vs runtime)

```text
AGENT_ONE_STATUS (organizational)  = PRIMARY_ORGANIZATIONAL_AGENT / CURRENT_INTENDED_ROOT
AGENT_ONE_RUNTIME_STATUS           = NOT_IMPLEMENTED
```

Code marker `FUTURE_NON_AUTHORITY_ROOT` in `agent_org/__init__.py` describes **runtime only** — wording is `[SUPERSEDED]` for organizational framing per HD-16-01.

### 6.2 Agent One exposed surfaces (future interface sections)

Every Agent One turn should be structurally capable of exposing:

| Surface | Content | Must not imply |
| --- | --- | --- |
| **Intent interpretation** | "What I understood" | Executed action |
| **Mission plan** | Proposed missions, constraints, domains | Approved mission |
| **Delegation** | Selected specialists + rationale | Peer authority |
| **Progress** | Phase, active work, blockers | Completion |
| **Uncertainty** | UNKNOWN / UNVERIFIED items | False confidence |
| **Contradictions** | Open ContradictionCase refs | Resolution by averaging |
| **Verification** | IV status per result | Self-verification |
| **Decisions required** | Explicit human gates | Optional nice-to-have |
| **Completion** | Accomplished vs pending verification | Accepted outcome |
| **Next discovery** | Proposed follow-up missions | Auto-scheduled work |

### 6.3 Agent One voice and interaction

- **Persian or English** input; Agent One responds in matched primary language with English identifiers preserved.
- **No sycophantic certainty** — epistemic labels over enthusiasm.
- **Structured default, prose optional** — expert mode may collapse sections; novice mode expands.
- **Never impersonates specialists** — cites which agent produced which artifact.

### 6.4 Agent One anti-patterns (forbidden UX)

- Single green checkmark on composite report
- "I've done everything" without verification/acceptance states
- Hidden specialist failures
- Auto-approval of own proposals
- Presenting TCB promotion as conversational fact

---

## 7. Command vs Request UX

### 7.1 Semantic classes (must be visually and linguistically distinct)

| Class | Definition | UX treatment |
| --- | --- | --- |
| **USER REQUEST** | Natural language intent; L5 until formalized | Neutral input styling |
| **PROPOSAL** | Agent One structured plan; no side effects | Draft badge, explicit APPROVE/EDIT/REJECT |
| **AUTHORIZED COMMAND** | Human-approved, MC-bound instruction | Command ID, scope hash, expiry |
| **INFORMATION** | Read-only synthesis | No action buttons |
| **APPROVAL** | Human L2 decision record | Audit-linked, irreversible styling where applicable |

### 7.2 Invariants (from Agent-15, validated)

```text
PROMPT ≠ AUTHORIZATION
USER REQUEST ≠ AUTHORIZED COMMAND
PROPOSAL ≠ EXECUTED
RESULT ≠ ACCEPTANCE
ACTIVE ≠ AUTHORIZED ≠ TRUSTED ≠ CORRECT
```

### 7.3 UX affordances per transition

```text
USER REQUEST → Agent One formalizes → PROPOSAL (mission card)
PROPOSAL + human APPROVE → AUTHORIZED COMMAND (state change + MC record)
PROPOSAL + human REJECT → REJECTED (terminal, reason captured)
PROPOSAL + human EDIT → revised PROPOSAL (version incremented)
```

**Dangerous pattern to eliminate:** A button labeled "Approve" that triggers execution without showing scope hash, affected resources, and reversal options.

---

## 8. Mission UX

### 8.1 Natural language → structured mission

Example transformation:

```text
USER (fa):
«بررسی کن سازمان برای عملکرد خودمختار آماده است یا نه.»

AGENT ONE (PROPOSAL — not yet authorized):
Mission: Autonomy Readiness Assessment
Objective: Determine whether organizational runtime supports autonomous multi-agent operation.
Constraints: READ_ONLY · NO_AHOS_MODIFICATION · NO_RUNTIME_CHANGES
Domains: Identity · Lifecycle · Mission Control · Messaging · Verification · Context · Security
Expected outputs: Readiness matrix · Blockers · Evidence · Contradictions · Recommended next mission
Human actions: [APPROVE] [EDIT] [REJECT]
```

### 8.2 Mission lifecycle UX (composed model)

Mission status is **not** a single enum. UX composes orthogonal dimensions:

| Dimension | States (UX vocabulary) |
| --- | --- |
| **Mission lifecycle** | Planning · Active · Waiting · Blocked · Verification · Acceptance · Complete |
| **Evidence status** | None · Partial · Sufficient · Stale · Contradicted |
| **Verification status** | Not requested · Pending · Pass · Fail · Inconclusive |
| **Acceptance status** | Not required · Pending · Accepted · Rejected · Deferred |

Slice 1 `TaskState` (`PROPOSED`, `AUTHORIZED`, `RUNNING`, `BLOCKED`, `COMPLETED`, `FAILED`, `CANCELLED`, `REJECTED`) maps to **mission lifecycle** partially — UX must add Verification and Acceptance explicitly.

### 8.3 Mission graph UX

Missions are often **DAGs**, not lines:

```text
Mission: Autonomy Readiness
├── Agent-03 Security        ──┐
├── Agent-05 Epistemic       ──┼──► Agent One synthesis
├── Agent-14 Runtime         ──┤
├── Agent-16 Verification    ──┘
└── Agent-19 Red Team (challenge)
```

**UX rules:**

- Parallel edges ≠ peer command authority
- Result dependency ≠ command dependency
- Synthesis node is Agent One — not a hidden merge of opinions

### 8.4 Mission card information architecture

Minimum fields on every mission surface:

```text
MISSION_ID · TITLE · OBJECTIVE · CONSTRAINTS · PHASE
COMMANDER · CREATED · UPDATED · CONTEXT_VERSION
PENDING_HUMAN_DECISIONS · BLOCKERS · CAPABILITY_GAPS
```

---

## 9. Agent Lifecycle UX

### 9.1 Agent status vocabulary (human-readable)

Map Constitution + Agent-14/15 lifecycle to UI labels:

```text
REGISTERED · IDLE · DORMANT · WAITING_FOR_COMMAND
ACTIVATION_REQUESTED · AUTHORIZED · ACTIVE · COMPLETED
FAILED · TIMEOUT · CANCELLED · BLOCKED · SUSPENDED · QUARANTINED
```

`[DOCUMENTED_ONLY]` — no agent lifecycle FSM in code; worker lifecycle in research path only.

### 9.2 Visual semantics (critical separations)

| Display | Must NOT visually imply |
| --- | --- |
| ACTIVE (working) | AUTHORIZED (governance grant) |
| AUTHORIZED | TRUSTED (epistemic) |
| TRUSTED | CORRECT (truth) |
| REGISTERED (in registry) | OPERATIONAL (can run) |

Slice 1 seeds all 19 roles at `MaturityLevel.REGISTERED` (0) — below execution threshold. UX must show **registered logical role** distinctly from **active specialist worker**.

### 9.3 Agent roster presentation

**Default:** Hidden or summarized ("3 specialists working on security, runtime, verification").

**Drill-down:** Full roster with plane label (A / D / Research), maturity, lifecycle, last mission, capability gaps.

---

## 10. Organizational Status UX

### 10.1 Level 0 organization snapshot

Single calm panel:

```text
ORGANIZATION STATUS: SUBSTRATE-1 — NOT OPERATIONAL (honest current label)

Active missions: 0 (or N)
Pending your decision: 0 (or N)
Unresolved contradictions: 1 (Dual-19)
Capability gaps blocking autonomy: 12 (launch blockers)

Nothing needs your attention.  ← valid prominent state
```

**Current honest label:** `MANUAL CONTROL PLANE — CURSOR MEDIATED`

### 10.2 Status dimension separation

Never collapse:

```text
MISSION STATUS ≠ AGENT STATUS ≠ EVIDENCE STATUS ≠ VERIFICATION STATUS ≠ ACCEPTANCE STATUS
```

Use **multi-badge** or **stacked status bar** — not one color dot.

### 10.3 Organizational maturity display

Adopt Agent-16 maturity framing:

```text
CURRENT:  SUBSTRATE-1 (tested policy + epistemic core)
TARGET:   SUBSTRATE-4+ (MC + Agent One + bus + durable + IV plane)
```

Show gap explicitly — prevents illusion of operational organization after test pass.

---

## 11. Evidence / Epistemic UX

### 11.1 Epistemic object display (bind to Slice 2B)

`[IMPLEMENTED]` types in `agent_org/epistemic.py`:

```text
Source · Evidence · Claim · Hypothesis · Prediction · Observation
KnowledgeCandidate · ContradictionCase · VerificationRecord · Approval · MemoryRecord
```

Each artifact in UX shows: **type · ID · lifecycle state · verification status · freshness · provenance · linked evidence**.

### 11.2 Epistemic posture vocabulary (Agent-05 aligned)

Organization-level epistemic states for summaries:

```text
KNOWN · UNCERTAIN · UNKNOWN · CONTRADICTORY · NOVEL
```

Mapping rules:

| State | UX meaning |
| --- | --- |
| KNOWN | Supported by current L0/L1 evidence, no open contradiction |
| UNCERTAIN | Partial evidence; explicit gaps listed |
| UNKNOWN | No evidence; not guessed |
| CONTRADICTORY | ContradictionCase OPEN or RETAINED_UNCERTAIN |
| NOVEL | New claim without prior organizational memory |

### 11.3 Forbidden UX patterns

```text
❌  AI Confidence: 97%        (when evidence weak)
✅  Evidence status: PARTIALLY_VERIFIED
     Independent verification: NOT PERFORMED
     Primary uncertainty: MC not implemented
     Contradictory sources: 2
```

```text
❌  Green "Verified" badge on agent completion
✅  "Result produced · Independent verification: PENDING · Acceptance: NOT REQUESTED"
```

### 11.4 Assurance field

Slice 2B `assurance` (0–100) on Evidence/Memory is **warrant strength metadata**, not user-facing confidence score. If shown, label **"Assurance (internal warrant)"** and never animate.

---

## 12. Trust Model

### 12.1 Trust is evidence-visible, not presentation-polished

User must always be able to answer:

1. **Why does the organization believe this?**
2. **What evidence supports it?**
3. **Who verified it (independently)?**
4. **What would falsify it?**
5. **What remains unknown?**

### 12.2 Trust ladder (display, not authority)

```text
FACT / OBSERVATION (L0 direct)
  ↑ supported by
EVIDENCE (bounded artifact)
  ↑ interpreted as
CLAIM / HYPOTHESIS
  ↑ tested via
VERIFICATION RECORD (INDEPENDENT ≠ SELF_CHECK)
  ↑ gated by
ACCEPTANCE (human/governance)
  ↓ may enter
ORGANIZATIONAL MEMORY (PROMOTED — not truth by default)
```

### 12.3 Distinct trust tokens (never collapse in UI)

```text
FACT/OBSERVATION · EVIDENCE · CLAIM · HYPOTHESIS · PREDICTION · MODEL OUTPUT
AGENT OPINION · CONSENSUS · CONTRADICTION · VERIFIED RESULT · ACCEPTED RESULT
DECISION · OUTCOME
```

**Consensus ≠ truth.** Correlated LLM agreement must display **"Correlated agreement — independence not established"**.

### 12.4 VerificationKind display

`[IMPLEMENTED]` in epistemic.py:

```text
INDEPENDENT  → may contribute to trust ladder
SELF_CHECK   → labeled "Self-check only — not independent verification"
```

---

## 13. Contradiction UX

Contradictions are **first-class**, never averaged, never hidden.

### 13.1 Contradiction card template

```text
⚠ CONTRADICTION DETECTED — UNRESOLVED

Position A: [Agent-08 / market interpretation X]
Evidence: [evidence.abc, evidence.def]
Source level: L3 architecture doc

Position B: [Agent-11 / risk implication Y]
Evidence: [evidence.ghi]
Source level: L3 architecture doc

Conflict type: INTERPRETATION · SCOPE · TEMPORAL · IDENTITY
Impact: HIGH — affects readiness assessment
Independent verification: REQUIRED
Organizational state: UNRESOLVED

Recommended action (PROPOSAL): Mission to reconcile via Agent-05 + Agent-16
[APPROVE RECONCILIATION MISSION] [DEFER] [OVERRIDE WITH REASON]
```

### 13.2 Known standing contradiction (must remain visible)

**Dual-19:** Plane A (`agent.*`) vs Plane D (`agent.org.*`) — see §30.

### 13.3 ContradictionState binding

`[IMPLEMENTED]` `ContradictionState`: OPEN · UNDER_INVESTIGATION · RESOLVED · RETAINED_UNCERTAIN

RETAINED_UNCERTAIN is a **valid terminal UX state** — organization honestly preserves disagreement.

---

## 14. Verification UX

### 14.1 Pipeline visibility

Never collapse:

```text
RESULT PRODUCED → AWAITING INDEPENDENT VERIFICATION → VERIFIED → AWAITING ACCEPTANCE → ACCEPTED
```

Each stage has distinct visual weight (Agent-18 implements; Agent-17 specifies requirement).

### 14.2 Verification request UX

Human or Agent One may trigger:

```text
VERIFICATION_REQUEST
  target: [artifact/claim/mission result]
  verifier: [Agent-16 role — when runtime exists]
  independence requirement: MUST NOT BE PRODUCER
  status: PENDING | PASS | FAIL | INCONCLUSIVE
```

Today: **`[PLANNED]`** — IV dispatch not implemented; UX shows manual Agent-16 mission as interim pattern with honest label.

### 14.3 Producer ≠ verifier

Same Cursor session verification today = **`[UNVERIFIED independence]`** — UX must warn if producer and verifier principals match.

---

## 15. Acceptance UX

Acceptance is **human/governance authority**, distinct from verification.

| State | Meaning | UX |
| --- | --- | --- |
| Not required | Informational mission | No acceptance gate shown |
| Pending | Verified or unverified result awaiting human | Explicit ACCEPT / REJECT / DEFER |
| Accepted | L2 decision recorded | Links to Approval artifact |
| Rejected | Explicit non-acceptance | Reason required |
| Deferred | Acknowledged; not now | Scheduled revisit optional |

**Slice 2B:** `Approval` artifact with expiry, scoped action — UX binds acceptance button to approval record creation, not chat acknowledgment.

---

## 16. Capability Gap UX

When requested capability does not exist, **never hallucinate organizational ability**.

### 16.1 Capability gap card

```text
⛔ CAPABILITY GAP

Requested: Durable Mission Controller
Current status: NOT IMPLEMENTED
Evidence: Agent-16 §4.2; repo search — no MC entry point
Available alternative: Document-only analysis (READ_ONLY mission)
Impact: Autonomous execution cannot proceed
Recommended next mission (PROPOSAL): Agent-14 Phase 1 implementation
```

### 16.2 Known capability gaps (UX must be able to display)

From Agent-16, validated:

```text
Mission Controller · Agent One runtime · Message bus · Agent lifecycle FSM
Durable persistence · Slice 1↔2B federation · Context sync gate
Instruction stack enforcement · IV dispatch · Cursor federation bridge
Organizational memory runtime · Domain runtime adapters
```

### 16.3 PLANNED vs AVAILABLE labeling

Any surface showing future inter-agent messages, bus traffic, or Agent One auto-delegation must carry:

```text
[PLANNED — NOT AVAILABLE AT RUNTIME]
```

---

## 17. Failure UX

Failures must be **typed**, not generic.

### 17.1 Failure taxonomy UX

| Type | User sees |
| --- | --- |
| UNKNOWN | What is unknown; what was attempted |
| BLOCKED | Blocker + authority missing |
| CAPABILITY GAP | §16 template |
| VERIFICATION FAILED | What failed verification; what remains valid |
| CONTRADICTION | §13 template |
| TIMEOUT | Elapsed, last progress, partial results |
| PARTIAL FAILURE | What succeeded vs failed |
| INDETERMINATE RESULT | Cannot decide; evidence insufficient |
| STALE CONTEXT | Context version/age; refresh action |
| MISSING EVIDENCE | Required evidence type absent |

### 17.2 Failure response structure

Every failure surface answers:

```text
WHAT FAILED · WHAT DID NOT FAIL · WHAT IS STILL TRUSTWORTHY · WHAT ACTION IS REQUIRED
```

**Forbidden:** "Something went wrong."

### 17.3 Comfortable ignorance

Prominent, non-alarming:

```text
"I don't know" — with listed missing evidence and proposed next step
```

---

## 18. Context UX

### 18.1 Context dimensions

```text
CURRENT CONTEXT · CONTEXT VERSION · CONTEXT AGE · STALE CONTEXT · CONTEXT CONFLICT
```

### 18.2 User query

> "Are you using the latest organizational context?"

Agent One response pattern:

```text
Context pack: ctx-20260914-017-v3
Hash: sha256:abc…
Assembled: 2026-09-14T19:30:00Z (4h ago)
Sources: 12 files · 3 mission artifacts · governance v0.1.0
Stale flags: Agent-14 doc SUPERSEDED partial — §Phase 7 wording
Conflict: Dual-19 identity map unresolved — both planes included with labels
Recommendation: Refresh context before consequential mission [PROPOSE]
```

Today: **`[PLANNED]`** — Context Pack Gate not implemented; honest answer is "context is whatever this Cursor session loaded."

### 18.3 Context conflict UX

When planes disagree, show **both** with plane labels — never silent pick.

---

## 19. Organizational Memory UX

Memory is **not** an opaque "AI memory" blob.

### 19.1 Memory kinds (`[IMPLEMENTED]` MemoryKind)

```text
EPISODIC · SEMANTIC · PROCEDURAL · FAILURE · HYPOTHESIS · CAUSAL
PERFORMANCE · SELF_MODEL
```

Add UX category for organizational decisions (maps to Approval + governance records when not MemoryRecord).

### 19.2 Memory card fields

```text
What · Why remembered · When learned · Evidence IDs · Verified? · Accepted?
Still current? · Superseded by? · Memory state (CANDIDATE/PROMOTED/…)
```

### 19.3 Memory ≠ truth

PROMOTED memory displays:

```text
Organizational memory (promoted) — not automatic truth
Last verified: [date or NEVER]
Open challenges: [N]
```

---

## 20. Change Propagation UX

Document edit ≠ organizational truth change.

### 20.1 Change propagation pipeline display

```text
CHANGE DETECTED: Operating Baseline v1.1 proposed
Affected: Agent-07 · Agent-08 · Agent-10 · Agent-12
Impact: HIGH
Propagation: PROPOSED → IMPACT ANALYSIS → OWNER → APPROVAL → MISSION
            → IMPLEMENTATION → VERIFICATION → ACCEPTANCE → MEMORY
Current stage: PROPOSED
Verification required: YES
Acceptance: PENDING
```

### 20.2 UX rule

Governance doc update in git ≠ propagated organizational rule until L2 adoption + acceptance recorded.

---

## 21. Agent-to-Agent Transparency

Expose **auditable artifacts**, not chain-of-thought.

### 21.1 Message inspection row (future — PLANNED)

```text
Agent-12 REQUESTED DATA FROM Agent-07
Type: EVIDENCE_REQUEST · Mission: MISSION-042 · Status: COMPLETED
Purpose: Schema validation for backtest inputs
Result ref: evidence.xyz · Authorization: grant scoped read
Timestamp: … · Verification: N/A (request) · Independent check: N/A
```

### 21.2 Current honest display

```text
INTER_AGENT_COMMUNICATION: NOT AVAILABLE
Historical agent work occurred via Cursor manual handoff — not message bus delivery.
```

Do not render fake message threads from markdown filenames alone without provenance.

---

## 22. Organizational Self-Model

Long-term goal: Agent One maintains inspectable self-model.

### 22.1 Self-model dimensions

```text
WHO EXISTS · WHO IS ACTIVE · WHO IS AUTHORIZED · WHO CAN DO WHAT
WHAT MISSIONS EXIST · WHAT CAPABILITIES EXIST · WHAT CAPABILITIES ARE MISSING
WHAT IS VERIFIED · WHAT IS UNKNOWN · WHAT IS BLOCKED · WHAT CHANGED · WHAT NEEDS ATTENTION
```

### 22.2 Current honest self-model snapshot

```text
WHO EXISTS: 19 Slice 1 logical roles + 1 research analyst + 19 Plane D blueprint (unseeded)
WHO IS ACTIVE: None at runtime — Cursor sessions only
WHO IS AUTHORIZED: All Slice 1 at REGISTERED maturity — below ALLOW threshold
CAPABILITIES MISSING: §16.2 list
VERIFIED: Substrate tests (251) — not organizational operation
UNKNOWN: Federation mapping, Agent One principal id, verifier rules
BLOCKED: 12 launch blockers (Agent-16)
NEEDS ATTENTION: Dual-19 · Agent One runtime · MC
```

UX presents self-model as **evidence-linked dashboard** — `[PLANNED]` until MC + registry federation exist.

---

## 23. Human Approval Gates

Derived from Constitution, Slice 1 global denies, Agent-15/16 — not assumed.

### 23.1 Categories requiring normal human approval

| Category | Source | UX gate |
| --- | --- | --- |
| Policy / governance changes | Constitution §3; `UPDATE_POLICY` denied to agents | Explicit L2 approval flow |
| Authority / grant changes | TCB `DELEGATE_AUTHORITY` | Scoped approval + expiry display |
| Credential access | Slice 1 deny `credentials.access` | Hard block + explanation |
| Production / AHOS execution | Global denies `ahos.*`, `production.operate` | Hard block unless future L2 |
| Live trading / financial execution | Deny `trading.live` | Hard block |
| Irreversible changes | Governance REQUIRES_REVIEW | Confirm + rollback plan if any |
| Organizational structural changes | Dual-19 merge, registry edit | HD-16-02 level decision |
| Agent One constitutional changes | Agent One forbidden policy modify | Human + Agent-04 path |
| Knowledge promotion | `PROMOTE_KNOWLEDGE` gated D-01/D-04 | Separate from mission approve |
| Mission activation (consequential) | MC design | APPROVE before RUNNING |

### 23.2 Categories that may auto-proceed (with constraints)

| Category | Condition |
| --- | --- |
| READ_ONLY analysis | Constraints bound; no mutation tokens |
| Status queries | Information only |
| Internal specialist delegation | Within approved mission scope + authority |
| Verification request routing | Cannot accept results |

---

## 24. Emergency / Stop UX

### 24.1 Control actions (distinct semantics)

| Action | Effect | Typical actor |
| --- | --- | --- |
| **PAUSE** | Suspend progress; preserve state | Human principal |
| **CANCEL** | Terminalize mission; no resume | Human principal |
| **STOP ORGANIZATION** | Halt all active missions | Human principal — high friction confirm |
| **QUARANTINE AGENT** | Isolate agent; block sends | Human + security path |
| **BLOCK CAPABILITY** | Deny specific capability token | Governance |
| **REVOKE AUTHORITY** | Invalidate grants | Governance / TCB |

### 24.2 UX requirements

- **PAUSE ≠ CANCEL ≠ QUARANTINE** — different colors, icons, confirmations
- STOP requires typed confirmation + consequence summary
- Post-stop: show what was safely preserved vs indeterminate

Today: **`[PLANNED]`** — no runtime to stop; UX applies to future MC.

---

## 25. Long-Running Mission UX

Missions may run minutes → days.

### 25.1 Async interaction model

Human does not watch continuously. Mission surfaces:

```text
Last meaningful update · Next expected event · Current phase
Active agents · Pending verification · Human decision required
Estimated completion: [unknown honest label if unknown]
```

### 25.2 Notification philosophy

Notify on:

- Human decision required
- Critical contradiction
- Verification failed / mission blocked
- Capability gap discovered
- Mission complete **awaiting acceptance** (not on mere progress ticks)

Do **not** notify on routine specialist progress (digest optional).

### 25.3 Re-entry UX

When human returns:

```text
"Since you were away: 2 specialists completed · 1 contradiction surfaced · 1 decision pending"
[Jump to decision] [Full timeline]
```

---

## 26. Alert Architecture

### 26.1 Alert types (future)

```text
CRITICAL CONTRADICTION · VERIFICATION FAILED · MISSION BLOCKED · CAPABILITY GAP
SECURITY ESCALATION · HUMAN DECISION REQUIRED · MISSION COMPLETE (pending acceptance)
NEW DISCOVERY · CANONICAL CHANGE PROPOSED · AGENT QUARANTINED
NO ACTION REQUIRED (anti-alert — daily digest ok)
```

### 26.2 Alert properties

| Property | Design |
| --- | --- |
| Severity | CRITICAL · HIGH · MEDIUM · LOW · INFO |
| Channel | In-app default; Telegram/n8n `[PLANNED]` not assumed integrated |
| Persistence | Until acknowledged or resolved |
| Acknowledgement | Required for CRITICAL/HUMAN DECISION |
| Escalation | Unacknowledged CRITICAL → repeat + email `[PLANNED]` |
| Suppression | User rules per mission type |
| Deduplication | Same blocker id — no alert storm |

### 26.3 Alarm fatigue prevention

**"Do nothing" is valid** — daily summary may say:

```text
✓ Nothing needs your attention. 3 missions progressing. Next decision: none scheduled.
```

---

## 27. Persian-First / Bilingual UX

### 27.1 Policy

AHOS product already treats Persian as first-class (`fa-IR`, RTL switching in product codebase). Agent Organization UX **inherits Persian-first** with English technical identifiers preserved.

### 27.2 Do not translate (machine-readable identifiers)

```text
AGENT-16 · TASK-20260914-017 · MISSION_STATUS · agent.org.05-epistemic-reasoning
File paths · Git hashes · Test names · Evidence IDs (evidence.abc)
```

### 27.3 Bilingual patterns

| Element | Persian | English |
| --- | --- | --- |
| UI chrome / explanations | Primary | Secondary toggle |
| Agent One conversational prose | Match user language | Match user language |
| Status tokens | Persian label + English token | `وضعیت: در انتظار تایید (PENDING_ACCEPTANCE)` |
| Numerals | Latin for precision (AHOS convention) | Latin |
| Timestamps | Jalali display option + ISO8601 technical | ISO8601 |
| Code citations | LTR isolated blocks | LTR |

### 27.4 RTL/LTR mixing

- Conversation RTL; code/evidence blocks LTR with `dir=ltr`
- Mixed badges: `[تایید نشده | NOT VERIFIED]`

### 27.5 Persian UX terminology samples `[PROPOSED]`

```text
ماموریت (Mission) · شواهد (Evidence) · تناقض (Contradiction)
تایید (Acceptance) · تایید مستقل (Independent Verification) · خلاء توانایی (Capability Gap)
بدون اقدام لازم (No Action Required) · پیشنهاد (Proposal) · دستور (Authorized Command)
```

---

## 28. Accessibility / Cognitive Load

### 28.1 Design for daily long-term use

- **Three density modes:** Calm (default) · Standard · Expert
- **Attention budget:** Level 0 fits one screen on mobile
- **Interruption-safe:** Decisions persist until acted
- **Overnight missions:** Morning summary, not hourly pings
- **Color never sole channel** — icon + text for status
- **Cognitive load cap:** Max 3 pending decisions shown prioritized; rest in queue

### 28.2 Accessibility

- WCAG 2.2 AA target for Agent-18 implementation
- Screen reader: status dimensions announced separately
- Reduced motion option — no animated "working" theatre
- High contrast epistemic badges

### 28.3 Novice vs expert

| Mode | Behavior |
| --- | --- |
| Novice | Hides agent IDs by default; plain language |
| Expert | Shows planes, IDs, envelope hashes, audit refs |

---

## 29. UX Threat Model

UI can cause governance failures without malicious intent.

### 29.1 Dangerous UI patterns and safeguards

| Threat | Example | Safeguard |
| --- | --- | --- |
| **False execution** | "Approve" runs code | Approve binds to scope hash; preview; separate EXECUTE confirm |
| **False verification** | Green "Verified" on completion | Stage-specific labels; INDEPENDENT vs SELF_CHECK |
| **False authority** | Specialist under Agent One looks authorized | Show maturity + grant scope; REGISTERED ≠ AUTHORIZED |
| **Consensus as truth** | "3 agents agree" | "Correlated — independence not established" |
| **False completion** | Mission complete before IV | Gate COMPLETE badge on acceptance criteria |
| **False canonical** | Proposed doc looks active | PROPOSED watermark; L2 adoption flag |
| **Fake automation** | Animated agent graph while manual | PLANNED label; current mode banner |
| **Confidence theatre** | Percentage without evidence | Epistemic block §11 |
| **Monolith illusion** | Agent One avatar executes all | Show delegation chain on drill-down |
| **Alert fatigue → ignore** | Noise notifications | NO ACTION REQUIRED state; dedup |
| **RTL injection confusion** | Bidirectional spoofing in evidence | Sanitize + isolate LTR technical blocks |

### 29.2 UX security principle

```text
UI APPEARANCE ≠ AUTHORITY
UI COMPLETENESS ≠ VERIFICATION
UI ACTIVITY ≠ PROGRESS
```

---

## 30. Dual-19 UX Implications

**DUAL_19 = UNRESOLVED** — `[VERIFIED]`

### 30.1 Two taxonomies

| Plane | ID pattern | Status |
| --- | --- | --- |
| **A** | `agent.chief-orchestrator`, … | `[IMPLEMENTED]` seeded |
| **D** | `agent.org.01-chief-architect`, … | `[PLANNED]` not seeded |

Plus **RESEARCH_ANALYST_AGENT** — implemented, in neither list.

### 30.2 UX requirements for unresolved roster

- Never show single unified "19 agents" without plane disclaimer
- Every agent reference shows: `AGENT-NN · Plane A|D|Research · Status`
- Dual-19 standing contradiction badge in org snapshot
- Mission delegation picks **explicit plane** — human decision HD-16-02 before hiding duality

### 30.3 UX consequences

- Commander tree cannot be enforced in UI until federation
- Communication recipient ambiguous — show warning on Plane D addresses
- Agent One identity unsettled (`agent.org.01-chief-architect` vs new id — HD-16-04)

---

## 31. Current vs Future UX

### 31.1 CURRENT (honest — what Mehrdad uses today)

```text
Human
  ↓
Cursor / Manual Control Plane
  ↓
Artifacts / Prompts / Reports (markdown, chat)
  ↓
Human (reconcile manually)
```

**Banner text `[PROPOSED]`:** `حالت فعلی: کنترل دستی از طریق Cursor — سازمان خودکار نیست`

### 31.2 FUTURE (target — not claimed as live)

```text
Human
  ↓
Agent One (primary interface)
  ↓
Mission Controller
  ↓
Specialists
  ↓
Evidence / Results
  ↓
Independent Verification
  ↓
Acceptance
  ↓
Organizational Memory
  ↓
Agent One
  ↓
Human
```

**Never mix** future surfaces into current mode without mode switch.

### 31.3 Mode switch UX

Explicit toggle or environment banner:

```text
[ CURRENT: MANUAL ]  |  [ FUTURE: preview mock — PLANNED ]
```

Preview mock must be watermarked **SIMULATION**.

---

## 32. Product Principles

Validated and refined from mission list:

| ID | Principle | Validation |
| --- | --- | --- |
| **P1** | Human Intent First | **ADOPT** — all flows start from intent formalization |
| **P2** | One Primary Organizational Interface | **ADOPT** — Agent One front door; specialists behind |
| **P3** | Progressive Disclosure | **ADOPT** — Levels 0–7 |
| **P4** | Evidence-Visible Trust | **ADOPT** — bind to Slice 2B artifacts |
| **P5** | Explicit Uncertainty | **ADOPT** — UNKNOWN comfortable |
| **P6** | Contradiction Visibility | **ADOPT** — first-class, Dual-19 standing |
| **P7** | No Fake Automation | **ADOPT** — PLANNED labels, current mode banner |
| **P8** | No Fake Capability | **ADOPT** — capability gap cards |
| **P9** | Human Authority Preservation | **ADOPT** — approval gates §23 |
| **P10** | Minimal Operational Burden | **ADOPT** — anti-micromanagement §34 |
| **P11** | Reversible Actions Where Possible | **ADOPT** — PAUSE vs CANCEL; soft deletes in memory |
| **P12** | Independent Verification Visibility | **ADOPT** — INDEPENDENT vs SELF_CHECK |
| **P13** | Clear Failure States | **ADOPT** — typed failures §17 |
| **P14** | Organizational Transparency | **ADOPT** — Layer B always available |
| **P15** | No Authority Through UI Appearance | **ADOPT** — §29 threat model |

**Added by Agent-17:**

| ID | Principle | Rationale |
| --- | --- | --- |
| **P16** | Product Separation | Org UX ≠ AHOS product UX |
| **P17** | Bilingual Equity | Persian-first, identifiers stable |
| **P18** | Calm Organization | No artificial activity signals |
| **P19** | Mode Honesty | CURRENT vs FUTURE never blurred |
| **P20** | Composition Over Collapse | Orthogonal status dimensions |

---

## 33. Human Operational Burden

### 33.1 Current assessment

```text
CURRENT_HUMAN_OPERATIONAL_BURDEN = HIGH
```

Mehrdad currently acts as:

- Mission controller
- Message bus (copy/paste)
- Context synchronizer
- Contradiction reconciler
- Verification scheduler
- Memory keeper
- Agent activator

`[VERIFIED]` Agent-16 §24.

### 33.2 Target assessment (future)

```text
TARGET_HUMAN_OPERATIONAL_BURDEN = LOW for coordination · MEDIUM for governance decisions
```

Human time on: intent, priorities, approvals, acceptance, escalations — not routing.

### 33.3 Burden reduction sequencing

1. MC + federation (stop manual mission tracking)
2. Agent One interface (stop per-agent prompt crafting)
3. Result ingestion (stop copy/paste)
4. IV dispatch (stop manual verification scheduling)
5. Context gate (stop manual context prep)

---

## 34. Anti-Micromanagement Design

### 34.1 Principles

- Default view excludes specialist prompts and raw traces
- Agent One summarizes; human drills down only when distrust or curiosity
- Batch decisions: "Approve all read-only sub-missions" with scope preview `[PROPOSED]`
- Trust but verify **structure** — verification scheduled by org, not requested ad hoc by human

### 34.2 What human still micromanages (acceptable)

- Irreversible actions
- Governance adoption
- Priority conflicts between domains
- Acceptance of contested results

### 34.3 What human must stop micromanaging (design target)

- Which specialist to open in Cursor
- Whether mission X is "done" (org tracks phases)
- Whether contexts match (context gate)

---

## 35. Agent One Anti-Monolith UX

UX must reflect architectural boundaries even when conversation feels unified.

### 35.1 Agent One does NOT personally (UX must not imply)

```text
Execute arbitrary code · Mutate databases · Verify itself · Approve itself
Grant authority · Bypass governance · Modify policy silently · Touch AHOS production
```

### 35.2 Delegation chain display (drill-down)

```text
Agent One (intent + synthesis)
  → Mission Controller (lifecycle + scope)
    → Specialist / Worker (domain work)
      → TCB (governed writes)
        → Verification (independent principal)
          → Acceptance (human)
```

### 35.3 Monolith warning signs in UX

If single avatar performs verify + accept + execute — **UX defect**. Show separated principals.

---

## 36. Future Dashboard / Interface Model

Not implementation — information architecture for Agent-18.

### 36.1 Primary surfaces

| Surface | Purpose | Layer |
| --- | --- | --- |
| **Conversation** | Agent One dialogue | A |
| **Mission Center** | Active/pending missions | A/B |
| **Decision Inbox** | Approvals, acceptances | A |
| **Contradiction Registry** | Open conflicts | B |
| **Evidence Explorer** | Artifact graph | B |
| **Org Map** | Self-model, capabilities | B |
| **Audit Timeline** | Events, envelopes | B |
| **System Mode** | CURRENT vs capabilities | A |

### 36.2 Layout philosophy

- **Conversation-first desktop:** Conversation left; contextual mission/evidence panel right (collapsible)
- **Mobile:** Conversation + Decision Inbox; drill-down to web for audit
- **No 19-agent dashboard default** — specialist roster is secondary

### 36.3 AHOS product separation

Separate app shell or clearly separated nav section:

```text
[ Organization ]  |  [ AHOS Intelligence ]   ← never merge without explicit product decision
```

---

## 37. Minimum Viable Organizational UX (MVOU)

Smallest UX proof aligned with Agent-15 MVCS:

### 37.1 Prerequisites (runtime — not UX alone)

1. Mission Controller (durable)
2. Cursor Federation Bridge
3. MissionCommandEnvelope validator
4. Agent One service (minimal — may be rules + LLM with strict output schema)
5. Result ingestion pipeline

### 37.2 MVOU feature set

```text
✓ Single Agent One conversation surface
✓ Mission proposal → approve/reject
✓ One specialist delegation (e.g., research or Cursor worker bound to mission id)
✓ Mission status (composed dimensions)
✓ Evidence ref display (minimum: report links + classification)
✓ CURRENT mode banner (honest)
✓ Capability gap when MC missing (honest before built)
✓ Persian/English input with identifier preservation
```

### 37.3 MVOU explicit exclusions

- Full 19-agent roster management
- Message bus visualization
- Organizational memory browser
- Telegram alerts
- AHOS integration UI

---

## 38. Future Advanced Organizational UX

After SUBSTRATE-4+:

- Live mission DAG visualization
- Inter-agent message inspector (PLANNED transport)
- Epistemic graph navigator (Slice 2B artifacts)
- Memory browser with supersession chain
- Change propagation tracker
- IV plane dashboard + verifier rotation
- Simulated org replay from audit (time travel)
- Expert mode: instruction stack layer view (L0–L8)
- Bilingual report export (PDF/md)

---

## 39. Open Questions

1. **Agent One embodiment:** Pure local service vs Cursor-backed hybrid during transition?
2. **Verifier independence:** Can LLM verify LLM output (HD-16-07)? UX must reflect decision.
3. **Dual-19 UX until resolved:** Show both planes forever vs forced merge UI?
4. **Acceptance granularity:** Per-mission vs per-artifact vs per-claim?
5. **Notification channel:** In-app only vs Telegram (currently not integrated)?
6. **Mobile scope:** Full audit on mobile or desktop-only Layer B?
7. **Agent One persona:** Named voice vs neutral organizational voice?
8. **Digest cadence:** Daily vs on-event for low-priority progress?
9. **Cross-product navigation:** When (if ever) does AHOS surface org missions?
10. **Simulation mode:** Allow Mehrdad to rehearse future UX against mock MC?

---

## 40. Human Decisions Required

Inherited from Agent-16 + UX-specific:

| ID | Decision |
| --- | --- |
| HD-16-01 | Adopt AGENT-01 = AGENT ONE as canonical L2 identity |
| HD-16-02 | Resolve Dual-19 — merge, federation, or dual-plane UX permanently |
| HD-16-03 | Legitimate agent contact channel (bus vs Cursor-only interim) |
| HD-16-04 | Agent One runtime principal id |
| HD-16-05 | Retire "Master Orchestrator" documentary commander labels |
| HD-16-06 | Operating Baseline v1 L2 adoption |
| HD-16-07 | Verifier eligibility and independence rules |
| **HD-17-01** | Persian-primary with English secondary — confirm for org UX |
| **HD-17-02** | Conversation-first vs dashboard-first default layout |
| **HD-17-03** | Accept SIMULATION/preview mode for future UX mockups |
| **HD-17-04** | Separate org app vs integrated AHOS nav (product boundary) |

---

## 41. Architectural Dependencies

UX implementation depends on (ordered):

```text
1. HD-16-01/02/04 human decisions (identity)
2. Agent-14 Phase 1: MC + lifecycle FSM + durable store + federation bridge
3. MissionCommandEnvelope + result ingestion (Agent-15)
4. Agent One service loop (minimal cognitive coordinator)
5. Context pack gate (Agent-15)
6. IV dispatch runtime (Agent-16 plane)
7. Slice 1 ↔ 2B federation (registry model)
8. Message bus (for Layer B inter-agent transparency)
9. Agent-18 visualization/frontend architecture
10. L2 governance adoption (approval semantics enforcement)
```

**UX cannot precede MC + federation** without violating P7/P8 (fake automation).

---

## 42. Verification Requirements

Agent-17 deliverables require independent verification:

| Claim | Verification method |
| --- | --- |
| No org UX runtime exists | Repo search + Agent-16 confirmation |
| Epistemic types match UX model | Crosswalk to `epistemic.py` |
| Approval gates match governance | Crosswalk to Constitution + policy denies |
| Dual-19 UX handling | Registry + planned map inspection |
| AHOS bilingual patterns | Spot-check AHOS `format.ts`, CommandCenter |
| Agent-16 discrepancies | Independent source reads |

**Recommended verifier:** Agent-16 or Agent-19 red team on UX threat model §29.

---

## 43. Recommended Next Mission

**STATE ONLY — DO NOT EXECUTE**

```text
PRIMARY:   AGENT-14 PHASE 1 IMPLEMENTATION (MC + federation + durable store)
           — prerequisite for any honest organizational UX beyond manual mode

PARALLEL:  AGENT-18 FRONTEND/VISUALIZATION ARCHITECTURE
           — consumes this document; builds visualization layer only

PARALLEL:  GOVERNANCE MISSION (HD-16-01/05/06) — identity + baseline adoption

SEQUENCED: AGENT ONE MINIMAL SERVICE + MVOU (after Phase 1 verified)

DO NOT:    Build polished dashboard before MC exists (violates P7/P8)
DO NOT:    Merge AHOS product UI with org control plane prematurely
```

---

## 44. AGENT-17 → AGENT-18 Handoff

### 44.1 What Agent-18 must build later (NOT now)

| Layer | Agent-18 deliverable |
| --- | --- |
| **Visualization** | Status badge system for orthogonal dimensions |
| **Visualization** | Mission card + DAG layout |
| **Visualization** | Contradiction card + evidence explorer |
| **Visualization** | Epistemic object renderers (12+ types) |
| **Visualization** | Drill-down Level 0–7 navigation |
| **Visualization** | RTL/bilingual layout system |
| **Visualization** | Decision inbox + approval flows |
| **Visualization** | CURRENT vs FUTURE mode banner + simulation watermark |
| **Visualization** | Alert/notification UI |
| **Frontend** | React (or chosen stack) components implementing above |
| **Frontend** | API bindings to MC / Agent One (when runtime exists) |

### 44.2 Separation preserved

```text
UX PRINCIPLE          → this document (Agent-17)
UX REQUIREMENT        → this document §5–§26
INTERACTION MODEL     → §4, §6, §7, §31
INFORMATION ARCHITECTURE → §8, §10, §36
VISUALIZATION REQUIREMENT → §36, §44.1 (Agent-18)
FRONTEND IMPLEMENTATION   → Agent-18 + engineering (future)
```

### 44.3 Agent-18 constraints from Agent-17

- No confidence percentages as primary trust signal
- No unified 19-agent grid as home screen
- No green "verified" without stage qualification
- Persian-first with LTR technical enclaves
- PLANNED features watermarked
- Agent One anti-monolith delegation display on drill-down

**AGENT_17_TO_AGENT_18_HANDOFF = COMPLETE — READY FOR VISUALIZATION ARCHITECTURE MISSION**

---

## Appendix A — Evidence Classification Key

Used throughout this document:

```text
VERIFIED · PARTIALLY_VERIFIED · DOCUMENTED_ONLY · PLANNED
UNVERIFIED · UNKNOWN · BLOCKED · SUPERSEDED
```

Runtime capabilities explicitly **NOT IMPLEMENTED** (independently confirmed):

```text
Agent One runtime · Mission Controller · Message Bus · Lifecycle Controller
Context Gate · Instruction Stack · Inter-agent communication
```

---

## Appendix B — Slice 1 TaskState → Mission UX Mapping

| TaskState | Mission lifecycle UX |
| --- | --- |
| PROPOSED | Planning |
| AUTHORIZED | Planning (approved) |
| RUNNING | Active |
| BLOCKED | Blocked |
| COMPLETED | Complete (pending verification/acceptance overlays) |
| FAILED | Blocked / failed |
| CANCELLED | Complete (cancelled) |
| REJECTED | Complete (rejected) |

---

```text
MISSION_STATUS = HUMAN_AGENT_ORGANIZATION_UX_ARCHITECTURE_ANALYSIS_COMPLETE_WITH_GAPS
AGENT_ID = AGENT-17
DIRECT_COMMANDER = AGENT-01 / AGENT ONE
LIFECYCLE_STATUS = IDLE / DORMANT / WAITING_FOR_NEW_COMMAND
AGENT_ONE_STATUS = PRIMARY_ORGANIZATIONAL_AGENT / CURRENT_INTENDED_ROOT
AGENT_ONE_RUNTIME_STATUS = NOT_IMPLEMENTED
DUAL_19 = UNRESOLVED
CURRENT_UX_STATUS = MANUAL_CURSOR_ARTIFACT_MEDIATED — NO ORGANIZATIONAL UX RUNTIME
ORGANIZATIONAL_UX_RUNTIME = NOT_IMPLEMENTED
AGENT_ONE_INTERFACE_RUNTIME = NOT_IMPLEMENTED
AHOS_IMPACT = NONE
CODE_CHANGES = NONE
RUNTIME_CHANGES = NONE
FRONTEND_CHANGES = NONE
DATABASE_CHANGES = NONE
GOVERNANCE_CHANGES = NONE
COMMIT = NONE
PUSH = NONE
LAUNCH_BLOCKERS = 12
NON_BLOCKING_GAPS = 22
HUMAN_DECISIONS_REQUIRED = HD-16-01; HD-16-02; HD-16-03; HD-16-04; HD-16-05; HD-16-06; HD-16-07; HD-17-01; HD-17-02; HD-17-03; HD-17-04
CAPABILITY_GAPS = Mission Controller; Agent One runtime; message bus; agent lifecycle FSM; durable persistence; Slice 1↔2B federation; context sync gate; instruction stack enforcement; IV dispatch; Cursor federation bridge; organizational memory runtime; domain runtime adapters; organizational UX surface; Agent One conversation interface; result ingestion pipeline; bilingual org UI i18n layer
CURRENT_HUMAN_OPERATIONAL_BURDEN = HIGH — Mehrdad is manual orchestrator, message bus, context sync, and reconciliation layer via Cursor
AGENT_16_INPUT_STATUS = MATERIALly ACCURATE — used as L1/L2 input; independently spot-checked source claims
AGENT_16_CORRECTIONS_REQUIRED = YES — code marker AGENT_ONE_STATUS comment should separate organizational role from runtime (HD-16-01); Constitution §3.1 "future orchestrator" wording; README nuance — governance mission, not this mission
AGENT_17_TO_AGENT_18_HANDOFF = COMPLETE — visualization and frontend architecture may proceed after human review of this document
NEW_CROSS_AGENT_DISCOVERIES = 4
RECOMMENDED_NEXT_MISSION = STATE ONLY — AGENT-14 PHASE 1 IMPLEMENTATION + PARALLEL AGENT-18 VISUALIZATION ARCHITECTURE — DO NOT EXECUTE
```
