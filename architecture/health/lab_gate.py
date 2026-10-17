"""M45 lab gate. Isolation is not assumed, so no child process is started."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LabGate:
    available: bool
    spawned: bool
    reason: str


def lab_status(*, low_priv_configured: bool) -> LabGate:
    if not low_priv_configured:
        return LabGate(False, False, "owner isolation is absent")
    return LabGate(False, False, "a flag is not isolation; spawn refused")
