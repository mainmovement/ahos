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


# =====================================================================================================
# Stage 3 / strategy_lab BATCH 4 (H14-H22, pre-registered in strategy_lab/hypotheses.py before this ran)
# =====================================================================================================
B4_OUT_REL = Path("reports") / "grok" / "M28" / "batch4_research.json"
DAILY = {"BTC": ("BTC-USD", 10.0), "ETH": ("ETH-USD", 10.0), "SOL": ("SOL-USD", 12.0), "XAU": ("GC=F", 4.0),
         "XAG": ("SI=F", 6.0), "WTI": ("CL=F", 5.0), "BRENT": ("BZ=F", 5.0), "SPX": ("^GSPC", 3.0), "QQQ": ("QQQ", 3.0),
         "DAX": ("^GDAXI", 4.0), "N225": ("^N225", 4.0), "HSI": ("^HSI", 5.0), "EURUSD": ("EURUSD=X", 2.0),
         "USDJPY": ("JPY=X", 2.0)}
PRIOR_TRIALS = 13 + 24      # strategy_lab H1-H13 + M28.1 walk-forward grid: every trial ever run counts in the DSR


def fetch_daily(yahoo: str, range_: str = "10y") -> list[tuple[int, float, float, float, float]]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.request.quote(yahoo)}?range={range_}&interval=1d"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25) as r:
        res = json.loads(r.read().decode())["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    return [(int(t), float(o), float(h), float(l), float(c)) for t, o, h, l, c in
            zip(res["timestamp"], q["open"], q["high"], q["low"], q["close"]) if None not in (o, h, l, c)]


def fetch_1h_ts(yahoo: str, range_: str = "730d") -> list[tuple[int, float, float, float, float]]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.request.quote(yahoo)}?range={range_}&interval=1h"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25) as r:
        res = json.loads(r.read().decode())["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    return [(int(t), float(o), float(h), float(l), float(c)) for t, o, h, l, c in
            zip(res["timestamp"], q["open"], q["high"], q["low"], q["close"]) if None not in (o, h, l, c)]


def _day(ts: int) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def _hold_trades(bars, entries: dict[int, int], hold: int, cost_bps: float) -> list[dict[str, Any]]:
    """entries: bar index -> direction. Non-overlapping fixed-hold trades, enter at close[i], exit close[i+hold]."""
    out, busy_until, c = [], -1, cost_bps / 1e4
    for i in sorted(entries):
        if i <= busy_until or i + hold >= len(bars) or not entries[i]:
            continue
        d = entries[i]
        out.append({"t_open": i, "t_close": i + hold, "ts_open": bars[i][0], "ret": (bars[i + hold][4] / bars[i][4] - 1) * d - 2 * c, "d": d})
        busy_until = i + hold
    return out


def _cand(hid: str, sym: str, title: str, trades: list[dict[str, Any]], split_ts: int, cost: float, source: str,
          extra: dict[str, Any] | None = None) -> dict[str, Any]:
    oos = [t for t in trades if t["ts_open"] >= split_ts]
    ins = [t for t in trades if t["ts_open"] < split_ts]
    r = [t["ret"] for t in oos]
    return {"strategy_id": f"b4-{hid}-{sym}", "hypothesis_id": hid, "title": title, "returns": [round(x, 6) for x in r],
            "cost_bps": cost, "lookahead_leak_detected": False, "is_trades": len(ins),
            "is_sharpe": round(sharpe([t["ret"] for t in ins]), 4), "oos_trades": len(oos), "oos_sharpe": round(sharpe(r), 4),
            "oos_total_return_pct": round(sum(r) * 100, 3), "oos_hit_rate": round(sum(1 for x in r if x > 0) / len(r), 3) if r else None,
            "split_utc": _day(split_ts), "source": source, "data_is_real": True,
            "_oos_by_day": {_day(t["ts_open"]): t["ret"] for t in oos}, "_is_by_day": {_day(t["ts_open"]): t["ret"] for t in ins},
            **(extra or {})}


def _benchmark(bars, hold: int, split_ts: int, cost_bps: float, trades: list[dict[str, Any]]) -> dict[str, Any]:
    """Same-direction, same-hold UNCONDITIONAL trades over the OOS window: is the signal better than just being in the market?"""
    c = cost_bps / 1e4
    oos = [t for t in trades if t["ts_open"] >= split_ts]
    if not oos:
        return {}
    i0 = next((i for i, b in enumerate(bars) if b[0] >= split_ts), len(bars))
    base = [(bars[i + hold][4] / bars[i][4] - 1) for i in range(i0, len(bars) - hold, hold)]
    if not base:
        return {}
    long_share = sum(1 for t in oos if t["d"] > 0) / len(oos)
    unc = statistics.fmean(base) * (2 * long_share - 1) - 2 * c
    sig = statistics.fmean([t["ret"] for t in oos])
    return {"oos_mean_trade": round(sig, 5), "unconditional_mean_trade": round(unc, 5),
            "excess_per_trade": round(sig - unc, 5), "long_share": round(long_share, 3)}


def _split_ts(bars, frac: float = 0.6) -> int:
    return bars[int(len(bars) * frac)][0]


def h14_netflow(daily, flows_by_asset, zthr: float = 1.5, _robust: bool = True):
    out = []
    for sym, asset in (("BTC", "btc"), ("ETH", "eth")):
        bars, fl = daily.get(sym) or [], flows_by_asset.get(asset) or []
        if len(bars) < 500 or len(fl) < 200:
            continue
        nf = {f["date"]: f["netflow"] for f in fl}
        dates = sorted(nf)
        ent = {}
        for i, b in enumerate(bars):
            cutoff = _day(b[0] - 2 * 86400)                      # only flows dated <= t-2 (publication lag)
            known = [d for d in dates if d <= cutoff][-91:]
            if len(known) < 91:
                continue
            w = [nf[d] for d in known[:-1]]
            sd = statistics.pstdev(w) or 1e-12
            z = (nf[known[-1]] - statistics.fmean(w)) / sd
            if abs(z) > zthr:
                ent[i] = -1 if z > 0 else 1
        tr = _hold_trades(bars, ent, 3, DAILY[sym][1])
        out.append(_cand("H14", sym, f"Exchange netflow z90 ±1.5, 3d hold — {sym}", tr, _split_ts(bars), DAILY[sym][1],
                         "coinmetrics_community+yahoo_daily", {"benchmark": _benchmark(bars, 3, _split_ts(bars), DAILY[sym][1], tr)}))
    return out


def h15_stablecoin(daily, stable, pctl: float = 0.8, _robust: bool = True):
    out = []
    sv = {s["date"]: s["usd"] for s in stable}
    dates = sorted(sv)
    g7 = {}
    for k in range(7, len(dates)):
        if sv[dates[k - 7]] > 0:
            g7[dates[k]] = sv[dates[k]] / sv[dates[k - 7]] - 1
    gd = sorted(g7)
    for sym in ("BTC", "ETH"):
        bars = daily.get(sym) or []
        ent = {}
        for i, b in enumerate(bars):
            cutoff = _day(b[0] - 86400)
            hist = [g7[d] for d in gd if d <= cutoff][-366:]
            if len(hist) < 366:
                continue
            thr = sorted(hist[:-1])[min(364, int(pctl * 365))]
            if hist[-1] > thr:
                ent[i] = 1
        tr = _hold_trades(bars, ent, 7, DAILY[sym][1])
        out.append(_cand("H15", sym, f"Stablecoin 7d supply growth > trailing-year p80, long 7d — {sym}", tr, _split_ts(bars),
                         DAILY[sym][1], "defillama_stablecoins+yahoo_daily", {"benchmark": _benchmark(bars, 7, _split_ts(bars), DAILY[sym][1], tr)}))
    return out


def h16_fomc(daily, cal):
    out = []
    days = sorted({e["at_utc"][:10] for e in cal.get("events") or [] if e["event"] == "FOMC_STATEMENT"})
    for sym in ("SPX", "QQQ"):
        bars = daily.get(sym) or []
        idx = {_day(b[0]): i for i, b in enumerate(bars)}
        ent = {idx[d] - 1: 1 for d in days if d in idx and idx[d] >= 1 and d <= _day(bars[-1][0])}
        tr = _hold_trades(bars, ent, 1, DAILY[sym][1])
        split = _split_ts([bars[i] for i in sorted(ent)]) if ent else 0
        out.append(_cand("H16", sym, f"Long close(t-1)->close(FOMC day) — {sym}", tr, split, DAILY[sym][1],
                         "federalreserve.gov+yahoo_daily", {"events_in_sample": len(ent)}))
    return out


def h17_eia(h1_wti, cal):
    bars = h1_wti
    if len(bars) < 500:
        return []
    rel = [int(datetime.fromisoformat(e["at_utc"]).timestamp()) for e in cal.get("events") or [] if e["event"] == "EIA_WPSR"]
    ts = [b[0] for b in bars]
    ent = {}
    import bisect
    for r in rel:
        i = bisect.bisect_right(ts, r) - 1
        if 0 <= i < len(bars) and r - ts[i] < 3600 and bars[i][0] + 3600 > r:
            d = 1 if bars[i][4] > bars[i][1] else -1 if bars[i][4] < bars[i][1] else 0
            if d:
                ent[i] = d
    tr = _hold_trades(bars, ent, 3, 5.0)
    split = _split_ts([bars[i] for i in sorted(ent)]) if ent else 0
    return [_cand("H17", "WTI", "EIA release-hour direction, hold 3h — WTI (CL=F 1h)", tr, split, 5.0,
                  "eia.gov schedule+yahoo_1h", {"events_in_sample": len(ent)})]


def h18_tsmom(daily, lb: int = 252, _robust: bool = True):
    out = []
    for sym, (y, cost) in DAILY.items():
        bars = daily.get(sym) or []
        if len(bars) < 600:
            continue
        ent = {i: (1 if bars[i][4] > bars[i - lb][4] else -1) for i in range(lb, len(bars) - 21, 21)}
        tr = _hold_trades(bars, ent, 21, cost)
        out.append(_cand("H18", sym, f"TSMOM 252d sign, 21d hold — {sym}", tr, _split_ts(bars), cost, f"yahoo_daily:{y}",
                         {"benchmark": _benchmark(bars, 21, _split_ts(bars), cost, tr)}))
    return out


def h19_logit(h1: dict[str, list], universe: dict[str, tuple[str, float]]):
    import numpy as np
    out = []
    for sym, (y, cost) in universe.items():
        raw = h1.get(sym) or []
        if len(raw) < 1500:
            continue
        bars = [[b[1], b[2], b[3], b[4], 0.0] for b in raw]
        cl = np.array([b[3] for b in bars])
        f, s = _ema_series(list(cl), 9), _ema_series(list(cl), 26)
        X, Y, idx = [], [], []
        H = 12
        for t in range(120, len(bars) - H):
            if not f[t] or not s[t]:
                continue
            w = cl[t - 47:t + 1]
            z = (cl[t] - w.mean()) / (w.std() or 1e-12)
            gap = (f[t] - s[t]) / s[t]
            r1 = cl[t] / cl[t - 1] - 1; r12 = cl[t] / cl[t - 12] - 1
            rv = np.std(np.diff(np.log(cl[t - 24:t + 1]))); rv100 = np.std(np.diff(np.log(cl[t - 100:t + 1])))
            X.append([gap * 100, z, r1 * 100, r12 * 100, (rv / (rv100 or 1e-12)) - 1])
            Y.append(1.0 if cl[t + H] > cl[t] else 0.0); idx.append(t)
        X, Y = np.array(X), np.array(Y)
        n_is = int(len(X) * 0.6)
        mu, sd = X[:n_is].mean(0), X[:n_is].std(0) + 1e-12
        Xs = np.c_[np.ones(len(X)), (X - mu) / sd]
        wv = np.zeros(Xs.shape[1])
        for _ in range(400):                           # L2-regularised logistic regression, fitted on IS only
            p = 1 / (1 + np.exp(-Xs[:n_is] @ wv))
            wv -= 0.1 * (Xs[:n_is].T @ (p - Y[:n_is]) / n_is + 0.01 * wv)
        p_oos = 1 / (1 + np.exp(-Xs[n_is:] @ wv))
        base = Y[:n_is].mean()
        brier = float(np.mean((p_oos - Y[n_is:]) ** 2)); brier_base = float(np.mean((base - Y[n_is:]) ** 2))
        ent = {}
        for k, t in enumerate(idx):
            if k < n_is:
                pk = 1 / (1 + np.exp(-Xs[k] @ wv))
            else:
                pk = p_oos[k - n_is]
            if pk > 0.55: ent[t] = 1
            elif pk < 0.45: ent[t] = -1
        ts_bars = [(b[0], b[1], b[2], b[3], b[4]) for b in raw]
        tr = _hold_trades(ts_bars, ent, H, cost)
        out.append(_cand("H19", sym, f"Calibrated logistic of brain features, p>0.55/<0.45, 12h hold — {sym}", tr,
                         raw[idx[n_is]][0], cost, f"yahoo_1h:{y}",
                         {"oos_brier": round(brier, 5), "oos_brier_base_rate": round(brier_base, 5),
                          "brier_skill": round(1 - brier / brier_base, 4) if brier_base else None,
                          "coefficients": [round(float(c), 4) for c in wv]}))
    return out


def hrp_weights(cov, corr):
    """Lopez de Prado (2016) HRP: single-linkage on sqrt((1-rho)/2), quasi-diagonal order, recursive bisection."""
    import numpy as np
    n = len(cov)
    dist = np.sqrt(np.clip((1 - corr) / 2, 0, 1))
    clusters = {i: [i] for i in range(n)}
    order_tree = {i: [i] for i in range(n)}
    active = list(range(n))
    nid = n
    while len(active) > 1:
        best = None
        for a_i in range(len(active)):
            for b_i in range(a_i + 1, len(active)):
                a, b = active[a_i], active[b_i]
                dmin = min(dist[x][y] for x in clusters[a] for y in clusters[b])
                if best is None or dmin < best[0]:
                    best = (dmin, a, b)
        _, a, b = best
        clusters[nid] = clusters[a] + clusters[b]
        order_tree[nid] = order_tree[a] + order_tree[b]
        active = [x for x in active if x not in (a, b)] + [nid]
        nid += 1
    order = order_tree[active[0]]
    w = np.ones(n)
    stack = [order]
    while stack:
        items = stack.pop()
        if len(items) < 2:
            continue
        h = len(items) // 2
        left, right = items[:h], items[h:]

        def cvar(ix):
            c = cov[np.ix_(ix, ix)]
            iv = 1 / np.diag(c); iv /= iv.sum()
            return float(iv @ c @ iv)
        vl, vr = cvar(left), cvar(right)
        alpha = 1 - vl / (vl + vr)
        w[left] *= alpha; w[right] *= 1 - alpha
        stack += [left, right]
    return w / w.sum()


def h20_hrp(cands: list[dict[str, Any]]):
    import numpy as np
    streams = [c for c in cands if len(c["_is_by_day"]) >= 10 and len(c["_oos_by_day"]) >= 5]
    if len(streams) < 3:
        return None
    is_days = sorted({d for c in streams for d in c["_is_by_day"]})
    oos_days = sorted({d for c in streams for d in c["_oos_by_day"]})
    R_is = np.array([[c["_is_by_day"].get(d, 0.0) for c in streams] for d in is_days])
    R_oos = np.array([[c["_oos_by_day"].get(d, 0.0) for c in streams] for d in oos_days])
    cov = np.cov(R_is.T) + np.eye(len(streams)) * 1e-10
    sd = np.sqrt(np.diag(cov)); corr = cov / np.outer(sd, sd)
    w = hrp_weights(cov, corr)
    eq = np.ones(len(streams)) / len(streams)
    p_h, p_e = R_oos @ w, R_oos @ eq
    ann = math.sqrt(252)
    def _sr(x): return float(x.mean() / x.std() * ann) if x.std() else 0.0
    return {"strategy_id": "b4-H20-HRP", "hypothesis_id": "H20", "streams": len(streams),
            "oos_days": len(oos_days), "oos_sharpe_ann_hrp": round(_sr(p_h), 3), "oos_sharpe_ann_equal": round(_sr(p_e), 3),
            "oos_total_return_pct_hrp": round(float(p_h.sum()) * 100, 3), "oos_total_return_pct_equal": round(float(p_e.sum()) * 100, 3),
            "top_weights": sorted([[c["strategy_id"], round(float(x), 4)] for c, x in zip(streams, w)], key=lambda r: -r[1])[:8],
            "verdict": "HRP_BETTER" if _sr(p_h) > _sr(p_e) else "HRP_NOT_BETTER",
            "note": "Allocation only; it cannot create edge if the streams have none."}


def _regime_and_perturbation(cands, daily, flows, stable):
    """Red-team evidence measured, never defaulted: OOS PnL by HIGH/LOW 30d-vol regime, and Sharpe retention under ±15%."""
    pert = {}
    for f in (0.85, 1.15):
        for c in h14_netflow(daily, flows, zthr=1.5 * f) + h15_stablecoin(daily, stable, pctl=min(0.95, 0.8 * f)) \
                + h18_tsmom(daily, lb=round(252 * f)):
            pert.setdefault(c["strategy_id"], []).append(c["oos_sharpe"])
    for c in cands:
        sym = c["strategy_id"].split("-")[-1]
        bars = daily.get(sym) or []
        if c["strategy_id"] in pert and c["oos_sharpe"] > 0:
            c["param_perturbation_sharpe_retention"] = round(min(pert[c["strategy_id"]]) / c["oos_sharpe"], 3)
        _regime_pnl(c, bars)


def _regime_pnl(c: dict[str, Any], bars) -> None:
    """OOS PnL split by HIGH/LOW trailing-30d realized vol of ``bars`` (median split); absent evidence -> no field."""
    if not bars or not c.get("_oos_by_day"):
        return
    idx = {_day(b[0]): i for i, b in enumerate(bars)}
    vols = {}
    for d in c["_oos_by_day"]:
        i = idx.get(d)
        if i and i > 31:
            rr = [bars[k][4] / bars[k - 1][4] - 1 for k in range(i - 29, i + 1)]
            vols[d] = statistics.pstdev(rr)
    if vols:
        med = statistics.median(vols.values())
        c["regime_pnl_pct"] = {"HIGH_VOL": round(sum(c["_oos_by_day"][d] for d, v in vols.items() if v > med) * 100, 3),
                               "LOW_VOL": round(sum(c["_oos_by_day"][d] for d, v in vols.items() if v <= med) * 100, 3)}


def run_batch4(root: Path) -> dict[str, Any]:
    from architecture.markets import macro_calendar as mc, onchain_flows as oc
    errors = {}
    daily = {}
    for sym, (y, _) in DAILY.items():
        try:
            daily[sym] = fetch_daily(y)
        except Exception as exc:
            errors[sym] = repr(exc)[:120]
    h1 = {}
    for sym, (y, _) in UNIVERSE.items():
        try:
            h1[sym] = fetch_1h_ts(y, "1y")
        except Exception as exc:
            errors[f"{sym}_1h"] = repr(exc)[:120]
    try:
        wti2y = fetch_1h_ts("CL=F", "730d")
    except Exception as exc:
        wti2y, errors["WTI_2y"] = [], repr(exc)[:120]
    flows = {a: oc.exchange_flows_history(a, "2019-01-01") for a in ("btc", "eth")}
    stable = oc.stablecoin_supply_history()
    cal = mc.build_calendar(root)
    cands = h14_netflow(daily, flows) + h15_stablecoin(daily, stable) + h16_fomc(daily, cal) + h17_eia(wti2y, cal) \
        + h18_tsmom(daily) + h19_logit(h1, UNIVERSE)
    _regime_and_perturbation(cands, daily, flows, stable)
    prior = _load_prior_sharpes(root)
    trial_sharpes = [c["oos_sharpe"] for c in cands] + prior
    n_trials = PRIOR_TRIALS + len(cands)
    for c in cands:
        c["deflated_sharpe"] = deflated_sharpe(c["returns"], n_trials, trial_sharpes)
    blocks = []
    for c in cands:
        b = [0.0] * 8
        r = c["returns"]
        for k, x in enumerate(r):
            b[min(7, k * 8 // max(1, len(r)))] += x
        blocks.append(b)
    pbo = pbo_cscv([b for b, c in zip(blocks, cands) if c["oos_trades"] >= 8])
    hrp = h20_hrp(cands)
    for c in cands:
        ok = (c["oos_trades"] >= 30 and (c["deflated_sharpe"] or 0) > 0.95 and pbo is not None and pbo < 0.5)
        c["gate"] = "PASS_STATS" if ok else "FAIL"
        c["gate_detail"] = f"oos_n={c['oos_trades']} DSR={c['deflated_sharpe']} PBO={pbo}"
    clean = [{k: v for k, v in c.items() if not k.startswith("_")} for c in cands]
    snap = {"schema": "ahos.strategy_lab.batch4.v1", "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "paper_only": True, "n_trials_this_batch": len(cands), "n_trials_counted_in_dsr": n_trials, "pbo_cscv": pbo,
            "promotion_rule": "OOS trades>=30 AND DSR>0.95 (all trials counted) AND PBO<0.5 AND survives strategy_red_team",
            "insufficient_history": {"H21": "OKX funding history ~3 months (free)", "H22": "GDELT DOC ~3 months, RSS not archived"},
            "hrp": hrp, "errors": errors, "candidates": clean}
    p = root / B4_OUT_REL
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def _load_prior_sharpes(root: Path) -> list[float]:
    try:
        s = json.loads((root / OUT_REL).read_text(encoding="utf-8"))
        return [c["oos_sharpe"] for c in s.get("candidates") or []]
    except Exception:
        return []


# =====================================================================================================
# BATCH 5 — H23-H28, pre-registered 2026-10-24 13:17 Tehran (strategy_lab/hypotheses.py _B5) BEFORE this code ran.
# Free data only. Gate: OOS obs >= 30, DSR = min(per-observation DSR, frequency-annualized DSR) > 0.95 with every
# trial ever run counted, PBO (time-aligned CSCV, 16 calendar blocks) < 0.5, and SURVIVED_RED_TEAM.
# =====================================================================================================
B5_OUT_REL = Path("reports") / "grok" / "M28" / "batch5_research.json"
IMPACT_OUT_REL = Path("reports") / "grok" / "M19" / "event_impact_matrix.json"
MACRO_DAILY = {"DXY": "DX-Y.NYB", "US10Y": "^TNX"}
NO_REAL_VOLUME = ("EURUSD", "USDJPY")
H26_PAIRS = {"FOMC_STATEMENT": ("SPX", "QQQ", "XAU", "EURUSD", "USDJPY", "BTC"), "EIA_WPSR": ("WTI", "BRENT")}
H26_NOT_RUN = {"ECB_GOV_COUNCIL": "official calendar holds <30 dated decisions", "BOJ_MPM_DECISION": "<30 dated decisions",
               "BOE_MPC_DECISION": "<30 dated decisions", "OPEC_MINISTERIAL": "<30 dated meetings"}
BL_ASSETS = ("BTC", "ETH", "XAU", "WTI", "SPX", "DAX", "N225", "EURUSD")
YEAR_S = 365.25 * 86400
PBO_BLOCKS = 16


def fetch_daily_v(yahoo: str, range_: str = "10y") -> list[tuple[int, float, float, float, float, float]]:
    """fetch_daily plus volume at index 5 (0.0 where the vendor reports none — never imputed)."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.request.quote(yahoo)}?range={range_}&interval=1d"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25) as r:
        res = json.loads(r.read().decode())["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    vols = q.get("volume") or [None] * len(q["close"])
    return [(int(t), float(o), float(h), float(l), float(c), float(v or 0.0)) for t, o, h, l, c, v in
            zip(res["timestamp"], q["open"], q["high"], q["low"], q["close"], vols) if None not in (o, h, l, c)]


def clears_cost_hurdle(expected_edge: float, one_way_turnover: float, cost_bps: float, *, multiple: float = 2.5) -> bool:
    """True when |expected edge| exceeds `multiple` times the round-trip cost of this rebalance.

    one_way_turnover is 0.5 * sum(|dw|). Round trip = that turnover * 2 * (cost_bps / 1e4).
    A zero-turnover hold clears, because it pays nothing.
    """
    if one_way_turnover <= 1e-12:
        return True
    round_trip = abs(one_way_turnover) * 2.0 * (cost_bps / 1e4)
    return abs(expected_edge) > multiple * round_trip


def apply_weight_hysteresis(previous: list[float], proposed: list[float], tau: float) -> list[float]:
    """Keep each previous weight unless |delta| > tau, then re-scale to gross 1."""
    if len(previous) != len(proposed):
        raise ValueError("weight vectors differ in length")
    out = []
    changed = False
    for prev, new in zip(previous, proposed):
        if abs(new - prev) > tau:
            out.append(new)
            changed = True
        else:
            out.append(prev)
    if not changed:
        return list(previous)
    gross = sum(abs(x) for x in out)
    if gross <= 0:
        return list(previous)
    return [x / gross for x in out]


def safe_simple_return(p0: float, p1: float) -> float | None:
    """Percent return. Undefined (None) when either price is non-positive, so a negative commodity print
    drops that day instead of producing NaN/Inf from a logarithm."""
    if p0 > 0.0 and p1 > 0.0:
        return p1 / p0 - 1.0
    return None


def wilder_atr(bars, n: int = 14) -> list[float | None]:
    """ATR at each bar from prior true ranges only (index i uses bars up to i, never i+1)."""
    out: list[float | None] = [None] * len(bars)
    prev = None
    for i, b in enumerate(bars):
        h, l, c = b[2], b[3], b[4]
        if i == 0:
            tr = h - l
        else:
            pc = bars[i - 1][4]
            tr = max(h - l, abs(h - pc), abs(l - pc))
        prev = tr if prev is None else (prev * (n - 1) + tr) / n
        out[i] = prev if i >= n else None
    return out


def atr_normalized_return(prev_close: float, close: float, prev_atr: float | None) -> float | None:
    """Dollar change divided by the prior bar's ATR. Finite when price itself is negative."""
    if prev_atr is None or prev_atr <= 0.0:
        return None
    return (close - prev_close) / prev_atr


def _bar_day(ts: int) -> str:
    """Trading date of a Yahoo daily bar (FX/futures bars are stamped the prior evening UTC)."""
    return _day(ts + 6 * 3600)


def _ts(day: str) -> int:
    return int(datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def deflated_sharpe_annualized(r: list[float], obs_per_year: float, n_trials: int, trial_ann_sharpes: list[float]) -> float | None:
    """DSR with the expected-max benchmark built from ANNUALIZED trial Sharpes, converted back to this trial's
    observation frequency — trials sampled at different frequencies are otherwise not comparable."""
    n = len(r)
    if n < 10 or n_trials < 2 or obs_per_year <= 0:
        return None
    sr = sharpe(r)
    m = statistics.fmean(r)
    sd = statistics.pstdev(r) or 1e-12
    skew = sum(((x - m) / sd) ** 3 for x in r) / n
    kurt = sum(((x - m) / sd) ** 4 for x in r) / n
    v = statistics.pvariance(trial_ann_sharpes) if len(trial_ann_sharpes) > 1 else 0.0
    emc = 0.5772156649
    sr0 = math.sqrt(v) * ((1 - emc) * _norm_ppf(1 - 1 / n_trials) + emc * _norm_ppf(1 - 1 / (n_trials * math.e)))
    sr0 /= math.sqrt(obs_per_year)
    den = math.sqrt(max(1e-12, 1 - skew * sr + (kurt - 1) / 4 * sr * sr))
    return round(_norm_cdf((sr - sr0) * math.sqrt(n - 1) / den), 4)


def _with_close(trades: list[dict[str, Any]], bars) -> list[dict[str, Any]]:
    for t in trades:
        t["ts_close"] = bars[t["t_close"]][0]
    return trades


def _purged_folds(trades: list[dict[str, Any]], split_ts: int, end_ts: int, k: int = 4, embargo_s: int = 0) -> dict[str, Any]:
    """Forward-only OOS folds; a trade whose holding period straddles a fold edge is purged, and ``embargo_s``
    after each edge is skipped (needed only where IS data fitted something)."""
    edges = [split_ts + (end_ts - split_ts) * j // k for j in range(k + 1)]
    folds, purged = [], 0
    for j in range(k):
        lo, hi = edges[j] + embargo_s, edges[j + 1]
        inside = [t for t in trades if lo <= t["ts_open"] < hi]
        keep = [t for t in inside if t["ts_close"] <= hi or j == k - 1]
        purged += len(inside) - len(keep)
        r = [t["ret"] for t in keep]
        folds.append({"fold": j + 1, "from": _day(lo), "to": _day(hi), "n": len(r),
                      "mean_ret_pct": round(statistics.fmean(r) * 100, 4) if r else None, "sharpe": round(sharpe(r), 4)})
    scored = [f for f in folds if f["n"] >= 3]
    return {"folds": folds, "purged_trades": purged, "embargo_days": embargo_s // 86400,
            "positive_folds": sum(1 for f in scored if (f["mean_ret_pct"] or 0) > 0), "scored_folds": len(scored)}


def _cand5(hid: str, sym: str, title: str, trades: list[dict[str, Any]], split_ts: int, cost: float, source: str, *,
           obs_per_year: float, end_ts: int, unit: str = "trade", embargo_s: int = 0,
           extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """batch-4 candidate row plus: IS trades realized after the split are purged, observation frequency, folds."""
    purged = {id(t) for t in trades if t["ts_open"] < split_ts < t["ts_close"]}
    oos_from = split_ts + embargo_s
    kept = [t for t in trades if id(t) not in purged and not (split_ts <= t["ts_open"] < oos_from)]
    c = _cand(hid, sym, title, kept, oos_from, cost, source, extra)
    c.update({"strategy_id": f"b5-{hid}-{sym}", "observation_unit": unit, "obs_per_year": round(obs_per_year, 3),
              "purged_is_trades": len(purged), "embargo_days": embargo_s // 86400,
              "walk_forward_folds": _purged_folds([t for t in kept if t["ts_open"] >= oos_from], oos_from, end_ts),
              "_trades": [(t["ts_open"], t["ts_close"], t["ret"]) for t in kept]})
    return c


def _span_years(t0: int, t1: int) -> float:
    return max(1e-6, (t1 - t0) / YEAR_S)


# ---------------- H23 regime x flow x liquidity confluence ----------------
def _latest_fresh(dates: list[str], table: dict[str, Any], cutoff: str, max_age_days: int = 5):
    import bisect
    j = bisect.bisect_right(dates, cutoff) - 1
    if j < 0 or dates[j] < _day(_ts(cutoff) - max_age_days * 86400):
        return None
    return table[dates[j]]


def _netflow_z(fl: list[dict[str, Any]]) -> dict[str, float]:
    nf = sorted((f["date"], f["netflow"]) for f in fl)
    vals = [v for _, v in nf]
    out = {}
    for k in range(90, len(nf)):
        w = vals[k - 90:k]
        out[nf[k][0]] = (vals[k] - statistics.fmean(w)) / (statistics.pstdev(w) or 1e-12)
    return out


def _stable_impulse(stable: list[dict[str, Any]], pctl: float) -> dict[str, bool]:
    sv = {s["date"]: s["usd"] for s in stable}
    dates = sorted(sv)
    g = [(dates[k], sv[dates[k]] / sv[dates[k - 7]] - 1) for k in range(7, len(dates)) if sv[dates[k - 7]] > 0]
    out = {}
    for k in range(365, len(g)):
        thr = sorted(x for _, x in g[k - 365:k])[min(364, int(pctl * 365))]
        out[g[k][0]] = g[k][1] > thr
    return out


def h23_confluence(daily, flows, stable, pctl: float = 0.6, hmm_win: int = 90):
    hot = _stable_impulse(stable, pctl)
    hd = sorted(hot)
    out = []
    for sym, asset in (("BTC", "btc"), ("ETH", "eth")):
        bars, fl = daily.get(sym) or [], flows.get(asset) or []
        if len(bars) < 400 or len(fl) < 200 or not hd:
            continue
        z = _netflow_z(fl)
        zd = sorted(z)
        cl = [b[4] for b in bars]
        e50 = _ema_series(cl, 50)
        ent, first_ok = {}, None
        for i in range(max(200, hmm_win), len(bars)):
            zz = _latest_fresh(zd, z, _day(bars[i][0] - 2 * 86400))
            gg = _latest_fresh(hd, hot, _day(bars[i][0] - 86400))
            if zz is None or gg is None:
                continue
            first_ok = first_ok or bars[i][0]
            if zz > 0 or not gg or not (cl[i] > statistics.fmean(cl[i - 199:i + 1]) and e50[i] and cl[i] > e50[i] and cl[i] > cl[i - 5]):
                continue
            rows = [[b[1], b[2], b[3], b[4], 0.0] for b in bars[i - hmm_win:i + 1]]
            if sb.hmm_pelt_regime(rows + [rows[-1]])["hmm_state"] in ("LOW", "NORMAL"):
                ent[i] = 1
        if first_ok is None:
            continue
        cost = DAILY[sym][1]
        tr = _with_close(_hold_trades(bars, ent, 7, cost), bars)
        split = _split_ts([b for b in bars if b[0] >= first_ok])
        out.append(_cand5("H23", sym, f"HMM calm/normal x trend x netflow<=0 x stablecoin impulse>p60, long 7d — {sym}", tr, split,
                          cost, "yahoo_daily+coinmetrics_community+defillama_stablecoins",
                          obs_per_year=len(tr) / _span_years(first_ok, bars[-1][0]), end_ts=bars[-1][0],
                          extra={"benchmark": _benchmark(bars, 7, split, cost, tr), "eligible_from": _day(first_ok)}))
    return out


# ---------------- H24 liquidity-sweep wick rejection ----------------
def h24_wick(daily, wick: float = 2.2, band: float = 2.0, vmult: float = 1.2):
    out, skipped, a = [], {}, 2.0 / 21
    for sym, (_, cost) in DAILY.items():
        bars = daily.get(sym) or []
        if sym in NO_REAL_VOLUME:
            skipped[sym] = "spot FX has no real traded volume on Yahoo; not imputed"
            continue
        if len(bars) < 300:
            skipped[sym] = "history < 300 daily bars"
            continue
        cover = sum(1 for b in bars if len(b) > 5 and b[5] > 0) / len(bars)
        if cover < 0.9:
            skipped[sym] = f"volume present on {cover:.0%} of bars (< 90%)"
            continue
        m, var, ent = bars[0][4], 0.0, {}
        for i in range(1, len(bars)):
            _, o, h, l, c, v = bars[i][:6]
            if i >= 40 and var > 0:
                s, body = math.sqrt(var), max(abs(c - o), 1e-4 * c)
                vm = statistics.fmean(b[5] for b in bars[i - 20:i])
                if vm > 0 and v > vmult * vm:
                    if min(o, c) - l >= wick * body and l <= m - band * s:
                        ent[i] = 1
                    elif h - max(o, c) >= wick * body and h >= m + band * s:
                        ent[i] = -1
            d = c - m
            m += a * d
            var = (1 - a) * (var + a * d * d)
        tr = _with_close(_hold_trades(bars, ent, 3, cost), bars)
        split = _split_ts(bars)
        out.append(_cand5("H24", sym, f"Wick >= {wick:.2f}x body beyond EWMA20 ±2σ + volume > 1.2x, fade 3d — {sym}", tr, split, cost,
                          "yahoo_daily_ohlcv", obs_per_year=len(tr) / _span_years(bars[40][0], bars[-1][0]), end_ts=bars[-1][0],
                          extra={"benchmark": _benchmark(bars, 3, split, cost, tr)}))
    return out, skipped


# ---------------- business-day grid for portfolio hypotheses ----------------
def _grid(daily, syms, ref: str = "SPX", max_stale: int = 5):
    days = [_bar_day(b[0]) for b in daily.get(ref) or []]
    series = {}
    for s in syms:
        mp = {_bar_day(b[0]): b[4] for b in daily.get(s) or []}
        last, age, col = None, max_stale + 1, []
        for d in days:
            if d in mp:
                last, age = mp[d], 0
            else:
                age += 1
            col.append(last if age <= max_stale else None)
        series[s] = col
    start = next((t for t in range(len(days)) if all(series[s][t] for s in syms)), None)
    return days, series, start


# ---------------- H25 DXY/US10Y-gated rotation ----------------
def h25_rotation(daily, macro, lb: int = 63, hyst: float = 0.25, cash_override: float = 1.0, cost_bps: float = 15.0):
    assets = ("XAU", "SPX", "BTC")
    days, S, start = _grid({**daily, **macro}, assets + ("DXY", "US10Y"))
    if start is None or len(days) - start < lb + 300:
        return None
    held, per, ew, switches, cash_w = "CASH", [], [], 0, 0
    for t in range(start + lb + 1, len(days) - 5, 5):
        if any(S[s][t - lb] is None or S[s][t] is None or S[s][t + 5] is None for s in assets + ("DXY", "US10Y")):
            continue
        score = {}
        for s in assets:
            xs = S[s][t - lb:t + 1]
            if any(x is None for x in xs):
                break
            rr = [xs[k + 1] / xs[k] - 1 for k in range(lb)]
            score[s] = (xs[-1] / xs[0] - 1) / ((statistics.pstdev(rr) * math.sqrt(lb)) or 1e-12)
        if len(score) < len(assets):
            continue
        lead = max(score, key=score.get)
        headwind = S["DXY"][t] > S["DXY"][t - lb] and S["US10Y"][t] > S["US10Y"][t - lb]
        if headwind and score[lead] <= cash_override:
            tgt = "CASH"
        elif held in score and score[lead] <= score[held] + hyst:
            tgt = held
        else:
            tgt = lead
        r = (S[tgt][t + 5] / S[tgt][t] - 1) if tgt != "CASH" else 0.0
        if tgt != held:
            r -= cost_bps / 1e4
            switches += 1
        cash_w += tgt == "CASH"
        per.append({"ts_open": _ts(days[t]), "ts_close": _ts(days[t + 5]), "ret": r, "d": 1})
        ew.append({"ts_open": _ts(days[t]), "ret": statistics.fmean(S[s][t + 5] / S[s][t] - 1 for s in assets)})
        held = tgt
    if len(per) < 60:
        return None
    split = per[int(len(per) * 0.6)]["ts_open"]
    ew_oos = [x["ret"] for x in ew if x["ts_open"] >= split]
    c = _cand5("H25", "ROT3", "DXY/US10Y-gated weekly rotation XAU/SPX/BTC/cash (63d ret/vol, hysteresis 0.25)", per, split, cost_bps,
               "yahoo_daily GC=F ^GSPC BTC-USD DX-Y.NYB ^TNX", obs_per_year=52.0, end_ts=per[-1]["ts_close"], unit="week",
               extra={"switches": switches, "weeks_in_cash": cash_w, "weeks_total": len(per),
                      "equal_weight_oos_sharpe": round(sharpe(ew_oos), 4)})
    c["excess_vs_equal_weight_oos_sharpe"] = round(c["oos_sharpe"] - c["equal_weight_oos_sharpe"], 4)
    return c


# ---------------- H26 post-announcement drift after pre-event vol compression ----------------
def h26_event_drift(daily, cal, comp: float = 0.8, kick: float = 0.5, hold: int = 3):
    out = []
    for ev, syms in H26_PAIRS.items():
        evdays = sorted({e["at_utc"][:10] for e in cal.get("events") or [] if e.get("event") == ev})
        for sym in syms:
            bars = daily.get(sym) or []
            if len(bars) < 300:
                continue
            idx = {_bar_day(b[0]): i for i, b in enumerate(bars)}
            cl = [b[4] for b in bars]
            hits = [idx[d] for d in evdays if d in idx and idx[d] >= 22]
            if len(hits) < 30:
                continue
            ent = {}
            for i in hits:
                r = [cl[j] / cl[j - 1] - 1 for j in range(i - 20, i)]
                rv5, rv20, ri = statistics.pstdev(r[-5:]), statistics.pstdev(r), cl[i] / cl[i - 1] - 1
                if rv20 > 0 and rv5 < comp * rv20 and abs(ri) > kick * rv20:
                    ent[i] = 1 if ri > 0 else -1
            cost = DAILY[sym][1]
            tr = _with_close(_hold_trades(bars, ent, hold, cost), bars)
            split = bars[hits[int(len(hits) * 0.6)]][0]
            tag = f"{ev.split('_')[0]}-{sym}"
            out.append(_cand5("H26", tag, f"{ev} pre-event vol compression (<{comp:.2f}x) + kick > {kick}σ, follow 3d — {sym}",
                              tr, split, cost, "official_calendar+yahoo_daily",
                              obs_per_year=len(tr) / _span_years(bars[hits[0]][0], bars[-1][0]), end_ts=bars[-1][0],
                              extra={"events_in_sample": len(hits), "qualifying_events": len(ent),
                                     "benchmark": _benchmark(bars, hold, split, cost, tr)}))
    return out


# ---------------- H27 Black-Litterman bull/bear agents, Ledoit-Wolf covariance, Brier-weighted confidence ----------------
def ledoit_wolf(X):
    """Ledoit & Wolf (2004) shrinkage of the sample covariance toward a scaled identity. Returns (sigma, shrinkage)."""
    import numpy as np
    T, N = X.shape
    Xc = X - X.mean(0)
    S = Xc.T @ Xc / T
    mu = float(np.trace(S)) / N
    F = mu * np.eye(N)
    d2 = float(((S - F) ** 2).sum())
    if d2 <= 0:
        return S, 0.0
    x2 = (Xc ** 2).sum(1)
    b2bar = float((x2 ** 2).sum() - 2 * np.einsum("ti,ij,tj->", Xc, S, Xc) + T * (S ** 2).sum()) / T ** 2
    sh = min(b2bar, d2) / d2
    return sh * F + (1 - sh) * S, sh


def _brier_skill(preds: list[tuple[int, str, Any, Any]], agent: str, now_t: int, C) -> float | None:
    import numpy as np
    errs, ref = [], []
    for t_res, ag, p, t0 in preds:
        if ag != agent or t_res > now_t:
            continue
        o = (C[t_res] > C[t0]).astype(float)
        errs.append(((p - o) ** 2).mean())
        ref.append(((0.5 - o) ** 2).mean())
    if len(errs) < 3:
        return None
    return 1 - float(np.mean(errs)) / max(1e-12, float(np.mean(ref)))


def h27_black_litterman(daily, tau: float = 0.05, delta: float = 2.5, view_sr: float = 0.05, lb: int = 252, step: int = 21,
                        assets: tuple[str, ...] = BL_ASSETS):
    import numpy as np
    days, S, start = _grid(daily, assets, max_stale=10)
    if start is None or len(days) - start < lb + 20 * step:
        return None
    rows_c, last_row = [], None
    for t in range(start, len(days)):
        row = [S[a][t] if S[a][t] is not None else (last_row[k] if last_row else None) for k, a in enumerate(assets)]
        if None in row:
            return None
        rows_c.append(row)
        last_row = row
    C = np.array(rows_c, dtype=float)
    bad = [a for k, a in enumerate(assets) if (C[:, k] <= 0).any()]
    if bad:
        raise ValueError(f"non-positive price in {bad}: simple returns undefined")
    R = C[1:] / C[:-1] - 1
    N = len(assets)
    cost = np.array([DAILY[a][1] for a in assets]) / 1e4
    weq = np.ones(N) / N
    preds: list[tuple[int, str, Any, Any]] = []
    per, ew, w_prev, ew_prev = [], [], np.zeros(N), np.zeros(N)
    shrinks, tilt, bss_log, active = [], [], [], 0
    for t in range(lb, len(C) - step, step):
        sig, sh = ledoit_wolf(R[t - lb:t])
        shrinks.append(sh)
        pi = delta * sig @ weq
        sd = np.sqrt(np.diag(sig))
        mom, rev = np.sign(C[t] / C[t - lb] - 1), -np.sign(C[t] / C[t - 5] - 1)
        bss = {ag: _brier_skill(preds, ag, t, C) for ag in ("bull", "bear")}
        bss_log.append(bss)
        rows, q, om = [], [], []
        for ag, vec in (("bull", mom), ("bear", rev)):
            conf = min(0.99, max(0.0, bss[ag] or 0.0))
            if conf > 0:
                rows.append(np.eye(N)); q.append(vec * view_sr * sd); om.append((1 - conf) / conf * tau * sd ** 2)
        if rows:
            active += 1
            P, Q, Om_inv = np.vstack(rows), np.concatenate(q), np.diag(1 / np.concatenate(om))
            ts_inv = np.linalg.inv(tau * sig)
            mu = np.linalg.solve(ts_inv + P.T @ Om_inv @ P, ts_inv @ pi + P.T @ Om_inv @ Q)
        else:
            mu = pi
        w = np.linalg.solve(delta * sig, mu)
        w = w / (np.abs(w).sum() or 1.0)
        tilt.append(float(np.abs(w - weq).sum()))
        g = C[t + step] / C[t] - 1
        per.append({"ts_open": _ts(days[start + t]), "ts_close": _ts(days[start + t + step]), "d": 1,
                    "ret": float(w @ g - np.abs(w - w_prev) @ cost)})
        ew.append({"ts_open": _ts(days[start + t]), "ret": float(weq @ g - np.abs(weq - ew_prev) @ cost)})
        w_prev, ew_prev = w, weq
        preds.append((t + step, "bull", 0.5 + 0.1 * mom, t))
        preds.append((t + step, "bear", 0.5 + 0.1 * rev, t))
    split = per[int(len(per) * 0.6)]["ts_open"]
    ew_oos = [x["ret"] for x in ew if x["ts_open"] >= split]
    last = bss_log[-1] if bss_log else {}
    c = _cand5("H27", "BL8", "Black-Litterman bull(12m trend)/bear(5d reversal) agents, LW covariance, Brier-weighted confidence",
               per, split, float(statistics.fmean(DAILY[a][1] for a in assets)), "yahoo_daily " + ",".join(assets),
               obs_per_year=252.0 / step, end_ts=per[-1]["ts_close"], unit="month",
               extra={"assets": list(assets), "equal_weight_oos_sharpe": round(sharpe(ew_oos), 4), "rebalances": len(per),
                      "rebalances_with_active_views": active, "mean_lw_shrinkage": round(statistics.fmean(shrinks), 4),
                      "mean_abs_tilt_vs_equal_weight": round(statistics.fmean(tilt), 4),
                      "final_brier_skill": {k: (round(v, 4) if v is not None else None) for k, v in last.items()}})
    c["excess_vs_equal_weight_oos_sharpe"] = round(c["oos_sharpe"] - c["equal_weight_oos_sharpe"], 4)
    return c


BL_OIL_SUBSTITUTE = {"WTI": "BRENT"}
DEVIATIONS: dict[str, str] = {}


def h27_run(daily, **kw):
    """H27 on the pre-registered assets; if a price series is non-positive (WTI front month printed -37.63 USD on
    2020-04-20) the same-exposure substitute is used and the deviation is recorded, never silently."""
    try:
        return h27_black_litterman(daily, **kw)
    except ValueError as exc:
        assets = tuple(BL_OIL_SUBSTITUTE.get(a, a) for a in BL_ASSETS)
        DEVIATIONS["H27"] = f"{exc}; substituted {BL_OIL_SUBSTITUTE} (same oil exposure, strictly positive history)"
        return h27_black_litterman(daily, assets=assets, **kw)


# ---------------- H28 vol-targeted allocator over IS-surviving streams ----------------
def h28_voltarget(streams: list[dict[str, Any]], target: float = 0.12, embargo_d: int = 21, kelly_frac: float = 0.25,
                  dd_thr: float = 0.05):
    import numpy as np
    streams = [c for c in streams if c.get("_trades")]
    if not streams:
        return None
    t0 = min(t[0] for c in streams for t in c["_trades"])
    t1 = max(t[1] for c in streams for t in c["_trades"])
    D = [_day(t0 + k * 86400) for k in range(int((t1 - t0) // 86400) + 1)]
    di = {d: k for k, d in enumerate(D)}
    M = np.zeros((len(D), len(streams)))
    for j, c in enumerate(streams):
        for a, b, r in c["_trades"]:
            ks = [k for k in range(di[_day(a)] + 1, di.get(_day(b), di[_day(a)]) + 1)] or [di[_day(a)]]
            for k in ks:
                M[k, j] += r / len(ks)
    split = int(len(D) * 0.6)
    IS = M[:split]
    sel = [j for j in range(len(streams)) if (IS[:, j] != 0).sum() >= 10 and IS[:, j].std() > 0 and IS[:, j].mean() > 0]
    base = {"hypothesis_id": "H28", "split_utc": D[split], "embargo_days": embargo_d,
            "streams_considered": len(streams), "streams_selected_on_is": [streams[j]["strategy_id"] for j in sel],
            "adv_cap": "1% ADV non-binding: paper notional <= $10k vs >= $50M ADV for every instrument"}
    if not sel:
        return {"strategy_id": "b5-H28-VT12", "title": "Vol-targeted allocator — no IS survivors", "returns": [],
                "oos_trades": 0, "oos_sharpe": 0.0, "is_trades": 0, "is_sharpe": 0.0, "status": "NO_IS_SURVIVORS",
                "cost_bps": 5.0, "lookahead_leak_detected": False, "data_is_real": True, "observation_unit": "week",
                "obs_per_year": 52.18, "_trades": [], "_oos_by_day": {}, "_is_by_day": {}, **base}
    sd_is = IS[:, sel].std(0)
    w = (1 / sd_is) / (1 / sd_is).sum()
    p = M[:, sel] @ w
    mu_is, var_is = float(p[:split].mean()), float(p[:split].var())
    kelly_cap = min(1.0, kelly_frac * mu_is / var_is) if mu_is > 0 and var_is > 0 else 0.0
    var = float(p[:20].var()) or 1e-8
    eq, curve, out = 1.0, [1.0], np.zeros(len(D))
    for k in range(len(D)):
        scale = min(1.0, kelly_cap, target / max(1e-6, math.sqrt(var * 365)))
        peak = max(curve[-20:])
        if 1 - eq / peak > dd_thr:
            scale *= 0.5
        out[k] = scale * p[k]
        eq *= 1 + out[k]
        curve.append(eq)
        var = 0.94 * var + 0.06 * p[k] ** 2
    oos0 = split + embargo_d
    weeks = []
    for k in range(0, len(D) - 6, 7):
        weeks.append({"ts_open": _ts(D[k]), "ts_close": _ts(D[k + 6]), "d": 1, "ret": float(out[k:k + 7].sum())})
    c = _cand5("H28", "VT12", f"Vol-target {target:.0%} allocator over IS-surviving batch-5 streams, quarter-Kelly, DD halving",
               weeks, _ts(D[split]), 5.0, "batch5 stream returns", obs_per_year=52.18, end_ts=_ts(D[-1]), unit="week",
               embargo_s=embargo_d * 86400,
               extra={**base, "quarter_kelly_cap_is": round(kelly_cap, 4), "weights": {streams[j]["strategy_id"]: round(float(x), 4) for j, x in zip(sel, w)},
                      "oos_starts_utc": D[min(oos0, len(D) - 1)]})
    return c


# ---------------- batch-5 trial accounting, PBO, red-team evidence ----------------
def _load_prior_trials(root: Path) -> tuple[int, list[tuple[float, float]]]:
    """(trials ever run before batch 5, [(per-observation SR, annualized SR)] of those on file)."""
    out, n_prior = [], PRIOR_TRIALS
    try:
        for c in json.loads((root / OUT_REL).read_text(encoding="utf-8")).get("candidates") or []:
            opy = (c.get("is_trades", 0) + c.get("oos_trades", 0)) / 1.0
            out.append((c["oos_sharpe"], c["oos_sharpe"] * math.sqrt(max(1.0, opy))))
    except Exception:
        pass
    try:
        b4 = json.loads((root / B4_OUT_REL).read_text(encoding="utf-8"))
        n_prior = int(b4.get("n_trials_counted_in_dsr") or n_prior)
        gen = datetime.strptime(b4["generated_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
        for c in b4.get("candidates") or []:
            span = _span_years(_ts(c["split_utc"]), int(gen)) / 0.4
            opy = (c.get("is_trades", 0) + c.get("oos_trades", 0)) / span
            out.append((c["oos_sharpe"], c["oos_sharpe"] * math.sqrt(max(1.0, opy))))
    except Exception:
        pass
    return n_prior, out


def time_aligned_pbo(cands: list[dict[str, Any]], s: int = PBO_BLOCKS) -> dict[str, Any]:
    """CSCV on equal CALENDAR blocks shared by every included trial (index-based blocks compare different dates).
    Trials whose first trade starts after the 75th-percentile start are excluded and listed."""
    elig = [c for c in cands if len(c.get("_trades") or []) >= 8]
    if len(elig) < 2:
        return {"pbo": None, "included": [], "excluded_short_history": [], "blocks": s}
    starts = sorted(min(t[0] for t in c["_trades"]) for c in elig)
    lo = starts[min(len(starts) - 1, int(0.75 * len(starts)))]
    inc = [c for c in elig if min(t[0] for t in c["_trades"]) <= lo]
    inc_ids = {c["strategy_id"] for c in inc}
    hi = min(max(t[0] for t in c["_trades"]) for c in inc)
    perf = []
    for c in inc:
        b = [0.0] * s
        for a, _, r in c["_trades"]:
            if lo <= a <= hi:
                b[min(s - 1, int((a - lo) * s / max(1, hi - lo)))] += r
        perf.append(b)
    return {"pbo": pbo_cscv(perf, s=s), "included": [c["strategy_id"] for c in inc], "blocks": s,
            "window_utc": [_day(lo), _day(hi)],
            "excluded_short_history": [c["strategy_id"] for c in elig if c["strategy_id"] not in inc_ids]}


def _b5_evidence(cands, daily, macro, flows, stable, cal) -> None:
    pert: dict[str, list[float]] = {}
    for f in (0.85, 1.15):
        runs = h23_confluence(daily, flows, stable, pctl=min(0.95, 0.6 * f)) + h24_wick(daily, wick=2.2 * f)[0] \
            + h26_event_drift(daily, cal, comp=min(0.99, 0.8 * f)) \
            + [x for x in (h25_rotation(daily, macro, hyst=0.25 * f), h27_run(daily, tau=0.05 * f)) if x]
        base_streams = [c for c in cands if c["hypothesis_id"] != "H28"]
        h28 = h28_voltarget(base_streams, target=0.12 * f)
        for c in runs + ([h28] if h28 else []):
            pert.setdefault(c["strategy_id"], []).append(c["oos_sharpe"])
    for c in cands:
        if c["strategy_id"] in pert and c["oos_sharpe"] > 0:
            c["param_perturbation_sharpe_retention"] = round(min(pert[c["strategy_id"]]) / c["oos_sharpe"], 3)
        sym = c["strategy_id"].split("-")[-1]
        _regime_pnl(c, daily.get(sym) or daily.get("SPX") or [])


def run_batch5(root: Path) -> dict[str, Any]:
    from architecture.markets import macro_calendar as mc, onchain_flows as oc
    errors: dict[str, str] = {}
    daily, macro = {}, {}
    for sym, (y, _) in DAILY.items():
        try:
            daily[sym] = fetch_daily_v(y)
        except Exception as exc:
            errors[sym] = repr(exc)[:120]
    for sym, y in MACRO_DAILY.items():
        try:
            macro[sym] = fetch_daily_v(y)
        except Exception as exc:
            errors[sym] = repr(exc)[:120]
    flows = {a: oc.exchange_flows_history(a, "2019-01-01") for a in ("btc", "eth")}
    stable = oc.stablecoin_supply_history()
    cal = mc.build_calendar(root)
    impact = mc.measure_event_impact(cal, daily)
    ip = root / IMPACT_OUT_REL
    ip.parent.mkdir(parents=True, exist_ok=True)
    ip.write_text(json.dumps(impact, ensure_ascii=False, indent=1), encoding="utf-8")

    h24, h24_skipped = h24_wick(daily)
    cands = h23_confluence(daily, flows, stable) + h24 + h26_event_drift(daily, cal) \
        + [x for x in (h25_rotation(daily, macro), h27_run(daily)) if x]
    not_built = {hid: "returned no candidate (insufficient aligned history)" for hid, ok in
                 (("H25", any(c["hypothesis_id"] == "H25" for c in cands)), ("H27", any(c["hypothesis_id"] == "H27" for c in cands))) if not ok}
    h28 = h28_voltarget(cands)
    if h28:
        cands.append(h28)
    _b5_evidence(cands, daily, macro, flows, stable, cal)

    n_prior, prior = _load_prior_trials(root)
    n_trials = n_prior + len(cands)
    tr_obs = [c["oos_sharpe"] for c in cands] + [p[0] for p in prior]
    tr_ann = [c["oos_sharpe"] * math.sqrt(max(1.0, c["obs_per_year"])) for c in cands] + [p[1] for p in prior]
    big = [c for c in cands if c["oos_trades"] >= 10]
    tr_obs10 = [c["oos_sharpe"] for c in big] + [p[0] for p in prior]
    tr_ann10 = [c["oos_sharpe"] * math.sqrt(max(1.0, c["obs_per_year"])) for c in big] + [p[1] for p in prior]
    for c in cands:
        v1 = deflated_sharpe(c["returns"], n_trials, tr_obs)
        v2 = deflated_sharpe_annualized(c["returns"], c["obs_per_year"], n_trials, tr_ann)
        c["dsr_per_observation"], c["dsr_annualized"] = v1, v2
        c["deflated_sharpe"] = min(v1, v2) if v1 is not None and v2 is not None else None
        s1 = deflated_sharpe(c["returns"], n_trials, tr_obs10)
        s2 = deflated_sharpe_annualized(c["returns"], c["obs_per_year"], n_trials, tr_ann10)
        c["dsr_sensitivity_trials_n_ge_10"] = min(s1, s2) if s1 is not None and s2 is not None else None
    pbo = time_aligned_pbo(cands)
    for c in cands:
        ok = c["oos_trades"] >= 30 and (c["deflated_sharpe"] or 0) > 0.95 and pbo["pbo"] is not None and pbo["pbo"] < 0.5
        c["gate"] = "PASS_STATS" if ok else "FAIL"
        c["gate_detail"] = f"oos_n={c['oos_trades']} DSR=min({c['dsr_per_observation']},{c['dsr_annualized']}) PBO={pbo['pbo']}"
    clean = [{k: v for k, v in c.items() if not k.startswith("_")} for c in cands]
    snap = {"schema": "ahos.strategy_lab.batch5.v1", "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "paper_only": True, "pre_registered": "strategy_lab/hypotheses.py _B5 @ 2026-10-24 13:17 Tehran (before first run)",
            "n_trials_this_batch": len(cands), "n_trials_prior": n_prior, "n_trials_counted_in_dsr": n_trials,
            "dsr_method": "min(per-observation DSR, annualized-trial DSR); trial Sharpes of every earlier batch on file",
            "pbo_cscv": pbo["pbo"], "pbo_detail": pbo,
            "promotion_rule": "OOS obs>=30 AND DSR>0.95 (all trials counted) AND PBO<0.5 AND survives strategy_red_team",
            "not_run": {"H26": H26_NOT_RUN, "H24": h24_skipped, **not_built},
            "deviations_from_preregistration": dict(DEVIATIONS),
            "event_impact_matrix": str(IMPACT_OUT_REL).replace("\\", "/"),
            "errors": errors, "candidates": clean}
    p = root / B5_OUT_REL
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap
