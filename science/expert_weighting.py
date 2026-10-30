"""Exponentiated-gradient experts and a short ADWIN check. river is not installed."""
from __future__ import annotations

import math
from typing import Any

from science.memory import peak_rss_mb


def exponentiated_gradient(weights: list[float], rewards: list[float], eta: float = 0.1) -> list[float]:
    if len(weights) != len(rewards) or not weights:
        return []
    grown = [weight * math.exp(eta * reward) for weight, reward in zip(weights, rewards)]
    total = sum(grown) or 1.0
    return [round(value / total, 6) for value in grown]


def adwin_drift(window: list[float]) -> bool:
    """True when the two halves disagree by more than a simple bound."""
    if len(window) < 4:
        return False
    mid = len(window) // 2
    left = window[:mid]
    right = window[mid:]
    mean_l = sum(left) / len(left)
    mean_r = sum(right) / len(right)
    bound = 1.0 / math.sqrt(len(window))
    return abs(mean_l - mean_r) > bound


def run_shadow() -> dict[str, Any]:
    weights = exponentiated_gradient([0.5, 0.5], [1.0, -1.0])
    drift = adwin_drift([0.0, 0.0, 1.0, 1.0])
    return {
        "id": "M9-09",
        "state": "PARTIAL",
        "library": "river",
        "library_present": False,
        "reason": "RIVER_ABSENT",
        "weights": weights,
        "drift": drift,
        "metric": "applied_to_live",
        "observed": 0,
        "threshold": 0,
        "threshold_met_on_fixture": abs(sum(weights) - 1.0) < 1e-3 and weights[0] > weights[1],
        "promoted": False,
        "peak_mb": peak_rss_mb(),
        "applied_to_live": False,
    }
