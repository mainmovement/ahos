"""Keyless listed-stock scanner. New names stay in shadow.

TradingView's public scanner is the source. One page is handled and dropped.
Only a short list is kept. Nothing here is added to the live paper book.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from architecture.markets.multi_market_desks import DESK_SPECS
from architecture.markets.paper_trade_gates import (
    MIN_AGREEING_FAMILIES,
    MIN_EXPECTED_PROFIT_TO_FEE_RATIO,
    VOTE_SCORE_FLOOR,
    independent_vote_gate,
)

REGISTRY_REL = Path("reports") / "grok" / "PAPER" / "equity_universe_registry.json"
OUT_REL = Path("reports") / "grok" / "PAPER" / "equity_universe.json"
PAGE = 400
MAX_PAGES = 40
TOP_N = 8
KEEP_PER_EXCHANGE = 32
CACHE_S = 900
MIN_VOLUME = 100_000
MIN_MARKET_CAP = 1_000_000_000
MIN_PRICE = 1.0
MIN_ABS_CHANGE = 1.0
MIN_VOLATILITY = 1.0
MAX_VOLATILITY = 80.0

# market path, exchange code, desk. Euronext is the country scanners that answer.
EXCHANGES: tuple[dict[str, str], ...] = (
    {"market": "america", "exchange": "NASDAQ", "desk": "US_EQUITIES"},
    {"market": "america", "exchange": "NYSE", "desk": "US_EQUITIES"},
    {"market": "germany", "exchange": "XETR", "desk": "EU_EQUITIES"},
    {"market": "uk", "exchange": "LSE", "desk": "EU_EQUITIES"},
    {"market": "france", "exchange": "EURONEXT", "desk": "EU_EQUITIES"},
    {"market": "netherlands", "exchange": "EURONEXT", "desk": "EU_EQUITIES"},
    {"market": "belgium", "exchange": "EURONEXT", "desk": "EU_EQUITIES"},
    {"market": "portugal", "exchange": "EURONEXT", "desk": "EU_EQUITIES"},
    {"market": "ireland", "exchange": "EURONEXT", "desk": "EU_EQUITIES"},
    {"market": "japan", "exchange": "TSE", "desk": "ASIA_EQUITIES"},
    {"market": "hongkong", "exchange": "HKEX", "desk": "ASIA_EQUITIES"},
)
COLUMNS = ["name", "close", "volume", "market_cap_basic", "change", "Volatility.D", "bid", "ask"]


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _num(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def write_registry(root: Path) -> dict[str, Any]:
    path = root / REGISTRY_REL
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    doc = {
        "schema": "ahos.equity_universe_registry.v1",
        "paper_only": True,
        "registered_at": _utc(),
        "top_n": TOP_N,
        "min_volume": MIN_VOLUME,
        "min_market_cap_scanner_units": MIN_MARKET_CAP,
        "min_price": MIN_PRICE,
        "min_abs_change": MIN_ABS_CHANGE,
        "min_volatility": MIN_VOLATILITY,
        "max_volatility": MAX_VOLATILITY,
        "min_agreeing_families": MIN_AGREEING_FAMILIES,
        "vote_score_floor": VOTE_SCORE_FLOOR,
        "min_expected_profit_to_fee_ratio": MIN_EXPECTED_PROFIT_TO_FEE_RATIO,
        "promotion_rule": (
            "A new name stays out of the live book until 30 closes that both "
            "opened and closed after registered_at pass the stats gate and the red team."
        ),
        "applied_to_live": False,
        "promotable": False,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return doc


def _screen(row: dict[str, Any], desk: str) -> dict[str, Any] | None:
    cols = row.get("d") or []
    if len(cols) < 6:
        return None
    price = _num(cols[1])
    volume = _num(cols[2])
    cap = _num(cols[3])
    change = _num(cols[4])
    volatility = _num(cols[5])
    bid = _num(cols[6]) if len(cols) > 6 else None
    ask = _num(cols[7]) if len(cols) > 7 else None
    if price is None or volume is None:
        return None
    spread = None
    if bid is not None and ask is not None and ask >= bid > 0 and price > 0:
        spread = (ask - bid) / ((ask + bid) / 2.0) * 100.0
    cap_ok = cap is not None and cap >= MIN_MARKET_CAP
    measurable = (
        volume >= MIN_VOLUME
        and cap_ok
        and price >= MIN_PRICE
        and change is not None
        and abs(change) >= MIN_ABS_CHANGE
        and volatility is not None
        and MIN_VOLATILITY <= volatility <= MAX_VOLATILITY
    )
    max_spread = float(DESK_SPECS.get(desk, {}).get("max_spread_pct", 0.5))
    spread_ok = spread is not None and spread <= max_spread
    return {
        "symbol": str(row.get("s") or ""),
        "name": cols[0] if isinstance(cols[0], str) else None,
        "price": price,
        "volume": volume,
        "market_cap": cap,
        "change": change,
        "volatility": volatility,
        "spread_pct": None if spread is None else round(spread, 4),
        "spread_status": "KNOWN" if spread is not None else "UNKNOWN",
        "passes_measurable": measurable,
        "passes_spread": spread_ok,
        "max_spread_pct": max_spread,
    }


def _keep(found: list[dict[str, Any]], row: dict[str, Any]) -> None:
    if not row.get("passes_measurable"):
        return
    found.append(row)
    found.sort(key=lambda item: float(item["volume"]), reverse=True)
    del found[KEEP_PER_EXCHANGE:]


def scan_exchange(
    spec: dict[str, str],
    fetch: Callable[[str, dict[str, Any]], dict[str, Any]],
    *,
    start_at: int = 0,
) -> dict[str, Any]:
    """Page the scanner. Drop each page after counting it."""
    url = f"https://scanner.tradingview.com/{spec['market']}/scan"
    start = max(0, int(start_at))
    pages = 0
    scanned = 0
    reported = None
    passed_measurable = 0
    spread_known = 0
    found: list[dict[str, Any]] = []
    error = None
    while pages < MAX_PAGES:
        payload = {
            "filter": [
                {"left": "type", "operation": "equal", "right": "stock"},
                {"left": "exchange", "operation": "in_range", "right": [spec["exchange"]]},
            ],
            "options": {"lang": "en"},
            "symbols": {"query": {"types": []}, "tickers": []},
            "columns": COLUMNS,
            "sort": {"sortBy": "volume", "sortOrder": "desc"},
            "range": [start, start + PAGE],
        }
        result = fetch(url, payload)
        if not result.get("ok"):
            error = result.get("reason") or "fetch_failed"
            break
        data = result.get("data") if isinstance(result.get("data"), dict) else {}
        if reported is None and isinstance(data.get("totalCount"), int):
            reported = int(data["totalCount"])
        rows = data.get("data") if isinstance(data.get("data"), list) else []
        if not rows:
            break
        for raw in rows:
            if not isinstance(raw, dict):
                continue
            scanned += 1
            screened = _screen(raw, spec["desk"])
            if screened is None:
                continue
            if screened["spread_status"] == "KNOWN":
                spread_known += 1
            if screened["passes_measurable"]:
                passed_measurable += 1
                _keep(found, screened)
        pages += 1
        start += len(rows)
        if reported is not None and start >= reported:
            break
    return {
        "market": spec["market"],
        "exchange": spec["exchange"],
        "desk": spec["desk"],
        "reported_total": reported,
        "scanned": scanned,
        "pages": pages,
        "truncated": bool(reported is not None and scanned < reported),
        "passed_measurable": passed_measurable,
        "spread_known": spread_known,
        "error": error,
        "shortlist": found,
    }


def _news_hits(root: Path, symbol: str) -> int:
    path = root / "reports" / "grok" / "PAPER" / "desk_news.jsonl"
    if not path.is_file():
        return 0
    ticker = symbol.split(":")[-1].upper()
    if len(ticker) < 2:
        return 0
    try:
        size = path.stat().st_size
        with path.open("rb") as handle:
            if size > 200_000:
                handle.seek(size - 200_000)
            blob = handle.read().decode("utf-8", "replace").upper()
    except OSError:
        return 0
    return blob.count(ticker)


def _shadow_size(root: Path, desk: str) -> dict[str, Any]:
    from architecture.markets.paper_trader import (
        CLUSTER_CAPS,
        CLUSTER_OF_DESK,
        DESK_WEIGHTS,
        INSTRUMENTS,
        MIN_STOP,
        RISK_PER_TRADE,
    )
    from architecture.markets.paper_trade_gates import effective_desk_notional_mult

    status_path = root / "reports" / "grok" / "PAPER" / "paper_trader_status.json"
    equity = 100.0
    if status_path.is_file():
        try:
            status = json.loads(status_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            status = {}
        mark = status.get("mark_to_market_equity_usd") if isinstance(status, dict) else None
        if isinstance(mark, (int, float)) and not isinstance(mark, bool) and mark > 0:
            equity = float(mark)
    on_desk = sum(1 for _sym, row in INSTRUMENTS.items() if row[0] == desk) or 1
    desk_cap = equity * float(DESK_WEIGHTS[desk]) / on_desk
    per_name = equity * RISK_PER_TRADE / MIN_STOP
    mult, source = effective_desk_notional_mult(root, desk)
    cluster = CLUSTER_OF_DESK[desk]
    cluster_cap = equity * float(CLUSTER_CAPS[cluster])
    notional = min(per_name, desk_cap, cluster_cap) * mult
    return {
        "equity_usd": round(equity, 4),
        "desk_cap_usd": round(desk_cap, 4),
        "per_name_cap_usd": round(min(per_name, desk_cap, cluster_cap) * mult, 4),
        "desk_notional_mult": mult,
        "desk_notional_source": source,
        "cluster_cap_usd": round(cluster_cap, 4),
        "applied_to_live": False,
        "shadow_notional_usd": round(notional, 4),
    }


def _candidate(root: Path, row: dict[str, Any], desk: str, exchange: str) -> dict[str, Any]:
    hits = _news_hits(root, str(row["symbol"]))
    change = row.get("change")
    side = "LONG" if isinstance(change, (int, float)) and change > 0 else "SHORT"
    vote_ok, vote = independent_vote_gate([], side)
    full = bool(row["passes_measurable"] and row["passes_spread"] and hits > 0 and vote.get("applicable") and vote_ok)
    from science.pump_anomaly import pump_veto

    token = "SWAP" in str(row["symbol"]) or str(row["symbol"]).startswith("DEX")
    anomaly = pump_veto(
        liquidity_locked=not token,
        holder_growth=token,
        change=float(change) if isinstance(change, (int, float)) else 0.0,
    )
    return {
        "symbol": row["symbol"],
        "name": row["name"],
        "exchange": exchange,
        "desk": desk,
        "volume": row["volume"],
        "change": row["change"],
        "volatility": row["volatility"],
        "spread_status": row["spread_status"],
        "news_hits": hits,
        "side_from_change": side,
        "families_present": vote.get("families_present"),
        "vote_applicable": vote.get("applicable"),
        "vote_ok_if_applicable": vote_ok,
        "fee_gate": "UNEVALUABLE",
        "fee_reason": "NO_SIGNAL_COMPOSITE",
        "passes_full_screen": full and not anomaly["veto"],
        "anomaly_veto": anomaly["veto"],
        "live_open": False,
        "size": _shadow_size(root, desk),
    }


def _default_fetch(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    from architecture.markets.http_guard import fetch_json

    source = "tv_universe_" + url.rstrip("/").rsplit("/", 1)[-1]
    return fetch_json(url, source=source, method="POST", payload=payload, timeout=20.0)


def _fresh(doc: dict[str, Any], now: datetime) -> bool:
    stamp = doc.get("generated_at")
    if not isinstance(stamp, str):
        return False
    try:
        moment = datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return False
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return (now - moment).total_seconds() < CACHE_S and doc.get("pass_stats") is False


def export_universe(
    root: Path,
    *,
    fetch: Callable[[str, dict[str, Any]], dict[str, Any]] | None = None,
    now: datetime | None = None,
    use_cache: bool = True,
) -> dict[str, Any]:
    root = Path(root)
    registry = write_registry(root)
    out = root / OUT_REL
    moment = now or datetime.now(timezone.utc)
    if use_cache and out.is_file():
        try:
            cached = json.loads(out.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cached = None
        if isinstance(cached, dict) and _fresh(cached, moment):
            return cached
    getter = fetch or _default_fetch
    exchanges = []
    pool: dict[str, list[dict[str, Any]]] = {}
    for spec in EXCHANGES:
        scanned = scan_exchange(spec, getter)
        for row in scanned.pop("shortlist"):
            pool.setdefault(spec["desk"], []).append({**row, "exchange": spec["exchange"]})
        exchanges.append(scanned)
    candidates = []
    per_desk = {}
    for desk, rows in pool.items():
        rows.sort(key=lambda item: float(item["volume"]), reverse=True)
        chosen = rows[:TOP_N]
        built = [_candidate(root, row, desk, str(row["exchange"])) for row in chosen]
        candidates.extend(built)
        per_desk[desk] = {
            "shortlist": len(built),
            "full_screen_pass": sum(1 for row in built if row["passes_full_screen"]),
            "live_open": 0,
        }
    doc = {
        "schema": "ahos.equity_universe.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "registered_at": registry.get("registered_at"),
        "cache_s": CACHE_S,
        "exchanges": exchanges,
        "candidates_per_desk": per_desk,
        "candidates": candidates,
        "live_names_added": 0,
        "fresh_closes": 0,
        "pass_stats": False,
        "red_team": "NOT_SURVIVED",
        "applied_to_live": False,
        "reasons": ["SPREAD_UNKNOWN_ON_SCANNER", "NO_FAMILY_VOTES", "NO_FRESH_CLOSES"],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return doc


def fetch_intraday_bars(symbols: list[str], *, timeout: float = 6.0) -> dict[str, dict[str, Any]]:
    """One free Yahoo chart read per symbol. A failure stays an empty bar."""
    import urllib.error
    import urllib.request

    out: dict[str, dict[str, Any]] = {}
    for symbol in symbols:
        yahoo = yahoo_symbol(symbol)
        url = (
            "https://query1.finance.yahoo.com/v8/finance/chart/"
            + urllib.request.quote(yahoo)
            + "?range=1d&interval=5m"
        )
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            result = ((payload.get("chart") or {}).get("result") or [None])[0] or {}
            quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
            closes = [float(v) for v in (quote.get("close") or []) if isinstance(v, (int, float))]
            highs = [float(v) for v in (quote.get("high") or []) if isinstance(v, (int, float))]
            lows = [float(v) for v in (quote.get("low") or []) if isinstance(v, (int, float))]
            out[symbol] = {
                "high": highs[-1] if highs else None,
                "low": lows[-1] if lows else None,
                "close": closes[-1] if closes else None,
                "closes": closes,
            }
        except (OSError, urllib.error.URLError, json.JSONDecodeError, TimeoutError, ValueError, IndexError):
            out[symbol] = {}
    return out


def yahoo_symbol(scanner_symbol: str) -> str:
    text = str(scanner_symbol or "")
    if ":" in text:
        text = text.split(":", 1)[1]
    return text.replace(".", "-")


def shadow_shortlist(root: Path, bars: dict[str, dict[str, float]]) -> dict[str, Any]:
    """Attach bar-range spread estimates and run close-only strategies. No live open."""
    from architecture.strategies.library import SPECS
    from architecture.strategies.signals import shadow_round_trips, sign_on_closes

    path = Path(root) / OUT_REL
    doc = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    candidates = doc.get("candidates") if isinstance(doc.get("candidates"), list) else []
    rows = []
    for cand in candidates:
        if not isinstance(cand, dict):
            continue
        symbol = str(cand.get("symbol") or "")
        bar = bars.get(symbol) or bars.get(yahoo_symbol(symbol)) or {}
        estimate = estimate_spread_pct(bar.get("high"), bar.get("low"), bar.get("close"))
        if cand.get("spread_status") != "KNOWN" and estimate is not None:
            cand["spread_pct"] = estimate
            cand["spread_status"] = "ESTIMATE"
            cand["spread_source"] = "intraday_bar"
        elif cand.get("spread_status") != "KNOWN":
            cand["spread_status"] = "UNKNOWN"
            cand["spread_source"] = "NO_BAR"
        closes = bar.get("closes") if isinstance(bar.get("closes"), list) else []
        fired = 0
        for spec in SPECS:
            signs = sign_on_closes(spec["id"], [float(v) for v in closes]) if closes else None
            if signs is None:
                continue
            trips = shadow_round_trips(
                signs, [float(v) for v in closes],
                float(spec["cost"]["fee_per_side"]), float(spec["cost"]["slippage_per_side"]),
            )
            if trips:
                fired += 1
        cand["shadow_strategies_with_closes"] = fired
        cand["live_open"] = False
        rows.append({
            "symbol": symbol,
            "desk": cand.get("desk"),
            "spread_status": cand.get("spread_status"),
            "spread_pct": cand.get("spread_pct"),
            "spread_source": cand.get("spread_source"),
            "shadow_strategies_with_closes": fired,
            "live_open": False,
        })
    if path.is_file():
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    receipt = {
        "schema": "ahos.equity_shadow_paths.v1",
        "paper_only": True,
        "candidates": len(rows),
        "estimated": sum(1 for row in rows if row["spread_status"] == "ESTIMATE"),
        "rows": rows,
        "live_open": 0,
        "applied_to_live": False,
    }
    out = Path(root) / "reports" / "grok" / "PAPER" / "equity_shadow_paths.json"
    out.write_text(json.dumps(receipt, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return receipt


def estimate_spread_pct(high: float, low: float, close: float) -> float | None:
    """Bar range as a spread stand-in. It is an estimate, not a quote."""
    if not all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in (high, low, close)):
        return None
    if close <= 0 or high < low:
        return None
    return round((high - low) / float(close) * 100.0, 4)
