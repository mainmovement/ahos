"""AHOS Decision Advisory layer.

Fuses every evidence stream into ONE recommendation with its reasoning:

    deterministic score  (architecture/scoring)
  + exit feasibility     (architecture/intel/exitability)
  + attention/virality   (architecture/intel/viral)
  + holder concentration (architecture/intel/whales)
  + news narrative       (architecture/intel/news)
  + AI council opinion   (architecture/ai/council_live)   [advisory only]
  ------------------------------------------------------------------
  = Advice(action, size, entry, targets, invalidation, WHY)

LAW: this layer ADVISES. It never places an order — none exists to place.
Every output ends with «تصمیم نهایی با کاربر است.»
"""

from .advisor import DecisionAdvisor, Advice, PositionAdvice    # noqa: F401

__all__ = ["DecisionAdvisor", "Advice", "PositionAdvice"]
