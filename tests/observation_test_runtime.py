"""Tests-only ObservationGrant authority. Not imported by architecture/.

Typed fake sensor readings are mapped by the adapter. This module never uses
production orchestrator verify secrets.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

from architecture.cognitive.loop.contracts import RetrievedItem
from architecture.cognitive.memory.observation import (
    ISSUER_ID_TEST,
    AcquisitionRecord,
    BoundIngestPort,
    GrantVerifyContext,
    ObservationAuthority,
    is_forbidden_production_secret,
    push_grant_verify_context,
    reset_grant_verify_context,
    verify_observation_grant,
)
from architecture.cognitive.memory.store import CognitiveMemoryStore
from architecture.cognitive.memory.types import DecayState, EpistemicKind, MemoryType, SourceType

NOW = 1_800_000_000.0
TEST_VECTOR_KEY = bytes.fromhex("a1" * 32)

if not is_forbidden_production_secret(TEST_VECTOR_KEY):
    raise RuntimeError("TEST_VECTOR_KEY must remain on the production denylist")


@dataclass(frozen=True)
class TypedFakeAcquisitionResult:
    """Fake sensor acquisition. Adapter builds the canonical observation."""

    sensor_channel: str
    raw_reading: str
    acquired_at: float
    sensor_id: str
    domain: str
    valid_until: float | None = None
    memory_id: str | None = None
    created_at: float | None = None
    status: str | None = None
    agent_id: str = ""
    agent_namespace: str = ""
    payload: dict | None = None


class TestAcquisitionAdapter:
    """Tests-only adapter. Maps typed fake results; not a production mint RPC."""

    def __init__(self) -> None:
        self._port = BoundIngestPort(
            ObservationAuthority(secret=TEST_VECTOR_KEY, issuer_id=ISSUER_ID_TEST)
        )

    def acquire(
        self, store: CognitiveMemoryStore, result: TypedFakeAcquisitionResult
    ):
        if result.sensor_channel.strip() == "":
            raise ValueError("sensor_channel required")
        statement = str(result.raw_reading).strip()
        acq = AcquisitionRecord(
            statement=statement,
            source_type=SourceType.SYSTEM.value,
            source_id=str(result.sensor_id),
            observed_at=float(result.acquired_at),
            domain=str(result.domain),
            valid_until=result.valid_until,
            source_location="tests/observation_test_runtime.py",
            producer="pytest-test-authority",
            producer_version="p5-v3",
            context="SYNTHETIC_TEST_DATA",
            payload=result.payload or {"data_label": "SYNTHETIC_TEST_DATA"},
            memory_id=result.memory_id,
            created_at=result.created_at,
            agent_id=result.agent_id,
            agent_namespace=result.agent_namespace,
        )
        rec = self._port.persist_acquired(store, acq)
        if result.status and result.status != DecayState.ACTIVE.value:
            rec = store.revise(
                rec.memory_id,
                status=result.status,
                correction_reason="test-status",
                now=NOW,
            )
        return rec


_ADAPTER = TestAcquisitionAdapter()


@contextmanager
def grant_verify_scope(*, trusted_now: float = NOW) -> Iterator[None]:
    token = push_grant_verify_context(
        GrantVerifyContext(TEST_VECTOR_KEY, ISSUER_ID_TEST, float(trusted_now))
    )
    try:
        yield
    finally:
        reset_grant_verify_context(token)


def persist_test_observation(
    store: CognitiveMemoryStore,
    result: TypedFakeAcquisitionResult,
):
    return _ADAPTER.acquire(store, result)


def timeout_retry_reading(
    raw_reading: str,
    *,
    sensor_id: str = "pytest",
    acquired_at: float = NOW - 20,
    domain: str = "software",
    valid_until: float | None = None,
    memory_id: str | None = None,
    created_at: float | None = NOW - 10,
    status: str | None = None,
    agent_id: str = "",
    agent_namespace: str = "",
    payload: dict | None = None,
) -> TypedFakeAcquisitionResult:
    return TypedFakeAcquisitionResult(
        sensor_channel="software.timeout_recovery",
        raw_reading=raw_reading,
        acquired_at=acquired_at,
        sensor_id=sensor_id,
        domain=domain,
        valid_until=valid_until,
        memory_id=memory_id,
        created_at=created_at,
        status=status,
        agent_id=agent_id,
        agent_namespace=agent_namespace,
        payload=payload,
    )


def verify_test_grant(grant, **kwargs) -> bool:
    return verify_observation_grant(
        grant,
        key=TEST_VECTOR_KEY,
        expected_issuer_id=ISSUER_ID_TEST,
        **kwargs,
    )
