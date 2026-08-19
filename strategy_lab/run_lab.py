#!/usr/bin/env python3
"""AHOS Strategy Research Laboratory — battery runner.
Registered hypotheses (strategy_lab/hypotheses.py) on REAL 3.6y data (research/data/).
Battery per candidate×symbol: Train(70%)/OOS(30%) + Walk-Forward(12mo→3mo) + MonteCarlo(1000,seed)
+ stress(costs×2). Verdicts per ACCEPTANCE gates below. NO candidate tuning. Append-only experiment log."""
from __future__ import annotations
import json, sys, os
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

# Add project root, engine and strategy_lab to sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
for p in [ROOT_DIR, ROOT_DIR / "engine", ROOT_DIR / "strategy_lab"]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

try:
    from engine.ahos_backtest import load, monte_carlo
    from strategy_lab.lab_engine import run_candidate, metrics_of, merge_aux, COST
    from strategy_lab.hypotheses import HYPOTHESES
    from strategy_lab.candidates import GENERATORS
except ImportError:
    from ahos_backtest import load, monte_carlo
    from lab_engine import run_candidate, metrics_of, merge_aux, COST
    from hypotheses import HYPOTHESES
    from candidates import GENERATORS

DATA = str(ROOT_DIR / "research" / "data")
SYMS = ["BTCUSDT","ETHUSDT","SOLUSDT"]
GATES = dict(min_pf_oos=1.3, min_expectancy=0.0, max_dd_oos=15.0, min_mc_positive=70.0,
             min_wf_pass_ratio=0.60, min_wf_trades=10, stress_min_pf=1.1)

def load_set(sym, suffix="3yr"):
    df = load(f"{DATA}/{sym}_1h_{suffix}.csv")
    f = pd.read_csv(f"{DATA}/{sym}_funding_{suffix}.csv"); f["timestamp"] = pd.to_datetime(f.timestamp, utc=True, format="mixed")
    o = pd.read_csv(f"{DATA}/{sym}_oi_daily_{suffix}.csv"); o["timestamp"] = pd.to_datetime(o.timestamp, utc=True, format="mixed")
    return merge_aux(df, dict(funding_df=f, oi_df=o))

def run_pack(gen, df, sym, warmup=120):
    """train / oos / wf / mc / stress for one candidate on one symbol."""
    n = len(df); cut = int(n*0.7)
    out = {}
    e_all, x = gen(df)
    bt = run_candidate(df, e_all, x, sym)
    out["full"] = metrics_of(bt); out["_res_full"] = bt
    e_tr, _ = gen(df.iloc[:cut])
    out["train"] = metrics_of(run_candidate(df.iloc[:cut], e_tr, x, sym))
    df_o = df.iloc[cut-warmup:]; e_o, _ = gen(df_o)
    res_o = run_candidate(df_o, e_o, x, sym)
    out["oos"] = metrics_of(res_o); out["_res_oos"] = res_o
    # stress: 2x fees+slippage on OOS
    res_s = run_candidate(df_o, e_o, x, sym, cost=dict(fee=COST["fee"]*2, slip=COST["slip"]*2))
    out["stress_oos_2xcost"] = metrics_of(res_s)
    # walk-forward: 12mo train window → 3mo test (params fixed; 'train' shows context stability)
    wf, i, step = [], 0, 24*90
    tr_len, te_len = 24*365, 24*90
    while i + tr_len + te_len <= n:
        te = df.iloc[i+tr_len-warmup : i+tr_len+te_len]
        e_w, _ = gen(te)
        m = metrics_of(run_candidate(te, e_w, x, sym))
        wf.append(dict(window=len(wf)+1, test=str(te.timestamp.iloc[warmup])[:10]+"→"+str(te.timestamp.iloc[-1])[:10],
                       pf=m.get("profit_factor"), wr=m.get("win_rate"), trades=m.get("trades")))
        i += step
    out["walk_forward"] = wf
    out["mc_oos"] = monte_carlo(res_o.trades) if res_o.trades else None
    return out

def verdict(pack_by_sym, gates=None):
    gates = gates or GATES
    per = {}
    for sym, p in pack_by_sym.items():
        o, st, mc = p["oos"], p["stress_oos_2xcost"], p["mc_oos"]
        wfp = [w for w in p["walk_forward"] if (w["trades"] or 0) >= gates["min_wf_trades"]]
        wf_ratio = (sum(1 for w in wfp if (w["pf"] or 0) > 1.0)/len(wfp)) if wfp else 0.0
        checks = {
          "oos_pf>gate": (o.get("profit_factor") or 0) > gates["min_pf_oos"],
          "expectancy>0": (o.get("expectancy") or -1) > gates["min_expectancy"],
          "oos_dd<15%": (o.get("max_drawdown_pct") or 99) < gates["max_dd_oos"],
          "mc_pos>70%": bool(mc) and mc["positive_outcomes_pct"] > gates["min_mc_positive"],
          "wf_stability>=60%": wf_ratio >= gates["min_wf_pass_ratio"] and len(wfp) >= 3,
          "stress_pf>1.1": (st.get("profit_factor") or 0) > gates["stress_min_pf"],
          "sample>=30 OOS trades": (o.get("trades") or 0) >= 30,
        }
        per[sym] = dict(checks=checks, passed=all(checks.values()),
                        oos=dict(pf=o.get("profit_factor"), wr=o.get("win_rate"), dd=o.get("max_drawdown_pct"),
                                 trades=o.get("trades"), mc_pos=mc["positive_outcomes_pct"] if mc else None),
                        wf_windows=len(wfp), wf_pass_ratio=round(wf_ratio,3),
                        bar=gates["min_pf_oos"])
    n_pass = sum(1 for v in per.values() if v["passed"])
    catastrophic = any((v["oos"]["pf"] or 0) < 0.8 for v in per.values())
    final = "ACCEPTED" if (n_pass >= 2 and not catastrophic) else "REJECTED"
    return final, per

def main():
    ids = None
    if len(sys.argv) > 2 and sys.argv[1] == "--ids":
        ids = set(sys.argv[2].split(","))
    experiments = ROOT_DIR / "research" / "experiments"
    experiments.mkdir(parents=True, exist_ok=True)
    log_path = experiments / f"exp_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}.json"
    record = dict(ts=datetime.now(timezone.utc).isoformat(),
                  data={s: json.load(open(f"{DATA}/MANIFEST.json"))["symbols"][s]["klines_out"]["sha256"][:12] for s in SYMS},
                  gates=GATES, candidates={})
    datasets = {s: load_set(s) for s in SYMS}
    for h in HYPOTHESES:
        hid = h["id"]
        if ids and hid not in ids: continue
        if h["status"].startswith("DATA-BLOCKED"):
            record["candidates"][hid] = dict(name=h["name"], status="DATA-BLOCKED", verdict="NOT TESTED"); continue
        gates = dict(GATES); gates.update(h.get("gates_override") or {})
        gen = GENERATORS[hid]
        scope = h.get("scope") or SYMS            # instrument-scope declared pre-run (H13)
        suffix = "ext" if h.get("batch") == 3 else "3yr"
        scope_sets = {sym: (datasets[sym] if suffix == "3yr" else load_set(sym, suffix)) for sym in scope}
        pack = {sym: run_pack(gen, scope_sets[sym], sym) for sym in scope}
        v, per = verdict(pack, gates)
        if h.get("scope"):  # scoped candidates judged on their declared instrument only
            n_pass = sum(1 for x in per.values() if x["passed"])
            v = "ACCEPTED (scoped:" + "+".join(scope) + ")" if n_pass == len(scope) else "REJECTED"
        acc_note = f" (batch-2 bar PF>{gates['min_pf_oos']})" if gates["min_pf_oos"] != GATES["min_pf_oos"] else ""
        record["candidates"][hid] = dict(name=h["name"], family=h["family"], verdict=v, per_symbol=per,
            detail={sym: dict(full={k: pack[sym]["full"].get(k) for k in ("trades","win_rate","profit_factor","total_return_pct","max_drawdown_pct")},
                              train_pf=pack[sym]["train"].get("profit_factor"),
                              oos={k: pack[sym]["oos"].get(k) for k in ("trades","win_rate","profit_factor","expectancy","total_return_pct","max_drawdown_pct","sharpe_annualized")},
                              stress_oos_pf=pack[sym]["stress_oos_2xcost"].get("profit_factor"),
                              mc_oos=pack[sym]["mc_oos"], walk_forward=pack[sym]["walk_forward"]) for sym in pack})
        acc = per
        acc = per
        print(f"\n=== {hid} {h['name']} → {v}{acc_note} ===")
        for sym in pack.keys():
            o = pack[sym]["oos"]
            print(f"  {sym}: trainPF={pack[sym]['train'].get('profit_factor')} oosPF={o.get('profit_factor')} "
                  f"WR={o.get('win_rate')}% DD={o.get('max_drawdown_pct')}% trades={o.get('trades')} "
                  f"stressPF={pack[sym]['stress_oos_2xcost'].get('profit_factor')} "
                  f"mcPos={pack[sym]['mc_oos']['positive_outcomes_pct'] if pack[sym]['mc_oos'] else 'n/a'}% "
                  f"wfPass={acc[sym]['wf_pass_ratio']*100:.0f}%")
    with open(log_path, "w") as f: json.dump(record, f, indent=2, default=str)
    # update registry (MERGE with existing — never drop prior verdicts)
    reg_path = ROOT_DIR / "strategy_lab" / "registry.json"
    try:
        prev = json.load(open(reg_path))
        candidates = prev.get("candidates", {})
    except Exception:
        candidates = {}
    candidates.update({hid: dict(name=c.get("name"), family=c.get("family","-"),
                                 status=c.get("status","TESTED"), verdict=c["verdict"],
                                 evidence=Path(log_path).name)
                       for hid, c in record["candidates"].items()})
    reg = dict(updated=datetime.now(timezone.utc).isoformat(), experiment_log=Path(log_path).name,
               candidates=candidates)
    with open(reg_path, "w") as f: json.dump(reg, f, indent=2)
    print("\nexperiment log:", log_path)
    print("registry: strategy_lab/registry.json (merged)")

if __name__ == "__main__":
    main()
