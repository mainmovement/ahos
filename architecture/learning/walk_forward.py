"""M28.1 / TRADING_SKILLS_v2 §8: walk-forward out-of-sample backtest of the live signal brain on REAL history.

Data: Yahoo chart 1h bars (free), last ~365 days. Signals reuse signal_brain primitives (no copy), computed
only from closed bars up to t (causality is TESTED, not assumed: features at t must not change when future
bars are removed). Trades open at bar t close, pay cost per side, exit on stop 2xATR / take 3xATR / signal flip.
Split: first 60% in-sample (IS), last 40% out-of-sample (OOS); only OOS is reported as evidence.
Overfitting checks: Deflated Sharpe Ratio (Bailey & López de Prado 2014) with the real number of trials,
Probability of Backtest Overfitting via CSCV (Bailey et al. 2015), ±15% parameter perturbation.
Output rows feed strategy_red_team.evaluate_strategy_red_team (replacing the hardcoded candidates).
"""
from __future__ import annotations

import itertools
import json
import math
import statistics
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from architecture.markets import signal_brain as sb

UA = {"User-Agent": "Mozilla/5.0 (AHOS research)"}
UNIVERSE = {"BTC": ("BTC-USD", 10.0), "ETH": ("ETH-USD", 10.0), "XAU": ("GC=F", 4.0), "WTI": ("CL=F", 5.0),
            "SPX": ("^GSPC", 3.0), "EURUSD": ("EURUSD=X", 2.0)}          # sym -> (yahoo, cost bps per side)
OUT_REL = Path("reports") / "grok" / "M28" / "walk_forward_snapshot.json"


def fetch_1h(yahoo: str, range_: str = "1y") -> list[list[float]]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.request.quote(yahoo)}?range={range_}&interval=1h"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
        res = json.loads(r.read().decode())["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    out = []
    for o, h, l, c, v in zip(q["open"], q["high"], q["low"], q["close"], q.get("volume") or [0] * len(q["close"])):
        if None not in (o, h, l, c):
            out.append([float(o), float(h), float(l), float(c), float(v or 0)])
    return out


# ---------------- strategies (parameterised, causal) ----------------
def _ema_series(xs: list[float], n: int) -> list[float | None]:
    k, out, e = 2.0 / (n + 1), [], None
    for i, x in enumerate(xs):
        if i + 1 < n:
            out.append(None); continue
        e = sum(xs[i + 1 - n:i + 1]) / n if e is None else x * k + e * (1 - k)
        out.append(e)
    return out


def signals(bars: list[list[float]], kind: str, p: dict[str, float]) -> list[int]:
    """Direction per bar (+1/-1/0) using only bars[0..t]."""
    cl = [b[3] for b in bars]
    f, s = _ema_series(cl, int(p["fast"])), _ema_series(cl, int(p["slow"]))
    hi = _ema_series(cl, int(p["slow"] * 4))
    out = []
    for t in range(len(bars)):
        d = 0
        if kind in ("trend", "trend_candle", "composite") and f[t] and s[t] and hi[t]:
            gap = (f[t] - s[t]) / s[t]
            d = 1 if gap > p["thr"] and cl[t] > hi[t] else -1 if gap < -p["thr"] and cl[t] < hi[t] else 0
        if kind in ("trend_candle", "composite") and d and t >= 1:
            cs = sb.candle_patterns(bars[max(0, t - 30):t + 1] + [bars[t]])   # closed() drops the dup tail
            if cs["available"] and cs["score"] * d < 0:
                d = 0
        if kind in ("zscore", "composite") and t >= 48:
            w = cl[t - 47:t + 1]
            m, sd = statistics.fmean(w), statistics.pstdev(w) or 1e-12
            z = (cl[t] - m) / sd
            zd = -1 if z > p["z"] else 1 if z < -p["z"] else 0
            d = zd if kind == "zscore" else (d if d and (zd == 0 or zd == d) else 0)
        out.append(d)
    return out


def _atr(bars: list[list[float]], t: int, n: int = 14) -> float:
    lo = max(1, t - n + 1)
    trs = [max(bars[i][1] - bars[i][2], abs(bars[i][1] - bars[i - 1][3]), abs(bars[i][2] - bars[i - 1][3])) for i in range(lo, t + 1)]
    return sum(trs) / len(trs) if trs else 0.0


def simulate(bars: list[list[float]], sig: list[int], cost_bps: float, start: int, end: int) -> list[dict[str, Any]]:
    trades, pos = [], None
    c = cost_bps / 1e4
    for t in range(max(start, 15), end):
        px = bars[t][3]
        if pos:
            d = pos["d"]
            hit_stop = (bars[t][2] <= pos["stop"]) if d > 0 else (bars[t][1] >= pos["stop"])
            hit_take = (bars[t][1] >= pos["take"]) if d > 0 else (bars[t][2] <= pos["take"])
            exit_px = pos["stop"] if hit_stop else pos["take"] if hit_take else px if sig[t] == -d or t == end - 1 else None
            if exit_px is not None:
                r = (exit_px / pos["entry"] - 1) * d - 2 * c
                trades.append({"t_open": pos["t"], "t_close": t, "ret": r, "d": d})
                pos = None
        if not pos and sig[t] and t < end - 1:
            a = _atr(bars, t)
            if a > 0:
                pos = {"d": sig[t], "entry": px, "t": t, "stop": px - 2 * a * sig[t], "take": px + 3 * a * sig[t]}
    return trades


# ---------------- statistics ----------------
def sharpe(r: list[float]) -> float:
    if len(r) < 2:
        return 0.0
    sd = statistics.stdev(r)
    return statistics.fmean(r) / sd if sd else 0.0


def _norm_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _norm_ppf(p: float) -> float:
    lo, hi = -10.0, 10.0
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if _norm_cdf(mid) < p else (lo, mid)
    return (lo + hi) / 2


def deflated_sharpe(r: list[float], n_trials: int, trial_sharpes: list[float]) -> float | None:
    """DSR = P[SR* > SR0], SR0 = expected max SR of N trials (per-trade units)."""
    n = len(r)
    if n < 10 or n_trials < 2:
        return None
    sr = sharpe(r)
    m = statistics.fmean(r)
    sd = statistics.pstdev(r) or 1e-12
    skew = sum(((x - m) / sd) ** 3 for x in r) / n
    kurt = sum(((x - m) / sd) ** 4 for x in r) / n
    v = statistics.pvariance(trial_sharpes) if len(trial_sharpes) > 1 else 0.0
    emc = 0.5772156649
    sr0 = math.sqrt(v) * ((1 - emc) * _norm_ppf(1 - 1 / n_trials) + emc * _norm_ppf(1 - 1 / (n_trials * math.e)))
    den = math.sqrt(max(1e-12, 1 - skew * sr + (kurt - 1) / 4 * sr * sr))
    return round(_norm_cdf((sr - sr0) * math.sqrt(n - 1) / den), 4)


def pbo_cscv(perf: list[list[float]], s: int = 8) -> float | None:
    """perf[k][j] = return of trial k in time block j. PBO = share of splits where IS-best ranks below OOS median."""
    if len(perf) < 2 or len(perf[0]) < s:
        return None
    blocks = list(range(s))
    lam = []
    for is_set in itertools.combinations(blocks, s // 2):
        oos = [b for b in blocks if b not in is_set]
        is_perf = [sum(p[b] for b in is_set) for p in perf]
        oos_perf = [sum(p[b] for b in oos) for p in perf]
        best = max(range(len(perf)), key=lambda k: is_perf[k])
        rank = sorted(oos_perf).index(oos_perf[best]) + 1
        w = rank / (len(perf) + 1)
        lam.append(math.log(w / (1 - w)))
    return round(sum(1 for x in lam if x <= 0) / len(lam), 4)


BASE = {"fast": 9, "slow": 26, "thr": 0.0015, "z": 2.0}
KINDS = {"trend": "MTF trend (EMA9/26 + 4x slow filter)", "trend_candle": "Trend + candle/wick veto",
         "zscore": "Z-score mean reversion (48 bars, |z|>2)", "composite": "Composite: trend + candle + z-score agreement"}


def causality_test(bars: list[list[float]], kind: str) -> bool:
    """True = leak detected. Signals up to t must be identical when bars after t are removed."""
    full = signals(bars, kind, BASE)
    for cut in (len(bars) // 2, (3 * len(bars)) // 4):
        part = signals(bars[:cut], kind, BASE)
        if part != full[:cut]:
            return True
    return False


def run(root: Path, *, fetcher: Callable[[str], list[list[float]]] | None = None,
        universe: dict[str, tuple[str, float]] | None = None) -> dict[str, Any]:
    fetcher = fetcher or fetch_1h
    universe = universe or UNIVERSE
    data = {}
    for sym, (y, _) in universe.items():
        try:
            data[sym] = fetcher(y)
        except Exception as exc:
            data[sym] = []
            print(f"fetch failed {sym}: {exc!r}"[:160])
    candidates, trial_rows = [], []
    for kind in KINDS:
        for sym, (y, cost) in universe.items():
            bars = data.get(sym) or []
            if len(bars) < 500:
                continue
            split = int(len(bars) * 0.6)
            sig = signals(bars, kind, BASE)
            oos = simulate(bars, sig, cost, split, len(bars))
            is_tr = simulate(bars, sig, cost, 0, split)
            pert = []
            for k in ("fast", "slow"):
                for f in (0.85, 1.15):
                    p = dict(BASE); p[k] = max(2, round(p[k] * f))
                    pert.append(sharpe([x["ret"] for x in simulate(bars, signals(bars, kind, p), cost, split, len(bars))]))
            sr = sharpe([x["ret"] for x in oos])
            vol = [sb.realized_vol([[0, 0, 0, b[3], 0] for b in bars[max(0, x["t_open"] - 97):x["t_open"] + 2]], 12) or 0 for x in oos]
            med = statistics.median(vol) if vol else 0
            regime = {"HIGH_VOL": round(sum(x["ret"] for x, v in zip(oos, vol) if v > med) * 100, 3),
                      "LOW_VOL": round(sum(x["ret"] for x, v in zip(oos, vol) if v <= med) * 100, 3)}
            blocks = [0.0] * 8
            span = (len(bars) - split) / 8
            for x in oos:
                blocks[min(7, int((x["t_open"] - split) / span))] += x["ret"]
            trial_rows.append(blocks)
            candidates.append({
                "strategy_id": f"wf-{kind}-{sym}", "title": f"{KINDS[kind]} — {sym} (real {y} 1h, OOS last 40%)",
                "returns": [round(x["ret"], 6) for x in oos], "cost_bps": cost,
                "lookahead_leak_detected": causality_test(bars[-1500:], kind),
                "regime_pnl_pct": regime,
                "param_perturbation_sharpe_retention": round(min(pert) / sr, 3) if sr > 0 else 0.0,
                "is_trades": len(is_tr), "is_sharpe": round(sharpe([x["ret"] for x in is_tr]), 4),
                "oos_trades": len(oos), "oos_sharpe": round(sr, 4),
                "oos_total_return_pct": round(sum(x["ret"] for x in oos) * 100, 3),
                "bars": len(bars), "source": f"yahoo_finance:{y}", "data_is_real": True,
            })
    trial_sharpes = [c["oos_sharpe"] for c in candidates]
    for c in candidates:
        c["deflated_sharpe"] = deflated_sharpe(c["returns"], len(candidates), trial_sharpes)
    snap = {"schema": "ahos.walk_forward.v1", "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "paper_only": True, "n_trials": len(candidates), "pbo_cscv": pbo_cscv(trial_rows),
            "promotion_rule": "DSR > 0.95 AND PBO < 0.5 AND OOS trades >= 30 AND survives red team",
            "candidates": candidates}
    p = root / OUT_REL
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap
