#!/usr/bin/env python3
"""Tests for the fail-closed Windows laptop baseline gate."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import record_local_laptop_baseline as baseline  # noqa: E402


def _eligible_dependencies(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        baseline,
        "git_meta",
        lambda: {"commit_sha": "a" * 40, "branch": "main", "working_tree_clean": True},
    )
    monkeypatch.setattr(baseline, "lane_a_verify", lambda: ([], [], []))
    monkeypatch.setattr(baseline, "integrity_check", lambda _path: "ok")
    monkeypatch.setattr(baseline, "get_data_dir", lambda: tmp_path)
    monkeypatch.setattr(baseline, "get_discovery_db_path", lambda: tmp_path / "discovery.sqlite")
    monkeypatch.setattr(baseline, "get_paper_trading_db_path", lambda: tmp_path / "paper.sqlite")
    monkeypatch.setattr(baseline, "get_local_db_path", lambda: tmp_path / "local.sqlite")
    monkeypatch.setattr(baseline, "get_knowledge_db_path", lambda: tmp_path / "knowledge.sqlite")
    for name in baseline._FORBIDDEN_EXECUTION_FLAGS:
        monkeypatch.delenv(name, raising=False)


def test_non_windows_host_is_never_official(monkeypatch, tmp_path):
    _eligible_dependencies(monkeypatch, tmp_path)
    monkeypatch.setattr(baseline.platform, "system", lambda: "Linux")

    report = baseline.build()

    assert report["schema"] == baseline.SCHEMA
    assert report["checks"]["windows_host"] is False
    assert report["official_168h_eligible"] is False
    assert "--observation-cycle" in report["daemon_command"]


def test_windows_healthy_clean_host_is_eligible(monkeypatch, tmp_path):
    _eligible_dependencies(monkeypatch, tmp_path)
    monkeypatch.setattr(baseline.platform, "system", lambda: "Windows")

    report = baseline.build()

    assert all(report["checks"].values())
    assert report["official_168h_eligible"] is True


def test_execution_flag_blocks_eligibility(monkeypatch, tmp_path):
    _eligible_dependencies(monkeypatch, tmp_path)
    monkeypatch.setattr(baseline.platform, "system", lambda: "Windows")
    monkeypatch.setenv("AHOS_EXECUTE_LIVE_TRADES", "1")

    report = baseline.build()

    assert report["checks"]["execution_flags_disabled"] is False
    assert report["official_168h_eligible"] is False


def test_missing_or_unhealthy_database_blocks_eligibility(monkeypatch, tmp_path):
    _eligible_dependencies(monkeypatch, tmp_path)
    monkeypatch.setattr(baseline.platform, "system", lambda: "Windows")
    monkeypatch.setattr(baseline, "integrity_check", lambda _path: "NO_DATA")

    report = baseline.build()

    assert report["checks"]["all_databases_integrity_ok"] is False
    assert report["official_168h_eligible"] is False
