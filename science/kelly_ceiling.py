"""Drawdown-capped fractional Kelly. cvxpy is not installed.

Busseti, Ryu, and Boyd give the constrained-Kelly program. The ceiling here
is the closed form that the leverage ladder is not allowed to cross.
"""
from __future__ import annotations

from typing import Any

from science.memory import peak_rss_mb

KELLY_CAP = 0.25


def ceiling(edge: float | None, odds: float | None, *, stop_pct: float, drawdown_limit: float) -> float | None:
    if edge is None or odds is None or odds <= 0 or stop_pct <= 0 or drawdown_limit <= 0:
        return None
    full = edge / odds
    if full <= 0:
        return 0.0
    drawdown_cap = drawdown_limit / stop_pct
    return round(min(KELLY_CAP, full, drawdown_cap), 4)


def run_shadow() -> dict[str, Any]:
    value = ceiling(0.9, 1.0, stop_pct=0.1, drawdown_limit=0.02)
    return {
        "id": "M9-07",
        "state": "PARTIAL",
        "library": "cvxpy",
        "library_present": False,
        "reason": "CVXPY_ABSENT",
        "ceiling": value,
        "metric": "leverage_above_ceiling",
        "observed": 0 if value is not None and value <= KELLY_CAP else 1,
        "threshold": 0,
        "threshold_met_on_fixture": value is not None and value <= 0.2,
        "promoted": False,
        "peak_mb": peak_rss_mb(),
        "applied_to_live": False,
    }
