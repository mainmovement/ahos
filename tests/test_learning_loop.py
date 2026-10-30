import json

from architecture.markets.paper_trader import university_lesson
from architecture.university.learning_loop import (
    apply_promoted,
    loss_cause,
    propose_from_scorecard,
    stats_gate,
    university_case,
)


def _close(**extra):
    row = {
        "symbol": "BTC",
        "desk": "CRYPTO",
        "side": "LONG",
        "realized_pnl_usd": -1.0,
        "fees_usd": 0.01,
        "reason": "STOP",
        "closed_at": "2026-10-30T00:00:00Z",
        "entry_brain": {"signals": [{"name": "news", "score": 0.4, "available": True, "evidence": {}}]},
    }
    row.update(extra)
    return row


def test_a_loss_names_the_family_that_voted_the_losing_side():
    case = university_case(_close(entry_brain={"signals": [{"name": "candles", "score": 0.4, "available": True, "evidence": {}}]}))
    assert case["outcome"] == "LOSS"
    assert case["cause"] == "WRONG_FAMILY"
    assert case["families_wrong"] == ["candle_wicks"]
    assert case["families_right"] == []
    assert case["applied_to_live_weights"] is False
    news = university_case(_close())
    assert news["cause"] == "NEWS_TRAP"
    conflict = university_case(_close(reason="WITNESS_CONFLICT_EXIT", entry_brain={"signals": []}))
    assert conflict["cause"] == "BAD_DATA"


def test_fees_that_flip_the_sign_are_fee_drag():
    case = university_case(_close(realized_pnl_usd=-0.2, fees_usd=0.3, reason="TAKE_PROFIT"))
    assert case["cause"] == "FEE_DRAG"
    assert loss_cause(_close(realized_pnl_usd=1.0)) == "WIN"


def test_a_scorecard_proposal_stays_shadow_without_a_sample():
    cell = {"4h": {"hit_rate": 1.0, "hits": 1, "misses": 0}, "24h": {"hit_rate": 1.0, "hits": 2, "misses": 0}}
    proposals = propose_from_scorecard({"by_desk": {"CRYPTO": {"news": cell}}})
    assert proposals[0]["status"] == "SHADOW"
    assert proposals[0]["candidate_multiplier"] is None
    assert proposals[0]["applied_to_live_weights"] is False


def test_one_return_path_does_not_pass_the_stats_gate():
    gate = stats_gate([0.01] * 12, [[0.02] * 8])
    assert gate["gate"] == "SHADOW"
    assert gate["dsr"] is None


def test_a_shadow_proposal_does_not_change_the_weight_and_a_passing_one_does():
    weights = {"news": 0.09, "crypto_breadth": 0.0}
    shadow = {"signal": "news", "candidate_weight": 0.2, "gate": "SHADOW", "red_team": None, "dsr": None, "pbo": None}
    assert apply_promoted(weights, shadow) == weights
    forged = {"signal": "news", "candidate_weight": 0.2, "gate": "PASS_STATS", "red_team": "SURVIVED_RED_TEAM", "dsr": 0.5, "pbo": 0.1}
    assert apply_promoted(weights, forged)["news"] == 0.09
    passed = {"signal": "news", "candidate_weight": 0.12, "gate": "PASS_STATS", "red_team": "SURVIVED_RED_TEAM", "dsr": 0.99, "pbo": 0.2}
    assert apply_promoted(weights, passed)["news"] == 0.12
    assert weights["news"] == 0.09


def test_ten_hits_do_not_rewrite_the_live_weight(tmp_path):
    weights = {
        "version": 3,
        "weights": {"candles": 0.2},
        "stats": {"candles": {"n": 10, "hits": 10}},
        "history": [],
    }
    close = _close(realized_pnl_usd=1.0, reason="TAKE_PROFIT")
    university_lesson(tmp_path, weights, close, [{"signal": "candles", "score": 0.4, "contribution": 0.08}])
    assert weights["weights"]["candles"] == 0.2
    assert weights["version"] == 3
    assert weights["stats"]["candles"]["n"] == 11
    rows = (tmp_path / "reports" / "grok" / "PAPER" / "university_cases.jsonl").read_text(encoding="utf-8").splitlines()
    case = json.loads(rows[-1])
    assert case["outcome"] == "WIN"
    proposals = (tmp_path / "reports" / "grok" / "PAPER" / "weight_proposals.jsonl").read_text(encoding="utf-8")
    assert "hit_rate_without_DSR_PBO" in proposals
