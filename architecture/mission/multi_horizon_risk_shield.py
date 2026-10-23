"""M60.R — Multi-horizon drawdown circuit breakers for $100 pilot (PAPER_ONLY)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from architecture.execution.live_ready_gateway import INITIAL_CAPITAL_USD
from architecture.markets.high_leverage_futures_engine import ALLOWED_LEVERAGE, MIN_LEVERAGE

PAPER_ONLY: bool = True
Side = Literal["LONG", "SHORT"]
SHIELD_VERDICT = "ARMED_GREEN"
WALLET_RESERVE_MIN_PCT = 40.0
MAX_CORRELATED_SAME_DIRECTION = 2

HORIZON_BREAKERS: tuple[dict[str, Any], ...] = (
    {
        "horizon_id": "INTRADAY_24H",
        "max_drawdown_pct": 3.0,
        "max_drawdown_usd": 3.0,
        "breach_action_fa": "قفل ۶ ساعتهٔ سردکن پس از عبور ۳٪",
        "status": "ARMED",
    },
    {
        "horizon_id": "WEEKLY_7D",
        "max_drawdown_pct": 6.0,
        "max_drawdown_usd": 6.0,
        "breach_action_fa": "کاهش اهرم ۲۵×→۱۰× + بازبینی تیم قرمز",
        "status": "ARMED",
    },
    {
        "horizon_id": "MONTHLY_30D",
        "max_drawdown_pct": 10.0,
        "max_drawdown_usd": 10.0,
        "breach_action_fa": "قرنطینهٔ کامل کاغذی تا بازگشت E>0",
        "status": "ARMED",
    },
)


def build_multi_horizon_risk_shield_snapshot(*, root: Any | None = None) -> dict[str, Any]:
    base = float(INITIAL_CAPITAL_USD)
    exposures: list[dict[str, Any]] = [
        {"symbol": "MGC", "side": "LONG", "leverage": 15, "isolated_margin_usd": 15.0},
        {"symbol": "MCL", "side": "SHORT", "leverage": 20, "isolated_margin_usd": 12.0},
        {"symbol": "BTCUSDT-PERP", "side": "LONG", "leverage": 10, "isolated_margin_usd": 10.0},
        {"symbol": "SOLUSDT-PERP", "side": "SHORT", "leverage": 25, "isolated_margin_usd": 18.0},
    ]
    for row in exposures:
        if row["leverage"] < MIN_LEVERAGE or row["leverage"] not in ALLOWED_LEVERAGE:
            raise ValueError("leverage out of allowed range")
    long_n = sum(1 for e in exposures if e["side"] == "LONG")
    short_n = sum(1 for e in exposures if e["side"] == "SHORT")
    reserve_pct = WALLET_RESERVE_MIN_PCT
    return {
        "schema": "ahos.multi_horizon_risk_shield.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "execution_mode": "PAPER_ONLY",
        "real_trading": False,
        "pilot_capital_usd": base,
        "supported_directions": ["LONG", "SHORT"],
        "leverage_range": "10x-25x",
        "shield_verdict": SHIELD_VERDICT,
        "horizon_breakers": [dict(h) for h in HORIZON_BREAKERS],
        "directional_balance": {
            "active_long_slices": long_n,
            "active_short_slices": short_n,
            "max_correlated_same_direction": MAX_CORRELATED_SAME_DIRECTION,
            "wallet_reserve_min_pct": reserve_pct,
            "reserve_usd": round(base * reserve_pct / 100.0, 2),
            "exposures": exposures,
        },
        "persian_summary_fa": (
            "سپر ضدضرر چندافقی M60.R (PAPER_ONLY): سقف افت ۳٪ روزانه، ۶٪ هفتگی و ۱۰٪ ماهانه روی پایهٔ ۱۰۰ دلار؛ "
            "حداکثر ۲ برش هم‌جهت همبسته؛ ذخیرهٔ کیف پول ≥۴۰٪؛ LONG/SHORT با اهرم ۱۰×–۲۵× — shield_verdict=ARMED_GREEN."
        ),
    }
