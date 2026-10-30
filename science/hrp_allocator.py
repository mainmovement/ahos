"""Hierarchical risk parity in numpy. Riskfolio-Lib is not installed."""
from __future__ import annotations

from typing import Any

import numpy as np

from science.memory import peak_rss_mb


def _distance(corr: np.ndarray) -> np.ndarray:
    clipped = np.clip(corr, -1.0, 1.0)
    return np.sqrt(np.maximum(0.0, (1.0 - clipped) / 2.0))


def _order(dist: np.ndarray) -> list[int]:
    """Single-linkage order. n is tiny; this is not a general clustering library."""
    n = dist.shape[0]
    remaining = set(range(n))
    current = 0
    remaining.remove(current)
    ordered = [current]
    while remaining:
        nxt = min(remaining, key=lambda index: dist[current, index])
        remaining.remove(nxt)
        ordered.append(nxt)
        current = nxt
    return ordered


def hrp_weights(cov: list[list[float]]) -> list[float]:
    matrix = np.asarray(cov, dtype=float)
    n = matrix.shape[0]
    if n == 0 or matrix.shape != (n, n):
        return []
    variance = np.clip(np.diag(matrix), 1e-12, None)
    std = np.sqrt(variance)
    corr = matrix / np.outer(std, std)
    ordered = _order(_distance(corr))
    weights = np.ones(n)

    def _split(group: list[int]) -> None:
        if len(group) <= 1:
            return
        mid = len(group) // 2
        left, right = group[:mid], group[mid:]
        left_var = float(sum(matrix[i, i] for i in left))
        right_var = float(sum(matrix[i, i] for i in right))
        alpha = 1.0 - left_var / (left_var + right_var)
        for index in left:
            weights[index] *= alpha
        for index in right:
            weights[index] *= 1.0 - alpha
        _split(left)
        _split(right)

    _split(ordered)
    total = float(weights.sum()) or 1.0
    return [round(float(value / total), 6) for value in weights]


def run_shadow() -> dict[str, Any]:
    weights = hrp_weights([[0.04, 0.01], [0.01, 0.09]])
    error = abs(sum(weights) - 1.0)
    return {
        "id": "M9-06",
        "state": "PARTIAL",
        "library": "riskfolio",
        "library_present": False,
        "reason": "RISKFOLIO_ABSENT",
        "weights": weights,
        "metric": "weight_sum_error",
        "observed": round(error, 6),
        "threshold": 0.001,
        "threshold_met_on_fixture": error <= 0.001 and all(value >= 0 for value in weights),
        "promoted": False,
        "peak_mb": peak_rss_mb(),
        "applied_to_live": False,
    }
