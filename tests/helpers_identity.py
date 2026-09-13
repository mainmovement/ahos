"""Lane B identity fixtures for tests. Not production evidence."""
from __future__ import annotations

from architecture.identity.types import (
    ChainIdentity,
    DexDeployment,
    IdentityResolution,
    IdentityState,
    PoolIdentity,
    TokenIdentity,
)

SOL_CANON = "So11111111111111111111111111111111111111112"


def calibration_identity_maps(
    token_ids: list[str],
    *,
    chain: str = "solana",
    address: str = SOL_CANON,
    symbol: str = "TOK",
) -> tuple[dict, dict]:
    """Matching VERIFIED maps for calibration math fixtures. Not production evidence."""
    pred: dict = {}
    out: dict = {}
    for tid in token_ids:
        ident = verified_identity_fixture(
            chain=chain, address=address, token_id=tid, symbol=symbol,
        )
        pred[tid] = ident
        out[tid] = ident
    return pred, out


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


def verified_pool_identity_fixture(
    *,
    chain: str = "solana",
    address: str = SOL_CANON,
    token_id: str = "test-fixture-token-id",
    symbol: str = "TOK",
    pair_address: str = "Pool111111111111111111111111111111111111111",
    dex_id: str = "raydium",
) -> IdentityResolution:
    """Token VERIFIED and pool VERIFIED bound to the token.

    Required for a positive canonical BUY / paper / opportunity alert.
    Token-only verification is MONITOR_ONLY (no pool liquidity claims).
    """
    token_res = verified_identity_fixture(
        chain=chain, address=address, token_id=token_id, symbol=symbol,
    )
    pool = PoolIdentity(
        chain=chain,
        dex_id=dex_id,
        pair_address=pair_address,
        pair_id="test-fixture-pair-id",
        token_id=token_id,
        base_token_address=address,
        state=IdentityState.VERIFIED,
        reason="test_fixture",
        belongs_to_token=True,
    )
    dex = DexDeployment(dex_id=dex_id, chain=chain, version="v4")
    return IdentityResolution(
        chain=token_res.chain,
        token=token_res.token,
        pool=pool,
        dex=dex,
        sources=token_res.sources,
        conflicts=token_res.conflicts,
        provenance=token_res.provenance,
        choices=token_res.choices,
        pools=(pool,),
        policy_version=token_res.policy_version,
        computed_ts=token_res.computed_ts,
    )
