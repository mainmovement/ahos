"""P5 V4-PIN adversarial matrix. Independent of p5_grant_fixtures mint helpers.

Production CognitiveOrchestrator must not accept attacker HMAC as FACTUAL_PREMISE.
Positive isolation uses TestCognitiveOrchestrator with distinct test keys.
"""

from __future__ import annotations

import inspect
import os
import sqlite3
from pathlib import Path

import pytest

from architecture.cognitive.hypothesis import HypothesisStore
from architecture.cognitive.loop.binding import ROLE_FACTUAL_PREMISE, bind_context, bind_item
from architecture.cognitive.loop.contracts import CognitiveTask, ReasoningMode, TaskType
from architecture.cognitive.loop.orchestrator import CognitiveOrchestrator
from architecture.cognitive.loop.reason import reason
from architecture.cognitive.loop.retrieval import MemoryRetriever
from architecture.cognitive.memory.observation import (
    GRANT_PAYLOAD_KEY,
    AcquisitionRecord,
    BoundIngestPort,
    GrantVerifyContext,
    ISSUER_ID,
    ISSUER_ID_TEST,
    ObservationAuthority,
    clear_grant_verify_context,
    current_grant_verify_context,
    grant_from_payload,
    push_grant_verify_context,
    reset_grant_verify_context,
    verify_observation_grant,
)
from architecture.cognitive.memory.record import MemoryRecord, compute_integrity_hash
from architecture.cognitive.memory.store import CognitiveMemoryStore
from architecture.cognitive.memory.types import (
    ContradictionState,
    DecayState,
    EpistemicKind,
    MemoryType,
    SourceType,
)
from tests.observation_test_runtime import (
    NOW,
    TEST_VECTOR_KEY,
    TestAcquisitionAdapter,
    TestCognitiveOrchestrator,
    TypedFakeAcquisitionResult,
    grant_verify_scope,
    persist_test_observation,
    timeout_retry_reading,
)

SUPPORT = "Retries after timeout reduced failures."
Q = "Do retries after timeout reduce failures?"
KEY_A = bytes.fromhex("c1" * 32)
KEY_B = bytes.fromhex("c2" * 32)


@pytest.fixture(autouse=True)
def _isolate_grant_verify_context() -> None:
    clear_grant_verify_context()
    yield
    clear_grant_verify_context()


def _task(**kwargs) -> CognitiveTask:
    base = dict(
        task_id="v4",
        task_type=TaskType.ANALYZE.value,
        objective="timeout retries",
        question=Q,
        domain="software",
        requester="v4",
        created_at=NOW,
        data_label="SYNTHETIC_TEST_DATA",
        reasoning_mode=ReasoningMode.DEDUCTIVE.value,
        write_back=True,
    )
    base.update(kwargs)
    return CognitiveTask(**base)


def _store(tmp_path: Path) -> CognitiveMemoryStore:
    return CognitiveMemoryStore(tmp_path / "mem.sqlite")


def _prod(tmp_path: Path, mem: CognitiveMemoryStore, retriever=None) -> CognitiveOrchestrator:
    return CognitiveOrchestrator(
        memory=mem,
        hypotheses=HypothesisStore(tmp_path / "hyp.jsonl"),
        ledger_path=tmp_path / "exp.jsonl",
        retriever=retriever,
    )


def _acq(statement: str = SUPPORT, *, secret: bytes, issuer_id: str, source_id: str = "att"):
    return BoundIngestPort(ObservationAuthority(secret=secret, issuer_id=issuer_id))


def _factual_after_run(orch: CognitiveOrchestrator, rec, *, now: float = NOW) -> bool:
    task = _task(requested_evidence=[rec.memory_id])
    result = orch.run(task, now=now)
    binds = orch._bind_context(result.context, task, now=now)
    return any(b.memory_id == rec.memory_id and b.may(ROLE_FACTUAL_PREMISE) for b in binds), result


# A / B / J — caller-created authority and BoundIngestPort


def test_a_caller_created_authority_is_not_production_factual(tmp_path: Path) -> None:
    mem = _store(tmp_path)
    k = os.urandom(32)
    rec = _acq(secret=k, issuer_id=ISSUER_ID).persist_acquired(
        mem,
        AcquisitionRecord(
            statement=SUPPORT,
            source_type=SourceType.SYSTEM.value,
            source_id="a",
            observed_at=NOW - 20,
            domain="software",
            valid_until=NOW + 3600,
        ),
    )
    orch = _prod(tmp_path, mem)
    ok, result = _factual_after_run(orch, rec)
    assert ok is False
    assert result.reusable_writeback is False


def test_b_caller_bound_ingest_port_is_not_production_factual(tmp_path: Path) -> None:
    mem = _store(tmp_path)
    rec = BoundIngestPort(ObservationAuthority(secret=os.urandom(32))).persist_acquired(
        mem,
        AcquisitionRecord(
            statement=SUPPORT,
            source_type=SourceType.SYSTEM.value,
            source_id="b",
            observed_at=NOW - 20,
            domain="software",
            valid_until=NOW + 3600,
        ),
    )
    ok, _ = _factual_after_run(_prod(tmp_path, mem), rec)
    assert ok is False


# C / D / E — ContextVar injection ignored by production run


def test_cde_contextvar_key_and_issuer_ignored_by_production_run(tmp_path: Path) -> None:
    mem = _store(tmp_path)
    k = os.urandom(32)
    rec = _acq(secret=k, issuer_id=ISSUER_ID).persist_acquired(
        mem,
        AcquisitionRecord(
            statement=SUPPORT,
            source_type=SourceType.SYSTEM.value,
            source_id="cde",
            observed_at=NOW - 20,
            domain="software",
            valid_until=NOW + 3600,
        ),
    )
    orch = _prod(tmp_path, mem)
    token = push_grant_verify_context(GrantVerifyContext(k, ISSUER_ID, float(NOW)))
    try:
        ok, result = _factual_after_run(orch, rec)
        assert ok is False
        assert result.reusable_writeback is False
    finally:
        reset_grant_verify_context(token)


def test_e_grant_verify_scope_does_not_rekey_production_orchestrator(tmp_path: Path) -> None:
    mem = _store(tmp_path)
    rec = persist_test_observation(mem, timeout_retry_reading(SUPPORT))
    orch = _prod(tmp_path, mem)
    with grant_verify_scope(trusted_now=NOW):
        ok, _ = _factual_after_run(orch, rec)
    assert ok is False


def test_public_bind_and_reason_fail_closed_despite_contextvar(tmp_path: Path) -> None:
    mem = _store(tmp_path)
    rec = persist_test_observation(mem, timeout_retry_reading(SUPPORT))
    task = _task(requested_evidence=[rec.memory_id])
    with grant_verify_scope(trusted_now=NOW):
        items = MemoryRetriever().retrieve(mem, task, now=NOW)
        from architecture.cognitive.loop.context import assemble_context

        ctx = assemble_context(items, mem, now=NOW)
        binds = bind_context(ctx, task, store=mem, now=NOW)
        assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in binds)
        v, _, _, _, _ = reason(task, ctx, retrieved_ids=[rec.memory_id], store=mem, now=NOW)
        assert v not in {"SUPPORTED", "WEAKLY_SUPPORTED"} or all(
            not b.may(ROLE_FACTUAL_PREMISE) for b in binds
        )


def test_public_apis_reject_authority_kwargs() -> None:
    assert "key" not in inspect.signature(bind_item).parameters
    assert "secret" not in inspect.signature(bind_item).parameters
    assert "verifier" not in inspect.signature(reason).parameters
    assert "key" not in inspect.signature(reason).parameters
    params = inspect.signature(CognitiveOrchestrator.__init__).parameters
    for forbidden in (
        "secret",
        "verifier",
        "ingest",
        "authority",
        "issuer",
        "grant_verify_context",
        "verify_secret",
        "verify_issuer_id",
    ):
        assert forbidden not in params


# F — malicious retriever


class _MaliciousRetriever(MemoryRetriever):
    def __init__(self) -> None:
        super().__init__()
        self.seen_key = None
        self.pushed = False

    def retrieve(self, store, task, *, now=None, **kwargs):
        ctx = current_grant_verify_context()
        self.seen_key = None if ctx is None else ctx.key
        k = os.urandom(32)
        push_grant_verify_context(GrantVerifyContext(k, ISSUER_ID, float(now or 0)))
        self.pushed = True
        return super().retrieve(store, task, now=now, **kwargs)


def test_f_malicious_retriever_cannot_obtain_or_replace_production_authority(
    tmp_path: Path,
) -> None:
    mem = _store(tmp_path)
    k = os.urandom(32)
    rec = _acq(secret=k, issuer_id=ISSUER_ID).persist_acquired(
        mem,
        AcquisitionRecord(
            statement=SUPPORT,
            source_type=SourceType.SYSTEM.value,
            source_id="ret",
            observed_at=NOW - 20,
            domain="software",
            valid_until=NOW + 3600,
        ),
    )
    spy = _MaliciousRetriever()
    orch = _prod(tmp_path, mem, retriever=spy)
    ok, _ = _factual_after_run(orch, rec)
    assert ok is False
    assert spy.seen_key is None
    assert spy.pushed is True


# G — malicious memory


class _SpyStore(CognitiveMemoryStore):
    def __init__(self, path) -> None:
        super().__init__(path)
        self.seen_before_push = "unset"
        self.pushed_key = os.urandom(32)
        self._pushed = False
        self.later_keys: list[bytes | None] = []

    def get(self, memory_id: str):
        ctx = current_grant_verify_context()
        observed = None if ctx is None else bytes(ctx.key)
        if not self._pushed:
            self.seen_before_push = observed
            push_grant_verify_context(
                GrantVerifyContext(self.pushed_key, ISSUER_ID, float(NOW))
            )
            self._pushed = True
        else:
            self.later_keys.append(observed)
        return super().get(memory_id)


def test_g_malicious_memory_cannot_select_production_verifier(tmp_path: Path) -> None:
    mem = _SpyStore(tmp_path / "spy.sqlite")
    k = os.urandom(32)
    rec = _acq(secret=k, issuer_id=ISSUER_ID).persist_acquired(
        mem,
        AcquisitionRecord(
            statement=SUPPORT,
            source_type=SourceType.SYSTEM.value,
            source_id="mem",
            observed_at=NOW - 20,
            domain="software",
            valid_until=NOW + 3600,
        ),
    )
    orch = _prod(tmp_path, mem)
    ok, _ = _factual_after_run(orch, rec)
    assert ok is False
    assert mem.seen_before_push is None
    assert all(key in {None, mem.pushed_key} for key in mem.later_keys)


# H — fake acquisition result is not a production mint input


def test_h_fake_acquisition_dataclass_is_not_production_authority(tmp_path: Path) -> None:
    mem = _store(tmp_path)
    fake = TypedFakeAcquisitionResult(
        sensor_channel="software.timeout_recovery",
        raw_reading=SUPPORT,
        acquired_at=NOW - 20,
        sensor_id="fake",
        domain="software",
        valid_until=NOW + 3600,
    )
    orch = _prod(tmp_path, mem)
    assert not hasattr(orch, "ingest")
    with pytest.raises(TypeError):
        orch.run(_task(), ingest=fake)  # type: ignore[call-arg]
    rec = persist_test_observation(mem, fake)
    ok, _ = _factual_after_run(orch, rec)
    assert ok is False


# I — issuer substitution


def test_i_attacker_issuer_rejected_by_production(tmp_path: Path) -> None:
    mem = _store(tmp_path)
    rec = _acq(secret=TEST_VECTOR_KEY, issuer_id="attacker.issuer").persist_acquired(
        mem,
        AcquisitionRecord(
            statement=SUPPORT,
            source_type=SourceType.SYSTEM.value,
            source_id="iss",
            observed_at=NOW - 20,
            domain="software",
            valid_until=NOW + 3600,
        ),
    )
    ok, _ = _factual_after_run(_prod(tmp_path, mem), rec)
    assert ok is False


# K — O1 / O2 isolation (tests-only secrets, not production urandom inspection)


def test_k_o1_grant_not_valid_for_o2(tmp_path: Path) -> None:
    mem = _store(tmp_path)
    rec = TestAcquisitionAdapter(secret=KEY_A, issuer_id=ISSUER_ID_TEST).acquire(
        mem,
        timeout_retry_reading(SUPPORT, sensor_id="iso"),
    )
    o1 = TestCognitiveOrchestrator(
        memory=mem,
        hypotheses=HypothesisStore(tmp_path / "h1.jsonl"),
        ledger_path=tmp_path / "e1.jsonl",
        verify_secret=KEY_A,
        verify_issuer_id=ISSUER_ID_TEST,
    )
    o2 = TestCognitiveOrchestrator(
        memory=mem,
        hypotheses=HypothesisStore(tmp_path / "h2.jsonl"),
        ledger_path=tmp_path / "e2.jsonl",
        verify_secret=KEY_B,
        verify_issuer_id=ISSUER_ID_TEST,
    )
    ok1, _ = _factual_after_run(o1, rec)
    ok2, _ = _factual_after_run(o2, rec)
    assert ok1 is True
    assert ok2 is False
    rec_b = TestAcquisitionAdapter(secret=KEY_B, issuer_id=ISSUER_ID_TEST).acquire(
        mem,
        timeout_retry_reading(SUPPORT, sensor_id="iso-b", memory_id="iso-b"),
    )
    ok1b, _ = _factual_after_run(o1, rec_b)
    ok2b, _ = _factual_after_run(o2, rec_b)
    assert ok1b is False
    assert ok2b is True


# L — SQLite insertion


def test_l_sqlite_row_without_production_grant_rejected(tmp_path: Path) -> None:
    mem = _store(tmp_path)
    rec = MemoryRecord(
        memory_id="sql-1",
        revision=1,
        memory_type=MemoryType.EPISODIC.value,
        epistemic_kind=EpistemicKind.OBSERVED_FACT.value,
        statement=SUPPORT,
        payload={"data_label": "SYNTHETIC_TEST_DATA"},
        created_at=NOW - 10,
        observed_at=NOW - 20,
        source_type=SourceType.SYSTEM.value,
        source_id="sql",
        source_location="sqlite",
        producer="attacker",
        producer_version="t",
        domain="software",
        context="SYNTHETIC_TEST_DATA",
        confidence=None,
        valid_from=None,
        valid_until=NOW + 3600,
        status=DecayState.ACTIVE.value,
        contradiction_state=ContradictionState.UNCONTESTED.value,
        integrity_hash="",
    )
    rec.integrity_hash = compute_integrity_hash(rec)
    conn = sqlite3.connect(str(mem.path))
    conn.execute(
        """INSERT INTO memories(
          memory_id, revision, memory_type, epistemic_kind, statement, payload_json,
          created_at, observed_at, source_type, source_id, source_location, producer,
          producer_version, domain, context, confidence, valid_from, valid_until,
          status, contradiction_state, supersedes, derived_from_json, outcome_link,
          hypothesis_id, experiment_id, agent_id, agent_namespace, ttl_seconds,
          session_id, task_id, priority, expires_at, integrity_hash, correction_reason,
          prediction_id, capability_gap_id, proposal_id
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            rec.memory_id,
            rec.revision,
            rec.memory_type,
            rec.epistemic_kind,
            rec.statement,
            __import__("json").dumps(rec.payload),
            rec.created_at,
            rec.observed_at,
            rec.source_type,
            rec.source_id,
            rec.source_location,
            rec.producer,
            rec.producer_version,
            rec.domain,
            rec.context,
            rec.confidence,
            rec.valid_from,
            rec.valid_until,
            rec.status,
            rec.contradiction_state,
            rec.supersedes,
            "[]",
            rec.outcome_link,
            rec.hypothesis_id,
            rec.experiment_id,
            rec.agent_id,
            rec.agent_namespace,
            rec.ttl_seconds,
            rec.session_id,
            rec.task_id,
            rec.priority,
            rec.expires_at,
            rec.integrity_hash,
            rec.correction_reason,
            rec.prediction_id,
            rec.capability_gap_id,
            rec.proposal_id,
        ),
    )
    conn.commit()
    conn.close()
    ok, _ = _factual_after_run(_prod(tmp_path, mem), rec)
    assert ok is False


# M — revision inheritance


def test_m_revision_does_not_inherit_stale_authority(tmp_path: Path) -> None:
    mem = _store(tmp_path)
    rec = persist_test_observation(mem, timeout_retry_reading(SUPPORT, sensor_id="rev"))
    nxt = mem.revise(
        rec.memory_id,
        statement="Retries after timeout increased failures.",
        correction_reason="mutate",
        now=NOW,
    )
    assert GRANT_PAYLOAD_KEY not in nxt.payload
    orch = TestCognitiveOrchestrator(
        memory=mem,
        hypotheses=HypothesisStore(tmp_path / "hyp.jsonl"),
        ledger_path=tmp_path / "exp.jsonl",
    )
    ok, _ = _factual_after_run(orch, rec)
    assert ok is False


# N — DERIVED_FACT


def test_n_derived_fact_cannot_become_observed_fact_authority(tmp_path: Path) -> None:
    mem = _store(tmp_path)
    authorized = persist_test_observation(mem, timeout_retry_reading(SUPPORT, sensor_id="df"))
    derived = mem.remember(
        memory_type=MemoryType.SEMANTIC,
        epistemic_kind=EpistemicKind.DERIVED_FACT,
        statement=SUPPORT,
        source_type=SourceType.SYSTEM,
        source_id="df2",
        source_location="derived",
        producer="attacker",
        producer_version="t",
        domain="software",
        context="SYNTHETIC_TEST_DATA",
        observed_at=NOW - 20,
        created_at=NOW - 10,
        payload={
            "data_label": "SYNTHETIC_TEST_DATA",
            GRANT_PAYLOAD_KEY: authorized.payload[GRANT_PAYLOAD_KEY],
        },
    )
    orch = TestCognitiveOrchestrator(
        memory=mem,
        hypotheses=HypothesisStore(tmp_path / "hyp.jsonl"),
        ledger_path=tmp_path / "exp.jsonl",
    )
    ok, _ = _factual_after_run(orch, derived)
    assert ok is False


# O — N-hop


def test_o_n_hop_ungranted_episode_cannot_amplify(tmp_path: Path) -> None:
    mem = _store(tmp_path)
    mem.remember(
        memory_type=MemoryType.EPISODIC,
        epistemic_kind=EpistemicKind.INFERENCE,
        statement="episode hop SYNTHETIC_TEST_DATA",
        source_type=SourceType.SYSTEM,
        source_id="hop",
        source_location="n-hop",
        producer="pytest",
        producer_version="t",
        domain="software",
        context="SYNTHETIC_TEST_DATA",
        observed_at=NOW,
        created_at=NOW,
        payload={"data_label": "SYNTHETIC_TEST_DATA", "verdict": "WEAKLY_SUPPORTED"},
    )
    orch = _prod(tmp_path, mem)
    task = _task(write_back=True)
    result = orch.run(task, now=NOW)
    binds = orch._bind_context(result.context, task, now=NOW)
    assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in binds)
    assert result.reusable_writeback is False


# P — writeback without production FACTUAL


def test_p_attacker_grant_does_not_unlock_writeback(tmp_path: Path) -> None:
    mem = _store(tmp_path)
    rec = _acq(secret=os.urandom(32), issuer_id=ISSUER_ID).persist_acquired(
        mem,
        AcquisitionRecord(
            statement=SUPPORT,
            source_type=SourceType.SYSTEM.value,
            source_id="wb",
            observed_at=NOW - 20,
            domain="software",
            valid_until=NOW + 3600,
        ),
    )
    orch = _prod(tmp_path, mem)
    _, result = _factual_after_run(orch, rec)
    assert result.reusable_writeback is False
    assert result.lesson_memory_id == ""
    assert result.hypothesis_id == ""


def test_nested_orchestrators_do_not_share_parent_context(tmp_path: Path) -> None:
    mem = _store(tmp_path)
    rec = persist_test_observation(mem, timeout_retry_reading(SUPPORT))
    inner = _prod(tmp_path / "inner", mem)
    outer = TestCognitiveOrchestrator(
        memory=mem,
        hypotheses=HypothesisStore(tmp_path / "h.jsonl"),
        ledger_path=tmp_path / "e.jsonl",
    )
    ok_outer, _ = _factual_after_run(outer, rec)
    ok_inner, _ = _factual_after_run(inner, rec)
    assert ok_outer is True
    assert ok_inner is False


def test_j_attacker_key_valid_hmac_is_not_production_authority(tmp_path: Path) -> None:
    mem = _store(tmp_path)
    attacker_key = os.urandom(32)
    rec = _acq(secret=attacker_key, issuer_id=ISSUER_ID).persist_acquired(
        mem,
        AcquisitionRecord(
            statement=SUPPORT,
            source_type=SourceType.SYSTEM.value,
            source_id="j",
            observed_at=NOW - 20,
            domain="software",
            valid_until=NOW + 3600,
        ),
    )
    grant = grant_from_payload(rec.payload)
    assert grant is not None
    assert (
        verify_observation_grant(
            grant,
            statement=SUPPORT,
            source_type=SourceType.SYSTEM.value,
            source_id="j",
            observed_at=NOW - 20,
            valid_until=NOW + 3600,
            domain="software",
            epistemic_kind=EpistemicKind.OBSERVED_FACT.value,
            now=NOW,
            key=attacker_key,
            expected_issuer_id=ISSUER_ID,
        )
        is True
    )
    token = push_grant_verify_context(
        GrantVerifyContext(attacker_key, ISSUER_ID, float(NOW))
    )
    try:
        assert (
            verify_observation_grant(
                grant,
                statement=SUPPORT,
                source_type=SourceType.SYSTEM.value,
                source_id="j",
                observed_at=NOW - 20,
                valid_until=NOW + 3600,
                domain="software",
                epistemic_kind=EpistemicKind.OBSERVED_FACT.value,
                now=NOW,
                key=None,
                expected_issuer_id=None,
            )
            is False
        )
        ok, result = _factual_after_run(_prod(tmp_path, mem), rec)
        assert ok is False
        assert result.reusable_writeback is False
    finally:
        reset_grant_verify_context(token)


def test_production_run_does_not_publish_or_copy_grant_context(tmp_path: Path) -> None:
    mem = _store(tmp_path)
    rec = persist_test_observation(mem, timeout_retry_reading(SUPPORT))
    assert current_grant_verify_context() is None
    orch = _prod(tmp_path, mem)
    orch.run(_task(requested_evidence=[rec.memory_id]), now=NOW)
    assert current_grant_verify_context() is None


def test_production_run_rejects_authority_kwargs(tmp_path: Path) -> None:
    mem = _store(tmp_path)
    orch = _prod(tmp_path, mem)
    task = _task()
    for kwargs in (
        {"secret": b"x" * 32},
        {"verifier": object()},
        {"issuer": ISSUER_ID},
        {"grant_verify_context": object()},
        {"authority": object()},
        {"ingest": object()},
    ):
        with pytest.raises(TypeError):
            orch.run(task, now=NOW, **kwargs)  # type: ignore[arg-type]


def test_permits_observation_grant_has_no_caller_key() -> None:
    params = inspect.signature(CognitiveOrchestrator._permits_observation_grant).parameters
    for forbidden in ("key", "secret", "verifier", "issuer", "grant_verify_context"):
        assert forbidden not in params


def test_production_repr_does_not_expose_secret_field(tmp_path: Path) -> None:
    mem = _store(tmp_path)
    orch = _prod(tmp_path, mem)
    text = repr(orch)
    assert "_grant_verify_secret" not in text
    assert "GrantVerifyContext" not in text
    str_text = str(orch)
    assert "_grant_verify_secret" not in str_text
