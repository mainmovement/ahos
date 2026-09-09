# P4.3 Lookalike Discrimination Audit

**UTC date:** 2026-09-09  
**Base:** `origin/main` `eb1dbcf883bf3cba94e18881c9bea9a5252a88af` (PR #91 / P4.2 merge)  
**Branch:** `cursor/agi-aci-p4-3-semantic-lookalike-discrimination-9500`  
**Soak:** `run_1788987515_7ad11528` — not contacted  
**Lane A:** 36/36 before and after

This is a query-time discrimination audit. It is **not** an intelligence score.

## A. Baseline (immutable)

Captured on merged P4.2 **before** P4.3 edits: `p4_3_p42_baseline.json`.

| Metric | P4.2 |
|---|---:|
| Precision | 0.2410 (20/83) |
| Recall | 1.0000 (20/20) |
| F1 | 0.3883 |
| Recall@1 / @3 / @5 / @10 | 0.4221 / 0.9481 / 0.9610 / 0.9870 |
| Unrelated retrieval | 0.7590 (63/83) |
| Same-domain false inclusion | 0.7802 (71/91) |
| MATCH_REASON | 1.0000 |
| False failure / contradiction pollution / empty-query pollution | 0 / 0 / 0 |
| Unknown refusal | 1.0000 |
| Context coverage | 0.4643 |

## B. Root cause (measured, not assumed)

Per-case dump of the 63 unlabeled retrievals showed two dominant patterns:

1. **Same-domain generic two-token overlap** `{retry, timeout}` (software DF 10 and 17). P4.2 treated ≥2 tokens as a strong lexical anchor. That flooded LEARN / FAIL / HYP / NS cases with the whole timeout cluster, plus `BM-A-PRIV` / `BM-B-PRIV` / `BM-SHARED`.
2. **Cross-domain operation cousins** `{recover, retry}` on `RET-KEYWORD-01` pulling finance/science/operations fact+lesson rows. Both tokens span 4 domains.
3. **Lookalike poster** `{http, timeout}` (`BM-SW-TIMEOUT-LOOKALIKE`) and **SIMULATION** `{recover, timeout}`.

Token overlap was being treated as task identity.

## C. Fields that exist (no invented metadata)

Used as-is:

- `CognitiveTask.domain`, `task_type`, `agent_id`, `requested_evidence`, `constraints` (`hypothesis_id`, `experiment_id`, `component`, `operation`, `failure_type`)
- `MemoryRecord.domain`, `agent_namespace`, `hypothesis_id`, `experiment_id`, `epistemic_kind`, `memory_type`, `payload.component|operation|failure_type|applicability`
- Deterministic document-frequency / domain-span over the visible `recent()` snapshot

Not invented: object graphs, embeddings, external vocabularies.

Limitation: most corpus rows have no `component`/`operation`. Those fields are **neutral when missing**. UNKNOWN ≠ mismatch.

## D. Design

Hard mismatch (explicit vs explicit, both non-UNKNOWN) rejects and cannot be outscored by lexical points.

Lexical gates:

- Cross-domain: need ≥3 overlap tokens **or** a token whose domain-span is 1
- Generic lookalike: query has a multi-domain operation token (`retry`/`recover`) but overlap contains none of them and overlap < 3
- LEARN / lesson intent: lexical path only for `LESSON`
- failure intent: lexical path only for `FAILURE` / fingerprint
- Structured query (exact id / hyp / exp): lexical-only candidates are not anchors
- OPINION / PREDICTION / SIMULATION: not lexical-only anchors
- Unscoped query: skip namespaced private rows
- Namespaced query: shared empty-namespace rows need a structured key

Relationship expansion remains one-hop from anchors.

## E. Remaining measured lookalikes

After P4.3, unlabeled retrievals on the P4.1 cases are:

- `RET-KEYWORD-01`: `BM-SHARED` (shared note still has `{retry, timeout}`)
- `RET-TEMP-01`: `BM-SW-TIMEOUT-HYP` (`{rate, timeout}`)

Those are the residual same-domain false inclusions.
