"""AHOS canonical decision layer (One-Brain, Option B).

This package is the single cross-runtime authority boundary: the Python brain
produces `CanonicalDecision` records (contract.py) keyed by the canonical token
identity (identity.py) and persists them to the canonical decision store
(decision_store.py). Every downstream adapter (web, Telegram, n8n) READS these
records; none may recompute security disposition, opportunity eligibility,
recommendation, score, ranking, or identity.

Fail-closed is the law: a missing, malformed, or stale record is never a
positive opportunity.
"""
from .contract import (  # noqa: F401
    CanonicalDecision,
    DECISION_VERSION,
    CANONICAL_SOURCE,
    BRAIN_VERSION,
)
from .identity import canonical_token_id  # noqa: F401

__all__ = [
    "CanonicalDecision",
    "DECISION_VERSION",
    "CANONICAL_SOURCE",
    "BRAIN_VERSION",
    "canonical_token_id",
]
