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

`SPEC_IMPLEMENTATION_ALIGNMENT = PARTIAL`: D-01 exclusive promotion remains in force; D-04 candidate binding is implemented pending independent verification; Remediation-02 closed D-03/05/06/11/16/20; Remediation-03 closed D-09/10/12/15/17 and dispositioned D-14/D-18 as spec-conformant. Remaining deferred: D-02 + D-07 + D-13 (Slice-2C architectural prerequisites), D-08 + D-19 (semantic policy — Human/Council decision per `docs/architecture/SLICE_2B_DEFERRED_DECISIONS_ADR.md`).

---

# Remediation-02 — defect-register closures (2026-09-15)

**Scope:** close the epistemic-integrity cluster that is implementable inside
Slice 2B's authorized limits (no production identity, no durable store).
D-02 (independent verification substance), D-07..D-10, D-12..D-15, D-17..D-19
are explicitly **not** silently redesigned.

Every closure below is: implemented + unit-tested + adversarially tested
(negative gates prove each check bites) + regression-run across both suites
(2411 passed / 0 failed / 4 skipped / 1 xfailed on this Linux dev host;
the Windows sentinel visibly skips off-Windows and still gates on Windows).
Independent verification per protocol remains a distinct future event; these
closures do not claim it.

| Defect | Before | Closure | Evidence |
|---|---|---|---|
| D-03 HIGH | `UNDER_REVIEW -> CHALLENGED -> VERIFIED` with zero contradiction objects ever existing; CHALLENGED was a bare enum flip | **FIXED_NOW** | TCB denies `knowledge_challenge_requires_contradiction_case` unless a stored `ContradictionCase` names the candidate; composed reachable chain (challenge filed -> CHALLENGED gate -> resolution with eligible evidence -> unresolved-contradiction block -> independent PASS -> VERIFIED -> PROMOTE) pinned by `tests2b/test_d03_challenge_requirement.py` (6 tests). A deliberately unreachable "VERIFIED requires challenge" branch was NOT added: VERIFIED is only reachable from CHALLENGED, so the CHALLENGED gate is the provably sufficient point of enforcement. |
| D-05 MEDIUM | Claim `SUBMITTED -> VERIFIED` without CHALLENGED | **FIXED_NOW** | Map edge removed; `tests2b/test_d05_claim_challenge_path.py` (4 tests) pins map, TCB denial, and the full challenged happy path. |
| D-06 MEDIUM | PASS verification could cite the target evidence itself (circular proof); fixtures encoded the pattern | **FIXED_NOW** | Layered: `VerificationRecord` refuses construction AND the TCB denies `verification_cannot_cite_target_itself` even under the documented `object.__setattr__` residual; fixtures now cite a distinct review artifact; `tests2b/test_d06_verification_self_citation.py` (5 tests). |
| D-11 MEDIUM | Memory map listed `-> PROMOTED` while the TCB denied it (policy split-brain, forbidden by spec section 24) | **FIXED_NOW** | Edges removed from the frozen map; TCB deny short-circuits before map evaluation to keep the precise reason; `MemoryState.PROMOTED` remains in the enum (spec-26 concept) but is unreachable; `tests2b/test_d11_memory_promotion_splitbrain.py` (5 tests). |
| D-16 LOW | 12 handler `assert isinstance(payload, ...)` vanished under `python -O` | **FIXED_NOW** | All 12 raise explicit `DomainDenied("payload_type_mismatch")`; zero `assert` statements remain in `agent_org/` (AST-pinned); forgery denied both in-process and in a real `python -O` subprocess; `tests2b/test_d16_assert_survival.py` (3 tests). |
| D-20 LOW | `Approval.action` was free-form `str` | **FIXED_NOW** | Typed `Operation` with fail-closed coercion at construction (string call sites keep working; forged strings rejected); promotion gate compares identity; `tests2b/test_d20_approval_action_typing.py` (5 tests). |

Residual observations recorded as organizational memory (not defects opened
here): (a) a candidate may lawfully re-enter CHALLENGED on an already-RESOLVED
challenge and exit VERIFIED again — a state no-op cycle with no privilege
gain, since every VERIFIED gate reruns; (b) a contradiction may be filed while
its candidate is still SUBMITTED, which models real pre-review challenges;
(c) D-03 introduces no ordering requirement between CREATE_CONTRADICTION and
the CHALLENGED transition other than artifact-existence at transition time.

---

# Remediation-03 — defect-register closures (2026-09-15, second loop)

Same evidence bar as Remediation-02; the dual-suite regression for this loop
is recorded in the session report (tests2b 142 passed / 1 skipped at last
loop-local run; the final combined run is the committed `reports/` artifact
referenced in the session summary).

| Defect | Before | Closure | Evidence |
|---|---|---|---|
| D-09 MEDIUM | Hypothesis `SUPPORTED` / Prediction `CONFIRMED` reachable with zero observations; Observation VERIFIED gate was **architecturally unreachable** (producer resolved from registrar provenance in a single-session plane, so INDEPENDENT verification of an observation could never be constructed) | **FIXED_NOW** | Root repaired before gating: `Observation.producer_principal_id` added (Evidence pattern) so INDEPENDENT verification (producer=agent, verifier=operator) is constructible; producer must be active at registration; `SUPPORTED`/`CONFIRMED` now require ≥1 VERIFIED observation from a non-invalidated run→plan→hypothesis chain. `tests2b/test_d09_observation_gates.py` (6 tests: none/unrecorded/foreign-chain/invalidated-run denied; full chain allows both states). **Residuals:** (i) `ExperimentPlan` has no transition-map entry at all — plans cannot be INVALIDATED while runs can (asymmetry noted for Slice 2C); (ii) `REFUTED`/`INCONCLUSIVE` terminals keep current semantics pending the council decision on symmetric evidence requirements. |
| D-10 MEDIUM | `ResearchMission.authority_resources` / `authority_capabilities` carried scope nothing could lawfully confer | **FIXED_NOW** | Registration denies protected resources and forbidden capabilities in task vocabulary; `tests2b/test_d10_mission_scope_guard.py` (3 tests). |
| D-12 MEDIUM | `CommandEnvelope` and payloads had `__dict__`: arbitrary attribute attachment on governed objects | **FIXED_NOW** | `slots=True` on all 14 dataclasses in `commands.py`; undeclared attachment raises (AttributeError/TypeError by runtime) with nothing stored; `tests2b/test_d12_envelope_slots.py` (3 tests). The documented `object.__setattr__` same-process residual is unchanged. |
| D-14 MEDIUM | `evidence_lineage` checked existence/prefix, not eligibility | **SPEC_CONFORMANT_BY_DESIGN** | Analysis: lineage is an audit-envelope field (spec §27), not a consumption input. Eligibility-at-citation would make honest curation flows unsubmittable (revoking stale evidence while citing it; resolving contradictions against superseded evidence). Eligibility stays enforced at consumption points. Pinned by `tests2b/test_d14_lineage_boundary.py` (2 tests). |
| D-15 MEDIUM | No audited principal revoke/suspend command | **FIXED_NOW** | `REVOKE_AGENT` end-to-end (enum + payload + policy row + TCB handler + root grant); denials: unknown / protected (operator+system) / already-revoked; identities forever (no re-registration); effect immediate via existing `revoked_at is None` liveness checks. Grant-cascade revocation documented as residual for the multi-session model (in-slice agent grants are unreachable — no session can be minted for an agent). `tests2b/test_d15_principal_revoke.py` (7 tests). |
| D-17 LOW | RT-06 constructor-only; RT-13 synthetic-ledger level unjustified | **FIXED_NOW** | rt06b: TCB-path INDEPENDENT self-verification under constructor bypass denied with the correct reason after all prior gates pass on real artifacts. rt13: documented why same-process private-state corruption is the correct attack level; rt13b/rt13c add middle-excision (count checkpoint) and field-forgery (event hash) variants. |
| D-18 LOW | "Projection staging" is a failure-injection trip, not a staged store | **SPEC_CONFORMANT_BY_DESIGN** | Spec §28 requires *copied views*; `snapshot_for_projection` deep-copies under lock. No staged projection store is required by spec. |

Human/Council decisions routed to `docs/architecture/SLICE_2B_DEFERRED_DECISIONS_ADR.md`: D-08 (contradiction affect-derivation policy), D-19 (delegation narrowing for task-less commands).

## D-09 follow-through — latent host-facade break (2026-09-15, same loop)

FOUND VIA CONSUMER SWEEP (the checklist item this defect now mandates):
`agent_org/research_host/host.py` `record_observation` constructed
`Observation` without the newly-required `producer_principal_id`. Every
suite stayed green because no test exercised the host's experiment chain —
a live instance of the repository law that green tests ≠ runtime health.

- **Fix:** factory threads `self.__context.principal_id` (the registered
  research principal — always distinct from the operator, keeping
  INDEPENDENT verification reachable) into the constructor.
- **RCA:** immediate = missing ctor argument; root = contract evolution
  preceded by an incomplete consumer sweep; contributing = zero runtime
  coverage of the host facade path, so the break was invisible to tests;
  process fix = consumer sweep added to the contract-change procedure plus
  `tests2b/test_research_host_experiment_flow.py` pinning the runtime path
  (2 tests: committed observation resolves producer = registered research
  principal; unknown-run denial leaves no residue).
- **Classification:** TEST-FIRST-EVIDENCE of a production constructor fix;
  the hysteresis of frozen fixture files is untouched (pre-D-09 test
  observations legitimately lack the field in their historical context —
  none of them is production code).

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
