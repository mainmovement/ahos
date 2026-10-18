"""M51 proposal in path; M58 close_eval lands in the same checkpoint."""
from __future__ import annotations

from architecture.markets.gold_paper import GOLD_PAPER_AGENT, GOLD_PAPER_MISSION, GoldPaperTrack
from architecture.markets.judge import judge_paper_ledger
from architecture.mission.ledger import MissionLedger
from architecture.providers.gold import VERIFIED, GoldPriceWitness

T0 = 1_700_000_200.0


def _ledger(tmp_path):
    path = tmp_path / "ledger.jsonl"
    ledger = MissionLedger(path)
    ledger.start(GOLD_PAPER_MISSION, phase="paper_trading", task="close eval", agent=GOLD_PAPER_AGENT)
    return ledger


def test_m51_proposal_is_structured_and_not_mergeable(tmp_path):
    ledger = _ledger(tmp_path)
    track = GoldPaperTrack()
    track.run_cycle(
        GoldPriceWitness(state=VERIFIED, reason="t", price_usd=4200.0, spread_pct=0.1, checked_at=T0),
        now=T0,
        ledger=ledger,
    )
    path = ledger.latest(GOLD_PAPER_MISSION)["CHECKPOINT"]["path"]
    m51 = path["m51"]
    assert m51["accepted"] is True
    assert m51["merge"] is False
    assert m51["cycle_id"] == "gold-1"


def test_close_eval_is_recorded_on_a_settled_trade(tmp_path):
    ledger = _ledger(tmp_path)
    track = GoldPaperTrack()
    track.run_cycle(
        GoldPriceWitness(state=VERIFIED, reason="t", price_usd=4200.0, spread_pct=0.1, checked_at=T0),
        now=T0,
        ledger=ledger,
    )
    track.run_cycle(
        GoldPriceWitness(state=VERIFIED, reason="t", price_usd=6400.0, spread_pct=0.1, checked_at=T0 + 60),
        now=T0 + 60,
        ledger=ledger,
    )
    cp = ledger.latest(GOLD_PAPER_MISSION)["CHECKPOINT"]
    assert cp["close_eval"] is not None
    assert cp["close_eval"]["hit"] is True
    assert cp["realized_pnl_usd"] is not None
    report = judge_paper_ledger(ledger, GOLD_PAPER_MISSION)
    assert report.verdict != "BROKEN_CHAIN"
