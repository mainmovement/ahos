#!/usr/bin/env python3
"""Holder-concentration analysis (Phase 5).

HIGH_HOLDER_CONCENTRATION (>70%) is the historic floor finding — same id,
penalty and wording so RiskEngine can merge without double-counting.
Top-1 dominance and thin holder bases fire only when that evidence exists.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..intelligence.evidence import (
    Evidence,
    EvidenceBundle,
    make_derived_evidence,
    numeric_value,
    require_evidence_bundle,
)
from ..risk.engine import RiskFinding

CONCENTRATION_FLOOR = 70.0
SINGLE_WALLET_CRITICAL = 25.0
THIN_HOLDER_COUNT = 50


@dataclass
class HolderReport:
    findings: list[RiskFinding] = field(default_factory=list)
    derived_evidence: list[Evidence] = field(default_factory=list)
    top10_share: float | None = None


class HolderAnalyzer:
    CONSUMER = "HolderAnalyzer.analyze"

    def analyze(self, evidence: EvidenceBundle) -> HolderReport:
        require_evidence_bundle(evidence, self.CONSUMER)
        findings: list[RiskFinding] = []
        derived: list[Evidence] = []
        ts = evidence.evaluated_at

        top10 = numeric_value(evidence.get("top10_concentration"))
        if top10 is None:
            top10 = numeric_value(evidence.get("whale_top10_share"))
        top1 = numeric_value(evidence.get("top1_concentration"))
        holders = numeric_value(evidence.get("holder_count"))

        if top10 is not None and top10 > CONCENTRATION_FLOOR:
            findings.append(RiskFinding(
                "HIGH_HOLDER_CONCENTRATION", "HIGH",
                f"تمرکز شدید هولدرها ({top10:.1f}%)",
                25.0, "security.top10_holder_concentration_pct",
            ))

        if top1 is not None and top1 >= SINGLE_WALLET_CRITICAL:
            findings.append(RiskFinding(
                "SINGLE_WALLET_DOMINANCE", "HIGH",
                f"یک کیف‌پول {top1:.1f}% عرضه را در اختیار دارد — ریسک تک‌نقطه‌ای",
                20.0, "security.top1_holder_concentration_pct",
            ))

        if holders is not None and holders < THIN_HOLDER_COUNT:
            findings.append(RiskFinding(
                "THIN_HOLDER_BASE", "MED",
                f"تعداد هولدر بسیار کم ({int(holders)}) — بازار واقعی وجود ندارد",
                12.0, "holder_count",
            ))

        dispersion = None
        if top10 is not None:
            dispersion = max(0.0, min(1.0, 1.0 - (top10 / 100.0)))
        derived.append(make_derived_evidence(
            "holder_dispersion", "Inverse top-10 concentration [0,1]", dispersion,
            provider="security.holders", timestamp=ts,
            source_field="holder_analysis.dispersion",
            status="DERIVED" if dispersion is not None else "UNKNOWN",
        ))
        return HolderReport(
            findings=findings, derived_evidence=derived, top10_share=top10,
        )
