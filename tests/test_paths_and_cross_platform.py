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
