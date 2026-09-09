# COGNITIVE_LOOP_BENCHMARK

**Status:** small deterministic suite EXECUTED on SYNTHETIC_TEST_DATA.  
**Not** an AGI benchmark. **Not** soak performance. **No** fabricated intelligence score.

## Suite (P3)

| # | Question | Result (unit) | Data label |
|---|----------|---------------|------------|
| 1 | Memory retrieval | PASS — MATCH_REASON populated | SYNTHETIC_TEST_DATA |
| 2 | Contradiction detection | PASS — contradiction_present; UNRESOLVED/CONTESTED | SYNTHETIC_TEST_DATA |
| 3 | Temporal reasoning | PASS — event vs ingest time; STALE not current | SYNTHETIC_TEST_DATA |
| 4 | Uncertainty handling | PASS — INSUFFICIENT_EVIDENCE / UNKNOWN / NOT_IMPLEMENTED allowed | SYNTHETIC_TEST_DATA |
| 5 | Hypothesis structure | PASS — HYP- id + falsification_condition; novelty ≠ truth | SYNTHETIC_TEST_DATA |
| 6 | Falsification | PARTIAL — string condition required; no live runner | SYNTHETIC_TEST_DATA |
| 7 | Failure recall | PASS — next task retrieves FAILURE | SYNTHETIC_TEST_DATA |
| 8 | Lesson reuse | PASS — MEMORY+LOOP 1.0 vs NO_MEMORY 0.0 | SYNTHETIC_TEST_DATA |
| 9 | Cross-domain | PASS — finance/science/software/operations adapters | SYNTHETIC_TEST_DATA |
| 10 | Provenance integrity | PASS — integrity_check ok; producer+source_id present | SYNTHETIC_TEST_DATA |

## NO_MEMORY vs MEMORY+LOOP

Measured by `run_memory_vs_no_memory` / `test_memory_vs_no_memory_benchmark`:

| Metric | NO_MEMORY | MEMORY+LOOP | Measured improvement |
|--------|-----------|-------------|----------------------|
| lesson_reuse_rate | 0.0 | 1.0 | +1.0 (presence of prior LESSON in retrieve) |
| unsupported_claim_rate | 0.0 | 0.0 | none (P3 downgrades SUPPORTED) |

Improvement means: the second episode can use the first episode's lesson.
It does **not** mean AHOS is more intelligent, calibrated on soak, or AGI-capable.

## Metric definitions

See `architecture/cognitive/loop/metrics.py`. Unmeasured population rates are
labelled unmeasured. Do not invent percentages.

## Limitations

- N is tiny (synthetic fixtures)
- Keyword retrieval ≠ semantic understanding
- Causal/counterfactual modes excluded (NOT_IMPLEMENTED)
- No soak rows
- Latency: e2e cycle asserted < 5s on Cloud Linux; not a production SLA
