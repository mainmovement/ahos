"""P5 test helpers using tests-only grant authority. Not a production API."""

from __future__ import annotations

import tempfile
from pathlib import Path

from architecture.cognitive.loop.contracts import RetrievedItem
from architecture.cognitive.memory.store import CognitiveMemoryStore
from architecture.cognitive.memory.types import DecayState, EpistemicKind, MemoryType, SourceType
from tests.observation_test_runtime import (
    NOW,
    persist_test_observation,
    test_authority_scope,
    timeout_retry_reading,
)


def ephemeral_store() -> CognitiveMemoryStore:
    return CognitiveMemoryStore(Path(tempfile.mkdtemp()) / "og.sqlite")


def persist_authorized(
    store: CognitiveMemoryStore,
    statement: str,
    *,
    source_id: str = "pytest",
    source_type: str = SourceType.SYSTEM.value,
    observed_at: float = NOW - 20,
    domain: str = "software",
    valid_until: float | None = None,
    memory_id: str | None = None,
    created_at: float | None = NOW - 10,
    payload: dict | None = None,
    status: str | None = None,
    agent_id: str = "",
    agent_namespace: str = "",
):
    del source_type
    return persist_test_observation(
        store,
        timeout_retry_reading(
            statement,
            sensor_id=source_id,
            acquired_at=observed_at,
            domain=domain,
            valid_until=valid_until,
            memory_id=memory_id,
            created_at=created_at,
            status=status,
            agent_id=agent_id,
            agent_namespace=agent_namespace,
            payload=payload,
        ),
    )


def authorize_retrieved_items(
    *items: RetrievedItem, store: CognitiveMemoryStore | None = None
) -> CognitiveMemoryStore:
    mem = store or ephemeral_store()
    for item in items:
        if mem.get(item.memory_id) is not None:
            continue
        if (
            item.epistemic_kind == EpistemicKind.OBSERVED_FACT.value
            and item.memory_type != MemoryType.FAILURE.value
            and item.observed_at is not None
        ):
            persist_authorized(
                mem,
                item.statement,
                source_id=item.source_id or "pytest",
                observed_at=float(item.observed_at),
                domain=item.domain,
                memory_id=item.memory_id,
                created_at=item.created_at,
                status=item.status,
            )
        else:
            mem.remember(
                memory_id=item.memory_id,
                memory_type=item.memory_type,
                epistemic_kind=item.epistemic_kind,
                statement=item.statement,
                source_type=SourceType.SYSTEM,
                source_id=item.source_id or "pytest",
                source_location="tests/p5_grant_fixtures.py",
                producer="pytest",
                producer_version="p5",
                domain=item.domain or "software",
                context="SYNTHETIC_TEST_DATA",
                observed_at=item.observed_at,
                created_at=item.created_at,
                payload={"data_label": "SYNTHETIC_TEST_DATA"},
            )
            if item.status and item.status != DecayState.ACTIVE.value:
                mem.revise(
                    item.memory_id,
                    status=item.status,
                    correction_reason="fixture-status",
                    now=NOW,
                )
    return mem
