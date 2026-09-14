# Agent Evidence Protocol

```text
DOCUMENT_ID      = AGENT_EVIDENCE_PROTOCOL
VERSION          = 0.1.0
STATUS           = DESIGN_ONLY as reporting protocol; Slice 2B epistemic objects are IMPLEMENTED separately
ENFORCEMENT      = NOT_IMPLEMENTED for 19-agent reports
RUNTIME_VERIFIED = NO
```

Layer: **Protocol (B)**.

## Forbidden collapse

```text
"I think X is true"
        ↓  must not become
"EVIDENCE"
```

Also:

```text
Evidence ≠ Claim ≠ Hypothesis ≠ Prediction ≠ Observation ≠ Decision ≠ Outcome
```

Slice 2B implements these as **typed artifacts** (`agent_org/epistemic.py`, `[IMPLEMENTED]`). This protocol is the **reporting** overlay so agents that are not writing TCB objects still stay honest.

Do not register TCB artifacts unless the task and session grant `epistemic.write`. Planned 01–19 agents have **no** such grant by default.

---

## Finding record (required when material)

```text
Evidence ID
Source
Location
Timestamp / Version if available
Observed Fact
Interpretation
Confidence
Verification Status
```

| Field | Rule |
| --- | --- |
| Evidence ID | Stable in the report (`EVD-…` or TCB id if one exists). Do not reuse for a different fact. |
| Source | File, test name, audit event, or “human statement (L5)” |
| Location | Path, module, test id, line if known |
| Timestamp / Version | File mtime unknown is OK; git hash if known. This workspace had **no `.git` directory** at Constitution v0.1 inspection → git version `[UNKNOWN]` unless later verified |
| Observed Fact | What was seen, not why |
| Interpretation | Separate; may be `NONE IDENTIFIED` |
| Confidence | Tied to status token, not theatre |
| Verification Status | Constitution taxonomy |

---

## Contradiction protocol

If two sources disagree, **do not silently pick one**.

```text
CONTRADICTION DETECTED
SOURCE A
SOURCE B
CONFLICT
IMPACT
CURRENT RESOLUTION     | UNRESOLVED
REQUIRED VERIFICATION
```

Mark the claim `[CONTRADICTED]` until resolved at L0/L1/L2.

Known **current** organization contradiction (must remain visible):

```text
SOURCE A  = ahos_org/registry.py CANONICAL_AGENT_IDS (19 logical Slice 1 roles) [IMPLEMENTED] [TESTED]
SOURCE B  = docs/agents/PLANNED_19_AGENT_MAP.md (19 specialist blueprint roles) [PLANNED] [DESIGN_ONLY]
CONFLICT  = two different 19-role taxonomies
IMPACT    = agents must not assume the blueprint replaced the registry
CURRENT RESOLUTION = both retained; blueprint not seeded; no silent merge
REQUIRED VERIFICATION = human decision on mapping / dual-running / retirement
```

Slice 2B `CREATE_CONTRADICTION` is the **store** analog (`[IMPLEMENTED]`) and is not automatically filled by this markdown report.

---

## Staleness

Evidence older than the files it cites, or citing L4 docs as current architecture, must be labeled `[STALE]`.

Test pass in one environment is not production proof.
