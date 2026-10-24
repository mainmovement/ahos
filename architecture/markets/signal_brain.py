"""AHOS paper-trader signal brain (PAPER_ONLY), built from AHOS_TRADING_SKILLS_v2 + owner t607u list.

Every signal returns {name, score in [-1, 1], available, evidence, source, spec}. Nothing is invented:
an input that could not be fetched is ``available: False`` and contributes 0.
Implemented (real data):
  mtf_trend      §2  multi-timeframe confluence on CLOSED 5m / 1h / session candles (Yahoo chart)
  candles        t607u(e) wick/shadow, hammer/shooting-star, engulfing on closed 5m and 1h candles
  zscore_mr      t607u(f) z-score mean reversion vs 1h mean
  vol_regime     §1 (simplified, filtered-only) realized-vol regime -> size multiplier, not direction
  order_flow     §3 OKX top-20 book imbalance + spread gate (crypto only)
  large_trades   t607u(c) OKX large prints (>= $50k) buy-vs-sell notional (crypto only)
  funding_oi     t607u(b) OKX perp funding rate (crowding, contrarian) + open interest (evidence)
  stablecoin     t607u(c) USDT+USDC market-cap change between cycles (CoinGecko) -> crypto liquidity
  macro          t607u(d) DXY + US10Y intraday move (two-source via CNBC) -> gold/equity/crypto pressure
  news           §10 decayed keyword sentiment from free RSS, counts only if >= 2 sources; event-risk filter
Not yet implemented (labelled in SPEC_TRACE.md): HMM/PELT regimes, central-bank calendar, on-chain whale
wallets / exchange net-flows, EIA/OPEC event calendar, calibrated ensemble (§9), research-paper hypotheses.
"""
from __future__ import annotations

import json
import math
import re
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

UA = {"User-Agent": "Mozilla/5.0 (AHOS paper research)"}
NEWS_FEEDS = {
    "cointelegraph": "https://cointelegraph.com/rss", "decrypt": "https://decrypt.co/feed",
    "cryptoslate": "https://cryptoslate.com/feed/", "theblock": "https://www.theblock.co/rss.xml",
    "oilprice": "https://oilprice.com/rss/main", "cnbc_markets": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "investing": "https://www.investing.com/rss/news_25.rss", "bbc_business": "https://feeds.bbci.co.uk/news/business/rss.xml",
    "fed_press": "https://www.federalreserve.gov/feeds/press_all.xml", "boj": "https://www.boj.or.jp/en/rss/whatsnew.xml",
    "eia": "https://www.eia.gov/rss/todayinenergy.xml",
}
ASSET_TERMS = {
    "CRYPTO": r"bitcoin|btc|ether|eth\b|solana|crypto|stablecoin",
    "PB_TOKEN": r"uniswap|\buni\b|chainlink|\blink\b|aave|defi|dex|token|ethereum",
    "GOLD": r"\bgold\b|bullion|precious metal",
    "OIL": r"\boil\b|crude|brent|wti|opec|barrel",
    "US_EQUITIES": r"s&p|nasdaq|wall street|stocks|equities|fed\b|federal reserve",
    "EU_EQUITIES": r"\bdax\b|europe|ecb|euro zone|eurozone",
    "ASIA_EQUITIES": r"nikkei|japan|boj|hong kong|hang seng|china",
    "FOREX": r"dollar|euro\b|yen|forex|currency",
}
POS = r"\b(surge\w*|rall(y|ies|ied)|soar\w*|jump\w*|gain\w*|record high|bullish|beats?|rebound\w*|climb\w*|inflows?|approv\w*)\b"
NEG = r"\b(plunge\w*|crash\w*|slump\w*|falls?|fell|drops?|dropped|tumble\w*|bearish|miss(es|ed)?|sell-?offs?|outflows?|hack\w*|bans?|banned|war|sanction\w*|lawsuits?|recession)\b"
NEWS_HALF_LIFE_H = 6.0
NEWS_MAX_FEEDS = 40
_NEWS_CACHE: dict[str, Any] = {"at": 0.0, "items": []}


def _get(url: str, timeout: float = 8.0) -> bytes | None:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
            return r.read()
    except Exception:
        return None


def _json(url: str, timeout: float = 8.0) -> Any:
    b = _get(url, timeout)
    try:
        return json.loads(b.decode("utf-8")) if b else None
    except ValueError:
        return None


def _sig(name: str, score: float | None, evidence: dict[str, Any], source: str, spec: str) -> dict[str, Any]:
    ok = score is not None and math.isfinite(score)
    return {"name": name, "score": round(max(-1.0, min(1.0, score)), 4) if ok else 0.0, "available": ok,
            "evidence": evidence, "source": source, "spec": spec}


# ---------- candle helpers (closed candles only: the last bar may still be forming -> dropped) ----------
def closed(ohlcv: list[list[float]]) -> list[list[float]]:
    return ohlcv[:-1] if len(ohlcv) > 1 else []


def resample(ohlcv: list[list[float]], n: int) -> list[list[float]]:
    out = []
    full = len(ohlcv) - len(ohlcv) % n
    for i in range(len(ohlcv) - full, len(ohlcv), n):
        ch = ohlcv[i:i + n]
        if len(ch) == n:
            out.append([ch[0][0], max(c[1] for c in ch), min(c[2] for c in ch), ch[-1][3], sum(c[4] for c in ch)])
    return out


def _ema(xs: list[float], n: int) -> float | None:
    if len(xs) < n:
        return None
    k = 2.0 / (n + 1)
    e = sum(xs[:n]) / n
    for x in xs[n:]:
        e = x * k + e * (1 - k)
    return e


def mtf_trend(ohlcv: list[list[float]]) -> dict[str, Any]:
    c5 = closed(ohlcv)
    h1 = resample(c5, 12)
    cl5 = [c[3] for c in c5]
    cl1 = [c[3] for c in h1]
    tfs = {}
    if len(cl5) >= 26:
        f, s = _ema(cl5, 9), _ema(cl5, 26)
        tfs["5m"] = (f - s) / s
    if len(cl1) >= 10:
        f, s = _ema(cl1, 3), _ema(cl1, 10)
        tfs["1h"] = (f - s) / s
    if len(cl5) >= 60:
        tfs["session"] = (cl5[-1] - cl5[0]) / cl5[0]
    if len(tfs) < 2:
        return _sig("mtf_trend", None, {"bars_5m": len(cl5)}, "yahoo_chart_5m", "§2")
    w = {"5m": 0.3, "1h": 0.45, "session": 0.25}
    score = sum(w[k] * (1 if v > 0 else -1 if v < 0 else 0) for k, v in tfs.items()) / sum(w[k] for k in tfs)
    higher = tfs.get("1h", tfs.get("session"))
    return _sig("mtf_trend", score, {"tf_gaps": {k: round(v, 5) for k, v in tfs.items()},
                                     "higher_tf_sign": 1 if higher > 0 else -1}, "yahoo_chart_5m", "§2")


def candle_patterns(ohlcv: list[list[float]]) -> dict[str, Any]:
    c5 = closed(ohlcv)
    h1 = resample(c5, 12)
    found, score = [], 0.0
    for tf, bars, w in (("5m", c5, 0.4), ("1h", h1, 0.6)):
        if len(bars) < 2:
            continue
        o, h, l, c, _ = bars[-1]
        po, _, _, pc, _ = bars[-2]
        rng = h - l
        if rng <= 0:
            continue
        body = abs(c - o)
        upper = h - max(o, c)
        lower = min(o, c) - l
        if lower >= 2 * body and upper <= 0.3 * rng:
            found.append(f"{tf}:hammer(lower_wick={lower / rng:.2f})"); score += w
        elif upper >= 2 * body and lower <= 0.3 * rng:
            found.append(f"{tf}:shooting_star(upper_wick={upper / rng:.2f})"); score -= w
        if c > o and pc < po and c >= po and o <= pc:
            found.append(f"{tf}:bullish_engulfing"); score += w
        elif c < o and pc > po and c <= po and o >= pc:
            found.append(f"{tf}:bearish_engulfing"); score -= w
    if not c5:
        return _sig("candles", None, {}, "yahoo_chart_5m", "t607u(e)")
    return _sig("candles", score, {"patterns": found or ["none"]}, "yahoo_chart_5m", "t607u(e)")


def zscore_mr(ohlcv: list[list[float]]) -> dict[str, Any]:
    cl = [c[3] for c in closed(ohlcv)][-48:]
    if len(cl) < 24:
        return _sig("zscore_mr", None, {}, "yahoo_chart_5m", "t607u(f)")
    m = sum(cl) / len(cl)
    sd = math.sqrt(sum((x - m) ** 2 for x in cl) / (len(cl) - 1)) or 1e-12
    z = (cl[-1] - m) / sd
    score = -(z / 3.0) if abs(z) >= 1.5 else 0.0      # contrarian only at stretched levels
    return _sig("zscore_mr", score, {"z": round(z, 3), "window_bars": len(cl)}, "yahoo_chart_5m", "t607u(f)")


def realized_vol(ohlcv: list[list[float]], n: int) -> float | None:
    cl = [c[3] for c in closed(ohlcv)][-(n + 1):]
    if len(cl) < n + 1:
        return None
    r = [math.log(cl[i + 1] / cl[i]) for i in range(len(cl) - 1) if cl[i] > 0 and cl[i + 1] > 0]
    if len(r) < 2:
        return None
    m = sum(r) / len(r)
    return math.sqrt(sum((x - m) ** 2 for x in r) / (len(r) - 1))


def garch11_vol(ohlcv: list[list[float]], target_vol_annual: float = 0.12) -> dict[str, Any]:
    """TS-5: EWMA (lambda=0.94) + GARCH(1,1) conditional volatility estimator & portfolio target-vol scaler."""
    cl = [c[3] for c in closed(ohlcv)]
    if len(cl) < 15:
        return {"ewma_vol": None, "garch11_vol": None, "annual_vol": None, "target_vol_mult": 1.0}
    rets = [math.log(cl[i + 1] / cl[i]) for i in range(len(cl) - 1) if cl[i] > 0 and cl[i + 1] > 0]
    if len(rets) < 10:
        return {"ewma_vol": None, "garch11_vol": None, "annual_vol": None, "target_vol_mult": 1.0}
    var0 = sum(r * r for r in rets[:10]) / 10.0 or 1e-8
    ewma_v = var0
    garch_v = var0
    omega = var0 * 0.02
    alpha, beta = 0.08, 0.90
    for r in rets:
        ewma_v = 0.94 * ewma_v + 0.06 * (r * r)
        garch_v = omega + alpha * (r * r) + beta * garch_v
    ewma_s = math.sqrt(max(1e-12, ewma_v))
    garch_s = math.sqrt(max(1e-12, garch_v))
    # 5m bars -> 288 bars/day * 252 trading days
    ann_vol = garch_s * math.sqrt(288.0 * 252.0)
    tv_mult = max(0.35, min(1.5, target_vol_annual / max(1e-4, ann_vol)))
    return {
        "ewma_vol": round(ewma_s, 6),
        "garch11_vol": round(garch_s, 6),
        "annual_vol": round(ann_vol, 4),
        "target_vol_mult": round(tv_mult, 4),
    }


def range_vol(ohlcv: list[list[float]], bar_interval: str = "5m") -> dict[str, Any]:
    """Parkinson and Garman-Klass on closed bars. Bar layout is open, high, low, close, volume.

    A bar with no positive open is skipped for Garman-Klass. Fewer than five usable bars
    returns None rather than a number from a shorter sample.
    """
    bars = closed(ohlcv)
    parks: list[float] = []
    gks: list[float] = []
    ln2 = math.log(2.0)
    for b in bars:
        if len(b) < 4:
            continue
        o, h, l, c = (float(b[0]), float(b[1]), float(b[2]), float(b[3]))
        if h <= 0 or l <= 0 or h < l or o <= 0 or c <= 0:
            continue
        if h + 1e-12 < max(o, c) or l - 1e-12 > min(o, c):
            continue
        hl = math.log(h / l)
        parks.append((hl * hl) / (4.0 * ln2))
        co = math.log(c / o)
        gks.append(0.5 * hl * hl - (2.0 * ln2 - 1.0) * co * co)
    def _sigma(xs: list[float]) -> float | None:
        if len(xs) < 5:
            return None
        var = sum(xs) / len(xs)
        if var <= 0:
            return None
        return math.sqrt(var)
    per_year = {"5m": 288.0 * 252.0, "1h": 6.5 * 252.0, "1d": 252.0}.get(bar_interval)
    def _ann(sig: float | None) -> float | None:
        if sig is None or per_year is None:
            return None
        return round(sig * math.sqrt(per_year), 6)
    p_sig, g_sig = _sigma(parks), _sigma(gks)
    return {
        "parkinson_vol": None if p_sig is None else round(p_sig, 8),
        "parkinson_annual": _ann(p_sig),
        "garman_klass_vol": None if g_sig is None else round(g_sig, 8),
        "garman_klass_annual": _ann(g_sig),
        "bars_used": len(parks),
        "bar_interval": bar_interval,
        "garman_klass_status": "OK" if g_sig is not None else "UNAVAILABLE",
    }


def book_depth_features(bids: list, asks: list) -> dict[str, Any]:
    """Top-5 and top-20 notional imbalance, plus the log-depth slope of the bid side."""
    def notional(levels, n: int) -> tuple[float, int]:
        total, used = 0.0, 0
        for row in list(levels)[:n]:
            if not isinstance(row, (list, tuple)) or len(row) < 2:
                continue
            px, sz = float(row[0]), float(row[1])
            if px > 0 and sz > 0:
                total += px * sz
                used += 1
        return total, used

    def imb(b: float, a: float) -> float | None:
        if b + a <= 0:
            return None
        return (b - a) / (b + a)

    b5, _ = notional(bids, 5)
    a5, _ = notional(asks, 5)
    b20, nb = notional(bids, 20)
    a20, na = notional(asks, 20)
    notionals = []
    for row in list(bids)[:20]:
        if isinstance(row, (list, tuple)) and len(row) >= 2 and float(row[0]) > 0 and float(row[1]) > 0:
            notionals.append(float(row[0]) * float(row[1]))
    slope = None
    if len(notionals) >= 5:
        xs = list(range(len(notionals)))
        ys = [math.log(v) for v in notionals]
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        varx = sum((x - mx) ** 2 for x in xs)
        if varx > 0:
            slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / varx
    i5, i20 = imb(b5, a5), imb(b20, a20)
    disagree = bool(i5 is not None and i20 is not None and i5 * i20 < 0)
    return {
        "imbalance_top5": None if i5 is None else round(i5, 4),
        "imbalance_top20": None if i20 is None else round(i20, 4),
        "bid_slope_log": None if slope is None else round(slope, 4),
        "depth_disagreement": disagree,
        "levels_bid": nb,
        "levels_ask": na,
    }


def funding_zscore(rate: float, history: list[float]) -> float | None:
    """Z-score of one funding print against earlier prints. Fewer than eight prints is None."""
    prior = [float(x) for x in history if isinstance(x, (int, float))]
    if len(prior) < 8:
        return None
    mean = sum(prior) / len(prior)
    var = sum((x - mean) ** 2 for x in prior) / (len(prior) - 1)
    if var <= 0:
        return None
    return (float(rate) - mean) / math.sqrt(var)


def hmm_pelt_regime(ohlcv: list[list[float]]) -> dict[str, Any]:
    """TS-1 & M24: Forward-only filtered 3-state Gaussian HMM + PELT change-point detection (zero look-ahead)."""
    cl = [c[3] for c in closed(ohlcv)]
    if len(cl) < 25:
        return {"hmm_state": "UNKNOWN", "hmm_probs": {"LOW": 0.33, "NORMAL": 0.34, "HIGH": 0.33}, "pelt_changepoints": []}
    rets = [math.log(cl[i + 1] / cl[i]) for i in range(len(cl) - 1) if cl[i] > 0 and cl[i + 1] > 0]
    abs_r = [abs(r) for r in rets]
    mean_abs = sum(abs_r) / len(abs_r) or 1e-4
    # 3 states: 0=LOW (0.5x mean_abs), 1=NORMAL (1.0x mean_abs), 2=HIGH (2.2x mean_abs)
    scales = (max(1e-6, 0.5 * mean_abs), max(1e-6, 1.0 * mean_abs), max(1e-6, 2.2 * mean_abs))
    trans = (
        (0.90, 0.09, 0.01),
        (0.06, 0.88, 0.06),
        (0.02, 0.10, 0.88),
    )
    probs = [1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0]
    for r in rets:
        pred = [sum(probs[i] * trans[i][j] for i in range(3)) for j in range(3)]
        lik = [math.exp(-0.5 * min(50.0, (r / scales[j]) ** 2)) / scales[j] for j in range(3)]
        post = [pred[j] * lik[j] for j in range(3)]
        s = sum(post) or 1.0
        probs = [p / s for p in post]

    # PELT L2 structural break detection on rolling local volatility (penalty = beta_pen)
    win = 8
    vols = [sum(abs_r[max(0, i - win):i + 1]) / max(1, min(win, i + 1)) for i in range(len(abs_r))]
    n = len(vols)
    pen = 2.5 * (sum((v - mean_abs) ** 2 for v in vols) / max(1, n)) + 1e-10
    prefix = [0.0] * (n + 1)
    prefix2 = [0.0] * (n + 1)
    for i, v in enumerate(vols, 1):
        prefix[i] = prefix[i - 1] + v
        prefix2[i] = prefix2[i - 1] + v * v

    def seg_cost(a: int, b: int) -> float:
        m = b - a
        if m <= 1:
            return 0.0
        s1 = prefix[b] - prefix[a]
        s2 = prefix2[b] - prefix2[a]
        return max(0.0, s2 - (s1 * s1) / m)

    f_cost = [0.0] * (n + 1)
    f_cost[0] = -pen
    cp_prev = [0] * (n + 1)
    candidates = [0]
    for t_idx in range(win, n + 1):
        best_c = float("inf")
        best_tau = 0
        for tau in candidates:
            if t_idx - tau < win // 2:
                continue
            c = f_cost[tau] + seg_cost(tau, t_idx) + pen
            if c < best_c:
                best_c = c
                best_tau = tau
        f_cost[t_idx] = best_c
        cp_prev[t_idx] = best_tau
        candidates = [tau for tau in candidates if f_cost[tau] + seg_cost(tau, t_idx) <= best_c + pen]
        candidates.append(t_idx)

    cps: list[int] = []
    cur = cp_prev[n]
    while cur > 0:
        cps.append(cur)
        cur = cp_prev[cur]
    cps.reverse()
    labels = ("LOW", "NORMAL", "HIGH")
    top_idx = max(range(3), key=lambda k: probs[k])
    return {
        "hmm_state": labels[top_idx],
        "hmm_probs": {labels[k]: round(probs[k], 4) for k in range(3)},
        "pelt_changepoints": cps[-5:],
        "bars_since_changepoint": (n - cps[-1]) if cps else n,
    }


def adv_cap_check(
    notional_usd: float,
    quote: dict[str, Any] | None,
    ohlcv: list[list[float]],
    *,
    max_adv_frac: float = 0.01,
) -> dict[str, Any]:
    """TS-3: Enforce order notional <= 1% of Average Daily Dollar Volume (ADV) for stocks, FX, commodities, crypto."""
    q = quote or {}
    px = float(q.get("price") or 0.0)
    vol_24h = q.get("vol_24h")
    adv_usd = float(vol_24h) if isinstance(vol_24h, (int, float)) and vol_24h > 0 else 0.0
    adv_source = "vendor_24h_volume" if adv_usd > 0 else None
    if adv_usd <= 0 and ohlcv and px > 0:
        vols = [float(c[4]) for c in closed(ohlcv) if len(c) > 4 and float(c[4]) > 0]
        if vols:
            adv_usd = (sum(vols) / len(vols)) * 288.0 * px
            adv_source = "5m_bar_volume_x288"
    # Liquid index/FX benchmark floor when feed omits tick volume
    if adv_usd <= 0:
        adv_usd = 50_000_000.0
        adv_source = "ASSUMED_FLOOR_50M_NO_VOLUME_IN_FEED"
    cap_usd = max_adv_frac * adv_usd
    allowed = notional_usd <= cap_usd
    return {
        "allowed": allowed,
        "notional_usd": round(notional_usd, 4),
        "adv_usd": round(adv_usd, 2),
        "adv_source": adv_source,
        "cap_1pct_usd": round(cap_usd, 2),
        "participation_rate": round(notional_usd / max(1.0, adv_usd), 8),
    }


def vol_regime(ohlcv: list[list[float]]) -> dict[str, Any]:
    short, long_ = realized_vol(ohlcv, 12), realized_vol(ohlcv, 96)
    garch = garch11_vol(ohlcv)
    ranges = range_vol(ohlcv)
    hmm = hmm_pelt_regime(ohlcv)
    if not short or not long_:
        return {
            "regime": hmm["hmm_state"] if hmm["hmm_state"] != "UNKNOWN" else "UNKNOWN",
            "size_mult": 0.5,
            "short_vol": short,
            "long_vol": long_,
            **garch,
            **ranges,
            **hmm,
            "spec": "§1(filtered_HMM+PELT+GARCH11+PARKINSON+GARMAN_KLASS)",
        }
    ratio = short / long_
    ratio_reg = "HIGH" if ratio > 1.6 else "LOW" if ratio < 0.6 else "NORMAL"
    # Combine forward-filtered HMM state with realized-vol ratio (conservative: HIGH wins)
    regime = "HIGH" if ("HIGH" in (ratio_reg, hmm["hmm_state"])) else ("LOW" if ratio_reg == "LOW" and hmm["hmm_state"] == "LOW" else "NORMAL")
    base_mult = {"HIGH": 0.5, "NORMAL": 1.0, "LOW": 0.8}[regime]
    return {
        "regime": regime,
        "ratio": round(ratio, 3),
        "size_mult": base_mult,
        "short_vol": round(short, 6),
        "long_vol": round(long_, 6),
        **garch,
        **ranges,
        **hmm,
        "spec": "§1(filtered_HMM+PELT+GARCH11+PARKINSON+GARMAN_KLASS)",
    }


# ---------- crypto microstructure (OKX public, free) ----------
OKX = {"BTC": "BTC", "ETH": "ETH", "SOL": "SOL"}


def order_flow(sym: str) -> dict[str, Any]:
    d = _json(f"https://www.okx.com/api/v5/market/books?instId={sym}-USDT&sz=20")
    try:
        book = d["data"][0]
        bids, asks = book["bids"], book["asks"]
        bb, ba = float(bids[0][0]), float(asks[0][0])
    except Exception:
        return _sig("order_flow", None, {}, "okx_books", "§3")
    depth = book_depth_features(bids, asks)
    imb = depth["imbalance_top20"]
    if imb is None or bb <= 0 or ba <= 0:
        return _sig("order_flow", None, depth, "okx_books", "§3")
    spread = (ba - bb) / ((ba + bb) / 2)
    return _sig("order_flow", imb, {**depth, "imbalance": round(imb, 4), "spread": round(spread, 6),
                                    "spread_gate_ok": spread < 0.001}, "okx_books", "§3")


def large_trades(sym: str, min_usd: float = 50_000) -> dict[str, Any]:
    d = _json(f"https://www.okx.com/api/v5/market/trades?instId={sym}-USDT-SWAP&limit=500")
    try:
        rows = d["data"]
    except Exception:
        return _sig("large_trades", None, {}, "okx_trades", "t607u(c)")
    ct = {"BTC": 0.01, "ETH": 0.1, "SOL": 1.0}[sym]          # OKX swap contract size in coin
    buy = sell = 0.0
    n = 0
    for t in rows:
        usd = float(t["px"]) * float(t["sz"]) * ct
        if usd >= min_usd:
            n += 1
            if t["side"] == "buy":
                buy += usd
            else:
                sell += usd
    if buy + sell == 0:
        return _sig("large_trades", 0.0, {"large_prints": 0, "window_trades": len(rows)}, "okx_trades", "t607u(c)")
    return _sig("large_trades", (buy - sell) / (buy + sell), {"large_prints": n, "buy_usd": round(buy), "sell_usd": round(sell),
                                                              "window_trades": len(rows)}, "okx_trades", "t607u(c)")


def funding_oi(sym: str, history: list[float] | None = None) -> dict[str, Any]:
    f = _json(f"https://www.okx.com/api/v5/public/funding-rate?instId={sym}-USDT-SWAP")
    oi = _json(f"https://www.okx.com/api/v5/public/open-interest?instType=SWAP&instId={sym}-USDT-SWAP")
    try:
        rate = float(f["data"][0]["fundingRate"])
    except Exception:
        return _sig("funding_oi", None, {}, "okx_public", "t607u(b)")
    oi_usd = None
    try:
        oi_usd = float(oi["data"][0]["oiUsd"])
    except Exception:
        pass
    z = funding_zscore(rate, history or [])
    if history is not None:
        history.append(rate)
        del history[:-30]
    # neutral ~0.01%/8h; strongly positive = crowded longs -> mild contrarian
    score = -max(-1.0, min(1.0, (rate - 0.0001) / 0.0004))
    return _sig("funding_oi", score * 0.5, {
        "funding_rate_8h": rate, "open_interest_usd": oi_usd,
        "funding_z": None if z is None else round(z, 4),
        "funding_z_n": len(history or []),
    }, "okx_public", "t607u(b)")


def stablecoin_flow(state: dict[str, Any]) -> dict[str, Any]:
    d = _json("https://api.coingecko.com/api/v3/simple/price?ids=tether,usd-coin&vs_currencies=usd&include_market_cap=true")
    try:
        cap = float(d["tether"]["usd_market_cap"]) + float(d["usd-coin"]["usd_market_cap"])
    except Exception:
        return _sig("stablecoin", None, {}, "coingecko_simple", "t607u(c)")
    prev = state.get("stable_cap")
    prev_ts = state.get("stable_cap_ts")
    state["stable_cap"], state["stable_cap_ts"] = cap, time.time()
    if not prev or not prev_ts or time.time() - prev_ts > 6 * 3600:
        return _sig("stablecoin", None, {"usdt_usdc_cap_usd": round(cap), "note": "first observation; needs a previous cycle"},
                    "coingecko_simple", "t607u(c)")
    ch = (cap - prev) / prev
    return _sig("stablecoin", ch / 0.001, {"usdt_usdc_cap_usd": round(cap), "change_since_last": round(ch, 6),
                                           "minutes": round((time.time() - prev_ts) / 60, 1)}, "coingecko_simple", "t607u(c)")


_ONCHAIN_CACHE: dict[str, Any] = {}


def exchange_netflow(sym: str, ttl_s: float = 6 * 3600) -> dict[str, Any]:
    """t607u(c) whales/banks: Coin Metrics daily exchange netflow z (90d). Net INFLOW to exchanges = sell pressure.
    SHADOW signal (weight 0) until a walk-forward test promotes it."""
    from architecture.markets import onchain_flows as oc
    asset = {"BTC": "btc", "ETH": "eth"}.get(sym)
    if not asset:
        return _sig("exchange_netflow", None, {"note": "coinmetrics community covers btc/eth only"}, "coinmetrics_community", "t607u(c)")
    c = _ONCHAIN_CACHE.get(asset)
    if not c or time.time() - c[0] > ttl_s:
        h = oc.exchange_flows_history(asset, (datetime.now(timezone.utc) - timedelta(days=200)).strftime("%Y-%m-%d"))
        c = _ONCHAIN_CACHE[asset] = (time.time(), h)
    z, last = oc.netflow_z(c[1], time.time())
    if z is None:
        return _sig("exchange_netflow", None, {"history_days": len(c[1])}, "coinmetrics_community", "t607u(c)")
    return _sig("exchange_netflow", -z / 3.0, {"netflow_z90": round(z, 3), "day": last["date"],
                                              "netflow_native": round(last["netflow"], 2), "lag_days": oc.LAG_DAYS},
                "coinmetrics_community", "t607u(c)")


def stablecoin_impulse(sym: str, ttl_s: float = 6 * 3600) -> dict[str, Any]:
    """H15 form (DefiLlama total supply): 7d growth percentile vs trailing year. >p80 -> +1 (long bias).
    Best batch-4 OOS result (beat unconditional long) but DSR 0.20 < 0.95 -> SHADOW (weight 0)."""
    from architecture.markets import onchain_flows as oc
    if sym not in ("BTC", "ETH", "SOL"):
        return _sig("stablecoin_impulse", None, {}, "defillama_stablecoins", "H15")
    c = _ONCHAIN_CACHE.get("stable")
    if not c or time.time() - c[0] > ttl_s:
        c = _ONCHAIN_CACHE["stable"] = (time.time(), oc.stablecoin_supply_history())
    h = [x for x in c[1] if x["usable_from_ts"] <= time.time()]
    if len(h) < 380:
        return _sig("stablecoin_impulse", None, {"days": len(h)}, "defillama_stablecoins", "H15")
    g = [h[k]["usd"] / h[k - 7]["usd"] - 1 for k in range(len(h) - 366, len(h)) if h[k - 7]["usd"] > 0]
    pct = sum(1 for x in g[:-1] if x < g[-1]) / max(1, len(g) - 1)
    return _sig("stablecoin_impulse", 1.0 if pct > 0.8 else 0.0, {"growth_7d": round(g[-1], 5), "percentile_1y": round(pct, 3)},
                "defillama_stablecoins", "H15")


def whale_mempool(sym: str, ttl_s: float = 600) -> dict[str, Any]:
    """BTC whale transfers (>=100 BTC) in the unconfirmed mempool sample. Direction unknown -> score 0, evidence only."""
    from architecture.markets import onchain_flows as oc
    if sym != "BTC":
        return _sig("whale_mempool", None, {}, "blockchain.info", "t607u(c)")
    c = _ONCHAIN_CACHE.get("whale")
    if not c or time.time() - c[0] > ttl_s:
        c = _ONCHAIN_CACHE["whale"] = (time.time(), oc.whale_mempool())
    if not c[1]:
        return _sig("whale_mempool", None, {}, "blockchain.info", "t607u(c)")
    return _sig("whale_mempool", 0.0, {"whale_txs": len(c[1]["whale_txs"]), "sampled": c[1]["sampled_txs"],
                                       "largest_btc": max([w["btc"] for w in c[1]["whale_txs"]], default=0)},
                "blockchain.info", "t607u(c)")


def macro_event(desk: str, root: Any = None) -> dict[str, Any]:
    """Official central-bank / EIA calendar. Pre-FOMC drift (Lucca & Moench 2015): US equities +0.5 in the 24h
    before a statement. Other desks: event proximity as evidence (score 0). SHADOW (weight 0) until promoted."""
    from pathlib import Path as _P
    from architecture.markets import macro_calendar as mc
    base = _P(root) if root else _P(__file__).resolve().parents[2]
    c = _ONCHAIN_CACHE.get("cal")
    if not c or time.time() - c[0] > 6 * 3600:
        c = _ONCHAIN_CACHE["cal"] = (time.time(), mc.load_or_build(base))
    up = mc.upcoming(c[1], desk, horizon_h=48)
    score = 0.0
    if mc.CALENDAR_DESK.get(desk, desk) == "US" and any(e["event"] == "FOMC_STATEMENT" and 0 < e["hours_until"] <= 24 for e in up):
        score = 0.5
    return _sig("macro_event", score, {"next_events": [{k: e[k] for k in ("event", "at_utc", "hours_until")} for e in up[:4]],
                                       "calendar_status": c[1].get("status")}, "official_calendars", "t607u(b)")


def event_shock(desk: str, symbol: str, root: Any = None, *, now: Any = None,
                calendar: dict[str, Any] | None = None, stories: list[dict[str, Any]] | None = None,
                matrix: dict[str, Any] | None = None) -> dict[str, Any]:
    """Causal event/news shock vector (WP-2, TS-10): scheduled-event window -> measured vol multiplier (sizing only,
    never larger) + documented drift; corroborated (>= 2 publishers) bank-attributed policy-tone news -> signed drift
    through the transmission matrix in news_desk. SHADOW (weight 0) until a walk-forward promotes it."""
    from datetime import datetime as _dt, timezone as _tz
    from pathlib import Path as _P
    from architecture.markets import macro_calendar as mc, news_desk as nd
    base = _P(root) if root else _P(__file__).resolve().parents[2]
    now = now or _dt.now(_tz.utc)
    if calendar is None:
        c = _ONCHAIN_CACHE.get("cal")
        if not c or time.time() - c[0] > 6 * 3600:
            c = _ONCHAIN_CACHE["cal"] = (time.time(), mc.load_or_build(base))
        calendar = c[1]
    if matrix is None:
        matrix = mc.load_impact_matrix(base)
    if stories is None:
        stories = nd.load_corroborated_stories(base)
    ev = mc.event_window_state(calendar, symbol, now=now, matrix=matrix)
    news = nd.causal_news_impact(stories, symbol, now=now)
    drift = max(-1.0, min(1.0, ev["documented_drift"] + news["drift"]))
    available = bool(ev["active_events"] or news["clusters_used"])
    return _sig("event_shock", drift if available else 0.0,
                {"vol_mult": ev["vol_mult"], "size_mult": round(min(1.0, 1.0 / max(1e-9, ev["vol_mult"])), 3),
                 "active_events": ev["active_events"][:4], "news_clusters": news["clusters_used"],
                 "news_evidence": news["evidence"][:3], "matrix_status": "MEASURED" if matrix.get("matrix") else "UNMEASURED"},
                "official_calendars+corroborated_newsroom", "WP-2/TS-10")


def macro_pressure(desk: str, quotes: dict[str, Any], witness: dict[str, Any]) -> dict[str, Any]:
    ev, score, used = {}, 0.0, 0
    for k in ("DXY", "US10Y"):
        q = quotes.get(k) or {}
        ch = q.get("change_24h")
        if isinstance(ch, (int, float)) and (witness.get(k) or {}).get("verdict") == "VERIFIED":
            ev[k] = ch
            used += 1
            score -= max(-1.0, min(1.0, ch / (0.5 if k == "DXY" else 1.5)))
    if not used or desk in ("FOREX", "OIL"):
        return _sig("macro", None, ev, "yahoo+cnbc", "t607u(d)")
    return _sig("macro", score / used, {"change_pct": ev, "rule": "rising dollar/yields pressure gold, equities, crypto"},
                "yahoo+cnbc", "t607u(d)")


# ---------- news (§10) ----------
def _parse_rss(xml: str, src: str) -> list[dict[str, Any]]:
    out = []
    for item in re.findall(r"<item[\s>].*?</item>", xml, flags=re.S | re.I)[:60]:
        t = re.search(r"<title[^>]*>(.*?)</title>", item, re.S | re.I)
        d = re.search(r"<pubDate[^>]*>(.*?)</pubDate>|<dc:date[^>]*>(.*?)</dc:date>", item, re.S | re.I)
        if not t:
            continue
        title = re.sub(r"<!\[CDATA\[|\]\]>|<[^>]+>", "", t.group(1)).strip()
        ts = None
        if d:
            try:
                raw = (d.group(1) or d.group(2)).strip()
                ts = parsedate_to_datetime(raw).timestamp() if d.group(1) else time.mktime(time.strptime(raw[:19], "%Y-%m-%dT%H:%M:%S"))
            except Exception:
                ts = None
        out.append({"title": title, "source": src, "ts": ts})
    return out


def fetch_news(max_age_s: float = 900) -> list[dict[str, Any]]:
    if time.time() - _NEWS_CACHE["at"] < max_age_s and _NEWS_CACHE["items"]:
        return _NEWS_CACHE["items"]
    items: list[dict[str, Any]] = []
    feeds = dict(NEWS_FEEDS)
    try:  # Stage 3: add registry-verified feeds for THIS host (M18 news_registry), capped for the 8 GB laptop
        import os
        from pathlib import Path as _P
        from architecture.markets import news_registry as nr
        host = os.environ.get("AHOS_HOST_ID", "laptop" if os.name == "nt" else "box")
        pri = ["crypto", "energy", "metals", "central_bank", "commodities", "macro", "fx", "markets", "asia", "eu", "official"]
        ver = sorted(nr.verified_feeds(_P(__file__).resolve().parents[2], host),
                     key=lambda f: pri.index(f["category"]) if f["category"] in pri else 99)
        for f in ver:
            if len(feeds) >= NEWS_MAX_FEEDS:
                break
            if f["category"] in pri:
                feeds.setdefault(f["id"], f["url"])
    except Exception:
        pass
    import concurrent.futures as _cf
    with _cf.ThreadPoolExecutor(max_workers=8) as ex:
        for src, b in zip(feeds, ex.map(lambda u: _get(u, 8.0), feeds.values())):
            if b:
                items.extend(_parse_rss(b.decode("utf-8", "replace"), src))
    seen, dedup = set(), []
    for it in items:                      # dedupe on normalised title
        key = re.sub(r"\W+", " ", it["title"].lower()).strip()[:90]
        if key and key not in seen:
            seen.add(key); dedup.append(it)
    _NEWS_CACHE.update(at=time.time(), items=dedup)
    return dedup


def news_signal(desk: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    now = time.time()
    terms = re.compile(ASSET_TERMS[desk], re.I)
    pos, neg = re.compile(POS, re.I), re.compile(NEG, re.I)
    total, srcs, hits = 0.0, set(), []
    for it in items:
        if not it.get("ts") or now - it["ts"] > 48 * 3600 or not terms.search(it["title"]):
            continue
        s = (1 if pos.search(it["title"]) else 0) - (1 if neg.search(it["title"]) else 0)
        if not s:
            continue
        decay = 0.5 ** ((now - it["ts"]) / 3600 / NEWS_HALF_LIFE_H)
        total += s * decay
        srcs.add(it["source"])
        hits.append({"title": it["title"][:120], "source": it["source"], "s": s, "age_h": round((now - it["ts"]) / 3600, 1)})
    corroborated = len(srcs) >= 2
    score = math.tanh(total / 3.0) if corroborated else 0.0
    return _sig("news", score if hits else (0.0 if items else None),
                {"items_matched": len(hits), "sources": sorted(srcs), "corroborated_2src": corroborated,
                 "top": sorted(hits, key=lambda h: h["age_h"])[:4], "feeds_live": len({i["source"] for i in items})},
                "rss:" + ",".join(sorted({i["source"] for i in items})), "§10")


DEFAULT_WEIGHTS = {"mtf_trend": 0.30, "candles": 0.12, "zscore_mr": 0.10, "order_flow": 0.10, "large_trades": 0.10,
                   "funding_oi": 0.06, "stablecoin": 0.05, "macro": 0.08, "news": 0.09,
                   # SHADOW signals: logged + hit-rate tracked, zero weight until promoted by walk-forward (Stage 3)
                   "exchange_netflow": 0.0, "whale_mempool": 0.0, "macro_event": 0.0, "stablecoin_impulse": 0.0,
                   "event_shock": 0.0}


def combine(signals: list[dict[str, Any]], weights: dict[str, float]) -> dict[str, Any]:
    num = den = 0.0
    contrib = []
    for s in signals:
        if not s["available"]:
            continue
        w = float(weights.get(s["name"], 0.0))
        num += w * s["score"]
        den += w
        contrib.append({"signal": s["name"], "score": s["score"], "weight": round(w, 4), "contribution": round(w * s["score"], 4)})
    composite = num / den if den else 0.0
    contrib.sort(key=lambda c: -abs(c["contribution"]))
    return {"composite": round(composite, 4), "weight_used": round(den, 4), "contributions": contrib}
