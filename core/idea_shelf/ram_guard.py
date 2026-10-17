"""RAM guard: shed non-core ideas under pressure (paper core never shed)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from core.idea_shelf.registry import ShelfIdea

RamGuardState = Literal["UNDER_FLOOR", "AT_FLOOR", "ABOVE_FLOOR", "UNKNOWN"]
RamPressure = Literal["OK", "SOFT", "HARD"]


@dataclass(frozen=True, slots=True)
class RamGuardDecision:
    pressure: RamPressure
    shed_ids: tuple[str, ...]
    kept_core: tuple[str, ...]
    reason: str


RAM_FLOOR_GB = 8.0
SOFT_PCT = 80.0
HARD_PCT = 90.0
REENABLE_PCT = 70.0


def ram_band(ram_gb: float | None) -> RamGuardState:
    if ram_gb is None:
        return "UNKNOWN"
    if ram_gb < RAM_FLOOR_GB:
        return "UNDER_FLOOR"
    if ram_gb == RAM_FLOOR_GB:
        return "AT_FLOOR"
    return "ABOVE_FLOOR"


def evaluate_ram_guard(
    ram_used_pct: float,
    ideas: tuple[ShelfIdea, ...],
    enabled_ids: set[str],
    *,
    hysteresis_below_70: bool = False,
) -> RamGuardDecision:
    """Decide which enabled non-core flags to shed."""
    core_kept = tuple(i.id for i in ideas if i.core and i.id in enabled_ids)
    if ram_used_pct < SOFT_PCT:
        if hysteresis_below_70 and ram_used_pct >= REENABLE_PCT:
            pass
        return RamGuardDecision("OK", (), core_kept, "ram below soft threshold")

    enabled_non_core = [
        i for i in ideas if i.id in enabled_ids and not i.core
    ]
    enabled_non_core.sort(key=lambda i: (i.priority, i.id))

    if ram_used_pct >= HARD_PCT:
        shed = tuple(i.id for i in enabled_non_core)
        return RamGuardDecision("HARD", shed, core_kept, "hard 90% — shed all non-core")

    # soft 80%: shed lowest priority non-core one at a time (lowest priority number = shed first)
    if not enabled_non_core:
        return RamGuardDecision("SOFT", (), core_kept, "soft 80% but no non-core enabled")
    victim = enabled_non_core[0]
    return RamGuardDecision("SOFT", (victim.id,), core_kept, "soft 80% — shed lowest priority non-core")
