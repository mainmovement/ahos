"""Private mint helper for tests only. Not a public forge API.

Leading underscore. Not exported in any __all__. Production code must not import this.
"""
from __future__ import annotations

from architecture.identity.resolution import _attach_verified_mint
from architecture.identity.types import IdentityResolution


def _mint_verified_for_tests(resolution: IdentityResolution) -> IdentityResolution:
    """Attach the same resolver mint cookie used by resolve_identity. Tests only."""
    return _attach_verified_mint(resolution)
