"""Live-ready execution plumbing (orders blocked while HOLD.flag present). PAPER_ONLY default."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

PAPER_ONLY: bool = True
INITIAL_CAPITAL_USD: float = 100.0

Side = Literal["LONG", "SHORT"]


@dataclass(frozen=True, slots=True)
class SignedOrderEnvelope:
    symbol: str
    side: Side
    notional_usd: float
    leverage: int
    paper_only: bool
    live_blocked: bool
    hold_flag_active: bool
    judge_verdict: str
    kill_switch_armed: bool


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def hold_flag_present(root: Path | None = None) -> bool:
    base = root or _repo_root()
    return (base / "HOLD.flag").is_file() or (base.parent / "ahos_arena" / "HOLD.flag").is_file()


def m42_judge_precheck() -> str:
    """Deterministic pre-trade judge stub (PAPER_ONLY)."""
    return "PASS_PAPER_ONLY"


def m39_kill_switch_status() -> bool:
    """Kill-switch armed when HOLD.flag exists."""
    return hold_flag_present()


def build_signed_order_envelope(
    *,
    symbol: str,
    side: Side,
    notional_usd: float,
    leverage: int,
    root: Path | None = None,
) -> SignedOrderEnvelope:
    hold = hold_flag_present(root)
    return SignedOrderEnvelope(
        symbol=symbol,
        side=side,
        notional_usd=notional_usd,
        leverage=leverage,
        paper_only=True,
        live_blocked=hold,
        hold_flag_active=hold,
        judge_verdict=m42_judge_precheck(),
        kill_switch_armed=m39_kill_switch_status(),
    )


def route_order_attempt(envelope: SignedOrderEnvelope) -> dict[str, Any]:
    """Fail-closed: never emits a live route while HOLD.flag is set."""
    if envelope.hold_flag_active or envelope.live_blocked:
        return {
            "status": "BLOCKED_HOLD_FLAG",
            "plumbing_status": "READY_LOCKED_BY_HOLD_FLAG",
            "live_orders_blocked_until_owner_unlock": True,
            "paper_only": True,
            "live": False,
            "reason": "HOLD.flag present — live adapter not invoked",
        }
    return {
        "status": "WOULD_ROUTE_PAPER_SIMULATION_ONLY",
        "plumbing_status": "READY_LOCKED_BY_HOLD_FLAG",
        "live_orders_blocked_until_owner_unlock": True,
        "paper_only": True,
        "live": False,
    }


def pilot_account_state(
    *,
    current_equity_usd: float | None = None,
    net_pnl_usd: float = 0.0,
) -> dict[str, Any]:
    equity = current_equity_usd if current_equity_usd is not None else INITIAL_CAPITAL_USD
    roi = ((equity - INITIAL_CAPITAL_USD) / INITIAL_CAPITAL_USD) * 100.0 if INITIAL_CAPITAL_USD else 0.0
    return {
        "initial_capital_usd": INITIAL_CAPITAL_USD,
        "current_equity_usd": round(equity, 4),
        "net_pnl_usd": round(net_pnl_usd, 4),
        "roi_pct": round(roi, 4),
        "paper_only": True,
        "live": False,
    }


def gateway_status(root: Path | None = None) -> dict[str, Any]:
    hold = hold_flag_present(root)
    return {
        "plumbing_status": "READY_LOCKED_BY_HOLD_FLAG",
        "execution_mode": "PAPER_ONLY",
        "real_trading": False,
        "live_orders_blocked_until_owner_unlock": True,
        "hold_flag_active": hold,
        "m42_judge": m42_judge_precheck(),
        "m39_kill_switch_armed": m39_kill_switch_status(),
        "initial_capital_usd": INITIAL_CAPITAL_USD,
        "paper_only": True,
        "live": False,
    }
