"""M24 paper capital weights. They must sum to 1. Live budget stays zero."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Allocation:
    accepted: bool
    reason: str
    live_budget: float


def allocate(weights: dict[str, float]) -> Allocation:
    if not weights or any(value < 0 for value in weights.values()):
        return Allocation(False, "weights must be non-negative", 0.0)
    total = sum(weights.values())
    if abs(total - 1.0) > 1e-6:
        return Allocation(False, "weights must sum to 1", 0.0)
    return Allocation(True, "paper weights", 0.0)
