"""M21 paper sizing. Unknown samples size to zero and never raise a cap."""
from __future__ import annotations

MIN_SAMPLE = 30
KELLY_CAP = 0.25


def fractional_kelly(*, win_rate: float | None, payoff: float | None, sample: int) -> float:
    if sample < MIN_SAMPLE or win_rate is None or payoff is None or payoff <= 0:
        return 0.0
    if not 0.0 < win_rate < 1.0:
        return 0.0
    edge = win_rate - (1.0 - win_rate) / payoff
    if edge <= 0:
        return 0.0
    full = edge / payoff
    return min(KELLY_CAP, full * KELLY_CAP)


def bound_notional(proposed: float, cap: float) -> float:
    if cap <= 0:
        return 0.0
    return min(max(float(proposed), 0.0), float(cap))
