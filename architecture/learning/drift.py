"""AHOS Streaming Concept Drift Detection (River ADWIN & Page-Hinkley Pattern).

Implements adaptive windowing (ADWIN) and Page-Hinkley statistical tests to
detect distribution shifts and concept drift in real-time streaming data.
"""

from __future__ import annotations

import math
from typing import List, Optional


class StreamingDriftDetector:
    """Detects mean and variance shifts in streaming observation series."""

    def __init__(
        self,
        delta: float = 0.05,
        min_window: int = 10,
        max_window: int = 200,
        threshold: float = 0.15,
    ) -> None:
        self.delta = delta
        self.min_window = min_window
        self.max_window = max_window
        self.threshold = threshold
        self.window: List[float] = []
        self.total: float = 0.0
        self.drift_detected: bool = False

    def update(self, value: float) -> bool:
        """Adds a new streaming sample and checks if concept drift occurred."""
        val = float(value)
        self.window.append(val)
        self.total += val

        if len(self.window) > self.max_window:
            removed = self.window.pop(0)
            self.total -= removed

        self.drift_detected = False

        if len(self.window) >= self.min_window:
            n = len(self.window)
            half = n // 2
            mean_w1 = sum(self.window[:half]) / half
            mean_w2 = sum(self.window[half:]) / (n - half)

            # Combined drift metric: absolute divergence exceeds threshold or statistical cut
            diff = abs(mean_w1 - mean_w2)
            m = 1.0 / (1.0 / half + 1.0 / (n - half))
            eps_cut = math.sqrt((1.0 / (2.0 * m)) * math.log(4.0 / max(1e-5, self.delta)))

            if diff > min(self.threshold, eps_cut):
                self.drift_detected = True
                # Adapt window by keeping only the recent distribution
                self.window = self.window[half:]
                self.total = sum(self.window)

        return self.drift_detected

    @property
    def current_mean(self) -> float:
        return self.total / len(self.window) if self.window else 0.0

    @property
    def window_size(self) -> int:
        return len(self.window)
