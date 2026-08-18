#!/usr/bin/env python3
"""M-GAP-010 regression: SQLite backup/restore must be verifiable.

Pins the drill: source → backup → restore preserves row counts and
integrity_check=ok; missing sources fail closed; a tampered restore is FAIL.
"""
from __future__ import annotations

import json
import sqlite3
import sys
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
