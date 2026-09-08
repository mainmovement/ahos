#!/usr/bin/env python3
"""End-to-End Opportunity Pipeline Integration Tests (Phase XX).

Proves the complete path:
  Providers -> Normalization -> Evidence -> Features -> Risk -> Opportunity Score -> Alert -> Telegram
"""
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
from architecture.providers.contracts import NormalizedTokenCandidate, MarketMetrics, SecuritySignals, ProviderResponse
from architecture.providers.registry import ProviderRouter
from telegram_ai.adapter import MockTelegramAdapter
from telegram_ai.response_contract import FOOTER_MANDATED
from tests.helpers_security import OLD_POOL_TS, passing_security_signals


class MockDiscoveryProvider:
    def __init__(self, name: str, candidates: list[NormalizedTokenCandidate]):
        self.provider_id = name
        self.capabilities = ["discovery"]
        self.candidates = candidates

    def fetch_candidate_tokens(self, chain: str, limit: int = 10):
        return ProviderResponse(self.provider_id, "OK", tokens=self.candidates[:limit])

    def fetch_token_metrics(self, chain: str, address: str):
        return ProviderResponse(self.provider_id, "OK", tokens=[])


def test_full_pipeline_orchestration_high_opportunity(tmp_path):
    db_file = tmp_path / "test_pipe_discovery.sqlite"
    telegram_adapter = MockTelegramAdapter()

    cand_high = NormalizedTokenCandidate(
        chain="solana",
        address="SolanaAlpha11111111111111111111111111111",
        symbol="ALPHA",
        name="Alpha Gem",
        source_provider="dexscreener",
        retrieved_ts=time.time(),
        pair_created_ts=OLD_POOL_TS,
        metrics=MarketMetrics(
            price_usd=0.10,
            liquidity_usd=80000.0,
            volume_1h=40000.0,
            volume_velocity=3.2,
            txns_1h_buys=90,
            txns_1h_sells=20
        ),
        security=passing_security_signals(
            is_honeypot=False,
            is_contract_verified=True,
            is_ownership_renounced=True,
            top10_holder_concentration_pct=22.0
        ),
        social_presence={"twitter": "https://x.com/alpha"}
    )

    router = ProviderRouter()
    router.providers["dexscreener"] = MockDiscoveryProvider("dexscreener", [cand_high])
    router.providers["geckoterminal"] = MockDiscoveryProvider("geckoterminal", [])

    collector = CollectorEngine(db_path=str(db_file), router=router)
    scorer = OpportunityScorer()
    alert_engine = AlertEngine(score_threshold=70.0)

    orchestrator = OpportunityPipelineOrchestrator(
        collector=collector,
        scorer=scorer,
        alert_engine=alert_engine,
        telegram_adapter=telegram_adapter,
        target_chat_id=123456
    )

    report = orchestrator.run_pipeline(chain="solana", limit=5)

    assert report.candidates_collected == 1
    assert report.scores_generated == 1
    assert report.top_opportunity is not None
    assert report.top_opportunity.token_symbol == "ALPHA"
    assert report.top_opportunity.opportunity_score >= 80.0
    assert report.top_opportunity.risk_level == "LOW"
    assert report.top_opportunity.confidence_level == "HIGH"

    # Alerts verification
    assert report.alerts_emitted >= 1
    assert any(a.cls == "OPPORTUNITY" for a in report.alerts)

    # Telegram notification verification
    assert report.telegram_messages_sent >= 1
    assert len(telegram_adapter.sent_messages) >= 1
    sent_text = telegram_adapter.sent_messages[-1]["text"]
    assert "ALPHA" in sent_text
    assert FOOTER_MANDATED in sent_text
    assert report.trace is not None
    assert report.trace.status == "OK"


def test_full_pipeline_honeypot_detection_and_security_alert(tmp_path):
    db_file = tmp_path / "test_pipe_sec.sqlite"
    telegram_adapter = MockTelegramAdapter()

    cand_scam = NormalizedTokenCandidate(
        chain="ethereum",
        address="0x3333333333333333333333333333333333333333",
        symbol="RUG",
        name="Rug Token",
        source_provider="dexscreener",
        retrieved_ts=time.time(),
        metrics=MarketMetrics(liquidity_usd=50000.0, volume_1h=20000.0),
        security=SecuritySignals(is_honeypot=True)
    )

    router = ProviderRouter()
    router.providers["dexscreener"] = MockDiscoveryProvider("dexscreener", [cand_scam])
    router.providers["geckoterminal"] = MockDiscoveryProvider("geckoterminal", [])
    router.providers["goplus"] = MockDiscoveryProvider("goplus", [cand_scam])

    collector = CollectorEngine(db_path=str(db_file), router=router)
    scorer = OpportunityScorer()
    alert_engine = AlertEngine(score_threshold=70.0)

    orchestrator = OpportunityPipelineOrchestrator(
        collector=collector,
        scorer=scorer,
        alert_engine=alert_engine,
        telegram_adapter=telegram_adapter,
        target_chat_id=123456
    )

    report = orchestrator.run_pipeline(chain="ethereum", limit=5)
    assert report.scores_generated == 1
    assert report.top_opportunity.opportunity_score == 0.0
    assert report.top_opportunity.risk_level == "CRITICAL"
    assert any(a.cls == "SECURITY_EVENT" for a in report.alerts)

    # Telegram received security alert
    assert any("رویداد امنیتی" in msg["text"] or "Honeypot" in msg["text"]
               for msg in telegram_adapter.sent_messages)
    assert not any("فرصت ویژه" in (msg.get("text") or "") for msg in telegram_adapter.sent_messages)


def test_pipeline_score_alone_does_not_send_special_telegram(tmp_path):
    """High score + incomplete security must not mint Telegram فرصت ویژه."""
    db_file = tmp_path / "test_pipe_score_only.sqlite"
    telegram_adapter = MockTelegramAdapter()
    cand = NormalizedTokenCandidate(
        chain="solana",
        address="SolanaAlpha11111111111111111111111111111",
        symbol="ALPHA",
        name="Alpha Gem",
        source_provider="dexscreener",
        retrieved_ts=time.time(),
        metrics=MarketMetrics(
            price_usd=0.10, liquidity_usd=80000.0, volume_1h=40000.0,
            volume_velocity=3.2, txns_1h_buys=90, txns_1h_sells=20,
        ),
        security=SecuritySignals(is_honeypot=False),
    )
    router = ProviderRouter()
    router.providers["dexscreener"] = MockDiscoveryProvider("dexscreener", [cand])
    router.providers["geckoterminal"] = MockDiscoveryProvider("geckoterminal", [])
    orchestrator = OpportunityPipelineOrchestrator(
        collector=CollectorEngine(db_path=str(db_file), router=router),
        scorer=OpportunityScorer(),
        alert_engine=AlertEngine(score_threshold=1.0),
        telegram_adapter=telegram_adapter,
        target_chat_id=123456,
    )
    report = orchestrator.run_pipeline(chain="solana", limit=5)
    assert report.top_opportunity is not None
    assert not any("فرصت ویژه" in (msg.get("text") or "") for msg in telegram_adapter.sent_messages)
    assert not any(a.cls == "OPPORTUNITY" for a in report.alerts)
