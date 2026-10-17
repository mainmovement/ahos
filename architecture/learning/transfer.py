"""M58.6 cross-domain note. It cannot change the target market's gate."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Transfer:
    state: str
    gate_changed: bool


def transfer(*, source: str, target: str, changes_gate: bool) -> Transfer:
    if changes_gate:
        return Transfer("REFUSED", False)
    if source == target:
        return Transfer("SAME_MARKET", False)
    return Transfer("EXPERIMENT_ONLY", False)
