# P4.1 BENCHMARK AUDIT

**UTC date:** 2026-09-09  
**Main baseline:** `6862c6fc20050622f6125853671f885b0e36b16a` (PR #89 / P3 merge)  
**Prior:** P2 `606b6f2` · P1 `1f4febb`

## What already existed

| Surface | Class | Reuse decision |
|---------|-------|----------------|
| `loop/benchmark.py` `run_memory_vs_no_memory` | PARTIAL | N=1 lesson reuse. Keep; P4.1 expands independently |
| `loop/metrics.py` METRIC_SPECS | PARTIAL | Definitions only; no numerator/denominator/status |
| `evaluation.py` `refuse_fabricated_score` | IMPLEMENTED_AND_VERIFIED | Reused; still rejects 99.9% |
| `COGNITIVE_LOOP_BENCHMARK.md` | PARTIAL | P3 N=1 pair; not replaced |
| `BENCHMARK_PLAN.md` | DOCUMENTATION_ONLY for AGI suite | Still not an AGI suite |
| Duplicate evaluation brains | none found | No second scorer created |
| Fake intelligence scores | none in cognitive package | Guard remains |

## Tests that only proved execution

P3 `test_memory_vs_no_memory_benchmark` proved one lesson was retrieved. It did not measure precision, distractors, incorrect lesson application, or Top-K.

## Non-determinism risks

- `time.time()` defaults on `CognitiveTask.created_at` — P4.1 cases use fixed `NOW`
- `recent()` sort is `(created_at, memory_id)` — corpus uses fixed timestamps + stable BM-* ids
- Wall-clock e2e latency excluded from reproducibility payload

## Retrieval behavior that will fail honest thresholds

`MemoryRetriever` adds `same_domain` for every same-domain row, `failure_relationship` for every FAILURE, and `contradiction_relationship` for every row with an edge — even without keyword overlap. Precision will be low. Empty-evidence queries can still retrieve global FAILURE/contradiction rows. **Do not retune the retriever in P4.1 to hide this.**

## Skills / governance

`ahos-governance-context`. Lane A frozen. Soak `run_1788987515_7ad11528` not contacted. PAPER_ONLY / L1_ANALYZE unchanged.
