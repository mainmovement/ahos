"""M26 real-pilot gate. This module never turns live trading on."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PilotGate:
    review: bool
    live: bool
    reason: str


def pilot_gate(*, owner_approved: bool, paper_months: int, live_requested: bool) -> PilotGate:
    if live_requested:
        return PilotGate(False, False, "live requested")
    if not owner_approved or paper_months < 3:
        return PilotGate(False, False, "human gate closed")
    return PilotGate(True, False, "owner may review; live stays off")
