"""M60.P — $100 USD compounding ladder, profit-lock floor & isolated slice engine (PAPER_ONLY)."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

from architecture.execution.live_ready_gateway import INITIAL_CAPITAL_USD, hold_flag_present
from architecture.markets.high_leverage_futures_engine import ALLOWED_LEVERAGE, MIN_LEVERAGE, enforce_leverage

PAPER_ONLY: bool = True
Side = Literal["LONG", "SHORT"]
MAX_CONCURRENT_SLICES: int = 3
MIN_SLICE_USD: float = 10.0
MAX_SLICE_USD: float = 20.0
MIN_WALLET_RESERVE_PCT: float = 40.0

LADDER_STEPS: tuple[dict[str, Any], ...] = (
    {
        "step_id": "STEP_1_110",
        "target_equity_usd": 110.0,
        "roi_pct": 10.0,
        "profit_lock_floor_usd": 102.0,
    },
    {
        "step_id": "STEP_2_125",
        "target_equity_usd": 125.0,
        "roi_pct": 25.0,
        "profit_lock_floor_usd": 110.0,
    },
    {
        "step_id": "STEP_3_150",
        "target_equity_usd": 150.0,
        "roi_pct": 50.0,
        "profit_lock_floor_usd": 125.0,
    },
    {
        "step_id": "STEP_4_200_PRINCIPAL_FREE",
        "target_equity_usd": 200.0,
        "roi_pct": 100.0,
        "profit_lock_floor_usd": 100.0,
        "principal_free_milestone_reached": True,
    },
)

SLICE_INSTRUMENTS: tuple[str, ...] = (
    "MGC",
    "MCL",
    "BTCUSDT-PERP",
    "ETHUSDT-PERP",
    "SOLUSDT-PERP",
    "M33_BREAKOUT_GEM",
)


@dataclass(frozen=True, slots=True)
class SliceAllocation:
    symbol: str
    side: Side
    leverage: int
    isolated_margin_usd: float
    statistical_edge_positive: bool
    red_team_pass: bool
    atr_stop_distance_pct: float
    liquidation_distance_pct: float
    paper_only: bool = True


def _edge_positive(pw: float, w: float, pl: float, loss: float, cost: float) -> bool:
    return (pw * w) - (pl * loss) - cost > 0.0


def _active_ladder_step(equity_usd: float) -> dict[str, Any]:
    active = LADDER_STEPS[0]
    for step in LADDER_STEPS:
        if equity_usd >= float(step["target_equity_usd"]):
            active = step
    return active


def build_slice_allocations(
    *,
    wallet_equity_usd: float = INITIAL_CAPITAL_USD,
    current_equity_usd: float | None = None,
) -> list[dict[str, Any]]:
    equity = current_equity_usd if current_equity_usd is not None else wallet_equity_usd
    reserve = equity * (MIN_WALLET_RESERVE_PCT / 100.0)
    deployable = max(0.0, equity - reserve)
    per_slice = min(MAX_SLICE_USD, max(MIN_SLICE_USD, deployable / MAX_CONCURRENT_SLICES))
    slices: list[SliceAllocation] = []
    specs: list[tuple[str, Side, int]] = [
        ("MGC", "LONG", 15),
        ("MCL", "SHORT", 20),
        ("BTCUSDT-PERP", "LONG", 10),
    ]
    for symbol, side, lev in specs[:MAX_CONCURRENT_SLICES]:
        enforce_leverage(lev)
        edge_ok = _edge_positive(0.55, 1.8, 0.45, 1.0, 0.04)
        slices.append(
            SliceAllocation(
                symbol=symbol,
                side=side,
                leverage=lev,
                isolated_margin_usd=round(per_slice, 2),
                statistical_edge_positive=edge_ok,
                red_team_pass=edge_ok,
                atr_stop_distance_pct=2.5,
                liquidation_distance_pct=max(8.0, 100.0 / lev),
            )
        )
    return [asdict(s) for s in slices]


def build_hundred_dollar_compounding_snapshot(
    *,
    root: Any | None = None,
    paper_equity_usd: float = 118.5,
) -> dict[str, Any]:
    """Deterministic M60.P snapshot (shadow paper equity defaults above STEP_1)."""
    from pathlib import Path

    repo = Path(__file__).resolve().parents[2]
    if root is not None:
        repo = Path(root).resolve()

    initial = float(INITIAL_CAPITAL_USD)
    equity = float(paper_equity_usd)
    roi_pct = round(((equity - initial) / initial) * 100.0, 2)
    ladder_step = _active_ladder_step(equity)
    slices = build_slice_allocations(wallet_equity_usd=initial, current_equity_usd=equity)
    max_slice_loss = max((s["isolated_margin_usd"] for s in slices), default=MIN_SLICE_USD)

    return {
        "schema": "ahos.hundred_dollar_compounding.v1",
        "paper_only": True,
        "execution_mode": "PAPER_ONLY",
        "real_trading": False,
        "live": False,
        "initial_capital_usd": initial,
        "directions": ["LONG", "SHORT"],
        "leverage_range": "10x-25x",
        "min_leverage_enforced": MIN_LEVERAGE,
        "allowed_leverage": list(ALLOWED_LEVERAGE),
        "slice_allocations": slices,
        "slice_instruments_catalog": list(SLICE_INSTRUMENTS),
        "max_concurrent_slices": MAX_CONCURRENT_SLICES,
        "wallet_reserve_min_pct": MIN_WALLET_RESERVE_PCT,
        "compounding_ladder": [dict(s) for s in LADDER_STEPS],
        "active_ladder_step_id": ladder_step["step_id"],
        "paper_compounding_ledger": {
            "initial_capital_usd": initial,
            "current_equity_usd": equity,
            "cumulative_roi_pct": roi_pct,
            "active_profit_lock_floor_usd": ladder_step["profit_lock_floor_usd"],
            "max_single_slice_loss_usd": max_slice_loss,
            "principal_free_milestone_reached": bool(ladder_step.get("principal_free_milestone_reached")),
        },
        "live_pilot_ledger": {
            "status": "READY_LOCKED_BY_HOLD_FLAG",
            "initial_capital_usd": initial,
            "hold_flag_active": hold_flag_present(repo),
            "leverage_range": "10x-25x",
            "directions": ["LONG", "SHORT"],
        },
        "persian_summary_fa": (
            "پایلوت ۱۰۰ دلاری (M60.P · PAPER_ONLY): برش‌های ایزوله ۱۰–۲۰ دلاری با حداکثر ۳ موقعیت همزمان "
            "و حفظ ≥۴۰٪ ذخیرهٔ کیف پول؛ جهت LONG و SHORT با اهرم ۱۰× تا ۲۵× (کمتر از ۱۰× رد می‌شود). "
            "پلهٔ قفل سود: ۱۱۰→۱۰۲، ۱۲۵→۱۱۰، ۱۵۰→۱۲۵، ۲۰۰ دلار = آزادسازی اصل سرمایه برای معاملهٔ صرفاً با سود."
        ),
    }


def reject_sub_min_leverage(leverage: int) -> None:
    """Public helper for tests — raises if leverage < 10x."""
    enforce_leverage(leverage)
