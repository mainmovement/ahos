#!/usr/bin/env python3
"""Tests for the narrative + virality intelligence layer.

Proves the laws that keep hype from becoming a buy signal:
  - unreachable feeds => UNKNOWN, never a fake "neutral"
  - wash-trading divergence is detected and refuses the VIRAL label
  - paid promotion is penalised, not rewarded
  - small samples are refused rather than over-interpreted
  - UNKNOWN inputs never silently become 0
"""
from __future__ import annotations

import sys
import urllib.error
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.intel.news import (  # noqa: E402
    NewsCollector, NewsItem, parse_feed, BULLISH_TERMS, BEARISH_TERMS,
)
from architecture.intel.viral import ViralityTracker, ACCEL_HOT  # noqa: E402
from architecture.providers.contracts import (  # noqa: E402
    NormalizedTokenCandidate, MarketMetrics,
)


RSS_SAMPLE = b"""<?xml version="1.0"?>
<rss version="2.0"><channel>
  <item>
    <title>Solana surges to new all-time high on ETF approval</title>
    <link>https://example.com/a</link>
    <pubDate>Mon, 17 Aug 2026 10:00:00 +0000</pubDate>
    <description>Massive rally continues</description>
  </item>
  <item>
    <title>DeFi protocol hacked, $40M exploit drains treasury</title>
    <link>https://example.com/b</link>
    <pubDate>Mon, 17 Aug 2026 09:00:00 +0000</pubDate>
    <description>Attackers exploited a vulnerability</description>
  </item>
</channel></rss>"""

ATOM_SAMPLE = b"""<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Bitcoin rally extends as institutional adoption grows</title>
    <link href="https://example.com/c"/>
    <updated>2026-08-17T08:00:00Z</updated>
    <summary>Bullish momentum</summary>
  </entry>
</feed>"""


def _mk_candidate(**metrics) -> NormalizedTokenCandidate:
    return NormalizedTokenCandidate(
        chain="solana", address="Tok111", symbol="TOK", name="Token",
        metrics=MarketMetrics(**metrics),
    )


# ============================== NEWS PARSING ==============================

def test_parse_rss_and_atom_both_supported():
    rss = parse_feed(RSS_SAMPLE, "test")
    assert len(rss) == 2
    assert "surges" in rss[0].title.lower()
    assert rss[0].published_ts is not None

    atom = parse_feed(ATOM_SAMPLE, "test")
    assert len(atom) == 1
    assert atom[0].link == "https://example.com/c"


def test_parse_feed_never_raises_on_garbage():
    assert parse_feed(b"not xml at all", "t") == []
    assert parse_feed(b"", "t") == []
    assert parse_feed(b"<rss><channel><item></item></channel></rss>", "t") == []


def test_unparseable_date_is_none_not_now():
    """A missing date must stay UNKNOWN — never silently stamped with time.time()."""
    items = parse_feed(
        b"<rss><channel><item><title>X happened</title></item></channel></rss>", "t")
    assert items[0].published_ts is None


def test_lexicons_are_directionally_correct():
    assert all(w > 0 for w in BULLISH_TERMS.values())
    assert all(w < 0 for w in BEARISH_TERMS.values())
    assert not (set(BULLISH_TERMS) & set(BEARISH_TERMS)), "a term cannot be both"


# ============================== NEWS SCORING ==============================

def test_all_feeds_unreachable_yields_unknown_not_neutral():
    """THE HONESTY LAW: no data must never masquerade as calm markets."""
    def dead_transport(req, timeout=None):
        raise urllib.error.URLError("filtered")

    sig = NewsCollector(transport=dead_transport).analyze("MARKET")
    assert sig.label == "UNKNOWN"
    assert sig.is_known is False
    assert sig.error_state is not None
    assert sig.error_state["kind"] == "all_feeds_unreachable"
    assert len(sig.feeds_failed) > 0


def test_bullish_and_bearish_headlines_score_directionally():
    bull = [NewsItem(t, "l", "s", None) for t in [
        "Token surges to all-time high after listing",
        "Major partnership drives rally and adoption",
    ]]
    sig = NewsCollector().analyze("TOK", items=bull, max_age_sec=None)
    assert sig.label == "BULLISH" and sig.sentiment > 0

    bear = [NewsItem(t, "l", "s", None) for t in [
        "Protocol hacked in massive exploit",
        "Team accused of fraud as token crashes",
    ]]
    sig2 = NewsCollector().analyze("TOK", items=bear, max_age_sec=None)
    assert sig2.label == "BEARISH" and sig2.sentiment < 0


def test_sentiment_is_bounded_and_evidence_backed():
    """One hysterical headline must not dominate; every score cites its source."""
    spam = [NewsItem("surge rally breakout moon adoption listing approval", "l", "s", None)] * 30
    sig = NewsCollector().analyze("TOK", items=spam, max_age_sec=None)
    assert -1.0 <= sig.sentiment <= 1.0
    assert sig.evidence, "a score without evidence is not admissible"
    assert all("sha256" in e for e in sig.evidence)


def test_keyword_filter_isolates_subject():
    items = [
        NewsItem("SOLTOKEN surges on listing", "l", "s", None),
        NewsItem("Unrelated coin crashes in exploit", "l", "s", None),
    ]
    sig = NewsCollector().analyze("SOLTOKEN", keywords=["soltoken"],
                                  items=items, max_age_sec=None)
    assert sig.mention_count == 1
    assert sig.label == "BULLISH"


def test_no_matching_coverage_is_unknown():
    items = [NewsItem("Something about bitcoin", "l", "s", None)]
    sig = NewsCollector().analyze("OBSCURE", keywords=["obscuretoken"],
                                  items=items, max_age_sec=None)
    assert sig.label == "UNKNOWN"
    assert sig.error_state["kind"] == "no_matching_coverage"


# ============================== VIRALITY ==================================

def test_genuine_acceleration_is_detected():
    # 1h = 600 txns => baseline 50 per 5m. 5m = 200 txns => 4.0x acceleration.
    c = _mk_candidate(volume_5m=10000, volume_1h=30000,
                      txns_5m_buys=150, txns_5m_sells=50,
                      txns_1h_buys=400, txns_1h_sells=200)
    sig = ViralityTracker().analyze(c)
    assert sig.label in ("VIRAL", "BUILDING")
    assert sig.txn_acceleration == pytest.approx(4.0, rel=1e-6)
    assert sig.txn_acceleration >= ACCEL_HOT
    assert sig.reasons


def test_wash_trading_divergence_refuses_viral_label():
    """Volume exploding while transaction count barely moves == manufactured."""
    c = _mk_candidate(volume_5m=100000, volume_1h=60000,     # ~20x volume accel
                      txns_5m_buys=12, txns_5m_sells=8,      # ~1x txn accel
                      txns_1h_buys=140, txns_1h_sells=100)
    sig = ViralityTracker().analyze(c)
    assert sig.wash_suspected is True
    assert sig.label == "UNKNOWN", "manufactured volume must never be called viral"
    assert any("صوری" in w for w in sig.warnings)


def test_paid_promotion_is_penalised_not_rewarded():
    kw = dict(volume_5m=10000, volume_1h=30000,
              txns_5m_buys=90, txns_5m_sells=30,
              txns_1h_buys=400, txns_1h_sells=200)
    organic = ViralityTracker().analyze(_mk_candidate(**kw))
    paid = ViralityTracker().analyze(_mk_candidate(**kw), boost_amount=500.0)
    assert paid.is_paid_promotion is True
    assert paid.score < organic.score, "bought attention must score below earned attention"
    assert paid.warnings


def test_tiny_sample_refuses_to_conclude():
    c = _mk_candidate(volume_5m=100, volume_1h=1000,
                      txns_5m_buys=2, txns_5m_sells=1,
                      txns_1h_buys=20, txns_1h_sells=10)
    sig = ViralityTracker().analyze(c)
    assert sig.label == "UNKNOWN"
    assert any("نمونه" in u for u in sig.unknowns)


def test_missing_metrics_are_unknown_never_zero():
    """UNKNOWN must never be coerced into a confident 'no activity' reading."""
    sig = ViralityTracker().analyze(_mk_candidate())
    assert sig.label == "UNKNOWN"
    assert sig.txn_acceleration is None
    assert sig.volume_acceleration is None
    assert sig.unknowns


def test_cooling_token_is_labelled_cooling():
    c = _mk_candidate(volume_5m=100, volume_1h=60000,
                      txns_5m_buys=8, txns_5m_sells=12,
                      txns_1h_buys=600, txns_1h_sells=600)
    sig = ViralityTracker().analyze(c)
    assert sig.label in ("COOLING", "FLAT", "UNKNOWN")


def test_virality_score_is_bounded():
    c = _mk_candidate(volume_5m=999999, volume_1h=1000,
                      txns_5m_buys=9999, txns_5m_sells=1,
                      txns_1h_buys=100, txns_1h_sells=100)
    sig = ViralityTracker().analyze(c)
    assert 0.0 <= sig.score <= 100.0
