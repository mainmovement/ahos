"""Deterministic benchmark cases. Expected sets are labeled, not fitted."""

from __future__ import annotations

from architecture.cognitive.benchmark.cases import BenchmarkCase
from architecture.cognitive.benchmark.corpus import (
    EXP_TIMEOUT,
    HYP_TIMEOUT,
    SOFTWARE_DEBUG_LESSONS,
    TIMEOUT_RELEVANT,
)
from architecture.cognitive.loop.contracts import ReasoningMode, TaskType


def retrieval_cases() -> tuple[BenchmarkCase, ...]:
    return (
        BenchmarkCase(
            case_id="RET-EXACT-01",
            family="retrieval_exact",
            domain="software",
            task_type=TaskType.ANALYZE.value,
            question="retrieve memory BM-SW-TIMEOUT-FACT",
            objective="exact id",
            requested_evidence=("BM-SW-TIMEOUT-FACT",),
            expected_relevant_ids=("BM-SW-TIMEOUT-FACT",),
        ),
        BenchmarkCase(
            case_id="RET-DOMAIN-01",
            family="retrieval_domain",
            domain="software",
            task_type=TaskType.LEARN.value,
            question="retrieve software debugging lessons timeout retries",
            objective="software debugging lessons",
            expected_relevant_ids=SOFTWARE_DEBUG_LESSONS,
        ),
        BenchmarkCase(
            case_id="RET-KEYWORD-01",
            family="retrieval_keyword",
            domain="software",
            task_type=TaskType.ANALYZE.value,
            question="HTTP timeout retries recovered",
            objective="timeout retries",
            expected_relevant_ids=TIMEOUT_RELEVANT,
        ),
        BenchmarkCase(
            case_id="RET-HYP-01",
            family="retrieval_hypothesis",
            domain="software",
            task_type=TaskType.HYPOTHESIZE.value,
            question="timeout retry hypothesis",
            objective="hypotheses about timeout",
            constraints={"hypothesis_id": HYP_TIMEOUT},
            expected_relevant_ids=("BM-SW-TIMEOUT-HYP", "BM-SW-TIMEOUT-EXP"),
        ),
        BenchmarkCase(
            case_id="RET-EXP-01",
            family="retrieval_experiment",
            domain="software",
            task_type=TaskType.TEST.value,
            question="timeout experiment record",
            objective="experiments about timeout",
            constraints={"experiment_id": EXP_TIMEOUT},
            expected_relevant_ids=("BM-SW-TIMEOUT-EXP",),
        ),
        BenchmarkCase(
            case_id="RET-FAIL-01",
            family="retrieval_failure",
            domain="software",
            task_type=TaskType.INVESTIGATE.value,
            question="prior timeout retry failure",
            objective="failure memory",
            expected_relevant_ids=("BM-SW-TIMEOUT-FAIL",),
        ),
        BenchmarkCase(
            case_id="RET-CONTRA-01",
            family="retrieval_contradiction",
            domain="software",
            task_type=TaskType.COMPARE.value,
            question="Did condition X occur on node seven?",
            objective="contradiction pair",
            expected_relevant_ids=("BM-SW-CONTRA-A", "BM-SW-CONTRA-B"),
            expected_contradiction_state="PRESENT",
        ),
        BenchmarkCase(
            case_id="RET-TEMP-01",
            family="retrieval_temporal",
            domain="software",
            task_type=TaskType.ANALYZE.value,
            question="current timeout rate this hour",
            objective="fresh timeout rate",
            expected_relevant_ids=("BM-SW-FRESH-FACT", "BM-SW-OLD-FACT"),
            expected_properties={"stale_must_remain_queryable": True},
        ),
        BenchmarkCase(
            case_id="RET-LESSON-01",
            family="retrieval_lesson",
            domain="software",
            task_type=TaskType.LEARN.value,
            question="What did we learn about timeout retries?",
            objective="lesson retrieval",
            expected_relevant_ids=("BM-SW-TIMEOUT-LESSON",),
        ),
        BenchmarkCase(
            case_id="RET-NS-A",
            family="retrieval_namespace",
            domain="software",
            task_type=TaskType.ANALYZE.value,
            question="private A note about timeout retries",
            objective="agent A private",
            agent_id="agent_A",
            expected_namespace="agent_A",
            expected_relevant_ids=("BM-A-PRIV",),
            expected_absent_ids=("BM-B-PRIV",),
        ),
        BenchmarkCase(
            case_id="RET-NS-B",
            family="retrieval_namespace",
            domain="software",
            task_type=TaskType.ANALYZE.value,
            question="private B note about timeout retries",
            objective="agent B private",
            agent_id="agent_B",
            expected_namespace="agent_B",
            expected_relevant_ids=("BM-B-PRIV",),
            expected_absent_ids=("BM-A-PRIV",),
        ),
    )


def unknown_cases() -> tuple[BenchmarkCase, ...]:
    return (
        BenchmarkCase(
            case_id="UNK-EMPTY-01",
            family="unknown_refusal",
            domain="general",
            task_type=TaskType.ANALYZE.value,
            question="What is the melting point of unobtainium-xyzzy?",
            objective="no evidence",
            expected_verdict_class="INSUFFICIENT_EVIDENCE",
            expected_uncertainty_class="INSUFFICIENT_EVIDENCE",
        ),
        BenchmarkCase(
            case_id="UNK-NI-CAUSAL",
            family="unknown_not_implemented",
            domain="software",
            task_type=TaskType.ANALYZE.value,
            question="What caused the timeout?",
            objective="causal mode",
            expected_reasoning_mode=ReasoningMode.CAUSAL_HYPOTHESIS.value,
            expected_verdict_class="NOT_IMPLEMENTED",
        ),
        BenchmarkCase(
            case_id="UNK-NI-CF",
            family="unknown_not_implemented",
            domain="software",
            task_type=TaskType.ANALYZE.value,
            question="What if retries had not been used?",
            objective="counterfactual mode",
            expected_reasoning_mode=ReasoningMode.COUNTERFACTUAL.value,
            expected_verdict_class="NOT_IMPLEMENTED",
        ),
    )


def contradiction_reason_cases() -> tuple[BenchmarkCase, ...]:
    return (
        BenchmarkCase(
            case_id="CONTRA-SW-01",
            family="contradiction_reason",
            domain="software",
            task_type=TaskType.COMPARE.value,
            question="Did condition X occur on node seven?",
            objective="unresolved contradiction",
            expected_relevant_ids=("BM-SW-CONTRA-A", "BM-SW-CONTRA-B"),
            expected_verdict_class="UNRESOLVED",
            expected_contradiction_state="PRESENT",
        ),
        BenchmarkCase(
            case_id="CONTRA-SCI-01",
            family="contradiction_reason",
            domain="science",
            task_type=TaskType.COMPARE.value,
            question="Is claim X supported or contradicted?",
            objective="science contradiction",
            expected_relevant_ids=("BM-SCI-CONTRA-A", "BM-SCI-CONTRA-B"),
            expected_verdict_class="UNRESOLVED",
            expected_contradiction_state="PRESENT",
        ),
    )


def reasoning_mode_cases() -> tuple[BenchmarkCase, ...]:
    modes = (
        ReasoningMode.DEDUCTIVE.value,
        ReasoningMode.INDUCTIVE.value,
        ReasoningMode.ABDUCTIVE.value,
        ReasoningMode.COMPARATIVE.value,
        ReasoningMode.TEMPORAL.value,
        ReasoningMode.ADVERSARIAL.value,
        ReasoningMode.METACOGNITIVE.value,
    )
    out: list[BenchmarkCase] = []
    for mode in modes:
        out.append(
            BenchmarkCase(
                case_id=f"MODE-{mode}",
                family="reasoning_mode",
                domain="software",
                task_type=TaskType.ANALYZE.value,
                question="Do retries after timeout help?",
                objective=f"mode {mode}",
                expected_reasoning_mode=mode,
                expected_properties={"must_have_assumptions": True, "no_supported_certainty": True},
            )
        )
    return tuple(out)


def cross_domain_cases() -> tuple[BenchmarkCase, ...]:
    pairs = (
        ("software", "Do retries after timeout help?", "timeout retries"),
        ("science", "Do calibration retries recover the measurement?", "calibration retries"),
        ("finance", "Do retries recover the token observation?", "token observation retries"),
        ("operations", "Do retries recover queue depth?", "queue depth retries"),
    )
    out: list[BenchmarkCase] = []
    for domain, q, obj in pairs:
        out.append(
            BenchmarkCase(
                case_id=f"DOM-{domain.upper()}",
                family="cross_domain",
                domain=domain,
                task_type=TaskType.ANALYZE.value,
                question=q,
                objective=obj,
            )
        )
    return tuple(out)


def adversarial_cases() -> tuple[BenchmarkCase, ...]:
    return (
        BenchmarkCase(
            case_id="ADV-LOOKALIKE",
            family="adversarial",
            domain="software",
            task_type=TaskType.ANALYZE.value,
            question="Did the HTTP timeout poster recover production?",
            objective="lookalike distractor",
            expected_properties={"must_not_be_supported": True},
        ),
        BenchmarkCase(
            case_id="ADV-OPINION",
            family="adversarial",
            domain="software",
            task_type=TaskType.ANALYZE.value,
            question="Do timeouts never happen in production?",
            objective="opinion phrased as fact",
            expected_properties={"must_not_be_supported": True},
        ),
        BenchmarkCase(
            case_id="ADV-PRED",
            family="adversarial",
            domain="software",
            task_type=TaskType.ANALYZE.value,
            question="Will timeouts stop tomorrow?",
            objective="high-confidence prediction",
            expected_properties={"must_not_be_supported": True},
        ),
        BenchmarkCase(
            case_id="ADV-CONTRA",
            family="adversarial",
            domain="software",
            task_type=TaskType.COMPARE.value,
            question="Did condition X occur on node seven?",
            objective="true plus contradictory claim",
            expected_verdict_class="UNRESOLVED",
            expected_properties={"must_not_be_supported": True},
        ),
        BenchmarkCase(
            case_id="ADV-HYP",
            family="adversarial",
            domain="science",
            task_type=TaskType.ANALYZE.value,
            question="Did calibration drift cause the outlier as established fact?",
            objective="unsupported hypothesis as fact",
            expected_properties={"must_not_be_supported": True},
        ),
        BenchmarkCase(
            case_id="ADV-SUPERSEDED",
            family="adversarial",
            domain="software",
            task_type=TaskType.ANALYZE.value,
            question="Is service X still on revision 1?",
            objective="superseded looks relevant",
            expected_properties={"must_not_be_supported": True},
        ),
        BenchmarkCase(
            case_id="ADV-FIN-OPINION",
            family="adversarial",
            domain="finance",
            task_type=TaskType.ANALYZE.value,
            question="Is this paper token obviously safe?",
            objective="finance opinion as fact",
            expected_properties={"must_not_be_supported": True},
        ),
    )
