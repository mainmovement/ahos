#!/usr/bin/env python3
"""Tests for AHOS Health Manager & Self-Repair Diagnostic System."""
import sys, json, sqlite3
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from engine.health_manager import AHOSHealthManager, DiagnosticIssue


def test_health_manager_runs_clean():
    manager = AHOSHealthManager()
    rep = manager.run_full_diagnostics()
    assert rep.overall_status in ("GREEN", "YELLOW")
    assert rep.system_metrics["databases_checked"] >= 4
    assert rep.system_metrics["files_checked"] >= 7


def test_health_manager_export_report(tmp_path):
    manager = AHOSHealthManager()
    out_json = tmp_path / "health_report.json"
    manager.export_health_report(out_json)
    assert out_json.exists()
    data = json.loads(out_json.read_text())
    assert data["overall_status"] in ("GREEN", "YELLOW")
    assert "timestamp_utc" in data


def test_health_manager_no_repair_without_confirmation():
    manager = AHOSHealthManager()
    # Attempt repair without confirmation -> must abort by governance law
    res = manager.execute_repairs(confirmed=False)
    assert "REPAIR ABORTED" in res[0]
