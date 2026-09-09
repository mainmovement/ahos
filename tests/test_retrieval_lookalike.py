"""P4.3 lookalike discrimination: similarity is not applicability."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from architecture.cognitive.benchmark.corpus import seed_corpus  # noqa: E402
from architecture.cognitive.loop.contracts import CognitiveTask, TaskType  # noqa: E402
from architecture.cognitive.loop.retrieval import MemoryRetriever  # noqa: E402
from architecture.cognitive.memory.store import CognitiveMemoryStore  # noqa: E402
from architecture.cognitive.memory.types import EpistemicKind, MemoryType, SourceType  # noqa: E402

NOW = 1_800_000_000.0


def _store(tmp_path: Path) -> CognitiveMemoryStore:
    store = CognitiveMemoryStore(tmp_path / "ahos_cognitive_memory.sqlite")
    seed_corpus(store, now=NOW)
    return store


def _task(**kwargs) -> CognitiveTask:
    base = dict(
        task_id="t",
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


def _remember(store: CognitiveMemoryStore, **kwargs) -> str:
    rec = store.remember(
        memory_type=kwargs.get("memory_type", MemoryType.EPISODIC),
        epistemic_kind=kwargs.get("epistemic_kind", EpistemicKind.OBSERVED_FACT),
        statement=kwargs["statement"],
        source_type=SourceType.SYSTEM,
        source_id=kwargs.get("source_id", "p43-test"),
        source_location="tests.test_retrieval_lookalike",
        producer="p4.3-tests",
        producer_version="p4.3.0",
        domain=kwargs.get("domain", "software"),
        context="SYNTHETIC_TEST_DATA",
        created_at=NOW - 10,
        observed_at=NOW - 20,
        memory_id=kwargs.get("memory_id"),
        payload=kwargs.get("payload") or {"data_label": "SYNTHETIC_TEST_DATA"},
    )
    return rec.memory_id


def test_same_domain_generic_words_different_task(tmp_path: Path) -> None:
    store = _store(tmp_path)
    items = MemoryRetriever().retrieve(
        store,
        _task(
            task_type=TaskType.LEARN.value,
            question="What lesson applies after HTTP timeout retries?",
            objective="lesson retrieval",
        ),
        now=NOW,
    )
    ids = {i.memory_id for i in items}
    assert "BM-SW-TIMEOUT-LESSON" in ids
    assert "BM-SW-COMPILE-DIST" not in ids
    assert "BM-SW-TIMEOUT-LOOKALIKE" not in ids


def test_same_operation_same_component_is_relevant(tmp_path: Path) -> None:
    store = _store(tmp_path)
    mid = _remember(
        store,
        memory_id="P43-HTTP-CLIENT",
        statement="SYNTHETIC_TEST_DATA: http_client timeout retry recovered the socket.",
        payload={
            "data_label": "SYNTHETIC_TEST_DATA",
            "component": "http_client",
            "operation": "retry",
        },
    )
    items = MemoryRetriever().retrieve(
        store,
        _task(
            question="http_client timeout retry recovered",
            objective="http client retry",
            constraints={"component": "http_client", "operation": "retry"},
        ),
        now=NOW,
    )
    assert mid in {i.memory_id for i in items}


def test_explicit_component_mismatch_rejected(tmp_path: Path) -> None:
    store = _store(tmp_path)
    explained = MemoryRetriever().retrieve_explained(
        store,
        _task(
            question="prior timeout retry failure",
            objective="failure memory",
            constraints={"component": "database", "failure_type": "disk_full"},
        ),
        now=NOW,
    )
    ids = {i.memory_id for i in explained.items}
    assert "BM-SW-TIMEOUT-FAIL" not in ids
    assert any(r.reason.startswith("HARD_MISMATCH") for r in explained.rejected)


def test_missing_component_is_not_mismatch(tmp_path: Path) -> None:
    store = _store(tmp_path)
    items = MemoryRetriever().retrieve(
        store,
        _task(
            question="prior timeout retry failure",
            objective="failure memory",
            constraints={"component": "http_client"},
        ),
        now=NOW,
    )
    # TIMEOUT-FAIL has component=http_client (match). FACT has no component (neutral).
    ids = {i.memory_id for i in items}
    assert "BM-SW-TIMEOUT-FAIL" in ids


def test_same_failure_class_different_fingerprint_not_automatic(tmp_path: Path) -> None:
    store = _store(tmp_path)
    items = MemoryRetriever().retrieve(
        store,
        _task(
            domain="operations",
            question="deploy checklist rollback missing",
            objective="ops deploy failure",
        ),
        now=NOW,
    )
    ids = {i.memory_id for i in items}
    assert "BM-OPS-FAIL" in ids
    assert "BM-SW-TIMEOUT-FAIL" not in ids


def test_same_failure_fingerprint_different_wording(tmp_path: Path) -> None:
    store = _store(tmp_path)
    items = MemoryRetriever().retrieve(
        store,
        _task(question="HTTP client timeout_retry failed without retries", objective="timeout failure"),
        now=NOW,
    )
    ids = {i.memory_id for i in items}
    assert "BM-SW-TIMEOUT-FAIL" in ids


def test_lesson_domain_not_applicability(tmp_path: Path) -> None:
    store = _store(tmp_path)
    items = MemoryRetriever().retrieve(
        store,
        _task(
            task_type=TaskType.LEARN.value,
            question="What did we learn about timeout retries?",
            objective="lesson retrieval",
        ),
        now=NOW,
    )
    ids = {i.memory_id for i in items}
    assert "BM-SW-TIMEOUT-LESSON" in ids
    assert "BM-SW-TIMEOUT-FACT" not in ids
    assert all(i.epistemic_kind == "LESSON" for i in items)


def test_generic_two_token_cross_domain_insufficient(tmp_path: Path) -> None:
    store = _store(tmp_path)
    explained = MemoryRetriever().retrieve_explained(
        store,
        _task(question="HTTP timeout retries recovered", objective="timeout retries"),
        now=NOW,
    )
    ids = {i.memory_id for i in explained.items}
    assert "BM-SW-TIMEOUT-FACT" in ids
    assert "BM-FIN-FACT" not in ids
    assert "BM-SCI-FACT" not in ids
    assert "BM-OPS-FACT" not in ids
    assert any(r.reason == "CROSS_DOMAIN_GENERIC_OVERLAP" for r in explained.rejected)


def test_discriminative_two_token_still_possible(tmp_path: Path) -> None:
    store = _store(tmp_path)
    items = MemoryRetriever().retrieve(
        store,
        _task(question="telescope pointing error arcsec", objective="pointing error", domain="science"),
        now=NOW,
    )
    assert "BM-SCI-DIST" in {i.memory_id for i in items}


def test_relevant_contradiction_still_expanded(tmp_path: Path) -> None:
    store = _store(tmp_path)
    items = MemoryRetriever().retrieve(
        store,
        _task(question="Did condition X occur on node seven?", objective="condition X node seven"),
        now=NOW,
    )
    ids = {i.memory_id for i in items}
    assert "BM-SW-CONTRA-A" in ids
    assert "BM-SW-CONTRA-B" in ids


def test_unrelated_contradiction_not_retrieved(tmp_path: Path) -> None:
    store = _store(tmp_path)
    items = MemoryRetriever().retrieve(
        store,
        _task(
            domain="operations",
            question="badge reader firmware version",
            objective="badge firmware",
        ),
        now=NOW,
    )
    ids = {i.memory_id for i in items}
    assert "BM-SW-CONTRA-A" not in ids
    assert "BM-SCI-CONTRA-A" not in ids


def test_empty_query_no_relevant_memory(tmp_path: Path) -> None:
    store = _store(tmp_path)
    explained = MemoryRetriever().retrieve_explained(
        store,
        _task(question="??", objective="...", domain="general"),
        now=NOW,
    )
    assert explained.no_relevant_memory is True
    assert explained.items == []


def test_exact_id_preserved(tmp_path: Path) -> None:
    store = _store(tmp_path)
    items = MemoryRetriever().retrieve(
        store,
        _task(
            question="retrieve memory BM-SW-TIMEOUT-FACT",
            objective="exact id",
            requested_evidence=["BM-SW-TIMEOUT-FACT"],
        ),
        now=NOW,
    )
    assert items
    assert items[0].memory_id == "BM-SW-TIMEOUT-FACT"
    assert "exact_id" in items[0].match_reasons


def test_namespace_isolation_100(tmp_path: Path) -> None:
    store = _store(tmp_path)
    ids = {
        i.memory_id
        for i in MemoryRetriever().retrieve(
            store,
            _task(
                question="private A note about timeout retries",
                objective="private A timeout",
                agent_id="agent_A",
            ),
            now=NOW,
        )
    }
    assert "BM-A-PRIV" in ids
    assert "BM-B-PRIV" not in ids
    assert "BM-SW-TIMEOUT-FACT" not in ids


def test_unscoped_query_does_not_see_private_notes(tmp_path: Path) -> None:
    store = _store(tmp_path)
    ids = {
        i.memory_id
        for i in MemoryRetriever().retrieve(
            store,
            _task(question="HTTP timeout retries recovered", objective="timeout retries"),
            now=NOW,
        )
    }
    assert "BM-A-PRIV" not in ids
    assert "BM-B-PRIV" not in ids


def test_stale_historical_still_queryable(tmp_path: Path) -> None:
    store = _store(tmp_path)
    items = MemoryRetriever().retrieve(
        store,
        _task(question="historical timeout rate last quarter", objective="historical timeout rate"),
        now=NOW,
    )
    stale = next(i for i in items if i.memory_id == "BM-SW-OLD-FACT")
    assert "stale_but_queryable" in stale.match_reasons


def test_superseded_preserved(tmp_path: Path) -> None:
    store = _store(tmp_path)
    items = MemoryRetriever().retrieve(
        store,
        _task(
            question="Is service X still on revision 1 historical superseded?",
            objective="superseded revision history",
        ),
        now=NOW,
    )
    assert "BM-SW-SUPERSEDED-OLD" in {i.memory_id for i in items}


def test_lookalike_poster_rejected(tmp_path: Path) -> None:
    store = _store(tmp_path)
    explained = MemoryRetriever().retrieve_explained(
        store,
        _task(question="HTTP timeout retries recovered", objective="timeout retries"),
        now=NOW,
    )
    assert "BM-SW-TIMEOUT-LOOKALIKE" not in {i.memory_id for i in explained.items}
    assert any(
        r.memory_id == "BM-SW-TIMEOUT-LOOKALIKE" and r.reason == "GENERIC_LOOKALIKE"
        for r in explained.rejected
    )


def test_hard_mismatch_does_not_treat_unknown_as_conflict(tmp_path: Path) -> None:
    store = _store(tmp_path)
    mid = _remember(
        store,
        memory_id="P43-UNKNOWN-COMP",
        statement="SYNTHETIC_TEST_DATA: timeout retry recovered after backoff.",
        payload={"data_label": "SYNTHETIC_TEST_DATA", "component": "UNKNOWN"},
    )
    items = MemoryRetriever().retrieve(
        store,
        _task(
            question="timeout retry recovered after backoff",
            objective="timeout retry",
            constraints={"component": "http_client"},
        ),
        now=NOW,
    )
    assert mid in {i.memory_id for i in items}
