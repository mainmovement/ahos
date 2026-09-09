"""Provenance-bearing memory record. Historical rows are never rewritten in place."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from architecture.cognitive.memory.types import (
    UNKNOWN,
    ContradictionState,
    DecayState,
    EpistemicKind,
    MemoryType,
    SourceType,
)


class InvalidProvenanceError(ValueError):
    pass


class EpistemicViolation(ValueError):
    pass


def _require_token(name: str, value: str | None) -> str:
    if value is None or not str(value).strip():
        raise InvalidProvenanceError(f"{name} missing; use {UNKNOWN!r} if unknown")
    return str(value).strip()


@dataclass
class MemoryRecord:
    memory_id: str
    revision: int
    memory_type: str
    epistemic_kind: str
    statement: str
    created_at: float
    observed_at: float | None
    source_type: str
    source_id: str
    source_location: str
    producer: str
    producer_version: str
    domain: str
    context: str
    confidence: float | None
    valid_from: float | None
    valid_until: float | None
    status: str
    contradiction_state: str
    integrity_hash: str
    payload: dict[str, Any] = field(default_factory=dict)
    supersedes: str = ""
    derived_from: list[str] = field(default_factory=list)
    outcome_link: str = ""
    hypothesis_id: str = ""
    experiment_id: str = ""
    agent_id: str = ""
    agent_namespace: str = ""
    ttl_seconds: float | None = None
    session_id: str = ""
    task_id: str = ""
    priority: int = 0
    expires_at: float | None = None
    correction_reason: str = ""
    prediction_id: str = ""
    capability_gap_id: str = ""
    proposal_id: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "revision": self.revision,
            "memory_type": self.memory_type,
            "epistemic_kind": self.epistemic_kind,
            "statement": self.statement,
            "created_at": self.created_at,
            "observed_at": self.observed_at,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "source_location": self.source_location,
            "producer": self.producer,
            "producer_version": self.producer_version,
            "domain": self.domain,
            "context": self.context,
            "confidence": self.confidence,
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
            "status": self.status,
            "contradiction_state": self.contradiction_state,
            "integrity_hash": self.integrity_hash,
            "payload": dict(self.payload),
            "supersedes": self.supersedes,
            "derived_from": list(self.derived_from),
            "outcome_link": self.outcome_link,
            "hypothesis_id": self.hypothesis_id,
            "experiment_id": self.experiment_id,
            "agent_id": self.agent_id,
            "agent_namespace": self.agent_namespace,
            "ttl_seconds": self.ttl_seconds,
            "session_id": self.session_id,
            "task_id": self.task_id,
            "priority": self.priority,
            "expires_at": self.expires_at,
            "correction_reason": self.correction_reason,
            "prediction_id": self.prediction_id,
            "capability_gap_id": self.capability_gap_id,
            "proposal_id": self.proposal_id,
        }

    def canonical_for_hash(self) -> dict[str, Any]:
        d = self.as_dict()
        d.pop("integrity_hash", None)
        return d


def compute_integrity_hash(record: MemoryRecord) -> str:
    payload = json.dumps(record.canonical_for_hash(), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_new_record(record: MemoryRecord) -> None:
    if not record.statement or not str(record.statement).strip():
        raise ValueError("statement required")
    MemoryType(record.memory_type)
    kind = EpistemicKind(record.epistemic_kind)
    source = SourceType(record.source_type)
    DecayState(record.status)
    ContradictionState(record.contradiction_state)
    for name in (
        "source_id",
        "source_location",
        "producer",
        "producer_version",
        "domain",
        "context",
    ):
        _require_token(name, getattr(record, name))
    if source in {SourceType.AI_MODEL, SourceType.AGENT} and kind in {
        EpistemicKind.OBSERVED_FACT,
        EpistemicKind.DERIVED_FACT,
    }:
        raise EpistemicViolation(
            "AI_MODEL/AGENT output cannot be stored as OBSERVED_FACT or DERIVED_FACT"
        )
    if kind == EpistemicKind.PREDICTION and not (record.prediction_id or record.outcome_link):
        # prediction_id may be UNKNOWN if the caller has no ledger id yet
        pass
    if record.memory_type == MemoryType.WORKING.value:
        if record.ttl_seconds is None or float(record.ttl_seconds) <= 0:
            raise ValueError("WORKING memory requires a positive ttl_seconds")
        if not record.session_id.strip():
            raise ValueError("WORKING memory requires session_id")
    if record.confidence is not None and not (0.0 <= float(record.confidence) <= 1.0):
        raise ValueError("confidence must be in [0, 1] or None (UNKNOWN)")
