"""M18.N news desk. One source is unknown. Disagreement is conflict. No fetch."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NewsView:
    state: str
    claim: str | None


def corroborate(items: list[tuple[str, str]]) -> NewsView:
    if len({source for source, _claim in items}) < 2:
        return NewsView("UNKNOWN", None)
    claims = {claim for _source, claim in items}
    if len(claims) != 1:
        return NewsView("CONFLICT", None)
    return NewsView("CORROBORATED", next(iter(claims)))
