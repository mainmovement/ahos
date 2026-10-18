"""Paper margin check. Leverage above the cap is a liquidation event, not an order."""
from __future__ import annotations

from dataclasses import dataclass

LEVERAGE_CAP = 2.0


@dataclass(frozen=True, slots=True)
class MarginState:
    leverage: float | None
    event: str
    live: bool


def assess(*, equity_usd: float, notional_usd: float) -> MarginState:
    if equity_usd <= 0 or notional_usd < 0:
        return MarginState(None, "UNKNOWN", False)
    leverage = notional_usd / equity_usd
    if leverage > LEVERAGE_CAP:
        return MarginState(round(leverage, 4), "LIQUIDATION", False)
    return MarginState(round(leverage, 4), "WITHIN_CAP", False)
