#!/usr/bin/env python3
"""Prove M47 soak HALT latch and M42 gold halt gate without the live ledger."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PYTEST_TARGETS = (
    "tests/test_soak_halt_latch.py",
    "tests/test_gold_halt_gate.py",
    "tests/test_m47_m39_faults.py::test_halt_latches_until_owner_and_downgrade_does_not",
)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="HALT latch + M42 gate drill (temp only)")
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "reports" / "grok" / "M47" / "halt_latch_drill.json",
    )
    args = ap.parse_args(argv)

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *PYTEST_TARGETS, "-q"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    combined = (proc.stdout or "") + (proc.stderr or "")
    passed = proc.returncode == 0
    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "suite": "M47+M42 halt drill",
        "pytest_rc": proc.returncode,
        "pytest_passed": passed,
        "targets": list(PYTEST_TARGETS),
        "pytest_tail": combined.strip()[-2000:],
        "live_soak": {
            "status": "NOT_PROVEN_HERE",
            "reason": "Running soak PID uses pre-restart code; owner restart via start_soak.ps1 (GAP 2)",
        },
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(out), "pytest_passed": passed}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
