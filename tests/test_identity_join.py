"""W4 Slice 4 — isolated canonical join boundary."""
from __future__ import annotations

from pathlib import Path

from architecture.identity.fusion import (
    CanonicalTokenId,
    FallbackKind,
    IdentityConflict,
    PoolAddress,
    ProviderResourceRef,
    RelationshipKind,
    RepresentationKind,
    TokenAddress,
    TokenIdNamespace,
    identity_conflict,
    identity_observation,
    identity_relationship,
    is_canonical_verified,
    pool_address,
    provider_resource_ref,
    resolution_version_ref,
    token_address,
)
from architecture.identity.join import (
    CONSUMER_CONTRACT,
    JoinClass,
    classify_canonical_join,
    permits_canonical_join,
)
from architecture.identity.resolution_contract import (
    compose_resolution_input,
    plan_fallback,
    plan_pool_address,
    plan_provider_disagreement,
    plan_provider_resource,
    plan_symbol,
    plan_token_address,
)
from architecture.identity.types import IdentityResolution, IdentityState, TokenIdentity
from tests.helpers_identity import verified_identity_fixture

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "architecture" / "identity" / "join.py").read_text(encoding="utf-8")

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
    "is_canonical_join_key",
    "resolve_identity(",
)

PRODUCTION = (
    ROOT / "architecture" / "runtime" / "__main__.py",
    ROOT / "architecture" / "runtime" / "__init__.py",
    ROOT / "architecture" / "pipeline" / "orchestrator.py",
    ROOT / "architecture" / "identity" / "__init__.py",
    ROOT / "architecture" / "knowledge" / "__init__.py",
)


def _with_token_state(ident: IdentityResolution, state: IdentityState, **kwargs) -> IdentityResolution:
    token = ident.token
    fields = {
        "chain": token.chain,
        "address_canonical": token.address_canonical,
        "address_input": token.address_input,
        "token_id": token.token_id,
        "symbol_alias": token.symbol_alias,
        "name_alias": token.name_alias,
        "state": state,
        "reason": f"test_{state.value.lower()}",
    }
    fields.update(kwargs)
    return IdentityResolution(
        chain=ident.chain,
        token=TokenIdentity(**fields),
        pool=None,
        dex=None,
        policy_version=ident.policy_version,
        computed_ts=ident.computed_ts,
    )


def _assert_not_canonical(decision) -> None:
    assert decision.classification is not JoinClass.CANONICAL_JOIN
    assert decision.permits_canonical_join is False
    assert decision.as_dict()["permits_canonical_join"] is False
    assert decision.as_dict()["identity_state_emitted"] is None
    assert decision.classification.value != IdentityState.VERIFIED.value
    assert "VERIFIED" not in JoinClass.__members__


def test_source_isolation():
    for token in FORBIDDEN:
        assert token not in SRC, token
    assert "from architecture.identity.resolution import" not in SRC
    assert CONSUMER_CONTRACT


def test_not_wired_into_runtime_or_package_init():
    for path in PRODUCTION:
        text = path.read_text(encoding="utf-8")
        assert "classify_canonical_join" not in text
        assert "identity.join" not in text
        assert "from architecture.identity.join" not in text


def test_join_class_is_not_identity_state():
    assert "VERIFIED" not in JoinClass.__members__
    assert set(JoinClass) != set(IdentityState)


def test_verified_identity_resolution_is_canonical_join():
    verified = verified_identity_fixture(token_id="abc123canonicalid", address=SOL)
    decision = classify_canonical_join(verified)
    assert decision.classification is JoinClass.CANONICAL_JOIN
    assert decision.permits_canonical_join is True
    assert permits_canonical_join(verified) is True
    assert is_canonical_verified(verified) is True
    assert decision.as_dict()["identity_state_emitted"] is None


def test_unresolved_resolution_is_not_canonical():
    unresolved = _with_token_state(verified_identity_fixture(), IdentityState.UNRESOLVED)
    decision = classify_canonical_join(unresolved)
    assert decision.classification is JoinClass.UNRESOLVED
    _assert_not_canonical(decision)


def test_conflict_resolution_is_not_canonical():
    conflict = _with_token_state(verified_identity_fixture(), IdentityState.CONFLICT)
    decision = classify_canonical_join(conflict)
    _assert_not_canonical(decision)
    assert decision.classification is JoinClass.UNRESOLVED


def test_stale_resolution_is_not_canonical():
    stale = _with_token_state(verified_identity_fixture(), IdentityState.STALE)
    decision = classify_canonical_join(stale)
    _assert_not_canonical(decision)
    assert decision.classification is JoinClass.UNRESOLVED


def test_invalid_resolution_is_not_canonical():
    invalid = _with_token_state(verified_identity_fixture(), IdentityState.INVALID)
    decision = classify_canonical_join(invalid)
    _assert_not_canonical(decision)
    assert decision.classification is JoinClass.REJECTED


def test_unsupported_resolution_is_not_canonical():
    unsupported = _with_token_state(verified_identity_fixture(), IdentityState.UNSUPPORTED)
    decision = classify_canonical_join(unsupported)
    _assert_not_canonical(decision)
    assert decision.classification is JoinClass.REJECTED


def test_missing_input_is_not_canonical():
    decision = classify_canonical_join(None)
    _assert_not_canonical(decision)
    assert decision.classification is JoinClass.REJECTED
    empty = classify_canonical_join()
    _assert_not_canonical(empty)


def test_forged_canonical_token_id_is_not_canonical():
    forged = CanonicalTokenId(value="forged", resolution_version="v9")
    decision = classify_canonical_join(forged)
    _assert_not_canonical(decision)
    assert decision.classification is JoinClass.REJECTED
    assert permits_canonical_join(forged) is False
    assert permits_canonical_join(subject="PEPE", resolution=forged) is False


def test_arbitrary_token_id_string_is_not_canonical():
    decision = classify_canonical_join("deadbeefcafebabe")
    _assert_not_canonical(decision)
    ns = TokenIdNamespace(value="deadbeefcafebabe")
    _assert_not_canonical(classify_canonical_join(ns))
    _assert_not_canonical(classify_canonical_join("unvalidated_token_id:abc123"))


def test_forged_verified_token_address_is_not_canonical():
    forged = TokenAddress(
        chain="solana",
        address=SOL,
        address_input=SOL,
        validation_state=IdentityState.VERIFIED,
        validation_reason="forged",
    )
    decision = classify_canonical_join(forged)
    _assert_not_canonical(decision)
    assert decision.classification is JoinClass.REJECTED
    assert permits_canonical_join(forged) is False


def test_symbol_is_display_only():
    for subject in (
        "PEPE",
        plan_symbol("PEPE"),
        identity_observation(representation_kind=RepresentationKind.SYMBOL, original_value="PEPE"),
        RepresentationKind.NAME,
        compose_resolution_input(symbol="PEPE", original_value="PEPE"),
    ):
        decision = classify_canonical_join(subject)
        _assert_not_canonical(decision)
        assert decision.classification in {JoinClass.DISPLAY_ONLY, JoinClass.UNRESOLVED}


def test_fallback_key_is_operational_or_unresolved():
    for raw in (
        "solana:unknown",
        "solana:sym:PEPE",
        "manual:PEPE",
        "solana:PEPE",
        "unvalidated_token_id",
        FallbackKind.CHAIN_SYM_SYMBOL,
        plan_fallback("manual:PEPE"),
    ):
        decision = classify_canonical_join(raw)
        _assert_not_canonical(decision)
        assert decision.classification in {
            JoinClass.OPERATIONAL_JOIN,
            JoinClass.UNRESOLVED,
        }


def test_provider_resource_is_provider_reference():
    ref = provider_resource_ref("geckoterminal", f"solana_{POOL}", "pool")
    decision = classify_canonical_join(ref)
    assert decision.classification is JoinClass.PROVIDER_REFERENCE
    _assert_not_canonical(decision)
    _assert_not_canonical(classify_canonical_join(plan_provider_resource("gecko", f"solana_{POOL}")))


def test_pool_address_is_pool_reference():
    pool = pool_address("solana", POOL)
    decision = classify_canonical_join(pool)
    assert decision.classification is JoinClass.POOL_REFERENCE
    assert isinstance(pool, PoolAddress)
    _assert_not_canonical(decision)
    _assert_not_canonical(classify_canonical_join(plan_pool_address("solana", POOL)))


def test_relationship_is_not_canonical():
    rel = identity_relationship(
        RelationshipKind.WRAPS,
        {"address": SOL},
        {"address": SOL_USDC},
    )
    decision = classify_canonical_join(rel)
    _assert_not_canonical(decision)
    alias = identity_relationship(RelationshipKind.ALIASES, {"symbol": "PEPE"}, {"symbol": "PEPE2"})
    _assert_not_canonical(classify_canonical_join(alias))


def test_historical_mapping_is_historical_reference():
    rel = identity_relationship(
        RelationshipKind.MIGRATES_TO,
        {"entity": "OLD_ENTITY"},
        {"entity": "NEW_ENTITY"},
    )
    decision = classify_canonical_join(rel)
    assert decision.classification is JoinClass.HISTORICAL_REFERENCE
    _assert_not_canonical(decision)
    verified = verified_identity_fixture()
    version = resolution_version_ref(verified, "v1")
    hist = classify_canonical_join(version)
    assert hist.classification is JoinClass.HISTORICAL_REFERENCE
    _assert_not_canonical(hist)


def test_malformed_resolution_is_rejected():
    class Fake:
        token = type(
            "T",
            (),
            {"state": IdentityState.VERIFIED, "token_id": "x", "address_canonical": SOL},
        )()

    decision = classify_canonical_join(Fake())
    assert decision.classification is JoinClass.REJECTED
    _assert_not_canonical(decision)
    _assert_not_canonical(classify_canonical_join({"state": "VERIFIED", "token_id": "x"}))
    _assert_not_canonical(classify_canonical_join(IdentityState.VERIFIED))


def test_unsupported_chain_is_rejected_or_unresolved():
    addr = token_address("aptos", SOL)
    decision = classify_canonical_join(addr)
    _assert_not_canonical(decision)
    assert decision.classification in {JoinClass.REJECTED, JoinClass.UNRESOLVED}
    _assert_not_canonical(classify_canonical_join(token_address("sol", SOL)))


def test_conflicting_provider_evidence_is_not_canonical():
    plan = plan_provider_disagreement("solana", {"a": SOL, "b": SOL_USDC})
    decision = classify_canonical_join(plan)
    _assert_not_canonical(decision)
    conflict = identity_conflict(left={"address": SOL}, right={"address": SOL_USDC}, reason="disagree")
    _assert_not_canonical(classify_canonical_join(conflict))
    assert isinstance(conflict, IdentityConflict)


def test_solana_canonical_join_requires_identity_resolution():
    verified = verified_identity_fixture(address=SOL, token_id="sol-canon")
    assert classify_canonical_join(verified).classification is JoinClass.CANONICAL_JOIN
    assert verified.token.address_canonical == SOL
    operational = classify_canonical_join(token_address("solana", SOL))
    assert operational.classification is JoinClass.OPERATIONAL_JOIN
    _assert_not_canonical(operational)


def test_lowercased_solana_key_is_never_canonical():
    folded = token_address("solana", SOL.lower())
    decision = classify_canonical_join(folded)
    _assert_not_canonical(decision)
    _assert_not_canonical(classify_canonical_join(SOL.lower()))
    _assert_not_canonical(classify_canonical_join(f"solana:{SOL.lower()}"))


def test_evm_canonical_join_requires_identity_resolution():
    verified = verified_identity_fixture(chain="ethereum", address=USDC_LOWER, token_id="evm-canon")
    assert classify_canonical_join(verified).classification is JoinClass.CANONICAL_JOIN
    operational = classify_canonical_join(token_address("ethereum", USDC))
    assert operational.classification is JoinClass.OPERATIONAL_JOIN
    assert operational.permits_canonical_join is False
    assert token_address("ethereum", USDC).address == USDC_LOWER


def test_empty_token_id_is_not_canonical():
    empty = _with_token_state(
        verified_identity_fixture(),
        IdentityState.VERIFIED,
        token_id="",
    )
    decision = classify_canonical_join(empty)
    _assert_not_canonical(decision)
    assert is_canonical_verified(empty) is False


def test_missing_canonical_address_is_not_canonical():
    missing = _with_token_state(
        verified_identity_fixture(),
        IdentityState.VERIFIED,
        address_canonical=None,
    )
    decision = classify_canonical_join(missing)
    _assert_not_canonical(decision)
    assert is_canonical_verified(missing) is False


def test_pool_token_representation_mismatch_is_not_canonical():
    decision = classify_canonical_join(
        token_address("solana", SOL),
        pool_address("solana", POOL),
    )
    _assert_not_canonical(decision)
    same_string = classify_canonical_join(
        token_address("solana", SOL),
        pool_address("solana", SOL),
    )
    _assert_not_canonical(same_string)


def test_adversarial_forged_wrapper_plus_verified_looking_address_and_symbol():
    decision = classify_canonical_join(
        CanonicalTokenId(value="forged"),
        TokenAddress(
            chain="solana",
            address=SOL,
            address_input=SOL,
            validation_state=IdentityState.VERIFIED,
            validation_reason="forged",
        ),
        "PEPE",
    )
    _assert_not_canonical(decision)


def test_adversarial_provider_symbol_and_pool_are_not_canonical():
    decision = classify_canonical_join(
        provider_resource_ref("gecko", f"solana_{POOL}", "pool"),
        "PEPE",
        pool_address("solana", POOL),
    )
    _assert_not_canonical(decision)


def test_adversarial_fallback_plus_historical_relationship():
    rel = identity_relationship(
        RelationshipKind.SUPERSEDED,
        {"old": POOL},
        {"new": SOL, "state": "VERIFIED"},
    )
    decision = classify_canonical_join("manual:PEPE", rel)
    _assert_not_canonical(decision)


def test_adversarial_forged_token_address_plus_arbitrary_token_id():
    decision = classify_canonical_join(
        TokenAddress(
            chain="solana",
            address=SOL,
            address_input=SOL,
            validation_state=IdentityState.VERIFIED,
            validation_reason="forged",
        ),
        "arbitrary-token-id",
    )
    _assert_not_canonical(decision)
    assert permits_canonical_join(
        TokenAddress(
            chain="solana",
            address=SOL,
            address_input=SOL,
            validation_state=IdentityState.VERIFIED,
            validation_reason="forged",
        ),
        resolution=CanonicalTokenId(value="arbitrary-token-id"),
    ) is False


def test_only_identity_resolution_crosses_canonical_boundary():
    verified = verified_identity_fixture()
    via_kw = classify_canonical_join("PEPE", resolution=verified)
    assert via_kw.classification is JoinClass.CANONICAL_JOIN
    via_pos = classify_canonical_join(verified, "PEPE")
    assert via_pos.classification is JoinClass.CANONICAL_JOIN
    without = classify_canonical_join("PEPE")
    _assert_not_canonical(without)


def test_identity_state_field_alone_is_not_canonical():
    _assert_not_canonical(classify_canonical_join(IdentityState.VERIFIED))
    _assert_not_canonical(classify_canonical_join(IdentityState.CONFLICT))


def test_usable_token_address_is_operational_not_canonical():
    addr = token_address("solana", SOL)
    assert addr.validation_state is IdentityState.UNRESOLVED
    decision = classify_canonical_join(addr)
    assert decision.classification is JoinClass.OPERATIONAL_JOIN
    _assert_not_canonical(decision)
    _assert_not_canonical(classify_canonical_join(plan_token_address("solana", SOL)))


def test_equivalent_decisions_are_deterministic():
    verified = verified_identity_fixture(token_id="same")
    a = classify_canonical_join(verified)
    b = classify_canonical_join(verified)
    assert a == b
    assert a.as_dict() == b.as_dict()
