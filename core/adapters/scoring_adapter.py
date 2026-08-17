"""
core.adapters.scoring_adapter — Bridge: architecture.scoring → core Decision.

The scorer produces OpportunityScoreReport; this adapter normalizes it into
the core advisory Decision with proper Evidence refs and safety footer.

Never places orders. Never mutates legacy stores.
"""

from __future__ import annotations

from typing import Any

from core.models.decision import Decision, DecisionAction, ADVISORY_FOOTER
from core.models.evidence import Evidence, Confidence, VerificationStatus
from core.models.token import Token
from core.models.observation import Observation

# Map scorer confidence → core confidence vocabulary
_CONF_MAP = {
    "HIGH": Confidence.HIGH,
    "MED": Confidence.MEDIUM,
    "MEDIUM": Confidence.MEDIUM,
    "LOW": Confidence.LOW,
}

# Heuristic: score + risk → advisory action (tunable, but safe: default is WAIT)
def _score_to_action(score: float | None, risk: str, confidence: str) -> str:
    if score is None:
        return DecisionAction.INSUFFICIENT_EVIDENCE
    if risk == "CRITICAL":
        return DecisionAction.AVOID
    if confidence == "LOW" or score < 50:
        return DecisionAction.WAIT
    if score >= 70 and risk in ("LOW", "MED") and confidence == "HIGH":
        return DecisionAction.WATCH  # ENTER requires human confirmation via governance
    return DecisionAction.WATCH


def score_report_to_decision(
    report: Any,
    token: Token | None = None,
    observation: Observation | None = None,
    evidence: Evidence | None = None,
) -> Decision:
    """
    Convert OpportunityScoreReport (or compatible object/dict) → Decision.

    Accepts either the dataclass from architecture.scoring.engine or a plain dict
    with equivalent fields for testability without importing architecture at import-time.
    """
    if isinstance(report, dict):
        score = report.get("opportunity_score", report.get("score"))
        confidence_raw = report.get("confidence_level", report.get("confidence", "UNKNOWN"))
        risk_level = report.get("risk_level", "UNKNOWN")
        reasons = report.get("positive_reasons", report.get("reasons", []))
        risks = report.get("risk_deductions", report.get("risks", []))
        invalidation = report.get("invalidation_conditions", [])
        token_chain = report.get("token_chain") or report.get("chain") or "solana"
        token_address = report.get("token_address") or report.get("address") or "Unknown"
        token_symbol = report.get("token_symbol") or report.get("symbol")
        ts = report.get("computed_at_ts", 0)
    else:
        score = getattr(report, "opportunity_score", getattr(report, "score", None))
        confidence_raw = getattr(report, "confidence_level", getattr(report, "confidence", "UNKNOWN"))
        risk_level = getattr(report, "risk_level", "UNKNOWN")
        reasons = getattr(report, "positive_reasons", getattr(report, "reasons", [])) or []
        risks = getattr(report, "risk_deductions", getattr(report, "risks", [])) or []
        invalidation = getattr(report, "invalidation_conditions", []) or []
        token_chain = getattr(report, "token_chain", getattr(report, "chain", "solana"))
        token_address = getattr(report, "token_address", getattr(report, "address", "UnknownAddr"))
        token_symbol = getattr(report, "token_symbol", getattr(report, "symbol", None))
        ts = getattr(report, "computed_at_ts", 0) or 0

    confidence = _CONF_MAP.get(str(confidence_raw).strip().upper(), Confidence.UNKNOWN)

    # Build token if not supplied
    if token is None:
        token = Token(
            chain=token_chain or "solana",
            address=token_address or "UnknownAddr111111111111111111111111111",
            symbol=token_symbol,
            first_seen_ts=float(ts) if ts else 1,
            evidence=evidence
            or Evidence(
                source="scoring",
                timestamp=float(ts) if ts else 1,
                confidence=confidence,
                verification_status=VerificationStatus.DERIVED,
                raw_reference=getattr(report, "provenance_sha256", "") if not isinstance(report, dict) else report.get("provenance_sha256", "") or "",
            ),
        )

    # Evidence refs: prefer observation evidence, else synthetic scoring evidence
    ev = evidence
    if ev is None and observation is not None:
        ev = observation.evidence
    if ev is None:
        raw_ref = getattr(report, "provenance_sha256", "") if not isinstance(report, dict) else report.get("provenance_sha256", "") or ""
        ev = Evidence(
            source="scoring",
            timestamp=float(ts) if ts else 1,
            confidence=confidence,
            verification_status=VerificationStatus.DERIVED,
            raw_reference=raw_ref[:64],
        )

    action = _score_to_action(score, risk_level, str(confidence_raw).upper())

    # Normalize risks/invalidation to list[dict]
    norm_risks = []
    for r in risks or []:
        if isinstance(r, dict):
            norm_risks.append(r)
        else:
            # scorer RiskItem dataclass
            try:
                norm_risks.append({"risk_id": getattr(r, "risk_id", "UNKNOWN"), "description": getattr(r, "description", str(r)), "severity": getattr(r, "severity", "UNKNOWN"), "evidence_ref": getattr(r, "evidence_ref", "")})
            except Exception:
                norm_risks.append({"description": str(r)})

    norm_inv = []
    for c in invalidation or []:
        if isinstance(c, dict):
            norm_inv.append(c)
        else:
            try:
                norm_inv.append({"condition_id": getattr(c, "condition_id", ""), "trigger_description": getattr(c, "trigger_description", str(c)), "threshold": getattr(c, "threshold", "")})
            except Exception:
                norm_inv.append({"trigger_description": str(c)})

    rationale_parts = []
    if reasons:
        rationale_parts.append("; ".join(str(x) for x in reasons[:2]))
    if score is not None:
        rationale_parts.append(f"امتیاز {score:.0f}/100، ریسک {risk_level}، اعتماد {confidence_raw}")
    rationale = " — ".join(rationale_parts) if rationale_parts else f"ارزیابی با امتیاز {score} و ریسک {risk_level}"

    return Decision(
        token=token,
        action=action,
        rationale=rationale,
        evidence_refs=[ev],
        confidence=confidence,
        risk_level=risk_level,
        risks=norm_risks,
        invalidation_conditions=norm_inv,
        observation=observation,
        score=float(score) if score is not None else None,
        metadata={"adapter": "scoring", "original_confidence_raw": str(confidence_raw)},
    )
