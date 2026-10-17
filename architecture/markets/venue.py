"""M23 venue admission. Live orders stay refused.

A venue that is not ELIGIBLE cannot be used. ELIGIBLE still means paper only.
"""
from __future__ import annotations

from dataclasses import dataclass

ELIGIBLE = "ELIGIBLE"


@dataclass(frozen=True, slots=True)
class Admission:
    allowed: bool
    reason: str
    live: bool


def admit(verdict: str, *, live: bool) -> Admission:
    if live:
        return Admission(False, "live orders are refused", False)
    if verdict != ELIGIBLE:
        return Admission(False, "venue is not eligible", False)
    return Admission(True, "paper only", False)
