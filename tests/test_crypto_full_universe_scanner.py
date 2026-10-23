"""Tests for M33 full-market crypto universe scanner."""
from __future__ import annotations

from architecture.markets.crypto_full_universe_scanner import (
    TOTAL_INDEXED_UNIVERSE,
    scan_full_crypto_universe,
)


def test_universe_coverage_and_m33_veto() -> None:
    snap = scan_full_crypto_universe()
    assert snap["total_indexed_universe"] >= 10_000
    assert snap["total_indexed_universe"] == TOTAL_INDEXED_UNIVERSE
    assert snap["paper_only"] is True
    assert snap["real_trading"] is False
    candidates = snap["candidates"]
    assert len(candidates) >= 2
    gems = [c for c in candidates if c["m33_verdict"] == "ELIGIBLE_GEM"]
    vetoes = [c for c in candidates if c["m33_verdict"] == "VETOED_SCAM"]
    assert gems
    assert vetoes
    for g in gems:
        assert g["m33_steps_passed"] == 24
        assert g["two_source_witness"] == "VERIFIED"
    breakout = next(c for c in candidates if c["volume_surge_multiple"] >= 8.0 and c["m33_verdict"] == "ELIGIBLE_GEM")
    assert breakout["discovery_reason_fa"]
