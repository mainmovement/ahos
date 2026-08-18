#!/usr/bin/env python3
"""AHOS Integrated Intelligence Engine (Phase 4).

Orchestrates the evidence-only decision floor:

    Evidence
        → Features
        → Risk
        → Opportunity Score + Confidence
        → Explanations (WHY-law)

No stage after materialization reads raw provider data. Optional Lane-A intel
signals (narrative / virality / whales / exitability) attach only as extra
Evidence via `architecture.intelligence.adapters`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from ..explanations.engine import ExplanationEngine, ExplanationPack
from ..features.extractor import FeatureExtractor, FeatureVector
from ..risk.engine import RiskAssessment, RiskEngine
from ..scoring.calculator import OpportunityCalculator, ScoreBreakdown
from .adapters import collect_intel_evidence
from .evidence import Evidence, EvidenceBundle, require_evidence_bundle


@dataclass
class IntelligenceReport:
    """Closed, explainable result of one intelligence evaluation."""
    evidence: EvidenceBundle
    features: FeatureVector
    risk: RiskAssessment
    score: ScoreBreakdown
    explanation: ExplanationPack

    @property
    def opportunity_score(self) -> float:
        return self.score.opportunity_score

    @property
    def confidence_level(self) -> str:
        return self.score.confidence_level

    @property
    def risk_level(self) -> str:
        return self.score.risk_level


class IntelligenceEngine:
    """Integrated Phase 4 engine. All calculations consume Evidence objects."""

    CONSUMER = "IntelligenceEngine.evaluate"

    def __init__(
        self,
        feature_extractor: FeatureExtractor | None = None,
        risk_engine: RiskEngine | None = None,
        calculator: OpportunityCalculator | None = None,
        explainer: ExplanationEngine | None = None,
    ):
        self.features = feature_extractor or FeatureExtractor()
        self.risk = risk_engine or RiskEngine()
        self.calculator = calculator or OpportunityCalculator()
        self.explainer = explainer or ExplanationEngine()

    def evaluate(
        self,
        evidence: EvidenceBundle,
        extra: Sequence[Evidence] | None = None,
        *,
        narrative: Any = None,
        virality: Any = None,
        whales: Any = None,
        exitability: Any = None,
    ) -> IntelligenceReport:
        require_evidence_bundle(evidence, self.CONSUMER)

        extras: list[Evidence] = list(extra or [])
        extras.extend(collect_intel_evidence(
            narrative=narrative, virality=virality,
            whales=whales, exitability=exitability,
        ))
        if extras:
            evidence = evidence.extended(extras)

        features = self.features.extract(evidence)
        risk = self.risk.assess(evidence)
        score = self.calculator.calculate(evidence, features, risk)
        explanation = self.explainer.explain(evidence, features, risk, score)
        return IntelligenceReport(
            evidence=evidence,
            features=features,
            risk=risk,
            score=score,
            explanation=explanation,
        )
