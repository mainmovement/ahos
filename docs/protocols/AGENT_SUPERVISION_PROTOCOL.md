# Agent Supervision Protocol

```text
DOCUMENT_ID      = AGENT_SUPERVISION_PROTOCOL
VERSION          = 0.1.0
STATUS           = DESIGN_ONLY
ENFORCEMENT      = PARTIAL (Slice 1 Authz + Slice 2B TCB + IsolatedResearchRuntime policy) — not a 19-agent supervisor service
RUNTIME_VERIFIED = NO
```

Layer: **Protocol (B)**.

## Principle

```text
An agent is not final authority about itself.
Self-assessment ≠ Independent verification
```

## Required assignment (every charter)

Each agent charter must name, as identities not as “the model”:

```text
WHO ASSIGNS WORK?
WHO REVIEWS OUTPUT?
WHO CAN CHALLENGE IT?
WHO CAN VERIFY IT?
WHO CAN REJECT ITS RESULT?
WHO CAN CHANGE ITS MISSION?
WHO CAN CHANGE ITS AUTHORITY?
```

Until charters exist, **defaults** (`DESIGN_ONLY`, not seeded in registry):

| Function | Default |
| --- | --- |
| Assign work | Human operator |
| Review output | Human operator; optionally planned agent 16 (QA) when chartered |
| Challenge | Human; planned agent 19 (Red Team); Slice 1 `agent.red-team` is a **different** logical role — do not treat as the same instance |
| Verify | Independent agent or human; never solely the producing agent |
| Reject result | Human / governance engine deny |
| Change mission | Human governance only |
| Change authority | Human governance + code change in the relevant plane; never the agent |

Agent One (unimplemented) may **request** work and **collect** results. It may not verify itself, approve, or change another agent’s authority.

---

## Repository reality (do not over-claim)

| Mechanism | Status | Supervises |
| --- | --- | --- |
| Slice 1 `GovernanceEngine.authorize` | `[IMPLEMENTED]` `[TESTED]` (Slice 1 tests) | Symbolic capability/resource/task gates |
| Slice 2B `TrustedCommandBoundary.submit` | `[IMPLEMENTED]` `[TESTED]` (tests2b) | Command policy, session, grants |
| `IsolatedResearchRuntime` locked `FIRST_AGENT_OPERATIONS` | `[IMPLEMENTED]` `[TESTED]` (analyst tests) | Worker IPC allow-list |
| 19-agent org supervisor | **absent** | `DEFERRED_IMPLEMENTATION` |

Python in-process code is **not** a security boundary (`POLICY ≠ SECURITY BOUNDARY`).

---

## Challenge and rejection

- A `CHALLENGE` (communication protocol) does not auto-revert TCB state.
- Rejection of a **documentary** RESULT is a human/governance act.
- Rejection of a **TCB command** is `DENIED` / `FAILED` from the boundary (`[IMPLEMENTED]`).

Agents must not treat a passed unit test of their own package as independent verification of a new claim.
