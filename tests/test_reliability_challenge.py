#!/usr/bin/env python3
"""Reliability challenge report schema + required challenge coverage."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import reliability_challenge as rc  # noqa: E402


REQUIRED_NAMES = {
    "process_kill_recovery",
    "database_interruption_recovery",
    "provider_outage_visibility",
    "clock_anomaly_handling",
    "duplicate_event_protection",
    "missing_heartbeat_behavior",
    "backup_restore_correctness",
}


def test_required_challenge_set_is_complete():
    names = {s["challenge"] for s in rc.REQUIRED}
    assert names == REQUIRED_NAMES


def test_run_challenge_all_required_pass(tmp_path):
    report = rc.run_challenge(workdir=tmp_path)
    assert report["schema"] == rc.SCHEMA
    assert report["result"] == "PASS", report["challenges"]
    assert report["exit_code"] == 0
    assert report["failed"] == 0
    assert {c["challenge"] for c in report["challenges"]} == REQUIRED_NAMES
    assert all(c["verdict"] == "PASS" for c in report["challenges"])
    assert report["git"]["commit_sha"]
    assert report["environment"]["fingerprint_sha256"]
    stamped, stable = rc.write_reports(report, tmp_path / "reports")
    loaded = json.loads(stable.read_text(encoding="utf-8"))
    assert loaded["passed"] == 7
    assert stamped.exists()
