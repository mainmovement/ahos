"""Purged and embargoed folds. Science scores go through these folds.

The older walk-forward helper is not rewritten. Rescoring old receipts would
be a new trial, and this registration has not authorized that.
"""
from __future__ import annotations

from typing import Any

from science.memory import peak_rss_mb


def purged_folds(n: int, *, horizon: int, n_splits: int = 5, embargo: int = 1) -> list[tuple[list[int], list[int]]]:
    if n_splits < 2 or n < n_splits:
        return []
    width = n // n_splits
    folds = []
    for fold in range(n_splits):
        start = fold * width
        stop = n if fold == n_splits - 1 else (fold + 1) * width
        test = list(range(start, stop))
        left = max(0, start - horizon - embargo)
        right = min(n, stop + embargo)
        train = [index for index in range(n) if index < left or index >= right]
        folds.append((train, test))
    return folds


def leaks(train: list[int], test: list[int], horizon: int, embargo: int) -> bool:
    if not test:
        return False
    start, stop = test[0], test[-1] + 1
    blocked_lo = start - horizon - embargo
    blocked_hi = stop + embargo
    return any(blocked_lo <= index < blocked_hi for index in train)


def run_shadow() -> dict[str, Any]:
    folds = purged_folds(20, horizon=2, n_splits=4, embargo=1)
    leaked = sum(1 for train, test in folds if leaks(train, test, 2, 1))
    return {
        "id": "M9-02",
        "state": "PARTIAL",
        "library": "own",
        "library_present": False,
        "reason": "LEGACY_WALK_FORWARD_NOT_REROUTED",
        "leaked_folds": leaked,
        "folds": len(folds),
        "metric": "leaked_folds",
        "observed": leaked,
        "threshold": 0,
        "threshold_met_on_fixture": leaked == 0,
        "promoted": False,
        "peak_mb": peak_rss_mb(),
        "applied_to_live": False,
    }
