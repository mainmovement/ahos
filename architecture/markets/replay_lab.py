"""Paper replay of a price path. A short sample is not an edge.

The result never says the path is profitable enough to trade. Fewer than 30
closed marks is NO_PROVEN_EDGE.
"""
from __future__ import annotations

from dataclasses import dataclass

MIN_MARKS = 30


@dataclass(frozen=True, slots=True)
class ReplayReport:
    marks: int
    pnl_usd: float
    verdict: str
    proven_edge: bool


def replay(prices: list[float], *, hold: int = 1) -> ReplayReport:
    usable = [p for p in prices if p > 0]
    if hold < 1:
        hold = 1
    pnl = 0.0
    marks = 0
    i = 0
    while i + hold < len(usable):
        pnl += usable[i + hold] - usable[i]
        marks += 1
        i += hold
    if marks < MIN_MARKS:
        return ReplayReport(marks, round(pnl, 4), "NO_PROVEN_EDGE", False)
    return ReplayReport(marks, round(pnl, 4), "SAMPLE_ONLY", False)
