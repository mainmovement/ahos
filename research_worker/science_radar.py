"""M44 science radar over already-fetched records.

No network and no code execution. Duplicates collapse. A record that tries to
carry executable text is dropped.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_CODE = re.compile(r"\b(exec|eval|__import__|subprocess|os\.system)\s*\(", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class Record:
    source: str
    external_id: str
    title: str
    summary: str


@dataclass(frozen=True, slots=True)
class RadarItem:
    source: str
    external_id: str
    title: str
    summary: str
    score: int


@dataclass(frozen=True, slots=True)
class RadarBatch:
    kept: tuple[RadarItem, ...]
    dropped: int
    executed: int


def _score(title: str, summary: str) -> int:
    text = f"{title} {summary}".lower()
    hits = 0
    for word in ("risk", "paper", "calibration", "ledger", "market"):
        if word in text:
            hits += 1
    return hits


def ingest(records: list[Record] | tuple[Record, ...]) -> RadarBatch:
    seen: set[tuple[str, str]] = set()
    seen_titles: set[str] = set()
    kept: list[RadarItem] = []
    dropped = 0
    for row in records:
        if _CODE.search(row.title) or _CODE.search(row.summary):
            dropped += 1
            continue
        key = (row.source.strip().lower(), row.external_id.strip())
        title_key = " ".join(row.title.lower().split())
        if key in seen or title_key in seen_titles:
            dropped += 1
            continue
        seen.add(key)
        seen_titles.add(title_key)
        kept.append(RadarItem(
            source=row.source,
            external_id=row.external_id,
            title=row.title,
            summary=row.summary,
            score=_score(row.title, row.summary),
        ))
    kept.sort(key=lambda item: (-item.score, item.external_id))
    return RadarBatch(tuple(kept), dropped, 0)
