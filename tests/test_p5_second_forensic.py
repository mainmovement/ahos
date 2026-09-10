"""P5 second forensic verification — write-back, mutation, seven modes, two-hop.

Not entailment. Not NER. Isolated SYNTHETIC_TEST_DATA.
"""

from __future__ import annotations

import ast
import inspect
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from architecture.cognitive.hypothesis import HypothesisStore  # noqa: E402
from architecture.cognitive.loop.binding import (  # noqa: E402
    ROLE_FACTUAL_PREMISE,
    SUPPORT_DIRECT,
    EvidenceBinding,
    bind_context,
)
from architecture.cognitive.loop.contracts import (  # noqa: E402
    CognitiveContext,
    CognitiveTask,
    CognitiveVerdict,
    ReasoningMode,
    RetrievedItem,
    TaskType,
)
from architecture.cognitive.loop.episode import (  # noqa: E402
    apply_episode_positive_policy,
    reusable_writeback_permitted,
)
from architecture.cognitive.loop.inference import (  # noqa: E402
    ACTION_CONTEST,
    ACTION_DOWNGRADE,
    ACTION_REFUSE,
    ACTION_REQUIRE_MORE,
    CandidateInference,
    apply_constraint,
)
from architecture.cognitive.loop.modes import MODE_FNS  # noqa: E402
from architecture.cognitive.loop.orchestrator import CognitiveOrchestrator  # noqa: E402
from architecture.cognitive.loop.reason import critique_result, reason  # noqa: E402
from architecture.cognitive.memory.store import CognitiveMemoryStore  # noqa: E402
from tests.p5_grant_fixtures import authorize_retrieved_items, persist_authorized  # noqa: E402
from architecture.cognitive.memory.types import (  # noqa: E402
    DecayState,
    EpistemicKind,
    MemoryType,
    SourceType,
)

NOW = 1_800_000_000.0
POSITIVE = {
    CognitiveVerdict.SUPPORTED.value,
    CognitiveVerdict.WEAKLY_SUPPORTED.value,
}
Q = "Do retries after timeout reduce failures?"
SUPPORT = "Retries after timeout reduced failures."
CONTRA = "Retries after timeout increased failures."
UNCERTAIN = "It is unknown whether retries after timeout reduce failures."
LEXICAL = "the lunch timeout retries were about cafeteria seating"
HELP_Q = "Do retries after timeout help?"
HELP_FACT = "retries after HTTP timeout recovered the request."

MODES = (
    ReasoningMode.DEDUCTIVE.value,
    ReasoningMode.INDUCTIVE.value,
    ReasoningMode.ABDUCTIVE.value,
    ReasoningMode.COMPARATIVE.value,
    ReasoningMode.TEMPORAL.value,
    ReasoningMode.ADVERSARIAL.value,
    ReasoningMode.METACOGNITIVE.value,
)


def _task(question: str = Q, **kwargs) -> CognitiveTask:
    base = dict(
        task_id="forensic2",
        task_type=TaskType.ANALYZE.value,
        objective="timeout retries",
        question=question,
        domain="software",
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
    hyps = tuple(i for i in items if i.epistemic_kind == EpistemicKind.HYPOTHESIS.value)
    preds = tuple(i for i in items if i.epistemic_kind == EpistemicKind.PREDICTION.value)
    opinions = tuple(i for i in items if i.epistemic_kind == EpistemicKind.OPINION.value)
    sims = tuple(i for i in items if i.epistemic_kind == EpistemicKind.SIMULATION.value)
    lessons = tuple(i for i in items if i.epistemic_kind == EpistemicKind.LESSON.value)
    fails = tuple(i for i in items if i.memory_type == MemoryType.FAILURE.value)
    inferences = tuple(i for i in items if i.epistemic_kind == EpistemicKind.INFERENCE.value)
    return CognitiveContext(
        facts=facts,
        inferences=inferences,
        hypotheses=hyps,
        predictions=preds,
        opinions=opinions,
        simulations=sims,
        experiments=(),
        outcomes=(),
        contradictions=edges,
        failures=fails,
        procedures=(),
        lessons=lessons,
        unknowns=() if items else ("empty",),
        excluded=(),
        contradiction_present=bool(edges),
        context_incomplete=not items,
        token_estimate=len(items),
    )


def _counts(mem: CognitiveMemoryStore) -> dict[str, int]:
    hyps = list(mem.find_by_type(MemoryType.HYPOTHESIS))
    lessons = [
        r
        for r in mem.find_by_type(MemoryType.SEMANTIC)
        if r.epistemic_kind == EpistemicKind.LESSON.value and r.statement.startswith("LESSON ")
    ]
    infs = [
        r
        for r in mem.find_by_type(MemoryType.SEMANTIC)
        if r.epistemic_kind == EpistemicKind.INFERENCE.value
        and r.statement.startswith("INFERENCE ")
    ]
    episodes = [
        r
        for r in mem.find_by_type(MemoryType.EPISODIC)
        if r.statement.startswith("episode ")
    ]
    return {
        "hypothesis": len(hyps),
        "lesson": len(lessons),
        "inference": len(infs),
        "episode": len(episodes),
    }


def _reason_row(task: CognitiveTask, *items: RetrievedItem, edges: tuple = ()):
    store = authorize_retrieved_items(*items)
    ctx = _ctx(*items, edges=edges)
    binds = bind_context(ctx, task, store=store)
    pre = MODE_FNS[task.reasoning_mode](task, binds)
    v, ep, trace, crit, _ = reason(
        task, ctx, retrieved_ids=[i.memory_id for i in items], store=store
    )
    permitted = reusable_writeback_permitted(v, binds)
    return {
        "bindings": binds,
        "candidate": pre.verdict,
        "critic": crit.action,
        "verdict": v,
        "epistemic": ep,
        "permitted": permitted,
        "trace": trace,
        "pre": pre,
        "crit": crit,
    }


def _orch(tmp_path: Path, specs: list[dict], task: CognitiveTask, *, contradict: bool = False):
    mem = CognitiveMemoryStore(tmp_path / "mem.sqlite")
    hyp = HypothesisStore(tmp_path / "hyp.jsonl")
    orch = CognitiveOrchestrator(memory=mem, hypotheses=hyp, ledger_path=tmp_path / "exp.jsonl")
    recs = []
    for i, spec in enumerate(specs):
        kw = dict(
            memory_type=MemoryType(spec.get("memory_type", MemoryType.EPISODIC.value)),
            epistemic_kind=EpistemicKind(spec.get("kind", EpistemicKind.OBSERVED_FACT.value)),
            statement=f"SYNTHETIC_TEST_DATA: {spec['statement']}",
            source_type=SourceType.SYSTEM,
            source_id=f"seed-{i}",
            source_location="tests/test_p5_second_forensic.py",
            producer="pytest",
            producer_version="p5",
            domain=spec.get("domain", task.domain),
            context="SYNTHETIC_TEST_DATA",
            observed_at=spec.get("observed_at", NOW - 40 + i),
            created_at=NOW - 30 + i,
            payload=spec.get("payload") or {"data_label": "SYNTHETIC_TEST_DATA"},
        )
        kind = EpistemicKind(spec.get("kind", EpistemicKind.OBSERVED_FACT.value))
        mtype = MemoryType(spec.get("memory_type", MemoryType.EPISODIC.value))
        if kind == EpistemicKind.OBSERVED_FACT and mtype != MemoryType.FAILURE:
            recs.append(
                persist_authorized(
                    mem,
                    kw["statement"],
                    source_id=kw["source_id"],
                    observed_at=kw["observed_at"],
                    domain=kw["domain"],
                    created_at=kw["created_at"],
                    payload=kw["payload"],
                )
            )
        else:
            recs.append(mem.remember(**kw))
        st = spec.get("status")
        if st and st != DecayState.ACTIVE.value:
            mem.revise(recs[-1].memory_id, status=st, correction_reason="forensic", now=NOW - 1)
    if contradict and len(recs) >= 2:
        mem.contradict(recs[0].memory_id, recs[1].memory_id, reason="seeded", now=NOW - 1)
    if recs:
        task.requested_evidence = [r.memory_id for r in recs]
    result = orch.run(task, now=NOW)
    return result, mem, _counts(mem)


def test_n_mixed_no_edge_write_back_true(tmp_path: Path) -> None:
    row = _reason_row(_task(), _item("s", SUPPORT), _item("c", CONTRA))
    assert row["verdict"] not in POSITIVE
    assert row["permitted"] is False
    assert row["candidate"] != CognitiveVerdict.WEAKLY_SUPPORTED.value or row["verdict"] not in POSITIVE
    result, _, c = _orch(
        tmp_path,
        [{"statement": SUPPORT}, {"statement": CONTRA}],
        _task(task_id="n", write_back=True, task_type=TaskType.INVESTIGATE.value),
    )
    assert result.verdict not in POSITIVE
    assert c["hypothesis"] == c["lesson"] == c["inference"] == 0
    assert c["episode"] == 1


def test_o_mixed_edge_write_back_true(tmp_path: Path) -> None:
    edges = ({"edge_id": "e", "from_id": "s", "to_id": "c", "relation": "CONTRADICTS"},)
    row = _reason_row(_task(), _item("s", SUPPORT), _item("c", CONTRA), edges=edges)
    assert row["verdict"] not in POSITIVE
    result, _, c = _orch(
        tmp_path,
        [{"statement": SUPPORT}, {"statement": CONTRA}],
        _task(task_id="o", write_back=True, task_type=TaskType.INVESTIGATE.value),
        contradict=True,
    )
    assert result.verdict not in POSITIVE
    assert c["hypothesis"] == c["lesson"] == c["inference"] == 0
    assert c["episode"] == 1


def test_p_supports_uncertain_write_back(tmp_path: Path) -> None:
    row = _reason_row(_task(), _item("s", SUPPORT), _item("u", UNCERTAIN))
    assert row["verdict"] not in POSITIVE
    assert row["permitted"] is False
    result, _, c = _orch(
        tmp_path,
        [{"statement": SUPPORT}, {"statement": UNCERTAIN}],
        _task(task_id="p", write_back=True, task_type=TaskType.INVESTIGATE.value),
    )
    assert result.verdict not in POSITIVE
    assert c["hypothesis"] == c["lesson"] == c["inference"] == 0


def test_q_support_plus_entity_mismatch(tmp_path: Path) -> None:
    q = "Do Service A retries after timeout reduce failures?"
    match = "Service A retries after timeout reduced failures."
    other = "Service B retries after timeout reduced failures."
    row = _reason_row(_task(q), _item("a", match), _item("b", other))
    by = {b.memory_id: b for b in row["bindings"]}
    assert by["a"].may_support_task() is True
    assert by["b"].may_support_task() is False
    assert by["b"].contradicts_task() is False
    assert row["verdict"] in POSITIVE
    result, _, c = _orch(
        tmp_path,
        [{"statement": match}, {"statement": other}],
        _task(q, task_id="q", write_back=True, task_type=TaskType.INVESTIGATE.value),
    )
    assert result.verdict in POSITIVE
    assert c["hypothesis"] >= 1 and c["lesson"] >= 1


def test_r_support_plus_entity_ambiguous() -> None:
    q = "Do Replica A1 retries after timeout reduce failures?"
    row = _reason_row(
        _task(q),
        _item("a", "Replica A1 retries after timeout reduced failures."),
        _item("g", "Retries after timeout reduced failures."),
    )
    by = {b.memory_id: b for b in row["bindings"]}
    assert by["a"].may_support_task() is True
    assert by["g"].may_support_task() is False
    assert row["verdict"] in POSITIVE
    assert "g" not in row["trace"].premises


def test_s_entity_scoped_vs_none(tmp_path: Path) -> None:
    st = "Service A retries after timeout reduced failures."
    row = _reason_row(_task(), _item("a", st))
    assert row["bindings"][0].may_support_task() is False
    assert row["verdict"] not in POSITIVE
    result, _, c = _orch(
        tmp_path,
        [{"statement": st}],
        _task(task_id="s", write_back=True, task_type=TaskType.INVESTIGATE.value),
    )
    assert result.verdict not in POSITIVE
    assert c["hypothesis"] == c["lesson"] == c["inference"] == 0


def test_t_stale_only_support(tmp_path: Path) -> None:
    row = _reason_row(_task(), _item("old", SUPPORT, status="STALE", observed_at=NOW - 10_000))
    assert row["bindings"][0].may(ROLE_FACTUAL_PREMISE) is False
    assert row["verdict"] not in POSITIVE
    assert row["permitted"] is False
    result, _, c = _orch(
        tmp_path,
        [{"statement": SUPPORT, "status": "STALE"}],
        _task(task_id="t", write_back=True, task_type=TaskType.INVESTIGATE.value),
    )
    assert result.verdict not in POSITIVE
    assert c["hypothesis"] == c["lesson"] == c["inference"] == 0
    assert c["episode"] == 1


def test_u_stale_plus_fresh_support() -> None:
    row = _reason_row(
        _task(),
        _item("old", SUPPORT, status="STALE", observed_at=NOW - 10_000),
        _item("new", SUPPORT),
    )
    by = {b.memory_id: b for b in row["bindings"]}
    assert by["old"].may(ROLE_FACTUAL_PREMISE) is False
    assert by["new"].may_support_task() is True
    assert row["verdict"] in POSITIVE
    assert "old" not in row["trace"].premises


def test_v_superseded_only_support(tmp_path: Path) -> None:
    row = _reason_row(_task(), _item("x", SUPPORT, status="SUPERSEDED"))
    assert row["verdict"] not in POSITIVE
    result, _, c = _orch(
        tmp_path,
        [{"statement": SUPPORT, "status": "SUPERSEDED"}],
        _task(task_id="v", write_back=True, task_type=TaskType.INVESTIGATE.value),
    )
    assert result.verdict not in POSITIVE
    assert c["hypothesis"] == 0


def test_w_assumption_only(tmp_path: Path) -> None:
    row = _reason_row(_task())
    assert row["verdict"] not in POSITIVE
    assert row["trace"].assumptions
    result, _, c = _orch(
        tmp_path, [], _task(task_id="w", write_back=True, task_type=TaskType.INVESTIGATE.value)
    )
    assert result.verdict not in POSITIVE
    assert c["hypothesis"] == c["lesson"] == c["inference"] == 0


def test_xyz_non_fact_kinds_not_reusable(tmp_path: Path) -> None:
    kinds = (
        ("X", EpistemicKind.PREDICTION.value),
        ("Y", EpistemicKind.OPINION.value),
        ("Z", EpistemicKind.SIMULATION.value),
    )
    for label, kind in kinds:
        item = _item(label, SUPPORT, kind=kind)
        row = _reason_row(_task(), item)
        assert row["verdict"] not in POSITIVE, label
        assert row["permitted"] is False, label
        result, _, c = _orch(
            tmp_path / label,
            [{"statement": SUPPORT, "kind": kind}],
            _task(task_id=label, write_back=True, task_type=TaskType.INVESTIGATE.value),
        )
        assert result.verdict not in POSITIVE, label
        assert c["hypothesis"] == c["lesson"] == c["inference"] == 0, label


def test_aa_unbound_citation_is_refused() -> None:
    task = _task()
    ctx = _ctx(_item("s", SUPPORT))
    binds = bind_context(ctx, task)
    cand = CandidateInference(
        verdict=CognitiveVerdict.WEAKLY_SUPPORTED.value,
        epistemic="PROBABLE",
        conclusion="forged unbound",
        conclusion_class="INFERENCE",
        supporting_ids=["UNBOUND-ID"],
        premises=["UNBOUND-ID"],
    )
    crit = critique_result(task=task, ctx=ctx, verdict=cand.verdict, assumptions=[], bindings=binds, candidate=cand)
    out = apply_constraint(cand, action=crit.action, findings=list(crit.findings))
    out = apply_episode_positive_policy(out, binds)
    assert crit.action == ACTION_REFUSE
    assert out.verdict not in POSITIVE
    assert reusable_writeback_permitted(out.verdict, binds) is False


def test_ab_irrelevant_citation_is_refused() -> None:
    task = _task()
    sky = _item("SKY", "SYNTHETIC_TEST_DATA: the sky is blue.")
    ctx = _ctx(sky)
    binds = bind_context(ctx, task)
    cand = CandidateInference(
        verdict=CognitiveVerdict.WEAKLY_SUPPORTED.value,
        epistemic="PROBABLE",
        conclusion="inventory",
        conclusion_class="INFERENCE",
        supporting_ids=["SKY"],
        premises=["SKY"],
    )
    crit = critique_result(task=task, ctx=ctx, verdict=cand.verdict, assumptions=[], bindings=binds, candidate=cand)
    out = apply_constraint(cand, action=crit.action, findings=list(crit.findings))
    assert crit.action in {ACTION_REFUSE, ACTION_REQUIRE_MORE}
    assert out.verdict not in POSITIVE


def test_ac_lexical_overlap_without_support() -> None:
    row = _reason_row(_task(), _item("lex", LEXICAL))
    assert row["bindings"][0].live_addresses_task() is True
    assert row["bindings"][0].may_support_task() is False
    assert row["verdict"] not in POSITIVE
    assert row["permitted"] is False


def test_ad_polarity_mutation_does_not_authorize() -> None:
    b = bind_context(_ctx(_item("c", CONTRA)), _task())[0]
    object.__setattr__(b, "support_polarity", "SUPPORTS")
    object.__setattr__(b, "support_class", "DIRECT_SUPPORT")
    object.__setattr__(b, "clause_force", "AFFIRMED")
    assert b.may_support_task() is False
    assert b.contradicts_task() is True


def test_ae_statement_change_is_authoritative_but_writeback_rebinds(tmp_path: Path) -> None:
    b = bind_context(_ctx(_item("c", CONTRA)), _task())[0]
    object.__setattr__(b, "statement", SUPPORT)
    assert b.may_support_task() is True
    result, _, c = _orch(
        tmp_path,
        [{"statement": CONTRA}],
        _task(task_id="ae", write_back=True, task_type=TaskType.INVESTIGATE.value),
    )
    assert result.verdict not in POSITIVE
    assert c["hypothesis"] == 0


def test_af_ag_did_can_not_identity() -> None:
    for q in ("Did retries after timeout reduce failures?", "Can retries after timeout reduce failures?"):
        row = _reason_row(_task(q), _item("s", SUPPORT))
        assert row["verdict"] in POSITIVE


def test_ah_cafeteria_metacognitive_not_positive() -> None:
    row = _reason_row(
        _task(reasoning_mode=ReasoningMode.METACOGNITIVE.value), _item("lex", LEXICAL)
    )
    assert row["verdict"] not in POSITIVE
    assert row["permitted"] is False


def test_ai_non_decision_bearing_plus_supporter_does_not_cite_cousin() -> None:
    row = _reason_row(
        _task(reasoning_mode=ReasoningMode.METACOGNITIVE.value),
        _item("s", SUPPORT),
        _item("lex", LEXICAL),
    )
    rec = row["trace"].inference_records[0]
    cited = set(rec["supporting_evidence_ids"]) | set(rec["premises"])
    assert "lex" not in cited
    assert "s" in cited
    assert row["verdict"] in POSITIVE


def test_aj_contradiction_added_after_initial_binding() -> None:
    first = _reason_row(_task(), _item("s", SUPPORT))
    assert first["verdict"] in POSITIVE
    second = _reason_row(_task(), _item("s", SUPPORT), _item("c", CONTRA))
    assert second["verdict"] not in POSITIVE
    assert second["permitted"] is False


def test_ak_duplicate_supporter_plus_contradiction() -> None:
    row = _reason_row(
        _task(), _item("s1", SUPPORT), _item("s2", SUPPORT), _item("c", CONTRA)
    )
    assert row["verdict"] not in POSITIVE
    assert row["permitted"] is False


def test_al_three_way_conflict() -> None:
    row = _reason_row(
        _task(), _item("s", SUPPORT), _item("c", CONTRA), _item("u", UNCERTAIN)
    )
    assert row["verdict"] not in POSITIVE
    assert row["permitted"] is False


def test_am_contradiction_different_entity_does_not_veto_match() -> None:
    q = "Do Service A retries after timeout reduce failures?"
    row = _reason_row(
        _task(q),
        _item("a", "Service A retries after timeout reduced failures."),
        _item("b", "Service B retries after timeout increased failures."),
    )
    by = {b.memory_id: b for b in row["bindings"]}
    assert by["b"].contradicts_task() is False
    assert row["verdict"] in POSITIVE


def test_an_contradiction_same_entity() -> None:
    q = "Do Service A retries after timeout reduce failures?"
    row = _reason_row(
        _task(q),
        _item("a1", "Service A retries after timeout reduced failures."),
        _item("a2", "Service A retries after timeout increased failures."),
    )
    assert row["verdict"] not in POSITIVE


def test_ao_task_domain_mismatch() -> None:
    row = _reason_row(
        _task(domain="software"),
        _item("f", SUPPORT, domain="finance"),
    )
    assert row["bindings"][0].may(ROLE_FACTUAL_PREMISE) is False
    assert row["verdict"] not in POSITIVE


def test_ap_lesson_applicability_mismatch(tmp_path: Path) -> None:
    mem = CognitiveMemoryStore(tmp_path / "m.sqlite")
    fact = persist_authorized(
        mem,
        f"SYNTHETIC_TEST_DATA: {HELP_FACT}",
        source_id="f",
        observed_at=NOW - 40,
        domain="software",
        created_at=NOW - 30,
    )
    lesson = mem.remember(
        memory_type=MemoryType.SEMANTIC,
        epistemic_kind=EpistemicKind.LESSON,
        statement="SYNTHETIC_TEST_DATA LESSON: logging format is not a timeout policy",
        source_type=SourceType.SYSTEM,
        source_id="l",
        source_location="forensic",
        producer="pytest",
        producer_version="p5",
        domain="software",
        context="SYNTHETIC_TEST_DATA",
        created_at=NOW - 20,
        payload={"data_label": "SYNTHETIC_TEST_DATA", "applicability": "finance"},
    )
    task = _task(HELP_Q, reasoning_mode=ReasoningMode.DEDUCTIVE.value)
    ctx = _ctx(
        _item(fact.memory_id, fact.statement),
        _item(lesson.memory_id, lesson.statement, kind=EpistemicKind.LESSON.value),
    )
    binds = bind_context(ctx, task, store=mem)
    lesson_b = next(b for b in binds if b.memory_id == lesson.memory_id)
    assert lesson_b.live_applicability() == "NOT_APPLICABLE"
    v, _, trace, _, _ = reason(task, ctx, retrieved_ids=[fact.memory_id, lesson.memory_id], store=mem)
    assert v in POSITIVE
    assert trace.inference_records[0].get("lesson_applied") is False


def test_aq_failure_applicability_mismatch(tmp_path: Path) -> None:
    fail = _item(
        "fail",
        "SYNTHETIC_TEST_DATA: timeout retry failed",
        memory_type=MemoryType.FAILURE.value,
        kind=EpistemicKind.OBSERVED_FACT.value,
    )
    row = _reason_row(
        _task(HELP_Q, constraints={"component": "http_client", "failure_type": "timeout_retry"}),
        _item("s", HELP_FACT),
        fail,
    )
    fail_b = next(b for b in row["bindings"] if b.memory_id == "fail")
    assert fail_b.live_applicability() in {"NOT_APPLICABLE", "UNKNOWN"}
    assert row["trace"].inference_records[0].get("failure_applied") is not True or fail_b.live_applicability() == "APPLICABLE"


def test_seven_modes_mixed_never_weakly() -> None:
    items = (_item("s", SUPPORT), _item("c", CONTRA))
    edges = ({"edge_id": "e", "from_id": "s", "to_id": "c", "relation": "CONTRADICTS"},)
    for mode in MODES:
        no_edge = _reason_row(_task(reasoning_mode=mode), *items)
        with_edge = _reason_row(_task(reasoning_mode=mode), *items, edges=edges)
        assert no_edge["verdict"] not in POSITIVE, mode
        assert with_edge["verdict"] not in POSITIVE, mode
        assert no_edge["permitted"] is False, mode
        assert with_edge["permitted"] is False, mode
        assert no_edge["candidate"] != CognitiveVerdict.WEAKLY_SUPPORTED.value or no_edge["verdict"] not in POSITIVE


def test_write_back_false_mints_nothing(tmp_path: Path) -> None:
    result, _, c = _orch(
        tmp_path,
        [{"statement": SUPPORT}],
        _task(HELP_Q, task_id="nwb", write_back=False, task_type=TaskType.INVESTIGATE.value),
    )
    assert c["hypothesis"] == c["lesson"] == c["inference"] == c["episode"] == 0


def test_mutation_role_escalation_cannot_make_opinion_factual() -> None:
    b = bind_context(
        _ctx(_item("op", SUPPORT, kind=EpistemicKind.OPINION.value)), _task()
    )[0]
    object.__setattr__(b, "allowed_reasoning_roles", (ROLE_FACTUAL_PREMISE,))
    object.__setattr__(b, "forbidden_reasoning_roles", ())
    object.__setattr__(b, "typed_class", "OBSERVED_FACT")
    object.__setattr__(b, "temporal_state", "CURRENT")
    assert b.may(ROLE_FACTUAL_PREMISE) is False
    assert reusable_writeback_permitted("WEAKLY_SUPPORTED", [b]) is False


def test_mutation_temporal_field_cannot_freshen_stale() -> None:
    b = bind_context(_ctx(_item("old", SUPPORT, status="STALE")), _task())[0]
    object.__setattr__(b, "temporal_state", "CURRENT")
    object.__setattr__(b, "allowed_reasoning_roles", (ROLE_FACTUAL_PREMISE,))
    assert b.live_temporal_state() == "STALE"
    assert b.may(ROLE_FACTUAL_PREMISE) is False


def test_mutation_clause_force_cannot_hide_uncertainty() -> None:
    binds = bind_context(_ctx(_item("s", SUPPORT), _item("u", UNCERTAIN)), _task())
    u = next(b for b in binds if b.memory_id == "u")
    object.__setattr__(u, "clause_force", "AFFIRMED")
    object.__setattr__(u, "addresses_task_flag", False)
    assert u.is_task_relevant_uncertain() is True
    assert reusable_writeback_permitted("WEAKLY_SUPPORTED", binds) is False


def test_frozen_assignment_raises() -> None:
    b = bind_context(_ctx(_item("s", SUPPORT)), _task())[0]
    with pytest.raises(FrozenInstanceError):
        b.support_polarity = "CONTRADICTS"  # type: ignore[misc]


def test_forged_evidence_binding_opinion_cannot_support() -> None:
    forged = EvidenceBinding(
        evidence_id="EVD-FAKE",
        memory_id="fake",
        typed_class="OBSERVED_FACT",
        relevance="RETRIEVED",
        applicability="APPLICABLE",
        temporal_state="CURRENT",
        provenance={},
        support_strength="DIRECT",
        contradiction_state="UNCONTESTED",
        allowed_reasoning_roles=(ROLE_FACTUAL_PREMISE,),
        forbidden_reasoning_roles=(),
        statement=SUPPORT,
        domain="software",
        status="ACTIVE",
        epistemic_kind=EpistemicKind.OPINION.value,
        memory_type=MemoryType.EPISODIC.value,
        task_question=Q,
        task_objective="timeout retries",
        task_domain="software",
        observed_at=NOW - 20,
    )
    assert forged.live_typed_class() == EpistemicKind.OPINION.value
    assert forged.may(ROLE_FACTUAL_PREMISE) is False
    assert reusable_writeback_permitted("WEAKLY_SUPPORTED", [forged]) is False


def test_critic_contradiction_constrains_candidate() -> None:
    task = _task(reasoning_mode=ReasoningMode.METACOGNITIVE.value)
    items = (_item("s", SUPPORT), _item("c", CONTRA))
    edges = ({"edge_id": "e", "from_id": "s", "to_id": "c", "relation": "CONTRADICTS"},)
    store = authorize_retrieved_items(*items)
    ctx = _ctx(*items, edges=edges)
    binds = bind_context(ctx, task, store=store)
    pre = MODE_FNS[task.reasoning_mode](task, binds)
    v, _, _, crit, _ = reason(task, ctx, retrieved_ids=["s", "c"], store=store)
    assert any("CONTRADICTION" in f for f in crit.findings)
    assert v not in POSITIVE
    assert v != CognitiveVerdict.WEAKLY_SUPPORTED.value


def test_critic_missing_premise_constrains() -> None:
    row = _reason_row(_task())
    assert row["critic"] == ACTION_REQUIRE_MORE
    assert row["verdict"] == CognitiveVerdict.INSUFFICIENT_EVIDENCE.value


def test_critic_constraint_function_is_load_bearing() -> None:
    from architecture.cognitive.loop.inference import (
        FINDING_OVERCONFIDENCE,
        FINDING_SCOPE_MISMATCH,
        FINDING_TEMPORAL_VIOLATION,
        FINDING_TYPE_VIOLATION,
        FINDING_UNSUPPORTED_ASSUMPTION,
    )

    weak = CandidateInference(
        verdict=CognitiveVerdict.WEAKLY_SUPPORTED.value,
        epistemic="PROBABLE",
        conclusion="x",
        conclusion_class="INFERENCE",
        supporting_ids=["s"],
        premises=["s"],
    )
    supported = CandidateInference(
        verdict=CognitiveVerdict.SUPPORTED.value,
        epistemic="KNOWN",
        conclusion="x",
        conclusion_class="INFERENCE",
        supporting_ids=["s"],
        premises=["s"],
    )
    out = apply_constraint(supported, action=ACTION_DOWNGRADE, findings=[f"{FINDING_OVERCONFIDENCE}:x"])
    assert out.verdict == CognitiveVerdict.WEAKLY_SUPPORTED.value
    out = apply_constraint(weak, action=ACTION_DOWNGRADE, findings=[f"{FINDING_TYPE_VIOLATION}:x"])
    assert out.verdict == CognitiveVerdict.INSUFFICIENT_EVIDENCE.value
    out = apply_constraint(weak, action=ACTION_DOWNGRADE, findings=[f"{FINDING_TEMPORAL_VIOLATION}:stale"])
    assert out.verdict not in POSITIVE
    out = apply_constraint(weak, action=ACTION_DOWNGRADE, findings=[f"{FINDING_SCOPE_MISMATCH}:x"])
    assert out.verdict not in POSITIVE
    out = apply_constraint(supported, action=ACTION_DOWNGRADE, findings=[f"{FINDING_UNSUPPORTED_ASSUMPTION}:ASM"])
    assert out.verdict == CognitiveVerdict.WEAKLY_SUPPORTED.value
    out = apply_constraint(weak, action=ACTION_CONTEST, findings=["CONTRADICTION_VIOLATION:present"])
    assert out.verdict not in POSITIVE


def test_critic_type_violation_on_opinion_as_fact() -> None:
    row = _reason_row(
        _task(reasoning_mode=ReasoningMode.ADVERSARIAL.value),
        _item("op", SUPPORT, kind=EpistemicKind.OPINION.value),
    )
    assert row["verdict"] not in POSITIVE


def test_episode_policy_order_in_reason_source() -> None:
    src = inspect.getsource(reason)
    i_constraint = src.find("apply_constraint(")
    i_policy = src.find("apply_episode_positive_policy(")
    i_write = src.find("reusable_writeback_permitted(")
    assert 0 <= i_constraint < i_policy < i_write


def test_two_hop_unresolved_episode_cannot_become_fact(tmp_path: Path) -> None:
    result, mem, c = _orch(
        tmp_path,
        [{"statement": SUPPORT}, {"statement": CONTRA}],
        _task(task_id="hop1", write_back=True, task_type=TaskType.INVESTIGATE.value),
    )
    assert c["hypothesis"] == c["lesson"] == c["inference"] == 0
    assert c["episode"] == 1
    episode = next(r for r in mem.find_by_type(MemoryType.EPISODIC) if r.statement.startswith("episode "))
    assert episode.epistemic_kind == EpistemicKind.INFERENCE.value
    hop = Path(tmp_path / "hop2")
    mem2 = CognitiveMemoryStore(hop / "mem.sqlite")
    hyp2 = HypothesisStore(hop / "hyp.jsonl")
    mem2.remember(
        memory_type=MemoryType.EPISODIC,
        epistemic_kind=EpistemicKind(episode.epistemic_kind),
        statement=episode.statement,
        source_type=SourceType.SYSTEM,
        source_id=episode.source_id,
        source_location="two-hop",
        producer="pytest",
        producer_version="p5",
        domain="software",
        context="SYNTHETIC_TEST_DATA",
        observed_at=NOW,
        created_at=NOW,
        payload=dict(episode.payload or {}),
    )
    orch2 = CognitiveOrchestrator(memory=mem2, hypotheses=hyp2, ledger_path=hop / "exp.jsonl")
    t2 = _task(task_id="hop2", write_back=True, task_type=TaskType.ANALYZE.value)
    t2.requested_evidence = [r.memory_id for r in mem2.find_by_type(MemoryType.EPISODIC)]
    r2 = orch2.run(t2, now=NOW + 5)
    assert r2.verdict not in POSITIVE
    retrieved_facts = [
        i for i in r2.retrieved if i.epistemic_kind == EpistemicKind.OBSERVED_FACT.value
    ]
    assert retrieved_facts == []
    binds = bind_context(r2.context, t2)
    assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in binds)
    c2 = _counts(mem2)
    assert c2["hypothesis"] == c2["lesson"] == c2["inference"] == 0


def test_three_hop_derived_artifact_cannot_escalate_authority(tmp_path: Path) -> None:
    """HOP1 unresolved → EPISODIC INFERENCE.
    HOP2 retrieve episode → reusable hyp/lesson/inference not permitted.
    HOP3 even a forcibly stored HYPOTHESIS/LESSON/INFERENCE cannot become
    OBSERVED_FACT, FACTUAL_PREMISE, or DIRECT support on a new task.
    """
    result, mem, c = _orch(
        tmp_path,
        [{"statement": SUPPORT}, {"statement": CONTRA}],
        _task(task_id="hop1", write_back=True, task_type=TaskType.INVESTIGATE.value),
    )
    assert result.verdict not in POSITIVE
    assert c["hypothesis"] == c["lesson"] == c["inference"] == 0
    assert c["episode"] == 1
    episode = next(r for r in mem.find_by_type(MemoryType.EPISODIC) if r.statement.startswith("episode "))
    assert episode.epistemic_kind == EpistemicKind.INFERENCE.value

    hop2 = Path(tmp_path / "hop2")
    mem2 = CognitiveMemoryStore(hop2 / "mem.sqlite")
    hyp2 = HypothesisStore(hop2 / "hyp.jsonl")
    mem2.remember(
        memory_type=MemoryType.EPISODIC,
        epistemic_kind=EpistemicKind.INFERENCE,
        statement=episode.statement,
        source_type=SourceType.SYSTEM,
        source_id=episode.source_id,
        source_location="three-hop-2",
        producer="pytest",
        producer_version="p5",
        domain="software",
        context="SYNTHETIC_TEST_DATA",
        observed_at=NOW,
        created_at=NOW,
        payload=dict(episode.payload or {}),
    )
    orch2 = CognitiveOrchestrator(memory=mem2, hypotheses=hyp2, ledger_path=hop2 / "exp.jsonl")
    t2 = _task(task_id="hop2", write_back=True, task_type=TaskType.ANALYZE.value)
    t2.requested_evidence = [r.memory_id for r in mem2.find_by_type(MemoryType.EPISODIC)]
    r2 = orch2.run(t2, now=NOW + 5)
    assert r2.verdict not in POSITIVE
    assert _counts(mem2)["hypothesis"] == _counts(mem2)["lesson"] == _counts(mem2)["inference"] == 0
    binds2 = bind_context(r2.context, t2)
    assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in binds2)
    assert all(b.live_typed_class() != "OBSERVED_FACT" for b in binds2)
    assert all(b.support_strength != SUPPORT_DIRECT for b in binds2)

    # Simulated substrate write of derived artifacts (ungoverned remember).
    # This is the hop-3 contamination attempt, not a production write-back.
    derived = (
        (MemoryType.HYPOTHESIS, EpistemicKind.HYPOTHESIS, f"HYPOTHESIS from {episode.statement}"),
        (MemoryType.SEMANTIC, EpistemicKind.LESSON, f"LESSON from {episode.statement}: {SUPPORT}"),
        (MemoryType.SEMANTIC, EpistemicKind.INFERENCE, f"INFERENCE from {episode.statement}: {SUPPORT}"),
        (MemoryType.SEMANTIC, EpistemicKind.PREDICTION, f"PREDICTION from {episode.statement}"),
        (MemoryType.SEMANTIC, EpistemicKind.OPINION, f"OPINION from {episode.statement}"),
        (MemoryType.SEMANTIC, EpistemicKind.SIMULATION, f"SIMULATION from {episode.statement}"),
    )
    hop3 = Path(tmp_path / "hop3")
    mem3 = CognitiveMemoryStore(hop3 / "mem.sqlite")
    hyp3 = HypothesisStore(hop3 / "hyp.jsonl")
    ids = []
    for i, (mtype, kind, statement) in enumerate(derived):
        rec = mem3.remember(
            memory_type=mtype,
            epistemic_kind=kind,
            statement=statement,
            source_type=SourceType.SYSTEM,
            source_id=f"derived-{i}",
            source_location="three-hop-3",
            producer="pytest",
            producer_version="p5",
            domain="software",
            context="SYNTHETIC_TEST_DATA",
            observed_at=NOW + 10,
            created_at=NOW + 10,
            payload={"data_label": "SYNTHETIC_TEST_DATA", "derived_from_episode": episode.memory_id},
        )
        ids.append(rec.memory_id)
    orch3 = CognitiveOrchestrator(memory=mem3, hypotheses=hyp3, ledger_path=hop3 / "exp.jsonl")
    t3 = _task(task_id="hop3", write_back=True, task_type=TaskType.ANALYZE.value)
    t3.requested_evidence = ids
    r3 = orch3.run(t3, now=NOW + 20)
    assert r3.verdict not in POSITIVE
    assert r3.verdict != CognitiveVerdict.WEAKLY_SUPPORTED.value
    binds3 = bind_context(r3.context, t3)
    assert binds3, "derived artifacts must be bound so roles can be audited"
    for b in binds3:
        assert b.live_typed_class() != "OBSERVED_FACT"
        assert not b.may(ROLE_FACTUAL_PREMISE)
        assert b.support_strength != SUPPORT_DIRECT
        assert b.epistemic_kind not in {
            EpistemicKind.OBSERVED_FACT.value,
            EpistemicKind.DERIVED_FACT.value,
        }
    c3 = _counts(mem3)
    # Forced substrate rows exist; governed hop-3 write-back must not add more.
    assert c3["hypothesis"] == 1
    assert c3["lesson"] == 1
    assert c3["inference"] == 1
    assert c3["episode"] == 1


def test_production_reason_applies_episode_policy() -> None:
    src = Path("architecture/cognitive/loop/reason.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        if isinstance(node, ast.Attribute):
            names.add(node.attr)
    assert "apply_episode_positive_policy" in names
    assert "reusable_writeback_permitted" in names
