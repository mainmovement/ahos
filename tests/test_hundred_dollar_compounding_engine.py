from __future__ import annotations

import pytest

from architecture.execution.live_ready_gateway import INITIAL_CAPITAL_USD
from architecture.markets.hundred_dollar_compounding_engine import (
    build_hundred_dollar_compounding_snapshot,
    reject_sub_min_leverage,
)
from architecture.markets.high_leverage_futures_engine import enforce_leverage


def test_initial_capital_and_ledgers() -> None:
    snap = build_hundred_dollar_compounding_snapshot()
    assert snap["initial_capital_usd"] == 100.0
    assert snap["paper_compounding_ledger"]["initial_capital_usd"] == 100.0
    assert snap["live_pilot_ledger"]["status"] == "READY_LOCKED_BY_HOLD_FLAG"
    assert snap["live_pilot_ledger"]["hold_flag_active"] is True
    assert "LONG" in snap["directions"] and "SHORT" in snap["directions"]


def test_leverage_enforcement() -> None:
    enforce_leverage(10)
    enforce_leverage(25)
    with pytest.raises(ValueError):
        reject_sub_min_leverage(5)


def test_slices_and_ladder() -> None:
    snap = build_hundred_dollar_compounding_snapshot(paper_equity_usd=200.0)
    assert len(snap["compounding_ladder"]) == 4
    assert snap["paper_compounding_ledger"]["principal_free_milestone_reached"] is True
    slices = snap["slice_allocations"]
    assert len(slices) <= 3
    for row in slices:
        assert 10.0 <= row["isolated_margin_usd"] <= 20.0
        assert row["side"] in ("LONG", "SHORT")
        assert row["leverage"] >= 10
