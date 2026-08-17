"""
intelligence.risk.engine — Aggregating Risk Engine (evidence-only)

Collects 4 analyzers (contract, liquidity, concentration, manipulation) and
produces an aggregate penalty + confidence. No trading, no secrets.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List

from core.models.evidence import Evidence
from .base import RiskResult, RiskLevel
from .contract_risk import ContractRiskAnalyzer
from .liquidity_risk import LiquidityRiskAnalyzer
from .concentration_risk import ConcentrationRiskAnalyzer
from .manipulation_risk import ManipulationRiskAnalyzer


@dataclass(frozen=True)
class RiskEngineResult:
    results: List[RiskResult]
    aggregate_score: float  # 0-100, max of sub-scores weighted
    aggregate_level: str
    highest_reasons: List[str]
    evidence_refs: List[str]
    computed_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "aggregate_score": self.aggregate_score,
            "aggregate_level": self.aggregate_level,
            "results": [r.to_dict() for r in self.results],
            "highest_reasons": self.highest_reasons,
            "evidence_refs": self.evidence_refs,
            "computed_at": self.computed_at,
        }


class RiskEngine:
    """
    Evidence-only risk aggregation. Deterministic, no I/O.
    """

    def __init__(self, analyzers=None):
        if analyzers is None:
            self.analyzers = [
                ContractRiskAnalyzer(),
                LiquidityRiskAnalyzer(),
                ConcentrationRiskAnalyzer(),
                ManipulationRiskAnalyzer(),
            ]
        else:
            self.analyzers = list(analyzers)

    def assess(self, evidence_map: Dict[str, Evidence], now: float | None = None) -> RiskEngineResult:
        ts = now if now is not None else time.time()
        results: List[RiskResult] = []
        for analyzer in self.analyzers:
            try:
                res = analyzer.analyze(evidence_map, now=ts)
            except Exception as exc:  # isolation: one analyzer crash must not kill pipeline
                res = RiskResult(analyzer=getattr(analyzer, "analyzer_id", "unknown"), level=RiskLevel.UNKNOWN, score=50, reasons=[f"تحلیل‌گر خطا داد: {type(exc).__name__}"], evidence_refs=[], metadata={"error": str(exc)}, computed_at=ts)
            results.append(res)

        # Aggregate: weighted max + unknown handling
        if not results:
            return RiskEngineResult(results=[], aggregate_score=50, aggregate_level=RiskLevel.UNKNOWN, highest_reasons=[], evidence_refs=[], computed_at=ts)

        # Level hierarchy: CRITICAL > HIGH > MEDIUM > LOW > UNKNOWN
        order = {RiskLevel.CRITICAL: 4, RiskLevel.HIGH: 3, RiskLevel.MEDIUM: 2, RiskLevel.LOW: 1, RiskLevel.UNKNOWN: 0}
        top_level = max(results, key=lambda r: order.get(r.level, 0)).level
        # Score: max of sub-scores, but UNKNOWN is capped
        valid_scores = [r.score for r in results if r.level != RiskLevel.UNKNOWN]
        aggregate_score = max(valid_scores) if valid_scores else max(r.score for r in results)
        # But if any CRITICAL, floor at 75
        if any(r.level == RiskLevel.CRITICAL for r in results):
            aggregate_score = max(aggregate_score, 75)

        # Highest reasons: from highest-risk analyzers
        top_results = sorted(results, key=lambda r: (order.get(r.level, 0), r.score), reverse=True)[:2]
        highest_reasons = []
        for r in top_results:
            highest_reasons.extend(r.reasons[:2])

        evidence_refs = []
        for r in results:
            evidence_refs.extend(r.evidence_refs)
        evidence_refs = sorted(set(evidence_refs))

        return RiskEngineResult(
            results=results,
            aggregate_score=float(max(0, min(100, aggregate_score))),
            aggregate_level=top_level,
            highest_reasons=highest_reasons[:4],
            evidence_refs=evidence_refs,
            computed_at=ts,
        )

    def is_safe(self, result: RiskEngineResult) -> bool:
        return result.aggregate_level not in (RiskLevel.CRITICAL, RiskLevel.HIGH)
