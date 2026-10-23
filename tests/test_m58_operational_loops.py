"""M58.2–M58.5 operational loops tests (Mistake->Eval fixtures, Devil's Advocate dissent, Brier calibration)."""
from __future__ import annotations

from architecture.learning.calibration import brier_score, log_odds_recalibrate
from architecture.learning.mistakes import from_loss, lessons_to_eval_fixtures
from architecture.markets.council_gate import advise, evaluate_council_with_dissent


def test_m58_2_mistake_lessons_to_eval_fixtures():
    assert from_loss(case_id="c1", pnl_usd=-5.0).status == "UNVERIFIED"
    lessons = [
        {"id": "L1", "mistake": "wide_spread_entry", "market": "gold", "unseen_passed": False},
        {"id": "L2", "mistake": "wide_spread_entry", "market": "gold", "unseen_passed": False},
        {"id": "L3", "mistake": "single_occurrence", "market": "gold"},
    ]
    fixtures = lessons_to_eval_fixtures(lessons, min_repeats=2)
    assert len(fixtures) == 1
    assert fixtures[0]["signature"] == "wide_spread_entry"
    assert fixtures[0]["status"] == "UNVERIFIED"
    assert fixtures[0]["threshold_changed"] is False


def test_m58_3_devils_advocate_dissent_required():
    assert advise(votes_to_promote=3, votes=3, tier="T0").promoted is False
    held = evaluate_council_with_dissent(
        proposal_id="P1",
        votes_for=4,
        votes_total=5,
        devils_advocate_dissent="",
        failure_modes=["spread_widening"],
    )
    assert held["status"] == "HOLD_FOR_REVIEW"
    assert held["approved_paper"] is False

    ok = evaluate_council_with_dissent(
        proposal_id="P2",
        votes_for=4,
        votes_total=5,
        devils_advocate_dissent="USD real-yield spike could invalidate gold breakout",
        failure_modes=["real_yield_spike", "comex_liquidity_gap"],
    )
    assert ok["status"] == "APPROVED_PAPER"
    assert ok["approved_paper"] is True
    assert ok["promoted"] is False


def test_m58_4_brier_calibration_and_recalibration():
    bs = brier_score([0.8, 0.2], [1.0, 0.0])
    assert abs(bs - 0.04) < 1e-6
    recal = log_odds_recalibrate([0.2, 0.5, 0.8], alpha=1.2)
    assert recal[1] == 0.5
    assert recal[2] > 0.8
    assert recal[0] < 0.2
