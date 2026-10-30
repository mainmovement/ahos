from architecture.markets.paper_trade_gates import (
    MIN_AGREEING_FAMILIES,
    MIN_EXPECTED_PROFIT_TO_FEE_RATIO,
    DESK_NOTIONAL_MULT,
    excess_composite_strength,
    fee_drag_gate,
    independent_vote_gate,
    round_trip_fees_usd,
)
from architecture.markets import paper_trader as pt


def test_excess_strength_zero_below_entry():
    assert excess_composite_strength(0.31, entry=0.32) == 0.0
    assert excess_composite_strength(0.40, entry=0.32) > 0.0


def test_fee_drag_blocks_when_expected_profit_under_2x_fees():
    ok, audit = fee_drag_gate(notional_usd=5.0, fee_rate_per_side=0.001, stop_pct=0.01, composite=0.34, entry=0.32)
    assert ok is False
    assert audit["expected_profit_usd"] < MIN_EXPECTED_PROFIT_TO_FEE_RATIO * audit["round_trip_fees_usd"]


def test_fee_drag_passes_when_composite_strong():
    ok, audit = fee_drag_gate(notional_usd=8.0, fee_rate_per_side=0.001, stop_pct=0.01, composite=0.85, entry=0.32)
    assert ok is True
    assert audit["ratio"] >= MIN_EXPECTED_PROFIT_TO_FEE_RATIO


def test_losing_desks_have_shrink_mult():
    assert DESK_NOTIONAL_MULT["CRYPTO"] == 0.25
    assert DESK_NOTIONAL_MULT["US_EQUITIES"] == 1.0


def test_entry_threshold_is_032():
    assert pt.ENTRY == 0.32


def _sig(name: str, score: float | None, available: bool = True) -> dict:
    return {"name": name, "score": score, "available": available}


def test_mtf_only_cycle_does_not_invent_votes():
    ok, audit = independent_vote_gate([_sig("mtf_trend", 0.8)], "LONG")
    assert ok is True
    assert audit["applicable"] is False


def test_two_families_must_agree():
    sigs = [
        _sig("mtf_trend", 0.9),
        _sig("news", 0.4),
        _sig("macro", -0.3),
        _sig("candles", 0.0),
        _sig("research_overlay", None, available=False),
    ]
    ok, audit = independent_vote_gate(sigs, "LONG")
    assert ok is False
    assert audit["agreeing_families"] == 1


def test_research_advisory_votes_without_moving_composite():
    from architecture.markets import signal_brain as sb

    research = {
        "name": "research_overlay",
        "score": 0.0,
        "available": False,
        "evidence": {"advisory_vote_score": 0.3, "composite_weight": 0.0, "vote_authority": "ADVISORY_ONLY"},
    }
    sigs = [_sig("news", 0.4), research]
    ok, audit = independent_vote_gate(sigs, "LONG")
    assert ok is True
    assert audit["agreeing_families"] == 2
    research_vote = next(v for v in audit["votes"] if v["family"] == "research")
    assert research_vote["vote"] == "AGREE"
    assert research_vote["advisory"] is True
    assert research_vote["composite_weight"] == 0.0
    w = dict(sb.DEFAULT_WEIGHTS)
    base = [_sig("news", 0.4)]
    assert sb.combine(base + [research], w)["composite"] == sb.combine(base, w)["composite"]
    assert MIN_AGREEING_FAMILIES == 2
    assert MIN_EXPECTED_PROFIT_TO_FEE_RATIO == 2.0


def test_research_without_numeric_score_stays_unavailable():
    research = {
        "name": "research_overlay",
        "score": 0.0,
        "available": False,
        "evidence": {"advisory_vote_score": None, "vote_authority": "UNAVAILABLE"},
    }
    ok, audit = independent_vote_gate([_sig("news", 0.4), research], "LONG")
    assert ok is False
    research_vote = next(v for v in audit["votes"] if v["family"] == "research")
    assert research_vote["vote"] == "UNAVAILABLE"


def test_news_and_wicks_agree_passes():
    sigs = [_sig("news", 0.2), _sig("candles", 0.3), _sig("macro", -0.4)]
    ok, audit = independent_vote_gate(sigs, "LONG")
    assert ok is True
    assert audit["agreeing_families"] == 2
