"""M13.x Pump Hunter (Paper-Only Alert Module).
Requires >=2 independent public signal families AND security gate PASS before logging a paper-only alert.
Contains zero live order or broker execution paths.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

VALID_SIGNAL_FAMILIES = frozenset(
    {
        "volume_atr_anomaly",
        "public_whale_inflow",
        "orderbook_depth_imbalance",
        "social_velocity_spike",
        "onchain_liquidity_add",
    }
)


@dataclass(frozen=True, slots=True)
class PumpAlertResult:
    symbol: str
    state: str
    paper_only: bool
    executes_order: bool
    corroborated_families: tuple[str, ...]
    security_gate: str
    reason: str


def evaluate_pump_candidate(
    *,
    symbol: str,
    signal_families: Sequence[str],
    security_gate: str,
    spread_bps: float = 15.0,
) -> PumpAlertResult:
    """Evaluate a candidate anomaly strictly as a paper-only alert."""
    fams = tuple(sorted({f for f in signal_families if f in VALID_SIGNAL_FAMILIES}))
    if security_gate != "PASS":
        return PumpAlertResult(
            symbol=symbol,
            state="VETOED_SECURITY",
            paper_only=True,
            executes_order=False,
            corroborated_families=fams,
            security_gate=security_gate,
            reason="token_security_veto",
        )
    if spread_bps > 150.0:
        return PumpAlertResult(
            symbol=symbol,
            state="VETOED_ILLIQUID_SPREAD",
            paper_only=True,
            executes_order=False,
            corroborated_families=fams,
            security_gate=security_gate,
            reason="spread_exceeds_cap",
        )
    if len(fams) < 2:
        return PumpAlertResult(
            symbol=symbol,
            state="WATCH_ONLY_SINGLE_FAMILY",
            paper_only=True,
            executes_order=False,
            corroborated_families=fams,
            security_gate=security_gate,
            reason="requires_at_least_2_independent_signal_families",
        )
    return PumpAlertResult(
        symbol=symbol,
        state="PAPER_ALERT",
        paper_only=True,
        executes_order=False,
        corroborated_families=fams,
        security_gate=security_gate,
        reason="two_family_corroborated_paper_alert",
    )
