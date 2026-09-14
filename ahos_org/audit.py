"""Append-only audit log with a deterministic hash chain."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ahos_org.clock import Clock, SystemClock, isoformat_utc
from ahos_org.errors import AppendOnlyViolationError, TamperDetectedError
from ahos_org.ids import IdFactory, UuidFactory
from ahos_org.models import EventType

GENESIS_HASH = "0" * 64


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    timestamp: str
    event_type: str
    actor: str
    task_id: str
    action: str
    target: str
    decision: str
    reason: str
    evidence_refs: tuple[str, ...]
    previous_event_hash: str
    event_hash: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence_refs"] = list(self.evidence_refs)
        return payload

    def payload_for_hash(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("event_hash")
        return payload


class AuditLog:
    """In-memory append-only log with optional JSONL persistence."""

    def __init__(
        self,
        clock: Clock | None = None,
        ids: IdFactory | None = None,
        path: Path | None = None,
    ) -> None:
        self._clock = clock or SystemClock()
        self._ids = ids or UuidFactory()
        self._path = path
        self._events: list[AuditEvent] = []
        if path is not None and path.exists():
            self._load(path)

    def __len__(self) -> int:
        return len(self._events)

    def events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)

    def last_hash(self) -> str:
        if not self._events:
            return GENESIS_HASH
        return self._events[-1].event_hash

    def append(
        self,
        *,
        event_type: EventType | str,
        actor: str,
        action: str,
        target: str,
        reason: str,
        task_id: str = "",
        decision: str = "",
        evidence_refs: tuple[str, ...] | list[str] | None = None,
    ) -> AuditEvent:
        refs = tuple(evidence_refs or ())
        previous = self.last_hash()
        event = AuditEvent(
            event_id=self._ids.new("evt"),
            timestamp=isoformat_utc(self._clock.now()),
            event_type=str(event_type),
            actor=actor,
            task_id=task_id,
            action=action,
            target=target,
            decision=decision,
            reason=reason,
            evidence_refs=refs,
            previous_event_hash=previous,
            event_hash="",
        )
        digest = sha256_text(canonical_json(event.payload_for_hash()))
        event = AuditEvent(
            event_id=event.event_id,
            timestamp=event.timestamp,
            event_type=event.event_type,
            actor=event.actor,
            task_id=event.task_id,
            action=event.action,
            target=event.target,
            decision=event.decision,
            reason=event.reason,
            evidence_refs=event.evidence_refs,
            previous_event_hash=event.previous_event_hash,
            event_hash=digest,
        )
        self._events.append(event)
        if self._path is not None:
            self._persist(event)
        return event

    def replace(self, *_args: Any, **_kwargs: Any) -> None:
        raise AppendOnlyViolationError("Audit events cannot be replaced.")

    def rewrite(self, *_args: Any, **_kwargs: Any) -> None:
        raise AppendOnlyViolationError("Audit events cannot be rewritten.")

    def delete(self, *_args: Any, **_kwargs: Any) -> None:
        raise AppendOnlyViolationError("Audit events cannot be deleted.")

    def clear(self) -> None:
        raise AppendOnlyViolationError("Audit log cannot be cleared.")

    def verify_integrity(self) -> bool:
        previous = GENESIS_HASH
        for event in self._events:
            if event.previous_event_hash != previous:
                raise TamperDetectedError(
                    f"Broken chain at {event.event_id}: previous hash mismatch."
                )
            expected = sha256_text(canonical_json(event.payload_for_hash()))
            if event.event_hash != expected:
                raise TamperDetectedError(
                    f"Broken hash at {event.event_id}: payload digest mismatch."
                )
            previous = event.event_hash
        return True

    def _persist(self, event: AuditEvent) -> None:
        assert self._path is not None
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(canonical_json(event.to_dict()) + "\n")

    def _load(self, path: Path) -> None:
        lines = path.read_text(encoding="utf-8").splitlines()
        for line in lines:
            if not line.strip():
                continue
            raw = json.loads(line)
            event = AuditEvent(
                event_id=raw["event_id"],
                timestamp=raw["timestamp"],
                event_type=raw["event_type"],
                actor=raw["actor"],
                task_id=raw.get("task_id", ""),
                action=raw["action"],
                target=raw["target"],
                decision=raw.get("decision", ""),
                reason=raw["reason"],
                evidence_refs=tuple(raw.get("evidence_refs") or ()),
                previous_event_hash=raw["previous_event_hash"],
                event_hash=raw["event_hash"],
            )
            self._events.append(event)
        self.verify_integrity()
