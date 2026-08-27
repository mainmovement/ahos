#!/usr/bin/env python3
"""AHOS Cross-Platform Path & Environment Resolver (Windows / Linux / VPS / Docker).

Dynamically resolves all directory and database paths across platforms:
  - Windows: Resolves relative to Windows project root (e.g. C:\\Users\\...\\ahos)
  - Linux / Mac: Resolves relative to repository root
  - Docker / VPS: Resolves relative to /app or configured AHOS_ROOT
  - Eliminates all hardcoded /home/user/ahos paths.
"""
from __future__ import annotations

import os
import platform
import sys
from pathlib import Path
from typing import Literal

PlatformType = Literal["windows", "linux", "darwin", "docker", "vps"]


def detect_platform() -> PlatformType:
    """Detects current runtime operating platform."""
    if os.path.exists("/.dockerenv") or os.environ.get("AHOS_IN_DOCKER") == "1":
        return "docker"
    system = platform.system().lower()
    if system == "windows" or os.name == "nt":
        return "windows"
    elif system == "darwin":
        return "darwin"
    elif os.environ.get("AHOS_ENV") == "vps":
        return "vps"
    return "linux"


def get_project_root() -> Path:
    """Dynamically locates AHOS project root directory."""
    env_root = os.environ.get("AHOS_ROOT")
    if env_root and os.path.isdir(env_root):
        return Path(env_root).resolve()

    # Locate from current file location (config/paths.py -> parents[1] == repo root)
    current_file = Path(__file__).resolve()
    candidate = current_file.parents[1]
    if (candidate / "contracts").exists() or (candidate / "architecture").exists():
        return candidate

    # Fallback to current working directory
    cwd = Path.cwd().resolve()
    if (cwd / "contracts").exists() or (cwd / "architecture").exists():
        return cwd

    return candidate


# Core directory getters
def get_data_dir() -> Path:
    data_dir = os.environ.get("AHOS_DATA_DIR")
    if data_dir:
        p = Path(data_dir).resolve()
    else:
        p = get_project_root() / "data"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_db_path(db_name: str) -> str:
    """Returns absolute path string to a SQLite database file."""
    if not db_name.endswith(".sqlite") and not db_name.endswith(".db"):
        db_name = f"{db_name}.sqlite"
    return str(get_data_dir() / db_name)


def get_config_dir() -> Path:
    return get_project_root() / "config"


def get_reports_dir() -> Path:
    p = get_project_root() / "reports"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_docs_dir() -> Path:
    return get_project_root() / "docs"


def get_contracts_dir() -> Path:
    return get_project_root() / "contracts"


def get_n8n_workflows_dir() -> Path:
    return get_project_root() / "n8n" / "workflows"


def get_research_dir() -> Path:
    return get_project_root() / "research"


# Common canonical DB paths
def get_discovery_db_path() -> str:
    return get_db_path("e01_discovery.sqlite")


def get_paper_trading_db_path() -> str:
    return get_db_path("paper_trading.sqlite")


def get_local_db_path() -> str:
    return get_db_path("ahos_local.sqlite")


def get_knowledge_db_path() -> str:
    return get_db_path("ahos_knowledge.sqlite")


def sqlite_ro_uri(path: Path | str) -> str:
    """Build a SQLite read-only URI that works on Windows and POSIX.

    Naive ``file:{path}?mode=ro`` breaks on Windows because ``Path`` yields
    backslashes and a drive colon (``C:\\...``), which are illegal in SQLite
    URI paths. ``Path.as_uri()`` emits ``file:///C:/...`` which is valid.
    """
    p = Path(path).resolve()
    return f"{p.as_uri()}?mode=ro"


def connect_sqlite_ro(path: Path | str):
    """Open an existing SQLite DB read-only (never creates the file)."""
    import sqlite3

    return sqlite3.connect(sqlite_ro_uri(path), uri=True)


# Dump to YAML for reference
def export_paths_yaml(output_file: Path | str | None = None) -> str:
    import yaml
    root = get_project_root()
    plat = detect_platform()
    paths_dict = {
        "platform_detected": plat,
        "is_windows": plat == "windows",
        "project_root": str(root),
        "data_dir": str(get_data_dir()),
        "config_dir": str(get_config_dir()),
        "reports_dir": str(get_reports_dir()),
        "docs_dir": str(get_docs_dir()),
        "contracts_dir": str(get_contracts_dir()),
        "n8n_workflows_dir": str(get_n8n_workflows_dir()),
        "databases": {
            "discovery": get_discovery_db_path(),
            "paper_trading": get_paper_trading_db_path(),
            "local": get_local_db_path(),
            "knowledge": get_knowledge_db_path(),
        }
    }
    content = yaml.safe_dump(paths_dict, sort_keys=False)
    if output_file:
        Path(output_file).write_text(content)
    return content


if __name__ == "__main__":
    # Prefer reports/ so machine-absolute dumps are not confused with tracked config.
    # config/paths.yaml is gitignored (local diagnostic only).
    out_path = get_reports_dir() / "paths_local.yaml"
    export_paths_yaml(out_path)
    print(f"Exported paths configuration to: {out_path}")
