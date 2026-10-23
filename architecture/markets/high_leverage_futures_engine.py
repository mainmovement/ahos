"""Isolated-margin high-leverage futures education engine ($100 pilot track). PAPER_ONLY."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

from architecture.execution.live_ready_gateway import INITIAL_CAPITAL_USD, hold_flag_present

Side = Literal["LONG", "SHORT"]
ALLOWED_LEVERAGE: tuple[int, ...] = (10, 15, 20, 25)
MIN_LEVERAGE: int = 10

INSTRUMENTS: tuple[str, ...] = (
    "XAUUSD-PERP",
    "WTI-PERP",
    "BTCUSDT-PERP",
    "ETHUSDT-PERP",
    "PEPE2-USDT-PERP",
)


@dataclass(frozen=True, slots=True)
class IsolatedPosition:
    symbol: str
    side: Side
    leverage: int
    isolated_margin_usd: float
    notional_usd: float
    entry_price: float
    atr_stop_distance_pct: float
    max_loss_usd: float
    paper_only: bool = True
    live: bool = False


def enforce_leverage(leverage: int) -> int:
    if leverage < MIN_LEVERAGE:
        raise ValueError(f"leverage must be >= {MIN_LEVERAGE}, got {leverage}")
    if leverage not in ALLOWED_LEVERAGE:
        raise ValueError(f"leverage must be one of {ALLOWED_LEVERAGE}, got {leverage}")
    return leverage


def open_isolated_position(
    *,
    symbol: str,
    side: Side,
    leverage: int,
    wallet_equity_usd: float = INITIAL_CAPITAL_USD,
    isolated_margin_usd: float = 10.0,
    entry_price: float = 100.0,
    atr_stop_distance_pct: float = 2.5,
) -> IsolatedPosition:
    lev = enforce_leverage(leverage)
    margin = min(isolated_margin_usd, wallet_equity_usd)
    notional = margin * lev
    return IsolatedPosition(
        symbol=symbol,
        side=side,
        leverage=lev,
        isolated_margin_usd=margin,
        notional_usd=notional,
        entry_price=entry_price,
        atr_stop_distance_pct=atr_stop_distance_pct,
        max_loss_usd=margin,
    )


def pnl_usd(position: IsolatedPosition, exit_price: float) -> float:
    move_pct = (exit_price - position.entry_price) / position.entry_price
    if position.side == "SHORT":
        move_pct = -move_pct
    raw = position.notional_usd * move_pct
    return max(-position.max_loss_usd, min(raw, position.notional_usd))


def apply_stop_loss(position: IsolatedPosition, adverse_move_pct: float) -> float:
    """Cap loss at isolated margin slice (wallet cannot lose more than margin on this leg)."""
    if position.side == "LONG":
        loss = position.notional_usd * (-adverse_move_pct / 100.0)
    else:
        loss = position.notional_usd * (-adverse_move_pct / 100.0)
    return max(loss, -position.max_loss_usd)


def demo_positions_snapshot() -> list[dict[str, Any]]:
    long_pos = open_isolated_position(symbol="BTCUSDT-PERP", side="LONG", leverage=10)
    short_pos = open_isolated_position(symbol="WTI-PERP", side="SHORT", leverage=15)
    return [
        {
            **asdict(long_pos),
            "explanation_fa": "لانگ ۱۰× با مارجین ایزوله ۱۰ دلار؛ حد ضرر ATR حداکثر زیان را به ۱۰ دلار محدود می‌کند.",
            "unrealized_pnl_usd": pnl_usd(long_pos, long_pos.entry_price * 1.01),
        },
        {
            **asdict(short_pos),
            "explanation_fa": "شورت ۱۵× نفت؛ در صورت حرکت مخالف، زیان از مارجین ایزوله فراتر نمی‌رود.",
            "unrealized_pnl_usd": pnl_usd(short_pos, short_pos.entry_price * 0.99),
        },
    ]


def build_futures_engine_summary(wallet_equity_usd: float = INITIAL_CAPITAL_USD) -> dict[str, Any]:
    return {
        "paper_only": True,
        "execution_mode": "PAPER_ONLY",
        "real_trading": False,
        "live": False,
        "min_leverage_enforced": MIN_LEVERAGE,
        "allowed_leverage": list(ALLOWED_LEVERAGE),
        "wallet_equity_usd": wallet_equity_usd,
        "isolated_margin_default_usd": 10.0,
        "hold_flag_blocks_live": hold_flag_present(),
        "positions": demo_positions_snapshot(),
        "instruments": list(INSTRUMENTS),
    }
