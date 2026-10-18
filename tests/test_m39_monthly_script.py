"""M39 monthly fault report script stays paper-only and fail-closed."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_m39_monthly_fault_report_writes_json(tmp_path):
    out = tmp_path / "m39.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "m39_monthly_fault_report.py"),
            "--out",
            str(out),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["paper_only"] is True
    assert data["all_halt"] is True
    assert len(data["faults"]) == 5
