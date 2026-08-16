"""AHOS Lab test suite — Agent-09 QA. Causality, determinism, registry schema, gate logic.
NOTE: synthetic arrays used ONLY to unit-test gate verdict logic & causality (never market data).
Run: python3 -m pytest tests/test_strategy_lab.py -q"""
import sys, json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
for p in [ROOT_DIR, ROOT_DIR / "engine", ROOT_DIR / "strategy_lab"]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

try:
    from engine.ahos_backtest import load
    from strategy_lab.lab_engine import run_candidate, metrics_of, merge_aux, COST
    from strategy_lab.candidates import GENERATORS
    from strategy_lab.hypotheses import HYPOTHESES
    from strategy_lab.run_lab import verdict, GATES
except ImportError:
    from ahos_backtest import load
    from lab_engine import run_candidate, metrics_of, merge_aux, COST
    from candidates import GENERATORS
    from hypotheses import HYPOTHESES
    from run_lab import verdict, GATES

RESEARCH_DATA = ROOT_DIR / "research" / "data"
BTC3 = str(RESEARCH_DATA / "BTCUSDT_1h_3yr.csv")

# ---------- causality: every generator's entry series identical on prefix ----------
def test_generators_causal_on_real_data():
    df = load(BTC3)
    f = pd.read_csv(RESEARCH_DATA / "BTCUSDT_funding_3yr.csv")
    f["timestamp"] = pd.to_datetime(f.timestamp, utc=True, format="mixed")
    o = pd.read_csv(RESEARCH_DATA / "BTCUSDT_oi_daily_3yr.csv")
    o["timestamp"] = pd.to_datetime(o.timestamp, utc=True, format="mixed")
    full = merge_aux(df, dict(funding_df=f, oi_df=o))
    for hid, gen in GENERATORS.items():
        e_full, _ = gen(full)
        for k in (1000, 15000, len(full)-5):
            e_part, _ = gen(full.iloc[:k])
            tail_full = e_full.iloc[k-1]; tail_part = e_part.iloc[-1]
            same = (pd.isna(tail_full) and pd.isna(tail_part)) or tail_full == tail_part
            assert same, f"{hid} look-ahead at {k}: full={tail_full} part={tail_part}"

# ---------- funding/OI merge never leaks the future ----------
def test_merge_aux_backward_only():
    df = load(BTC3).head(4000)
    f = pd.read_csv(RESEARCH_DATA / "BTCUSDT_funding_3yr.csv").head(40)
    f["timestamp"] = pd.to_datetime(f.timestamp, utc=True, format="mixed")
    m = merge_aux(df, dict(funding_df=f))
    j = f.set_index("timestamp").sort_index()
    for ts, fval in m.dropna(subset=["funding"]).iloc[::997][["timestamp","funding"]].itertuples(index=False):
        assert (j.index <= ts).any()
        assert j[j.index <= ts]["funding_rate"].iloc[-1] == fval, "funding leak: used future settle"

# ---------- engine determinism on real slice ----------
def test_engine_deterministic():
    df = load(BTC3).head(5000)
    e, x = GENERATORS["H1"](df)
    m1 = metrics_of(run_candidate(df, e, x, "BTCUSDT"))
    m2 = metrics_of(run_candidate(df, e, x, "BTCUSDT"))
    assert m1 == m2

# ---------- hypotheses registry completeness ----------
def test_hypothesis_cards_complete():
    req = {"id","family","name","hypothesis","reasoning","market_mechanism",
           "required_data","risk_model","expected_failure_mode","status"}
    for h in HYPOTHESES:
        assert req <= set(h), f"{h['id']} missing fields"
    assert len(HYPOTHESES) >= 9  # batch-1 (H1-9) + batch-2 (H10-12); batches append-only
    batch2 = [h for h in HYPOTHESES if h.get("batch") == 2]
    assert all("gates_override" in h and h["gates_override"]["min_pf_oos"] > 1.3 for h in batch2), \
        "batch-2 must carry the raised multiplicity bar"

# ---------- gate logic (SYNTHETIC fixture — tests the evaluator, not market data) ----------
def _pack(pf, exp, dd, mcp, wfr):
    oos = dict(profit_factor=pf, expectancy=exp, max_drawdown_pct=dd, trades=40, win_rate=50)
    st = dict(profit_factor=max(pf-0.2, 0.01))
    wf = [dict(window=i+1, pf=1.1 if i < int(wfr*5) else 0.9, trades=12) for i in range(5)]
    mc = dict(positive_outcomes_pct=mcp)
    return {"oos": oos, "stress_oos_2xcost": st, "walk_forward": wf, "mc_oos": mc}

def test_verdict_gates():
    good = {s: _pack(1.5, 0.1, 9.0, 80.0, 0.8) for s in ("A","B","C")}
    v, per = verdict(good)
    assert v == "ACCEPTED", per
    weakB = dict(good); weakB["B"] = _pack(1.5, 0.1, 9.0, 80.0, 0.2)  # wf instability
    v, per = verdict(weakB)
    assert v == "REJECTED" or per["B"]["passed"] is False  # at most conditional; must NOT be all-pass
    cat = dict(good); cat["C"] = _pack(0.5, -0.3, 40.0, 20.0, 0.2)   # catastrophic one asset
    v, per = verdict(cat)
    assert v == "REJECTED"

# ---------- registry artifact exists and is consistent ----------
def test_registry_schema():
    reg = json.loads((ROOT_DIR / "strategy_lab" / "registry.json").read_text(encoding="utf-8"))
    assert "updated" in reg and "candidates" in reg
    for hid, c in reg["candidates"].items():
        assert {"name","verdict","evidence"} <= set(c)
        assert c["verdict"] in ("ACCEPTED","REJECTED","NOT TESTED")
