"""Tests for M33 24-Step Token Hunter Pipeline."""
from __future__ import annotations

from architecture.markets.token_hunter_24 import (
    STEP_NAMES_24,
    default_token_hunter_fixtures,
    evaluate_token_24_steps,
    format_veto_reasons_fa,
    screen_token_batch,
)


def test_24_steps_defined_and_enforced() -> None:
    assert len(STEP_NAMES_24) == 24
    results = screen_token_batch()
    assert len(results) == 4
    by_sym = {r.symbol: r for r in results}

    assert by_sym["AERO"].state == "PAPER_WATCH_ELIGIBLE"
    assert by_sym["AERO"].steps_passed == 24
    assert by_sym["AERO"].paper_only is True
    assert by_sym["AERO"].live is False
    assert by_sym["AERO"].trades is False

    assert by_sym["JUP"].state == "PAPER_WATCH_ELIGIBLE"
    assert by_sym["JUP"].steps_passed == 24

    assert by_sym["RUGMEME"].state == "VETO_UNSAFE"
    assert len(by_sym["RUGMEME"].veto_reasons) >= 15
    fa = format_veto_reasons_fa(by_sym["RUGMEME"].veto_reasons)
    assert len(fa) == len(by_sym["RUGMEME"].veto_reasons)
    assert all(isinstance(line, str) and len(line) > 0 for line in fa)
    assert any("رد مرحله" in line or "—" in line for line in fa)

    assert by_sym["SINGLE_SRC_TOKEN"].state == "VETO_UNSAFE"
    assert any("02_two_source_security_witness" in reason for reason in by_sym["SINGLE_SRC_TOKEN"].veto_reasons)


def test_paid_source_dextools_triggers_hard_veto() -> None:
    good = dict(default_token_hunter_fixtures()[0])
    good["sources"] = ["goplus", "dextools"]
    verdict = evaluate_token_24_steps(good)
    assert verdict.state == "VETO_UNSAFE"
    assert any("01_free_source_policy" in r for r in verdict.veto_reasons)
