"""M57 team registration. Authority stays NONE. Teams are not auto-created."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TeamVerdict:
    accepted: bool
    reason: str


def register_team(*, authority: str, auto_create: bool) -> TeamVerdict:
    if auto_create:
        return TeamVerdict(False, "auto-create refused")
    if authority != "NONE":
        return TeamVerdict(False, "authority must be NONE")
    return TeamVerdict(True, "recorded")
