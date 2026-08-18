#!/usr/bin/env python3
"""System-state snapshot must not invent operational success."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import system_state_snapshot as sss  # noqa: E402


def test_snapshot_schema_and_honest_missing_stores(monkeypatch, tmp_path):
    monkeypatch.setenv("AHOS_DATA_DIR", str(tmp_path / "empty_data"))
    report = sss.build_snapshot(probe_providers=False, window_hours=1.0)
    assert report["schema"] == sss.SCHEMA
    assert report["result"] == "RECORDED"
    assert "command" in report and report["git"]["commit_sha"]
    assert "environment" in report and report["environment"]["fingerprint_sha256"]
    assert report["watchdog"]["status"] == "NO_HEARTBEATS"
    for name, st in report["stores"].items():
        assert st["exists"] is False, name
        assert st["integrity_check"] == "NO_DATA"
    assert report["events"], "every snapshot must emit observation events"
    for ev in report["events"]:
        assert ev["timestamp_utc"]
        assert ev["commit_sha"]
        assert ev["event_type"]
        assert ev["severity"] in {"INFO", "WARN", "ERROR"}
        assert ev["evidence_path"]


def test_snapshot_write_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("AHOS_DATA_DIR", str(tmp_path / "empty_data"))
    dest = tmp_path / "system_state_snapshot.json"
    rc = sss.main(["--out", str(dest)])
    assert rc == 0
    loaded = json.loads(dest.read_text(encoding="utf-8"))
    assert loaded["result"] == "RECORDED"
    assert loaded["lane_a"]["ok"] is True
