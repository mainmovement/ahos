"""Tests for M13.1-M13.6 & M19 Multi-Market Paper Desks."""
from __future__ import annotations

import ast
from pathlib import Path

from architecture.markets.multi_market_desks import (
    CONFLICT,
    DESK_SPECS,
    PAPER_ONLY,
    UNRESOLVED,
    VERIFIED,
    evaluate_all_desks,
    evaluate_desk_paper_cycle,
    verify_two_source_witness,
)


def test_two_source_witness_verified() -> None:
    res = verify_two_source_witness(
        "CRYPTO",
        "BTCUSDT",
        [
            {"source": "binance_public", "price": 68400.0},
            {"source": "coingecko_public", "price": 68430.0},
        ],
    )
    assert res.state == VERIFIED
    assert res.consensus_price == 68415.0
    assert res.paper_only is True
    assert res.live is False
    assert len(res.sources) == 2


def test_single_source_witness_unresolved() -> None:
    res = verify_two_source_witness(
        "US_EQUITIES",
        "SPY",
        [{"source": "stooq_us", "price": 584.20}],
    )
    assert res.state == UNRESOLVED
    assert res.consensus_price is None


def test_divergent_sources_conflict() -> None:
    res = verify_two_source_witness(
        "FOREX",
        "EURUSD",
        [
            {"source": "ecb_ref", "price": 1.0800},
            {"source": "fred_stooq_fx", "price": 1.1200},
        ],
    )
    assert res.state == CONFLICT
    assert res.consensus_price is None


def test_all_seven_desks_evaluate_in_paper_mode() -> None:
    assert PAPER_ONLY is True
    expected_desks = {"GOLD", "OIL", "CRYPTO", "US_EQUITIES", "EU_EQUITIES", "ASIA_EQUITIES", "FOREX"}
    assert set(DESK_SPECS.keys()) == expected_desks
    cycles = evaluate_all_desks()
    assert len(cycles) >= 13
    for c in cycles:
        assert c.paper_only is True
        assert c.live is False
        assert c.witness.state == VERIFIED
        assert c.oms_state == "ACCEPTED_PAPER"

    unresolved_cycle = evaluate_desk_paper_cycle(
        "EU_EQUITIES",
        "DAX",
        [{"source": "stooq_eu", "price": 19480.0}],
    )
    assert unresolved_cycle.witness.state == UNRESOLVED
    assert unresolved_cycle.oms_state == "NO_ENTRY_WITNESS_GATE"


def test_ast_zero_live_order_guarantee() -> None:
    mod_path = Path(__file__).resolve().parents[1] / "architecture" / "markets" / "multi_market_desks.py"
    tree = ast.parse(mod_path.read_text(encoding="utf-8"))
    forbidden_calls = {"requests", "urllib", "httpx", "ccxt", "place_live_order", "send_live_order"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_calls
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_calls
