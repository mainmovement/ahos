#!/usr/bin/env python3
"""Manipulation / suspicious-pattern detection (Phase 5).

Wash-trading uses the same WASH_SUSPECTED risk_id as the historic floor so
RiskEngine can merge. Tax abuse and volume/tx divergence are additive and
only fire on known evidence.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..intelligence.evidence import (
    Evidence,
    EvidenceBundle,
    bool_value,
    make_derived_evidence,
    numeric_value,
    require_evidence_bundle,
)
from ..risk.engine import RiskFinding

EXTREME_SELL_TAX = 25.0
HIGH_BUY_TAX = 10.0
VELOCITY_DIVERGENCE = 4.0
MIN_TXNS_FOR_VELOCITY = 10


@dataclass
class ManipulationReport:
    findings: list[RiskFinding] = field(default_factory=list)
    derived_evidence: list[Evidence] = field(default_factory=list)
    suspicious: bool = False


class ManipulationDetector:
    CONSUMER = "ManipulationDetector.analyze"

    def analyze(self, evidence: EvidenceBundle) -> ManipulationReport:
        require_evidence_bundle(evidence, self.CONSUMER)
        findings: list[RiskFinding] = []
        derived: list[Evidence] = []
        ts = evidence.evaluated_at

        if bool_value(evidence.get("wash_suspected")) is True:
            findings.append(RiskFinding(
                "WASH_SUSPECTED", "HIGH",
                "الگوی معاملات صوری (wash trading) در شواهد شتاب حجم",
                15.0, "virality.wash_suspected",
            ))

        if bool_value(evidence.get("is_paid_promotion")) is True:
            findings.append(RiskFinding(
                "PAID_HYPE", "MED",
                "توجه این توکن خریداری شده است، نه ارگانیک",
                5.0, "virality.is_paid_promotion",
            ))

        sell_tax = numeric_value(evidence.get("sell_tax_pct"))
        if sell_tax is not None and sell_tax > EXTREME_SELL_TAX:
            findings.append(RiskFinding(
                "EXTREME_SELL_TAX", "CRITICAL",
                f"مالیات فروش افراطی ({sell_tax:.1f}%) — خروج عملاً مسدود است",
                40.0, "security.sell_tax_pct",
            ))

        buy_tax = numeric_value(evidence.get("buy_tax_pct"))
        if buy_tax is not None and buy_tax > HIGH_BUY_TAX:
            findings.append(RiskFinding(
                "HIGH_BUY_TAX", "MED",
                f"مالیات خرید بالا ({buy_tax:.1f}%)",
                8.0, "security.buy_tax_pct",
            ))

        velocity = numeric_value(evidence.get("volume_velocity"))
        buys = numeric_value(evidence.get("txns_1h_buys"))
        sells = numeric_value(evidence.get("txns_1h_sells"))
        if velocity is not None and buys is not None and sells is not None:
            total_tx = buys + sells
            if velocity >= VELOCITY_DIVERGENCE and total_tx < MIN_TXNS_FOR_VELOCITY:
                findings.append(RiskFinding(
                    "VOLUME_TX_DIVERGENCE", "MED",
                    "شتاب حجم بدون تراکنش کافی — الگوی مشکوک ساختگی",
                    10.0, "metrics.volume_velocity",
                ))

        flag = bool(findings)
        derived.append(make_derived_evidence(
            "manipulation_flag", "Manipulation suspected", flag,
            provider="security.manipulation", timestamp=ts,
            source_field="manipulation_detection.flag",
        ))
        return ManipulationReport(
            findings=findings, derived_evidence=derived, suspicious=flag,
        )
