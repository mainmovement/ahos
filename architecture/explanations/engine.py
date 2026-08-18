#!/usr/bin/env python3
"""AHOS Explanation Engine (Phase 4) — WHY-law.

Consumes Evidence + Features + Risk + Score. Produces the structured answers
the rest of AHOS already exposes on OpportunityScoreReport:

  why scored · evidence · missing · risks · invalidation
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..features.extractor import FeatureVector
from ..intelligence.evidence import Evidence, EvidenceBundle, numeric_value, require_evidence_bundle
from ..risk.engine import RiskAssessment
from ..scoring.calculator import ScoreBreakdown
from ..scoring.engine import InvalidationCondition


@dataclass
class ExplanationPack:
    positive_reasons: list[str] = field(default_factory=list)
    missing_unknowns: list[str] = field(default_factory=list)
    invalidation_conditions: list[InvalidationCondition] = field(default_factory=list)
    report_evidence: list[Evidence] = field(default_factory=list)
    why: str = ""
    evidence_refs: list[str] = field(default_factory=list)


class ExplanationEngine:
    """SCORE + EVIDENCE → explainable answers (never a trade order)."""

    CONSUMER = "ExplanationEngine.explain"

    def explain(self, evidence: EvidenceBundle, features: FeatureVector,
                risk: RiskAssessment, score: ScoreBreakdown) -> ExplanationPack:
        require_evidence_bundle(evidence, self.CONSUMER)
        if not isinstance(features, FeatureVector):
            raise TypeError("ExplanationEngine.explain requires a FeatureVector")
        if not isinstance(risk, RiskAssessment):
            raise TypeError("ExplanationEngine.explain requires a RiskAssessment")
        if not isinstance(score, ScoreBreakdown):
            raise TypeError("ExplanationEngine.explain requires a ScoreBreakdown")

        liq = numeric_value(evidence.get("liquidity_usd")) or 0.0
        vol = numeric_value(evidence.get("volume_1h")) or 0.0
        invalidation = [
            InvalidationCondition(
                "INV-01",
                "کاهش نقدینگی به زیر ۲۰٪ سطح فعلی",
                f"< ${max(liq, 0) * 0.2:,.0f}",
            ),
            InvalidationCondition(
                "INV-02",
                "افت حجم معاملات ۱ ساعته به زیر ۷۰٪ سطح فعلی",
                f"< ${max(vol, 0) * 0.3:,.0f}",
            ),
            InvalidationCondition(
                "INV-03",
                "فعال شدن سیگنال Honeypot یا قفل ناموفق",
                "is_honeypot = True",
            ),
            InvalidationCondition(
                "INV-04",
                "افزایش مالیات خرید/فروش به بالای ۱۰٪",
                "buy/sell tax > 10%",
            ),
        ]

        reasons = list(features.reasons)
        missing = evidence.missing_unknowns()
        why = "\n".join(f"+ {r}" for r in reasons) if reasons else "امتیاز پایه حداقلی"
        report_ev = evidence.report_evidence()
        refs = list(dict.fromkeys(
            list(features.evidence_refs) + list(risk.evidence_refs) + [e.key for e in report_ev]
        ))
        return ExplanationPack(
            positive_reasons=reasons,
            missing_unknowns=missing,
            invalidation_conditions=invalidation,
            report_evidence=report_ev,
            why=why,
            evidence_refs=refs,
        )
