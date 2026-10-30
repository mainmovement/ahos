"""Crypto breadth from public tickers. Advisory only. Weight stays 0. PAPER_ONLY."""
from __future__ import annotations

import math
from typing import Any

STABLES = frozenset({"USDC", "USDT", "FDUSD", "TUSD", "USDP", "DAI", "USDE", "USD1", "EUR", "AEUR"})
LEVERED_SUFFIX = ("UP", "DOWN", "BULL", "BEAR")
# These feeds did not answer from this network. They are not called.
DROPPED_SOURCES = {
    "dexscreener": "HTTP 403",
    "geckoterminal_networks_trending": "timeout",
}


def _f(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _rows_from_pairs(pairs: list[tuple[str, float, float]]) -> list[dict[str, Any]]:
    return [{"symbol": sym, "change_pct": chg, "volume": vol} for sym, chg, vol in pairs]


def parse_binance_24h(payload: Any) -> list[dict[str, Any]]:
    rows = []
    if not isinstance(payload, list):
        return rows
    for row in payload:
        if not isinstance(row, dict):
            continue
        symbol = str(row.get("symbol") or "")
        if not symbol.endswith("USDT"):
            continue
        base = symbol[:-4]
        if base in STABLES or base.endswith(LEVERED_SUFFIX):
            continue
        change = _f(row.get("priceChangePercent"))
        volume = _f(row.get("quoteVolume"))
        if change is None or volume is None or volume <= 0:
            continue
        rows.append((base, change, volume))
    return _rows_from_pairs(rows)


def parse_okx_spot(payload: Any) -> list[dict[str, Any]]:
    data = payload.get("data") if isinstance(payload, dict) else None
    rows = []
    for row in data or []:
        if not isinstance(row, dict) or row.get("instType") not in (None, "SPOT"):
            continue
        inst = str(row.get("instId") or "")
        if not inst.endswith("-USDT"):
            continue
        base = inst[:-5]
        if base in STABLES or base.endswith(LEVERED_SUFFIX):
            continue
        last, opened = _f(row.get("last")), _f(row.get("open24h"))
        volume = _f(row.get("volCcy24h"))
        if last is None or opened is None or opened <= 0 or volume is None or volume <= 0:
            continue
        rows.append((base, (last - opened) / opened * 100.0, volume))
    return _rows_from_pairs(rows)


def _cg_change(row: dict[str, Any], key: str) -> float | None:
    value = _f(row.get(key))
    if value is None and key.endswith("_in_currency"):
        value = _f(row.get(key[: -len("_in_currency")]))
    return value


def parse_coingecko_markets(payload: Any) -> dict[str, list[dict[str, Any]]]:
    """1h, 24h, and 7d from the top-list payload. Missing horizons stay empty."""
    out: dict[str, list[dict[str, Any]]] = {"1h": [], "24h": [], "7d": []}
    if not isinstance(payload, list):
        return out
    keys = {
        "1h": "price_change_percentage_1h_in_currency",
        "24h": "price_change_percentage_24h_in_currency",
        "7d": "price_change_percentage_7d_in_currency",
    }
    for row in payload:
        if not isinstance(row, dict):
            continue
        symbol = str(row.get("symbol") or "").upper()
        if not symbol or symbol in STABLES:
            continue
        volume = _f(row.get("total_volume"))
        if volume is None or volume <= 0:
            continue
        for horizon, key in keys.items():
            change = _cg_change(row, key)
            if change is None:
                continue
            out[horizon].append({"symbol": symbol, "change_pct": change, "volume": volume})
    return out


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"n": 0, "pct_up": None, "volume_weighted_breadth": None, "top_movers": []}
    up = [row for row in rows if row["change_pct"] > 0]
    volume = sum(row["volume"] for row in rows)
    volume_up = sum(row["volume"] for row in up)
    ordered = sorted(row["volume"] for row in rows)
    median = ordered[len(ordered) // 2]
    spiked = [row for row in rows if median > 0 and row["volume"] >= 3.0 * median]
    spiked.sort(key=lambda row: abs(row["change_pct"]), reverse=True)
    return {
        "n": len(rows),
        "pct_up": round(len(up) / len(rows), 4),
        "volume_weighted_breadth": None if volume <= 0 else round(volume_up / volume, 4),
        "top_movers": [
            {"symbol": row["symbol"], "change_pct": round(row["change_pct"], 2), "volume": round(row["volume"], 2)}
            for row in spiked[:5]
        ],
    }


def _side(breadth: float) -> int:
    if breadth > 0.5:
        return 1
    if breadth < 0.5:
        return -1
    return 0


def advisory_score(breadths: list[float]) -> tuple[float | None, str]:
    """A sign needs two venues on the same side of 0.5. One venue, or a split, does not score."""
    if len(breadths) < 2:
        return None, "single_source"
    sides = {_side(value) for value in breadths}
    if len(sides) != 1:
        return None, "conflict"
    if sides == {0}:
        return 0.0, "flat"
    mid = sum(breadths) / len(breadths)
    score = math.tanh((mid - 0.5) / 0.10)
    return max(-1.0, min(1.0, score)), "agree"


def build_breadth_snapshot(*, binance: Any = None, okx: Any = None, coingecko: Any = None,
                           latency_ms: dict[str, int] | None = None) -> dict[str, Any]:
    binance_rows = parse_binance_24h(binance)
    okx_rows = parse_okx_spot(okx)
    cg = parse_coingecko_markets(coingecko)
    venues = {
        "binance": summarize(binance_rows),
        "okx": summarize(okx_rows),
        "coingecko": {
            "1h": summarize(cg["1h"]),
            "24h": summarize(cg["24h"]),
            "7d": summarize(cg["7d"]),
        },
    }
    present = []
    for name in ("binance", "okx"):
        breadth = venues[name]["volume_weighted_breadth"]
        if isinstance(breadth, float):
            present.append(breadth)
    cg_breadth = venues["coingecko"]["24h"]["volume_weighted_breadth"]
    if isinstance(cg_breadth, float):
        present.append(cg_breadth)
    score, reason = advisory_score(present)
    return {
        "paper_only": True,
        "composite_weight": 0.0,
        "promotion": "weight stays 0 until PASS_STATS+SURVIVED_RED_TEAM",
        "vote_authority": "ADVISORY_ONLY",
        "advisory_score": None if score is None else round(score, 4),
        "agreement": reason,
        "venues": venues,
        "latency_ms": latency_ms or {},
        "dropped_sources": dict(DROPPED_SOURCES),
        "counts_toward_entry_gate": False,
    }


def lock_shadow_weight(weights: dict[str, Any]) -> dict[str, Any]:
    """The saved weight file cannot turn this family on."""
    weights["crypto_breadth"] = 0.0
    return weights


BINANCE_24H_URL = "https://api.binance.com/api/v3/ticker/24hr"
OKX_SPOT_URL = "https://www.okx.com/api/v5/market/tickers?instType=SPOT"
COINGECKO_MARKETS_URL = (
    "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc"
    "&per_page=250&page=1&price_change_percentage=1h,24h,7d"
)


def _pull(getter, url: str, source: str) -> tuple[Any, int]:
    try:
        data, latency = getter(url, source)
    except Exception:
        return None, 0
    return data, int(latency or 0)


def load_cycle_snapshot(*, getter=None) -> dict[str, Any]:
    """One breadth pass plus funding and open-interest context. No keys."""
    if getter is None:
        from architecture.markets.http_guard import fetch_json

        def getter(url: str, source: str):
            result = fetch_json(url, source=source)
            if not result.get("ok"):
                return None, int(result.get("latency_ms") or 0)
            return result.get("data"), int(result.get("latency_ms") or 0)

    from concurrent.futures import ThreadPoolExecutor

    from architecture.markets.crypto_futures_context import SYMBOLS, build_futures_context

    jobs: list[tuple[str, str, str]] = [
        ("binance", BINANCE_24H_URL, "binance_breadth"),
        ("okx", OKX_SPOT_URL, "okx_breadth"),
        ("coingecko", COINGECKO_MARKETS_URL, "coingecko_breadth"),
    ]
    for sym in SYMBOLS:
        jobs.extend((
            (f"binance_funding_{sym}", f"https://fapi.binance.com/fapi/v1/premiumIndex?symbol={sym}USDT", f"binance_funding_{sym}"),
            (f"binance_oi_{sym}", f"https://fapi.binance.com/futures/data/openInterestHist?symbol={sym}USDT&period=1h&limit=2", f"binance_oi_{sym}"),
            (f"okx_funding_{sym}", f"https://www.okx.com/api/v5/public/funding-rate?instId={sym}-USDT-SWAP", f"okx_funding_{sym}"),
            (f"okx_oi_{sym}", f"https://www.okx.com/api/v5/public/open-interest?instType=SWAP&instId={sym}-USDT-SWAP", f"okx_oi_{sym}"),
            (f"okx_oi_hist_{sym}", f"https://www.okx.com/api/v5/rubik/stat/contracts/open-interest-history?instId={sym}-USDT-SWAP&period=1H", f"okx_oi_hist_{sym}"),
        ))
    with ThreadPoolExecutor(max_workers=8) as pool:
        fetched = {key: pool.submit(_pull, getter, url, source) for key, url, source in jobs}
        got = {key: job.result() for key, job in fetched.items()}
    snapshot = build_breadth_snapshot(
        binance=got["binance"][0], okx=got["okx"][0], coingecko=got["coingecko"][0],
        latency_ms={"binance": got["binance"][1], "okx": got["okx"][1], "coingecko": got["coingecko"][1]},
    )
    futures_payload = {
        sym: {
            "binance_funding": got[f"binance_funding_{sym}"][0],
            "binance_oi": got[f"binance_oi_{sym}"][0],
            "okx_funding": got[f"okx_funding_{sym}"][0],
            "okx_oi": got[f"okx_oi_{sym}"][0],
            "okx_oi_hist": got[f"okx_oi_hist_{sym}"][0],
        }
        for sym in SYMBOLS
    }
    snapshot["futures"] = build_futures_context(futures_payload)
    signal = advisory_signal(snapshot)
    signal["evidence"]["futures"] = snapshot["futures"]
    return {"signal": signal, "log": {
        "paper_only": True,
        "composite_weight": 0.0,
        "counts_toward_entry_gate": False,
        "advisory_score": snapshot.get("advisory_score"),
        "agreement": snapshot.get("agreement"),
        "venues": snapshot.get("venues"),
        "futures": snapshot["futures"],
        "latency_ms": snapshot.get("latency_ms"),
        "dropped_sources": snapshot.get("dropped_sources"),
    }}


def advisory_signal(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Unavailable to combine(). The scorecard reads advisory_vote_score."""
    return {
        "name": "crypto_breadth",
        "score": 0.0,
        "available": False,
        "source": "binance+okx+coingecko",
        "spec": "shadow",
        "evidence": {
            "advisory_vote_score": snapshot.get("advisory_score"),
            "composite_weight": 0.0,
            "promotion": snapshot.get("promotion"),
            "vote_authority": "ADVISORY_ONLY",
            "agreement": snapshot.get("agreement"),
            "venues": snapshot.get("venues"),
            "latency_ms": snapshot.get("latency_ms"),
            "dropped_sources": snapshot.get("dropped_sources"),
        },
    }
