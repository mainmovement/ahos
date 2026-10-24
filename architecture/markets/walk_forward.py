"""Spec path for the Stage-7 price-safe return transform.

The transform is implemented in ``architecture.learning.walk_forward`` — the one walk-forward engine —
and re-exported here. This module does not simulate, score, or store a second set of trials.
"""
from architecture.learning.walk_forward import atr_normalized_return, safe_simple_return, wilder_atr

__all__ = ["atr_normalized_return", "safe_simple_return", "wilder_atr"]
