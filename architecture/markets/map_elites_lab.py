"""MAP-Elites archive and the four Batch-6 composites (H29–H32).

Pre-registered in strategy_lab/hypotheses.py ``_B6`` at 2026-10-24 18:18 Tehran, before any run.
An out-of-sample trial is spent only after the in-sample screens (active share, pairwise |rho|).
A screened hypothesis is written down and is not counted in ``trials_counted_in_dsr``.
The walk-forward arithmetic stays in architecture.learning.walk_forward.
"""
from __future__ import annotations

import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from architecture.learning.walk_forward import (
    B5_OUT_REL, DAILY, _bar_day, _cand5, _grid, _regime_pnl, _ts,
    deflated_sharpe, deflated_sharpe_annualized, fetch_daily_v, ledoit_wolf,
    sharpe, time_aligned_pbo,
)
from architecture.markets.walk_forward import atr_normalized_return, safe_simple_return, wilder_atr

B6_OUT_REL = Path("reports") / "grok" / "M28" / "batch6_research.json"
GRID_REL = Path("reports") / "grok" / "M28" / "map_elites_grid.json"
HORIZONS = ("intraday", "swing_2_5d", "macro_weekly")
REGIMES = ("trend_breakout", "vol_compression_carry", "crisis_defensive")
RHO_MAX = 0.65
CELLS = {
    "H29": ("macro_weekly", "vol_compression_carry"),
    "H30": ("macro_weekly", "trend_breakout"),
    "H31": ("swing_2_5d", "trend_breakout"),
    "H32": ("macro_weekly", "crisis_defensive"),
}
ACTIVE_MIN = {"H29": 0.30, "H30": 0.25, "H31": 0.25, "H32": 0.25}
BL_ASSETS = ("BTC", "ETH", "XAU", "WTI", "SPX", "DAX", "N225", "EURUSD")
H31_SKIP = ("EURUSD", "USDJPY")
PRIOR_THROUGH_BATCH5 = 89


def pearson(xs: list[float], ys: list[float]) -> float | None:
    n = min(len(xs), len(ys))
    if n < 30:
        return None
    a, b = xs[:n], ys[:n]
    mx, my = statistics.fmean(a), statistics.fmean(b)
    vx = sum((x - mx) ** 2 for x in a)
    vy = sum((y - my) ** 2 for y in b)
    if vx <= 0 or vy <= 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(a, b)) / math.sqrt(vx * vy)


def active_share(weights: list[float]) -> float:
    """Cremers active share against equal weight, on gross-normalized weights (sum |w| = 1)."""
    gross = sum(abs(w) for w in weights)
    if gross <= 0:
        return 0.0
    n = len(weights)
    w = [x / gross for x in weights]
    return 0.5 * sum(abs(x - 1.0 / n) for x in w)


def screen_book(is_returns: list[float], baselines: dict[str, list[float]], siblings: dict[str, list[float]],
                share: float, min_share: float, rho_max: float = RHO_MAX) -> tuple[bool, str]:
    """In-sample only. Failure refuses the out-of-sample trial."""
    if share < min_share:
        return False, f"active_share {share:.3f} < {min_share}"
    if len(is_returns) < 30:
        return False, f"is_observations {len(is_returns)} < 30"
    for name, series in {**baselines, **siblings}.items():
        rho = pearson(is_returns, series)
        if rho is not None and abs(rho) >= rho_max:
            return False, f"|rho|={abs(rho):.3f} vs {name} >= {rho_max}"
    return True, "ADMITTED"


def _closes(daily: dict, assets: tuple[str, ...]) -> tuple[list[str], np.ndarray]:
    days, series, _ = _grid(daily, assets, ref=assets[0], max_stale=5)
    mat = np.array([[np.nan if series[a][t] is None else float(series[a][t]) for a in assets] for t in range(len(days))],
                   dtype=float)
    return days, mat


def _g(C: np.ndarray, t: int, step: int) -> np.ndarray:
    out = np.full(C.shape[1], np.nan)
    for i in range(C.shape[1]):
        r = _fwd(float(C[t, i]), float(C[t + step, i]))
        if r is not None:
            out[i] = r
    return out


def _fwd(p0: float, p1: float) -> float | None:
    if not (math.isfinite(p0) and math.isfinite(p1)):
        return None
    return safe_simple_return(p0, p1)


def _trade(days: list[str], t: int, step: int, ret: float, w: np.ndarray, assets: tuple[str, ...], ew: float) -> dict:
    return {"ts_open": _ts(days[t]), "ts_close": _ts(days[min(t + step, len(days) - 1)]), "ret": float(ret),
            "d": 1, "weights": {a: round(float(w[i]), 4) for i, a in enumerate(assets)}, "ew_ret": float(ew)}


def _renorm(w: np.ndarray, good: np.ndarray) -> np.ndarray | None:
    ww = w.copy()
    ww[~good] = 0.0
    gross = np.abs(ww).sum()
    if gross <= 0:
        return None
    return ww / gross


def h29_book(daily: dict, *, lb: int = 252, vol_lb: int = 63, step: int = 5, cost_bps: float = 15.0,
             until_ts: int | None = None) -> list[dict]:
    assets = tuple(DAILY)
    days, C = _closes(daily, assets)
    n, k = C.shape
    trades, w_prev = [], np.zeros(k)
    cost = cost_bps / 1e4
    for t in range(lb, n - step, step):
        if until_ts is not None and _ts(days[t]) >= until_ts:
            break
        score = []
        vol = np.full(k, np.nan)
        for i in range(k):
            mom = _fwd(C[t - lb, i], C[t, i])
            rets = [r for r in (_fwd(C[j - 1, i], C[j, i]) for j in range(t - vol_lb + 1, t + 1)) if r is not None]
            if mom is None or len(rets) < 20 or statistics.pstdev(rets) <= 0:
                continue
            vol[i] = statistics.pstdev(rets)
            score.append((i, mom / vol[i]))
        if len(score) < 6:
            continue
        score.sort(key=lambda x: x[1])
        third = max(1, len(score) // 3)
        raw = np.zeros(k)
        for i, _s in score[:third]:
            raw[i] = -1.0 / vol[i]
        for i, _s in score[-third:]:
            raw[i] = 1.0 / vol[i]
        g = _g(C, t, step)
        good = np.isfinite(g)
        w = _renorm(raw, good)
        if w is None:
            continue
        turn = 0.5 * float(np.abs(w - w_prev).sum())
        trades.append(_trade(days, t, step, float(np.nansum(w * g)) - turn * cost, w, assets, float(np.nanmean(g))))
        w_prev = w
    return trades


def h30_book(daily: dict, *, lb: int = 252, step: int = 21, tau: float = 0.05, delta: float = 2.5,
             until_ts: int | None = None) -> list[dict]:
    assets = BL_ASSETS
    days, C = _closes(daily, assets)
    n, k = C.shape
    cost = np.array([DAILY[a][1] for a in assets]) / 1e4
    trades, w_prev, past = [], np.zeros(k), []
    for t in range(lb, n - step, step):
        if until_ts is not None and _ts(days[t]) >= until_ts:
            break
        rows = []
        for j in range(t - lb + 1, t + 1):
            row = [_fwd(C[j - 1, i], C[j, i]) for i in range(k)]
            if None not in row:
                rows.append(row)
        if len(rows) < lb // 2:
            continue
        R = np.array(rows, dtype=float)
        sig, _sh = ledoit_wolf(R)
        weq = np.ones(k) / k
        mom = np.array([_fwd(C[t - lb, i], C[t, i]) or 0.0 for i in range(k)])
        sign = np.sign(mom)
        ic = _trailing_ic(past)
        conf = min(0.99, abs(ic)) if ic is not None else 0.0
        if conf >= 0.02:
            sd = np.sqrt(np.clip(np.diag(sig), 1e-12, None))
            pi = delta * sig @ weq
            om = tau * sd ** 2 / conf
            q = sign * 0.05 * sd
            ts_inv = np.linalg.inv(tau * sig)
            mu = np.linalg.solve(ts_inv + np.diag(1.0 / om), ts_inv @ pi + q / om)
            w = np.linalg.solve(delta * sig, mu)
            w = w / (np.abs(w).sum() or 1.0)
        else:
            w = weq.copy()
        g = _g(C, t, step)
        good = np.isfinite(g)
        ww = _renorm(w, good)
        if ww is None:
            continue
        ret = float(np.nansum(ww * g) - np.abs(ww - w_prev) @ cost)
        ew = float(np.nanmean(g))
        trades.append(_trade(days, t, step, ret, ww, assets, ew))
        past.append((sign, np.array([x if x is not None else 0.0 for x in g])))
        w_prev = ww
    return trades


def _trailing_ic(past: list[tuple[np.ndarray, np.ndarray]]) -> float | None:
    if len(past) < 8:
        return None
    xs, ys = [], []
    for sign, realized in past:
        xs.extend(float(s) for s in sign)
        ys.extend(float(r) for r in realized)
    return pearson(xs, ys)


def _causal_high_prob(closes: np.ndarray) -> list[float | None]:
    """Forward-only 3-state vol filter. Emission scales use trailing absolute returns, never the future.
    Full-sample PELT is deliberately not used: its penalty is fit on the whole path."""
    trans = ((0.90, 0.09, 0.01), (0.06, 0.88, 0.06), (0.02, 0.10, 0.88))
    probs = [1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0]
    hist: list[float] = []
    out: list[float | None] = [None]
    for i in range(1, len(closes)):
        r = _fwd(closes[i - 1], closes[i])
        if r is None:
            out.append(None)
            continue
        past = hist[-252:] or [1e-4]
        mean_abs = sum(past) / len(past) or 1e-4
        scales = (0.5 * mean_abs, mean_abs, 2.2 * mean_abs)
        pred = [sum(probs[a] * trans[a][b] for a in range(3)) for b in range(3)]
        lik = [math.exp(-0.5 * min(50.0, (r / scales[b]) ** 2)) / scales[b] for b in range(3)]
        post = [pred[b] * lik[b] for b in range(3)]
        s = sum(post) or 1.0
        probs = [p / s for p in post]
        hist.append(abs(r))
        out.append(pred[2])
    return out


def h31_book(daily: dict, *, wick: float = 2.2, comp: float = 0.8, hold: int = 3, until_ts: int | None = None) -> list[dict]:
    assets = tuple(a for a in DAILY if a not in H31_SKIP)
    days, C = _closes(daily, assets)
    ohlc = {a: {_bar_day(b[0]): b for b in daily.get(a) or []} for a in assets}
    high_p = [_causal_high_prob(C[:, i]) for i in range(len(assets))]
    trades, busy = [], -1
    for t in range(40, len(days) - hold):
        if t < busy or (until_ts is not None and _ts(days[t]) >= until_ts):
            continue
        fired = []
        for i, a in enumerate(assets):
            bar = ohlc[a].get(days[t])
            if bar is None or high_p[i][t] is None or high_p[i][t] >= 0.5:
                continue
            rets = [r for r in (_fwd(C[j - 1, i], C[j, i]) for j in range(t - 19, t + 1)) if r is not None]
            if len(rets) < 20:
                continue
            if statistics.pstdev(rets[-5:]) >= comp * statistics.pstdev(rets):
                continue
            o, h, l, c = bar[1], bar[2], bar[3], bar[4]
            body = abs(c - o) or 1e-12
            lower, upper = min(o, c) - l, h - max(o, c)
            if lower >= wick * body and lower > upper:
                fired.append((i, 1.0))
            elif upper >= wick * body and upper > lower:
                fired.append((i, -1.0))
        if not fired:
            continue
        w = np.zeros(len(assets))
        for i, d in fired:
            w[i] = d
        g = _g(C, t, hold)
        good = np.isfinite(g) & (w != 0)
        ww = _renorm(w, good)
        if ww is None:
            continue
        cost = statistics.fmean(DAILY[a][1] for a in assets) / 1e4
        ret = float(np.nansum(ww * g)) - 2 * cost
        ew = float(np.nanmean(g))
        trades.append(_trade(days, t, hold, ret, ww, assets, ew))
        busy = t + hold
    return trades


def h32_book(daily: dict, *, vol_lb: int = 20, med_lb: int = 252, mom_lb: int = 63, step: int = 5,
             cost_bps: float = 15.0, until_ts: int | None = None) -> list[dict]:
    assets = ("XAU", "DXY", "BTC", "ETH", "SPX")
    panel = {**daily}
    days, C = _closes(panel, assets)
    ix = {a: i for i, a in enumerate(assets)}
    trades, w_prev = [], np.zeros(len(assets))
    cost = cost_bps / 1e4
    spx = ix["SPX"]
    for t in range(med_lb + vol_lb, len(days) - step, step):
        if until_ts is not None and _ts(days[t]) >= until_ts:
            break
        vols = []
        for j in range(t - med_lb, t + 1):
            window = [r for r in (_fwd(C[u - 1, spx], C[u, spx]) for u in range(j - vol_lb + 1, j + 1)) if r is not None]
            if len(window) >= vol_lb // 2:
                vols.append(statistics.pstdev(window))
        if len(vols) < med_lb // 2:
            continue
        high = vols[-1] > statistics.median(vols[:-1])
        raw = np.zeros(len(assets))
        if high:
            raw[ix["XAU"]] = 0.5
            raw[ix["DXY"]] = 0.5
        else:
            risk = []
            for a in ("BTC", "ETH", "SPX"):
                mom = _fwd(C[t - mom_lb, ix[a]], C[t, ix[a]])
                if mom is not None and mom > 0:
                    risk.append(ix[a])
            if risk:
                for i in risk:
                    raw[i] = 1.0 / len(risk)
        g = _g(C, t, step)
        good = np.isfinite(g)
        w = _renorm(raw, good) if raw.sum() > 0 else None
        if w is None:
            trades.append(_trade(days, t, step, 0.0, np.zeros(len(assets)), assets, float(np.nanmean(g))))
            w_prev = np.zeros(len(assets))
            continue
        turn = 0.5 * float(np.abs(w - w_prev).sum())
        ret = float(np.nansum(w * g)) - turn * cost
        trades.append(_trade(days, t, step, ret, w, assets, float(np.nanmean(g))))
        w_prev = w
    return trades


def _mean_share(trades: list[dict]) -> float:
    shares = [active_share(list(t["weights"].values())) for t in trades if any(t["weights"].values())]
    return statistics.fmean(shares) if shares else 0.0


def _split_of(days: list[str]) -> int:
    return _ts(days[int(len(days) * 0.6)])


def _baselines(daily: dict, until_ts: int) -> dict[str, list[float]]:
    """Equal-weight and 12-month time-series momentum, in-sample only. Not trials."""
    assets = tuple(DAILY)
    days, C = _closes(daily, assets)
    ew, mom = [], []
    for t in range(252, len(days) - 5, 5):
        if _ts(days[t]) >= until_ts:
            break
        g = [_fwd(C[t, i], C[t + 5, i]) for i in range(C.shape[1])]
        good = [x for x in g if x is not None]
        if len(good) < 6:
            continue
        ew.append(statistics.fmean(good))
        signs = []
        for i, r in enumerate(g):
            m = _fwd(C[t - 252, i], C[t, i])
            if r is not None and m is not None and m != 0:
                signs.append((1.0 if m > 0 else -1.0) * r)
        if signs:
            mom.append(statistics.fmean(signs))
    return {"equal_weight": ew, "tsmom_12m": mom}


def _atr_sharpe(daily: dict, trades: list[dict], split_ts: int) -> float | None:
    cache: dict[str, tuple[dict[str, int], list]] = {}
    rets = []
    for t in trades:
        if t["ts_open"] < split_ts:
            continue
        acc = 0.0
        for sym, w in t["weights"].items():
            if abs(w) < 1e-12 or sym not in daily:
                continue
            if sym not in cache:
                bars = daily[sym]
                cache[sym] = ({_bar_day(b[0]): i for i, b in enumerate(bars)}, wilder_atr(bars))
            idx, atrs = cache[sym]
            bars = daily[sym]
            i0, i1 = idx.get(_bar_day(t["ts_open"])), idx.get(_bar_day(t["ts_close"]))
            if i0 is None or i1 is None:
                continue
            r = atr_normalized_return(bars[i0][4], bars[i1][4], atrs[i0])
            if r is not None:
                acc += w * r
        rets.append(acc)
    return round(sharpe(rets), 4) if len(rets) >= 5 else None


BUILDERS = {"H29": h29_book, "H30": h30_book, "H31": h31_book, "H32": h32_book}
TITLES = {
    "H29": "Cross-sectional momentum, inverse-vol, 15 bps turnover",
    "H30": "Black-Litterman momentum view, omega inverse to trailing IC",
    "H31": "Wick fade under vol compression, causal vol-state gate",
    "H32": "Gold/USD in high vol, crypto/equity momentum in low vol",
}


def _to_candidate(hid: str, trades: list[dict], split_ts: int, daily: dict) -> dict[str, Any]:
    end_ts = max(t["ts_close"] for t in trades)
    step = {"H29": 5, "H30": 21, "H31": 3, "H32": 5}[hid]
    c = _cand5(hid, "BOOK", TITLES[hid], trades, split_ts, 15.0, "yahoo_daily_price_safe",
               obs_per_year=252.0 / step, end_ts=end_ts, unit="rebalance")
    c["strategy_id"] = f"b6-{hid}-BOOK"
    oos_ew = [t["ew_ret"] for t in trades if t["ts_open"] >= split_ts]
    c["equal_weight_oos_sharpe"] = round(sharpe(oos_ew), 4)
    c["excess_vs_equal_weight_oos_sharpe"] = round(c["oos_sharpe"] - c["equal_weight_oos_sharpe"], 4)
    c["is_active_share"] = round(_mean_share([t for t in trades if t["ts_open"] < split_ts]), 4)
    c["atr_oos_sharpe"] = _atr_sharpe(daily, trades, split_ts)
    c["atr_sign_disagrees"] = bool(c["atr_oos_sharpe"] is not None and c["oos_sharpe"] != 0
                                   and (c["atr_oos_sharpe"] > 0) != (c["oos_sharpe"] > 0))
    c["map_elites_cell"] = {"horizon": CELLS[hid][0], "regime": CELLS[hid][1]}
    c["return_method"] = "percent, non-positive price days dropped per asset; ATR series is a receipt not a trial"
    _regime_pnl(c, daily.get("SPX") or [])
    return c


def evaluate_batch6(daily: dict) -> dict[str, Any]:
    """Screen on the in-sample date split, then spend an OOS trial only for admitted books."""
    ref_days, _ = _closes(daily, tuple(DAILY))
    split_ts = _split_of(ref_days)
    baselines = _baselines(daily, split_ts)
    admitted: list[dict[str, Any]] = []
    screened: list[dict[str, Any]] = []
    sibling_is: dict[str, list[float]] = {}
    for hid in ("H29", "H30", "H31", "H32"):
        probe = BUILDERS[hid](daily, until_ts=split_ts)
        is_rets = [t["ret"] for t in probe]
        share = _mean_share(probe)
        ok, reason = screen_book(is_rets, baselines, sibling_is, share, ACTIVE_MIN[hid])
        if not ok:
            screened.append({"hypothesis_id": hid, "strategy_id": f"b6-{hid}-BOOK", "counted_in_dsr": False,
                             "screen": reason, "is_observations": len(is_rets), "is_active_share": round(share, 4),
                             "cell": {"horizon": CELLS[hid][0], "regime": CELLS[hid][1]}})
            continue
        full = BUILDERS[hid](daily)
        cand = _to_candidate(hid, full, split_ts, daily)
        cand["screen"] = reason
        admitted.append(cand)
        sibling_is[hid] = is_rets
    return {"admitted": admitted, "screened": screened, "split_ts": split_ts,
            "nonpositive_days": _nonpositive_days(daily)}


def _nonpositive_days(daily: dict) -> dict[str, int]:
    out = {}
    for sym, bars in daily.items():
        n = sum(1 for b in bars if b[4] <= 0)
        if n:
            out[sym] = n
    return out


def _prior(root: Path) -> tuple[int, list[tuple[float, float]]]:
    n, rows = PRIOR_THROUGH_BATCH5, []
    try:
        b5 = json.loads((root / B5_OUT_REL).read_text(encoding="utf-8"))
        n = int(b5.get("n_trials_counted_in_dsr") or n)
        for c in b5.get("candidates") or []:
            opy = c.get("obs_per_year") or 1.0
            rows.append((c["oos_sharpe"], c["oos_sharpe"] * math.sqrt(max(1.0, opy))))
    except (OSError, ValueError, KeyError):
        pass
    return n, rows


def _score(cands: list[dict], root: Path) -> dict[str, Any]:
    n_prior, prior = _prior(root)
    n_trials = n_prior + len(cands)
    if cands:
        tr_obs = [c["oos_sharpe"] for c in cands] + [p[0] for p in prior]
        tr_ann = [c["oos_sharpe"] * math.sqrt(max(1.0, c["obs_per_year"])) for c in cands] + [p[1] for p in prior]
        for c in cands:
            v1 = deflated_sharpe(c["returns"], n_trials, tr_obs)
            v2 = deflated_sharpe_annualized(c["returns"], c["obs_per_year"], n_trials, tr_ann)
            c["dsr_per_observation"], c["dsr_annualized"] = v1, v2
            c["deflated_sharpe"] = min(v1, v2) if v1 is not None and v2 is not None else None
    pbo = time_aligned_pbo(cands) if len(cands) >= 2 else {"pbo": None, "included": [], "blocks": 16}
    for c in cands:
        ok = c["oos_trades"] >= 30 and (c["deflated_sharpe"] or 0) > 0.95 and pbo["pbo"] is not None and pbo["pbo"] < 0.5
        c["gate"] = "PASS_STATS" if ok else "FAIL"
        c["gate_detail"] = f"oos_n={c['oos_trades']} DSR={c.get('deflated_sharpe')} PBO={pbo['pbo']}"
        c["param_perturbation_sharpe_retention"] = _perturb_retention(c, root)
    return {"n_prior": n_prior, "n_trials": n_trials, "pbo": pbo}


def _measured_retention(hid: str, daily: dict, split_ts: int, base: float) -> float | None:
    """+/-15% on the pre-registered lookback. A diagnostic rerun, not an additional counted trial."""
    if base <= 0:
        return None
    if hid == "H29":
        alt = h29_book(daily, lb=int(252 * 1.15))
    elif hid == "H30":
        alt = h30_book(daily, lb=int(252 * 1.15))
    elif hid == "H31":
        alt = h31_book(daily, wick=2.2 * 1.15)
    else:
        alt = h32_book(daily, vol_lb=int(20 * 1.15))
    alt_s = sharpe([t["ret"] for t in alt if t["ts_open"] >= split_ts])
    return round(min(alt_s, base) / base, 3)


def _perturb_retention(cand: dict, root: Path) -> float | None:
    return cand.get("param_perturbation_sharpe_retention")


def map_elites_grid(admitted: list[dict], screened: list[dict]) -> dict[str, Any]:
    cells = {h: {r: None for r in REGIMES} for h in HORIZONS}
    for c in admitted:
        cell = c["map_elites_cell"]
        slot = cells[cell["horizon"]][cell["regime"]]
        quality = c.get("is_sharpe") or 0.0
        if slot is None or quality > slot["is_sharpe"]:
            cells[cell["horizon"]][cell["regime"]] = {
                "strategy_id": c["strategy_id"], "hypothesis_id": c["hypothesis_id"],
                "is_sharpe": quality, "oos_sharpe": c["oos_sharpe"], "gate": c["gate"],
                "quality_definition": "IS Sharpe (admission). OOS Sharpe is reported and is not the archive key.",
            }
    occupied = sum(1 for h in cells.values() for v in h.values() if v)
    return {"schema": "ahos.map_elites_grid.v1", "paper_only": True,
            "descriptors": {"horizon": list(HORIZONS), "regime": list(REGIMES)},
            "cells_occupied": occupied, "cells_total": len(HORIZONS) * len(REGIMES),
            "empty_cells_mean": "no admitted strategy, not a zero-quality strategy",
            "grid": cells, "screened": screened}


def run_batch6(root: Path, daily: dict | None = None) -> dict[str, Any]:
    root = Path(root)
    errors: dict[str, str] = {}
    if daily is None:
        daily = {}
        for sym, (yahoo, _c) in {**DAILY, "DXY": ("DX-Y.NYB", 2.0)}.items():
            try:
                daily[sym] = fetch_daily_v(yahoo)
            except Exception as exc:  # noqa: BLE001 - a missing series is recorded, the book skips it
                errors[sym] = repr(exc)[:160]
    cache = {sym: {_bar_day(b[0]): b[4] for b in bars if b[4] > 0}
             for sym, bars in daily.items() if sym in ("SPX", "XAU", "BTC", "WTI")}
    cp = root / "reports" / "grok" / "M28" / "daily_close_cache.json"
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_text(json.dumps({"schema": "ahos.daily_close_cache.v1", "paper_only": True, "closes": cache}), encoding="utf-8")
    ev = evaluate_batch6(daily)
    for c in ev["admitted"]:
        c["param_perturbation_sharpe_retention"] = _measured_retention(c["hypothesis_id"], daily, ev["split_ts"], c["oos_sharpe"])
    scored = _score(ev["admitted"], root)
    # Retention needs a second causal run. It is not counted. None leaves the red-team vector failing closed.
    clean = [{k: v for k, v in c.items() if not k.startswith("_")} for c in ev["admitted"]]
    for c in clean:
        c.pop("weights", None)
    snap = {"schema": "ahos.strategy_lab.batch6.v1",
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "paper_only": True,
            "pre_registered": "strategy_lab/hypotheses.py _B6 @ 2026-10-24 18:18 Tehran (before first run)",
            "return_method": "percent returns; a day with price <= 0 is dropped for that asset and weights are "
                             "renormalized. ATR-normalized dollar changes are reported as atr_oos_sharpe and are not a second trial.",
            "nonpositive_price_days": ev["nonpositive_days"],
            "screens": {"rho_max": RHO_MAX, "active_share_min": ACTIVE_MIN,
                        "rule": "screened hypotheses are not counted in n_trials_counted_in_dsr"},
            "n_trials_this_batch": len(clean), "n_trials_prior": scored["n_prior"],
            "n_trials_counted_in_dsr": scored["n_trials"],
            "pbo_cscv": scored["pbo"].get("pbo"), "pbo_detail": scored["pbo"],
            "screened": ev["screened"], "errors": errors, "candidates": clean,
            "promotion_rule": "OOS obs>=30 AND DSR>0.95 (89 prior + this batch's admitted trials) AND PBO<0.5 "
                              "AND excess over equal weight > 0 AND survives strategy_red_team"}
    out = root / B6_OUT_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    grid = map_elites_grid(clean, ev["screened"])
    grid["generated_at"] = snap["generated_at"]
    gp = root / GRID_REL
    gp.write_text(json.dumps(grid, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap
