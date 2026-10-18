"""Oil paper cycles stay off the gold mission. Margin cannot go live."""
from architecture.markets.gold_paper import GOLD_PAPER_MISSION
from architecture.markets.margin import assess
from architecture.markets.oil_paper import OIL_PAPER_MISSION, run_oil_cycle
from architecture.mission.ledger import MissionLedger


def test_oil_cycle_uses_its_own_mission(tmp_path):
    ledger = MissionLedger(tmp_path / "ledger.jsonl")
    cycle = run_oil_cycle(ledger, left=70.0, right=70.1)
    assert cycle.quote.state == "VERIFIED"
    assert cycle.oms == "ACCEPTED_PAPER"
    assert cycle.live is False
    cp = ledger.latest(OIL_PAPER_MISSION)["CHECKPOINT"]
    assert cp["trades"] is False
    assert cp["margin_event"] == "WITHIN_CAP"
    assert ledger.latest(GOLD_PAPER_MISSION) is None
    refused = run_oil_cycle(ledger, left=70.0, right=None)
    assert refused.quote.state == "UNKNOWN"
    assert refused.oms == "NO_ENTRY"


def test_margin_liquidates_above_the_cap_and_stays_paper():
    inside = assess(equity_usd=10_000, notional_usd=1_000)
    assert inside.event == "WITHIN_CAP"
    assert inside.live is False
    outside = assess(equity_usd=1_000, notional_usd=5_000)
    assert outside.event == "LIQUIDATION"
    assert assess(equity_usd=0, notional_usd=10).event == "UNKNOWN"
