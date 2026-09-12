"""W4 Slice 6 — security identity consumer: canonical attachment boundary."""
from __future__ import annotations

from architecture.identity.fusion import (
    CanonicalTokenId,
    RepresentationKind,
    TokenAddress,
    identity_observation,
    pool_address,
    provider_resource_ref,
    token_address,
)
from architecture.identity.join import JoinClass, classify_canonical_join
from architecture.identity.types import IdentityResolution, IdentityState, TokenIdentity
from architecture.providers.contracts import (
    MarketMetrics,
    NormalizedTokenCandidate,
    SecuritySignals,
)
from architecture.security.gate import (
    SecurityState,
    evaluate_security,
    evaluate_security_from_candidate,
    security_allows_positive_eligibility,
)
from architecture.security.identity_join import (
    SecurityAttachmentOutcome,
    SecuritySubjectKind,
    attach_security_identity,
    goplus_query_may_attach_as_token_security,
    legacy_security_row_is_canonical,
    overlay_attachment_for_item,
    overlay_key_is_canonical_authority,
    rugcheck_query_may_attach_as_token_security,
    security_canonical_token_id,
)
from architecture.security.overlay_query import attachment_for_overlay_item, run
from tests.helpers_identity import verified_identity_fixture
from tests.helpers_security import OLD_POOL_TS, passing_security_signals

SOL = "So11111111111111111111111111111111111111112"
SOL_USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
POOL = "58oQChx4yWmvKdwLLZzBi4ChoCc2fqCUWBkwMihLYQo2"
NOW = 1_800_000_000.0


def _candidate(address: str = SOL, symbol: str = "TEST", security=None, **over):
    return NormalizedTokenCandidate(
        chain=over.get("chain", "solana"),
        address=address,
        symbol=symbol,
        name=over.get("name", "Test Token"),
        source_provider=over.get("source_provider", "dexscreener"),
        retrieved_ts=over.get("retrieved_ts", NOW),
        pair_created_ts=over.get("pair_created_ts", OLD_POOL_TS),
        metrics=over.get(
            "metrics",
            MarketMetrics(price_usd=0.1, liquidity_usd=80_000, volume_1h=40_000),
        ),
        security=security if security is not None else passing_security_signals(),
    )


def _with_state(ident: IdentityResolution, state: IdentityState, **kwargs) -> IdentityResolution:
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


def _attach(identity=None, subject_kind="TOKEN", **kwargs):
    return attach_security_identity(identity, subject_kind=subject_kind, **kwargs)


# --- 1. Legitimate VERIFIED permits canonical attachment ---

def test_verified_resolution_permits_canonical_security_attachment():
    verified = verified_identity_fixture(token_id="sec-canon-1", address=SOL)
    assert classify_canonical_join(verified).classification is JoinClass.CANONICAL_JOIN
    att = _attach(verified)
    assert att.outcome == SecurityAttachmentOutcome.CANONICAL.value
    assert att.is_canonical
    assert att.canonical_token_id == "sec-canon-1"
    assert att.observed_address == SOL
    assert att.observed_chain == "solana"
    assert att.subject_kind == SecuritySubjectKind.TOKEN.value
    overlay = evaluate_security_from_candidate(
        _candidate(address=SOL), now=NOW, identity=verified, subject_kind="TOKEN",
    )
    assert overlay.state == SecurityState.PASS
    assert overlay.canonical_token_id == "sec-canon-1"
    assert overlay.identity_attachment == "CANONICAL"
    assert overlay.observed_address == SOL


# --- 2–8. Noncanonical identity states stay unlinked/rejected ---

def test_unresolved_identity_is_unlinked():
    att = _attach(_with_state(verified_identity_fixture(), IdentityState.UNRESOLVED))
    assert att.canonical_token_id is None
    assert att.outcome == SecurityAttachmentOutcome.UNLINKED.value
    assert att.join_class != JoinClass.CANONICAL_JOIN.value


def test_conflict_identity_is_unlinked():
    att = _attach(_with_state(verified_identity_fixture(), IdentityState.CONFLICT))
    assert att.canonical_token_id is None
    assert att.outcome == SecurityAttachmentOutcome.UNLINKED.value


def test_invalid_identity_is_rejected():
    att = _attach(_with_state(verified_identity_fixture(), IdentityState.INVALID))
    assert att.canonical_token_id is None
    assert att.outcome == SecurityAttachmentOutcome.REJECTED.value


def test_stale_identity_is_unlinked():
    att = _attach(_with_state(verified_identity_fixture(), IdentityState.STALE))
    assert att.canonical_token_id is None
    assert att.outcome == SecurityAttachmentOutcome.UNLINKED.value


def test_unsupported_identity_is_rejected():
    att = _attach(_with_state(verified_identity_fixture(), IdentityState.UNSUPPORTED))
    assert att.canonical_token_id is None
    assert att.outcome == SecurityAttachmentOutcome.REJECTED.value


def test_missing_identity_is_unlinked():
    att = _attach(None)
    assert att.canonical_token_id is None
    assert att.outcome == SecurityAttachmentOutcome.UNLINKED.value
    assert security_canonical_token_id(None) is None
    overlay = evaluate_security_from_candidate(_candidate(), now=NOW)
    assert overlay.canonical_token_id is None
    assert overlay.identity_attachment != "CANONICAL"


def test_ambiguous_identity_is_rejected_or_unlinked():
    att = attach_security_identity(
        verified_identity_fixture(), subject_kind=None,
    )
    assert att.canonical_token_id is None
    assert att.outcome == SecurityAttachmentOutcome.REJECTED.value
    assert att.reason == "missing_subject_kind"
    unknown = _attach(verified_identity_fixture(), subject_kind="AMBIGUOUS")
    assert unknown.canonical_token_id is None
    assert unknown.outcome == SecurityAttachmentOutcome.REJECTED.value


# --- 9–10. Symbol / name cannot attach ---

def test_symbol_only_security_cannot_attach_canonically():
    att = _attach("PEPE")
    assert att.canonical_token_id is None
    assert att.outcome != SecurityAttachmentOutcome.CANONICAL.value
    obs = identity_observation(
        representation_kind=RepresentationKind.SYMBOL, original_value="PEPE",
    )
    assert _attach(obs).canonical_token_id is None


def test_name_only_security_cannot_attach_canonically():
    obs = identity_observation(
        representation_kind=RepresentationKind.NAME, original_value="Pepe Token",
    )
    att = _attach(obs)
    assert att.canonical_token_id is None
    assert att.outcome != SecurityAttachmentOutcome.CANONICAL.value


# --- 11–13. Forged / arbitrary identifiers ---

def test_arbitrary_token_id_cannot_prove_canonical_identity():
    assert security_canonical_token_id("deadbeefcafebabe") is None
    att = _attach("deadbeefcafebabe")
    assert att.canonical_token_id is None


def test_forged_canonical_token_id_cannot_prove_canonical_identity():
    forged = CanonicalTokenId(value="forged", resolution_version="v9")
    assert security_canonical_token_id(forged) is None
    assert _attach(forged).canonical_token_id is None


def test_forged_verified_token_address_cannot_prove_canonical_identity():
    forged = TokenAddress(
        chain="solana",
        address=SOL,
        address_input=SOL,
        validation_state=IdentityState.VERIFIED,
        validation_reason="forged",
    )
    assert classify_canonical_join(forged).classification is not JoinClass.CANONICAL_JOIN
    assert _attach(forged).canonical_token_id is None


# --- 14–16. Pool / provider / fallback ---

def test_pool_address_cannot_attach_token_security():
    att = _attach(pool_address("solana", POOL))
    assert att.canonical_token_id is None
    assert att.join_class == JoinClass.POOL_REFERENCE.value
    overlay = evaluate_security_from_candidate(
        _candidate(address=POOL), now=NOW,
        identity=pool_address("solana", POOL), subject_kind="TOKEN",
    )
    assert overlay.canonical_token_id is None
    assert overlay.identity_attachment != "CANONICAL"


def test_provider_resource_id_cannot_attach_token_security():
    ref = provider_resource_ref("geckoterminal", f"solana_{POOL}", "pool")
    att = _attach(ref)
    assert att.canonical_token_id is None
    assert att.join_class == JoinClass.PROVIDER_REFERENCE.value


def test_fallback_identifier_cannot_attach_token_security():
    att = _attach("solana:sym:PEPE")
    assert att.canonical_token_id is None
    assert att.outcome != SecurityAttachmentOutcome.CANONICAL.value


# --- 17–18. Solana case ---

def test_lowercased_solana_address_cannot_attach_canonical_security():
    folded = token_address("solana", SOL.lower())
    att = _attach(folded, observed_address=SOL.lower())
    assert att.canonical_token_id is None
    assert att.observed_address != SOL or att.canonical_token_id is None
    overlay = evaluate_security_from_candidate(
        _candidate(address=SOL.lower()), now=NOW,
        identity=folded, subject_kind="TOKEN",
    )
    assert overlay.canonical_token_id is None


def test_exact_solana_mint_identity_remains_case_preserving():
    verified = verified_identity_fixture(address=SOL, token_id="sol-canon")
    att = _attach(verified, observed_address=SOL.lower())
    assert att.is_canonical
    assert att.observed_address == SOL
    assert att.observed_address != SOL.lower()
    overlay = evaluate_security_from_candidate(
        _candidate(address=SOL.lower()), now=NOW,
        identity=verified, subject_kind="TOKEN",
    )
    assert overlay.canonical_token_id == "sol-canon"
    assert overlay.observed_address == SOL


# --- 19–21. Subject separation ---

def test_deployer_security_remains_deployer_scoped():
    verified = verified_identity_fixture(token_id="should-not-leak")
    att = _attach(verified, subject_kind="DEPLOYER", observed_address="Deployer111")
    assert att.outcome == SecurityAttachmentOutcome.SUBJECT_SCOPED.value
    assert att.canonical_token_id is None
    assert att.subject_kind == "DEPLOYER"
    assert att.observed_address == "Deployer111"


def test_holder_security_remains_holder_scoped():
    verified = verified_identity_fixture(token_id="should-not-leak")
    att = _attach(verified, subject_kind="HOLDER", observed_address="Holder111")
    assert att.outcome == SecurityAttachmentOutcome.SUBJECT_SCOPED.value
    assert att.canonical_token_id is None
    assert att.subject_kind == "HOLDER"


def test_pool_security_remains_pool_scoped():
    verified = verified_identity_fixture(token_id="should-not-leak")
    att = _attach(
        verified, subject_kind="POOL",
        observed_chain="solana", observed_address=POOL,
    )
    assert att.outcome == SecurityAttachmentOutcome.SUBJECT_SCOPED.value
    assert att.canonical_token_id is None
    assert att.subject_kind == "POOL"
    assert att.observed_address == POOL


# --- 22. Historical records are not rewritten ---

def test_historical_security_records_are_not_rewritten():
    row = {
        "token_id": "legacy-token-id",
        "token_key": "solana:legacy",
        "state": "PASS",
    }
    snapshot = dict(row)
    att = _attach("PEPE")
    assert att.canonical_token_id is None
    assert row == snapshot
    assert legacy_security_row_is_canonical(row) is False
    assert legacy_security_row_is_canonical(row, identity="PEPE") is False


# --- 23. Missing / ambiguous subject kind fails closed ---

def test_missing_ambiguous_subject_kind_fails_closed():
    verified = verified_identity_fixture(token_id="gated")
    assert attach_security_identity(verified, subject_kind=None).canonical_token_id is None
    assert attach_security_identity(verified, subject_kind="").canonical_token_id is None
    assert attach_security_identity(verified, subject_kind="  ").canonical_token_id is None
    overlay = evaluate_security_from_candidate(
        _candidate(), now=NOW, identity=verified,
    )
    assert overlay.canonical_token_id is None
    assert overlay.identity_attachment == "REJECTED"
    assert overlay.attachment_reason == "missing_subject_kind"


# --- 24. Security veto / fail-closed unchanged ---

def test_security_veto_fail_closed_behavior_unchanged():
    honey = _candidate(security=passing_security_signals(is_honeypot=True))
    verified = verified_identity_fixture(token_id="veto-canon")
    bare = evaluate_security_from_candidate(honey, now=NOW)
    linked = evaluate_security_from_candidate(
        honey, now=NOW, identity=verified, subject_kind="TOKEN",
    )
    assert bare.state == SecurityState.REJECT
    assert linked.state == SecurityState.REJECT
    assert bare.to_dict()["state"] == linked.to_dict()["state"]
    assert bare.to_dict()["veto_reasons"] == linked.to_dict()["veto_reasons"]
    assert not security_allows_positive_eligibility(bare)
    assert not security_allows_positive_eligibility(linked)
    assert linked.canonical_token_id == "veto-canon"
    missing = evaluate_security(None, now=NOW)
    assert missing.state == SecurityState.INCOMPLETE
    assert not security_allows_positive_eligibility(missing)


# --- 25. Legacy noncanonical rows do not become canonical ---

def test_legacy_noncanonical_security_rows_do_not_become_canonical():
    row = {"token_id": SOL, "token_key": f"solana:{SOL.lower()}", "symbol": "SOL"}
    assert overlay_key_is_canonical_authority(row["token_key"]) is False
    assert legacy_security_row_is_canonical(row) is False
    att = overlay_attachment_for_item(row, identity=row["token_id"], subject_kind="TOKEN")
    assert att.canonical_token_id is None
    verified = verified_identity_fixture(token_id="live-only")
    assert legacy_security_row_is_canonical(row, identity=verified) is True
    assert row["token_id"] == SOL
    assert row["token_id"] != "live-only"


# --- Provider subject safety ---

def test_goplus_subject_is_not_implicitly_a_token():
    verified = verified_identity_fixture(token_id="gplus")
    assert goplus_query_may_attach_as_token_security(
        subject_kind="TOKEN", identity=verified, queried_address=SOL,
    )
    assert goplus_query_may_attach_as_token_security(
        subject_kind="DEPLOYER", identity=verified, queried_address=SOL,
    ) is False
    assert goplus_query_may_attach_as_token_security(
        subject_kind="TOKEN", identity=None, queried_address=SOL,
    ) is False
    assert goplus_query_may_attach_as_token_security(
        subject_kind="TOKEN", identity="0xabc", queried_chain="ethereum",
    ) is False


def test_rugcheck_subject_is_not_implicitly_a_mint():
    verified = verified_identity_fixture(address=SOL, token_id="rug-canon")
    assert rugcheck_query_may_attach_as_token_security(
        subject_kind="TOKEN", identity=verified, queried_address=SOL,
    )
    assert rugcheck_query_may_attach_as_token_security(
        subject_kind="TOKEN", identity=verified, queried_address=SOL.lower(),
    ) is False
    assert rugcheck_query_may_attach_as_token_security(
        subject_kind="TOKEN", identity=verified, queried_address=POOL,
    ) is False
    assert rugcheck_query_may_attach_as_token_security(
        subject_kind="POOL", identity=verified, queried_address=SOL,
    ) is False
    assert rugcheck_query_may_attach_as_token_security(
        subject_kind="HOLDER", identity=verified, queried_address=SOL,
    ) is False


# --- Overlay query operational keys ---

def test_overlay_token_key_is_not_canonical_authority():
    states = run({"tokens": [{"tokenKey": "solana:x", "signals": {}}]}, now=NOW)
    assert states["solana:x"] == "INCOMPLETE"
    assert overlay_key_is_canonical_authority("solana:x") is False
    att = attachment_for_overlay_item(
        {"tokenKey": "solana:x", "token_id": "looks-canonical"},
        subject_kind="TOKEN",
    )
    assert att.canonical_token_id is None


# --- Adversarial compositions + isolation ---

def test_adversarial_compositions_cannot_canonicalize_security():
    forged_addr = TokenAddress(
        chain="solana",
        address=SOL,
        address_input=SOL,
        validation_state=IdentityState.VERIFIED,
        validation_reason="forged",
    )
    cases = [
        ("PEPE", "TOKEN"),
        (CanonicalTokenId(value="forged"), "TOKEN"),
        (pool_address("solana", POOL), "TOKEN"),
        (provider_resource_ref("gecko", f"solana_{POOL}"), "TOKEN"),
        (token_address("solana", SOL.lower()), "TOKEN"),
        (verified_identity_fixture(token_id="leak"), "POOL"),
        (verified_identity_fixture(token_id="leak"), "DEPLOYER"),
        (verified_identity_fixture(token_id="leak"), None),
        ("deadbeef", "TOKEN"),
        (identity_observation(
            representation_kind=RepresentationKind.NAME, original_value="Solana",
        ), "TOKEN"),
    ]
    for identity, kind in cases:
        att = attach_security_identity(identity, subject_kind=kind)
        assert att.canonical_token_id is None
        assert att.outcome != SecurityAttachmentOutcome.CANONICAL.value


def test_evaluate_security_veto_json_contract_unchanged():
    sec = passing_security_signals()
    overlay = evaluate_security(sec, now=NOW, pair_created_ts=OLD_POOL_TS, retrieved_ts=NOW)
    assert set(overlay.to_dict()) == {
        "state", "reason", "lane_a_verdict", "veto_reasons",
        "unknown_critical", "coverage", "policy_version", "computed_ts", "extras",
    }
    assert overlay.state == SecurityState.PASS
    assert overlay.canonical_token_id is None


def test_canonical_attachment_preserves_provenance_and_does_not_rewrite_observation():
    verified = verified_identity_fixture(token_id="prov-1", address=SOL)
    cand = _candidate(address=SOL, source_provider="goplus")
    overlay = evaluate_security_from_candidate(
        cand, now=NOW, identity=verified, subject_kind="TOKEN",
        source_provider="goplus",
    )
    assert overlay.canonical_token_id == "prov-1"
    assert overlay.observed_chain == "solana"
    assert overlay.observed_address == SOL
    assert overlay.subject_kind == "TOKEN"
    assert cand.address == SOL
    assert cand.source_provider == "goplus"


def test_usdc_and_sol_remain_distinct_under_symbol_collision():
    a = _attach("USDC")
    b = _attach("USDC")
    assert a.canonical_token_id is None and b.canonical_token_id is None
    sol = verified_identity_fixture(address=SOL, token_id="sol-id", symbol="USDC")
    usdc = verified_identity_fixture(address=SOL_USDC, token_id="usdc-id", symbol="USDC")
    assert _attach(sol).canonical_token_id == "sol-id"
    assert _attach(usdc).canonical_token_id == "usdc-id"
    assert _attach(sol).observed_address != _attach(usdc).observed_address
