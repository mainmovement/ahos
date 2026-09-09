"""Novelty classification. Novelty is not truth."""

from __future__ import annotations

from enum import Enum
from typing import Any


class NoveltyClass(str, Enum):
    KNOWN = "KNOWN"
    KNOWN_BUT_UNCERTAIN = "KNOWN_BUT_UNCERTAIN"
    UNKNOWN = "UNKNOWN"
    CONTRADICTORY = "CONTRADICTORY"
    NOVEL = "NOVEL"
    POTENTIALLY_IMPORTANT_NOVELTY = "POTENTIALLY_IMPORTANT_NOVELTY"


def classify_novelty(
    *,
    seen_before: bool,
    evidence_conflict: bool,
    confidence: float | None,
    importance_hint: bool = False,
) -> dict[str, Any]:
    """Return a novelty envelope. Does not promote claims to knowledge."""
    if evidence_conflict:
        klass = NoveltyClass.CONTRADICTORY
    elif not seen_before:
        klass = (
            NoveltyClass.POTENTIALLY_IMPORTANT_NOVELTY
            if importance_hint
            else NoveltyClass.NOVEL
        )
    elif confidence is None:
        klass = NoveltyClass.UNKNOWN
    elif confidence < 0.5:
        klass = NoveltyClass.KNOWN_BUT_UNCERTAIN
    else:
        klass = NoveltyClass.KNOWN
    return {
        "class": klass.value,
        "novelty_equals_truth": False,
        "auto_promote": False,
        "next_action": "investigate" if klass != NoveltyClass.KNOWN else "retain",
        "notes": (
            "A novelty signal must lead to investigation, not automatic promotion."
        ),
    }
