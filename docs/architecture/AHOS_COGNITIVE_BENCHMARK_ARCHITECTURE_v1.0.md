# AHOS Cognitive Benchmark Architecture v1.0 (P4.1)

**Status:** Lane-B evaluation layer IMPLEMENTED (executed). **Not an intelligence score. Not AGI/ACI.**  
**Code:** `architecture/cognitive/benchmark/`  
**Runner:** `scripts/run_cognitive_benchmark.py`  
**Tests:** `tests/test_cognitive_benchmark.py`  
**Base:** main `6862c6fc20050622f6125853671f885b0e36b16a` (post PR #89)

## Placement

```text
P3 cognitive loop (architecture/cognitive/loop)
        ↑ measured by
P4.1 benchmark (architecture/cognitive/benchmark)
        × no soak / Lane A / LLM / network
```

The benchmark is non-authoritative. It cannot promote code, authorize execution, or write soak DBs.

## Corpus

Labeled `SYNTHETIC_TEST_DATA` memories with stable `BM-*` ids: facts, inferences, hypotheses, predictions, simulations, opinions, procedures, lessons, failures, experiments, distractors, contradictions, stale/superseded/unknown-age, and agent_A / agent_B private notes. Four domains: software, science, finance, operations.

## Metrics

Each result has numerator, denominator, value, threshold, status (`PASS`/`FAIL`/`NOT_MEASURED`/`NOT_APPLICABLE`), population, limitations, N, benchmark version.

Denominator 0 → `NOT_MEASURED` (never `PASS`).

No composite AGI score.

## Thresholds

`GOVERNANCE` invariants (leakage, unsupported SUPPORTED, nondeterminism, contradiction false-resolution) are floors that must not be lowered to hide failures.

`PROVISIONAL` floors (precision 0.5, etc.) are first governance expectations, **not** fitted to the current retriever. FAIL is evidence.

## Reproducibility

`comparable_payload` excludes wall-clock timing and host environment. Two isolated runs must serialize identically.

## Self-improvement safety

`WEAKNESS_DETECTED` and `IMPROVEMENT_CANDIDATE` are recorded. The benchmark does not apply patches.

## Limitations

Synthetic only. Small N. Keyword/domain retrieval. Causal/counterfactual NOT_IMPLEMENTED. Not soak evidence.
