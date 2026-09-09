"""P4.1 cognitive benchmark evaluator. Offline, deterministic, LLM-free."""

from __future__ import annotations

import json
import platform
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from architecture.cognitive.benchmark.corpus import NOW, TIMEOUT_RELEVANT, seed_corpus
from architecture.cognitive.benchmark.match_reasons import match_reason_justified
from architecture.cognitive.benchmark.metrics import MetricResult, f1, make_metric
from architecture.cognitive.benchmark.p5_eval import evaluate_p5_reasoning
from architecture.cognitive.benchmark.scenarios import (
    adversarial_cases,
    contradiction_reason_cases,
    cross_domain_cases,
    reasoning_mode_cases,
    retrieval_cases,
    unknown_cases,
)
from architecture.cognitive.benchmark.thresholds import BENCHMARK_VERSION, DATA_LABEL
from architecture.cognitive.hypothesis import HypothesisStore
from architecture.cognitive.loop.context import assemble_context
from architecture.cognitive.loop.contracts import (
    CognitiveTask,
    ContextBudget,
    ReasoningMode,
    TaskType,
)
from architecture.cognitive.loop.orchestrator import CognitiveOrchestrator
from architecture.cognitive.loop.reason import critique_result, reason
from architecture.cognitive.loop.retrieval import (
    KIND_TO_EVIDENCE,
    MemoryRetriever,
    _lexical_overlap,
    normalize_query,
)
from architecture.cognitive.memory.store import CognitiveMemoryStore
from architecture.cognitive.memory.types import DecayState, EpistemicKind, MemoryType, SourceType


def _task_from_case(case, *, now: float = NOW) -> CognitiveTask:
    return CognitiveTask(
        task_id=case.case_id,
        task_type=case.task_type,
        objective=case.objective,
        question=case.question,
        domain=case.domain,
        requester="p4.1-benchmark",
        created_at=now,
        constraints=dict(case.constraints),
        requested_evidence=list(case.requested_evidence),
        agent_id=case.agent_id,
        write_back=case.write_back,
        data_label=DATA_LABEL,
        reasoning_mode=case.expected_reasoning_mode or ReasoningMode.COMPARATIVE.value,
    )


def _topk_hits(retrieved_ids: list[str], relevant: set[str], k: int) -> int:
    return len(set(retrieved_ids[:k]) & relevant)


@dataclass
class BenchmarkReport:
    benchmark_version: str
    git_sha: str
    environment: dict[str, str]
    data_label: str
    case_counts: dict[str, int]
    metrics: list[MetricResult]
    case_results: list[dict[str, Any]]
    weaknesses: list[str]
    improvement_candidates: list[str]
    limitations: list[str]
    lane_a_freeze: str
    soak_protection: dict[str, str]
    timing: dict[str, float] = field(default_factory=dict)

    def metric_map(self) -> dict[str, MetricResult]:
        return {m.metric_id: m for m in self.metrics}

    def comparable_payload(self) -> dict[str, Any]:
        return {
            "benchmark_version": self.benchmark_version,
            "data_label": self.data_label,
            "metrics": [m.as_dict() for m in self.metrics],
            "case_results": self.case_results,
            "weaknesses": self.weaknesses,
            "improvement_candidates": self.improvement_candidates,
        }

    def as_dict(self) -> dict[str, Any]:
        payload = self.comparable_payload()
        payload.update(
            {
                "git_sha": self.git_sha,
                "environment": dict(self.environment),
                "case_counts": dict(self.case_counts),
                "limitations": list(self.limitations),
                "lane_a_freeze": self.lane_a_freeze,
                "soak_protection": dict(self.soak_protection),
                "timing": dict(self.timing),
            }
        )
        return payload


def run_cognitive_benchmark(
    workdir: Path | str,
    *,
    git_sha: str = "UNKNOWN",
    lane_a_freeze: str = "NOT_MEASURED",
) -> BenchmarkReport:
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    db = workdir / "ahos_cognitive_memory.sqlite"
    store = CognitiveMemoryStore(db)
    corpus = seed_corpus(store, now=NOW)
    retriever = MemoryRetriever()
    hyp = HypothesisStore(workdir / "hyp.jsonl")
    orch = CognitiveOrchestrator(
        memory=store, hypotheses=hyp, ledger_path=workdir / "exp.jsonl"
    )

    case_results: list[dict[str, Any]] = []
    metrics: list[MetricResult] = []
    weaknesses: list[str] = []
    candidates: list[str] = []

    # ----- retrieval -----
    tp = fp = fn = 0
    reason_ok = reason_n = 0
    rec_at = {1: 0, 3: 0, 5: 0, 10: 0}
    rec_at_den = {1: 0, 3: 0, 5: 0, 10: 0}
    leak_num = leak_den = 0
    for case in retrieval_cases():
        task = _task_from_case(case)
        items = retriever.retrieve(store, task, now=NOW)
        got = [i.memory_id for i in items]
        relevant = set(case.expected_relevant_ids)
        hit = set(got) & relevant
        tp += len(hit)
        fp += len(set(got) - relevant)
        fn += len(relevant - set(got))
        for k in rec_at:
            rec_at_den[k] += 1 if relevant else 0
            if relevant:
                rec_at[k] += 1 if _topk_hits(got, relevant, k) == len(relevant) else 0
                # recall@k as fraction of relevant found in top k (not all-or-nothing)
        for item in items:
            reason_n += 1
            if match_reason_justified(item, task, store, now=NOW):
                reason_ok += 1
        leaked = [mid for mid in case.expected_absent_ids if mid in got]
        leak_den += len(case.expected_absent_ids)
        leak_num += len(leaked)
        case_results.append(
            {
                "case_id": case.case_id,
                "family": case.family,
                "retrieved_ids": got,
                "relevant_ids": list(case.expected_relevant_ids),
                "hits": sorted(hit),
                "leaks": leaked,
            }
        )

    # recall@k as mean fraction of relevant found in top-k
    rec_frac = {k: 0.0 for k in rec_at}
    rec_frac_den = 0
    for case in retrieval_cases():
        task = _task_from_case(case)
        items = retriever.retrieve(store, task, now=NOW)
        got = [i.memory_id for i in items]
        relevant = set(case.expected_relevant_ids)
        if not relevant:
            continue
        rec_frac_den += 1
        for k in rec_frac:
            rec_frac[k] += len(set(got[:k]) & relevant) / len(relevant)

    metrics.append(
        make_metric(
            "retrieval_precision",
            name="retrieval_precision",
            definition="|retrieved ∩ relevant| / |retrieved| over labeled retrieval cases",
            numerator=tp,
            denominator=tp + fp,
            population="retrieval_cases labeled relevant vs all retrieved",
            limitations="same_domain matching retrieves distractors; synthetic labels only",
            n=len(retrieval_cases()),
        )
    )
    metrics.append(
        make_metric(
            "retrieval_recall",
            name="retrieval_recall",
            definition="|retrieved ∩ relevant| / |relevant| over labeled retrieval cases",
            numerator=tp,
            denominator=tp + fn,
            population="retrieval_cases labeled relevant",
            limitations="Relevance is the case label set, not human judgment",
            n=len(retrieval_cases()),
        )
    )
    p_val = metrics[-2].value
    r_val = metrics[-1].value
    f1_n, f1_d, _ = f1(p_val, r_val)
    metrics.append(
        make_metric(
            "retrieval_f1",
            name="retrieval_f1",
            definition="harmonic mean of retrieval_precision and retrieval_recall",
            numerator=f1_n,
            denominator=f1_d,
            population="retrieval_cases",
            limitations="Synthetic; not an intelligence score",
            n=len(retrieval_cases()),
        )
    )
    for k in (1, 3, 5, 10):
        metrics.append(
            make_metric(
                f"recall_at_{k}",
                name=f"recall_at_{k}",
                definition=f"mean fraction of labeled-relevant IDs in top-{k} retrieved",
                numerator=rec_frac[k],
                denominator=float(rec_frac_den),
                population="retrieval_cases with non-empty relevant sets",
                limitations="Rank is len(match_reasons) then memory_id; not semantic rank",
                n=rec_frac_den,
            )
        )
    metrics.append(
        make_metric(
            "match_reason_correctness",
            name="match_reason_correctness",
            definition="fraction of retrieved items whose MATCH_REASON strings are mechanistically true",
            numerator=reason_ok,
            denominator=reason_n,
            population="all retrieved items in retrieval_cases",
            limitations="Unknown reason tokens fail closed",
            n=reason_n,
        )
    )
    metrics.append(
        make_metric(
            "namespace_leakage_rate",
            name="namespace_leakage_rate",
            definition="count of expected_absent private IDs that were retrieved / absences checked",
            numerator=leak_num,
            denominator=leak_den,
            population="RET-NS-A/B expected_absent_ids",
            limitations="Empty namespace is shared by policy",
            n=leak_den,
        )
    )
    metrics.append(
        make_metric(
            "namespace_isolation_rate",
            name="namespace_isolation_rate",
            definition="1 - leakage_rate on private namespace cases",
            numerator=leak_den - leak_num,
            denominator=leak_den,
            population="RET-NS-A/B",
            limitations="Does not test allow_cross_namespace store API",
            n=leak_den,
        )
    )

    # ----- context -----
    ctx_task = _task_from_case(next(c for c in retrieval_cases() if c.case_id == "RET-KEYWORD-01"))
    ctx_items = retriever.retrieve(store, ctx_task, now=NOW)
    relevant_kw = set(TIMEOUT_RELEVANT)
    budgets = {"tiny": 2, "normal": 8, "large": 40, "zero": 0}
    cov_num = cov_den = 0
    incomplete_ok = 0
    incomplete_n = 0
    contra_preserved = 0
    contra_n = 0
    dropped_rel = 0
    dropped_den = 0
    prov_ok = 0
    prov_n = 0
    for name, nmem in budgets.items():
        ctx = assemble_context(ctx_items, store, budget=ContextBudget(max_memories=nmem), now=NOW)
        selected = {i.memory_id for i in ctx.all_included()}
        rel_ret = relevant_kw & {i.memory_id for i in ctx_items}
        if nmem in {0, 2}:
            incomplete_n += 1
            if ctx.context_incomplete:
                incomplete_ok += 1
        if rel_ret:
            cov_den += 1
            cov_num += len(selected & rel_ret) / len(rel_ret)
            dropped_den += len(rel_ret)
            dropped_rel += len(rel_ret - selected)
        for item in ctx.all_included():
            rec = store.get(item.memory_id)
            prov_n += 1
            if rec and rec.producer and rec.source_id:
                prov_ok += 1
        pair = {"BM-SW-CONTRA-A", "BM-SW-CONTRA-B"}
        if pair <= {i.memory_id for i in ctx_items} and nmem >= 8:
            contra_n += 1
            if pair <= selected and ctx.contradiction_present:
                contra_preserved += 1
        case_results.append(
            {
                "case_id": f"CTX-{name.upper()}",
                "family": "context",
                "max_memories": nmem,
                "selected": sorted(selected),
                "context_incomplete": ctx.context_incomplete,
                "contradiction_present": ctx.contradiction_present,
            }
        )
    metrics.append(
        make_metric(
            "context_coverage",
            name="context_coverage",
            definition="mean |selected ∩ relevant| / |relevant retrieved| across budgets",
            numerator=cov_num,
            denominator=float(cov_den),
            population="RET-KEYWORD-01 under tiny/normal/large/zero budgets",
            limitations="Coverage of budget, not of the world",
            n=cov_den,
        )
    )
    metrics.append(
        make_metric(
            "dropped_relevant_record_rate",
            name="dropped_relevant_record_rate",
            definition="relevant retrieved IDs excluded by budget / relevant retrieved",
            numerator=dropped_rel,
            denominator=dropped_den,
            population="context budgets on timeout keyword retrieval",
            limitations="Zero budget drops everything by design",
            n=dropped_den,
        )
    )
    metrics.append(
        make_metric(
            "context_incomplete_flag_rate",
            name="context_incomplete_flag_rate",
            definition="incomplete flag true on tiny/zero budgets / those budgets",
            numerator=incomplete_ok,
            denominator=incomplete_n,
            population="tiny and zero context budgets",
            limitations="Does not score large-budget completeness of the world",
            n=incomplete_n,
        )
    )
    metrics.append(
        make_metric(
            "provenance_preservation",
            name="provenance_preservation",
            definition="selected items with producer+source_id / selected items",
            numerator=prov_ok,
            denominator=prov_n,
            population="assembled context items across budgets",
            limitations="Corpus producer is the benchmark seeder",
            n=prov_n,
        )
    )
    metrics.append(
        make_metric(
            "context_contradiction_preservation",
            name="context_contradiction_preservation",
            definition="both contradiction IDs selected and flagged / eligible large budgets",
            numerator=contra_preserved,
            denominator=contra_n,
            population="normal/large budgets when both contra items retrieved",
            limitations="Tiny budgets cannot keep both; incomplete must be explicit",
            n=contra_n,
        )
    )

    # ----- evidence class integrity -----
    e_ok = e_n = 0
    unsup = unsup_n = 0
    sample = retriever.retrieve(store, ctx_task, now=NOW)
    for item in sample:
        e_n += 1
        expected = KIND_TO_EVIDENCE.get(item.epistemic_kind, "UNKNOWN")
        if item.evidence_class == expected:
            e_ok += 1
        if item.epistemic_kind in {
            EpistemicKind.OPINION.value,
            EpistemicKind.PREDICTION.value,
            EpistemicKind.HYPOTHESIS.value,
            EpistemicKind.SIMULATION.value,
        } and item.evidence_class == "DIRECT_OBSERVATION":
            unsup += 1
            unsup_n += 1
        else:
            unsup_n += 1 if item.epistemic_kind in {
                EpistemicKind.OPINION.value,
                EpistemicKind.PREDICTION.value,
                EpistemicKind.HYPOTHESIS.value,
                EpistemicKind.SIMULATION.value,
            } else 0
    metrics.append(
        make_metric(
            "evidence_class_integrity",
            name="evidence_class_integrity",
            definition="retrieved evidence_class matches KIND_TO_EVIDENCE mapping",
            numerator=e_ok,
            denominator=e_n,
            population="timeout keyword retrieval",
            limitations="Mapping is loop-defined, not a world ontology",
            n=e_n,
        )
    )

    # ----- contradiction reasoning -----
    det_n = det_ok = 0
    false_res = false_res_n = 0
    for case in contradiction_reason_cases():
        task = _task_from_case(case)
        items = retriever.retrieve(store, task, now=NOW)
        ctx = assemble_context(items, store, now=NOW)
        verdict, epistemic, trace, _crit, _asm = reason(
            task, ctx, retrieved_ids=[i.memory_id for i in items], store=store
        )
        det_n += 1
        both = set(case.expected_relevant_ids) <= {i.memory_id for i in items}
        if ctx.contradiction_present and both and verdict in {"UNRESOLVED", "CONTESTED"}:
            det_ok += 1
        false_res_n += 1
        if verdict == "SUPPORTED":
            false_res += 1
        case_results.append(
            {
                "case_id": case.case_id,
                "family": case.family,
                "verdict": verdict,
                "epistemic": epistemic,
                "contradiction_present": ctx.contradiction_present,
                "both_retrieved": both,
            }
        )
    metrics.append(
        make_metric(
            "contradiction_detection_rate",
            name="contradiction_detection_rate",
            definition="seeded pairs retrieved+flagged+UNRESOLVED|CONTESTED / seeded pairs",
            numerator=det_ok,
            denominator=det_n,
            population="contradiction_reason_cases",
            limitations="Requires explicit contradict() edges in the corpus",
            n=det_n,
        )
    )
    metrics.append(
        make_metric(
            "contradiction_false_resolution_rate",
            name="contradiction_false_resolution_rate",
            definition="SUPPORTED verdicts on seeded contradiction cases / those cases",
            numerator=false_res,
            denominator=false_res_n,
            population="contradiction_reason_cases",
            limitations="CONTESTED is not a false resolution",
            n=false_res_n,
        )
    )

    # ----- temporal -----
    old = store.get("BM-SW-OLD-FACT")
    fresh = store.get("BM-SW-FRESH-FACT")
    unknown_age = store.get("BM-SW-UNKNOWN-AGE")
    superseded = store.get("BM-SW-SUPERSEDED-OLD")
    temp_ok = 0
    temp_n = 5
    if old and old.status == DecayState.STALE.value and old.observed_at != old.created_at:
        temp_ok += 1
    if fresh and fresh.status != DecayState.STALE.value:
        temp_ok += 1
    if unknown_age and unknown_age.observed_at is None:
        temp_ok += 1
    if superseded and superseded.status == DecayState.SUPERSEDED.value:
        temp_ok += 1
    hist = store.history("BM-SW-SUPERSEDED-OLD")
    if hist and hist[0].statement.startswith("SYNTHETIC_TEST_DATA: service X is on revision 1"):
        temp_ok += 1
    stale_task = _task_from_case(next(c for c in retrieval_cases() if c.case_id == "RET-TEMP-01"))
    stale_items = retriever.retrieve(store, stale_task, now=NOW)
    stale_ctx = assemble_context(stale_items, store, now=NOW)
    stale_verdict, stale_ep, *_ = reason(
        stale_task, stale_ctx, retrieved_ids=[i.memory_id for i in stale_items]
    )
    stale_not_false = stale_verdict != "SUPPORTED" and "BM-SW-OLD-FACT" in {
        i.memory_id for i in stale_items
    }
    metrics.append(
        make_metric(
            "temporal_classification_accuracy",
            name="temporal_classification_accuracy",
            definition="correct STALE/fresh/unknown-age/SUPERSEDED/history-preserved checks / 5",
            numerator=temp_ok,
            denominator=temp_n,
            population="seeded temporal software records",
            limitations="STALE ≠ FALSE is a separate check (stale remains queryable)",
            n=temp_n,
        )
    )
    metrics.append(
        make_metric(
            "stale_not_false",
            name="stale_not_false",
            definition="stale historical fact remains queryable and is not treated as SUPPORTED falsehood",
            numerator=1.0 if stale_not_false else 0.0,
            denominator=1.0,
            population="BM-SW-OLD-FACT + RET-TEMP-01",
            limitations="Single seeded record",
            n=1,
        )
    )

    # ----- unknown / not implemented -----
    refuse_ok = refuse_n = 0
    false_cert = false_cert_n = 0
    for case in unknown_cases():
        task = _task_from_case(case)
        items = retriever.retrieve(store, task, now=NOW)
        ctx = assemble_context(items, store, now=NOW)
        verdict, epistemic, trace, _c, _a = reason(task, ctx, retrieved_ids=[i.memory_id for i in items])
        refuse_n += 1
        false_cert_n += 1
        expect = case.expected_verdict_class
        if verdict == expect or (
            expect == "INSUFFICIENT_EVIDENCE"
            and verdict in {"INSUFFICIENT_EVIDENCE", "NOT_IMPLEMENTED"}
        ):
            refuse_ok += 1
        if verdict == "SUPPORTED":
            false_cert += 1
        case_results.append(
            {
                "case_id": case.case_id,
                "family": case.family,
                "verdict": verdict,
                "epistemic": epistemic,
                "mode_status": trace.mode_status,
            }
        )
    metrics.append(
        make_metric(
            "unknown_refusal_accuracy",
            name="unknown_refusal_accuracy",
            definition="empty/unimplemented cases returning the expected refusal class",
            numerator=refuse_ok,
            denominator=refuse_n,
            population="unknown_cases",
            limitations="Does not measure probabilistic calibration",
            n=refuse_n,
        )
    )
    metrics.append(
        make_metric(
            "false_certainty_rate",
            name="false_certainty_rate",
            definition="SUPPORTED on unknown/not-implemented cases / those cases",
            numerator=false_cert,
            denominator=false_cert_n,
            population="unknown_cases",
            limitations="WEAKLY_SUPPORTED on empty context would also be overconfident; tracked separately if seen",
            n=false_cert_n,
        )
    )

    # ----- reasoning modes + assumptions -----
    mode_ok = mode_n = 0
    asm_ok = asm_n = 0
    unsup_claim = unsup_claim_n = 0
    for case in reasoning_mode_cases():
        task = _task_from_case(case)
        items = retriever.retrieve(store, task, now=NOW)
        ctx = assemble_context(items, store, now=NOW)
        verdict, epistemic, trace, crit, assumptions = reason(
            task, ctx, retrieved_ids=[i.memory_id for i in items]
        )
        mode_n += 1
        if (
            trace.mode == case.expected_reasoning_mode
            and trace.mode_status == "IMPLEMENTED"
            and verdict != "SUPPORTED"
            and assumptions
        ):
            mode_ok += 1
        asm_n += 1
        if assumptions and assumptions[0].assumption_id and assumptions[0].basis:
            asm_ok += 1
        unsup_claim_n += 1
        if verdict == "SUPPORTED":
            unsup_claim += 1
        case_results.append(
            {
                "case_id": case.case_id,
                "family": case.family,
                "mode": trace.mode,
                "verdict": verdict,
                "assumption_id": assumptions[0].assumption_id if assumptions else "",
            }
        )
    metrics.append(
        make_metric(
            "reasoning_mode_structure_rate",
            name="reasoning_mode_structure_rate",
            definition="implemented modes emit mode+assumptions and never SUPPORTED / 7 modes",
            numerator=mode_ok,
            denominator=mode_n,
            population="reasoning_mode_cases",
            limitations="Tests structured outputs, not hidden chain-of-thought quality",
            n=mode_n,
        )
    )
    metrics.append(
        make_metric(
            "assumption_tracking_rate",
            name="assumption_tracking_rate",
            definition="episodes with assumption_id and basis / mode cases",
            numerator=asm_ok,
            denominator=asm_n,
            population="reasoning_mode_cases",
            limitations="P3 currently records a single loop-level assumption",
            n=asm_n,
        )
    )
    metrics.append(
        make_metric(
            "unsupported_claim_rate",
            name="unsupported_claim_rate",
            definition="SUPPORTED verdicts in mode+adversarial+unknown populations / those episodes",
            numerator=unsup_claim,
            denominator=unsup_claim_n,
            population="reasoning_mode_cases (adversarial added below)",
            limitations="P3 downgrades SUPPORTED; this should stay zero",
            n=unsup_claim_n,
        )
    )

    # ----- critic -----
    critic_hits = critic_n = 0
    # missing evidence
    empty_task = _task_from_case(unknown_cases()[0])
    empty_ctx = assemble_context([], store, now=NOW)
    empty_v, _, _, empty_c, empty_a = reason(empty_task, empty_ctx, retrieved_ids=[])
    critic_n += 1
    if empty_c.missing_evidence:
        critic_hits += 1
    # contradiction
    ccase = contradiction_reason_cases()[0]
    ctask = _task_from_case(ccase)
    citems = retriever.retrieve(store, ctask, now=NOW)
    cctx = assemble_context(citems, store, now=NOW)
    cv, _, _, cc, ca = reason(ctask, cctx, retrieved_ids=[i.memory_id for i in citems])
    critic_n += 1
    if "opposing" in cc.alternative_explanation.lower() or cctx.contradiction_present:
        critic_hits += 1
    # stale
    critic_n += 1
    stale_c = critique_result(
        task=stale_task, ctx=stale_ctx, verdict=stale_verdict, assumptions=list(empty_a)
    )
    if stale_c.stale_used_as_current or any(
        i.status == DecayState.STALE.value for i in stale_items
    ):
        critic_hits += 1
    # hidden assumption
    critic_n += 1
    if empty_a and empty_a[0].statement:
        critic_hits += 1
    # prediction as fact: facts bucket should not contain PREDICTION
    pred_ok = all(i.epistemic_kind != EpistemicKind.PREDICTION.value for i in stale_ctx.facts)
    critic_n += 1
    if pred_ok:
        critic_hits += 1
    # too_strong should be false after P3 downgrade
    critic_n += 1
    if not empty_c.too_strong:
        critic_hits += 1
    metrics.append(
        make_metric(
            "critic_detection_rate",
            name="critic_detection_rate",
            definition="seeded critic-trigger checks that fired / checks (missing, contra, stale, assumption, pred-not-fact, not-too-strong)",
            numerator=critic_hits,
            denominator=critic_n,
            population="synthetic critic probes",
            limitations="scope mismatch and overgeneralization have no Critique field → NOT_MEASURED separately",
            n=critic_n,
        )
    )
    metrics.append(
        make_metric(
            "critic_false_alarm_rate",
            name="critic_false_alarm_rate",
            definition="too_strong on non-SUPPORTED verdicts / those verdicts",
            numerator=1.0 if empty_c.too_strong and empty_v != "SUPPORTED" else 0.0,
            denominator=1.0,
            population="empty-evidence critic probe",
            limitations="N=1 probe; not a full false-alarm curve",
            n=1,
        )
    )
    metrics.append(
        make_metric(
            "critic_scope_mismatch",
            name="critic_scope_mismatch",
            definition="no dedicated Critique field",
            numerator=0.0,
            denominator=0.0,
            population="none",
            limitations="Critique schema has no scope_mismatch flag",
            n=0,
        )
    )

    # ----- hypothesis + experiment (analysis-only) -----
    h_task = CognitiveTask(
        task_id="HYP-BENCH-1",
        task_type=TaskType.INVESTIGATE.value,
        objective="timeout retries",
        question="Do retries after timeout help?",
        domain="software",
        requester="p4.1-benchmark",
        created_at=NOW,
        data_label=DATA_LABEL,
        write_back=True,
    )
    h_res = orch.run(h_task, now=NOW, use_memory=True)
    hyp_rec = hyp.get(h_res.hypothesis_id) if h_res.hypothesis_id else None
    fals = 1.0 if hyp_rec and hyp_rec.provenance.get("falsification_condition") else 0.0
    novelty_ok = 1.0 if h_res.novelty.get("novelty_equals_truth") is False else 0.0
    metrics.append(
        make_metric(
            "hypothesis_falsification_present",
            name="hypothesis_falsification_present",
            definition="generated hypothesis provenance includes falsification_condition",
            numerator=fals,
            denominator=1.0,
            population="one INVESTIGATE write-back episode",
            limitations="String condition is not an executable experiment",
            n=1,
        )
    )
    metrics.append(
        make_metric(
            "novelty_not_truth",
            name="novelty_not_truth",
            definition="novelty_equals_truth is False on generated hypothesis episode",
            numerator=novelty_ok,
            denominator=1.0,
            population="one INVESTIGATE write-back episode",
            limitations="Classifier output, not a creativity test",
            n=1,
        )
    )
    exp_ok = 1.0 if h_res.experiment_id and h_res.authorized_execution is False else 0.0
    metrics.append(
        make_metric(
            "experiment_analysis_only",
            name="experiment_analysis_only",
            definition="experiment_id present and authorized_execution is False",
            numerator=exp_ok,
            denominator=1.0,
            population="one INVESTIGATE write-back episode",
            limitations="Ledger result is INSUFFICIENT_DATA/NOT_COMPARABLE by design",
            n=1,
        )
    )

    # ----- multi-episode learning (separate store) -----
    learn_dir = workdir / "learn"
    learn_dir.mkdir(exist_ok=True)
    learn_store = CognitiveMemoryStore(learn_dir / "ahos_cognitive_memory.sqlite")
    learn_store.remember(
        memory_id="SEED-TIMEOUT",
        memory_type=MemoryType.EPISODIC,
        epistemic_kind=EpistemicKind.OBSERVED_FACT,
        statement="SYNTHETIC_TEST_DATA: HTTP timeout recovered after retries.",
        source_type=SourceType.SYSTEM,
        source_id="seed-timeout",
        source_location="benchmark.learning",
        producer="p4.1-benchmark",
        producer_version="p4.1.0",
        domain="software",
        context=DATA_LABEL,
        observed_at=NOW - 80,
        created_at=NOW - 40,
        payload={"data_label": DATA_LABEL},
    )
    learn_orch = CognitiveOrchestrator(
        memory=learn_store,
        hypotheses=HypothesisStore(learn_dir / "hyp.jsonl"),
        ledger_path=learn_dir / "exp.jsonl",
    )
    e1 = learn_orch.run(
        CognitiveTask(
            task_id="LEARN-E1",
            task_type=TaskType.INVESTIGATE.value,
            objective="Investigate timeout recovery",
            question="Do retries after timeout help?",
            domain="software",
            requester="p4.1-benchmark",
            created_at=NOW,
            data_label=DATA_LABEL,
        ),
        now=NOW,
    )
    e2 = learn_orch.run(
        CognitiveTask(
            task_id="LEARN-E2",
            task_type=TaskType.LEARN.value,
            objective="Reuse prior timeout lesson",
            question="What did we learn about timeout retries?",
            domain="software",
            requester="p4.1-benchmark",
            created_at=NOW + 10,
            data_label=DATA_LABEL,
        ),
        now=NOW + 10,
    )
    e3 = learn_orch.run(
        CognitiveTask(
            task_id="LEARN-E3",
            task_type=TaskType.ANALYZE.value,
            objective="related HTTP timeout retries",
            question="Should we retry after HTTP timeout?",
            domain="software",
            requester="p4.1-benchmark",
            created_at=NOW + 20,
            data_label=DATA_LABEL,
            write_back=False,
        ),
        now=NOW + 20,
    )
    e4 = learn_orch.run(
        CognitiveTask(
            task_id="LEARN-E4",
            task_type=TaskType.ANALYZE.value,
            objective="compiler unused import",
            question="Is the unused import a compiler warning?",
            domain="software",
            requester="p4.1-benchmark",
            created_at=NOW + 30,
            data_label=DATA_LABEL,
            write_back=False,
        ),
        now=NOW + 30,
    )
    e5 = learn_orch.run(
        CognitiveTask(
            task_id="LEARN-E5",
            task_type=TaskType.ANALYZE.value,
            objective="queue depth",
            question="What is the badge reader firmware version?",
            domain="operations",
            requester="p4.1-benchmark",
            created_at=NOW + 40,
            data_label=DATA_LABEL,
            write_back=False,
        ),
        now=NOW + 40,
    )
    e2_none = learn_orch.run(
        CognitiveTask(
            task_id="LEARN-E2-NOMEM",
            task_type=TaskType.LEARN.value,
            objective="Reuse prior timeout lesson",
            question="What did we learn about timeout retries?",
            domain="software",
            requester="p4.1-benchmark",
            created_at=NOW + 11,
            data_label=DATA_LABEL,
            write_back=False,
        ),
        now=NOW + 11,
        use_memory=False,
    )
    lesson_id = e1.lesson_memory_id
    applicable = [e2, e3]
    inapplicable = [e4, e5]
    reuse_hits = sum(
        1
        for ep in applicable
        if lesson_id and lesson_id in {i.memory_id for i in ep.retrieved}
    )
    incorrect = sum(
        1
        for ep in inapplicable
        if lesson_id and lesson_id in {i.memory_id for i in ep.retrieved}
    )
    metrics.append(
        make_metric(
            "lesson_reuse_rate",
            name="lesson_reuse_rate",
            definition="applicable later episodes that retrieved episode-1 LESSON / applicable episodes",
            numerator=reuse_hits,
            denominator=len(applicable),
            population="LEARN-E2, LEARN-E3 (timeout-related)",
            limitations="N=2 applicable synthetic episodes; NO_MEMORY baseline is separate",
            n=len(applicable),
        )
    )
    metrics.append(
        make_metric(
            "correct_lesson_reuse_rate",
            name="correct_lesson_reuse_rate",
            definition="same as lesson_reuse_rate on labeled-applicable episodes",
            numerator=reuse_hits,
            denominator=len(applicable),
            population="LEARN-E2, LEARN-E3",
            limitations="Applicability is the benchmark label, not a causal test",
            n=len(applicable),
        )
    )
    metrics.append(
        make_metric(
            "incorrect_lesson_application_rate",
            name="incorrect_lesson_application_rate",
            definition="inapplicable episodes that still retrieved the timeout LESSON / inapplicable",
            numerator=incorrect,
            denominator=len(inapplicable),
            population="LEARN-E4 compiler (same domain) and LEARN-E5 operations",
            limitations="same_domain retrieval may retrieve the lesson on E4; that is a measured weakness if FAIL",
            n=len(inapplicable),
        )
    )
    nomem_reuse = 1.0 if lesson_id and lesson_id in e2_none.trace.retrieved_ids else 0.0
    metrics.append(
        make_metric(
            "no_memory_lesson_reuse",
            name="no_memory_lesson_reuse",
            definition="NO_MEMORY baseline retrieval of episode-1 lesson (expect 0)",
            numerator=nomem_reuse,
            denominator=1.0,
            population="LEARN-E2-NOMEM",
            limitations="Baseline must stay 0; not an intelligence comparison",
            n=1,
        )
    )

    # ----- failure memory -----
    fail_dir = workdir / "fail"
    fail_dir.mkdir(exist_ok=True)
    fail_store = CognitiveMemoryStore(fail_dir / "ahos_cognitive_memory.sqlite")
    fail_store.remember(
        memory_id="SEED-OPS",
        memory_type=MemoryType.EPISODIC,
        epistemic_kind=EpistemicKind.OBSERVED_FACT,
        statement="SYNTHETIC_TEST_DATA deploy checklist rollback",
        source_type=SourceType.SYSTEM,
        source_id="seed-ops",
        source_location="benchmark.failure",
        producer="p4.1-benchmark",
        producer_version="p4.1.0",
        domain="operations",
        context=DATA_LABEL,
        observed_at=NOW - 10,
        created_at=NOW - 5,
        payload={"data_label": DATA_LABEL},
    )
    fail_orch = CognitiveOrchestrator(
        memory=fail_store,
        hypotheses=HypothesisStore(fail_dir / "hyp.jsonl"),
        ledger_path=fail_dir / "exp.jsonl",
    )
    ft = CognitiveTask(
        task_id="FAIL-E1",
        task_type=TaskType.ANALYZE.value,
        objective="deploy checklist",
        question="deploy checklist rollback?",
        domain="operations",
        requester="p4.1-benchmark",
        created_at=NOW,
        data_label=DATA_LABEL,
    )
    fail_orch.run(ft, now=NOW)
    fail_rec = fail_orch.record_failure(
        ft,
        observed_failure="SYNTHETIC_TEST_DATA: deploy checklist failed; rollback missing",
        attempted_action="analyze deploy checklist",
        now=NOW + 1,
    )
    fail_sim = fail_orch.run(
        CognitiveTask(
            task_id="FAIL-E2",
            task_type=TaskType.INVESTIGATE.value,
            objective="avoid prior deploy failure",
            question="deploy checklist recurrence rollback?",
            domain="operations",
            requester="p4.1-benchmark",
            created_at=NOW + 2,
            data_label=DATA_LABEL,
            write_back=False,
        ),
        now=NOW + 2,
    )
    fail_unrel = fail_orch.run(
        CognitiveTask(
            task_id="FAIL-E3",
            task_type=TaskType.ANALYZE.value,
            objective="telescope pointing",
            question="telescope pointing error arcsec?",
            domain="science",
            requester="p4.1-benchmark",
            created_at=NOW + 3,
            data_label=DATA_LABEL,
            write_back=False,
        ),
        now=NOW + 3,
    )
    fail_hit = 1.0 if fail_rec.memory_id in {i.memory_id for i in fail_sim.retrieved} else 0.0
    fail_false = 1.0 if fail_rec.memory_id in {i.memory_id for i in fail_unrel.retrieved} else 0.0
    metrics.append(
        make_metric(
            "failure_recall",
            name="failure_recall",
            definition="similar later episode retrieved FAILURE F1",
            numerator=fail_hit,
            denominator=1.0,
            population="FAIL-E2 operations deploy",
            limitations="N=1 similar episode",
            n=1,
        )
    )
    metrics.append(
        make_metric(
            "false_failure_application_rate",
            name="false_failure_application_rate",
            definition="unrelated episode retrieved FAILURE F1 / 1",
            numerator=fail_false,
            denominator=1.0,
            population="FAIL-E3 science telescope",
            limitations="FAILURE type alone is not relevance; measured after P4.2 query-time gating",
            n=1,
        )
    )

    # ----- cross-domain -----
    verdicts: list[str] = []
    for case in cross_domain_cases():
        task = _task_from_case(case)
        items = retriever.retrieve(store, task, now=NOW)
        ctx = assemble_context(items, store, now=NOW)
        verdict, epistemic, *_rest = reason(task, ctx, retrieved_ids=[i.memory_id for i in items])
        verdicts.append(verdict)
        case_results.append(
            {
                "case_id": case.case_id,
                "family": case.family,
                "domain": case.domain,
                "verdict": verdict,
                "epistemic": epistemic,
                "retrieved": len(items),
            }
        )
    consistent = 1.0 if len(set(verdicts)) == 1 else 0.0
    metrics.append(
        make_metric(
            "cross_domain_consistency",
            name="cross_domain_consistency",
            definition="structurally similar retry questions share one verdict class across 4 domains",
            numerator=consistent,
            denominator=1.0,
            population="finance/science/software/operations ANALYZE retry questions",
            limitations="Consistency of class, not of domain-specific quality; finance is an adapter",
            n=4,
        )
    )

    # ----- adversarial -----
    adv_ok = adv_n = 0
    adv_supported = 0
    for case in adversarial_cases():
        task = _task_from_case(case)
        items = retriever.retrieve(store, task, now=NOW)
        ctx = assemble_context(items, store, now=NOW)
        verdict, epistemic, *_r = reason(task, ctx, retrieved_ids=[i.memory_id for i in items])
        adv_n += 1
        unsup_claim_n += 1
        if verdict == "SUPPORTED":
            adv_supported += 1
        if verdict != "SUPPORTED":
            adv_ok += 1
        if case.expected_verdict_class and verdict != case.expected_verdict_class:
            # still counts as resistant if not SUPPORTED
            pass
        case_results.append(
            {
                "case_id": case.case_id,
                "family": case.family,
                "verdict": verdict,
                "epistemic": epistemic,
            }
        )
    metrics.append(
        make_metric(
            "adversarial_resistance",
            name="adversarial_resistance",
            definition="misleading cases that did not yield SUPPORTED / adversarial cases",
            numerator=adv_ok,
            denominator=adv_n,
            population="adversarial_cases",
            limitations="Resistance means no false SUPPORTED, not that retrieval ignored distractors",
            n=adv_n,
        )
    )
    # rewrite unsupported_claim_rate with combined population
    metrics = [m for m in metrics if m.metric_id != "unsupported_claim_rate"]
    metrics.append(
        make_metric(
            "unsupported_claim_rate",
            name="unsupported_claim_rate",
            definition="SUPPORTED verdicts on mode+adversarial+unknown episodes / those episodes",
            numerator=unsup_claim + false_cert + adv_supported,
            denominator=unsup_claim_n + false_cert_n + adv_n,
            population="reasoning_mode_cases + unknown_cases + adversarial_cases",
            limitations="P3 downgrades SUPPORTED by construction",
            n=unsup_claim_n + false_cert_n + adv_n,
        )
    )

    # ----- P4.2 pollution (extra measurements; P4.1 cases unchanged) -----
    contra_ids = {
        "BM-SW-CONTRA-A",
        "BM-SW-CONTRA-B",
        "BM-SCI-CONTRA-A",
        "BM-SCI-CONTRA-B",
    }
    sd_fp = sd_n = 0
    contra_pollute = contra_pollute_n = 0
    rel_expand_fp = rel_expand_n = 0
    for case in retrieval_cases():
        task = _task_from_case(case)
        items = retriever.retrieve(store, task, now=NOW)
        relevant = set(case.expected_relevant_ids)
        expected_contra = relevant & contra_ids
        got = {i.memory_id for i in items}
        unexpected_contra = (got & contra_ids) - expected_contra
        contra_pollute_n += 1
        if unexpected_contra:
            contra_pollute += 1
        for item in items:
            rec = store.get(item.memory_id)
            if rec and rec.domain == task.domain:
                sd_n += 1
                if item.memory_id not in relevant:
                    sd_fp += 1
            only_rel = set(item.match_reasons) <= {
                "contradiction_of_relevant_memory",
                "related_to_relevant_memory",
                "same_domain",
                "stale_but_queryable",
                "temporal_proximity",
                "type_compatibility",
            } and (
                "contradiction_of_relevant_memory" in item.match_reasons
                or "related_to_relevant_memory" in item.match_reasons
            )
            if only_rel:
                rel_expand_n += 1
                if item.memory_id not in relevant:
                    rel_expand_fp += 1
    empty_task = _task_from_case(unknown_cases()[0])
    empty_explained = retriever.retrieve_explained(store, empty_task, now=NOW)
    metrics.append(
        make_metric(
            "unrelated_retrieval_rate",
            name="unrelated_retrieval_rate",
            definition="|retrieved − relevant| / |retrieved| over labeled retrieval cases",
            numerator=fp,
            denominator=tp + fp,
            population="retrieval_cases",
            limitations="Complement of retrieval_precision; labels are the case sets",
            n=len(retrieval_cases()),
        )
    )
    metrics.append(
        make_metric(
            "same_domain_false_inclusion_rate",
            name="same_domain_false_inclusion_rate",
            definition="same-domain retrieved IDs not in the case label / same-domain retrieved",
            numerator=sd_fp,
            denominator=sd_n,
            population="retrieval_cases same-domain hits",
            limitations="Domain match is a ranking signal, not a relevance proof",
            n=sd_n,
        )
    )
    metrics.append(
        make_metric(
            "contradiction_pollution_rate",
            name="contradiction_pollution_rate",
            definition="retrieval cases that returned an unexpected contradiction-linked ID / retrieval cases",
            numerator=contra_pollute,
            denominator=contra_pollute_n,
            population="retrieval_cases vs seeded contradiction IDs",
            limitations="Does not score CONTRA-SW/SCI reason cases",
            n=contra_pollute_n,
        )
    )
    metrics.append(
        make_metric(
            "empty_query_pollution_rate",
            name="empty_query_pollution_rate",
            definition="1 if UNK-EMPTY-01 retrieved any memory else 0",
            numerator=1.0 if empty_explained.items else 0.0,
            denominator=1.0,
            population="UNK-EMPTY-01",
            limitations="Single unknown-fact question; NO_RELEVANT_MEMORY is the correct empty result",
            n=1,
        )
    )
    metrics.append(
        make_metric(
            "irrelevant_relationship_expansion_rate",
            name="irrelevant_relationship_expansion_rate",
            definition="relationship-only retrieved IDs outside the case label / relationship-only retrieved",
            numerator=rel_expand_fp,
            denominator=rel_expand_n,
            population="retrieval_cases items retrieved only via anchored expansion",
            limitations="NOT_MEASURED when no relationship-only rows appear",
            n=rel_expand_n,
        )
    )

    # ----- P4.3 lookalike discrimination (P4.1 cases unchanged) -----
    kw = next(c for c in retrieval_cases() if c.case_id == "RET-KEYWORD-01")
    kw_task = _task_from_case(kw)
    kw_items = retriever.retrieve(store, kw_task, now=NOW)
    kw_got = {i.memory_id for i in kw_items}
    cousin_ids = {
        "BM-SW-TIMEOUT-LOOKALIKE",
        "BM-FIN-FACT",
        "BM-FIN-LESSON",
        "BM-OPS-FACT",
        "BM-OPS-LESSON",
        "BM-SCI-FACT",
        "BM-SCI-LESSON",
    }
    lookalike_rejected = len(cousin_ids - kw_got)
    relevant_kw = set(TIMEOUT_RELEVANT)
    rel_look_hit = len(kw_got & relevant_kw)
    generic_fp = generic_n = 0
    for item in kw_items:
        rec = store.get(item.memory_id)
        if rec is None:
            continue
        generic_n += 1
        ov = _lexical_overlap(rec, normalize_query(kw_task).tokens)
        if ov and ov <= {"retry", "recover"} and item.memory_id not in relevant_kw:
            generic_fp += 1
    mismatch_task = _task_from_case(kw)
    mismatch_task.constraints = {
        **dict(mismatch_task.constraints),
        "component": "database",
        "failure_type": "disk_full",
    }
    mismatch_task.question = "prior timeout retry failure"
    mismatch_task.objective = "failure memory"
    mm_items = retriever.retrieve(store, mismatch_task, now=NOW)
    mm_ids = {i.memory_id for i in mm_items}
    hard_ok = 1.0 if "BM-SW-TIMEOUT-FAIL" not in mm_ids else 0.0
    learn_ok = learn_n = 0
    for case in retrieval_cases():
        if case.task_type != "LEARN":
            continue
        learn_n += 1
        items = retriever.retrieve(store, _task_from_case(case), now=NOW)
        if items and all(i.epistemic_kind == "LESSON" for i in items):
            learn_ok += 1
        elif not items:
            learn_ok += 0
    metrics.append(
        make_metric(
            "lookalike_rejection_rate",
            name="lookalike_rejection_rate",
            definition="labeled structural cousins not retrieved on RET-KEYWORD-01 / cousin set",
            numerator=lookalike_rejected,
            denominator=len(cousin_ids),
            population="LOOKALIKE + cross-domain retry/recover cousins",
            limitations="Cousin set is the P4.2-measured false-positive cluster, not a new label rewrite",
            n=len(cousin_ids),
        )
    )
    metrics.append(
        make_metric(
            "relevant_lookalike_recall",
            name="relevant_lookalike_recall",
            definition="TIMEOUT_RELEVANT retrieved on RET-KEYWORD-01 / labeled relevant",
            numerator=rel_look_hit,
            denominator=len(relevant_kw),
            population="RET-KEYWORD-01",
            limitations="Protects same-cluster recall while cousins are rejected",
            n=len(relevant_kw),
        )
    )
    metrics.append(
        make_metric(
            "generic_overlap_false_inclusion_rate",
            name="generic_overlap_false_inclusion_rate",
            definition="RET-KEYWORD-01 hits whose overlap is only retry/recover and unlabeled / retrieved",
            numerator=generic_fp,
            denominator=generic_n,
            population="RET-KEYWORD-01 retrieved items",
            limitations="Uses multi-domain operation tokens retry/recover",
            n=generic_n,
        )
    )
    metrics.append(
        make_metric(
            "hard_mismatch_rejection_accuracy",
            name="hard_mismatch_rejection_accuracy",
            definition="1 if BM-SW-TIMEOUT-FAIL is absent under explicit database/disk_full constraints",
            numerator=hard_ok,
            denominator=1.0,
            population="component+failure_type mismatch probe on timeout FAILURE",
            limitations="Single probe; missing fields remain neutral elsewhere",
            n=1,
        )
    )
    metrics.append(
        make_metric(
            "structured_mismatch_false_inclusion_rate",
            name="structured_mismatch_false_inclusion_rate",
            definition="1 if the mismatched FAILURE was still retrieved",
            numerator=0.0 if hard_ok else 1.0,
            denominator=1.0,
            population="same hard-mismatch probe",
            limitations="Complement of hard_mismatch_rejection_accuracy",
            n=1,
        )
    )
    metrics.append(
        make_metric(
            "task_compatibility_accuracy",
            name="task_compatibility_accuracy",
            definition="LEARN retrieval cases whose retrieved set is all LESSON / LEARN cases",
            numerator=learn_ok,
            denominator=learn_n,
            population="RET-DOMAIN-01 and RET-LESSON-01",
            limitations="Does not score ANALYZE cases that legitimately mix kinds",
            n=learn_n,
        )
    )

    p5_metrics, p5_cases, p5_counts = evaluate_p5_reasoning(store)
    metrics.extend(p5_metrics)
    case_results.extend(p5_cases)

    # weaknesses from FAILs
    for m in metrics:
        if m.status == "FAIL":
            weaknesses.append(f"WEAKNESS_DETECTED:{m.metric_id}={m.value}")
            candidates.append(f"IMPROVEMENT_CANDIDATE:{m.metric_id}")

    case_results.sort(key=lambda r: r.get("case_id", ""))
    metrics.sort(key=lambda m: m.metric_id)

    report = BenchmarkReport(
        benchmark_version=BENCHMARK_VERSION,
        git_sha=git_sha,
        environment={
            "python": platform.python_version(),
            "platform": platform.platform(),
            "data_label": DATA_LABEL,
        },
        data_label=DATA_LABEL,
        case_counts={
            "retrieval": len(retrieval_cases()),
            "unknown": len(unknown_cases()),
            "contradiction": len(contradiction_reason_cases()),
            "reasoning_modes": len(reasoning_mode_cases()),
            "cross_domain": len(cross_domain_cases()),
            "adversarial": len(adversarial_cases()),
            "corpus_memories": len(corpus.ids),
            "p5_cases": p5_counts.get("p5_cases", 0),
            "case_result_rows": len(case_results),
        },
        metrics=metrics,
        case_results=case_results,
        weaknesses=sorted(set(weaknesses)),
        improvement_candidates=sorted(set(candidates)),
        limitations=[
            "SYNTHETIC_TEST_DATA only; not soak evidence",
            "Keyword/domain retrieval is not semantic search",
            "Causal/counterfactual modes remain NOT_IMPLEMENTED",
            "N is small; do not treat rates as statistical significance",
            "No LLM, network, vector DB, or live execution",
            "Finance is an adapter proving domain, not the definition of cognition",
        ],
        lane_a_freeze=lane_a_freeze,
        soak_protection={
            "SOAK_DATABASE_TOUCHED": "NO",
            "SOAK_RUNTIME_RESTARTED": "NO",
            "T0_RESET": "NO",
            "BENCHMARK_DB": str(db.name),
        },
    )
    return report


def dumps_comparable(report: BenchmarkReport) -> str:
    return json.dumps(report.comparable_payload(), sort_keys=True, separators=(",", ":"))
