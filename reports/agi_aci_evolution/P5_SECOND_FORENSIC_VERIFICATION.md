# P5 Second Forensic Verification

**Kind:** Release/security gate. Not a feature phase. Not a claim upgrade.  
**PR:** #93 (DRAFT; do not merge)  
**Data label:** `SYNTHETIC_TEST_DATA`  
**Lane A:** freeze 36/36, files not modified  
**Soak:** not touched, not restarted  
**Original gate file:** `P5_FORENSIC_ARCHITECTURE_GATE.md` **unchanged**

This is not entailment, NER, AGI, or ACI.

Honest capability: governed typed eligibility + closed-lexicon support classification + live-recomputed EvidenceBinding + episode mixed-polarity policy + critic constraint + write-back invariant below `CognitiveOrchestrator.run`.

---

## 1. Exact audited SHA

| Field | Value |
| --- | --- |
| Branch | `cursor/agi-aci-p5-typed-evidence-reasoning-9500` |
| Integrity hardening + forensic tests | `93dc6d8a2f59d514e49954c9253e23cbbdb4fc24` |
| This report commit | `1244fd60b533a7b83bbf4be4c4d855c6e306d602` |

The production tree to audit is HEAD of this branch after this report lands.

---

## 2. Scope

Prove that unresolved contradictory, uncertain, identity/entity-incompatible, stale, assumption-only, or non-decision-bearing evidence cannot mint reusable `HYPOTHESIS` / `LESSON` / `INFERENCE` on any live P5/P3 reason/write-back path.

Out of scope: retrieval redesign, Lane A, soak, calibration, original forensic rewrite, AGI features.

---

## 3. Architecture path (live)

```
MemoryRetriever.retrieve
  → assemble_context                    # contradiction_present = graph edges only
  → bind_context / bind_item            # EvidenceBinding; live class/temporal/roles/support
  → MODE_FNS[mode]                      # candidate; eligibility templates, not formal operators
  → critique_result / _inspect          # critic findings
  → apply_constraint                    # load-bearing on action
  → apply_episode_positive_policy       # mixed polarity/uncertainty; strip non-supporters
  → reason() returns verdict + trace.reusable_writeback
  → CognitiveOrchestrator.run
       bind_context(ctx, task) AGAIN    # ignores mutated reason() DTOs
       reusable_writeback_permitted(verdict, fresh_bindings)
       HYPOTHESIS / LESSON / SEMANTIC INFERENCE only if True
       EPISODIC "episode {id} {verdict}" if write_back (allowed for unresolved)
```

Separation (still distinct):

| Layer | Question |
| --- | --- |
| Retrieval | lexical/structured candidate? |
| `addresses_task` | lexical overlap? |
| `classify_support` / `may_support_task` | closed-lexicon support? |
| `may(FACTUAL_PREMISE)` | decision-eligible typed/temporal/applicability? |
| `reusable_writeback_permitted` | may mint reusable knowledge? |

---

## 4. Root-cause status

Original C1 (mixed SUPPORTS+CONTRADICTS, no graph edge → WEAKLY + reusable mint): **CLOSED** on the live path.

This verification found residual **stored-metadata escalation** holes and closed them:

- `may()` trusted copied role tuples → now `live_roles()` from memory_type, epistemic_kind, status, observed_at, payload, task snapshot.
- Uncertain detection trusted `clause_force` / `addresses_task_flag` → now `is_task_relevant_uncertain()` from statement+task.
- `temporal_state` field mutation could claim CURRENT → ignored; `temporal_from_parts(status, observed_at)`.
- Critic `DOWNGRADE` of temporal/scope on WEAKLY left positivity intact → now INSUFFICIENT.

Orchestrator write-back already rebound from `RetrievedItem`s; that remains the persistence boundary.

---

## 5. Write-back boundary analysis

`reusable_writeback_permitted` callers in production:

| Caller | File | Governed? |
| --- | --- | --- |
| `CognitiveOrchestrator.run` | `orchestrator.py` | YES — only persistence of reusable HYP/LESSON/INFERENCE |
| `reason()` trace field | `reason.py` | YES — advisory; orchestrator does not trust it alone |

Independent enforcement at the **final write-back rebind**:

| ID | Case | Binding | Candidate | Critic | Final | permitted | HYP | LESSON | INF | EPISODE | Re-ingest risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | mixed + CONTRADICTS, no edge | support+contra live | CONTESTED/UNRESOLVED | CONTEST | not WEAKLY | False | 0 | 0 | 0 | 1 if wb=True | episode is INFERENCE, not FACT |
| B | SUPPORTS+UNCERTAIN | live uncertain | UNRESOLVED/non-pos | contest/mismatch | not WEAKLY | False | 0 | 0 | 0 | 1 | none |
| C–F | identity/entity mismatch/scoped/ambiguous | mismatch not `may_support_task` | INSUFFICIENT unless MATCH coexists | — | mismatch cannot mint | False if only mismatch | 0 | 0 | 0 | 1 | MATCH coexists: reusable from MATCH only |
| G–J | stale/superseded/historical/unknown-age | no FACTUAL_PREMISE | INSUFFICIENT | — | not WEAKLY | False | 0 | 0 | 0 | 1 | none |
| K | assumption-only | no bindings | INSUFFICIENT | REQUIRE_MORE | not WEAKLY | False | 0 | 0 | 0 | 1 | ASM not retrieved as fact |
| L | non-decision-bearing | lexical/META inventory | INSUFFICIENT | ACCEPT/REFUSE | not WEAKLY | False | 0 | 0 | 0 | 1 | none |
| M | prediction/opinion/simulation | not FACTUAL_PREMISE | INSUFFICIENT | type path | not WEAKLY | False | 0 | 0 | 0 | 1 | none |
| N | unbound citation | forged ids | WEAKLY forged | REFUSE | INSUFFICIENT | False | — | — | — | — | n/a |
| O | irrelevant citation | sky | WEAKLY forged | REFUSE | INSUFFICIENT | False | — | — | — | — | n/a |
| P | lexical without support | addresses_task True, support False | INSUFFICIENT | — | not WEAKLY | False | 0 | 0 | 0 | 1 | none |
| Q | unsupported conclusion | no supporter | INSUFFICIENT | REQUIRE_MORE/REFUSE | not WEAKLY | False | 0 | 0 | 0 | 1 | none |
| R | graph CONTRADICTS edge | CONTESTED bindings | UNRESOLVED | CONTEST | not WEAKLY | False | 0 | 0 | 0 | 1 | none |
| S | mixed no edge | same as A | UNRESOLVED | CONTEST mixed_polarity | not WEAKLY | False | 0 | 0 | 0 | 1 | none |

`write_back=False`: hyp=lesson=inf=episode=0 even on clean SUPPORTS.

EPISODIC records of unresolved episodes are **allowed**. They are `memory_type=EPISODIC`, `epistemic_kind=INFERENCE`, statement `episode {task_id} {verdict}`. They must not become OBSERVED_FACT on retrieval (two-hop PROVEN).

---

## 6. A–AQ matrix

Executed in `tests/test_p5_episode_polarity.py` (A–M) and `tests/test_p5_second_forensic.py` (N–AQ, modes, mutation, two-hop). Focused: **56 passed**.

| CASE | FINAL VERDICT | WRITEBACK | HYP | LESSON | INF | EPISODE (wb=True) | RETRIEVABLE REUSE RISK | PASS/FAIL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A SUPPORTS only | WEAKLY | True | ≥1 | ≥1 | ≥1 | 1 | intended reusable | PASS |
| B CONTRADICTS only | CONTESTED | False | 0 | 0 | 0 | 1 | none | PASS |
| C mixed no edge | UNRESOLVED/CONTESTED | False | 0 | 0 | 0 | 1 | episode ≠ fact | PASS |
| D mixed + edge | UNRESOLVED/CONTESTED | False | 0 | 0 | 0 | 1 | none | PASS |
| E SUPPORTS+UNCERTAIN | not WEAKLY | False | 0 | 0 | 0 | 1 | none | PASS |
| F SUPPORTS+MISMATCH | WEAKLY from MATCH | True | ≥1 | ≥1 | ≥1 | 1 | mismatch not cited | PASS |
| G META cafeteria+support | WEAKLY cites support only | True if support | — | — | — | — | cafeteria not cited | PASS |
| H polarity mutation | Frozen + recompute | n/a | — | — | — | — | stored polarity ignored | PASS |
| I Did question | WEAKLY | True | — | — | — | — | not identity | PASS |
| J Can question | WEAKLY | True | — | — | — | — | not identity | PASS |
| K entity-scoped vs NONE | not WEAKLY | False | 0 | 0 | 0 | 1 | none | PASS |
| L assumption-only | INSUFFICIENT | False | 0 | 0 | 0 | 1 | ASM not evidence | PASS |
| M stale-only | not WEAKLY | False | 0 | 0 | 0 | 1 | none | PASS |
| N mixed no edge wb=True | not WEAKLY | False | 0 | 0 | 0 | 1 | none | PASS |
| O mixed edge wb=True | not WEAKLY | False | 0 | 0 | 0 | 1 | none | PASS |
| P SUPPORTS+UNCERTAIN wb=True | not WEAKLY | False | 0 | 0 | 0 | 1 | none | PASS |
| Q support+MISMATCH | WEAKLY MATCH | True | ≥1 | ≥1 | ≥1 | 1 | mismatch not basis | PASS |
| R support+AMBIGUOUS | WEAKLY MATCH | True | — | — | — | — | ambiguous not cited | PASS |
| S scoped vs NONE | not WEAKLY | False | 0 | 0 | 0 | 1 | none | PASS |
| T stale-only | not WEAKLY | False | 0 | 0 | 0 | 1 | none | PASS |
| U stale+fresh | WEAKLY fresh | True | — | — | — | — | stale not in premises | PASS |
| V superseded-only | not WEAKLY | False | 0 | — | — | — | none | PASS |
| W assumption-only | INSUFFICIENT | False | 0 | 0 | 0 | 1 | none | PASS |
| X prediction-only | not WEAKLY | False | 0 | 0 | 0 | 1 | none | PASS |
| Y opinion-only | not WEAKLY | False | 0 | 0 | 0 | 1 | none | PASS |
| Z simulation-only | not WEAKLY | False | 0 | 0 | 0 | 1 | none | PASS |
| AA unbound citation | INSUFFICIENT | False | — | — | — | — | REFUSE | PASS |
| AB irrelevant citation | INSUFFICIENT | False | — | — | — | — | REFUSE | PASS |
| AC lexical non-support | INSUFFICIENT | False | — | — | — | — | none | PASS |
| AD polarity mutate | still contradicts | n/a | — | — | — | — | ignored | PASS |
| AE statement mutate | DTO follows statement; orch rebinds original | False on CONTRA store | 0 | 0 | 0 | 1 | write-back uses item text | PASS |
| AF Did | WEAKLY | True | — | — | — | — | not ID | PASS |
| AG Can | WEAKLY | True | — | — | — | — | not ID | PASS |
| AH cafeteria META | INSUFFICIENT | False | — | — | — | — | none | PASS |
| AI cafeteria+support | WEAKLY, cafeteria uncited | True | — | — | — | — | cousin not cited | PASS |
| AJ contra added later | second episode not WEAKLY | False | — | — | — | — | none | PASS |
| AK dup support+contra | not WEAKLY | False | — | — | — | — | none | PASS |
| AL support+contra+uncertain | not WEAKLY | False | — | — | — | — | polarity wins | PASS |
| AM contra other entity | WEAKLY MATCH | True | — | — | — | — | other-entity not contrary | PASS |
| AN contra same entity | not WEAKLY | False | — | — | — | — | mixed | PASS |
| AO domain mismatch | not WEAKLY | False | — | — | — | — | no FACTUAL_PREMISE | PASS |
| AP lesson applicability mismatch | WEAKLY; lesson_applied False | — | — | — | — | — | inapplicable lesson unused | PASS |
| AQ failure applicability mismatch | failure not applied unless APPLICABLE | — | — | — | — | — | fingerprints required | PASS |

---

## 7. Mutation attack results

| Attack | Result |
| --- | --- |
| Assign polarity/class/clause/entity on frozen DTO | `FrozenInstanceError` |
| `object.__setattr__` polarity/class/clause on CONTRADICTS | `may_support_task` still False (recompute) |
| Mutate `clause_force` + `addresses_task_flag` on UNCERTAIN | `is_task_relevant_uncertain` still True |
| Mutate `temporal_state` to CURRENT on STALE | `live_temporal_state` still STALE; no FACTUAL_PREMISE |
| Role escalation + typed_class OBSERVED_FACT on OPINION | `live_typed_class` still OPINION; `may(FACTUAL_PREMISE)` False |
| Forged `EvidenceBinding(...)` with FACTUAL_PREMISE roles, OPINION kind | write-back False |
| Change statement on DTO to SUPPORT | DTO recomputes True; orchestrator rebind uses original CONTRA → no reusable mint |
| Forged `supporting_ids=["UNBOUND-ID"]` | critic REFUSE → not positive |

**PROVEN** for the live orchestrator path: stored DTO metadata cannot authorize persistence. Statement change on the DTO is treated as a new interpretation of that object only; write-back rebinds from `RetrievedItem`.

Residual: `CognitiveMemoryStore.remember` remains a public API. A caller that bypasses `CognitiveOrchestrator.run` can write any kind. That is not the P5 loop. Listed in bypass table.

---

## 8. Seven-mode results

Modes remain **eligibility gates/templates**, not independent formal operators.

| Mode | Eligible roles (positive) | Mixed no-edge | Mixed + edge | Write-back mixed |
| --- | --- | --- | --- | --- |
| DEDUCTIVE | FACTUAL_PREMISE + `may_support_task` | not WEAKLY | not WEAKLY | False |
| INDUCTIVE | supporting examples ≥2 | not WEAKLY | not WEAKLY | False |
| ABDUCTIVE | supporting observations + explanations | not WEAKLY | not WEAKLY | False |
| COMPARATIVE | supporting facts | not WEAKLY | not WEAKLY | False |
| TEMPORAL | dated/aging supporting facts | not WEAKLY | not WEAKLY | False |
| ADVERSARIAL | supporting facts; seeks falsifiers | not WEAKLY | not WEAKLY | False |
| METACOGNITIVE | decision-bearing supporters only | not WEAKLY | not WEAKLY | False |

Hard invariant: **NO MODE emits a live `reason()` WEAKLY_SUPPORTED on unresolved mixed evidence.** PROVEN (`test_seven_modes_mixed_never_weakly`).

---

## 9. Critic load-bearing proof

| Finding | Before | Action | After | Live path |
| --- | --- | --- | --- | --- |
| CONTRADICTION / mixed_polarity | WEAKLY or CONTESTED | CONTEST | UNRESOLVED/CONTESTED | PROVEN |
| MISSING_PREMISE empty | WEAKLY not issued | REQUIRE_MORE | INSUFFICIENT | PROVEN |
| unbound / irrelevant / lexical without support | forged WEAKLY | REFUSE | INSUFFICIENT | PROVEN |
| TYPE_VIOLATION | WEAKLY/SUPPORTED | DOWNGRADE | INSUFFICIENT | PROVEN (function + opinion live) |
| TEMPORAL_VIOLATION | WEAKLY | DOWNGRADE | INSUFFICIENT (this verification) | PROVEN function; live roles usually prevent the finding |
| SCOPE_MISMATCH | WEAKLY | DOWNGRADE | INSUFFICIENT (this verification) | PROVEN function |
| OVERCONFIDENCE SUPPORTED | SUPPORTED | DOWNGRADE | WEAKLY then governance strips SUPPORTED | PROVEN function |
| UNSUPPORTED_ASSUMPTION | only if candidate SUPPORTED | DOWNGRADE | WEAKLY | **PARTIALLY PROVEN** — does not fire on WEAKLY; ASM-000001 always present and is not evidence |

Critic is load-bearing on the actions it emits. It is not the only gate; episode policy and write-back rebind still apply.

---

## 10. Episode-policy ordering

`test_episode_policy_order_in_reason_source` asserts in `reason()`:

`apply_constraint` → `apply_episode_positive_policy` → `reusable_writeback_permitted`

Modes may still *construct* WEAKLY internally; `reason()` cannot return mixed WEAKLY. Orchestrator cannot mint from mixed even if verdict were wrongly WEAKLY (rebind + helper).

---

## 11. Repository bypass audit

| CALLER | FILE | PATH | GOVERNED? | WHY | RISK | ACTION |
| --- | --- | --- | --- | --- | --- | --- |
| `CognitiveOrchestrator.run` | `loop/orchestrator.py` | live P5/P3 | YES | helper + fresh bind | low | keep |
| `reason()` | `loop/reason.py` | no persist | YES | policy + critic | none for memory | keep |
| `MODE_FNS` | `loop/modes.py` | library | PARTIAL | WEAKLY candidates exist; must go through `reason()` | new caller skipping `reason()` | do not call MODE_FNS then `remember` |
| `HypothesisStore.propose` | orchestrator only in `architecture/` | persistence | YES | gated by helper | tests also call propose | tests only |
| `memory.remember` | `memory/store.py` | general API | NO | store does not know P5 policy | any producer can insert LESSON | not a P5 loop bypass; do not use from new loop code |
| `ConsolidationGate.accept` | `memory/consolidation.py` | explicit accept | YES | cannot write OBSERVED_FACT/DERIVED_FACT; `requires_human` | human misuse | keep |
| `loop/adapters.py` | observation ingest | remember facts | N/A | not conclusions | none | keep |
| `benchmark/evaluator.py` / `p5_eval.py` | `orch.run` / `reason` write_back False | YES | synthetic | none | keep |
| Lane A discovery/paper_trading | frozen | N/A | not P5 | none | freeze |

**P5 production write-back bypass: NOT FOUND.** Store-level `remember` is an ungoverned substrate API by design.

---

## 12. Two-hop contamination

Mixed SUPPORTS+CONTRADICTS, `write_back=True`:

- reusable HYP/LESSON/INFERENCE = 0
- EPISODIC INFERENCE episode row = 1
- Copied into a fresh store and re-reasoned: verdict not positive; retrieved OBSERVED_FACT count 0; no FACTUAL_PREMISE; no second-hop reusable mint

**PROVEN:** unresolved episode cannot become OBSERVED_FACT or DIRECT_SUPPORT merely because it was generated.

---

## 13. Lane A verification

`python3 -B scripts/freeze_lane_a.py` → `Lane-A integrity OK (36 files pinned)`  
No edits under `discovery/**` or `paper_trading/**`.

---

## 14. Soak verification

No soak DB writes, no daemon start, no observation reset. PAPER_ONLY unchanged.

---

## 15. Full test results

| Check | Result |
| --- | --- |
| freeze 36/36 | PASS |
| P5 envelope 1 | 409 passed |
| P5 envelope 2 | 409 passed |
| Focused A–AQ + mutation + two-hop + modes | 56 passed |
| `validate_imports.py` (cache cleaned; JSON restored) | VALIDATION PASSED |
| `pytest tests` entire tree | **1954 passed, 3 skipped, 2 failed** |

The two full-suite failures are **pre-existing doc-drift**, not P5:

`docs/architecture/AHOS_COGNITIVE_MEMORY_ARCHITECTURE_v1.0.md` references `data/ahos_cognitive_memory.sqlite` which is not in the repo. `test_evidence_package` asserts `stale_reference_count == 0`.

They are outside this write-back invariant. Not fixed here (would be an unrelated docs edit).

---

## 16. Changed files (this verification)

- `architecture/cognitive/loop/binding.py` — live typed/temporal/roles/uncertain
- `architecture/cognitive/loop/episode.py` — live uncertain detection
- `architecture/cognitive/loop/reason.py` — critic uses live typed/temporal
- `architecture/cognitive/loop/inference.py` — temporal/scope DOWNGRADE removes positivity
- `architecture/cognitive/loop/orchestrator.py` — comment: rebind from items
- `tests/test_p5_second_forensic.py` — A–AQ expansion, mutation, modes, two-hop, critic
- this report

`P5_FORENSIC_ARCHITECTURE_GATE.md` not modified. Retrieval not redesigned.

---

## 17. Remaining limitations

1. Modes are still templates, not formal operators.
2. Closed lexicons are not NLI; unrecognized contradiction wording stays UNKNOWN.
3. `Did`/`Can` exclusion is function-word, not NER.
4. `TEMP_CURRENT` is still never assigned.
5. Assumptions are recorded, not a constraint engine; `UNSUPPORTED_ASSUMPTION` only on SUPPORTED.
6. Retrieval failure-intent still suppresses OBSERVED_FACT lexical hits (unchanged P4.3).
7. `CognitiveMemoryStore.remember` can insert any kind if a non-loop caller uses it.
8. Full-tree pytest is not green due to unrelated doc-drift.

---

## 18. Highest justified claim

Governed typed eligibility + closed-lexicon support classification + live-recomputed binding + episode mixed-polarity policy + critic constraint + orchestrator write-back invariant.

Not AGI, ACI, entailment, NER, causal reasoning, or general intelligence.

---

## 19. MERGE decision / gate checklist

| Item | Status |
| --- | --- |
| mixed cannot become WEAKLY_SUPPORTED | PROVEN |
| uncertainty cannot become reusable | PROVEN |
| identity mismatch cannot become reusable | PROVEN |
| entity mismatch cannot become reusable | PROVEN |
| stale cannot become current positive | PROVEN |
| assumptions cannot become evidence | PROVEN |
| lexical relevance ≠ support | PROVEN |
| unbound citations ≠ support | PROVEN |
| critic constraints load-bearing | PROVEN (assumption finding PARTIALLY) |
| episode policy load-bearing | PROVEN |
| write-back gate load-bearing | PROVEN |
| no P5 production write-back bypass | PROVEN |
| two-hop contamination blocked | PROVEN |
| seven modes preserve invariant | PROVEN |
| A–AQ passes | PROVEN |
| full pytest passes | **FAIL** (2 pre-existing doc-drift) |
| import validation | PROVEN |
| Lane A unchanged | PROVEN |
| original forensic gate unchanged | PROVEN |
| no soak interference | PROVEN |
| no fake AGI/ACI claim | PROVEN |

Because **full pytest is not all-green**, the strict ALL-items rule cannot yield CONDITIONALLY_CLOSED.

`ARCHITECTURE_GATE = FAIL`  
`CODE_CHANGES_REQUIRED = NO` for P5 write-back (remaining full-suite failures are unrelated doc-drift)  
`P5_WRITEBACK_INVARIANT = PROVEN`  
`MERGE = NO`  
`READY_FOR_REVIEW = NO`

Human review is still required. Do not merge PR #93.
