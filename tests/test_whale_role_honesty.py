#!/usr/bin/env python3
"""Concentration is not identity. wallet_role stays UNKNOWN without evidence."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.intel.whales import WhaleTracker


def test_concentration_does_not_imply_smart_money():
    sig = WhaleTracker().analyze(symbol="TOK", top10_share_pct=55.0)
    assert sig.wallet_role == "UNKNOWN"
    assert any("identity" in u or "wallet_role" in u for u in sig.unknowns)


def test_role_requires_evidence():
    sig = WhaleTracker().analyze(
        symbol="TOK", top10_share_pct=55.0,
        wallet_role="SMART_MONEY", role_evidence=None)
    assert sig.wallet_role == "UNKNOWN"


def test_role_accepted_with_evidence():
    sig = WhaleTracker().analyze(
        symbol="TOK", top10_share_pct=55.0,
        wallet_role="DEPLOYER", role_evidence="deployer_address==top1")
    assert sig.wallet_role == "DEPLOYER"
