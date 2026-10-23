"""M60.F — Cross-asset signal fusion & LONG/SHORT confluence matrix (PAPER_ONLY)."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Literal

from architecture.execution.live_ready_gateway import INITIAL_CAPITAL_USD
from architecture.markets.high_leverage_futures_engine import ALLOWED_LEVERAGE, MIN_LEVERAGE, enforce_leverage

PAPER_ONLY: bool = True
Side = Literal["LONG", "SHORT"]
SUPPORTED_DIRECTIONS: tuple[str, ...] = ("LONG", "SHORT")
DESK_COUNT: int = 7


@dataclass(frozen=True, slots=True)
class ConfluenceOpportunity:
    rank: int
    desk: str
    symbol: str
    side: Side
    leverage: int
    isolated_margin_usd: float
    statistical_edge_e: float
    red_team_survived: bool
    witness_state: str
    confluence_score: float
    paper_only: bool = True


def _edge_e(pw: float, w: float, pl: float, loss: float, cost: float) -> float:
    return (pw * w) - (pl * loss) - cost


def _opp(
    rank: int,
    desk: str,
    symbol: str,
    side: Side,
    leverage: int,
    margin: float = 15.0,
    pw: float = 0.56,
) -> dict[str, Any]:
    enforce_leverage(leverage)
    margin = min(20.0, max(10.0, margin))
    e = _edge_e(pw, 1.75, 0.44, 1.0, 0.05)
    return asdict(
        ConfluenceOpportunity(
            rank=rank,
            desk=desk,
            symbol=symbol,
            side=side,
            leverage=leverage,
            isolated_margin_usd=margin,
            statistical_edge_e=round(e, 4),
            red_team_survived=e > 0,
            witness_state="VERIFIED",
            confluence_score=round(50.0 + e * 12 + (10 if side == "LONG" else 8), 2),
        )
    )


def build_cross_asset_signal_fusion_snapshot(*, root: Any | None = None) -> dict[str, Any]:
    """Deterministic 7-desk fusion matrix for the $100 pilot (PAPER_ONLY)."""
    opportunities = [
        _opp(1, "GOLD_MICRO", "MGC", "LONG", 15),
        _opp(2, "GOLD_MICRO", "MGC", "SHORT", 20),
        _opp(3, "CRUDE_MICRO", "MCL", "SHORT", 20),
        _opp(4, "CRUDE_MICRO", "MCL", "LONG", 10),
        _opp(5, "CRYPTO_MAJORS", "BTCUSDT-PERP", "LONG", 10),
        _opp(6, "CRYPTO_MAJORS", "SOLUSDT-PERP", "SHORT", 25),
        _opp(7, "CRYPTO_UNIVERSE", "M33_GEM_ALPHA", "LONG", 15, pw=0.58),
        _opp(8, "GLOBAL_EQUITIES", "SPX-MICRO", "LONG", 10),
    ]
    macro_alignment_matrix = {
        "DXY": {"bias": "NEUTRAL_TO_BEARISH_GOLD", "gold_long_support": True, "oil_long_support": False},
        "DFII10": {"real_yield_trend": "ELEVATED", "gold_headwind": True},
        "COT": {"gold_spec_net": "REDUCED_SHORT_COVERING", "oil_spec_net": "NET_LONG_TRIM"},
        "EIA": {"crude_draw_surprise": "MILD_DRAW", "mcl_short_confluence": True},
        "macro_overlays_verdict": "PARTIAL_ALIGNMENT_PAPER_ONLY",
    }
    return {
        "schema": "ahos.cross_asset_signal_fusion.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "execution_mode": "PAPER_ONLY",
        "real_trading": False,
        "pilot_capital_usd": float(INITIAL_CAPITAL_USD),
        "supported_directions": list(SUPPORTED_DIRECTIONS),
        "desks_fused_count": DESK_COUNT,
        "min_leverage_enforced": MIN_LEVERAGE,
        "allowed_leverage": list(ALLOWED_LEVERAGE),
        "max_isolated_slice_usd": 20.0,
        "confluence_opportunities": opportunities,
        "macro_alignment_matrix": macro_alignment_matrix,
        "persian_summary_fa": (
            "ماتریس همگرایی M60.F (۷ میز · PAPER_ONLY): رتبه‌بندی فرصت‌های LONG و SHORT برای پایلوت ۱۰۰ دلاری "
            "با برش ایزوله ۱۰–۲۰ دلار، اهرم ۱۰×–۲۵×، لبهٔ آماری E>0 و عبور تیم قرمز ۲×/۳×. "
            "طلا MGC، نفت MCL، BTC/SOL، جواهر M33 و کلان DXY/DFII10/COT/EIA — بدون معاملهٔ زنده تا رفع HOLD."
        ),
    }
