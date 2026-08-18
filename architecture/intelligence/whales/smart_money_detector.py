#!/usr/bin/env python3
"""Smart-money / wallet classification (Phase 5).

Classifies observed wallets from Evidence (never from raw chain scrapes).
Insider distribution is a risk; smart-money accumulation is a derived
signal, not a buy recommendation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict

from ..evidence import (
    Evidence,
    EvidenceBundle,
    make_derived_evidence,
    require_evidence_bundle,
)
from ...risk.engine import RiskFinding
from .wallet_activity import WalletActivityAnalyzer, WalletActivityReport, WalletMove

INSIDER_DUMP_USD = 1_000.0


@dataclass
class SmartMoneyReport:
    findings: list[RiskFinding] = field(default_factory=list)
    derived_evidence: list[Evidence] = field(default_factory=list)
    classifications: dict[str, str] = field(default_factory=dict)
    smart_net_usd: float | None = None
    insider_net_usd: float | None = None
    label: str = "UNKNOWN"                       # ACCUMULATING | DISTRIBUTING | MIXED | UNKNOWN


class SmartMoneyDetector:
    CONSUMER = "SmartMoneyDetector.analyze"

    def __init__(self, activity: WalletActivityAnalyzer | None = None):
        self.activity = activity or WalletActivityAnalyzer()

    def analyze(self, evidence: EvidenceBundle,
                activity: WalletActivityReport | None = None) -> SmartMoneyReport:
        require_evidence_bundle(evidence, self.CONSUMER)
        act = activity or self.activity.analyze(evidence)
        ts = evidence.evaluated_at

        classes: dict[str, str] = {}
        nets: dict[str, float] = defaultdict(float)
        for move in act.moves:
            klass = _classify(move)
            classes[move.address] = klass
            signed = move.usd if move.side == "BUY" else -move.usd
            nets[klass] += signed

        smart_net = nets.get("SMART")
        insider_net = nets.get("INSIDER")
        if smart_net is None and insider_net is None and not classes:
            label = "UNKNOWN"
        elif (smart_net or 0) > 0 and (insider_net or 0) >= 0:
            label = "ACCUMULATING"
        elif (smart_net or 0) < 0 or (insider_net or 0) < 0:
            label = "DISTRIBUTING"
        elif classes:
            label = "MIXED"
        else:
            label = "UNKNOWN"

        findings: list[RiskFinding] = []
        if insider_net is not None and insider_net <= -INSIDER_DUMP_USD:
            findings.append(RiskFinding(
                "INSIDER_DISTRIBUTION", "HIGH",
                f"کیف‌پول‌های داخلی در حال توزیع هستند (${insider_net:,.0f})",
                15.0, "wallet_events",
            ))

        derived = [
            make_derived_evidence(
                "smart_money_label", "Smart-money flow label", label,
                provider="intelligence.whales", timestamp=ts,
                source_field="smart_money.label",
                status="DERIVED" if label != "UNKNOWN" else "UNKNOWN",
            ),
            make_derived_evidence(
                "smart_money_net_usd", "Smart-money net USD", smart_net,
                provider="intelligence.whales", timestamp=ts,
                source_field="smart_money.net",
                status="DERIVED" if smart_net is not None else "UNKNOWN",
            ),
            make_derived_evidence(
                "wallet_classifications", "Wallet classifications",
                dict(classes) if classes else None,
                provider="intelligence.whales", timestamp=ts,
                source_field="smart_money.classifications",
                status="DERIVED" if classes else "UNKNOWN",
            ),
        ]
        return SmartMoneyReport(
            findings=findings, derived_evidence=derived,
            classifications=classes, smart_net_usd=smart_net,
            insider_net_usd=insider_net, label=label,
        )


def _classify(move: WalletMove) -> str:
    if move.label in ("SMART", "INSIDER", "WHALE", "RETAIL"):
        return move.label
    if move.usd >= 10_000:
        return "WHALE"
    return "UNKNOWN"
