# P5 FIX CORRECTION REPORT

**PR:** #93  
**Branch:** `cursor/agi-aci-p5-typed-evidence-reasoning-9500`  
**Pre-fix SHA:** `b77d6177a23e2a6056578892e2819935e6ffc930`  
**Base:** `976516123b0b682e99fcc6e9c6f0efabb91a9495`  
**Data label:** `SYNTHETIC_TEST_DATA`  
**Lane A:** `Lane-A integrity OK (36 files pinned)`  
**Soak:** not touched  

This is not AGI, ACI, formal deduction, or statistical induction.

## 1. Baseline

Inspected before edits:

- Branch `cursor/agi-aci-p5-typed-evidence-reasoning-9500`
- HEAD `b77d617` matching PR #93 `headRefOid`
- Working tree: untracked `next-env.d.ts`, `reports/PRE_SOAK_STATUS.txt` only
- PR #93 OPEN, DRAFT
- Review verdict that this pass implements: `FIX_REQUIRED`

## 2. Findings Addressed

| ID | Status |
| -- | ------ |
| F-01 | Fixed: `or True` removed; detection requires CONTEST or CONTRADICTION finding |
| F-02 | Fixed: `apply_constraint(...)` no longer counted in `critic_constraint_rate` |
| F-03 | Fixed: lexical `addresses_task` gate; irrelevant OBSERVED_FACT → INSUFFICIENT |
| F-04 | Fixed: REFUSE is live (accepted + unbound citation, or accepted + irrelevant citation) |
| F-05 | Fixed: ACTIVE+`observed_at` is `DATED`, not `CURRENT` |
| F-06 | Fixed: domain-only lesson → UNKNOWN, not APPLICABLE |
| F-07 | Fixed: both component and failure_type must match when both are explicit |
| F-08 | Fixed: cited IDs must be ⊆ bound memory IDs; else REFUSE |
| F-09 | Honest scope: metric renamed to `assumption_record_presence` |
| F-10 | Fixed: LESSON write-back only for `WEAKLY_SUPPORTED` |
| F-11 | Fixed: vacuous `or True` removed |
| Live critic test | Added |
| Seven-mode behavioral probes | Added |

## 3. Findings Intentionally Deferred

None of the required or strongly preferred review items were deferred.

Not in scope (unchanged by design): causal/CF, world model, experiment analysis, embeddings, LLM judges, Lane A, soak.

## 4. Exact Code Changes

- `architecture/cognitive/loop/binding.py` — `addresses_task`, `TEMP_DATED`, lesson/failure fingerprint rules, `cited_unbound_ids`
- `architecture/cognitive/loop/modes.py` — task-relevant premises; temporal DATED vs STALE; metacognitive irrelevant inventory still WEAKLY so critic can REFUSE
- `architecture/cognitive/loop/reason.py` — live REFUSE; contradiction finding always recorded; post-constraint unbound citation refuse
- `architecture/cognitive/loop/inference.py` — REFUSE documented as live
- `architecture/cognitive/loop/orchestrator.py` — no general LESSON from unresolved/insufficient/contested
- `architecture/cognitive/benchmark/p5_eval.py` — honest detection/constraint probes
- `architecture/cognitive/benchmark/thresholds.py` — `assumption_record_presence`
- `tests/test_typed_reasoning.py` — relevance, live critic, seven modes, lesson/failure/lesson-write-back

`retrieval.py` not edited.

## 5. Behavioral Changes

- "The sky is blue" + timeout question: DEDUCTIVE `INSUFFICIENT_EVIDENCE`; METACOGNITIVE candidate WEAKLY then critic `REFUSE` → `INSUFFICIENT_EVIDENCE`
- Domain-only software lesson does not constrain a timeout task
- Same-component / different-`failure_type` does not apply
- ACTIVE dated facts remain usable premises but temporal scope is `DATED`
- Unresolved episodes persist as episodes, not reusable LESSONs

## 6. Critic Detection Measurement

`p5_critic_detection_rate` = **4/4 = 1.0**

Population: empty-context REQUIRE_MORE; contradiction finding on live `reason()`; metacognitive CONTEST; irrelevant-inventory REFUSE.

No `or True`. No case-ID branch in production.

## 7. Critic Constraint Measurement

`critic_constraint_rate` = **2/2 = 1.0**

Population: `P5-CRITIC-LIVE` (mode WEAKLY → critic CONTEST → UNRESOLVED) and `P5-SKY-META` (mode WEAKLY → critic REFUSE → INSUFFICIENT).

Direct `apply_constraint(ACTION_DOWNGRADE)` is not in the denominator.

## 8. Evidence Relevance

`addresses_task` uses existing `content_tokens` + documented inflections. Fail-closed on empty overlap. Not embeddings. Valid type ≠ relevant content.

## 9. Seven-Mode Coverage

`test_seven_modes_governed_behavior_not_aliases` checks distinct governed outputs (not mode-name equality). `MODE_SEMANTICITY` remains **PARTIAL** (gates, not calculi).

## 10. Benchmark Integrity

- No `or True` in P5 evaluator or P5 tests
- No production references to `P5-*` or `BM-*` IDs
- Thresholds not lowered
- Isolated double run: `repro_equal=True`, FAIL metrics: none

## 11. P4.3 Regression

From isolated `run_cognitive_benchmark` (not a rewrite of retrieval):

| Metric | Value |
| ------ | ----- |
| precision | 0.9091 (20/22) |
| recall | 1.0 |
| F1 | 0.9524 |
| match_reason_correctness | 1.0 |
| generic-overlap false inclusion | 0 |
| hard-mismatch rejection | 1.0 |
| relevant-lookalike recall | 1.0 (7/7) |
| contradiction pollution | 0 |
| unknown refusal | 1.0 (3/3) |

## 12. Determinism

Two isolated benchmark runs: comparable payload equal. No LLM/network in the loop.

## 13. Security / Governance

PAPER_ONLY preserved. `authorized_execution=False`. No live path. No self-modification.

## 14. Lane A / Soak Integrity

Freeze 36/36. Diff still excludes `discovery/**`, `paper_trading/**`, soak DB, `.env`.

`P5 CAN BE REVIEWED AND MERGED WITHOUT RESTARTING THE ACTIVE SOAK`

## 15. Remaining Limitations

- Lexical relevance can miss paraphrase and can over-accept shared tokens
- Deduction/induction/abduction remain gates, not scientific engines
- Assumptions are recorded, not causal
- Many P5 metrics remain N=1 synthetic probes
- Experiments still `INSUFFICIENT_DATA`

## 16. Final P5 Status

`P5_CORRECTED_READY_FOR_REVIEW`
