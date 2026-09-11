"""Thin domain adapters. Cognitive core stays domain-general."""

from __future__ import annotations

from typing import Any

from architecture.cognitive.memory.store import CognitiveMemoryStore
from architecture.cognitive.memory.types import EpistemicKind, MemoryType, SourceType

SYNTHETIC = "SYNTHETIC_TEST_DATA"


def ingest_generic_observation(
    store: CognitiveMemoryStore,
    *,
    domain: str,
    statement: str,
    source_id: str,
    observed_at: float,
    created_at: float,
    kind: EpistemicKind | str = EpistemicKind.INFERENCE,
    extra: dict[str, Any] | None = None,
) -> str:
    resolved = EpistemicKind(kind).value
    if resolved == EpistemicKind.OBSERVED_FACT.value:
        raise ValueError(
            "ingest_generic_observation cannot mint OBSERVED_FACT"
        )
    payload = {"data_label": SYNTHETIC, **(extra or {})}
    rec = store.remember(
        memory_type=MemoryType.EPISODIC,
        epistemic_kind=resolved,
        statement=statement,
        source_type=SourceType.SYSTEM,
        source_id=source_id,
        source_location="architecture.cognitive.loop.adapters",
        producer="test-adapter",
        producer_version="p3-v1",
        domain=domain,
        context=SYNTHETIC,
        observed_at=observed_at,
        created_at=created_at,
        payload=payload,
    )
    return rec.memory_id


def finance_observation(store: CognitiveMemoryStore, **kwargs: Any) -> str:
    return ingest_generic_observation(store, domain="finance", **kwargs)


def science_observation(store: CognitiveMemoryStore, **kwargs: Any) -> str:
    return ingest_generic_observation(store, domain="science", **kwargs)


def software_observation(store: CognitiveMemoryStore, **kwargs: Any) -> str:
    return ingest_generic_observation(store, domain="software", **kwargs)


def operations_observation(store: CognitiveMemoryStore, **kwargs: Any) -> str:
    return ingest_generic_observation(store, domain="operations", **kwargs)
