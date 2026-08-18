#!/usr/bin/env python3
"""AHOS Risk Engine (Phase 4).

Consumes EvidenceBundle ONLY. Emits structured RiskFindings with explicit
evidence references. Security vetoes (honeypot) remain non-compensable at the
scoring layer via a 100-point CRITICAL penalty.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..intelligence.evidence import (
    EvidenceBundle,
    bool_value,
    numeric_value,
    require_evidence_bundle,
)


@dataclass(frozen=True)
class RiskFinding:
    risk_id: str
    severity: str                                # LOW | MED | HIGH | CRITICAL
    description: str
    penalty_points: float
    evidence_ref: str


@dataclass
class RiskAssessment:
    findings: list[RiskFinding] = field(default_factory=list)
    total_penalties: float = 0.0
    risk_level: str = "LOW"                      # filled by scoring, previewed here
    evidence_refs: list[str] = field(default_factory=list)

    def has(self, risk_id: str) -> bool:
        return any(f.risk_id == risk_id for f in self.findings)


class RiskEngine:
    """EVIDENCE → RISK. Pure function of an EvidenceBundle."""

    CONSUMER = "RiskEngine.assess"

    def assess(self, evidence: EvidenceBundle) -> RiskAssessment:
        require_evidence_bundle(evidence, self.CONSUMER)

        findings: list[RiskFinding] = []
        refs: list[str] = []

        liq = numeric_value(evidence.get("liquidity_usd"))
        if liq is not None and liq < 2000:
            findings.append(RiskFinding(
                "LOW_LIQUIDITY", "HIGH", "نقدینگی بسیار اندک (< $2k)",
                25.0, "metrics.liquidity_usd",
            ))
            refs.append("liquidity_usd")

        buys = numeric_value(evidence.get("txns_1h_buys"))
        sells = numeric_value(evidence.get("txns_1h_sells"))
        if buys is not None and sells is not None:
            total_tx = buys + sells
            if total_tx > 20:
                buy_ratio = buys / total_tx
                if buy_ratio < 0.50:
                    findings.append(RiskFinding(
                        "SELL_PRESSURE", "MED", "فشار فروش غالب در ۱ ساعت گذشته",
                        10.0, "txns_1h",
                    ))
                    refs.append("txns_1h_sells")

        if bool_value(evidence.get("is_honeypot")) is True:
            findings.append(RiskFinding(
                "CRITICAL_HONEYPOT", "CRITICAL",
                "قرارداد به عنوان Honeypot شناسایی شد",
                100.0, "security.is_honeypot",
            ))
            refs.append("is_honeypot")

        if bool_value(evidence.get("has_mint_authority")) is True:
            findings.append(RiskFinding(
                "MINT_AUTHORITY_ACTIVE", "HIGH",
                "قابلیت ضرب توکن نامحدود فعال است",
                20.0, "security.has_mint_authority",
            ))
            refs.append("has_mint_authority")

        if bool_value(evidence.get("has_freeze_authority")) is True:
            findings.append(RiskFinding(
                "FREEZE_AUTHORITY_ACTIVE", "HIGH",
                "قابلیت مسدودسازی کیف‌پول‌ها فعال است",
                20.0, "security.has_freeze_authority",
            ))
            refs.append("has_freeze_authority")

        concentration = numeric_value(evidence.get("top10_concentration"))
        if concentration is not None and concentration > 70.0:
            findings.append(RiskFinding(
                "HIGH_HOLDER_CONCENTRATION", "HIGH",
                f"تمرکز شدید هولدرها ({concentration:.1f}%)",
                25.0, "security.top10_holder_concentration_pct",
            ))
            refs.append("top10_concentration")

        if bool_value(evidence.get("is_contract_verified")) is False:
            findings.append(RiskFinding(
                "UNVERIFIED_CONTRACT", "MED",
                "سورس کد قرارداد تایید نشده است",
                10.0, "security.is_contract_verified",
            ))
            refs.append("is_contract_verified")

        unknowns = evidence.missing_unknowns()
        if len(unknowns) >= 3:
            findings.append(RiskFinding(
                "HIGH_UNCERTAINTY", "MED",
                f"عدم قطعیت بالا ({len(unknowns)} فیلد ناشناخته)",
                len(unknowns) * 3.0, "unknown_fields",
            ))
            refs.append("unknown_fields")

        # Optional intel-derived evidence (never required; never overrides vetoes).
        if bool_value(evidence.get("wash_suspected")) is True:
            findings.append(RiskFinding(
                "WASH_SUSPECTED", "HIGH",
                "الگوی معاملات صوری (wash trading) در شواهد شتاب حجم",
                15.0, "virality.wash_suspected",
            ))
            refs.append("wash_suspected")

        total = sum(f.penalty_points for f in findings)
        if any(f.severity == "CRITICAL" for f in findings) or total >= 50.0:
            level = "CRITICAL"
        elif any(f.severity == "HIGH" for f in findings) or total >= 25.0:
            level = "HIGH"
        elif any(f.severity == "MED" for f in findings) or total >= 10.0:
            level = "MED"
        else:
            level = "LOW"

        return RiskAssessment(
            findings=findings,
            total_penalties=total,
            risk_level=level,
            evidence_refs=refs,
        )
