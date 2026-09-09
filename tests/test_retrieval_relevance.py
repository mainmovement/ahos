"""P4.2 retrieval relevance: contextual signals are not relevance by themselves."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from architecture.cognitive.benchmark.corpus import seed_corpus  # noqa: E402
from architecture.cognitive.loop.contracts import CognitiveTask, TaskType  # noqa: E402
from architecture.cognitive.loop.retrieval import MemoryRetriever, normalize_query  # noqa: E402
from architecture.cognitive.memory.store import CognitiveMemoryStore  # noqa: E402

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


def test_same_domain_is_not_relevance(tmp_path: Path) -> None:
    store = _store(tmp_path)
    items = MemoryRetriever().retrieve(
        store,
        _task(question="HTTP timeout retries recovered", objective="timeout retries"),
        now=NOW,
    )
    ids = {i.memory_id for i in items}
    assert "BM-SW-TIMEOUT-FACT" in ids
    assert "BM-SW-COMPILE-DIST" not in ids
    assert "BM-SW-LINT-DIST" not in ids


def test_unrelated_failure_not_retrieved(tmp_path: Path) -> None:
    store = _store(tmp_path)
    items = MemoryRetriever().retrieve(
        store,
        _task(
            domain="science",
            question="telescope pointing error arcsec",
            objective="science experiment uncertainty",
        ),
        now=NOW,
    )
    ids = {i.memory_id for i in items}
    assert "BM-SW-TIMEOUT-FAIL" not in ids
    assert "BM-OPS-FAIL" not in ids
    assert "BM-SCI-DIST" in ids


def test_unrelated_contradiction_not_polluting(tmp_path: Path) -> None:
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
    assert "BM-SW-CONTRA-B" not in ids
    assert "BM-SCI-CONTRA-A" not in ids


def test_empty_query_returns_no_relevant_memory(tmp_path: Path) -> None:
    store = _store(tmp_path)
    explained = MemoryRetriever().retrieve_explained(
        store,
        _task(question="??", objective="...", domain="general"),
        now=NOW,
    )
    assert explained.no_relevant_memory is True
    assert explained.items == []
    assert any(r.reason == "NO_QUERY_SIGNAL" for r in explained.rejected)


def test_domain_only_query_does_not_flood(tmp_path: Path) -> None:
    store = _store(tmp_path)
    items = MemoryRetriever().retrieve(
        store,
        _task(question="software", objective="software", domain="software"),
        now=NOW,
    )
    assert items == []


def test_relevant_failure_still_retrieved(tmp_path: Path) -> None:
    store = _store(tmp_path)
    items = MemoryRetriever().retrieve(
        store,
        _task(question="prior timeout retry failure", objective="timeout failure"),
        now=NOW,
    )
    ids = {i.memory_id for i in items}
    assert "BM-SW-TIMEOUT-FAIL" in ids
    assert any(
        "failure_fingerprint" in i.match_reasons or "task_keyword_match" in i.match_reasons
        for i in items
        if i.memory_id == "BM-SW-TIMEOUT-FAIL"
    )


def test_relevant_contradiction_expanded_from_anchor(tmp_path: Path) -> None:
    store = _store(tmp_path)
    items = MemoryRetriever().retrieve(
        store,
        _task(
            question="Did condition X occur on node seven?",
            objective="condition X node seven",
        ),
        now=NOW,
    )
    ids = {i.memory_id for i in items}
    assert "BM-SW-CONTRA-A" in ids
    assert "BM-SW-CONTRA-B" in ids


def test_namespace_boundary_preserved(tmp_path: Path) -> None:
    store = _store(tmp_path)
    ids_a = {
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
    assert "BM-A-PRIV" in ids_a
    assert "BM-B-PRIV" not in ids_a


def test_exact_id_remains_reliable(tmp_path: Path) -> None:
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


def test_historical_stale_still_queryable(tmp_path: Path) -> None:
    store = _store(tmp_path)
    items = MemoryRetriever().retrieve(
        store,
        _task(
            question="historical timeout rate last quarter",
            objective="historical timeout rate",
        ),
        now=NOW,
    )
    ids = {i.memory_id for i in items}
    assert "BM-SW-OLD-FACT" in ids
    stale = next(i for i in items if i.memory_id == "BM-SW-OLD-FACT")
    assert "stale_but_queryable" in stale.match_reasons


def test_same_failure_category_different_component(tmp_path: Path) -> None:
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


def test_synonym_like_timeout_wording_still_hits(tmp_path: Path) -> None:
    store = _store(tmp_path)
    items = MemoryRetriever().retrieve(
        store,
        _task(question="HTTP timeout recovered after retries", objective="timeout recovery"),
        now=NOW,
    )
    ids = {i.memory_id for i in items}
    assert "BM-SW-TIMEOUT-FACT" in ids
    assert "BM-SW-TIMEOUT-LESSON" in ids


def test_query_normalization_is_deterministic() -> None:
    a = normalize_query(_task(question="Timeout Retries!", objective="TIMEOUT retries"))
    b = normalize_query(_task(question="timeout retries", objective="timeout retries"))
    assert a.tokens == b.tokens
    assert a.fingerprint == b.fingerprint


def test_single_token_cross_domain_is_not_an_anchor(tmp_path: Path) -> None:
    store = _store(tmp_path)
    explained = MemoryRetriever().retrieve_explained(
        store,
        _task(question="retries only", objective="retries", domain="software"),
        now=NOW,
    )
    ids = {i.memory_id for i in explained.items}
    assert "BM-SCI-FACT" not in ids
    assert "BM-FIN-FACT" not in ids
    assert "BM-OPS-FACT" not in ids
    assert any(r.reason == "WEAK_LEXICAL_OVERLAP" for r in explained.rejected)


def test_relevant_lesson_synonym_wording(tmp_path: Path) -> None:
    store = _store(tmp_path)
    items = MemoryRetriever().retrieve(
        store,
        _task(question="What lesson applies after HTTP timeout retries?", objective="lesson"),
        now=NOW,
    )
    ids = {i.memory_id for i in items}
    assert "BM-SW-TIMEOUT-LESSON" in ids
    lesson = next(i for i in items if i.memory_id == "BM-SW-TIMEOUT-LESSON")
    assert "lesson_keyword_match" in lesson.match_reasons


def test_unrelated_lesson_same_domain_excluded(tmp_path: Path) -> None:
    store = _store(tmp_path)
    items = MemoryRetriever().retrieve(
        store,
        _task(question="compiler unused import warning", objective="compiler warning"),
        now=NOW,
    )
    ids = {i.memory_id for i in items}
    assert "BM-SW-COMPILE-DIST" in ids
    assert "BM-SW-TIMEOUT-LESSON" not in ids


def test_adversarial_contradiction_edge_without_query_anchor(tmp_path: Path) -> None:
    store = _store(tmp_path)
    items = MemoryRetriever().retrieve(
        store,
        _task(
            domain="finance",
            question="unrelated liquidity note different pair",
            objective="liquidity pair",
        ),
        now=NOW,
    )
    ids = {i.memory_id for i in items}
    assert "BM-FIN-DIST" in ids
    assert "BM-SW-CONTRA-A" not in ids
    assert "BM-SCI-CONTRA-A" not in ids


def test_stale_current_query_does_not_hide_history(tmp_path: Path) -> None:
    store = _store(tmp_path)
    items = MemoryRetriever().retrieve(
        store,
        _task(question="current timeout rate this hour", objective="fresh timeout rate"),
        now=NOW,
    )
    ids = {i.memory_id for i in items}
    assert "BM-SW-FRESH-FACT" in ids
    assert "BM-SW-OLD-FACT" in ids


def test_superseded_historical_query_still_retrieves(tmp_path: Path) -> None:
    store = _store(tmp_path)
    items = MemoryRetriever().retrieve(
        store,
        _task(
            question="Is service X still on revision 1 historical superseded?",
            objective="superseded revision history",
        ),
        now=NOW,
    )
    ids = {i.memory_id for i in items}
    assert "BM-SW-SUPERSEDED-OLD" in ids


def test_unknown_age_memory_is_not_promoted_by_domain(tmp_path: Path) -> None:
    store = _store(tmp_path)
    items = MemoryRetriever().retrieve(
        store,
        _task(question="software", objective="software", domain="software"),
        now=NOW,
    )
    assert "BM-SW-UNKNOWN-AGE" not in {i.memory_id for i in items}


def test_provenance_survives_filtering(tmp_path: Path) -> None:
    store = _store(tmp_path)
    items = MemoryRetriever().retrieve(
        store,
        _task(question="HTTP timeout retries recovered", objective="timeout retries"),
        now=NOW,
    )
    assert items
    rec = store.get(items[0].memory_id)
    assert rec is not None
    assert rec.producer
    assert rec.source_id
    assert items[0].source_id == rec.source_id
    assert items[0].domain == rec.domain


def test_common_in_domain_token_does_not_pull_contradictions(tmp_path: Path) -> None:
    store = _store(tmp_path)
    items = MemoryRetriever().retrieve(
        store,
        _task(
            domain="science",
            question="Do calibration retries recover the measurement?",
            objective="calibration retries",
        ),
        now=NOW,
    )
    ids = {i.memory_id for i in items}
    assert "BM-SCI-FACT" in ids
    assert "BM-SCI-CONTRA-A" not in ids
    assert "BM-SCI-CONTRA-B" not in ids


def test_empty_result_is_no_relevant_memory_contract(tmp_path: Path) -> None:
    store = _store(tmp_path)
    explained = MemoryRetriever().retrieve_explained(
        store,
        _task(
            question="melting point of unobtainium-xyzzy",
            objective="no evidence",
            domain="general",
        ),
        now=NOW,
    )
    assert explained.no_relevant_memory is True
    assert explained.accepted_count == 0
    assert explained.items == []
