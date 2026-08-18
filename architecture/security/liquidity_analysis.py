#!/usr/bin/env python3
"""Liquidity-risk analysis (Phase 5).

LOW_LIQUIDITY (historic floor) stays in RiskEngine so scores do not double-count.
This module adds lock/burn/age evidence and derived LP-quality atoms.
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

UNLOCKED_THRESHOLD_PCT = 30.0
FRESH_POOL_SECONDS = 7 * 86400


@dataclass
class LiquidityReport:
    findings: list[RiskFinding] = field(default_factory=list)
    derived_evidence: list[Evidence] = field(default_factory=list)
    lock_quality: float | None = None


class LiquidityAnalyzer:
    CONSUMER = "LiquidityAnalyzer.analyze"

    def analyze(self, evidence: EvidenceBundle) -> LiquidityReport:
        require_evidence_bundle(evidence, self.CONSUMER)
        findings: list[RiskFinding] = []
        derived: list[Evidence] = []
        ts = evidence.evaluated_at

        locked = numeric_value(evidence.get("liquidity_locked_pct"))
        burned = numeric_value(evidence.get("liquidity_burned_pct"))
        created = numeric_value(evidence.get("pair_created_ts"))
        depth = numeric_value(evidence.get("liquidity_usd"))

        secured = 0.0
        if locked is not None:
            secured = max(secured, locked)
        if burned is not None:
            secured = max(secured, burned)
        lock_quality = None
        if locked is not None or burned is not None:
            lock_quality = max(0.0, min(1.0, secured / 100.0))
            if secured < UNLOCKED_THRESHOLD_PCT:
                findings.append(RiskFinding(
                    "UNLOCKED_LP", "HIGH",
                    f"نقدینگی عمدتاً قفل/سوخته نیست ({secured:.0f}% پوشش)",
                    15.0, "security.liquidity_locked_pct",
                ))

        if created is not None and lock_quality is not None:
            age = max(0.0, ts - created)
            if age < FRESH_POOL_SECONDS and lock_quality < 0.5:
                findings.append(RiskFinding(
                    "YOUNG_UNLOCKED_POOL", "HIGH",
                    "استخر تازه و نقدینگی بدون قفل معنادار — ریسک خروج نقدینگی",
                    12.0, "pair_created_ts",
                ))

        derived.append(make_derived_evidence(
            "lp_lock_quality", "LP lock/burn quality [0,1]", lock_quality,
            provider="security.liquidity", timestamp=ts,
            source_field="liquidity_analysis.lock_quality",
            status="DERIVED" if lock_quality is not None else "UNKNOWN",
        ))
        derived.append(make_derived_evidence(
            "liquidity_depth_usd", "Observed pool depth", depth,
            provider="security.liquidity", timestamp=ts,
            source_field="liquidity_usd",
            status="DERIVED" if depth is not None else "UNKNOWN",
        ))
        return LiquidityReport(
            findings=findings, derived_evidence=derived, lock_quality=lock_quality,
        )
