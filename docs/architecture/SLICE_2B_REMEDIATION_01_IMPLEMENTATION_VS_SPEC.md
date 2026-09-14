# Slice 2B Remediation-01 — Implementation vs Restored Slice 2A Spec

**Mission:** CLOSE D-01 + restore Slice 2A spec  
**Spec:** `docs/architecture/SLICE_2A_EPISTEMIC_CORE_AND_TCB_SPEC.md` (`2A-RESTORED-2`)  
**Scope:** focused classification. D-02..D-20 are **not** silently redesigned.

This review does **not** independently re-verify D-01. It records what this remediation changed and what remains.

---

## Alignment summary

| Area | Result |
|---|---|
| Exclusive `PROMOTE_KNOWLEDGE` path for `KnowledgeState.PROMOTED` | FIXED_NOW (D-01) |
| Generic `TRANSITION_ARTIFACT` cannot promote | FIXED_NOW |
| One frozen promotion policy (map + helper + TCB) | FIXED_NOW |
| Candidate-bound Approval | REMEDIATED_PENDING_INDEPENDENT_VERIFICATION (D-04) |
| Independent verification beyond sock-puppet producer | DOCUMENTED_DEFERRED (D-02) |
| Challenge object required before VERIFIED | DOCUMENTED_DEFERRED (D-03) |
| Production identity / process isolation / durable store | DOCUMENTED_DEFERRED (Slice 2C prerequisites) |

`SPEC_IMPLEMENTATION_ALIGNMENT = PARTIAL`: D-01 exclusive promotion remains in force; D-04 candidate binding is implemented pending independent verification; D-02, D-03, and D-05..D-20 remain deferred.

---

## Defect register

### D-01 — CRITICAL — `FIXED_NOW`

- Generic `LEGAL_ARTIFACT_TRANSITIONS` no longer includes `KnowledgeCandidate: VERIFIED -> PROMOTED`.
- The table is frozen (`MappingProxyType`) and import-time validated against `KNOWLEDGE_PROMOTION_STATES`.
- `transition_artifact` refuses promotion states.
- `TrustedCommandBoundary.__transition_epistemic` refuses promotion targets and resulting `PROMOTED` state.
- The only production assignment `lifecycle_state=KnowledgeState.PROMOTED` is `__promote`, reachable only via `CommandType.PROMOTE_KNOWLEDGE`.
- Dedicated gates are unchanged (existence, VERIFIED, evidence eligibility, revocation/staleness, contradiction, independent verification, scoped human approval, expiry/revocation, scope match, global deny).
- Approval-alone cannot promote via generic transition (Attack D).

### D-02 — HIGH — `DOCUMENTED_DEFERRED`

Independent verification remains principal-string inequality plus artifacts attributed to a non-acting agent while the local operator is the only session holder. Slice 2C blocker. Not required to close D-01.

### D-03 — HIGH — `DOCUMENTED_DEFERRED`

`KnowledgeState.CHALLENGED` is a lifecycle enum, not a requirement that a `ContradictionCase` exist. Happy path still transitions `UNDER_REVIEW -> CHALLENGED` with no contradiction object. Not required to close D-01.

### D-04 — HIGH — `REMEDIATED_PENDING_INDEPENDENT_VERIFICATION`

Approval now carries optional `candidate_id`. Knowledge promotion requires `Approval.candidate_id == KnowledgeCandidate.candidate_id`. Missing binding is denied (`approval_missing_candidate_binding`) and is not a task-scoped wildcard. Mismatched binding is denied (`approval_candidate_mismatch`). Generic `TRANSITION_ARTIFACT` still cannot promote. Implementation testing is not independent verification.

### D-05 — MEDIUM — `DOCUMENTED_DEFERRED`

Claim lifecycle still allows `SUBMITTED -> VERIFIED` without `CHALLENGED`. Weaker than knowledge. Not changed.

### D-06 — MEDIUM — `DOCUMENTED_DEFERRED`

PASS verification may cite existing evidence IDs including the target evidence itself. Not changed.

### D-07 — MEDIUM — `DOCUMENTED_DEFERRED`

`Evidence.content_hash` is stored, not verified against bytes. No content plane exists. Spec now states hashes are identifiers, not fetch-proof.

### D-08 — MEDIUM — `DOCUMENTED_DEFERRED`

Contradiction `affects_candidate_ids` is caller-chosen and length-1 in Slice 2B. Sibling candidates sharing claims/evidence may be omitted. Not changed.

### D-09 — MEDIUM — `DOCUMENTED_DEFERRED`

Hypothesis `SUPPORTED` / Prediction `CONFIRMED` still lack observation extra-gates. Types remain distinct. Not changed.

### D-10 — MEDIUM — `DOCUMENTED_DEFERRED`

`ResearchMission.authority_resources` is not filtered against `PROTECTED_RESOURCES`. Contract poisoning, not execution. Not changed.

### D-11 — MEDIUM — `DOCUMENTED_DEFERRED`

`LEGAL_ARTIFACT_TRANSITIONS[MemoryRecord]` still lists `PROMOTED`; TCB still denies memory-as-truth. Split-brain remains for memory only. Not in D-01 scope (different type and enum).

### D-12 — MEDIUM — `DOCUMENTED_DEFERRED`

`CommandEnvelope` has no `slots=True`. `object.__setattr__` remains a same-process residual. Not changed.

### D-13 — MEDIUM — `DOCUMENTED_DEFERRED`

Untrusted import boundary is static AST/tests, not a runtime import firewall. No plugin runtime. Not changed.

### D-14 — MEDIUM — `DOCUMENTED_DEFERRED`

Command `evidence_lineage` checks existence/prefix, not eligibility. Not changed.

### D-15 — MEDIUM — `DOCUMENTED_DEFERRED`

No audited principal revoke/suspend command. Not changed.

### D-16 — LOW — `DOCUMENTED_DEFERRED`

Handler `assert isinstance(payload, ...)` is stripped by `python -O`. Envelope construction still type-checks. Not changed.

### D-17 — LOW — `DOCUMENTED_DEFERRED`

RT-06 constructor-only and RT-13 synthetic ledger remain test-quality issues. Not retargeted in this mission.

### D-18 — LOW — `DOCUMENTED_DEFERRED`

“Projection staging” is a failure-injection trip, not an independent staged projection store. Spec records that projections copy committed state.

### D-19 — LOW — `DOCUMENTED_DEFERRED`

Some `task_required=False` commands cannot be usefully delegated because child grants must narrow to a task. Not changed.

### D-20 — LOW — `DOCUMENTED_DEFERRED`

`Approval.action` remains `str` rather than `Operation`. Not changed.

---

## Architectural deviations vs restored spec

| Item | Class |
|---|---|
| Local operator stub instead of production auth | ARCHITECTURAL_DEVIATION (authorized stub) |
| In-memory store instead of durable transactions | ARCHITECTURAL_DEVIATION (authorized Slice 2B limit) |
| Bootstrap/session issue not command-audited | ARCHITECTURAL_DEVIATION (declared trusted constructor) |
| Memory generic map still allows PROMOTED (D-11) | ARCHITECTURAL_DEVIATION / DOCUMENTED_DEFERRED |
| Approval candidate-bound (D-04) | REMEDIATED_PENDING_INDEPENDENT_VERIFICATION |
| Forensic claim that 121 tests were re-run this audit | FALSE_POSITIVE relative to forensic `WINDOWS_VALIDATION = NOT_RUN`; this remediation re-runs the suite |

No other silent architecture change was introduced to make tests pass.
