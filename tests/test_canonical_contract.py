#!/usr/bin/env python3
"""Phase 1 — canonical decision contract (fail-closed validation + invariant)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.canonical.contract import CanonicalDecision, DECISION_VERSION
from architecture.security.gate import (
    VERDICT_VETO, VERDICT_PASS_WITH_UNKNOWN, VERDICT_PASS, CAP_AVOID, CAP_WATCH, CAP_PASS,
)


def _rec(**over):
    base = dict(
        canonical_token_id="abc123",
        chain="solana",
        normalized_contract_address="So11111111111111111111111111111111111111112",
        security_disposition=VERDICT_PASS,
        recommendation_cap=CAP_PASS,
        opportunity_eligible=True,
        opportunity_score=82.0,
        evidence_reference="sha:deadbeef",
        decision_timestamp=1_000_000.0,
    )
    base.update(over)
    return CanonicalDecision(**base)


def test_valid_pass_eligible():
    assert _rec().validate() is True


def test_unknown_cannot_be_eligible():
    assert _rec(security_disposition=VERDICT_PASS_WITH_UNKNOWN,
                recommendation_cap=CAP_WATCH, opportunity_eligible=True).validate() is False


def test_veto_cannot_be_eligible():
    assert _rec(security_disposition=VERDICT_VETO,
                recommendation_cap=CAP_AVOID, opportunity_eligible=True).validate() is False


def test_unknown_not_eligible_is_valid():
    assert _rec(security_disposition=VERDICT_PASS_WITH_UNKNOWN,
                recommendation_cap=CAP_WATCH, opportunity_eligible=False).validate() is True


def test_invalid_vocabulary_fails():
    assert _rec(security_disposition="MAYBE").validate() is False
    assert _rec(recommendation_cap="BUY").validate() is False


def test_version_mismatch_fails():
    assert _rec(decision_version=DECISION_VERSION + 99).validate() is False


def test_missing_identity_or_bad_timestamp_fails():
    assert _rec(canonical_token_id="").validate() is False
    assert _rec(decision_timestamp=0).validate() is False


def test_roundtrip_and_from_dict_fail_closed():
    rec = _rec()
    assert CanonicalDecision.from_dict(rec.to_dict()) == rec
    assert CanonicalDecision.from_dict({}) is None
    assert CanonicalDecision.from_dict("nope") is None
    # eligible-but-not-PASS payload must be rejected on reconstruction
    bad = rec.to_dict()
    bad["security_disposition"] = VERDICT_VETO
    bad["opportunity_eligible"] = True
    assert CanonicalDecision.from_dict(bad) is None


def test_staleness():
    rec = _rec(decision_timestamp=1_000_000.0)
    assert rec.is_stale(now=1_000_000.0 + 100, budget_sec=50) is True
    assert rec.is_stale(now=1_000_000.0 + 10, budget_sec=50) is False
