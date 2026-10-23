"""M13.x Pump Hunter paper-only alert module tests + AST zero-execution check."""
from __future__ import annotations

import ast
from pathlib import Path

from architecture.markets.pump_hunter import evaluate_pump_candidate


def test_pump_hunter_requires_two_independent_signal_families_and_security_pass():
    vetoed = evaluate_pump_candidate(
        symbol="SCAM/USDT",
        signal_families=["volume_atr_anomaly", "public_whale_inflow"],
        security_gate="FAIL",
    )
    assert vetoed.state == "VETOED_SECURITY"
    assert vetoed.executes_order is False

    single = evaluate_pump_candidate(
        symbol="SOL/USDT",
        signal_families=["volume_atr_anomaly"],
        security_gate="PASS",
    )
    assert single.state == "WATCH_ONLY_SINGLE_FAMILY"
    assert single.executes_order is False

    alert = evaluate_pump_candidate(
        symbol="SOL/USDT",
        signal_families=["volume_atr_anomaly", "public_whale_inflow"],
        security_gate="PASS",
    )
    assert alert.state == "PAPER_ALERT"
    assert alert.paper_only is True
    assert alert.executes_order is False


def test_pump_hunter_ast_contains_zero_execution_or_network_calls():
    src = Path(__file__).resolve().parents[1] / "architecture" / "markets" / "pump_hunter.py"
    tree = ast.parse(src.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mod = getattr(node, "module", "") or ""
            assert "execution" not in mod and "ccxt" not in mod and "requests" not in mod
