"""
core.models.observation — Observation value object.

An Observation is a point-in-time measurement of a Token's market state.
Every Observation is Evidence-anchored: price, liquidity, volume, txn counts
are meaningless without provenance.

FROZEN semantics: an Observation records what a provider claimed at a
retrieved_ts. It never mutates. A new timestamp → new Observation.
Missing metrics are None (UNKNOWN), never zero-filled.

Compatibility: adapters translate discovery_observations rows and
architecture.providers.MarketMetrics → this type.
"""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from .evidence import Evidence, Confidence, VerificationStatus
from .token import Token

STALE_AFTER_SECONDS = 4 * 3600  # 4h — matches architecture/alerts engine threshold


@dataclass(frozen=True)
class Observation:
    """
    Frozen snapshot of token market state at a single retrieved instant.

    Attributes
    ----------
    token: canonical Token identity.
    observed_at: retrieved_ts epoch seconds (wall clock when provider responded).
    source_ts: provider-owned timestamp if disclosed (None = not supplied).
    provider: provider id string (redundant with evidence.source but kept for query convenience).
    metrics: dict of market metrics (price_usd, liquidity_usd, volume_*, txns_*, price_change_*, fdv_usd, market_cap_usd, etc.)
             Missing → not present or None (UNKNOWN).
    evidence: Evidence anchor (source, confidence, verification, raw_reference).
    observation_id: stable 32 hex id = sha256(token_id|provider|observed_at|raw_ref)[:32]
    raw_reference: sha256 hex of raw payload (mirrors evidence.raw_reference for convenience).
    """

    token: Token
    observed_at: float
    provider: str
    evidence: Evidence
    metrics: dict[str, Any] = field(default_factory=dict)
    source_ts: float | None = None
    raw_reference: str = field(default="")
    observation_id: str = field(default="")

    def __post_init__(self) -> None:
        if not isinstance(self.token, Token):
            raise ValueError("Observation.token must be Token")
        if not isinstance(self.observed_at, (int, float)) or self.observed_at <= 0:
            raise ValueError("Observation.observed_at must be positive epoch seconds")
        if not isinstance(self.provider, str) or not self.provider.strip():
            raise ValueError("Observation.provider must be non-empty string")
        if not isinstance(self.evidence, Evidence):
            raise ValueError("Observation.evidence must be Evidence instance")
        if not isinstance(self.metrics, dict):
            raise ValueError("Observation.metrics must be dict")
        object.__setattr__(self, "provider", self.provider.strip())
        # Default raw_reference from evidence if not explicit
        if not self.raw_reference:
            object.__setattr__(self, "raw_reference", self.evidence.raw_reference)
        # Deterministic observation id if not supplied
        if not self.observation_id:
            raw = self.raw_reference or self.evidence.raw_reference or ""
            tid = self.token.token_id_
            oid = hashlib.sha256(f"{tid}|{self.provider}|{self.observed_at:.6f}|{raw}".encode("utf-8")).hexdigest()[:32]
            object.__setattr__(self, "observation_id", oid)

    # ------------------------------------------------------------------
    # Metrics helpers
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        return self.metrics.get(key, default)

    @property
    def price_usd(self) -> float | None:
        return self.metrics.get("price_usd")

    @property
    def liquidity_usd(self) -> float | None:
        return self.metrics.get("liquidity_usd")

    @property
    def volume_24h(self) -> float | None:
        return self.metrics.get("volume_24h")

    @property
    def volume_1h(self) -> float | None:
        return self.metrics.get("volume_1h")

    @property
    def fdv_usd(self) -> float | None:
        v = self.metrics.get("fdv_usd")
        if v is None:
            v = self.metrics.get("fdv")
        return v

    @property
    def market_cap_usd(self) -> float | None:
        v = self.metrics.get("market_cap_usd")
        if v is None:
            v = self.metrics.get("market_cap")
        return v

    @property
    def age_seconds(self) -> float:
        return max(0.0, time.time() - self.observed_at)

    def is_stale(self, threshold: float = STALE_AFTER_SECONDS) -> bool:
        return self.age_seconds > threshold

    def is_price_valid(self) -> bool:
        p = self.price_usd
        return p is not None and isinstance(p, (int, float)) and p > 0

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "token": self.token.to_dict(),
            "observed_at": self.observed_at,
            "source_ts": self.source_ts,
            "provider": self.provider,
            "metrics": dict(self.metrics),
            "evidence": self.evidence.to_dict(),
            "raw_reference": self.raw_reference,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Observation":
        return cls(
            token=Token.from_dict(data["token"]),
            observed_at=float(data["observed_at"]),
            provider=data["provider"],
            evidence=Evidence.from_dict(data["evidence"]),
            metrics=dict(data.get("metrics", {})),
            source_ts=data.get("source_ts"),
            raw_reference=data.get("raw_reference", ""),
            observation_id=data.get("observation_id", ""),
        )

    # ------------------------------------------------------------------
    # Adapter factories
    # ------------------------------------------------------------------

    @classmethod
    def from_discovery_row(cls, row: dict[str, Any], token: Token, evidence: Evidence | None = None) -> "Observation":
        """Translate a discovery_observations row → Observation."""
        retrieved = float(row["retrieved_ts"])
        prov = row.get("provider", "unknown")
        # Collect metric columns that exist in schema_sqlite.sql
        metric_keys = [
            "price_usd", "liquidity_usd", "fdv", "market_cap",
            "volume_5m", "volume_1h", "volume_6h", "volume_24h",
            "txns_5m_buys", "txns_5m_sells", "txns_1h_buys", "txns_1h_sells",
            "txns_24h_buys", "txns_24h_sells",
            "price_change_5m", "price_change_1h", "price_change_6h", "price_change_24h",
            "pair_age_minutes", "boost_amount",
        ]
        metrics: dict[str, Any] = {k: row.get(k) for k in metric_keys if row.get(k) is not None}
        # Normalize fdv/market_cap naming to *_usd
        if "fdv" in metrics and "fdv_usd" not in metrics:
            metrics["fdv_usd"] = metrics.pop("fdv")
        if "market_cap" in metrics and "market_cap_usd" not in metrics:
            metrics["market_cap_usd"] = metrics.pop("market_cap")
        ev = evidence
        if ev is None:
            err = row.get("error_state")
            if err:
                ev = Evidence(
                    source=prov,
                    timestamp=retrieved,
                    confidence=Confidence.LOW,
                    verification_status=VerificationStatus.REJECTED,
                    raw_reference=row.get("raw_ref", "") or "",
                    metadata={"error_state": err},
                )
            else:
                ev = Evidence(
                    source=prov,
                    timestamp=retrieved,
                    confidence=Confidence.HIGH if row.get("price_usd") is not None else Confidence.LOW,
                    verification_status=VerificationStatus.UNVERIFIED,
                    raw_reference=row.get("raw_ref", "") or "",
                )
        return cls(
            token=token,
            observed_at=retrieved,
            provider=prov,
            evidence=ev,
            metrics=metrics,
            source_ts=float(row["source_ts"]) if row.get("source_ts") else None,
            raw_reference=row.get("raw_ref", "") or ev.raw_reference,
            observation_id=row.get("obs_id", "") or "",
        )

    @classmethod
    def from_candidate(cls, candidate: Any, metrics_override: dict[str, Any] | None = None) -> "Observation":
        """Translate NormalizedTokenCandidate → Observation (adapter, late import)."""
        from .token import Token as _Token

        token = _Token.from_candidate(candidate)
        prov = getattr(candidate, "source_provider", "unknown")
        ts = float(getattr(candidate, "retrieved_ts", time.time()))
        raw = getattr(candidate, "raw_payload_sha256", "") or ""
        # Pull MarketMetrics fields into dict
        m_obj = getattr(candidate, "metrics", None)
        metrics: dict[str, Any] = dict(metrics_override or {})
        if m_obj is not None and not metrics_override:
            for field_name in (
                "price_usd", "liquidity_usd", "volume_5m", "volume_1h", "volume_24h",
                "volume_velocity", "fdv_usd", "market_cap_usd",
                "price_change_5m", "price_change_1h", "price_change_6h", "price_change_24h",
                "txns_5m_buys", "txns_5m_sells", "txns_1h_buys", "txns_1h_sells",
            ):
                v = getattr(m_obj, field_name, None)
                if v is not None:
                    metrics[field_name] = v
        ev = Evidence(
            source=prov,
            timestamp=ts,
            confidence=Confidence.HIGH if metrics.get("price_usd") else Confidence.LOW,
            verification_status=VerificationStatus.UNVERIFIED,
            raw_reference=raw,
        )
        return cls(
            token=token,
            observed_at=ts,
            provider=prov,
            evidence=ev,
            metrics=metrics,
            raw_reference=raw,
        )

    def describe(self) -> str:
        parts = [f"obs={self.observation_id[:8]}", f"token={self.token.display()}", f"at={self.observed_at:.0f}"]
        if self.price_usd is not None:
            parts.append(f"price=${self.price_usd:g}")
        if self.liquidity_usd is not None:
            parts.append(f"liq=${self.liquidity_usd:,.0f}")
        parts.append(self.evidence.describe())
        return " | ".join(parts)
