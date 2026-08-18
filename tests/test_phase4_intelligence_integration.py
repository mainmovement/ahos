#!/usr/bin/env python3
"""Phase 4 integration review: wiring, isolation, no raw-data leakage.

Checks the mandate:
  - intelligence / features / scoring / risk / explanations exist and connect
  - calculation modules do not import NormalizedTokenCandidate
  - pipeline orchestrator runs the Evidence path
  - no isolated modules (imports resolve; orchestrator holds IntelligenceEngine)
"""
from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.intelligence import IntelligenceEngine, materialize_evidence
from architecture.pipeline.orchestrator import OpportunityPipelineOrchestrator
from architecture.providers.contracts import (
    MarketMetrics,
    NormalizedTokenCandidate,
    ProviderResponse,
    SecuritySignals,
)
from architecture.providers.registry import ProviderRouter
from architecture.collector.engine import CollectorEngine
from architecture.scoring.engine import OpportunityScorer
from architecture.alerts.engine import AlertEngine
from telegram_ai.adapter import MockTelegramAdapter


CALC_MODULES = [
    ROOT / "architecture" / "features" / "extractor.py",
    ROOT / "architecture" / "risk" / "engine.py",
    ROOT / "architecture" / "scoring" / "calculator.py",
    ROOT / "architecture" / "explanations" / "engine.py",
    ROOT / "architecture" / "intelligence" / "engine.py",
    ROOT / "architecture" / "security" / "engine.py",
    ROOT / "architecture" / "security" / "contract_analysis.py",
    ROOT / "architecture" / "security" / "liquidity_analysis.py",
    ROOT / "architecture" / "security" / "holder_analysis.py",
    ROOT / "architecture" / "security" / "manipulation_detection.py",
    ROOT / "architecture" / "intelligence" / "whales" / "wallet_activity.py",
    ROOT / "architecture" / "intelligence" / "whales" / "smart_money_detector.py",
    ROOT / "architecture" / "intelligence" / "whales" / "whale_signals.py",
]


def test_phase4_packages_exist_and_import():
    for name in (
        "architecture.intelligence",
        "architecture.features",
        "architecture.scoring",
        "architecture.risk",
        "architecture.explanations",
        "architecture.security",
        "architecture.intelligence.whales",
    ):
        mod = importlib.import_module(name)
        assert mod is not None


def test_calculation_modules_do_not_import_raw_candidate():
    """No isolated raw-data path: these modules must not mention the candidate type."""
    for path in CALC_MODULES:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src)
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imported.append((node.module or "", [a.name for a in node.names]))
            elif isinstance(node, ast.Import):
                imported.append((None, [a.name for a in node.names]))
        assert "NormalizedTokenCandidate" not in src, f"{path.name} mentions raw candidate"
        for module, names in imported:
            assert "NormalizedTokenCandidate" not in names
            if module:
                assert "providers.contracts" not in module


def test_only_materialize_reads_candidate_metrics():
    src = (ROOT / "architecture" / "intelligence" / "evidence.py").read_text(encoding="utf-8")
    assert "def materialize_evidence" in src
    assert "THE ONLY admitted conversion" in src or "single admitted conversion" in src


def test_orchestrator_holds_intelligence_engine(tmp_path):
    orch = OpportunityPipelineOrchestrator(
        collector=CollectorEngine(db_path=str(tmp_path / "x.sqlite")),
        scorer=OpportunityScorer(),
        alert_engine=AlertEngine(),
    )
    assert isinstance(orch.intelligence, IntelligenceEngine)


def test_pipeline_uses_evidence_path(tmp_path):
    class MockDiscoveryProvider:
        def __init__(self, candidates):
            self.provider_id = "dexscreener"
            self.capabilities = ["discovery"]
            self.candidates = candidates

        def fetch_candidate_tokens(self, chain, limit=10):
            return ProviderResponse(self.provider_id, "OK", tokens=self.candidates[:limit])

        def fetch_token_metrics(self, chain, address):
            return ProviderResponse(self.provider_id, "OK", tokens=[])

    cand = NormalizedTokenCandidate(
        chain="solana",
        address="SolanaAlpha11111111111111111111111111111",
        symbol="ALPHA",
        name="Alpha Gem",
        source_provider="dexscreener",
        retrieved_ts=1_787_000_000.0,
        metrics=MarketMetrics(
            price_usd=0.10, liquidity_usd=80000.0, volume_1h=40000.0,
            volume_velocity=3.2, txns_1h_buys=90, txns_1h_sells=20,
        ),
        security=SecuritySignals(
            is_honeypot=False, is_contract_verified=True,
            is_ownership_renounced=True, top10_holder_concentration_pct=22.0,
        ),
        social_presence={"twitter": "https://x.com/alpha"},
    )
    router = ProviderRouter()
    router.providers["dexscreener"] = MockDiscoveryProvider([cand])
    router.providers["geckoterminal"] = MockDiscoveryProvider([])
    orch = OpportunityPipelineOrchestrator(
        collector=CollectorEngine(db_path=str(tmp_path / "p.sqlite"), router=router),
        scorer=OpportunityScorer(),
        alert_engine=AlertEngine(score_threshold=70.0),
        telegram_adapter=MockTelegramAdapter(),
        target_chat_id=1,
    )
    report = orch.run_pipeline(chain="solana", limit=5, now=1_787_000_000.0)
    assert report.scores_generated == 1
    assert report.top_opportunity is not None
    assert report.top_opportunity.opportunity_score >= 80.0
    assert report.top_opportunity.evidence_items
    # Evidence path leaves a provenance digest (empty string was the pre-Phase-4 default).
    assert report.top_opportunity.provenance_sha256


def test_no_duplicate_score_math_in_facade():
    """OpportunityScorer.evaluate must delegate; it must not reimplement brackets."""
    src = (ROOT / "architecture" / "scoring" / "engine.py").read_text(encoding="utf-8")
    assert "materialize_evidence" in src
    assert "from_intelligence" in src
    assert "50000" not in src
    assert "CRITICAL_HONEYPOT" not in src


def test_pipeline_keeps_candidate_score_pairing(tmp_path):
    """A high-score token must not inherit another token's identity after ranking."""
    class MockDiscoveryProvider:
        def __init__(self, candidates):
            self.provider_id = "dexscreener"
            self.capabilities = ["discovery"]
            self.candidates = candidates

        def fetch_candidate_tokens(self, chain, limit=10):
            return ProviderResponse(self.provider_id, "OK", tokens=self.candidates[:limit])

        def fetch_token_metrics(self, chain, address):
            return ProviderResponse(self.provider_id, "OK", tokens=[])

    weak = NormalizedTokenCandidate(
        chain="solana", address="WeakTok111111111111111111111111111111111",
        symbol="WEAK", name="Weak", source_provider="dexscreener",
        retrieved_ts=1_787_000_000.0,
        metrics=MarketMetrics(liquidity_usd=500.0, volume_1h=100.0),
        security=SecuritySignals(is_honeypot=False),
    )
    strong = NormalizedTokenCandidate(
        chain="solana", address="StrongTok1111111111111111111111111111111",
        symbol="STRNG", name="Strong", source_provider="dexscreener",
        retrieved_ts=1_787_000_000.0,
        metrics=MarketMetrics(
            liquidity_usd=90000.0, volume_1h=50000.0,
            txns_1h_buys=80, txns_1h_sells=20,
        ),
        security=SecuritySignals(
            is_honeypot=False, is_contract_verified=True,
            top10_holder_concentration_pct=20.0,
        ),
        social_presence={"x": "1"},
    )
    router = ProviderRouter()
    router.providers["dexscreener"] = MockDiscoveryProvider([weak, strong])
    router.providers["geckoterminal"] = MockDiscoveryProvider([])
    orch = OpportunityPipelineOrchestrator(
        collector=CollectorEngine(db_path=str(tmp_path / "pair.sqlite"), router=router),
        scorer=OpportunityScorer(),
        alert_engine=AlertEngine(score_threshold=70.0),
    )
    report = orch.run_pipeline(chain="solana", limit=5, now=1_787_000_000.0)
    assert report.scores_generated == 2
    assert report.top_opportunity is not None
    assert report.top_opportunity.token_symbol == "STRNG"
    assert report.top_opportunity.token_address == strong.address
    assert all(a.symbol != "WEAK" or a.cls != "OPPORTUNITY" for a in report.alerts)


def test_lane_isolation_phase4_modules():
    """New architecture modules must not import experiment packages."""
    import re
    bad = []
    roots = [
        ROOT / "architecture" / "intelligence",
        ROOT / "architecture" / "features",
        ROOT / "architecture" / "risk",
        ROOT / "architecture" / "explanations",
        ROOT / "architecture" / "scoring",
        ROOT / "architecture" / "security",
        ROOT / "architecture" / "intelligence" / "whales",
    ]
    for folder in roots:
        for path in folder.glob("*.py"):
            text = path.read_text(encoding="utf-8")
            for pat in ("discovery", "paper_trading", "research", "telegram_ai", "engine"):
                if re.search(rf"^\s*(from|import)\s+{pat}(\.|$|\s)", text, re.M):
                    bad.append(f"{path.name}:{pat}")
    assert bad == [], bad
