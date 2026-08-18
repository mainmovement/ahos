#!/usr/bin/env python3
"""Phase 8 failure-resilience challenge.

Reuses the existing Month-1 controlled-failure matrix and the SQLite backup
drill. Does not mock the system under test. Writes:

    reports/reliability_matrix_<timestamp>.json
    reports/reliability_matrix.json          (same payload, stable name)

Usage:
    python scripts/reliability_challenge.py
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.evidence_common import environment_fingerprint, git_meta, utc_now  # noqa: E402
from scripts import month1_failure_matrix as fm  # noqa: E402
from scripts import sqlite_backup_restore as brr  # noqa: E402

SCHEMA = "ahos.reliability_matrix.v1"

# Required Phase-8 challenges → existing matrix scenario names.
REQUIRED = [
    {
        "challenge": "process_kill_recovery",
        "source": "month1_failure_matrix",
        "scenario": "crashed_process_recovery",
    },
    {
        "challenge": "database_interruption_recovery",
        "source": "month1_failure_matrix",
        "scenario": "interrupted_write",
    },
    {
        "challenge": "provider_outage_visibility",
        "source": "month1_failure_matrix",
        "scenario": "collector_failure_durable_visible",
    },
    {
        "challenge": "clock_anomaly_handling",
        "source": "month1_failure_matrix",
        "scenario": "clock_step_forward_backward",
    },
    {
        "challenge": "duplicate_event_protection",
        "source": "month1_failure_matrix",
        "scenario": "duplicate_event_rejected",
    },
    {
        "challenge": "missing_heartbeat_behavior",
        "source": "month1_failure_matrix",
        "scenario": "watchdog_fail_closed",
    },
    {
        "challenge": "backup_restore_correctness",
        "source": "sqlite_backup_restore",
        "scenario": "drill",
    },
]


def _map_matrix(results: list[dict]) -> dict[str, dict]:
    return {r["scenario"]: r for r in results}


def run_challenge(workdir: Path | None = None) -> dict:
    own = workdir is None
    workdir = workdir or Path(tempfile.mkdtemp(prefix="ahos_reliability_"))
    matrix_dir = workdir / "matrix"
    matrix_dir.mkdir(parents=True, exist_ok=True)
    git = git_meta()
    started = utc_now()
    fm.RESULTS.clear()
    matrix = fm.run_all(workdir=matrix_dir)
    by_name = _map_matrix(matrix)
    drill = brr.run_drill(workdir / "backup", include_ahos_stores=False)

    challenges: list[dict] = []
    for spec in REQUIRED:
        if spec["source"] == "sqlite_backup_restore":
            challenges.append({
                "challenge": spec["challenge"],
                "source": spec["source"],
                "scenario": spec["scenario"],
                "verdict": drill["verdict"],
                "evidence": (
                    f"stores={drill['store_count']} passed={drill['passed']} "
                    f"failed={drill['failed']}"
                ),
            })
        else:
            row = by_name.get(spec["scenario"])
            if row is None:
                challenges.append({
                    "challenge": spec["challenge"],
                    "source": spec["source"],
                    "scenario": spec["scenario"],
                    "verdict": "FAIL",
                    "evidence": "scenario missing from matrix (matrix shrank)",
                })
            else:
                challenges.append({
                    "challenge": spec["challenge"],
                    "source": spec["source"],
                    "scenario": spec["scenario"],
                    "verdict": row["verdict"],
                    "evidence": row["evidence"],
                    "injected_fault": row.get("injected_fault"),
                    "expected_behavior": row.get("expected_behavior"),
                })

    failed = [c for c in challenges if c["verdict"] != "PASS"]
    report = {
        "schema": SCHEMA,
        "timestamp_utc": started,
        "finished_utc": utc_now(),
        "command": "python scripts/reliability_challenge.py",
        "git": git,
        "environment": environment_fingerprint(),
        "exit_code": 0 if not failed else 1,
        "result": "PASS" if not failed else "FAIL",
        "required_count": len(REQUIRED),
        "passed": sum(1 for c in challenges if c["verdict"] == "PASS"),
        "failed": len(failed),
        "challenges": challenges,
        "matrix_total": len(matrix),
        "matrix_passed": sum(1 for r in matrix if r["verdict"] == "PASS"),
        "backup_drill": {
            "verdict": drill["verdict"],
            "passed": drill["passed"],
            "failed": drill["failed"],
        },
        "note": "Faults injected at edges only. System under test is the real component.",
    }
    if own:
        import shutil
        shutil.rmtree(workdir, ignore_errors=True)
    return report


def write_reports(report: dict, reports_dir: Path) -> tuple[Path, Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    stamped = reports_dir / f"reliability_matrix_{report['timestamp_utc'].replace(':', '').replace('-', '')}.json"
    stable = reports_dir / "reliability_matrix.json"
    text = json.dumps(report, indent=2, default=str) + "\n"
    stamped.write_text(text, encoding="utf-8")
    stable.write_text(text, encoding="utf-8")
    return stamped, stable


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AHOS Phase-8 reliability challenge")
    ap.add_argument("--reports-dir", default=str(ROOT / "reports"))
    args = ap.parse_args(argv)
    report = run_challenge()
    stamped, stable = write_reports(report, Path(args.reports_dir))
    print(json.dumps({
        "result": report["result"],
        "exit_code": report["exit_code"],
        "passed": report["passed"],
        "failed": report["failed"],
        "commit_sha": report["git"]["commit_sha"],
        "artifact": str(stable),
        "stamped": str(stamped),
    }, indent=2))
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
