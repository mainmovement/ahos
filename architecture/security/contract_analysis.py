#!/usr/bin/env python3
"""Contract-risk analysis (Phase 5).

Consumes EvidenceBundle only. Emits RiskFindings that match the historic
deterministic floor for honeypot / mint / freeze / unverified, plus additive
ownership, proxy, and deployer-rug checks. UNKNOWN never becomes PASS.
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


@dataclass
class ContractReport:
    findings: list[RiskFinding] = field(default_factory=list)
    derived_evidence: list[Evidence] = field(default_factory=list)
    coverage: dict[str, str] = field(default_factory=dict)


class ContractAnalyzer:
    CONSUMER = "ContractAnalyzer.analyze"

    def analyze(self, evidence: EvidenceBundle) -> ContractReport:
        require_evidence_bundle(evidence, self.CONSUMER)
        findings: list[RiskFinding] = []
        derived: list[Evidence] = []
        coverage: dict[str, str] = {}
        ts = evidence.evaluated_at

        def mark(key: str, known: bool) -> None:
            coverage[key] = "VERIFIED" if known else "UNKNOWN"

        honeypot = bool_value(evidence.get("is_honeypot"))
        mark("is_honeypot", honeypot is not None)
        if honeypot is True:
            findings.append(RiskFinding(
                "CRITICAL_HONEYPOT", "CRITICAL",
                "قرارداد به عنوان Honeypot شناسایی شد",
                100.0, "security.is_honeypot",
            ))

        mint = bool_value(evidence.get("has_mint_authority"))
        mark("has_mint_authority", mint is not None)
        if mint is True:
            findings.append(RiskFinding(
                "MINT_AUTHORITY_ACTIVE", "HIGH",
                "قابلیت ضرب توکن نامحدود فعال است",
                20.0, "security.has_mint_authority",
            ))

        freeze = bool_value(evidence.get("has_freeze_authority"))
        mark("has_freeze_authority", freeze is not None)
        if freeze is True:
            findings.append(RiskFinding(
                "FREEZE_AUTHORITY_ACTIVE", "HIGH",
                "قابلیت مسدودسازی کیف‌پول‌ها فعال است",
                20.0, "security.has_freeze_authority",
            ))

        verified = bool_value(evidence.get("is_contract_verified"))
        mark("is_contract_verified", verified is not None)
        if verified is False:
            findings.append(RiskFinding(
                "UNVERIFIED_CONTRACT", "MED",
                "سورس کد قرارداد تایید نشده است",
                10.0, "security.is_contract_verified",
            ))

        renounced = bool_value(evidence.get("is_ownership_renounced"))
        mark("is_ownership_renounced", renounced is not None)
        if renounced is False:
            findings.append(RiskFinding(
                "OWNERSHIP_NOT_RENOUNCED", "MED",
                "مالکیت قرارداد سلب نشده است — ادمین می‌تواند قوانین را عوض کند",
                10.0, "security.is_ownership_renounced",
            ))

        proxy = bool_value(evidence.get("is_proxy"))
        mark("is_proxy", proxy is not None)
        if proxy is True:
            findings.append(RiskFinding(
                "PROXY_UPGRADEABLE", "HIGH",
                "قرارداد پروکسی/قابل‌ارتقا است — منطق می‌تواند عوض شود",
                15.0, "security.is_proxy",
            ))

        rugs = numeric_value(evidence.get("deployer_past_rug_count"))
        mark("deployer_past_rug_count", rugs is not None)
        if rugs is not None and rugs > 0:
            findings.append(RiskFinding(
                "DEPLOYER_PRIOR_RUG", "CRITICAL",
                f"سازنده قرارداد سابقه {int(rugs)} بار رِگ‌پول دارد",
                40.0, "security.deployer_past_rug_count",
            ))

        if any(f.severity == "CRITICAL" for f in findings):
            label = "VETO"
        elif findings:
            label = "ELEVATED"
        elif all(v == "VERIFIED" for v in coverage.values()) and coverage:
            label = "CLEAN"
        else:
            label = "INCOMPLETE"

        derived.append(make_derived_evidence(
            "contract_risk_label", "Contract risk label", label,
            provider="security.contract", timestamp=ts,
            source_field="contract_analysis.label",
        ))
        return ContractReport(findings=findings, derived_evidence=derived, coverage=coverage)
