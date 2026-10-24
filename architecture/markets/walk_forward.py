"""Spec path for the Stage-7 price-safe return transform.

The transform is implemented in ``architecture.learning.walk_forward`` — the one walk-forward engine —
and re-exported here. This module does not simulate, score, or store a second set of trials.
"""
from architecture.learning.walk_forward import (
    apply_weight_hysteresis, atr_normalized_return, clears_cost_hurdle, safe_simple_return, wilder_atr,
)

__all__ = [
    "apply_weight_hysteresis", "atr_normalized_return", "clears_cost_hurdle", "safe_simple_return", "wilder_atr",
]
