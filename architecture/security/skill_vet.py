"""M52 skill vetting. No license or an install request is refused. Nothing is installed."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VetResult:
    accepted: bool
    reason: str
    installed: bool
    merge: bool


def vet(*, spdx: str, requested_install: bool) -> VetResult:
    if requested_install:
        return VetResult(False, "install refused", False, False)
    if not spdx.strip():
        return VetResult(False, "spdx required", False, False)
    return VetResult(True, "shelf only", False, False)
