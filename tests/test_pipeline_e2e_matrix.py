#!/usr/bin/env python3
"""Multi-Chain Pipeline & Scoring Edge Case Matrix Tests (Phase XX)."""
import sys, time
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from architecture.pipeline.orchestrator import OpportunityPipelineOrchestrator
from architecture.collector.engine import CollectorEngine
from architecture.scoring.engine import OpportunityScorer
from architecture.alerts.engine import AlertEngine
from architecture.providers.contracts import (
    NormalizedTokenCandidate, MarketMetrics, SecuritySignals, ProviderResponse
)
from architecture.providers.registry import ProviderRouter
from telegram_ai.adapter import MockTelegramAdapter


class MockMultiChainProvider:
    def __init__(self, candidates: list[NormalizedTokenCandidate]):
        self.provider_id = "dexscreener"
        self.capabilities = ["discovery"]
        self.candidates = candidates

    def fetch_candidate_tokens(self, chain: str, limit: int = 10):
        matched = [c for c in self.candidates if c.chain == chain]
        return ProviderResponse(self.provider_id, "OK", tokens=matched[:limit])

    def fetch_token_metrics(self, chain: str, address: str):
        return ProviderResponse(self.provider_id, "OK", tokens=[])


def test_pipeline_stamps_source_provider_into_ledger(tmp_path):
    """The production scoring path (pipeline -> from_intelligence) must stamp
    the candidate's discovery provider into every persisted prediction, so
    calibration can segment by provider (Q8). The evaluate() path is covered
    by test_score_ledger_calibration; this pins the pipeline path."""
    from architecture.learning.score_ledger import ScoreLedger

    cand = NormalizedTokenCandidate(
        chain="solana",
        address="SolanaProvider11111111111111111111111111111",
        symbol="PROV",
        name="Provider Token",
        source_provider="geckoterminal",       # distinct from the router id
        retrieved_ts=time.time(),
        metrics=MarketMetrics(liquidity_usd=40000.0, volume_1h=15000.0,
                              txns_1h_buys=30, txns_1h_sells=10),
        security=SecuritySignals(is_honeypot=False, is_contract_verified=True)
    )

    router = ProviderRouter()
    router.providers["dexscreener"] = MockMultiChainProvider([cand])
    router.providers["geckoterminal"] = MockMultiChainProvider([])

    collector = CollectorEngine(db_path=str(tmp_path / "disc.sqlite"), router=router)
    ledger = ScoreLedger(db_path=str(tmp_path / "ledger.sqlite"))
    orchestrator = OpportunityPipelineOrchestrator(
        collector=collector,
        scorer=OpportunityScorer(),
        alert_engine=AlertEngine(),
        telegram_adapter=MockTelegramAdapter(),
        target_chat_id=123,
        score_ledger=ledger,
    )

    rep = orchestrator.run_pipeline(chain="solana", limit=5)
    assert rep.scores_persisted == rep.scores_generated == 1
    rows = ledger.recent(1)
    assert rows[0]["source_provider"] == "geckoterminal", (
        "pipeline must stamp the candidate's discovery provider, not the "
        "router provider id")


@pytest.mark.parametrize("chain", ["solana", "ethereum", "bsc", "base", "arbitrum"])
def test_multi_chain_pipeline_execution(tmp_path, chain):
    db_file = tmp_path / f"test_pipe_{chain}.sqlite"
    cand = NormalizedTokenCandidate(
        chain=chain,
        address=f"0x{chain[:3]}111111111111111111111111111111111111",
        symbol=chain[:4].upper(),
        name=f"{chain.capitalize()} Token",
        source_provider="dexscreener",
        retrieved_ts=time.time(),
        metrics=MarketMetrics(liquidity_usd=40000.0, volume_1h=15000.0, txns_1h_buys=30, txns_1h_sells=10),
        security=SecuritySignals(is_honeypot=False, is_contract_verified=True)
    )

    router = ProviderRouter()
    router.providers["dexscreener"] = MockMultiChainProvider([cand])
    router.providers["geckoterminal"] = MockMultiChainProvider([])
    router.providers["goplus"] = MockMultiChainProvider([cand])
    router.providers["rugcheck"] = MockMultiChainProvider([cand])

    collector = CollectorEngine(db_path=str(db_file), router=router)
    scorer = OpportunityScorer()
    alert_engine = AlertEngine()
    adapter = MockTelegramAdapter()

    orchestrator = OpportunityPipelineOrchestrator(
        collector=collector,
        scorer=scorer,
        alert_engine=alert_engine,
        telegram_adapter=adapter,
        target_chat_id=123
    )

    rep = orchestrator.run_pipeline(chain=chain, limit=5)
    assert rep.candidates_collected == 1
    assert rep.scores_generated == 1
    assert rep.top_opportunity.token_chain == chain
    assert rep.top_opportunity.opportunity_score >= 60.0


def test_scoring_low_liquidity_heavy_penalty():
    cand = NormalizedTokenCandidate(
        chain="solana",
        address="SolanaLowLiq1111111111111111111111111111",
        symbol="LOWLIQ",
        name="Low Liquidity",
        source_provider="dexscreener",
        metrics=MarketMetrics(liquidity_usd=500.0, volume_1h=10000.0)  # Liquidity < $2k
    )
    scorer = OpportunityScorer()
    report = scorer.evaluate(cand)
    assert any(r.risk_id == "LOW_LIQUIDITY" for r in report.risk_deductions)
    assert report.risk_level in ("HIGH", "CRITICAL")


def test_scoring_high_concentration_penalty():
    cand = NormalizedTokenCandidate(
        chain="solana",
        address="SolanaWhale11111111111111111111111111111",
        symbol="WHALE",
        name="Whale Dominated",
        source_provider="dexscreener",
        metrics=MarketMetrics(liquidity_usd=50000.0, volume_1h=20000.0),
        security=SecuritySignals(top10_holder_concentration_pct=85.0)  # > 70% concentration
    )
    scorer = OpportunityScorer()
    report = scorer.evaluate(cand)
    assert any(r.risk_id == "HIGH_HOLDER_CONCENTRATION" for r in report.risk_deductions)


def test_scoring_sell_pressure_penalty():
    cand = NormalizedTokenCandidate(
        chain="solana",
        address="SolanaDump111111111111111111111111111111",
        symbol="DUMP",
        name="Dumping Token",
        source_provider="dexscreener",
        metrics=MarketMetrics(
            liquidity_usd=30000.0,
            volume_1h=15000.0,
            txns_1h_buys=5,
            txns_1h_sells=50  # Heavy sell pressure
        )
    )
    scorer = OpportunityScorer()
    report = scorer.evaluate(cand)
    assert any(r.risk_id == "SELL_PRESSURE" for r in report.risk_deductions)
