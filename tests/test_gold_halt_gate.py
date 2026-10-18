"""M42 HALT on the mission ledger blocks new gold entries (fail-closed)."""
from __future__ import annotations

from architecture.markets.gold_paper import GOLD_PAPER_AGENT, GOLD_PAPER_MISSION, GoldPaperTrack
from architecture.mission.ledger import MissionLedger
from architecture.providers.gold import VERIFIED, GoldPriceWitness

T0 = 1_791_579_599.0


def _witness(price: float = 4200.0) -> GoldPriceWitness:
    return GoldPriceWitness(
        state=VERIFIED, reason="halt gate test", price_usd=price, spread_pct=0.1, checked_at=T0
    )


def test_recorded_halt_blocks_flat_entry(tmp_path):
    path = tmp_path / "halt_gate.jsonl"
    ledger = MissionLedger(path)
    ledger.start(GOLD_PAPER_MISSION, phase="paper_trading", task="halt gate", agent=GOLD_PAPER_AGENT)
    ledger.halt("M42-reconcile", "copy drill mismatch", agent=GOLD_PAPER_AGENT)
    assert ledger.halted()[0] is True

    track = GoldPaperTrack()
    result = track.run_cycle(_witness(), now=T0, ledger=ledger)
    assert result.position is None
    cp = ledger.latest(GOLD_PAPER_MISSION)["CHECKPOINT"]
    halt = cp.get("halt") or {}
    assert halt.get("state") == "HALTED"
    assert halt.get("allowed") is False
