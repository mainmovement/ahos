"""Live futures stay at 1x until evidence. Shadow 5x and 10x do not move that equity."""
from __future__ import annotations

from pathlib import Path

from architecture.markets.leverage_ladder import (
    DSR_MIN,
    MAX_DRAWDOWN,
    MIN_CLOSED,
    PBO_MAX,
    books_report,
    evidence_passes,
    live_rung,
    mark_shadow_book,
    measure,
    mirror_shadow_open,
    rung_decision,
)
from architecture.markets.paper_trade_gates import MIN_AGREEING_FAMILIES, MIN_EXPECTED_PROFIT_TO_FEE_RATIO


def _pass() -> dict:
    return {"closed": MIN_CLOSED, "dsr": 0.97, "pbo": 0.2, "max_drawdown_pct": 5.0}


def test_one_path_cannot_pass_dsr_or_pbo() -> None:
    ev = measure([0.1] * 30)
    assert ev["dsr"] is None and ev["pbo"] is None
    assert evidence_passes(ev) is False
    assert DSR_MIN == 0.95 and PBO_MAX == 0.5 and MAX_DRAWDOWN == 0.15
    assert MIN_AGREEING_FAMILIES == 2
    assert MIN_EXPECTED_PROFIT_TO_FEE_RATIO == 2.0


def test_rungs_step_one_at_a_time_and_drawdown_steps_down() -> None:
    up = rung_decision(1.0, _pass(), 0.0)
    assert up["applied"] == 2.0 and up["lock"] == "EVIDENCE_STEP_UP"
    assert rung_decision(2.0, _pass(), 0.0)["applied"] == 3.0
    assert rung_decision(3.0, _pass(), 0.0)["applied"] == 5.0
    assert rung_decision(5.0, _pass(), 0.0)["lock"] == "RUNG_HELD"
    down = rung_decision(3.0, _pass(), 0.16)
    assert down["applied"] == 2.0 and down["lock"] == "DRAWDOWN_STEP_DOWN"
    floor = rung_decision(1.0, _pass(), 0.40)
    assert floor["applied"] == 1.0 and floor["lock"] == "DRAWDOWN_FLOOR"
    assert rung_decision(1.0, measure([]), 0.0)["lock"] == "EVIDENCE_INCOMPLETE"


def test_live_rung_does_not_step_twice_in_one_stamp(tmp_path: Path) -> None:
    from architecture.markets.leverage_ladder import STATE_REL, _write

    _write(tmp_path / STATE_REL, {"LISTED_FUTURES": {"rung": 3.0, "peak_pnl_usd": 100.0}})
    first = live_rung(tmp_path, "LISTED_FUTURES", [], unrealized=-20.0, stamp="t1")
    second = live_rung(tmp_path, "LISTED_FUTURES", [], unrealized=-40.0, stamp="t1")
    assert first["applied"] == 2.0
    assert second["applied"] == 2.0


def test_shadow_liquidates_without_touching_live_equity(tmp_path: Path) -> None:
    mirror_shadow_open(
        tmp_path, symbol="ES", desk="LISTED_FUTURES", side="LONG", margin_usd=10.0, price=100.0,
        fee=0.0003, slip=0.0, ts=1_000.0, opened_at="2026-10-30T00:00:00Z",
        votes=[{"family": "news", "vote": "AGREE"}, {"family": "macro_central_bank", "vote": "AGREE"}],
    )
    mark_shadow_book(tmp_path, {"ES": {"price": 100.0}}, 1_000.0, live_open={"ES"})
    crashed = mark_shadow_book(tmp_path, {"ES": {"price": 70.0}}, 2_000.0, live_open={"ES"})
    assert crashed is None
    doc = books_report(tmp_path, {"ES": {"desk": "LISTED_FUTURES", "side": "LONG", "leverage": 1.0,
                                         "notional_usd": 10.0, "liquidation_price": 5.0}}, [])
    row = next(r for r in doc["rows"] if r["symbol"] == "ES")
    assert row["live"]["leverage"] == 1.0
    assert row["shadow"]["5.0"]["open"] is False
    assert row["shadow"]["5.0"]["close_reason"] == "SIMULATED_LIQUIDATION"
    assert row["shadow"]["10.0"]["close_reason"] == "SIMULATED_LIQUIDATION"
    assert doc["shadow_changes_live_equity"] is False
    assert doc["desks"]["LISTED_FUTURES"]["live_leverage"] == 1.0
