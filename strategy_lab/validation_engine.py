"""AHOS Walk-Forward & Purged Cross-Validation Engine (De Prado CPCV Pattern).

Implements:
- Purged K-Fold Cross-Validation with Embargo windowing
- Rolling Walk-Forward Analysis (WFA)
- Out-of-Sample (OOS) vs In-Sample (IS) Efficiency Ratios
- Monte Carlo Trade Sequence Permutation Stress Tests
"""

from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from research.quant_metrics import QuantMetricsEngine


class CrossValidationEngine:
    """Statistical cross-validation and walk-forward verification engine."""

    @staticmethod
    def generate_purged_kfold_splits(
        n_samples: int,
        n_splits: int = 5,
        embargo_pct: float = 0.01,
    ) -> List[Tuple[np.ndarray, np.ndarray]]:
        """Generates Purged and Embargoed K-Fold train/test index splits."""
        if n_samples < n_splits * 2:
            raise ValueError(f"Insufficient samples {n_samples} for {n_splits} splits")

        indices = np.arange(n_samples)
        fold_size = n_samples // n_splits
        embargo_size = int(n_samples * embargo_pct)

        splits = []
        for i in range(n_splits):
            test_start = i * fold_size
            test_end = test_start + fold_size if i < n_splits - 1 else n_samples
            test_indices = indices[test_start:test_end]

            # Embargo training samples immediately after test set
            embargo_end = min(n_samples, test_end + embargo_size)

            train_mask = np.ones(n_samples, dtype=bool)
            train_mask[test_start:embargo_end] = False
            train_indices = indices[train_mask]

            splits.append((train_indices, test_indices))

        return splits

    @staticmethod
    def rolling_walk_forward_splits(
        n_samples: int,
        train_window: int = 100,
        test_window: int = 25,
    ) -> List[Tuple[np.ndarray, np.ndarray]]:
        """Generates rolling out-of-sample walk forward windows."""
        splits = []
        start = 0
        while start + train_window + test_window <= n_samples:
            train_idx = np.arange(start, start + train_window)
            test_idx = np.arange(
                start + train_window, start + train_window + test_window
            )
            splits.append((train_idx, test_idx))
            start += test_window

        return splits

    @staticmethod
    def compute_oos_efficiency(
        is_sharpe: float, oos_sharpe: float
    ) -> float:
        """Computes Out-of-Sample Efficiency Ratio: OOS_Sharpe / IS_Sharpe."""
        if is_sharpe <= 0.0:
            return 0.0
        return float(max(0.0, min(2.0, oos_sharpe / is_sharpe)))

    @staticmethod
    def monte_carlo_permutation_test(
        trade_returns: List[float],
        n_simulations: int = 1000,
        seed: int = 42,
    ) -> Dict[str, Any]:
        """Permutes the sequence of historical trades to test maximum drawdown robustness."""
        tr = np.asarray(trade_returns, dtype=np.float64)
        if len(tr) < 3:
            return {
                "observed_max_dd": 0.0,
                "mc_median_max_dd": 0.0,
                "mc_95th_max_dd": 0.0,
                "p_value_drawdown": 1.0,
            }

        rng = np.random.default_rng(seed)
        obs_eq = np.cumprod(1.0 + tr)
        obs_dd, _ = QuantMetricsEngine.max_drawdown_and_duration(obs_eq)

        mc_drawdowns = []
        for _ in range(n_simulations):
            shuffled = rng.permutation(tr)
            sim_eq = np.cumprod(1.0 + shuffled)
            dd, _ = QuantMetricsEngine.max_drawdown_and_duration(sim_eq)
            mc_drawdowns.append(abs(dd))

        mc_arr = np.array(mc_drawdowns)
        median_dd = float(np.median(mc_arr))
        p95_dd = float(np.percentile(mc_arr, 95))
        p_val = float(np.mean(mc_arr >= abs(obs_dd)))

        return {
            "observed_max_dd_pct": round(abs(obs_dd) * 100.0, 2),
            "mc_median_max_dd_pct": round(median_dd * 100.0, 2),
            "mc_95th_max_dd_pct": round(p95_dd * 100.0, 2),
            "p_value_drawdown": round(p_val, 4),
        }
