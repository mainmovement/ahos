#!/usr/bin/env python3
"""AHOS Crypto News & Narrative Collector.

Pulls keyless public RSS/Atom feeds (CoinTelegraph, CoinDesk, The Block, Decrypt,
CryptoSlate) and turns headlines into a bounded, auditable narrative signal.

NON-NEGOTIABLE LAWS
-------------------
  - $0 COST: RSS only. No paid news API, ever.
  - STDLIB ONLY: parses with xml.etree — `feedparser` is optional, never required.
  - NARRATIVE IS NOT PROOF: the output is a bounded modifier in [-1.0, +1.0] with
    an explicit evidence list. It can NEVER by itself justify a BUY, and it can
    NEVER override a security veto. DATA > AI > NARRATIVE.
  - NO FABRICATION: an unreachable feed yields error_state, never a neutral 0.0
    pretending to be an observation. Zero feeds reachable => UNKNOWN, not calm.
  - IRAN-RESILIENT: every fetch honours HTTPS_PROXY/ALL_PROXY and degrades to
    UNKNOWN instead of raising when a feed is filtered.

The lexicon is deliberately small, explicit and auditable. A hand-checkable word
list beats an opaque sentiment model you cannot debug at 3am.
"""
from __future__ import annotations

import hashlib
import re
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

UA = {"User-Agent": "ahos-intel/1.0 (+research; non-commercial)"}

# ---------------------------------------------------------------------------
# Free, keyless, no-signup RSS feeds. Add/remove freely — the collector treats
# the list as data and degrades gracefully when any subset is unreachable.
# ---------------------------------------------------------------------------
DEFAULT_FEEDS: dict[str, str] = {
    "cointelegraph": "https://cointelegraph.com/rss",
    "coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "decrypt": "https://decrypt.co/feed",
    "cryptoslate": "https://cryptoslate.com/feed/",
    "bitcoinmagazine": "https://bitcoinmagazine.com/feed",
}

# --- Auditable sentiment lexicon -------------------------------------------
# Weights are intentionally coarse. Precision here is false precision.
BULLISH_TERMS: dict[str, float] = {
    "surge": 1.0, "soar": 1.0, "rally": 0.9, "breakout": 0.9, "all-time high": 1.0,
    "ath": 0.8, "adoption": 0.7, "partnership": 0.7, "listing": 0.8, "listed": 0.7,
    "upgrade": 0.6, "integration": 0.6, "bullish": 0.9, "gains": 0.7, "soars": 1.0,
    "jumps": 0.8, "surges": 1.0, "approval": 0.9, "approved": 0.9, "etf": 0.6,
    "institutional": 0.6, "accumulation": 0.7, "buyback": 0.7, "burn": 0.5,
    "mainnet": 0.6, "launch": 0.5, "funding": 0.6, "raises": 0.6,
}

BEARISH_TERMS: dict[str, float] = {
    "hack": -1.0, "hacked": -1.0, "exploit": -1.0, "rug": -1.0, "rugpull": -1.0,
    "scam": -1.0, "fraud": -1.0, "lawsuit": -0.8, "sued": -0.8, "sec charges": -0.9,
    "investigation": -0.7, "crash": -1.0, "plunge": -0.9, "plunges": -0.9,
    "dump": -0.8, "dumps": -0.8, "bearish": -0.8, "selloff": -0.8, "sell-off": -0.8,
    "delisting": -0.9, "delisted": -0.9, "halt": -0.7, "halted": -0.7,
    "bankruptcy": -1.0, "insolvent": -1.0, "collapse": -1.0, "drain": -0.9,
    "vulnerability": -0.8, "backdoor": -1.0, "honeypot": -1.0, "ban": -0.8,
    "banned": -0.8, "warning": -0.5, "liquidated": -0.7, "liquidation": -0.7,
}

# Terms that mark a headline as HIGH-IMPACT regardless of direction.
HIGH_IMPACT_TERMS = {
    "sec", "etf", "hack", "exploit", "bankruptcy", "ban", "regulation",
    "federal reserve", "cpi", "rate cut", "rate hike",
}


@dataclass
class NewsItem:
    """A single normalized headline with provenance."""
    title: str
    link: str
    source: str
    published_ts: float | None            # None = feed omitted a parseable date
    summary: str = ""
    item_sha256: str = ""

    def __post_init__(self):
        if not self.item_sha256:
            self.item_sha256 = hashlib.sha256(
                f"{self.source}|{self.title}|{self.link}".encode("utf-8")
            ).hexdigest()

    @property
    def text(self) -> str:
        return f"{self.title} {self.summary}".lower()


@dataclass
class NarrativeSignal:
    """Bounded, explainable narrative verdict for a symbol or the whole market."""
    subject: str                                   # symbol, or "MARKET"
    sentiment: float                               # [-1.0, +1.0]; 0.0 only when observed-neutral
    label: str                                     # BULLISH | BEARISH | NEUTRAL | UNKNOWN
    mention_count: int
    high_impact_count: int
    matched_terms: list[str] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    feeds_ok: list[str] = field(default_factory=list)
    feeds_failed: list[dict[str, str]] = field(default_factory=list)
    computed_ts: float = field(default_factory=time.time)
    error_state: dict[str, Any] | None = None

    @property
    def is_known(self) -> bool:
        return self.label != "UNKNOWN"

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "sentiment": self.sentiment,
            "label": self.label,
            "mention_count": self.mention_count,
            "high_impact_count": self.high_impact_count,
            "matched_terms": self.matched_terms,
            "evidence": self.evidence,
            "feeds_ok": self.feeds_ok,
            "feeds_failed": self.feeds_failed,
            "computed_ts": self.computed_ts,
            "error_state": self.error_state,
        }


def _parse_date(raw: str | None) -> float | None:
    """RFC-822 / ISO-8601 -> epoch. Unparseable => None (never time.time())."""
    if not raw:
        return None
    raw = raw.strip()
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S",
    ):
        try:
            from datetime import datetime
            dt = datetime.strptime(raw, fmt)
            return dt.timestamp()
        except (ValueError, OverflowError):
            continue
    return None


_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(s: str) -> str:
    return _TAG_RE.sub(" ", s or "").strip()


def _local(tag: str) -> str:
    """Strip XML namespace: '{http://...}entry' -> 'entry'."""
    return tag.rsplit("}", 1)[-1].lower()


def parse_feed(xml_bytes: bytes, source: str) -> list[NewsItem]:
    """Parse RSS 2.0 or Atom with the standard library. Never raises on junk."""
    items: list[NewsItem] = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return items

    for node in root.iter():
        if _local(node.tag) not in ("item", "entry"):
            continue
        title = link = summary = date_raw = ""
        for child in node:
            name = _local(child.tag)
            if name == "title":
                title = (child.text or "").strip()
            elif name == "link":
                link = (child.get("href") or child.text or "").strip()
            elif name in ("description", "summary", "content"):
                summary = _strip_html(child.text or "")[:400]
            elif name in ("pubdate", "published", "updated"):
                date_raw = (child.text or "").strip()
        if title:
            items.append(NewsItem(
                title=title, link=link, source=source,
                published_ts=_parse_date(date_raw), summary=summary,
            ))
    return items


class NewsCollector:
    """Fetches and scores crypto news. Deterministic given the same inputs."""

    def __init__(self,
                 feeds: dict[str, str] | None = None,
                 timeout_sec: float = 12.0,
                 transport: Callable = urllib.request.urlopen):
        self.feeds = dict(feeds or DEFAULT_FEEDS)
        self.timeout_sec = timeout_sec
        self._transport = transport

    # -- fetching -----------------------------------------------------------
    def fetch_all(self) -> tuple[list[NewsItem], list[str], list[dict[str, str]]]:
        """Returns (items, feeds_ok, feeds_failed). Never raises on network error."""
        items: list[NewsItem] = []
        ok: list[str] = []
        failed: list[dict[str, str]] = []

        for name, url in self.feeds.items():
            try:
                req = urllib.request.Request(url, headers=UA)
                with self._transport(req, timeout=self.timeout_sec) as resp:
                    payload = resp.read()
                parsed = parse_feed(payload, name)
                if parsed:
                    items.extend(parsed)
                    ok.append(name)
                else:
                    failed.append({"feed": name, "error": "empty_or_unparseable"})
            except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as e:
                # Filtered / offline / TLS-blocked: recorded honestly, never faked.
                failed.append({"feed": name, "error": f"{type(e).__name__}: {str(e)[:120]}"})
        return items, ok, failed

    # -- scoring ------------------------------------------------------------
    @staticmethod
    def score_text(text: str) -> tuple[float, list[str], int]:
        """Score one text. Returns (raw_score, matched_terms, high_impact_hits)."""
        low = text.lower()
        score = 0.0
        matched: list[str] = []
        for term, weight in {**BULLISH_TERMS, **BEARISH_TERMS}.items():
            if term in low:
                score += weight
                matched.append(term)
        impact = sum(1 for t in HIGH_IMPACT_TERMS if t in low)
        return score, matched, impact

    def analyze(self,
                subject: str = "MARKET",
                keywords: Iterable[str] | None = None,
                items: list[NewsItem] | None = None,
                max_age_sec: float | None = 86400.0,
                now: float | None = None,
                feeds_ok: list[str] | None = None,
                feeds_failed: list[dict[str, str]] | None = None) -> NarrativeSignal:
        """Produce a bounded narrative signal for `subject`.

        `keywords` filters headlines (e.g. a token symbol + name). When omitted the
        whole feed is treated as market-wide context.

        When `items` is supplied (shared prefetch for a pipeline run), optional
        `feeds_ok` / `feeds_failed` preserve fetch provenance so unreachable
        feeds remain UNKNOWN rather than silent.
        """
        ts = time.time() if now is None else now
        ok: list[str] = list(feeds_ok or [])
        failed: list[dict[str, str]] = list(feeds_failed or [])

        if items is None:
            items, ok, failed = self.fetch_all()

        # HONESTY GATE: zero reachable feeds is UNKNOWN, never "neutral".
        if not items and failed:
            return NarrativeSignal(
                subject=subject, sentiment=0.0, label="UNKNOWN",
                mention_count=0, high_impact_count=0,
                feeds_ok=ok, feeds_failed=failed, computed_ts=ts,
                error_state={"kind": "all_feeds_unreachable",
                             "detail": "no narrative evidence available"},
            )

        # Age filter — stale news is not current narrative.
        if max_age_sec is not None:
            items = [i for i in items
                     if i.published_ts is None or (ts - i.published_ts) <= max_age_sec]

        # Keyword filter.
        keys = [k.lower() for k in (keywords or []) if k and len(str(k)) >= 2]
        if keys:
            items = [i for i in items if any(k in i.text for k in keys)]

        if not items:
            return NarrativeSignal(
                subject=subject, sentiment=0.0, label="UNKNOWN",
                mention_count=0, high_impact_count=0,
                feeds_ok=ok, feeds_failed=failed, computed_ts=ts,
                error_state={"kind": "no_matching_coverage",
                             "detail": f"no headlines matched {subject}"},
            )

        total = 0.0
        all_terms: list[str] = []
        impact_total = 0
        evidence: list[dict[str, Any]] = []

        for item in items:
            s, terms, impact = self.score_text(item.text)
            total += s
            all_terms.extend(terms)
            impact_total += impact
            if terms:
                evidence.append({
                    "title": item.title[:160],
                    "source": item.source,
                    "link": item.link,
                    "score": round(s, 3),
                    "terms": terms,
                    "sha256": item.item_sha256[:16],
                })

        # Normalise by mention count, then clamp. Bounded by construction so a
        # single hysterical headline cannot dominate the decision.
        raw = total / max(len(items), 1)
        sentiment = max(-1.0, min(1.0, raw))

        if sentiment >= 0.25:
            label = "BULLISH"
        elif sentiment <= -0.25:
            label = "BEARISH"
        else:
            label = "NEUTRAL"

        return NarrativeSignal(
            subject=subject,
            sentiment=round(sentiment, 4),
            label=label,
            mention_count=len(items),
            high_impact_count=impact_total,
            matched_terms=sorted(set(all_terms)),
            evidence=evidence[:12],
            feeds_ok=ok,
            feeds_failed=failed,
            computed_ts=ts,
        )
