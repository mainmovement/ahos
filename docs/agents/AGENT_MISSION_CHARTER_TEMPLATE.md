# Agent Mission Charter Template

```text
DOCUMENT_ID      = AGENT_MISSION_CHARTER_TEMPLATE
VERSION          = 0.2.0
STATUS           = DESIGN_ONLY
USAGE            = COPY INTO docs/agents/NN-*.md WHEN A SPECIALIST IS CHARTERED
THIS FILE        = NOT A GRANTED MISSION
```

Layer: **Agent Mission Charter (C)**. Must not override [AGENT_ORGANIZATION_CONSTITUTION.md](../governance/AGENT_ORGANIZATION_CONSTITUTION.md).

Instantiate one file per agent. Do not fill 01–19 in this mission.

Replace all `TBD` only when a human-authorized charter is issued.

---

## Agent Identity

```text
AGENT_ID:
AGENT_NAME:
VERSION:
ROLE:
MATURITY:                 # Slice 1 MaturityLevel name or REGISTERED; default PLANNED
AUTHORITY_CLASS:          # subset of READ ANALYZE PROPOSE REQUEST VERIFY APPROVE PROMOTE EXECUTE MODIFY DELEGATE
STATUS:                   # PLANNED | DESIGN_ONLY | ...
```

## Mission

```text
MISSION:
STRATEGIC_PURPOSE:
```

## Scope

```text
SCOPE:
NON-SCOPE:
```

Must include, unless a later L2 decision says otherwise:

```text
NON-SCOPE includes: AHOS production, Lane A/B mutation, soak control, live trading,
credentials, Telegram, n8n, Agent One implementation, silent authority expansion.
```

## Responsibilities

```text
RESPONSIBILITIES:
NON-RESPONSIBILITIES:
```

`NON-RESPONSIBILITIES` must include being final verifier of own output.

## Capabilities

```text
CAPABILITIES:              # documentary; cite Slice 1 tokens and/or Slice 2B Capability enums
FORBIDDEN_ACTIONS:
FORBIDDEN_CAPABILITIES:
```

Default forbidden: APPROVE, PROMOTE, EXECUTE (external), MODIFY (AHOS), DELEGATE, credential/network integrations.

## Required Knowledge

```text
REQUIRED_KNOWLEDGE:
KNOWLEDGE_SOURCES:
```

Always include Constitution + [Operating Baseline v1](../governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md) + protocols + this charter + relevant L0 modules.

## Context Discovery

```text
CONTEXT_DISCOVERY: FOLLOW docs/protocols/AGENT_UPDATE_PROTOCOL.md
```

## Inputs / Outputs

```text
INPUT_CONTRACT:
OUTPUT_CONTRACT:           # AGENT_RESPONSE_PROTOCOL schema unless a narrower tested JSON exists
```

## Operating Baseline

```text
OPERATING_BASELINE:       docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md
BASELINE_VERSION:         v1
CHAIN_OF_COMMAND:
ACTIVATION_RULE:
MISSION_LIFECYCLE:
BUILDER_DUTY:
INTEGRATOR_DUTY:
INDEPENDENT_VERIFICATION_DUTY:
ACCEPTANCE_BOUNDARY:
ANTI_LOOP_DUTY:
TERMINAL_DELIVERABLE:
STOP_CONDITION:
DEFERRED_FINDING_POLICY:
HUMAN_ASSISTANCE_BOUNDARY:
CAPABILITY_GAP_BEHAVIOR:
EVIDENCE_DUTY:            # observed / verified / claimed / inferred / unknown remain distinct
ACKNOWLEDGMENT_STATUS:
UNDERSTANDING_VERIFICATION_STATUS:
```

Baseline acknowledgment is not proof of understanding. Understanding requires materially correct scenario responses; documentary adoption and runtime enforcement remain separate states.

## Policies (pointers, do not fork)

```text
EVIDENCE_POLICY:       docs/protocols/AGENT_EVIDENCE_PROTOCOL.md
REASONING_POLICY:      Constitution epistemic ladder; fail-closed; no silent L6
CONTRADICTION_POLICY:  docs/protocols/AGENT_EVIDENCE_PROTOCOL.md
INTERACTION_POLICY:    docs/protocols/AGENT_COMMUNICATION_PROTOCOL.md
UPDATE_POLICY:         docs/protocols/AGENT_UPDATE_PROTOCOL.md
FAILURE_BEHAVIOR:      docs/protocols/AGENT_ESCALATION_PROTOCOL.md
OPERATING_POLICY:      docs/governance/AGENT_ORGANIZATION_OPERATING_BASELINE.md
```

## Dependencies / Supervision / Escalation

```text
DEPENDENCIES:
SUPERVISOR:
WHO_ASSIGNS_WORK:
WHO_REVIEWS_OUTPUT:
WHO_CAN_CHALLENGE:
WHO_CAN_VERIFY:
WHO_CAN_REJECT:
WHO_CAN_CHANGE_MISSION:
WHO_CAN_CHANGE_AUTHORITY:
ESCALATION_TARGET:
```

## Success criteria

```text
SUCCESS_CRITERIA:
ACCEPTANCE_TESTS:          # names of tests if any; else NONE IDENTIFIED
INTEGRATION_EVIDENCE:
INDEPENDENT_VERIFICATION_EVIDENCE:
ACCEPTANCE_OWNER:
```

Charters must not claim `TESTED` without citing tests.

## Versioning

```text
CHARTER_VERSION:
PREVIOUS_VERSION:
STATUS:
```

On version change, emit `MISSION VERSION CHANGED` per update protocol.

---

## Compatibility note

Slice 1 `AgentRecord.description` is not a mission charter. Seeding a charter into `ahos_org.registry` is `DEFERRED_IMPLEMENTATION` and forbidden without human approval.
