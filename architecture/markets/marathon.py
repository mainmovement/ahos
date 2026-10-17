"""M25 paper marathon. A short sample has no deflated edge and cannot promote."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Marathon:
    verdict: str
    promoted: bool
    dsr: float | None


def evaluate(*, trades: int, trials: int) -> Marathon:
    if trades < 30 or trials < 1:
        return Marathon("INSUFFICIENT", False, None)
    return Marathon("NOT_A_PROMOTION", False, None)
