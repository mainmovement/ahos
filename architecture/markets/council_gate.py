"""M15 council advice. Votes cannot change the tier."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CouncilAdvice:
    tier: str
    promoted: bool


def advise(*, votes_to_promote: int, votes: int, tier: str) -> CouncilAdvice:
    if votes < 1 or votes_to_promote > votes:
        return CouncilAdvice(tier, False)
    return CouncilAdvice(tier, False)
