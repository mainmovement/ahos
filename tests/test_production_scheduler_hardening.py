#!/usr/bin/env python3
"""Tests for Production Scheduler Hardening & Downtime Recovery (Phase XX)."""
import sys, time, sqlite3
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from architecture.scheduling.engine import (
    ProductionScheduler, ScheduleTask, SNAPSHOT_SCHEDULE
)


@pytest.fixture
def scheduler(tmp_path):
    local_db = tmp_path / "local.sqlite"
    discovery_db = tmp_path / "discovery.sqlite"

    # Setup discovery schema for missed window tests
    conn = sqlite3.connect(str(discovery_db))
    conn.execute("""
        CREATE TABLE observation_state (
            token_id TEXT PRIMARY KEY,
            state TEXT NOT NULL,
            first_seen_ts REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE discovery_observations (
            token_id TEXT NOT NULL,
            retrieved_ts REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE gap_register (
            token_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            expected_ts REAL,
            noted_ts REAL,
            detail TEXT
        )
    """)
    conn.commit()
    conn.close()

    return ProductionScheduler(db_path=str(local_db), discovery_db_path=str(discovery_db))


def test_scheduler_atomic_lease_concurrency(scheduler):
    now = 1000.0
    # Process 1 acquires lease
    assert scheduler.acquire_lease("OBS_LOCK", "run_A", now) is True

    # Process 2 attempts concurrent acquisition within lease window -> REFUSED
    assert scheduler.acquire_lease("OBS_LOCK", "run_B", now + 10.0) is False

    # Process 1 releases lease
    scheduler.release_lease("OBS_LOCK", "run_A")

    # Process 2 can now acquire lease
    assert scheduler.acquire_lease("OBS_LOCK", "run_B", now + 20.0) is True


def test_scheduler_lease_auto_expiration(scheduler):
    now = 1000.0
    scheduler.lease_duration_sec = 60.0
    assert scheduler.acquire_lease("OBS_LOCK", "run_A", now) is True

    # After 65 seconds (lease expired) -> Process 2 takes over
    assert scheduler.acquire_lease("OBS_LOCK", "run_B", now + 65.0) is True


def test_scheduler_heartbeat_and_downtime_detection(scheduler):
    now = 1000.0
    # Initial heartbeat
    d0 = scheduler.record_heartbeat("worker_1", now=now)
    assert d0 == 0.0

    # Next run after 500s of downtime
    d1 = scheduler.record_heartbeat("worker_1", now=now + 500.0)
    assert d1 == 500.0


def test_scheduler_missed_window_honest_registration(scheduler):
    t0 = 1000.0
    now = t0 + 7200.0  # 2 hours later (s+15m and s+1h have passed and are overdue)

    conn = sqlite3.connect(scheduler.discovery_db_path)
    conn.execute("INSERT INTO observation_state VALUES ('tok_test', 'OBSERVING', ?)", (t0,))
    conn.commit()
    conn.close()

    missed = scheduler.audit_and_register_missed_windows(now=now)
    assert "s+15m" in missed
    assert "s+1h" in missed

    # Verify rows in gap_register
    conn = sqlite3.connect(scheduler.discovery_db_path)
    gaps = conn.execute("SELECT kind FROM gap_register WHERE token_id='tok_test'").fetchall()
    kinds = [g[0] for g in gaps]
    assert "missed:s+15m" in kinds
    assert "missed:s+1h" in kinds
    conn.close()

    # Re-running does not duplicate gaps (idempotency)
    missed2 = scheduler.audit_and_register_missed_windows(now=now)
    assert missed2 == {}


def test_scheduler_drift_abort(scheduler):
    scheduler.check_clock_drift = lambda: 10.0  # Mock 10s drift (>5s safety limit)
    res = scheduler.execute_scheduled_cycle("DRIFT_CYCLE", [ScheduleTask("t", 100, 10, lambda: None, "Task")])
    assert res["status"] == "ABORTED_DRIFT"
    assert "exceeds safety threshold" in res["reason"]
