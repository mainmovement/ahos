"""Canonical token identity — the SINGLE authoritative identity boundary.

There is exactly one authoritative token-identity algorithm in AHOS:
``discovery.identity.token_id(chain, address)`` (Lane-A, frozen). This module is
only a thin, fail-closed boundary around it so Lane-B / adapters can obtain the
canonical id without re-implementing (or re-normalizing) identity anywhere else.

The Lane-A import is performed lazily inside functions, matching the existing
accepted pattern in ``architecture/learning/score_ledger.py`` (the package
isolation test scans only control_plane/provider_router/council). No second
identity scheme is introduced; TS ``tokenKey`` is NOT an authority identity.

Fail-closed: missing chain, missing address, unknown chain, or empty address
yields ``None`` (never a guessed identity).
"""
from __future__ import annotations

from typing import Optional


def _lane_a_identity():
    # Lazy import: the canonical identity lives in the frozen Lane-A module.
    from discovery import identity  # noqa: WPS433 (intentional local import)
    return identity


def canonical_token_id(chain: Optional[str], address: Optional[str]) -> Optional[str]:
    """Return the canonical token id, or None (fail-closed) if it cannot be formed."""
    if not chain or not address:
        return None
    if not isinstance(chain, str) or not isinstance(address, str):
        return None
    try:
        return _lane_a_identity().token_id(chain, address)
    except (ValueError, TypeError, AttributeError):
        return None


def canonical_chain(chain: Optional[str]) -> Optional[str]:
    """Normalized chain vocabulary (fail-closed) via the canonical registry."""
    if not chain or not isinstance(chain, str):
        return None
    try:
        return _lane_a_identity().normalize_chain(chain)
    except (ValueError, TypeError, AttributeError):
        return None


def canonical_address(chain: Optional[str], address: Optional[str]) -> Optional[str]:
    """Normalized contract address (EVM lowercased, else preserved); fail-closed."""
    c = canonical_chain(chain)
    if c is None or not address or not isinstance(address, str) or not address.strip():
        return None
    try:
        return _lane_a_identity().normalize_address(c, address)
    except (ValueError, TypeError, AttributeError):
        return None
