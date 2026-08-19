#!/usr/bin/env python3
"""Alerts, Governance Invariants, and WHY-Law Matrix Tests (Phase XXI)."""
import sys, time
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from architecture.alerts.engine import AlertEngine
from architecture.scoring.engine import OpportunityScorer, OpportunityScoreReport, InvalidationCondition
from architecture.providers.contracts import NormalizedTokenCandidate, MarketMetrics, SecuritySignals
from telegram_ai.alerts import build as build_alert, render_fa, ALERT_CLASSES, FOOTER


# ---------------- WHY-Law Invariant Tests ----------------
@pytest.mark.parametrize("alert_class", list(ALERT_CLASSES.keys()))
def test_all_alert_classes_enforce_why_and_evidence(alert_class):
    alert = build_alert(
        cls=alert_class,
        symbol="GOVTOK",
        reasons=["دلیل نمونه تست حاکمیت"],
        evidence=["prov:dexscreener", "score=80"],
        severity="MED"
    )
    assert alert.cls == alert_class
    assert len(alert.reasons) >= 1
    assert len(alert.evidence) >= 1

    fa_text = render_fa(alert)
    assert alert.symbol in fa_text
    assert "چرا:" in fa_text
    assert "شواهد:" in fa_text
    if ALERT_CLASSES[alert_class]["decisional"]:
        assert FOOTER in fa_text


def test_alert_engine_stale_data_warning():
    cand = NormalizedTokenCandidate(
        chain="solana",
        address="StaleAlertSolana111111111111111111111111",
        symbol="STALE",
        name="Stale Token",
        source_provider="dexscreener",
        retrieved_ts=time.time() - 5 * 3600,  # 5 hours old
        metrics=MarketMetrics(liquidity_usd=20000.0, volume_1h=5000.0)
    )
    scorer = OpportunityScorer()
    rep = scorer.evaluate(cand)
    engine = AlertEngine()
    alerts = engine.evaluate_opportunity(rep, cand)

    assert any(a.cls == "SITUATION_CHANGING" for a in alerts)
    assert any("قدیمی" in r for a in alerts for r in a.reasons)


def test_alert_engine_abnormal_movement_spike():
    cand = NormalizedTokenCandidate(
        chain="solana",
        address="VelocityAlertSolana111111111111111111111",
        symbol="VEL",
        name="Velocity Spike",
        source_provider="dexscreener",
        retrieved_ts=time.time(),
        metrics=MarketMetrics(
            liquidity_usd=50000.0,
            volume_1h=30000.0,
            volume_5m=12500.0,
            txns_1h_buys=300,
            txns_1h_sells=300,
            txns_5m_buys=125,
            txns_5m_sells=125,
        ),
        security=SecuritySignals(is_honeypot=False)
    )
    scorer = OpportunityScorer()
    rep = scorer.evaluate(cand)
    engine = AlertEngine(volume_spike_threshold=3.0)
    alerts = engine.evaluate_opportunity(rep, cand)

    assert any(a.cls == "ABNORMAL_MOVEMENT" for a in alerts)
    assert any("شتاب غیرعادی" in r for a in alerts for r in a.reasons)
