"""Stationary block bootstrap. The arch package is not installed.

Politis and Romano, 1994. A path fails when its fifth percentile is not above zero.
"""
from __future__ import annotations

import random
from typing import Any

from science.memory import peak_rss_mb


def stationary_paths(series: list[float], *, draws: int, mean_block: int, seed: int) -> list[float]:
    if not series or draws < 1 or mean_block < 1:
        return []
    rng = random.Random(seed)
    n = len(series)
    means = []
    p_restart = 1.0 / mean_block
    for _ in range(draws):
        path = []
        index = rng.randrange(n)
        while len(path) < n:
            path.append(series[index])
            if rng.random() < p_restart:
                index = rng.randrange(n)
            else:
                index = (index + 1) % n
        means.append(sum(path) / n)
    return means


def fifth_percentile(means: list[float]) -> float | None:
    if not means:
        return None
    ordered = sorted(means)
    rank = max(0, int(0.05 * (len(ordered) - 1)))
    return ordered[rank]


def survives(series: list[float], *, draws: int = 40, mean_block: int = 3, seed: int = 7) -> bool:
    percentile = fifth_percentile(stationary_paths(series, draws=draws, mean_block=mean_block, seed=seed))
    return percentile is not None and percentile > 0


def run_shadow() -> dict[str, Any]:
    bad = survives([-0.02] * 12)
    return {
        "id": "M9-10",
        "state": "PARTIAL",
        "library": "arch",
        "library_present": False,
        "reason": "ARCH_ABSENT",
        "negative_path_survives": bad,
        "metric": "fifth_percentile_after_costs",
        "observed": 0.0 if not bad else 1.0,
        "threshold": 0,
        "threshold_met_on_fixture": bad is False,
        "promoted": False,
        "peak_mb": peak_rss_mb(),
        "applied_to_live": False,
    }
