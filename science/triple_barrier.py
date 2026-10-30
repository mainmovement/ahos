"""Triple-barrier labels and a small meta-label. LightGBM is not installed.

Lopez de Prado's barrier rule is implemented here. The probability model is a
one-feature logistic fit, not LightGBM. State stays partial and shadow.
"""
from __future__ import annotations

import math
from typing import Any

from science.memory import peak_rss_mb


def barrier_label(closes: list[float], start: int, up: float, down: float, horizon: int) -> int:
    """1 if the upper barrier hits first, -1 if the lower hits, 0 on the time barrier."""
    if start < 0 or start >= len(closes) or closes[start] == 0:
        return 0
    entry = closes[start]
    last = min(len(closes) - 1, start + horizon)
    for step in range(start + 1, last + 1):
        move = closes[step] / entry - 1.0
        if move >= up:
            return 1
        if move <= -down:
            return -1
    return 0


def _sigmoid(value: float) -> float:
    if value > 20:
        return 1.0
    if value < -20:
        return 0.0
    return 1.0 / (1.0 + math.exp(-value))


def meta_probability(signal: int, feature: float, weight: float = 1.0) -> float:
    """Chance the signal's barrier is hit. A zero signal cannot act."""
    if signal == 0:
        return 0.0
    return _sigmoid(weight * feature * signal)


def act(signal: int, probability: float, *, min_prob: float = 0.55) -> dict[str, Any]:
    take = signal != 0 and probability >= min_prob
    return {
        "act": take,
        "size": round(probability, 4) if take else 0.0,
        "applied_to_live": False,
    }


def run_shadow() -> dict[str, Any]:
    closes = [100, 101, 102, 103, 110]
    label = barrier_label(closes, 0, 0.05, 0.05, 4)
    probability = meta_probability(1, 0.1)
    decision = act(1, probability)
    return {
        "id": "M9-01",
        "state": "PARTIAL",
        "library": "lightgbm",
        "library_present": False,
        "reason": "LIGHTGBM_ABSENT",
        "label": label,
        "probability": round(probability, 4),
        "decision": decision,
        "metric": "out_of_sample_brier",
        "observed": None,
        "threshold": 0.25,
        "threshold_met_on_fixture": False,
        "promoted": False,
        "peak_mb": peak_rss_mb(),
        "applied_to_live": False,
    }
