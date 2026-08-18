#!/usr/bin/env python3
"""Soak snapshot tool — verifies honest reporting on live and empty stores."""
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from architecture.scheduling.engine import ProductionScheduler  # noqa: E402
from scripts import soak_snapshot as snap  # noqa: E402


def test_snapshot_reports_real_runs(tmp_path):
    local = str(tmp_path / "local.sqlite")
    disc = str(tmp_path / "discovery.sqlite")
    s = ProductionScheduler(db_path=local, discovery_db_path=disc)
    t0 = time.time()
    s.execute_scheduled_cycle("SOAK_TEST", [], now=t0)
    s.record_heartbeat("main_scheduler", now=t0)

    out = snap.snapshot(local, disc, window_hours=1.0, now=t0 + 60.0)
    assert out["scheduler"]["runs_in_window"] == 1
    assert out["scheduler"]["status_counts"].get("SUCCESS") == 1
    assert out["scheduler"]["last_runs"][0]["duration_sec"] is not None
    assert out["scheduler"]["heartbeat_ages_sec"]["main_scheduler"] >= 60.0
    assert out["watchdog"]["status"] == "OK"
    assert out["integrity"]["local_db"] == "ok"


def test_snapshot_missing_stores_report_no_data_never_fabricated(tmp_path):
    out = snap.snapshot(str(tmp_path / "none1.sqlite"), str(tmp_path / "none2.sqlite"),
                        window_hours=1.0, now=time.time())
    assert out["scheduler"]["runs_in_window"] == 0
    assert out["watchdog"]["status"] == "NO_HEARTBEATS"
    assert out["observations"]["production_window_count"] == "NO_DATA"
    assert out["integrity"]["local_db"] == "NO_DATA"


def test_snapshot_stale_heartbeat_visible(tmp_path):
    local = str(tmp_path / "local.sqlite")
    disc = str(tmp_path / "discovery.sqlite")
    s = ProductionScheduler(db_path=local, discovery_db_path=disc)
    t0 = time.time() - 5000.0
    s.record_heartbeat("main_scheduler", now=t0)
    out = snap.snapshot(local, disc, window_hours=1.0)
    assert out["watchdog"]["status"] == "STALE"
    assert out["watchdog"]["stale_components"][0]["component"] == "main_scheduler"
