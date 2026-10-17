"""M13.1 oil quote witness. Two sources or no price. No orders.

Gold soak acceptance is still open, so this module does not join the gold
track and it has no order function.
"""
from __future__ import annotations

from dataclasses import dataclass

VERIFIED = "VERIFIED"
CONFLICT = "CONFLICT"
UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class OilQuote:
    state: str
    reason: str
    price_usd: float | None
    trades: bool


def witness(left: float | None, right: float | None, *, max_spread_pct: float = 0.5) -> OilQuote:
    if left is None or right is None or left <= 0 or right <= 0:
        return OilQuote(UNKNOWN, "a source is missing", None, False)
    mid = (left + right) / 2.0
    spread = abs(left - right) / mid * 100.0
    if spread > max_spread_pct:
        return OilQuote(CONFLICT, f"spread {spread:.3f}%", None, False)
    return OilQuote(VERIFIED, "two sources agree", mid, False)
