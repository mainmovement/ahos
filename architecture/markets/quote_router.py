"""Public keyless primaries. Yahoo stays the fallback. PAPER_ONLY. No keys."""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Callable

from architecture.markets.cnbc_quotes import SYMBOLS as CNBC_SYMBOLS
from architecture.markets.cnbc_quotes import fetch_cnbc_primary
from architecture.markets.frankfurter_fx import fetch_frankfurter
from architecture.markets.gold_api_quote import fetch_gold_witness
from architecture.markets.hyperliquid_mids import fetch_hyperliquid_mids
from architecture.markets.tradingview_batch import TICKERS as TV_TICKERS
from architecture.markets.tradingview_batch import fetch_tradingview_batch

MAX_DEVIATION_PCT = 0.5
DAILY_SANITY_PCT = 2.0
# Prior-day FX is a sanity check. The 0.5% cycle witness for these two is the perp.
FX_PERP = {"EURUSD", "USDJPY"}
PRIMARY_VENDORS = ("tradingview", "cnbc")
# FDAX printed, but it has no Yahoo continuous and no perp, so it is not a book.
OMITTED = {"FDAX"}
# Cash twins get the same perp witness as the listed contract.
HL_CASH = {"WTI": "CL", "BRENT": "BZ", "GC": "XAU"}


def _safe(fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        return fn() or {}
    except Exception:
        return {}


def _epoch(raw: Any) -> float | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    text = raw.strip()
    if len(text) == 20 and text.endswith("Z"):
        try:
            return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
        except ValueError:
            return None
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        try:
            return datetime.strptime(text, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()
        except ValueError:
            return None
    try:
        return datetime.fromisoformat(text.replace(".000", "")).timestamp()
    except ValueError:
        return None


def _z(moment: float) -> str:
    return datetime.fromtimestamp(moment, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _pct(witness: Any, ref: Any) -> float | None:
    if not isinstance(witness, (int, float)) or not isinstance(ref, (int, float)) or ref <= 0:
        return None
    return abs(float(witness) - float(ref)) / float(ref) * 100.0


def independent_witness(quote: dict[str, Any] | None, fetched: dict[str, Any] | None) -> dict[str, Any] | None:
    """A TradingView or CNBC fill must not be verified by the same vendor."""
    quote = quote or {}
    vendor = str(quote.get("source") or "").split(":", 1)[0]
    got = str((fetched or {}).get("source") or "").split(":", 1)[0]
    yahoo = quote.get("yahoo_witness")
    if vendor in PRIMARY_VENDORS and isinstance(yahoo, dict) and isinstance(yahoo.get("price"), (int, float)):
        if not fetched or got == vendor:
            return yahoo
    return fetched


def _adopt(quote: dict[str, Any], primary: dict[str, Any], asof: float) -> None:
    yahoo_px = quote.get("price")
    if isinstance(yahoo_px, (int, float)) and yahoo_px > 0:
        quote["yahoo_witness"] = {
            "price": float(yahoo_px),
            "source": quote.get("source") or "yahoo",
            "market_time": quote.get("market_time"),
            "contract_month": quote.get("contract_month"),
            "source_role": "witness",
        }
        quote["yahoo_price"] = float(yahoo_px)
    moment = _epoch(primary.get("source_timestamp") or primary.get("market_time"))
    if moment is None:
        moment = asof - max(0, int(primary.get("delay_s") or 0))
    stamp = _z(moment)
    quote["price"] = primary["price"]
    quote["source"] = primary["source"]
    quote["source_role"] = "primary"
    quote["market_time"] = stamp
    quote["source_timestamp"] = stamp
    quote["latency_ms"] = primary.get("latency_ms")
    quote["delay_flag"] = primary.get("delay_flag")
    quote["delay_s"] = primary.get("delay_s") or 0
    age = asof - moment
    quote["age_seconds"] = int(age) if age >= 0 else None
    quote["freshness"] = "LIVE" if 0 <= age < 300 else "STALE"
    quote["paper_only"] = True


def _note(quote: dict[str, Any], source: str, price: float, ref: float, flag: str) -> float | None:
    gap = _pct(price, ref)
    if gap is None:
        return None
    quote.setdefault("witnesses", []).append({
        "source": source, "price": price, "ref": ref, "deviation_pct": round(gap, 4), "delay_flag": flag,
    })
    return gap


def route_public_quotes(quotes: dict[str, Any], *, asof: float | None = None,
                        cnbc: Callable[[], dict[str, Any]] | None = None,
                        tv: Callable[[], dict[str, Any]] | None = None,
                        hl: Callable[[], dict[str, Any]] | None = None,
                        gold: Callable[[], dict[str, Any]] | None = None,
                        fx: Callable[[], dict[str, Any]] | None = None) -> dict[str, Any]:
    """Fill named symbols from the public primary. A witness gap above 0.5% skips that symbol."""
    moment = time.time() if asof is None else asof
    jobs = {
        "cnbc": cnbc or fetch_cnbc_primary,
        "tv": tv or fetch_tradingview_batch,
        "hl": hl or fetch_hyperliquid_mids,
        "gold": gold or fetch_gold_witness,
        "fx": fx or fetch_frankfurter,
    }
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        fetched = {name: pool.submit(_safe, fn) for name, fn in jobs.items()}
        got = {name: job.result() for name, job in fetched.items()}
    cnbc_q, tv_q, hl_q = got["cnbc"], got["tv"], got["hl"]
    gold_q, fx_q = got["gold"], got["fx"]

    for sym in CNBC_SYMBOLS:
        primary = cnbc_q.get(sym)
        quote = quotes.get(sym)
        if not isinstance(quote, dict):
            continue
        if isinstance(primary, dict) and isinstance(primary.get("price"), (int, float)):
            _adopt(quote, primary, moment)
        elif isinstance(quote.get("price"), (int, float)):
            quote["source_role"] = "yahoo_fallback"
            quote.setdefault("delay_flag", "yahoo")
    for sym, primary in tv_q.items():
        if sym in OMITTED:
            quotes[sym] = {**primary, "omitted_from_book": True, "paper_only": True}
            continue
        quote = quotes.get(sym)
        if not isinstance(quote, dict) or not isinstance(primary, dict):
            continue
        if isinstance(primary.get("price"), (int, float)):
            _adopt(quote, primary, moment)
    for sym in TV_TICKERS:
        if sym in OMITTED or sym in tv_q:
            continue
        quote = quotes.get(sym)
        if isinstance(quote, dict) and isinstance(quote.get("price"), (int, float)) and quote.get("source_role") != "primary":
            quote["source_role"] = "yahoo_fallback"
            quote.setdefault("delay_flag", "yahoo")

    for sym, quote in list(quotes.items()):
        if not isinstance(quote, dict) or not isinstance(quote.get("price"), (int, float)):
            continue
        gaps: list[float] = []
        yahoo = quote.get("yahoo_witness") if isinstance(quote.get("yahoo_witness"), dict) else None
        if yahoo and quote.get("source_role") == "primary":
            gap = _note(quote, str(yahoo.get("source") or "yahoo"), float(yahoo["price"]), float(quote["price"]), "yahoo")
            if gap is not None and sym not in FX_PERP:
                gaps.append(gap)
        extra = gold_q.get(sym) if sym in ("XAU", "GC") else None
        if sym == "GC" and extra is None:
            extra = gold_q.get("XAU")
        if isinstance(extra, dict) and isinstance(extra.get("price"), (int, float)):
            gap = _note(quote, str(extra.get("source")), float(extra["price"]), float(quote["price"]), str(extra.get("delay_flag") or ""))
            if gap is not None:
                gaps.append(gap)
        fx_row = fx_q.get(sym)
        if isinstance(fx_row, dict) and isinstance(fx_row.get("price"), (int, float)):
            gap = _pct(fx_row["price"], quote["price"])
            if gap is not None:
                quote["frankfurter_deviation_pct"] = round(gap, 4)
                quote["daily_sanity"] = "PASS" if gap <= DAILY_SANITY_PCT else "FAIL"
                quote.setdefault("witnesses", []).append({
                    "source": str(fx_row.get("source") or "frankfurter"), "price": float(fx_row["price"]),
                    "ref": float(quote["price"]), "deviation_pct": round(gap, 4), "delay_flag": "daily",
                    "role": "daily_sanity",
                })
        quote["witness_deviation_pct"] = None if not gaps else round(max(gaps), 4)
        quote["divergence_skip"] = quote["witness_deviation_pct"] is not None and quote["witness_deviation_pct"] > MAX_DEVIATION_PCT

    for sym, row in hl_q.items():
        if not isinstance(row, dict):
            continue
        targets = [sym]
        targets += [cash for cash, listed in HL_CASH.items() if listed == sym]
        for target in targets:
            quote = quotes.get(target)
            if not isinstance(quote, dict) or not isinstance(quote.get("price"), (int, float)):
                continue
            if not isinstance(row.get("price"), (int, float)):
                continue
            basis = row.get("basis_future")
            basis_q = quotes.get(basis) if isinstance(basis, str) else None
            ref = quote["price"]
            if isinstance(basis_q, dict) and isinstance(basis_q.get("price"), (int, float)) and not basis_q.get("divergence_skip"):
                ref = basis_q["price"]
            gap = _note(quote, str(row.get("source")), float(row["price"]), float(ref), "realtime")
            if gap is None:
                continue
            prior = quote.get("witness_deviation_pct")
            worst = gap if prior is None else max(float(prior), gap)
            quote["witness_deviation_pct"] = round(worst, 4)
            if worst > MAX_DEVIATION_PCT:
                quote["divergence_skip"] = True
            elif "divergence_skip" not in quote:
                quote["divergence_skip"] = False
    return quotes
