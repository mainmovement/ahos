"""Tests for AHOS Walk-Forward & Purged Cross-Validation Engine (OSS-005)."""

from __future__ import annotations

import numpy as np
import pytest

from strategy_lab.validation_engine import CrossValidationEngine


def test_purged_kfold_splits_integrity():
    n_samples = 1000
    n_splits = 5
    splits = CrossValidationEngine.generate_purged_kfold_splits(
        n_samples=n_samples, n_splits=n_splits, embargo_pct=0.02
    )

    assert len(splits) == 5
    for train_idx, test_idx in splits:
        assert len(test_idx) == 200
        # Check no overlap between train and test
        overlap = set(train_idx).intersection(set(test_idx))
        assert len(overlap) == 0
        # Check embargo gap
        test_max = np.max(test_idx)
        if test_max < n_samples - 1:
            embargo_point = test_max + 1
            assert embargo_point not in train_idx


def test_rolling_walk_forward_splits():
    n_samples = 500
    train_w = 100
    test_w = 50
    splits = CrossValidationEngine.rolling_walk_forward_splits(
        n_samples, train_window=train_w, test_window=test_w
    )

    assert len(splits) == 8
    for train_idx, test_idx in splits:
        assert len(train_idx) == 100
        assert len(test_idx) == 50
        assert np.max(train_idx) < np.min(test_idx)


def test_monte_carlo_permutation():
    trades = [0.08, -0.04, 0.05, -0.02, 0.10, -0.06, 0.04, -0.03, 0.07, -0.05]
    mc_results = CrossValidationEngine.monte_carlo_permutation_test(
        trades, n_simulations=500, seed=42
    )

    assert "observed_max_dd_pct" in mc_results
    assert "mc_median_max_dd_pct" in mc_results
    assert "p_value_drawdown" in mc_results
    assert 0.0 <= mc_results["p_value_drawdown"] <= 1.0
