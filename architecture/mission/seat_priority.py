"""Which empty seats this mission fills.

The order is a pre-registered judgment of where a new module changes the paper
book: first the path that was rewriting live weights, then the path that names
why a close lost. Seats further down stay empty until they have a module and a
test of their own. This list is not a fitted weight.
"""
from __future__ import annotations

from typing import Any

# agent_id, why it is ahead of the remaining empty seats.
PRIORITY: tuple[tuple[str, str], ...] = (
    ("AG-18", "The learning loop records each close and stops a hit rate from editing a live weight."),
    ("AG-19", "The daily diagnosis names one loss cause and replays the fix in shadow."),
    ("AG-40", "Mistake memory shrinks or vetoes a repeated paper loss and does not write a weight."),
    ("AG-34", "Candle patterns are an entry family. They do not decide alone."),
    ("AG-33", "Desk news stays at weight 0. A pump headline still needs another family and the safety veto."),
)


def rank_unfilled(doc: dict[str, Any]) -> list[dict[str, str]]:
    unfilled = {row["agent_id"] for row in doc.get("unfilled_seats") or []}
    return [
        {"agent_id": agent_id, "why": why}
        for agent_id, why in PRIORITY
        if agent_id in unfilled
    ]
