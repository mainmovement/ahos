#!/usr/bin/env python3
"""Month-3 feed-through tests: virality / paid-promotion evidence appears in
the opportunity report with provider provenance.

Roadmap item: "Narrative + smart-money inputs promoted from B/C to C/D —
feed-through test: evidence items appear in explanations with provenance."

The wiring uses the EXISTING canonical converters:
  ViralityTracker (intel/viral) -> evidence_from_virality (intelligence/
  adapters.py) -> EvidenceBundle.extra -> OpportunityScoreReport
  .intel_evidence_items / answer_intel_evidence().

The frozen 4-item `answer_evidence()` contract is NOT changed.

Pinned here:
  * A hot candidate produces virality atoms with provider "intel.viral".
  * Observed boost spend => is_paid_promotion DERIVED True (a RISK marker).
  * Missing boost data => is_paid_promotion UNKNOWN with value None — the raw
    signal's False-on-missing default must never leak as a fabricated
    negative.
  * Missing txn data => wash_suspected UNKNOWN (never a fabricated False).
  * Sparse data => virality_label UNKNOWN (never a fabricated FLAT).
  * The legacy answer_evidence() surface stays exactly the 4 canonical items.
  * No network: everything is fixture-driven.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.intelligence.adapters import evidence_from_virality  # noqa: E402
from architecture.intel.viral import ViralitySignal  # noqa: E402
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
            liquidity_usd=80000.0,
            volume_1h=40000.0,
            txns_5m_buys=40,
            txns_5m_sells=10,
            txns_1h_buys=120,
            txns_1h_sells=30,
        ),
        security=SecuritySignals(is_honeypot=False, is_contract_verified=True,
                                 top10_holder_concentration_pct=22.0),
    )
    base.update(kw)
    return NormalizedTokenCandidate(**base)


def _report(**kw) -> dict:
    """{key: atom-dict} of the full intel evidence surface of a scored report."""
    report = OpportunityScorer().evaluate(_candidate(**kw))
    return {e["key"]: e for e in report.answer_intel_evidence()}


# ------------------------------------------------------------ feed-through

def test_hot_candidate_emits_virality_atoms_with_provenance():
    atoms = _report()
    label = atoms.get("virality_label")
    assert label is not None
    assert label["provider"] == "intel.viral"
    assert label["status"] == "DERIVED"
    assert label["value"] in ("VIRAL", "BUILDING", "FLAT", "COOLING")
    assert 0.0 <= atoms["virality_score"]["value"] <= 100.0
    # txn data present -> wash suspicion is a real computation
    assert atoms["wash_suspected"]["status"] == "DERIVED"
    assert atoms["wash_suspected"]["value"] is False  # fixture is clean volume


def test_boost_spend_is_a_known_risk_marker():
    atoms = _report(boost_amount=250.0)
    paid = atoms["is_paid_promotion"]
    assert paid["status"] == "DERIVED"
    assert paid["value"] is True  # paid promotion is a RISK marker by design


def test_missing_boost_data_is_unknown_never_false():
    atoms = _report(boost_amount=None)
    paid = atoms["is_paid_promotion"]
    assert paid["status"] == "UNKNOWN"
    assert paid["value"] is None  # never a fabricated 'not promoted'


def test_sparse_data_yields_unknown_virality_not_flat():
    atoms = _report(
        metrics=MarketMetrics(price_usd=0.1, liquidity_usd=80000.0),
        boost_amount=None,
    )
    assert atoms["virality_label"]["status"] == "UNKNOWN"
    # the signal's own explicit unknown marker, never a fabricated 'FLAT'
    assert atoms["virality_label"]["value"] == "UNKNOWN"
    # wash suspicion requires txn data -> UNKNOWN, never a fabricated False
    assert atoms["wash_suspected"]["status"] == "UNKNOWN"
    assert atoms["wash_suspected"]["value"] is None


# ----------------------------------------- shared converter honesty (direct)

def test_evidence_from_virality_defaults_to_unknown_not_derived():
    sig = ViralitySignal(subject="t", label="VIRAL", score=70.0,
                         txn_acceleration=2.0, volume_acceleration=1.5,
                         buy_pressure=1.2, wash_suspected=True,
                         is_paid_promotion=False, computed_ts=time.time())
    atoms = {e.key: e for e in evidence_from_virality(sig)}

    # flags not provided -> conservative UNKNOWN, value None
    assert atoms["is_paid_promotion"].status == "UNKNOWN"
    assert atoms["is_paid_promotion"].value is None
    assert atoms["wash_suspected"].status == "UNKNOWN"
    assert atoms["wash_suspected"].value is None
    # label/score follow the signal's own known-ness
    assert atoms["virality_label"].status == "DERIVED"


def test_evidence_from_virality_honours_observed_flags():
    sig = ViralitySignal(subject="t", label="BUILDING", score=40.0,
                         txn_acceleration=None, volume_acceleration=None,
                         buy_pressure=None, wash_suspected=False,
                         is_paid_promotion=True, computed_ts=time.time())
    atoms = {e.key: e for e in evidence_from_virality(
        sig, boost_seen=True, txns_seen=True)}
    assert atoms["is_paid_promotion"].status == "DERIVED"
    assert atoms["is_paid_promotion"].value is True
    assert atoms["wash_suspected"].status == "DERIVED"
    assert atoms["wash_suspected"].value is False


# ------------------------------------------------------------ contract intact

def test_legacy_four_item_evidence_contract_is_unchanged():
    report = OpportunityScorer().evaluate(_candidate(boost_amount=100.0))
    legacy = {e["key"] for e in report.answer_evidence()}
    # the frozen canonical surface stays exactly the historical four items
    assert legacy == {"liquidity_usd", "volume_1h", "is_honeypot",
                      "top10_concentration"}
    # virality is NOT smuggled into the legacy surface; it lives in the
    # full intel surface with provenance
    intel = {e["key"] for e in report.answer_intel_evidence()}
    assert "virality_label" in intel
    assert "virality_label" not in legacy
