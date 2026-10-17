"""M29 crisis shock on a paper price path. A deep drawdown halts new paper entries."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CrisisReport:
    drawdown_pct: float
    level: str
    entries_allowed: bool


def shock(prices: list[float], *, drop_pct: float, halt_dd_pct: float = 10.0) -> CrisisReport:
    usable = [p for p in prices if p > 0]
    if not usable or drop_pct < 0 or drop_pct >= 1:
        return CrisisReport(0.0, "UNKNOWN", False)
    peak = max(usable)
    trough = min(p * (1.0 - drop_pct) for p in usable)
    dd = (peak - trough) / peak * 100.0
    if dd > halt_dd_pct:
        return CrisisReport(round(dd, 4), "HALT", False)
    return CrisisReport(round(dd, 4), "READ", True)
