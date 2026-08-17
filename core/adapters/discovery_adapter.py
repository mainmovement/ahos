"""
core.adapters.discovery_adapter — Bridge: discovery / architecture.providers → core.

Zero storage mutation. Every mapping preserves source timestamps and raw refs
as Evidence so downstream reasoning stays auditable.

Functions are deliberately free (not methods) for easy import and testing.
Late imports avoid hard coupling to legacy packages at load-time.
"""

from __future__ import annotations

from typing import Any

from core.models.evidence import Evidence, Confidence, VerificationStatus
from core.models.token import Token
from core.models.observation import Observation


def discovery_row_to_observation(
    row: dict[str, Any],
    token_row: dict[str, Any] | None = None,
) -> Observation:
    """
    discovery_observations + tokens rows → core Observation.
    Pass both rows when available for richer token metadata.
    """
    # Build token identity from token_row if supplied, else minimal token from obs row
    if token_row is not None:
        token = Token.from_discovery_row(token_row)
    else:
        token = Token(
            chain=row.get("chain_id", "solana") or "solana",
            address=row.get("token_address") or row.get("address") or "Unknown111111111111111111111111111111111111111",
            symbol=row.get("symbol"),
            first_seen_ts=float(row.get("retrieved_ts", 0) or row.get("first_seen_ts", 0) or 1),
            evidence=Evidence(
                source=row.get("provider", "discovery"),
                timestamp=float(row.get("retrieved_ts", 0) or 1),
                confidence=Confidence.UNKNOWN,
                verification_status=VerificationStatus.UNVERIFIED,
                raw_reference=row.get("raw_ref", "") or "",
            ),
        )
    # Delegate to Observation adapter (re-uses its discovery_row logic)
    return Observation.from_discovery_row(row, token)


def candidate_to_observation(candidate: Any) -> Observation:
    """
    architecture.providers.NormalizedTokenCandidate → core Observation.
    Thin wrapper around Observation.from_candidate for ergonomics.
    """
    return Observation.from_candidate(candidate)


def pal_envelope_to_evidence(envelope: dict[str, Any]) -> Evidence:
    """
    discovery.pal envelope (provider_id, source_timestamp, retrieval_timestamp,
    error_state, raw_sha256 …) → Evidence.
    """
    provider = envelope.get("provider_id", envelope.get("provider", "unknown"))
    retrieved = float(envelope.get("retrieval_timestamp", envelope.get("retrieved_ts", 0)) or 0) or 1
    err = envelope.get("error_state")
    raw = envelope.get("raw_sha256", envelope.get("raw_ref", "")) or ""
    availability = envelope.get("availability", "UNKNOWN")
    if err or availability == "DOWN":
        return Evidence(
            source=provider,
            timestamp=retrieved,
            confidence=Confidence.LOW,
            verification_status=VerificationStatus.REJECTED,
            raw_reference=raw,
            metadata={"error_state": err, "availability": availability},
        )
    if availability == "DEGRADED":
        return Evidence(
            source=provider,
            timestamp=retrieved,
            confidence=Confidence.LOW,
            verification_status=VerificationStatus.PENDING,
            raw_reference=raw,
        )
    return Evidence(
        source=provider,
        timestamp=retrieved,
        confidence=Confidence.MEDIUM,
        verification_status=VerificationStatus.UNVERIFIED,
        raw_reference=raw,
    )
