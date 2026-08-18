#!/usr/bin/env python3
"""Whale wallet-activity analysis (Phase 5).

Consumes EvidenceBundle only. Reads wallet_events / whale_net_flow_1h /
inflow-outflow atoms. Missing wallet data → UNKNOWN, never an invented flow.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..evidence import (
    Evidence,
    EvidenceBundle,
    list_value,
    make_derived_evidence,
    numeric_value,
    require_evidence_bundle,
)
from ...risk.engine import RiskFinding

LARGE_USD = 5_000.0
LARGE_LIQ_SHARE = 0.05


@dataclass(frozen=True)
class WalletMove:
    address: str
    side: str                                    # BUY | SELL
    usd: float
    label: str                                   # WHALE | SMART | INSIDER | RETAIL | UNKNOWN


@dataclass
class WalletActivityReport:
    findings: list[RiskFinding] = field(default_factory=list)
    derived_evidence: list[Evidence] = field(default_factory=list)
    moves: list[WalletMove] = field(default_factory=list)
    net_flow_usd: float | None = None
    label: str = "UNKNOWN"                       # ACCUMULATING | DISTRIBUTING | QUIET | UNKNOWN


class WalletActivityAnalyzer:
    CONSUMER = "WalletActivityAnalyzer.analyze"

    def analyze(self, evidence: EvidenceBundle) -> WalletActivityReport:
        require_evidence_bundle(evidence, self.CONSUMER)
        ts = evidence.evaluated_at
        moves = _parse_moves(list_value(evidence.get("wallet_events")))
        inflow = numeric_value(evidence.get("large_wallet_inflow_usd"))
        outflow = numeric_value(evidence.get("large_wallet_outflow_usd"))
        net = numeric_value(evidence.get("whale_net_flow_1h"))
        depth = numeric_value(evidence.get("liquidity_usd"))

        if moves and net is None:
            net = sum(m.usd if m.side == "BUY" else -m.usd for m in moves)
        if net is None and inflow is not None and outflow is not None:
            net = inflow - outflow

        findings: list[RiskFinding] = []
        derived: list[Evidence] = []

        large = [m for m in moves if _is_large(m.usd, depth)]
        if not large and outflow is not None and depth is not None and depth > 0:
            if outflow >= max(LARGE_USD, depth * LARGE_LIQ_SHARE):
                findings.append(RiskFinding(
                    "LARGE_WALLET_OUTFLOW", "HIGH",
                    f"خروج کیف‌پول بزرگ ${outflow:,.0f} نسبت به عمق استخر",
                    12.0, "whale_net_flow_1h",
                ))
        elif large and sum(m.usd for m in large if m.side == "SELL") >= LARGE_USD:
            sold = sum(m.usd for m in large if m.side == "SELL")
            findings.append(RiskFinding(
                "LARGE_WALLET_OUTFLOW", "HIGH",
                f"خروج کیف‌پول‌های بزرگ ${sold:,.0f} در پنجره مشاهده",
                12.0, "wallet_events",
            ))

        if net is None and not moves and inflow is None and outflow is None:
            label = "UNKNOWN"
        elif net is not None and net > 0:
            label = "ACCUMULATING"
        elif net is not None and net < 0:
            label = "DISTRIBUTING"
        else:
            label = "QUIET"

        derived.append(make_derived_evidence(
            "whale_activity_label", "Wallet activity label", label,
            provider="intelligence.whales", timestamp=ts,
            source_field="wallet_activity.label",
            status="DERIVED" if label != "UNKNOWN" else "UNKNOWN",
        ))
        derived.append(make_derived_evidence(
            "whale_net_flow_observed", "Observed whale net flow USD", net,
            provider="intelligence.whales", timestamp=ts,
            source_field="wallet_activity.net_flow",
            status="DERIVED" if net is not None else "UNKNOWN",
        ))
        return WalletActivityReport(
            findings=findings, derived_evidence=derived,
            moves=moves, net_flow_usd=net, label=label,
        )


def _is_large(usd: float, depth: float | None) -> bool:
    if usd >= LARGE_USD:
        return True
    if depth is not None and depth > 0 and usd >= depth * LARGE_LIQ_SHARE:
        return True
    return False


def _parse_moves(raw: list[Any]) -> list[WalletMove]:
    out: list[WalletMove] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            usd = float(item.get("usd") or item.get("amount_usd") or 0.0)
        except (TypeError, ValueError):
            continue
        if usd <= 0:
            continue
        side = str(item.get("side") or item.get("direction") or "").upper()
        if side not in ("BUY", "SELL"):
            continue
        label = str(item.get("label") or "UNKNOWN").upper()
        if label not in ("WHALE", "SMART", "INSIDER", "RETAIL", "UNKNOWN"):
            label = "UNKNOWN"
        out.append(WalletMove(
            address=str(item.get("address") or "unknown"),
            side=side, usd=usd, label=label,
        ))
    return out
