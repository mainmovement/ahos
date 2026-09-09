# P4.2 Retrieval Benchmark Report

**Evaluator:** unchanged P4.1 suite (`architecture/cognitive/benchmark/`, version `p4.1.0`)  
**Data label:** `SYNTHETIC_TEST_DATA`  
**P4.1 baseline SHA:** `6e65f1573dea8c2fe91d6a181b25a20015e76fe1`  
**P4.2 implementation SHA:** `7349c0bb88cb3ae3f586213763e51058b02aab6f`  
**Lane-A freeze:** `Lane-A integrity OK (36 files pinned)`  
**Reproducibility:** two isolated runs, `comparable_payload` equal = YES  

This is **not** an AGI/ACI score. Deterministic retrieval relevance improved under the evaluated populations. FAIL remains FAIL when a provisional floor is missed.

## Comparison (P4.1 baseline vs P4.2)

| Metric | P4.1 | P4.2 | Delta | Status |
|---|---:|---:|---:|---|
| Precision | 0.0615 (20/325) | 0.2410 (20/83) | +0.1794 | FAIL → FAIL (improved, floor 0.5 unmet) |
| Recall | 1.0000 (20/20) | 1.0000 (20/20) | 0.0000 | PASS (protected) |
| F1 | 0.1159 | 0.3883 | +0.2724 | FAIL → FAIL (improved, floor 0.5 unmet) |
| Recall@1 | 0.0455 | 0.4221 | +0.3766 | FAIL → PASS |
| Recall@3 | 0.1364 | 0.9481 | +0.8117 | FAIL → PASS |
| Recall@5 | 0.6623 | 0.9610 | +0.2987 | PASS (improved) |
| Recall@10 | 0.8896 | 0.9870 | +0.0974 | PASS (improved) |
| MATCH_REASON correctness | 1.0000 (325/325) | 1.0000 (83/83) | 0.0000 | PASS |
| False failure application | 1.0000 | 0.0000 | −1.0000 | FAIL → PASS |
| Unknown refusal accuracy | 0.6667 | 1.0000 | +0.3333 | FAIL → PASS |
| Contradiction pollution | (not a P4.1 metric; implied by empty-query UNRESOLVED) | 0.0000 (0/11) | — | PASS |
| Empty-query pollution | (UNK-EMPTY-01 retrieved contra/FAILURE) | 0.0000 | — | PASS |
| Unrelated retrieval rate | 0.9385 (305/325) | 0.7590 (63/83) | −0.1794 | FAIL (floor MAX 0.5 unmet) |
| Same-domain false inclusion | (not separately numbered) | 0.7802 (71/91) | — | FAIL (floor MAX 0.5 unmet) |
| Incorrect lesson application | 0.5000 | 0.0000 | −0.5000 | PASS (improved) |
| Lesson reuse | 1.0000 | 1.0000 | 0.0000 | PASS |
| Failure recall | 1.0000 | 1.0000 | 0.0000 | PASS |
| Contradiction detection | 1.0000 | 1.0000 | 0.0000 | PASS |
| False contradiction resolution | 0.0000 | 0.0000 | 0.0000 | PASS |
| Namespace isolation | 1.0000 | 1.0000 | 0.0000 | PASS |
| Namespace leakage | 0.0000 | 0.0000 | 0.0000 | PASS |
| Adversarial resistance | 1.0000 | 1.0000 | 0.0000 | PASS |
| Stale ≠ false | 1.0000 | 1.0000 | 0.0000 | PASS |
| Provenance preservation | 1.0000 | 1.0000 | 0.0000 | PASS |
| Cross-domain consistency | 1.0000 | 1.0000 | 0.0000 | PASS |
| Context coverage | 0.2500 | 0.4643 | +0.2143 | FAIL → FAIL (tiny/zero budgets) |
| False certainty | 0.0000 | 0.0000 | 0.0000 | PASS |

P4.1 baseline file: `p4_2_p41_baseline.json`.  
P4.2 machine-readable run: `p4_2_retrieval_benchmark_latest.json`.

## Recall protection

| Requirement | Evidence |
|-------------|----------|
| Exact ID recall 100% | `RET-EXACT-01` retrieved only `BM-SW-TIMEOUT-FACT` with `exact_id` |
| Relevant contradiction intact | `RET-CONTRA-01` / `CONTRA-SW-01` / `CONTRA-SCI-01` both sides; detection 1.0 |
| Relevant failure intact | `failure_recall` 1.0; `RET-FAIL-01` hits `BM-SW-TIMEOUT-FAIL` |
| Relevant lesson intact | `lesson_reuse_rate` 1.0; `RET-LESSON-01` hits `BM-SW-TIMEOUT-LESSON` |
| Recall@5 / @10 not collapsed | 0.961 / 0.987 (both up) |
| Namespace isolation 100% | leakage numerator 0 |
| MATCH_REASON 100% | 83/83 justified |

Classification: **not a recall-collapse false improvement**. Precision rose because retrieved volume fell (325 → 83) while labeled hits stayed 20/20.

## Unknown / empty handling

`UNK-EMPTY-01` (“melting point of unobtainium-xyzzy”) now retrieves nothing (`NO_RELEVANT_MEMORY`). Verdict `INSUFFICIENT_EVIDENCE`. Unknown-refusal accuracy 3/3.

## Failure relevance

`FAIL-E3` (science telescope) no longer retrieves the operations deploy FAILURE. False-failure application 0.0. Similar deploy episode still retrieves it.

## Contradiction relevance

Seeded pairs remain retrievable when the query anchors one side. Unrelated queries do not ingest the contradiction graph (`contradiction_pollution_rate` 0/11).

`context_contradiction_preservation` is `NOT_MEASURED` on this run: the P4.1 probe reused `RET-KEYWORD-01`, which correctly no longer retrieves the software contradiction pair. Dedicated contradiction cases still PASS.

## Tests added

`tests/test_retrieval_relevance.py` — same-domain distractors, unrelated failures, contradiction pollution, empty/domain-only queries, relevant failure/contradiction, namespace, exact ID, historical stale, same failure class / different component, synonym-like timeout wording, rare-token DF gate, lesson vs unrelated same-domain lesson, superseded history, provenance survival, `NO_RELEVANT_MEMORY` contract.

148 targeted cognitive tests passed (benchmark + loop + memory + core + evolution + council + new relevance file). Pre-P4.2 P4.1 suite was 61 in that smaller file set; no pre-existing failures were hidden.

## Performance

Primary evaluator wall time ≈ 0.36s in this environment (isolated temp SQLite). Candidate generation remains `recent(limit=500)` over the 41-row corpus. Correctness first; no unbounded production scan was introduced.

## Soak / Lane A

- SOAK DATABASE TOUCHED: NO
- SOAK RUNTIME RESTARTED: NO
- T0 RESET: NO
- Lane A: 36/36

## Limitations

- SYNTHETIC_TEST_DATA only; not soak evidence
- Precision still below the provisional 0.5 floor
- Two-token overlap (`retry`+`recover`) still retrieves cross-domain structural cousins that P4.1 labels do not count as relevant
- Same-domain timeout cluster still dominates namespace / lesson queries (labeled FPs)
- Closed inflection table is small and explicit; not general morphology
- In-domain DF gate uses the current `recent()` snapshot
- Not AGI, not ACI, not a world model, not authorization to promote or trade
