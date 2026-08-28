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
            volume_velocity=3.5,
            txns_1h_buys=80,
            txns_1h_sells=20
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
    import os
    os.environ["AHOS_PAPER_ONLY"] = "1"
    audit = assert_safe_environment()
    assert audit["paper_only_enforced"] is True
    assert audit["zero_real_trading"] is True
    assert audit["live_trading_flags_absent"] is True
