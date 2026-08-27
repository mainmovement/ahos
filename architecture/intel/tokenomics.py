#!/usr/bin/env python3
"""AHOS Tokenomics Analyzer (Lane B intel — P1-2).

Models only what evidence actually supplies:
  - FDV / market cap relationship (circulating proxy)
  - mint / freeze authority flags
  - ownership renounce
  - top-10 holder concentration
  - deployer rug history when present

Unlocks/vesting schedules are NOT invented. Missing → UNKNOWN.
Never upgrades UNKNOWN into a false "safe" tokenomics grade.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

TOKENOMICS_VERSION = "AHOS-TOKENOMICS-v1"


@dataclass
class TokenomicsSignal:
    subject: str
    label: str                          # SOUND | CONCERNING | CRITICAL | UNKNOWN
    fdv_usd: float | None
    market_cap_usd: float | None
    circ_to_fdv_ratio: float | None     # market_cap/fdv when both known
    has_mint_authority: bool | None
    has_freeze_authority: bool | None
    ownership_renounced: bool | None
    top10_concentration_pct: float | None
    deployer_rug_count: int | None
    unlock_vesting_status: str          # always UNKNOWN until real schedule evidence exists
    reasons: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    computed_ts: float = field(default_factory=time.time)
    version: str = TOKENOMICS_VERSION

    @property
    def is_known(self) -> bool:
        return self.label != "UNKNOWN"

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "label": self.label,
            "fdv_usd": self.fdv_usd,
            "market_cap_usd": self.market_cap_usd,
            "circ_to_fdv_ratio": self.circ_to_fdv_ratio,
            "has_mint_authority": self.has_mint_authority,
            "has_freeze_authority": self.has_freeze_authority,
            "ownership_renounced": self.ownership_renounced,
            "top10_concentration_pct": self.top10_concentration_pct,
            "deployer_rug_count": self.deployer_rug_count,
            "unlock_vesting_status": self.unlock_vesting_status,
            "reasons": self.reasons,
            "unknowns": self.unknowns,
            "computed_ts": self.computed_ts,
            "version": self.version,
        }


class TokenomicsAnalyzer:
    def analyze(self, candidate: Any, *, now: float | None = None) -> TokenomicsSignal:
        ts = time.time() if now is None else now
        symbol = str(getattr(candidate, "symbol", "") or "UNKNOWN")
        metrics = getattr(candidate, "metrics", None)
        security = getattr(candidate, "security", None)
        unknowns: list[str] = []
        reasons: list[str] = []

        fdv = getattr(metrics, "fdv_usd", None) if metrics else None
        mcap = getattr(metrics, "market_cap_usd", None) if metrics else None
        mint = getattr(security, "has_mint_authority", None) if security else None
        freeze = getattr(security, "has_freeze_authority", None) if security else None
        renounced = getattr(security, "is_ownership_renounced", None) if security else None
        top10 = getattr(security, "top10_holder_concentration_pct", None) if security else None
        rugs = getattr(security, "deployer_past_rug_count", None) if security else None

        if fdv is None:
            unknowns.append("fdv_usd")
        if mcap is None:
            unknowns.append("market_cap_usd")
        if mint is None:
            unknowns.append("has_mint_authority")
        if freeze is None:
            unknowns.append("has_freeze_authority")
        if renounced is None:
            unknowns.append("is_ownership_renounced")
        if top10 is None:
            unknowns.append("top10_holder_concentration_pct")
        unknowns.append("unlock_vesting_schedule")  # never fabricated

        circ_ratio = None
        if fdv is not None and fdv > 0 and mcap is not None:
            circ_ratio = max(0.0, min(1.0, mcap / fdv))
            if circ_ratio < 0.15:
                reasons.append(f"low circulating/FDV ratio {circ_ratio:.2f}")

        if mint is True:
            reasons.append("mint authority still active")
        if freeze is True:
            reasons.append("freeze authority still active")
        if renounced is False:
            reasons.append("ownership not renounced")
        if top10 is not None and top10 >= 70.0:
            reasons.append(f"top10 concentration {top10:.1f}%")
        if rugs is not None and rugs > 0:
            reasons.append(f"deployer past rug count={rugs}")

        # Label: CRITICAL if authority/concentration/deployer evidence is bad;
        # UNKNOWN if we lack almost all tokenomics fields.
        known_bits = sum(x is not None for x in (fdv, mcap, mint, freeze, renounced, top10, rugs))
        if known_bits == 0:
            label = "UNKNOWN"
        elif (mint is True) or (freeze is True) or (rugs is not None and rugs > 0) or (
                top10 is not None and top10 >= 85.0):
            label = "CRITICAL"
        elif (renounced is False) or (top10 is not None and top10 >= 70.0) or (
                circ_ratio is not None and circ_ratio < 0.15):
            label = "CONCERNING"
        else:
            label = "SOUND"

        return TokenomicsSignal(
            subject=symbol,
            label=label,
            fdv_usd=fdv,
            market_cap_usd=mcap,
            circ_to_fdv_ratio=round(circ_ratio, 4) if circ_ratio is not None else None,
            has_mint_authority=mint,
            has_freeze_authority=freeze,
            ownership_renounced=renounced,
            top10_concentration_pct=top10,
            deployer_rug_count=rugs,
            unlock_vesting_status="UNKNOWN",
            reasons=reasons,
            unknowns=unknowns,
            computed_ts=ts,
        )
