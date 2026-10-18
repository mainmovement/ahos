"""M42 judge over the oil paper mission checkpoints."""
from __future__ import annotations

from architecture.markets.judge import CLEAN, judge_paper_ledger
from architecture.markets.oil_paper import OIL_PAPER_MISSION, run_oil_cycle
from architecture.mission.ledger import MissionLedger


def test_seven_oil_cycles_judge_clean(tmp_path):
    ledger = MissionLedger(tmp_path / "oil.jsonl")
    for _ in range(7):
        run_oil_cycle(ledger, left=70.0, right=70.1)
    report = judge_paper_ledger(ledger, OIL_PAPER_MISSION)
    assert report.verdict == CLEAN
    assert report.mission_id == OIL_PAPER_MISSION
