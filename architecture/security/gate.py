#!/usr/bin/env python3
"""AHOS Lane-B production security-authority gate (P0 — One-Brain sub-PR 1).

WHY
---
Lane-B previously treated security only as *penalties*. UNKNOWN security could
therefore survive with a LOW/MED risk level, earn a high numeric opportunity
score, reach ranking, and trigger a positive opportunity alert. That violates
the canonical doctrine:

    UNKNOWN security  =>  recommendation <= WATCH
    security veto     =>  precedes ranking / opportunity / alerting

SEMANTICS
---------
This gate reuses the *canonical Lane-A semantics* of `discovery/security_gate.py`
(verdict vocabulary + "UNKNOWN != PASS" + "veto precedes ranking") WITHOUT
importing Lane-A, because the Lane-B `architecture/` package must never import
from `discovery/` (isolation law, `architecture/__init__.py`). It introduces no
new security philosophy and makes no new provider calls: it is a pure disposition
over the Evidence the intelligence engine has already produced (plus the
SecurityIntelligence analyzers' own CRITICAL findings).

    SECURITY_VETO      -> recommendation_cap = AVOID   (affirmed-critical failure)
    PASS_WITH_UNKNOWN  -> recommendation_cap = WATCH   (canonical security dimension not established)
    PASS               -> recommendation_cap = PASS    (security established clean)

This module is deterministic and consumes Evidence only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..intelligence.evidence import EvidenceBundle, bool_value, numeric_value

# Verdict vocabulary — identical to discovery/security_gate.py (canonical reference).
VERDICT_VETO = "SECURITY_VETO"
VERDICT_PASS_WITH_UNKNOWN = "PASS_WITH_UNKNOWN"
VERDICT_PASS = "PASS"

CAP_AVOID = "AVOID"
CAP_WATCH = "WATCH"
CAP_PASS = "PASS"

# A sell tax at or above this level is treated as an affirmed critical failure,
# mirroring the Lane-A ``sell_tax_extreme`` CRITICAL registry entry.
EXTREME_SELL_TAX_PCT = 50.0


@dataclass(frozen=True)
class SecurityDisposition:
    """Deterministic security authority for one candidate, computed BEFORE ranking."""

    verdict: str                                  # SECURITY_VETO | PASS_WITH_UNKNOWN | PASS
    recommendation_cap: str                       # AVOID | WATCH | PASS
    veto_reasons: tuple[str, ...] = ()
    unknown_critical: tuple[str, ...] = ()

    def is_veto(self) -> bool:
        return self.verdict == VERDICT_VETO

    def allows_opportunity(self) -> bool:
        """Only an explicit security PASS may proceed to a positive opportunity."""
        return self.verdict == VERDICT_PASS

    def caps_to_watch(self) -> bool:
        return self.recommendation_cap in (CAP_AVOID, CAP_WATCH)


class SecurityGate:
    """Maps already-computed security Evidence into a VETO / WATCH-cap / PASS disposition.

    Reuses the Lane-A canonical registry semantics: affirmed critical failure vetoes;
    an unestablished canonical security dimension caps at WATCH; only a clean,
    established security check passes.
    """

    CONSUMER = "SecurityGate.evaluate"

    # Affirmed-critical checks (value == True/positive ⇒ veto). Mirrors the CRITICAL
    # subset of discovery/security_gate.py VETO_REGISTRY, mapped onto Lane-B evidence.
    def evaluate(
        self,
        evidence: EvidenceBundle,
        security_report: Any | None = None,
    ) -> SecurityDisposition:
        veto_reasons: list[str] = []

        def add_veto(reason: str) -> None:
            if reason not in veto_reasons:
                veto_reasons.append(reason)

        if bool_value(evidence.get("is_honeypot")) is True:
            add_veto("honeypot")
        if bool_value(evidence.get("has_mint_authority")) is True:
            add_veto("mint_authority_active")
        if bool_value(evidence.get("has_freeze_authority")) is True:
            add_veto("freeze_authority_active")
        rug = numeric_value(evidence.get("deployer_past_rug_count"))
        if rug is not None and rug > 0:
            add_veto("deployer_prior_rug")
        sell_tax = numeric_value(evidence.get("sell_tax_pct"))
        if sell_tax is not None and sell_tax >= EXTREME_SELL_TAX_PCT:
            add_veto("sell_tax_extreme")

        # Honor the SecurityIntelligence analyzers' own CRITICAL classifications so we
        # do not invent a second security philosophy (reuse, not duplicate).
        if security_report is not None:
            for finding in getattr(security_report, "findings", ()) or ():
                if getattr(finding, "severity", "") == "CRITICAL":
                    add_veto(str(getattr(finding, "risk_id", "critical_finding")))

        if veto_reasons:
            return SecurityDisposition(
                verdict=VERDICT_VETO,
                recommendation_cap=CAP_AVOID,
                veto_reasons=tuple(veto_reasons),
            )

        # UNKNOWN != PASS: the canonical security dimension must be established.
        # `is_honeypot` is AHOS's canonical contract-security check (one of the four
        # canonical report-evidence keys). If it is not established, cap at WATCH.
        unknown_critical: list[str] = []
        honeypot_atom = evidence.get("is_honeypot")
        if honeypot_atom is None or honeypot_atom.value is None:
            unknown_critical.append("honeypot")

        if unknown_critical:
            return SecurityDisposition(
                verdict=VERDICT_PASS_WITH_UNKNOWN,
                recommendation_cap=CAP_WATCH,
                unknown_critical=tuple(unknown_critical),
            )

        return SecurityDisposition(verdict=VERDICT_PASS, recommendation_cap=CAP_PASS)
