"""AHOS pytest suite — Agent-09 QA. Unit + integration + governance tests.
Run: python3 -m pytest tests/test_ahos.py -q"""
import sys, json, glob
from pathlib import Path
import pandas as pd
import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[1]
for p in [ROOT_DIR, ROOT_DIR / "engine", ROOT_DIR / "tests"]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

try:
    from engine.ahos_backtest import (P, load, add_indicators, position_size, leverage_allowed,
                                     run_backtest, metrics, monte_carlo, walk_forward)
    from tests.validate_n8n import validate
except ImportError:
    from ahos_backtest import (P, load, add_indicators, position_size, leverage_allowed,
                               run_backtest, metrics, monte_carlo, walk_forward)
    from validate_n8n import validate

UPLOAD_BTC = Path("/home/user/uploads/LBANK_BTCUSDT_1h_2000_clean.csv")
RESEARCH_BTC = ROOT_DIR / "research" / "data" / "BTCUSDT_1h_3yr.csv"
BTC = str(UPLOAD_BTC if UPLOAD_BTC.exists() else RESEARCH_BTC)

# ---------- Risk Manager (Agent-08) ----------
def test_risk_sizing_2pct():
    assert abs(position_size(100.0, 100.0, 2.0) - 100.0) < 1e-9  # 2% equity at 2% SL = 100 notional

def test_leverage_cap_binds():
    assert abs(position_size(100.0, 100.0, 0.5) - 200.0) < 1e-9  # capped at 2x equity

def test_zero_guards():
    assert position_size(0, 100, 1) == 0 and position_size(100, 0, 1) == 0 and position_size(100, 100, 0) == 0

def test_leverage_ladder():
    assert leverage_allowed(0.95, True, micro_mode=True) == 2.0
    assert leverage_allowed(0.95, True, micro_mode=False) == 10.0
    assert leverage_allowed(0.50, False, micro_mode=False) == 5.0

# ---------- Strategy determinism / no look-ahead (Agent-02/09) ----------
def test_no_lookahead_indicators():
    df = load(BTC); full = add_indicators(df)
    for k in (30, 500, 1200, 1996):
        part = add_indicators(df.iloc[:k+1])
        for col in ("ema", "atr", "vol_sma"):
            a, b = full[col].iloc[k], part[col].iloc[k]
            if np.isnan(b): assert np.isnan(a)
            else: assert abs(a - b) < 1e-9, f"look-ahead at {k}:{col}"

def test_spec_frozen_constants():
    assert P["vol_mult"] == 1.2 and P["sl_atr"] == 1.5 and P["tp_atr"] == 2.0
    assert P["risk_pct"] == 0.02 and P["leverage"] == 2.0
    assert P["fee_taker"] == 0.00055 and P["slippage"] == 0.0002

def test_backtest_executes_and_records():
    bt = run_backtest(load(BTC).head(500), "BTCUSDT")
    m = metrics(bt)
    assert m["trades"] >= 0 and "profit_factor" in m and "max_drawdown_pct" in m

def test_walk_forward_window_count():
    wf = walk_forward(load(BTC).iloc[:2000].copy(), "BTCUSDT")
    assert len(wf) == 4  # 2000 rows, train 960 + test 240, step 240

def test_monte_carlo_deterministic_seeded():
    bt = run_backtest(load(BTC).head(800), "BTCUSDT")
    m1, m2 = monte_carlo(bt.trades, n=50, seed=7), monte_carlo(bt.trades, n=50, seed=7)
    assert m1 == m2

# ---------- n8n artifacts (Agent-04/09) ----------
def test_n8n_workflows_valid():
    wf_dir = ROOT_DIR / "n8n" / "workflows"
    for f in sorted(wf_dir.glob("*.json")):
        errs, _ = validate(str(f))
        assert not errs, f"{f}: {errs}"

# ---------- Governance (frozen baseline FAILS gates — gate must stay CLOSED) ----------
def test_live_gate_closed_on_current_evidence():
    bt = run_backtest(load(BTC), "BTCUSDT")
    m = metrics(bt)
    fails_gate = not (m["profit_factor"] and m["profit_factor"] > 1.3 and m["win_rate"] > 48 and m["max_drawdown_pct"] < 15)
    assert fails_gate, "Gate must remain CLOSED with current metrics (PF<1.3/DD>15)"
