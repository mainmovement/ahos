"""A prior over strategies. It does not open a trade and it does not replace family votes."""
from __future__ import annotations

import random
from typing import Any

KELLY_CAP = 0.25


def thompson_weights(
    ids: list[str],
    *,
    seed: int = 7,
    outcomes: dict[str, tuple[int, int]] | None = None,
) -> dict[str, Any]:
    """Beta(1, 1) until a shadow round trip exists. The draw does not open a trade."""
    rng = random.Random(seed)
    if not ids:
        return {"mode": "EMPTY", "weights": {}, "applied_to_live": False, "kelly_cap": KELLY_CAP}
    book = outcomes or {}
    used = any((wins or losses) for wins, losses in book.values())
    draws = {}
    for name in ids:
        wins, losses = book.get(name, (0, 0))
        draws[name] = rng.betavariate(1.0 + wins, 1.0 + losses)
    total = sum(draws.values()) or 1.0
    weights = {name: round(value / total, 6) for name, value in draws.items()}
    return {
        "mode": "SHADOW_LOOKBACK" if used else "PRIOR_THOMPSON",
        "reason": (
            "Shadow round trips updated the prior. They are not fresh closes."
            if used
            else "No fresh paper closes entered the posterior."
        ),
        "weights": weights,
        "kelly_cap": KELLY_CAP,
        "kelly": None,
        "can_open_without_family_votes": False,
        "applied_to_live": False,
    }


def capped_kelly(edge: float | None, odds: float | None) -> float | None:
    """Full Kelly clipped by KELLY_CAP. A missing edge stays missing."""
    if edge is None or odds is None or odds <= 0:
        return None
    full = edge / odds
    if full <= 0:
        return 0.0
    return round(min(KELLY_CAP, full), 4)
