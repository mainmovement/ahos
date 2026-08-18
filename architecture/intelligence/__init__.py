"""AHOS Integrated Intelligence Engine (Phase 4).

Eager exports are limited to Evidence types so `from architecture.intelligence.evidence`
cannot re-enter the orchestrator. Engine symbols resolve lazily.
"""
from .evidence import (
    Evidence,
    EvidenceBundle,
    EvidenceContractError,
    TokenRef,
    materialize_evidence,
    require_evidence_bundle,
)

__all__ = [
    "IntelligenceEngine",
    "IntelligenceReport",
    "Evidence",
    "EvidenceBundle",
    "EvidenceContractError",
    "TokenRef",
    "materialize_evidence",
    "require_evidence_bundle",
    "collect_intel_evidence",
]


def __getattr__(name: str):
    if name in ("IntelligenceEngine", "IntelligenceReport"):
        from .engine import IntelligenceEngine, IntelligenceReport
        return IntelligenceEngine if name == "IntelligenceEngine" else IntelligenceReport
    if name == "collect_intel_evidence":
        from .adapters import collect_intel_evidence
        return collect_intel_evidence
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
