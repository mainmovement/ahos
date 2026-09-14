# Agent Organization Security Architecture

```text
DOCUMENT_ID      = AGENT_ORGANIZATION_SECURITY_ARCHITECTURE
MISSION_ID       = TASK-20260914-003
VERSION          = 0.1.0
STATUS           = PROPOSED / READ_ONLY_SECURITY_ARCHITECTURE
AUTHORITY        = NONE CREATED
RUNTIME_EFFECT   = NONE
AHOS_EFFECT      = NONE
AGENT_ID         = AGENT-03 (agent.org.03-security-architect — documentary)
DIRECT_COMMANDER = MASTER_ORCHESTRATOR
```

This document is a **security architecture and threat-modeling artifact**. It does not implement controls, adopt governance, or grant authority. Facts cite repository evidence with explicit status labels. Proposals are labeled `[PROPOSED]`.

---

## 1. Executive Summary

`[VERIFIED]` The AHOS Agent Organization (`ahos-agent-org`) is an independent control-plane workspace with three implemented but **separate** foundations:

1. **Slice 1** (`ahos_org/`) — in-process logical registry, fail-closed symbolic authorization, task state machine, audit hash chain.
2. **Slice 2B** (`agent_org/`) — in-memory Trusted Command Boundary (TCB), epistemic artifact model, scoped grants/delegation, non-production session stub.
3. **Research path** (`research_worker/` + `agent_org/research_host/`) — one bounded Class A deterministic analyst with Windows `spawn` process isolation and JSON IPC firewalls.

`[VERIFIED]` None of these is Agent One, a production multi-agent mesh, a message bus, production identity, or an AHOS integration. `AGENT_ONE_STATUS = FUTURE_NON_AUTHORITY_ROOT`.

`[VERIFIED]` Security today is **policy logic and test-driven red-team suites**, not OS sandboxing, production authentication, or network isolation. The repository explicitly states: `DOCUMENTED CONTROL ≠ ENFORCED CONTROL`, `POLICY ≠ SECURITY BOUNDARY`.

`[PLANNED]` The future multi-agent cognitive system must scale from the current Cursor Control-Plane (human + Master Orchestrator in chat) into a governed runtime without allowing any specialist, orchestrator, memory store, communication channel, or external integration to silently become an unauthorized authority or execution path.

**Primary security objective:** prevent **authority collapse** — where identity, authorization, verification, and execution merge into a single undifferentiated component (especially the Master Orchestrator or a future Agent One).

**Current security posture:** `[PARTIALLY_VERIFIED]` — strong fail-closed **design** in Slice 1 and Slice 2B with extensive red-team tests; weak **enforcement boundary** against determined local attackers or production adversaries.

**Dual-19 status:** `[VERIFIED]` Plane A (Slice 1 `agent.*`) and Plane D (planned `agent.org.NN-*`) remain **unresolved**. This report analyzes security implications only; it does not merge, rename, or retire either taxonomy.

---

## 2. Security Principles

Evaluation against organizational principles:

| Principle | Current state | Future requirement |
| --- | --- | --- |
| **Least privilege** | `[IMPLEMENTED]` Slice 1 default deny; Slice 2B exact grants; research worker hard-deny list | Per-mission tool/data grants; no default tool access |
| **Zero trust** | `[PARTIALLY_VERIFIED]` — in-process trust assumptions remain; stub session is not production auth | Never trust model output, tool output, memory, or external content as authority |
| **Fail closed** | `[IMPLEMENTED]` `[TESTED]` — unknown capability/operation/resource → DENY; IPC malformed → terminate worker | All lifecycle transitions default deny without explicit authorization |
| **Separation of duties** | `[DESIGN_ONLY]` in protocols; `[IMPLEMENTED]` in TCB promotion gates (D-01/D-04) | Identity ≠ authority ≠ verification ≠ approval ≠ execution |
| **Defense in depth** | `[PARTIALLY_VERIFIED]` — policy + IPC schema + process spawn; no OS sandbox | Layered: command auth, mission scope, tool policy, data policy, TCB, human gate |
| **Explicit authority** | `[DESIGN_ONLY]` Constitution; `[IMPLEMENTED]` grant chain derivation | No implied authority from role title, prompt, or documentation |
| **Provenance** | `[IMPLEMENTED]` audit hash chains (in-memory); `[DESIGN_ONLY]` inter-agent message provenance | Every claim, command, and memory write carries source binding |
| **Auditability** | `[IMPLEMENTED]` Slice 1 + 2B audit append; tamper detection in tests | Durable, externally anchorable audit for production |
| **Idempotency** | `[IMPLEMENTED]` command replay detection in TCB | Mission/command deduplication at orchestration layer |
| **Revocability** | `[IMPLEMENTED]` grant/session revocation in Slice 2B; `[DOCUMENTED_DEFERRED]` principal suspend (D-15) | Instant revocation of mission grants, memory promotion, tool access |
| **Isolation** | `[PARTIALLY_VERIFIED]` — spawn worker only; core TCB same-process | Process/container isolation per specialist; mediated AHOS boundary |
| **Deterministic boundaries** | `[IMPLEMENTED]` closed command/operation sets; frozen IPC allow-lists | Closed MESSAGE_TYPE, lifecycle transition, and tool catalogs |

**Honesty constraint:** Do not claim full Zero Trust. Current implementation trusts the Python process, local operator session stub, and same-Windows-user process model.

---

## 3. Current Security Architecture

### 3.1 Layer map (as-built)

```text
┌─────────────────────────────────────────────────────────────────┐
│  CURSOR CONTROL-PLANE (L5)                                      │
│  Human Principal → Master Orchestrator (chat/worker launch)     │
└────────────────────────────┬────────────────────────────────────┘
                             │ no runtime enforcement
┌────────────────────────────▼────────────────────────────────────┐
│  GOVERNANCE DOCUMENTATION (L3) — DESIGN_ONLY                    │
│  Constitution, protocols, planned 19 map, charters (template)   │
└────────────────────────────┬────────────────────────────────────┘
                             │ vocabulary only unless code agrees
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐   ┌─────────────────┐   ┌──────────────────────┐
│ Slice 1       │   │ Slice 2B        │   │ Research path        │
│ ahos_org/     │   │ agent_org/      │   │ worker + host        │
│ [IMPLEMENTED] │   │ [IMPLEMENTED]   │   │ [IMPLEMENTED]        │
│ in-process    │   │ in-memory TCB   │   │ spawn + JSON IPC     │
│ policy model  │   │ epistemic core  │   │ Class A analyst only │
└───────────────┘   └─────────────────┘   └──────────────────────┘
        │                    │                    │
        └────────────────────┴────────────────────┘
                             │ no AHOS connection
                             ▼
                    ┌─────────────────┐
                    │ AHOS (separate) │  — NOT CONNECTED
                    └─────────────────┘
```

### 3.2 Implemented security controls

| Control | Location | Status | Boundary class |
| --- | --- | --- | --- |
| Global deny capabilities (AHOS, credentials, trading, Telegram, n8n) | `ahos_org/policy.py` | `[IMPLEMENTED]` `[TESTED]` | Symbolic policy |
| Fail-closed authz pipeline | `ahos_org/governance.py` | `[IMPLEMENTED]` `[TESTED]` | In-process |
| Task state machine (legal transitions only) | `ahos_org/tasks.py` | `[IMPLEMENTED]` `[TESTED]` | In-process |
| Protected resource registry (empty AHOS allow-lists) | `ahos_org/resources.py` | `[IMPLEMENTED]` `[TESTED]` | Symbolic |
| Audit hash chain | `ahos_org/audit.py`, `agent_org/audit.py` | `[IMPLEMENTED]` `[TESTED]` | In-memory |
| TCB single mutation ingress | `agent_org/tcb.py` | `[IMPLEMENTED]` `[TESTED]` | In-process |
| Command replay protection | TCB duplicate command ID | `[IMPLEMENTED]` `[TESTED]` | In-process |
| Grant/delegation attenuation (max depth 3) | `agent_org/authority.py` | `[IMPLEMENTED]` `[TESTED]` | In-process |
| D-01 exclusive promotion path | `agent_org/epistemic.py`, TCB | `[IMPLEMENTED]` `[TESTED]` | In-process |
| D-04 candidate-bound approval | Approval.candidate_id binding | `[IMPLEMENTED]` pending independent verification | In-process |
| Memory ≠ truth firewall | TCB denies memory promotion | `[IMPLEMENTED]` `[TESTED]` | In-process |
| Research IPC hard-deny + schema validation | `research_worker/protocol.py`, `ipc_handler.py` | `[IMPLEMENTED]` `[TESTED]` | Process + API |
| Windows spawn isolation | `IsolatedResearchRuntime` | `[IMPLEMENTED]` `[TESTED]` | Process (same user) |
| Import boundary (static/test-enforced) | `agent_org/untrusted/` | `[IMPLEMENTED]` | Static analysis |

### 3.3 What is NOT a security boundary today

| Item | Evidence | Risk |
| --- | --- | --- |
| Python in-process code | Slice 2B implementation report §4 | Reflection/bypass of store permit in same process |
| Local operator session stub | `agent_org/identity.py` | Holding stub object ≈ root trust |
| Constitution/protocols | All marked `DESIGN_ONLY` / `NOT_IMPLEMENTED` | Documentation cannot deny what code allows |
| Cursor chat / mission text | L5 | Prompt injection, authority confusion |
| Master Orchestrator | No runtime enforcement | Can synthesize without separation of duties |
| OS network/shell | `OS_NETWORK_ISOLATION = NOT_PROVIDED` | API denial ≠ OS impossibility |
| Durable encrypted store | Not implemented | State loss; no at-rest protection |

### 3.4 Test evidence

`[VERIFIED]` Test definitions exist: ~49 methods in `tests/`, ~203+ in `tests2b/` (static count). Red-team suites cover Slice 1 (`test_red_team.py`), Slice 2B (`test_red_team_2b.py`), research host (`test_research_host_red_team.py`), and worker (`test_research_worker.py`).

`[STALE]` Slice 2B implementation report cites 121/121 PASS; current inventory is larger. Current PASS status for full suite: `[UNVERIFIED]` in this mission (tests not re-executed).

---

## 4. Future Security Architecture

`[PROPOSED]` Target layered architecture for safe multi-agent scaling:

```text
HUMAN PRINCIPAL
       │
       ▼
MASTER ORCHESTRATOR                    ← coordination only; not verifier/executor
       │
       ▼
COMMAND / AUTHORIZATION BOUNDARY       ← signed commands, mission binding, replay protection
       │
       ▼
MISSION CONTROLLER                     ← lifecycle FSM, scope enforcement, timeout/quarantine
       │
       ▼
SPECIALIST ISOLATION                   ← per-agent process/container, least privilege
       │
       ▼
TOOL / DATA POLICY                     ← per-mission grants, no default tools
       │
       ▼
EVIDENCE / MEMORY BOUNDARY             ← typed writes, promotion gates, provenance
       │
       ▼
VERIFICATION                           ← independent principal, not producer
       │
       ▼
GOVERNANCE / TCB                       ← Slice 2B evolution; durable store; production auth
       │
       ▼
MEDIATED EXECUTION                     ← human/L2 gate; no recommendation → execute
       │
       ▼
AHOS (via explicit mediated interface only)
```

**Key invariant:** Each layer has a distinct trust root and failure mode. Collapse of any two adjacent layers is an anti-pattern (see §18).

**Cursor Control-Plane persistence:** Even after runtime exists, human-facing coordination via Cursor should remain an explicit layer — the runtime must not silently absorb human decision authority.

---

## 5. Chain-of-Command Security

### 5.1 Required flow

```text
COMMANDER (Human / authorized orchestrator)
   ↓  signed, scoped, time-bound command
ACTIVATION REQUEST
   ↓  mission controller validates
AUTHORIZATION
   ↓  grants issued (attenuated, task-scoped)
AGENT ACTIVE
   ↓  bounded work within mission
RESULT (non-authoritative by default)
   ↓  collection + normalization
DEACTIVATION
   ↓  grants revoked, session ended
IDLE / DORMANT
```

### 5.2 Threats and controls

| Threat | Current mitigation | Future control `[PROPOSED]` |
| --- | --- | --- |
| Self-activation | Agent 03 mission text requires explicit command; no runtime auto-start | Mission controller rejects activation without valid command token |
| Unauthorized activation | No multi-agent runtime | Commander identity binding; activation requires human or delegated grant |
| Stale command reuse | TCB command replay detection | Command TTL + mission version binding + nonce |
| Replayed commands | `[IMPLEMENTED]` duplicate command ID → REPLAYED | Extend to orchestration envelope layer |
| Forged commander identity | No production auth | Cryptographic commander signature; session ≠ commander |
| Command substitution | Frozen command envelopes in TCB | Immutable mission package hash; specialist receives digest only |
| Command escalation | Policy fixed mapping; global denies | Attenuation on every delegation; no grant widening |
| Cross-agent command injection | No message bus | Recipient binding; orchestrator-mediated routing only |
| Unauthorized delegation | Research path: no DELEGATE_AUTHORITY | Delegation requires explicit grant + depth limit + audit |
| Privilege escalation | RT-07 capability escalation tests | Per-mission capability ceiling; runtime re-validation |
| Circular delegation | Max depth 3 in Slice 2B | Cycle detection in delegation graph |
| Runaway delegation | No runtime orchestrator | Delegation budget per mission; auto-suspend on exceed |

### 5.3 Command record (minimum fields)

```text
COMMAND_ID          unique, non-reusable
MISSION_ID          binds to mission version
TASK_ID             optional parent linkage
COMMANDER_ID        human or authorized orchestrator principal
TARGET_AGENT_ID     explicit recipient + plane (A/B/C/D)
COMMAND_TYPE        closed set
AUTHORITY_CLASS     maximum granted class (READ..DELEGATE)
SCOPE               files, resources, tools allowed
NON_SCOPE           explicit exclusions
ISSUED_AT / EXPIRES_AT
SIGNATURE / PROOF   future: cryptographic
CORRELATION_ID      trace across layers
```

---

## 6. Agent Lifecycle Security

### 6.1 Lifecycle states

```text
REGISTERED → IDLE → ACTIVATION_REQUESTED → AUTHORIZED → ACTIVE
                                                      ↓
                    COMPLETED / FAILED / TIMEOUT / CANCELLED / BLOCKED
                                                      ↓
                    SUSPENDED / QUARANTINED / RETIRED → IDLE (or terminal)
```

### 6.2 Transition matrix

| Transition | Who may request | Who may authorize | Evidence required | Conditions | Audit | Invalidates |
| --- | --- | --- | --- | --- | --- | --- |
| → REGISTERED | Human governance | Human governance | Charter/spec | Unique agent ID | Registration event | Duplicate ID |
| IDLE → ACTIVATION_REQUESTED | Commander | — | Valid command | Agent enabled; not quarantined | Request logged | Missing mission ID |
| ACTIVATION_REQUESTED → AUTHORIZED | — | Mission controller + human gate if HIGH/CRITICAL | Command + scope check | Grants derivable; no global deny hit | Authorization decision | Scope exceeds charter |
| AUTHORIZED → ACTIVE | Mission controller | — | Grants active | Session valid; task bound | Activation event | Expired command |
| ACTIVE → COMPLETED | Agent (result) or controller | — | Result envelope | Scope check pass | Result + deactivation | Out-of-scope work |
| ACTIVE → FAILED | Agent or supervisor | — | Failure class payload | Fail-closed | Failure audit | — |
| ACTIVE → TIMEOUT | Mission controller | — | Clock evidence | Deadline exceeded | Timeout event | — |
| ACTIVE → CANCELLED | Commander | Commander | Cancel command | Active mission | Cancel audit | — |
| * → BLOCKED | Supervisor/human | Human if authority-related | Block reason | Fail-closed | Block event | — |
| * → SUSPENDED | Human/supervisor | Human | Incident or policy | — | Suspend event | — |
| * → QUARANTINED | Security supervisor | Human + security review | Incident class | Suspected compromise | Quarantine record | — |
| QUARANTINED → ACTIVE | — | Human + security review (stronger) | Clearance evidence | Root cause addressed | Reactivation audit | Prior mission reuse |
| COMPLETED → ACTIVE | Commander only | Mission controller | **New** command + **new** TASK_ID/MISSION_ID | Old mission closed | New activation | Reusing old task ID |
| FAILED → ACTIVE | Commander only | Human if repeated failure | Explicit reactivation | Failure reviewed | Reactivation audit | Silent retry |
| TIMEOUT → ACTIVE | Commander only | Human decision | Timeout review | — | Decision record | Auto-resume |
| ACTIVE → ACTIVE | **FORBIDDEN** | — | — | Must deactivate first | — | Silent mission continuation |

### 6.3 Critical lifecycle rules

```text
ACTIVE → ACTIVE     = FORBIDDEN (no silent mission continuation)
COMPLETED → ACTIVE  = requires NEW command + NEW Task/Mission identity
FAILED → ACTIVE     = requires explicit reactivation + review
TIMEOUT → ACTIVE    = requires explicit human/controller decision
QUARANTINED → ACTIVE = requires stronger review than normal reactivation
```

`[VERIFIED]` Slice 1 task FSM implements legal transition enforcement for org tasks (`ahos_org/tasks.py`). Agent lifecycle FSM for 19 specialists: `[PLANNED]`.

---

## 7. Identity / Authority Separation

Four questions must never collapse:

| Question | Must be answered by | Must NOT be answered by |
| --- | --- | --- |
| Who is the agent? | Registry/identity store (Plane A/B/C/D) | Model self-description |
| What may the agent do? | Grant chain + policy + mission scope | Role title or prompt |
| Who authorized this action? | Commander + authorization record | The acting agent |
| Who verified the result? | Independent principal | Producer agent |
| Who approved the change? | Human/L2 governance | Recommendation or consensus |

### 7.1 Current implementation

| Plane | Identity | Authority mechanism |
| --- | --- | --- |
| A (Slice 1) | `agent.*` string ID | Capability tokens on AgentRecord + GovernanceEngine |
| B (Slice 2B) | `principal.*` + Session | CapabilityGrant + derive_authority() |
| C (Research) | `RESEARCH_ANALYST_AGENT` | No grants; host mediates under operator session |
| D (Planned) | `agent.org.NN-*` | **None** — documentary only |

`[VERIFIED]` Federation between planes: `DEFERRED_IMPLEMENTATION` (`AGENT_REGISTRY_MODEL.md`).

### 7.2 Security implications of dual-19

| Risk | Description | Mitigation `[PROPOSED]` |
| --- | --- | --- |
| Identity confusion | Same human expects Plane A ID to match Plane D specialist | Always declare plane in commands/results |
| Authority leakage | Plane D name treated as registered agent | No runtime action without Plane A/B/C registration |
| Orchestrator mapping error | Chief orchestrator (A) conflated with Agent One or agent.org.01 | Explicit naming firewall in command envelopes |
| Duplicate security roles | `agent.security` (A) vs `agent.org.03-security-architect` (D) | Separate charters; distinct mission scopes |

**This report does not resolve dual-19.** `SECURITY RECOMMENDATION ≠ GOVERNANCE DECISION`.

---

## 8. Master Orchestrator Security

### 8.1 Threat model

The Master Orchestrator is a **high-value control-plane component** operating at L5 (chat) today with no runtime enforcement.

| Threat | Description | Severity |
| --- | --- | --- |
| Prompt injection | Repository files, specialist results, or external content embed imperative commands | HIGH |
| Poisoned context | Stale, contradictory, or malicious files in context window | HIGH |
| Forged specialist result | Unverified worker output presented as `[VERIFIED]` | HIGH |
| Malicious specialist | Compromised or mis-scoped specialist exceeds charter | HIGH |
| Malicious file | Repo file mimics governance text to grant authority | MEDIUM |
| Stale context | Old test results or docs treated as current L0 | MEDIUM |
| Authority confusion | Orchestrator acts as verifier, approver, and executor | CRITICAL |
| Accidental escalation | Scope inflation in generated task packages | MEDIUM |
| Excessive delegation | Too many specialists activated without independence | MEDIUM |
| Circular delegation | Specialist A validates Specialist B validates A | MEDIUM |
| Hidden external instructions | Web fetch, issue text, or tool output as covert commands | HIGH |
| Credential exposure | Orchestrator context includes secrets | CRITICAL |

### 8.2 Required boundaries

The Master Orchestrator must **not** become:

```text
SOURCE OF TRUTH + AUTHORITY + VERIFIER + EXECUTOR
```

as one undifferentiated component.

| Function | Orchestrator may | Orchestrator must not |
| --- | --- | --- |
| Understand / formalize | Yes | — |
| Classify risk | Yes | Treat classification as authorization |
| Select specialists | Yes | Grant capabilities |
| Collect results | Yes | Verify own synthesis as independent proof |
| Detect contradictions | Yes | Silently resolve them |
| Synthesize | Yes | Promote synthesis to L2 governance |
| Recommend | Yes (PROPOSE class) | Execute or approve |

`[PROPOSED]` Future orchestrator runtime should be a **stateless coordinator** with:
- Read-only access to projections (not TCB/store)
- No direct tool execution
- Mandatory human gate for authority-impacting outputs
- Structured result normalization without status inflation

---

## 9. Specialist Security

Default: **SPECIALIST = LEAST PRIVILEGE**

### 9.1 Per-specialist security profile (template)

| Dimension | Default (all planned 01–19) | Exception path |
| --- | --- | --- |
| Identity | Plane D ID + issued charter | Must register in runtime plane before activation |
| Command source | Master Orchestrator only | No peer commands without bus + auth |
| Allowed input | Mission package + declared files | No whole-repo implicit access |
| Allowed output | RESULT envelope (non-authoritative) | No TCB commands |
| Tools | **None by default** | Per-mission grant |
| Data access | Read-only declared paths | No credentials, AHOS, production |
| Memory access | Read projections only | No promotion writes |
| Other-agent access | None (orchestrator-mediated) | Explicit MESSAGE_TYPE only |
| Execution access | **Denied** | Human/L2 + mediated interface |
| Authority | READ, ANALYZE, PROPOSE, REQUEST | VERIFY only if independently assigned |

### 9.2 High-risk specialists (enhanced controls)

| Specialist | Extra risks | Enhanced controls `[PROPOSED]` |
| --- | --- | --- |
| 03 Security Architect | Findings treated as enforcement | Cannot modify policy; analysis only |
| 10 Token Security | External data ingestion | Sandboxed fetch; no wallet keys |
| 14 Runtime Engineering | TCB proximity | Separate process; no store import |
| 15 Prompt Engineering | Instruction injection | Cannot issue commands; charter edits require human |
| 16 QA / 19 Red Team | Must be independent | Different principal than producer; blind review option |
| 01 Chief Architect | Agent One confusion | Explicit non-authority charter clause |

### 9.3 RESEARCH_ANALYST_AGENT (implemented reference)

`[VERIFIED]` Class A bounded agent — useful security reference implementation:
- Process isolation (spawn)
- JSON IPC with hard-deny operations
- Forbidden authority keys in payloads
- Host-derived commit plan (worker requests not executed directly)
- Output forced non-authoritative

---

## 10. Prompt Injection / Context Poisoning

### 10.1 Threat sources

| Source | Data vs instruction risk | Current handling |
| --- | --- | --- |
| Repository files | HIGH — AGENTS.md, charters, mission text | Manual agent discipline; no runtime parser |
| External documents / web | HIGH | Not ingested by org runtime |
| GitHub issues | MEDIUM | Not connected |
| Model-generated text | HIGH | Unbounded in Cursor layer |
| Specialist results | HIGH — recommendation → command | Protocol: RESULT ≠ AUTHORITY |
| User-supplied content | HIGH | L5 until recorded L2 |
| Previous agent outputs | MEDIUM — context chaining | No automatic promotion |
| Memory | CRITICAL if promoted | Memory ≠ truth in TCB |
| Tool output | HIGH | No default tools in org runtime |

### 10.2 Required distinction

```text
DATA        = content to analyze
INSTRUCTION = binding only from authorized commander envelope
AUTHORITY   = grant recorded in policy/TCB/human decision
```

Rules:
- Imperative language in a file does not create instruction.
- Specialist recommendation does not create command.
- Documentation does not create enforcement.
- Test pass does not create production proof.

### 10.3 Controls `[PROPOSED]`

1. **Instruction firewall** — parse context into `DATA` and `INSTRUCTION` channels; only commander envelope writes instruction channel.
2. **Provenance tags** — every context block labeled with source level (L0–L6).
3. **Mission-bound context** — specialists receive task slice only, not full orchestrator history.
4. **Sanitization** — strip or quarantine patterns resembling command envelopes from untrusted DATA.
5. **Human confirmation** — any detected authority claim in DATA triggers escalation, not compliance.

---

## 11. Memory Security

### 11.1 Memory categories (future)

| Type | Read default | Write default | Promotion |
| --- | --- | --- | --- |
| Episodic | Task-scoped | Agent-scoped | Never to truth |
| Semantic | Projections | TCB only | Via PROMOTE_KNOWLEDGE only |
| Procedural | Read-only | Human/TCB | Not automatic |
| Failure | Read-only | TCB | Lessons ≠ enforcement |
| Hypothesis | Read | Agent (labeled) | Never without verification |
| Causal | Read | TCB | Evidence-backed only |
| Performance | Read | Metrics pipeline | Not authority |
| Self-model | Agent read | **Denied** | Prevents self-authorization |

### 11.2 Current implementation

`[VERIFIED]` Slice 2B `MemoryRecord` exists; TCB blocks memory → promoted truth. D-11: generic transition map still lists PROMOTED for memory (split-brain documented, execution denied).

### 11.3 Threats

| Threat | Control |
| --- | --- |
| MEMORY → UNVERIFIED TRUTH | Exclusive promotion path (D-01); independent verification + approval (D-04) |
| Memory poisoning | Evidence ID resolution; unknown evidence denied (RT-14) |
| Cross-task contamination | Task-scoped memory namespaces |
| Stale memory | Version + expiry; STALE label |
| Revocation gap | Grant/session revocation; `[DOCUMENTED_DEFERRED]` principal suspend (D-15) |

---

## 12. Evidence Security

### 12.1 Chain

```text
SOURCE → EVIDENCE → CLAIM → HYPOTHESIS → PREDICTION → OBSERVATION
    → VERIFICATION → KNOWLEDGE CANDIDATE → (PROMOTE) → promoted knowledge
```

Each arrow requires provenance binding. Skipping steps is an anti-pattern.

### 12.2 Threats

| Threat | Current mitigation | Gap |
| --- | --- | --- |
| Evidence forgery | Registered-object resolution in TCB | Same-process bypass |
| Provenance loss | Audit events | Not durable |
| Evidence substitution | ID binding in promotion | D-07: content_hash not verified against bytes |
| Stale evidence | Staleness checks in promotion | Manual in reports |
| Replay | Command replay detection | Not at evidence artifact level |
| Cherry-picking | Contradiction visibility (RT-15) | No automated detection in reports |
| Cross-task contamination | Task scope on grants | Report-level only |
| Identity mismatch | Session/principal binding | Stub auth |
| Context mismatch | — | `[PLANNED]` correlation IDs |

---

## 13. Communication Security

### 13.1 Pattern comparison

| Pattern | AuthN | AuthZ | Integrity | Confidentiality | Provenance | Replay | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Direct (agent↔agent) | — | — | — | — | — | — | **Not implemented** — forbidden until bus exists |
| Orchestrator-mediated | Partial (Cursor) | Manual | None | Chat provider | Manual | None | **Current de facto** |
| Message bus | `[PLANNED]` | `[PLANNED]` | `[PLANNED]` | `[PLANNED]` | `[PLANNED]` | `[PLANNED]` | Not implemented |
| Event stream | `[PLANNED]` | `[PLANNED]` | `[PLANNED]` | `[PLANNED]` | `[PLANNED]` | `[PLANNED]` | Not implemented |
| Shared memory | `[PLANNED]` | TCB-gated | TCB | — | TCB audit | — | Slice 2B store only |

### 13.2 Required message properties (future)

Authentication, authorization, integrity, confidentiality, provenance, correlation IDs, replay protection, idempotency, ordering, duplicate detection, message expiration, sender binding, recipient binding.

`[VERIFIED]` Communication protocol envelope schema exists (`docs/protocols/AGENT_COMMUNICATION_PROTOCOL.md`) — `DESIGN_ONLY`.

**Rule:** Slice 2B `CommandType` ≠ communication `MESSAGE_TYPE`. Never route envelopes into `TCB.submit` without translation and re-authorization.

---

## 14. Tool Security

Principle: **NO TOOL ACCESS BY DEFAULT**

| Tool class | Default | Research path | Future gate |
| --- | --- | --- | --- |
| Filesystem | Denied | Workspace sandbox reads only | Path allow-list per mission |
| Shell / PowerShell | Denied | Hard-deny IPC | OS sandbox if ever granted |
| Python exec | Denied | Worker isolated; API deny | Controlled interpreter |
| Git | Denied | Not exposed | Read-only grant optional |
| GitHub | Denied | Not connected | Token-scoped API |
| Web | Denied | Not exposed | Fetch sandbox + allow-list |
| Database | Denied | Not connected | Mediated read-only views |
| Network | Denied | `OS_NETWORK_ISOLATION = NOT_PROVIDED` | Network policy + egress filter |
| Telegram / n8n | Globally denied | Hard-deny | Remains denied |
| External APIs | Denied | Not connected | Per-mission scoped credentials |
| Credentials | Globally denied | Forbidden authority keys | Vault with injection, never in context |

`[VERIFIED]` Slice 1 `GLOBAL_DENY_CAPABILITIES` and research `HARD_DENY_OPERATIONS` implement symbolic/API denial. OS-level enforcement: `[NOT IMPLEMENTED]`.

---

## 15. AHOS Security Boundary

```text
AGENT ORGANIZATION
        │
        ▼
MEDIATED INTERFACE (future — explicit L2 authorization required)
        │
        ▼
AHOS (separate product — G:\robat\ahos)
```

**Forbidden path:**

```text
SPECIALIST → DIRECT AHOS INTERNALS
```

### 15.1 Protections required at boundary

| Asset | Requirement |
| --- | --- |
| AHOS source code | No write from org agents unless explicit bounded L2 mission |
| Databases | No direct access; mediated read-only API if ever authorized |
| Credentials | Never in agent context; vault injection at execution layer only |
| Trading | Globally denied (`trading.live`, `live_trade`) |
| Providers | Globally denied (`provider.connect`) |
| Telegram / n8n | Globally denied |
| Production runtime | Globally denied (`production.operate`) |
| Lane A / B / soak | Globally denied |

`[VERIFIED]` Current state: no AHOS connection exists. Denies are symbolic in Slice 1 and hard-deny in research IPC.

### 15.2 Mediated interface design `[PROPOSED]`

- Separate service account with minimal AHOS permissions
- Read-only projection API for research (no mutation)
- All writes require human approval + audit + out-of-band verification
- Rate limiting and anomaly detection
- No agent holds long-lived credentials

---

## 16. Execution Security

### 16.1 Verb separation

| Verb | Meaning | Who may perform |
| --- | --- | --- |
| ANALYZE | Read and interpret | Specialist (default) |
| RECOMMEND | Propose action (PROPOSE class) | Specialist, Orchestrator |
| REQUEST | Ask for verification/approval | Specialist, Orchestrator |
| APPROVE | Grant governance consent | Human / L2 only |
| VERIFY | Independent reproduction | Independent agent/human |
| EXECUTE | Mutate external state | Mediated execution layer + human gate |

**Prohibited:**
```text
RECOMMENDATION → AUTOMATIC EXECUTION
AGENT CONSENSUS → EXECUTION
ORCHESTRATOR SYNTHESIS → EXECUTION
TEST PASS → PRODUCTION DEPLOY
```

### 16.2 Current enforcement

`[IMPLEMENTED]` TCB global denies on EXECUTION, EXTERNAL_EXECUTION, protected resources. Research worker cannot execute commits directly — host-derived plan only.

---

## 17. Incident Model

| Incident class | Detect | Contain | Quarantine | Investigate | Recover | Verify | Resume |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PROMPT_INJECTION | Instruction firewall; anomaly in DATA | Stop agent; freeze context | Affected agent | Source trace; context audit | Clean context; re-issue command | Independent review | New mission ID |
| IDENTITY_FORGERY | Session/principal mismatch deny | Deny command | Suspected agent | Audit chain | Revoke grants | Identity re-bind | Explicit reactivation |
| AUTHORITY_ESCALATION | Policy deny; RT tests | Fail-closed deny | Agent | Grant chain audit | Patch policy | Red-team re-test | Human approval |
| MEMORY_POISONING | Unknown evidence deny | Block promotion | Memory namespace | Provenance trace | Revoke memory writes | Promotion re-test | Scoped restore |
| EVIDENCE_FORGERY | Object resolution fail | Deny promotion | Candidate | Audit + source check | Remove artifact | Independent verify | New evidence path |
| MALICIOUS_AGENT | Scope breach; IPC deny | Terminate worker | Agent + deps | Forensics | Rebuild agent | Red-team | Quarantine clearance |
| TOOL_ABUSE | Deny list hit | Kill tool session | Agent | Tool audit log | Revoke tool grant | Pen-test | New grant |
| CREDENTIAL_EXPOSURE | Secret scanner | Revoke credential | All agents with access | Exposure scope | Rotate secrets | Access audit | Least-privilege re-grant |
| UNAUTHORIZED_EXECUTION | TCB deny | Rollback transaction | Executor | Audit chain | State restore | Verification | Human gate |
| MESSAGE_REPLAY | Duplicate ID | REPLAYED result | Channel | Correlation audit | Idempotency key rotation | Re-test | — |
| RUNAWAY_AGENT | Timeout; resource limit | Supervisor kill | Agent | Mission audit | Fix scope | Load test | New mission |
| RUNAWAY_DELEGATION | Depth/budget exceed | Suspend delegation | Orchestrator chain | Delegation graph | Revoke grants | Policy update | Human approval |
| PARTIAL_COMMIT | Transaction rollback | TCB working-copy abort | Affected task | Audit checkpoint | Re-submit | Atomic re-test | — |
| CORRUPTED_STATE | Hash chain fail | Read-only mode | Store | Forensic audit | Restore backup | Integrity check | Controlled reopen |

`[PLANNED]` No incident response service exists. Slice 2B audit and supervisor fail-closed provide partial detect/contain for research path only.

---

## 18. Security Anti-Patterns

Minimum 20 identified:

| # | Anti-pattern | Why dangerous | Current status |
| --- | --- | --- | --- |
| 1 | SELF-ACTIVATION | Agent starts without commander | Manual only; no runtime |
| 2 | SELF-AUTHORIZATION | Agent grants own capabilities | Denied by TCB bootstrap model |
| 3 | SELF-VERIFICATION | Producer verifies own output | RT-06; independent required for promotion |
| 4 | SELF-PROMOTION | Agent promotes own claims to truth | D-01 exclusive path |
| 5 | SELF-APPROVAL | Agent approves own changes | Forged approval denied (RT-02) |
| 6 | COMMANDER SPOOFING | Fake commander identity | Stub session only; no crypto |
| 7 | STALE COMMAND REUSE | Old mission re-run silently | TCB replay; no orchestration TTL |
| 8 | MISSION REPLAY | Completed mission restarted | Not enforced at orchestration layer |
| 9 | AGENT CONSENSUS = AUTHORITY | Vote count → decision | Protocol forbids; manual risk |
| 10 | MEMORY = TRUTH | Unverified memory → knowledge | TCB blocks; D-11 map inconsistency |
| 11 | DOCUMENTATION = ENFORCEMENT | Markdown grants capability | Constitution explicit |
| 12 | POLICY = SANDBOX | Python policy ≡ OS isolation | Explicitly denied |
| 13 | DIRECT CREDENTIAL ACCESS | Agent reads secrets | Global deny |
| 14 | DIRECT EXECUTION | Specialist mutates production | Global deny |
| 15 | UNBOUNDED DELEGATION | Unlimited sub-delegation | Depth limit 3 |
| 16 | CIRCULAR DELEGATION | A→B→A verification | Not fully detected |
| 17 | UNBOUNDED CONTEXT | Full repo/history to specialist | Cursor practice; not gated |
| 18 | TRUSTED MODEL OUTPUT | LLM text as evidence | No LLM in research path; Cursor risk |
| 19 | TRUSTED TOOL OUTPUT | Tool result as authority | No default tools |
| 20 | TRUSTED EXTERNAL CONTENT | Web/issue text as command | Not ingested by runtime |
| 21 | ACTIVE → ACTIVE | Silent mission continuation | Agent 03 rule; not runtime enforced |
| 22 | ROLE TITLE = AUTHORITY | "Security Architect" implies EXECUTE | Constitution §6 |
| 23 | ORCHESTRATOR = VERIFIER | MO validates own synthesis | Design rule; manual |
| 24 | RECOMMENDATION → EXECUTE | Auto-implement on suggest | Not in org runtime |
| 25 | PLANE A = PLANE D | ID interchange | Unresolved dual-19 |
| 26 | MERGE = GOVERNANCE | Git merge implies approval | Constitution inequality |
| 27 | TEST PASS = PROD PROOF | Unit tests ≡ production safe | Explicitly forbidden |
| 28 | HUMAN MESSAGE = L2 | Chat creates governance | L5 until recorded |

---

## 19. Security Controls Roadmap

`FUTURE_SECURITY_IMPLEMENTATION_REQUIREMENT` — not executed in this mission.

| Phase | Control | Depends on | Priority |
| --- | --- | --- | --- |
| **S1** | Mission controller + lifecycle FSM | Charter framework | HIGH |
| **S1** | Command envelope with TTL + mission version | Orchestrator runtime | HIGH |
| **S1** | Orchestrator instruction firewall | Cursor/runtime integration | HIGH |
| **S2** | Production identity (replace session stub) | Human L2 decision | CRITICAL for production |
| **S2** | Durable encrypted TCB store | Slice 2C | HIGH |
| **S2** | Inter-agent message bus with auth | Registry federation | MEDIUM |
| **S3** | OS sandbox / container per specialist | Runtime engineering | HIGH |
| **S3** | Network egress policy | Infrastructure | HIGH |
| **S3** | Credential vault with injection | AHOS boundary design | CRITICAL before AHOS |
| **S4** | Mediated AHOS interface | AHOS governance | MEDIUM |
| **S4** | Incident response service | Audit durability | MEDIUM |
| **S4** | Automated secret scanning | CI/CD | MEDIUM |
| **Ongoing** | Red-team suite expansion | Each new agent/path | HIGH |
| **Ongoing** | Close D-02..D-20 deferred defects | Slice 2C | Per defect priority |

---

## 20. Current Security Gaps

| ID | Gap | Severity | Evidence |
| --- | --- | --- | --- |
| G-01 | No production authentication | CRITICAL | `LocalOperatorSessionStub` |
| G-02 | In-process TCB bypass possible | HIGH | Slice 2B report §4 |
| G-03 | No OS sandbox | HIGH | `FULL_OS_SANDBOX = NO` |
| G-04 | API denial ≠ network isolation | HIGH | `PROCESS_ISOLATED_RESEARCH_WORKER.md` |
| G-05 | No multi-agent supervisor service | HIGH | Supervision protocol |
| G-06 | No message bus auth | HIGH | Communication protocol |
| G-07 | Constitution not enforced in code | MEDIUM | `ENFORCEMENT = NOT_IMPLEMENTED` |
| G-08 | Dual-19 identity confusion | MEDIUM | Registry model |
| G-09 | No orchestration replay/TTL | MEDIUM | No mission controller |
| G-10 | D-02 independent verification weak | HIGH | Remediation doc |
| G-11 | D-03 challenge object not required | MEDIUM | Remediation doc |
| G-12 | D-15 no principal suspend | MEDIUM | Remediation doc |
| G-13 | D-07 content hash not verified | MEDIUM | Remediation doc |
| G-14 | Volatile state (no durable store) | HIGH | Slice 2B in-memory |
| G-15 | Same Windows user host/worker | MEDIUM | Research worker doc |
| G-16 | Cursor MO unbounded context | HIGH | Control-plane reality |
| G-17 | No incident response automation | MEDIUM | This analysis |
| G-18 | Plane A/B/C/D federation absent | HIGH | Registry model |
| G-19 | agent_org.tcb importable in worker | LOW-MEDIUM | Worker probe RT-WORKER-07 |
| G-20 | REQUIRES_REVIEW not hard block at caller | MEDIUM | Slice 1 design |

---

## 21. Open Security Questions

Requires human governance decision — not resolved in this mission:

1. **Dual-19 resolution strategy** — dual-run, merge, map, or retire? (Security impact: identity confusion until resolved.)
2. **Agent One authority ceiling** — what explicit denies beyond current `FUTURE_NON_AUTHORITY_ROOT`?
3. **Production identity model** — WebAuthn, HSM, mTLS, or human-in-loop only?
4. **Orchestrator runtime** — remain Cursor-only vs dedicated service?
5. **AHOS mediated interface scope** — read-only research vs bounded write missions?
6. **LLM specialist admission** — if Class B agents added, what isolation tier?
7. **Memory durability and promotion** — when does episodic memory become semantic?
8. **Cross-plane grant federation** — single grant store or bridge with attenuation?
9. **Incident quarantine authority** — who may QUARANTINE → ACTIVE?
10. **Audit external anchoring** — blockchain, WORM storage, or SIEM?
11. **Constitution L2 adoption** — when does markdown become enforceable governance?
12. **Independent verification definition (D-02)** — cryptographic identity or procedural separation?
13. **Red-team frequency and scope** — per mission, per release, or continuous?
14. **Credential vault placement** — inside org repo vs external secret manager?
15. **Maximum delegation depth in production** — keep 3 or reduce to 2?

---

## 22. Recommended Next Mission

`RECOMMENDED_NEXT_MISSION` `[PLANNED]` — **STATE ONLY; DO NOT EXECUTE**

```text
MISSION_ID (proposed)  = TASK-20260914-004
TITLE                  = SPECIALIST_CHARTER_FRAMEWORK_AND_DOMAIN_BOUNDARY_OPTIONS
OWNER                  = MASTER_ORCHESTRATOR
PURPOSE                = Define charter-enforced security profiles for Plane D specialists
                       before any runtime operationalization; include tool/data/MO boundaries
PREREQUISITE           = Human review of this security architecture document
AUTHORITY_IMPACT       = DOCUMENTATION ONLY (charter templates); no runtime grants
```

Alternate follow-on (if human prioritizes implementation path):

```text
MISSION_ID (proposed)  = TASK-20260914-005
TITLE                  = MISSION_CONTROLLER_AND_LIFECYCLE_FSM_DESIGN
PURPOSE                = Specify enforceable agent lifecycle transitions (§6) as design + tests
                       without connecting to production or AHOS
```

---

## Evidence Index

| ID | Claim | Status | Source |
| --- | --- | --- | --- |
| EVD-S01 | Slice 1 global denies AHOS/credentials/trading | `[VERIFIED]` | `ahos_org/policy.py` |
| EVD-S02 | TCB single mutation ingress | `[VERIFIED]` | `agent_org/tcb.py` |
| EVD-S03 | D-01 promotion exclusive path | `[VERIFIED]` | Remediation doc, tests |
| EVD-S04 | Research spawn isolation | `[VERIFIED]` | `PROCESS_ISOLATED_RESEARCH_WORKER.md` |
| EVD-S05 | No message bus | `[VERIFIED]` | Communication protocol |
| EVD-S06 | Agent One not implemented | `[VERIFIED]` | `agent_org/__init__.py` |
| EVD-S07 | Dual-19 unresolved | `[VERIFIED]` | Registry model, planned map |
| EVD-S08 | Constitution DESIGN_ONLY | `[VERIFIED]` | Constitution header |
| EVD-S09 | Test counts ~49 + ~203+ | `[PARTIALLY_VERIFIED]` | Static inspection |
| EVD-S10 | Current test PASS | `[UNVERIFIED]` | Not executed this mission |

---

```text
MISSION_STATUS =
SECURITY_ARCHITECTURE_ANALYSIS_COMPLETE_WITH_GAPS
AGENT_ID =
AGENT-03
DIRECT_COMMANDER =
MASTER_ORCHESTRATOR
LIFECYCLE_STATUS =
IDLE / DORMANT / WAITING_FOR_NEW_COMMAND
DUAL_19 =
UNRESOLVED
AGENT_ONE =
NOT_IMPLEMENTED / FUTURE_NON_AUTHORITY_ROOT
AHOS_IMPACT =
NONE
CODE_CHANGES =
NONE
RUNTIME_CHANGES =
NONE
GOVERNANCE_CHANGES =
NONE
COMMIT =
NONE
PUSH =
NONE
HUMAN_DECISIONS_REQUIRED =
1. Dual-19 resolution strategy (identity federation)
2. Agent One authority ceiling when/if built
3. Production identity model selection
4. Orchestrator runtime placement (Cursor vs service)
5. AHOS mediated interface scope authorization
6. LLM specialist admission policy and isolation tier
7. Constitution L2 adoption timing
8. Independent verification definition (close D-02)
9. Audit durability and external anchoring approach
10. Delegation depth limit for production
RECOMMENDED_NEXT_MISSION =
STATE_ONLY — DO NOT EXECUTE
```
