"""
AHOS v2 Intelligence Engine — Evidence-Driven Analysis Layer
=============================================================
Pure intelligence on top of the Evidence Architecture.
All functions are deterministic, evidence-only, and produce advisory
output (never execution). Built on core evidence, never on raw values.

Structure:
  intelligence.features  — Feature Registry (versioned, evidence-anchored)
  intelligence.scoring   — Opportunity Scoring Engine v2 (evidence → sub-scores)
  intelligence.risk      — Risk Engine (contract, liquidity, concentration, manipulation)
  intelligence.explanations — Human-readable explanation generator

Paper-only law: no trading primitives, no wallet signing, no secrets.
"""

from importlib import metadata as _m  # noqa: F401

__version__ = "2.0.0-intelligence"
__all__ = []
