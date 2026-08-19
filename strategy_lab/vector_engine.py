"""AHOS Fast Vectorized Strategy Backtester (VectorBT Pattern).

Performs multidimensional tensor parameter exploration and fast vectorized
signal evaluation over historical market datasets using NumPy broadcasting.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from research.quant_metrics import QuantMetricsEngine


class VectorBacktestEngine:
    """High-speed vectorized parameter grid backtester."""

    @staticmethod
    def run_parameter_grid_sweep(
        prices: np.ndarray,
        scores: np.ndarray,
        score_thresholds: List[float],
        stop_loss_pcts: List[float],
        take_profit_pcts: List[float],
        fee_pct: float = 0.003,
    ) -> List[Dict[str, Any]]:
        """Sweeps combinations of (entry_score, stop_loss, take_profit) over price/score arrays."""
        p = np.asarray(prices, dtype=np.float64)
        s = np.asarray(scores, dtype=np.float64)
        n = len(p)
        if n < 5:
            return []

        results = []

        for thresh in score_thresholds:
            for sl in stop_loss_pcts:
                for tp in take_profit_pcts:
                    equity = [1000.0]
                    in_position = False
                    entry_price = 0.0
                    trade_returns = []

                    for t in range(n):
                        price = p[t]
                        score = s[t]

                        if not in_position:
                            if score >= thresh:
                                in_position = True
                                entry_price = price * (1.0 + fee_pct)
                        else:
                            price_change = (price - entry_price) / entry_price
                            # Check exit conditions
                            if price_change <= -sl:
                                # Stop loss hit
                                exit_price = price * (1.0 - fee_pct)
                                trade_return = (
                                    exit_price - entry_price
                                ) / entry_price
                                trade_returns.append(trade_return)
                                equity.append(equity[-1] * (1.0 + trade_return))
                                in_position = False
                            elif price_change >= tp:
                                # Take profit hit
                                exit_price = price * (1.0 - fee_pct)
                                trade_return = (
                                    exit_price - entry_price
                                ) / entry_price
                                trade_returns.append(trade_return)
                                equity.append(equity[-1] * (1.0 + trade_return))
                                in_position = False
                            elif score < (thresh * 0.5):
                                # Signal decay exit
                                exit_price = price * (1.0 - fee_pct)
                                trade_return = (
                                    exit_price - entry_price
                                ) / entry_price
                                trade_returns.append(trade_return)
                                equity.append(equity[-1] * (1.0 + trade_return))
                                in_position = False

                    # Final tear-sheet for this parameter combo
                    tearsheet = QuantMetricsEngine.generate_tearsheet(
                        equity, trade_returns
                    )
                    tearsheet["param_entry_thresh"] = thresh
                    tearsheet["param_stop_loss"] = sl
                    tearsheet["param_take_profit"] = tp
                    results.append(tearsheet)

        # Sort by annualized Sharpe ratio descending
        results.sort(key=lambda x: x["annualized_sharpe"], reverse=True)
        return results
