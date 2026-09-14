# Agent Response Protocol

```text
DOCUMENT_ID      = AGENT_RESPONSE_PROTOCOL
VERSION          = 0.1.0
STATUS           = DESIGN_ONLY
ENFORCEMENT      = NOT_IMPLEMENTED (except Class A AgentOutput JSON for RESEARCH_ANALYST_AGENT)
RUNTIME_VERIFIED = NO
```

Layer: **Protocol (B)**.

## Purpose

Every specialist (when chartered) reports in a **structured** form so other agents and humans can compare evidence without scraping prose.

## Minimum response schema

```text
AGENT
TASK
STATUS
SCOPE_CHECK
CONTEXT_REVIEWED
FINDINGS
EVIDENCE
ANALYSIS
CONTRADICTIONS
RISKS
DEPENDENCIES
RECOMMENDATIONS
OPEN_QUESTIONS
ESCALATION
NEXT_ACTION
CONFIDENCE
```

### Field rules

| Field | Rule |
| --- | --- |
| `AGENT` | Identity contract `AGENT_ID` + `VERSION` |
| `TASK` | `TASK_ID` or human task statement; do not invent IDs |
| `STATUS` | Constitution taxonomy token(s) |
| `SCOPE_CHECK` | In-scope / out-of-scope vs charter + Constitution; cite `NON-SCOPE` hits |
| `CONTEXT_REVIEWED` | List of L0–L3 artifacts actually read (paths). If discovery incomplete: `CONTEXT_STATUS = INSUFFICIENT` and stop analysis |
| `FINDINGS` | Observed facts, each traceable |
| `EVIDENCE` | Evidence protocol records; not opinions |
| `ANALYSIS` | Interpretation, labeled separately from findings |
| `CONTRADICTIONS` | `NONE IDENTIFIED` or full contradiction blocks |
| `RISKS` | Harm / authority / stale-doc risks |
| `DEPENDENCIES` | Other agents, tests, or human decisions required |
| `RECOMMENDATIONS` | `PROPOSE` class only unless charter grants more |
| `OPEN_QUESTIONS` | Unresolved; do not fill with guesses |
| `ESCALATION` | `NONE IDENTIFIED` or escalation protocol payload |
| `NEXT_ACTION` | Single next step; fail-closed if blocked |
| `CONFIDENCE` | Qualitative; never a fake numeric score without a defined method |

**Do not pad.** If a section has nothing: `NONE IDENTIFIED` or `NOT APPLICABLE`.

Forbidden: generating empty-looking “findings” to look complete.

---

## Existing Class A output (`[IMPLEMENTED]`)

`research_worker/research_task.py` `AgentOutput` is a **narrow JSON contract** for the deterministic analyst. It is **not** this 15-field specialist template.

`DEFERRED_IMPLEMENTATION`: optional adapter from `AgentOutput` → this schema for human reports. Do not break the worker JSON validator to force this template.

---

## Uncertainty

```text
UNKNOWN ≠ SAFE
If CONTEXT_STATUS = INSUFFICIENT → do not emit confident FINDINGS
Hypotheses allowed only when the task says so, and must be labeled HYPOTHESIS
```
