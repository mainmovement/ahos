"""W4 Slice 1 — isolated typed identity foundation contracts."""
from __future__ import annotations

from pathlib import Path

import pytest

from architecture.identity.fusion import (
    CONSUMER_CONTRACT,
    CanonicalTokenId,
    FallbackKind,
    PoolAddress,
    ProviderResourceRef,
    RelationshipKind,
    RepresentationKind,
    TokenAddress,
    TokenIdNamespace,
    TokenRepresentation,
    classify_fallback_key,
    classify_gecko_new_pool_item,
    copy_canonical_token_id,
    display_search_fold,
    distinct_entity_types,
    fallback_may_be_canonical,
    gecko_silently_treats_pool_as_token,
    identity_conflict,
    identity_observation,
    identity_relationship,
    is_canonical_join_key,
    is_canonical_verified,
    pool_address,
    pool_representation,
    provider_resource_ref,
    relationship_grants_canonical,
    resolution_version_ref,
    token_address,
    token_representation,
)
from architecture.identity.types import (
    ChainIdentity,
    IdentityResolution,
    IdentityState,
    TokenIdentity,
)
from tests.helpers_identity import verified_identity_fixture

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "architecture" / "identity" / "fusion.py").read_text(encoding="utf-8")

SOL = "So11111111111111111111111111111111111111112"
SOL_USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
POOL = "58oQChx4yWmvKdwLLZzBi4ChoCc2fqCUWBkwMihLYQo2"
USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
USDC_LOWER = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"

FORBIDDEN = (
    "discovery.",
    "paper_trading",
    "architecture.runtime",
    "architecture.pipeline",
    "architecture.learning",
    "architecture.calibration",
    "architecture.cognitive",
    "import sqlite3",
    "import hashlib",
    "datetime.now",
    "time.time",
    "uuid",
    "telegram",
    "wallet",
)

PRODUCTION = (
    ROOT / "architecture" / "runtime" / "__main__.py",
    ROOT / "architecture" / "runtime" / "__init__.py",
    ROOT / "architecture" / "pipeline" / "orchestrator.py",
    ROOT / "architecture" / "identity" / "__init__.py",
    ROOT / "architecture" / "knowledge" / "__init__.py",
)

RELATIONSHIP_KINDS = (
    RelationshipKind.WRAPS,
    RelationshipKind.BRIDGES_TO,
    RelationshipKind.MIGRATES_TO,
    RelationshipKind.SUCCEEDS,
    RelationshipKind.PROXIES,
    RelationshipKind.ALIASES,
    RelationshipKind.PAIRS_WITH,
    RelationshipKind.CONTAINS,
    RelationshipKind.OBSERVED_AS,
    RelationshipKind.CONFLICTS_WITH,
    RelationshipKind.SUPERSEDED,
    RelationshipKind.IDENTITY,
    RelationshipKind.QUOTES,
)


def _unverified(**kwargs) -> IdentityResolution:
    ident = verified_identity_fixture(**kwargs)
    token = ident.token
    return IdentityResolution(
        chain=ident.chain,
        token=TokenIdentity(
            chain=token.chain,
            address_canonical=token.address_canonical,
            address_input=token.address_input,
            token_id=token.token_id,
            symbol_alias=token.symbol_alias,
            name_alias=token.name_alias,
            state=IdentityState.UNRESOLVED,
            reason="insufficient_independent_sources",
        ),
        pool=None,
        dex=None,
        policy_version=ident.policy_version,
        computed_ts=ident.computed_ts,
    )


def test_source_isolation():
    for token in FORBIDDEN:
        assert token not in SRC, token
    assert "resolve_identity" not in SRC
    assert "from discovery" not in SRC
    assert "discovery.identity" not in SRC


def test_not_wired_into_runtime_or_package_init():
    for path in PRODUCTION:
        text = path.read_text(encoding="utf-8")
        assert "fusion" not in text
        assert "compose_feedback_signal" not in text
        assert "compose_evidence_graph" not in text


def test_only_verified_resolution_is_canonical():
    verified = verified_identity_fixture(token_id="abc123canonicalid")
    assert is_canonical_verified(verified) is True
    copied = copy_canonical_token_id(verified, resolution_version="v1")
    assert isinstance(copied, CanonicalTokenId)
    assert copied.value == "abc123canonicalid"
    assert copied.resolution_version == "v1"


def test_unverified_resolution_is_not_canonical():
    unresolved = _unverified(token_id="looks_like_a_hash")
    assert is_canonical_verified(unresolved) is False
    assert copy_canonical_token_id(unresolved) is None


def test_verified_without_token_id_is_not_canonical():
    bare = verified_identity_fixture(token_id="")
    token = bare.token
    empty = IdentityResolution(
        chain=bare.chain,
        token=TokenIdentity(
            chain=token.chain,
            address_canonical=token.address_canonical,
            address_input=token.address_input,
            token_id=None,
            symbol_alias=token.symbol_alias,
            name_alias=token.name_alias,
            state=IdentityState.VERIFIED,
            reason="test",
        ),
        pool=None,
        dex=None,
    )
    assert is_canonical_verified(empty) is False
    assert copy_canonical_token_id(empty) is None


def test_forged_object_cannot_be_canonical():
    class Fake:
        token = type("T", (), {"state": IdentityState.VERIFIED, "token_id": "x", "address_canonical": "y"})()

    assert is_canonical_verified(Fake()) is False
    assert is_canonical_verified(None) is False
    assert is_canonical_verified({"state": "VERIFIED", "token_id": "x"}) is False


def test_namespace_token_id_is_not_canonical():
    ns = TokenIdNamespace(value="abc123canonicalid")
    assert is_canonical_verified(ns) is False
    assert is_canonical_join_key(ns) is False
    assert ns.as_dict()["authoritative"] is False


def test_pool_token_types_are_distinct():
    tok = token_address("solana", SOL)
    pool = pool_address("solana", POOL)
    assert isinstance(tok, TokenAddress)
    assert isinstance(pool, PoolAddress)
    assert type(tok) is not type(pool)
    assert tok != pool
    assert distinct_entity_types(tok, pool) is True
    assert tok.entity_kind == "TOKEN"
    assert pool.entity_kind == "POOL"


def test_same_string_still_different_entity_types():
    tok = token_address("solana", SOL)
    pool = pool_address("solana", SOL)
    assert tok.address == pool.address
    assert type(tok) is not type(pool)
    assert tok != pool


def test_gecko_new_pool_shape_does_not_treat_pool_as_token():
    item = {
        "id": f"solana_{POOL}",
        "type": "pool",
        "attributes": {"address": POOL, "name": "SOL / USDC"},
        "relationships": {
            "base_token": {"data": {"id": f"solana_{SOL}", "type": "token"}},
            "quote_token": {"data": {"id": f"solana_{SOL_USDC}", "type": "token"}},
        },
    }
    classified = classify_gecko_new_pool_item(item)
    assert classified.item_type == "pool"
    assert isinstance(classified.pool_address, PoolAddress)
    assert classified.pool_address.address == POOL
    assert isinstance(classified.base_token_address, TokenAddress)
    assert classified.base_token_address.address == SOL
    assert isinstance(classified.quote_token_address, TokenAddress)
    assert classified.quote_token_address.address == SOL_USDC
    assert isinstance(classified.provider_pool_id, ProviderResourceRef)
    assert classified.provider_pool_id.value == f"solana_{POOL}"
    assert gecko_silently_treats_pool_as_token(classified) is False
    assert is_canonical_verified(classified) is False
    assert copy_canonical_token_id(classified) is None
    assert is_canonical_join_key(classified.provider_pool_id) is False


def test_provider_resource_cannot_mint_canonical_identity():
    ref = provider_resource_ref("coingecko", "solana_xyz", "token")
    assert is_canonical_verified(ref) is False
    assert copy_canonical_token_id(ref) is None
    assert is_canonical_join_key(RepresentationKind.PROVIDER_RESOURCE, ref.value) is False


def test_solana_case_preserved():
    tok = token_address("solana", SOL)
    assert tok.address == SOL
    assert tok.address != SOL.lower()
    assert "A" in tok.address or "S" in tok.address
    folded = display_search_fold(SOL)
    assert folded == SOL.lower()
    assert folded != tok.address
    assert is_canonical_join_key("search_fold", folded) is False
    assert is_canonical_join_key("display_search_fold", folded) is False


def test_solana_case_distinct_strings_are_not_equal():
    a = token_address("solana", "ABCd111111111111111111111111111111111111111")
    b = token_address("solana", "ABCD111111111111111111111111111111111111111")
    assert a.address != b.address
    assert a.address_input != b.address_input


def test_lowercased_solana_cannot_canonicalize():
    folded = token_address("solana", SOL.lower())
    assert is_canonical_verified(folded) is False
    assert copy_canonical_token_id(folded) is None
    assert isinstance(folded, TokenAddress)
    rep = token_representation(token_addr=folded, symbol="SOL")
    assert is_canonical_verified(rep) is False


def test_evm_checksum_insensitive_matches_existing_validator():
    a = token_address("ethereum", USDC)
    b = token_address("ethereum", USDC_LOWER)
    assert a.address == USDC_LOWER
    assert b.address == USDC_LOWER
    assert a.address == b.address
    assert a.validation_state is IdentityState.UNRESOLVED
    assert is_canonical_verified(a) is False


def test_symbol_name_alias_cannot_canonicalize():
    for kind, value in (
        (RepresentationKind.SYMBOL, "PEPE"),
        (RepresentationKind.NAME, "Pepe Token"),
        (RepresentationKind.ALIAS, "PEPE"),
        (FallbackKind.CHAIN_SYM_SYMBOL, "solana:sym:PEPE"),
        (FallbackKind.MANUAL_SYMBOL, "manual:PEPE"),
        (FallbackKind.CHAIN_SYMBOL, "solana:PEPE"),
    ):
        obs = identity_observation(representation_kind=RepresentationKind.SYMBOL, original_value=value)
        assert is_canonical_verified(obs) is False
        assert copy_canonical_token_id(obs) is None
        assert is_canonical_join_key(kind, value) is False
        assert fallback_may_be_canonical(kind) is False
    rep = token_representation(symbol="PEPE", name="Pepe")
    assert rep.token_address is None
    assert is_canonical_verified(rep) is False


def test_token_representation_symbol_does_not_fill_address():
    rep = token_representation(symbol="PEPE", name="Pepe", source="ui")
    assert isinstance(rep, TokenRepresentation)
    assert rep.token_address is None
    assert copy_canonical_token_id(rep) is None


def test_fallback_keys_remain_non_canonical():
    samples = {
        "solana:unknown": FallbackKind.CHAIN_UNKNOWN,
        "solana:sym:PEPE": FallbackKind.CHAIN_SYM_SYMBOL,
        "manual:PEPE": FallbackKind.MANUAL_SYMBOL,
        "unvalidated_token_id:abc123": FallbackKind.UNVALIDATED_TOKEN_ID,
    }
    for raw, expected in samples.items():
        assert classify_fallback_key(raw) is expected
        assert fallback_may_be_canonical(expected) is False
        assert is_canonical_join_key(expected, raw) is False
        assert is_canonical_verified(raw) is False
        assert copy_canonical_token_id(raw) is None


def test_relationships_do_not_grant_canonical_identity():
    left = token_address("solana", SOL).as_dict()
    right = pool_address("solana", POOL).as_dict()
    for kind in RELATIONSHIP_KINDS:
        rel = identity_relationship(kind, left, right)
        assert relationship_grants_canonical(rel) is False
        assert rel.as_dict()["grants_canonical_identity"] is False
        assert is_canonical_verified(rel) is False
        assert copy_canonical_token_id(rel) is None


def test_historical_versions_are_append_only():
    older = verified_identity_fixture(token_id="hist-v1")
    newer = _unverified(token_id="hist-v1")
    v1 = resolution_version_ref(older, "v1")
    v2 = resolution_version_ref(newer, "v2")
    rel = identity_relationship(
        RelationshipKind.SUPERSEDED,
        v1.as_dict(),
        v2.as_dict(),
        note="provider_corrected_pool_as_token",
    )
    assert v1.resolution.token.state is IdentityState.VERIFIED
    assert v2.resolution.token.state is IdentityState.UNRESOLVED
    assert v1.resolution_version != v2.resolution_version
    assert is_canonical_verified(v1.resolution) is True
    assert is_canonical_verified(v2.resolution) is False
    assert relationship_grants_canonical(rel) is False
    original = identity_observation(
        source="geckoterminal",
        representation_kind=RepresentationKind.POOL_ADDRESS,
        original_value=POOL,
        normalized_value=POOL,
        observed_at=1_700_000_000.0,
    )
    assert original.original_value == POOL
    with pytest.raises(Exception):
        v1.resolution_version = "mutated"  # type: ignore[misc]


def test_missing_resolution_version_is_not_invented():
    older = verified_identity_fixture()
    with pytest.raises(ValueError):
        resolution_version_ref(older, None)


def test_observation_does_not_invent_timestamp():
    obs = identity_observation(
        source="human",
        representation_kind=RepresentationKind.SYMBOL,
        original_value="PEPE",
    )
    assert obs.observed_at is None
    assert "time.time" not in SRC
    supplied = identity_observation(
        source="human",
        representation_kind=RepresentationKind.TOKEN_ADDRESS,
        original_value=SOL,
        normalized_value=SOL,
        observed_at=123.0,
    )
    assert supplied.observed_at == 123.0


def test_conflict_has_no_winner():
    conflict = identity_conflict(
        source="providers",
        left={"address": SOL},
        right={"address": POOL},
        reason="provider_address_mismatch",
    )
    assert conflict.as_dict()["winner"] is None
    assert is_canonical_verified(conflict) is False


def test_export_mutation_does_not_change_internal_state():
    rel = identity_relationship(
        RelationshipKind.ALIASES,
        {"symbol": "PEPE"},
        {"symbol": "PEPE2"},
    )
    exported = rel.as_dict()
    exported["left"]["symbol"] = "MUTATED"
    assert rel.left["symbol"] == "PEPE"


def test_nested_caller_mapping_is_isolated():
    payload = {"symbol": "PEPE"}
    rel = identity_relationship(RelationshipKind.ALIASES, payload, {"symbol": "X"})
    payload["symbol"] = "MUTATED"
    assert rel.left["symbol"] == "PEPE"


def test_equivalent_inputs_are_deterministic():
    a = token_address("solana", SOL)
    b = token_address("solana", SOL)
    assert a == b
    assert a.as_dict() == b.as_dict()
    g1 = classify_gecko_new_pool_item({
        "id": "solana_p",
        "type": "pool",
        "attributes": {"address": POOL},
        "relationships": {"base_token": {"data": {"id": f"solana_{SOL}"}}},
    })
    g2 = classify_gecko_new_pool_item({
        "id": "solana_p",
        "type": "pool",
        "attributes": {"address": POOL},
        "relationships": {"base_token": {"data": {"id": f"solana_{SOL}"}}},
    })
    assert g1.as_dict() == g2.as_dict()


def test_malformed_identity_cannot_become_verified():
    empty = token_address(None, None)
    assert empty.validation_state is IdentityState.INVALID
    assert is_canonical_verified(empty) is False
    assert copy_canonical_token_id(empty) is None
    pool_rep = pool_representation(source="gecko")
    assert pool_rep.pool_address is None
    assert is_canonical_verified(pool_rep) is False
    assert CONSUMER_CONTRACT


def test_pool_representation_keeps_legs_separate():
    rep = pool_representation(
        pool_addr=pool_address("solana", POOL),
        provider_pool_id=provider_resource_ref("geckoterminal", f"solana_{POOL}", "pool"),
        base_token_address=token_address("solana", SOL),
        quote_token_address=token_address("solana", SOL_USDC),
        source="geckoterminal",
    )
    assert isinstance(rep.pool_address, PoolAddress)
    assert isinstance(rep.base_token_address, TokenAddress)
    assert rep.pool_address.address != rep.base_token_address.address
    assert is_canonical_verified(rep) is False
