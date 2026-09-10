"""P5 ObservationGrant adversarial + positive-path proofs.

Isolated SYNTHETIC_TEST_DATA. Not AGI. Bind-time MAC is the authority boundary.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import architecture.cognitive as cognitive_pkg  # noqa: E402
import architecture.cognitive.loop as loop_pkg  # noqa: E402
import architecture.cognitive.memory as memory_pkg  # noqa: E402
from architecture.cognitive.hypothesis import HypothesisStore  # noqa: E402
from architecture.cognitive.loop.adapters import (  # noqa: E402
    finance_observation,
    ingest_generic_observation,
)
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
from architecture.cognitive.memory.observation import (  # noqa: E402
    GRANT_PAYLOAD_KEY,
    AcquisitionRecord,
    ObservationAuthority,
    ObservationGrant,
    canonical_observation_bytes,
    persist_observed_acquisition,
    statement_sha256,
    verify_observation_grant,
)
from architecture.cognitive.memory.record import MemoryRecord, compute_integrity_hash  # noqa: E402
from architecture.cognitive.memory.store import CognitiveMemoryStore  # noqa: E402
from architecture.cognitive.memory.types import (  # noqa: E402
    ContradictionState,
    DecayState,
    EpistemicKind,
    MemoryType,
    SourceType,
)
from tests.p5_grant_fixtures import persist_authorized  # noqa: E402

NOW = 1_800_000_000.0
POSITIVE = {
    CognitiveVerdict.SUPPORTED.value,
    CognitiveVerdict.WEAKLY_SUPPORTED.value,
}
Q = "Do retries after timeout reduce failures?"
SUPPORT = "Retries after timeout reduced failures."
OTHER = "Service B retries after timeout reduced failures."


def _task(**kwargs) -> CognitiveTask:
    base = dict(
        task_id="og",
        task_type=TaskType.ANALYZE.value,
        objective="timeout retries",
        question=Q,
        domain="software",
        requester="og-audit",
        created_at=NOW,
        data_label="SYNTHETIC_TEST_DATA",
        reasoning_mode=ReasoningMode.DEDUCTIVE.value,
        write_back=True,
    )
    base.update(kwargs)
    return CognitiveTask(**base)


def _run(mem: CognitiveMemoryStore, tmp_path: Path, task: CognitiveTask):
    hyp = HypothesisStore(tmp_path / "hyp.jsonl")
    orch = CognitiveOrchestrator(memory=mem, hypotheses=hyp, ledger_path=tmp_path / "exp.jsonl")
    result = orch.run(task, now=NOW + 1)
    binds = bind_context(result.context, task, store=mem)
    return result, binds


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


def test_no_public_issue_or_grant_mint_export() -> None:
    for mod in (cognitive_pkg, memory_pkg, loop_pkg):
        assert not hasattr(mod, "issue")
        exported = set(getattr(mod, "__all__", ()))
        assert "issue" not in exported
        assert "ObservationAuthority" not in exported
        assert "IngestPort" not in exported
        assert "persist_observed_acquisition" not in exported
    import architecture.cognitive.memory.observation as og

    assert not hasattr(og, "issue")
    assert not hasattr(ObservationAuthority, "issue")
    with pytest.raises(AttributeError):
        og.issue(statement=SUPPORT)  # type: ignore[attr-defined]


def test_ordinary_remember_observed_fact_is_not_factual(tmp_path: Path) -> None:
    mem = CognitiveMemoryStore(tmp_path / "mem.sqlite")
    rec = mem.remember(
        memory_type=MemoryType.EPISODIC,
        epistemic_kind=EpistemicKind.OBSERVED_FACT,
        statement=SUPPORT,
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
    assert rec.epistemic_kind == EpistemicKind.OBSERVED_FACT.value
    result, binds = _run(mem, tmp_path, _task(requested_evidence=[rec.memory_id]))
    assert binds
    assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in binds)
    assert result.verdict not in POSITIVE
    assert reusable_writeback_permitted(result.verdict, binds) is False


def test_positive_trusted_acquisition_path(tmp_path: Path) -> None:
    mem = CognitiveMemoryStore(tmp_path / "mem.sqlite")
    rec = persist_authorized(mem, SUPPORT, source_id="sensor")
    assert GRANT_PAYLOAD_KEY in rec.payload
    assert "authorized" not in rec.payload[GRANT_PAYLOAD_KEY]
    loaded = mem.get(rec.memory_id)
    assert loaded is not None
    task = _task(requested_evidence=[rec.memory_id])
    items = MemoryRetriever().retrieve(mem, task, now=NOW)
    assert any(i.memory_id == rec.memory_id for i in items)
    result, binds = _run(mem, tmp_path, task)
    assert any(b.may(ROLE_FACTUAL_PREMISE) for b in binds)
    assert any(b.support_strength == SUPPORT_DIRECT for b in binds)
    assert result.verdict in POSITIVE


def test_forged_and_modified_grant_fail(tmp_path: Path) -> None:
    mem = CognitiveMemoryStore(tmp_path / "mem.sqlite")
    rec = persist_authorized(mem, SUPPORT, source_id="g1")
    grant = dict(rec.payload[GRANT_PAYLOAD_KEY])
    forged = dict(grant)
    forged["mac"] = "00" * 32
    mem2 = CognitiveMemoryStore(tmp_path / "forged.sqlite")
    bad = mem2.remember(
        memory_type=MemoryType.EPISODIC,
        epistemic_kind=EpistemicKind.OBSERVED_FACT,
        statement=SUPPORT,
        source_type=SourceType.SYSTEM,
        source_id="g1",
        source_location="forged",
        producer="attacker",
        producer_version="t",
        domain="software",
        context="SYNTHETIC_TEST_DATA",
        observed_at=NOW - 20,
        created_at=NOW - 10,
        payload={"data_label": "SYNTHETIC_TEST_DATA", GRANT_PAYLOAD_KEY: forged},
    )
    _, binds = _run(mem2, tmp_path / "f", _task(requested_evidence=[bad.memory_id]))
    assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in binds)


def test_copied_grant_does_not_authorize_other_statement(tmp_path: Path) -> None:
    mem = CognitiveMemoryStore(tmp_path / "mem.sqlite")
    a = persist_authorized(mem, SUPPORT, source_id="a")
    grant = dict(a.payload[GRANT_PAYLOAD_KEY])
    copied = mem.remember(
        memory_type=MemoryType.EPISODIC,
        epistemic_kind=EpistemicKind.OBSERVED_FACT,
        statement=OTHER,
        source_type=SourceType.SYSTEM,
        source_id="a",
        source_location="copy",
        producer="attacker",
        producer_version="t",
        domain="software",
        context="SYNTHETIC_TEST_DATA",
        observed_at=NOW - 20,
        created_at=NOW - 10,
        payload={"data_label": "SYNTHETIC_TEST_DATA", GRANT_PAYLOAD_KEY: grant},
    )
    _, binds = _run(mem, tmp_path, _task(requested_evidence=[copied.memory_id]))
    target = next(b for b in binds if b.memory_id == copied.memory_id)
    assert target.may(ROLE_FACTUAL_PREMISE) is False


def test_replayed_grant_on_mutated_authority_fields(tmp_path: Path) -> None:
    mem = CognitiveMemoryStore(tmp_path / "mem.sqlite")
    rec = persist_authorized(mem, SUPPORT, source_id="src-a", domain="software")
    grant = rec.payload[GRANT_PAYLOAD_KEY]
    mutations = (
        {"source_id": "src-b"},
        {"source_type": SourceType.HUMAN.value},
        {"observed_at": NOW - 5},
        {"valid_until": NOW + 10_000},
        {"domain": "finance"},
    )
    for i, kw in enumerate(mutations):
        payload = {"data_label": "SYNTHETIC_TEST_DATA", GRANT_PAYLOAD_KEY: dict(grant)}
        extra = dict(
            memory_type=MemoryType.EPISODIC,
            epistemic_kind=EpistemicKind.OBSERVED_FACT,
            statement=SUPPORT,
            source_type=SourceType.SYSTEM,
            source_id="src-a",
            source_location="mut",
            producer="attacker",
            producer_version="t",
            domain="software",
            context="SYNTHETIC_TEST_DATA",
            observed_at=NOW - 20,
            created_at=NOW - 10,
            payload=payload,
        )
        extra.update(kw)
        row = mem.remember(**extra)
        _, binds = _run(
            mem, tmp_path / f"m{i}", _task(task_id=f"m{i}", requested_evidence=[row.memory_id])
        )
        assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in binds), kw


def test_new_authority_instance_cannot_mint_process_valid_grant(tmp_path: Path) -> None:
    other = ObservationAuthority()
    acq = AcquisitionRecord(
        statement=SUPPORT,
        source_type=SourceType.SYSTEM.value,
        source_id="x",
        observed_at=NOW - 20,
        domain="software",
    )
    alien = other._mint(acq)
    mem = CognitiveMemoryStore(tmp_path / "mem.sqlite")
    rec = mem.remember(
        memory_type=MemoryType.EPISODIC,
        epistemic_kind=EpistemicKind.OBSERVED_FACT,
        statement=SUPPORT,
        source_type=SourceType.SYSTEM,
        source_id="x",
        source_location="alien",
        producer="other-authority",
        producer_version="t",
        domain="software",
        context="SYNTHETIC_TEST_DATA",
        observed_at=NOW - 20,
        created_at=NOW - 10,
        payload={"data_label": "SYNTHETIC_TEST_DATA", GRANT_PAYLOAD_KEY: alien.to_dict()},
    )
    _, binds = _run(mem, tmp_path, _task(requested_evidence=[rec.memory_id]))
    assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in binds)


def test_revision_cannot_inherit_stale_authority(tmp_path: Path) -> None:
    mem = CognitiveMemoryStore(tmp_path / "mem.sqlite")
    rec = persist_authorized(mem, SUPPORT, source_id="rev")
    nxt = mem.revise(rec.memory_id, statement=OTHER, correction_reason="mutate", now=NOW)
    assert GRANT_PAYLOAD_KEY not in nxt.payload
    result, binds = _run(mem, tmp_path, _task(requested_evidence=[rec.memory_id]))
    assert nxt.epistemic_kind == EpistemicKind.OBSERVED_FACT.value
    assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in binds)
    assert result.verdict not in POSITIVE


def test_observation_field_mutations_break_mac(tmp_path: Path) -> None:
    mem = CognitiveMemoryStore(tmp_path / "mem.sqlite")
    rec = persist_authorized(mem, SUPPORT, source_id="mut", valid_until=NOW + 50_000)
    grant = rec.payload[GRANT_PAYLOAD_KEY]
    assert statement_sha256(SUPPORT) == grant["statement_sha256"]
    assert statement_sha256(SUPPORT + " extra") != grant["statement_sha256"]
    mem2 = CognitiveMemoryStore(tmp_path / "fresh.sqlite")
    good = persist_authorized(mem2, SUPPORT, source_id="mut2")
    loaded = mem2.get(good.memory_id)
    assert loaded is not None
    tampered = loaded
    tampered.statement = OTHER
    tampered.integrity_hash = compute_integrity_hash(tampered)
    conn = sqlite3.connect(str(mem2.path))
    conn.execute(
        "UPDATE memories SET statement=?, integrity_hash=? WHERE memory_id=?",
        (OTHER, tampered.integrity_hash, good.memory_id),
    )
    conn.commit()
    conn.close()
    result, binds = _run(mem2, tmp_path / "u", _task(requested_evidence=[good.memory_id]))
    assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in binds)
    assert result.verdict not in POSITIVE


def test_expired_and_future_observation_not_factual(tmp_path: Path) -> None:
    mem = CognitiveMemoryStore(tmp_path / "mem.sqlite")
    expired = persist_authorized(
        mem, SUPPORT, source_id="exp", valid_until=NOW - 10
    )
    future = persist_authorized(
        mem, SUPPORT, source_id="fut", observed_at=NOW + 5_000
    )
    _, b1 = _run(mem, tmp_path / "e", _task(task_id="e", requested_evidence=[expired.memory_id]))
    _, b2 = _run(mem, tmp_path / "f", _task(task_id="f", requested_evidence=[future.memory_id]))
    assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in b1)
    assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in b2)


def test_timezone_canonical_equivalence() -> None:
    utc = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    offset = datetime(2026, 1, 1, 16, 0, tzinfo=timezone(timedelta(hours=4)))
    a = canonical_observation_bytes(
        statement="  café  ",
        source_type="SYSTEM",
        source_id="s",
        observed_at=utc.timestamp(),
        valid_until=None,
        domain="software",
    )
    b = canonical_observation_bytes(
        statement="café",
        source_type="SYSTEM",
        source_id="s",
        observed_at=offset.timestamp(),
        valid_until=None,
        domain="software",
    )
    assert a == b
    c = canonical_observation_bytes(
        statement="café",
        source_type="SYSTEM",
        source_id="s",
        observed_at=utc.timestamp() + 1,
        valid_until=None,
        domain="software",
    )
    assert a != c


def test_unicode_nfc_canonical() -> None:
    composed = "café"
    decomposed = "cafe\u0301"
    assert statement_sha256(composed) == statement_sha256(decomposed)


def test_generic_ingestion_cannot_mint_factual(tmp_path: Path) -> None:
    mem = CognitiveMemoryStore(tmp_path / "mem.sqlite")
    mid = ingest_generic_observation(
        mem,
        domain="software",
        statement=SUPPORT,
        source_id="gen",
        observed_at=NOW - 20,
        created_at=NOW - 10,
    )
    rec = mem.get(mid)
    assert rec is not None
    assert rec.epistemic_kind != EpistemicKind.OBSERVED_FACT.value
    with pytest.raises(ValueError):
        ingest_generic_observation(
            mem,
            domain="software",
            statement=SUPPORT,
            source_id="gen2",
            observed_at=NOW - 20,
            created_at=NOW - 10,
            kind=EpistemicKind.OBSERVED_FACT,
        )
    finance_observation(
        mem,
        statement=SUPPORT,
        source_id="fin",
        observed_at=NOW - 20,
        created_at=NOW - 10,
    )
    _, binds = _run(mem, tmp_path, _task(requested_evidence=[mid]))
    assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in binds)


def test_world_model_cannot_mint_observed_fact(tmp_path: Path) -> None:
    mem = CognitiveMemoryStore(tmp_path / "mem.sqlite")
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
    with pytest.raises(ValueError):
        mem.record_world_model_object(
            object_kind="ENTITY",
            statement=SUPPORT,
            epistemic_kind=EpistemicKind.OBSERVED_FACT,
            source_type=SourceType.SYSTEM,
            source_id="wm2",
            source_location="wm",
            producer="t",
            producer_version="t",
            domain="software",
            context="SYNTHETIC_TEST_DATA",
        )


def test_direct_sqlite_insert_is_not_factual(tmp_path: Path) -> None:
    mem = CognitiveMemoryStore(tmp_path / "mem.sqlite")
    rec = MemoryRecord(
        memory_id="SQL-FORGE",
        revision=1,
        memory_type=MemoryType.EPISODIC.value,
        epistemic_kind=EpistemicKind.OBSERVED_FACT.value,
        statement=SUPPORT,
        created_at=NOW - 10,
        observed_at=NOW - 20,
        source_type=SourceType.SYSTEM.value,
        source_id="sqlite",
        source_location="direct-insert",
        producer="attacker",
        producer_version="t",
        domain="software",
        context="SYNTHETIC_TEST_DATA",
        confidence=None,
        valid_from=None,
        valid_until=None,
        status=DecayState.ACTIVE.value,
        contradiction_state=ContradictionState.UNCONTESTED.value,
        integrity_hash="",
        payload={"data_label": "SYNTHETIC_TEST_DATA"},
    )
    _insert_row(mem, rec)
    loaded = mem.get("SQL-FORGE")
    assert loaded is not None
    assert loaded.epistemic_kind == EpistemicKind.OBSERVED_FACT.value
    result, binds = _run(mem, tmp_path, _task(requested_evidence=["SQL-FORGE"]))
    assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in binds)
    assert result.verdict not in POSITIVE


def test_direct_sqlite_delete_reinsert_without_grant(tmp_path: Path) -> None:
    mem = CognitiveMemoryStore(tmp_path / "mem.sqlite")
    rec = persist_authorized(mem, SUPPORT, source_id="del")
    mid = rec.memory_id
    conn = sqlite3.connect(str(mem.path))
    conn.execute("DELETE FROM memories WHERE memory_id=?", (mid,))
    conn.commit()
    conn.close()
    clone = MemoryRecord(
        memory_id=mid,
        revision=1,
        memory_type=MemoryType.EPISODIC.value,
        epistemic_kind=EpistemicKind.OBSERVED_FACT.value,
        statement=SUPPORT,
        created_at=NOW - 10,
        observed_at=NOW - 20,
        source_type=SourceType.SYSTEM.value,
        source_id="del",
        source_location="reinsert",
        producer="attacker",
        producer_version="t",
        domain="software",
        context="SYNTHETIC_TEST_DATA",
        confidence=None,
        valid_from=None,
        valid_until=None,
        status=DecayState.ACTIVE.value,
        contradiction_state=ContradictionState.UNCONTESTED.value,
        integrity_hash="",
        payload={"data_label": "SYNTHETIC_TEST_DATA"},
    )
    _insert_row(mem, clone)
    _, binds = _run(mem, tmp_path, _task(requested_evidence=[mid]))
    assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in binds)


def test_derived_fact_cannot_use_observation_grant(tmp_path: Path) -> None:
    mem = CognitiveMemoryStore(tmp_path / "mem.sqlite")
    authorized = persist_authorized(mem, SUPPORT, source_id="df")
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
    _, binds = _run(mem, tmp_path, _task(requested_evidence=[derived.memory_id]))
    target = next(b for b in binds if b.memory_id == derived.memory_id)
    assert target.live_typed_class() == "DERIVED_FACT"
    assert target.may(ROLE_FACTUAL_PREMISE) is False
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
    )


@pytest.mark.parametrize(
    "kind,mtype",
    [
        (EpistemicKind.HYPOTHESIS, MemoryType.HYPOTHESIS),
        (EpistemicKind.LESSON, MemoryType.SEMANTIC),
        (EpistemicKind.INFERENCE, MemoryType.SEMANTIC),
        (EpistemicKind.INFERENCE, MemoryType.EPISODIC),
        (EpistemicKind.PREDICTION, MemoryType.SEMANTIC),
        (EpistemicKind.OPINION, MemoryType.SEMANTIC),
        (EpistemicKind.SIMULATION, MemoryType.SEMANTIC),
    ],
)
def test_non_fact_kinds_cannot_become_factual_via_grant(
    tmp_path: Path, kind: EpistemicKind, mtype: MemoryType
) -> None:
    mem = CognitiveMemoryStore(tmp_path / "mem.sqlite")
    authorized = persist_authorized(mem, SUPPORT, source_id="nf")
    grant = authorized.payload[GRANT_PAYLOAD_KEY]
    rec = mem.remember(
        memory_type=mtype,
        epistemic_kind=kind,
        statement=f"{kind.value} {SUPPORT}",
        source_type=SourceType.SYSTEM,
        source_id=f"k-{kind.value}-{mtype.value}",
        source_location="kind",
        producer="t",
        producer_version="t",
        domain="software",
        context="SYNTHETIC_TEST_DATA",
        observed_at=NOW - 20,
        created_at=NOW - 10,
        prediction_id="PRED-1" if kind == EpistemicKind.PREDICTION else "",
        payload={"data_label": "SYNTHETIC_TEST_DATA", GRANT_PAYLOAD_KEY: dict(grant)},
    )
    _, binds = _run(
        mem, tmp_path / kind.value, _task(task_id=kind.value, requested_evidence=[rec.memory_id])
    )
    assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in binds)


def test_stale_and_unknown_not_factual(tmp_path: Path) -> None:
    mem = CognitiveMemoryStore(tmp_path / "mem.sqlite")
    rec = persist_authorized(mem, SUPPORT, source_id="st")
    mem.revise(rec.memory_id, status=DecayState.STALE, correction_reason="stale", now=NOW)
    _, binds = _run(mem, tmp_path, _task(requested_evidence=[rec.memory_id]))
    assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in binds)


def test_serialized_grant_without_secret_is_not_authority(tmp_path: Path) -> None:
    mem = CognitiveMemoryStore(tmp_path / "mem.sqlite")
    rec = persist_authorized(mem, SUPPORT, source_id="ser")
    blob = json.dumps(rec.as_dict())
    assert "mac" in blob
    restored = json.loads(blob)
    assert GRANT_PAYLOAD_KEY not in str(restored.get("integrity_hash"))
    clone = mem.remember(
        memory_type=MemoryType.EPISODIC,
        epistemic_kind=EpistemicKind.OBSERVED_FACT,
        statement=SUPPORT + " copy",
        source_type=SourceType.SYSTEM,
        source_id="ser2",
        source_location="ser",
        producer="t",
        producer_version="t",
        domain="software",
        context="SYNTHETIC_TEST_DATA",
        observed_at=NOW - 20,
        created_at=NOW - 10,
        payload=dict(restored["payload"]),
    )
    _, binds = _run(mem, tmp_path, _task(requested_evidence=[clone.memory_id]))
    target = next(b for b in binds if b.memory_id == clone.memory_id)
    assert target.may(ROLE_FACTUAL_PREMISE) is False


def test_toctou_revise_after_grant_latest_hash_wins(tmp_path: Path) -> None:
    mem = CognitiveMemoryStore(tmp_path / "mem.sqlite")
    rec = persist_authorized(mem, SUPPORT, source_id="toc")
    items = MemoryRetriever().retrieve(mem, _task(requested_evidence=[rec.memory_id]), now=NOW)
    mem.revise(rec.memory_id, statement=OTHER, correction_reason="toctou", now=NOW + 1)
    task = _task(requested_evidence=[rec.memory_id])
    from architecture.cognitive.loop.context import assemble_context

    ctx = assemble_context(items, mem, now=NOW + 2)
    binds = bind_context(ctx, task, store=mem)
    assert binds
    assert all(not b.may(ROLE_FACTUAL_PREMISE) for b in binds)


def test_entity_scope_still_live_after_grant(tmp_path: Path) -> None:
    mem = CognitiveMemoryStore(tmp_path / "mem.sqlite")
    rec = persist_authorized(
        mem,
        "Service A retries after timeout reduced failures.",
        source_id="ent",
    )
    task = _task(question="Do Service B retries after timeout reduce failures?")
    result, binds = _run(mem, tmp_path, task)
    assert result.verdict not in POSITIVE
    if binds:
        assert all(not (b.may(ROLE_FACTUAL_PREMISE) and b.may_support_task()) for b in binds)
