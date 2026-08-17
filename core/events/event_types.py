"""
core.events.event_types — Typed domain events for AHOS v2.

Each event is a frozen dataclass with:
  event_id, event_type, aggregate_id (token_id or decision_id),
  timestamp, version, payload, evidence_ids, correlation_id, provenance.

Events are append-only facts — they never mutate and never command execution.
Handlers must treat events as advisory and enforce safety via governance.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any

EVENT_VERSION = "v2"


class EventType:
    """Controlled vocabulary for domain events. New types are added, never renamed."""

    # Discovery / ingestion
    TOKEN_DISCOVERED = "TOKEN_DISCOVERED"
    OBSERVATION_RECORDED = "OBSERVATION_RECORDED"
    EVIDENCE_VERIFIED = "EVIDENCE_VERIFIED"
    EVIDENCE_REJECTED = "EVIDENCE_REJECTED"

    # Analysis
    SCORE_COMPUTED = "SCORE_COMPUTED"
    PANEL_VERDICT = "PANEL_VERDICT"

    # Decision (advisory)
    DECISION_PROPOSED = "DECISION_PROPOSED"
    DECISION_ACKNOWLEDGED = "DECISION_ACKNOWLEDGED"  # human confirmation
    DECISION_REJECTED = "DECISION_REJECTED"          # safety veto

    # Position (paper only)
    PAPER_OBSERVATION = "PAPER_OBSERVATION"
    POSITION_REVIEWED = "POSITION_REVIEWED"

    # Alerts & comms
    ALERT_EMITTED = "ALERT_EMITTED"
    TELEGRAM_DISPATCHED = "TELEGRAM_DISPATCHED"

    # Provider
    PROVIDER_HEALTH_CHANGED = "PROVIDER_HEALTH_CHANGED"
    PROVIDER_RATE_LIMITED = "PROVIDER_RATE_LIMITED"

    # Governance
    SAFETY_VIOLATION = "SAFETY_VIOLATION"
    RUNTIME_STARTED = "RUNTIME_STARTED"
    RUNTIME_STOPPED = "RUNTIME_STOPPED"

    ALL = (
        TOKEN_DISCOVERED,
        OBSERVATION_RECORDED,
        EVIDENCE_VERIFIED,
        EVIDENCE_REJECTED,
        SCORE_COMPUTED,
        PANEL_VERDICT,
        DECISION_PROPOSED,
        DECISION_ACKNOWLEDGED,
        DECISION_REJECTED,
        PAPER_OBSERVATION,
        POSITION_REVIEWED,
        ALERT_EMITTED,
        TELEGRAM_DISPATCHED,
        PROVIDER_HEALTH_CHANGED,
        PROVIDER_RATE_LIMITED,
        SAFETY_VIOLATION,
        RUNTIME_STARTED,
        RUNTIME_STOPPED,
    )


@dataclass(frozen=True)
class Event:
    """
    Frozen domain event.

    Attributes
    ----------
    event_id: uuid4 hex (unique).
    event_type: one of EventType.ALL.
    aggregate_id: token_id / observation_id / decision_id the event is about.
    timestamp: epoch seconds UTC (>0).
    version: schema version (default EVENT_VERSION).
    payload: arbitrary JSON-serializable dict with event-specific fields.
    evidence_ids: list of Evidence.evidence_id this event is derived from.
    correlation_id: groups events from the same pipeline run.
    provenance_sha256: optional deterministic digest over (type+aggregate+timestamp+payload).
    metadata: optional free-form dict.
    """

    event_type: str
    aggregate_id: str
    timestamp: float = field(default_factory=time.time)
    payload: dict[str, Any] = field(default_factory=dict)
    evidence_ids: list[str] = field(default_factory=list)
    correlation_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    version: str = EVENT_VERSION
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    provenance_sha256: str = field(default="")
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.event_type not in EventType.ALL:
            raise ValueError(f"Event.event_type must be one of {EventType.ALL}, got {self.event_type!r}")
        if not isinstance(self.aggregate_id, str) or not self.aggregate_id.strip():
            raise ValueError("Event.aggregate_id must be non-empty string")
        if not isinstance(self.timestamp, (int, float)) or self.timestamp <= 0:
            raise ValueError("Event.timestamp must be positive epoch seconds")
        if not isinstance(self.payload, dict):
            raise ValueError("Event.payload must be dict")
        if not isinstance(self.evidence_ids, list):
            raise ValueError("Event.evidence_ids must be list")
        for eid in self.evidence_ids:
            if not isinstance(eid, str) or not eid.strip():
                raise ValueError("evidence_ids elements must be non-empty strings")
        # Provenance derivation if not supplied
        if not self.provenance_sha256:
            import hashlib, json

            digest_payload = json.dumps(
                {"t": self.event_type, "a": self.aggregate_id.strip(), "ts": self.timestamp, "p": self.payload},
                sort_keys=True,
                ensure_ascii=False,
                default=str,
            )
            sha = hashlib.sha256(digest_payload.encode("utf-8")).hexdigest()
            object.__setattr__(self, "provenance_sha256", sha)
        object.__setattr__(self, "aggregate_id", self.aggregate_id.strip())

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp,
            "version": self.version,
            "payload": dict(self.payload),
            "evidence_ids": list(self.evidence_ids),
            "correlation_id": self.correlation_id,
            "provenance_sha256": self.provenance_sha256,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        return cls(
            event_type=data["event_type"],
            aggregate_id=data["aggregate_id"],
            timestamp=float(data.get("timestamp", time.time())),
            payload=dict(data.get("payload", {})),
            evidence_ids=list(data.get("evidence_ids", [])),
            correlation_id=data.get("correlation_id", uuid.uuid4().hex[:16]),
            version=data.get("version", EVENT_VERSION),
            event_id=data.get("event_id", uuid.uuid4().hex),
            provenance_sha256=data.get("provenance_sha256", ""),
            metadata=dict(data.get("metadata", {})),
        )

    def describe(self) -> str:
        return f"{self.event_type} [{self.aggregate_id[:12]}] @{self.timestamp:.0f} corr={self.correlation_id[:8]}"


# ---------------------------------------------------------------------------
# Convenience factories
# ---------------------------------------------------------------------------

def create_event(
    event_type: str,
    aggregate_id: str,
    payload: dict[str, Any] | None = None,
    evidence_ids: list[str] | None = None,
    correlation_id: str | None = None,
    timestamp: float | None = None,
    metadata: dict[str, Any] | None = None,
) -> Event:
    """Ergonomic factory — validates through Event.__post_init__."""
    return Event(
        event_type=event_type,
        aggregate_id=aggregate_id,
        timestamp=timestamp if timestamp is not None else time.time(),
        payload=dict(payload or {}),
        evidence_ids=list(evidence_ids or []),
        correlation_id=correlation_id or uuid.uuid4().hex[:16],
        metadata=dict(metadata or {}),
    )
