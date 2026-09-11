# P5 Memory Authorization Boundary — Architecture Design

**Kind:** Pre-implementation architecture. Not a fix. Not a feature.  
**PR:** [#93](https://github.com/mainmovement/ahos/pull/93) — **DRAFT. MERGE = NO. READY_FOR_REVIEW = NO.**  
**AUDITED_SHA:** `38247d172319741f5df7bd6e01ba2817bf211def`  
**Previous production:** `1a7e5e74a016da7b8d7aed65a4049c4f2a727e12`  
**Data label:** `SYNTHETIC_TEST_DATA`  
**CODE_CHANGES_ALLOWED: NO**  
**IMPLEMENTATION_AUTHORIZED: NO**

This document specifies the **minimum safe memory authorization boundary** to be implemented later, after independent review. It does not implement it.

Proof language: **PROVEN** / **DISPROVEN** / **UNRESOLVED**. Claims cite code or tests at this SHA.

This is not entailment, NER, AGI, or ACI. Lane A freeze 36/36. `P5_FORENSIC_ARCHITECTURE_GATE.md` last content commit `02c41be`. Soak untouched.

---

## 0. Decision in one page

| Question | Answer |
| --- | --- |
| What manufactured authority? | **PROVEN:** `CognitiveMemoryStore.remember(epistemic_kind=OBSERVED_FACT)` lets an ordinary in-process caller label a row as fact. Consumption then honors that label (`typed_class_of` → FACTUAL_PREMISE if DATED/AGING/CURRENT + applicable). Tests: `tests/test_p5_memory_authorization_boundary.py`. |
| Is retrieval a silent retype bug? | **DISPROVEN.** Retrieval copies `epistemic_kind`. HYP/LESSON/INFERENCE cannot become OBSERVED_FACT. |
| Is `propose()` a fact bypass? | **DISPROVEN.** JSONL only; `MemoryRetriever` reads `CognitiveMemoryStore` only. |
| Is `accept()` a fact bypass? | **DISPROVEN** for OBSERVED_FACT (raises `EpistemicViolation`). **PROVEN** it can mint SEMANTIC labels without `proposed_kind` / source existence / human. Those labels cannot bind as FACTUAL_PREMISE. |
| Smallest break in the attack chain? | **Refuse FACT_KINDS on generic `remember` unless an unforgeable-by-ordinary-callers ObservationGrant, minted by ObservationAuthority, is bound to this statement+source+observed_at.** |
| Recommended option | **B** (capability / typed authorization token), with the issuer designed so it can later become Option C without changing consumption. |
| Option A (new public method, same kwargs)? | **DISPROVEN** as sufficient (moves the bypass). |
| In-process Python debugger-proof? | **UNRESOLVED / limited.** Same-process attackers who can import the issuer key or patch the store are out of scope. Target: ordinary API callers. |

---

## 1. Reconstruct the current authority model

Live path (production code, not names):

```
CALLER
  → CognitiveMemoryStore.remember(...)          # architecture/cognitive/memory/store.py
  → MemoryRecord + validate_new_record          # record.py
  → SQLite INSERT memories
  → MemoryRetriever.retrieve                    # retrieval.py  (store.recent + anchors)
  → assemble_context                            # context.py
  → bind_context / bind_item                    # binding.py
  → MODE_FNS[reasoning_mode]                    # modes.py
  → critique / apply_constraint                 # reason.py, inference.py
  → apply_episode_positive_policy               # episode.py
  → reusable_writeback_permitted                # episode.py
  → CognitiveOrchestrator.run write-back        # orchestrator.py  (rebinds from RetrievedItems)
```

### Stage table

| Stage | Trusted | Caller-controlled | Recomputed | Merely stored | Actually authorized | Forgeable | Mutable later | Promotable | Consumable as factual evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `remember` kwargs | enums; AI_MODEL/AGENT ↛ FACT_KINDS; confidence range; non-empty tokens | kind, statement, source_*, observed_at, valid_until, confidence, payload | nothing epistemic | everything else | **nothing beyond “row may persist”** | kind=OBSERVED_FACT | `revise()` can change statement/status/confidence | caller chooses kind at write | if kind=OBSERVED_FACT and later bind allows FACTUAL_PREMISE |
| `validate_new_record` | presence of provenance strings; AI veto | content of those strings, including literal `UNKNOWN` | no | — | valid **data**, not authorized **evidence** | `UNKNOWN` tokens | n/a | no | n/a |
| persistence | append-only `(memory_id, revision)`; integrity hash | payload JSON | hash from canonical fields | status=ACTIVE always on insert | persistence only | valid_until in the past still ACTIVE | `revise` appends revision | no | n/a |
| retrieval | store row fields | `requested_evidence` on task (public); question tokens | lexical/structured scores | evidence_class mapped from **stored kind** (`KIND_TO_EVIDENCE`) | “may appear in context” not “is a fact” | requested_evidence ids | DTO copy of fields | **DISPROVEN** kind retype | OBSERVED_FACT → `DIRECT_OBSERVATION` **because stored kind says so** |
| EvidenceBinding | frozen dataclass | initial copies of type/kind/status/statement | `live_typed_class`, `live_temporal_state`, `live_roles`, `may_support_task`, polarity, entity from **statement+task** | copied allowed_roles (ignored by `may()`) | roles from live type+temporal+applicability | stored role tuples **DISPROVEN** as authority (`may()` recomputes) | FrozenInstanceError on assign | no | FACTUAL_PREMISE iff live type OBSERVED_FACT and temporal in {CURRENT, AGING, DATED} and applicable |
| support classification | `classify_support(statement, task)` | statement | polarity, support_class, clause_force, entity | none as authority | task-support, not type | stored support_class **DISPROVEN** | live | no | DIRECT_SUPPORT is a **clause class**, not a stored kind |
| episode policy | bindings after critic | — | mixed polarity / uncertain | — | positive verdict eligibility | graph edges not required | n/a | no | needs decision-bearing FACTUAL_PREMISE |
| critic | findings from bindings+candidate | — | action | — | can kill/downgrade verdict | — | n/a | no (downgrade) | kill-class DOWNGRADE removes reusable positive |
| verdict | constrained candidate | — | — | string on episode payload | episode-level conclusion | — | n/a | no | positive only if policy allows |
| reusable write-back | `reusable_writeback_permitted(verdict, rebind(RetrievedItems))` | `write_back`, task_type | rebind | reason() DTO flag not trusted by orchestrator | HYP/LESSON/SEMANTIC INFERENCE mint | DTO **DISPROVEN** | n/a | loop conclusions, not OBSERVED_FACT | derived kinds cannot FACTUAL_PREMISE |

**PROVEN:** Authority for *consumption as fact* is `epistemic_kind` on the store row + temporal/applicability at bind, not a separate authorization object.  
**PROVEN:** Authority for *reusable conclusions* is orchestrator + `reusable_writeback_permitted`.  
**PROVEN:** There is **no** write-side authorization object for OBSERVED_FACT other than “caller passed the enum.”

---

## 2. Define the authority boundary

These five must not be equated.

| Layer | Meaning | Current trusted boundary | Minimum future trusted boundary |
| --- | --- | --- | --- |
| **A. Storage** | May persist this object | `validate_new_record` | Unchanged for non-FACT_KINDS. FACT_KINDS additionally require ObservationGrant. |
| **B. Retrieval** | May retrieve this object | `MemoryRetriever` anchors (exact_id, lexical, P4.3 rejects) | Unchanged. Retrieval must not become the fact-authorization gate. P4.3 FAILURE-intent reject is **not** authorization (**PROVEN** `requested_evidence` still anchors). |
| **C. Epistemic classification** | May classify as a kind | **Caller-chosen** `epistemic_kind` | FACT_KINDS classified only if ObservationAuthority issued a grant for this statement hash. Other kinds remain caller-chosen labels (consumption already forbids FACTUAL_PREMISE). |
| **D. Evidence authorization** | May function as factual evidence | Bind roles: OBSERVED_FACT + DATED/AGING/CURRENT + applicable | Same consumption rules **plus** the row must have been written under a grant (stored grant id / issuer in provenance). Bind does not need to re-verify HMAC if write already required it; bind still recomputes support from statement. |
| **E. Reusable knowledge authorization** | May participate in reusable write-back | `reusable_writeback_permitted` after critic+episode, rebind | Unchanged. |

### OBSERVED_FACT meaning — design choice

**Reject:** “A caller stored a row labeled OBSERVED_FACT.”  
That interpretation **is** the proven bypass.

**Adopt:** “AHOS ObservationAuthority has issued a grant that this statement, at this `observed_at`, from this `source_type`/`source_id`, may be persisted as OBSERVED_FACT. Consumption may then treat it as a candidate factual premise if temporal/applicability/support still hold.”

This is **not** a truth oracle. Grant ≠ the statement is true. Grant = **this caller was allowed to assert an observation-class record**. P5 still decides whether that record **supports this task**.

`FACTUAL_PREMISE` remains a **reasoning role**, never a stored kind (**PROVEN** `EpistemicKind` has no FACTUAL_PREMISE; `test_remember_rejects_factual_premise_kind`).

---

## 3. OBSERVED_FACT ingestion contract (not implemented)

Authority-bearing inputs for **issuing a grant** (ObservationAuthority), not for a renamed `remember()`.

| Field | Class | Purpose (demonstrated) |
| --- | --- | --- |
| `statement` | REQUIRED FOR AUTHORITY | Bind and support recompute from statement (`binding.py`, `support.py`). Empty rejected today. |
| `statement_sha256` | DERIVED BY AHOS | Binds grant to exact bytes; blocks grant reuse on a different sentence. |
| `epistemic_kind=OBSERVED_FACT` (or DERIVED_FACT) | REQUIRED FOR AUTHORITY | The kind being authorized. |
| `source_type` | REQUIRED FOR AUTHORITY | Existing AI_MODEL/AGENT veto (`validate_new_record`). Must not be UNKNOWN for FACT_KINDS. Allowed: SENSOR, SYSTEM, DATABASE, HUMAN (existing `SourceType`). |
| `source_id` | REQUIRED FOR AUTHORITY | Provenance identity string. Must not be UNKNOWN/empty-equivalent. **Not** a registered source (**PROVEN** no SourceRegistry in `architecture/cognitive`). Integrity of id, not truth of claim. |
| `source_location` | REQUIRED FOR AUTHORITY | Existing required token; ingest path (file, adapter, probe). Not UNKNOWN for FACT_KINDS. |
| `producer` + `producer_version` | REQUIRED FOR AUTHORITY | Who minted the grant. Not UNKNOWN for FACT_KINDS. |
| `observed_at` | REQUIRED FOR AUTHORITY | Without it bind yields UNKNOWN_AGE and **forbids FACTUAL_PREMISE** (**PROVEN** `test_missing_observed_at_is_not_factual_premise`). Grant must require it so authorized facts are not immediately non-premises. |
| `created_at` / ingest time | DERIVED BY AHOS | Store already sets created_at. Do not trust caller to prove freshness. |
| `valid_until` | OPTIONAL METADATA at write; **consulted at bind** | Store field exists; bind currently **ignores** it (**PROVEN** `temporal_from_parts(status, observed_at)` only; `RetrievedItem` has no `valid_until`). See §5. |
| `valid_from` | OPTIONAL METADATA | Same as valid_until; decay uses it for AGING window. |
| `domain` | REQUIRED FOR AUTHORITY as a **label**, not as truth | Applicability uses domain at bind. Not UNKNOWN-as-missing for facts if we want scoped observations; `COGNITIVE_CORE` currently yields APPLICABILITY_UNKNOWN (`binding._applicability`). |
| `confidence` | OPTIONAL METADATA | Stored; **MUST NEVER BE TRUSTED** as type or support (**PROVEN** not used in `_roles`). Range check stays. |
| `payload` | OPTIONAL METADATA | Applicability fingerprints (component) live here; bind reads via `store.get`. Do not trust payload to set kind or polarity. |
| `status` | DERIVED BY AHOS | Insert always ACTIVE (**PROVEN**). Caller must not pass ACTIVE to mean “fresh.” |
| `contradiction_state` | DERIVED BY AHOS | Insert UNCONTESTED (**PROVEN**). |
| `polarity` / `support_class` / `clause_force` / `temporal_state` DTO | MUST NEVER BE TRUSTED FROM CALLER | Not even on remember today; bind recomputes. Do not add write-side copies as authority. |
| `entity` as extracted ids | MUST NEVER BE TRUSTED FROM CALLER at write | Entity is recomputed from statement (`classify_support`). Do not add NER at write. |
| Acquisition path | REQUIRED FOR AUTHORITY as `source_location` + `producer` | Distinguishes adapter vs raw remember. |
| Integrity hash | DERIVED BY AHOS | Already `compute_integrity_hash`. |
| ObservationGrant HMAC | DERIVED BY AHOS | See Option B. |

**Not added:** source registry, cryptographic identity of the physical sensor, world-model object graph, NLI scores. No code path today consumes those (**PROVEN** absence).

---

## 4. UNKNOWN provenance

### Where UNKNOWN is created (**PROVEN**)

| Location | What |
| --- | --- |
| `architecture/cognitive/memory/types.py` `UNKNOWN = "UNKNOWN"` | Canonical token |
| `remember()` defaults | `source_type=SourceType.UNKNOWN`, `source_id=UNKNOWN`, `source_location=UNKNOWN`, `producer=UNKNOWN`, `producer_version=UNKNOWN`, `context=UNKNOWN` (`store.py`) |
| `_require_token` | Rejects only missing/blank; **accepts** the string `UNKNOWN` (`record.py`) |
| `record_failure` | `probable_cause` / `recovery` default UNKNOWN; source_id can be component or UNKNOWN |
| Orchestrator | `recovery="UNKNOWN"`; `data_label` may be `"UNKNOWN"` |
| Binding | UNKNOWN_AGE, APPLICABILITY_UNKNOWN, SUPPORT_UNKNOWN — **recomputed**, not write provenance |

### Can UNKNOWN coexist with OBSERVED_FACT?

**PROVEN YES.** Defaults allow it. `test_remember_accepts_arbitrary_observed_fact` uses `source_id=UNKNOWN`.

### Can it become DIRECT_OBSERVATION / FACTUAL_PREMISE / positive / write-back?

**PROVEN YES** if `observed_at` is set and the statement supports the task (`test_consumption_remembered_observed_fact_is_factual_premise`, `test_lexical_retriever_without_failure_intent_consumes_forged_fact`). UNKNOWN provenance is not consulted at bind for roles.

### Minimum rule (not a global ban)

| Kind | UNKNOWN provenance tokens (`source_id`, `source_location`, `producer`, `source_type`) |
| --- | --- |
| OBSERVED_FACT / DERIVED_FACT (Z3 candidate) | **FORBIDDEN** at grant issue. `UNKNOWN ≠ fabricated evidence`. |
| HYPOTHESIS / LESSON / INFERENCE / OPINION / PREDICTION / SIMULATION / EPISODIC INFERENCE | **ALLOWED** (uncertainty and incomplete provenance are legitimate for non-facts). |
| FAILURE records | ALLOWED for unknown recovery fields; typed_class FAILURE ≠ FACTUAL_PREMISE (**PROVEN** `typed_class_from_parts`). |
| EpistemicAnswer.UNKNOWN / UNKNOWN_AGE | **Preserved** — these are consumption uncertainty, not write provenance. |

Do not ban UNKNOWN in critic findings, temporal UNKNOWN_AGE, or task `data_label=UNKNOWN`.

---

## 5. Temporal authority

### Actual model (**PROVEN**)

| Mechanism | Behavior |
| --- | --- |
| Insert | `status=ACTIVE` always. `valid_until` stored if passed. |
| `apply_decay` | If `expires_at` or `valid_until` ≤ now → STALE; near valid_until → AGING. **Must be called.** Corpus tests call it; live orchestrator **does not** call it on `run`. |
| Bind `temporal_from_parts` | Uses **`status` + `observed_at` only**. ACTIVE + observed_at → **DATED**, never CURRENT. CURRENT is reserved and unused by this layer. |
| `RetrievedItem` | **No `valid_until` field.** Bind cannot see expiry without `store.get`. |
| Past `valid_until` on insert | Status stays ACTIVE → still FACTUAL_PREMISE (**PROVEN** `test_forged_temporal_valid_until_does_not_mark_stale_on_insert`). |
| Missing `observed_at` | UNKNOWN_AGE → not FACTUAL_PREMISE (**PROVEN**). |
| STALE status | not FACTUAL_PREMISE (**PROVEN**). |

Stale is **stored** as `status` after decay, **not** recomputed from `valid_until` at retrieve/bind/reason.

### Minimum invariant (do not redesign decay)

> An object whose `valid_until` (or `expires_at`) is already ≤ `now` must not receive FACTUAL_PREMISE merely because `status` is still ACTIVE.

**Where to enforce (minimum, two points):**

1. **Grant issue (write):** ObservationAuthority refuses FACT grants if `valid_until` is not None and `valid_until ≤ issue_now`.  
2. **Bind (consumption, TOCTOU-safe):** `live_temporal_state` / `_roles` treat expired `valid_until`/`expires_at` as STALE-equivalent for FACTUAL_PREMISE **when store is available** (same pattern as payload lookup in `bind_item`). Do not invent an age-from-clock threshold for rows without `valid_until` — that would redesign temporal semantics (**PROVEN** comment in `temporal_state_of`).

Do not require `apply_decay` as the only gate; orchestrator does not call it today.

Future observation timestamps (`observed_at` > now): **UNRESOLVED** in current tests. Minimum: grant refuses `observed_at > issue_now + epsilon`. Consumption: do not treat future-dated rows as CURRENT (already cannot; they would be DATED). Optional bind reject of future `observed_at` as UNKNOWN_AGE — specify in implementation as fail-closed if `observed_at > now`.

---

## 6. Source authority

**PROVEN:** `source_id` is a **string** on `MemoryRecord` / `RetrievedItem`. There is no registered source table, no verified-source API, no evidence-object pointer, no authority-bearing provenance record type.

`find_by_source(source_id)` is equality on that string.

**Minimum safe rule for factual ingestion:**

- `source_type ∈ {SENSOR, SYSTEM, DATABASE, HUMAN}` (not UNKNOWN, not AI_MODEL, not AGENT — last already vetoed).  
- `source_id` non-empty and not in UNKNOWN_FIELD.  
- Existence in an external registry is **not** required (no registry exists; inventing one is not minimum).  
- Matching `source_id` **MUST NEVER** mean the claim is true.

Provenance integrity: the id is attributable. Truth remains P5 support classification.

---

## 7. Entity and scope

**PROVEN:** Write path does not parse entities. `classify_support` / `entity_alignment` run at bind from statement vs task (`support.py`, `EvidenceBinding.may_support_task`). Domain/applicability: `_applicability` in `binding.py` (LESSON component/domain; FAILURE fingerprints; else domain match).

| Invariant | Where it belongs |
| --- | --- |
| Entity-specific evidence ↛ unscoped task support | **Bind / reason** (already: ENTITY_MISMATCH / ENTITY_SCOPED). Do **not** duplicate at write (would require NER). |
| Scoped observation ↛ unrelated task | **Bind** applicability + support class; **retrieve** may still return lexical cousins (P4.3 exists). |
| Write | Optional payload fingerprints if the adapter already knows a component id — OPTIONAL METADATA, never sufficient for FACTUAL_PREMISE. |
| Write-back | Unchanged: reusable_writeback needs decision-bearing FACTUAL_PREMISE (entity-compatible supporters). |

Minimum write-side entity rule: **none** beyond not storing caller-supplied polarity/entity fields as authority.

---

## 8. Confidence and polarity

| Metadata | Caller supplied? | Normalized | Recomputed | Immutable | Forbidden to override |
| --- | --- | --- | --- | --- | --- |
| polarity / support_class / clause_force | no (not on remember) | n/a | **yes** from statement+task | on frozen binding | **yes** as authority |
| identity / entity tokens | no | tokenizer | **yes** | binding frozen | **yes** |
| temporal_state DTO | no | n/a | **yes** from status+observed_at (+ valid_until per §5) | | **yes** |
| confidence | optional on remember | range [0,1] | no | via revise | **must not** set type/roles (**PROVEN** unused in `_roles`) |
| epistemic_kind | **yes today** | enum | no | revise does not take kind | future: FACT_KINDS only via grant |

Existing P5 principle remains: **stored metadata must never manufacture authority when the statement contradicts it.** Live recompute stays. The new write grant authorizes **kind persistence**, not support class.

---

## 9. HypothesisStore.propose

| Question | Finding |
| --- | --- |
| 1. Purely storage? | **PROVEN** JSONL append, state=PROPOSED, statement required. |
| 2. Epistemic authorization point? | **DISPROVEN** for P5 facts. No critic, no grant. |
| 3. Create reusable knowledge? | Ledger row only. Reusable P5 HYPOTHESIS **memory** is `remember(HYPOTHESIS)` after write-back. |
| 4. Retrieved by MemoryRetriever? | **DISPROVEN** (`retrieve` takes `CognitiveMemoryStore` only). |
| 5–7. Become OBSERVED_FACT / FACTUAL_PREMISE / positive support? | **DISPROVEN** unless also remembered as a memory row; HYPOTHESIS memory still not FACTUAL_PREMISE. |
| 8. Influence later write-back? | Only if orchestrator already has reusable_writeback from **facts**. propose-only: **DISPROVEN** (`test_propose_does_not_enter_memory_retriever`). |

**Preserve the API.** Do not “fix” it in the minimum OBSERVED_FACT boundary.

---

## 10. ConsolidationGate.accept

**PROVEN cannot:** write OBSERVED_FACT or DERIVED_FACT.  
**PROVEN can:** `remember(SEMANTIC, caller_kind)` with any non-empty `actor`; forged `ConsolidationCandidate` with empty `derived_from`; kind ≠ `proposed_kind`.  
**PROVEN consumption:** SEMANTIC LESSON/HYPOTHESIS cannot FACTUAL_PREMISE (`test_consolidation_accept_mints_semantic_but_cannot_factify`, `test_consolidation_forged_candidate_skips_propose_from_episodes`).

| Transition | Classification |
| --- | --- |
| EPISODIC → SEMANTIC INFERENCE | ALLOWED ONLY WITH EXPLICIT AUTHORIZATION conceptually; **today** actor string only |
| EPISODIC → LESSON | same |
| EPISODIC → HYPOTHESIS (semantic) | same |
| * → OBSERVED_FACT | **FORBIDDEN** |
| * → DERIVED_FACT | **FORBIDDEN** |
| * → FACTUAL_PREMISE | **UNREACHABLE** (not a stored kind; bind role) |
| LESSON → OBSERVED_FACT | **FORBIDDEN** / **UNREACHABLE** via accept |
| INFERENCE → FACTUAL_PREMISE | **UNREACHABLE** at consumption (**PROVEN** roles) |

`accept()` is **semantic labeling/storage**, not factual authorization. Missing `proposed_kind` / source existence / `requires_human` is a **label-integrity gap**, not the proven fact bypass.

**Minimum OBSERVED_FACT design: do not change `accept()`.** Follow-on (not this minimum): bind accepted kind to `proposed_kind`; require existing `derived_from`; treat `requires_human` as real (out of scope unless a human-attestation grant exists).

---

## 11. Authority escalation matrix

Legend: **DIRECT** = happens by storing/consuming that kind as-is. **AUTHORIZED TRANSFORMATION** = only via an explicit grant/orchestrator policy. **CONDITIONALLY ALLOWED** = allowed if other gates pass. **FORBIDDEN** = code veto or consumption forbid. **UNREACHABLE** = no path.

Rows = source. Columns = target.

| From \ To | OBSERVED_FACT | FACTUAL_PREMISE | DIRECT_SUPPORT (clause) | SUPPORTS / WEAKLY_SUPPORTED | reusable HYP/LESSON/INF |
| --- | --- | --- | --- | --- | --- |
| UNKNOWN provenance + OBSERVED_FACT label | DIRECT today | CONDITIONALLY ALLOWED today | CONDITIONALLY ALLOWED today | CONDITIONALLY ALLOWED today | CONDITIONALLY ALLOWED today |
| **future granted OBSERVED_FACT** | AUTHORIZED TRANSFORMATION | CONDITIONALLY ALLOWED (bind) | CONDITIONALLY ALLOWED (statement) | CONDITIONALLY ALLOWED (P5) | CONDITIONALLY ALLOWED (write-back) |
| FACTUAL_PREMISE as stored kind | UNREACHABLE | UNREACHABLE | UNREACHABLE | UNREACHABLE | UNREACHABLE |
| HYPOTHESIS | FORBIDDEN | FORBIDDEN | FORBIDDEN as fact | FORBIDDEN alone | DIRECT label; write-back extra FORBIDDEN without facts |
| LESSON | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN alone | same |
| INFERENCE | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN alone | same |
| EPISODIC + OBSERVED_FACT | DIRECT (type+kind) | CONDITIONALLY ALLOWED | CONDITIONALLY ALLOWED | CONDITIONALLY ALLOWED | CONDITIONALLY ALLOWED |
| EPISODIC + INFERENCE | FORBIDDEN retype | FORBIDDEN | FORBIDDEN DIRECT strength | FORBIDDEN alone | episode log DIRECT; reusable extra FORBIDDEN |
| PREDICTION | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN extra |
| OPINION | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN extra |
| SIMULATION | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN extra |
| ASSUMPTION (not a kind) | UNREACHABLE | FORBIDDEN | FORBIDDEN | FORBIDDEN | FORBIDDEN |
| CONTRADICTORY pair of facts | each remains OBSERVED_FACT | mixed: FORBIDDEN positive | both may classify SUPPORT/CONTRA | FORBIDDEN WEAKLY_SUPPORTED | FORBIDDEN reusable |
| STALE OBSERVED_FACT | stays OBSERVED_FACT | FORBIDDEN | FORBIDDEN FACTUAL_PREMISE | FORBIDDEN | FORBIDDEN |

Critical invariant (design): **No epistemically weaker or non-factual artifact may silently gain factual authority.** Consumption already enforces this for non-OBSERVED_FACT. Write must enforce it for minting OBSERVED_FACT.

UNKNOWN row: **future** FORBIDDEN to mint OBSERVED_FACT with UNKNOWN provenance. UNKNOWN_AGE (missing observed_at) stays FORBIDDEN as FACTUAL_PREMISE.

---

## 12. Direct bypass model

### 12.1 `remember(OBSERVED_FACT)` — **PROVEN** chain

```
untrusted caller
  → remember(kind=OBSERVED_FACT, statement=SUPPORT, observed_at=…)
  → row status=ACTIVE, kind honored
  → retrieve (requested_evidence OR lexical without FAILURE intent)
  → evidence_class=DIRECT_OBSERVATION          # KIND_TO_EVIDENCE
  → bind: FACTUAL_PREMISE + support_strength DIRECT
  → classify_support: DIRECT_SUPPORT if statement matches
  → critic: ACCEPT if no findings
  → episode policy: clear if no contra/uncertain
  → verdict: SUPPORTED or WEAKLY_SUPPORTED
  → reusable_writeback_permitted True
  → orchestrator remember HYP/LESSON/SEMANTIC INFERENCE
  → hop-2/3: those artifacts FORBIDDEN as FACTUAL_PREMISE   # PROVEN
```

**Authority is manufactured at write (kind label), consumed at bind (roles honor label).** Not at critic. Not at hop-2.

**Smallest break:** between caller and persistence of FACT_KINDS — **ObservationGrant required**. Then the rest of the chain may run only on granted observations (legitimate ingest).

### 12.2 `propose()` — **PROVEN** no chain into retrieve

Break not required for fact authority. Preserve.

### 12.3 `accept()` — **PROVEN** chain stops at SEMANTIC non-fact

Break not required for fact authority. Label-integrity follow-on only.

---

## 13. TOCTOU / mutation safety

Preserve (**PROVEN** existing tests in `test_p5_second_forensic.py`): frozen EvidenceBinding; live `may()`; orchestrator rebind; no forged supporting IDs; no stored role escalation.

**New TOCTOU if write grant is insert-only:** `revise(statement=…)` on an OBSERVED_FACT (**PROVEN** `revise` can change statement without re-validation of kind). Attacker: grant a benign observation, revise statement into a task-supporting fact.

**Minimum close:**

- `revise` of `statement` (or `epistemic_kind` if ever added) on FACT_KINDS **either** requires a new grant bound to the new statement hash **or** **demotes** kind off FACT_KINDS (fail-closed). Demotion is smaller.  
- `supersede()` calls `remember` with copied kind (**PROVEN** `store.supersede`) — must not copy OBSERVED_FACT without a new grant (or demote).  
- Grant is single-use (nonce) or bound to `(store_id, statement_sha256, observed_at, source_id)` so it cannot be replayed onto another row.  
- Bind still recomputes support from **latest** statement (already). Grant does not freeze polarity.

Valid_until expiry after insert: bind-side check (§5) — **required** so grant-at-t0 cannot remain FACTUAL_PREMISE at t1 after expiry without decay.

No new TOCTOU if these three are in the spec: revise demote/regrant, supersede regrant, bind expiry.

---

## 14. Minimum safe architecture options

### OPTION A — Minimal authorization wrapper

`remember` refuses FACT_KINDS; new `record_observation(**same_kwargs)`.

| Axis | Evaluation |
| --- | --- |
| Security | **DISPROVEN** as sufficient: ordinary callers invoke the new method with the same untrusted arguments (user constraint §15). |
| Simplicity | Highest |
| Testability | Easy |
| Backward compatibility | All current `remember(OBSERVED_FACT)` call sites rename |
| Provenance | Still optional UNKNOWN unless extra predicates (predicates ≠ authorization) |
| Performance | Negligible |
| Cognitive Core future | Paints a second public ingest surface |
| New bypass risk | **High** (moved bypass) |
| Code change | Small |
| Lane A | None |
| Migration | Tests/benchmarks/adapters |

### OPTION B — Capability / typed authorization token

`remember` persists FACT_KINDS only if `observation_grant: ObservationGrant` verifies (HMAC + statement hash + source + observed_at + issuer). `ObservationAuthority` is the only supported mint. Ordinary `remember(..., epistemic_kind=OBSERVED_FACT)` without grant **rejected**.

| Axis | Evaluation |
| --- | --- |
| Security | Stops ordinary API bypass. Same-process key theft **UNRESOLVED** (Python). Target is ordinary callers. |
| Simplicity | Medium (one frozen grant type + issuer + remember check + revise rule) |
| Testability | High: forge grant, replay grant, mismatch hash, missing grant |
| Backward compatibility | Adapters, corpus, tests, `record_failure` must obtain grants (synthetic issuer for SYNTHETIC_TEST_DATA) |
| Provenance | Grant mint enforces non-UNKNOWN for facts |
| Performance | HMAC per fact write, negligible |
| Cognitive Core future | Issuer can later become Option C service without changing bind/reason |
| New bypass risk | Grant constructor public without HMAC = A in disguise — **must** HMAC or sealed mint |
| Code change | Moderate, Lane B only |
| Lane A | None |
| Migration | Explicit synthetic grants in tests; no soak DB rewrite |

### OPTION C — Trusted observation ingestion service

Separate process or module-isolated service acquires observations, validates, writes via private store handle. `remember` FACT_KINDS not importable from app code.

| Axis | Evaluation |
| --- | --- |
| Security | Strongest if process-isolated; in-process “service” without token ≈ A |
| Simplicity | Lowest (IPC, auth, ops) |
| Testability | Needs fakes |
| Backward compatibility | All ingest rewritten |
| Provenance | Natural home for provider adapters |
| Performance | IPC cost if isolated |
| Cognitive Core future | Best long-term (tools, multiple providers) |
| New bypass risk | If the service exposes the same kwargs RPC, bypass moves |
| Code change | Large |
| Lane A | Must not open soak DBs (**PROVEN** FORBIDDEN_DB_NAMES) |
| Migration | High |

### Selection

**RECOMMENDED_OPTION: B**

Reasons: A is **DISPROVEN** as an authorization boundary. C is the correct *issuer evolution* but is not the minimum change and risks a larger incomplete surface. B puts authority in an object ordinary call sites cannot mint without the issuer, keeps retrieval/bind/reason unchanged, and lets ObservationAuthority later become the C service.

---

## 15. Constraint compliance

- Not solved by privatizing `remember` and adding `record_observation` with the same kwargs.  
- Not solved by `kind==OBSERVED_FACT and source_id!="UNKNOWN" and confidence>X`. Those are **valid data** predicates. Authorization is **ObservationGrant minted by ObservationAuthority**.  
- VALID DATA: enums, non-empty statement, ranges.  
- AUTHORIZED EVIDENCE: grant present, HMAC valid, hashes match, issuer is ObservationAuthority, FACT_KINDS only.

---

## 16. Cognitive Core future compatibility

Do not implement these. Avoid corners:

| Future | How B stays compatible |
| --- | --- |
| Real observation ingestion | New adapters call ObservationAuthority, not remember |
| External tools / multiple providers | Each provider is an issuer identity on the grant |
| Provenance chains | `derived_from` already exists; grants for facts; derived kinds stay non-FACTUAL_PREMISE |
| Contradiction / temporal / entity | Remain at bind/reason |
| Causal / experiment / learning / agents | Loop write-back still uses remember for **non-fact** kinds; facts still granted |
| Domain adapters | Replace raw `ingest_generic_observation` → remember with issuer.issue_then_persist |

Do not add world model, NLI, NER, or autonomous evolution in this design.

---

## 17. Governance and trust zones

```
Z0 Untrusted caller input
    → validate_new_record (VALID DATA)
Z1 Validated data
    → ObservationAuthority.issue  [explicit authorization]
Z2 Provenance-bound observation (grant + non-UNKNOWN source + observed_at)
    → remember with grant  [explicit authorization]
Z3 Authorized factual evidence (persisted OBSERVED_FACT under grant)
    → retrieve (not an authority upgrade)
    → bind FACTUAL_PREMISE if temporal/applicability/support  [consumption, recomputed]
Z4 Derived/reasoned knowledge (verdict, episode INFERENCE log)
    → reusable_writeback_permitted  [explicit authorization]
Z5 Reusable knowledge (HYP/LESSON/SEMANTIC INFERENCE)
    → later retrieve: FORBIDDEN as FACTUAL_PREMISE
```

| Transition | Requires explicit authorization? |
| --- | --- |
| Z0→Z1 | Validation only |
| Z1→Z2 | **Yes — ObservationAuthority** |
| Z2→Z3 | **Yes — remember+grant verify** |
| Z3→FACTUAL_PREMISE role | Consumption recompute (not a write grant) |
| Z3/Z4→Z5 | **Yes — reusable_writeback_permitted** |
| Z5→Z3 | **FORBIDDEN** |
| Z1 non-fact → persist | No extra grant (`remember` non-FACT_KINDS) |
| accept SEMANTIC | Not Z3; follow-on label policy |
| propose JSONL | Not Z3 |

---

## 18. Test design (must exist before implementation is complete)

Do not add these tests in this task. They are the future gate.

For each: attacker = in-process caller with public APIs only (no monkeypatch of ObservationAuthority internals except where the test *is* the issuer).

| Test | Attacker | Expected | Invariant | Store? | Retrieve? | Factual evidence? | Write-back? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Direct forged OBSERVED_FACT via remember, no grant | remember kwargs | **REJECTED** | no grant → no Z3 | no | no | no | no |
| UNKNOWN provenance grant request | issuer.issue(source_id=UNKNOWN) | **REJECTED** | UNKNOWN ≠ evidence | no | no | no | no |
| Nonexistent source_id string (non-UNKNOWN) | issuer + remember | **ACCEPTED as provenance string** | no registry; not a truth oracle | yes | yes | maybe (bind) | if P5 allows |
| Forged source_type AI_MODEL + OBSERVED_FACT | remember/issue | **REJECTED** | existing AI veto | no | no | no | no |
| Forged grant HMAC / wrong statement hash | remember(grant=tampered) | **REJECTED** | grant binding | no | no | no | no |
| Replayed grant on different statement | remember | **REJECTED** | hash bind | no | no | no | no |
| Expired valid_until at issue | issuer | **REJECTED** | §5 write | no | no | no | no |
| Insert ACTIVE with past valid_until if somehow stored | bind | not FACTUAL_PREMISE | §5 bind | maybe | yes | **no** | no |
| Future observed_at | issuer | **REJECTED** | no future facts | no | no | no | no |
| Empty statement | remember/issue | **REJECTED** | existing | no | no | no | no |
| Forged polarity / support class on DTO | mutate binding | FrozenInstanceError / live recompute | P5 | n/a | n/a | no extra | no extra |
| Forged confidence 1.0 with grant | remember | store; type not from confidence | confidence ≠ truth | yes | yes | per bind | per P5 |
| Entity mismatch statement with grant | remember+run | stored; not task-supporting | entity at bind | yes | yes | not for that task | no |
| Scope mismatch | same | not applicable / not supporting | applicability at bind | yes | yes | no | no |
| Contradiction two granted facts | run | not positive | episode policy | yes | yes | yes as items | no |
| Stale status | revise STALE | not FACTUAL_PREMISE | temporal | yes | yes | no | no |
| Replayed observation same grant nonce | second remember | **REJECTED** | single-use/nonce | first only | first | first | per P5 |
| Mutate statement after grant (`revise`) | revise | demote or regrant | TOCTOU | revision yes | yes | **no** as OBSERVED_FACT if demoted | no from that row as fact |
| Direct propose() | propose | JSONL only | §9 | hyp file | no memory | no | no |
| Direct accept() | accept | SEMANTIC non-fact | §10 | yes | yes | no | no |
| Two-hop / three-hop | copy derived | not FACTUAL_PREMISE | existing | yes | yes | no | no |
| Fresh reasoning after malicious insertion without grant | remember+run | remember fails; empty/non-fact context | chain break | no | no | no | no |
| Legitimate adapter ingest with grant | issuer+remember+run | may FACTUAL_PREMISE | no regression of real ingest | yes | yes | if support | if P5 |
| Synthetic test grant labeled SYNTHETIC_TEST_DATA | test issuer | allowed in tests | data_label | yes | yes | yes in tests | yes in tests |
| record_failure OBSERVED_FACT kind | internal | FAILURE typed_class, not FACTUAL_PREMISE | type wins | yes | yes | no | n/a |

Existing P5 A–AQ, mutation, two-hop, three-hop, freeze, soak, forensic gate files remain green.

---

## 19. Regression requirements (future implementation)

Must preserve: second-forensic protections; authorization-boundary *consumption* tests that non-facts cannot factify; Lane A 36/36; soak untouched; `P5_FORENSIC_ARCHITECTURE_GATE.md` unchanged; legitimate hypothesis JSONL; no new production bypass; no silent escalation.

Tests that today **document the gap** by asserting `remember(OBSERVED_FACT)` **succeeds** and authorizes (`test_consumption_remembered_observed_fact_is_factual_premise`, `test_direct_bypass_false_claim_via_remember_then_second_hop`, `test_lexical_retriever_without_failure_intent_consumes_forged_fact`, `test_forged_temporal_valid_until_does_not_mark_stale_on_insert`) **must invert** on implementation: ungranted remember **REJECTED**; granted+expired valid_until **not** FACTUAL_PREMISE. That is a planned test flip, not silent weakening.

---

## 20. Future implementation specification (do not implement)

### Boundary location

- `CognitiveMemoryStore.remember`: if `EpistemicKind(epistemic_kind) in FACT_KINDS` and `MemoryType` is not handled as FAILURE-typed (see below), require `observation_grant` and verify.  
- `ObservationAuthority.issue(...)` in a new module under `architecture/cognitive/memory/` (Lane B only).  
- `bind_item` / `live_temporal_state`: consult `valid_until`/`expires_at` from store when present.  
- `revise` / `supersede`: §13.

### Trusted callers (grant mint)

- ObservationAuthority only.  
- Domain adapters call the authority, not raw FACT remember.  
- Benchmark corpus / tests: `issue_synthetic(..., data_label=SYNTHETIC_TEST_DATA)`.  
- `record_failure`: keep FAILURE memory_type; **prefer** changing kind off OBSERVED_FACT in a later patch, or an internal grant scoped to FAILURE so typed_class remains FAILURE. Minimum: FAILURE+OBSERVED_FACT remains non-FACTUAL_PREMISE (**PROVEN** type wins) but should not be a back door to FACTUAL_PREMISE if `typed_class_from_parts` ever changes — pin a test.

### Untrusted callers

- Any other in-process module calling `remember(..., epistemic_kind=OBSERVED_FACT)` without a grant.  
- Direct construction of grant bytes without HMAC.

### Input contract

Issue requires: statement, source_type ∈ {SENSOR,SYSTEM,DATABASE,HUMAN}, source_id not UNKNOWN_FIELD, source_location, producer, producer_version, observed_at ≤ now, valid_until is None or > now, kind ∈ FACT_KINDS.  
Remember(FACT) requires: that grant, matching statement hash, matching source_id/observed_at/kind.

### Authority object

Frozen `ObservationGrant`: issuer_id, issued_at, nonce, kind, statement_sha256, source_type, source_id, observed_at, hmac. HMAC key: process-local, held by ObservationAuthority, not passed in caller kwargs.

### Invariants

- No FACT_KINDS persist without valid grant.  
- Grant mismatch → reject, no row.  
- UNKNOWN provenance ↛ FACT_KINDS.  
- Expired valid_until ↛ FACTUAL_PREMISE at bind.  
- Non-facts still cannot FACTUAL_PREMISE.  
- Reusable write-back unchanged.  
- Retrieval unchanged (no redesign).

### Rejection conditions

Missing/invalid grant; hash mismatch; UNKNOWN provenance on facts; AI_MODEL/AGENT (existing); empty statement; future observed_at; expired valid_until at issue; replayed nonce.

### Storage / retrieval / binding / reasoning / write-back

Storage: append-only as now, plus payload or columns for grant nonce (payload is enough to avoid schema fight; schema add is optional later).  
Retrieval: unchanged.  
Binding: + expiry consult; still live support.  
Reasoning: unchanged.  
Write-back: still non-FACT kinds via remember **without** fact grant.

### Migration / compatibility / rollback

- Call sites of FACT remember: adapters, `benchmark/corpus.py`, `evaluator.py`, `p5_eval.py`, tests listed in grep.  
- No Lane A. No soak migration.  
- Rollback: revert the remember check and authority module; grants unused.  
- Backward compatibility: old DBs may contain ungranted OBSERVED_FACT rows. **UNRESOLVED policy:** (i) read-only grandfather as DATED facts (leaves historical bypass in data), or (ii) consume pre-grant facts as INFERENCE/UNKNOWN until re-granted. **Recommend (ii) fail-closed for FACTUAL_PREMISE if payload lacks grant nonce**, so old forged rows cannot keep authorizing. Benchmarks always rewrite tmp stores.

### Security / regression tests

§18 plus existing P5 envelope, freeze 36/36, validate_imports, full pytest.

---

## 21. Files / code changes this task

| Allowed | Done |
| --- | --- |
| Inspect repo / tests / call graph | Yes |
| Exactly one design report | This file |
| Production / tests / API / schema / Lane A / soak / other docs | **Not done** |

---

## 22. Proof standard notes

Unresolved items (explicit):

1. Same-process HMAC key extraction / monkeypatch of `remember` — out of ordinary-caller threat model.  
2. Pre-existing DB rows without grant nonce — recommend fail-closed FACTUAL_PREMISE until re-granted; not proven in code because not implemented.  
3. Future `observed_at` — no current test; specified reject at issue.  
4. Whether DERIVED_FACT must require a grant: **not** the proven bypass (roles forbid FACTUAL_PREMISE). Spec still includes FACT_KINDS to avoid a second door. Alternative minimum is OBSERVED_FACT-only grants; **UNRESOLVED which is smaller vs safer** — recommendation: both FACT_KINDS.

---

## 23. Final decision

### ARCHITECTURE-DESIGN = VALID

The minimum boundary is internally consistent with proven code: consumption already refuses non-fact → fact; write currently treats OBSERVED_FACT as a caller label; Option B severs that label from ordinary `remember` without renaming the bypass; `propose`/`accept` need not move for fact authority; temporal expiry belongs at grant + bind; entity/polarity stay recomputed; TOCTOU on `revise` is specified.

`RECOMMENDED_OPTION: B`

`CODE_CHANGES_ALLOWED: NO`

`IMPLEMENTATION_AUTHORIZED: NO`

`MERGE: NO`

`READY_FOR_REVIEW: NO`

`LANE_A_STATUS: UNTOUCHED`

`SOAK_STATUS: UNTOUCHED`

`REPORT: reports/agi_aci_evolution/P5_MEMORY_AUTHORIZATION_BOUNDARY_ARCHITECTURE_DESIGN.md`

`AUDITED_SHA: 38247d172319741f5df7bd6e01ba2817bf211def`

STOP. Do not implement. Do not merge PR #93. Do not mark ready. Do not modify forensic reports.
