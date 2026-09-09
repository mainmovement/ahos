# P4.1 Cognitive Benchmark Report

**Benchmark version:** `p4.1.0`  
**Git SHA:** `525443d9ed182d4f464ce260ee4d8b7a4bfffab5`  
**Data label:** `SYNTHETIC_TEST_DATA`  
**Lane-A freeze:** `Lane-A integrity OK (36 files pinned)`  

This is **not** an AGI/ACI score. Metrics have numerators and denominators.
Denominator 0 → `NOT_MEASURED`, never `PASS`.

## Case counts

- `adversarial`: 7
- `case_result_rows`: 38
- `contradiction`: 2
- `corpus_memories`: 41
- `cross_domain`: 4
- `reasoning_modes`: 7
- `retrieval`: 11
- `unknown`: 3

## Metrics

| metric | value | n/d | threshold | status | class |
|---|---:|---:|---:|---|---|
| `adversarial_resistance` | 1.0000 | 7.0000/7.0000 | 1.0000 MIN | PASS | GOVERNANCE |
| `assumption_tracking_rate` | 1.0000 | 7.0000/7.0000 | — | PASS | PROVISIONAL |
| `context_contradiction_preservation` | 1.0000 | 2.0000/2.0000 | — | PASS | PROVISIONAL |
| `context_coverage` | 0.2500 | 1.0000/4.0000 | 0.5000 MIN | FAIL | PROVISIONAL |
| `context_incomplete_flag_rate` | 1.0000 | 2.0000/2.0000 | — | PASS | PROVISIONAL |
| `contradiction_detection_rate` | 1.0000 | 2.0000/2.0000 | 1.0000 MIN | PASS | GOVERNANCE |
| `contradiction_false_resolution_rate` | 0.0000 | 0.0000/2.0000 | 0.0000 ZERO | PASS | GOVERNANCE |
| `correct_lesson_reuse_rate` | 1.0000 | 2.0000/2.0000 | 0.5000 MIN | PASS | PROVISIONAL |
| `critic_detection_rate` | 1.0000 | 6.0000/6.0000 | 0.5000 MIN | PASS | PROVISIONAL |
| `critic_false_alarm_rate` | 0.0000 | 0.0000/1.0000 | — | PASS | PROVISIONAL |
| `critic_scope_mismatch` | — | 0.0000/0.0000 | — | NOT_MEASURED | PROVISIONAL |
| `cross_domain_consistency` | 1.0000 | 1.0000/1.0000 | 1.0000 MIN | PASS | PROVISIONAL |
| `dropped_relevant_record_rate` | 0.7500 | 21.0000/28.0000 | — | PASS | PROVISIONAL |
| `evidence_class_integrity` | 1.0000 | 32.0000/32.0000 | 1.0000 MIN | PASS | GOVERNANCE |
| `experiment_analysis_only` | 1.0000 | 1.0000/1.0000 | — | PASS | PROVISIONAL |
| `failure_recall` | 1.0000 | 1.0000/1.0000 | 0.5000 MIN | PASS | PROVISIONAL |
| `false_certainty_rate` | 0.0000 | 0.0000/3.0000 | 0.0000 ZERO | PASS | GOVERNANCE |
| `false_failure_application_rate` | 1.0000 | 1.0000/1.0000 | 0.5000 MAX | FAIL | PROVISIONAL |
| `hypothesis_falsification_present` | 1.0000 | 1.0000/1.0000 | — | PASS | PROVISIONAL |
| `incorrect_lesson_application_rate` | 0.5000 | 1.0000/2.0000 | 0.5000 MAX | PASS | PROVISIONAL |
| `lesson_reuse_rate` | 1.0000 | 2.0000/2.0000 | 0.5000 MIN | PASS | PROVISIONAL |
| `match_reason_correctness` | 1.0000 | 325.0000/325.0000 | 1.0000 MIN | PASS | GOVERNANCE |
| `namespace_isolation_rate` | 1.0000 | 2.0000/2.0000 | 1.0000 MIN | PASS | GOVERNANCE |
| `namespace_leakage_rate` | 0.0000 | 0.0000/2.0000 | 0.0000 ZERO | PASS | GOVERNANCE |
| `no_memory_lesson_reuse` | 0.0000 | 0.0000/1.0000 | 0.0000 ZERO | PASS | GOVERNANCE |
| `novelty_not_truth` | 1.0000 | 1.0000/1.0000 | — | PASS | PROVISIONAL |
| `provenance_preservation` | 1.0000 | 27.0000/27.0000 | — | PASS | PROVISIONAL |
| `reasoning_mode_structure_rate` | 1.0000 | 7.0000/7.0000 | — | PASS | PROVISIONAL |
| `recall_at_1` | 0.0455 | 0.5000/11.0000 | 0.2000 MIN | FAIL | PROVISIONAL |
| `recall_at_10` | 0.8896 | 9.7857/11.0000 | 0.6000 MIN | PASS | PROVISIONAL |
| `recall_at_3` | 0.1364 | 1.5000/11.0000 | 0.4000 MIN | FAIL | PROVISIONAL |
| `recall_at_5` | 0.6623 | 7.2857/11.0000 | 0.5000 MIN | PASS | PROVISIONAL |
| `retrieval_f1` | 0.1159 | 0.1159/1.0000 | 0.5000 MIN | FAIL | PROVISIONAL |
| `retrieval_precision` | 0.0615 | 20.0000/325.0000 | 0.5000 MIN | FAIL | PROVISIONAL |
| `retrieval_recall` | 1.0000 | 20.0000/20.0000 | 0.7000 MIN | PASS | PROVISIONAL |
| `stale_not_false` | 1.0000 | 1.0000/1.0000 | 1.0000 MIN | PASS | GOVERNANCE |
| `temporal_classification_accuracy` | 1.0000 | 5.0000/5.0000 | 1.0000 MIN | PASS | GOVERNANCE |
| `unknown_refusal_accuracy` | 0.6667 | 2.0000/3.0000 | 1.0000 MIN | FAIL | GOVERNANCE |
| `unsupported_claim_rate` | 0.0000 | 0.0000/24.0000 | 0.0000 ZERO | PASS | GOVERNANCE |

## Status counts

- PASS: 31
- FAIL: 7
- NOT_MEASURED: 1

## Weaknesses

- WEAKNESS_DETECTED:context_coverage=0.25
- WEAKNESS_DETECTED:false_failure_application_rate=1.0
- WEAKNESS_DETECTED:recall_at_1=0.045454545454545456
- WEAKNESS_DETECTED:recall_at_3=0.13636363636363635
- WEAKNESS_DETECTED:retrieval_f1=0.11594202898550725
- WEAKNESS_DETECTED:retrieval_precision=0.06153846153846154
- WEAKNESS_DETECTED:unknown_refusal_accuracy=0.6666666666666666

## Improvement candidates (not auto-applied)

- IMPROVEMENT_CANDIDATE:context_coverage
- IMPROVEMENT_CANDIDATE:false_failure_application_rate
- IMPROVEMENT_CANDIDATE:recall_at_1
- IMPROVEMENT_CANDIDATE:recall_at_3
- IMPROVEMENT_CANDIDATE:retrieval_f1
- IMPROVEMENT_CANDIDATE:retrieval_precision
- IMPROVEMENT_CANDIDATE:unknown_refusal_accuracy

## Soak protection

- `SOAK_DATABASE_TOUCHED`: NO
- `SOAK_RUNTIME_RESTARTED`: NO
- `T0_RESET`: NO
- `BENCHMARK_DB`: ahos_cognitive_memory.sqlite
- `REPRODUCIBILITY_EQUAL`: YES

## Limitations

- SYNTHETIC_TEST_DATA only; not soak evidence
- Keyword/domain retrieval is not semantic search
- Causal/counterfactual modes remain NOT_IMPLEMENTED
- N is small; do not treat rates as statistical significance
- No LLM, network, vector DB, or live execution
- Finance is an adapter proving domain, not the definition of cognition

## What this is not

- Not AGI, not ACI, not a world model, not soak evidence.
- Not a 99.9% intelligence score.
- Not authorization to promote, trade, or execute live.

