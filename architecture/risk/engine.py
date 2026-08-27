#!/usr/bin/env python3
"""AHOS Risk Engine (Phase 4/5).

Consumes EvidenceBundle ONLY. Emits structured RiskFindings with explicit
evidence references.

Phase 5: contract / holder / manipulation / whale findings are produced by
`architecture.security` and `architecture.intelligence.whales` and merged here
(deduped by risk_id). This module keeps the historic market-structure floor:
LOW_LIQUIDITY, SELL_PRESSURE, HIGH_UNCERTAINTY, WASH_SUSPECTED.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..intelligence.evidence import (
    EvidenceBundle,
    bool_value,
    numeric_value,
    require_evidence_bundle,
    text_value,
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


def merge_findings(*groups: list[RiskFinding]) -> list[RiskFinding]:
    """First finding per risk_id wins — prevents double penalties."""
    out: list[RiskFinding] = []
    seen: set[str] = set()
    for group in groups:
        for finding in group:
            if finding.risk_id in seen:
                continue
            out.append(finding)
            seen.add(finding.risk_id)
    return out


def classify_risk_level(findings: list[RiskFinding], total_penalties: float) -> str:
    if any(f.severity == "CRITICAL" for f in findings) or total_penalties >= 50.0:
        return "CRITICAL"
    if any(f.severity == "HIGH" for f in findings) or total_penalties >= 25.0:
        return "HIGH"
    if any(f.severity == "MED" for f in findings) or total_penalties >= 10.0:
        return "MED"
    return "LOW"


class RiskEngine:
    """EVIDENCE → RISK. Pure function of an EvidenceBundle."""

    CONSUMER = "RiskEngine.assess"

    def assess(self, evidence: EvidenceBundle,
               extra_findings: list[RiskFinding] | None = None) -> RiskAssessment:
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

        unknowns = evidence.missing_unknowns()
        if len(unknowns) >= 3:
            findings.append(RiskFinding(
                "HIGH_UNCERTAINTY", "MED",
                f"عدم قطعیت بالا ({len(unknowns)} فیلد ناشناخته)",
                len(unknowns) * 3.0, "unknown_fields",
            ))
            refs.append("unknown_fields")

        if bool_value(evidence.get("wash_suspected")) is True:
            findings.append(RiskFinding(
                "WASH_SUSPECTED", "HIGH",
                "الگوی معاملات صوری (wash trading) در شواهد شتاب حجم",
                15.0, "virality.wash_suspected",
            ))
            refs.append("wash_suspected")

        # Market-structure / tokenomics feed-through (P1): penalties only when
        # DERIVED labels indicate fragility — never invent findings from UNKNOWN.
        mstruct_ev = evidence.get("mstruct_label")
        label = None
        if mstruct_ev is not None and getattr(mstruct_ev, "status", "") != "UNKNOWN":
            label = text_value(mstruct_ev)
        if label == "ABNORMAL":
            findings.append(RiskFinding(
                "ABNORMAL_MARKET_STRUCTURE", "HIGH",
                "ساختار بازار غیرعادی (نسبت حجم به نقدینگی / واگرایی فعالیت)",
                12.0, "market_structure.label",
            ))
            refs.append("mstruct_label")
        elif label == "FRAGILE":
            findings.append(RiskFinding(
                "FRAGILE_MARKET_STRUCTURE", "MED",
                "ساختار بازار شکننده (نقدینگی نازک یا فشار نامتوازن)",
                8.0, "market_structure.label",
            ))
            refs.append("mstruct_label")

        tok_ev = evidence.get("tokenomics_label")
        if tok_ev is not None and getattr(tok_ev, "status", "") != "UNKNOWN":
            tok_label = text_value(tok_ev)
            if tok_label == "CRITICAL":
                findings.append(RiskFinding(
                    "TOKENOMICS_CRITICAL", "HIGH",
                    "توکنومیکس بحرانی (اختیار mint/freeze یا تمرکز/سابقه deployer)",
                    18.0, "tokenomics.label",
                ))
                refs.append("tokenomics_label")
            elif tok_label == "CONCERNING":
                findings.append(RiskFinding(
                    "TOKENOMICS_CONCERNING", "MED",
                    "توکنومیکس نگران‌کننده بر اساس شواهد موجود",
                    8.0, "tokenomics.label",
                ))
                refs.append("tokenomics_label")

        if extra_findings is None:
            extra_findings = _standalone_intelligence_findings(evidence)

        findings = merge_findings(findings, extra_findings)
        for finding in findings:
            if finding.evidence_ref not in refs:
                refs.append(finding.evidence_ref)

        total = sum(f.penalty_points for f in findings)
        level = classify_risk_level(findings, total)
        return RiskAssessment(
            findings=findings,
            total_penalties=total,
            risk_level=level,
            evidence_refs=refs,
        )


def _standalone_intelligence_findings(evidence: EvidenceBundle) -> list[RiskFinding]:
    """When callers skip IntelligenceEngine, still apply Phase 5 analyzers."""
    from ..security import SecurityIntelligence
    from ..intelligence.whales import WhaleIntelligence

    security = SecurityIntelligence().analyze(evidence)
    whales = WhaleIntelligence().analyze(evidence)
    return merge_findings(security.findings, whales.findings)
