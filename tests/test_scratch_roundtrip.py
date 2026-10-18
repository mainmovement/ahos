"""Scratch ledger round-trip includes the paper path field."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_scratch_script_on_temp_ledger(tmp_path):
    ledger = tmp_path / "scratch.jsonl"
    py = ROOT / ".venv" / "Scripts" / "python.exe"
    proc = subprocess.run(
        [str(py), str(ROOT / "scripts" / "scratch_gold_roundtrip.py"), "--ledger", str(ledger)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert "oms=ACCEPTED_PAPER" in proc.stdout
    assert "judge=" in proc.stdout
