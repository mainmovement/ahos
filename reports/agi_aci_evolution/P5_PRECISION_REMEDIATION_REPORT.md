# P5 PRECISION REMEDIATION REPORT

**PR:** #93 (DRAFT — do not merge, do not mark ready)  
**Branch:** `cursor/agi-aci-p5-typed-evidence-reasoning-9500`  
**Parent:** `ae66e3e1a8b257bdeb992ed50c7378ac8fbbf629`  
**Data label:** `SYNTHETIC_TEST_DATA`  
**Lane A:** `Lane-A integrity OK (36 files pinned)`  
**Soak:** not touched (`SOAK_DATABASE_TOUCHED=NO`)

This is not formal reasoning, entailment, AGI, or ACI.

Honest capability name: **governed typed eligibility + deterministic support-class fail-closed + critic-constrained templates**.

## Required rules

`LEXICAL_MATCH != EVIDENCE_SUPPORT`  
`RELEVANCE != ENTAILMENT`  
`ELIGIBLE_EVIDENCE != SUFFICIENT_EVIDENCE`

Positive verdicts require `DIRECT_SUPPORT` + `SUPPORTS`.  
`NON_SUPPORTING_MATCH` and `UNKNOWN_SUPPORT` refuse `WEAKLY_SUPPORTED` / `SUPPORTED`.

## P4.3 retrieval (unchanged; `retrieval.py` not edited)

Isolated benchmark, two runs, `equal=YES`:

| metric | value |
| --- | --- |
| precision | 0.9091 |
| recall | 1.0 |
| F1 | 0.9524 |
| Recall@1 | 0.7857 |
| Recall@3 | 0.9481 |
| Recall@5 | 0.9610 |
| Recall@10 | 1.0 |
| MATCH_REASON | 1.0 |
| generic-overlap FP | 0 |
| hard-mismatch reject | 1.0 |
| lookalike recall | 1.0 |
| contradiction pollution | 0 |
| unknown refusal | 1.0 |

## New support metrics (live `reason()` / bindings; no `or True`)

| metric | value | n | ground truth |
| --- | --- | --- | --- |
| lexical_match_without_support_rate | 1.0 (3/3) | 3 | labeled lexical cousins classified non-DIRECT |
| unsupported_positive_verdict_rate | 0.0 (0/13) | 13 | no-support probes including cafeteria×7 |
| direct_support_positive_rate | 1.0 (1/1) | 1 | exact-support DEDUCTIVE still positive |
| unknown_support_refusal_rate | 1.0 (3/3) | 3 | UNKNOWN_SUPPORT refused positive |

## Noted P4 provisional (not lowered)

`cross_domain_consistency` is now FAIL (finance retrieved context is INSUFFICIENT; science/ops/software WEAKLY).  
`p5_cross_domain_invariance` (one local fact) remains 1.0. Threshold not lowered.

## Hypothesis write-back

Option A: UNRESOLVED / INSUFFICIENT / CONTESTED do not write HYPOTHESIS, LESSON, or reusable INFERENCE. Episode records remain. Second episode does not retrieve an unresolved hypothesis as knowledge.

## P6 / FUTURE ARCHITECTURAL GAP

True semantic entailment, embeddings, and LLM judges are not implemented. Residual `UNKNOWN_SUPPORT` is fail-closed on purpose.
