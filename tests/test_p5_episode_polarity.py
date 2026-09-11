"""P5 episode-level polarity architecture — adversarial matrix A–M.

Not entailment. Not NER. Isolated SYNTHETIC_TEST_DATA.
Graph CONTRADICTS edges are optional; mixed polarity must fail closed without them.
"""

from __future__ import annotations

import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from architecture.cognitive.hypothesis import HypothesisStore  # noqa: E402
from architecture.cognitive.loop.binding import bind_context  # noqa: E402
from architecture.cognitive.loop.contracts import (  # noqa: E402
    CognitiveContext,
    CognitiveTask,
    CognitiveVerdict,
    ReasoningMode,
    RetrievedItem,
    TaskType,
)
from architecture.cognitive.loop.episode import (  # noqa: E402
    MIXED_POLARITY,
    episode_positive_block_reason,
    reusable_writeback_permitted,
)
from architecture.cognitive.loop.orchestrator import CognitiveOrchestrator  # noqa: E402
from architecture.cognitive.loop.reason import reason  # noqa: E402
from architecture.cognitive.loop.support import (  # noqa: E402
    ENTITY_NONE,
    ENTITY_SCOPED,
    POLARITY_SUPPORTS,
    classify_support,
    identity_tokens,
)
from architecture.cognitive.memory.store import CognitiveMemoryStore  # noqa: E402
from tests.observation_test_runtime import test_authority_scope  # noqa: E402
from tests.p5_grant_fixtures import authorize_retrieved_items, persist_authorized  # noqa: E402
from architecture.cognitive.memory.types import DecayState, EpistemicKind, MemoryType, SourceType  # noqa: E402

NOW = 1_800_000_000.0
POSITIVE = {
    CognitiveVerdict.SUPPORTED.value,
    CognitiveVerdict.WEAKLY_SUPPORTED.value,
}
Q_UNSCOPED = "Do retries after timeout reduce failures?"
SUPPORT = "Retries after timeout reduced failures."
CONTRA = "Retries after timeout increased failures."
UNCERTAIN = "It is unknown whether retries after timeout reduce failures."
CAFETERIA = "the lunch timeout retries were about cafeteria seating"


@pytest.fixture(autouse=True)
def _test_grant_scope():
    with test_authority_scope(trusted_now=NOW):
        yield


def _task(question: str = Q_UNSCOPED, *, domain: str = "software", **kwargs) -> CognitiveTask:
    base = dict(
        task_id="ep-polarity",
        task_type=TaskType.ANALYZE.value,
        objective="timeout retries",
        question=question,
        domain=domain,
        requester="pytest",
        created_at=NOW,
        data_label="SYNTHETIC_TEST_DATA",
        reasoning_mode=ReasoningMode.DEDUCTIVE.value,
        write_back=False,
    )
    base.update(kwargs)
    return CognitiveTask(**base)


def _item(mid: str, statement: str, **kwargs) -> RetrievedItem:
    return RetrievedItem(
        memory_id=mid,
        revision=1,
        statement=statement,
        match_reasons=("test",),
        evidence_class="DIRECT_OBSERVATION",
        memory_type=kwargs.get("memory_type", MemoryType.EPISODIC.value),
        epistemic_kind=kwargs.get("kind", EpistemicKind.OBSERVED_FACT.value),
        status=kwargs.get("status", "ACTIVE"),
        domain=kwargs.get("domain", "software"),
        source_id="pytest",
        agent_namespace="",
        observed_at=kwargs.get("observed_at", NOW - 20),
        created_at=NOW - 10,
    )


def _ctx(*items: RetrievedItem, edges: tuple = ()) -> CognitiveContext:
    facts = tuple(
        i
        for i in items
        if i.epistemic_kind
        in {EpistemicKind.OBSERVED_FACT.value, EpistemicKind.DERIVED_FACT.value}
        and i.memory_type != MemoryType.FAILURE.value
    )
    return CognitiveContext(
        facts=facts,
        inferences=(),
        hypotheses=(),
        predictions=(),
        opinions=(),
        simulations=(),
        experiments=(),
        outcomes=(),
        contradictions=edges,
        failures=(),
        procedures=(),
        lessons=(),
        unknowns=() if items else ("empty",),
        excluded=(),
        contradiction_present=bool(edges),
        context_incomplete=not items,
        token_estimate=len(items),
    )


def _live(task: CognitiveTask, *items: RetrievedItem, edges: tuple = ()):
    store = authorize_retrieved_items(*items)
    ctx = _ctx(*items, edges=edges)
    binds = bind_context(ctx, task, store=store, now=NOW)
    v, _, trace, _, _ = reason(
        task, ctx, retrieved_ids=[i.memory_id for i in items], store=store, now=NOW
    )
    return binds, v, trace


def _reusable(mem: CognitiveMemoryStore) -> tuple[list, list, list]:
    hyps = list(mem.find_by_type(MemoryType.HYPOTHESIS))
    lessons = [
        rec
        for rec in mem.find_by_type(MemoryType.SEMANTIC)
        if rec.epistemic_kind == EpistemicKind.LESSON.value
        and rec.statement.startswith("LESSON ")
    ]
    inferences = [
        rec
        for rec in mem.find_by_type(MemoryType.SEMANTIC)
        if rec.epistemic_kind == EpistemicKind.INFERENCE.value
        and rec.statement.startswith("INFERENCE ")
    ]
    return hyps, lessons, inferences


def _run_orch(
    tmp_path: Path,
    statements: list[str],
    task: CognitiveTask,
    *,
    contradict: bool = False,
    statuses: list[str] | None = None,
):
    mem = CognitiveMemoryStore(tmp_path / "mem.sqlite")
    hyp = HypothesisStore(tmp_path / "hyp.jsonl")
    orch = CognitiveOrchestrator(
        memory=mem, hypotheses=hyp, ledger_path=tmp_path / "exp.jsonl"
    )
    recs = []
    for i, statement in enumerate(statements):
        recs.append(
            persist_authorized(
                mem,
                f"SYNTHETIC_TEST_DATA: {statement}",
                source_id=f"seed-{i}",
                observed_at=NOW - 40 + i,
                domain=task.domain,
                created_at=NOW - 30 + i,
            )
        )
    if statuses:
        for rec, st in zip(recs, statuses):
            if st and st != DecayState.ACTIVE.value:
                mem.revise(
                    rec.memory_id,
                    status=st,
                    correction_reason="test-temporal",
                    now=NOW - 1,
                )
    if contradict and len(recs) >= 2:
        mem.contradict(recs[0].memory_id, recs[1].memory_id, reason="seeded", now=NOW - 1)
    if recs:
        task.requested_evidence = [rec.memory_id for rec in recs]
    result = orch.run(task, now=NOW)
    return result, mem, _reusable(mem)


def test_a_supports_only_may_be_weakly_and_reusable(tmp_path: Path) -> None:
    binds, v, trace = _live(_task(), _item("s", SUPPORT))
    assert binds[0].may_support_task() is True
    assert binds[0].contradicts_task() is False
    assert episode_positive_block_reason(binds) == ""
    assert v == CognitiveVerdict.WEAKLY_SUPPORTED.value
    assert trace.reusable_writeback is True
    wb_task = _task(
        task_id="a-wb",
        write_back=True,
        task_type=TaskType.INVESTIGATE.value,
    )
    result, mem, (hyps, lessons, infs) = _run_orch(tmp_path, [SUPPORT], wb_task)
    assert result.verdict == CognitiveVerdict.WEAKLY_SUPPORTED.value
    assert result.reusable_writeback is True
    assert result.hypothesis_id
    assert result.lesson_memory_id
    assert hyps and lessons and infs
    no_wb = _task(
        task_id="a-nowb",
        write_back=False,
        task_type=TaskType.INVESTIGATE.value,
    )
    result_f, mem_f, reusable_f = _run_orch(tmp_path / "nowb", [SUPPORT], no_wb)
    assert result_f.verdict == CognitiveVerdict.WEAKLY_SUPPORTED.value
    assert result_f.hypothesis_id == ""
    assert result_f.lesson_memory_id == ""
    assert reusable_f == ([], [], [])
    assert mem_f.find_by_type(MemoryType.HYPOTHESIS) == []


def test_b_contradicts_only_is_contested_no_reusable(tmp_path: Path) -> None:
    binds, v, trace = _live(_task(), _item("c", CONTRA))
    assert binds[0].may_support_task() is False
    assert binds[0].contradicts_task() is True
    assert v not in POSITIVE
    assert v == CognitiveVerdict.CONTESTED.value
    assert trace.reusable_writeback is False
    result, _, reusable = _run_orch(
        tmp_path,
        [CONTRA],
        _task(task_id="b-wb", write_back=True, task_type=TaskType.INVESTIGATE.value),
    )
    assert result.verdict not in POSITIVE
    assert result.reusable_writeback is False
    assert reusable == ([], [], [])
    assert result.hypothesis_id == ""
    assert result.lesson_memory_id == ""


def test_c_mixed_polarity_without_graph_edge_fail_closed(tmp_path: Path) -> None:
    binds, v, trace = _live(_task(), _item("s", SUPPORT), _item("c", CONTRA))
    assert any(b.may_support_task() for b in binds)
    assert any(b.contradicts_task() for b in binds)
    assert episode_positive_block_reason(binds) == MIXED_POLARITY
    assert v not in POSITIVE
    assert v in {
        CognitiveVerdict.CONTESTED.value,
        CognitiveVerdict.UNRESOLVED.value,
    }
    assert trace.reusable_writeback is False
    assert reusable_writeback_permitted("WEAKLY_SUPPORTED", binds) is False
    result, mem, reusable = _run_orch(
        tmp_path,
        [SUPPORT, CONTRA],
        _task(task_id="c-wb", write_back=True, task_type=TaskType.INVESTIGATE.value),
    )
    assert result.verdict not in POSITIVE
    assert result.reusable_writeback is False
    assert reusable == ([], [], [])
    assert result.hypothesis_id == ""
    assert result.lesson_memory_id == ""
    assert result.episode_memory_id
    result_f, _, reusable_f = _run_orch(
        tmp_path / "c-nowb",
        [SUPPORT, CONTRA],
        _task(task_id="c-nowb", write_back=False, task_type=TaskType.INVESTIGATE.value),
    )
    assert result_f.verdict not in POSITIVE
    assert reusable_f == ([], [], [])


def test_d_mixed_polarity_with_graph_edge_fail_closed(tmp_path: Path) -> None:
    edges = (
        {
            "edge_id": "e",
            "from_id": "s",
            "to_id": "c",
            "relation": "CONTRADICTS",
        },
    )
    binds, v, trace = _live(
        _task(), _item("s", SUPPORT), _item("c", CONTRA), edges=edges
    )
    assert episode_positive_block_reason(binds) == MIXED_POLARITY
    assert v not in POSITIVE
    assert v in {
        CognitiveVerdict.CONTESTED.value,
        CognitiveVerdict.UNRESOLVED.value,
    }
    assert trace.reusable_writeback is False
    result, _, reusable = _run_orch(
        tmp_path,
        [SUPPORT, CONTRA],
        _task(task_id="d-wb", write_back=True, task_type=TaskType.INVESTIGATE.value),
        contradict=True,
    )
    assert result.verdict not in POSITIVE
    assert reusable == ([], [], [])


def test_e_supports_plus_uncertain_not_weakly(tmp_path: Path) -> None:
    binds, v, trace = _live(_task(), _item("s", SUPPORT), _item("u", UNCERTAIN))
    assert any(b.may_support_task() for b in binds)
    assert episode_positive_block_reason(binds)
    assert v not in POSITIVE
    assert trace.reusable_writeback is False
    result, _, reusable = _run_orch(
        tmp_path,
        [SUPPORT, UNCERTAIN],
        _task(task_id="e-wb", write_back=True, task_type=TaskType.INVESTIGATE.value),
    )
    assert result.verdict not in POSITIVE
    assert reusable == ([], [], [])


def test_f_supports_plus_entity_mismatch_keeps_compatible_supporter(
    tmp_path: Path,
) -> None:
    q = "Do Service A retries after timeout reduce failures?"
    match = "Service A retries after timeout reduced failures."
    other = "Service B retries after timeout reduced failures."
    binds, v, trace = _live(_task(q), _item("a", match), _item("b", other))
    by_id = {b.memory_id: b for b in binds}
    assert by_id["a"].may_support_task() is True
    assert by_id["b"].may_support_task() is False
    assert by_id["b"].contradicts_task() is False
    assert episode_positive_block_reason(binds) == ""
    assert v == CognitiveVerdict.WEAKLY_SUPPORTED.value
    assert "b" not in trace.premises
    result, _, (hyps, lessons, infs) = _run_orch(
        tmp_path,
        [match, other],
        _task(
            q,
            task_id="f-wb",
            write_back=True,
            task_type=TaskType.INVESTIGATE.value,
        ),
    )
    assert result.verdict == CognitiveVerdict.WEAKLY_SUPPORTED.value
    assert hyps and lessons and infs


def test_g_metacognitive_cafeteria_does_not_cite_or_upgrade(tmp_path: Path) -> None:
    meta = _task(reasoning_mode=ReasoningMode.METACOGNITIVE.value)
    binds, v, trace = _live(meta, _item("s", SUPPORT), _item("cafe", CAFETERIA))
    by_id = {b.memory_id: b for b in binds}
    assert by_id["s"].may_support_task() is True
    assert by_id["cafe"].may_support_task() is False
    rec = trace.inference_records[0]
    cited = set(rec["supporting_evidence_ids"]) | set(rec["premises"])
    assert "cafe" not in cited
    assert "s" in cited
    assert v == CognitiveVerdict.WEAKLY_SUPPORTED.value
    cafe_only, v_cafe, trace_cafe = _live(meta, _item("cafe", CAFETERIA))
    assert cafe_only[0].may_support_task() is False
    assert v_cafe not in POSITIVE
    assert trace_cafe.reusable_writeback is False
    result, _, reusable = _run_orch(
        tmp_path,
        [CAFETERIA],
        _task(
            task_id="g-cafe",
            write_back=True,
            task_type=TaskType.INVESTIGATE.value,
            reasoning_mode=ReasoningMode.METACOGNITIVE.value,
        ),
    )
    assert result.verdict not in POSITIVE
    assert reusable == ([], [], [])


def test_h_polarity_mutation_cannot_override_recompute() -> None:
    task = _task()
    binds = bind_context(_ctx(_item("c", CONTRA)), task)
    b = binds[0]
    assert b.may_support_task() is False
    with pytest.raises(FrozenInstanceError):
        b.support_polarity = POLARITY_SUPPORTS  # type: ignore[misc]
    object.__setattr__(b, "support_polarity", POLARITY_SUPPORTS)
    object.__setattr__(b, "support_class", "DIRECT_SUPPORT")
    object.__setattr__(b, "clause_force", "AFFIRMED")
    assert b.may_support_task() is False
    assert b.contradicts_task() is True
    _, v, trace = _live(task, _item("c", CONTRA))
    assert v not in POSITIVE
    assert trace.reusable_writeback is False


def test_i_did_is_not_an_identity_marker() -> None:
    q = "Did retries after timeout reduce failures?"
    ids = identity_tokens(q)
    assert "did" not in ids
    a = classify_support(SUPPORT, _task(q))
    assert a.entity_state == ENTITY_NONE
    binds, v, trace = _live(_task(q), _item("s", SUPPORT))
    assert binds[0].may_support_task() is True
    assert v == CognitiveVerdict.WEAKLY_SUPPORTED.value
    assert trace.reusable_writeback is True


def test_j_can_is_not_an_identity_marker() -> None:
    q = "Can retries after timeout reduce failures?"
    ids = identity_tokens(q)
    assert "can" not in ids
    a = classify_support(SUPPORT, _task(q))
    assert a.entity_state == ENTITY_NONE
    binds, v, _ = _live(_task(q), _item("s", SUPPORT))
    assert binds[0].may_support_task() is True
    assert v == CognitiveVerdict.WEAKLY_SUPPORTED.value


def test_k_entity_scoped_evidence_does_not_support_unscoped_task(
    tmp_path: Path,
) -> None:
    statement = "Service A retries after timeout reduced failures."
    a = classify_support(statement, _task(Q_UNSCOPED))
    assert a.entity_state == ENTITY_SCOPED
    assert a.may_support_positive() is False
    binds, v, trace = _live(_task(), _item("a", statement))
    assert binds[0].may_support_task() is False
    assert v not in POSITIVE
    assert trace.reusable_writeback is False
    result, _, reusable = _run_orch(
        tmp_path,
        [statement],
        _task(task_id="k-wb", write_back=True, task_type=TaskType.INVESTIGATE.value),
    )
    assert result.verdict not in POSITIVE
    assert reusable == ([], [], [])


def test_l_assumption_only_is_not_evidence(tmp_path: Path) -> None:
    binds, v, trace = _live(_task())
    assert binds == []
    assert v == CognitiveVerdict.INSUFFICIENT_EVIDENCE.value
    assert trace.assumptions
    assert trace.assumptions[0].origin == "ASSUMED"
    assert not trace.premises
    assert trace.reusable_writeback is False
    result, mem, reusable = _run_orch(
        tmp_path,
        [],
        _task(task_id="l-wb", write_back=True, task_type=TaskType.INVESTIGATE.value),
    )
    assert result.verdict not in POSITIVE
    assert reusable == ([], [], [])
    cited = " ".join(trace.premises)
    assert "ASM-" not in cited


def test_m_stale_is_not_current_and_not_reusable(tmp_path: Path) -> None:
    stale = _item("old", SUPPORT, status="STALE", observed_at=NOW - 10_000)
    binds, v, trace = _live(_task(), stale)
    assert binds[0].temporal_state in {"STALE", "SUPERSEDED", "HISTORICAL"}
    assert binds[0].temporal_state != "CURRENT"
    assert v not in POSITIVE
    assert trace.reusable_writeback is False
    result, mem, reusable = _run_orch(
        tmp_path,
        [SUPPORT],
        _task(task_id="m-wb", write_back=True, task_type=TaskType.INVESTIGATE.value),
        statuses=["STALE"],
    )
    # Orchestrator remember() may still store ACTIVE unless status is honored;
    # live bind path above is the architecture check. Re-bind the stored row.
    stored = [r for r in mem.find_by_type(MemoryType.EPISODIC) if r.statement.startswith("SYNTHETIC_TEST_DATA")]
    assert stored
    assert stored[0].status == DecayState.STALE.value
    assert result.verdict not in POSITIVE
    assert reusable == ([], [], [])


def test_writeback_invariant_is_enforced_below_caller() -> None:
    """A forged WEAKLY_SUPPORTED string cannot mint reusable knowledge."""
    task = _task()
    mixed = bind_context(_ctx(_item("s", SUPPORT), _item("c", CONTRA)), task)
    uncertain = bind_context(_ctx(_item("s", SUPPORT), _item("u", UNCERTAIN)), task)
    scoped = bind_context(
        _ctx(_item("a", "Service A retries after timeout reduced failures.")), task
    )
    cafe = bind_context(_ctx(_item("cafe", CAFETERIA)), task)
    empty = bind_context(_ctx(), task)
    for binds in (mixed, uncertain, scoped, cafe, empty):
        assert reusable_writeback_permitted("WEAKLY_SUPPORTED", binds) is False
        assert reusable_writeback_permitted("SUPPORTED", binds) is False


def test_seven_modes_mixed_polarity_none_emit_weakly() -> None:
    items = (_item("s", SUPPORT), _item("c", CONTRA))
    for mode in (
        ReasoningMode.DEDUCTIVE.value,
        ReasoningMode.INDUCTIVE.value,
        ReasoningMode.ABDUCTIVE.value,
        ReasoningMode.COMPARATIVE.value,
        ReasoningMode.TEMPORAL.value,
        ReasoningMode.ADVERSARIAL.value,
        ReasoningMode.METACOGNITIVE.value,
    ):
        _, v, trace = _live(_task(reasoning_mode=mode), *items)
        assert v not in POSITIVE, mode
        assert trace.reusable_writeback is False, mode
