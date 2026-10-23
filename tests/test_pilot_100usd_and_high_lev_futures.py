"""Pilot $100 track, HOLD.flag gateway, and >=10x isolated futures (PAPER_ONLY)."""
from __future__ import annotations

import pytest

from architecture.execution.live_ready_gateway import (
    INITIAL_CAPITAL_USD,
    build_signed_order_envelope,
    gateway_status,
    pilot_account_state,
    route_order_attempt,
)
from architecture.markets.high_leverage_futures_engine import (
    MIN_LEVERAGE,
    open_isolated_position,
    pnl_usd,
    enforce_leverage,
    apply_stop_loss,
)


def test_pilot_100_usd_account_and_hold_locked_gateway() -> None:
    acct = pilot_account_state()
    assert acct["initial_capital_usd"] == 100.0
    assert acct["current_equity_usd"] == 100.0
    assert acct["paper_only"] is True
    gw = gateway_status()
    assert gw["plumbing_status"] == "READY_LOCKED_BY_HOLD_FLAG"
    assert gw["live_orders_blocked_until_owner_unlock"] is True
    env = build_signed_order_envelope(symbol="BTCUSDT-PERP", side="LONG", notional_usd=50.0, leverage=10)
    route = route_order_attempt(env)
    assert route["live"] is False
    assert route["status"] == "BLOCKED_HOLD_FLAG"


def test_leverage_ge_10_long_short_pnl_and_isolated_loss_cap() -> None:
    with pytest.raises(ValueError):
        enforce_leverage(5)
    long_p = open_isolated_position(symbol="XAUUSD-PERP", side="LONG", leverage=10)
    short_p = open_isolated_position(symbol="WTI-PERP", side="SHORT", leverage=25)
    assert long_p.leverage >= MIN_LEVERAGE
    assert pnl_usd(long_p, long_p.entry_price * 1.02) > 0
    assert pnl_usd(short_p, short_p.entry_price * 1.02) < 0
    capped = apply_stop_loss(long_p, adverse_move_pct=50.0)
    assert capped >= -long_p.max_loss_usd
    assert long_p.max_loss_usd <= 10.0
    wallet_after_worst = INITIAL_CAPITAL_USD + capped
    assert wallet_after_worst >= INITIAL_CAPITAL_USD - 10.0
