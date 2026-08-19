"""Tests for AHOS Concept Drift & Market Regime Classifier (OSS-009)."""

from __future__ import annotations

import numpy as np
import pytest

from architecture.intel.regimes import MarketRegimeClassifier
from architecture.learning.drift import StreamingDriftDetector


def test_streaming_drift_detector_detects_step_change():
    detector = StreamingDriftDetector(delta=0.005, min_window=10)

    # Feed stationary series around 0.5
    for _ in range(50):
        detector.update(0.50 + np.random.normal(0, 0.01))

    # Suddenly shift mean to 0.90
    drift_seen = False
    for _ in range(25):
        if detector.update(0.90 + np.random.normal(0, 0.01)):
            drift_seen = True
            break

    assert drift_seen is True


def test_market_regime_classifier_fit_and_predict():
    np.random.seed(42)
    classifier = MarketRegimeClassifier()

    # Generate synthetic returns
    bull_returns = np.random.normal(0.01, 0.005, 50)
    bear_returns = np.random.normal(-0.015, 0.02, 50)
    chop_returns = np.random.normal(0.0001, 0.002, 50)
    all_returns = np.concatenate([bull_returns, bear_returns, chop_returns])

    classifier.fit_returns(all_returns)

    # Test prediction on fresh bull returns
    pred_bull = classifier.predict_regime_probabilities(
        np.random.normal(0.012, 0.004, 15)
    )
    assert pred_bull["active_regime"] == "BULL_TREND"

    # Test prediction on fresh bear returns
    pred_bear = classifier.predict_regime_probabilities(
        np.random.normal(-0.018, 0.02, 15)
    )
    assert pred_bear["active_regime"] == "BEAR_VOLATILE"
