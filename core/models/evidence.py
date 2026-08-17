"""
core.models.evidence — Evidence First object.

Every future data point in AHOS v2 MUST carry an Evidence anchor:

    source            — which provider / subsystem produced it (e.g. "dexscreener", "gecko", "ranker")
    timestamp         — retrieval / assertion instant (float epoch seconds UTC)
    confidence        — HIGH | MEDIUM | LOW | UNKNOWN  (evidence quality, not price certainty)
    verification_status — VERIFIED | DERIVED | PENDING | UNVERIFIED | REJECTED | STALE | UNKNOWN
    raw_reference     — sha256 or storage pointer to the archived raw payload

Law: no number is ever stored without its Evidence. NULL / None is UNKNOWN,
never zero-filled or hallucinated.
"""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any

# ---------------------------------------------------------------------------
# Controlled vocabularies — kept as constants (not Enum) for JSON-serializable
# frozen dataclass compatibility while remaining lint-friendly.
# ---------------------------------------------------------------------------

class Confidence:
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"
    ALL = (HIGH, MEDIUM, LOW, UNKNOWN)


class VerificationStatus:
    VERIFIED = "VERIFIED"       # independently corroborated by ≥1 source or on-chain
    DERIVED = "DERIVED"         # computed from verified inputs (e.g. rank, score)
    PENDING = "PENDING"         # not yet corroborated, awaiting second source/horizon
    UNVERIFIED = "UNVERIFIED"   # single source, not yet checked
    REJECTED = "REJECTED"       # failed verification (contract unverified, honeypot flag)
    STALE = "STALE"             # once-verified but freshness window exceeded
    UNKNOWN = "UNKNOWN"         # no verification attempt
    ALL = (VERIFIED, DERIVED, PENDING, UNVERIFIED, REJECTED, STALE, UNKNOWN)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_now() -> float:
    return time.time()


def _provenance_sha(source: str, timestamp: float, raw_reference: str, confidence: str, verification_status: str) -> str:
    """Deterministic provenance digest for deduplication / audit."""
    payload = f"{source}|{timestamp:.6f}|{raw_reference}|{confidence}|{verification_status}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Evidence — frozen value object
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Evidence:
    """
    Frozen Evidence anchor for any domain fact.

    Attributes
    ----------
    source: canonical provider id or subsystem name (non-empty).
    timestamp: epoch seconds UTC (>0).
    confidence: one of Confidence.ALL.
    verification_status: one of VerificationStatus.ALL.
    raw_reference: sha256 hex (64 chars) or archival pointer (non-empty).
                   Empty string only allowed when no raw payload exists
                   (requires confidence=UNKNOWN and verification=UNKNOWN).
    evidence_id: stable uuid4 hex (auto-generated, inspectable).
    provenance_sha256: deterministic digest over (source, timestamp, raw_ref, confidence, status).
    metadata: optional free-form dict for provider latency, http_status, etc.
              Must not contain secrets; callers should use architecture.security
              to sanitize before persisting.
    """

    source: str
    timestamp: float
    confidence: str
    verification_status: str
    raw_reference: str
    evidence_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    provenance_sha256: str = field(default="")
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Frozen dataclass requires object.__setattr__ for fixups.
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("Evidence.source must be non-empty string")
        if not isinstance(self.timestamp, (int, float)) or self.timestamp <= 0:
            raise ValueError("Evidence.timestamp must be positive epoch seconds")
        if self.confidence not in Confidence.ALL:
            raise ValueError(f"Evidence.confidence must be one of {Confidence.ALL}, got {self.confidence!r}")
        if self.verification_status not in VerificationStatus.ALL:
            raise ValueError(f"Evidence.verification_status must be one of {VerificationStatus.ALL}, got {self.verification_status!r}")
        if not isinstance(self.raw_reference, str):
            raise ValueError("Evidence.raw_reference must be string")
        # raw_reference may be empty only for UNKNOWN/UNKNOWN placeholder
        if not self.raw_reference.strip():
            if not (self.confidence == Confidence.UNKNOWN and self.verification_status == VerificationStatus.UNKNOWN):
                raise ValueError("Evidence.raw_reference may be empty only with confidence=UNKNOWN and verification_status=UNKNOWN")

        # Derive provenance if not supplied
        if not self.provenance_sha256:
            sha = _provenance_sha(
                self.source.strip(),
                float(self.timestamp),
                self.raw_reference.strip(),
                self.confidence,
                self.verification_status,
            )
            object.__setattr__(self, "provenance_sha256", sha)
        # Normalize fields (strip source)
        object.__setattr__(self, "source", self.source.strip())
        object.__setattr__(self, "raw_reference", self.raw_reference.strip())
        # Ensure metadata is serializable shallow copy
        if self.metadata is not None and not isinstance(self.metadata, dict):
            raise ValueError("Evidence.metadata must be dict")

    # ------------------------------------------------------------------
    # Derived properties
    # ------------------------------------------------------------------

    @property
    def is_verified(self) -> bool:
        return self.verification_status == VerificationStatus.VERIFIED

    @property
    def is_rejected(self) -> bool:
        return self.verification_status == VerificationStatus.REJECTED

    @property
    def is_unknown(self) -> bool:
        return (
            self.confidence == Confidence.UNKNOWN
            and self.verification_status == VerificationStatus.UNKNOWN
        )

    @property
    def age_seconds(self) -> float:
        return max(0.0, _utc_now() - self.timestamp)

    def is_fresh(self, max_age_seconds: float = 3600.0) -> bool:
        """Freshness check against configurable window (default 1h)."""
        return self.age_seconds <= max_age_seconds and self.verification_status != VerificationStatus.STALE

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # Ensure deterministic ordering for audit hashing
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Evidence":
        return cls(
            source=data["source"],
            timestamp=float(data["timestamp"]),
            confidence=data["confidence"],
            verification_status=data["verification_status"],
            raw_reference=data["raw_reference"],
            evidence_id=data.get("evidence_id", uuid.uuid4().hex),
            provenance_sha256=data.get("provenance_sha256", ""),
            metadata=dict(data.get("metadata", {})),
        )

    # ------------------------------------------------------------------
    # Constructors for common cases
    # ------------------------------------------------------------------

    @classmethod
    def verified(
        cls,
        source: str,
        timestamp: float | None = None,
        raw_reference: str = "",
        confidence: str = Confidence.HIGH,
        metadata: dict[str, Any] | None = None,
    ) -> "Evidence":
        return cls(
            source=source,
            timestamp=timestamp if timestamp is not None else _utc_now(),
            confidence=confidence,
            verification_status=VerificationStatus.VERIFIED,
            raw_reference=raw_reference,
        )

    @classmethod
    def unverified(
        cls,
        source: str,
        timestamp: float | None = None,
        raw_reference: str = "",
        confidence: str = Confidence.LOW,
        metadata: dict[str, Any] | None = None,
    ) -> "Evidence":
        return cls(
            source=source,
            timestamp=timestamp if timestamp is not None else _utc_now(),
            confidence=confidence,
            verification_status=VerificationStatus.UNVERIFIED,
            raw_reference=raw_reference,
            metadata=dict(metadata or {}),
        )

    @classmethod
    def unknown(cls, source: str = "unknown", timestamp: float | None = None) -> "Evidence":
        """Placeholder for missing data — preserved as UNKNOWN, never zero."""
        return cls(
            source=source,
            timestamp=timestamp if timestamp is not None else _utc_now(),
            confidence=Confidence.UNKNOWN,
            verification_status=VerificationStatus.UNKNOWN,
            raw_reference="",
        )

    # Display helper (user-facing Persian-ready)
    def describe(self) -> str:
        age = self.age_seconds
        if age < 60:
            age_s = f"{int(age)}s پیش"
        elif age < 3600:
            age_s = f"{int(age/60)}m پیش"
        else:
            age_s = f"{age/3600:.1f}h پیش"
        return (
            f"منبع={self.source} | اعتماد={self.confidence} | "
            f"وضعیت={self.verification_status} | {age_s} | ref={self.raw_reference[:12] or '—'}"
        )
