#!/usr/bin/env python3
"""Tests for K-02 Versioned Claim & Evidence Store (Phase XXII)."""
import sys, time, sqlite3
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from architecture.knowledge.contracts import (
    TrustClass, ClaimCategory, VersionedClaim, EvidenceLink
)
from architecture.knowledge.store import VersionedClaimStore


@pytest.fixture
def store(tmp_path):
    db_file = tmp_path / "test_knowledge.sqlite"
    return VersionedClaimStore(str(db_file))


def test_claim_store_append_only_versioning(store):
    ev = EvidenceLink(
        evidence_id="ev_01",
        source_id="SRC-SHANNON-1948",
        trust_class=TrustClass.VERIFIED_PRIMARY,
        pointer="p380",
        description="Entropy formula",
        raw_sha256="abc",
        retrieved_ts=time.time()
    )
    claim_v1 = VersionedClaim(
        claim_id="CLAIM-INFO-ENTROPY",
        version=1,
        category=ClaimCategory.RESEARCH,
        statement="High entropy volume distributions represent lower information predictability.",
        trust_class=TrustClass.EXPERT_INTERPRETATION,
        author_or_source_id="SRC-SHANNON-1948",
        evidence_links=[ev],
        contradicting_evidence_ids=[],
        contradiction_edges=[],
        provenance_sha256="prov1",
        created_ts=time.time(),
        review_status="ACTIVE",
        confidence=0.90
    )
    res_v1 = store.store_claim(claim_v1)
    assert res_v1 == "CLAIM-INFO-ENTROPY:v1"

    # Store updated claim with new evidence
    claim_v2 = VersionedClaim(
        claim_id="CLAIM-INFO-ENTROPY",
        version=1,  # will auto-increment to v2
        category=ClaimCategory.RESEARCH,
        statement="High entropy volume distributions represent lower information predictability under non-stationary regimes.",
        trust_class=TrustClass.EXPERT_INTERPRETATION,
        author_or_source_id="SRC-SHANNON-1948",
        evidence_links=[ev],
        contradicting_evidence_ids=[],
        contradiction_edges=[],
        provenance_sha256="prov2",
        created_ts=time.time() + 10,
        review_status="ACTIVE",
        confidence=0.95
    )
    res_v2 = store.store_claim(claim_v2)
    assert res_v2 == "CLAIM-INFO-ENTROPY:v2"

    history = store.get_claim_version_history("CLAIM-INFO-ENTROPY")
    assert len(history) == 2
    assert history[0].version == 1
    assert history[1].version == 2

    latest = store.get_latest_claim("CLAIM-INFO-ENTROPY")
    assert latest.version == 2
    assert "non-stationary" in latest.statement


def test_claim_store_ai_cannot_author_canonical(store):
    ai_claim = VersionedClaim(
        claim_id="CLAIM-CANONICAL-UNAUTHORIZED",
        version=1,
        category=ClaimCategory.CANONICAL,
        statement="AI decided that Lane A rules are changed.",
        trust_class=TrustClass.AI_INTERPRETATION,  # AI trying to write CANONICAL directly
        author_or_source_id="LLM-AGENT",
        evidence_links=[],
        contradicting_evidence_ids=[],
        contradiction_edges=[],
        provenance_sha256="fake",
        created_ts=time.time(),
        review_status="ACTIVE",
        confidence=1.0
    )
    with pytest.raises(PermissionError) as exc:
        store.store_claim(ai_claim)
    assert "EPISTEMIC VETO" in str(exc.value)


def test_claim_store_contradiction_tracking(store):
    c1 = VersionedClaim(
        claim_id="CLAIM-EFFICIENT-MARKET",
        version=1,
        category=ClaimCategory.RESEARCH,
        statement="Markets follow random walk with Gaussian returns.",
        trust_class=TrustClass.EXPERT_INTERPRETATION,
        author_or_source_id="FAMA-1970",
        evidence_links=[],
        contradicting_evidence_ids=[],
        contradiction_edges=[],
        provenance_sha256="p1",
        created_ts=time.time(),
        review_status="DISPUTED",
        confidence=0.60
    )
    store.store_claim(c1)

    c2 = VersionedClaim(
        claim_id="CLAIM-FAT-TAILS",
        version=1,
        category=ClaimCategory.RESEARCH,
        statement="Markets exhibit heavy-tailed Mandelbrot power laws, refuting Gaussian hypothesis.",
        trust_class=TrustClass.EXPERT_INTERPRETATION,
        author_or_source_id="SRC-MANDELBROT-1997",
        evidence_links=[],
        contradicting_evidence_ids=[],
        contradiction_edges=[{"target_claim_id": "CLAIM-EFFICIENT-MARKET", "reason": "Infinite variance power law refutes mild Gaussian bell curve."}],
        provenance_sha256="p2",
        created_ts=time.time() + 10,
        review_status="ACTIVE",
        confidence=0.95
    )
    store.store_claim(c2)

    contradictions = store.find_contradictions_for_claim("CLAIM-EFFICIENT-MARKET")
    assert len(contradictions) == 1
    assert contradictions[0]["source_claim_id"] == "CLAIM-FAT-TAILS"
    assert "Gaussian" in contradictions[0]["reason"]
