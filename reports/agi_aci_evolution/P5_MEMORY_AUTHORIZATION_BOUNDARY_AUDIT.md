# P5 Memory Authorization Boundary Audit

**Kind:** Architectural decision / forensic proof. Not a feature. Not a fix.  
**PR:** [#93](https://github.com/mainmovement/ahos/pull/93) — **DRAFT. MERGE = NO. READY_FOR_REVIEW = NO.**  
**Data label:** `SYNTHETIC_TEST_DATA`  
**This is not entailment, NER, AGI, or ACI.**

Original `reports/agi_aci_evolution/P5_FORENSIC_ARCHITECTURE_GATE.md` is **unchanged** (`02c41be569798568909e336f4b2277dc84b79dfe`).

---

## 1. Exact audited SHA

| Field | Value |
| --- | --- |
| Branch | `cursor/agi-aci-p5-typed-evidence-reasoning-9500` |
| Audited production HEAD | `1a7e5e74a016da7b8d7aed65a4049c4f2a727e12` |
| Previous production start | `f0d2c4ee7233f1ee0fc09c9245b6c449c0027638` |
| Proof tests + this report | `fedecd6c590bcf8a01f15a08e2a9306ada807980` |

---

## 2. PR state

**DRAFT.** MERGE = NO. READY_FOR_REVIEW = NO. Base `main`.

---

## 3. Three API write-path maps

### 3.1 `CognitiveMemoryStore.remember`

```
CALLER (any in-process Python)
  → remember(memory_type, epistemic_kind, statement, source_*, …)
  → INPUT: any MemoryType × EpistemicKind (FACTUAL_PREMISE is not a kind → ValueError)
  → VALIDATION: validate_new_record
        statement non-empty
        enums
        provenance tokens non-empty (literal "UNKNOWN" is allowed)
        AI_MODEL/AGENT ↛ OBSERVED_FACT/DERIVED_FACT
        WORKING TTL
        confidence in [0,1] or None
  → PROVENANCE CHECK: presence only, not authenticity
  → EPISTEMIC CHECK: enum + AI veto only; caller chooses kind
  → CONTRADICTION CHECK: none (status UNCONTESTED)
  → TEMPORAL CHECK: none; status always ACTIVE on insert; valid_until not applied
  → ENTITY/SCOPE CHECK: none
  → CONFIDENCE HANDLING: stored; not used as truth; out-of-range rejected
  → STORAGE: append-only SQLite memories row
  → RETRIEVAL: MemoryRetriever over CognitiveMemoryStore
        exact_id (requested_evidence) is a structured anchor
        lexical retrieve can accept OBSERVED_FACT when FAILURE/LESSON intents are absent
        question token "failures" → UNRELATED_FAILURE for unanchored non-FAILURE rows
  → CONSUMPTION: typed_class_from_parts + live roles
        OBSERVED_FACT + DATED/AGING/CURRENT + applicable → FACTUAL_PREMISE + DIRECT
        HYP/LESSON/INFERENCE/PREDICTION/OPINION/SIMULATION → FACTUAL_PREMISE forbidden
```

**Can independently create**

| Type | Create? | Later consumable by reasoning? |
| --- | --- | --- |
| OBSERVED_FACT | **YES** | **YES as FACTUAL_PREMISE / DIRECT** (if fresh enough and task-supporting) |
| FACTUAL_PREMISE | NO (not a stored kind) | N/A |
| HYPOTHESIS | YES | Retrieved as HYPOTHESIS; not FACTUAL_PREMISE |
| LESSON | YES | Retrieved as LESSON; ROLE_CONSTRAINT if applicable; not FACTUAL_PREMISE |
| INFERENCE | YES | Retrieved as INFERENCE; not FACTUAL_PREMISE |
| EPISODIC | YES (memory_type) | Consumable as whatever epistemic_kind was stored |

**Classification for remember:** **C** for OBSERVED_FACT/DERIVED_FACT (true epistemic write-authority for evidence). **A** for non-fact kinds (stored-but-nonreusable as facts). Overall API: **C**.

### 3.2 `HypothesisStore.propose`

```
CALLER (any in-process Python)
  → propose(statement, domain=, provenance=, now=)
  → INPUT: non-empty statement; optional provenance dict (unchecked)
  → VALIDATION: statement.strip() non-empty
  → PROVENANCE / EPISTEMIC / CONTRADICTION / TEMPORAL / ENTITY / CONFIDENCE: none
  → STORAGE: JSONL append, state=PROPOSED, id HYP-NNNNNN
  → RETRIEVAL: MemoryRetriever does **not** read this file
  → CONSUMPTION: P5 reason/bind never see propose()-only rows
```

Orchestrator copies a hypothesis into `memory.remember(HYPOTHESIS)` only after `reusable_writeback_permitted`. Direct `propose()` does not perform that copy.

**Classification for propose:** **A** — explicitly labeled hypothesis ledger, not P5 evidence authorization. Persisted ≠ retrieved ≠ fact.

### 3.3 `ConsolidationGate.accept`

```
CALLER (any in-process Python)
  → accept(store, candidate, actor=, epistemic_kind=, producer=)
  → INPUT: ConsolidationCandidate (public dataclass; propose_from_episodes is optional)
  → VALIDATION: actor non-empty; epistemic_kind not OBSERVED_FACT/DERIVED_FACT
  → PROVENANCE: hardcoded SYSTEM / consolidation_gate; derived_from copied, not verified to exist
  → EPISTEMIC: caller-chosen kind; **not** forced to candidate.proposed_kind
  → CONTRADICTION / TEMPORAL / ENTITY / CONFIDENCE: none
  → requires_human on candidate is **not enforced** (any non-empty actor string works)
  → STORAGE: remember(SEMANTIC, kind)
  → RETRIEVAL/CONSUMPTION: as SEMANTIC + chosen kind; cannot be FACTUAL_PREMISE
```

`propose_from_episodes` only suggests INFERENCE (or OPINION/SIMULATION if sources are AI_MODEL/OPINION/SIMULATION) and always sets `requires_human=True`. `accept` does not re-run that policy.

**Classification for accept:** **A** for factification (cannot mint OBSERVED_FACT). It **is** a weak SEMANTIC promotion API (EPISODIC → LESSON/INFERENCE/HYPOTHESIS labels) whose outputs remain **STORED-BUT-NONREUSABLE as facts**. Not an independent fact-authorization boundary.

---

## 4. Semantic authorization results

Isolated store. Production APIs only. Verdicts: **ACCEPTED** (stored and authorizing as evidence), **REJECTED** (raise), **STORED-BUT-NONREUSABLE** (persisted, cannot be FACTUAL_PREMISE / cannot yield positive verdict alone).

| # | Attempt | remember | propose | accept |
| --- | --- | --- | --- | --- |
| 1 | arbitrary OBSERVED_FACT | **ACCEPTED** (authorizing) | n/a (no fact kind) | **REJECTED** EpistemicViolation |
| 2 | arbitrary FACTUAL_PREMISE | **REJECTED** (not an EpistemicKind) | n/a | n/a |
| 3 | arbitrary HYPOTHESIS | STORED-BUT-NONREUSABLE | STORED in JSONL, **not retrieved** | STORED-BUT-NONREUSABLE (SEMANTIC HYPOTHESIS) |
| 4 | arbitrary LESSON | STORED-BUT-NONREUSABLE | n/a | STORED-BUT-NONREUSABLE |
| 5 | arbitrary INFERENCE | STORED-BUT-NONREUSABLE | n/a | STORED-BUT-NONREUSABLE |
| 6 | assumption / uncertain clause | STORED; consumption not positive | JSONL only | SEMANTIC non-fact |
| 7 | prediction content | STORED-BUT-NONREUSABLE | n/a | allowed kind, non-fact |
| 8 | opinion content | STORED-BUT-NONREUSABLE | n/a | allowed kind, non-fact |
| 9 | simulation content | STORED-BUT-NONREUSABLE | n/a | allowed kind, non-fact |
| 10 | unresolved contradiction (two OBSERVED_FACTs) | both ACCEPTED as facts; episode policy **not positive** | n/a | n/a |
| 11 | stale (revise STALE after remember) | stored; **not** FACTUAL_PREMISE | n/a | n/a |
| 12 | entity mismatch statement | stored OBSERVED_FACT; **not** task-supporting | n/a | n/a |
| 13 | forged provenance (`UNKNOWN` tokens) | **ACCEPTED** | provenance dict unchecked | actor string only |
| 14 | forged confidence `1.0` | **ACCEPTED** (in range); type unchanged. `1.5` **REJECTED** | n/a | n/a |
| 15 | forged temporal (`valid_until` in the past) | **ACCEPTED**, status still ACTIVE, still FACTUAL_PREMISE | n/a | n/a |
| — | missing `observed_at` | stored; UNKNOWN_AGE; **not** FACTUAL_PREMISE | n/a | n/a |
| — | AI_MODEL + OBSERVED_FACT | **REJECTED** | n/a | n/a |
| — | empty actor / empty statement | n/a | **REJECTED** | **REJECTED** |

**Do not interpret stored as authorized.** Rows 3–9 are stored and non-authorizing as facts. Row 1 is stored **and** authorizing.

---

## 5. Consumption-side results

Production path: `MemoryRetriever.retrieve` → `assemble_context` → `bind_context` → `reason` → `CognitiveOrchestrator.run`.

| Inserted artifact | Retrieved type | Consumed role | Positive verdict? | Reusable write-back? |
| --- | --- | --- | --- | --- |
| remember OBSERVED_FACT + supporting statement + `requested_evidence` | OBSERVED_FACT, evidence_class DIRECT_OBSERVATION | FACTUAL_PREMISE, support_strength DIRECT, support_class DIRECT_SUPPORT | **YES** | **YES** (HYP/LESSON/INFERENCE) |
| same, lexical retrieve, question contains "failures" | **not retrieved** (UNRELATED_FAILURE) | — | no (empty context) | no |
| same, lexical retrieve, "Do retries after timeout help?" | OBSERVED_FACT | FACTUAL_PREMISE | **YES** | **YES** |
| remember HYPOTHESIS / LESSON / INFERENCE / PREDICTION / OPINION / SIMULATION / EPISODIC INFERENCE | same kind | not FACTUAL_PREMISE, not DIRECT | **NO** | **NO** extra reusable mint |
| propose() only | not in store | none | **NO** | **NO** |
| accept() LESSON/HYPOTHESIS | LESSON/HYPOTHESIS | not FACTUAL_PREMISE | **NO** | **NO** |

**STORAGE ≠ AUTHORIZATION** is **true for non-fact kinds, propose(), and accept()**.

**STORAGE ≠ AUTHORIZATION is FALSE for remember(OBSERVED_FACT)** when the row is retrieved (structured id **or** lexical without FAILURE-intent). Retrieval does not retype kinds (RETRIEVAL ≠ FACTIFICATION for HYP→FACT). Retrieval **does** expose caller-chosen OBSERVED_FACT as DIRECT_OBSERVATION. That is not silent metadata promotion; it is **honoring the stored kind**. The authority leak is at **write**, not a retrieval retype.

---

## 6. Authority escalation matrix

SOURCE (stored epistemic_kind / type) → RETRIEVED typed_class → CONSUMED ROLE

| Stored | Retrieved typed_class | FACTUAL_PREMISE | DIRECT strength | Becomes OBSERVED_FACT? |
| --- | --- | --- | --- | --- |
| OBSERVED_FACT (ACTIVE, observed_at set) | OBSERVED_FACT | yes if applicable | DIRECT | already fact |
| HYPOTHESIS | HYPOTHESIS | no | no | **no** |
| LESSON | LESSON | no | no | **no** |
| INFERENCE | INFERENCE | no | no | **no** |
| EPISODIC + INFERENCE | INFERENCE | no | no (INDIRECT) | **no** |
| PREDICTION | PREDICTION | no | no | **no** |
| OPINION | OPINION | no | no | **no** |
| SIMULATION | SIMULATION | no | no | **no** |
| STALE OBSERVED_FACT | OBSERVED_FACT | **no** | no | stale ≠ CURRENT |
| mixed SUPPORT+CONTRA OBSERVED_FACT | both OBSERVED_FACT | polarity fail-closed | — | not SUPPORTS / not WEAKLY_SUPPORTED |
| UNKNOWN_AGE OBSERVED_FACT | OBSERVED_FACT | **no** | no | no |
| FACTUAL_PREMISE as kind | cannot store | — | — | — |
| ASSUMPTION as kind | cannot store | — | — | — |

Impossible on the **read** path (proven):

- UNKNOWN → FACT (empty/unknown-age does not get FACTUAL_PREMISE)
- HYPOTHESIS / LESSON / INFERENCE → OBSERVED_FACT
- EPISODIC INFERENCE → DIRECT / FACTUAL_PREMISE
- PREDICTION / OPINION / SIMULATION → FACTUAL_PREMISE
- STALE → FACTUAL_PREMISE
- CONTRADICTORY pair → WEAKLY_SUPPORTED

**Possible on the write path:** caller stores OBSERVED_FACT. That is not hop-escalation; it is **minting the first hop as fact**.

---

## 7. Direct bypass attack

Attacker/developer calls public APIs **without** `CognitiveOrchestrator.run` for the write, then runs a fresh task.

### 7.1 `remember(OBSERVED_FACT, supporting statement)`

1. Enter memory? **YES**  
2. Retrieved? **YES** if `requested_evidence` (public task field) or lexical without FAILURE intent  
3. Epistemic type returned? **OBSERVED_FACT**  
4. Become evidence? **YES** (DIRECT_OBSERVATION)  
5. Support a task? **YES** if statement classifies as DIRECT_SUPPORT  
6. Contribute to WEAKLY_SUPPORTED / SUPPORTED? **YES**  
7. Create HYPOTHESIS / LESSON / INFERENCE? **YES**, via subsequent orchestrator write-back  
8. Survive hop 2/3 as fact? **NO** — derived HYP/LESSON/INFERENCE cannot retype to OBSERVED_FACT / FACTUAL_PREMISE  

**This is a true epistemic write-authority gap** for observation-class evidence. Not a security exploit. It is the public storage API acting as fact ingest with no P5 critic.

### 7.2 `propose(supporting statement)`

1. Enters hypothesis JSONL only  
2. Not retrieved  
3. No type in P5 context  
4–8. Cannot become evidence, support, WEAKLY_SUPPORTED, or mint loop artifacts  

### 7.3 `accept(...)` with forged `ConsolidationCandidate` (skip `propose_from_episodes`)

1. Enters SEMANTIC HYPOTHESIS/LESSON/INFERENCE  
2. Retrieved as that kind  
3–8. Cannot FACTUAL_PREMISE, cannot positive verdict, cannot extra reusable fact-backed write-back  
Also: `accept` may store LESSON even when `proposed_kind` was INFERENCE; `requires_human=False` on a forged candidate is ignored except the actor string.

---

## 8. Provenance preservation

| Field | Write | Retrieve | Bind / reason |
| --- | --- | --- | --- |
| source_id | stored as given (UNKNOWN allowed) | copied onto RetrievedItem | provenance.source_id |
| memory_id / evidence identity | assigned MEM- | same | same |
| epistemic kind | caller-chosen | copied; live_typed_class from type+kind | **not** retyped |
| polarity / support class / entity / clause force | **not stored as authority** | statement is stored | **recomputed** from statement+task |
| temporal | status ACTIVE; observed_at stored | status + observed_at | live_temporal_state; DTO temporal_state ignored |
| confidence | stored | not a bind role | does not promote type |
| scope / applicability | payload | payload via store.get | live_applicability |

Authoritative for support/polarity/entity: **statement + task**, not stored metadata.  
Authoritative for kind/roles: **store epistemic_kind + memory_type + status + observed_at**.  
Forged DTO roles cannot escalate (frozen EvidenceBinding; prior mutation suite).  
Forged **write** of OBSERVED_FACT **is** authoritative for kind.

---

## 9. ConsolidationGate analysis

Consolidation **is** an epistemic **label** promotion (EPISODIC → SEMANTIC INFERENCE/LESSON/HYPOTHESIS/OPINION/SIMULATION/PREDICTION/PROCEDURE) with:

- veto: cannot write OBSERVED_FACT or DERIVED_FACT  
- required: non-empty `actor` string  
- **not** required: real human, matching `proposed_kind`, existing source ids, non-contradictory sources, fresh sources, P5 critic, `reusable_writeback_permitted`

Contradictory/uncertain/stale/assumption-only episodes **can** be accepted into a SEMANTIC LESSON/INFERENCE. Those rows **cannot** later bind as FACTUAL_PREMISE. So consolidation is **not** a fact-promotion mechanism and **is** a weakly governed reusable-**label** mint.

---

## 10. HypothesisStore analysis

`propose()` means **store an explicitly labeled hypothesis** (state PROPOSED) in JSONL. It does **not** authorize a reusable P5 cognitive artifact. Downstream P5 consumers never see it unless something also `remember`s a HYPOTHESIS row. When that row exists, consumption preserves HYPOTHESIS (no FACTUAL_PREMISE). `SUPPORTED` on the JSONL record still requires `experiment_id` (separate lifecycle). Persisted ≠ validated ≠ retrieved.

---

## 11. Architectural classification

**BOUNDARY-GAP = PROVEN**

Not because retrieval silently factifies HYP/LESSON/INFERENCE (it does not).  
Because **`remember` independently mints OBSERVED_FACT that production retrieve+reason treat as FACTUAL_PREMISE and that can authorize WEAKLY_SUPPORTED plus orchestrator reusable write-back.**

`propose` and `accept` are not fact-authorizing. Treating them as “currently unused therefore safe” is refused: they are public; tests call them; `accept` can mint SEMANTIC labels; consumption still will not factify those labels.

P5 live-path mixed-polarity / critic / hop protections remain intact **after** evidence exists. They do not govern **who may declare evidence**.

---

## 12. Minimum safe change (proposal only — NOT IMPLEMENTED)

Single clear authorization boundary:

1. **Split write APIs by authority class**  
   - Observation ingest: a dedicated `record_observation(...)` (or capability token) as the **only** writer of OBSERVED_FACT / DERIVED_FACT. Require `observed_at`, forbid `source_id=UNKNOWN` (or require SENSOR/SYSTEM/HUMAN with a real source_id).  
   - `remember(...)` refuses FACT_KINDS (or requires the same token).  
2. **Keep** consumption-side typing (already prevents HYP→FACT).  
3. **`propose`** stays a labeled ledger; do not auto-insert into CognitiveMemoryStore.  
4. **`accept`** must (minimum): refuse kinds other than `candidate.proposed_kind`; require non-empty existing `derived_from`; re-run source-kind policy; do not treat actor string as human governance. Still must not write OBSERVED_FACT.

Do **not** redesign retrieval. Do **not** add NLI/NER/embeddings.

**IMPLEMENTATION = NOT AUTHORIZED** in this audit.

---

## 13. P5 regression analysis

A future governance wrap of `remember` for FACT_KINDS would preserve, if it does not weaken consumption or episode policy:

| Protection | Independent of remember ingest? |
| --- | --- |
| mixed polarity | yes (episode policy on bindings) |
| uncertainty | yes |
| identity/entity | yes (statement recompute) |
| stale | yes (status STALE → no FACTUAL_PREMISE) |
| assumption-only | yes (no FACTUAL_PREMISE supporters) |
| non-decision-bearing | yes |
| critic load-bearing | yes |
| mutation/TOCTOU | yes (frozen bind + orchestrator rebind) |
| two-hop / three-hop | yes (derived kinds cannot factify) |

Closing the gap is **additive write restriction**, not a retrieval redesign.

---

## 14. Lane A

`scripts/freeze_lane_a.py` → **36/36**. No `discovery/**` or `paper_trading/**` edits.

---

## 15. Soak

Soak DBs not opened by this audit’s writers. Frozen evidence not rewritten. `P5_FORENSIC_ARCHITECTURE_GATE.md` unchanged. Untracked `reports/PRE_SOAK_STATUS.txt` / `next-env.d.ts` not committed.

---

## 16. Tests

Interpreter `/tmp/ahos-test-venv/bin/python`. `.pytest_cache` cleaned before `validate_imports`.

| Check | Result |
| --- | --- |
| `tests/test_p5_memory_authorization_boundary.py` | **23 passed** |
| `tests/test_p5_second_forensic.py` (A–AQ, seven modes, mutation, two-hop, three-hop) | **42 passed** |
| Focused P5 + boundary | **211 passed** |
| `pytest tests` | **1980 passed, 3 skipped, 0 failed** |
| `validate_imports.py` | VALIDATION PASSED |
| freeze | 36/36 |

Proof tests pin **current** authorizing behavior of `remember(OBSERVED_FACT)` (gap documentation), and pin **non**-factification of HYP/LESSON/INFERENCE/propose/accept. Thresholds were not weakened.

---

## 17. Changed files

| File | Change |
| --- | --- |
| `tests/test_p5_memory_authorization_boundary.py` | production-path authorization proof tests |
| `reports/agi_aci_evolution/P5_MEMORY_AUTHORIZATION_BOUNDARY_AUDIT.md` | this report |

No production API edits. No Lane A. No retrieval redesign.

---

## 18. Remaining limitations

- `remember` is fact-authorizing ingest for OBSERVED_FACT.  
- `valid_until` in the past does not stale on insert; bind uses `status`+`observed_at`.  
- Provenance tokens may be the literal UNKNOWN.  
- `accept` ignores `proposed_kind` / `requires_human` / source existence.  
- `propose` is a parallel ledger.  
- Typed eligibility is not entailment.  
- P4.3 FAILURE-intent lexical reject is not a substitute for write authorization (`requested_evidence` still anchors).

---

## 19. Highest justified claim

P5 consumption preserves kind: HYPOTHESIS/LESSON/INFERENCE/EPISODIC-INFERENCE/PREDICTION/OPINION/SIMULATION cannot silently become OBSERVED_FACT or FACTUAL_PREMISE. Two-hop and three-hop derived artifacts cannot factify. Critic, mixed polarity, stale, and mutation gates remain load-bearing **given** stored evidence.

`CognitiveMemoryStore.remember` is **not** a non-authorizing storage primitive for OBSERVED_FACT: a direct call can create FACTUAL_PREMISE-eligible evidence and, after a normal `CognitiveOrchestrator.run`, reusable HYP/LESSON/INFERENCE. That is a **write-authority gap**, not a retrieval retype bug.

Not AGI. Not ACI. Not production-ready. Not mergeable.

---

## 20. Merge decision

| Item | Value |
| --- | --- |
| BOUNDARY-GAP | **PROVEN** |
| CODE_CHANGES_REQUIRED | **YES** |
| IMPLEMENTATION | **NOT AUTHORIZED** |
| ARCHITECTURE_GATE | **FAIL** (authorization boundary; P5 consumption invariants still hold) |
| MERGE | **NO** |
| READY_FOR_REVIEW | **NO** |

Previous `CONDITIONALLY_CLOSED` assumed storage ≠ authorization. Consumption-side execution shows that equality **does** hold for `remember(OBSERVED_FACT)`. The P5 mixed-evidence live path remains proven **downstream of evidence**. The missing boundary is **who may write evidence**.
