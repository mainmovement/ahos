# Agent Communication Protocol

```text
DOCUMENT_ID      = AGENT_COMMUNICATION_PROTOCOL
VERSION          = 0.1.0
STATUS           = DESIGN_ONLY
ENFORCEMENT      = NOT_IMPLEMENTED
TRANSPORT        = NONE
RUNTIME_VERIFIED = NO
```

Layer: **Protocol (B)**. Cannot grant authority. Cannot override the Constitution.

## Repository reality

`[VERIFIED]` There is **no** inter-agent message bus, queue, or envelope runtime in this repository.

Existing related artifacts (do not treat as this protocol):

- Slice 1 `TaskRecord` / `TaskStateMachine` — human/org task states, not agent-to-agent messages.
- Slice 2B `CommandEnvelope` — TCB ingress, not specialist chat.
- Research worker JSON (`WORKER_REQUEST`, `PROBE_RESULT`, …) — **host↔worker IPC**, not 19-agent communication.

`DEFERRED_IMPLEMENTATION`: persist envelopes, route them, authorize `MESSAGE_TYPE`s.

Until then, any agent-to-agent “message” in a report is a **documentary object** (L3/L5), not a delivered command.

---

## Envelope (required fields)

```text
MESSAGE_ID
TASK_ID
SENDER_AGENT
RECIPIENT_AGENT
MESSAGE_TYPE
PURPOSE
CONTEXT_REFERENCE
EVIDENCE_REFERENCES
REQUEST
CONSTRAINTS
EXPECTED_OUTPUT
PRIORITY
CREATED_AT
STATUS
```

Rules:

- `SENDER_AGENT` / `RECIPIENT_AGENT` must be known identity strings (Slice 1 id, research id, planned `agent.org.*`, or `human.*`). Unknown recipient → `BLOCKED`, do not invent a listener.
- `CONSTRAINTS` must include Constitution non-overrides and any `FORBIDDEN_CAPABILITIES`.
- `EVIDENCE_REFERENCES` are IDs or paths, not prose “as above”.
- Empty optional facts: `NONE IDENTIFIED`.

---

## MESSAGE_TYPE (initial closed set)

```text
TASK_REQUEST
RESEARCH_REQUEST
VERIFICATION_REQUEST
CHALLENGE
EVIDENCE_REQUEST
CONTRADICTION_REPORT
DEPENDENCY_REQUEST
REVIEW_REQUEST
RESULT
ESCALATION
BLOCKER
```

Do not add types without a protocol version change.

Mapping notes (`DESIGN_ONLY`):

- `ESCALATION` / `BLOCKER` also follow [AGENT_ESCALATION_PROTOCOL.md](AGENT_ESCALATION_PROTOCOL.md).
- `CONTRADICTION_REPORT` must include the contradiction block from [AGENT_EVIDENCE_PROTOCOL.md](AGENT_EVIDENCE_PROTOCOL.md).
- `RESULT` bodies must follow [AGENT_RESPONSE_PROTOCOL.md](AGENT_RESPONSE_PROTOCOL.md).

Incompatibility: Slice 2B `CommandType` is a **different closed set**. Never send a communication envelope into `TCB.submit` as if it were a command.

---

## Uncontrolled communication

Forbidden:

- side-channel advice that changes another agent’s authority;
- sharing credentials, tokens, or live endpoints;
- treating a `TASK_REQUEST` as `APPROVE` / `PROMOTE` / `EXECUTE`.

Allowed documentary flow:

```text
Human or supervisor assigns TASK
  → specialist RESULT
  → optional VERIFICATION_REQUEST to a different agent
  → optional CHALLENGE
  → human / governance decision (L2)
```

---

## STATUS values for messages

Use Constitution taxonomy plus message lifecycle:

```text
[PLANNED] [UNVERIFIED] [BLOCKED] [REJECTED] [STALE]
```

Delivery `STATUS` (documentary): `DRAFTED` | `ISSUED` | `ACKNOWLEDGED` | `COMPLETED` | `FAILED` — all `DESIGN_ONLY`.
