"""Domain-general cognitive vocabularies. Not a capability claim."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CapabilityStatus(str, Enum):
    IMPLEMENTED_AND_VERIFIED = "IMPLEMENTED_AND_VERIFIED"
    IMPLEMENTED_BUT_UNVERIFIED = "IMPLEMENTED_BUT_UNVERIFIED"
    PARTIAL = "PARTIAL"
    DOCUMENTATION_ONLY = "DOCUMENTATION_ONLY"
    PLACEHOLDER = "PLACEHOLDER"
    MISSING = "MISSING"
    CONFLICTING = "CONFLICTING"
    DEPRECATED = "DEPRECATED"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


class HypothesisState(str, Enum):
    PROPOSED = "PROPOSED"
    UNDER_REVIEW = "UNDER_REVIEW"
    TESTING = "TESTING"
    SUPPORTED = "SUPPORTED"
    WEAKENED = "WEAKENED"
    REJECTED = "REJECTED"
    UNCERTAIN = "UNCERTAIN"
    SUPERSEDED = "SUPERSEDED"


class EpistemicState(str, Enum):
    KNOWN = "KNOWN"
    KNOWN_BUT_UNCERTAIN = "KNOWN_BUT_UNCERTAIN"
    UNKNOWN = "UNKNOWN"
    CONTRADICTORY = "CONTRADICTORY"
    NOVEL = "NOVEL"
    POTENTIALLY_IMPORTANT_NOVELTY = "POTENTIALLY_IMPORTANT_NOVELTY"


class CreativeClass(str, Enum):
    IDEA = "IDEA"
    HYPOTHESIS = "HYPOTHESIS"
    EXPERIMENT = "EXPERIMENT"
    VALIDATED_KNOWLEDGE = "VALIDATED_KNOWLEDGE"
    REJECTED = "REJECTED"
    UNCERTAIN = "UNCERTAIN"


class AutonomyLevel(str, Enum):
    L0_OBSERVE = "L0_OBSERVE"
    L1_ANALYZE = "L1_ANALYZE"
    L2_RECOMMEND = "L2_RECOMMEND"
    L3_AUTONOMOUS_EXPERIMENT = "L3_AUTONOMOUS_EXPERIMENT"
    L4_PAPER_TRADING = "L4_PAPER_TRADING"
    L5_SIMULATED_EXECUTION = "L5_SIMULATED_EXECUTION"
    L6_LIMITED_LIVE_EXECUTION = "L6_LIMITED_LIVE_EXECUTION"
    L7_CONTROLLED_AUTONOMOUS_EXECUTION = "L7_CONTROLLED_AUTONOMOUS_EXECUTION"


# Cognitive Core must not claim paper-trading autonomy. Frozen paper_trading/
# exists independently; this ceiling is for the cognitive package only.
CURRENT_AUTONOMY_CEILING = AutonomyLevel.L1_ANALYZE


class DomainKind(str, Enum):
    COGNITIVE_CORE = "COGNITIVE_CORE"
    FINANCIAL_ADAPTER = "FINANCIAL_ADAPTER"
    OTHER_ADAPTER = "OTHER_ADAPTER"


@dataclass
class CognitiveClaim:
    claim_id: str
    statement: str
    epistemic: EpistemicState
    domain: DomainKind = DomainKind.COGNITIVE_CORE
    evidence_refs: list[str] = field(default_factory=list)
    confidence: float | None = None
    provenance: dict[str, Any] = field(default_factory=dict)
    status: CapabilityStatus = CapabilityStatus.PARTIAL

    def as_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "statement": self.statement,
            "epistemic": self.epistemic.value,
            "domain": self.domain.value,
            "evidence_refs": list(self.evidence_refs),
            "confidence": self.confidence,
            "provenance": dict(self.provenance),
            "status": self.status.value,
        }


@dataclass(frozen=True)
class CapabilityAssessment:
    """One row of the AGI/ACI capability matrix. Not a performance score."""

    capability: str
    status: CapabilityStatus
    evidence: tuple[str, ...] = ()
    architecture_target: str = ""
    gap: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "capability": self.capability,
            "status": self.status.value,
            "evidence": list(self.evidence),
            "architecture_target": self.architecture_target,
            "gap": self.gap,
        }
