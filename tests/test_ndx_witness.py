"""NASDAQ-100 is its own book. QQQ is not a same-price witness for ^NDX."""
from __future__ import annotations

from architecture.markets.paper_trader import INSTRUMENTS
from architecture.markets.paper_trade_gates import (
    MIN_AGREEING_FAMILIES,
    MIN_EXPECTED_PROFIT_TO_FEE_RATIO,
)
from architecture.markets.second_source import STOOQ_MAP, TOLERANCE, TV_MAP, witness
from architecture.markets.weekday_session_gate import SYMBOL_VENUE


def test_ndx_verifies_only_against_an_index_level_source() -> None:
    assert INSTRUMENTS["NDX"][0] == "US_EQUITIES"
    assert TV_MAP["NDX"] == "NASDAQ:NDX"
    assert STOOQ_MAP["NDX"] == "^ndq"
    assert SYMBOL_VENUE["NDX"] == "NYSE"
    assert TOLERANCE["NDX"] == 0.0035
    agree = witness("NDX", {"price": 20000.0, "source": "yahoo:^NDX"},
                    {"price": 20040.0, "source": "tradingview:NASDAQ:NDX"})
    assert agree["verdict"] == "VERIFIED"
    one = witness("NDX", {"price": 20000.0, "source": "yahoo:^NDX"}, {})
    assert one["verdict"] == "UNRESOLVED"
    qqq = witness(
        "NDX",
        {"price": 20000.0, "source": "yahoo:^NDX"},
        {"price": 490.0, "source": "yahoo:QQQ", "instrument_basis": "qqq_etf"},
    )
    assert qqq["verdict"] == "UNRESOLVED"
    assert MIN_AGREEING_FAMILIES == 2
    assert MIN_EXPECTED_PROFIT_TO_FEE_RATIO == 2.0
