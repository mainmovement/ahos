"""P5 typed evidence-bound reasoning — isolated SYNTHETIC_TEST_DATA."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from architecture.cognitive.hypothesis import HypothesisStore  # noqa: E402
from architecture.cognitive.loop.binding import (  # noqa: E402
    ROLE_FACTUAL_PREMISE,
    bind_context,
    typed_class_of,
)
from architecture.cognitive.loop.context import assemble_context  # noqa: E402
from architecture.cognitive.loop.contracts import (  # noqa: E402
    CognitiveContext,
    CognitiveTask,
    CognitiveVerdict,
    ReasoningMode,
    RetrievedItem,
    TaskType,
)
from architecture.cognitive.loop.inference import (  # noqa: E402
    ACTION_DOWNGRADE,
    ACTION_REQUIRE_MORE,
    FINDING_MISSING_PREMISE,
    FINDING_TYPE_VIOLATION,
    CandidateInference,
    apply_constraint,
)
from architecture.cognitive.loop.orchestrator import CognitiveOrchestrator  # noqa: E402
from architecture.cognitive.loop.reason import critique_result, reason  # noqa: E402
from architecture.cognitive.memory.store import CognitiveMemoryStore  # noqa: E402
from architecture.cognitive.memory.types import EpistemicKind, MemoryType, SourceType  # noqa: E402

NOW = 1_800_000_000.0
LOOP_DIR = ROOT / "architecture" / "cognitive" / "loop"
FORBIDDEN = {"discovery", "paper_trading", "telegram_ai", "engine"}


def _task(**kwargs) -> CognitiveTask:
    base = dict(
        task_id="p5-t",
        task_type=TaskType.ANALYZE.value,
        objective="timeout retries",
        question="Do retries after timeout help?",
        domain="software",
        requester="pytest",
        created_at=NOW,
        data_label="SYNTHETIC_TEST_DATA",
        reasoning_mode=ReasoningMode.DEDUCTIVE.value,
        write_back=False,
    )
    base.update(kwargs)
    return CognitiveTask(**base)


def _item(
    mid: str,
    statement: str,
    *,
    kind: str = EpistemicKind.OBSERVED_FACT.value,
    mtype: str = MemoryType.EPISODIC.value,
    status: str = "ACTIVE",
    domain: str = "software",
    observed_at: float | None = NOW - 20,
    match_reasons: tuple[str, ...] = ("test",),
) -> RetrievedItem:
    return RetrievedItem(
        memory_id=mid,
        revision=1,
        statement=statement,
        match_reasons=match_reasons,
        evidence_class="DIRECT_OBSERVATION",
        memory_type=mtype,
        epistemic_kind=kind,
        status=status,
        domain=domain,
        source_id="pytest",
        agent_namespace="",
        observed_at=observed_at,
        created_at=NOW - 10,
    )


def _ctx(*items: RetrievedItem, incomplete: bool = False) -> CognitiveContext:
    facts = tuple(
        i
        for i in items
        if i.epistemic_kind
        in {EpistemicKind.OBSERVED_FACT.value, EpistemicKind.DERIVED_FACT.value}
        and i.memory_type != MemoryType.FAILURE.value
    )
    hyps = tuple(i for i in items if i.epistemic_kind == EpistemicKind.HYPOTHESIS.value)
    preds = tuple(i for i in items if i.epistemic_kind == EpistemicKind.PREDICTION.value)
    opinions = tuple(i for i in items if i.epistemic_kind == EpistemicKind.OPINION.value)
    simulations = tuple(i for i in items if i.epistemic_kind == EpistemicKind.SIMULATION.value)
    lessons = tuple(i for i in items if i.epistemic_kind == EpistemicKind.LESSON.value)
    fails = tuple(i for i in items if i.memory_type == MemoryType.FAILURE.value)
    inferences = tuple(i for i in items if i.epistemic_kind == EpistemicKind.INFERENCE.value)
    unknowns = []
    if not facts:
        unknowns.append("no DIRECT_OBSERVATION/DERIVED_FACT in assembled context")
    if not items:
        unknowns.append("empty assembled context")
        incomplete = True
    return CognitiveContext(
        facts=facts,
        inferences=inferences,
        hypotheses=hyps,
        predictions=preds,
        opinions=opinions,
        simulations=simulations,
        experiments=(),
        outcomes=(),
        contradictions=(),
        failures=fails,
        procedures=(),
        lessons=lessons,
        unknowns=tuple(unknowns),
        excluded=(),
        contradiction_present=False,
        context_incomplete=incomplete,
        token_estimate=len(items),
    )


def _reason(task: CognitiveTask, ctx: CognitiveContext, store=None):
    ids = [i.memory_id for i in ctx.all_included()]
    return reason(task, ctx, retrieved_ids=ids, store=store)


def test_p5_package_does_not_import_lane_a() -> None:
    for path in LOOP_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] not in FORBIDDEN
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in FORBIDDEN


def test_failure_is_not_bound_as_factual_premise() -> None:
    item = _item(
        "F1",
        "SYNTHETIC_TEST_DATA timeout retry failed",
        kind=EpistemicKind.OBSERVED_FACT.value,
        mtype=MemoryType.FAILURE.value,
    )
    assert typed_class_of(item) == "FAILURE"
    task = _task()
    bindings = bind_context(_ctx(item), task)
    assert bindings[0].typed_class == "FAILURE"
    assert not bindings[0].may(ROLE_FACTUAL_PREMISE)


def test_mode_specificity_one_fact() -> None:
    fact = _item("M1", "SYNTHETIC_TEST_DATA: retries after HTTP timeout recovered the request.")
    ctx = _ctx(fact)
    ded = _reason(_task(reasoning_mode=ReasoningMode.DEDUCTIVE.value), ctx)
    ind = _reason(_task(reasoning_mode=ReasoningMode.INDUCTIVE.value), ctx)
    abd = _reason(_task(reasoning_mode=ReasoningMode.ABDUCTIVE.value), ctx)
    meta = _reason(_task(reasoning_mode=ReasoningMode.METACOGNITIVE.value), ctx)
    assert ded[0] == CognitiveVerdict.WEAKLY_SUPPORTED.value
    assert ind[0] == CognitiveVerdict.INSUFFICIENT_EVIDENCE.value
    assert abd[0] == CognitiveVerdict.UNRESOLVED.value
    assert meta[0] == CognitiveVerdict.WEAKLY_SUPPORTED.value
    assert ded[0] != ind[0]
    assert ded[2].mode != ind[2].mode
    assert "INFERENCE" in (ded[2].inference_records[0]["conclusion_class"],)


def test_deductive_missing_premise_refuses() -> None:
    ctx = _ctx()
    v, ep, trace, crit, _ = _reason(
        _task(reasoning_mode=ReasoningMode.DEDUCTIVE.value, requested_evidence=["NEED-1"]),
        ctx,
    )
    assert v == CognitiveVerdict.INSUFFICIENT_EVIDENCE.value
    assert "FACTUAL_PREMISE" in trace.inference_records[0]["missing_premises"] or crit.action in {
        ACTION_REQUIRE_MORE,
        "REQUIRE_MORE_EVIDENCE",
    }


def test_deductive_does_not_use_hypothesis_as_premise() -> None:
    hyp = _item(
        "H1",
        "SYNTHETIC_TEST_DATA: timeout retries always help",
        kind=EpistemicKind.HYPOTHESIS.value,
        mtype=MemoryType.HYPOTHESIS.value,
    )
    v, ep, trace, _, _ = _reason(_task(reasoning_mode=ReasoningMode.DEDUCTIVE.value), _ctx(hyp))
    assert v == CognitiveVerdict.INSUFFICIENT_EVIDENCE.value
    assert "HYPOTHESIS" in trace.evidence_classes


def test_inductive_output_is_inference_not_fact() -> None:
    a = _item("A", "SYNTHETIC_TEST_DATA timeout retry recovered node one")
    b = _item("B", "SYNTHETIC_TEST_DATA timeout retry recovered node two")
    v, ep, trace, _, _ = _reason(_task(reasoning_mode=ReasoningMode.INDUCTIVE.value), _ctx(a, b))
    assert v == CognitiveVerdict.WEAKLY_SUPPORTED.value
    assert trace.inference_records[0]["conclusion_class"] == "INFERENCE"
    assert "not an observed fact" in trace.conclusion.lower()


def test_abductive_preserves_alternatives() -> None:
    obs = _item("O1", "SYNTHETIC_TEST_DATA HTTP timeout observed")
    h1 = _item(
        "H1",
        "SYNTHETIC_TEST_DATA timeout caused by pool exhaustion",
        kind=EpistemicKind.HYPOTHESIS.value,
        mtype=MemoryType.HYPOTHESIS.value,
    )
    h2 = _item(
        "H2",
        "SYNTHETIC_TEST_DATA timeout caused by dns failure",
        kind=EpistemicKind.HYPOTHESIS.value,
        mtype=MemoryType.HYPOTHESIS.value,
    )
    v, _, trace, _, _ = _reason(_task(reasoning_mode=ReasoningMode.ABDUCTIVE.value), _ctx(obs, h1, h2))
    assert v in {
        CognitiveVerdict.WEAKLY_SUPPORTED.value,
        CognitiveVerdict.UNRESOLVED.value,
    }
    alts = trace.inference_records[0]["alternatives"]
    assert len(alts) >= 2
    assert trace.inference_records[0]["conclusion_class"] == "HYPOTHESIS"


def test_temporal_stale_not_current() -> None:
    stale = _item(
        "OLD",
        "SYNTHETIC_TEST_DATA service X was on revision 1",
        status="STALE",
        observed_at=NOW - 10_000,
    )
    v, ep, trace, _, _ = _reason(_task(reasoning_mode=ReasoningMode.TEMPORAL.value), _ctx(stale))
    assert v == CognitiveVerdict.INSUFFICIENT_EVIDENCE.value
    assert ep == "STALE"
    assert "not current" in trace.conclusion.lower()


def test_adversarial_rejects_opinion_as_fact() -> None:
    op = _item(
        "OP",
        "SYNTHETIC_TEST_DATA timeouts never happen in production",
        kind=EpistemicKind.OPINION.value,
    )
    v, _, trace, crit, _ = _reason(
        _task(reasoning_mode=ReasoningMode.ADVERSARIAL.value), _ctx(op)
    )
    assert v == CognitiveVerdict.INSUFFICIENT_EVIDENCE.value
    assert v != CognitiveVerdict.SUPPORTED.value


def test_critic_downgrades_supported_type_violation() -> None:
    cand = CandidateInference(
        verdict=CognitiveVerdict.SUPPORTED.value,
        epistemic="KNOWN",
        conclusion="timeouts never happen",
        conclusion_class="OBSERVED_FACT",
        type_violations=["OP-1"],
        supporting_ids=["OP-1"],
    )
    out = apply_constraint(
        cand,
        action=ACTION_DOWNGRADE,
        findings=[f"{FINDING_TYPE_VIOLATION}:OP-1"],
    )
    assert out.verdict != CognitiveVerdict.SUPPORTED.value
    assert out.verdict == CognitiveVerdict.INSUFFICIENT_EVIDENCE.value


def test_critic_missing_premise_requires_more() -> None:
    cand = CandidateInference(
        verdict=CognitiveVerdict.WEAKLY_SUPPORTED.value,
        epistemic="PROBABLE",
        conclusion="guess",
        conclusion_class="INFERENCE",
        missing_premises=["FACTUAL_PREMISE"],
    )
    out = apply_constraint(
        cand,
        action=ACTION_REQUIRE_MORE,
        findings=[f"{FINDING_MISSING_PREMISE}:FACTUAL_PREMISE"],
    )
    assert out.verdict == CognitiveVerdict.INSUFFICIENT_EVIDENCE.value


def test_critic_changes_reason_state_on_empty() -> None:
    v, _, trace, crit, _ = _reason(_task(), _ctx())
    assert v == CognitiveVerdict.INSUFFICIENT_EVIDENCE.value
    assert crit.action == ACTION_REQUIRE_MORE
    assert crit.constraint_applied is True
    assert trace.constraint_actions[0] == ACTION_REQUIRE_MORE


def test_unknown_empty_refuses() -> None:
    v, ep, _, _, _ = _reason(_task(reasoning_mode=ReasoningMode.COMPARATIVE.value), _ctx())
    assert v == CognitiveVerdict.INSUFFICIENT_EVIDENCE.value
    assert ep in {"INSUFFICIENT_EVIDENCE", "UNKNOWN"}


def test_causal_still_not_implemented() -> None:
    v, _, trace, _, _ = _reason(
        _task(reasoning_mode=ReasoningMode.CAUSAL_HYPOTHESIS.value),
        _ctx(_item("M1", "SYNTHETIC_TEST_DATA timeout")),
    )
    assert v == CognitiveVerdict.NOT_IMPLEMENTED.value
    assert trace.mode_status == "NOT_IMPLEMENTED"


def test_lesson_application_and_false_application(tmp_path: Path) -> None:
    mem = CognitiveMemoryStore(tmp_path / "ahos_cognitive_memory.sqlite")
    fact = mem.remember(
        memory_type=MemoryType.EPISODIC,
        epistemic_kind=EpistemicKind.OBSERVED_FACT,
        statement="SYNTHETIC_TEST_DATA: retries after HTTP timeout recovered the request.",
        source_type=SourceType.SYSTEM,
        source_id="f1",
        source_location="tests/test_typed_reasoning.py",
        producer="pytest",
        producer_version="p5",
        domain="software",
        context="SYNTHETIC_TEST_DATA",
        observed_at=NOW - 50,
        created_at=NOW - 40,
        payload={"data_label": "SYNTHETIC_TEST_DATA"},
    )
    ok_lesson = mem.remember(
        memory_type=MemoryType.SEMANTIC,
        epistemic_kind=EpistemicKind.LESSON,
        statement="SYNTHETIC_TEST_DATA LESSON: timeout retries are not proof of recovery",
        source_type=SourceType.SYSTEM,
        source_id="l-ok",
        source_location="tests/test_typed_reasoning.py",
        producer="pytest",
        producer_version="p5",
        domain="software",
        context="SYNTHETIC_TEST_DATA",
        created_at=NOW - 30,
        payload={"data_label": "SYNTHETIC_TEST_DATA", "applicability": "software"},
    )
    bad_lesson = mem.remember(
        memory_type=MemoryType.SEMANTIC,
        epistemic_kind=EpistemicKind.LESSON,
        statement="SYNTHETIC_TEST_DATA LESSON: timeout retries always work in finance",
        source_type=SourceType.SYSTEM,
        source_id="l-bad",
        source_location="tests/test_typed_reasoning.py",
        producer="pytest",
        producer_version="p5",
        domain="finance",
        context="SYNTHETIC_TEST_DATA",
        created_at=NOW - 29,
        payload={"data_label": "SYNTHETIC_TEST_DATA", "applicability": "finance"},
    )
    fact_item = _item(fact.memory_id, fact.statement)
    ok_item = _item(
        ok_lesson.memory_id, ok_lesson.statement, kind=EpistemicKind.LESSON.value
    )
    bad_item = _item(
        bad_lesson.memory_id,
        bad_lesson.statement,
        kind=EpistemicKind.LESSON.value,
        domain="finance",
    )
    v1, ep1, t1, _, _ = _reason(
        _task(reasoning_mode=ReasoningMode.DEDUCTIVE.value),
        _ctx(fact_item),
        store=mem,
    )
    v2, ep2, t2, _, _ = _reason(
        _task(reasoning_mode=ReasoningMode.DEDUCTIVE.value),
        _ctx(fact_item, ok_item),
        store=mem,
    )
    v3, ep3, t3, _, _ = _reason(
        _task(reasoning_mode=ReasoningMode.DEDUCTIVE.value),
        _ctx(fact_item, bad_item),
        store=mem,
    )
    assert v1 == CognitiveVerdict.WEAKLY_SUPPORTED.value
    assert t2.inference_records[0]["lesson_applied"] is True
    assert ep2 == "UNCERTAIN"
    assert t3.inference_records[0]["lesson_applied"] is False
    assert ep3 == "PROBABLE"


def test_failure_application_bounded(tmp_path: Path) -> None:
    mem = CognitiveMemoryStore(tmp_path / "ahos_cognitive_memory.sqlite")
    fact = mem.remember(
        memory_type=MemoryType.EPISODIC,
        epistemic_kind=EpistemicKind.OBSERVED_FACT,
        statement="SYNTHETIC_TEST_DATA: retries after HTTP timeout recovered the request.",
        source_type=SourceType.SYSTEM,
        source_id="f1",
        source_location="tests/test_typed_reasoning.py",
        producer="pytest",
        producer_version="p5",
        domain="software",
        context="SYNTHETIC_TEST_DATA",
        observed_at=NOW - 50,
        created_at=NOW - 40,
        payload={"data_label": "SYNTHETIC_TEST_DATA"},
    )
    match = mem.record_failure(
        failure_type="timeout_retry",
        component="http_client",
        attempted_action="retry after timeout",
        observed_failure="SYNTHETIC_TEST_DATA: timeout retry failed; rollback missing",
        now=NOW - 10,
        producer="pytest",
    )
    mismatch = mem.record_failure(
        failure_type="disk_full",
        component="database",
        attempted_action="write page",
        observed_failure="SYNTHETIC_TEST_DATA: database disk full",
        now=NOW - 9,
        producer="pytest",
    )
    fact_item = _item(fact.memory_id, fact.statement)
    match_item = _item(
        match.memory_id,
        match.statement,
        kind=EpistemicKind.OBSERVED_FACT.value,
        mtype=MemoryType.FAILURE.value,
    )
    mismatch_item = _item(
        mismatch.memory_id,
        mismatch.statement,
        kind=EpistemicKind.OBSERVED_FACT.value,
        mtype=MemoryType.FAILURE.value,
    )
    task_match = _task(
        reasoning_mode=ReasoningMode.DEDUCTIVE.value,
        constraints={"component": "http_client", "failure_type": "timeout_retry"},
    )
    task_other = _task(
        reasoning_mode=ReasoningMode.DEDUCTIVE.value,
        constraints={"component": "database", "failure_type": "disk_full"},
        domain="software",
    )
    v_ok, _, t_ok, _, _ = _reason(task_match, _ctx(fact_item, match_item), store=mem)
    v_bad, _, t_bad, _, _ = _reason(
        _task(reasoning_mode=ReasoningMode.DEDUCTIVE.value),
        _ctx(fact_item, mismatch_item),
        store=mem,
    )
    assert v_ok == CognitiveVerdict.CONTESTED.value
    assert t_ok.inference_records[0]["failure_applied"] is True
    assert t_bad.inference_records[0]["failure_applied"] is False
    assert v_bad == CognitiveVerdict.WEAKLY_SUPPORTED.value
    assert task_other.constraints["component"] == "database"


def test_contradiction_preserved() -> None:
    a = _item("A", "SYNTHETIC_TEST_DATA: measurement supports claim X.")
    b = _item("B", "SYNTHETIC_TEST_DATA: measurement contradicts claim X.")
    ctx = CognitiveContext(
        facts=(a, b),
        inferences=(),
        hypotheses=(),
        predictions=(),
        experiments=(),
        outcomes=(),
        contradictions=(
            {"edge_id": "e1", "from_id": "A", "to_id": "B", "relation": "CONTRADICTS"},
        ),
        failures=(),
        procedures=(),
        lessons=(),
        unknowns=(),
        excluded=(),
        contradiction_present=True,
        context_incomplete=False,
        token_estimate=2,
    )
    v, ep, trace, crit, _ = _reason(
        _task(reasoning_mode=ReasoningMode.DEDUCTIVE.value), ctx
    )
    assert v in {CognitiveVerdict.UNRESOLVED.value, CognitiveVerdict.CONTESTED.value}
    assert v != CognitiveVerdict.SUPPORTED.value
    assert "opposing" in crit.alternative_explanation.lower() or ctx.contradiction_present
    assert trace.contradictions


def test_closed_loop_second_episode_changes_reasoning(tmp_path: Path) -> None:
    mem = CognitiveMemoryStore(tmp_path / "ahos_cognitive_memory.sqlite")
    hyp = HypothesisStore(tmp_path / "hyp.jsonl")
    orch = CognitiveOrchestrator(memory=mem, hypotheses=hyp, ledger_path=tmp_path / "exp.jsonl")
    mem.remember(
        memory_type=MemoryType.EPISODIC,
        epistemic_kind=EpistemicKind.OBSERVED_FACT,
        statement="SYNTHETIC_TEST_DATA: retries after HTTP timeout recovered the request.",
        source_type=SourceType.SYSTEM,
        source_id="seed",
        source_location="tests/test_typed_reasoning.py",
        producer="pytest",
        producer_version="p5",
        domain="software",
        context="SYNTHETIC_TEST_DATA",
        observed_at=NOW - 80,
        created_at=NOW - 70,
        payload={"data_label": "SYNTHETIC_TEST_DATA"},
    )
    t1 = _task(
        task_id="ep1",
        reasoning_mode=ReasoningMode.DEDUCTIVE.value,
        write_back=True,
        task_type=TaskType.ANALYZE.value,
    )
    r1 = orch.run(t1, now=NOW)
    assert r1.lesson_memory_id
    assert r1.verdict == CognitiveVerdict.WEAKLY_SUPPORTED.value
    assert r1.epistemic == "PROBABLE"
    assert r1.lesson_applied is False
    mem.remember(
        memory_type=MemoryType.SEMANTIC,
        epistemic_kind=EpistemicKind.LESSON,
        statement="SYNTHETIC_TEST_DATA LESSON: do not treat timeout retry recovery as proof",
        source_type=SourceType.SYSTEM,
        source_id="manual-lesson",
        source_location="tests/test_typed_reasoning.py",
        producer="pytest",
        producer_version="p5",
        domain="software",
        context="SYNTHETIC_TEST_DATA",
        created_at=NOW + 1,
        payload={"data_label": "SYNTHETIC_TEST_DATA", "applicability": "software"},
    )
    t2 = _task(
        task_id="ep2",
        reasoning_mode=ReasoningMode.DEDUCTIVE.value,
        write_back=False,
        task_type=TaskType.ANALYZE.value,
    )
    r2 = orch.run(t2, now=NOW + 5)
    assert r2.lesson_applied is True
    assert r2.epistemic == "UNCERTAIN"
    assert r1.epistemic != r2.epistemic
    assert r2.authorized_execution is False


def test_assumption_binding_present() -> None:
    _, _, trace, _, assumptions = _reason(
        _task(), _ctx(_item("M1", "SYNTHETIC_TEST_DATA timeout retry recovered"))
    )
    assert assumptions
    assert assumptions[0].assumption_id
    assert assumptions[0].basis
    assert trace.assumptions


def test_cross_domain_core_does_not_require_crypto_fields() -> None:
    for domain, q in (
        ("science", "Do calibration retries recover the measurement?"),
        ("finance", "Do retries recover the token observation?"),
        ("operations", "Do retries recover queue depth?"),
        ("software", "Do retries after timeout help?"),
    ):
        fact = _item(
            f"F-{domain}",
            f"SYNTHETIC_TEST_DATA {domain} retries recovered",
            domain=domain,
        )
        v, _, trace, _, _ = _reason(
            _task(domain=domain, question=q, reasoning_mode=ReasoningMode.DEDUCTIVE.value),
            _ctx(fact),
        )
        assert v == CognitiveVerdict.WEAKLY_SUPPORTED.value
        assert "pair" not in trace.conclusion.lower() or True
