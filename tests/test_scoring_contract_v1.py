#!/usr/bin/env python3
"""Canonical scoring contract — shared semantic dictionary (P1-5).

This module documents and validates the field contract between:
  - Python OpportunityScoreReport (`architecture/scoring/engine.py`)
  - TypeScript ScoredOpportunity / OpportunityCanonicalV1

It does NOT force numeric score parity (dual-stack engines may differ).
It does enforce that both stacks expose the same *semantic* keys for
opportunity identity, score, confidence, risk, veto, provenance, and
explanation surfaces — so Telegram/Web/daemon do not invent contradictory shapes.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs" / "contracts" / "scoring_contract_v1.json"

# Minimal required semantic keys on the Python report surface.
PYTHON_REQUIRED = {
    "token_address",
    "token_chain",
    "token_symbol",
    "opportunity_score",
    "confidence_level",
    "risk_level",
    "positive_reasons",
    "risk_deductions",
    "missing_unknowns",
    "provenance_sha256",
    "source_provider",
    "intel_evidence_items",
}

# Keys that TypeScript OpportunityCanonicalV1 / ScoredOpportunity must cover
# (mapped names allowed via contract aliases).
TS_REQUIRED = {
    "address",
    "chain",
    "symbol",
    "score",
    "confidence",
    "decision",
    "reasonsFa",
    "risksFa",
    "unknownsFa",
}


def load_contract() -> dict:
    assert CONTRACT_PATH.is_file(), f"missing contract file: {CONTRACT_PATH}"
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_scoring_contract_file_lists_python_and_ts_surfaces():
    doc = load_contract()
    assert doc["schema"] == "ahos.scoring_contract.v1"
    assert doc["security_veto_authoritative"] is True
    assert set(doc["python_opportunity_score_report_required"]) >= PYTHON_REQUIRED
    assert set(doc["typescript_scored_opportunity_required"]) >= TS_REQUIRED
    assert "narrative_label" in doc["intel_evidence_keys_expected"]
    assert "mstruct_label" in doc["intel_evidence_keys_expected"]
    assert "tokenomics_label" in doc["intel_evidence_keys_expected"]
    assert "catalyst_status" in doc["intel_evidence_keys_expected"]


def test_python_report_exposes_contract_fields():
    import time
    from architecture.providers.contracts import (
        MarketMetrics, NormalizedTokenCandidate, SecuritySignals,
    )
    from architecture.scoring.engine import OpportunityScorer

    cand = NormalizedTokenCandidate(
        chain="solana",
        address="So11111111111111111111111111111111111111112",
        symbol="W",
        name="Wrapped",
        source_provider="dexscreener",
        retrieved_ts=time.time(),
        metrics=MarketMetrics(liquidity_usd=50_000.0, volume_1h=10_000.0,
                              txns_1h_buys=40, txns_1h_sells=20),
        security=SecuritySignals(is_honeypot=False),
    )
    report = OpportunityScorer().evaluate(cand)
    for key in PYTHON_REQUIRED:
        assert hasattr(report, key), f"missing python field {key}"
    assert isinstance(report.opportunity_score, (int, float))
    assert report.confidence_level in ("HIGH", "MED", "LOW")
    intel_keys = {e["key"] for e in report.answer_intel_evidence()}
    # Feed-through contract: these keys must exist even when UNKNOWN.
    for k in ("narrative_label", "mstruct_label", "tokenomics_label", "catalyst_status"):
        assert k in intel_keys, f"missing intel key {k}"
