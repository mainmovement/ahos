# P5 Typed Evidence-Bound Reasoning Benchmark

**Evaluator:** P4.1 suite (`p4.1.0`) plus additive P5 reasoning population (`p5_eval.py`)  
**Data label:** `SYNTHETIC_TEST_DATA`  
**P4.3 baseline SHA:** `976516123b0b682e99fcc6e9c6f0efabb91a9495`  
**Reproducibility:** two isolated runs, comparable payload equal = YES  
**Lane-A freeze:** `Lane-A integrity OK (36 files pinned)`  

Not an AGI/ACI score. Not soak evidence. P5 measures typed eligibility, bounded gates, and critic constraint — not formal reasoning calculi.

## REGRESSION RESULT (P4.3 population, unchanged labels)

| Metric | P4.3 | P5-fix | Status |
|--------|-----:|-------:|--------|
| Precision | 0.9091 (20/22) | 0.9091 (20/22) | PASS (protected) |
| Recall | 1.0000 | 1.0000 | PASS (protected) |
| F1 | 0.9524 | 0.9524 | PASS |
| MATCH_REASON | 1.0000 | 1.0000 | PASS |
| generic-overlap false inclusion | 0 | 0 | PASS |
| hard-mismatch rejection | 1.0 | 1.0 | PASS |
| relevant-lookalike recall | 1.0 (7/7) | 1.0 (7/7) | PASS |
| unknown refusal | 1.0000 | 1.0000 | PASS |
| contradiction pollution | 0 | 0 | PASS |
| false failure application (retrieval) | 0 | 0 | PASS |

Residual cousins (`BM-SHARED`, `BM-SW-TIMEOUT-HYP`) remain. This is the P4.3 leftover, not a P5 regression.

## NEW BENCHMARK RESULT (P5 reasoning population, post-fix)

| Metric | Numerator | Denominator | Result | Threshold | Status |
| -------------------------- | --------: | ----------: | -----: | --------: | ------ |
| Typed evidence compliance | 5 | 5 | 1.0000 | 1.0 MIN | PASS |
| Unsupported claim rate (P5) | 0 | 8 | 0.0000 | 0 ZERO | PASS |
| Evidence type violation | 0 | 2 | 0.0000 | 0 ZERO | PASS |
| Critic detection (P5) | 4 | 4 | 1.0000 | 0.5 MIN | PASS |
| Critic constraint | 2 | 2 | 1.0000 | 0.5 MIN | PASS |
| Missing premise refusal | 1 | 1 | 1.0000 | 1.0 MIN | PASS |
| Contradiction preservation | 1 | 1 | 1.0000 | 1.0 MIN | PASS |
| Temporal accuracy | 1 | 1 | 1.0000 | 1.0 MIN | PASS |
| Lesson application | 1 | 1 | 1.0000 | 1.0 MIN | PASS |
| False lesson application | 0 | 1 | 0.0000 | 0 ZERO | PASS |
| Failure application | 1 | 1 | 1.0000 | 1.0 MIN | PASS |
| False failure application (P5) | 0 | 1 | 0.0000 | 0 ZERO | PASS |
| Mode specificity | 1 | 1 | 1.0000 | 1.0 MIN | PASS |
| Mode confusion | 0 | 1 | 0.0000 | 0 ZERO | PASS |
| Unknown refusal (P5) | 1 | 1 | 1.0000 | 1.0 MIN | PASS |
| Assumption record presence | 7 | 7 | 1.0000 | 1.0 MIN | PASS |
| Cross-domain invariance | 1 | 1 | 1.0000 | 1.0 MIN | PASS |
| Reproducibility | 1 | 1 | 1.0000 | 1.0 MIN | PASS |

Critic detection counts live `_inspect` findings/actions only. Critic constraint counts live `reason()` paths where the critic **changes** the mode verdict (`P5-CRITIC-LIVE`, `P5-SKY-META`). Direct `apply_constraint` calls are not in that rate.

## Adversarial

Opinion-as-fact, hypothesis-as-fact, stale-as-current, inapplicable lesson, mismatched failure, contradiction, missing premise, **irrelevant valid fact**: refuse or contest as specified. No SUPPORTED certainty on P5 probes.

## Limitations

- Synthetic, small N (many metrics N=1).
- Modes are typed eligibility gates, not theorem/statistical/abductive engines.
- Relevance is lexical overlap, not semantics.
- Experiments remain analysis placeholders.
- Residual P4.3 retrieval FPs unchanged.

## Soak / Lane A

- SOAK DATABASE TOUCHED: NO
- SOAK RUNTIME RESTARTED: NO
- T0 RESET: NO
- Lane A: 36/36

Machine-readable dump: `p5_typed_evidence_reasoning_latest.json`
