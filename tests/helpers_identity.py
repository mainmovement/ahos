"""Lane B identity fixtures for tests. Not production evidence."""
from __future__ import annotations

from architecture.identity.types import (
    ChainIdentity,
    IdentityResolution,
    IdentityState,
    TokenIdentity,
)

SOL_CANON = "So11111111111111111111111111111111111111112"


def verified_identity_fixture(
    *,
    chain: str = "solana",
    address: str = SOL_CANON,
    token_id: str = "test-fixture-token-id",
    symbol: str = "TOK",
) -> IdentityResolution:
    """Construct a VERIFIED resolution without calling resolve_identity.

    Advisor tests historically used non-canonical addresses such as `Tok111`.
    GATE 0 consumes this fixture so those tests exercise later gates rather
    than Solana address validation.
    """
    return IdentityResolution(
        chain=ChainIdentity(chain, chain, IdentityState.VERIFIED, "test_fixture"),
        token=TokenIdentity(
            chain=chain,
            address_canonical=address,
            address_input=address,
            token_id=token_id,
            symbol_alias=symbol,
            name_alias=f"{symbol} Token",
            state=IdentityState.VERIFIED,
            reason="test_fixture",
        ),
        pool=None,
        dex=None,
        policy_version="identity-resolution-v1",
        computed_ts=0.0,
    )
