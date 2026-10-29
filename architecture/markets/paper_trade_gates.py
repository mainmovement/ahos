"""Pre-trade gates: higher entry bar and fee-drag filter (PAPER_ONLY)."""
from __future__ import annotations

from pathlib import Path

MIN_EXPECTED_PROFIT_TO_FEE_RATIO = 2.0

# Desks net-negative on live book (EDGE_REPORT 2026-10-29); paper-only size haircut until owner review.
DESK_NOTIONAL_MULT: dict[str, float] = {
    "ASIA_EQUITIES": 0.35,
    "CRYPTO": 0.25,
    "FOREX": 0.35,
    "GOLD": 0.25,
    "OIL": 0.30,
    "PB_TOKEN": 0.35,
    "US_EQUITIES": 1.0,
    "EU_EQUITIES": 1.0,
}


def effective_desk_notional_mult(root: Path | None, desk: str) -> tuple[float, str]:
    """Conservative merge: min(static haircut, EDGE desk_policy if present)."""
    static = float(DESK_NOTIONAL_MULT.get(desk, 1.0))
    if root is None:
        return static, "static"
    try:
        from architecture.markets.edge_desk_policy import load_desk_policy

        pol = load_desk_policy(Path(root))
        if not pol:
            return static, "static"
        edge_m = (pol.get("notional_mult_by_desk") or {}).get(desk)
        if edge_m is None:
            return static, "static"
        merged = min(static, float(edge_m))
        return merged, "edge_merged"
    except Exception:
        return static, "static"


def composite_entry_threshold() -> float:
    from architecture.markets import paper_trader as pt

    return float(pt.ENTRY)


def excess_composite_strength(composite: float, entry: float | None = None) -> float:
    entry = composite_entry_threshold() if entry is None else entry
    return max(0.0, (abs(composite) - entry) / max(1e-9, 1.0 - entry))


def round_trip_fees_usd(notional_usd: float, fee_rate_per_side: float) -> float:
    return notional_usd * fee_rate_per_side * 2.0


def expected_take_profit_usd(
    notional_usd: float,
    stop_pct: float,
    composite: float,
    *,
    entry: float | None = None,
    take_mult: float | None = None,
) -> float:
    from architecture.markets import paper_trader as pt

    take_mult = pt.TAKE_MULT if take_mult is None else take_mult
    entry = composite_entry_threshold() if entry is None else entry
    strength = excess_composite_strength(composite, entry)
    return notional_usd * stop_pct * take_mult * strength


def fee_drag_gate(
    notional_usd: float,
    fee_rate_per_side: float,
    stop_pct: float,
    composite: float,
    *,
    entry: float | None = None,
    min_ratio: float = MIN_EXPECTED_PROFIT_TO_FEE_RATIO,
) -> tuple[bool, dict]:
    """Pass when modeled take-profit (composite-scaled) >= min_ratio * round-trip fees."""
    fees = round_trip_fees_usd(notional_usd, fee_rate_per_side)
    expected = expected_take_profit_usd(notional_usd, stop_pct, composite, entry=entry)
    ratio = (expected / fees) if fees > 1e-12 else (999.0 if expected > 0 else 0.0)
    ok = expected >= min_ratio * fees
    return ok, {
        "expected_profit_usd": round(expected, 6),
        "round_trip_fees_usd": round(fees, 6),
        "min_ratio": min_ratio,
        "ratio": round(ratio, 4),
        "composite": composite,
        "notional_usd": notional_usd,
        "stop_pct": stop_pct,
        "fee_rate_per_side": fee_rate_per_side,
    }
