#!/usr/bin/env python3
"""Evidence freshness grading (W36 phase 10).

The Evidence contract documented STALE ("measured, but older than the
evaluation freshness budget") but nothing ever assigned it. Now the atom
builder grades measured items older than EVIDENCE_FRESHNESS_BUDGET_SEC as
STALE. Pinned here:

  * a fresh measured item is VERIFIED;
  * an old measured item is STALE with its value intact (is_known() stays
    True — stale evidence is still evidence, just visibly old);
  * an unknown item stays UNKNOWN regardless of age;
  * scoring is invariant: STALE vs VERIFIED produces the identical
    opportunity score / confidence / risk (no scoring math branches on
    status), only the visible status differs.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.intelligence.evidence import (  # noqa: E402
    EVIDENCE_FRESHNESS_BUDGET_SEC,
    materialize_evidence,
)
from architecture.providers.contracts import (  # noqa: E402
    MarketMetrics,
    NormalizedTokenCandidate,
    SecuritySignals,
)
from architecture.scoring.engine import OpportunityScorer  # noqa: E402

NOW = 1756000000.0
FRESH_TS = NOW - 3600.0           # 1h old
STALE_TS = NOW - 3 * EVIDENCE_FRESHNESS_BUDGET_SEC  # 72h old


def _candidate(retrieved_ts: float) -> NormalizedTokenCandidate:
    return NormalizedTokenCandidate(
        chain="solana",
        address="So11111111111111111111111111111111111111112",
        symbol="TEST",
        name="Test Token",
        source_provider="dexscreener",
        retrieved_ts=retrieved_ts,
        metrics=MarketMetrics(price_usd=0.1, liquidity_usd=80000.0,
                              volume_1h=40000.0, txns_1h_buys=90,
                              txns_1h_sells=20),
        security=SecuritySignals(is_honeypot=False, is_contract_verified=True,
                                 top10_holder_concentration_pct=22.0),
    )


def test_fresh_measured_item_is_verified():
    bundle = materialize_evidence(_candidate(FRESH_TS), now=NOW)
    item = bundle.get("liquidity_usd")
    assert item is not None
    assert item.status == "VERIFIED"
    assert item.is_known() is True


def test_old_measured_item_is_stale_with_value_intact():
    bundle = materialize_evidence(_candidate(STALE_TS), now=NOW)
    item = bundle.get("liquidity_usd")
    assert item is not None
    assert item.status == "STALE"
    assert item.value == 80000.0            # value intact
    assert item.is_known() is True          # stale is still evidence
    assert item.freshness_seconds > EVIDENCE_FRESHNESS_BUDGET_SEC


def test_unknown_stays_unknown_regardless_of_age():
    bundle = materialize_evidence(_candidate(STALE_TS), now=NOW)
    item = bundle.get("volume_5m")          # not provided -> UNKNOWN
    assert item is None or item.status == "UNKNOWN"


def test_scoring_is_invariant_to_stale_status():
    """STALE vs VERIFIED must not change score/confidence/risk — only the
    visible status field differs (no scoring math branches on status)."""
    fresh_report = OpportunityScorer().evaluate(_candidate(FRESH_TS), now=NOW)
    stale_report = OpportunityScorer().evaluate(_candidate(STALE_TS), now=NOW)

    assert fresh_report.opportunity_score == stale_report.opportunity_score
    assert fresh_report.confidence_level == stale_report.confidence_level
    assert fresh_report.risk_level == stale_report.risk_level

    fresh_ev = {e["key"]: e for e in fresh_report.answer_evidence()}
    stale_ev = {e["key"]: e for e in stale_report.answer_evidence()}
    # same known fields, same values
    assert fresh_ev["liquidity_usd"]["value"] == stale_ev["liquidity_usd"]["value"]
    # but the stale one is visibly STALE
    assert fresh_ev["liquidity_usd"]["status"] == "VERIFIED"
    assert stale_ev["liquidity_usd"]["status"] == "STALE"
