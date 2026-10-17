"""M53 quarantine plan. The plan names trees. It does not delete them."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QuarantinePlan:
    paths: tuple[str, ...]
    deleted: int


def plan(paths: list[str]) -> QuarantinePlan:
    named = tuple(sorted({p.replace("\\", "/") for p in paths if p.strip()}))
    return QuarantinePlan(named, 0)


def delete_paths(_paths: list[str]) -> None:
    raise PermissionError("M53 cannot delete files")
