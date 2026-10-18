"""Ledger copy wiring probe refuses live path as dest."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_prove_wiring_on_scratch_ledger(tmp_path):
    src = tmp_path / "src.jsonl"
    dest = tmp_path / "dest.jsonl"
    from architecture.markets.gold_paper import GOLD_PAPER_AGENT, GOLD_PAPER_MISSION
    from architecture.mission.ledger import MissionLedger

    ledger = MissionLedger(src)
    ledger.start(GOLD_PAPER_MISSION, phase="paper", task="probe", agent=GOLD_PAPER_AGENT)

    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "prove_wiring_on_ledger_copy.py"),
            "--source",
            str(src),
            "--dest",
            str(dest),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["path_oms"] == "ACCEPTED_PAPER"
    assert data["m51"]["merge"] is False
    assert "m58_cap_unchanged" in data["lessons_keys"] or "visible_gold" in data["lessons_keys"]
