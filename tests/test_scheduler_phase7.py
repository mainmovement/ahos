#!/usr/bin/env python3
"""Phase 7 scheduler hardening tests: real clock-drift measurement + heartbeat watchdog.

Covers audit-v2 gaps B (drift stub) and C (silent-death detection).
"""
import sys
import time as _real_time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest

from architecture.scheduling import engine as sched_engine
from architecture.scheduling.engine import ProductionScheduler, ScheduleTask
from architecture.scheduling import watchdog


class _FakeTime:
    """Replaces the `time` module inside the engine: wall clock stepped, monotonic real."""

    def __init__(self, wall_offset_sec: float):
        self._wall_offset = wall_offset_sec

    def time(self) -> float:
        return _real_time.time() + self._wall_offset

    def monotonic(self) -> float:
        return _real_time.monotonic()


@pytest.fixture
def scheduler(tmp_path):
    return ProductionScheduler(
        db_path=str(tmp_path / "local.sqlite"),
        discovery_db_path=str(tmp_path / "discovery.sqlite"),
    )


# ---------------- clock drift (real measurement, replaces former stub) ---------

def test_drift_zero_when_clock_steady(scheduler):
    """No wall-clock step since construction -> drift is a tiny fraction of a second."""
    assert scheduler.check_clock_drift() < 1.0


def test_drift_detects_wall_clock_step(scheduler, monkeypatch):
    """A +600s wall-clock jump (NTP correction / VM resume) must be measured."""
    monkeypatch.setattr(sched_engine, "time", _FakeTime(wall_offset_sec=600.0))
    drift = scheduler.check_clock_drift()
    assert 595.0 < drift < 605.0


def test_drift_detects_backwards_clock_step(scheduler, monkeypatch):
    monkeypatch.setattr(sched_engine, "time", _FakeTime(wall_offset_sec=-3600.0))
    assert scheduler.check_clock_drift() > 3500.0


def test_drift_absurd_wall_clock_fails_closed(scheduler, monkeypatch):
    """Pre-2023 wall clock is treated as broken (9999s drift), never trusted."""
    class _BrokenClock(_FakeTime):
        def time(self) -> float:
            return 1_600_000_000.0

    monkeypatch.setattr(sched_engine, "time", _BrokenClock(0.0))
    assert scheduler.check_clock_drift() == 9999.0


def test_cycle_aborts_on_measured_drift(scheduler, monkeypatch):
    """execute_scheduled_cycle must abort when real drift exceeds the threshold."""
    monkeypatch.setattr(sched_engine, "time", _FakeTime(wall_offset_sec=600.0))
    result = scheduler.execute_scheduled_cycle("drifted_cycle", [])
    assert result["status"] == "ABORTED_DRIFT"
    assert result["clock_drift_sec"] > scheduler.max_allowed_clock_drift_sec


def test_cycle_runs_when_clock_steady(scheduler):
    """Steady clock -> cycle executes (and passes the drift gate it previously stubbed)."""
    ran = []
    task = ScheduleTask(task_id="t1", target_offset_sec=0, tolerance_sec=1,
                        action_fn=lambda: ran.append(1), label="tick")
    result = scheduler.execute_scheduled_cycle("steady_cycle", [task])
    assert result["status"] in ("SUCCESS", "PARTIAL_FAILURE")
    assert ran == [1]


# ---------------- heartbeat watchdog (silent-death detection) -------------------

def test_watchdog_ok_on_fresh_heartbeat(scheduler, tmp_path):
    t0 = 1_755_000_000.0
    scheduler.record_heartbeat("main_scheduler", now=t0)
    report = watchdog.watchdog_report(str(tmp_path / "local.sqlite"), max_age_sec=300, now=t0 + 10)
    assert report["status"] == "OK"
    assert report["stale_components"] == []


def test_watchdog_flags_stale_component(scheduler, tmp_path):
    t0 = 1_755_000_000.0
    scheduler.record_heartbeat("main_scheduler", now=t0)
    report = watchdog.watchdog_report(str(tmp_path / "local.sqlite"), max_age_sec=300, now=t0 + 1000)
    assert report["status"] == "STALE"
    assert report["stale_components"][0]["component"] == "main_scheduler"
    assert report["stale_components"][0]["age_sec"] >= 999.0


def test_watchdog_no_heartbeat_fresh_or_dead(tmp_path):
    """Missing DB / never-recorded heartbeat is NOT reported as OK (fail-closed)."""
    missing = str(tmp_path / "does_not_exist.sqlite")
    assert watchdog.has_any_heartbeat(missing) is False
    report = watchdog.watchdog_report(missing, max_age_sec=300)
    assert report["status"] == "NO_HEARTBEATS"


def test_watchdog_cli_exit_codes(scheduler, tmp_path, capsys):
    db = str(tmp_path / "local.sqlite")
    # Beat recorded 100s ago (deterministic relative to wall clock)
    scheduler.record_heartbeat("main_scheduler", now=_real_time.time() - 100.0)
    # 300s budget -> fresh -> exit 0
    assert watchdog.main(["--status", "--db-path", db, "--max-age-sec", "300"]) == 0
    # 50s budget -> 100s-old beat is stale -> exit 2
    assert watchdog.main(["--status", "--db-path", db, "--max-age-sec", "50"]) == 2


def test_watchdog_cli_json_emits_report(scheduler, tmp_path, capsys):
    db = str(tmp_path / "local.sqlite")
    scheduler.record_heartbeat("main_scheduler", now=_real_time.time())
    code = watchdog.main(["--status", "--db-path", db, "--json"])
    out = capsys.readouterr().out
    assert code == 0
    assert '"status"' in out and '"OK"' in out
