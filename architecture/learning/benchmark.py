"""M58.4 benchmark history. Recording a score does not move a gate."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BenchPoint:
    name: str
    score: float


def record(history: list[BenchPoint], name: str, score: float) -> tuple[list[BenchPoint], bool]:
    history.append(BenchPoint(name, score))
    return history, False
