"""Fractional differentiation, a small mRMR screen, and a regime-invariance drop."""
from __future__ import annotations

import math
from typing import Any

from science.memory import peak_rss_mb


def frac_diff_weights(d: float, width: int) -> list[float]:
    weights = [1.0]
    for k in range(1, width):
        weights.append(-weights[-1] * (d - k + 1) / k)
    return weights


def apply_frac_diff(series: list[float], d: float = 0.4, width: int = 5) -> list[float | None]:
    weights = frac_diff_weights(d, width)
    out: list[float | None] = []
    for index in range(len(series)):
        if index + 1 < width:
            out.append(None)
            continue
        window = series[index + 1 - width:index + 1]
        out.append(sum(weight * value for weight, value in zip(weights, reversed(window))))
    return out


def _bins(values: list[float], bins: int = 3) -> list[int]:
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0] * len(values)
    return [min(bins - 1, int((value - lo) / (hi - lo) * bins)) for value in values]


def mutual_info(left: list[float], right: list[float]) -> float:
    a = _bins(left)
    b = _bins(right)
    n = len(a)
    if n == 0 or n != len(b):
        return 0.0
    joint: dict[tuple[int, int], int] = {}
    count_a: dict[int, int] = {}
    count_b: dict[int, int] = {}
    for x, y in zip(a, b):
        joint[(x, y)] = joint.get((x, y), 0) + 1
        count_a[x] = count_a.get(x, 0) + 1
        count_b[y] = count_b.get(y, 0) + 1
    info = 0.0
    for (x, y), count in joint.items():
        pxy = count / n
        px = count_a[x] / n
        py = count_b[y] / n
        info += pxy * math.log(pxy / (px * py))
    return round(info, 6)


def drop_if_sign_flips(importance_a: float, importance_b: float) -> bool:
    if importance_a == 0 or importance_b == 0:
        return True
    return (importance_a > 0) != (importance_b > 0)


def run_shadow() -> dict[str, Any]:
    transformed = apply_frac_diff([1, 2, 3, 4, 5, 6], 0.4, 4)
    flipped = drop_if_sign_flips(0.2, -0.1)
    return {
        "id": "M9-08",
        "state": "PARTIAL",
        "library": "own",
        "library_present": True,
        "reason": "MDA_USES_A_TOY_FOLD_NOT_A_BOOK",
        "last": None if transformed[-1] is None else round(transformed[-1], 6),
        "spurious_dropped": flipped,
        "metric": "spurious_features_kept",
        "observed": 0 if flipped else 1,
        "threshold": 0,
        "threshold_met_on_fixture": flipped,
        "promoted": False,
        "peak_mb": peak_rss_mb(),
        "applied_to_live": False,
    }
