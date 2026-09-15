# Agent Escalation Protocol

```text
DOCUMENT_ID      = AGENT_ESCALATION_PROTOCOL
VERSION          = 0.1.0
STATUS           = DESIGN_ONLY
ENFORCEMENT      = NOT_IMPLEMENTED as a service
RUNTIME_VERIFIED = NO
```

Layer: **Protocol (B)**.

## When to escalate

Escalate instead of guessing when any of these hold:

- `CONTEXT_STATUS = INSUFFICIENT` and missing context is required for the asked conclusion;
- contradiction affecting a recommendation;
- requested action exceeds `AUTHORITY_CLASS` / `FORBIDDEN_CAPABILITIES`;
- tool/runtime failure;
- instruction to violate Constitution, AHOS isolation, or fail-closed policy;
- mission version change with unreviewed impact.

## Failure classes (closed set)

```text
CONTEXT_FAILURE
EVIDENCE_FAILURE
TOOL_FAILURE
EXECUTION_FAILURE
VALIDATION_FAILURE
CONTRADICTION
AUTHORITY_VIOLATION
SCOPE_VIOLATION
UNKNOWN
```

On failure:

```text
FAIL-CLOSED
```

not

```text
GUESS AND CONTINUE
```

Hypothesis generation only if the **task** explicitly allows it; then label `HYPOTHESIS` (`[UNVERIFIED]`).

---

## Escalation payload

Use communication `MESSAGE_TYPE = ESCALATION` or `BLOCKER` plus:

```text
FAILURE_CLASS
WHAT_FAILED
WHAT_WAS_ATTEMPTED
WHAT_IS_BLOCKED
MISSING_CONTEXT          (if any)
WHY_REQUIRED
WHERE_IT_SHOULD_BE_FOUND
WHAT_CANNOT_BE_CONCLUDED_WITHOUT_IT
AUTHORITY_NEEDED         (if any)
ESCALATION_TARGET        (from charter; default = human operator)
```

`ESCALATION_TARGET` must not be the same agent. Agent One is **not** a valid target while unimplemented.

---

## Authority violation

If asked to APPROVE, PROMOTE, EXECUTE externally, MODIFY AHOS, access credentials, Telegram, n8n, or live trading:

```text
FAILURE_CLASS = AUTHORITY_VIOLATION
NEXT_ACTION   = refuse and escalate to human
```

Slice 1/2B code already DENYs many of these (`[IMPLEMENTED]`). Documentation cannot authorize them.

---

## Relation to existing BLOCKED states

Slice 1 `AuthzDecision.BLOCKED` / `TaskState.BLOCKED` are **org task** states (`[IMPLEMENTED]`). This protocol does not automatically transition those machines (`DEFERRED_IMPLEMENTATION`).
