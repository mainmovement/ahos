"""W4 Slice 2 — isolated identity resolution planning contract."""
from __future__ import annotations

from pathlib import Path

import pytest

from architecture.identity.fusion import (
    CanonicalTokenId,
    FallbackKind,
    PoolAddress,
    ProviderResourceRef,
    RelationshipKind,
    RepresentationKind,
    TokenAddress,
    TokenIdNamespace,
    classify_fallback_key,
    identity_relationship,
    is_canonical_verified,
    pool_address,
    provider_resource_ref,
    token_address,
)
from architecture.identity.resolution_contract import (
    CANONICALIZATION_BOUNDARY,
    CONSUMER_CONTRACT,
    EvidenceKind,
    ResolutionCandidate,
    ResolutionPlanStatus,
    ResolutionSubjectKind,
    authoritative_canonical,
    compose_resolution_input,
    copy_canonical_if_authoritative,
    fallback_is_canonical,
    plan_fallback,
    plan_gecko_new_pool,
    plan_historical_mapping,
    plan_pool_address,
    plan_promotes_to_verified,
    plan_provider_disagreement,
    plan_provider_resource,
    plan_resolution,
    plan_symbol,
    plan_token_address,
    relationship_is_authority,
    resolution_evidence,
    solana_case_preserved,
)
from architecture.identity.types import IdentityResolution, IdentityState, TokenIdentity
from architecture.identity.validate import validate_address_for_chain
from tests.helpers_identity import verified_identity_fixture

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "architecture" / "identity" / "resolution_contract.py").read_text(encoding="utf-8")

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
)

PRODUCTION = (
    ROOT / "architecture" / "runtime" / "__main__.py",
    ROOT / "architecture" / "runtime" / "__init__.py",
    ROOT / "architecture" / "pipeline" / "orchestrator.py",
    ROOT / "architecture" / "identity" / "__init__.py",
    ROOT / "architecture" / "knowledge" / "__init__.py",
)

FALLBACKS = (
    "solana:unknown",
    "solana:sym:PEPE",
    "solana:symbol",
    "manual:PEPE",
    "solana:PEPE",
    "unvalidated_token_id",
    "unvalidated_token_id:abc123",
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


def _token_candidates(plan) -> list[ResolutionCandidate]:
    return [c for c in plan.candidates if c.subject_kind is ResolutionSubjectKind.TOKEN]


def _kinds(plan) -> set[ResolutionSubjectKind]:
    return {c.subject_kind for c in plan.candidates}


def _assert_not_canonical_plan(plan) -> None:
    assert plan.as_dict()["input"]["is_canonical"] is False
    assert plan.as_dict()["identity_state_emitted"] is None
    assert plan_promotes_to_verified(plan) is False
    assert plan.status is not IdentityState.VERIFIED
    assert plan.status.value != IdentityState.VERIFIED.value
    for ev in plan.evidence:
        assert ev.as_dict()["produces_verified"] is False
    assert is_canonical_verified(plan) is False
    assert authoritative_canonical(plan) is False
    assert copy_canonical_if_authoritative(plan) is None


def test_source_isolation():
    for token in FORBIDDEN:
        assert token not in SRC, token
    assert "from discovery" not in SRC
    assert "discovery.identity" not in SRC
    assert "from architecture.identity.resolution" not in SRC
    assert "resolve_identity(" not in SRC


def test_not_wired_into_runtime_or_package_init():
    for path in PRODUCTION:
        text = path.read_text(encoding="utf-8")
        assert "resolution_contract" not in text
        assert "fusion" not in text
        assert "compose_feedback_signal" not in text
        assert "compose_evidence_graph" not in text


def test_plan_status_enum_has_no_verified():
    assert "VERIFIED" not in ResolutionPlanStatus.__members__
    assert IdentityState.VERIFIED.value not in {s.value for s in ResolutionPlanStatus}
    assert CANONICALIZATION_BOUNDARY[-2] == "VERIFIED"
    assert CANONICALIZATION_BOUNDARY[-1] == "canonical join permitted"
    assert CONSUMER_CONTRACT


def test_token_address_becomes_token_candidate():
    plan = plan_token_address("solana", SOL, source="onchain")
    tokens = _token_candidates(plan)
    assert len(tokens) == 1
    assert tokens[0].subject_kind is ResolutionSubjectKind.TOKEN
    assert isinstance(tokens[0].token_address, TokenAddress)
    assert tokens[0].token_address.address == SOL
    assert tokens[0].pool_address is None
    assert plan.status is ResolutionPlanStatus.READY_FOR_RESOLUTION
    assert plan.requirements.ready is True
    assert plan.existing_canonical is False
    _assert_not_canonical_plan(plan)


def test_pool_address_cannot_become_token_candidate():
    plan = plan_pool_address("solana", POOL, source="geckoterminal")
    assert _token_candidates(plan) == []
    assert ResolutionSubjectKind.POOL in _kinds(plan)
    assert ResolutionSubjectKind.TOKEN not in _kinds(plan)
    for cand in plan.candidates:
        assert not isinstance(cand.pool_address, TokenAddress)
        assert cand.token_address is None
        assert isinstance(cand.pool_address, PoolAddress)
    assert plan.requirements.subject_is_token is False
    assert plan.requirements.pool_alone_insufficient is True
    assert plan.status is ResolutionPlanStatus.UNRESOLVED
    assert plan.existing_canonical is False
    _assert_not_canonical_plan(plan)


def test_same_string_pool_is_still_not_a_token_candidate():
    plan = plan_pool_address("solana", SOL)
    assert _token_candidates(plan) == []
    assert plan.candidates[0].subject_kind is ResolutionSubjectKind.POOL
    assert plan.candidates[0].pool_address.address == SOL
    assert plan.status is not ResolutionPlanStatus.READY_FOR_RESOLUTION
    _assert_not_canonical_plan(plan)


def test_provider_resource_cannot_become_token_candidate():
    plan = plan_provider_resource("geckoterminal", f"solana_{POOL}", chain="solana")
    assert _token_candidates(plan) == []
    assert ResolutionSubjectKind.PROVIDER_RESOURCE in _kinds(plan)
    assert plan.requirements.provider_id_alone_insufficient is True
    assert plan.status is ResolutionPlanStatus.UNRESOLVED
    assert plan.existing_canonical is False
    _assert_not_canonical_plan(plan)


def test_symbol_only_remains_unresolved_or_ambiguous():
    plan = plan_symbol("PEPE", chain="solana", name="Pepe")
    assert _token_candidates(plan) == []
    assert plan.payload.token_address is None
    assert plan.requirements.symbol_alone_insufficient is True
    assert plan.status in {
        ResolutionPlanStatus.AMBIGUOUS,
        ResolutionPlanStatus.UNRESOLVED,
    }
    assert plan.existing_canonical is False
    _assert_not_canonical_plan(plan)


def test_symbol_does_not_select_unique_entity():
    a = plan_symbol("PEPE")
    b = plan_symbol("PEPE", chain="solana")
    assert a.status == b.status
    assert _token_candidates(a) == _token_candidates(b) == []
    assert a.as_dict()["identity_state_emitted"] is None
    assert authoritative_canonical(a.payload) is False


def test_fallback_keys_remain_non_canonical():
    for raw in FALLBACKS:
        plan = plan_fallback(raw)
        assert fallback_is_canonical(plan.payload.fallback_kind) is False
        assert fallback_is_canonical(classify_fallback_key(raw)) is False
        assert plan.requirements.fallback_alone_insufficient is True
        assert plan.requirements.unvalidated_token_id_insufficient is True
        assert plan.status in {
            ResolutionPlanStatus.AMBIGUOUS,
            ResolutionPlanStatus.UNRESOLVED,
            ResolutionPlanStatus.MISSING,
        }
        assert plan.existing_canonical is False
        _assert_not_canonical_plan(plan)


def test_solana_exact_base58_preserved():
    plan = plan_token_address("solana", SOL)
    tok = plan.payload.token_address
    assert tok is not None
    assert tok.address == SOL
    assert tok.address_input == SOL
    assert tok.address != SOL.lower()
    assert solana_case_preserved(tok) is True
    assert plan.requirements.solana_case_ok is True
    assert plan.status is ResolutionPlanStatus.READY_FOR_RESOLUTION
    _assert_not_canonical_plan(plan)


def test_lowercased_solana_remains_non_canonical():
    folded = plan_token_address("solana", SOL.lower())
    tok = folded.payload.token_address
    assert tok is not None
    assert tok.address != SOL
    assert solana_case_preserved(tok) is False
    assert folded.requirements.solana_case_ok is False
    assert folded.requirements.ready is False
    assert folded.status is not ResolutionPlanStatus.READY_FOR_RESOLUTION
    assert folded.existing_canonical is False
    _assert_not_canonical_plan(folded)
    assert authoritative_canonical(tok) is False
    assert copy_canonical_if_authoritative(tok) is None


def test_evm_validation_uses_existing_validator():
    plan_mixed = plan_token_address("ethereum", USDC)
    plan_lower = plan_token_address("ethereum", USDC_LOWER)
    state, reason, canonical, _checksum = validate_address_for_chain("ethereum", USDC)
    assert plan_mixed.payload.token_address is not None
    assert plan_mixed.payload.token_address.address == canonical == USDC_LOWER
    assert plan_lower.payload.token_address.address == USDC_LOWER
    assert plan_mixed.payload.token_address.validation_state is state
    assert plan_mixed.payload.token_address.validation_reason == reason
    assert plan_mixed.payload.token_address.validation_state is IdentityState.UNRESOLVED
    assert plan_mixed.status is ResolutionPlanStatus.READY_FOR_RESOLUTION
    _assert_not_canonical_plan(plan_mixed)
    bad = plan_token_address("ethereum", "0xnotanaddress")
    evm_state, evm_reason, *_ = validate_address_for_chain("ethereum", "0xnotanaddress")
    assert bad.payload.token_address.validation_state is evm_state is IdentityState.INVALID
    assert bad.payload.token_address.validation_reason == evm_reason
    assert bad.status is ResolutionPlanStatus.INVALID
    _assert_not_canonical_plan(bad)


def test_missing_base_token_does_not_infer_token_from_pool_address():
    item = {
        "id": f"solana_{POOL}",
        "type": "pool",
        "attributes": {"address": POOL, "name": "SOL / USDC"},
        "relationships": {},
    }
    plan = plan_gecko_new_pool(item, network_chain="solana")
    assert plan.payload.pool_address is not None
    assert plan.payload.pool_address.address == POOL
    assert isinstance(plan.payload.pool_address, PoolAddress)
    assert plan.payload.token_address is None
    assert _token_candidates(plan) == []
    assert any(c.subject_kind is ResolutionSubjectKind.POOL for c in plan.candidates)
    assert plan.status in {
        ResolutionPlanStatus.UNRESOLVED,
        ResolutionPlanStatus.MISSING,
    }
    assert plan.existing_canonical is False
    _assert_not_canonical_plan(plan)


def test_gecko_with_base_token_keeps_pool_and_token_distinct():
    item = {
        "id": f"solana_{POOL}",
        "type": "pool",
        "attributes": {"address": POOL, "name": "SOL / USDC"},
        "relationships": {
            "base_token": {"data": {"id": f"solana_{SOL}", "type": "token"}},
            "quote_token": {"data": {"id": f"solana_{SOL_USDC}", "type": "token"}},
        },
    }
    plan = plan_gecko_new_pool(item)
    tokens = _token_candidates(plan)
    assert len(tokens) == 1
    assert tokens[0].token_address.address == SOL
    assert plan.payload.pool_address.address == POOL
    assert plan.payload.pool_address.address != tokens[0].token_address.address
    quote_ev = [e for e in plan.evidence if e.kind is EvidenceKind.POOL_QUOTE_TOKEN]
    assert quote_ev
    assert plan.status is ResolutionPlanStatus.READY_FOR_RESOLUTION
    _assert_not_canonical_plan(plan)


def test_provider_disagreement_remains_conflict():
    plan = plan_provider_disagreement(
        "solana",
        {"geckoterminal": SOL, "dexscreener": SOL_USDC},
    )
    tokens = _token_candidates(plan)
    assert len({c.token_address.address for c in tokens}) == 2
    assert plan.status is ResolutionPlanStatus.CONFLICT
    assert plan.requirements.no_provider_disagreement is False
    assert plan.requirements.ready is False
    assert any(e.kind is EvidenceKind.PROVIDER_DISAGREEMENT for e in plan.evidence)
    assert "winner" not in " ".join(plan.reasons)
    assert plan.existing_canonical is False
    _assert_not_canonical_plan(plan)


def test_provider_disagreement_does_not_pick_newer_or_first():
    a = plan_provider_disagreement("solana", {"a": SOL, "b": SOL_USDC})
    b = plan_provider_disagreement("solana", {"b": SOL_USDC, "a": SOL})
    assert a.status is b.status is ResolutionPlanStatus.CONFLICT
    assert {c.token_address.address for c in _token_candidates(a)} == {
        SOL,
        SOL_USDC,
    }


def test_historical_mapping_remains_explicit_and_append_only():
    original = compose_resolution_input(
        chain="solana",
        token_addr=token_address("solana", SOL),
        original_value=SOL,
        operational_value=SOL,
    )
    rel = identity_relationship(
        RelationshipKind.MIGRATES_TO,
        {"entity": "OLD_ENTITY", "address": SOL},
        {"entity": "NEW_ENTITY", "address": SOL_USDC},
        note="explicit_migration",
    )
    plan = plan_historical_mapping(rel, original=original)
    assert original.original_value == SOL
    assert original.relationships == ()
    assert original.token_address.address == SOL
    assert plan.payload.original_value == SOL
    assert plan.payload.token_address.address == SOL
    assert rel in plan.payload.relationships
    assert any(e.kind is EvidenceKind.HISTORICAL_MAPPING for e in plan.evidence)
    assert relationship_is_authority(rel) is False
    assert plan.payload.as_dict()["is_canonical"] is False
    _assert_not_canonical_plan(plan)
    with pytest.raises(Exception):
        original.original_value = "mutated"  # type: ignore[misc]


def test_relationship_does_not_create_authority():
    rel = identity_relationship(
        RelationshipKind.IDENTITY,
        {"token_id": "forged"},
        {"token_id": "also_forged"},
    )
    plan = plan_historical_mapping(rel)
    assert relationship_is_authority(rel) is False
    assert rel.as_dict()["grants_canonical_identity"] is False
    assert plan.requirements.relationship_alone_insufficient is True
    assert plan.status in {
        ResolutionPlanStatus.UNRESOLVED,
        ResolutionPlanStatus.AMBIGUOUS,
        ResolutionPlanStatus.MISSING,
    }
    assert plan.existing_canonical is False
    _assert_not_canonical_plan(plan)


def test_identity_resolution_is_only_authoritative_canonical_source():
    verified = verified_identity_fixture(token_id="abc123canonicalid")
    assert authoritative_canonical(verified) is True
    assert is_canonical_verified(verified) is True
    copied = copy_canonical_if_authoritative(verified)
    assert isinstance(copied, CanonicalTokenId)
    assert copied.value == "abc123canonicalid"
    payload = compose_resolution_input(token_addr=token_address("solana", SOL))
    plan = plan_resolution(payload, existing_resolution=verified)
    assert plan.existing_canonical is True
    assert plan.status is ResolutionPlanStatus.READY_FOR_RESOLUTION
    _assert_not_canonical_plan(plan)


def test_non_verified_resolution_never_becomes_canonical():
    unresolved = _unverified(token_id="looks_like_a_hash")
    assert authoritative_canonical(unresolved) is False
    assert copy_canonical_if_authoritative(unresolved) is None
    payload = compose_resolution_input(token_addr=token_address("solana", SOL))
    plan = plan_resolution(payload, existing_resolution=unresolved)
    assert plan.existing_canonical is False
    _assert_not_canonical_plan(plan)


def test_verified_classification_requires_existing_authoritative_object():
    verified = verified_identity_fixture()
    assert authoritative_canonical(verified) is True
    assert authoritative_canonical(verified.token) is False
    assert authoritative_canonical({"state": "VERIFIED", "token_id": "x"}) is False
    assert authoritative_canonical(None) is False
    class Fake:
        token = type(
            "T",
            (),
            {"state": IdentityState.VERIFIED, "token_id": "x", "address_canonical": SOL},
        )()
    assert authoritative_canonical(Fake()) is False
    payload = compose_resolution_input(token_addr=token_address("solana", SOL))
    plan = plan_resolution(payload, existing_resolution=Fake())
    assert plan.existing_canonical is False
    _assert_not_canonical_plan(plan)


def test_arbitrary_canonical_token_id_does_not_grant_verified_authority():
    forged = CanonicalTokenId(value="deadbeefcafebabe", resolution_version="v9")
    assert authoritative_canonical(forged) is False
    assert copy_canonical_if_authoritative(forged) is None
    assert is_canonical_verified(forged) is False
    ns = TokenIdNamespace(value="deadbeefcafebabe")
    assert authoritative_canonical(ns) is False
    payload = compose_resolution_input(token_addr=token_address("solana", SOL))
    plan = plan_resolution(payload, existing_resolution=forged)
    assert plan.existing_canonical is False
    _assert_not_canonical_plan(plan)


def test_no_outcome_silently_promotes_to_verified():
    plans = [
        plan_token_address("solana", SOL),
        plan_pool_address("solana", POOL),
        plan_provider_resource("gecko", "solana_x"),
        plan_symbol("PEPE"),
        plan_fallback("manual:PEPE"),
        plan_token_address("solana", "!!!"),
        plan_token_address("aptos", SOL),
        plan_provider_disagreement("solana", {"a": SOL, "b": SOL_USDC}),
        plan_gecko_new_pool(None),
        plan_resolution(
            compose_resolution_input(token_addr=token_address("solana", SOL)),
            existing_resolution=verified_identity_fixture(),
        ),
        plan_resolution(
            compose_resolution_input(token_addr=token_address("solana", SOL)),
            stale=True,
        ),
    ]
    for plan in plans:
        _assert_not_canonical_plan(plan)
        assert plan_promotes_to_verified(plan) is False


def test_malformed_inputs_fail_closed():
    plans = [
        plan_token_address(None, None),
        plan_token_address("", ""),
        plan_token_address({"chain": "solana"}, 123),
        plan_token_address("solana", "not-a-mint!!!"),
        plan_pool_address(None, None),
        plan_symbol(""),
        plan_symbol(None),
        plan_fallback(None),
        plan_fallback(""),
        plan_gecko_new_pool("not-a-mapping"),
        plan_gecko_new_pool(None),
        plan_provider_resource(None, None),
    ]
    for plan in plans:
        assert plan.status in {
            ResolutionPlanStatus.INVALID,
            ResolutionPlanStatus.MISSING,
            ResolutionPlanStatus.UNRESOLVED,
            ResolutionPlanStatus.AMBIGUOUS,
            ResolutionPlanStatus.UNSUPPORTED,
        }
        assert plan.status is not ResolutionPlanStatus.READY_FOR_RESOLUTION
        _assert_not_canonical_plan(plan)


def test_unsupported_chains_fail_closed():
    for chain in ("aptos", "sol", "bitcoin", "tron"):
        plan = plan_token_address(chain, SOL)
        assert plan.status is ResolutionPlanStatus.UNSUPPORTED
        assert plan.requirements.chain_supported is False
        assert plan.requirements.ready is False
        _assert_not_canonical_plan(plan)


def test_pool_token_provider_types_remain_distinct():
    token_plan = plan_token_address("solana", SOL)
    pool_plan = plan_pool_address("solana", POOL)
    provider_plan = plan_provider_resource("geckoterminal", f"solana_{POOL}")
    assert token_plan.candidates[0].subject_kind is ResolutionSubjectKind.TOKEN
    assert pool_plan.candidates[0].subject_kind is ResolutionSubjectKind.POOL
    assert provider_plan.candidates[0].subject_kind is ResolutionSubjectKind.PROVIDER_RESOURCE
    assert type(token_plan.payload.token_address) is TokenAddress
    assert type(pool_plan.payload.pool_address) is PoolAddress
    assert type(provider_plan.payload.provider_ref) is ProviderResourceRef
    assert token_plan.payload.token_address != pool_plan.payload.pool_address
    assert _token_candidates(pool_plan) == []
    assert _token_candidates(provider_plan) == []


def test_adversarial_inputs_cannot_become_canonical_authority():
    forged_id = CanonicalTokenId(value="forged-token-id")
    forged_addr = TokenAddress(
        chain="solana",
        address=SOL,
        address_input=SOL,
        validation_state=IdentityState.VERIFIED,
        validation_reason="forged",
    )
    fake_rel = identity_relationship(
        "TOTALLY_CANONICAL",
        {"canonical_token_id": "forged"},
        {"canonical_token_id": "winner"},
    )
    fake_hist = identity_relationship(
        RelationshipKind.SUPERSEDED,
        {"old": POOL, "note": "rewrite_history"},
        {"new": SOL, "state": "VERIFIED"},
    )
    payloads = [
        compose_resolution_input(original_value="arbitrary-string"),
        compose_resolution_input(token_addr=forged_addr),
        compose_resolution_input(pool_addr=pool_address("solana", POOL)),
        compose_resolution_input(
            provider_ref=provider_resource_ref("gecko", f"solana_{POOL}", "pool")
        ),
        compose_resolution_input(
            representation_kind=RepresentationKind.SYMBOL,
            symbol="PEPE",
            original_value="PEPE",
        ),
        compose_resolution_input(
            token_addr=token_address("solana", SOL.lower()),
        ),
        compose_resolution_input(chain="???", original_value=SOL),
        compose_resolution_input(chain="aptos", token_addr=token_address("aptos", SOL)),
        compose_resolution_input(relationships=(fake_rel,)),
        compose_resolution_input(
            token_addr=token_address("solana", SOL),
            relationships=(fake_hist,),
        ),
        compose_resolution_input(
            representation_kind=RepresentationKind.FALLBACK,
            original_value="manual:PEPE",
            fallback_kind=FallbackKind.MANUAL_SYMBOL,
        ),
    ]
    extras = [
        None,
        forged_id,
        _unverified(),
        TokenIdNamespace(value="abc"),
        {"state": "VERIFIED", "token_id": "x"},
    ]
    for payload in payloads:
        for existing in extras:
            plan = plan_resolution(payload, existing_resolution=existing)
            _assert_not_canonical_plan(plan)
            if not isinstance(existing, IdentityResolution) or existing.token.state is not IdentityState.VERIFIED:
                assert plan.existing_canonical is False
    disagree = plan_provider_disagreement("solana", {"a": SOL, "b": POOL})
    _assert_not_canonical_plan(disagree)
    assert disagree.status is ResolutionPlanStatus.CONFLICT
    missing_base = plan_gecko_new_pool(
        {"id": "solana_x", "attributes": {"address": POOL}},
        network_chain="solana",
    )
    assert missing_base.payload.token_address is None
    _assert_not_canonical_plan(missing_base)
    hist = plan_historical_mapping(fake_hist)
    assert relationship_is_authority(fake_hist) is False
    _assert_not_canonical_plan(hist)


def test_forged_verified_token_address_is_not_usable():
    forged = TokenAddress(
        chain="solana",
        address=SOL,
        address_input=SOL,
        validation_state=IdentityState.VERIFIED,
        validation_reason="forged",
    )
    plan = plan_resolution(compose_resolution_input(token_addr=forged))
    assert plan.requirements.address_usable is False
    assert plan.requirements.ready is False
    assert plan.status is not ResolutionPlanStatus.READY_FOR_RESOLUTION
    _assert_not_canonical_plan(plan)


def test_evidence_never_produces_verified():
    ev = resolution_evidence("NOT_A_KIND", {"state": "VERIFIED"}, source="human")
    assert ev.kind is EvidenceKind.ALIAS
    assert ev.as_dict()["produces_verified"] is False
    ev2 = resolution_evidence(EvidenceKind.USER_MAPPING, {"token_id": "abc"})
    assert ev2.as_dict()["produces_verified"] is False
    assert authoritative_canonical(ev2) is False


def test_stale_plan_does_not_become_verified():
    payload = compose_resolution_input(token_addr=token_address("solana", SOL))
    plan = plan_resolution(
        payload,
        existing_resolution=verified_identity_fixture(),
        stale=True,
    )
    assert plan.status is ResolutionPlanStatus.STALE
    assert plan.existing_canonical is True
    _assert_not_canonical_plan(plan)


def test_resolution_input_is_never_canonical():
    payload = compose_resolution_input(
        chain="solana",
        token_addr=token_address("solana", SOL),
        symbol="SOL",
        name="Wrapped SOL",
    )
    assert payload.as_dict()["is_canonical"] is False
    assert authoritative_canonical(payload) is False


def test_equivalent_plans_are_deterministic():
    a = plan_token_address("solana", SOL)
    b = plan_token_address("solana", SOL)
    assert a.status == b.status
    assert a.as_dict()["candidates"] == b.as_dict()["candidates"]
    assert a.as_dict()["requirements"] == b.as_dict()["requirements"]
