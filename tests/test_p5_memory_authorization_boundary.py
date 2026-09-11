"""P5 memory authorization boundary — production-path proof.

Not a feature. Not entailment. Isolated SYNTHETIC_TEST_DATA.
Calls only public production APIs: remember / propose / accept /
MemoryRetriever.retrieve / CognitiveOrchestrator.run.

Records ACCEPTED | REJECTED | STORED-BUT-NONREUSABLE.
Does not treat storage as authorization.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from architecture.cognitive.hypothesis import HypothesisStore  # noqa: E402
from architecture.cognitive.loop.binding import (  # noqa: E402
    ROLE_FACTUAL_PREMISE,
    SUPPORT_DIRECT,
    bind_context,
)
from architecture.cognitive.loop.contracts import (  # noqa: E402
    CognitiveTask,
    CognitiveVerdict,
    ReasoningMode,
    TaskType,
)
from architecture.cognitive.loop.episode import reusable_writeback_permitted  # noqa: E402
from architecture.cognitive.loop.orchestrator import CognitiveOrchestrator  # noqa: E402
from architecture.cognitive.loop.retrieval import MemoryRetriever  # noqa: E402
from architecture.cognitive.loop.support import SUPPORT_DIRECT as TASK_DIRECT_SUPPORT  # noqa: E402
from architecture.cognitive.memory.consolidation import (  # noqa: E402
    ConsolidationCandidate,
    ConsolidationGate,
)
from architecture.cognitive.memory.record import EpistemicViolation  # noqa: E402
from architecture.cognitive.memory.store import CognitiveMemoryStore  # noqa: E402
from architecture.cognitive.memory.types import (  # noqa: E402
    DecayState,
    EpistemicKind,
    MemoryType,
    SourceType,
    UNKNOWN,
)

NOW = 1_800_000_000.0
POSITIVE = {
    CognitiveVerdict.SUPPORTED.value,
    CognitiveVerdict.WEAKLY_SUPPORTED.value,
}
Q = "Do retries after timeout reduce failures?"
SUPPORT = "Retries after timeout reduced failures."
CONTRA = "Retries after timeout increased failures."
MISMATCH = "Retries after timeout reduced cafeteria seating failures."
UNCERTAIN = "It is unknown whether retries after timeout reduce failures."


def _task(**kwargs) -> CognitiveTask:
    base = dict(
        task_id="auth-boundary",
        task_type=TaskType.ANALYZE.value,
        objective="timeout retries",
        question=Q,
        domain="software",
        requester="boundary-audit",
        created_at=NOW,
        data_label="SYNTHETIC_TEST_DATA",
        reasoning_mode=ReasoningMode.DEDUCTIVE.value,
        write_back=True,
    )
    base.update(kwargs)
    return CognitiveTask(**base)


def _store(tmp_path: Path) -> tuple[CognitiveMemoryStore, HypothesisStore, Path]:
    mem = CognitiveMemoryStore(tmp_path / "mem.sqlite")
    hyp = HypothesisStore(tmp_path / "hyp.jsonl")
    ledger = tmp_path / "exp.jsonl"
    return mem, hyp, ledger


def _remember(mem: CognitiveMemoryStore, **kwargs):
    kw = dict(
        memory_type=MemoryType.EPISODIC,
        epistemic_kind=EpistemicKind.OBSERVED_FACT,
        statement=SUPPORT,
        source_type=SourceType.SYSTEM,
        source_id="attacker",
        source_location="direct-remember",
        producer="unprivileged-caller",
        producer_version="none",
        domain="software",
        context=UNKNOWN,
        observed_at=NOW - 20,
        created_at=NOW - 10,
        payload={"data_label": "SYNTHETIC_TEST_DATA"},
    )
    kw.update(kwargs)
    return mem.remember(**kw)


def _run(tmp_path: Path, mem: CognitiveMemoryStore, hyp: HypothesisStore, ledger: Path, task: CognitiveTask):
    orch = CognitiveOrchestrator(memory=mem, hypotheses=hyp, ledger_path=ledger)
    items = MemoryRetriever().retrieve(mem, task, now=NOW)
    result = orch.run(task, now=NOW + 1)
    binds = bind_context(result.context, task, store=mem, now=NOW + 1)
    return result, items, binds


def _counts(mem: CognitiveMemoryStore) -> dict[str, int]:
    return {
        "hypothesis": len(list(mem.find_by_type(MemoryType.HYPOTHESIS))),
        "lesson": len(
            [
                r
                for r in mem.find_by_type(MemoryType.SEMANTIC)
                if r.epistemic_kind == EpistemicKind.LESSON.value
            ]
        ),
        "inference": len(
            [
                r
                for r in mem.find_by_type(MemoryType.SEMANTIC)
                if r.epistemic_kind == EpistemicKind.INFERENCE.value
                and r.statement.startswith("INFERENCE ")
            ]
        ),
        "episode": len(
            [
                r
                for r in mem.find_by_type(MemoryType.EPISODIC)
                if r.statement.startswith("episode ")
            ]
        ),
    }


def test_remember_rejects_factual_premise_kind(tmp_path: Path) -> None:
    mem, _, _ = _store(tmp_path)
    with pytest.raises(ValueError):
        _remember(mem, epistemic_kind="FACTUAL_PREMISE")


def test_remember_accepts_arbitrary_observed_fact(tmp_path: Path) -> None:
    mem, _, _ = _store(tmp_path)
    rec = _remember(mem, source_id=UNKNOWN, producer=UNKNOWN, producer_version=UNKNOWN)
    assert rec.epistemic_kind == EpistemicKind.OBSERVED_FACT.value
    assert rec.status == DecayState.ACTIVE.value


def test_remember_rejects_ai_model_observed_fact(tmp_path: Path) -> None:
    mem, _, _ = _store(tmp_path)
    with pytest.raises(EpistemicViolation):
        _remember(mem, source_type=SourceType.AI_MODEL)


def test_remember_rejects_out_of_range_confidence(tmp_path: Path) -> None:
    mem, _, _ = _store(tmp_path)
    with pytest.raises(ValueError):
        _remember(mem, confidence=1.5)


def test_remember_accepts_forged_confidence_in_range(tmp_path: Path) -> None:
    mem, _, _ = _store(tmp_path)
    rec = _remember(mem, confidence=1.0)
    assert rec.confidence == 1.0
    assert rec.epistemic_kind == EpistemicKind.OBSERVED_FACT.value


def test_remember_non_fact_kinds_store(tmp_path: Path) -> None:
    mem, _, _ = _store(tmp_path)
    kinds = (
        EpistemicKind.HYPOTHESIS,
        EpistemicKind.LESSON,
        EpistemicKind.INFERENCE,
        EpistemicKind.PREDICTION,
        EpistemicKind.OPINION,
        EpistemicKind.SIMULATION,
    )
    for kind in kinds:
        rec = _remember(
            mem,
            memory_type=MemoryType.SEMANTIC
            if kind != EpistemicKind.HYPOTHESIS
            else MemoryType.HYPOTHESIS,
            epistemic_kind=kind,
            statement=f"{kind.value}: {SUPPORT}",
            source_id=f"k-{kind.value}",
        )
        assert rec.epistemic_kind == kind.value


def test_consumption_remembered_observed_fact_is_factual_premise(tmp_path: Path) -> None:
    """remember() may persist OBSERVED_FACT, but without a grant it is data only."""
    mem, hyp, ledger = _store(tmp_path)
    rec = _remember(mem)
    task = _task(requested_evidence=[rec.memory_id])
    result, items, binds = _run(tmp_path, mem, hyp, ledger, task)
    assert items, "production retriever must see requested OBSERVED_FACT"
    assert all(i.epistemic_kind == EpistemicKind.OBSERVED_FACT.value for i in items)
    assert any(i.evidence_class == "DIRECT_OBSERVATION" for i in items)
    assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in binds)
    assert all(b.support_strength != SUPPORT_DIRECT for b in binds)
    assert result.verdict not in POSITIVE
    assert reusable_writeback_permitted(result.verdict, binds) is False
    c = _counts(mem)
    assert c["hypothesis"] == 0
    assert c["lesson"] == 0
    assert c["inference"] == 0


def test_consumption_remembered_hypothesis_cannot_factify(tmp_path: Path) -> None:
    mem, hyp, ledger = _store(tmp_path)
    rec = _remember(
        mem,
        memory_type=MemoryType.HYPOTHESIS,
        epistemic_kind=EpistemicKind.HYPOTHESIS,
        statement=f"HYPOTHESIS: {SUPPORT}",
    )
    task = _task(requested_evidence=[rec.memory_id], write_back=True)
    result, _, binds = _run(tmp_path, mem, hyp, ledger, task)
    assert binds
    assert all(b.live_typed_class() == "HYPOTHESIS" for b in binds)
    assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in binds)
    assert all(b.support_strength != SUPPORT_DIRECT for b in binds)
    assert result.verdict not in POSITIVE
    c = _counts(mem)
    assert c["hypothesis"] == 1
    assert c["lesson"] == 0
    assert c["inference"] == 0


def test_consumption_remembered_lesson_inference_prediction_opinion_simulation(
    tmp_path: Path,
) -> None:
    mem, hyp, ledger = _store(tmp_path)
    specs = (
        (MemoryType.SEMANTIC, EpistemicKind.LESSON, f"LESSON: {SUPPORT}"),
        (MemoryType.SEMANTIC, EpistemicKind.INFERENCE, f"INFERENCE: {SUPPORT}"),
        (MemoryType.SEMANTIC, EpistemicKind.PREDICTION, f"PREDICTION: {SUPPORT}"),
        (MemoryType.SEMANTIC, EpistemicKind.OPINION, f"OPINION: {SUPPORT}"),
        (MemoryType.SEMANTIC, EpistemicKind.SIMULATION, f"SIMULATION: {SUPPORT}"),
        (MemoryType.EPISODIC, EpistemicKind.INFERENCE, f"episode unresolved {SUPPORT}"),
    )
    ids = []
    for mtype, kind, statement in specs:
        rec = _remember(
            mem,
            memory_type=mtype,
            epistemic_kind=kind,
            statement=statement,
            source_id=f"s-{kind.value}-{mtype.value}",
        )
        ids.append(rec.memory_id)
    task = _task(requested_evidence=ids)
    result, _, binds = _run(tmp_path, mem, hyp, ledger, task)
    assert binds
    for b in binds:
        assert b.live_typed_class() != "OBSERVED_FACT"
        assert not b.may(ROLE_FACTUAL_PREMISE)
        assert b.support_strength != SUPPORT_DIRECT
    assert result.verdict not in POSITIVE
    assert result.verdict != CognitiveVerdict.WEAKLY_SUPPORTED.value


def test_consumption_assumption_uncertain_stale_mismatch_contradiction(tmp_path: Path) -> None:
    mem, hyp, ledger = _store(tmp_path)

    uncertain = _remember(mem, statement=UNCERTAIN, source_id="unc")
    r1, _, b1 = _run(tmp_path, mem, hyp, ledger, _task(task_id="unc", requested_evidence=[uncertain.memory_id], write_back=True))
    assert r1.verdict not in POSITIVE
    assert all(not b.may(ROLE_FACTUAL_PREMISE) or not b.may_support_task() for b in b1) or r1.verdict not in POSITIVE

    stale = _remember(mem, statement=SUPPORT, source_id="stale")
    mem.revise(stale.memory_id, status=DecayState.STALE, correction_reason="audit", now=NOW)
    r2, _, b2 = _run(
        tmp_path,
        mem,
        hyp,
        ledger,
        _task(task_id="stale", requested_evidence=[stale.memory_id], write_back=True),
    )
    assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in b2)
    assert r2.verdict not in POSITIVE

    mismatch = _remember(mem, statement=MISMATCH, source_id="mm")
    r3, _, b3 = _run(
        tmp_path,
        mem,
        hyp,
        ledger,
        _task(task_id="mm", requested_evidence=[mismatch.memory_id], write_back=True),
    )
    assert r3.verdict not in POSITIVE
    assert all(not (b.may(ROLE_FACTUAL_PREMISE) and b.may_support_task()) for b in b3)

    a = _remember(mem, statement=SUPPORT, source_id="a")
    b = _remember(mem, statement=CONTRA, source_id="b")
    r4, _, _ = _run(
        tmp_path,
        mem,
        hyp,
        ledger,
        _task(task_id="mix", requested_evidence=[a.memory_id, b.memory_id], write_back=True),
    )
    assert r4.verdict not in POSITIVE


def test_forged_temporal_valid_until_does_not_mark_stale_on_insert(tmp_path: Path) -> None:
    """remember() always stores status=ACTIVE. Past valid_until is not decay."""
    mem, hyp, ledger = _store(tmp_path)
    rec = _remember(mem, valid_until=NOW - 10_000)
    assert rec.status == DecayState.ACTIVE.value
    task = _task(requested_evidence=[rec.memory_id])
    result, _, binds = _run(tmp_path, mem, hyp, ledger, task)
    assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in binds)
    assert result.verdict not in POSITIVE


def test_missing_observed_at_is_not_factual_premise(tmp_path: Path) -> None:
    mem, hyp, ledger = _store(tmp_path)
    rec = _remember(mem, observed_at=None)
    task = _task(requested_evidence=[rec.memory_id], write_back=True)
    result, _, binds = _run(tmp_path, mem, hyp, ledger, task)
    assert all(b.live_temporal_state() == "UNKNOWN_AGE" for b in binds)
    assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in binds)
    assert result.verdict not in POSITIVE


def test_propose_does_not_enter_memory_retriever(tmp_path: Path) -> None:
    mem, hyp, ledger = _store(tmp_path)
    rec = hyp.propose(SUPPORT, domain="software", provenance={"forged": True}, now=NOW)
    assert rec.state == "PROPOSED"
    assert rec.statement == SUPPORT
    task = _task()
    items = MemoryRetriever().retrieve(mem, task, now=NOW)
    assert items == []
    orch = CognitiveOrchestrator(memory=mem, hypotheses=hyp, ledger_path=ledger)
    result = orch.run(task, now=NOW + 1)
    assert result.verdict not in POSITIVE
    assert _counts(mem)["hypothesis"] == 0
    assert _counts(mem)["lesson"] == 0


def test_propose_empty_statement_rejected(tmp_path: Path) -> None:
    _, hyp, _ = _store(tmp_path)
    with pytest.raises(ValueError):
        hyp.propose("   ")


def test_consolidation_cannot_write_observed_or_derived_fact(tmp_path: Path) -> None:
    mem, _, _ = _store(tmp_path)
    ep = _remember(mem, statement=SUPPORT, source_id="ep")
    gate = ConsolidationGate()
    cand = gate.propose_from_episodes(mem, [ep.memory_id], statement=SUPPORT)
    assert cand.requires_human is True
    with pytest.raises(EpistemicViolation):
        gate.accept(
            mem,
            cand,
            actor="auditor",
            epistemic_kind=EpistemicKind.OBSERVED_FACT,
            producer="attacker",
        )
    with pytest.raises(EpistemicViolation):
        gate.accept(
            mem,
            cand,
            actor="auditor",
            epistemic_kind=EpistemicKind.DERIVED_FACT,
            producer="attacker",
        )


def test_consolidation_accept_empty_actor_rejected(tmp_path: Path) -> None:
    mem, _, _ = _store(tmp_path)
    ep = _remember(mem, source_id="ep2")
    gate = ConsolidationGate()
    cand = gate.propose_from_episodes(mem, [ep.memory_id], statement=SUPPORT)
    with pytest.raises(ValueError):
        gate.accept(
            mem,
            cand,
            actor="  ",
            epistemic_kind=EpistemicKind.INFERENCE,
            producer="attacker",
        )


def test_consolidation_accept_mints_semantic_but_cannot_factify(tmp_path: Path) -> None:
    mem, hyp, ledger = _store(tmp_path)
    ep = _remember(mem, statement=CONTRA, source_id="ep-contra")
    gate = ConsolidationGate()
    cand = gate.propose_from_episodes(mem, [ep.memory_id], statement=SUPPORT)
    semantic = gate.accept(
        mem,
        cand,
        actor="anyone",
        epistemic_kind=EpistemicKind.LESSON,
        producer="attacker",
    )
    assert semantic.epistemic_kind == EpistemicKind.LESSON.value
    assert semantic.memory_type == MemoryType.SEMANTIC.value
    assert cand.proposed_kind == EpistemicKind.INFERENCE.value
    assert semantic.epistemic_kind != cand.proposed_kind
    isolated, hyp2, led2 = _store(tmp_path / "iso")
    copied = isolated.remember(
        memory_type=semantic.memory_type,
        epistemic_kind=semantic.epistemic_kind,
        statement=semantic.statement,
        source_type=semantic.source_type,
        source_id=semantic.source_id,
        source_location=semantic.source_location,
        producer=semantic.producer,
        producer_version=semantic.producer_version,
        domain=semantic.domain,
        context=semantic.context,
        created_at=NOW,
        payload=dict(semantic.payload or {}),
    )
    task = _task(requested_evidence=[copied.memory_id], write_back=True)
    result, _, binds = _run(tmp_path, isolated, hyp2, led2, task)
    assert binds
    assert all(b.live_typed_class() == "LESSON" for b in binds)
    assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in binds)
    assert result.verdict not in POSITIVE
    assert result.verdict != CognitiveVerdict.WEAKLY_SUPPORTED.value


def test_consolidation_forged_candidate_skips_propose_from_episodes(tmp_path: Path) -> None:
    mem, hyp, ledger = _store(tmp_path)
    forged = ConsolidationCandidate(
        source_memory_ids=(),
        statement=SUPPORT,
        proposed_kind=EpistemicKind.INFERENCE.value,
        requires_human=False,
        blocked_reason="",
    )
    rec = ConsolidationGate().accept(
        mem,
        forged,
        actor="forged-actor",
        epistemic_kind=EpistemicKind.HYPOTHESIS,
        producer="attacker",
    )
    assert rec.epistemic_kind == EpistemicKind.HYPOTHESIS.value
    task = _task(requested_evidence=[rec.memory_id], write_back=True)
    result, _, binds = _run(tmp_path, mem, hyp, ledger, task)
    assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in binds)
    assert result.verdict not in POSITIVE


def test_direct_bypass_false_claim_via_remember_then_second_hop(tmp_path: Path) -> None:
    """Attacker calls remember() then a fresh CognitiveOrchestrator.run().

    Hop 1: ungranted OBSERVED_FACT must not authorize a positive verdict.
    Hop 2: no reusable factual escalation is minted from that row.
    """
    mem, hyp, ledger = _store(tmp_path)
    rec = _remember(mem, source_id="forged-observation")
    task1 = _task(task_id="bypass-1", requested_evidence=[rec.memory_id], write_back=True)
    r1, _, b1 = _run(tmp_path, mem, hyp, ledger, task1)
    assert r1.verdict not in POSITIVE
    assert reusable_writeback_permitted(r1.verdict, b1) is False
    c1 = _counts(mem)
    assert c1["hypothesis"] == 0
    assert c1["lesson"] == 0
    assert c1["inference"] == 0
    assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in b1)


def test_authority_escalation_matrix_via_production_bind(tmp_path: Path) -> None:
    mem, hyp, ledger = _store(tmp_path)
    rows = [
        ("OF", MemoryType.EPISODIC, EpistemicKind.OBSERVED_FACT, SUPPORT),
        ("HYP", MemoryType.HYPOTHESIS, EpistemicKind.HYPOTHESIS, f"HYPOTHESIS {SUPPORT}"),
        ("LES", MemoryType.SEMANTIC, EpistemicKind.LESSON, f"LESSON {SUPPORT}"),
        ("INF", MemoryType.SEMANTIC, EpistemicKind.INFERENCE, f"INFERENCE {SUPPORT}"),
        ("EPI", MemoryType.EPISODIC, EpistemicKind.INFERENCE, f"episode {SUPPORT}"),
        ("PRE", MemoryType.SEMANTIC, EpistemicKind.PREDICTION, f"PREDICTION {SUPPORT}"),
        ("OPI", MemoryType.SEMANTIC, EpistemicKind.OPINION, f"OPINION {SUPPORT}"),
        ("SIM", MemoryType.SEMANTIC, EpistemicKind.SIMULATION, f"SIMULATION {SUPPORT}"),
    ]
    ids = {}
    for key, mtype, kind, statement in rows:
        ids[key] = _remember(
            mem,
            memory_type=mtype,
            epistemic_kind=kind,
            statement=statement,
            source_id=key,
        ).memory_id
    task = _task(requested_evidence=list(ids.values()), write_back=False)
    _, _, binds = _run(tmp_path, mem, hyp, ledger, task)
    by_src = {b.provenance.get("source_id"): b for b in binds}
    of = by_src["OF"]
    assert of.live_typed_class() == "OBSERVED_FACT"
    assert not of.may(ROLE_FACTUAL_PREMISE)
    assert of.support_strength != SUPPORT_DIRECT
    for key, typed in (
        ("HYP", "HYPOTHESIS"),
        ("LES", "LESSON"),
        ("INF", "INFERENCE"),
        ("EPI", "INFERENCE"),
        ("PRE", "PREDICTION"),
        ("OPI", "OPINION"),
        ("SIM", "SIMULATION"),
    ):
        b = by_src[key]
        assert b.live_typed_class() == typed, key
        assert not b.may(ROLE_FACTUAL_PREMISE), key
        assert b.support_strength != SUPPORT_DIRECT, key


def test_provenance_source_id_survives_retrieval_and_binding(tmp_path: Path) -> None:
    mem, hyp, ledger = _store(tmp_path)
    rec = _remember(mem, source_id="sensor-77", producer="ingest")
    task = _task(requested_evidence=[rec.memory_id], write_back=False)
    _, items, binds = _run(tmp_path, mem, hyp, ledger, task)
    assert items[0].source_id == "sensor-77"
    assert binds[0].provenance["source_id"] == "sensor-77"
    assert binds[0].epistemic_kind == rec.epistemic_kind
    assert binds[0].memory_id == rec.memory_id


def test_lexical_retriever_failure_intent_rejects_unanchored_fact(tmp_path: Path) -> None:
    """P4.3: question token 'failures' is FAILURE intent. Unanchored OBSERVED_FACT
    is rejected as UNRELATED_FAILURE. This is retrieval gating, not remember gating.
    requested_evidence still anchors the same row (see gap proof tests).
    """
    mem, _, _ = _store(tmp_path)
    rec = _remember(mem, source_id="lex-fail")
    task = _task(requested_evidence=[])
    explained = MemoryRetriever().retrieve_explained(mem, task, now=NOW)
    assert rec.memory_id not in {i.memory_id for i in explained.items}
    assert any(r.reason == "UNRELATED_FAILURE" for r in explained.rejected)


def test_lexical_retriever_without_failure_intent_consumes_forged_fact(tmp_path: Path) -> None:
    """Ungranted remember()'d OBSERVED_FACT may retrieve, but cannot factify."""
    mem, hyp, ledger = _store(tmp_path)
    _remember(
        mem,
        statement="retries after HTTP timeout recovered the request.",
        source_id="lex-help",
    )
    task = _task(
        question="Do retries after timeout help?",
        requested_evidence=[],
        write_back=True,
    )
    items = MemoryRetriever().retrieve(mem, task, now=NOW)
    assert any(i.epistemic_kind == EpistemicKind.OBSERVED_FACT.value for i in items)
    result = CognitiveOrchestrator(memory=mem, hypotheses=hyp, ledger_path=ledger).run(
        task, now=NOW + 1
    )
    binds = bind_context(result.context, task, store=mem, now=NOW + 1)
    assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in binds)
    assert result.verdict not in POSITIVE
