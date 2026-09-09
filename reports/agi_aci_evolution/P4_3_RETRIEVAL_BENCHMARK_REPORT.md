# P4.3 Retrieval Benchmark Report

**Evaluator:** unchanged P4.1 case/label suite (`p4.1.0`) plus additive P4.3 metrics  
**Data label:** `SYNTHETIC_TEST_DATA`  
**P4.2 baseline SHA:** `eb1dbcf883bf3cba94e18881c9bea9a5252a88af`  
**P4.3 implementation SHA:** `b0ffffb5232ed18e05f1f02cb9e57324409cc8b3`  
**Lane-A freeze:** `Lane-A integrity OK (36 files pinned)`  
**Reproducibility:** two isolated runs, `comparable_payload` equal = YES  
**Primary evaluator wall time:** ≈ 0.34s

This is **not** an AGI/ACI score. Deterministic retrieval discrimination improved under the evaluated populations.

## Comparison (P4.2 → P4.3)

| Metric | P4.2 | P4.3 | Delta | Status |
|---|---:|---:|---:|---|
| Precision | 0.2410 (20/83) | 0.9091 (20/22) | +0.6681 | FAIL → PASS |
| Recall | 1.0000 (20/20) | 1.0000 (20/20) | 0.0000 | PASS (protected) |
| F1 | 0.3883 | 0.9524 | +0.5641 | FAIL → PASS |
| Recall@1 | 0.4221 | 0.7857 | +0.3636 | PASS (improved) |
| Recall@3 | 0.9481 | 0.9481 | 0.0000 | PASS |
| Recall@5 | 0.9610 | 0.9610 | 0.0000 | PASS |
| Recall@10 | 0.9870 | 1.0000 | +0.0130 | PASS |
| MATCH_REASON | 1.0000 | 1.0000 (22/22) | 0 | PASS |
| Unrelated retrieval | 0.7590 | 0.0909 (2/22) | −0.6681 | FAIL → PASS |
| Same-domain false inclusion | 0.7802 | 0.2308 (6/26) | −0.5494 | FAIL → PASS |
| False failure application | 0.0000 | 0.0000 | 0 | PASS |
| Contradiction pollution | 0.0000 | 0.0000 | 0 | PASS |
| Unknown refusal | 1.0000 | 1.0000 | 0 | PASS |
| Incorrect lesson application | 0.0000 | 0.0000 | 0 | PASS |
| Context coverage | 0.4643 | 0.5714 | +0.1071 | FAIL → PASS |
| Namespace isolation | 1.0000 | 1.0000 | 0 | PASS |
| Provenance preservation | 1.0000 | 1.0000 | 0 | PASS |
| Stale ≠ false | 1.0000 | 1.0000 | 0 | PASS |
| Lookalike rejection | — | 1.0000 (7/7) | — | PASS |
| Hard-mismatch rejection | — | 1.0000 | — | PASS |
| Generic-overlap false inclusion | — | 0.0000 | — | PASS |
| Structured-mismatch false inclusion | — | 0.0000 | — | PASS |
| Relevant-lookalike recall | — | 1.0000 (7/7) | — | PASS |
| Task compatibility accuracy | — | 1.0000 (2/2) | — | PASS |

No benchmark FAIL metrics on this run. `context_contradiction_preservation` remains `NOT_MEASURED` (the P4.1 probe still uses `RET-KEYWORD-01`, which correctly does not retrieve the software contradiction pair). Dedicated contradiction cases still detect both sides.

## Recall protection

| Path | Evidence |
|------|----------|
| Exact ID | `RET-EXACT-01` → only `BM-SW-TIMEOUT-FACT` |
| Relevant timeout cluster | `RET-KEYWORD-01` hits all 7 `TIMEOUT_RELEVANT` |
| Relevant failure | `RET-FAIL-01` / `failure_recall` 1.0 |
| Relevant lesson | `RET-LESSON-01` / `lesson_reuse_rate` 1.0 |
| Relevant contradiction | `RET-CONTRA-01` both IDs; detection 1.0 |
| Relevant hyp/exp | `RET-HYP-01` / `RET-EXP-01` exact structured hits |
| Historical stale | `RET-TEMP-01` includes `BM-SW-OLD-FACT` |
| Namespace | `RET-NS-A/B` only the private note |

Classification: **not a recall-collapse false improvement**.

## Tests

`tests/test_retrieval_lookalike.py` — 15 required classes plus adversarial lookalike poster, unknown-component neutrality, unscoped private-note isolation.

167 targeted cognitive tests passed (lookalike + P4.2 relevance + loop + memory + core + benchmark + evolution + council).

## Soak / Lane A

- SOAK DATABASE TOUCHED: NO
- SOAK RUNTIME RESTARTED: NO
- T0 RESET: NO
- Lane A: 36/36
- validate_imports: PASS (restore `reports/*.json` side effects)

## Limitations

- SYNTHETIC only; small N
- `BM-SHARED` still matches `{retry, timeout}` on ANALYZE timeout queries
- `BM-SW-TIMEOUT-HYP` still matches `{rate, timeout}` on the temporal rate query
- Most memories still lack structured component/operation; those fields stay neutral
- Closed inflection table and domain-span statistics are snapshot-local
- Not AGI, not causality, not soak evidence
