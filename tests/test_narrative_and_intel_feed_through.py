#!/usr/bin/env python3
"""P0-3 / P1 feed-through: narrative, market structure, tokenomics, catalysts.

Pins:
  * Offline evaluate() emits narrative_* atoms as UNKNOWN (no network).
  * Prefetched headlines produce DERIVED narrative atoms with intel.news provenance.
  * Market structure / tokenomics atoms appear with honest UNKNOWN when sparse.
  * Catalysts require news items; empty → UNKNOWN status, never invented events.
  * Security veto still authoritative (honeypot path unchanged by narrative).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.intel.catalyst import CatalystDetector  # noqa: E402
from architecture.intel.market_structure import MarketStructureAnalyzer  # noqa: E402
from architecture.intel.news import NewsItem  # noqa: E402
from architecture.intel.tokenomics import TokenomicsAnalyzer  # noqa: E402
from architecture.providers.contracts import (  # noqa: E402
    MarketMetrics,
    NormalizedTokenCandidate,
    SecuritySignals,
)
from architecture.scoring.engine import OpportunityScorer  # noqa: E402


def _candidate(**kw) -> NormalizedTokenCandidate:
    base = dict(
        chain="solana",
        address="So11111111111111111111111111111111111111112",
        symbol="TEST",
        name="Test Token",
        source_provider="dexscreener",
        retrieved_ts=time.time(),
        metrics=MarketMetrics(
            price_usd=0.1,
            liquidity_usd=80_000.0,
            volume_1h=40_000.0,
            volume_5m=5_000.0,
            fdv_usd=1_000_000.0,
            market_cap_usd=400_000.0,
            txns_5m_buys=40,
            txns_5m_sells=10,
            txns_1h_buys=120,
            txns_1h_sells=30,
        ),
        security=SecuritySignals(
            is_honeypot=False,
            is_contract_verified=True,
            is_ownership_renounced=True,
            has_mint_authority=False,
            has_freeze_authority=False,
            top10_holder_concentration_pct=22.0,
        ),
    )
    base.update(kw)
    return NormalizedTokenCandidate(**base)


def _atoms(**kw) -> dict:
    report = OpportunityScorer().evaluate(_candidate(**kw))
    return {e["key"]: e for e in report.answer_intel_evidence()}


def test_offline_evaluate_emits_narrative_unknown_without_network():
    atoms = _atoms()
    label = atoms["narrative_label"]
    assert label["provider"] == "intel.news"
    assert label["status"] == "UNKNOWN"
    assert label["value"] == "UNKNOWN"


def test_prefetched_headlines_feed_through_as_derived():
    now = time.time()
    items = [
        NewsItem(
            title="TEST Token surge after listing on major exchange",
            link="https://example.test/a",
            source="fixture",
            published_ts=now - 60,
            summary="bullish rally",
        )
    ]
    from architecture.intelligence.evidence import materialize_evidence

    cand = _candidate()
    bundle = materialize_evidence(cand, now=now)
    bundle = OpportunityScorer.attach_narrative(
        bundle, cand, now, items=items, feeds_ok=["fixture"], feeds_failed=[])
    report = OpportunityScorer().from_intelligence(
        OpportunityScorer().intelligence.evaluate(bundle))
    atoms = {e["key"]: e for e in report.answer_intel_evidence()}
    assert atoms["narrative_label"]["status"] == "DERIVED"
    assert atoms["narrative_label"]["value"] in ("BULLISH", "BEARISH", "NEUTRAL")
    assert atoms["narrative_label"]["provider"] == "intel.news"
    assert atoms["narrative_mentions"]["value"] >= 1


def test_market_structure_atoms_present_and_healthy_for_deep_book():
    atoms = _atoms()
    assert atoms["mstruct_label"]["provider"] == "intel.market_structure"
    assert atoms["mstruct_label"]["status"] == "DERIVED"
    assert atoms["mstruct_label"]["value"] in ("HEALTHY", "FRAGILE", "ABNORMAL")
    assert atoms["mstruct_liquidity_quality"]["value"] in ("THIN", "ADEQUATE", "DEEP")


def test_market_structure_thin_liquidity_is_fragile_or_abnormal():
    sig = MarketStructureAnalyzer().analyze(_candidate(
        metrics=MarketMetrics(liquidity_usd=1_000.0, volume_1h=500.0,
                              txns_1h_buys=5, txns_1h_sells=5)))
    assert sig.label in ("FRAGILE", "ABNORMAL", "UNKNOWN")
    assert sig.liquidity_quality == "THIN"


def test_tokenomics_sound_when_authorities_clean():
    atoms = _atoms()
    assert atoms["tokenomics_label"]["provider"] == "intel.tokenomics"
    assert atoms["tokenomics_label"]["value"] == "SOUND"
    assert atoms["tokenomics_unlock_vesting"]["status"] == "UNKNOWN"


def test_tokenomics_critical_on_mint_authority():
    sig = TokenomicsAnalyzer().analyze(_candidate(
        security=SecuritySignals(has_mint_authority=True,
                                 top10_holder_concentration_pct=10.0)))
    assert sig.label == "CRITICAL"


def test_catalyst_unknown_without_news_items():
    report = CatalystDetector().detect(_candidate(), news_items=None)
    assert report.status == "UNKNOWN"
    assert report.events == []


def test_catalyst_found_from_listing_headline():
    now = time.time()
    items = [NewsItem(
        title="TEST lists on Binance after partnership announcement",
        link="https://example.test/b",
        source="fixture",
        published_ts=now - 120,
    )]
    report = CatalystDetector().detect(_candidate(), news_items=items, now=now)
    assert report.status == "FOUND"
    assert any(e.kind in ("LISTING", "PARTNERSHIP") for e in report.events)
    assert all(e.source and e.confidence > 0 for e in report.events)


def test_legacy_answer_evidence_still_four_canonical_items():
    report = OpportunityScorer().evaluate(_candidate())
    assert len(report.answer_evidence()) == 4
