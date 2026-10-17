"""M51 self-improvement proposals. One per cycle. Never merged.

A proposal that touches a gate, a policy, or a cap is refused. A proposal
may not be derived from the loop's own previous output.
"""
from __future__ import annotations

from dataclasses import dataclass

_BLOCKED = ("gate", "policy", "cap", "hold.flag", "limit")


@dataclass(frozen=True, slots=True)
class Improvement:
    accepted: bool
    reason: str
    merge: bool
    cycle_id: str


def propose(
    *,
    cycle_id: str,
    seen_cycles: set[str],
    target: str,
    based_on_own_output: bool,
) -> Improvement:
    if cycle_id in seen_cycles:
        return Improvement(False, "one proposal per cycle", False, cycle_id)
    if based_on_own_output:
        return Improvement(False, "cannot train on its own output", False, cycle_id)
    lowered = target.replace("\\", "/").lower()
    if any(word in lowered for word in _BLOCKED):
        return Improvement(False, "gate policy or cap is closed", False, cycle_id)
    return Improvement(True, "proposal recorded", False, cycle_id)
