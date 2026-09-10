# P5 Episode Polarity Architecture Report

**Kind:** Architecture fix + adversarial re-audit. Not a claim upgrade.  
**PR:** #93 (remains DRAFT; `MERGE = NO`)  
**Repository:** `mainmovement/ahos`  
**Data label of probes:** `SYNTHETIC_TEST_DATA`  
**Lane A:** untouched (`Lane-A integrity OK (36 files pinned)`)  
**Soak:** untouched, not restarted  
**PAPER_ONLY:** unchanged  

This is not formal entailment, NER, AGI, or ACI.

Honest capability name after this fix: **governed typed eligibility + closed-lexicon support classification + episode-level mixed-polarity policy + frozen EvidenceBinding recompute + write-back invariant below orchestration callers**.

The original read-only gate `reports/agi_aci_evolution/P5_FORENSIC_ARCHITECTURE_GATE.md` is **unchanged**. It remains the FAIL record for SHA `7e88ad2ed782b35db84c1c1ea7261b1b5bfa6613`.

---

## 1. Executive Verdict

The critical live-path leak is closed at episode level without requiring a CONTRADICTS graph edge.

A bound episode that contains both decision-bearing SUPPORT and CONTRADICTS no longer becomes `WEAKLY_SUPPORTED`, is not ACCEPTed as reusable knowledge, and cannot mint `HYPOTHESIS` / `LESSON` / `INFERENCE` merely because `context.contradiction_present` is false.

That does **not** make seven modes into formal reasoning operators, does **not** make assumptions load-bearing constraints, and does **not** assign `TEMP_CURRENT`.

`C1_MIXED_POLARITY_NO_EDGE = CLOSED`  
`WRITE_BACK_INVARIANT = ENFORCED_BELOW_CALLER`  
`ORIGINAL_FORENSIC_GATE_FILE = UNCHANGED_FAIL_AT_7e88ad2`  
`P5_STATUS = ARCHITECTURE_FIXED_NOT_AUTHORIZED_FOR_NEXT_GATE`  
`MERGE = NO`  
`READY_FOR_REVIEW = NO`

Highest justified claim remains: lexical relevance + structured compatibility over closed markers, now with an episode polarity policy. Not entailment, NER, AGI, or ACI.

---

## 2. Root Cause (original C1)

Live path:

`classify_support → may_support_task() → DEDUCTIVE → critic → write_back`

Per-item classification was load-bearing. Episode aggregation was not.

- DEDUCTIVE treated `contrary and not premises` as CONTESTED, then `if premises: WEAKLY_SUPPORTED`.
- A SUPPORTING fact plus a CONTRADICTING fact therefore collapsed to WEAKLY.
- `contradiction_present` was graph-edge only (`assemble_context`).
- The critic ACCEPTed when no edge existed.
- Orchestrator minted reusable knowledge from `verdict == "WEAKLY_SUPPORTED"` alone.

The contrary binding was classified correctly (`contradicts_task=True`) and then ignored.

---

## 3. Architectural Fix

Deterministic episode policy in `architecture/cognitive/loop/episode.py`, independent of graph edges:

| Episode content | Policy |
| --- | --- |
| SUPPORTS only (decision-bearing FACTUAL_PREMISE) | positive candidate allowed |
| CONTRADICTS only | CONTESTED; no reusable write-back |
| SUPPORTS + CONTRADICTS | `mixed_polarity` → CONTESTED/UNRESOLVED; no reusable write-back |
| SUPPORTS + task-relevant UNCERTAIN | `mixed_uncertainty` → UNRESOLVED/non-positive; no reusable write-back |
| ENTITY_MISMATCH beside a compatible MATCH supporter | mismatch is non-decision-bearing; does not veto the MATCH supporter |
| Entity-scoped evidence vs ENTITY_NONE task | `ENTITY_SCOPED`; not automatic support |
| METACOGNITIVE lexical inventory | counted, never cited as support |

Enforcement layers (none is caller convention):

1. Mode templates call `_episode_blocks_positive` before remaining WEAKLY returns.
2. Critic `_inspect` records `CONTRADICTION_VIOLATION:mixed_polarity_no_edge_required` even with no edge, and CONTEST runs before `already_refused` short-circuit.
3. `reason()` always applies `apply_episode_positive_policy` after critic constraint.
4. `reusable_writeback_permitted(verdict, bindings)` is the persistence gate. A forged `WEAKLY_SUPPORTED` string is not enough.
5. Orchestrator uses that helper, not `verdict == "WEAKLY_SUPPORTED"`. Episode rows may still be written; LESSON / HYPOTHESIS / reusable INFERENCE may not.

EvidenceBinding is `@dataclass(frozen=True)`. `may_support_task()` / `contradicts_task()` recompute from statement + task snapshot. Stored polarity cannot authorize support.

`Did` / `Can` (and other auxiliary/interrogative surface forms) are identity function-words, not entity markers.

Decision-bearing evidence = `may_support_task()` AND eligible `FACTUAL_PREMISE`. Stale/historical/unknown-age and non-facts cannot authorize a positive or reusable write-back.

---

## 4. Invariants Introduced

1. **Mixed polarity fail-closed.** SUPPORTS + CONTRADICTS cannot collapse to WEAKLY. Graph edge not required.
2. **Write-back invariant.** No unresolved contradictory, uncertain, identity-incompatible, entity-incompatible, stale, assumption-only, or otherwise non-decision-bearing episode may mint reusable HYPOTHESIS / LESSON / INFERENCE. Enforced in `reusable_writeback_permitted`, called from the orchestrator below any task caller.
3. **Binding integrity.** Frozen DTO + live recompute. Polarity field mutation does not change `may_support_task()` without changing the statement.
4. **METACOGNITIVE isolation.** Only decision-bearing supporters are cited. Lexical inventory cannot upgrade an episode.
5. **Entity scope.** Evidence with identity markers vs an unscoped task is `SCOPED`, not automatic support.

---

## 5. Commit Audited

| Field | Value |
| --- | --- |
| Production SHA (this report's parent before this file) | `3350ffa48947f0f6986e60581391fb1ac3f7f64a` |
| Architecture commit | `664415d` Fail-close mixed polarity at episode level without requiring graph edges. |
| Original FAIL audit | `7e88ad2ed782b35db84c1c1ea7261b1b5bfa6613` |
| Original FAIL report commit | `02c41be569798568909e336f4b2277dc84b79dfe` |
| Retrieval | `architecture/cognitive/loop/retrieval.py` not redesigned |

Exact SHA of the commit that includes this report is the commit that adds this file.

---

## 6. Files Changed

Relative to `02c41be` (original forensic report commit):

| File | Why |
| --- | --- |
| `architecture/cognitive/loop/episode.py` | Episode polarity policy + write-back invariant + post-critic gate |
| `architecture/cognitive/loop/modes.py` | Fail-closed mixed checks; META cites only decision-bearing supporters |
| `architecture/cognitive/loop/reason.py` | Critic mixed-polarity finding; non-bypassable episode policy |
| `architecture/cognitive/loop/orchestrator.py` | Write-back uses `reusable_writeback_permitted` |
| `architecture/cognitive/loop/binding.py` | Frozen EvidenceBinding; live recompute; TEMP_CURRENT documented unused |
| `architecture/cognitive/loop/support.py` | `ENTITY_SCOPED`; identity function-words (`Did`/`Can`/…) |
| `architecture/cognitive/loop/contracts.py` | `reusable_writeback` on trace and result |
| `architecture/cognitive/loop/context.py` | `contradiction_present` documented as edge-only |
| `architecture/cognitive/benchmark/evaluator.py` | HYP-BENCH-1 uses a dedicated DIRECT_SUPPORT seed (mixed leftover store must not mint) |
| `tests/test_p5_episode_polarity.py` | Adversarial matrix A–M |
| `tests/test_typed_reasoning.py` | META live-path assertions aligned with fail-closed inventory |

Lane A (`discovery/**`, `paper_trading/**`) not modified. Original forensic report not modified. Thresholds not weakened. No fixture-specific production tokens.

---

## 7. Tests Added/Changed

Added: `tests/test_p5_episode_polarity.py` (matrix A–M, seven-mode mixed sweep, forged-WEAKLY invariant).

Changed: `tests/test_typed_reasoning.py` META critic tests so cafeteria-only inventory is non-positive without requiring a WEAKLY→REFUSE two-step.

---

## 8. Adversarial Matrix Results

Live `reason()` plus `write_back=True` / `write_back=False` orchestrator probes. Pytest: 15 passed × 2.

| Case | Decision | Reusable write-back |
| --- | --- | --- |
| A SUPPORTS only | WEAKLY_SUPPORTED | allowed when `write_back=True`; none when False |
| B CONTRADICTS only | CONTESTED | none |
| C SUPPORTS+CONTRADICTS, no graph edge | UNRESOLVED/CONTESTED, not WEAKLY | none (`write_back=True` still writes episode row only) |
| D SUPPORTS+CONTRADICTS, edge present | UNRESOLVED/CONTESTED | none |
| E SUPPORTS+UNCERTAIN | not WEAKLY | none |
| F SUPPORTS + ENTITY_MISMATCH (MATCH supporter present) | WEAKLY from MATCH; mismatch not cited | allowed from the compatible supporter |
| G SUPPORTS + lexical METACOGNITIVE cousin | WEAKLY cites supporter only; cousin-only is insufficient | cousin-only: none |
| H polarity mutation after bind | FrozenInstanceError; forced field write still recomputes | n/a (CONTRA remains non-supporting) |
| I `Did retries…?` | `did` is not an identity marker; unscoped SUPPORT still WEAKLY | same as Do-question |
| J `Can retries…?` | `can` is not an identity marker | same |
| K entity-specific vs ENTITY_NONE task | SCOPED; not WEAKLY | none |
| L assumption-only | INSUFFICIENT; ASM recorded, not in premises | none |
| M stale/non-current | not CURRENT; not WEAKLY from STALE FACTUAL_PREMISE | none |

Seven modes on C (mixed, no edge): none emit WEAKLY; `reusable_writeback=False` for all.

---

## 9. Write-back Safety Results

Manual live-path probe (SYNTHETIC_TEST_DATA, in-process, no soak DB):

| Probe | Verdict | reusable_writeback | HYP/LESSON/INFERENCE minted |
| --- | --- | --- | --- |
| mixed, no edge, `write_back=True` | UNRESOLVED | False | 0 / 0 / 0 (episode row only) |
| mixed, no edge, `write_back=False` | UNRESOLVED | False | 0 / 0 / 0 (no episode row) |
| mixed, edge present, `write_back=True` | UNRESOLVED | False | 0 / 0 / 0 (episode row only) |
| forged `reusable_writeback_permitted("WEAKLY_SUPPORTED", mixed_bindings)` | — | False | cannot |

Critic findings on mixed no-edge DEDUCTIVE: `CONTRADICTION_VIOLATION:mixed_polarity_no_edge_required`. Action CONTEST.

---

## 10. Original P5 Forensic Gate

File `P5_FORENSIC_ARCHITECTURE_GATE.md` was **not edited**.

| Field | Result |
| --- | --- |
| Audited SHA in that file | `7e88ad2ed782b35db84c1c1ea7261b1b5bfa6613` |
| `ARCHITECTURE_GATE` recorded there | FAIL |
| `P5_STATUS` recorded there | FIX_REQUIRED |
| Re-run of C1 on current code | CLOSED (UNRESOLVED, no reusable mint) |

The original document is the historical failure record. Passing tests on this SHA do not rewrite it.

---

## 11. Validation Envelope

| Check | Result |
| --- | --- |
| `python3 -B scripts/freeze_lane_a.py` | Lane-A integrity OK (36 files pinned) |
| Targeted pytest envelope 1 | 368 passed |
| Targeted pytest envelope 2 | 368 passed |
| Matrix A–M 1 | 15 passed |
| Matrix A–M 2 | 15 passed |
| `scripts/validate_imports.py` (after cache clean; report JSON restored) | VALIDATION PASSED |
| Lane A files | not modified |
| Soak | not touched |

Pytest interpreter: `/tmp/ahos-test-venv/bin/python`. Envelope:

`tests/test_p5_episode_polarity.py tests/test_p5_negation_entity.py tests/test_typed_reasoning.py tests/test_retrieval_lookalike.py tests/test_retrieval_relevance.py tests/test_cognitive_benchmark.py tests/test_cognitive_loop.py tests/test_cognitive_memory.py tests/test_cognitive_core.py tests/test_self_evolution_engine.py tests/test_multi_mind_council_anti_echo.py tests/test_evolution_validate.py tests/test_cognitive_panel.py tests/test_canonical_security_gate.py tests/test_security_hardening.py`

---

## 12. Remaining Limitations

1. **Seven modes** are still distinct eligibility gates / templates over EvidenceBinding lists, not independent formal operators. They now share a fail-closed episode policy. That is not deduction, statistical induction, or entailment.
2. **Assumptions** are recorded (`ASM-000001`) and do not enter EvidenceBinding lists. They do not constrain WEAKLY inference beyond critic rules that almost never fire on P5 (SUPPORTED is stripped). They must not be treated as evidence; they are also not a working assumption engine.
3. **`TEMP_CURRENT` is never assigned.** `ACTIVE + observed_at` is `DATED`. A timestamp is not freshness proof. This layer does not invent an age-from-clock current-state model.
4. **Retrieval is unchanged (P4.3).** Questions containing `failure`/`failures` still set failure-intent and will not lexically retrieve OBSERVED_FACT rows. Episode policy does not repair retrieval.
5. **Closed lexicons are not NLI.** Mixed polarity is detected from already-classified bindings. Unrecognized contradiction wording remains UNKNOWN, not magically CONTRADICTS.
6. **Identity markers are not NER.** Function-words are excluded; remaining title-case / short-ID overlap is still a closed heuristic.
7. **Callers that bypass `CognitiveOrchestrator.run` and write memory themselves** are outside this invariant. The live production path is the orchestrator + `reason()`.

---

## 13. Claim Discipline

Until a later gate is explicitly authorized:

- Do not claim AGI, ACI, entailment, or NER.
- Do not claim the original forensic file now passes.
- Do not merge PR #93.
- Do not mark ready for review.

`MERGE = NO`  
`READY_FOR_REVIEW = NO`
