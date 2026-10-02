#!/usr/bin/env python3
"""Tests for Alert Engine & Scheduler & Security Observability."""
import sqlite3
import sys, time
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from architecture.alerts.engine import AlertEngine
from architecture.scoring.engine import OpportunityScorer
from architecture.providers.contracts import NormalizedTokenCandidate, MarketMetrics, SecuritySignals
from tests.helpers_security import OLD_POOL_TS, passing_security_signals
from tests.helpers_identity import verified_pool_identity_fixture
from architecture.scheduling.engine import ProductionScheduler, ScheduleTask, SNAPSHOT_SCHEDULE
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
        security=passing_security_signals(
            is_honeypot=False,
            is_contract_verified=True,
            is_ownership_renounced=True,
        ),
        source_provider="dexscreener",
        retrieved_ts=time.time(),
        pair_created_ts=OLD_POOL_TS,
    )
    scorer = OpportunityScorer()
    rep = scorer.evaluate(cand)
    engine = AlertEngine(score_threshold=70.0)
    alerts = engine.evaluate_opportunity(
        rep, cand, identity=verified_pool_identity_fixture(address=cand.address, symbol="ALRT"),
    )

    assert any(a.cls == "OPPORTUNITY" for a in alerts)
    assert any(a.cls == "ABNORMAL_MOVEMENT" for a in alerts)
    for a in alerts:
        assert len(a.reasons) >= 1
        assert len(a.evidence) >= 1


# ---------------- Production Scheduler Tests ----------------
def test_production_scheduler_cycle(tmp_path):
    # M9: discovery_db_path MUST be injected. Without it the scheduler audits
    # the real production discovery DB (3720 tokens x 8 snapshot slots of
    # unindexed dedup probes) and this "unit" test stalls until the harness
    # kills it. A test must never depend on production state.
    db_path = tmp_path / "test_sched.sqlite"
    disc_path = tmp_path / "test_discovery.sqlite"
    _con = sqlite3.connect(str(disc_path))
    _con.executescript(
        "CREATE TABLE IF NOT EXISTS observation_state "
        "(token_id TEXT PRIMARY KEY, state TEXT, first_seen_ts REAL);"
        "CREATE TABLE IF NOT EXISTS discovery_observations "
        "(token_id TEXT, retrieved_ts REAL);"
        "CREATE TABLE IF NOT EXISTS gap_register "
        "(id INTEGER PRIMARY KEY AUTOINCREMENT, token_id TEXT, kind TEXT,"
        " expected_ts REAL, noted_ts REAL, detail TEXT);"
    )
    _con.commit()
    _con.close()
    scheduler = ProductionScheduler(str(db_path), discovery_db_path=str(disc_path))

    executed = []
    task1 = ScheduleTask("t1", 900.0, 300.0, lambda: executed.append("t1"), "Snapshot 15m")
    task2 = ScheduleTask("t2", 3600.0, 600.0, lambda: executed.append("t2"), "Snapshot 1h")

    res = scheduler.execute_scheduled_cycle("OBSERVE_CYCLE", [task1, task2])
    assert res["status"] == "SUCCESS"
    assert res["tasks_executed"] == 2
    assert executed == ["t1", "t2"]


def test_audit_and_register_missed_windows_is_not_on2(tmp_path):
    """M9 regression: the dedup probe must stay O(rows) total, not per-slot.

    The original code ran one unindexed SELECT against gap_register for every
    (token, slot) pair. Against 3720 production tokens that was ~30k full table
    scans and the cycle never returned. This test seeds enough rows that the old
    code would take minutes and asserts the audit finishes fast and correct.
    """
    disc_path = tmp_path / "missed_discovery.sqlite"
    con = sqlite3.connect(str(disc_path))
    con.executescript(
        "CREATE TABLE observation_state "
        "(token_id TEXT PRIMARY KEY, state TEXT, first_seen_ts REAL);"
        "CREATE TABLE discovery_observations (token_id TEXT, retrieved_ts REAL);"
        "CREATE TABLE gap_register "
        "(id INTEGER PRIMARY KEY AUTOINCREMENT, token_id TEXT, kind TEXT,"
        " expected_ts REAL, noted_ts REAL, detail TEXT);"
    )
    # 200 tokens, all first-seen long ago so every snapshot slot is overdue,
    # and no observations -- every slot is a genuine missed window.
    long_ago = time.time() - 30 * 86400.0
    con.executemany(
        "INSERT INTO observation_state(token_id, state, first_seen_ts) VALUES (?,?,?)",
        [(f"tok{i:04d}", "OBSERVING", long_ago) for i in range(200)],
    )
    con.commit()
    con.close()

    scheduler = ProductionScheduler(
        str(tmp_path / "sched.sqlite"), discovery_db_path=str(disc_path)
    )

    start = time.monotonic()
    counts = scheduler.audit_and_register_missed_windows()
    elapsed = time.monotonic() - start

    # All 8 slots missed for all 200 tokens.
    assert sum(counts.values()) == 200 * len(SNAPSHOT_SCHEDULE), counts
    # The old code needed >60s for far fewer tokens; the fix is orders of
    # magnitude faster. Generous bound to stay resilient on a loaded CI box.
    assert elapsed < 10.0, f"audit took {elapsed:.1f}s -- dedup is O(n^2) again"

    # Idempotency: a second pass must not double-register.
    counts2 = scheduler.audit_and_register_missed_windows()
    assert sum(counts2.values()) == 0, f"second pass re-registered gaps: {counts2}"


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
