# P5 — Typed Evidence-Bound Reasoning Audit

**Phase:** P5  
**Data label:** `SYNTHETIC_TEST_DATA`  
**Base:** `origin/main` `976516123b0b682e99fcc6e9c6f0efabb91a9495` (P4.3 / PR #92)  
**Lane-A freeze:** `Lane-A integrity OK (36 files pinned)`  
**Implementation:** Lane B only. No soak I/O. No Lane A edits.

This is not AGI, ACI, or an intelligence score.

## 1. EXECUTIVE SUMMARY

P4.4 identified the bottleneck: retrieved memories were scored as an undifferentiated keyword pool; the critic did not constrain results. P5 implements deterministic typed-evidence eligibility, bounded mode-specific inference gates, and critic-constrained candidate handling. This is not formal deduction, statistical induction, full abductive reasoning, AGI, or ACI.

P4.3 retrieval metrics are unchanged on the frozen vector (precision 0.9091, recall 1.0000, MATCH_REASON 1.0000). P5 metrics on a separate reasoning population are measured without hardcoded passes. Regression envelope: 195 passed (28 P5-specific in `tests/test_typed_reasoning.py`).

## 2. PRE-P5 BASELINE

P4.3 merged retrieval discrimination. P3 `reason()` called `_verdict_from_context` for every implemented mode. `critique_result` set flags; `too_strong` could not fire because SUPPORTED was downgraded first.

## 3. P4.4 FINDING VERIFICATION

**CONFIRMED.** Inspected `architecture/cognitive/loop/reason.py` on `9765161`: one keyword-overlap verdict; critic commentary only. Context coverage 0.5714 remains a four-budget average, not the reason to build P5.

## 4. ARCHITECTURE CHANGE

```text
Memory → RetrievedItem → EvidenceBinding → mode reasoner → CandidateInference
    → critic _inspect → apply_constraint → ReasoningResult
```

New modules: `binding.py`, `inference.py`, `modes.py`. `reason.py` dispatches; `retrieval.py` untouched.

## 5. TYPED EVIDENCE MODEL

Binding `typed_class` uses the existing taxonomy: OBSERVED_FACT, INFERENCE, HYPOTHESIS, PREDICTION, SIMULATION, OPINION, PROCEDURE, LESSON, plus FAILURE / EXPERIMENT from `MemoryType` (failures stored as OBSERVED_FACT are still typed FAILURE).

Opinions and simulations are now first-class context buckets so they cannot vanish from `all_included()`.

## 6. EVIDENCE BINDING

`EvidenceBinding` records roles (allowed/forbidden), applicability, temporal_state, support_strength (DIRECT/INDIRECT/NONE/UNKNOWN — not a probability), contradiction_state, provenance. Does not rewrite memory.

## 7. INFERENCE MODEL

`Inference` / `CandidateInference` carry conclusion_class, premises, alternatives, missing_premises, critic_action, lesson_applied, failure_applied.

## 8–14. MODES

| Mode | Distinct behavior (one-fact software timeout probe) |
|------|------------------------------------------------------|
| DEDUCTIVE | WEAKLY_SUPPORTED from current FACTUAL_PREMISE only |
| INDUCTIVE | INSUFFICIENT_EVIDENCE (n<2 examples); output class INFERENCE |
| ABDUCTIVE | UNRESOLVED without explanation candidates |
| COMPARATIVE | Typed dimensions; contradiction → UNRESOLVED |
| TEMPORAL | Stale-only → INSUFFICIENT + STALE |
| ADVERSARIAL | Opinion/prediction/simulation cannot establish fact |
| METACOGNITIVE | Inventory; never SUPPORTED |
| CAUSAL / CF | NOT_IMPLEMENTED (critic must not rewrite this to INSUFFICIENT) |

## 15. CRITIC CONSTRAINT

Findings include TYPE_VIOLATION, MISSING_PREMISE, CONTRADICTION_VIOLATION, TEMPORAL_VIOLATION, APPLICABILITY_VIOLATION, OVERCONFIDENCE, SCOPE_MISMATCH. Actions change the candidate. Empty context → REQUIRE_MORE_EVIDENCE. NOT_IMPLEMENTED is not overwritten.

## 16–17. LESSON / FAILURE APPLICATION

Applicable lesson (`payload.applicability` matches domain) constrains deduction (epistemic UNCERTAIN). Finance lesson on software task is not applied. Failure caution requires matching explicit component/failure_type; mismatch or unknown applicability does not apply.

## 18–19. CONTRADICTION / UNKNOWN

Contradicted premises → UNRESOLVED/CONTESTED. Empty / unimplemented → INSUFFICIENT / NOT_IMPLEMENTED. UNKNOWN remains UNKNOWN.

## 20–21. HYPOTHESIS / EXPERIMENT

Existing HypothesisStore and ExperimentLedger reused. Experiments remain analysis-only (`INSUFFICIENT_DATA` / `NOT_COMPARABLE`). Hypotheses are EXPLANATION_CANDIDATE, never FACTUAL_PREMISE.

## 22. CLOSED-LOOP LEARNING

`test_closed_loop_second_episode_changes_reasoning`: episode 1 DEDUCTIVE WEAKLY/PROBABLE; after an applicable lesson is stored, episode 2 is UNCERTAIN with `lesson_applied=True`. Persistence, retrieval, and application are distinguished in tests/metrics.

## 23. BENCHMARK DESIGN

Existing P4.1 cases/labels unchanged. Additive population in `p5_eval.py` (deductive/inductive/abductive/comparative/temporal/adversarial/metacognitive probes, lesson/failure apply and false-apply, critic constraint).

## 24. METRICS

See `P5_TYPED_EVIDENCE_REASONING_BENCHMARK.md`. Every metric has numerator, denominator, population, version, threshold, limitations.

## 25. P4.3 REGRESSION

Precision 0.9091, recall 1.0000, MATCH_REASON 1.0000, generic-overlap 0, hard-mismatch 1.0, relevant-lookalike 1.0. Retrieval module not edited.

## 26. ADVERSARIAL RESULTS

Opinion/hypothesis-as-fact, stale-as-current, inapplicable lesson, mismatched failure, contradiction, missing premise: constrained. No SUPPORTED on P5 probes.

## 27. REPRODUCIBILITY

`run_twice` equal = YES.

## 28. DOMAIN-GENERALITY

Software / science / finance / operations one-fact DEDUCTIVE share verdict class. No crypto fields in the reasoner.

## 29. SECURITY / GOVERNANCE

No Lane A imports in `loop/`. No live execution. Derived inferences are namespaced (`cognitive-inference`) so they do not pollute unscoped retrieval. Hypothesis/experiment stores reused, not duplicated.

## 30. LANE-A INTEGRITY

`python3 -B scripts/freeze_lane_a.py` → 36/36.

## 31. SOAK STATUS

SOAK DATABASE TOUCHED: NO. SOAK RUNTIME RESTARTED: NO. T0 RESET: NO.

## 32. LIMITATIONS

Synthetic small N. Modes are typed eligibility gates, not scientific calculi. Relevance is lexical overlap (existing tokenizer), not embeddings. ACTIVE+timestamp is DATED, not proven CURRENT. Assumptions are recorded, not load-bearing. Experiments remain placeholders. Residual P4.3 retrieval cousins remain. Critic is a deterministic rule list, not an independent agent.

## 33. REMAINING GAPS

ACI-GAP-002 world model OPEN. Causal/CF NOT_IMPLEMENTED. Experiment analysis `INSUFFICIENT_DATA`. ACI-GAP-010 not a six-baseline AGI suite. Soak ingest still missing (ACI-GAP-001).

## 34. NEXT SINGLE HIGHEST-VALUE CAPABILITY

**Evidence-bound experiment analysis.** Hypotheses cannot be honestly SUPPORTED/REJECTED from cognition while every cognitive experiment is a placeholder code. Do not build a world model or Council next.
