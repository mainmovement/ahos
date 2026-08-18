#!/usr/bin/env python3
"""Security intelligence suite (Phase 5).

Runs the four Evidence-only analyzers and returns a single SecurityReport
that RiskEngine / IntelligenceEngine can merge. No raw candidate access.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..intelligence.evidence import Evidence, EvidenceBundle, require_evidence_bundle
from ..risk.engine import RiskFinding
from .contract_analysis import ContractAnalyzer, ContractReport
from .holder_analysis import HolderAnalyzer, HolderReport
from .liquidity_analysis import LiquidityAnalyzer, LiquidityReport
from .manipulation_detection import ManipulationDetector, ManipulationReport


@dataclass
class SecurityReport:
    findings: list[RiskFinding] = field(default_factory=list)
    derived_evidence: list[Evidence] = field(default_factory=list)
    contract: ContractReport | None = None
    liquidity: LiquidityReport | None = None
    holders: HolderReport | None = None
    manipulation: ManipulationReport | None = None

    def has(self, risk_id: str) -> bool:
        return any(f.risk_id == risk_id for f in self.findings)


class SecurityIntelligence:
    """Contract + liquidity + holders + manipulation, Evidence in / Evidence out."""

    CONSUMER = "SecurityIntelligence.analyze"

    def __init__(
        self,
        contract: ContractAnalyzer | None = None,
        liquidity: LiquidityAnalyzer | None = None,
        holders: HolderAnalyzer | None = None,
        manipulation: ManipulationDetector | None = None,
    ):
        self.contract = contract or ContractAnalyzer()
        self.liquidity = liquidity or LiquidityAnalyzer()
        self.holders = holders or HolderAnalyzer()
        self.manipulation = manipulation or ManipulationDetector()

    def analyze(self, evidence: EvidenceBundle) -> SecurityReport:
        require_evidence_bundle(evidence, self.CONSUMER)
        contract = self.contract.analyze(evidence)
        liquidity = self.liquidity.analyze(evidence)
        holders = self.holders.analyze(evidence)
        manipulation = self.manipulation.analyze(evidence)

        findings: list[RiskFinding] = []
        seen: set[str] = set()
        derived: list[Evidence] = []
        for report in (contract, liquidity, holders, manipulation):
            for finding in report.findings:
                if finding.risk_id not in seen:
                    findings.append(finding)
                    seen.add(finding.risk_id)
            derived.extend(report.derived_evidence)

        return SecurityReport(
            findings=findings,
            derived_evidence=derived,
            contract=contract,
            liquidity=liquidity,
            holders=holders,
            manipulation=manipulation,
        )
