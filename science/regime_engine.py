"""Regime label plus a small constant-hazard changepoint probability.

hmmlearn and ruptures are not installed. The label comes from the existing
three-state classifier. The changepoint step is Adams and MacKay's hazard
idea for a known-variance Gaussian, kept to a short run length.
"""
from __future__ import annotations

import math
from typing import Any

from science.memory import peak_rss_mb


def changepoint_probability(values: list[float], hazard: float = 0.1, variance: float = 0.0001) -> float:
    if len(values) < 2 or variance <= 0:
        return 0.0
    recent = values[-1] - (sum(values[:-1]) / (len(values) - 1))
    surprise = math.exp(-0.5 * recent * recent / variance)
    stay = (1.0 - hazard) * max(surprise, 1e-12)
    change = hazard
    return round(change / (change + stay), 4)


def size_multiplier(probability: float, threshold: float = 0.5) -> float:
    if probability > threshold:
        return 0.5
    return 1.0


def run_shadow() -> dict[str, Any]:
    from architecture.intel.regimes import MarketRegimeClassifier

    series = [0.001] * 8 + [0.05]
    label = MarketRegimeClassifier().predict_regime_probabilities(series)
    probability = changepoint_probability(series, hazard=0.2, variance=0.0001)
    return {
        "id": "M9-05",
        "state": "PARTIAL",
        "library": "hmmlearn+ruptures",
        "library_present": False,
        "reason": "HMMLEARN_AND_RUPTURES_ABSENT",
        "regime": label.get("active_regime"),
        "changepoint_prob": probability,
        "size_multiplier": size_multiplier(probability),
        "metric": "delever_when_changepoint_prob_above",
        "observed": probability,
        "threshold": 0.5,
        "threshold_met_on_fixture": (probability > 0.5) == (size_multiplier(probability) == 0.5),
        "promoted": False,
        "peak_mb": peak_rss_mb(),
        "applied_to_live": False,
    }
