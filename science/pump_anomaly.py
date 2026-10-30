"""A small isolation score plus lock rules. sklearn is not installed."""
from __future__ import annotations

import random
from typing import Any

from science.memory import peak_rss_mb


def mean_depth(rows: list[list[float]], target: list[float], *, trees: int = 6, seed: int = 1) -> float | None:
    if len(rows) < 2 or not target:
        return None
    rng = random.Random(seed)
    dims = len(target)
    depths = []
    for _ in range(trees):
        subset = rows
        depth = 0
        while depth < 4 and len(subset) > 1:
            dim = rng.randrange(dims)
            values = [row[dim] for row in subset if len(row) > dim]
            if not values:
                break
            lo, hi = min(values), max(values)
            if hi == lo:
                break
            cut = lo + (hi - lo) * rng.random()
            go_low = target[dim] < cut
            nxt = [row for row in subset if len(row) > dim and ((row[dim] < cut) == go_low)]
            if not nxt or len(nxt) == len(subset):
                break
            subset = nxt
            depth += 1
        depths.append(depth)
    return sum(depths) / len(depths)


def pump_veto(
    *,
    liquidity_locked: bool,
    holder_growth: bool,
    change: float,
    rows: list[list[float]] | None = None,
    target: list[float] | None = None,
) -> dict[str, Any]:
    """A token that fails the lock or isolates too fast is vetoed. It still cannot open alone."""
    rule = (not liquidity_locked and holder_growth) or abs(change) >= 50
    depth = None if rows is None or target is None else mean_depth(rows, target)
    anomaly = depth is not None and depth <= 1
    return {
        "veto": bool(rule or anomaly),
        "depth": depth,
        "live_open": False,
        "applied_to_live": False,
    }


def run_shadow() -> dict[str, Any]:
    decision = pump_veto(liquidity_locked=False, holder_growth=True, change=5.0)
    return {
        "id": "M9-11",
        "state": "PARTIAL",
        "library": "sklearn.IsolationForest",
        "library_present": False,
        "reason": "SKLEARN_ABSENT",
        "veto": decision["veto"],
        "metric": "lone_token_opens",
        "observed": 0,
        "threshold": 0,
        "threshold_met_on_fixture": decision["veto"] and decision["live_open"] is False,
        "promoted": False,
        "peak_mb": peak_rss_mb(),
        "applied_to_live": False,
    }
