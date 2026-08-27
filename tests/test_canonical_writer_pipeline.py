#!/usr/bin/env python3
"""Phase 3 — the Python pipeline is the canonical decision writer.

Proves the orchestrator persists a canonical record reflecting the SAME
disposition it already computed (VETO/UNKNOWN never eligible; PASS eligible),
and that the store is fail-closed for tokens that never passed.

Addresses are deliberately FAKE (non-resolvable) so the collector's security
enrichment returns UNKNOWN — keeping these tests deterministic and offline,
matching the Sub-PR 1 pattern.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.pipeline.orchestrator import OpportunityPipelineOrchestrator
from architecture.collector.engine import CollectorEngine
from architecture.scoring.engine import OpportunityScorer
from architecture.alerts.engine import AlertEngine
from architecture.providers.contracts import (
    NormalizedTokenCandidate, MarketMetrics, SecuritySignals, ProviderResponse,
)
from architecture.providers.registry import ProviderRouter
from architecture.canonical.decision_store import CanonicalDecisionStore
from architecture.canonical.identity import canonical_token_id
from telegram_ai.adapter import MockTelegramAdapter


class _MockDiscoveryProvider:
    def __init__(self, name, candidates):
        self.provider_id = name
        self.capabilities = ["discovery"]
        self.candidates = candidates

    def fetch_candidate_tokens(self, chain, limit=10):
        return ProviderResponse(self.provider_id, "OK", tokens=self.candidates[:limit])

    def fetch_token_metrics(self, chain, address):
        return ProviderResponse(self.provider_id, "OK", tokens=[])


def _strong():
    return MarketMetrics(price_usd=0.1, liquidity_usd=90000.0, volume_1h=45000.0,
                         txns_1h_buys=95, txns_1h_sells=15)


def _run(address, security, tmp_path, dbn):
    cand = NormalizedTokenCandidate(
        chain="solana", address=address, symbol="TK", name="Token",
        source_provider="dexscreener", retrieved_ts=1_000_000.0,
        metrics=_strong(), security=security)
    router = ProviderRouter()
    router.providers["dexscreener"] = _MockDiscoveryProvider("dexscreener", [cand])
    router.providers["geckoterminal"] = _MockDiscoveryProvider("geckoterminal", [])
    collector = CollectorEngine(db_path=str(tmp_path / dbn), router=router)
    store = CanonicalDecisionStore(store_dir=tmp_path / "canon", freshness_budget_sec=900)
    orch = OpportunityPipelineOrchestrator(
        collector=collector, scorer=OpportunityScorer(),
        alert_engine=AlertEngine(score_threshold=70.0),
        telegram_adapter=MockTelegramAdapter(), target_chat_id=1,
        decision_store=store,
    )
    now = 1_000_000.0
    orch.run_pipeline(chain="solana", limit=5, now=now)
    return store, now, canonical_token_id("solana", address)


def test_pass_token_is_written_eligible(tmp_path):
    store, now, cid = _run(
        "SolCanonPass1111111111111111111111111111",
        SecuritySignals(is_honeypot=False, is_contract_verified=True,
                        is_ownership_renounced=True, top10_holder_concentration_pct=20.0),
        tmp_path, "cw_pass.sqlite")
    rec = store.get(cid, now=now)
    assert rec is not None
    assert rec.security_disposition == "PASS"
    assert rec.opportunity_eligible is True
    assert store.is_positive_opportunity(cid, now=now) is True


def test_unknown_token_is_written_not_eligible(tmp_path):
    store, now, cid = _run(
        "SolCanonUnk11111111111111111111111111111",
        SecuritySignals(), tmp_path, "cw_unk.sqlite")
    rec = store.get(cid, now=now)
    assert rec is not None
    assert rec.security_disposition == "PASS_WITH_UNKNOWN"
    assert rec.opportunity_eligible is False
    assert store.is_positive_opportunity(cid, now=now) is False


def test_veto_token_is_written_not_eligible(tmp_path):
    store, now, cid = _run(
        "SolCanonVeto1111111111111111111111111111",
        SecuritySignals(is_honeypot=False, has_mint_authority=True),
        tmp_path, "cw_veto.sqlite")
    rec = store.get(cid, now=now)
    assert rec is not None
    assert rec.security_disposition == "SECURITY_VETO"
    assert rec.opportunity_eligible is False
    assert store.is_positive_opportunity(cid, now=now) is False


def test_score_is_evidence_not_authority(tmp_path):
    """UNKNOWN token with a high numeric score is still not a positive opportunity."""
    store, now, cid = _run(
        "SolCanonScore111111111111111111111111111",
        SecuritySignals(), tmp_path, "cw_score.sqlite")
    rec = store.get(cid, now=now)
    assert rec is not None
    assert rec.opportunity_eligible is False


def test_pipeline_without_store_is_noop(tmp_path):
    """No injected store ⇒ no canonical write (ad-hoc/test constructions stay clean)."""
    cand = NormalizedTokenCandidate(
        chain="solana", address="SolCanonNoop1111111111111111111111111111",
        symbol="X", name="X", source_provider="dexscreener",
        retrieved_ts=1_000_000.0, metrics=_strong(),
        security=SecuritySignals(is_honeypot=False))
    router = ProviderRouter()
    router.providers["dexscreener"] = _MockDiscoveryProvider("dexscreener", [cand])
    router.providers["geckoterminal"] = _MockDiscoveryProvider("geckoterminal", [])
    collector = CollectorEngine(db_path=str(tmp_path / "cw_noop.sqlite"), router=router)
    orch = OpportunityPipelineOrchestrator(collector=collector)  # no decision_store
    rep = orch.run_pipeline(chain="solana", limit=5, now=1_000_000.0)
    assert rep.scores_generated == 1
