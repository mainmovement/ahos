from architecture.markets.paper_trade_gates import (
    MIN_EXPECTED_PROFIT_TO_FEE_RATIO,
    DESK_NOTIONAL_MULT,
    excess_composite_strength,
    fee_drag_gate,
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
