#!/usr/bin/env python3
"""AHOS Catalyst Detector (Lane B intel — P1-3).

Deterministic, provenance-aware catalyst extraction from news headlines and
optional structured fields. Does NOT invent listings or partnerships.

Every catalyst carries: source, timestamp, confidence, freshness, evidence.
When no matching headlines exist → empty catalog with UNKNOWN status (honest).
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any, Iterable

CATALYST_VERSION = "AHOS-CATALYST-v1"

# keyword → catalyst kind (auditable lexicon)
_CATALYST_PATTERNS: list[tuple[str, re.Pattern[str], float]] = [
    ("LISTING", re.compile(r"\b(listing|listed|lists on|lists onto)\b", re.I), 0.7),
    ("LAUNCH", re.compile(r"\b(launch|launches|launched|mainnet|goes live)\b", re.I), 0.6),
    ("PARTNERSHIP", re.compile(r"\b(partnership|partners with|collaborat)\b", re.I), 0.65),
    ("UPGRADE", re.compile(r"\b(upgrade|hard fork|protocol upgrade|v\d+)\b", re.I), 0.55),
    ("GOVERNANCE", re.compile(r"\b(governance|proposal|snapshot vote|dao vote)\b", re.I), 0.5),
    ("RELEASE", re.compile(r"\b(release|airdrop|token generation|tge)\b", re.I), 0.55),
    ("REGULATION", re.compile(r"\b(sec|etf|approval|approved|regulation)\b", re.I), 0.75),
]


@dataclass
class CatalystEvent:
    kind: str
    title: str
    source: str
    link: str
    timestamp: float | None
    confidence: float
    freshness_seconds: float | None
    evidence_sha16: str
    matched_term: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "title": self.title,
            "source": self.source,
            "link": self.link,
            "timestamp": self.timestamp,
            "confidence": self.confidence,
            "freshness_seconds": self.freshness_seconds,
            "evidence_sha16": self.evidence_sha16,
            "matched_term": self.matched_term,
        }


@dataclass
class CatalystReport:
    subject: str
    status: str                     # FOUND | NONE | UNKNOWN
    events: list[CatalystEvent] = field(default_factory=list)
    feeds_considered: int = 0
    computed_ts: float = field(default_factory=time.time)
    version: str = CATALYST_VERSION
    error_state: dict[str, Any] | None = None

    @property
    def is_known(self) -> bool:
        return self.status in ("FOUND", "NONE")

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "status": self.status,
            "events": [e.to_dict() for e in self.events],
            "feeds_considered": self.feeds_considered,
            "computed_ts": self.computed_ts,
            "version": self.version,
            "error_state": self.error_state,
        }


class CatalystDetector:
    """Extract catalysts from NewsItem-like objects (title/summary/source/...)."""

    def detect(
        self,
        candidate: Any = None,
        *,
        news_items: Iterable[Any] | None = None,
        now: float | None = None,
        max_age_sec: float = 86400.0 * 3,
    ) -> CatalystReport:
        ts = time.time() if now is None else now
        symbol = str(getattr(candidate, "symbol", "") or "").strip() if candidate else ""
        name = str(getattr(candidate, "name", "") or "").strip() if candidate else ""
        subject = symbol or name or "MARKET"
        keys = [k.lower() for k in (symbol, name) if k and len(k) >= 2]

        items = list(news_items or [])
        if not items:
            return CatalystReport(
                subject=subject,
                status="UNKNOWN",
                feeds_considered=0,
                computed_ts=ts,
                error_state={
                    "kind": "no_news_items",
                    "detail": "catalyst detector requires news items; none supplied",
                },
            )

        events: list[CatalystEvent] = []
        considered = 0
        for item in items:
            title = str(getattr(item, "title", "") or "")
            summary = str(getattr(item, "summary", "") or "")
            text = f"{title} {summary}"
            low = text.lower()
            pub = getattr(item, "published_ts", None)
            if pub is not None and (ts - float(pub)) > max_age_sec:
                continue
            if keys and not any(k in low for k in keys):
                # market-wide catalysts still allowed when subject is MARKET
                if subject != "MARKET":
                    continue
            considered += 1
            for kind, pattern, conf in _CATALYST_PATTERNS:
                m = pattern.search(text)
                if not m:
                    continue
                sha = str(getattr(item, "item_sha256", "") or "")[:16]
                freshness = (ts - float(pub)) if pub is not None else None
                events.append(CatalystEvent(
                    kind=kind,
                    title=title[:160],
                    source=str(getattr(item, "source", "") or "unknown"),
                    link=str(getattr(item, "link", "") or ""),
                    timestamp=float(pub) if pub is not None else None,
                    confidence=conf,
                    freshness_seconds=freshness,
                    evidence_sha16=sha,
                    matched_term=m.group(0).lower(),
                ))
                break  # one kind per headline

        # Deduplicate by sha+kind
        seen: set[str] = set()
        uniq: list[CatalystEvent] = []
        for ev in events:
            key = f"{ev.kind}:{ev.evidence_sha16}:{ev.title[:40]}"
            if key in seen:
                continue
            seen.add(key)
            uniq.append(ev)

        status = "FOUND" if uniq else "NONE"
        return CatalystReport(
            subject=subject,
            status=status,
            events=uniq[:20],
            feeds_considered=considered,
            computed_ts=ts,
        )
