"""M59.1 source registry. No license or a duplicate URL is dropped. Nothing is fetched."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Source:
    url: str
    license_name: str


@dataclass(frozen=True, slots=True)
class Registry:
    kept: tuple[str, ...]
    dropped: int
    fetched: int


def register(sources: list[Source]) -> Registry:
    seen: set[str] = set()
    kept: list[str] = []
    dropped = 0
    for source in sources:
        url = source.url.strip()
        if not source.license_name.strip() or url in seen or not url:
            dropped += 1
            continue
        seen.add(url)
        kept.append(url)
    return Registry(tuple(kept), dropped, 0)
