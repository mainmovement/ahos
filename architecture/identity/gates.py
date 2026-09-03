#!/usr/bin/env python3
"""Identity eligibility gates — no second brain, identity first."""
from __future__ import annotations

from architecture.identity.types import IdentityResolution, IdentityState

BLOCKING_TOKEN_STATES = {
    IdentityState.INVALID,
    IdentityState.CONFLICT,
    IdentityState.UNRESOLVED,
    IdentityState.UNSUPPORTED,
    IdentityState.STALE,
}


def identity_allows_positive_decision(resolution: IdentityResolution | None) -> bool:
    """INVALID/CONFLICT/UNRESOLVED/STALE/UNSUPPORTED/MISSING ⇒ no positive rec."""
    if resolution is None:
        return False
    return resolution.token.state == IdentityState.VERIFIED


def identity_allows_alert(resolution: IdentityResolution | None) -> bool:
    return identity_allows_positive_decision(resolution)


def identity_allows_paper_candidate(resolution: IdentityResolution | None) -> bool:
    return identity_allows_positive_decision(resolution)


def identity_allows_identity_mutation(resolution: IdentityResolution | None) -> bool:
    return identity_allows_positive_decision(resolution)


def pool_liquidity_claims_allowed(resolution: IdentityResolution | None) -> bool:
    """Verified token + unresolved pool ⇒ monitoring only, no pool liquidity claims."""
    if not identity_allows_positive_decision(resolution) or resolution is None:
        return False
    if resolution.pool is None:
        return False
    return (
        resolution.pool.state == IdentityState.VERIFIED
        and resolution.pool.belongs_to_token is True
    )


def token_monitoring_allowed(resolution: IdentityResolution | None) -> bool:
    if resolution is None:
        return False
    return resolution.token.state == IdentityState.VERIFIED
