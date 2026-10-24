"""Walk-forward logistic calibration.

The fit uses only rows whose timestamp is strictly before every test row.
A violated order sets leaked=True and returns no probabilities.
"""
from __future__ import annotations

import math
from typing import Any


def _sigmoid(x: float) -> float:
    x = max(-20.0, min(20.0, x))
    return 1.0 / (1.0 + math.exp(-x))


def brier_score(probs: list[float], outcomes: list[float]) -> float | None:
    if not probs or len(probs) != len(outcomes):
        return None
    return sum((p - y) ** 2 for p, y in zip(probs, outcomes)) / len(probs)


def brier_skill_score(brier: float | None, climatology: float = 0.25) -> float | None:
    if brier is None or climatology <= 0:
        return None
    return 1.0 - brier / climatology


def fit_and_apply(train: list[dict[str, Any]], test: list[dict[str, Any]], features: tuple[str, ...],
                  *, l2: float = 0.05) -> dict[str, Any]:
    """Ridge logistic regression. Features are standardized on the training rows only."""
    if not train or not test:
        return {"leaked": False, "status": "INSUFFICIENT_ROWS", "probs": []}
    if max(r["ts"] for r in train) >= min(r["ts"] for r in test):
        return {"leaked": True, "status": "LEAK_DETECTED", "probs": []}
    means, scales = [], []
    for name in features:
        col = [float(r["features"][name]) for r in train]
        mu = sum(col) / len(col)
        var = sum((x - mu) ** 2 for x in col) / len(col)
        means.append(mu)
        scales.append(math.sqrt(var) or 1.0)

    def row(rec: dict[str, Any]) -> list[float]:
        return [1.0] + [(float(rec["features"][n]) - mu) / sd for n, mu, sd in zip(features, means, scales)]

    x_train = [row(r) for r in train]
    y = [1.0 if r["y"] else 0.0 for r in train]
    k = len(features) + 1
    beta = [0.0] * k
    for _ in range(30):
        grad = [0.0] * k
        hess = [[0.0] * k for _i in range(k)]
        for xi, yi in zip(x_train, y):
            eta = sum(b * x for b, x in zip(beta, xi))
            p = _sigmoid(eta)
            w = max(1e-6, p * (1.0 - p))
            for a in range(k):
                grad[a] += xi[a] * (yi - p)
                for b in range(k):
                    hess[a][b] += w * xi[a] * xi[b]
        for a in range(1, k):
            grad[a] -= l2 * beta[a]
            hess[a][a] += l2
        step = _solve(hess, grad)
        if step is None:
            break
        beta = [b + s for b, s in zip(beta, step)]
        if max(abs(s) for s in step) < 1e-8:
            break
    probs = []
    for rec in test:
        eta = sum(b * x for b, x in zip(beta, row(rec)))
        probs.append(_sigmoid(eta))
    return {"leaked": False, "status": "FIT", "probs": probs, "n_train": len(train), "n_test": len(test),
            "features": list(features), "intercept_unpenalized": True}


def _solve(hess: list[list[float]], grad: list[float]) -> list[float] | None:
    n = len(grad)
    a = [row[:] + [grad[i]] for i, row in enumerate(hess)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(a[r][col]))
        if abs(a[pivot][col]) < 1e-12:
            return None
        a[col], a[pivot] = a[pivot], a[col]
        div = a[col][col]
        for j in range(col, n + 1):
            a[col][j] /= div
        for r in range(n):
            if r == col:
                continue
            factor = a[r][col]
            for j in range(col, n + 1):
                a[r][j] -= factor * a[col][j]
    return [a[i][n] for i in range(n)]
