"""ObservationGrant: bind-time factual authority for OBSERVED_FACT only.

Not a public signing API. Not an authority mechanism for DERIVED_FACT.
Ordinary remember()/SQLite rows remain data until verification succeeds.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time
import unicodedata
from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from architecture.cognitive.memory.store import CognitiveMemoryStore, IntegrityError
from architecture.cognitive.memory.types import (
    UNKNOWN,
    DecayState,
    EpistemicKind,
    MemoryType,
    SourceType,
)

GRANT_VERSION = "AHOS-OG-v1"
GRANT_PURPOSE = "FACTUAL_INGEST"
GRANT_KIND = EpistemicKind.OBSERVED_FACT.value
GRANT_PAYLOAD_KEY = "observation_grant"
ISSUER_ID = "ahos.observation_authority"
VALID_UNTIL_NONE = "NONE"

_UNKNOWN_TOKENS = frozenset({"", "UNKNOWN", "NONE", "N/A", "unknown", "none", UNKNOWN})


def _unknown_token(value: Any) -> bool:
    text = str(value or "").strip()
    return text in _UNKNOWN_TOKENS or text.upper() in _UNKNOWN_TOKENS


def normalize_statement(statement: str) -> str:
    """UTF-8 NFC after one strip(). No case-fold."""
    return unicodedata.normalize("NFC", str(statement)).strip()


def statement_sha256(statement: str) -> str:
    return hashlib.sha256(normalize_statement(statement).encode("utf-8")).hexdigest()


def timestamp_us(value: float) -> int:
    return int(round(float(value) * 1_000_000))


def valid_until_token(value: float | None) -> str:
    if value is None:
        return VALID_UNTIL_NONE
    return str(timestamp_us(value))


def canonical_observation_bytes(
    *,
    statement: str,
    source_type: str,
    source_id: str,
    observed_at: float,
    valid_until: float | None,
    domain: str,
    issuer_id: str = ISSUER_ID,
) -> bytes:
    """Deterministic MAC input for the authority-bearing observation tuple."""
    parts = (
        GRANT_VERSION,
        GRANT_PURPOSE,
        GRANT_KIND,
        statement_sha256(statement),
        str(source_type),
        str(source_id),
        str(timestamp_us(observed_at)),
        valid_until_token(valid_until),
        str(domain),
        str(issuer_id),
    )
    return "|".join(parts).encode("utf-8")


@dataclass(frozen=True)
class ObservationGrant:
    """Immutable grant material. Authority is the MAC, not a boolean flag."""

    version: str
    purpose: str
    kind: str
    statement_sha256: str
    source_type: str
    source_id: str
    observed_at_us: int
    valid_until: str
    domain: str
    issuer_id: str
    mac: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "purpose": self.purpose,
            "kind": self.kind,
            "statement_sha256": self.statement_sha256,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "observed_at_us": int(self.observed_at_us),
            "valid_until": self.valid_until,
            "domain": self.domain,
            "issuer_id": self.issuer_id,
            "mac": self.mac,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> ObservationGrant | None:
        if not isinstance(data, Mapping):
            return None
        try:
            return cls(
                version=str(data["version"]),
                purpose=str(data["purpose"]),
                kind=str(data["kind"]),
                statement_sha256=str(data["statement_sha256"]),
                source_type=str(data["source_type"]),
                source_id=str(data["source_id"]),
                observed_at_us=int(data["observed_at_us"]),
                valid_until=str(data["valid_until"]),
                domain=str(data["domain"]),
                issuer_id=str(data["issuer_id"]),
                mac=str(data["mac"]),
            )
        except (KeyError, TypeError, ValueError):
            return None


@dataclass(frozen=True)
class AcquisitionRecord:
    """Structured acquisition. Not a free-form 'sign this statement' request."""

    statement: str
    source_type: str
    source_id: str
    observed_at: float
    domain: str
    valid_until: float | None = None
    source_location: str = "trusted-acquisition"
    producer: str = "observation-authority"
    producer_version: str = "og-v1"
    context: str = "SYNTHETIC_TEST_DATA"
    payload: dict[str, Any] | None = None
    memory_type: str = MemoryType.EPISODIC.value
    memory_id: str | None = None
    created_at: float | None = None
    agent_id: str = ""
    agent_namespace: str = ""
    hypothesis_id: str = ""
    experiment_id: str = ""
    prediction_id: str = ""


class ObservationAuthority:
    """Process-held issuer. Constructing a new instance yields a different secret."""

    def __init__(self, *, secret: bytes | None = None) -> None:
        if secret is not None:
            if len(secret) < 32:
                raise ValueError("ObservationAuthority secret must be at least 32 bytes")
            self._secret = bytes(secret)
        else:
            self._secret = os.urandom(32)

    def _mac_hex(self, canonical: bytes) -> str:
        return hmac.new(self._secret, canonical, hashlib.sha256).hexdigest()

    def _mint(self, acq: AcquisitionRecord) -> ObservationGrant:
        _validate_acquisition(acq)
        canonical = canonical_observation_bytes(
            statement=acq.statement,
            source_type=str(acq.source_type),
            source_id=str(acq.source_id),
            observed_at=float(acq.observed_at),
            valid_until=acq.valid_until,
            domain=str(acq.domain),
        )
        return ObservationGrant(
            version=GRANT_VERSION,
            purpose=GRANT_PURPOSE,
            kind=GRANT_KIND,
            statement_sha256=statement_sha256(acq.statement),
            source_type=str(acq.source_type),
            source_id=str(acq.source_id),
            observed_at_us=timestamp_us(float(acq.observed_at)),
            valid_until=valid_until_token(acq.valid_until),
            domain=str(acq.domain),
            issuer_id=ISSUER_ID,
            mac=self._mac_hex(canonical),
        )

    def _verify_mac(self, grant: ObservationGrant, canonical: bytes) -> bool:
        expected = self._mac_hex(canonical)
        try:
            return hmac.compare_digest(expected, str(grant.mac))
        except (TypeError, ValueError):
            return False


class _ProcessAuthority:
    instance: ObservationAuthority | None = None


def _process_authority() -> ObservationAuthority:
    if _ProcessAuthority.instance is None:
        _ProcessAuthority.instance = ObservationAuthority()
    return _ProcessAuthority.instance


def _validate_acquisition(acq: AcquisitionRecord) -> None:
    if not normalize_statement(acq.statement):
        raise ValueError("AcquisitionRecord.statement required")
    if acq.observed_at is None:
        raise ValueError("AcquisitionRecord.observed_at required")
    if _unknown_token(acq.source_type) or _unknown_token(acq.source_id):
        raise ValueError("trusted acquisition forbids UNKNOWN provenance")
    if _unknown_token(acq.domain):
        raise ValueError("trusted acquisition requires a domain")
    src = SourceType(acq.source_type)
    if src in {SourceType.AI_MODEL, SourceType.AGENT}:
        raise ValueError("AI_MODEL/AGENT cannot receive an ObservationGrant")


class IngestPort:
    """Trusted persist surface. Minting uses the process authority only."""

    def persist_acquired(
        self, store: CognitiveMemoryStore, acq: AcquisitionRecord
    ) -> Any:
        grant = _process_authority()._mint(acq)
        payload = dict(acq.payload or {})
        payload[GRANT_PAYLOAD_KEY] = grant.to_dict()
        return store.remember(
            memory_id=acq.memory_id,
            memory_type=acq.memory_type,
            epistemic_kind=EpistemicKind.OBSERVED_FACT,
            statement=acq.statement,
            source_type=acq.source_type,
            source_id=acq.source_id,
            source_location=acq.source_location,
            producer=acq.producer,
            producer_version=acq.producer_version,
            domain=acq.domain,
            context=acq.context,
            observed_at=float(acq.observed_at),
            created_at=acq.created_at,
            valid_until=acq.valid_until,
            payload=payload,
            agent_id=acq.agent_id,
            agent_namespace=acq.agent_namespace,
            hypothesis_id=acq.hypothesis_id,
            experiment_id=acq.experiment_id,
            prediction_id=acq.prediction_id,
        )


def persist_observed_acquisition(
    store: CognitiveMemoryStore, acq: AcquisitionRecord
) -> Any:
    """Only trusted persist path that can mint a process-verifiable grant."""
    return IngestPort().persist_acquired(store, acq)


def grant_from_payload(payload: Mapping[str, Any] | None) -> ObservationGrant | None:
    if not isinstance(payload, Mapping):
        return None
    return ObservationGrant.from_dict(payload.get(GRANT_PAYLOAD_KEY))


def verify_observation_grant(
    grant: ObservationGrant | None,
    *,
    statement: str,
    source_type: str,
    source_id: str,
    observed_at: float | None,
    valid_until: float | None,
    domain: str,
    epistemic_kind: str,
    now: float,
    status: str = "",
) -> bool:
    """Fail-closed cryptographic + temporal + kind check against latest fields."""
    if grant is None:
        return False
    if grant.version != GRANT_VERSION or grant.purpose != GRANT_PURPOSE:
        return False
    if grant.kind != GRANT_KIND or grant.issuer_id != ISSUER_ID:
        return False
    if str(epistemic_kind) != GRANT_KIND:
        return False
    if observed_at is None:
        return False
    if _unknown_token(source_type) or _unknown_token(source_id):
        return False
    if float(observed_at) > float(now):
        return False
    if valid_until is not None and float(valid_until) <= float(now):
        return False
    if status in {
        DecayState.STALE.value,
        DecayState.SUPERSEDED.value,
        DecayState.ARCHIVED.value,
    }:
        return False
    if statement_sha256(statement) != grant.statement_sha256:
        return False
    canonical = canonical_observation_bytes(
        statement=statement,
        source_type=source_type,
        source_id=source_id,
        observed_at=float(observed_at),
        valid_until=valid_until,
        domain=domain,
        issuer_id=grant.issuer_id,
    )
    return _process_authority()._verify_mac(grant, canonical)


def latest_observation_fields(
    store: CognitiveMemoryStore | None,
    memory_id: str,
) -> Any:
    if store is None or not memory_id:
        return None
    try:
        return store.get(memory_id)
    except IntegrityError:
        return None


def observation_grant_permits_factual(
    *,
    statement: str,
    epistemic_kind: str,
    memory_type: str,
    source_type: str,
    source_id: str,
    observed_at: float | None,
    valid_until: float | None,
    domain: str,
    payload: Mapping[str, Any] | None,
    now: float,
    status: str = "",
) -> bool:
    if memory_type == MemoryType.FAILURE.value:
        return False
    return verify_observation_grant(
        grant_from_payload(payload),
        statement=statement,
        source_type=source_type,
        source_id=source_id,
        observed_at=observed_at,
        valid_until=valid_until,
        domain=domain,
        epistemic_kind=epistemic_kind,
        now=now,
        status=status,
    )


class _IngestPortProtocol(Protocol):
    def persist_acquired(self, store: CognitiveMemoryStore, acq: AcquisitionRecord) -> Any:
        ...
