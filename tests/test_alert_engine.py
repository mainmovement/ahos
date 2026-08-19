#!/usr/bin/env python3
"""Tests for Alert Engine & Scheduler & Security Observability."""
import sys, time
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from architecture.alerts.engine import AlertEngine
from architecture.scoring.engine import OpportunityScorer
from architecture.providers.contracts import NormalizedTokenCandidate, MarketMetrics, SecuritySignals
from architecture.scheduling.engine import ProductionScheduler, ScheduleTask
from architecture.security import sanitize_secrets, sanitize_dict, assert_safe_environment
from architecture.observability import Tracer


# ---------------- Alert Engine Tests ----------------
def test_alert_engine_opportunity_trigger():
    cand = NormalizedTokenCandidate(
        chain="solana",
        address="AlertSolanaTok11111111111111111111111111111",
        symbol="ALRT",
        name="Alert Token",
        metrics=MarketMetrics(
            price_usd=1.0,
            liquidity_usd=80000.0,
            volume_1h=40000.0,
            # Was `volume_velocity=3.5`, a field production never sets.
            # 10,000 in five minutes against a 40,000 hour is 3x the per-5m rate.
            volume_5m=10000.0,
            txns_1h_buys=80,
            txns_1h_sells=20,
            txns_5m_buys=20,
            txns_5m_sells=5
        ),
        security=SecuritySignals(
            is_honeypot=False,
            is_contract_verified=True,
            is_ownership_renounced=True
        ),
        source_provider="dexscreener",
        retrieved_ts=time.time()
    )
    scorer = OpportunityScorer()
    rep = scorer.evaluate(cand)
    engine = AlertEngine(score_threshold=70.0)
    alerts = engine.evaluate_opportunity(rep, cand)

    assert any(a.cls == "OPPORTUNITY" for a in alerts)
    assert any(a.cls == "ABNORMAL_MOVEMENT" for a in alerts)
    for a in alerts:
        assert len(a.reasons) >= 1
        assert len(a.evidence) >= 1


# ---------------- Production Scheduler Tests ----------------
def test_production_scheduler_cycle(tmp_path):
    db_path = tmp_path / "test_sched.sqlite"
    scheduler = ProductionScheduler(str(db_path))

    executed = []
    task1 = ScheduleTask("t1", 900.0, 300.0, lambda: executed.append("t1"), "Snapshot 15m")
    task2 = ScheduleTask("t2", 3600.0, 600.0, lambda: executed.append("t2"), "Snapshot 1h")

    res = scheduler.execute_scheduled_cycle("OBSERVE_CYCLE", [task1, task2])
    assert res["status"] == "SUCCESS"
    assert res["tasks_executed"] == 2
    assert executed == ["t1", "t2"]


# ---------------- Security & Observability Tests ----------------
def test_secret_sanitization():
    raw_log = "Error connecting to bot with token 123456789:ABCdefGHIjklMNOpqrsTUVwxyz1234567 and key sk-1234567890abcdef1234567890abcdef"
    clean = sanitize_secrets(raw_log)
    assert "123456789:ABCdef" not in clean
    assert "sk-1234567890" not in clean
    assert "[REDACTED_SECRET]" in clean


def test_tracer_provenance_and_latency():
    tracer = Tracer("scoring_engine", version="1.0")
    ctx = tracer.trace_operation("evaluate", {"token": "SOL_ABC"})
    time.sleep(0.01)
    trace = ctx.success({"score": 85.0})

    assert trace.status == "OK"
    assert trace.duration_ms > 0
    assert trace.input_provenance != ""
    assert trace.output_provenance != ""
    assert "run_id" in trace.to_json()


def test_safe_environment_assertion():
    audit = assert_safe_environment()
    assert audit["paper_only_enforced"] is True
    assert audit["zero_real_trading"] is True


# ============ the alert class that was dead in production (Wave-33e) --

def _spike_candidate(volume_5m: float, txns_5m: int, volume_1h: float = 90_000.0,
                     txns_1h: int = 900):
    """A candidate built ONLY from fields the adapters actually populate."""
    return NormalizedTokenCandidate(
        chain="solana",
        address="AlertSolanaTok11111111111111111111111111111",
        symbol="SPIKE", name="Spike",
        source_provider="dexscreener", retrieved_ts=time.time(),
        metrics=MarketMetrics(
            price_usd=0.01, liquidity_usd=250_000.0,
            volume_5m=volume_5m, volume_1h=volume_1h, volume_24h=1_500_000.0,
            txns_1h_buys=txns_1h // 2, txns_1h_sells=txns_1h // 2,
            txns_5m_buys=txns_5m // 2, txns_5m_sells=txns_5m // 2,
        ),
        security=SecuritySignals(is_honeypot=False, is_contract_verified=True,
                                 is_ownership_renounced=True),
    )


def _movement_alerts(cand):
    rep = OpportunityScorer().evaluate(cand)
    return [a for a in AlertEngine(score_threshold=70.0).evaluate_opportunity(rep, cand)
            if a.cls == "ABNORMAL_MOVEMENT"]


def test_abnormal_movement_fires_on_fields_production_actually_sets():
    """The rule keyed on `volume_velocity`, which no adapter ever populated.

    It was therefore always None, and the entire ABNORMAL_MOVEMENT class was
    dead code: a token doing 90k in five minutes against 200k for the whole
    day raised nothing. Three test fixtures hand-set the field, so the suite
    was green the whole time.
    """
    # 37,500 in 5m against a 90,000 hour is 5x the per-5m baseline.
    assert _movement_alerts(_spike_candidate(volume_5m=37_500.0, txns_5m=375))


def test_a_flat_market_raises_no_movement_alert():
    # 7,500 in 5m against a 90,000 hour is exactly the baseline rate.
    assert not _movement_alerts(_spike_candidate(volume_5m=7_500.0, txns_5m=75))


def test_manufactured_volume_is_not_reported_as_interest():
    """Volume outrunning transaction count is wash trading, not attention.

    Reporting "12x volume spike!" without that caveat would hand the user a
    manufactured number as though it were a discovery.
    """
    alerts = _movement_alerts(_spike_candidate(volume_5m=90_000.0, txns_5m=75))
    assert alerts
    alert = alerts[0]
    assert alert.severity == "HIGH"
    assert any("صوری" in r for r in alert.reasons)


def test_a_genuine_spike_is_not_labelled_wash_trading():
    """Volume and trade count rising together is real attention."""
    alerts = _movement_alerts(_spike_candidate(volume_5m=37_500.0, txns_5m=375))
    assert alerts[0].severity == "MED"
    assert not any("صوری" in r for r in alerts[0].reasons)


def test_the_never_populated_field_is_gone_from_the_contract():
    """Keeping it invites the same bug: a rule keyed to a field nobody fills."""
    import dataclasses
    names = {f.name for f in dataclasses.fields(MarketMetrics)}
    assert "volume_velocity" not in names


def test_alert_acceleration_matches_the_virality_analyzer():
    """Two derivations of one quantity drift apart; there must be only one."""
    from architecture.intel.viral import ViralityTracker
    from architecture.alerts.engine import _volume_acceleration
    cand = _spike_candidate(volume_5m=37_500.0, txns_5m=375)
    signal = ViralityTracker().analyze(cand)
    assert _volume_acceleration(cand.metrics) == pytest.approx(
        signal.volume_acceleration)
