#!/usr/bin/env python3
"""AHOS Social Intelligence — canonical source → evidence pipeline.

Vision: Social is a first-class capability, not "RSS only". This module is
the single home for social *collection contracts*. It does not scrape
platforms, steal credentials, or bypass ToS. Every source has an honest
status; live claims are never made for blocked sources.

Pipeline (every source, even blocked ones, is named in this order):

    SOURCE → COLLECTION → NORMALIZATION → PROVENANCE → DEDUPLICATION
         → BOT/WASH DETECTION → VIRALITY → SENTIMENT/NARRATIVE → EVIDENCE

Laws
----
  * Social NEVER produces a BUY / opportunity score by itself.
  * UNKNOWN stays UNKNOWN. False-on-missing is forbidden.
  * OBSERVED / DERIVED / UNKNOWN are distinct.
  * No illegal scraping, no credential theft, no paid API without config.
  * Author identity is UNKNOWN unless the source actually supplied it.
"""
from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Iterable

from .news import NewsCollector, NewsItem, NarrativeSignal

SOCIAL_VERSION = "AHOS-SOCIAL-v1"

# ---------------------------------------------------------------------------
# Source registry — the architecture truth for social. Status is the product.
# ---------------------------------------------------------------------------
# IMPLEMENTED          collector exists, offline-testable, no live claim
# AUTH_REQUIRED        official API exists; inert without a key
# COST_BLOCKED         paid-only official API ($0 ceiling)
# OUT_OF_POLICY        would require scraping / ToS-gray user-session access
# EXTERNALLY_BLOCKED   reachable in principle, live egress not assumed here

SOURCE_STATUS_VOCAB = (
    "IMPLEMENTED",
    "AUTH_REQUIRED",
    "COST_BLOCKED",
    "OUT_OF_POLICY",
    "EXTERNALLY_BLOCKED",
)


@dataclass(frozen=True)
class SocialSource:
    source_id: str
    platform: str
    collection: str
    status: str
    reason: str
    live_claim: str = "NONE"          # NEVER "LIVE" without a probe artifact
    key_env: str | None = None
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


SOCIAL_SOURCE_REGISTRY: dict[str, SocialSource] = {
    "rss": SocialSource(
        source_id="rss", platform="rss/news",
        collection="keyless public RSS/Atom via architecture.intel.news",
        status="IMPLEMENTED",
        reason="CoinTelegraph/CoinDesk/Decrypt/CryptoSlate/BitcoinMagazine RSS; stdlib parser",
        live_claim="NONE",
        notes="Narrative is evidence, never proof. Unreachable feed → UNKNOWN.",
    ),
    "github": SocialSource(
        source_id="github", platform="github",
        collection="public GitHub search/events API (keyless, 60 req/h anon)",
        status="IMPLEMENTED",
        reason="dev-activity / mention search; official public API, no scraping",
        live_claim="NONE",
        key_env="GITHUB_TOKEN",
        notes="Optional token raises rate limit; absence is not AUTH_REQUIRED (anon works).",
    ),
    "reddit": SocialSource(
        source_id="reddit", platform="reddit",
        collection="official Reddit OAuth JSON",
        status="AUTH_REQUIRED",
        reason="Reddit no longer serves unauthenticated JSON; OAuth client required",
        live_claim="NONE",
        key_env="REDDIT_CLIENT_ID",
        notes="No scraping of old.reddit / blocked JSON. Adapter returns AUTH_REQUIRED.",
    ),
    "x_twitter": SocialSource(
        source_id="x_twitter", platform="x/twitter",
        collection="official X API",
        status="COST_BLOCKED",
        reason="X API is paid-only; violates $0 ceiling unless operator authorizes spend",
        live_claim="NONE",
        key_env="X_BEARER_TOKEN",
        notes="No scraping. No unofficial syndication.",
    ),
    "telegram_channels": SocialSource(
        source_id="telegram_channels", platform="telegram",
        collection="Telethon user-session / MTProto",
        status="OUT_OF_POLICY",
        reason="Public-channel harvest via a user account is ToS-gray; AHOS Telegram is UX, not a scrape plane",
        live_claim="NONE",
        notes="Primary Telegram surface remains telegram_ai (operator UX).",
    ),
    "instagram": SocialSource(
        source_id="instagram", platform="instagram",
        collection="none",
        status="OUT_OF_POLICY",
        reason="No official free research API; scraping is ToS-violating",
        live_claim="NONE",
    ),
    "tiktok": SocialSource(
        source_id="tiktok", platform="tiktok",
        collection="none",
        status="OUT_OF_POLICY",
        reason="No official free research API; scraping is ToS-violating",
        live_claim="NONE",
    ),
    "youtube": SocialSource(
        source_id="youtube", platform="youtube",
        collection="YouTube Data API v3",
        status="AUTH_REQUIRED",
        reason="Official API is key-gated (YOUTUBE_API_KEY); no scraping",
        live_claim="NONE",
        key_env="YOUTUBE_API_KEY",
    ),
    "web_public": SocialSource(
        source_id="web_public", platform="web",
        collection="none (no crawler)",
        status="OUT_OF_POLICY",
        reason="Open-web crawling is out of policy; RSS + official APIs only",
        live_claim="NONE",
    ),
}


def source_registry() -> dict[str, dict[str, Any]]:
    return {k: v.as_dict() for k, v in SOCIAL_SOURCE_REGISTRY.items()}


# ---------------------------------------------------------------------------
# Normalized event + pipeline envelopes
# ---------------------------------------------------------------------------

@dataclass
class SocialEvent:
    """One normalized social/news item with provenance. Author may be UNKNOWN."""
    event_id: str
    source_id: str
    platform: str
    text: str
    text_hash: str
    url: str
    retrieved_ts: float
    published_ts: float | None = None          # None = UNKNOWN, never time.time()
    author_ref: str | None = None              # None = UNKNOWN
    language: str | None = None
    token_refs: tuple[str, ...] = ()
    raw_sha256: str = ""
    collector_version: str = SOCIAL_VERSION
    observation_kind: str = "OBSERVED"         # OBSERVED only — never invented

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["token_refs"] = list(self.token_refs)
        return d


@dataclass
class SocialCollectionResult:
    source_id: str
    status: str                 # OK | EMPTY | AUTH_REQUIRED | COST_BLOCKED |
                                # OUT_OF_POLICY | DOWN | ERROR | UNKNOWN
    events: list[SocialEvent] = field(default_factory=list)
    error_message: str | None = None
    live_claim: str = "NONE"

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "status": self.status,
            "event_count": len(self.events),
            "events": [e.as_dict() for e in self.events],
            "error_message": self.error_message,
            "live_claim": self.live_claim,
        }


@dataclass
class BotWashAssessment:
    """Bot / wash / coordination heuristics. Honesty-first.

    RSS and most keyless sources do not carry author identity, account age,
    or engagement graphs. Those dimensions stay UNKNOWN — they are never
    reported as 'not a bot'.
    """
    subject: str
    recycled_content: bool | None          # True/False only if hashes observed
    coordinated_timing: bool | None        # True/False only if ≥2 timestamps
    unique_author_ratio: float | None      # None unless authors observed
    paid_promo_markers: bool | None        # True if lexicon hit; None if no text
    confidence: str                        # OBSERVED | DERIVED | UNKNOWN
    unknowns: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SocialIntelligenceReport:
    """Closed social verdict for one subject. Never a trade decision."""
    subject: str
    sources: dict[str, dict[str, Any]]
    events_collected: int
    events_after_dedup: int
    narrative: dict[str, Any] | None
    bot_wash: dict[str, Any]
    mention_velocity_1h: float | None
    cross_source_propagation: int | None   # distinct sources with a match
    unknowns: list[str]
    computed_ts: float
    version: str = SOCIAL_VERSION
    # Social cannot create an opportunity. Disposition is informational.
    decision_floor: str = "SOCIAL_IS_EVIDENCE_NOT_PROOF"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# Paid-promo / shill phrase bank — versioned, reviewable, small on purpose.
_PAID_PROMO_MARKERS = (
    "sponsored", "paid promotion", "advertisement", "#ad", "promoted by",
    "airdrop alert", "guaranteed profit",
)


def _text_hash(text: str) -> str:
    norm = re.sub(r"\s+", " ", (text or "").strip().lower())
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def _event_id(source_id: str, url: str, text_hash: str) -> str:
    return hashlib.sha256(f"{source_id}|{url}|{text_hash}".encode("utf-8")).hexdigest()[:16]


def normalize_news_item(item: NewsItem, *, retrieved_ts: float,
                        token_refs: Iterable[str] = ()) -> SocialEvent:
    """NewsItem → SocialEvent (RSS collection → normalization)."""
    text = f"{item.title} {item.summary}".strip()
    th = _text_hash(text)                         # content fingerprint (dedupe)
    raw = item.item_sha256 or th                  # item identity (includes URL)
    return SocialEvent(
        event_id=_event_id("rss", item.link, raw),
        source_id="rss",
        platform="rss/news",
        text=text,
        text_hash=th,
        url=item.link or "",
        retrieved_ts=retrieved_ts,
        published_ts=item.published_ts,          # may be None
        author_ref=None,                         # RSS typically has no author
        language=None,
        token_refs=tuple(r for r in token_refs if r),
        raw_sha256=raw,
    )


def stamp_provenance(event: SocialEvent) -> SocialEvent:
    """Provenance is already on the event; re-stamp empty hashes only."""
    if event.text_hash:
        return event
    th = _text_hash(event.text)
    event.text_hash = th
    event.raw_sha256 = event.raw_sha256 or th
    event.event_id = event.event_id or _event_id(event.source_id, event.url, th)
    return event


def deduplicate(events: Iterable[SocialEvent]) -> list[SocialEvent]:
    """Dedupe by text_hash (recycled-content fingerprint). First-seen wins."""
    seen: set[str] = set()
    out: list[SocialEvent] = []
    for ev in events:
        stamp_provenance(ev)
        key = ev.text_hash or ev.event_id
        if key in seen:
            continue
        seen.add(key)
        out.append(ev)
    return out


def detect_bot_wash(events: list[SocialEvent], *, subject: str) -> BotWashAssessment:
    """Heuristics that refuse to invent negatives.

    * recycled_content: DERIVED True when two distinct URLs share a hash.
      False only when ≥2 events were observed with distinct hashes.
      UNKNOWN when <2 events.
    * coordinated_timing: DERIVED True when ≥3 events from ≥2 sources share
      a published_ts window of ≤120s. UNKNOWN when timestamps missing.
    * unique_author_ratio: UNKNOWN unless at least one author_ref is present.
    * paid_promo_markers: DERIVED True on lexicon hit; False when text was
      observed and no marker hit; UNKNOWN when no text.
    """
    unknowns: list[str] = []
    reasons: list[str] = []

    if not events:
        return BotWashAssessment(
            subject=subject, recycled_content=None, coordinated_timing=None,
            unique_author_ratio=None, paid_promo_markers=None,
            confidence="UNKNOWN",
            unknowns=["no_social_events"],
            reasons=["no events to assess — UNKNOWN, not 'clean'"],
        )

    # recycled content
    by_hash: dict[str, set[str]] = {}
    for ev in events:
        by_hash.setdefault(ev.text_hash, set()).add(ev.url or ev.event_id)
    recycled: bool | None
    if len(events) < 2:
        recycled = None
        unknowns.append("recycled_content (need ≥2 events)")
    else:
        recycled = any(len(urls) >= 2 for urls in by_hash.values())
        if recycled:
            reasons.append("same text_hash on distinct URLs (recycled content)")

    # coordinated timing
    stamps = [ev.published_ts for ev in events if ev.published_ts is not None]
    sources_with_ts = {ev.source_id for ev in events if ev.published_ts is not None}
    coordinated: bool | None
    if len(stamps) < 3 or len(sources_with_ts) < 2:
        coordinated = None
        unknowns.append("coordinated_timing (need ≥3 dated events across ≥2 sources)")
    else:
        ordered = sorted(stamps)
        coordinated = False
        for i in range(len(ordered) - 2):
            if ordered[i + 2] - ordered[i] <= 120.0:
                coordinated = True
                reasons.append("≥3 dated posts across sources within 120s")
                break

    authors = [ev.author_ref for ev in events if ev.author_ref]
    unique_ratio: float | None
    if not authors:
        unique_ratio = None
        unknowns.append("unique_author_ratio (no author_ref on this source)")
    else:
        unique_ratio = len(set(authors)) / max(len(authors), 1)

    texts = [ev.text for ev in events if ev.text]
    paid: bool | None
    if not texts:
        paid = None
        unknowns.append("paid_promo_markers (no text)")
    else:
        blob = " ".join(texts).lower()
        paid = any(m in blob for m in _PAID_PROMO_MARKERS)
        if paid:
            reasons.append("paid-promotion phrase bank hit")

    if unknowns and not reasons:
        conf = "UNKNOWN"
    elif unknowns:
        conf = "DERIVED"
    else:
        conf = "DERIVED"

    return BotWashAssessment(
        subject=subject,
        recycled_content=recycled,
        coordinated_timing=coordinated,
        unique_author_ratio=unique_ratio,
        paid_promo_markers=paid,
        confidence=conf,
        unknowns=unknowns,
        reasons=reasons,
    )


def mention_velocity(events: list[SocialEvent], *, now: float,
                     window_sec: float = 3600.0) -> float | None:
    """Mentions / hour in `window_sec`. UNKNOWN when no dated events in window."""
    dated = [ev for ev in events
             if ev.published_ts is not None and 0 <= now - ev.published_ts <= window_sec]
    if not dated:
        return None
    hours = max(window_sec / 3600.0, 1e-9)
    return round(len(dated) / hours, 4)


class SocialIntelligence:
    """Canonical social collector + pipeline. Network is injected, never assumed."""

    def __init__(self, *, news: NewsCollector | None = None,
                 github_transport: Callable | None = None):
        self.news = news or NewsCollector()
        self._github_transport = github_transport

    def collect_source(self, source_id: str, *, subject: str = "MARKET",
                       keywords: Iterable[str] | None = None,
                       items: list[NewsItem] | None = None,
                       now: float | None = None) -> SocialCollectionResult:
        """Collect one source. Blocked sources return their status, zero events."""
        ts = time.time() if now is None else now
        src = SOCIAL_SOURCE_REGISTRY.get(source_id)
        if src is None:
            return SocialCollectionResult(
                source_id=source_id, status="UNKNOWN",
                error_message="unregistered source", live_claim="NONE",
            )
        if src.status == "COST_BLOCKED":
            return SocialCollectionResult(
                source_id=source_id, status="COST_BLOCKED",
                error_message=src.reason, live_claim="NONE",
            )
        if src.status == "OUT_OF_POLICY":
            return SocialCollectionResult(
                source_id=source_id, status="OUT_OF_POLICY",
                error_message=src.reason, live_claim="NONE",
            )
        if src.status == "AUTH_REQUIRED":
            return SocialCollectionResult(
                source_id=source_id, status="AUTH_REQUIRED",
                error_message=src.reason, live_claim="NONE",
            )
        if source_id == "rss":
            return self._collect_rss(subject=subject, keywords=keywords,
                                     items=items, now=ts)
        if source_id == "github":
            return self._collect_github(subject=subject, keywords=keywords, now=ts)
        return SocialCollectionResult(
            source_id=source_id, status="UNKNOWN",
            error_message="no collector bound", live_claim="NONE",
        )

    def _collect_rss(self, *, subject: str, keywords: Iterable[str] | None,
                     items: list[NewsItem] | None, now: float) -> SocialCollectionResult:
        if items is None:
            fetched, _ok, failed = self.news.fetch_all()
            items = fetched
            if not items and failed:
                return SocialCollectionResult(
                    source_id="rss", status="DOWN",
                    error_message="all_feeds_unreachable", live_claim="NONE",
                )
        keys = [k.lower() for k in (keywords or []) if k and len(str(k)) >= 2]
        if keys:
            items = [i for i in items if any(k in i.text for k in keys)]
        events = [normalize_news_item(i, retrieved_ts=now,
                                      token_refs=keys) for i in items]
        status = "OK" if events else "EMPTY"
        return SocialCollectionResult(source_id="rss", status=status, events=events)

    def _collect_github(self, *, subject: str, keywords: Iterable[str] | None,
                        now: float) -> SocialCollectionResult:
        """Official public API only. No live call unless a transport is injected.

        Without a transport the collector is honest EMPTY/UNKNOWN — it does
        not pretend GitHub was queried. Tests inject a fixture transport.
        """
        if self._github_transport is None:
            return SocialCollectionResult(
                source_id="github", status="EMPTY",
                error_message="no transport injected; live GitHub not claimed",
                live_claim="NONE",
            )
        try:
            payload = self._github_transport(subject=subject, keywords=list(keywords or []))
        except Exception as e:  # noqa: BLE001 — fail-open observation
            return SocialCollectionResult(
                source_id="github", status="DOWN",
                error_message=f"{type(e).__name__}: {str(e)[:120]}",
                live_claim="NONE",
            )
        if not payload:
            return SocialCollectionResult(source_id="github", status="EMPTY")
        events: list[SocialEvent] = []
        for row in payload:
            if not isinstance(row, dict):
                continue
            text = str(row.get("text") or row.get("title") or "")
            url = str(row.get("url") or "")
            th = _text_hash(text)
            pub = row.get("published_ts")
            try:
                pub_ts = float(pub) if pub is not None else None
            except (TypeError, ValueError):
                pub_ts = None
            author = row.get("author")
            events.append(SocialEvent(
                event_id=_event_id("github", url, th),
                source_id="github", platform="github", text=text,
                text_hash=th, url=url, retrieved_ts=now,
                published_ts=pub_ts,
                author_ref=str(author) if author else None,
                token_refs=tuple(keywords or ()),
                raw_sha256=th,
            ))
        return SocialCollectionResult(
            source_id="github", status="OK" if events else "EMPTY", events=events,
        )

    def analyze(self, subject: str = "MARKET", *,
                keywords: Iterable[str] | None = None,
                news_items: list[NewsItem] | None = None,
                extra_events: list[SocialEvent] | None = None,
                now: float | None = None,
                sources: Iterable[str] | None = None) -> SocialIntelligenceReport:
        """Run the full pipeline. Blocked sources contribute status, not events."""
        ts = time.time() if now is None else now
        wanted = list(sources) if sources is not None else list(SOCIAL_SOURCE_REGISTRY)
        collected: list[SocialEvent] = []
        source_status: dict[str, dict[str, Any]] = {}
        for sid in wanted:
            kw = keywords
            items = news_items if sid == "rss" else None
            result = self.collect_source(sid, subject=subject, keywords=kw,
                                         items=items, now=ts)
            source_status[sid] = {
                "status": result.status,
                "event_count": len(result.events),
                "live_claim": result.live_claim,
                "error_message": result.error_message,
                "registry_status": SOCIAL_SOURCE_REGISTRY[sid].status
                if sid in SOCIAL_SOURCE_REGISTRY else "UNKNOWN",
            }
            collected.extend(result.events)
        if extra_events:
            collected.extend(extra_events)

        n_raw = len(collected)
        events = deduplicate(collected)
        wash = detect_bot_wash(events, subject=subject)
        velocity = mention_velocity(events, now=ts)
        sources_hit = {ev.source_id for ev in events}
        propagation = len(sources_hit) if events else None

        narrative: NarrativeSignal | None = None
        rss_items = news_items
        if rss_items is None:
            rss_items = [
                NewsItem(title=ev.text[:160], link=ev.url, source=ev.source_id,
                         published_ts=ev.published_ts, summary="")
                for ev in events if ev.source_id == "rss"
            ]
        if rss_items:
            narrative = self.news.analyze(
                subject=subject, keywords=keywords, items=rss_items,
                now=ts,
            )

        unknowns: list[str] = list(wash.unknowns)
        if velocity is None:
            unknowns.append("mention_velocity_1h (no dated events in window)")
        if not events:
            unknowns.append("social_events")
        if narrative is None or not getattr(narrative, "is_known", False):
            unknowns.append("narrative")

        return SocialIntelligenceReport(
            subject=subject,
            sources=source_status,
            events_collected=n_raw,
            events_after_dedup=len(events),
            narrative=narrative.to_dict() if narrative is not None else None,
            bot_wash=wash.as_dict(),
            mention_velocity_1h=velocity,
            cross_source_propagation=propagation,
            unknowns=unknowns,
            computed_ts=ts,
        )
