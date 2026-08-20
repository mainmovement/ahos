#!/usr/bin/env python3
"""Operational (role) expert lenses — advisory, honest UNKNOWN, disagreement preserved."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.intelligence.evidence import (  # noqa: E402
    Evidence, EvidenceBundle, TokenRef, _digest,
)
from architecture.knowledge.operational_lenses import (  # noqa: E402
    OPERATIONAL_LENS_REGISTRY, OperationalLensLibrary,
)

REQUIRED_ROLES = {
    "Market Analyst", "Quant", "Risk Manager", "Security Auditor",
    "Smart Money Analyst", "On-chain Analyst", "Tokenomics Analyst",
    "News Analyst", "Social Analyst", "Narrative Analyst", "Macro Analyst",
    "Contrarian", "Bull", "Bear", "Fraud Hunter", "Exitability Specialist",
    "Data Quality Auditor", "Adversarial Reviewer", "Historian", "Arbitrator",
}


def _atom(key, value, status="VERIFIED"):
    ts = 1.0
    return Evidence(
        key=key, description=key, value=value, provider="test",
        timestamp=ts, freshness_seconds=0.0, status=status,
        source_field=key, sha256=_digest(key, value, "test", ts),
    )


def _bundle(pairs: dict) -> EvidenceBundle:
    items = tuple(_atom(k, v) for k, v in pairs.items())
    ident = TokenRef("solana", "Tok111", "TOK", "Token", "dexscreener", 1.0)
    return EvidenceBundle(identity=ident, items=items, evaluated_at=time.time())


def test_all_twenty_operational_roles_registered():
    lib = OperationalLensLibrary()
    roles = {l.role for l in lib.list_lenses()}
    assert REQUIRED_ROLES <= roles
    assert len(lib.list_lenses()) >= 20
    for lens in lib.list_lenses():
        assert lens.mandate
        assert lens.documented_failures


def test_missing_evidence_is_abstain_not_veto():
    lib = OperationalLensLibrary()
    empty = _bundle({})
    opinions = lib.deliberate(empty)
    by_role = {o.role: o for o in opinions}
    # Risk manager must not treat missing honeypot as False
    assert by_role["Risk Manager"].verdict in ("ABSTAIN", "UNKNOWN")
    assert by_role["Security Auditor"].verdict in ("ABSTAIN", "UNKNOWN")
    assert by_role["Macro Analyst"].verdict == "ABSTAIN"
    assert all(o.verdict != "VETO" for o in opinions if o.role in (
        "Risk Manager", "Security Auditor", "Fraud Hunter"))


def test_honeypot_produces_security_and_risk_veto():
    lib = OperationalLensLibrary()
    b = _bundle({"is_honeypot": True, "liquidity_usd": 50_000.0, "volume_1h": 10_000.0})
    opinions = lib.deliberate(b)
    veto_roles = {o.role for o in opinions if o.verdict == "VETO"}
    assert "Risk Manager" in veto_roles
    assert "Security Auditor" in veto_roles
    assert "Fraud Hunter" in veto_roles


def test_quant_never_claims_a_probability():
    lib = OperationalLensLibrary()
    b = _bundle({"volume_1h": 12_000.0, "txns_1h_buys": 40, "txns_1h_sells": 30})
    opinions = {o.role: o for o in lib.deliberate(b)}
    assert opinions["Quant"].verdict in ("ABSTAIN", "CAUTION")
    assert "probability" in opinions["Quant"].rationale.lower() or \
        "calibrated" in opinions["Quant"].rationale.lower() or \
        opinions["Quant"].verdict == "ABSTAIN"


def test_social_lens_cannot_support_selection():
    lib = OperationalLensLibrary()
    b = _bundle({"virality_label": "VIRAL", "social_presence": {"twitter": "x"}})
    opinions = {o.role: o for o in lib.deliberate(b)}
    assert opinions["Social Analyst"].verdict != "SUPPORT"


def test_synthesis_preserves_disagreement_and_is_advisory():
    lib = OperationalLensLibrary()
    b = _bundle({
        "is_honeypot": True,
        "liquidity_usd": 80_000.0,
        "volume_1h": 40_000.0,
        "txns_1h_buys": 90,
        "txns_1h_sells": 20,
        "has_mint_authority": False,
        "has_freeze_authority": False,
        "top10_concentration": 20.0,
    })
    opinions = lib.deliberate(b)
    syn = lib.synthesize(opinions)
    assert syn["advisory_only"] is True
    assert syn["consensus"] in ("DISAGREEMENT", "VETO")
    assert syn["dissent"]["vetoes"]
    # bull may SUPPORT on depth while security VETOes — disagreement is the point
    assert "vetoes" in syn["dissent"]


def test_extension_without_parallel_subsystem():
    from architecture.knowledge.operational_lenses import OperationalLens, _abstain
    lib = OperationalLensLibrary()
    extra = OperationalLens(
        lens_id="LENS-ROLE-CUSTOM", role="Custom Reviewer",
        mandate="example extension", questions=("?",),
        required_evidence_keys=(), documented_failures=("n/a",),
        domain="INFORMATION_THEORY",
    )
    lib.register(extra, evaluator=lambda lens, b: _abstain(lens, ["n/a"]))
    assert lib.get("LENS-ROLE-CUSTOM") is not None
    assert any(o.lens_id == "LENS-ROLE-CUSTOM" for o in lib.deliberate(_bundle({})))


def test_registry_matches_library():
    assert set(OPERATIONAL_LENS_REGISTRY) == {
        l.lens_id for l in OperationalLensLibrary().list_lenses()
    }
