#!/usr/bin/env python3
"""Social Intelligence — source registry + pipeline honesty.

Pins:
  * every vision source is named with an honest status (never LIVE-claimed)
  * OUT_OF_POLICY / COST_BLOCKED / AUTH_REQUIRED collect zero events
  * RSS wraps NewsCollector; unreachable → DOWN/UNKNOWN, never fake-neutral
  * dedupe by text_hash; recycled content is DERIVED only with ≥2 events
  * author-less RSS cannot report unique_author_ratio as 0 (that's fabrication)
  * social evidence never produces a buy/opportunity decision
  * GitHub without a transport does not claim a live fetch
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.intel.news import NewsItem  # noqa: E402
from architecture.intel.social import (  # noqa: E402
    SOCIAL_SOURCE_REGISTRY, SocialEvent, SocialIntelligence,
    detect_bot_wash, deduplicate, mention_velocity, source_registry,
)
from architecture.intelligence.adapters import evidence_from_social  # noqa: E402


REQUIRED_SOURCES = {
    "rss", "github", "reddit", "x_twitter", "telegram_channels",
    "instagram", "tiktok", "youtube", "web_public",
}


def test_registry_names_every_vision_source_with_honest_status():
    reg = source_registry()
    assert REQUIRED_SOURCES <= set(reg)
    for sid, row in reg.items():
        assert row["status"] in (
            "IMPLEMENTED", "AUTH_REQUIRED", "COST_BLOCKED",
            "OUT_OF_POLICY", "EXTERNALLY_BLOCKED",
        )
        assert row["live_claim"] == "NONE"
        assert row["reason"]
    assert reg["rss"]["status"] == "IMPLEMENTED"
    assert reg["x_twitter"]["status"] == "COST_BLOCKED"
    assert reg["instagram"]["status"] == "OUT_OF_POLICY"
    assert reg["tiktok"]["status"] == "OUT_OF_POLICY"
    assert reg["reddit"]["status"] == "AUTH_REQUIRED"
    assert reg["youtube"]["status"] == "AUTH_REQUIRED"
    assert reg["telegram_channels"]["status"] == "OUT_OF_POLICY"


def test_blocked_sources_collect_zero_events_and_do_not_live_claim():
    si = SocialIntelligence()
    for sid in ("x_twitter", "instagram", "tiktok", "reddit",
                "youtube", "telegram_channels", "web_public"):
        result = si.collect_source(sid, subject="TOK")
        assert result.events == []
        assert result.live_claim == "NONE"
        assert result.status in (
            "COST_BLOCKED", "OUT_OF_POLICY", "AUTH_REQUIRED",
        )


def test_rss_pipeline_from_injected_items_no_network():
    items = [
        NewsItem(title="Alpha lists on a major venue", link="https://e/a",
                 source="cointelegraph", published_ts=1_700_000_000.0,
                 summary="listing"),
        NewsItem(title="Alpha lists on a major venue", link="https://e/b",
                 source="decrypt", published_ts=1_700_000_010.0,
                 summary="listing"),  # recycled text, distinct URL
    ]
    si = SocialIntelligence()
    report = si.analyze(
        subject="ALPHA", keywords=["alpha"], news_items=items,
        sources=["rss"], now=1_700_000_100.0,
    )
    assert report.events_collected == 2
    assert report.events_after_dedup == 1          # same normalized text
    assert report.decision_floor == "SOCIAL_IS_EVIDENCE_NOT_PROOF"
    assert report.sources["rss"]["status"] in ("OK", "EMPTY")
    assert report.sources["rss"]["live_claim"] == "NONE"


def test_bot_wash_author_ratio_unknown_without_authors():
    events = [
        SocialEvent(event_id="1", source_id="rss", platform="rss",
                    text="hello world", text_hash="aaa", url="u1",
                    retrieved_ts=1.0, published_ts=1.0, author_ref=None),
        SocialEvent(event_id="2", source_id="rss", platform="rss",
                    text="other text", text_hash="bbb", url="u2",
                    retrieved_ts=1.0, published_ts=2.0, author_ref=None),
    ]
    wash = detect_bot_wash(events, subject="TOK")
    assert wash.unique_author_ratio is None
    assert any("author" in u for u in wash.unknowns)
    assert wash.recycled_content is False          # two distinct hashes, observed
    assert wash.paid_promo_markers is False        # text observed, no marker


def test_bot_wash_empty_is_unknown_not_clean():
    wash = detect_bot_wash([], subject="TOK")
    assert wash.confidence == "UNKNOWN"
    assert wash.recycled_content is None
    assert wash.paid_promo_markers is None


def test_paid_promo_marker_is_derived_from_text():
    events = [
        SocialEvent(event_id="1", source_id="rss", platform="rss",
                    text="This is a sponsored airdrop alert", text_hash="x",
                    url="u", retrieved_ts=1.0),
    ]
    wash = detect_bot_wash(events, subject="TOK")
    assert wash.paid_promo_markers is True


def test_mention_velocity_unknown_without_dates():
    events = [
        SocialEvent(event_id="1", source_id="rss", platform="rss",
                    text="x", text_hash="x", url="u", retrieved_ts=10.0,
                    published_ts=None),
    ]
    assert mention_velocity(events, now=10.0) is None


def test_github_without_transport_does_not_claim_live():
    si = SocialIntelligence()
    result = si.collect_source("github", subject="ahos")
    assert result.status == "EMPTY"
    assert result.live_claim == "NONE"
    assert result.events == []


def test_github_injected_transport_normalizes_and_keeps_unknown_author():
    def transport(*, subject, keywords):
        return [{"text": "ahos release", "url": "https://github.com/x",
                 "published_ts": 50.0}]  # no author
    si = SocialIntelligence(github_transport=transport)
    result = si.collect_source("github", subject="ahos", now=100.0)
    assert result.status == "OK"
    assert len(result.events) == 1
    assert result.events[0].author_ref is None
    assert result.events[0].source_id == "github"


def test_social_evidence_adapter_unknown_velocity_stays_unknown():
    si = SocialIntelligence()
    report = si.analyze(subject="Z", news_items=[], sources=["rss"], now=1.0)
    atoms = evidence_from_social(report)
    vel = next(a for a in atoms if a.key == "social_mention_velocity_1h")
    assert vel.status == "UNKNOWN"
    assert vel.value is None
    floor = next(a for a in atoms if a.key == "social_decision_floor")
    assert "EVIDENCE_NOT_PROOF" in str(floor.value)


def test_dedup_keeps_first_seen():
    a = SocialEvent(event_id="1", source_id="rss", platform="rss",
                    text="Same", text_hash="hh", url="u1", retrieved_ts=1.0)
    b = SocialEvent(event_id="2", source_id="github", platform="github",
                    text="Same", text_hash="hh", url="u2", retrieved_ts=2.0)
    out = deduplicate([a, b])
    assert len(out) == 1
    assert out[0].url == "u1"


def test_analyze_records_blocked_sources_in_report():
    si = SocialIntelligence()
    report = si.analyze(subject="M", news_items=[], now=1.0)
    assert "x_twitter" in report.sources
    assert report.sources["x_twitter"]["status"] == "COST_BLOCKED"
    assert report.sources["instagram"]["status"] == "OUT_OF_POLICY"
    assert SOCIAL_SOURCE_REGISTRY["rss"].status == "IMPLEMENTED"
