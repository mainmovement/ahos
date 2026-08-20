"""DEPRECATED PARALLEL SUBSYSTEM (PR #14). Not imported by canonical AHOS.

This Pydantic Token/TokenScore model duplicated (and contradicted) the
canonical `NormalizedTokenCandidate` + `OpportunityScoreReport` contracts.
It also treated stocks/forex/commodities as first-class — outside AHOS
mission (crypto opportunity intelligence). Kept as a stub so the path
remains explainable; do not import.
"""
from __future__ import annotations


class Token:
    """Removed. Use architecture.providers.contracts.NormalizedTokenCandidate."""

    def __init__(self, *args, **kwargs):
        raise RuntimeError(
            "core.models.token.Token is deprecated (PR #14 parallel subsystem). "
            "Use architecture.providers.contracts.NormalizedTokenCandidate."
        )


class TokenScore:
    def __init__(self, *args, **kwargs):
        raise RuntimeError(
            "core.models.token.TokenScore is deprecated. "
            "Use architecture.scoring.engine.OpportunityScoreReport."
        )
