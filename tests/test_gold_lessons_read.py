"""M49 lessons are read into the gold path; they do not block or resize entries."""
from __future__ import annotations

from architecture.learning.lessons_ledger import LessonsLedger
from architecture.markets.gold_paper import GOLD_PAPER_AGENT, GOLD_PAPER_MISSION, GoldPaperTrack
from architecture.mission.ledger import MissionLedger
from architecture.providers.gold import VERIFIED, GoldPriceWitness

T0 = 1_700_000_100.0


def _ledger(tmp_path):
    path = tmp_path / "ledger.jsonl"
    ledger = MissionLedger(path)
    ledger.start(GOLD_PAPER_MISSION, phase="paper_trading", task="lessons read", agent=GOLD_PAPER_AGENT)
    return ledger


def test_unreviewed_lessons_are_visible_with_zero_weight(tmp_path):
    ledger = _ledger(tmp_path)
    store = LessonsLedger(ledger.path.with_name("m49_lessons.sqlite"))
    store.append(
        lesson_id="gold-prior",
        source="trade_loss",
        market="gold",
        taxonomy="paper",
        evidence_refs=("cycle:1",),
        claim="prior loss",
        counterfactual="no gate move",
        valid_from="1970-01-01T00:00:00Z",
    )
    store.close()

    track = GoldPaperTrack()
    result = track.run_cycle(
        GoldPriceWitness(state=VERIFIED, reason="test", price_usd=4200.0, spread_pct=0.1, checked_at=T0),
        now=T0,
        ledger=ledger,
    )
    assert result.position is not None
    lessons = ledger.latest(GOLD_PAPER_MISSION)["CHECKPOINT"]["path"]["lessons"]
    assert lessons["visible_gold"] == 1
    assert lessons["weight_one"] == 0
    assert lessons["notional_unchanged"] is True
    assert lessons["m58_cap_unchanged"] is True
    assert lessons["m58_daily_cap_pct"] == 3.0


def test_reviewed_lesson_counts_weight_one_without_blocking(tmp_path):
    ledger = _ledger(tmp_path)
    store = LessonsLedger(ledger.path.with_name("m49_lessons.sqlite"))
    store.append(
        lesson_id="gold-reviewed",
        source="trade_loss",
        market="gold",
        taxonomy="paper",
        evidence_refs=("cycle:2",),
        claim="reviewed loss",
        counterfactual="no gate move",
        valid_from="1970-01-01T00:00:00Z",
    )
    store.review("gold-reviewed", reviewer="16", valid_from="1970-01-01T00:00:00Z")
    store.close()

    track = GoldPaperTrack()
    result = track.run_cycle(
        GoldPriceWitness(state=VERIFIED, reason="test", price_usd=4200.0, spread_pct=0.1, checked_at=T0),
        now=T0,
        ledger=ledger,
    )
    assert result.position is not None
    lessons = ledger.latest(GOLD_PAPER_MISSION)["CHECKPOINT"]["path"]["lessons"]
    assert lessons["weight_one"] == 1
    assert lessons["notional_unchanged"] is True
    assert lessons["m58_cap_unchanged"] is True
    assert lessons["m58_daily_cap_pct"] == 3.0
