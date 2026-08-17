"""
core.models.evidence — Evidence First object (AHOS v2 Evidence-Driven Layer).

Every future data point in AHOS v2 MUST carry an Evidence anchor with
the unified architecture:

    source              — which provider / subsystem produced it (e.g. "dexscreener", "gecko", "ranker", "council")
    value               — the observed / computed value (price, score, verdict, metric) — None only for UNKNOWN
    timestamp           — retrieval / assertion instant (float epoch seconds UTC)
    confidence          — HIGH | MEDIUM | LOW | UNKNOWN  (evidence quality, not price certainty)
    verification_status — VERIFIED | DERIVED | PENDING | UNVERIFIED | REJECTED | STALE | UNKNOWN
    metadata            — free-form dict (latency, http_status, error_state, raw_ref, etc.)

Compatibility: Phase 2 evidence used `raw_reference` as the 5th field. Phase 3
introduces `value` + `metadata` as first-class. This implementation keeps
both: `raw_reference` remains the archival pointer (sha256 hex) and is
mirrored into `metadata["raw_reference"]` for forward compatibility, while
`value` carries the measurement. All three representations round-trip.

Law: no number is ever stored without its Evidence. NULL / None is UNKNOWN,
never zero-filled or hallucinated. Evidence is frozen / immutable.
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


def _provenance_sha(source: str, timestamp: float, raw_reference: str, confidence: str, verification_status: str, value_repr: str = "") -> str:
    """Deterministic provenance digest for deduplication / audit."""
    # Include value_repr for v2 evidence to distinguish same source/ts with different values
    payload = f"{source}|{timestamp:.6f}|{raw_reference}|{confidence}|{verification_status}|{value_repr}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Evidence — frozen value object (unified Phase 2 + Phase 3 contract)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Evidence:
    """
    Frozen Evidence anchor for any domain fact.

    Unified Phase 3 contract (6 required logical fields)
    -----------------------------------------------------
    source: canonical provider id or subsystem name (non-empty).
    value: the measured / computed value (float, dict, str, etc.). None only when UNKNOWN.
    timestamp: epoch seconds UTC (>0).
    confidence: one of Confidence.ALL.
    verification_status: one of VerificationStatus.ALL.
    metadata: dict for provider latency, http_status, error_state, raw_reference, etc.
              Must not contain secrets; callers should use architecture.security
              to sanitize before persisting.

    Backwards-compatible / audit fields
    -------------------------------------
    raw_reference: sha256 hex (64 chars) or archival pointer (non-empty).
                   Empty string only allowed when no raw payload exists
                   (requires confidence=UNKNOWN and verification=UNKNOWN).
                   Mirrored to metadata["raw_reference"] for new readers.
    evidence_id: stable uuid4 hex (auto-generated, inspectable).
    provenance_sha256: deterministic digest over (source, timestamp, raw_ref, confidence, status, value).

    Invariants
    ----------
    * All 6 logical fields are always present in to_dict() (value may be None for UNKNOWN).
    * Provenance is deterministic and deduplicates identical claims.
    """

    source: str
    timestamp: float
    confidence: str
    verification_status: str
    raw_reference: str
    # Phase 3 first-class fields
    value: Any = None
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

        # Ensure metadata is dict (allow None → {})
        meta = self.metadata if isinstance(self.metadata, dict) else {}
        # Mirror raw_reference into metadata for Phase 3 readers (non-destructive)
        if self.raw_reference and "raw_reference" not in meta:
            meta = dict(meta)
            meta["raw_reference"] = self.raw_reference
        object.__setattr__(self, "metadata", meta)

        # Derive provenance if not supplied — include value repr for v2 uniqueness
        if not self.provenance_sha256:
            try:
                value_repr = str(self.value)[:200] if self.value is not None else ""
            except Exception:
                value_repr = ""
            sha = _provenance_sha(
                self.source.strip(),
                float(self.timestamp),
                self.raw_reference.strip(),
                self.confidence,
                self.verification_status,
                value_repr,
            )
            object.__setattr__(self, "provenance_sha256", sha)
        # Normalize fields (strip source)
        object.__setattr__(self, "source", self.source.strip())
        object.__setattr__(self, "raw_reference", self.raw_reference.strip())

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
    # Serialization — unified Phase 2 + Phase 3 keys
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # Ensure deterministic ordering for audit hashing; also guarantee Phase 3 keys
        # exist even when value is None (explicit null beats missing key)
        d.setdefault("value", self.value)
        d.setdefault("metadata", dict(self.metadata))
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Evidence":
        # Accept both Phase 2 (raw_reference) and Phase 3 (value+metadata) shapes
        # Prefer explicit value; fall back to metadata value or None
        value = data.get("value")
        if value is None and isinstance(data.get("metadata"), dict):
            # Some older producers stored value inside metadata — extract without mutating
            value = data["metadata"].get("value", value)
        return cls(
            source=data["source"],
            timestamp=float(data["timestamp"]),
            confidence=data["confidence"],
            verification_status=data["verification_status"],
            raw_reference=data.get("raw_reference", data.get("metadata", {}).get("raw_reference", "") if isinstance(data.get("metadata"), dict) else "") or "",
            value=value,
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
        value: Any = None,
    ) -> "Evidence":
        return cls(
            source=source,
            timestamp=timestamp if timestamp is not None else _utc_now(),
            confidence=confidence,
            verification_status=VerificationStatus.VERIFIED,
            raw_reference=raw_reference,
            value=value if value is not None else (metadata or {}).get("value"),
            metadata=dict(metadata or {}),
        )

    @classmethod
    def unverified(
        cls,
        source: str,
        timestamp: float | None = None,
        raw_reference: str = "",
        confidence: str = Confidence.LOW,
        metadata: dict[str, Any] | None = None,
        value: Any = None,
    ) -> "Evidence":
        return cls(
            source=source,
            timestamp=timestamp if timestamp is not None else _utc_now(),
            confidence=confidence,
            verification_status=VerificationStatus.UNVERIFIED,
            raw_reference=raw_reference,
            value=value if value is not None else (metadata or {}).get("value"),
            metadata=dict(metadata or {}),
        )

    @classmethod
    def unknown(cls, source: str = "unknown", timestamp: float | None = None, value: Any = None) -> "Evidence":
        """Placeholder for missing data — preserved as UNKNOWN, never zero."""
        return cls(
            source=source,
            timestamp=timestamp if timestamp is not None else _utc_now(),
            confidence=Confidence.UNKNOWN,
            verification_status=VerificationStatus.UNKNOWN,
            raw_reference="",
            value=value,
            metadata={},
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
        val_s = ""
        if self.value is not None:
            try:
                v = str(self.value)
                val_s = f" | مقدار={v[:40]}"
            except Exception:
                val_s = ""
        return (
            f"منبع={self.source} | اعتماد={self.confidence} | "
            f"وضعیت={self.verification_status} | {age_s}{val_s} | ref={self.raw_reference[:12] or '—'}"
        )

    # ------------------------------------------------------------------
    # Phase 3 helpers — evidence validation predicate
    # ------------------------------------------------------------------

    def has_required_fields(self) -> bool:
        """Phase 3 contract: every evidence must carry source, value, timestamp, confidence, verification_status, metadata."""
        return (
            isinstance(self.source, str) and self.source.strip() != ""
            and self.timestamp is not None and self.timestamp > 0
            and self.confidence in Confidence.ALL
            and self.verification_status in VerificationStatus.ALL
            and isinstance(self.metadata, dict)
            # value may be None only for UNKNOWN placeholder — still considered present
            and hasattr(self, "value")
        )

    def is_council_eligible(self) -> bool:
        """
        Council eligibility: agents may only receive evidence that is
        not UNVERIFIED + LOW-confidence unverified raw. Rejected or Unknown
        evidence is never eligible; unverified requires explicit gating.
        """
        if self.verification_status in (VerificationStatus.REJECTED, VerificationStatus.UNKNOWN) and self.confidence == Confidence.UNKNOWN:
            return False
        if self.verification_status == VerificationStatus.REJECTED:
            return False
        # Unverified low-confidence evidence requires verification before council
        if self.verification_status == VerificationStatus.UNVERIFIED and self.confidence == Confidence.LOW:
            return False
        return True
