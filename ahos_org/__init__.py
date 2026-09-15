"""AHOS Agent Organization — Slice 1 governance core.

This package is an independent organizational control plane.
It is not an AHOS runtime, not a trading system, and not an AGI.
"""

from ahos_org.organization import AgentOrganization

__all__ = ["AgentOrganization"]
__slice__ = 1
__maturity_claim__ = "IMPLEMENTED"  # evidence: code exists; tests decide TESTED
