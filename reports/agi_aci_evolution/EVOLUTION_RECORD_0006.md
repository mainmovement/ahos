# EVOLUTION_RECORD_0006

```text
Record ID: EVOLUTION_RECORD_0006
UTC timestamp: 2026-09-09
Git SHA: (implementation commit on cursor/agi-aci-p4-2-retrieval-relevance-tightening-9500)
Base SHA: 6e65f1573dea8c2fe91d6a181b25a20015e76fe1
Branch: cursor/agi-aci-p4-2-retrieval-relevance-tightening-9500
Status: IMPLEMENTED (suite executed; some provisional metrics still FAIL honestly)
Objective: P4.2 deterministic retrieval relevance tightening
Trigger: MASTER CURSOR DIRECTIVE P4.2 after PR #90 / P4.1 measured over-retrieval
Audit: P4_2_RETRIEVAL_RELEVANCE_AUDIT.md — same_domain / unanchored FAILURE / unanchored contradiction were sufficient alone
Architecture decision: Query-time hard relevance gates + one-hop expansion from anchors; no embeddings; no LLM judge; no corpus rewrite; P4.1 cases/labels/thresholds not weakened
Files changed: architecture/cognitive/loop/retrieval.py; match_reasons.py; evaluator.py (additive pollution metrics); thresholds.py (additive floors only); tests/test_retrieval_relevance.py; reports/agi_aci_evolution P4.2 artifacts; DOC_TRUTH_MAP / index / gap updates
Tests: 148 passed (retrieval relevance + benchmark + loop + memory + core + evolution + council); freeze 36/36; validate_imports PASS after restoring validate side-effect JSON
Benchmark: P4.2_RETRIEVAL_BENCHMARK_REPORT.md + p4_2_retrieval_benchmark_latest.json; reproducibility equal
Measured movement: precision 0.0615→0.2410; F1 0.1159→0.3883; Recall@1 0.0455→0.4221; Recall@3 0.1364→0.9481; false_failure 1.0→0.0; unknown_refusal 0.6667→1.0; recall 1.0 protected; MATCH_REASON 1.0
Failures (honest): retrieval_precision 0.2410 (20/83) vs floor 0.5; retrieval_f1 0.3883; context_coverage 0.4643; unrelated_retrieval_rate 0.7590; same_domain_false_inclusion_rate 0.7802
Limitations: SYNTHETIC only; small N; not soak; not AGI; two-token cross-domain retry/recover still unlabeled FP
Security: PAPER_ONLY; L1_ANALYZE; no live execution; no self-modification
Soak impact: none — SOAK DATABASE TOUCHED: NO; RUNTIME RESTARTED: NO; T0 RESET: NO
Lane-A impact: none — 36/36
Rollback: revert branch/PR; P4.1 corpus remains the regression fixture
Capability classification: retrieval relevance PARTIAL (measured improvement, precision floor unmet); AGI/ACI NOT_IMPLEMENTED
Remaining gaps: ACI-GAP-010 still not a six-baseline AGI suite; residual same-domain/lookalike FPs are the highest-value measured weakness
Next action: Rank/filter same-domain lookalikes and two-token structural cousins without collapsing labeled recall — do not add embeddings, soak ingest, or a world model
```
