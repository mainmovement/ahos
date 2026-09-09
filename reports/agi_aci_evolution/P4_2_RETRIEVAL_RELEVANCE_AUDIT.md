# P4.2 Retrieval Relevance Audit

**UTC date:** 2026-09-09  
**Base:** `origin/main` `6e65f1573dea8c2fe91d6a181b25a20015e76fe1` (PR #90 / P4.1 merge)  
**Branch:** `cursor/agi-aci-p4-2-retrieval-relevance-tightening-9500`  
**Soak:** `run_1788987515_7ad11528` — not contacted  
**Lane A:** 36/36 before and after

This is a query-time correction audit. It is **not** an intelligence score and not a claim that AHOS became smarter.

## A. Current repository (inspected)

| Surface | State at P4.2 start |
|---------|---------------------|
| P4.1 benchmark | `architecture/cognitive/benchmark/` on main; corpus 41 `BM-*` memories; cases unchanged |
| P3 retriever | `architecture/cognitive/loop/retrieval.py` — `same_domain`, `failure_relationship`, `contradiction_relationship`, `explicit_relationship`, `stale_but_queryable` were each sufficient alone |
| P2 store | Unchanged. No memory rewrite, no soak DB, no schema migration |
| Active soak | Windows run_id `run_1788987515_7ad11528` — not opened, not restarted |
| Lane A | `scripts/freeze_lane_a.py` → `Lane-A integrity OK (36 files pinned)` |

P4.1 baseline captured **before** retrieval edits: `p4_2_p41_baseline.json`.

## B. Root cause (from code, not from the directive)

In the pre-P4.2 `MemoryRetriever.retrieve()` loop, a candidate was accepted if **any** of these fired:

1. `exact_id` / structured hypothesis or experiment id
2. `task_keyword_match` (raw 4+ character token overlap, including schema words)
3. `same_domain` — `query.domain == memory.domain`
4. `failure_relationship` — `memory_type == FAILURE` with no task overlap
5. `contradiction_relationship` — any row that had a CONTRADICTS edge
6. `explicit_relationship` — any row returned by `find_related_memories`
7. `stale_but_queryable` — STALE status alone

Empty / unknown questions still scanned `recent()` and therefore pulled global FAILURE and contradiction rows. The loop then saw `contradiction_present` and emitted `UNRESOLVED` (`UNK-EMPTY-01`).

That matches the P4.1 measurements: precision 20/325, recall 1.0, false-failure application 1.0, unknown-refusal 2/3.

## C. Design correction

Contextual signals may **rank** or **expand**. They must not **create** relevance from nothing.

Pipeline actually implemented:

```text
QUERY
  → normalize_query (lowercase, 4+ char tokens, stopwords, closed inflections, intents)
  → scan recent() candidates (bounded)
  → hard relevance filter (anchors only)
  → one-hop relationship expansion from anchors
  → annotate domain / stale / type-compatibility (ranking only)
  → integer score + memory_id tie-break
  → optional top-k
  → RetrievalResult (MATCH_REASON + rejection reasons + no_relevant_memory)
```

### Anchors (sufficient)

- exact requested memory id
- same hypothesis_id / experiment_id
- source_id substring of the question
- **strong lexical overlap:** ≥2 canonical content tokens
- **rare same-domain lexical overlap:** exactly 1 canonical token **and** that token’s in-domain document frequency ≤ 3
- **failure fingerprint:** same strength rule over statement + `failure_type` / `component` / `observed_failure` / `attempted_action`, after stripping schema labels

### Not anchors

- same domain
- mere FAILURE / LESSON / recency / STALE
- unanchored CONTRADICTS / RELATED / SUPERSEDES edges
- a single common in-domain token (`timeout`, `measurement`, …)
- schema words printed into statements (`FAILURE`, `LESSON`, …)

### Expansion

`find_contradictions` / `find_related_memories` run **only** from accepted anchors (one hop). Reasons: `contradiction_of_relevant_memory`, `related_to_relevant_memory`.

### Empty query

No identifier, no structured key, no content tokens → `NO_RELEVANT_MEMORY`. Rejections labeled `NO_QUERY_SIGNAL`. The loop then returns `INSUFFICIENT_EVIDENCE` / `UNKNOWN`, not a polluted `UNRESOLVED`.

`NO_RELEVANT_MEMORY` means: no sufficiently relevant stored evidence for this query. It does not mean the proposition is false, the store is empty, or the system failed.

## D. What was not changed

- P4.1 corpus, case labels, and GOVERNANCE/PROVISIONAL thresholds (except **additive** P4.2 pollution metric floors)
- Memory storage / provenance / soak / Lane A / production observation
- No embeddings, no LLM judge, no self-modification

## E. Ranking (integer, documented)

| Signal | Score |
|--------|------:|
| exact_id | 100 |
| hypothesis / experiment key | 80 |
| source_id in question | 70 |
| failure_fingerprint | 60 |
| lexical (10 per token, cap 50) | ≤50 |
| contradiction expansion | 45 |
| related expansion | 35 |
| type_compatibility (lesson/failure/history intent on an already accepted item) | 25 |
| same_domain boost | +5 |
| temporal_proximity boost | +3 |

Tie-break: `memory_id` ascending. Identical inputs → identical order.

## F. Rejection reasons

`DOMAIN_ONLY`, `WEAK_LEXICAL_OVERLAP`, `UNRELATED_FAILURE`, `UNRELATED_CONTRADICTION`, `NO_QUERY_SIGNAL`, `NAMESPACE_BLOCKED`, `BELOW_RELEVANCE_THRESHOLD`.

## G. Remaining measured weaknesses

Precision is still 20/83 (0.241) vs the provisional 0.5 floor. Timeout/retry queries still retrieve same-domain lookalikes and some cross-domain retry-recovery rows that share two content tokens. That is unlabeled under P4.1 case sets — a measurement limit, not a license to weaken labels.

Context coverage remains 0.464 under tiny/zero budgets (provisional floor 0.5).
