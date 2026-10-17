"""M28 paper strategy ranking. The winner is not promoted."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ArenaResult:
    winner: str | None
    promoted: bool


def rank(scores: dict[str, float]) -> ArenaResult:
    if not scores:
        return ArenaResult(None, False)
    winner = max(scores, key=lambda name: scores[name])
    return ArenaResult(winner, False)
