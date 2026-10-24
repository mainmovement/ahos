"""Independent free price sources + Two-Source Witness Law (Master Map law 6; Trading Skills v2 §0, §11; TS-0, TS-11).

Source A is the execution feed (Yahoo / CoinGecko, see live_price_feed). Witness sources, all free and keyless:
  * B: TradingView public scanner -> oil, gold futures, indices, FX, QQQ, DXY, US10Y (often 10-min delayed).
       Futures are requested for the SAME contract month that source A is on (explicit ``ICEEUR:BRNF2027``),
       because vendors roll their "1!" continuous series on different days.
  * B fallback: CNBC public quote service (403 from Iran) and Kraken public ticker (BTC, ETH, SOL, UNI, PAXG).
  * C: Stooq (independent vendor) through the r.jina.ai reader mirror; fetched lazily, only for symbols where
       A-B did not verify plus oil (roll-basis diagnostics).

Witness verdict per symbol (the pair must contain A, because A is the price the paper trader fills at):
  VERIFIED   - A agrees with B or C within tolerance on a comparable quote (same contract month when both know it)
  CONFLICT   - two or more prices exist and no pair containing A agrees (also when B and C agree and A is the outlier)
  UNRESOLVED - A missing, or no witness source answered
Gaps and roll basis are evidence only, never traded.
"""
from __future__ import annotations

import concurrent.futures as _cf
import json
import re
import urllib.request
from datetime import datetime, timezone
from typing import Any, Callable
from zoneinfo import ZoneInfo

UA = {"User-Agent": "Mozilla/5.0 (AHOS paper research)"}
CNBC_URL = ("https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol?symbols={syms}"
            "&requestMethod=itv&noform=1&partnerId=2&fund=1&exthrs=1&output=json")
CNBC_MAP = {"WTI": "@CL.1", "BRENT": "@LCO.1", "SPX": ".SPX", "DAX": ".GDAXI", "N225": ".N225",
            "HSI": ".HSI", "EURUSD": "EUR=", "USDJPY": "JPY=", "QQQ": "QQQ", "DXY": ".DXY", "US10Y": "US10Y"}
KRAKEN_URL = "https://api.kraken.com/0/public/Ticker?pair=XBTUSD,ETHUSD,SOLUSD,UNIUSD,PAXGUSD"
KRAKEN_MAP = {"XXBTZUSD": "BTC", "XETHZUSD": "ETH", "SOLUSD": "SOL", "UNIUSD": "UNI", "PAXGUSD": "XAU"}
# Same-contract tolerance (fraction): oil/gold <= 50 bps, FX/indices <= 35 bps (owner spec WP-1); yields are
# compared on the yield level; crypto spot across venues 40 bps.
TOLERANCE = {"XAU": 0.005, "WTI": 0.005, "BRENT": 0.005,
             "SPX": 0.0035, "QQQ": 0.0035, "DAX": 0.0035, "N225": 0.0035, "HSI": 0.0035,
             "EURUSD": 0.0035, "USDJPY": 0.0035, "DXY": 0.0035, "US10Y": 0.02}
DEFAULT_TOL = 0.004
FUTURES = ("BRENT", "WTI", "XAU")
MONTH_CODES = "FGHJKMNQUVXZ"


def _get(url: str, timeout: float) -> Any:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _num(s: Any) -> float | None:
    if isinstance(s, (int, float)):
        return float(s)
    if isinstance(s, str):
        try:
            return float(s.replace(",", "").replace("%", ""))
        except ValueError:
            return None
    return None


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _iso_cnbc(t: str | None) -> str | None:
    if not t:
        return None
    try:
        return datetime.fromisoformat(t.replace(".000", "")).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None


def fetch_cnbc(timeout: float = 8.0) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    try:
        d = _get(CNBC_URL.format(syms="|".join(CNBC_MAP.values())), timeout)
        rows = d["FormattedQuoteResult"]["FormattedQuote"]
    except Exception:
        return out
    rev = {v: k for k, v in CNBC_MAP.items()}
    for q in rows:
        sym = rev.get(q.get("symbol"))
        px = _num(q.get("last"))
        if sym and px:
            out[sym] = {"price": px, "source": f"cnbc:{q.get('symbol')}", "market_time": _iso_cnbc(q.get("last_time")),
                        "volume": _num(q.get("volume")), "vendor": "cnbc",
                        "contract_month": None}
    return out


def fetch_kraken(timeout: float = 8.0) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    try:
        res = _get(KRAKEN_URL, timeout)["result"]
    except Exception:
        return out
    now = _now_iso()
    for k, v in res.items():
        sym = KRAKEN_MAP.get(k)
        px = _num((v.get("c") or [None])[0])
        if sym and px:
            out[sym] = {"price": px, "source": f"kraken:{k}", "market_time": now, "volume_24h": _num((v.get("v") or [0, 0])[1]),
                        "vendor": "kraken", "instrument_basis": "spot_token" if sym == "XAU" else None}
    return out


TV_URL = "https://scanner.tradingview.com/global/scan"
TV_MAP = {"WTI": "NYMEX:CL1!", "BRENT": "ICEEUR:BRN1!", "XAU": "COMEX:GC1!", "SPX": "SP:SPX", "DAX": "XETR:DAX",
          "N225": "TVC:NI225", "HSI": "TVC:HSI", "EURUSD": "FX:EURUSD", "USDJPY": "FX:USDJPY", "QQQ": "NASDAQ:QQQ",
          "DXY": "TVC:DXY", "US10Y": "TVC:US10Y"}
TV_FUTURES_ROOT = {"WTI": "NYMEX:CL", "BRENT": "ICEEUR:BRN", "XAU": "COMEX:GC"}


def tv_contract_ticker(sym: str, contract_month: str | None) -> str | None:
    """``2027-01`` -> ``ICEEUR:BRNF2027``."""
    root = TV_FUTURES_ROOT.get(sym)
    if not root or not contract_month or not re.fullmatch(r"\d{4}-\d{2}", contract_month):
        return None
    y, m = int(contract_month[:4]), int(contract_month[5:])
    return f"{root}{MONTH_CODES[m - 1]}{y}" if 1 <= m <= 12 else None


def _tv_delay_s(update_mode: Any) -> int:
    m = re.search(r"(\d+)$", str(update_mode or ""))
    return int(m.group(1)) if m and "delayed" in str(update_mode) else 0


def fetch_tradingview(timeout: float = 8.0, *, contract_months: dict[str, str | None] | None = None) -> dict[str, dict[str, Any]]:
    """TradingView public scanner (free, no key, reachable from Iran; CNBC returns 403 there). Often 10-min delayed.
    With ``contract_months`` the futures row is the explicit same-month contract; the "1!" row is kept as diagnostic."""
    explicit = {s: tv_contract_ticker(s, m) for s, m in (contract_months or {}).items()}
    tickers = list(TV_MAP.values()) + [t for t in explicit.values() if t]
    body = json.dumps({"symbols": {"tickers": tickers}, "columns": ["close", "volume", "update_mode", "expiration"]}).encode()
    try:
        req = urllib.request.Request(TV_URL, data=body, headers={**UA, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            rows = json.loads(r.read().decode("utf-8"))["data"]
    except Exception:
        return {}
    rev = {v: k for k, v in TV_MAP.items()}
    rev_explicit = {t: s for s, t in explicit.items() if t}
    now = _now_iso()
    out: dict[str, dict[str, Any]] = {}
    continuous: dict[str, dict[str, Any]] = {}
    for row in rows:
        d = row.get("d") or []
        px = _num(d[0]) if d else None
        if not px:
            continue
        q = {"price": px, "source": f"tradingview:{row['s']}", "fetched_at": now, "vendor": "tradingview",
             "volume": _num(d[1]) if len(d) > 1 else None, "update_mode": d[2] if len(d) > 2 else None,
             "delay_s": _tv_delay_s(d[2] if len(d) > 2 else None)}
        exp = d[3] if len(d) > 3 else None
        if row["s"] in rev_explicit:
            sym = rev_explicit[row["s"]]
            out[sym] = {**q, "contract_month": contract_months[sym], "expiration": exp}  # type: ignore[index]
        elif row["s"] in rev:
            sym = rev[row["s"]]
            continuous[sym] = {**q, "contract_month": None}
    for sym, q in continuous.items():
        if sym in out:
            out[sym]["continuous_front"] = {"price": q["price"], "source": q["source"]}
        else:
            out[sym] = q
    return out


def fetch_second_sources(timeout: float = 8.0, *, contract_months: dict[str, str | None] | None = None) -> dict[str, dict[str, Any]]:
    """Source B: TradingView first (same contract month for futures), CNBC fills gaps, Kraken for crypto.
    CNBC/Kraken continuous futures are never substituted when the month-aligned TradingView contract answered."""
    b = fetch_cnbc(timeout)
    b.update(fetch_tradingview(timeout, contract_months=contract_months))
    k = fetch_kraken(timeout)
    for sym, q in k.items():
        if sym != "XAU" or "XAU" not in b:
            b[sym] = q
    return b


# ---------------- Source C: Stooq (independent vendor) via the r.jina.ai reader mirror ----------------
JINA_STOOQ_URL = "https://r.jina.ai/https://stooq.com/q/?s={sym}"
STOOQ_MAP = {"BRENT": "cb.f", "WTI": "cl.f", "XAU": "gc.f", "DAX": "^dax", "N225": "^nkx",
             "HSI": "^hsi", "EURUSD": "eurusd", "USDJPY": "usdjpy", "QQQ": "qqq.us", "US10Y": "10usy.b"}
WARSAW = ZoneInfo("Europe/Warsaw")
_MON3 = {m: i + 1 for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}


def _http_text(url: str, timeout: float) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (AHOS paper research)"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read(400_000).decode("utf-8", "replace")
    except Exception:
        return None


def parse_stooq_page(text: str, stooq_sym: str, *, now: datetime | None = None) -> dict[str, Any] | None:
    """Parse ``**Crude Oil Brent - ICE (CB.F)**23 Oct, 23:00**116.72+3.55(+3.14%)**`` (Warsaw local time)."""
    pat = r"\(" + re.escape(stooq_sym.upper()) + r"\)\*\*([^*]{3,24})\*\*([0-9][0-9,]*(?:\.[0-9]+)?)"
    m = re.search(pat, text or "")
    if not m:
        return None
    px = _num(m.group(2))
    if not px:
        return None
    now = now or datetime.now(timezone.utc)
    local_now = now.astimezone(WARSAW)
    raw_t = m.group(1).strip()
    mt = None
    dm = re.match(r"(\d{1,2}) ([A-Za-z]{3}),? (\d{1,2}):(\d{2})", raw_t)
    tm = re.match(r"(\d{1,2}):(\d{2})(?::(\d{2}))?$", raw_t)
    try:
        if dm:
            mon = _MON3.get(dm.group(2).lower())
            if mon:
                year = local_now.year - (1 if mon > local_now.month + 1 else 0)
                mt = datetime(year, mon, int(dm.group(1)), int(dm.group(3)), int(dm.group(4)), tzinfo=WARSAW)
        elif tm:
            mt = local_now.replace(hour=int(tm.group(1)), minute=int(tm.group(2)), second=int(tm.group(3) or 0), microsecond=0)
    except ValueError:
        mt = None
    return {"price": px, "source": f"stooq:{stooq_sym}", "vendor": "stooq", "via": "r.jina.ai",
            "market_time": mt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if mt else None,
            "market_time_raw": raw_t, "contract_month": None, "fetched_at": _now_iso()}


def fetch_third_sources(symbols: list[str] | tuple[str, ...], *, timeout: float = 25.0, max_symbols: int = 6,
                        getter: Callable[[str, float], str | None] = _http_text) -> dict[str, dict[str, Any]]:
    wanted = [s for s in dict.fromkeys(symbols) if s in STOOQ_MAP][:max_symbols]
    if not wanted:
        return {}
    def one(sym: str) -> dict[str, Any] | None:
        for _ in range(2):  # the free reader mirror rate-limits bursts
            q = parse_stooq_page(getter(JINA_STOOQ_URL.format(sym=STOOQ_MAP[sym]), timeout) or "", STOOQ_MAP[sym])
            if q:
                return q
        return None

    out: dict[str, dict[str, Any]] = {}
    with _cf.ThreadPoolExecutor(max_workers=min(2, len(wanted))) as ex:
        for sym, q in zip(wanted, ex.map(one, wanted)):
            if q:
                out[sym] = q
    return out


# ---------------- witness ----------------
def _parse_iso(ts: Any) -> float | None:
    try:
        return datetime.strptime(str(ts), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
    except (TypeError, ValueError):
        return None


def _a_price_at(a: dict[str, Any], ts: float | None) -> tuple[float | None, bool]:
    """Price of the execution feed at a witness's effective time (delayed vendors), from A's own 5m bars."""
    pa = a.get("price")
    bars, stamps = a.get("ohlcv_5m") or [], a.get("ohlcv_5m_ts") or []
    if ts is None or not bars or len(bars) != len(stamps) or not any(stamps):
        return pa, False
    a_mt = _parse_iso(a.get("market_time"))
    if a_mt is not None and ts >= a_mt:
        return pa, False
    best = None
    for st, bar in zip(stamps, bars):
        if st and st + 300 <= ts:  # bar must have closed by ts (5m bars, Yahoo stamps = bar start)
            best = bar[3]
    return (float(best), True) if best else (pa, False)


def _gap(x: float, y: float) -> float:
    return abs(x - y) / ((x + y) / 2.0)


def _comparable(a: dict[str, Any], x: dict[str, Any]) -> bool:
    if x.get("instrument_basis"):
        return False
    ma, mx = a.get("contract_month"), x.get("contract_month")
    return not (ma and mx and ma != mx)


def witness(sym: str, a: dict[str, Any] | None, b: dict[str, Any] | None, c: dict[str, Any] | None = None) -> dict[str, Any]:
    a, b, c = a or {}, b or {}, c or {}
    pa, pb, pc = a.get("price"), b.get("price"), c.get("price")
    tol = TOLERANCE.get(sym, DEFAULT_TOL)
    base: dict[str, Any] = {"symbol": sym, "source_a": a.get("source"), "price_a": pa,
                            "source_b": b.get("source"), "price_b": pb, "tolerance": tol,
                            "source_c": c.get("source"), "price_c": pc,
                            "contract_month_a": a.get("contract_month"), "contract_month_b": b.get("contract_month")}
    ok = lambda p: isinstance(p, (int, float)) and p > 0  # noqa: E731
    if not ok(pa) or (not ok(pb) and not ok(pc)):
        return {**base, "verdict": "UNRESOLVED", "gap": None, "pair": None, "n_sources": int(ok(pa)) + int(ok(pb)) + int(ok(pc))}
    diag: dict[str, Any] = {}
    pairs: list[tuple[str, float, bool]] = []
    for label, x, px in (("A-B", b, pb), ("A-C", c, pc)):
        if not ok(px):
            continue
        eff_ts = None
        if x.get("delay_s"):
            eff_ts = (_parse_iso(x.get("fetched_at")) or 0) - float(x["delay_s"])
        ref, aligned = _a_price_at(a, eff_ts)
        g = _gap(float(ref), float(px))
        diag[f"gap_{label.replace('-', '').lower()}"] = round(g, 5)
        if aligned:
            diag[f"time_aligned_{label.replace('-', '').lower()}"] = True
        if x.get("instrument_basis"):
            diag[f"basis_{label.replace('-', '').lower()}"] = x["instrument_basis"]
        pairs.append((label, g, _comparable(a, x)))
    if ok(pb) and ok(pc):
        diag["gap_bc"] = round(_gap(float(pb), float(pc)), 5)
    if sym in FUTURES and ok(pc) and a.get("contract_month") and not c.get("contract_month"):
        diag["futures_roll_basis_bps"] = round((float(pc) - float(pa)) / float(pa) * 1e4, 1)
    front = (b.get("continuous_front") or {}).get("price")
    if sym in FUTURES and ok(front):
        diag["front_vs_a_bps"] = round((float(front) - float(pa)) / float(pa) * 1e4, 1)
    n_sources = 1 + int(ok(pb)) + int(ok(pc))
    agree = sorted((p for p in pairs if p[2] and p[1] <= tol), key=lambda p: p[1])
    if agree:
        label, g, _ = agree[0]
        other = pb if label == "A-B" else pc
        return {**base, "verdict": "VERIFIED", "gap": round(g, 5), "pair": label, "n_sources": n_sources,
                "corroborated_price": round((float(pa) + float(other)) / 2.0, 6), "diagnostics": diag}
    comparable = [p for p in pairs if p[2]]
    if not comparable:
        return {**base, "verdict": "UNRESOLVED", "gap": None, "pair": None, "n_sources": n_sources,
                "diagnostics": {**diag, "reason": "no_same_contract_witness"}}
    if diag.get("gap_bc") is not None and diag["gap_bc"] <= tol:
        diag["a_outlier"] = True
    worst = min(comparable, key=lambda p: p[1])
    return {**base, "verdict": "CONFLICT", "gap": round(worst[1], 5), "pair": worst[0], "n_sources": n_sources,
            "diagnostics": diag}


def third_source_needed(pre: dict[str, dict[str, Any]]) -> list[str]:
    """Symbols that need source C: A-B not VERIFIED, plus futures for roll-basis evidence."""
    need = [s for s, w in pre.items() if w.get("verdict") != "VERIFIED" and s in STOOQ_MAP]
    return list(dict.fromkeys(need + [s for s in FUTURES if s in pre]))
