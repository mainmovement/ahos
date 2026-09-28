#!/usr/bin/env python3
"""M-GAP-010 regression: SQLite backup/restore must be verifiable.

Pins the drill: source → backup → restore preserves row counts and
integrity_check=ok; missing sources fail closed; a tampered restore is FAIL.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import sqlite_backup_restore as brr  # noqa: E402


def test_backup_restore_preserves_row_counts_and_integrity(tmp_path):
    source = tmp_path / "source.sqlite"
    brr.build_synthetic_source(source)
    result = brr.drill_one(
        source,
        tmp_path / "backup.sqlite",
        tmp_path / "restored.sqlite",
    )
    assert result["verdict"] == "PASS", result["failures"]
    assert result["source"]["integrity_check"] == "ok"
    assert result["backup"]["integrity_check"] == "ok"
    assert result["restored"]["integrity_check"] == "ok"
    assert result["source"]["row_counts"] == {
        "drill_events": 3,
        "drill_meta": 2,
    }
    assert result["source"]["row_counts"] == result["restored"]["row_counts"]
    assert result["source"]["sha256"]
    assert result["backup"]["sha256"]
    assert result["restored"]["sha256"]


def test_missing_source_fails_closed(tmp_path):
    result = brr.drill_one(
        tmp_path / "absent.sqlite",
        tmp_path / "backup.sqlite",
        tmp_path / "restored.sqlite",
    )
    assert result["verdict"] == "FAIL"
    assert result["source"]["exists"] is False
    assert any("missing" in f for f in result["failures"])


def test_row_count_mismatch_is_fail(tmp_path):
    source = tmp_path / "source.sqlite"
    brr.build_synthetic_source(source)
    backup = tmp_path / "backup.sqlite"
    restored = tmp_path / "restored.sqlite"
    brr.copy_sqlite(source, backup)
    brr.copy_sqlite(backup, restored)
    conn = sqlite3.connect(str(restored))
    conn.execute("DELETE FROM drill_events WHERE id = 3")
    conn.commit()
    conn.close()
    failures = brr.verify_restore(brr.inspect(source, "source"), brr.inspect(restored, "restored"))
    assert failures, "tampered restore must not verify"
    assert any("row_count mismatch" in f for f in failures)


def test_run_drill_synthetic_writes_hashes_and_counts(tmp_path):
    report = brr.run_drill(tmp_path / "work", include_ahos_stores=False)
    dest = tmp_path / "evidence.json"
    brr.write_report(report, dest)
    loaded = json.loads(dest.read_text(encoding="utf-8"))
    assert loaded["schema"] == brr.SCHEMA_VERSION
    assert loaded["verdict"] == "PASS"
    assert loaded["failed"] == 0
    assert loaded["store_count"] == 1
    store = loaded["stores"][0]
    for role in ("source", "backup", "restored"):
        assert store[role]["sha256"]
        assert store[role]["integrity_check"] == "ok"
        assert store[role]["row_counts"]["drill_events"] == 3
    assert "git" in loaded and "commit_sha" in loaded["git"]
    assert loaded["timestamp_utc"]
    assert loaded["unproven"], "residual host-level unknowns must stay explicit"


def test_record_test_run_parses_pytest_summary():
    from scripts.record_test_run import parse_pytest_summary

    parsed = parse_pytest_summary(".................\n10 passed in 1.23s\n")
    assert parsed is not None
    assert parsed["passed"] == 10
    assert parse_pytest_summary("no summary here\n") is None


def test_record_test_run_default_timeout_scales_for_pytest():
    # The full suite runs ~1h; the blanket default was half that, so recording
    # `pytest tests/` as soak evidence would have timed out and been written
    # down as a FAIL. The default must scale for pytest-class commands.
    from scripts.record_test_run import default_timeout

    assert default_timeout(["python", "-m", "pytest", "tests/", "-q"]) > 3600
    assert default_timeout(["python", "scripts/validate_imports.py"]) == 1800
    assert default_timeout(["python", "scripts/soak_snapshot.py", "--window-hours", "6"]) == 1800


def test_record_test_run_anchors_relative_executable():
    # Windows CreateProcess does not search the cwd= parameter for the
    # executable, so the relative venv path the soak protocol and the Windows
    # operator runbook both document dies with WinError 2. It must be anchored
    # against ROOT. A bare name is left for PATH resolution.
    from scripts.record_test_run import _resolve_command

    rel = _resolve_command([".venv/Scripts/python.exe", "scripts/validate_imports.py"])
    assert rel[0].endswith(("python.exe", "python"))
    assert os.path.isabs(rel[0]), "a documented relative invocation must resolve to an absolute path"
    assert rel[1] == "scripts/validate_imports.py"

    # bare names go to PATH, not ROOT
    assert _resolve_command(["python3", "-m", "pytest"]) == ["python3", "-m", "pytest"]
    assert _resolve_command([]) == []


def test_record_test_run_records_launch_failure_instead_of_crashing():
    # A recorder that crashes records nothing. A launch failure is evidence.
    from scripts.record_test_run import record_run

    artifact = record_run(
        ["definitely_not_a_real_executable_xyz.py", "--help"],
        Path(tempfile.gettempdir()) / f"ahos_launch_fail_{os.getpid()}.json",
        timeout=30,
    )
    assert artifact["exit_code"] == 127
    assert artifact["verdict"] == "FAIL"
    assert "LAUNCH FAILED" in artifact["stderr"]


def test_record_test_run_refuses_to_overwrite_existing_artifact(tmp_path):
    # Evidence is append-only: AHOS_LOCAL_SOAK_PROTOCOL.md commits reports/ and
    # never overwrites. A reused --out would silently destroy a prior receipt,
    # which is exactly how a historical run gets lost. Refuse unless --force.
    from scripts.record_test_run import main

    existing = tmp_path / "prior_run.json"
    existing.write_text('{"schema": "ahos.test_run.v1", "timestamp_utc": "2026-08-20T12:15:06Z"}',
                        encoding="utf-8")

    argv = ["--out", str(existing), "--", sys.executable, "-c", "print('new')"]
    rc = main(argv)
    assert rc == 3, "an existing artifact must not be overwritten without --force"
    # the prior receipt must be byte-identical
    assert '"timestamp_utc": "2026-08-20T12:15:06Z"' in existing.read_text(encoding="utf-8")


def test_record_test_run_force_overrides_the_guard(tmp_path):
    from scripts.record_test_run import main

    existing = tmp_path / "prior_run.json"
    existing.write_text("stale", encoding="utf-8")

    rc = main(["--out", str(existing), "--force", "--", sys.executable, "-c", "print('new')"])
    assert rc == 0
    assert "stale" not in existing.read_text(encoding="utf-8")

