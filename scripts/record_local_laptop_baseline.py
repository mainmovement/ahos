#!/usr/bin/env python3
"""Create the eligibility artifact for the official Windows-laptop soak.

Run this only on the Windows laptop after installing dependencies, initializing
all local databases, and verifying the repository. The command is read-only
except for writing ``reports/local_laptop_baseline.json``. Arena/sandbox runs
must never become eligible for the official 168-hour clock.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.paths import (  # noqa: E402
    get_data_dir,
    get_discovery_db_path,
    get_knowledge_db_path,
    get_local_db_path,
    get_paper_trading_db_path,
)
from scripts.evidence_common import environment_fingerprint, git_meta, utc_now  # noqa: E402
from scripts.freeze_lane_a import verify as lane_a_verify  # noqa: E402
from scripts.sqlite_backup_restore import integrity_check  # noqa: E402

SCHEMA = "ahos.local_laptop_baseline.v1"
DESTINATION = ROOT / "reports" / "local_laptop_baseline.json"
_FORBIDDEN_EXECUTION_FLAGS = ("AHOS_EXECUTE_LIVE_TRADES", "AHOS_ALLOW_REAL_FUNDS")
_TRUTHY = {"1", "true", "yes", "on"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _enabled_env(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in _TRUTHY


def build() -> dict:
    """Build a baseline report without writing it."""
    git = git_meta()
    drift, missing, untracked = lane_a_verify()
    stores = {
        "e01_discovery": Path(get_discovery_db_path()),
        "paper_trading": Path(get_paper_trading_db_path()),
        "ahos_local": Path(get_local_db_path()),
        "ahos_knowledge": Path(get_knowledge_db_path()),
    }
    integrity = {name: integrity_check(path) for name, path in stores.items()}
    execution_flags = {name: os.environ.get(name) for name in _FORBIDDEN_EXECUTION_FLAGS}

    checks = {
        "windows_host": platform.system() == "Windows",
        "python_3_11_or_newer": sys.version_info >= (3, 11),
        "working_tree_clean_before_artifact": git.get("working_tree_clean") is True,
        "lane_a_intact": not drift and not missing and not untracked,
        "all_databases_integrity_ok": all(value == "ok" for value in integrity.values()),
        "execution_flags_disabled": not any(_enabled_env(name) for name in _FORBIDDEN_EXECUTION_FLAGS),
    }

    return {
        "schema": SCHEMA,
        "timestamp_utc": utc_now(),
        "git": git,
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "python": {
            "version": sys.version.split()[0],
            "executable": sys.executable,
        },
        "environment": environment_fingerprint(),
        "dependency_hash": {
            "requirements_txt_sha256": _sha256(ROOT / "requirements.txt"),
            "lane_a_freeze_sha256": _sha256(ROOT / "config" / "lane_a_freeze.sha256"),
        },
        "lane_a": {
            "ok": checks["lane_a_intact"],
            "drift": drift,
            "missing": missing,
            "untracked": untracked,
        },
        "databases": {
            "data_dir": str(get_data_dir()),
            "paths": {name: str(path) for name, path in stores.items()},
            "integrity": integrity,
        },
        "safety": {
            "execution_environment": execution_flags,
            "execution_flags_disabled": checks["execution_flags_disabled"],
            "mode": "observation-only",
        },
        "checks": checks,
        "daemon_command": [
            sys.executable,
            "-m",
            "architecture.runtime",
            "--daemon",
            "--interval-sec",
            "60",
            "--observation-cycle",
        ],
        "official_168h_eligible": all(checks.values()),
        "note": (
            "Eligibility requires Windows, Python 3.11+, a clean tree before this artifact, "
            "Lane-A integrity, four healthy local databases, and disabled execution flags. "
            "A sandbox run must remain ineligible."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    # Phase 14 audit finding: this entrypoint previously ignored argv entirely,
    # so `--help` (the first thing an operator types) skipped straight to
    # building and OVERWROTE reports/local_laptop_baseline.json. Asking a tool
    # what it does must never mutate evidence.
    parser = argparse.ArgumentParser(
        description="Record the Windows-laptop eligibility baseline for the "
                    "official 168-hour soak. Writes "
                    "reports/local_laptop_baseline.json and exits 2 when the "
                    "host is not eligible.")
    parser.parse_args(argv)

    report = build()
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    DESTINATION.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "artifact": str(DESTINATION),
        "commit_sha": report["git"]["commit_sha"],
        "working_tree_clean": report["git"]["working_tree_clean"],
        "os": report["os"]["system"],
        "lane_a_ok": report["lane_a"]["ok"],
        "database_integrity": report["databases"]["integrity"],
        "official_168h_eligible": report["official_168h_eligible"],
        "failed_checks": [name for name, passed in report["checks"].items() if not passed],
    }, indent=2))
    if not report["official_168h_eligible"]:
        print("STOP: baseline is not eligible; do not start the official 168h clock.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
