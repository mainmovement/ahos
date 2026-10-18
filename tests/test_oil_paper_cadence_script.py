"""Oil cadence CLI stays on a scratch ledger and never touches gold mission."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_oil_cadence_seven_cycles(tmp_path):
    ledger = tmp_path / "oil_scratch.jsonl"
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "oil_paper_cadence.py"),
            "--ledger",
            str(ledger),
            "--cycles",
            "7",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["cycles"] == 7
    assert data["gold_mission_present"] is False
    assert data["margin_event"] == "WITHIN_CAP"
    assert data["last"]["oms"] == "ACCEPTED_PAPER"


def test_oil_cadence_break_cycle_unknown(tmp_path):
    ledger = tmp_path / "oil_break.jsonl"
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "oil_paper_cadence.py"),
            "--ledger",
            str(ledger),
            "--cycles",
            "3",
            "--break-cycle",
            "2",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["last"]["quote"] == "VERIFIED"
