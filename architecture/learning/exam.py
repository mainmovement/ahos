"""M50 exam grader. Held-out overlap is a leak. The score cannot promote."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExamResult:
    score: float
    leaked: bool
    promoted: bool


def grade(key: dict[str, str], answers: dict[str, str], training_ids: set[str]) -> ExamResult:
    overlap = set(key) & set(training_ids)
    if overlap:
        return ExamResult(0.0, True, False)
    if not key:
        return ExamResult(0.0, False, False)
    correct = sum(1 for item, want in key.items() if answers.get(item) == want)
    return ExamResult(correct / len(key), False, False)
