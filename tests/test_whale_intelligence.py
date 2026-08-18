#!/usr/bin/env python3
"""Phase 5 whale intelligence — Evidence-only wallet / smart-money / signals."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.intelligence import (
    EvidenceContractError,
    IntelligenceEngine,
    materialize_evidence,
)
from architecture.intelligence.whales import (
    SmartMoneyDetector,
    WalletActivityAnalyzer,
    WhaleIntelligence,
)
from architecture.providers.contracts import (
    MarketMetrics,
    NormalizedTokenCandidate,
    SecuritySignals,
)

NOW = 1_787_000_000.0


def _cand(**kwargs) -> NormalizedTokenCandidate:
    c = NormalizedTokenCandidate(
        chain="solana",
        address="WhaleTok11111111111111111111111111111111",
        symbol="WHL", name="Whale Token",
        source_provider="dexscreener", retrieved_ts=NOW,
        metrics=kwargs.pop("metrics", MarketMetrics(
            liquidity_usd=80000.0, volume_1h=20000.0, price_change_1h=0.05,
        )),
        security=kwargs.pop("security", SecuritySignals(
            is_honeypot=False, top10_holder_concentration_pct=30.0,
        )),
        social_presence={"x": "1"},
    )
    for k, v in kwargs.items():
        setattr(c, k, v)
    return c


def test_whale_modules_reject_raw_data():
    raw = _cand()
    with pytest.raises(EvidenceContractError):
        WalletActivityAnalyzer().analyze(raw)  # type: ignore[arg-type]
    with pytest.raises(EvidenceContractError):
        SmartMoneyDetector().analyze(raw)  # type: ignore[arg-type]
    with pytest.raises(EvidenceContractError):
        WhaleIntelligence().analyze(raw)  # type: ignore[arg-type]


def test_unknown_wallet_data_is_unknown_not_invented():
    report = WhaleIntelligence().analyze(materialize_evidence(_cand(), now=NOW))
    assert report.label in ("STABLE", "UNKNOWN")
    assert not report.has("LARGE_WALLET_OUTFLOW")
    assert not report.has("INSIDER_DISTRIBUTION")
    assert not report.has("WHALE_TRAP")


def test_large_outflow_and_distribution():
    cand = _cand(wallet_events=[
        {"address": "W1", "side": "SELL", "usd": 20000.0, "label": "WHALE"},
        {"address": "W2", "side": "SELL", "usd": 8000.0, "label": "WHALE"},
    ])
    report = WhaleIntelligence().analyze(materialize_evidence(cand, now=NOW))
    assert report.label == "DISTRIBUTING"
    assert report.has("LARGE_WALLET_OUTFLOW")
    assert report.activity is not None
    assert report.activity.net_flow_usd is not None
    assert report.activity.net_flow_usd < 0


def test_accumulation_signal():
    cand = _cand(wallet_events=[
        {"address": "S1", "side": "BUY", "usd": 15000.0, "label": "SMART"},
        {"address": "S2", "side": "BUY", "usd": 4000.0, "label": "SMART"},
    ])
    report = WhaleIntelligence().analyze(materialize_evidence(cand, now=NOW))
    assert report.label == "ACCUMULATING"
    assert report.smart_money is not None
    assert report.smart_money.label == "ACCUMULATING"
    assert report.smart_money.classifications


def test_insider_distribution_is_a_risk():
    cand = _cand(wallet_events=[
        {"address": "IN1", "side": "SELL", "usd": 9000.0, "label": "INSIDER"},
    ])
    report = SmartMoneyDetector().analyze(materialize_evidence(cand, now=NOW))
    assert report.label == "DISTRIBUTING"
    assert any(f.risk_id == "INSIDER_DISTRIBUTION" for f in report.findings)


def test_wallet_classification_rules():
    cand = _cand(wallet_events=[
        {"address": "U1", "side": "BUY", "usd": 25000.0},   # unlabeled large → WHALE
        {"address": "U2", "side": "BUY", "usd": 100.0, "label": "RETAIL"},
    ])
    report = SmartMoneyDetector().analyze(materialize_evidence(cand, now=NOW))
    assert report.classifications["U1"] == "WHALE"
    assert report.classifications["U2"] == "RETAIL"


def test_trap_when_accumulating_into_a_pump():
    cand = _cand(
        metrics=MarketMetrics(
            liquidity_usd=80000.0, volume_1h=20000.0, price_change_1h=0.40,
        ),
        wallet_events=[{"address": "W1", "side": "BUY", "usd": 18000.0, "label": "WHALE"}],
    )
    report = WhaleIntelligence().analyze(materialize_evidence(cand, now=NOW))
    assert report.has("WHALE_TRAP")


def test_intelligence_engine_exposes_whale_features_and_score_path():
    cand = _cand(wallet_events=[
        {"address": "W1", "side": "SELL", "usd": 22000.0, "label": "WHALE"},
    ])
    intel = IntelligenceEngine().evaluate(materialize_evidence(cand, now=NOW))
    assert intel.whales is not None
    assert intel.whales.label == "DISTRIBUTING"
    assert intel.features.get("whale_regime") is not None
    assert intel.features.get("whale_flow") is not None
    assert intel.risk.has("LARGE_WALLET_OUTFLOW")
    # 0-point whale features must not inflate the historic floor
    assert intel.features.get("whale_regime").points == 0.0


def test_no_double_count_with_high_concentration():
    cand = _cand(security=SecuritySignals(
        is_honeypot=False, top10_holder_concentration_pct=88.0,
    ))
    intel = IntelligenceEngine().evaluate(materialize_evidence(cand, now=NOW))
    conc = [f for f in intel.risk.findings if f.risk_id == "HIGH_HOLDER_CONCENTRATION"]
    assert len(conc) == 1
    assert intel.whales is not None
    assert intel.whales.label == "DANGEROUS"
