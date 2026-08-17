"""
intelligence.risk.base — Risk analyzer interface (evidence-only)

Every risk analyzer is a pure function: evidence in → RiskResult out.
No I/O, no network, no trading. Evidence-only.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List

from core.models.evidence import Evidence


class RiskLevel:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"
    ALL = (LOW, MEDIUM, HIGH, CRITICAL, UNKNOWN)


@dataclass(frozen=True)
class RiskResult:
    """
    Frozen risk assessment for a single risk dimension.

    Attributes
    ----------
    analyzer: identifier string (e.g. "contract_risk")
    level: one of RiskLevel.ALL
    score: 0-100 risk magnitude (higher = more risky)
    reasons: human-readable risk reasons (Persian-ready, but stored English source)
    evidence_refs: list of evidence_ids that support the assessment
    metadata: free-form dict (thresholds, calculations)
    computed_at: epoch seconds
    """

    analyzer: str
    level: str
    score: float
    reasons: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    computed_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if self.analyzer not in ("contract_risk", "liquidity_risk", "concentration_risk", "manipulation_risk", "aggregate"):
            # Allow aggregate and future analyzers, but warn for unknown?
            pass
        if self.level not in RiskLevel.ALL:
            raise ValueError(f"RiskResult.level must be one of {RiskLevel.ALL}, got {self.level!r}")
        if not 0 <= float(self.score) <= 100:
            raise ValueError(f"RiskResult.score 0-100, got {self.score!r}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def is_critical(self) -> bool:
        return self.level == RiskLevel.CRITICAL


class RiskAnalyzer(ABC):
    """
    Abstract risk analyzer — evidence only.

    Implementations must:
      * read only Evidence.value, .confidence, .verification_status
      * treat missing evidence as UNKNOWN (not 0)
      * never fabricate evidence
      * never call trading primitives
    """

    analyzer_id: str = "base"

    @abstractmethod
    def analyze(self, evidence_map: Dict[str, Evidence], now: float | None = None) -> RiskResult:
        """
        Analyze the evidence map for this risk dimension.

        Parameters
        ----------
        evidence_map: dict[str, Evidence] keyed by metric name (e.g. "is_honeypot", "liquidity_usd")
        now: epoch seconds for deterministic tests (default time.time())

        Returns
        -------
        RiskResult (frozen, evidence-anchored)
        """
        raise NotImplementedError

    def evidence_refs_for(self, evidence_map: Dict[str, Evidence], keys: List[str]) -> List[str]:
        return [evidence_map[k].evidence_id for k in keys if k in evidence_map and isinstance(evidence_map[k], Evidence)]
