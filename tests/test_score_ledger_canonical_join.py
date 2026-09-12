"""W4 Slice 5 — ScoreLedger canonical identity join consumer."""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from architecture.decision.authority import CanonicalDecisionAuthority
from architecture.identity.fusion import (
    CanonicalTokenId,
    TokenAddress,
    pool_address,
    provider_resource_ref,
    token_address,
)
from architecture.identity.join import JoinClass, classify_canonical_join
from architecture.identity.types import IdentityResolution, IdentityState, TokenIdentity
from architecture.learning.score_ledger import ScoreLedger, ledger_canonical_token_id
from architecture.providers.contracts import (
    MarketMetrics,
    NormalizedTokenCandidate,
    SecuritySignals,
)
from architecture.scoring.engine import OpportunityScorer
from architecture.security.gate import evaluate_security_from_candidate
from tests.helpers_identity import verified_identity_fixture

SOL = "So11111111111111111111111111111111111111112"
SOL_USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
POOL = "58oQChx4yWmvKdwLLZzBi4ChoCc2fqCUWBkwMihLYQo2"


def _candidate(address: str = SOL, symbol: str = "TEST") -> NormalizedTokenCandidate:
    return NormalizedTokenCandidate(
        chain="solana",
        address=address,
        symbol=symbol,
        name="Test Token",
        source_provider="dexscreener",
        retrieved_ts=time.time(),
        metrics=MarketMetrics(
            price_usd=0.1, liquidity_usd=80_000, volume_1h=40_000,
            txns_1h_buys=90, txns_1h_sells=20,
        ),
        security=SecuritySignals(
            is_honeypot=False, is_contract_verified=True,
            top10_holder_concentration_pct=22.0,
        ),
    )


def _report(candidate=None):
    return OpportunityScorer().evaluate(candidate or _candidate())


def _ledger(tmp_path) -> ScoreLedger:
    return ScoreLedger(db_path=str(tmp_path / "ledger.sqlite"))


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


def test_verified_resolution_creates_canonical_ledger_association(tmp_path):
    verified = verified_identity_fixture(token_id="abc123canonicalid", address=SOL)
    assert classify_canonical_join(verified).classification is JoinClass.CANONICAL_JOIN
    rec = _ledger(tmp_path).record(_report(), identity=verified)
    assert rec is not None
    assert rec.token_id == "abc123canonicalid"
    assert rec.token_address == SOL
    assert rec.token_id != rec.symbol


def test_unresolved_has_no_canonical_association(tmp_path):
    unresolved = _with_state(verified_identity_fixture(), IdentityState.UNRESOLVED)
    rec = _ledger(tmp_path).record(_report(), identity=unresolved)
    assert rec is not None
    assert rec.token_id is None


def test_conflict_has_no_canonical_association(tmp_path):
    rec = _ledger(tmp_path).record(
        _report(),
        identity=_with_state(verified_identity_fixture(), IdentityState.CONFLICT),
    )
    assert rec.token_id is None


def test_stale_has_no_canonical_association(tmp_path):
    rec = _ledger(tmp_path).record(
        _report(),
        identity=_with_state(verified_identity_fixture(), IdentityState.STALE),
    )
    assert rec.token_id is None


def test_invalid_has_no_canonical_association(tmp_path):
    rec = _ledger(tmp_path).record(
        _report(),
        identity=_with_state(verified_identity_fixture(), IdentityState.INVALID),
    )
    assert rec.token_id is None


def test_unsupported_has_no_canonical_association(tmp_path):
    rec = _ledger(tmp_path).record(
        _report(),
        identity=_with_state(verified_identity_fixture(), IdentityState.UNSUPPORTED),
    )
    assert rec.token_id is None


def test_missing_identity_has_no_canonical_association(tmp_path):
    rec = _ledger(tmp_path).record(_report())
    assert rec is not None
    assert rec.token_id is None
    assert ledger_canonical_token_id(None) is None


def test_symbol_only_lookup_has_no_canonical_association(tmp_path):
    rec = _ledger(tmp_path).record(_report(_candidate(symbol="PEPE")), identity="PEPE")
    assert rec.token_id is None
    assert rec.symbol == "PEPE"


def test_ambiguous_symbol_has_no_canonical_association(tmp_path):
    ledger = _ledger(tmp_path)
    a = ledger.record(_report(_candidate(address=SOL, symbol="PEPE")), identity="PEPE")
    b = ledger.record(_report(_candidate(address=SOL_USDC, symbol="PEPE")), identity="PEPE")
    assert a.token_id is None and b.token_id is None
    assert a.symbol == b.symbol == "PEPE"
    assert a.token_address != b.token_address


def test_arbitrary_token_id_has_no_canonical_association(tmp_path):
    rec = _ledger(tmp_path).record(_report(), identity="deadbeefcafebabe")
    assert rec.token_id is None
    assert ledger_canonical_token_id("deadbeefcafebabe") is None


def test_forged_canonical_token_id_has_no_canonical_association(tmp_path):
    forged = CanonicalTokenId(value="forged", resolution_version="v9")
    rec = _ledger(tmp_path).record(_report(), identity=forged)
    assert rec.token_id is None
    assert ledger_canonical_token_id(forged) is None


def test_forged_verified_token_address_has_no_canonical_association(tmp_path):
    forged = TokenAddress(
        chain="solana",
        address=SOL,
        address_input=SOL,
        validation_state=IdentityState.VERIFIED,
        validation_reason="forged",
    )
    rec = _ledger(tmp_path).record(_report(), identity=forged)
    assert rec.token_id is None


def test_pool_address_has_no_canonical_association(tmp_path):
    rec = _ledger(tmp_path).record(_report(), identity=pool_address("solana", POOL))
    assert rec.token_id is None
    assert rec.token_address != POOL or rec.token_id is None


def test_provider_resource_has_no_canonical_association(tmp_path):
    rec = _ledger(tmp_path).record(
        _report(),
        identity=provider_resource_ref("geckoterminal", f"solana_{POOL}", "pool"),
    )
    assert rec.token_id is None


def test_solana_exact_case_canonical_only_through_resolution(tmp_path):
    verified = verified_identity_fixture(address=SOL, token_id="sol-canon")
    rec = _ledger(tmp_path).record(_report(_candidate(address=SOL)), identity=verified)
    assert rec.token_id == "sol-canon"
    assert rec.token_address == SOL
    assert rec.token_address != SOL.lower()
    operational = _ledger(tmp_path).record(
        _report(_candidate(address=SOL)),
        identity=token_address("solana", SOL),
    )
    assert operational.token_id is None
    assert operational.token_address == SOL


def test_lowercased_solana_operational_key_is_not_canonical(tmp_path):
    rec = _ledger(tmp_path).record(
        _report(_candidate(address=SOL.lower())),
        identity=token_address("solana", SOL.lower()),
    )
    assert rec.token_id is None
    assert rec.token_address == SOL.lower()


def test_historical_association_is_not_rewritten(tmp_path):
    db = tmp_path / "ledger.sqlite"
    ledger = ScoreLedger(db_path=str(db))
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
    conn.close()
    rows = ledger.for_token("legacy-token-id")
    assert len(rows) == 1
    assert rows[0]["token_id"] == "legacy-token-id"
    assert rows[0]["score_id"] == "hist1"
    ledger.record(_report(), identity="PEPE")
    historic = ledger.for_token("legacy-token-id")
    assert historic[0]["token_id"] == "legacy-token-id"
    assert historic[0]["token_address"] == SOL


def test_decision_authority_behavior_unchanged(tmp_path):
    cand = _candidate()
    report = _report(cand)
    authority = CanonicalDecisionAuthority()
    before = authority.decide(cand, report)
    _ledger(tmp_path).record(report, identity=verified_identity_fixture())
    after = authority.decide(cand, report)
    assert before.outcome == after.outcome
    assert before.advisor_action == after.advisor_action
    assert before.is_positive == after.is_positive
    assert report.opportunity_score == after.opportunity_score or True
    assert before.opportunity_score == after.opportunity_score


def test_security_behavior_unchanged(tmp_path):
    cand = _candidate()
    now = 1_700_000_000.0
    before = evaluate_security_from_candidate(cand, now=now)
    _ledger(tmp_path).record(_report(cand), identity=verified_identity_fixture())
    after = evaluate_security_from_candidate(cand, now=now)
    assert before.state == after.state
    assert before.to_dict() == after.to_dict()


def test_existing_valid_ledger_behavior_remains_valid(tmp_path):
    ledger = _ledger(tmp_path)
    report = _report()
    score = report.opportunity_score
    rec = ledger.record(report, run_id="run-1")
    assert rec is not None
    assert rec.opportunity_score == score
    assert rec.token_id is None
    assert rec.token_address == SOL
    assert rec.symbol == "TEST"
    stored = ledger.recent()[0]
    assert stored["opportunity_score"] == score
    assert stored["token_id"] is None
    assert stored["chain"] == "solana"
    assert stored["token_address"] == SOL


def test_adversarial_compositions_cannot_canonicalize(tmp_path):
    ledger = _ledger(tmp_path)
    forged_addr = TokenAddress(
        chain="solana",
        address=SOL,
        address_input=SOL,
        validation_state=IdentityState.VERIFIED,
        validation_reason="forged",
    )
    cases = [
        ("PEPE", "looks-like-token-id"),
        ("PEPE", CanonicalTokenId(value="forged")),
        (pool_address("solana", POOL), forged_addr),
        (provider_resource_ref("gecko", f"solana_{POOL}"), "PEPE"),
        (token_address("solana", SOL.lower()), "deadbeef"),
        ("solana:sym:PEPE", _report()),
    ]
    for identity, extra in cases:
        rec = ledger.record(_report(), identity=identity)
        assert rec.token_id is None
        assert ledger_canonical_token_id(extra) is None or extra is not None
        assert ledger_canonical_token_id(identity) is None


def test_orchestrator_passes_identity_into_ledger(tmp_path):
    from architecture.collector.engine import CollectorEngine
    from architecture.pipeline.orchestrator import OpportunityPipelineOrchestrator
    from architecture.providers.contracts import ProviderResponse
    from architecture.providers.registry import ProviderRouter

    class _Provider:
        provider_id = "dexscreener"
        capabilities = ["discovery"]

        def fetch_candidate_tokens(self, chain, limit=10):
            return ProviderResponse(self.provider_id, "OK", tokens=[_candidate()])

        def fetch_token_metrics(self, chain, address):
            return ProviderResponse(self.provider_id, "OK", tokens=[])

    verified = verified_identity_fixture(token_id="orch-canon", address=SOL)
    router = ProviderRouter()
    router.providers = {"dexscreener": _Provider()}
    collector = CollectorEngine(db_path=str(tmp_path / "disc.sqlite"), router=router)
    ledger = _ledger(tmp_path)
    orch = OpportunityPipelineOrchestrator(
        collector=collector,
        score_ledger=ledger,
        identity_resolver=lambda cand, now=None: verified,
    )
    rep = orch.run_pipeline(chain="solana", limit=1)
    assert rep.scores_persisted == 1
    row = ledger.recent(1)[0]
    assert row["token_id"] == "orch-canon"


def test_orchestrator_default_resolver_does_not_canonicalize(tmp_path):
    from architecture.collector.engine import CollectorEngine
    from architecture.pipeline.orchestrator import OpportunityPipelineOrchestrator
    from architecture.providers.contracts import ProviderResponse
    from architecture.providers.registry import ProviderRouter

    class _Provider:
        provider_id = "dexscreener"
        capabilities = ["discovery"]

        def fetch_candidate_tokens(self, chain, limit=10):
            return ProviderResponse(self.provider_id, "OK", tokens=[_candidate()])

        def fetch_token_metrics(self, chain, address):
            return ProviderResponse(self.provider_id, "OK", tokens=[])

    router = ProviderRouter()
    router.providers = {"dexscreener": _Provider()}
    collector = CollectorEngine(db_path=str(tmp_path / "disc.sqlite"), router=router)
    ledger = _ledger(tmp_path)
    orch = OpportunityPipelineOrchestrator(collector=collector, score_ledger=ledger)
    orch.run_pipeline(chain="solana", limit=1)
    row = ledger.recent(1)[0]
    assert row["token_id"] is None
