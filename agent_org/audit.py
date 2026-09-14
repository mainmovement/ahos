"""Versioned, deterministic, tamper-evident audit envelope for Slice 2B."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol

from agent_org.contracts import require_id, require_utc


GENESIS_HASH = "0" * 64
AUDIT_SCHEMA_VERSION = 1


class IdFactory(Protocol):
    def new(self, prefix: str) -> str: ...


def canonical_value(value: Any) -> Any:
    if is_dataclass(value):
        return canonical_value(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("naive datetime cannot be audited")
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, dict):
        return {str(key): canonical_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [canonical_value(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise TypeError(f"unsupported canonical value: {type(value)!r}")


def canonical_json(value: Any) -> str:
    return json.dumps(
        canonical_value(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    timestamp: datetime
    actor_principal: str
    session_id: str
    authority_chain: tuple[str, ...]
    command_id: str
    correlation_id: str
    causation_id: str | None
    parent_task_id: str | None
    resource_id: str
    operation: str
    capability_id: str
    policy_version: str
    artifact_version: int | None
    evidence_lineage: tuple[str, ...]
    previous_state: str | None
    previous_version: int | None
    resulting_state: str | None
    resulting_version: int | None
    result: str
    failure_reason: str | None
    payload_hash: str
    event_hash: str
    previous_event_hash: str
    schema_version: int = AUDIT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        require_id(self.event_id, "event.", "event_id")
        require_utc(self.timestamp, "timestamp")
        if not self.command_id or not self.result or not self.payload_hash:
            raise ValueError("audit command, result, and payload hash are required")

    def hash_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("event_hash")
        return payload


class AuditIntegrityError(RuntimeError):
    pass


class AuditLedger:
    """In-memory append-only chain with an internal head/count checkpoint.

    The checkpoint detects local truncation of the event list.  It is not an
    external anchor and this class intentionally makes no tamper-proof claim.
    """

    def __init__(self) -> None:
        self.__events: list[AuditEvent] = []
        self.__expected_count = 0
        self.__expected_head = GENESIS_HASH

    def events(self) -> tuple[AuditEvent, ...]:
        return tuple(self.__events)

    @property
    def head(self) -> str:
        return self.__expected_head

    @property
    def count(self) -> int:
        return self.__expected_count

    def append(
        self,
        *,
        ids: IdFactory,
        timestamp: datetime,
        actor_principal: str,
        session_id: str,
        authority_chain: tuple[str, ...],
        command_id: str,
        correlation_id: str,
        causation_id: str | None,
        parent_task_id: str | None,
        resource_id: str,
        operation: str,
        capability_id: str,
        policy_version: str,
        artifact_version: int | None,
        evidence_lineage: tuple[str, ...],
        previous_state: str | None,
        previous_version: int | None,
        resulting_state: str | None,
        resulting_version: int | None,
        result: str,
        failure_reason: str | None,
        payload_hash: str,
    ) -> AuditEvent:
        event = AuditEvent(
            event_id=ids.new("event"),
            timestamp=timestamp,
            actor_principal=actor_principal,
            session_id=session_id,
            authority_chain=authority_chain,
            command_id=command_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
            parent_task_id=parent_task_id,
            resource_id=resource_id,
            operation=operation,
            capability_id=capability_id,
            policy_version=policy_version,
            artifact_version=artifact_version,
            evidence_lineage=evidence_lineage,
            previous_state=previous_state,
            previous_version=previous_version,
            resulting_state=resulting_state,
            resulting_version=resulting_version,
            result=result,
            failure_reason=failure_reason,
            payload_hash=payload_hash,
            event_hash="",
            previous_event_hash=self.__expected_head,
        )
        event = AuditEvent(**{**asdict(event), "event_hash": digest(event.hash_payload())})
        self.__events.append(event)
        self.__expected_count += 1
        self.__expected_head = event.event_hash
        return event

    def verify(self) -> bool:
        if len(self.__events) != self.__expected_count:
            raise AuditIntegrityError("audit event count checkpoint mismatch")
        previous = GENESIS_HASH
        for event in self.__events:
            if event.previous_event_hash != previous:
                raise AuditIntegrityError("audit previous hash mismatch")
            if digest(event.hash_payload()) != event.event_hash:
                raise AuditIntegrityError("audit event hash mismatch")
            previous = event.event_hash
        if previous != self.__expected_head:
            raise AuditIntegrityError("audit head checkpoint mismatch")
        return True

