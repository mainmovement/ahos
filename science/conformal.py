"""Split conformal interval and one adaptive step. MAPIE is not installed."""
from __future__ import annotations

from typing import Any

from science.memory import peak_rss_mb


def quantile(values: list[float], level: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    rank = min(len(ordered) - 1, max(0, int(level * len(ordered))))
    return ordered[rank]


def interval(prediction: float, residuals: list[float], alpha: float = 0.1) -> tuple[float, float]:
    width = quantile([abs(value) for value in residuals], 1.0 - alpha)
    return prediction - width, prediction + width


def abstain(low: float, high: float, edge: float, round_trip_cost: float) -> bool:
    crosses = low < 0.0 < high
    too_small = abs(edge) < round_trip_cost
    return crosses or too_small


def adapt_alpha(alpha: float, covered: bool, step: float = 0.01) -> float:
    """One adaptive conformal update. A miss widens the interval."""
    nxt = alpha + step if covered else alpha - step
    return min(0.5, max(0.01, nxt))


def run_shadow() -> dict[str, Any]:
    low, high = interval(0.0, [-0.02, 0.01, 0.03, -0.01])
    must = abstain(low, high, 0.001, 0.002)
    return {
        "id": "M9-03",
        "state": "PARTIAL",
        "library": "mapie",
        "library_present": False,
        "reason": "MAPIE_ABSENT",
        "abstained": must,
        "metric": "abstain_when_interval_crosses_zero_or_edge_below_cost",
        "observed": 1 if must else 0,
        "threshold": 1,
        "threshold_met_on_fixture": must,
        "promoted": False,
        "peak_mb": peak_rss_mb(),
        "applied_to_live": False,
    }
