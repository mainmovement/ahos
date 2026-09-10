# P5 ObservationGrant — Adversarial Threat Model

**Kind:** Pre-implementation security review. Not an implementation.  
**PR:** [#93](https://github.com/mainmovement/ahos/pull/93) — **DRAFT**  
**AUDITED_SHA:** `38247d172319741f5df7bd6e01ba2817bf211def`  
**DESIGN_COMMIT:** `50cbe7e01b8583aae85eccb7b230c3ca787919d1`  
**Design report:** `reports/agi_aci_evolution/P5_MEMORY_AUTHORIZATION_BOUNDARY_ARCHITECTURE_DESIGN.md`

`CODE_CHANGES_ALLOWED = NO`  
`IMPLEMENTATION_AUTHORIZED = NO`  
`MERGE = NO`  
`READY_FOR_REVIEW = NO`

Attacker: ordinary in-process Python; all current public memory APIs; dataclass construction; mutation of mutable objects; replay; arbitrary strings; unexpected call order; repeated `CognitiveOrchestrator.run`.  
Attacker does **not** have: AHOS HMAC secret, a separately instantiated trusted ObservationAuthority held only by a composition root, or privileged external credentials.

Proof language: **PROVEN** / **DISPROVEN** / **UNRESOLVED**.  
This is not AGI/ACI/entailment/NER.

---

## 1. Current authority model

**PROVEN (code at audited SHA):** factual consumption authority is the stored `epistemic_kind` plus bind-time temporal/applicability/support. There is no ObservationGrant object. `remember(OBSERVED_FACT)` is sufficient to reach FACTUAL_PREMISE when the row is retrieved (`tests/test_p5_memory_authorization_boundary.py`).

Option B (design commit) proposes: persist FACT_KINDS only with an HMAC-bound grant; bind need **not** re-verify HMAC; `ObservationAuthority` is the only mint.

This review attacks that **proposed** control, not a running implementation.

---

## 2. Attack surface inventory (reachable OBSERVED_FACT without a grant — **today**)

| Path | Location | Classification **today** | After Option B **as written** |
| --- | --- | --- | --- |
| `CognitiveMemoryStore.remember(..., epistemic_kind=OBSERVED_FACT)` | `store.py` | **PROVEN BYPASS** | Intended break (grant required). Survives if grant check is skipped or `issue()` is public — see §3. |
| `ingest_generic_observation` / `finance_observation` etc. | `adapters.py` | **PROVEN BYPASS** (wrapper around remember, default OBSERVED_FACT, exported from `architecture.cognitive.loop`) | **UNRESOLVED:** if adapters call `issue()` then remember, this **moves** the bypass unless adapters are not publicly callable with arbitrary `statement`. They **are** public and take `statement` today. |
| `CognitiveMemoryStore.record_failure` | `store.py` | Kind OBSERVED_FACT but `typed_class` FAILURE → not FACTUAL_PREMISE (**PROVEN** `typed_class_from_parts`). Not a FACTUAL_PREMISE bypass. | Must not become a back door if type-override is ever removed. |
| `CognitiveMemoryStore.record_world_model_object(..., epistemic_kind=OBSERVED_FACT)` | `store.py` `**kwargs` into remember | **PROVEN BYPASS** (helper does not pin kind; default is INFERENCE but caller can pass OBSERVED_FACT) | Must require grant or refuse FACT_KINDS. **Not named** in the design spec. |
| `CognitiveMemoryStore.supersede` | `store.py` | Copies `old.epistemic_kind` via remember | **UNRESOLVED** in spec beyond “regrant or demote”; must not copy OBSERVED_FACT without new grant. |
| `CognitiveMemoryStore.revise(statement=)` | `store.py` | Changes statement; kind preserved | Design says demote/regrant. If unimplemented, **PROVEN BYPASS** of grant-statement binding. |
| `ConsolidationGate.accept` | `consolidation.py` | **PROVEN SAFE** for OBSERVED_FACT (raises). | No change required for facts. |
| `HypothesisStore.propose` | `hypothesis.py` | **PROVEN SAFE** (JSONL; not retrieved). | No change. |
| `CognitiveOrchestrator.run` write-back | `orchestrator.py` | Writes HYP/LESSON/INFERENCE, not OBSERVED_FACT. **PROVEN SAFE** for fact mint. | Unchanged. |
| Benchmark `corpus.py` / `evaluator.py` / `p5_eval.py` | `architecture/cognitive/benchmark/` | **PROVEN BYPASS** in eval harness (importable in production). | Must use synthetic issuer **not** on production `__all__`. |
| Direct `sqlite3.connect(store.path)` + `INSERT INTO memories` | stdlib + public `store.path` | **PROVEN BYPASS** of any Python-only `remember` check | **PROVEN BYPASS of Option B as written** because the design says bind need not re-verify HMAC. |
| SQLite backup/restore of a cognitive DB | `scripts/sqlite_backup_restore.py` targets other DBs; no cognitive-specific import found | **UNRESOLVED** if an operator restores a file containing forged rows | Consumption-side grant verify would neutralize. |
| `MemoryRecord(...)` constructor | `record.py` | Does not persist by itself. | **PROVEN SAFE** unless something inserts without remember. |
| Test helpers | `tests/` | Not production. | Must not be imported by `architecture/`. |

**Hidden helper that the design omitted:** `record_world_model_object`.

---

## 3. ObservationGrant threat model (Attacks A–M)

These attacks assume Option B is implemented **as specified** in the design report.

| Attack | Description | Authority survives? |
| --- | --- | --- |
| **A** Fake grant dataclass | Construct `ObservationGrant(...)` without HMAC | **Must not.** If grant is a public frozen dataclass and verify only checks field presence, **PROVEN BYPASS**. HMAC verify is mandatory. |
| **B** Copy a valid grant | Reuse bytes/object on a second remember | **Survives** unless nonce/single-use or (statement_sha256, source, observed_at) uniqueness is enforced at persist. Design mentioned nonce; **not specified enough** (store vs issuer ledger). **UNRESOLVED → treat as FAIL if unimplemented.** |
| **C** Modify statement after grant | `revise(statement=)` or mutate grant.statement | Grant must not cover new statement. Design: demote/regrant. **If only remember verifies grant once, revise bypasses. PROVEN BYPASS of spec as written.** |
| **D** Modify source after grant | `revise` does **not** take source_id (**PROVEN**). New remember with old grant + new source_id | Hash binding of source_id required. Copy-grant to new source = Attack B/I. |
| **E** Modify observed_at after grant | `revise` does not take observed_at (**PROVEN**). New row with old grant | Must bind observed_at in HMAC. |
| **F** Modify valid_until after grant | `revise` does not take valid_until (**PROVEN**). Insert-time past valid_until | Bind must recompute expiry (**PROVEN** current bind ignores valid_until). Spec added bind check; **must** HMAC-bind valid_until so attacker cannot store None vs past inconsistently. |
| **G** Modify entity/scope after grant | Entity is **recomputed from statement** (**PROVEN**). Payload/domain: `revise` cannot change domain/payload (**PROVEN**). | Statement hash covers entity. **Domain must be HMAC-bound** or insert-time domain is attacker-chosen forever. Scope broadening via payload is limited (no payload revise). |
| **H** Replay old grant vs new observation | Same as B | See replay §7. |
| **I** Replay grant vs different statement | HMAC(statement_sha256) mismatch | **Rejected if hash is bound and verified at remember AND at bind against latest statement.** Spec skipped bind verify → **PROVEN BYPASS** via revise or SQLite. |
| **J** Serialize/deserialize grant | JSON/pickle of grant including hmac field | Pickle of a grant object is not a signature bypass if verify uses HMAC(secret, canonical bytes). Pickle of **Authority with key** is a secret leak. **Forbid pickle of Authority.** Grant JSON without secret is OK if HMAC still verified. |
| **K** Field order / representation | JSON key order, float formatting | See §6 canonicalization. Unspecified in design → **UNRESOLVED / FAIL for readiness.** |
| **L** Type confusion | `epistemic_kind="OBSERVED_FACT"` vs enum; grant.kind vs remember kind; WORLD_MODEL + OBSERVED_FACT | remember must require grant.kind == requested kind == persisted kind. `record_world_model_object` must not accept FACT_KINDS without grant. |
| **M** Forged HMAC | Random hmac bytes | **Rejected** if secret unknown. **Survives** if verify is skipped, secret is `"test"`, or `hmac.compare_digest` is not used (timing is secondary). |

**Critical result:** Option B **as written** (HMAC at remember only, no bind re-verify, unspecified minting callers) **does not survive C, I (via revise), or SQLite INSERT.**

---

## 4. HMAC threat model

| # | Question | Finding |
| --- | --- | --- |
| 1 | Where must the secret live? | Process-local, held **only** by ObservationAuthority instance created at composition root. **Not** in grant objects, logs, exceptions, or env by default (env is world-readable on many Windows/CI setups). See §17. |
| 2 | Who may mint? | **UNRESOLVED in the design.** “ObservationAuthority.issue” without a caller allowlist means **any importer can request signatures for arbitrary statements.** That **DISPROVES** HMAC-as-authorization. |
| 3 | Can ordinary callers access the signing primitive? | If `issue()` / `_sign()` is a public method on an importable class: **YES**. Attacker model includes public APIs. |
| 4 | Can signing be imported directly? | Python has no real `internal`. `__all__` omission is not a security boundary. |
| 5 | Secret from config/env? | If `AHOS_OBSERVATION_HMAC` is set, any in-process reader of `os.environ` gets it. Attacker “does not possess secret” **fails** if secret is in env. |
| 6 | Arbitrary signatures? | **YES** if `issue(statement=attacker)` is the public mint. **This is Attack A at one remove.** |
| 7 | Canonical serialization required? | **YES** (§6). Not specified. |
| 8 | Domain separation required? | **YES:** HMAC key usage `AHOS-OBSERVATIONGRANT-v1` prefix so grants cannot be confused with other MACs. |
| 9 | Sufficient binding material? | Design listed statement hash, source, observed_at. **Missing:** `kind`, `domain`, `valid_until` (incl. explicit none), `schema_version`, `nonce`, `issuer_id`, `purpose`. |
| 10 | Replay prevention required? | **YES** at persist uniqueness of nonce **or** (hash, source, observed_at, kind) plus bind re-check of latest statement hash. |
| 11 | Expiration cryptographically bound? | `valid_until` must be in MAC. Bind still recomputes vs `now` (time passes). |
| 12 | Revocation/revision invalidates grant? | Latest revision statement hash must match grant. Else old grant authorizes new text. |

**Authority flow that would actually work (not implemented):**

```
composition root
  → constructs ObservationAuthority(secret)   # not importable factory with default secret
  → injects IngestPort into trusted adapters only
  → adapter may only persist observations it constructed from its acquisition path
remember(FACT) verifies MAC + bindings
bind(FACTUAL_PREMISE) re-verifies MAC against **latest** row statement hash + expiry
```

`ObservationGrant.create(...)` callable by tests/production with arbitrary claims is **DISPROVEN** as a boundary.

---

## 5. Minimum grant payload

| Field | Class | Why |
| --- | --- | --- |
| `schema_version` | REQUIRED | Domain separation / evolution |
| `purpose` | REQUIRED | Literal `FACTUAL_INGEST` so tokens cannot be reused for other MACs |
| `kind` | REQUIRED | OBSERVED_FACT only for this token type (see §9 DERIVED_FACT) |
| `statement_sha256` | REQUIRED (DERIVED from statement) | Exact representation bind |
| `source_type` | REQUIRED | Provenance class; not UNKNOWN |
| `source_id` | REQUIRED | Provenance id; not UNKNOWN |
| `observed_at` | REQUIRED | Canonical number (integer microseconds UTC) |
| `valid_until` | REQUIRED as bound field (value may be `null` canonical) | Expiry cannot be swapped |
| `domain` | REQUIRED | Applicability; cannot be swapped post-issue |
| `issuer_id` | REQUIRED | Who minted |
| `nonce` | REQUIRED | Replay |
| `issued_at` | DERIVED | Audit; bind expiry uses valid_until + now |
| `hmac` | DERIVED | MAC over canonical bytes |
| statement plaintext | OPTIONAL in grant object | Store has it; hash is enough in MAC |
| ingested_at / created_at | DERIVED at persist | Not caller-trusted freshness |
| entity / scope strings | NOT TRUSTED in grant | Recomputed from statement+task; do not add NER |
| observation/memory id | OPTIONAL | Assigned at persist; include in MAC only after id exists (second MAC) or omit |
| audience | OPTIONAL | Not needed for single-process Lane B |
| provenance blob | NOT TRUSTED as extra authority | source_type+id already bound |
| version (revision) | NOT in grant | Latest row hash must match grant; revision number is not authority |

**Minimum secure MAC input (canonical bytes):**  
`v1 | FACTUAL_INGEST | kind | statement_sha256 | source_type | source_id | observed_at_us | valid_until_us_or_NONE | domain | issuer_id | nonce`

---

## 6. Canonicalization model

Risk: two different observations sharing a hash/MAC.

| Channel | Rule |
| --- | --- |
| Statement | UTF-8 NFC; hash **exact persist bytes** (`statement.strip()` must be the same function at issue and remember — **one** strip spec). No case-folding. Whitespace after strip is significant. |
| JSON grant | Keys sorted; no NaN; integers for times; `null` not omitted for valid_until. |
| Timestamps | Integer microseconds since Unix epoch UTC. No ISO strings in MAC. Timezone: store UTC only. |
| Enums | Exact `EpistemicKind.value` / `SourceType.value` strings. |
| Null vs missing | Forbidden in MAC fields; always emit `NONE` token or integer. |

Invariant: **MAC equality ⇔ identical authority-bearing tuple.** Semantically similar English sentences **must not** share a hash.

Unicode homoglyphs: different bytes → different grants. That is correct (not a bypass).

---

## 7. Replay model

| Scenario | Result required |
| --- | --- |
| valid grant → persist A → persist A again | Second remember **REJECTED** (nonce spent **or** unique constraint on statement_sha256+source_id+observed_at+kind) |
| valid grant → A → revise statement → replay old grant | Latest row hash ≠ grant → **not** FACTUAL_PREMISE; kind demoted or FACTUAL_PREMISE denied at bind |
| valid grant → A → remember B with same grant | Hash mismatch → **REJECTED** |
| Old grant vs new entity/scope/source/time/valid_until | Bound fields differ → **REJECTED** |

Minimum mechanism: **HMAC-bound nonce + persist uniqueness + bind-time hash check of latest statement.** Do not build a distributed revocation list for v1.

---

## 8. Revision / demotion

**PROVEN today:** `revise()` can change `statement` while keeping `epistemic_kind`.

Attack: grant benign text → persist OBSERVED_FACT → `revise(statement=SUPPORT)` → retrieve → FACTUAL_PREMISE.

**Where old authority survives if only remember checked the grant:** the latest row still says OBSERVED_FACT; bind does not see the grant.

**Invariant:** A grant authorizes exactly the observation representation for which it was issued.

**Required enforcement (both):**

1. `revise(statement=)` on FACT_KINDS: **demote** off OBSERVED_FACT (smallest) **or** require a new grant.  
2. Bind: if kind is OBSERVED_FACT, verify stored grant MAC against **current** statement hash; mismatch → treat as not FACTUAL_PREMISE (fail-closed), even if demote was skipped.

---

## 9. DERIVED_FACT model

| Question | Finding |
| --- | --- |
| Who can create it today? | Any `remember(epistemic_kind=DERIVED_FACT)` (**PROVEN**). Consolidation **cannot** (**PROVEN**). Orchestrator write-back uses INFERENCE, not DERIVED_FACT (**PROVEN**). |
| Factual vs derived authority? | Bind: **forbidden FACTUAL_PREMISE**; `ROLE_INFERRED_PREMISE`; support_strength INDIRECT (**PROVEN**). |
| ObservationGrant? | **Must not** share OBSERVED_FACT grants (`kind` in MAC). |
| Become FACTUAL_PREMISE / DIRECT / positive via decision_bearing_supporters? | **DISPROVEN** for FACTUAL_PREMISE. `ctx.facts` still **buckets** DERIVED_FACT with OBSERVED_FACT (`context.py`) — naming confusion, not role grant. Modes use `may(FACTUAL_PREMISE)`. |
| Write-back as OBSERVED_FACT later? | No orchestrator path. Direct remember would still be the bypass. |
| Mistaken for DIRECT_OBSERVATION? | Retrieval maps DERIVED_FACT → `DERIVED_RESULT`, not `DIRECT_OBSERVATION` (**PROVEN** `KIND_TO_EVIDENCE`). |

**Explicit model:** DERIVED_FACT is **derived authority**, not observation authority. It must **not** use ObservationGrant. It must **not** be in the same mint API as OBSERVED_FACT. Future derived-fact promotion, if any, is a **different** transformation grant from P5 — out of minimum OBSERVED_FACT work. Until then, `remember(DERIVED_FACT)` should be refused or treated as INFERENCE (implementation later). **Do not silently merge with OBSERVED_FACT.**

Design’s `FACT_KINDS` union is **ARCHITECTURE_CONFLICTED-adjacent**: it invites one grant type for two semantics. Threat-model requirement: **ObservationGrant authorizes OBSERVED_FACT only.**

---

## 10. UNKNOWN provenance

Relationship to factual authority only — not a global ban.

| Input | Factual authority |
| --- | --- |
| source_id/source_type/producer/source_location ∈ UNKNOWN_FIELD | **FORBIDDEN** for OBSERVED_FACT persist **and** for FACTUAL_PREMISE |
| Missing / empty tokens | Already rejected by `_require_token` except UNKNOWN literal |
| Fake non-UNKNOWN source_id | **ALLOWED as a string** (no registry). Not a truth oracle. |
| Synthetic `SYNTHETIC_TEST_DATA` | Test issuer only; production FACTUAL_PREMISE policy **UNRESOLVED** (keep data_label; do not treat as SENSOR truth) |
| Contradictory metadata | Episode policy at reason; not grant |

Non-facts may still store UNKNOWN. UNKNOWN_AGE (no observed_at) remains non-FACTUAL_PREMISE.

---

## 11. Source authenticity ≠ observation authorization ≠ truth

**PROVEN:** `source_id` is a string; no registry.

A “valid” source_id does not make the statement true, current, or non-opinion. Grant = permission to persist an **observation-class row** with that provenance tuple. P5 still classifies support, polarity, staleness, contradiction.

Do not add a truth oracle.

---

## 12. Temporal attacks

| Attack | Today | Required |
| --- | --- | --- |
| Expired valid_until, status ACTIVE | FACTUAL_PREMISE **PROVEN** | Bind: expired → not FACTUAL_PREMISE; MAC binds valid_until |
| Future observed_at | **UNRESOLVED** (no test) | Issue **REJECT**; bind fail-closed if observed_at > now |
| Future valid_until | Allowed; means not yet expired | OK |
| Old observation newly inserted | ACTIVE+DATED, **not** CURRENT (**PROVEN** TEMP_CURRENT unused). Still FACTUAL_PREMISE if DATED | **Keep:** DATED ≠ CURRENT. Do **not** treat insert as freshness. FACTUAL_PREMISE-for-DATED is existing P5 semantics (**PROVEN**). Grant must not change that unless a separate “current-only” role is added (not minimum). |
| Timezone / formatting | Float epoch | Integer microseconds UTC in MAC |
| Clock skew | **UNRESOLVED** | Small issue epsilon; do not design NTP |
| Missing observed_at | not FACTUAL_PREMISE **PROVEN** | Issue refuses FACT without observed_at |
| Revise after expiration | status may still ACTIVE | Bind expiry on each reason() |

**Invariant:** Newly inserting an old observation must not manufacture **CURRENT** factual authority. **PROVEN already** (DATED not CURRENT). It **can** still be a DATED FACTUAL_PREMISE today; that is not CURRENT.

---

## 13. Entity / scope attacks

Entity is live from statement vs task (**PROVEN**). Grant binds statement ⇒ entity cannot be swapped without a new hash.

| Attempt | Result |
| --- | --- |
| Grant for statement about ENTITY_A used as ENTITY_B | Different statement or live ENTITY_MISMATCH → not `may_support_task` |
| Scoped observation vs ENTITY_NONE task | Existing entity_alignment; write-side NER **not** required |
| Unscoped observation vs ENTITY_A | Existing ENTITY_SCOPED / mismatch rules |

**INV-06:** “Entity/scope cannot be broadened after authorization” — **statement+domain HMAC + no payload/domain revise** is sufficient. Do not store entity lists in the grant (caller-forged entities would **weaken** live recompute).

---

## 14. API bypass inventory (can produce OBSERVED_FACT without ObservationGrant)

| API | Persist? | Modify? | Assign kind? | Without grant (today) | Option B must |
| --- | --- | --- | --- | --- | --- |
| `remember` | yes | no | yes | **YES** | require grant for OBSERVED_FACT |
| `revise` | revision | statement/status/confidence | no (keeps kind) | **YES** keeps kind | demote or regrant + bind verify |
| `supersede` | yes | via remember | copies kind | **YES** | demote/regrant |
| `record_failure` | yes | no | OBSERVED_FACT+FAILURE type | kind yes, role no | pin FAILURE kind ≠ fact role |
| `record_world_model_object` | yes | no | via kwargs | **YES** | refuse OBSERVED_FACT |
| `ingest_generic_observation` | yes | no | default OBSERVED_FACT | **YES** | not a public fact mint |
| `ConsolidationGate.accept` | yes | no | not FACT | **NO** | unchanged |
| `HypothesisStore.propose` | JSONL | no | n/a | **NO** | unchanged |
| `orchestrator.run` write-back | yes | no | HYP/LESSON/INF | **NO** | unchanged |
| `apply_decay` / `contradict` | status/edges | yes | no | n/a | unchanged |
| sqlite INSERT | yes | yes | yes | **YES** | bind-side MAC verify |
| knowledge `VersionedClaimStore` | other DB | — | claims | **NO** P5 retrieve | unchanged |

---

## 15. propose() / accept()

Hidden escalation search:

`propose` → JSONL → MemoryRetriever? **DISPROVEN.**  
`propose` → orchestrator copies only after `reusable_writeback_permitted` from **facts**. propose-only does not create those facts. **PROVEN SAFE — NO CHANGE REQUIRED.**

`accept` → SEMANTIC LESSON/INFERENCE/HYPOTHESIS → bind FACTUAL_PREMISE? **DISPROVEN.**  
`accept` → OBSERVED_FACT? **DISPROVEN** (EpistemicViolation).  
**PROVEN SAFE — NO CHANGE REQUIRED** for factual authority.

---

## 16. N-hop escalation

Graphs HYPOTHESIS/LESSON/INFERENCE/EPISODIC_INFERENCE/PREDICTION/OPINION/SIMULATION/UNKNOWN/STALE → … → FACT.

**PROVEN:** consumption will not retype those kinds to OBSERVED_FACT or FACTUAL_PREMISE. Intermediate labels cannot manufacture observation authority.

ObservationGrant is required **only at persist of OBSERVED_FACT** (and at bind verify of that row). It is **not** required on hop-2 reusable write-back (those kinds are non-facts).

---

## 17. TOCTOU

| Sequence | Spec hole | Required |
| --- | --- | --- |
| grant → mutate statement → retrieve → bind → reason | remember-only verify | bind re-verify latest hash |
| retrieve → mutate EvidenceBinding → reason | Frozen + live `may()` **PROVEN** | preserve |
| authorize → revise → write-back | write-back uses rebind from store **PROVEN** | demote/regrant so store kind/hash consistent |
| sqlite write after remember | Python check skipped | bind MAC |

Preserve: immutable binding, live recompute, orchestrator rebind, no stale copied roles.

---

## 18. Secret-management requirements

Do **not** put the HMAC secret in:

- environment variables by default (Windows process env, CI logs, child processes)
- committed config / `.env` examples
- grant JSON, SQLite rows, tracebacks, `str(grant)`
- test fixtures that ship a static `"secret"` used in production code paths

v1 requirement: **os.urandom(32) at ObservationAuthority construction**, process-lifetime only, never logged. Tests inject a **test double issuer** in `tests/`, not a committed production key.

CI: no production secret. Composition root later may load from OS secret store — **out of minimum**, must not be `os.environ["AHOS_..."]` in library code.

Filesystem key files: easy to copy; not v1.

If the secret is in the same process, a debugger can read it. **Out of attacker profile** (no secret). **In-process `ObservationAuthority.issue` is in profile** if imported.

---

## 19. Trust-zone model (hardened)

```
Z0 UNTRUSTED INPUT
  caller: anyone
  authority: none
  crypto: none
  persist: no FACT

Z0 → Z1 VALIDATED DATA
  validate_new_record predicates only
  not evidence

Z1 → Z2 PROVENANCE-BOUND OBSERVATION
  caller: trusted ingest only (injected Authority / IngestPort)
  validation: non-UNKNOWN source, observed_at, canonical statement
  crypto: HMAC mint (issue not a public “sign this claim” API)
  persist: no

Z2 → Z3 AUTHORIZED FACTUAL EVIDENCE
  caller: remember with matching grant
  crypto: verify HMAC; persist nonce
  persist: OBSERVED_FACT row + grant material
  retrieval: allowed
  promotion: none (already observation-class)

Z3 → FACTUAL_PREMISE (consumption)
  caller: bind/reason
  crypto: re-verify HMAC vs latest statement + expiry
  validation: live support/entity/temporal
  promotion: role only, not kind change

Z3/Z4 → Z5 REUSABLE KNOWLEDGE
  caller: orchestrator
  authority: reusable_writeback_permitted
  crypto: none (non-fact kinds)
  promotion: FORBIDDEN to OBSERVED_FACT

Z5 → Z3
  FORBIDDEN
```

**Design as written skipped Z3 consumption crypto.** That is why this review is not READY_TO_IMPLEMENT.

---

## 20. Security invariants (non-negotiable)

**INV-01** No untrusted caller can manufacture factual authority. (`issue()` must not be a public arbitrary-claim signer; adapters that take raw `statement` are untrusted mints unless gated.)

**INV-02** A valid grant is bound to the exact authorized observation (canonical MAC tuple §5).

**INV-03** Changing authority-bearing fields (statement, source_*, observed_at, kind, domain, valid_until) invalidates the grant.

**INV-04** UNKNOWN provenance cannot obtain OBSERVED_FACT persist or FACTUAL_PREMISE.

**INV-05** Expired `valid_until`/`expires_at` cannot be FACTUAL_PREMISE; insert does not mint CURRENT.

**INV-06** Entity/scope cannot be broadened except by a new statement (new hash). Domain HMAC-bound. No caller-supplied entity authority.

**INV-07** Revision cannot inherit stale factual authority (demote/regrant + bind hash check).

**INV-08** Derived knowledge (incl. DERIVED_FACT, INFERENCE, LESSON, HYPOTHESIS, episode logs) cannot silently become observation.

**INV-09** No alternate production API (`record_world_model_object`, adapters, sqlite INSERT without verifiable MAC, benchmark seeders in production `__all__`) can bypass the grant.

**INV-10** P5 consumption protections remain intact (frozen bind, live recompute, critic, episode policy, hop-2/3).

**INV-11** ObservationGrant authorizes **OBSERVED_FACT only**, not DERIVED_FACT.

**INV-12** FACTUAL_PREMISE requires a **currently verifiable** grant on the **latest** revision, not a historic remember() success.

---

## 21. Implementation readiness

Option B remains the right **family** (capability token, not renamed remember).

The **written specification is not safe to implement as-is**:

1. Bind-side HMAC omitted → SQLite/revise bypass (**PROVEN** given current `store.path` + `revise`).  
2. Who may call `issue()` unspecified → HMAC signs attacker claims (**DISPROVEN** as authorization).  
3. `ingest_generic_observation` remains a public statement ingest.  
4. `record_world_model_object` omitted.  
5. Canonicalization unspecified.  
6. FACT_KINDS conflates DERIVED_FACT.  
7. Secret/env footgun unspecified.  
8. Nonce uniqueness store unspecified.

### NOT_READY

No unresolved **consumption** retype bypass (hops, propose, accept). Unresolved **write/mint/verify** details that would leave INV-01 broken.

Do not authorize implementation until a revised spec (separate review) includes: public-mint ban, bind-time verify, OBSERVED_FACT-only grants, helper-API closures, canonical MAC, nonce, secret rules.

---

## 22. Files this task

Only this report. Production, tests, schemas, Lane A, soak, forensic reports: **untouched**.

Lane A freeze not re-run as a mutation; no files in `discovery/**` or `paper_trading/**` were edited.

---

## 23. FINAL STATUS

`ARCHITECTURE-DESIGN = INSUFFICIENT`

`SECURITY-REVIEW = FAIL`

`IMPLEMENTATION_AUTHORIZED = NO`

`CODE_CHANGES_ALLOWED = NO`

`MERGE = NO`

`READY_FOR_REVIEW = NO`

`LANE_A_STATUS = UNTOUCHED`

`SOAK_STATUS = UNTOUCHED`

`AUDITED_SHA = 38247d172319741f5df7bd6e01ba2817bf211def`

`DESIGN_COMMIT = 50cbe7e`

`REPORT = reports/agi_aci_evolution/P5_OBSERVATIONGRANT_THREAT_MODEL.md`

STOP.
