"""Lane-B cognitive memory substrate — provenance, contradiction, persistence."""
from __future__ import annotations

import ast
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from architecture.cognitive import (  # noqa: E402
    HypothesisState,
    HypothesisStore,
    record_cognitive_experiment,
)
from architecture.cognitive.memory import (  # noqa: E402
    CognitiveMemoryStore,
    ConsolidationGate,
    EpistemicKind,
    EpistemicViolation,
    IntegrityError,
    InvalidProvenanceError,
    MemoryAuthorizationError,
    MemoryType,
    SoakBoundaryError,
    SourceType,
    compute_integrity_hash,
)
from architecture.cognitive.memory.self_query import (  # noqa: E402
    build_self_research_with_memory,
)
from architecture.cognitive.memory.store import assert_not_soak_db  # noqa: E402
from architecture.cognitive.memory.types import DecayState  # noqa: E402

COGNITIVE_DIR = ROOT / "architecture" / "cognitive"
FORBIDDEN = {"discovery", "paper_trading", "telegram_ai", "engine"}


def _store(tmp_path: Path) -> CognitiveMemoryStore:
    return CognitiveMemoryStore(tmp_path / "ahos_cognitive_memory.sqlite")


def test_cognitive_memory_does_not_import_lane_a():
    for path in sorted((COGNITIVE_DIR / "memory").rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        roots: set[str] = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                for alias in n.names:
                    roots.add(alias.name.split(".")[0])
            elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
                roots.add(n.module.split(".")[0])
        assert not (FORBIDDEN & roots), path


def test_refuses_soak_and_lane_a_database_names(tmp_path: Path):
    for name in (
        "e01_discovery.sqlite",
        "paper_trading.sqlite",
        "ahos_local.sqlite",
        "ahos_knowledge.sqlite",
    ):
        with pytest.raises(SoakBoundaryError):
            CognitiveMemoryStore(tmp_path / name)
        with pytest.raises(SoakBoundaryError):
            assert_not_soak_db(tmp_path / name)


def test_write_read_restart_and_deterministic_ids(tmp_path: Path):
    path = tmp_path / "ahos_cognitive_memory.sqlite"
    store = CognitiveMemoryStore(path)
    a = store.remember(
        memory_type=MemoryType.EPISODIC,
        epistemic_kind=EpistemicKind.OBSERVED_FACT,
        statement="cycle reported DEGRADED",
        source_type=SourceType.SYSTEM,
        source_id="observation_loop",
        source_location="architecture.runtime.observation_loop",
        producer="test",
        producer_version="t1",
        domain="COGNITIVE_CORE",
        context="unit",
        observed_at=100.0,
        created_at=200.0,
    )
    assert a.memory_id == "MEM-000001"
    assert a.observed_at == 100.0
    assert a.created_at == 200.0
    assert a.observed_at != a.created_at
    b = store.remember(
        memory_type=MemoryType.EPISODIC,
        epistemic_kind=EpistemicKind.OBSERVED_FACT,
        statement="second episode",
        source_type=SourceType.SYSTEM,
        source_id="observation_loop",
        source_location="architecture.runtime.observation_loop",
        producer="test",
        producer_version="t1",
        domain="COGNITIVE_CORE",
        context="unit",
    )
    assert b.memory_id == "MEM-000002"
    with pytest.raises(ValueError, match="already exists"):
        store.remember(
            memory_id="MEM-000001",
            memory_type=MemoryType.EPISODIC,
            epistemic_kind=EpistemicKind.OBSERVED_FACT,
            statement="dup",
            source_type=SourceType.SYSTEM,
            source_id="observation_loop",
            source_location="x",
            producer="test",
            producer_version="t1",
            domain="COGNITIVE_CORE",
            context="unit",
        )
    del store
    reopened = CognitiveMemoryStore(path)
    got = reopened.get("MEM-000001")
    assert got is not None
    assert got.statement == "cycle reported DEGRADED"
    assert got.revision == 1
    assert reopened.integrity_check() == "ok"


def test_unknown_vs_invalid_provenance(tmp_path: Path):
    store = _store(tmp_path)
    ok = store.remember(
        memory_type=MemoryType.EPISODIC,
        epistemic_kind=EpistemicKind.OBSERVED_FACT,
        statement="source unknown on purpose",
        source_type=SourceType.UNKNOWN,
        source_id="UNKNOWN",
        source_location="UNKNOWN",
        producer="UNKNOWN",
        producer_version="UNKNOWN",
        domain="COGNITIVE_CORE",
        context="UNKNOWN",
    )
    assert ok.source_id == "UNKNOWN"
    with pytest.raises(InvalidProvenanceError):
        store.remember(
            memory_type=MemoryType.EPISODIC,
            epistemic_kind=EpistemicKind.OBSERVED_FACT,
            statement="blank source",
            source_type=SourceType.SYSTEM,
            source_id="",
            source_location="here",
            producer="test",
            producer_version="t1",
            domain="COGNITIVE_CORE",
            context="unit",
        )


def test_fact_classification_and_ai_cannot_be_observed_fact(tmp_path: Path):
    store = _store(tmp_path)
    fact = store.remember(
        memory_type=MemoryType.EPISODIC,
        epistemic_kind=EpistemicKind.OBSERVED_FACT,
        statement="provider returned HTTP 429",
        source_type=SourceType.SYSTEM,
        source_id="dexscreener",
        source_location="adapter",
        producer="test",
        producer_version="t1",
        domain="FINANCIAL_ADAPTER",
        context="probe",
    )
    pred = store.remember(
        memory_type=MemoryType.EPISODIC,
        epistemic_kind=EpistemicKind.PREDICTION,
        statement="Token X will rise",
        source_type=SourceType.SYSTEM,
        source_id="score_ledger",
        source_location="architecture.learning.score_ledger",
        producer="test",
        producer_version="t1",
        domain="FINANCIAL_ADAPTER",
        context="prediction",
        prediction_id="pred_test_1",
    )
    sim = store.remember(
        memory_type=MemoryType.EPISODIC,
        epistemic_kind=EpistemicKind.SIMULATION,
        statement="synthetic path up 4x",
        source_type=SourceType.SYSTEM,
        source_id="hindsight",
        source_location="architecture.evolution.hindsight",
        producer="test",
        producer_version="t1",
        domain="COGNITIVE_CORE",
        context="simulation",
    )
    inf = store.remember(
        memory_type=MemoryType.SEMANTIC,
        epistemic_kind=EpistemicKind.INFERENCE,
        statement="join pairs remain zero until labels match",
        source_type=SourceType.HUMAN,
        source_id="operator",
        source_location="snapshot",
        producer="test",
        producer_version="t1",
        domain="COGNITIVE_CORE",
        context="self-research",
    )
    hyp = store.remember(
        memory_type=MemoryType.HYPOTHESIS,
        epistemic_kind=EpistemicKind.HYPOTHESIS,
        statement="eligible joins stay 0 through T+24h",
        source_type=SourceType.HYPOTHESIS_STORE,
        source_id="HYP-000001",
        source_location="hypothesis.jsonl",
        producer="test",
        producer_version="t1",
        domain="COGNITIVE_CORE",
        context="lifecycle",
        hypothesis_id="HYP-000001",
    )
    opinion = store.remember(
        memory_type=MemoryType.AGENT,
        epistemic_kind=EpistemicKind.OPINION,
        statement="council stance WAIT",
        source_type=SourceType.AI_MODEL,
        source_id="provider-x",
        source_location="architecture.council",
        producer="council",
        producer_version="v1",
        domain="COGNITIVE_CORE",
        context="advisory",
        agent_id="LENS-MUNGER",
        agent_namespace="LENS-MUNGER",
    )
    assert fact.epistemic_kind == "OBSERVED_FACT"
    assert pred.epistemic_kind == "PREDICTION"
    assert pred.prediction_id == "pred_test_1"
    assert sim.epistemic_kind == "SIMULATION"
    assert inf.epistemic_kind == "INFERENCE"
    assert hyp.epistemic_kind == "HYPOTHESIS"
    assert opinion.epistemic_kind == "OPINION"
    with pytest.raises(EpistemicViolation):
        store.remember(
            memory_type=MemoryType.SEMANTIC,
            epistemic_kind=EpistemicKind.OBSERVED_FACT,
            statement="Token X will rise",
            source_type=SourceType.AI_MODEL,
            source_id="llm",
            source_location="chat",
            producer="model",
            producer_version="x",
            domain="COGNITIVE_CORE",
            context="opinion",
        )


def test_contradiction_preserves_both_and_supersede_keeps_history(tmp_path: Path):
    store = _store(tmp_path)
    a = store.remember(
        memory_type=MemoryType.SEMANTIC,
        epistemic_kind=EpistemicKind.INFERENCE,
        statement="liquidity is sufficient",
        source_type=SourceType.HUMAN,
        source_id="analyst",
        source_location="note",
        producer="test",
        producer_version="t1",
        domain="COGNITIVE_CORE",
        context="unit",
    )
    b = store.remember(
        memory_type=MemoryType.SEMANTIC,
        epistemic_kind=EpistemicKind.INFERENCE,
        statement="liquidity is not executable",
        source_type=SourceType.HUMAN,
        source_id="analyst",
        source_location="note",
        producer="test",
        producer_version="t1",
        domain="COGNITIVE_CORE",
        context="unit",
    )
    edge = store.contradict(a.memory_id, b.memory_id, reason="opposite liquidity claims")
    assert store.get(a.memory_id) is not None
    assert store.get(b.memory_id) is not None
    assert store.get(a.memory_id).contradiction_state == "CONTESTED"
    assert store.get(a.memory_id).revision == 2
    assert store.get(a.memory_id, revision=1).contradiction_state == "UNCONTESTED"
    cons = store.find_contradictions(a.memory_id)
    assert any(e.edge_id == edge.edge_id for e in cons)
    store.support(a.memory_id, b.memory_id, reason="later evidence still conflicts")
    store.resolve_contradiction(edge.edge_id, resolver="human-reviewer")
    assert store.get(a.memory_id).contradiction_state == "RESOLVED"
    assert store.find_contradictions(a.memory_id)[0].resolution == "RESOLVED"
    successor = store.supersede(
        a.memory_id,
        statement="liquidity claim withdrawn pending data",
        correction_reason="insufficient executable depth",
        producer="human-reviewer",
    )
    old = store.get(a.memory_id)
    assert old.status == DecayState.SUPERSEDED.value
    assert successor.supersedes == a.memory_id
    hist = store.history(a.memory_id)
    assert len(hist) >= 3


def test_temporal_decay_stale_is_not_false(tmp_path: Path):
    store = _store(tmp_path)
    rec = store.remember(
        memory_type=MemoryType.WORKING,
        epistemic_kind=EpistemicKind.INFERENCE,
        statement="scratch context",
        source_type=SourceType.SYSTEM,
        source_id="session",
        source_location="wm",
        producer="test",
        producer_version="t1",
        domain="COGNITIVE_CORE",
        context="session-1",
        ttl_seconds=10,
        session_id="sess-1",
        task_id="task-1",
        created_at=1000.0,
        observed_at=1000.0,
        valid_from=1000.0,
        valid_until=1010.0,
    )
    assert rec.expires_at == 1010.0
    with pytest.raises(ValueError):
        store.remember(
            memory_type=MemoryType.WORKING,
            epistemic_kind=EpistemicKind.INFERENCE,
            statement="no ttl",
            source_type=SourceType.SYSTEM,
            source_id="session",
            source_location="wm",
            producer="test",
            producer_version="t1",
            domain="COGNITIVE_CORE",
            context="session-1",
            session_id="sess-1",
        )
    changed = store.apply_decay(now=2000.0)
    assert rec.memory_id in changed
    stale = store.get(rec.memory_id)
    assert stale.status == "STALE"
    assert stale.statement == "scratch context"
    ranged = store.find_by_time_range(start=999.0, end=1001.0, field="observed_at")
    assert any(r.memory_id == rec.memory_id for r in ranged)
    # Revision ingestion time is not the event time.
    assert store.get(rec.memory_id).created_at != store.get(rec.memory_id).observed_at


def test_hypothesis_experiment_outcome_links(tmp_path: Path):
    store = _store(tmp_path)
    hyps = HypothesisStore(tmp_path / "hyp.jsonl")
    hyp = hyps.propose("Novelty is not truth.")
    exp = record_cognitive_experiment(
        hypothesis_store=hyps,
        hypothesis_id=hyp.hypothesis_id,
        baseline="no ledger row",
        method="attach experiment",
        result="INSUFFICIENT_DATA",
        ledger_path=tmp_path / "experiments.jsonl",
        evidence_refs=["tests/test_cognitive_memory.py"],
    )
    mem = store.remember(
        memory_type=MemoryType.HYPOTHESIS,
        epistemic_kind=EpistemicKind.HYPOTHESIS,
        statement=hyp.statement,
        source_type=SourceType.HYPOTHESIS_STORE,
        source_id=hyp.hypothesis_id,
        source_location=str(tmp_path / "hyp.jsonl"),
        producer="test",
        producer_version="t1",
        domain="COGNITIVE_CORE",
        context="link",
        hypothesis_id=hyp.hypothesis_id,
        experiment_id=exp.experiment_id,
        outcome_link="outcome:UNKNOWN",
    )
    assert store.find_by_hypothesis(hyp.hypothesis_id)[0].memory_id == mem.memory_id
    assert store.find_by_experiment(exp.experiment_id)[0].hypothesis_id == hyp.hypothesis_id
    linked = hyps.get(hyp.hypothesis_id)
    assert linked is not None
    assert linked.state == HypothesisState.TESTING.value
    assert exp.experiment_id in linked.experiment_ids


def test_failure_recurrence_and_retrieval(tmp_path: Path):
    store = _store(tmp_path)
    first = store.record_failure(
        failure_type="PROVIDER_TIMEOUT",
        component="dexscreener",
        attempted_action="poll pairs",
        observed_failure="timeout after 15s",
        probable_cause="egress",
        now=10.0,
    )
    second = store.record_failure(
        failure_type="PROVIDER_TIMEOUT",
        component="dexscreener",
        attempted_action="poll pairs",
        observed_failure="timeout after 15s",
        probable_cause="egress",
        now=20.0,
    )
    fp = first.payload["fingerprint"]
    stats = store.failure_stats(fp)
    assert stats is not None
    assert stats["recurrence_count"] == 2
    assert stats["last_memory_id"] == second.memory_id
    found = store.find_failures(failure_type="PROVIDER_TIMEOUT", component="dexscreener")
    assert len(found) == 2


def test_agent_namespace_isolation(tmp_path: Path):
    store = _store(tmp_path)
    store.remember(
        memory_type=MemoryType.AGENT,
        epistemic_kind=EpistemicKind.LESSON,
        statement="agent A lesson",
        source_type=SourceType.AGENT,
        source_id="AG-14",
        source_location="passport",
        producer="test",
        producer_version="t1",
        domain="COGNITIVE_CORE",
        context="private",
        agent_id="AG-14",
        agent_namespace="AG-14",
    )
    store.remember(
        memory_type=MemoryType.AGENT,
        epistemic_kind=EpistemicKind.LESSON,
        statement="agent B lesson",
        source_type=SourceType.AGENT,
        source_id="AG-20",
        source_location="passport",
        producer="test",
        producer_version="t1",
        domain="COGNITIVE_CORE",
        context="private",
        agent_id="AG-20",
        agent_namespace="AG-20",
    )
    a_only = store.find_by_agent("AG-14")
    assert [r.statement for r in a_only] == ["agent A lesson"]
    ctx = store.relevant_context(agent_id="AG-14", limit=10)
    assert all(r.agent_namespace in {"", "AG-14"} for r in ctx)
    assert all(r.statement != "agent B lesson" for r in ctx)


def test_integrity_detects_tamper(tmp_path: Path):
    store = _store(tmp_path)
    rec = store.remember(
        memory_type=MemoryType.EPISODIC,
        epistemic_kind=EpistemicKind.OBSERVED_FACT,
        statement="untampered",
        source_type=SourceType.SYSTEM,
        source_id="sys",
        source_location="here",
        producer="test",
        producer_version="t1",
        domain="COGNITIVE_CORE",
        context="unit",
    )
    assert compute_integrity_hash(rec) == rec.integrity_hash
    conn = sqlite3.connect(str(store.path))
    conn.execute(
        "UPDATE memories SET statement=? WHERE memory_id=? AND revision=?",
        ("tampered", rec.memory_id, rec.revision),
    )
    conn.commit()
    conn.close()
    with pytest.raises(IntegrityError):
        store.get(rec.memory_id)


def test_memory_cannot_authorize_execution(tmp_path: Path):
    store = _store(tmp_path)
    with pytest.raises(MemoryAuthorizationError):
        store.authorize_execution()
    with pytest.raises(MemoryAuthorizationError):
        store.authorize_trading()
    with pytest.raises(MemoryAuthorizationError):
        store.elevate_autonomy()


def test_consolidation_refuses_observed_fact(tmp_path: Path):
    store = _store(tmp_path)
    ep = store.remember(
        memory_type=MemoryType.EPISODIC,
        epistemic_kind=EpistemicKind.OBSERVED_FACT,
        statement="timeout observed",
        source_type=SourceType.SYSTEM,
        source_id="sys",
        source_location="here",
        producer="test",
        producer_version="t1",
        domain="COGNITIVE_CORE",
        context="unit",
    )
    gate = ConsolidationGate()
    cand = gate.propose_from_episodes(store, [ep.memory_id], statement="timeouts recur")
    assert cand.requires_human is True
    with pytest.raises(EpistemicViolation):
        gate.accept(
            store,
            cand,
            actor="human",
            epistemic_kind=EpistemicKind.OBSERVED_FACT,
            producer="test",
        )
    semantic = gate.accept(
        store,
        cand,
        actor="human",
        epistemic_kind=EpistemicKind.INFERENCE,
        producer="test",
    )
    assert semantic.memory_type == MemoryType.SEMANTIC.value
    assert semantic.epistemic_kind == EpistemicKind.INFERENCE.value
    assert ep.memory_id in semantic.derived_from


def test_world_model_object_storage_is_not_a_world_model(tmp_path: Path):
    store = _store(tmp_path)
    rec = store.record_world_model_object(
        object_kind="ENTITY",
        statement="token T is an entity placeholder",
        source_type=SourceType.SYSTEM,
        source_id="wm-prep",
        source_location="memory",
        producer="test",
        producer_version="t1",
        domain="COGNITIVE_CORE",
        context="p2-prep",
    )
    assert rec.memory_type == MemoryType.WORLD_MODEL.value
    assert rec.epistemic_kind == EpistemicKind.INFERENCE.value
    assert rec.payload["object_kind"] == "ENTITY"


def test_self_research_memory_sidecar_is_not_soak_authority(tmp_path: Path):
    store = _store(tmp_path)
    store.record_failure(
        failure_type="X",
        component="c",
        attempted_action="a",
        observed_failure="fail",
    )
    report, summary = build_self_research_with_memory(
        snapshot={"OBSERVING": 800, "eligible_join_pairs_estimate": 0},
        data_label="TEST",
        soak_snapshot_is_authoritative=False,
        store=store,
    )
    assert summary["live_observer"] is False
    assert summary["soak_authority"] is False
    assert summary["failure_count"] == 1
    assert report.soak_snapshot_is_authoritative is False


def test_retrieval_primitives(tmp_path: Path):
    store = _store(tmp_path)
    rec = store.remember(
        memory_type=MemoryType.PROCEDURAL,
        epistemic_kind=EpistemicKind.PROCEDURE,
        statement="run freeze_lane_a before claiming COMPLETE",
        source_type=SourceType.SYSTEM,
        source_id="skill:ahos-change-verification",
        source_location=".cursor/skills/ahos-change-verification/SKILL.md",
        producer="test",
        producer_version="t1",
        domain="COGNITIVE_CORE",
        context="procedure",
    )
    assert store.find_by_type(MemoryType.PROCEDURAL)[0].memory_id == rec.memory_id
    assert store.find_by_source("skill:ahos-change-verification")[0].memory_id == rec.memory_id
    assert store.find_by_domain("COGNITIVE_CORE")
    assert store.recent(limit=1)[0].memory_id == rec.memory_id
    assert store.get(rec.memory_id) is not None
    rel = store.relevant_context(session_id="nope", limit=5)
    assert rel == []
