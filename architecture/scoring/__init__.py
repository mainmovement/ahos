"""AHOS Opportunity Scoring & Evidence Synthesis Subsystem (Section VIII / Phase 4)."""
from .calculator import OpportunityCalculator, ScoreBreakdown

__all__ = [
    "OpportunityScorer",
    "OpportunityScoreReport",
    "EvidenceItem",
    "RiskItem",
    "InvalidationCondition",
    "OpportunityCalculator",
    "ScoreBreakdown",
]


def __getattr__(name: str):
    if name in (
        "OpportunityScorer",
        "OpportunityScoreReport",
        "EvidenceItem",
        "RiskItem",
        "InvalidationCondition",
    ):
        from . import engine as _engine
        return getattr(_engine, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
