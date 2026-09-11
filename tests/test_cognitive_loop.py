"""P3 cognitive loop: retrieval, context, reasoning, learning — Lane B PAPER_ONLY.

Synthetic data is labelled SYNTHETIC_TEST_DATA. Isolated SQLite only.
Does not open soak databases. Does not import Lane A.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from architecture.cognitive import (  # noqa: E402
    HypothesisStore,
    LaneAChangeRequired,
    record_cognitive_experiment,
    propose_lane_b_evolution,
)
from architecture.cognitive.loop.adapters import (  # noqa: E402
    finance_observation,
    operations_observation,
    science_observation,
    software_observation,
)
from architecture.cognitive.loop.benchmark import run_memory_vs_no_memory  # noqa: E402
from architecture.cognitive.loop.context import assemble_context  # noqa: E402
from architecture.cognitive.loop.contracts import (  # noqa: E402
    CognitiveTask,
    ContextBudget,
    ReasoningMode,
    RetrievedItem,
    TaskType,
)
from architecture.cognitive.loop.metacognition import metacognitive_state  # noqa: E402
from architecture.cognitive.loop.metrics import METRIC_SPECS, compute_lesson_reuse  # noqa: E402
from architecture.cognitive.loop.reason import reason  # noqa: E402
from architecture.cognitive.loop.retrieval import MemoryRetriever  # noqa: E402
from architecture.cognitive.loop.tools import plan_tools  # noqa: E402
from architecture.cognitive.loop.world_boundary import current_world_model_boundary  # noqa: E402
from architecture.cognitive.memory.store import (  # noqa: E402
    CognitiveMemoryStore,
    MemoryAuthorizationError,
    SoakBoundaryError,
)
from tests.observation_test_runtime import TestCognitiveOrchestrator  # noqa: E402
from tests.p5_grant_fixtures import persist_authorized  # noqa: E402
from architecture.cognitive.memory.types import (  # noqa: E402
    DecayState,
    EpistemicKind,
    MemoryType,
    SourceType,
)
LOOP_DIR = ROOT / "architecture" / "cognitive" / "loop"
FORBIDDEN = {"discovery", "paper_trading", "telegram_ai", "engine"}
NOW = 1_800_000_000.0


def _task(**kwargs) -> CognitiveTask:
    base = dict(
        task_id="t1",
        task_type=TaskType.ANALYZE.value,
        objective="objective",
        question="question",
        domain="software",
        requester="pytest",
        created_at=NOW,
        data_label="SYNTHETIC_TEST_DATA",
    )
    base.update(kwargs)
    return CognitiveTask(**base)


def _stores(tmp_path: Path) -> tuple[CognitiveMemoryStore, HypothesisStore, Path]:
    mem = CognitiveMemoryStore(tmp_path / "ahos_cognitive_memory.sqlite")
    hyp = HypothesisStore(tmp_path / "p3_hyp.jsonl")
    ledger = tmp_path / "p3_exp.jsonl"
    return mem, hyp, ledger


def _seed_fact(
    store: CognitiveMemoryStore,
    *,
    statement: str,
    domain: str,
    source_id: str,
    observed_at: float = NOW - 200.0,
    created_at: float = NOW - 100.0,
    valid_until: float | None = None,
    agent_id: str = "",
    agent_namespace: str = "",
) -> str:
    rec = persist_authorized(
        store,
        statement,
        source_id=source_id,
        observed_at=observed_at,
        domain=domain,
        valid_until=valid_until,
        created_at=created_at,
        agent_id=agent_id,
        agent_namespace=agent_namespace,
    )
    return rec.memory_id


def test_closed_loop_second_episode_retrieves_lesson(tmp_path: Path) -> None:
    mem, hyp, ledger = _stores(tmp_path)
    _seed_fact(
        mem,
        statement="SYNTHETIC_TEST_DATA: retries after HTTP timeout recovered the request.",
        domain="software",
        source_id="seed-timeout",
    )
    orch = TestCognitiveOrchestrator(memory=mem, hypotheses=hyp, ledger_path=ledger)
    r1 = orch.run(
        _task(
            task_id="task-loop-1",
            task_type=TaskType.INVESTIGATE.value,
            objective="Investigate timeout recovery",
            question="Do retries after timeout help?",
            domain="software",
        ),
        now=NOW,
    )
    assert r1.hypothesis_id
    assert r1.experiment_id
    assert r1.lesson_memory_id
    hyp_rec = hyp.get(r1.hypothesis_id)
    assert hyp_rec is not None
    assert hyp_rec.provenance.get("falsification_condition")
    assert hyp_rec.provenance.get("novelty_equals_truth") is False
    lesson = mem.get(r1.lesson_memory_id)
    assert lesson is not None
    assert lesson.epistemic_kind == EpistemicKind.LESSON.value
    assert lesson.memory_type != MemoryType.EPISODIC.value or lesson.epistemic_kind != EpistemicKind.OBSERVED_FACT.value
    episode = mem.get(r1.episode_memory_id)
    assert episode is not None
    assert episode.epistemic_kind == EpistemicKind.INFERENCE.value
    assert episode.epistemic_kind != EpistemicKind.OBSERVED_FACT.value

    r2 = orch.run(
        _task(
            task_id="task-loop-2",
            task_type=TaskType.LEARN.value,
            objective="Reuse prior timeout lesson",
            question="What did we learn about timeout retries?",
            domain="software",
            created_at=NOW + 10,
        ),
        now=NOW + 10,
    )
    assert r2.context is not None
    lesson_ids = {item.memory_id for item in r2.context.lessons}
    assert r1.lesson_memory_id in lesson_ids
    assert r1.lesson_memory_id in r2.trace.retrieved_ids
    kinds = [i.epistemic_kind for i in r2.retrieved]
    assert compute_lesson_reuse(kinds, used_memory=True) == 1.0
    state = metacognitive_state(r2)
    assert r1.lesson_memory_id in state["what_evidence_supports_it"] or state["what_i_know"] is not None
    assert r2.trace.assumptions
    assert r1.authorized_execution is False


def test_no_memory_baseline_does_not_retrieve_lesson(tmp_path: Path) -> None:
    mem, hyp, ledger = _stores(tmp_path)
    _seed_fact(
        mem,
        statement="SYNTHETIC_TEST_DATA timeout retry recovered",
        domain="software",
        source_id="seed-a",
    )
    orch = TestCognitiveOrchestrator(memory=mem, hypotheses=hyp, ledger_path=ledger)
    r1 = orch.run(
        _task(
            task_id="nm-1",
            task_type=TaskType.INVESTIGATE.value,
            objective="timeout",
            question="timeout retry?",
        ),
        now=NOW,
        use_memory=True,
    )
    r2 = orch.run(
        _task(
            task_id="nm-2",
            task_type=TaskType.LEARN.value,
            objective="timeout lesson",
            question="timeout retry lesson?",
            created_at=NOW + 5,
            write_back=False,
        ),
        now=NOW + 5,
        use_memory=False,
    )
    assert r2.context is not None
    assert r2.context.all_included() == []
    assert r1.lesson_memory_id not in r2.trace.retrieved_ids
    assert compute_lesson_reuse([], used_memory=False) == 0.0


def test_failure_learning_next_task_retrieves_failure(tmp_path: Path) -> None:
    mem, hyp, ledger = _stores(tmp_path)
    _seed_fact(
        mem,
        statement="SYNTHETIC_TEST_DATA deploy checklist missing rollback",
        domain="operations",
        source_id="seed-fail",
    )
    orch = TestCognitiveOrchestrator(memory=mem, hypotheses=hyp, ledger_path=ledger)
    task1 = _task(
        task_id="fail-1",
        task_type=TaskType.ANALYZE.value,
        objective="deploy checklist",
        question="deploy checklist rollback?",
        domain="operations",
    )
    r1 = orch.run(task1, now=NOW)
    fail = orch.record_failure(
        task1,
        observed_failure="SYNTHETIC_TEST_DATA: deploy checklist failed; rollback missing",
        attempted_action="analyze deploy checklist",
        recovery="retrieve prior failure before retry",
        recovery_worked=True,
        now=NOW + 1,
    )
    r2 = orch.run(
        _task(
            task_id="fail-2",
            task_type=TaskType.INVESTIGATE.value,
            objective="avoid prior deploy failure",
            question="deploy checklist recurrence rollback?",
            domain="operations",
            created_at=NOW + 2,
        ),
        now=NOW + 2,
    )
    fail_ids = {item.memory_id for item in (r2.context.failures if r2.context else ())}
    assert fail.memory_id in fail_ids
    fail_item = next(i for i in r2.retrieved if i.memory_id == fail.memory_id)
    assert any("failure" in r for r in fail_item.match_reasons)
    assert r1.verdict  # first episode recorded; failure is a separate write


def test_contradiction_preserved_unresolved(tmp_path: Path) -> None:
    mem, hyp, ledger = _stores(tmp_path)
    a = _seed_fact(
        mem,
        statement="SYNTHETIC_TEST_DATA: measurement supports claim X.",
        domain="science",
        source_id="mem-supports-x",
    )
    b = _seed_fact(
        mem,
        statement="SYNTHETIC_TEST_DATA: measurement contradicts claim X.",
        domain="science",
        source_id="mem-contradicts-x",
        created_at=NOW - 90,
    )
    mem.contradict(a, b, reason="synthetic opposing measurements")
    orch = TestCognitiveOrchestrator(memory=mem, hypotheses=hyp, ledger_path=ledger)
    result = orch.run(
        _task(
            task_id="contra-1",
            task_type=TaskType.COMPARE.value,
            objective="evaluate claim X",
            question="Is claim X supported or contradicted?",
            domain="science",
        ),
        now=NOW,
    )
    ids = {item.memory_id for item in result.retrieved}
    assert a in ids
    assert b in ids
    assert result.context is not None
    assert result.context.contradiction_present
    assert result.verdict in {"CONTESTED", "UNRESOLVED"}
    assert result.trace.contradictions
    a_rec = mem.get(a)
    b_rec = mem.get(b)
    assert a_rec is not None and b_rec is not None
    assert a_rec.statement.startswith("SYNTHETIC_TEST_DATA")
    assert b_rec.statement.startswith("SYNTHETIC_TEST_DATA")


def test_temporal_stale_not_current_history_queryable(tmp_path: Path) -> None:
    mem, _, _ = _stores(tmp_path)
    old_obs = NOW - 10_000.0
    new_obs = NOW - 10.0
    ingested = NOW - 5.0
    old_id = _seed_fact(
        mem,
        statement="SYNTHETIC_TEST_DATA historical temperature 10C",
        domain="science",
        source_id="hist-old",
        observed_at=old_obs,
        created_at=ingested,
        valid_until=NOW - 1_000.0,
    )
    new_id = _seed_fact(
        mem,
        statement="SYNTHETIC_TEST_DATA current temperature 20C",
        domain="science",
        source_id="hist-new",
        observed_at=new_obs,
        created_at=ingested,
    )
    mem.apply_decay(now=NOW)
    old_rec = mem.get(old_id)
    new_rec = mem.get(new_id)
    assert old_rec is not None and new_rec is not None
    assert old_rec.observed_at != old_rec.created_at
    assert old_rec.status == DecayState.STALE.value
    assert new_rec.status != DecayState.STALE.value
    hist = mem.history(old_id)
    assert hist[0].statement == "SYNTHETIC_TEST_DATA historical temperature 10C"
    retriever = MemoryRetriever()
    items = retriever.retrieve(
        mem,
        _task(
            task_id="temp-1",
            objective="temperature",
            question="current temperature reading",
            domain="science",
        ),
        now=NOW,
    )
    ids = {i.memory_id for i in items}
    assert old_id in ids
    assert new_id in ids
    stale_item = next(i for i in items if i.memory_id == old_id)
    assert any("stale" in r for r in stale_item.match_reasons)


def test_agent_namespace_isolation(tmp_path: Path) -> None:
    mem, _, _ = _stores(tmp_path)
    a_id = _seed_fact(
        mem,
        statement="SYNTHETIC_TEST_DATA private A note",
        domain="operations",
        source_id="priv-a",
        agent_id="agent_A",
        agent_namespace="agent_A",
    )
    b_id = _seed_fact(
        mem,
        statement="SYNTHETIC_TEST_DATA private B note",
        domain="operations",
        source_id="priv-b",
        agent_id="agent_B",
        agent_namespace="agent_B",
    )
    retriever = MemoryRetriever()
    ids_a = {
        i.memory_id
        for i in retriever.retrieve(
            mem,
            _task(
                task_id="ns-a",
                objective="private note",
                question="private A note",
                domain="operations",
                requester="agent_A",
                agent_id="agent_A",
            ),
            now=NOW,
        )
    }
    assert a_id in ids_a
    assert b_id not in ids_a
    ids_b = {
        i.memory_id
        for i in retriever.retrieve(
            mem,
            _task(
                task_id="ns-b",
                objective="private note",
                question="private B note",
                domain="operations",
                requester="agent_B",
                agent_id="agent_B",
            ),
            now=NOW,
        )
    }
    assert b_id in ids_b
    assert a_id not in ids_b


def test_domain_generality_four_adapters(tmp_path: Path) -> None:
    mem, hyp, ledger = _stores(tmp_path)
    finance_observation(
        mem,
        statement="SYNTHETIC_TEST_DATA paper token observation",
        source_id="fin-1",
        observed_at=NOW - 20,
        created_at=NOW - 10,
    )
    science_observation(
        mem,
        statement="SYNTHETIC_TEST_DATA lab measurement",
        source_id="sci-1",
        observed_at=NOW - 20,
        created_at=NOW - 10,
    )
    software_observation(
        mem,
        statement="SYNTHETIC_TEST_DATA build timeout",
        source_id="sw-1",
        observed_at=NOW - 20,
        created_at=NOW - 10,
    )
    operations_observation(
        mem,
        statement="SYNTHETIC_TEST_DATA queue depth",
        source_id="ops-1",
        observed_at=NOW - 20,
        created_at=NOW - 10,
    )
    orch = TestCognitiveOrchestrator(memory=mem, hypotheses=hyp, ledger_path=ledger)
    for domain, q in (
        ("finance", "token observation"),
        ("science", "lab measurement"),
        ("software", "build timeout"),
        ("operations", "queue depth"),
    ):
        result = orch.run(
            _task(
                task_id=f"dom-{domain}",
                objective=q,
                question=q,
                domain=domain,
                write_back=False,
            ),
            now=NOW,
        )
        assert result.retrieved
        assert all(
            (item.domain == domain) or ("SYNTHETIC_TEST_DATA" in item.statement)
            for item in result.retrieved
        )
        rec = mem.get(result.retrieved[0].memory_id)
        assert rec is not None
        assert rec.payload.get("data_label") == "SYNTHETIC_TEST_DATA"


def test_causal_and_counterfactual_not_implemented(tmp_path: Path) -> None:
    mem, _, _ = _stores(tmp_path)
    mid = _seed_fact(
        mem,
        statement="SYNTHETIC_TEST_DATA event",
        domain="science",
        source_id="c-1",
    )
    rec = mem.get(mid)
    assert rec is not None
    item = RetrievedItem(
        memory_id=rec.memory_id,
        revision=rec.revision,
        statement=rec.statement,
        match_reasons=("same_domain",),
        evidence_class="DIRECT_OBSERVATION",
        memory_type=rec.memory_type,
        epistemic_kind=rec.epistemic_kind,
        status=rec.status,
        domain=rec.domain,
        source_id=rec.source_id,
        agent_namespace=rec.agent_namespace,
        observed_at=rec.observed_at,
        created_at=rec.created_at,
    )
    ctx = assemble_context([item], mem)
    r_causal = reason(
        _task(task_id="ni-1", domain="science", reasoning_mode=ReasoningMode.CAUSAL_HYPOTHESIS.value),
        ctx,
        retrieved_ids=[mid],
    )
    r_cf = reason(
        _task(task_id="ni-2", domain="science", reasoning_mode=ReasoningMode.COUNTERFACTUAL.value),
        ctx,
        retrieved_ids=[mid],
    )
    assert r_causal[0] == "NOT_IMPLEMENTED"
    assert r_cf[0] == "NOT_IMPLEMENTED"


def test_loop_cannot_authorize_execution(tmp_path: Path) -> None:
    mem, hyp, ledger = _stores(tmp_path)
    orch = TestCognitiveOrchestrator(memory=mem, hypotheses=hyp, ledger_path=ledger)
    with pytest.raises(MemoryAuthorizationError):
        orch.authorize_execution("anything")


def test_tool_selection_interface_only() -> None:
    from architecture.cognitive.contracts import CapabilityStatus

    out = plan_tools("analyze logs")
    assert out.status == CapabilityStatus.NOT_IMPLEMENTED.value


def test_world_model_boundary_is_not_a_world_model() -> None:
    b = current_world_model_boundary()
    assert b.status == "NOT_IMPLEMENTED"
    assert "ENTITY" in b.allowed_object_kinds


def test_evolution_cannot_leave_b_only() -> None:
    with pytest.raises(LaneAChangeRequired):
        propose_lane_b_evolution(
            diagnosis="p3",
            detected_by="pytest",
            proposed_by="pytest",
            is_ai=True,
            candidate_diff_ref="none",
            test_battery=["tests/test_cognitive_loop.py"],
            rollback_plan={"trigger": "any", "action": "revert branch"},
            target_scope="LANE_A_FORBIDDEN",
        )


def test_metric_definitions_have_no_fabricated_scores() -> None:
    names = {s.name for s in METRIC_SPECS}
    assert "lesson_reuse_rate" in names
    assert "contradiction_detection_rate" in names
    for spec in METRIC_SPECS:
        blob = f"{spec.baseline} {spec.limitations}".lower()
        assert "99.9" not in blob
        assert "limitation" in spec.limitations.lower() or len(spec.limitations) > 10


def test_context_incomplete_is_explicit(tmp_path: Path) -> None:
    mem, _, _ = _stores(tmp_path)
    mid = _seed_fact(
        mem,
        statement="SYNTHETIC_TEST_DATA overflow item timeout",
        domain="software",
        source_id="ov-1",
    )
    rec = mem.get(mid)
    assert rec is not None
    item = RetrievedItem(
        memory_id=rec.memory_id,
        revision=rec.revision,
        statement=rec.statement,
        match_reasons=("same_domain",),
        evidence_class="DIRECT_OBSERVATION",
        memory_type=rec.memory_type,
        epistemic_kind=rec.epistemic_kind,
        status=rec.status,
        domain=rec.domain,
        source_id=rec.source_id,
        agent_namespace=rec.agent_namespace,
        observed_at=rec.observed_at,
        created_at=rec.created_at,
    )
    ctx = assemble_context([item], mem, budget=ContextBudget(max_memories=0))
    assert ctx.context_incomplete is True
    assert ctx.excluded


def test_p3_loop_must_not_import_lane_a_or_telegram() -> None:
    for path in LOOP_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    assert top not in FORBIDDEN, f"{path.name} imports {alias.name}"
            elif isinstance(node, ast.ImportFrom) and node.module:
                top = node.module.split(".")[0]
                assert top not in FORBIDDEN, f"{path.name} imports {node.module}"


def test_loop_sqlite_filename_still_guarded(tmp_path: Path) -> None:
    with pytest.raises(SoakBoundaryError):
        CognitiveMemoryStore(tmp_path / "paper_trading.sqlite")


def test_record_cognitive_experiment_still_analysis_only(tmp_path: Path) -> None:
    store = HypothesisStore(tmp_path / "hyp.jsonl")
    rec = store.propose("SYNTHETIC_TEST_DATA P3 eval")
    exp = record_cognitive_experiment(
        hypothesis_store=store,
        hypothesis_id=rec.hypothesis_id,
        baseline="none",
        method="bounded analysis",
        result="INSUFFICIENT_DATA",
        ledger_path=tmp_path / "exp.jsonl",
    )
    dumped = exp.ledger_record.as_dict()
    assert dumped["result"] == "INSUFFICIENT_DATA"
    assert dumped["classification"] == "COGNITIVE"


def test_memory_vs_no_memory_benchmark(tmp_path: Path) -> None:
    from architecture.cognitive.memory.observation import GRANT_PAYLOAD_KEY

    mem, hyp, ledger = _stores(tmp_path)
    out = run_memory_vs_no_memory(mem, hyp, ledger, now=NOW)
    assert out["data_label"] == "SYNTHETIC_TEST_DATA"
    assert out["no_memory_lesson_reuse"] == 0.0
    ofacts = [
        r
        for r in mem.find_by_type(MemoryType.EPISODIC)
        if r.epistemic_kind == EpistemicKind.OBSERVED_FACT.value
    ]
    assert ofacts
    assert all(GRANT_PAYLOAD_KEY not in (r.payload or {}) for r in ofacts)
    # Production helper cannot mint; ungranted seed is not a factual premise.
    assert out["memory_loop_lesson_reuse"] == 0.0
    assert not out["episode1_lesson_id"]
    assert out["episode2_retrieved_lesson"] is False
    assert out["unsupported_claim_rate"] == 0.0
    assert out["integrity"] == "ok"
    assert out["e2e_cycle_seconds"] < 5.0

    mem2, hyp2, ledger2 = _stores(tmp_path / "granted")
    persist_authorized(
        mem2,
        "SYNTHETIC_TEST_DATA retries after HTTP timeout recovered the request.",
        source_id="bench-timeout",
    )
    orch = TestCognitiveOrchestrator(memory=mem2, hypotheses=hyp2, ledger_path=ledger2)
    r1 = orch.run(
        _task(
            task_id="bench-1",
            task_type=TaskType.INVESTIGATE.value,
            objective="Investigate timeout recovery",
            question="Do retries after timeout help?",
            domain="software",
        ),
        now=NOW,
        use_memory=True,
    )
    r2 = orch.run(
        _task(
            task_id="bench-2",
            task_type=TaskType.LEARN.value,
            objective="Reuse prior timeout lesson",
            question="What did we learn about timeout retries?",
            domain="software",
            created_at=NOW + 1.0,
        ),
        now=NOW + 1.0,
        use_memory=True,
    )
    kinds_mem = [i.epistemic_kind for i in r2.retrieved]
    assert compute_lesson_reuse(kinds_mem, used_memory=True) == 1.0
    assert r1.lesson_memory_id
    assert r1.lesson_memory_id in {i.memory_id for i in (r2.context.lessons if r2.context else ())}
