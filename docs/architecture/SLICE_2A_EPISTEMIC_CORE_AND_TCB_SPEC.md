# SLICE 2A EPISTEMIC CORE AND TCB SPECIFICATION — RESTORED/VERSIONED

**Document id:** `SLICE_2A_EPISTEMIC_CORE_AND_TCB_SPEC`  
**Version:** `2A-RESTORED-2`  
**Status:** RESTORED/VERSIONED contract for Slice 2B implementation, D-01 exclusive promotion, and D-04 candidate-bound approval  
**Architecture verdict this contract implements:** `FOUNDATION_EXTENSIBLE_WITH_MANDATORY_TCB_AND_EPISTEMIC_FIREWALL`

---

## Provenance

This file is **not** a cryptographic or archival replica of a missing original.

- The original Slice 2A architecture was specified **before** Slice 2B implementation.
- The named source artifact `SLICE_2A_EPISTEMIC_CORE_AND_TCB_SPEC.md` was **absent** from `G:\robat\ahos-agent-org` when Slice 2B was implemented and when forensic verification ran.
- This version **reconstructs** the previously authorized Slice 2A contract from:
  - Slice 1.5 architectural review (epistemic core + trusted command boundary as the required next design);
  - the complete Slice 2B implementation authorization (identity, TCB, commands, epistemic objects, promotion, audit, projections, import boundary, residual risks);
  - the D-01 exclusive-promotion invariant that the authorization implied by requiring a dedicated promotion command and a complete promotion gate, but that Slice 2B failed to encode in the generic lifecycle map.
- Implementation **must be checked against this document**. Any deviation must be recorded explicitly (see `docs/architecture/SLICE_2B_REMEDIATION_01_IMPLEMENTATION_VS_SPEC.md`).
- No hash, signature, git object, or third-party archive is claimed as provenance.
- Identical copies are placed at the historically expected repository-root path and under `docs/architecture/`. They are the same restored text, not two competing specifications.
- **Version history (reconstructed series, not archival originals):** `2A-RESTORED-1` recorded exclusive `PROMOTE_KNOWLEDGE` (D-01). `2A-RESTORED-2` makes knowledge-promotion Approval bind to `KnowledgeCandidate.candidate_id` (D-04). Missing candidate binding is not a wildcard.

---

## 0. Character and non-goals

This specification defines an **isolated in-process control-plane foundation**.

It is **not**:

- an AHOS implementation or integration;
- an execution engine, tool runner, or trading system;
- an agent runtime, Agent One, or a 19-agent council;
- a provider, model-API, network, browser, Docker, or cloud system;
- production authentication, WebAuthn, or external identity;
- durable database, queue, or multi-process isolation.

Python standard library, immutable dataclasses, explicit state machines, fail-closed policy, and deterministic tests are the intended implementation style.

---

## 1. Foundational principles

These equalities are **forbidden**. The corresponding objects, commands, and states must remain distinct:

```text
COGNITION != GOVERNANCE != EXECUTION
EVIDENCE != CLAIM != HYPOTHESIS != PREDICTION
!= OBSERVATION != DECISION != OUTCOME
UNKNOWN != SAFE
```

Additional non-collapses:

- `CLAIM != FACT`
- `HYPOTHESIS != KNOWLEDGE`
- `PREDICTION != OBSERVATION`
- `OBSERVATION != INTERPRETATION`
- `MEMORY != TRUTH`
- `COMPLETED EXPERIMENT != PROVEN`
- `SELF_CHECK != INDEPENDENT VERIFICATION`
- `LOCAL_OPERATOR_STUB != PRODUCTION_HUMAN_AUTHENTICATION`
- `TAMPER-EVIDENT != TAMPER-PROOF`
- `IMPLEMENTED != TESTED != VERIFIED != PRODUCTION-READY`

Fail-closed beats convenience. Absence of evidence is not safety. Open contradiction is not resolved by recency or confidence.

---

## 2. Epistemic Core

The Epistemic Core is the typed object model for sources, evidence, claims, hypotheses, predictions, observations, knowledge candidates, contradictions, research missions, experiments, verification, approval, assurance, and memory.

It is **not** a world model, researcher, or learner. It stores **propositions and their warrants**, not operational truth.

Required properties of every epistemic artifact:

- immutable identity in a typed namespace;
- typed provenance (creator principal, session, command, method);
- explicit lifecycle state;
- timezone-aware timestamps;
- positive version;
- lineage where applicable;
- construction validation that rejects empty or forged identifiers.

Arbitrary strings must not masquerade as registered artifacts. IDs used as references must resolve to stored objects of the expected type.

---

## 3. Trusted Command Boundary

The Trusted Command Boundary (TCB) is the **sole mutation ingress** for governed Slice 2B state.

Conceptual flow:

```text
UNTRUSTED CALLER
  -> immutable CommandEnvelope + Session
  -> TrustedCommandBoundary.submit
       schema / session / principal
       policy evaluation (fail-closed)
       TCB-derived AuthorityContext
       domain transition on a working copy
       audit append
       atomic commit of state + audit
  -> typed CommandResult
```

Direct mutation of governed state by untrusted callers is **forbidden**. Naming, comments, and developer discipline are not enforcement. Structural bounds that Python actually permits (frozen envelopes, permit-gated store, single public `submit`, import-boundary tests) are required.

`submit(command, session)` must perform, in order:

1. schema validation (envelope construction);
2. session validation;
3. principal resolution;
4. authority derivation (TCB-owned);
5. capability / operation / resource evaluation;
6. policy evaluation;
7. scope validation;
8. expected-state-version validation;
9. domain validation;
10. state transition on a working copy;
11. audit append;
12. projection-stage hook (read models are copied from committed state);
13. typed result.

No privileged mutation may bypass this path.

---

## 4. Principal

A Principal is an immutable identity record:

- `principal_id` (namespaced);
- `identity_type` ∈ {AGENT, HUMAN, SYSTEM};
- `status` ∈ {ACTIVE, SUSPENDED, REVOKED};
- provenance;
- created/revoked timestamps.

Specializations:

- `AgentIdentity` — logical agent; not an authority root; not a session issuer in this slice;
- `HumanIdentity` — the only identity that may issue Approval artifacts;
- `SystemIdentity` — TCB/bootstrap component identity.

Caller-controlled trust flags are forbidden as authorization sources:

- `trusted=true`
- `verified=true`
- `operational=true`
- `human_approved=true`

An agent must not establish those properties by payload fields.

---

## 5. Session

A Session binds a principal to a bounded interval:

- `session_id`;
- `principal_id`;
- `auth_method`;
- `issued_at` / `expires_at`;
- optional `revoked_at`.

Commands are denied if the session is unknown, unequal to the registered session, expired, revoked, or bound to a different principal than `actor_principal_id`.

---

## 6. AuthorityContext

`AuthorityContext` is **derived by the TCB**, never accepted from the caller.

It records:

- principal, task (or explicit none), capability, operation, resource;
- policy version;
- authority chain of grant IDs;
- derivation time and expiry.

Command envelopes must carry a sentinel such as `DERIVE_AT_TCB`. Any caller-supplied authority blob is a construction failure.

---

## 7. Capability–operation–resource binding

Authorization is an **exact** tuple:

`principal × capability × operation × resource × task × policy_version`

Default is DENY. Empty allow-list is DENY. There are no wildcards.

Denied without exception:

- expired grant;
- revoked grant;
- wrong principal;
- wrong task;
- wrong operation;
- wrong resource;
- wrong capability;
- broken authority chain;
- child authority exceeding parent;
- delegation depth exceeded;
- protected AHOS / execution resources;
- `Capability.EXECUTION` and `Capability.POLICY_MODIFY`;
- `Operation.EXECUTE` and `Operation.UPDATE_POLICY`.

Cognitive authority must not imply execution authority.

---

## 8. Authority attenuation

Delegation creates a child grant that is a **narrowing** of a parent grant:

- time contained in parent lifetime;
- capability/operation/resource cannot expand;
- task scope must narrow (root task-unscoped grants, if any, must become task-scoped children);
- depth = parent + 1 and ≤ configured maximum;
- recorded as an explicit Delegation artifact.

Untrusted commands cannot mint root grants (`parent_grant_id is None`).

---

## 9. Immutable CommandEnvelope

Privileged commands are frozen typed envelopes containing:

- `command_id`, `command_type`
- `actor_principal_id`, `session_id`
- `authority_context_ref` (TCB sentinel only)
- `task_scope`, `resource_scope`, `capability_scope`, `requested_operation`
- `policy_version`
- `causation_id`, `correlation_id`, `parent_command_id`
- `evidence_lineage`
- `expected_state_version`
- typed frozen `payload`
- `issued_at`

Where a field is not applicable, represent that **explicitly**. Malformed envelopes fail closed **before** authorization. Payload type is bound to command type. After construction, normal assignment cannot mutate the envelope.

---

## 10. TCB-derived authority

Effective authority is computed inside `submit` from registered grants. Handlers must not trust envelope fields that claim authorization. Policy mapping from `command_type` to `(capability, operation, resource, task_required)` is fixed. Callers cannot substitute a more powerful tuple onto a weaker command.

---

## 11. Single-writer mutation and atomic state + audit

Governed state lives in a store that:

- is mutated only with an unforgeable permit held by the TCB;
- uses a single-writer lock;
- copies state at `begin`, mutates the copy, and replaces live state only at `commit`;
- commits **state change and audit event together**, or not at all.

If any stage fails after `begin`, live state and live audit remain as before that command. Denial is an audited non-mutation of domain objects (the command id may be recorded to prevent replay). This is an **in-memory** transaction, not durable crash recovery.

---

## 12. Source

`Source` is a registered origin of evidence: type, locator, content hash, provenance, lifecycle `REGISTERED | SUPERSEDED | REVOKED`. Hashes are stored identifiers, not proof that bytes were fetched.

---

## 13. Evidence

`Evidence` is retrieved content with:

- `evidence_id`, `source_id`, producer principal;
- retrieval and observation timestamps;
- `content_hash`, `content_ref`, extraction method;
- validity/lifecycle, freshness policy, expiry;
- assurance score (0..100), lineage, supersession, revocation;
- verification status.

Invariants:

- revoked evidence cannot support new positive promotion;
- stale evidence cannot silently become valid;
- unknown evidence IDs fail;
- evidence cannot self-declare `VALID` / `PASS` at registration;
- positive support requires current, non-revoked, unexpired, independently PASS-verified evidence.

---

## 14. Claim

`Claim` is an interpretation of evidence. It is not a fact. Lifecycle includes draft/submitted/challenged/verified/rejected/superseded. Verification of a claim requires an independent verification record. Claims must not collapse into KnowledgeCandidate or Outcome.

---

## 15. Hypothesis

`Hypothesis` is a falsifiable proposition with supporting claim IDs and falsification criteria. `SUPPORTED` is not knowledge and not a promoted truth.

---

## 16. Prediction

`Prediction` is an expected observation bound to a hypothesis and an evaluation deadline. Confirmation of a prediction is not an Observation and not promoted knowledge.

---

## 17. Observation

`Observation` is a measured value from an experiment run. It is not an interpretation. Independent verification may be required to mark it verified. Invalidated observations remain first-class.

---

## 18. KnowledgeCandidate

`KnowledgeCandidate` is a proposition that **may** become promoted knowledge only through the dedicated promotion path.

Lifecycle:

```text
SUBMITTED
  -> UNDER_REVIEW
  -> CHALLENGED
  -> VERIFIED
  -> PROMOTED          # dedicated command only; see §24
alternatives: REJECTED | DEFERRED | SUPERSEDED
```

A candidate requires proposition, claims, evidence, producer, and provenance. It cannot pre-declare verification or contradiction IDs at birth. It cannot register already `PROMOTED`.

---

## 19. Contradiction

`ContradictionCase` is a first-class conflict between artifacts, with rationale and affected candidate IDs.

- Open / under-investigation / retained-uncertain contradictions **block promotion**.
- Resolution requires eligible evidence; it is not “newest claim wins” and not confidence.
- Contradictory evidence must not disappear; there is no delete of governed artifacts in this slice.
- Automatic selection of a winner is forbidden.

---

## 20. ResearchMission

Contract-only research workflow: question, unknowns, hypotheses, required evidence, constraints, allowed methods, assigned agent, authority scope, expiry, deliverables, verification requirement, success/failure criteria, parent mission, causal lineage.

No autonomous researcher, web research, or model calls.

---

## 21. Experiment

`ExperimentPlan` (protocol) and `ExperimentRun` (execution record) with states:

`PLANNED | RUNNING | COMPLETED | FAILED | INCONCLUSIVE | INVALIDATED`

`COMPLETED != PROVEN`. Negative and inconclusive outcomes are first-class. No external experiment execution.

---

## 22. VerificationRecord

Independent verification:

- producer ≠ independent verifier;
- `SELF_CHECK` may exist and must **not** satisfy promotion;
- target must be a registered artifact;
- unknown evidence references deny;
- status is set at creation (no FAIL→PASS rewrite of the same record).

Independence in this slice is **principal-id inequality plus verification kind**, not organizational independence, competence, or compromise history. That limitation is residual and blocks treating verification as production-grade.

---

## 23. Approval

Approval is an artifact, never `human_approved=true`.

Required properties:

- scoped to action, resource, capability, task (where applicable), policy version;
- immutable after issue except revocation;
- expiring;
- revocable;
- bound to a human principal;
- auditable.

Approval cannot override a global deny or manufacture a forbidden capability.

**Candidate binding:** human approval for knowledge promotion is artifact/candidate scoped. The canonical identifier is `KnowledgeCandidate.candidate_id`. A valid approval for candidate A cannot authorize promotion of candidate B. Missing `candidate_id` is not a wildcard and is not a task-scoped substitute. Presence of a valid approval still does **not** make `TRANSITION_ARTIFACT` a promotion mechanism.

---

## 24. Knowledge promotion lifecycle — exclusive command

> **`KnowledgeState.PROMOTED` is not reachable through generic artifact transition. It is exclusively controlled by the dedicated promotion command and its complete promotion gate.**

### Authoritative policy (one policy, no split-brain)

| Axis | Rule |
|---|---|
| Artifact type | `KnowledgeCandidate` |
| Target lifecycle | `KnowledgeState.PROMOTED` |
| Command | `CommandType.PROMOTE_KNOWLEDGE` only |
| Generic command | `CommandType.TRANSITION_ARTIFACT` **must deny** any request whose target denotes that promotion state |
| Generic lifecycle map | **must not** list `PROMOTED` as a legal `TRANSITION_ARTIFACT` edge |
| Writer | TCB promotion handler after every gate succeeds |

A table that says `VERIFIED -> PROMOTED` is legal while the TCB secretly denies it is a **policy split-brain** and is forbidden unless an explicit test proves the TCB is the sole authority **and** the table is not consulted as policy. Prefer one frozen map that cannot name the promotion edge at all, plus a typed refuse in the generic helper, plus a resulting-state check in the generic TCB handler.

### Dedicated promotion gates (all required)

A KnowledgeCandidate may reach `PROMOTED` only if:

1. the candidate exists and is a `KnowledgeCandidate`;
2. expected version matches;
3. lifecycle is `VERIFIED`;
4. producer/verifier requirements remain satisfied;
5. evidence eligibility is revalidated now;
6. revoked evidence is rejected;
7. stale evidence is rejected;
8. an open / under-investigation / retained-uncertain contradiction affecting the candidate is rejected;
9. independent verification (`INDEPENDENT` + `PASS` + verifier ≠ producer + verifier currently ACTIVE) is present;
10. an active scoped human Approval exists;
11. the approval is not expired;
12. the approval is not revoked;
13. the approval matches task / action / resource / capability / policy version **and** `Approval.candidate_id == KnowledgeCandidate.candidate_id` (missing binding denies; A cannot authorize B);
14. global deny still wins.

Missing any gate: `PROMOTION = DENY`. Domain state remains `VERIFIED`. The denial is audited.

Generic `TRANSITION_ARTIFACT` to `PROMOTED` is denied **even when every dedicated gate would have passed**, including when a perfect Approval exists.

---

## 25. Assurance

Assurance is a bounded numeric annotation on evidence/memory. It is **not** authority, not truth, and not a substitute for verification, contradiction handling, or approval. Scalar scores must not create capabilities.

---

## 26. Memory categories

Conceptual kinds (single `MemoryRecord` type, not ten databases):

Episodic, Semantic, Procedural, Failure, Hypothesis, Causal, Performance, Self-model.

Memory requires evidence references, provenance, and a lifecycle that can be challenged. **Memory must never automatically become TCB-authoritative knowledge.** Autonomous learning is out of scope.

---

## 27. Audit envelope

Slice 2A `AuditEvent` fields:

`event_id`, `timestamp`, `actor_principal`, `session_id`, `authority_chain`, `command_id`, `correlation_id`, `causation_id`, `parent_task_id`, `resource_id`, `operation`, `capability_id`, `policy_version`, `artifact_version`, `evidence_lineage`, `previous_state`, `previous_version`, `resulting_state`, `resulting_version`, `result`, `failure_reason`, `payload_hash`, `event_hash`, `previous_event_hash`.

Canonical serialization and SHA-256 chaining are **tamper-evident**, not tamper-proof. Required controls: duplicate detection, replay rejection, expected-version checking, hash-chain verification. No external anchor in this slice.

---

## 28. Projections

Untrusted callers may read copied views of agents, tasks, epistemic objects, research missions, audit events, and capability/delegation status. Projections have **no mutators** and must not expose secrets (this slice stores none). Write-through via returned objects is forbidden.

---

## 29. Import boundary

Untrusted/future-plugin modules must not import governed-store mutators, TCB internals, governance internals, authority internals, or the audit ledger. Static inspection is the Slice 2A/2B control. Runtime import firewalls and process isolation are deferred.

---

## 30. Threat model (Slice 2A/2B)

**In scope (must deny or contain):**

- untrusted in-process caller using only supported APIs (`CommandEnvelope` + `submit` + projections);
- forged session, actor, approval, evidence ID, verification target;
- self-verification presented as independent;
- capability/operation/resource substitution;
- excess child authority;
- expired/revoked grants and sessions;
- command replay;
- generic lifecycle used as a promotion backdoor;
- a valid approval for candidate A used to promote candidate B;
- missing approval candidate binding treated as a wildcard;
- memory registered or transitioned as truth;
- policy self-modification;
- cognitive command used to obtain execution/AHOS scope.

**Out of scope / residual:**

- hostile same-process Python with reflection against name-mangled attributes;
- attacker who already owns all process memory (can rewrite audit + checkpoints together);
- process restart (state and replay set are volatile);
- multi-process writers;
- production identity proof.

---

## 31. Residual same-process Python risk

Python is not a process security boundary. `object.__setattr__`, name-mangled attribute access, and `importlib` of trusted modules remain possible for code already running in the process. Module privacy and permits are **structural for supported APIs**, not a hostile-code TCB. Classify reflection-only bypasses as `EXPECTED_SAME_PROCESS_RESIDUAL`. Do not implement those bypasses. Do not load plugins or model-generated code until a stronger isolation boundary exists.

---

## 32. Deferred process isolation

Process isolation, language-level sandboxing, and a separate trusted runtime are **deferred**. They are Slice 2C (or later) prerequisites, not this contract’s implementation.

---

## 33. Deferred external identity

Production human authentication, passwords, WebAuthn, IdP federation, workload identity for agents, and credential storage are **deferred**. They must exist before any sensitive integration.

---

## 34. Explicit non-production local operator stub

`NON_PRODUCTION_LOCAL_OPERATOR_AUTH` / `LOCAL_OPERATOR_STUB`:

- issues sessions for **one configured human**;
- bounded lifetime, expiry, revocation;
- no passwords, secrets, or credentials in source or logs;
- holding the stub is equivalent to holding the local trust root;
- bootstrap of system principal, operator principal, and root grants is a trusted constructor, **not** command-ingress audited.

This stub **proves session semantics** for tests. It does **not** prove human identity.

---

## 35. Slice 1 compatibility

Legacy Slice 1 (`ahos_org`) remains a separate governance scaffold. It is not authoritative for Slice 2A/2B governed state. Wrap-and-harden: do not silently preserve bypass APIs into the new store. Do not wire Slice 1 mutators to future runtimes.

---

## 36. Explicitly out of scope until later authorized missions

Agent One runtime; autonomous agents; AHOS source/database/soak/lanes; Telegram; n8n; providers; network; browser; Docker; cloud; live or paper trading; model APIs; durable DB; WebAuthn.

---

## 37. Language

Do not claim “secure”, “tamper-proof”, “production-ready”, “fully trusted”, or “unbreakable” unless a later mission actually proves it. Prefer: implemented, tested, fail-closed, tamper-evident, not yet verified, residual risk.
