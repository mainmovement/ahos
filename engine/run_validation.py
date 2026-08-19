#!/usr/bin/env python3
"""AHOS Phase-2/3 validation runner — exact recomputation on real data.
Agent-09 QA. Writes reports/validation_results.json + markdown."""
import json, sys, os
from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(ROOT_DIR / "engine") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "engine"))

from ahos_backtest import load, run_backtest, metrics, monte_carlo, walk_forward
from config.paths import get_reports_dir, get_research_dir

UPLOAD_DIR = ROOT_DIR.parent / "uploads"
RESEARCH_DATA = get_research_dir() / "data"

def get_data_file(sym):
    u_clean = UPLOAD_DIR / f"LBANK_{sym}_1h_2000_clean.csv"
    u_raw = UPLOAD_DIR / f"LBANK_{sym}_1h_2000.csv"
    r_3yr = RESEARCH_DATA / f"{sym}_1h_3yr.csv"
    if u_clean.exists(): return str(u_clean)
    if u_raw.exists(): return str(u_raw)
    return str(r_3yr)

DATA = {
    "BTCUSDT": get_data_file("BTCUSDT"),
    "ETHUSDT": get_data_file("ETHUSDT"),
    "SOLUSDT": get_data_file("SOLUSDT"),
}
REMOVED_ROWS_REGISTRY = [  # honest registry — bad OHLCV rows removed by Phase-1B process
    {"symbol": "BTCUSDT", "timestamp": "2026-05-25T00:00:00Z", "reason": "open < low (source data defect)"},
    {"symbol": "BTCUSDT", "timestamp": "2026-06-13T01:00:00Z", "reason": "open < low (source data defect)"},
]

out = {"generated_by": "ahos_backtest.py v1.0", "strategy_spec": "STRATEGY_SPEC_v1.0 (frozen)",
       "data_limitation": "~83 days (2000c) real LBank data; 3-year dataset NOT yet acquired — OOS/WF/MC marked LIMITED",
       "removed_rows_registry": REMOVED_ROWS_REGISTRY, "symbols": {}}

for sym, path in DATA.items():
    df = load(path)
    # Full-sample
    bt = run_backtest(df, sym)
    m_full = metrics(bt)
    # OOS split: train first 70%, test last 30% (no parameter tuning at all — fixed spec)
    cut = int(len(df)*0.7)
    m_train = metrics(run_backtest(df.iloc[:cut].copy(), sym))
    m_oos = metrics(run_backtest(pd.concat([df.iloc[:cut].tail(60), df.iloc[cut:]]).copy(), sym))
    # Walk-forward (limited windows)
    wf = walk_forward(df, sym)
    # Monte Carlo on full-sample trade sequence
    mc = monte_carlo(bt.trades) if bt.trades else None
    out["symbols"][sym] = dict(full=m_full, train_70=m_train, oos_30=m_oos, walk_forward=wf, monte_carlo=mc)

out_file = get_reports_dir() / "validation_results.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2)

for sym, r in out["symbols"].items():
    print(f"\n===== {sym} =====")
    print("FULL :", json.dumps({k: r['full'][k] for k in ('trades','win_rate','profit_factor','total_return_pct','max_drawdown_pct','sharpe_annualized','expectancy')}, default=str))
    print("TRAIN:", json.dumps({k: r['train_70'][k] for k in ('trades','win_rate','profit_factor')}, default=str))
    print("OOS30:", json.dumps({k: r['oos_30'][k] for k in ('trades','win_rate','profit_factor')}, default=str))
    for w in r["walk_forward"]: print("WF   :", json.dumps(w, default=str))
    if r["monte_carlo"]: print("MC   :", json.dumps(r["monte_carlo"]))
print(f"\nSaved {out_file}")
