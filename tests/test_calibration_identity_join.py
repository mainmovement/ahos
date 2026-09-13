"""W4 Slice 7 — calibration identity pairing boundary."""
from __future__ import annotations

import sqlite3
import time

import pytest

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
from architecture.learning.calibration import (
    MIN_N_PER_BAND,
    MIN_POSITIVES,
    SCORE_BANDS,
    CalibrationHarness,
    _brier,
    _spearman,
)
from architecture.learning.calibration_identity_join import (
    PAIR_PAIRED,
    PAIR_REJECTED,
    PAIR_UNMATCHED,
    pair_calibration_identities,
)
from architecture.learning.score_ledger import SOURCE_TEST, ScoreLedger
from tests.helpers_identity import calibration_identity_maps, verified_identity_fixture

SOL = "So11111111111111111111111111111111111111112"
SOL_USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
POOL = "58oQChx4yWmvKdwLLZzBi4ChoCc2fqCUWBkwMihLYQo2"
ETH_USDC = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"


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


def _pair(pred=None, outcome=None, subject_kind="TOKEN"):
    return pair_calibration_identities(pred, outcome, subject_kind=subject_kind)


def _verified(token_id="cal-canon", address=SOL, chain="solana"):
    return verified_identity_fixture(token_id=token_id, address=address, chain=chain)


# --- 1. Same legitimate VERIFIED identity pairs ---

def test_same_verified_canonical_identity_pairs():
    ident = _verified("same-id")
    assert classify_canonical_join(ident).classification is JoinClass.CANONICAL_JOIN
    decision = _pair(ident, ident)
    assert decision.permits_pair
    assert decision.outcome == PAIR_PAIRED
    assert decision.canonical_token_id == "same-id"
    assert decision.observed_address == SOL
    assert decision.observed_chain == "solana"


# --- 2. One-sided remains unmatched ---

def test_one_sided_canonical_identity_is_unmatched():
    ident = _verified()
    assert _pair(ident, None).outcome == PAIR_UNMATCHED
    assert _pair(None, ident).outcome == PAIR_UNMATCHED
    assert _pair(ident, None).canonical_token_id is None


# --- 3–8. Noncanonical states ---

def test_both_sides_unresolved_remain_unmatched():
    left = _with_state(_verified(), IdentityState.UNRESOLVED)
    right = _with_state(_verified(), IdentityState.UNRESOLVED)
    assert _pair(left, right).outcome == PAIR_UNMATCHED
    assert _pair(left, right).canonical_token_id is None


def test_conflict_remains_unmatched():
    ident = _with_state(_verified(), IdentityState.CONFLICT)
    assert _pair(ident, ident).outcome == PAIR_UNMATCHED


def test_invalid_remains_unmatched_or_rejected():
    ident = _with_state(_verified(), IdentityState.INVALID)
    decision = _pair(ident, ident)
    assert decision.canonical_token_id is None
    assert decision.outcome in {PAIR_UNMATCHED, PAIR_REJECTED}


def test_stale_remains_unmatched():
    ident = _with_state(_verified(), IdentityState.STALE)
    assert _pair(ident, ident).outcome == PAIR_UNMATCHED


def test_unsupported_remains_unmatched_or_rejected():
    ident = _with_state(_verified(), IdentityState.UNSUPPORTED)
    decision = _pair(ident, ident)
    assert decision.canonical_token_id is None
    assert decision.outcome in {PAIR_UNMATCHED, PAIR_REJECTED}


def test_missing_identity_remains_unmatched():
    decision = _pair(None, None)
    assert decision.outcome == PAIR_UNMATCHED
    assert decision.reason == "missing_identity"


def test_ambiguous_identity_remains_unmatched():
    ident = _verified()
    assert _pair([ident, ident], ident).outcome == PAIR_UNMATCHED
    assert _pair(ident, ident, subject_kind=None).outcome == PAIR_REJECTED
    assert _pair(ident, ident, subject_kind="AMBIGUOUS").outcome == PAIR_REJECTED


# --- 9–12. Symbol / name / raw token_id / forged wrappers ---

def test_symbol_only_matching_is_blocked():
    assert _pair("PEPE", "PEPE").permits_pair is False
    obs = identity_observation(
        representation_kind=RepresentationKind.SYMBOL, original_value="PEPE",
    )
    assert _pair(obs, obs).permits_pair is False


def test_name_only_matching_is_blocked():
    obs = identity_observation(
        representation_kind=RepresentationKind.NAME, original_value="Pepe Token",
    )
    assert _pair(obs, obs).permits_pair is False


def test_raw_token_id_equality_without_resolution_is_blocked():
    assert _pair("deadbeefcafebabe", "deadbeefcafebabe").permits_pair is False


def test_forged_canonical_token_id_is_blocked():
    forged = CanonicalTokenId(value="forged", resolution_version="v9")
    assert _pair(forged, forged).permits_pair is False


def test_forged_verified_token_address_is_blocked():
    forged = TokenAddress(
        chain="solana",
        address=SOL,
        address_input=SOL,
        validation_state=IdentityState.VERIFIED,
        validation_reason="forged",
    )
    assert classify_canonical_join(forged).classification is not JoinClass.CANONICAL_JOIN
    assert _pair(forged, forged).permits_pair is False


# --- 15–18. Pool / provider / fallback / operational ---

def test_pool_address_cannot_pair_with_token():
    pool = pool_address("solana", POOL)
    token = _verified()
    assert _pair(pool, token).permits_pair is False
    assert _pair(token, pool).permits_pair is False
    assert _pair(pool, pool).permits_pair is False


def test_provider_id_cannot_pair_records():
    ref = provider_resource_ref("geckoterminal", f"solana_{POOL}", "pool")
    assert _pair(ref, ref).permits_pair is False
    assert _pair(ref, _verified()).permits_pair is False


def test_fallback_identifier_cannot_pair_records():
    assert _pair("solana:sym:PEPE", "solana:sym:PEPE").permits_pair is False


def test_operational_key_cannot_pair_canonically():
    addr = token_address("solana", SOL)
    assert _pair(addr, addr).permits_pair is False
    assert _pair("solana:" + SOL, "solana:" + SOL).permits_pair is False


# --- 19–20. Solana ---

def test_lowercased_solana_key_cannot_pair_canonically():
    folded = token_address("solana", SOL.lower())
    assert _pair(folded, folded).permits_pair is False
    verified = _verified(address=SOL)
    folded_verified = verified_identity_fixture(
        token_id="same-id", address=SOL.lower(),
    )
    # Even a constructed resolution with a folded mint must not pair to exact mint
    # unless addresses are exactly equal. Different address_canonical ⇒ unmatched.
    assert _pair(verified, folded_verified).permits_pair is False


def test_exact_solana_mint_case_preserving_identity_can_pair():
    ident = _verified(address=SOL, token_id="sol-canon")
    decision = _pair(ident, ident)
    assert decision.permits_pair
    assert decision.observed_address == SOL
    assert decision.observed_address != SOL.lower()


# --- 21–22. Cross-chain and different IDs ---

def test_same_address_on_different_chains_does_not_pair():
    evm = verified_identity_fixture(
        chain="ethereum", address=ETH_USDC, token_id="shared-id",
    )
    sol = verified_identity_fixture(
        chain="solana", address=ETH_USDC, token_id="shared-id",
    )
    decision = _pair(evm, sol)
    assert decision.permits_pair is False
    assert decision.reason == "cross_chain_mismatch"


def test_different_canonical_token_ids_do_not_pair():
    a = _verified(token_id="aaa", address=SOL)
    b = _verified(token_id="bbb", address=SOL)
    decision = _pair(a, b)
    assert decision.permits_pair is False
    assert decision.reason == "different_canonical_token_id"


# --- 23–24. Historical safety ---

def test_historical_records_are_not_rewritten(tmp_path):
    row = {"token_id": "legacy-token-id", "score_id": "hist1", "opportunity_score": 50.0}
    snapshot = dict(row)
    assert _pair("legacy-token-id", "legacy-token-id").permits_pair is False
    assert row == snapshot
    db = tmp_path / "ledger.sqlite"
    ScoreLedger(db_path=str(db))
    conn = sqlite3.connect(str(db))
    conn.execute(
        """INSERT INTO opportunity_score_ledger(
             score_id, scored_ts, scored_utc, source, chain, token_address,
             token_id, symbol, opportunity_score, confidence_level, risk_level,
             base_score, total_penalties, engine_version, weights_sha256,
             evidence_sha256, known_field_count, unknown_field_count,
             positive_reasons_json, risk_findings_json, missing_unknowns_json,
             invalidation_json, score_breakdown_json)
           VALUES ('hist1', 1.0, '2026-01-01T00:00:00Z', 'sandbox', 'solana',
                   ?, 'legacy-token-id', 'T', 50.0, 'MED', 'LOW', 0.0, 0.0,
                   'v1', ?, ?, 3, 1, '[]', '[]', '[]', '[]', '{}')""",
        (SOL, "a" * 64, "b" * 64),
    )
    conn.commit()
    before = conn.execute("SELECT * FROM opportunity_score_ledger").fetchone()
    _pair(_verified("legacy-token-id"), None)
    after = conn.execute("SELECT * FROM opportunity_score_ledger").fetchone()
    conn.close()
    assert before == after


def test_historical_association_without_explicit_mapping_is_unmatched():
    current = _verified(token_id="current")
    historical = "legacy-token-id"
    assert _pair(current, historical).permits_pair is False
    assert _pair(historical, current).permits_pair is False


# --- 25. Calibration mathematics unchanged ---

def test_calibration_mathematics_and_metrics_remain_unchanged():
    assert SCORE_BANDS[0] == ("0-20", 0.0, 20.0)
    assert MIN_N_PER_BAND == 200
    assert MIN_POSITIVES == 20
    assert _brier([0.8, 0.2], [1.0, 0.0]) == ((0.8 - 1.0) ** 2 + (0.2 - 0.0) ** 2) / 2
    assert _spearman([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0)


# --- 26–27. Unmatched reporting + ambiguity fail-closed ---

def test_unmatched_reporting_remains_observable(tmp_path):
    ledger_db = tmp_path / "ledger.sqlite"
    disc_db = tmp_path / "disc.sqlite"
    ScoreLedger(db_path=str(ledger_db))
    t0 = time.time() - 86400
    conn = sqlite3.connect(str(ledger_db))
    dconn = sqlite3.connect(str(disc_db))
    dconn.execute(
        """CREATE TABLE outcome_label (
             token_id TEXT NOT NULL, horizon TEXT NOT NULL, event_class TEXT NOT NULL,
             hit INTEGER, max_favorable REAL, max_adverse REAL,
             entry_price REAL, entry_price_ts REAL, resolved_ts REAL NOT NULL,
             PRIMARY KEY (token_id, horizon, event_class))""")
    conn.execute(
        """INSERT INTO opportunity_score_ledger(
             score_id, scored_ts, scored_utc, run_id, source, chain, token_address,
             token_id, symbol, opportunity_score, confidence_level, risk_level,
             base_score, total_penalties, engine_version, weights_sha256,
             evidence_sha256, known_field_count, unknown_field_count,
             positive_reasons_json, risk_findings_json, missing_unknowns_json,
             invalidation_json, score_breakdown_json)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("s0", t0, "2026-01-01T00:00:00Z", "run", SOURCE_TEST, "solana",
         SOL, "legacy-eq", "T", 90.0, "HIGH", "LOW", 0.0, 0.0,
         "AHOS-SCORE-v1", "a" * 64, "b" * 64, 4, 0, "[]", "[]", "[]", "[]", "{}"))
    dconn.execute(
        "INSERT INTO outcome_label(token_id,horizon,event_class,hit,resolved_ts) "
        "VALUES (?,?,?,?,?)", ("legacy-eq", "24h", "+50%", 1, t0 + 3600))
    conn.commit(); conn.close()
    dconn.commit(); dconn.close()
    report = CalibrationHarness(
        ledger_db=str(ledger_db), discovery_db=str(disc_db),
        eligible_sources={SOURCE_TEST},
    ).run()
    assert report.joined_pairs == 0
    assert report.exclusion_reasons.get("identity_unmatched") == 1
    assert report.verdict == "INSUFFICIENT_DATA"


def test_duplicate_ambiguous_candidates_do_not_auto_select():
    ident = _verified()
    other = _verified(token_id="other")
    assert _pair([ident, other], ident).permits_pair is False
    assert _pair(ident, [ident, other]).permits_pair is False


def test_harness_pairs_only_when_both_maps_agree(tmp_path):
    ledger_db = tmp_path / "ledger.sqlite"
    disc_db = tmp_path / "disc.sqlite"
    ScoreLedger(db_path=str(ledger_db))
    t0 = time.time() - 86400
    conn = sqlite3.connect(str(ledger_db))
    dconn = sqlite3.connect(str(disc_db))
    dconn.execute(
        """CREATE TABLE outcome_label (
             token_id TEXT NOT NULL, horizon TEXT NOT NULL, event_class TEXT NOT NULL,
             hit INTEGER, max_favorable REAL, max_adverse REAL,
             entry_price REAL, entry_price_ts REAL, resolved_ts REAL NOT NULL,
             PRIMARY KEY (token_id, horizon, event_class))""")
    conn.execute(
        """INSERT INTO opportunity_score_ledger(
             score_id, scored_ts, scored_utc, run_id, source, chain, token_address,
             token_id, symbol, opportunity_score, confidence_level, risk_level,
             base_score, total_penalties, engine_version, weights_sha256,
             evidence_sha256, known_field_count, unknown_field_count,
             positive_reasons_json, risk_findings_json, missing_unknowns_json,
             invalidation_json, score_breakdown_json)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("s0", t0, "2026-01-01T00:00:00Z", "run", SOURCE_TEST, "solana",
         SOL, "pair-me", "T", 90.0, "HIGH", "LOW", 0.0, 0.0,
         "AHOS-SCORE-v1", "a" * 64, "b" * 64, 4, 0, "[]", "[]", "[]", "[]", "{}"))
    dconn.execute(
        "INSERT INTO outcome_label(token_id,horizon,event_class,hit,resolved_ts) "
        "VALUES (?,?,?,?,?)", ("pair-me", "24h", "+50%", 1, t0 + 3600))
    conn.commit(); conn.close()
    dconn.commit(); dconn.close()
    pred, out = calibration_identity_maps(["pair-me"], address=SOL)
    report = CalibrationHarness(
        ledger_db=str(ledger_db), discovery_db=str(disc_db),
        eligible_sources={SOURCE_TEST},
        prediction_identities=pred,
        outcome_identities=out,
    ).run()
    assert report.joined_pairs == 1
    one_sided = CalibrationHarness(
        ledger_db=str(ledger_db), discovery_db=str(disc_db),
        eligible_sources={SOURCE_TEST},
        prediction_identities=pred,
    ).run()
    assert one_sided.joined_pairs == 0
    assert one_sided.exclusion_reasons.get("identity_unmatched") == 1


# --- 28. No schema / migration ---

def test_no_schema_or_migration_is_introduced():
    from architecture.learning.score_ledger import SCHEMA_SCORE_LEDGER
    from architecture.learning import calibration_identity_join as mod
    src = open(mod.__file__, encoding="utf-8").read()
    assert "ALTER TABLE" not in src
    assert "CREATE TABLE" not in src
    assert "CREATE INDEX" not in src
    assert "token_id" in SCHEMA_SCORE_LEDGER


def test_subject_kind_pool_cannot_pair_tokens():
    ident = _verified()
    assert _pair(ident, ident, subject_kind="POOL").permits_pair is False
    assert _pair(ident, ident, subject_kind="DEPLOYER").permits_pair is False
    assert _pair(ident, ident, subject_kind="HOLDER").permits_pair is False
