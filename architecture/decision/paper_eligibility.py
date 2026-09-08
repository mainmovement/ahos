#!/usr/bin/env python3
"""Lane B paper-candidate eligibility.

Does not edit frozen `paper_trading/**`. Paper engines remain Lane A.
Lane B only answers: may this canonical decision become a paper candidate?
"""
from __future__ import annotations

from architecture.decision.authority import CanonicalDecision, CanonicalOutcome


def paper_candidate_allowed(decision: CanonicalDecision) -> tuple[bool, str]:
    """ENTER/BUY after identity+security+pool gates. Never from score alone."""
    if decision is None:
        return False, "missing_canonical_decision"
    if decision.paper_allowed and decision.outcome == CanonicalOutcome.BUY:
        return True, "eligible"
    return False, decision.primary_reason or decision.outcome.value
