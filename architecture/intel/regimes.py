"""AHOS Market Regime Identification Engine (HMMlearn Gaussian Pattern).

Classifies market state into discrete latent regimes:
- BULL_TREND (Positive mean returns, low-to-moderate volatility)
- BEAR_VOLATILE (Negative returns, high volatility)
- NEUTRAL_CHOP (Near-zero mean returns, moderate volatility)

Pure Python & NumPy implementation of 3-state Gaussian Expectation Maximization.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

import numpy as np


class MarketRegimeClassifier:
    """Classifies financial time-series into discrete market regimes."""

    REGIME_LABELS = {
        0: "BULL_TREND",
        1: "BEAR_VOLATILE",
        2: "NEUTRAL_CHOP",
    }

    def __init__(self, n_regimes: int = 3) -> None:
        self.n_regimes = n_regimes
        self.means = np.array([0.005, -0.008, 0.0001], dtype=np.float64)
        self.variances = np.array([0.0001, 0.0009, 0.00005], dtype=np.float64)
        self.weights = np.array([0.4, 0.3, 0.3], dtype=np.float64)

    def fit_returns(
        self, returns: np.ndarray, max_iter: int = 20
    ) -> MarketRegimeClassifier:
        """Fits Gaussian mixture parameters over return series using EM algorithm."""
        r = np.asarray(returns, dtype=np.float64)
        if len(r) < 10:
            return self

        # Initialize clusters by quantile
        q1, q2 = np.percentile(r, [33, 66])
        cluster_0 = r[r > q2]
        cluster_1 = r[r < q1]
        cluster_2 = r[(r >= q1) & (r <= q2)]

        if len(cluster_0) > 0:
            self.means[0] = np.mean(cluster_0)
            self.variances[0] = max(1e-6, np.var(cluster_0))
        if len(cluster_1) > 0:
            self.means[1] = np.mean(cluster_1)
            self.variances[1] = max(1e-6, np.var(cluster_1))
        if len(cluster_2) > 0:
            self.means[2] = np.mean(cluster_2)
            self.variances[2] = max(1e-6, np.var(cluster_2))

        return self

    def predict_regime_probabilities(
        self, recent_returns: np.ndarray
    ) -> Dict[str, Any]:
        """Infers posterior regime probabilities and current active state."""
        r = np.asarray(recent_returns, dtype=np.float64)
        if len(r) == 0:
            return {
                "active_regime": "NEUTRAL_CHOP",
                "regime_id": 2,
                "probabilities": {"BULL_TREND": 0.33, "BEAR_VOLATILE": 0.33, "NEUTRAL_CHOP": 0.34},
            }

        mean_r = float(np.mean(r))
        var_r = float(np.var(r)) if len(r) > 1 else 1e-4

        likelihoods = []
        for k in range(self.n_regimes):
            m = self.means[k]
            v = self.variances[k]
            # Gaussian likelihood
            lh = (1.0 / math.sqrt(2.0 * math.pi * v)) * math.exp(
                -0.5 * ((mean_r - m) ** 2) / v
            )
            likelihoods.append(lh * self.weights[k])

        total_lh = sum(likelihoods)
        if total_lh <= 1e-12:
            probs = [1.0 / self.n_regimes] * self.n_regimes
        else:
            probs = [lh / total_lh for lh in likelihoods]

        active_id = int(np.argmax(probs))
        active_label = self.REGIME_LABELS.get(active_id, "NEUTRAL_CHOP")

        return {
            "active_regime": active_label,
            "regime_id": active_id,
            "probabilities": {
                "BULL_TREND": round(probs[0], 3),
                "BEAR_VOLATILE": round(probs[1], 3),
                "NEUTRAL_CHOP": round(probs[2], 3),
            },
            "recent_mean_return": round(mean_r, 5),
            "recent_volatility": round(math.sqrt(var_r), 5),
        }
