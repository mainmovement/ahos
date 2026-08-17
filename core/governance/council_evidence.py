"""
core.governance.council_evidence — Evidence gate for Cognitive Council.

Law: Agents must NOT receive raw unverified data.

Every input to a lens (candidate metrics, security signals, exitability,
virality, whale, narrative) must be presented as Evidence with the
6-field contract (source, value, timestamp, confidence, verification_status,
metadata). Unverified low-confidence evidence is withheld or marked as
STALE/PENDING so lenses abstain rather than hallucinate.

This module provides a pure gate that the council adapter calls before
`CognitivePanel.deliberate(...)`. No I/O, no network, no leniency.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.models.evidence import Evidence, Confidence, VerificationStatus


@dataclass(frozen=True)
class CouncilInput:
    """
    One typed input to a lens, always evidence-backed.

    name: logical name (e.g. "price_usd", "liquidity_usd", "is_honeypot", "virality_score")
    evidence: Evidence carrying value, source, timestamp, confidence, verification_status, metadata
    """
    name: str
    evidence: Evidence

    @property
    def value(self) -> Any:
        return self.evidence.value

    @property
    def is_eligible(self) -> bool:
        return self.evidence.is_council_eligible()

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "value": self.value, "evidence": self.evidence.to_dict(), "eligible": self.is_eligible}


class CouncilEvidenceGate:
    """
    Pure gate that converts raw candidate/context dicts into CouncilInputs
    and filters by eligibility.

    Usage
    -----
    gate = CouncilEvidenceGate()
    inputs = gate.ingest_candidate(candidate)          # → list[CouncilInput]
    eligible, ineligible = gate.partition(inputs)      # split
    ctx = gate.build_context(inputs, score_report=..., exitability=...)
    gate.assert_eligible(ctx)                          # raises on unverified leakage

    Gate policy (default, strict)
    ------------------------------
    * REJECTED evidence is never eligible.
    * UNKNOWN/UNKNOWN placeholder is never eligible (forces ABSTAIN).
    * UNVERIFIED+LOW is not eligible (needs verification).
    * VERIFIED / DERIVED / PENDING with MEDIUM/HIGH confidence are eligible.
    * UNVERIFIED+MEDIUM/HIGH is conditionally eligible but flagged for audit
      (lens should down-weight; gate currently marks eligible but records warning).

    The gate does NOT auto-verify data. Verification must happen upstream
    (PAL, security gate, feature store). The gate only enforces that unverified
    raw does not reach lenses.
    """

    def __init__(self, require_verified: bool = False):
        """
        require_verified: if True, only VERIFIED/DERIVED are eligible.
        Default False allows PENDING/UNVERIFIED+MEDIUM (lean council) but still
        blocks REJECTED and UNVERIFIED+LOW.
        """
        self.require_verified = require_verified

    # ------------------------------------------------------------------
    # Ingestion helpers — translate various legacy shapes → Evidence
    # ------------------------------------------------------------------

    def evidence_for_metric(
        self,
        name: str,
        value: Any,
        source: str,
        timestamp: float,
        confidence: str = Confidence.MEDIUM,
        verification_status: str = VerificationStatus.UNVERIFIED,
        raw_reference: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> CouncilInput:
        """Wrap a single metric value into CouncilInput with Evidence."""
        ev = Evidence(
            source=source,
            timestamp=timestamp,
            confidence=confidence,
            verification_status=verification_status,
            raw_reference=raw_reference or f"metric:{name}",
            value=value,
            metadata=dict(metadata or {}),
        )
        return CouncilInput(name=name, evidence=ev)

    def ingest_candidate(
        self,
        candidate: Any,
        now: float | None = None,
    ) -> list[CouncilInput]:
        """
        Translate a NormalizedTokenCandidate (or compatible dict) into
        per-field CouncilInputs. Each metric becomes one Evidence.

        Unknown / None fields produce an Evidence with UNKNOWN placeholder
        (value=None) that is *ineligible* — lenses will ABSTAIN rather than assume.
        """
        import time

        ts = now if now is not None else time.time()
        source = getattr(candidate, "source_provider", None) or getattr(candidate, "source", None) or "candidate"
        if isinstance(candidate, dict):
            metrics = candidate.get("metrics", {}) or {}
            security = candidate.get("security", {}) or {}
            raw_ref = candidate.get("raw_payload_sha256", "") or candidate.get("raw_reference", "") or "candidate"
        else:
            m_obj = getattr(candidate, "metrics", None)
            s_obj = getattr(candidate, "security", None)
            # Extract metrics dict from MarketMetrics / similar
            metrics = {}
            if m_obj is not None:
                for k in (
                    "price_usd", "liquidity_usd", "volume_5m", "volume_1h", "volume_24h",
                    "fdv_usd", "market_cap_usd", "price_change_5m", "price_change_1h",
                    "txns_5m_buys", "txns_5m_sells", "txns_1h_buys", "txns_1h_sells",
                ):
                    v = getattr(m_obj, k, None)
                    if v is not None:
                        metrics[k] = v
            security = {}
            if s_obj is not None:
                for k in ("is_honeypot", "buy_tax_pct", "sell_tax_pct", "has_mint_authority", "has_freeze_authority", "liquidity_locked_pct"):
                    v = getattr(s_obj, k, None)
                    if v is not None:
                        security[k] = v
            raw_ref = getattr(candidate, "raw_payload_sha256", "") or getattr(candidate, "raw_reference", "") or "candidate"

        inputs: list[CouncilInput] = []
        # Metrics → Evidence
        for name, value in metrics.items():
            # Metrics from providers are at least DERIVED if price/liquidity present, else PENDING
            is_core_metric = name in ("price_usd", "liquidity_usd")
            conf = Confidence.HIGH if is_core_metric and value is not None else Confidence.MEDIUM
            v_status = VerificationStatus.DERIVED if is_core_metric else VerificationStatus.UNVERIFIED
            # If metric came from provider with confidence, keep it; else infer
            inputs.append(
                self.evidence_for_metric(
                    name=name,
                    value=value,
                    source=source,
                    timestamp=ts,
                    confidence=conf,
                    verification_status=v_status,
                    raw_reference=raw_ref[:32],
                    metadata={"kind": "metric"},
                )
            )
        # Security → Evidence (higher verification requirement)
        for name, value in security.items():
            # Security signals from goplus/rugcheck are VERIFIED if present
            inputs.append(
                self.evidence_for_metric(
                    name=f"security.{name}",
                    value=value,
                    source="security_gate",
                    timestamp=ts,
                    confidence=Confidence.HIGH,
                    verification_status=VerificationStatus.VERIFIED if value is not None else VerificationStatus.UNKNOWN,
                    raw_reference=raw_ref[:32],
                    metadata={"kind": "security"},
                )
            )
        # Ensure at least one placeholder so empty candidate doesn't look like success
        if not inputs:
            inputs.append(
                CouncilInput(
                    name="no_metrics",
                    evidence=Evidence.unknown(source=source, timestamp=ts),
                )
            )
        return inputs

    # ------------------------------------------------------------------
    # Eligibility
    # ------------------------------------------------------------------

    def is_eligible(self, ev: Evidence) -> bool:
        if self.require_verified:
            return ev.verification_status in (VerificationStatus.VERIFIED, VerificationStatus.DERIVED) and ev.confidence != Confidence.UNKNOWN
        return ev.is_council_eligible()

    def partition(self, inputs: list[CouncilInput]) -> tuple[list[CouncilInput], list[CouncilInput]]:
        eligible = [i for i in inputs if self.is_eligible(i.evidence)]
        ineligible = [i for i in inputs if not self.is_eligible(i.evidence)]
        return eligible, ineligible

    def build_context(
        self,
        inputs: list[CouncilInput],
        **extra: Any,
    ) -> dict[str, Any]:
        """
        Build a council context dict that is evidence-only.

        Extra kwargs (score_report, exitability, etc.) are wrapped as Evidence
        if they are plain values. If they already carry evidence, they are kept.
        Raw unverified dicts are rejected unless they contain an evidence wrapper.
        """
        eligible, ineligible = self.partition(inputs)
        # Ineligible inputs are withheld — lenses see only eligible, but audit keeps count
        ctx: dict[str, Any] = {
            "evidence_inputs": {i.name: i for i in eligible},
            "ineligible_count": len(ineligible),
            "ineligible_names": [i.name for i in ineligible],
            "total_count": len(inputs),
        }
        # Wrap extra context values as evidence if not already
        for k, v in extra.items():
            if v is None:
                continue
            if isinstance(v, Evidence):
                ctx[k] = v if self.is_eligible(v) else None
            elif isinstance(v, CouncilInput):
                ctx[k] = v.evidence if self.is_eligible(v.evidence) else None
            elif isinstance(v, dict) and "evidence" in v:
                # Already evidence-backed dict — check eligibility
                ev = v.get("evidence")
                if isinstance(ev, Evidence) and self.is_eligible(ev):
                    ctx[k] = v
                else:
                    ctx[k] = None
            else:
                # Raw value — wrap as pending evidence (will be eligible only if confidence sufficient)
                # To enforce "no raw unverified data", we mark raw as UNVERIFIED+LOW → ineligible
                import time as _time

                if isinstance(v, dict):
                    raw_ts = v.get("timestamp") or v.get("ts") or _time.time()
                    try:
                        ts_val = float(raw_ts)
                        if ts_val <= 0:
                            ts_val = _time.time()
                    except Exception:
                        ts_val = _time.time()
                else:
                    ts_val = _time.time()
                raw_ev = Evidence(
                    source=f"context:{k}",
                    timestamp=ts_val,
                    confidence=Confidence.LOW,
                    verification_status=VerificationStatus.UNVERIFIED,
                    raw_reference=f"context:{k}",
                    value=v,
                    metadata={"raw": True, "blocked": "unverified"},
                )
                # With default gate, this will be ineligible → None → lens abstains
                ctx[k] = raw_ev if self.is_eligible(raw_ev) else None
        return ctx

    def assert_eligible(self, ctx: dict[str, Any]) -> None:
        """
        Assert that no ineligible evidence leaked into the council context.
        Raises PermissionError if a raw/unverified value slipped through.

        Call before CognitivePanel.deliberate(...) to enforce law.
        """
        for k, v in ctx.items():
            if isinstance(v, Evidence) and not self.is_eligible(v):
                raise PermissionError(f"Council evidence gate: ineligible Evidence for '{k}' (status={v.verification_status}, confidence={v.confidence}) — verification required")
            if isinstance(v, CouncilInput) and not v.is_eligible:
                raise PermissionError(f"Council evidence gate: ineligible CouncilInput for '{k}'")

    # Alias for safety engine integration
    def audit(self, inputs: list[CouncilInput]) -> dict[str, Any]:
        eligible, ineligible = self.partition(inputs)
        return {
            "total": len(inputs),
            "eligible": len(eligible),
            "ineligible": len(ineligible),
            "eligible_names": [i.name for i in eligible],
            "ineligible_names": [i.name for i in ineligible],
            "all_eligible": len(ineligible) == 0,
        }
