"""Testable risk rules. The names are the traders' themes. The predicates are ours.

They do not change the live book.
"""
from __future__ import annotations

from typing import Any

# One percent of the paper stake. Pre-registered, not fit to the ledger.
DAILY_LOSS_USD = 1.0
MAX_RISK_FRACTION = 0.005


def cut_loser(loss_pct: float, stop_pct: float) -> str:
    """Seykota and Dennis: a loss past the stop is an exit."""
    if loss_pct >= stop_pct > 0:
        return "EXIT"
    return "HOLD"


def let_winner_run(gain_pct: float, stop_pct: float, giveback_pct: float) -> str:
    """Dennis: a winner is not closed for a gain smaller than the stop."""
    if gain_pct < stop_pct:
        return "HOLD"
    if giveback_pct >= 0.5 * stop_pct:
        return "TRAIL"
    return "HOLD"


def max_risk(notional_usd: float, equity_usd: float, stop_pct: float) -> bool:
    """Tudor Jones and Druckenmiller: one trade cannot risk more than the cap."""
    if equity_usd <= 0 or stop_pct <= 0:
        return False
    risk = notional_usd * stop_pct
    return risk <= equity_usd * MAX_RISK_FRACTION + 1e-9


def no_average_down(position_pnl_usd: float, adding: bool) -> bool:
    """Livermore: do not add to a losing position."""
    if adding and position_pnl_usd < 0:
        return False
    return True


def daily_loss_stop(day_pnl_usd: float, limit_usd: float = DAILY_LOSS_USD) -> str:
    if day_pnl_usd <= -abs(limit_usd):
        return "STOP_NEW_RISK"
    return "OPEN"


def review_book(closes: list[dict[str, Any]], *, limit_usd: float = DAILY_LOSS_USD) -> dict[str, Any]:
    """Count historical days that would have stopped new risk. This does not rewrite them."""
    by_day: dict[str, float] = {}
    for row in closes:
        if row.get("event") != "CLOSE":
            continue
        pnl = row.get("realized_pnl_usd")
        stamp = str(row.get("closed_at") or "")[:10]
        if not stamp or not isinstance(pnl, (int, float)) or isinstance(pnl, bool):
            continue
        by_day[stamp] = by_day.get(stamp, 0.0) + float(pnl)
    stopped = [day for day, pnl in sorted(by_day.items()) if pnl <= -abs(limit_usd)]
    return {
        "days": len(by_day),
        "days_past_stop": len(stopped),
        "limit_usd": limit_usd,
        "applied_to_live": False,
        "state": "shadow",
    }
