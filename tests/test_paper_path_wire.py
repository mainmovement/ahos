"""Gold entries pass the paper OMS path. Extra gates only block."""
from __future__ import annotations

from architecture.markets.gold_paper import GOLD_PAPER_AGENT, GOLD_PAPER_MISSION, GoldPaperTrack
from architecture.markets.judge import judge_paper_ledger
from architecture.mission.ledger import MissionLedger
from architecture.providers.gold import VERIFIED, GoldPriceWitness

T0 = 1_791_579_599.0


def _witness(price: float = 4200.0) -> GoldPriceWitness:
    return GoldPriceWitness(state=VERIFIED, reason="test", price_usd=price, spread_pct=0.1, checked_at=T0)


def _ledger(tmp_path):
    path = tmp_path / "ledger.jsonl"
    ledger = MissionLedger(path)
    ledger.start(GOLD_PAPER_MISSION, phase="paper_trading", task="path wire", agent=GOLD_PAPER_AGENT)
    return ledger


def test_a_clean_entry_is_booked_through_the_paper_path(tmp_path):
    ledger = _ledger(tmp_path)
    track = GoldPaperTrack()
    result = track.run_cycle(_witness(), now=T0, ledger=ledger)
    assert result.position is not None
    path = result.recorded and ledger.latest(GOLD_PAPER_MISSION)["CHECKPOINT"]["path"]
    assert path["oms"] == "ACCEPTED_PAPER"
    assert path["live"] is False
    assert path["blocks"] == []
    assert path["proposal_merge"] is False
    assert path["notional_usd"] <= 1000.0
    report = judge_paper_ledger(ledger, GOLD_PAPER_MISSION)
    assert report.verdict != "BROKEN_CHAIN"


def test_an_ineligible_venue_blocks_the_entry(tmp_path):
    ledger = _ledger(tmp_path)
    track = GoldPaperTrack(venue_verdict="UNKNOWN")
    result = track.run_cycle(_witness(), now=T0, ledger=ledger)
    assert result.position is None
    path = ledger.latest(GOLD_PAPER_MISSION)["CHECKPOINT"]["path"]
    assert path["oms"] == "REJECTED"
    assert path["blocks"]


def test_a_deep_paper_drawdown_is_recorded_as_a_block(tmp_path):
    ledger = _ledger(tmp_path)
    track = GoldPaperTrack()
    track.equity_curve = [10_000.0, 8_000.0]
    result = track.run_cycle(_witness(), now=T0, ledger=ledger)
    assert result.position is None
    path = ledger.latest(GOLD_PAPER_MISSION)["CHECKPOINT"]["path"]
    assert path["crisis"] == "HALT"
    assert "crisis drawdown" in path["blocks"]
