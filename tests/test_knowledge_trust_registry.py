#!/usr/bin/env python3
"""Tests for K-01 Knowledge & Trust Registry (Phase XXII)."""
import sys, time
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from architecture.knowledge.contracts import (
    TrustClass, KnowledgeDomain, KnowledgeSourceRecord
)
from architecture.knowledge.trust_registry import KnowledgeTrustRegistry


def test_trust_class_hierarchy_ranks():
    """Verify strict epistemic rank ordering (no silent collapsing)."""
    assert TrustClass.RAW_FACT.rank > TrustClass.VERIFIED_PRIMARY.rank
    assert TrustClass.VERIFIED_PRIMARY.rank > TrustClass.SECONDARY.rank
    assert TrustClass.SECONDARY.rank > TrustClass.EXPERT_INTERPRETATION.rank
    assert TrustClass.EXPERT_INTERPRETATION.rank > TrustClass.AI_INTERPRETATION.rank
    assert TrustClass.AI_INTERPRETATION.rank > TrustClass.HYPOTHESIS.rank
    assert TrustClass.HYPOTHESIS.rank > TrustClass.SPECULATION.rank

    assert TrustClass.RAW_FACT.is_at_least(TrustClass.EXPERT_INTERPRETATION) is True
    assert TrustClass.AI_INTERPRETATION.is_at_least(TrustClass.RAW_FACT) is False


def test_knowledge_trust_registry_seeded_sources():
    reg = KnowledgeTrustRegistry()
    shannon = reg.get_source("SRC-SHANNON-1948")
    assert shannon is not None
    assert shannon.trust_class == TrustClass.VERIFIED_PRIMARY
    assert shannon.domain == KnowledgeDomain.INFORMATION_THEORY
    assert shannon.confidence == 1.0

    nakamoto = reg.get_source("SRC-NAKAMOTO-2008")
    assert nakamoto is not None
    assert nakamoto.trust_class == TrustClass.VERIFIED_PRIMARY
    assert nakamoto.domain == KnowledgeDomain.CRYPTOGRAPHY


def test_knowledge_trust_registry_speculation_confidence_clamped():
    reg = KnowledgeTrustRegistry()
    spec_source = KnowledgeSourceRecord(
        source_id="SRC-RUMOR-01",
        source_name="Anonymous Twitter Account",
        source_type="SOCIAL",
        trust_class=TrustClass.SPECULATION,
        domain=KnowledgeDomain.ON_CHAIN_ANALYTICS,
        origin="https://x.com/anon",
        timestamp=time.time(),
        version="1.0",
        license_legal_status="Public Social",
        provenance_hash="abc",
        review_status="PENDING_REVIEW",
        confidence=0.99,  # Unreasonable confidence for speculation
        known_bias="Pump-and-dump incentives"
    )
    reg.register_source(spec_source)
    retrieved = reg.get_source("SRC-RUMOR-01")
    assert retrieved.confidence <= 0.40  # Clamped by epistemic law


def test_knowledge_trust_registry_filtering():
    reg = KnowledgeTrustRegistry()
    primary_sources = reg.list_sources_by_trust(TrustClass.VERIFIED_PRIMARY)
    assert len(primary_sources) >= 2
    assert all(s.trust_class.rank >= TrustClass.VERIFIED_PRIMARY.rank for s in primary_sources)

    crypto_sources = reg.list_sources_by_domain(KnowledgeDomain.CRYPTOGRAPHY)
    assert len(crypto_sources) >= 1
    assert any(s.source_id == "SRC-NAKAMOTO-2008" for s in crypto_sources)
