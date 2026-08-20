#!/usr/bin/env python3
"""Tests for K-03 Expert Lens Library — 10 Pilot Data Cards (Phase XXII)."""
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from architecture.knowledge.contracts import TrustClass, KnowledgeDomain, ExpertLensCard
from architecture.knowledge.lenses import ExpertLensLibrary, LENS_PILOT_REGISTRY


def test_lens_library_contains_pilot_cards():
    lib = ExpertLensLibrary()
    lenses = lib.list_lenses()
    assert len(lenses) >= 20

    identities = [l.identity for l in lenses]
    assert any("Shannon" in i for i in identities)
    assert any("von Neumann" in i for i in identities)
    assert any("Mandelbrot" in i for i in identities)
    assert any("Kahneman" in i for i in identities)
    assert any("Munger" in i for i in identities)
    assert any("Taleb" in i for i in identities)
    assert any("Nakamoto" in i for i in identities)
    assert any("Finney" in i for i in identities)
    assert any("Buterin" in i for i in identities)
    assert any("Marks" in i for i in identities)
    # Batch 2 thinkers
    assert any("Nash" in i for i in identities)
    assert any("Thompson" in i for i in identities)
    assert any("Boole" in i for i in identities)
    assert any("Turing" in i for i in identities)
    assert any("Gödel" in i for i in identities)
    assert any("Bayes" in i for i in identities)
    assert any("Fisher" in i for i in identities)
    assert any("Pearl" in i for i in identities)
    assert any("Schneier" in i for i in identities)
    assert any("Brewer" in i for i in identities)


def test_lens_cards_have_documented_failure_modes_and_citations():
    lib = ExpertLensLibrary()
    for lens in lib.list_lenses():
        assert len(lens.verified_principles) >= 1
        assert len(lens.mental_models) >= 1
        assert len(lens.documented_failures) >= 1, f"Lens {lens.lens_id} must have documented failure modes"
        assert len(lens.citations) >= 1
        assert lens.provenance != ""
        # Check that principles have citation references
        for p in lens.verified_principles:
            assert "citation_ref" in p and p["citation_ref"] != ""


def test_lens_application_munger_inversion_veto():
    lib = ExpertLensLibrary()
    token_scam = {"liquidity_usd": 50000.0, "volume_1h": 20000.0, "is_honeypot": True}
    insights = lib.evaluate_opportunity_with_lenses(token_scam)

    assert any(i["lens_id"] == "LENS-MUNGER" and i["verdict"] == "VETO" for i in insights)


def test_lens_application_taleb_trapped_capital():
    lib = ExpertLensLibrary()
    token_fragile = {"liquidity_usd": 500.0, "volume_1h": 1000.0, "is_honeypot": False}
    insights = lib.evaluate_opportunity_with_lenses(token_fragile)

    assert any(i["lens_id"] == "LENS-TALEB" and "TRAPPED_CAPITAL" in i["verdict"] for i in insights)


def test_lens_application_shannon_high_snr():
    lib = ExpertLensLibrary()
    token_signal = {"liquidity_usd": 60000.0, "volume_1h": 35000.0, "is_honeypot": False}
    insights = lib.evaluate_opportunity_with_lenses(token_signal)

    assert any(i["lens_id"] == "LENS-SHANNON" and i["verdict"] == "CONFIRM_SIGNAL" for i in insights)


def test_missing_fields_do_not_fabricate_false_or_zero():
    """False-on-missing is forbidden: unknown honeypot is not a clean bill,
    unknown liquidity is not $0 trapped-capital."""
    lib = ExpertLensLibrary()
    insights = lib.evaluate_opportunity_with_lenses({})
    verdicts = {(i["lens_id"], i["verdict"]) for i in insights}
    assert ("LENS-MUNGER", "VETO") not in verdicts
    assert ("LENS-TALEB", "AVOID_TRAPPED_CAPITAL") not in verdicts
    assert any(i["verdict"] == "ABSTAIN_UNKNOWN" for i in insights)


def test_lens_domain_filtering():
    lib = ExpertLensLibrary()
    crypto_lenses = lib.list_by_domain(KnowledgeDomain.CRYPTOGRAPHY)
    assert len(crypto_lenses) >= 2
    lens_ids = [l.lens_id for l in crypto_lenses]
    assert "LENS-NAKAMOTO" in lens_ids
    assert "LENS-FINNEY" in lens_ids
