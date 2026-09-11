"""Layer 4 — independent V3 authority-boundary and clock tests.

This module MUST NOT import tests.p5_grant_fixtures.
Negative tests do not mint. Clock/positive cases use tests.observation_test_runtime
(tests-only key + typed fake acquisition), never production signing material.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import os
import sqlite3
from pathlib import Path

import pytest

from architecture.cognitive.hypothesis import HypothesisStore
from architecture.cognitive.loop.adapters import ingest_generic_observation
from architecture.cognitive.loop.binding import ROLE_FACTUAL_PREMISE, bind_context
from architecture.cognitive.loop.contracts import CognitiveTask, ReasoningMode, TaskType
from architecture.cognitive.loop.orchestrator import CognitiveOrchestrator
from architecture.cognitive.loop.retrieval import MemoryRetriever
from architecture.cognitive.memory.observation import (
    GRANT_PAYLOAD_KEY,
    AcquisitionRecord,
    BoundIngestPort,
    GRANT_VERSION,
    IngestPort,
    ISSUER_ID,
    ISSUER_ID_TEST,
    ObservationAuthority,
    ObservationGrant,
    is_forbidden_production_secret,
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

NOW = 1_800_000_000.0
PAST = NOW - 400 * 86400.0
FUTURE = NOW + 400 * 86400.0
SUPPORT = "Retries after timeout reduced failures."
Q = "Do retries after timeout reduce failures?"
TEST_VECTOR_KEY = bytes.fromhex("a1" * 32)


def _task(created_at: float = NOW, **kwargs) -> CognitiveTask:
    base = dict(
        task_id="v3",
        task_type=TaskType.ANALYZE.value,
        objective="timeout retries",
        question=Q,
        domain="software",
        requester="v3-audit",
        created_at=created_at,
        data_label="SYNTHETIC_TEST_DATA",
        reasoning_mode=ReasoningMode.DEDUCTIVE.value,
        write_back=False,
    )
    base.update(kwargs)
    return CognitiveTask(**base)


def _store(tmp_path: Path) -> CognitiveMemoryStore:
    return CognitiveMemoryStore(tmp_path / "mem.sqlite")


def _orch(tmp_path: Path, mem: CognitiveMemoryStore) -> CognitiveOrchestrator:
    return CognitiveOrchestrator(
        memory=mem,
        hypotheses=HypothesisStore(tmp_path / "hyp.jsonl"),
        ledger_path=tmp_path / "exp.jsonl",
    )


def _remember_ungranted(mem: CognitiveMemoryStore, statement: str = SUPPORT, **kwargs):
    kw = dict(
        memory_type=MemoryType.EPISODIC,
        epistemic_kind=EpistemicKind.OBSERVED_FACT,
        statement=statement,
        source_type=SourceType.SYSTEM,
        source_id="ordinary",
        source_location="direct",
        producer="caller",
        producer_version="t",
        domain="software",
        context="SYNTHETIC_TEST_DATA",
        observed_at=NOW - 20,
        created_at=NOW - 10,
        payload={"data_label": "SYNTHETIC_TEST_DATA"},
    )
    kw.update(kwargs)
    return mem.remember(**kw)


def _insert_row(store: CognitiveMemoryStore, rec: MemoryRecord) -> None:
    rec.integrity_hash = compute_integrity_hash(rec)
    conn = sqlite3.connect(str(store.path))
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
            json.dumps(rec.payload, sort_keys=True),
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
            json.dumps(list(rec.derived_from), sort_keys=True),
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


def _bind_factual(mem: CognitiveMemoryStore, rec, *, now: float, created_at: float) -> bool:
    task = _task(created_at=created_at, requested_evidence=[rec.memory_id])
    items = MemoryRetriever().retrieve(mem, task, now=now)
    from architecture.cognitive.loop.context import assemble_context

    ctx = assemble_context(items, mem, now=now)
    binds = bind_context(ctx, task, store=mem, now=now)
    return any(b.memory_id == rec.memory_id and b.may(ROLE_FACTUAL_PREMISE) for b in binds)


# ---------------------------------------------------------------------------
# Closed / removed mint APIs
# ---------------------------------------------------------------------------


def test_persist_observed_acquisition_is_absent_from_module() -> None:
    import architecture.cognitive.memory.observation as obs

    assert not hasattr(obs, "persist_observed_acquisition")
    with pytest.raises(AttributeError):
        obs.persist_observed_acquisition  # type: ignore[attr-defined]


def test_process_authority_getter_is_absent() -> None:
    import architecture.cognitive.memory.observation as obs

    assert not hasattr(obs, "_process_authority")


def test_ingest_port_persist_acquired_cannot_mint(tmp_path: Path) -> None:
    mem = _store(tmp_path)
    port = IngestPort()
    acq = AcquisitionRecord(
        statement=SUPPORT,
        source_type=SourceType.SYSTEM.value,
        source_id="attacker",
        observed_at=NOW - 20,
        domain="software",
        valid_until=NOW + 3600,
    )
    with pytest.raises(RuntimeError, match="cannot mint"):
        port.persist_acquired(mem, acq)


def test_cognitive_orchestrator_rejects_ingest_kwarg(tmp_path: Path) -> None:
    mem = _store(tmp_path)
    with pytest.raises(TypeError):
        CognitiveOrchestrator(  # type: ignore[call-arg]
            memory=mem,
            hypotheses=HypothesisStore(tmp_path / "hyp.jsonl"),
            ledger_path=tmp_path / "exp.jsonl",
            ingest=object(),
        )


def test_cognitive_orchestrator_rejects_verifier_kwarg(tmp_path: Path) -> None:
    mem = _store(tmp_path)
    with pytest.raises(TypeError):
        CognitiveOrchestrator(  # type: ignore[call-arg]
            memory=mem,
            hypotheses=HypothesisStore(tmp_path / "hyp.jsonl"),
            ledger_path=tmp_path / "exp.jsonl",
            verifier=object(),
        )


def test_cognitive_orchestrator_rejects_secret_kwarg(tmp_path: Path) -> None:
    mem = _store(tmp_path)
    with pytest.raises(TypeError):
        CognitiveOrchestrator(  # type: ignore[call-arg]
            memory=mem,
            hypotheses=HypothesisStore(tmp_path / "hyp.jsonl"),
            ledger_path=tmp_path / "exp.jsonl",
            secret=b"x" * 32,
        )


def test_cognitive_orchestrator_signature_has_no_authority_injection() -> None:
    params = inspect.signature(CognitiveOrchestrator.__init__).parameters
    forbidden = {
        "ingest",
        "verifier",
        "secret",
        "issuer",
        "grant_secret",
        "observation_authority",
        "bound_ingest",
        "ingest_port",
        "grant_key",
    }
    assert forbidden.isdisjoint(params.keys())


def test_matching_issuer_verifier_pair_cannot_be_injected_into_orchestrator(
    tmp_path: Path,
) -> None:
    mem = _store(tmp_path)
    attacker_key = os.urandom(32)
    issuer = ObservationAuthority(secret=attacker_key, issuer_id="attacker")
    with pytest.raises(TypeError):
        CognitiveOrchestrator(  # type: ignore[call-arg]
            memory=mem,
            hypotheses=HypothesisStore(tmp_path / "hyp.jsonl"),
            ledger_path=tmp_path / "exp.jsonl",
            ingest=BoundIngestPort(issuer),
            verifier=lambda **kw: True,
        )


def test_bound_ingest_and_authority_are_not_package_exports() -> None:
    import architecture.cognitive as cognitive_pkg
    import architecture.cognitive.loop as loop_pkg
    import architecture.cognitive.memory as mem

    for mod in (cognitive_pkg, loop_pkg, mem):
        exported = set(getattr(mod, "__all__", ()))
        assert "BoundIngestPort" not in exported
        assert "ObservationAuthority" not in exported
        assert "IngestPort" not in exported
        assert "persist_observed_acquisition" not in exported
        assert "persist_authorized_observation" not in exported


def test_production_modules_do_not_import_test_authority() -> None:
    import architecture.cognitive.loop.orchestrator as orch_mod
    import architecture.cognitive.memory.observation as obs

    for mod in (obs, orch_mod):
        src = inspect.getsource(mod)
        assert "tests.observation_test_runtime" not in src
        assert "p5_grant_fixtures" not in src
        assert "TEST_VECTOR_KEY" not in src


# ---------------------------------------------------------------------------
# Ungranted surfaces are not FACTUAL_PREMISE
# ---------------------------------------------------------------------------


def test_remember_observed_fact_is_not_factual_premise(tmp_path: Path) -> None:
    mem = _store(tmp_path)
    rec = _remember_ungranted(mem)
    assert _bind_factual(mem, rec, now=NOW, created_at=NOW) is False


def test_direct_sqlite_observed_fact_is_not_factual_premise(tmp_path: Path) -> None:
    mem = _store(tmp_path)
    rec = MemoryRecord(
        memory_id="SQL-V3",
        revision=1,
        memory_type=MemoryType.EPISODIC.value,
        epistemic_kind=EpistemicKind.OBSERVED_FACT.value,
        statement=SUPPORT,
        created_at=NOW - 10,
        observed_at=NOW - 20,
        source_type=SourceType.SYSTEM.value,
        source_id="sqlite-attacker",
        source_location="direct-insert",
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
        payload={"data_label": "SYNTHETIC_TEST_DATA"},
    )
    _insert_row(mem, rec)
    loaded = mem.get("SQL-V3")
    assert loaded is not None
    assert _bind_factual(mem, loaded, now=NOW, created_at=NOW) is False


def test_generic_ingest_is_not_factual_premise(tmp_path: Path) -> None:
    mem = _store(tmp_path)
    mid = ingest_generic_observation(
        mem,
        domain="software",
        statement=SUPPORT,
        source_id="generic",
        observed_at=NOW - 20,
        created_at=NOW - 10,
    )
    rec = mem.get(mid)
    assert rec is not None
    assert rec.epistemic_kind != EpistemicKind.OBSERVED_FACT.value
    assert _bind_factual(mem, rec, now=NOW, created_at=NOW) is False
    with pytest.raises(ValueError):
        ingest_generic_observation(
            mem,
            domain="software",
            statement=SUPPORT,
            source_id="generic-of",
            observed_at=NOW - 20,
            created_at=NOW - 10,
            kind=EpistemicKind.OBSERVED_FACT,
        )


def test_world_model_insertion_is_not_factual_premise(tmp_path: Path) -> None:
    mem = _store(tmp_path)
    rec = mem.record_world_model_object(
        object_kind="ENTITY",
        statement=SUPPORT,
        source_type=SourceType.SYSTEM,
        source_id="wm",
        source_location="wm",
        producer="t",
        producer_version="t",
        domain="software",
        context="SYNTHETIC_TEST_DATA",
    )
    assert rec.epistemic_kind != EpistemicKind.OBSERVED_FACT.value
    assert _bind_factual(mem, rec, now=NOW, created_at=NOW) is False


def test_corpus_seed_is_not_factual_premise(tmp_path: Path) -> None:
    from architecture.cognitive.benchmark.corpus import seed_corpus

    mem = _store(tmp_path)
    seed_corpus(mem, now=NOW)
    rec = mem.get("BM-SW-TIMEOUT-FACT")
    assert rec is not None
    assert GRANT_PAYLOAD_KEY not in (rec.payload or {})
    assert _bind_factual(mem, rec, now=NOW, created_at=NOW) is False


# ---------------------------------------------------------------------------
# Key separation
# ---------------------------------------------------------------------------


def test_production_issuer_rejects_test_vector_key() -> None:
    assert is_forbidden_production_secret(TEST_VECTOR_KEY)
    assert hashlib.sha256(TEST_VECTOR_KEY).hexdigest() == (
        "52fe6094743bfd4f9be4321d98adc7e23c1ab622b0ba830e271d1ee1cbfd7850"
    )
    with pytest.raises(ValueError, match="tests-only vector"):
        ObservationAuthority(secret=TEST_VECTOR_KEY, issuer_id=ISSUER_ID)


def test_test_issuer_accepts_test_vector_key() -> None:
    auth = ObservationAuthority(secret=TEST_VECTOR_KEY, issuer_id=ISSUER_ID_TEST)
    acq = AcquisitionRecord(
        statement=SUPPORT,
        source_type=SourceType.SYSTEM.value,
        source_id="fixture",
        observed_at=NOW - 20,
        domain="software",
        valid_until=NOW + 3600,
    )
    grant = auth._mint(acq)
    assert grant.issuer_id == ISSUER_ID_TEST
    assert verify_observation_grant(
        grant,
        statement=SUPPORT,
        source_type=SourceType.SYSTEM.value,
        source_id="fixture",
        observed_at=NOW - 20,
        valid_until=NOW + 3600,
        domain="software",
        epistemic_kind=EpistemicKind.OBSERVED_FACT.value,
        now=NOW,
        key=TEST_VECTOR_KEY,
        expected_issuer_id=ISSUER_ID_TEST,
    )


def test_env_observation_grant_secret_is_not_read(tmp_path: Path) -> None:
    os.environ["AHOS_OBSERVATION_GRANT_SECRET"] = "deadbeef" * 8
    try:
        orch = _orch(tmp_path, _store(tmp_path))
        assert orch._grant_verify_secret != bytes.fromhex("deadbeef" * 8)
        assert is_forbidden_production_secret(orch._grant_verify_secret) is False
    finally:
        del os.environ["AHOS_OBSERVATION_GRANT_SECRET"]


def test_module_has_no_live_secret_or_authority_global() -> None:
    import architecture.cognitive.memory.observation as obs

    names = dir(obs)
    for forbidden in ("_SECRET", "_secret", "_process_authority", "_AUTHORITY", "PROCESS_AUTHORITY"):
        assert forbidden not in names
    for value in vars(obs).values():
        if isinstance(value, ObservationAuthority):
            raise AssertionError("module-global ObservationAuthority is forbidden")
        if isinstance(value, BoundIngestPort):
            raise AssertionError("module-global BoundIngestPort is forbidden")


# ---------------------------------------------------------------------------
# Clock: task.created_at must not control factual validity
# ---------------------------------------------------------------------------


def test_case_a_old_created_at_current_trusted_now(tmp_path: Path) -> None:
    from tests.observation_test_runtime import (
        persist_test_observation,
        grant_verify_scope,
        timeout_retry_reading,
    )

    mem = _store(tmp_path)
    rec = persist_test_observation(
        mem,
        timeout_retry_reading(
            SUPPORT, acquired_at=NOW - 20, valid_until=NOW + 3600
        ),
    )
    with grant_verify_scope(trusted_now=NOW):
        assert _bind_factual(mem, rec, now=NOW, created_at=PAST) is True


def test_case_b_future_created_at_cannot_extend_validity(tmp_path: Path) -> None:
    from tests.observation_test_runtime import (
        persist_test_observation,
        grant_verify_scope,
        timeout_retry_reading,
    )

    mem = _store(tmp_path)
    rec = persist_test_observation(
        mem,
        timeout_retry_reading(
            SUPPORT,
            acquired_at=NOW - 7200,
            valid_until=NOW - 60,
        ),
    )
    with grant_verify_scope(trusted_now=NOW):
        assert _bind_factual(mem, rec, now=NOW, created_at=FUTURE) is False


def test_case_c_run_now_freeze_is_trusted_runtime(tmp_path: Path) -> None:
    from tests.observation_test_runtime import (
        persist_test_observation,
        grant_verify_scope,
        timeout_retry_reading,
    )

    mem = _store(tmp_path)
    rec = persist_test_observation(
        mem,
        timeout_retry_reading(
            SUPPORT, acquired_at=NOW - 20, valid_until=NOW + 3600
        ),
    )
    orch = _orch(tmp_path, mem)
    task = _task(created_at=PAST, requested_evidence=[rec.memory_id])
    with grant_verify_scope(trusted_now=NOW):
        result = orch.run(task, now=NOW)
        binds = bind_context(result.context, task, store=mem, now=NOW)
        assert any(b.may(ROLE_FACTUAL_PREMISE) for b in binds)
        assert all(
            b.authority_now == NOW for b in binds if b.may(ROLE_FACTUAL_PREMISE)
        )


def test_case_d_grant_expired_relative_to_trusted_runtime(tmp_path: Path) -> None:
    from tests.observation_test_runtime import (
        persist_test_observation,
        grant_verify_scope,
        timeout_retry_reading,
    )

    mem = _store(tmp_path)
    rec = persist_test_observation(
        mem,
        timeout_retry_reading(
            SUPPORT, acquired_at=NOW - 7200, valid_until=NOW - 60
        ),
    )
    with grant_verify_scope(trusted_now=NOW):
        assert _bind_factual(mem, rec, now=NOW, created_at=NOW) is False


def test_case_e_future_observation_relative_to_trusted_runtime(tmp_path: Path) -> None:
    from tests.observation_test_runtime import (
        persist_test_observation,
        grant_verify_scope,
        timeout_retry_reading,
    )

    mem = _store(tmp_path)
    rec = persist_test_observation(
        mem,
        timeout_retry_reading(
            SUPPORT, acquired_at=FUTURE, valid_until=FUTURE + 3600
        ),
    )
    with grant_verify_scope(trusted_now=NOW):
        assert _bind_factual(mem, rec, now=NOW, created_at=NOW) is False


def test_bind_without_trusted_now_is_not_factual(tmp_path: Path) -> None:
    from tests.observation_test_runtime import persist_test_observation, timeout_retry_reading

    mem = _store(tmp_path)
    rec = persist_test_observation(
        mem,
        timeout_retry_reading(
            SUPPORT, acquired_at=NOW - 20, valid_until=NOW + 3600
        ),
    )
    task = _task(created_at=NOW, requested_evidence=[rec.memory_id])
    items = MemoryRetriever().retrieve(mem, task, now=NOW)
    from architecture.cognitive.loop.context import assemble_context

    ctx = assemble_context(items, mem, now=NOW)
    binds = bind_context(ctx, task, store=mem)
    assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in binds)


# ---------------------------------------------------------------------------
# Authority adversarial matrix (independent of p5_grant_fixtures)
# ---------------------------------------------------------------------------


def test_direct_grant_construction_is_not_factual(tmp_path: Path) -> None:
    mem = _store(tmp_path)
    forged = ObservationGrant(
        version=GRANT_VERSION,
        purpose="FACTUAL_INGEST",
        kind=EpistemicKind.OBSERVED_FACT.value,
        statement_sha256="00" * 32,
        source_type=SourceType.SYSTEM.value,
        source_id="forged",
        observed_at_us=int(NOW - 20) * 1_000_000,
        valid_until="NONE",
        domain="software",
        issuer_id=ISSUER_ID,
        mac="11" * 32,
    )
    rec = _remember_ungranted(
        mem,
        source_id="forged",
        payload={
            "data_label": "SYNTHETIC_TEST_DATA",
            GRANT_PAYLOAD_KEY: forged.to_dict(),
        },
    )
    assert _bind_factual(mem, rec, now=NOW, created_at=NOW) is False


def test_alien_bound_ingest_port_is_not_production_valid(tmp_path: Path) -> None:
    mem = _store(tmp_path)
    attacker = BoundIngestPort(ObservationAuthority(secret=os.urandom(32), issuer_id="attacker"))
    rec = attacker.persist_acquired(
        mem,
        AcquisitionRecord(
            statement=SUPPORT,
            source_type=SourceType.SYSTEM.value,
            source_id="alien",
            observed_at=NOW - 20,
            domain="software",
            valid_until=NOW + 3600,
        ),
    )
    orch = _orch(tmp_path, mem)
    task = _task(requested_evidence=[rec.memory_id])
    result = orch.run(task, now=NOW)
    binds = bind_context(result.context, task, store=mem, now=NOW)
    assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in binds)


def test_copied_grant_does_not_authorize_other_statement(tmp_path: Path) -> None:
    from tests.observation_test_runtime import (
        persist_test_observation,
        grant_verify_scope,
        timeout_retry_reading,
    )

    mem = _store(tmp_path)
    a = persist_test_observation(
        mem, timeout_retry_reading(SUPPORT, sensor_id="a")
    )
    grant = dict(a.payload[GRANT_PAYLOAD_KEY])
    copied = _remember_ungranted(
        mem,
        statement="Service B retries after timeout reduced failures.",
        source_id="a",
        payload={"data_label": "SYNTHETIC_TEST_DATA", GRANT_PAYLOAD_KEY: grant},
    )
    with grant_verify_scope(trusted_now=NOW):
        assert _bind_factual(mem, copied, now=NOW, created_at=NOW) is False


def test_serialized_grant_reconstruction_without_matching_fields(tmp_path: Path) -> None:
    from tests.observation_test_runtime import (
        persist_test_observation,
        grant_verify_scope,
        timeout_retry_reading,
    )

    mem = _store(tmp_path)
    rec = persist_test_observation(mem, timeout_retry_reading(SUPPORT, sensor_id="ser"))
    blob = json.dumps(rec.as_dict())
    restored = json.loads(blob)
    clone = _remember_ungranted(
        mem,
        statement=SUPPORT + " copy",
        source_id="ser2",
        payload=dict(restored["payload"]),
    )
    with grant_verify_scope(trusted_now=NOW):
        assert _bind_factual(mem, clone, now=NOW, created_at=NOW) is False


def test_revision_cannot_reuse_prior_grant(tmp_path: Path) -> None:
    from tests.observation_test_runtime import (
        persist_test_observation,
        grant_verify_scope,
        timeout_retry_reading,
    )

    mem = _store(tmp_path)
    rec = persist_test_observation(mem, timeout_retry_reading(SUPPORT, sensor_id="rev"))
    nxt = mem.revise(
        rec.memory_id,
        statement="Retries after timeout increased failures.",
        correction_reason="mutate",
        now=NOW,
    )
    assert GRANT_PAYLOAD_KEY not in nxt.payload
    with grant_verify_scope(trusted_now=NOW):
        assert _bind_factual(mem, rec, now=NOW, created_at=NOW) is False


def test_toctou_mutate_after_issuance(tmp_path: Path) -> None:
    from tests.observation_test_runtime import (
        persist_test_observation,
        grant_verify_scope,
        timeout_retry_reading,
    )

    mem = _store(tmp_path)
    rec = persist_test_observation(mem, timeout_retry_reading(SUPPORT, sensor_id="toc"))
    task = _task(requested_evidence=[rec.memory_id])
    items = MemoryRetriever().retrieve(mem, task, now=NOW)
    mem.revise(
        rec.memory_id,
        statement="Retries after timeout increased failures.",
        correction_reason="toctou",
        now=NOW + 1,
    )
    from architecture.cognitive.loop.context import assemble_context

    ctx = assemble_context(items, mem, now=NOW + 2)
    with grant_verify_scope(trusted_now=NOW + 2):
        binds = bind_context(ctx, task, store=mem, now=NOW + 2)
    assert binds
    assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in binds)


def test_derived_fact_cannot_reuse_observation_grant(tmp_path: Path) -> None:
    from tests.observation_test_runtime import (
        persist_test_observation,
        grant_verify_scope,
        timeout_retry_reading,
    )

    mem = _store(tmp_path)
    authorized = persist_test_observation(
        mem, timeout_retry_reading(SUPPORT, sensor_id="df")
    )
    grant = authorized.payload[GRANT_PAYLOAD_KEY]
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
        payload={"data_label": "SYNTHETIC_TEST_DATA", GRANT_PAYLOAD_KEY: dict(grant)},
    )
    with grant_verify_scope(trusted_now=NOW):
        assert _bind_factual(mem, derived, now=NOW, created_at=NOW) is False
        assert not verify_observation_grant(
            ObservationGrant.from_dict(grant),
            statement=SUPPORT,
            source_type=SourceType.SYSTEM.value,
            source_id="df2",
            observed_at=NOW - 20,
            valid_until=None,
            domain="software",
            epistemic_kind=EpistemicKind.DERIVED_FACT.value,
            now=NOW,
            key=TEST_VECTOR_KEY,
            expected_issuer_id=ISSUER_ID_TEST,
        )


def test_n_hop_ungranted_observed_fact_cannot_write_reusable_memory(
    tmp_path: Path,
) -> None:
    mem = _store(tmp_path)
    rec = _remember_ungranted(mem)
    orch = _orch(tmp_path, mem)
    task = _task(
        created_at=NOW,
        requested_evidence=[rec.memory_id],
        write_back=True,
        task_type=TaskType.INVESTIGATE.value,
    )
    result = orch.run(task, now=NOW)
    assert result.reusable_writeback is False
    assert result.hypothesis_id == ""
    assert result.lesson_memory_id == ""
    binds = bind_context(result.context, task, store=mem, now=NOW)
    assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in binds)


def test_no_public_alternate_mint_factory() -> None:
    import architecture.cognitive.memory.observation as obs

    for name in ("issue", "mint", "sign", "grant_for", "from_statement"):
        assert not hasattr(obs, name)
        assert not hasattr(ObservationAuthority, name)
        assert not hasattr(IngestPort, name)
