#!/usr/bin/env python3
"""Tests for Cross-Platform Path & Environment Resolver (Windows/Linux/Docker)."""
import sys, os
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from config.paths import (
    detect_platform, get_project_root, get_data_dir, get_db_path,
    get_discovery_db_path, get_paper_trading_db_path, get_local_db_path,
    get_knowledge_db_path, export_paths_yaml
)


def test_sqlite_ro_uri_has_no_backslashes(tmp_path):
    """Windows-safe URI: Path.as_uri() form, never file:C:\\..."""
    from config.paths import sqlite_ro_uri, connect_sqlite_ro
    import sqlite3

    db = tmp_path / "win_uri.sqlite"
    sqlite3.connect(str(db)).close()
    uri = sqlite_ro_uri(db)
    assert uri.startswith("file:")
    assert "\\" not in uri
    assert uri.endswith("?mode=ro")
    conn = connect_sqlite_ro(db)
    assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    conn.close()


def test_naive_windows_style_uri_fails():
    """Document why connect_sqlite_ro exists: naive Windows paths break SQLite URI mode."""
    import sqlite3
    naive = r"file:C:\Users\operator\ahos\data\t.sqlite?mode=ro"
    try:
        sqlite3.connect(naive, uri=True)
        # Some platforms may not raise until execute; force a use.
        raise AssertionError("naive Windows URI unexpectedly connected")
    except sqlite3.Error:
        pass


def test_detect_platform():
    plat = detect_platform()
    assert plat in ("windows", "linux", "darwin", "docker", "vps")


def test_get_project_root_dynamic():
    root = get_project_root()
    assert root.exists()
    assert (root / "contracts").exists() or (root / "architecture").exists()


def test_get_db_paths_dynamic():
    assert get_discovery_db_path().endswith("e01_discovery.sqlite")
    assert get_paper_trading_db_path().endswith("paper_trading.sqlite")
    assert get_local_db_path().endswith("ahos_local.sqlite")
    assert get_knowledge_db_path().endswith("ahos_knowledge.sqlite")


def test_export_paths_yaml(tmp_path):
    out_yaml = tmp_path / "paths_test.yaml"
    content = export_paths_yaml(out_yaml)
    assert out_yaml.exists()
    assert "databases:" in content
    assert "project_root:" in content
