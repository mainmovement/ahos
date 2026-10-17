"""M37 frontier model slots. Locked slots are never selected.

An order path cannot receive a slot. A full budget cap locks the slot.
"""
from __future__ import annotations

from dataclasses import dataclass

LOCKED = "LOCKED_PENDING_KEY_AND_OWNER_BUDGET"
OPEN = "OPEN"


@dataclass(frozen=True, slots=True)
class FrontierSlot:
    name: str
    state: str
    spent_ratio: float


class OrderPathError(RuntimeError):
    pass


def choose_slot(slots: list[FrontierSlot] | tuple[FrontierSlot, ...], *, purpose: str) -> FrontierSlot | None:
    if purpose == "order":
        raise OrderPathError("a frontier slot cannot sit on an order path")
    for slot in slots:
        if slot.spent_ratio >= 1.0:
            continue
        if slot.state != OPEN:
            continue
        return slot
    return None
