#!/usr/bin/env python3
"""Phase 1 — Lane B canonical identity overlay.

Does not edit frozen discovery/identity.py. Covers the master identity gates:
valid identity, invalid address, wrong chain, symbol collision, pool mismatch,
provider conflict, stale identity, duplicate identity, unsupported chain,
EIP-55, Solana case preservation, and no-positive-decision / no-pool-claim.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.decision.advisor import DecisionAdvisor  # noqa: E402
from architecture.identity.dex_registry import (  # noqa: E402
    load_dex_registry,
    lookup_dex,
    registry_version,
)
from architecture.identity.gates import (  # noqa: E402
    identity_allows_alert,
    identity_allows_identity_mutation,
    identity_allows_paper_candidate,
    identity_allows_positive_decision,
    pool_liquidity_claims_allowed,
    token_monitoring_allowed,
)
from architecture.identity.keccak256 import keccak256  # noqa: E402
from architecture.identity.resolution import resolve_identity  # noqa: E402
from architecture.identity.types import (  # noqa: E402
    IdentityResolution,
    IdentitySource,
    IdentityState,
    TokenIdentity,
)
from architecture.identity.validate import (  # noqa: E402
    eip55_checksum,
    validate_evm_address,
    validate_solana_address,
)
from architecture.intel.exitability import ExitabilityAnalyzer  # noqa: E402
from architecture.providers.contracts import (  # noqa: E402
    MarketMetrics,
    NormalizedTokenCandidate,
    SecuritySignals,
)
from architecture.scoring.engine import OpportunityScorer  # noqa: E402
from discovery.identity import pair_id, token_id  # noqa: E402
from tests.helpers_identity import verified_identity_fixture  # noqa: E402

NOW = 1_800_000_000.0
USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
USDC_LOWER = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
USDC_BAD = "0xA0B86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
SOL = "So11111111111111111111111111111111111111112"
SOL_USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
EIP55_VITALIK = "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"


def _src(provider: str, chain: str, address: str, kind: str, age: float = 0.0) -> IdentitySource:
    return IdentitySource(
        provider=provider,
        chain=chain,
        address=address,
        kind=kind,
        retrieved_ts=NOW,
        source_ts=NOW - age,
    )


def _min_sources(chain: str, address: str) -> tuple[IdentitySource, IdentitySource]:
    return (
        _src("rpc", chain, address, "onchain"),
        _src("dexscreener", chain, address, "market"),
    )


def test_keccak256_empty_digest():
    assert keccak256(b"").hex() == (
        "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
    )


def test_eip55_known_vectors():
    assert eip55_checksum(USDC_LOWER) == USDC
    assert eip55_checksum(EIP55_VITALIK.lower()) == EIP55_VITALIK
    st, reason, canonical, ok = validate_evm_address(USDC)
    assert st == IdentityState.UNRESOLVED
    assert canonical == USDC_LOWER
    assert ok is True
    st, reason, canonical, ok = validate_evm_address(USDC_BAD)
    assert st == IdentityState.INVALID
    assert reason == "evm_checksum_mismatch"
    assert ok is False
    st, _reason, canonical, ok = validate_evm_address(USDC_LOWER)
    assert st == IdentityState.UNRESOLVED
    assert canonical == USDC_LOWER
    assert ok is None


def test_invalid_evm_address_length():
    st, reason, canonical, _ok = validate_evm_address("0x1234")
    assert st == IdentityState.INVALID
    assert "20_bytes" in reason
    assert canonical is None


def test_solana_preserves_canonical_representation():
    st, reason, canonical = validate_solana_address(SOL)
    assert st == IdentityState.UNRESOLVED
    assert canonical == SOL
    other = validate_solana_address(SOL.lower())
    assert other[2] == SOL.lower()
    assert other[2] != SOL


def test_solana_invalid_not_32_byte_pubkey():
    st, reason, canonical = validate_solana_address("not-base58!!!")
    assert st == IdentityState.INVALID
    assert canonical is None
    st, reason, canonical = validate_solana_address("ABCd")
    assert st == IdentityState.INVALID
    assert reason == "solana_not_32_byte_pubkey"


def test_valid_identity_evm_verified():
    res = resolve_identity(
        chain="eth",
        address=USDC,
        symbol="USDC",
        name="USD Coin",
        sources=_min_sources("ethereum", USDC),
        now=NOW,
    )
    assert res.chain.state == IdentityState.VERIFIED
    assert res.chain.canonical_chain == "ethereum"
    assert res.token.state == IdentityState.VERIFIED
    assert res.token.address_canonical == USDC_LOWER
    assert res.token.token_id == token_id("ethereum", USDC)
    assert res.token.token_id == token_id("eth", USDC_LOWER)
    assert res.token.symbol_alias == "USDC"
    assert identity_allows_positive_decision(res)
    assert identity_allows_alert(res)
    assert identity_allows_paper_candidate(res)
    assert token_monitoring_allowed(res)
    assert not pool_liquidity_claims_allowed(res)


def test_valid_identity_solana_verified():
    res = resolve_identity(
        chain="solana",
        address=SOL,
        sources=_min_sources("solana", SOL),
        now=NOW,
    )
    assert res.token.state == IdentityState.VERIFIED
    assert res.token.address_canonical == SOL
    assert res.token.token_id == token_id("solana", SOL)
    assert identity_allows_positive_decision(res)


def test_invalid_address_cannot_produce_positive_decision():
    res = resolve_identity(
        chain="ethereum",
        address="0x1234",
        sources=_min_sources("ethereum", "0x1234"),
        now=NOW,
    )
    assert res.token.state == IdentityState.INVALID
    assert res.token.token_id is None
    assert not identity_allows_positive_decision(res)
    assert not identity_allows_alert(res)
    assert not identity_allows_paper_candidate(res)
    assert not identity_allows_identity_mutation(res)


def test_wrong_chain_provider_conflict():
    res = resolve_identity(
        chain="ethereum",
        address=USDC,
        sources=(
            _src("rpc", "ethereum", USDC, "onchain"),
            _src("dexscreener", "bsc", USDC, "market"),
        ),
        now=NOW,
    )
    assert res.token.state == IdentityState.CONFLICT
    assert any("provider_chain_mismatch:dexscreener" in c for c in res.conflicts)
    assert res.provenance
    assert not identity_allows_positive_decision(res)


def test_symbol_only_is_unresolved_and_does_not_guess():
    res = resolve_identity(
        chain="ethereum",
        symbol="PEPE",
        alias_matches=(
            {"chain": "ethereum", "address": USDC, "symbol": "PEPE"},
            {"chain": "ethereum", "address": WETH, "symbol": "PEPE"},
        ),
        now=NOW,
    )
    assert res.token.state == IdentityState.UNRESOLVED
    assert res.token.token_id is None
    assert len(res.choices) == 2
    assert not identity_allows_positive_decision(res)
    assert not token_monitoring_allowed(res)


def test_symbol_is_alias_never_identity():
    a = resolve_identity(
        chain="ethereum", address=USDC, symbol="USDC",
        sources=_min_sources("ethereum", USDC), now=NOW,
    )
    b = resolve_identity(
        chain="ethereum", address=USDC, symbol="USDCoin",
        sources=_min_sources("ethereum", USDC), now=NOW,
    )
    assert a.token.token_id == b.token.token_id
    assert a.token.symbol_alias != b.token.symbol_alias


def test_pool_mismatch_blocks_liquidity_claims_not_token_monitoring():
    res = resolve_identity(
        chain="ethereum",
        address=USDC,
        sources=_min_sources("ethereum", USDC),
        pool_dex="uniswap",
        pool_dex_version="v2",
        pool_address=WETH,
        pool_base_token=WETH,
        now=NOW,
    )
    assert res.token.state == IdentityState.VERIFIED
    assert res.pool is not None
    assert res.pool.state == IdentityState.CONFLICT
    assert res.pool.belongs_to_token is False
    assert res.pools[0] is res.pool
    assert token_monitoring_allowed(res)
    assert not pool_liquidity_claims_allowed(res)
    assert identity_allows_positive_decision(res)


def test_unresolved_pool_on_verified_token_forbids_pool_liquidity_claims():
    res = resolve_identity(
        chain="ethereum",
        address=USDC,
        sources=_min_sources("ethereum", USDC),
        pool_dex="uniswap",
        pool_dex_version="v3",
        pool_address=WETH,
        now=NOW,
    )
    assert res.token.state == IdentityState.VERIFIED
    assert res.pool is not None
    assert res.pool.state == IdentityState.UNRESOLVED
    assert res.pool.reason == "pool_base_unknown"
    assert token_monitoring_allowed(res)
    assert not pool_liquidity_claims_allowed(res)


def test_verified_pool_belonging_allows_liquidity_claims():
    res = resolve_identity(
        chain="solana",
        address=SOL,
        sources=_min_sources("solana", SOL),
        pool_dex="raydium",
        pool_address=SOL_USDC,
        pool_base_token=SOL,
        now=NOW,
    )
    assert res.token.state == IdentityState.VERIFIED
    assert res.pool is not None
    assert res.pool.state == IdentityState.VERIFIED
    assert res.pool.belongs_to_token is True
    assert res.pool.pair_id == pair_id("solana", "raydium", SOL_USDC)
    assert res.dex is not None and res.dex.dex_id == "raydium"
    assert pool_liquidity_claims_allowed(res)


def test_provider_address_conflict_is_preserved():
    res = resolve_identity(
        chain="ethereum",
        address=USDC,
        sources=(
            _src("rpc", "ethereum", USDC, "onchain"),
            _src("dexscreener", "ethereum", WETH, "market"),
        ),
        now=NOW,
    )
    assert res.token.state == IdentityState.CONFLICT
    assert any("provider_address_mismatch:dexscreener" in c for c in res.conflicts)
    assert len(res.provenance) == 2
    assert res.token.address_canonical == USDC_LOWER
    assert not identity_allows_positive_decision(res)
    assert not identity_allows_identity_mutation(res)


def test_stale_identity():
    res = resolve_identity(
        chain="ethereum",
        address=USDC,
        sources=(
            _src("rpc", "ethereum", USDC, "onchain", age=8 * 24 * 3600),
            _src("dexscreener", "ethereum", USDC, "market", age=8 * 24 * 3600),
        ),
        now=NOW,
    )
    assert res.token.state == IdentityState.STALE
    assert not identity_allows_positive_decision(res)


def test_insufficient_sources_unresolved_not_stale():
    res = resolve_identity(
        chain="ethereum",
        address=USDC,
        sources=(_src("dexscreener", "ethereum", USDC, "market", age=8 * 24 * 3600),),
        now=NOW,
    )
    assert res.token.state == IdentityState.UNRESOLVED
    assert res.token.reason == "insufficient_independent_sources"


def test_duplicate_identity_same_token_id():
    a = resolve_identity(
        chain="ethereum", address=USDC, sources=_min_sources("ethereum", USDC), now=NOW,
    )
    b = resolve_identity(
        chain="ETH", address=USDC_LOWER, sources=_min_sources("ethereum", USDC_LOWER), now=NOW,
    )
    assert a.token.token_id == b.token.token_id
    assert a.token.token_id == token_id("ethereum", USDC)


def test_solana_case_difference_is_not_the_same_identity():
    a = resolve_identity(
        chain="solana", address=SOL, sources=_min_sources("solana", SOL), now=NOW,
    )
    lower = SOL.lower()
    # lowercased SOL is not a valid 32-byte pubkey AND not the same string
    b = resolve_identity(
        chain="solana", address=lower, sources=_min_sources("solana", lower), now=NOW,
    )
    if b.token.state != IdentityState.INVALID:
        assert a.token.token_id != b.token.token_id


def test_unsupported_chain():
    res = resolve_identity(chain="foobar", address=USDC, now=NOW)
    assert res.chain.state == IdentityState.UNSUPPORTED
    assert res.token.state == IdentityState.UNSUPPORTED
    assert not identity_allows_positive_decision(res)


def test_missing_chain_invalid():
    res = resolve_identity(chain=None, address=USDC, now=NOW)
    assert res.chain.state == IdentityState.INVALID
    assert res.token.state == IdentityState.INVALID


def test_no_silent_identity_overwrite():
    res = resolve_identity(
        chain="ethereum", address=USDC, sources=_min_sources("ethereum", USDC), now=NOW,
    )
    with pytest.raises(Exception):
        res.token.state = IdentityState.VERIFIED  # type: ignore[misc]
    with pytest.raises(Exception):
        res.token.token_id = "mutated"  # type: ignore[misc]


def test_every_pool_is_preserved():
    res = resolve_identity(
        chain="solana",
        address=SOL,
        sources=_min_sources("solana", SOL),
        pool_dex="raydium",
        pool_address=SOL_USDC,
        pool_base_token=SOL,
        pools=(
            {"dex_id": "orca", "address": SOL, "base_token": SOL},
        ),
        now=NOW,
    )
    assert len(res.pools) == 2
    assert {p.dex_id for p in res.pools} == {"raydium", "orca"}


def test_dex_registry_is_versioned_and_ambiguous_without_version():
    assert registry_version() == "dex-registry-v1"
    _ver, rows = load_dex_registry()
    assert rows
    assert lookup_dex("ethereum", "uniswap") is None
    v2 = lookup_dex("ethereum", "uniswap", "v2")
    v3 = lookup_dex("ethereum", "uniswap", "v3")
    assert v2 is not None and v3 is not None
    assert v2.version != v3.version
    assert lookup_dex("solana", "raydium") is not None


def test_blocking_states_cannot_produce_positive_surfaces():
    for state in (
        IdentityState.INVALID,
        IdentityState.CONFLICT,
        IdentityState.UNRESOLVED,
        IdentityState.STALE,
        IdentityState.UNSUPPORTED,
    ):
        res = IdentityResolution(
            chain=verified_identity_fixture().chain,
            token=TokenIdentity(
                "ethereum", USDC_LOWER, USDC, "x", "USDC", "USD Coin", state, "fixture",
            ),
            pool=None,
            dex=None,
        )
        assert not identity_allows_positive_decision(res)
        assert not identity_allows_alert(res)
        assert not identity_allows_paper_candidate(res)
        assert not identity_allows_identity_mutation(res)


def test_missing_identity_is_fail_closed():
    assert not identity_allows_positive_decision(None)
    assert not token_monitoring_allowed(None)
    assert not pool_liquidity_claims_allowed(None)


def _healthy_candidate():
    return NormalizedTokenCandidate(
        chain="solana",
        address="Tok111",
        symbol="TOK",
        name="TOK Token",
        metrics=MarketMetrics(
            price_usd=0.002, liquidity_usd=150_000,
            volume_5m=9_000, volume_1h=30_000, volume_24h=250_000,
            txns_5m_buys=90, txns_5m_sells=25,
            txns_1h_buys=400, txns_1h_sells=250, price_change_1h=12.0,
        ),
        security=SecuritySignals(
            is_honeypot=False, sell_tax_pct=1.0, buy_tax_pct=1.0,
            liquidity_locked_pct=95.0, has_mint_authority=False,
            has_freeze_authority=False, is_contract_verified=True,
            top10_holder_concentration_pct=20.0,
        ),
        source_provider="dexscreener",
        retrieved_ts=NOW,
    )


def test_advisor_missing_identity_cannot_enter():
    cand = _healthy_candidate()
    report = OpportunityScorer().evaluate(cand)
    advice = DecisionAdvisor(bankroll_usd=1000.0).advise_entry(
        cand, report, exitability=ExitabilityAnalyzer().analyze(cand, 200), identity=None,
    )
    assert advice.action == "AVOID"
    assert advice.is_actionable is False
    assert advice.identity_state == "MISSING"
    assert any("Identity gate" in v for v in advice.hard_vetoes)


def test_advisor_conflict_identity_cannot_enter():
    cand = _healthy_candidate()
    report = OpportunityScorer().evaluate(cand)
    conflicted = resolve_identity(
        chain="ethereum",
        address=USDC,
        sources=(
            _src("rpc", "ethereum", USDC, "onchain"),
            _src("dexscreener", "ethereum", WETH, "market"),
        ),
        now=NOW,
    )
    advice = DecisionAdvisor(bankroll_usd=1000.0).advise_entry(
        cand, report, exitability=ExitabilityAnalyzer().analyze(cand, 200),
        identity=conflicted,
    )
    assert advice.action == "AVOID"
    assert advice.identity_state == "CONFLICT"


def test_advisor_verified_identity_can_still_enter():
    cand = _healthy_candidate()
    report = OpportunityScorer().evaluate(cand)
    advice = DecisionAdvisor(bankroll_usd=1000.0).advise_entry(
        cand, report, exitability=ExitabilityAnalyzer().analyze(cand, 200),
        identity=verified_identity_fixture(),
    )
    assert advice.action == "ENTER"
    assert advice.identity_state == "VERIFIED"
