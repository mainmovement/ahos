"""ObservationGrant: bind-time factual authority for OBSERVED_FACT only.

Not a public signing API. Not an authority mechanism for DERIVED_FACT.
Ordinary remember()/SQLite rows remain data until verification succeeds.
Public IngestPort cannot mint. There is no persist_observed_acquisition RPC.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import unicodedata
from contextvars import ContextVar
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
ISSUER_ID_TEST = "ahos.observation_authority.test-vector-v1"
VALID_UNTIL_NONE = "NONE"

# SHA-256 of the tests-only vector key. Production never stores the raw vector.
_FORBIDDEN_SECRET_SHA256 = frozenset(
    {"52fe6094743bfd4f9be4321d98adc7e23c1ab622b0ba830e271d1ee1cbfd7850"}
)

_UNKNOWN_TOKENS = frozenset({"", "UNKNOWN", "NONE", "N/A", "unknown", "none", UNKNOWN})


def _unknown_token(value: Any) -> bool:
    text = str(value or "").strip()
    return text in _UNKNOWN_TOKENS or text.upper() in _UNKNOWN_TOKENS


def secret_sha256_hex(secret: bytes) -> str:
    return hashlib.sha256(bytes(secret)).hexdigest()


def is_forbidden_production_secret(secret: bytes) -> bool:
    return secret_sha256_hex(secret) in _FORBIDDEN_SECRET_SHA256


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


def mac_hex(key: bytes, canonical: bytes) -> str:
    return hmac.new(bytes(key), canonical, hashlib.sha256).hexdigest()


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
    """Adapter-built acquisition tuple. Not a public sign-this-claim RPC."""

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


@dataclass(frozen=True)
class GrantVerifyContext:
    """Verify material for the current episode. Not a public orchestrator kwarg."""

    key: bytes
    issuer_id: str
    trusted_now: float


_grant_verify_ctx: ContextVar[GrantVerifyContext | None] = ContextVar(
    "ahos_og_verify", default=None
)


def current_grant_verify_context() -> GrantVerifyContext | None:
    """Episode metadata only. Production verification does not read this."""
    return _grant_verify_ctx.get()


def push_grant_verify_context(ctx: GrantVerifyContext):
    """Sets episode metadata. Has no authority-bearing effect on production verify.

    ``CognitiveOrchestrator._permits_observation_grant`` uses instance-owned
    ``K_O`` and ``ISSUER_ID``. It does not read this ContextVar.
    """
    return _grant_verify_ctx.set(ctx)


def reset_grant_verify_context(token: Any) -> None:
    _grant_verify_ctx.reset(token)


def clear_grant_verify_context() -> None:
    """Drop episode metadata. Does not select or publish production authority."""
    _grant_verify_ctx.set(None)


class ObservationAuthority:
    """HMAC issuer. New instance without a shared key cannot satisfy another verifier."""

    def __init__(self, *, secret: bytes | None = None, issuer_id: str = ISSUER_ID) -> None:
        if secret is not None:
            if len(secret) < 32:
                raise ValueError("ObservationAuthority secret must be at least 32 bytes")
            material = bytes(secret)
        else:
            material = os.urandom(32)
            while is_forbidden_production_secret(material):
                material = os.urandom(32)
        if issuer_id == ISSUER_ID and is_forbidden_production_secret(material):
            raise ValueError("production issuer cannot use the tests-only vector key")
        self._secret = material
        self._issuer_id = str(issuer_id)

    def _mac_hex(self, canonical: bytes) -> str:
        return mac_hex(self._secret, canonical)

    def _mint(self, acq: AcquisitionRecord) -> ObservationGrant:
        _validate_acquisition(acq)
        canonical = canonical_observation_bytes(
            statement=acq.statement,
            source_type=str(acq.source_type),
            source_id=str(acq.source_id),
            observed_at=float(acq.observed_at),
            valid_until=acq.valid_until,
            domain=str(acq.domain),
            issuer_id=self._issuer_id,
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
            issuer_id=self._issuer_id,
            mac=self._mac_hex(canonical),
        )

    def _verify_mac(self, grant: ObservationGrant, canonical: bytes) -> bool:
        expected = self._mac_hex(canonical)
        try:
            return hmac.compare_digest(expected, str(grant.mac))
        except (TypeError, ValueError):
            return False


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
    """Public persist surface. Cannot mint ObservationGrant."""

    def persist_acquired(
        self, store: CognitiveMemoryStore, acq: AcquisitionRecord
    ) -> Any:
        raise RuntimeError("IngestPort cannot mint ObservationGrant")


class BoundIngestPort:
    """Minting persist bound to one ObservationAuthority. Not a public package export."""

    def __init__(self, authority: ObservationAuthority) -> None:
        self._authority = authority

    def persist_acquired(
        self, store: CognitiveMemoryStore, acq: AcquisitionRecord
    ) -> Any:
        grant = self._authority._mint(acq)
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
    key: bytes | None = None,
    expected_issuer_id: str | None = None,
) -> bool:
    """Fail-closed cryptographic + temporal + kind check.

    Production authority is the explicit ``key`` argument (supplied only by
    ``CognitiveOrchestrator._permits_observation_grant``). ContextVar keys and
    issuers are ignored and cannot select production verification.
    """
    if grant is None:
        return False
    use_key = key
    use_issuer = expected_issuer_id if expected_issuer_id is not None else ISSUER_ID
    if use_key is None:
        return False
    if grant.version != GRANT_VERSION or grant.purpose != GRANT_PURPOSE:
        return False
    if grant.kind != GRANT_KIND or grant.issuer_id != use_issuer:
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
    expected = mac_hex(use_key, canonical)
    try:
        return hmac.compare_digest(expected, str(grant.mac))
    except (TypeError, ValueError):
        return False


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
    key: bytes | None = None,
    expected_issuer_id: str | None = None,
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
        key=key,
        expected_issuer_id=expected_issuer_id,
    )


class _IngestPortProtocol(Protocol):
    def persist_acquired(self, store: CognitiveMemoryStore, acq: AcquisitionRecord) -> Any:
        ...
