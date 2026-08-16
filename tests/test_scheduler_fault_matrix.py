#!/usr/bin/env python3
"""Scheduler Fault Matrix & Boundary Tests (Phase XX)."""
import sys, time, sqlite3
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from architecture.scheduling.engine import ProductionScheduler, ScheduleTask, SNAPSHOT_SCHEDULE


@pytest.fixture
def scheduler(tmp_path):
    local_db = tmp_path / "local.sqlite"
    discovery_db = tmp_path / "discovery.sqlite"
    conn = sqlite3.connect(str(discovery_db))
    conn.execute("CREATE TABLE observation_state (token_id TEXT PRIMARY KEY, state TEXT, first_seen_ts REAL)")
    conn.execute("CREATE TABLE discovery_observations (token_id TEXT, retrieved_ts REAL)")
    conn.execute("CREATE TABLE gap_register (token_id TEXT, kind TEXT, expected_ts REAL, noted_ts REAL, detail TEXT)")
    conn.commit()
    conn.close()
    return ProductionScheduler(db_path=str(local_db), discovery_db_path=str(discovery_db))


def test_task_failure_isolation(scheduler):
    """One task throwing an unhandled exception must not abort remaining tasks in the cycle."""
    executed = []
    def _failing_task():
        raise RuntimeError("Task failed")

    t1 = ScheduleTask("t1", 100, 10, lambda: executed.append("t1"), "Task 1")
    t2 = ScheduleTask("t2", 100, 10, _failing_task, "Failing Task")
    t3 = ScheduleTask("t3", 100, 10, lambda: executed.append("t3"), "Task 3")

    res = scheduler.execute_scheduled_cycle("ISOLATION_TEST", [t1, t2, t3])
    assert res["status"] == "PARTIAL_FAILURE"
    assert res["tasks_executed"] == 2
    assert res["tasks_failed"] == 1
    assert executed == ["t1", "t3"]


@pytest.mark.parametrize("drift_sec,expected_status", [
    (0.0, "SUCCESS"),
    (2.5, "SUCCESS"),
    (4.99, "SUCCESS"),
    (5.01, "ABORTED_DRIFT"),
    (15.0, "ABORTED_DRIFT")
])
def test_clock_drift_boundaries(scheduler, drift_sec, expected_status):
    scheduler.check_clock_drift = lambda: drift_sec
    res = scheduler.execute_scheduled_cycle("DRIFT_BOUNDARY", [ScheduleTask("t", 100, 10, lambda: None, "T")])
    assert res["status"] == expected_status


@pytest.mark.parametrize("slot_label,slot_offset", [
    ("s+15m", 900.0),
    ("s+1h", 3600.0),
    ("s+4h", 14400.0),
    ("s+12h", 43200.0),
    ("s+24h", 86400.0),
    ("s+48h", 172800.0),
    ("s+72h", 259200.0),
])
def test_individual_slot_missed_window_detection(scheduler, slot_label, slot_offset):
    t0 = 1000.0
    now = t0 + slot_offset + 3600.0  # past window

    conn = sqlite3.connect(scheduler.discovery_db_path)
    conn.execute("INSERT INTO observation_state VALUES (?, 'OBSERVING', ?)", (f"tok_{slot_label}", t0))
    conn.commit()
    conn.close()

    missed = scheduler.audit_and_register_missed_windows(now=now)
    assert slot_label in missed
