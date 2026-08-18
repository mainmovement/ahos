#!/usr/bin/env python3
"""Composed whale intelligence signals (Phase 5).

Fuses wallet activity, smart-money classification, and holder evidence into
one Evidence-compatible report. Does not re-emit HIGH_HOLDER_CONCENTRATION
(that lives in security/holder_analysis) so RiskEngine cannot double-count.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..evidence import (
    Evidence,
    EvidenceBundle,
    make_derived_evidence,
    numeric_value,
    require_evidence_bundle,
)
from ...risk.engine import RiskFinding
from .smart_money_detector import SmartMoneyDetector, SmartMoneyReport
from .wallet_activity import WalletActivityAnalyzer, WalletActivityReport

TRAP_PRICE_CHANGE = 0.20                         # +20% while accumulating
DANGEROUS_TOP10 = 80.0


@dataclass
class WhaleIntelligenceReport:
    findings: list[RiskFinding] = field(default_factory=list)
    derived_evidence: list[Evidence] = field(default_factory=list)
    label: str = "UNKNOWN"                       # ACCUMULATING | DISTRIBUTING | STABLE | DANGEROUS | UNKNOWN
    activity: WalletActivityReport | None = None
    smart_money: SmartMoneyReport | None = None

    def has(self, risk_id: str) -> bool:
        return any(f.risk_id == risk_id for f in self.findings)


class WhaleIntelligence:
    """Evidence → whale activity + smart money + composed signal."""

    CONSUMER = "WhaleIntelligence.analyze"

    def __init__(
        self,
        activity: WalletActivityAnalyzer | None = None,
        smart_money: SmartMoneyDetector | None = None,
    ):
        self.activity = activity or WalletActivityAnalyzer()
        self.smart_money = smart_money or SmartMoneyDetector(activity=self.activity)

    def analyze(self, evidence: EvidenceBundle) -> WhaleIntelligenceReport:
        require_evidence_bundle(evidence, self.CONSUMER)
        ts = evidence.evaluated_at
        activity = self.activity.analyze(evidence)
        smart = self.smart_money.analyze(evidence, activity=activity)

        top10 = numeric_value(evidence.get("top10_concentration"))
        if top10 is None:
            top10 = numeric_value(evidence.get("whale_top10_share"))
        top1 = numeric_value(evidence.get("top1_concentration"))
        prev = numeric_value(evidence.get("previous_top10_concentration"))
        px = numeric_value(evidence.get("price_change_1h"))

        label = _compose_label(top10, top1, prev, activity.label, smart.label)
        findings: list[RiskFinding] = []
        seen: set[str] = set()
        derived: list[Evidence] = []
        for report in (activity, smart):
            for finding in report.findings:
                if finding.risk_id not in seen:
                    findings.append(finding)
                    seen.add(finding.risk_id)
            derived.extend(report.derived_evidence)

        # Trap: accumulation into a rising thin float — only when movement evidence exists.
        accumulating = activity.label == "ACCUMULATING" or (
            prev is not None and top10 is not None and (top10 - prev) >= 3.0
        )
        if accumulating and px is not None and px >= TRAP_PRICE_CHANGE:
            findings.append(RiskFinding(
                "WHALE_TRAP", "HIGH",
                "الگوی تله: قیمت بالا رفته و همزمان نهنگ‌ها در حال انباشت‌اند",
                15.0, "whale_activity_label",
            ))

        derived.append(make_derived_evidence(
            "whale_label", "Composed whale regime", label,
            provider="intelligence.whales", timestamp=ts,
            source_field="whale_signals.label",
            status="DERIVED" if label != "UNKNOWN" else "UNKNOWN",
        ))
        derived.append(make_derived_evidence(
            "whale_bias", "Whale flow bias",
            1 if label == "ACCUMULATING" else (-1 if label == "DISTRIBUTING" else 0),
            provider="intelligence.whales", timestamp=ts,
            source_field="whale_signals.bias",
            status="DERIVED" if label != "UNKNOWN" else "UNKNOWN",
        ))
        return WhaleIntelligenceReport(
            findings=findings, derived_evidence=derived, label=label,
            activity=activity, smart_money=smart,
        )


def _compose_label(top10: float | None, top1: float | None, prev: float | None,
                   activity_label: str, smart_label: str) -> str:
    if top10 is not None and top10 >= DANGEROUS_TOP10:
        return "DANGEROUS"
    if top1 is not None and top1 >= 25.0:
        return "DANGEROUS"
    if activity_label == "DISTRIBUTING" or smart_label == "DISTRIBUTING":
        return "DISTRIBUTING"
    if activity_label == "ACCUMULATING" or smart_label == "ACCUMULATING":
        return "ACCUMULATING"
    if prev is not None and top10 is not None:
        delta = top10 - prev
        if delta <= -3.0:
            return "DISTRIBUTING"
        if delta >= 3.0:
            return "ACCUMULATING"
    if top10 is not None or activity_label == "QUIET":
        return "STABLE"
    return "UNKNOWN"
