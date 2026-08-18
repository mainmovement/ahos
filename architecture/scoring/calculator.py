#!/usr/bin/env python3
"""AHOS Opportunity Score Calculator (Phase 4).

Consumes EvidenceBundle + FeatureVector + RiskAssessment. Never reads raw
candidate metrics. Numeric combination is the deterministic floor:

    clip(base_score − Σ penalties, 0, 100)
"""
from __future__ import annotations

from dataclasses import dataclass

from ..features.extractor import FeatureVector
from ..intelligence.evidence import EvidenceBundle, require_evidence_bundle
from ..risk.engine import RiskAssessment


@dataclass(frozen=True)
class ScoreBreakdown:
    base_score: float
    total_penalties: float
    final_score: float
    opportunity_score: float
    confidence_level: str                        # HIGH | MED | LOW
    risk_level: str                              # LOW | MED | HIGH | CRITICAL
    components: dict[str, float]


class OpportunityCalculator:
    """FEATURES + RISK + EVIDENCE → OPPORTUNITY + CONFIDENCE."""

    CONSUMER = "OpportunityCalculator.calculate"

    def calculate(self, evidence: EvidenceBundle, features: FeatureVector,
                  risk: RiskAssessment) -> ScoreBreakdown:
        require_evidence_bundle(evidence, self.CONSUMER)
        if not isinstance(features, FeatureVector):
            raise TypeError("OpportunityCalculator.calculate requires a FeatureVector")
        if not isinstance(risk, RiskAssessment):
            raise TypeError("OpportunityCalculator.calculate requires a RiskAssessment")

        base = float(features.base_score)
        penalties = float(risk.total_penalties)
        final = max(0.0, min(100.0, base - penalties))

        # Risk level: keep the engine's preview (same rules as the historic scorer).
        risk_level = risk.risk_level

        unknowns = evidence.missing_unknowns()
        known_report = evidence.report_evidence()
        if len(unknowns) == 0 and len(known_report) >= 4:
            confidence = "HIGH"
        elif len(unknowns) <= 2 and len(known_report) >= 2:
            confidence = "MED"
        else:
            confidence = "LOW"

        return ScoreBreakdown(
            base_score=base,
            total_penalties=penalties,
            final_score=final,
            opportunity_score=round(final, 1),
            confidence_level=confidence,
            risk_level=risk_level,
            components={
                "base_score": base,
                "total_penalties": penalties,
                "final_score": final,
            },
        )
