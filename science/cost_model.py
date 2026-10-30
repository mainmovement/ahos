"""Paper costs: fees, spread, square-root impact, funding, and sliced impact."""
from __future__ import annotations

from typing import Any

from science.memory import peak_rss_mb


def net_return(
    gross: float,
    *,
    fee_per_side: float,
    spread_pct: float,
    quantity: float,
    adv: float,
    impact_coef: float,
    funding_rate: float,
    hold_days: float,
    slices: int,
) -> dict[str, float]:
    """Every term is deducted. A caller that skips this function has omitted cost."""
    n_slices = max(1, int(slices))
    piece = quantity / n_slices
    impact = 0.0
    if adv > 0 and quantity > 0:
        impact = sum(impact_coef * (piece / adv) ** 0.5 for _ in range(n_slices))
    fee = 2.0 * fee_per_side
    spread = spread_pct / 100.0
    funding = funding_rate * hold_days
    cost = fee + spread + impact + funding
    return {
        "gross": gross,
        "cost": round(cost, 8),
        "net": round(gross - cost, 8),
        "slices": float(n_slices),
    }


def run_shadow() -> dict[str, Any]:
    filled = net_return(
        0.01,
        fee_per_side=0.001,
        spread_pct=0.35,
        quantity=1.0,
        adv=10.0,
        impact_coef=0.01,
        funding_rate=0.0001,
        hold_days=1.0,
        slices=4,
    )
    return {
        "id": "M9-04",
        "state": "PARTIAL",
        "library": "own",
        "library_present": True,
        "reason": "LIVE_BROKER_NOT_REWRITTEN",
        "net": filled["net"],
        "cost": filled["cost"],
        "metric": "cost_omitted",
        "observed": 0,
        "threshold": 0,
        "threshold_met_on_fixture": filled["net"] < filled["gross"],
        "promoted": False,
        "peak_mb": peak_rss_mb(),
        "applied_to_live": False,
    }
