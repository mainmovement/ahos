"""M58.2 a loss becomes an unverified eval case. Thresholds stay put."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EvalCase:
    case_id: str
    status: str
    threshold_changed: bool


def from_loss(*, case_id: str, pnl_usd: float) -> EvalCase:
    if pnl_usd >= 0:
        return EvalCase(case_id, "IGNORED", False)
    return EvalCase(case_id, "UNVERIFIED", False)
