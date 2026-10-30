"""Paper listed futures. Separate from the crypto swap book and from the cash books.

Execution price is Yahoo's continuous future. A second free witness must agree.
FDAX is omitted: Yahoo has no free continuous FDAX or FDXS ticker.
Leverage stays 1.0. There is no wallet and no live order.

The roll is a flatten before last trade. Yahoo's continuous series does not
quote both legs of a calendar spread, so this book does not invent a spread fill.
The next contract can open only through the same gates.
"""
from __future__ import annotations

import json
from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from architecture.markets.family_vote_scorecard import OBS_REL
from architecture.markets.weekday_session_gate import holiday_name

DESK = "LISTED_FUTURES"
EQUITY_CAP = 0.10
LEVERAGE_CAP = 1.0
SCORECARD_DAYS = 7
# Pre-registered paper maintenance fraction. Not a broker schedule and not fit to a book.
MAINTENANCE_MARGIN_RATE = 0.05
ROLL_LEAD_DAYS = 5

# Yahoo continuous plus TradingView. Fees match the cash book of the same underlying.
SPECS: dict[str, dict[str, Any]] = {
    "CL": {"yahoo": "CL=F", "root": ("CL", "NYM"), "venue": "CME_GLOBEX", "underlying_desk": "OIL",
           "cftc": ("OIL", "WTI"), "fee": 0.0005, "slip": 0.0004, "tv": "NYMEX:CL1!", "tv_root": "NYMEX:CL"},
    "BZ": {"yahoo": "BZ=F", "root": ("BZ", "NYM"), "venue": "ICE_BRENT", "underlying_desk": "OIL",
           "cftc": ("OIL", "BRENT"), "fee": 0.0005, "slip": 0.0004, "tv": "ICEEUR:BRN1!", "tv_root": "ICEEUR:BRN"},
    "GC": {"yahoo": "GC=F", "root": ("GC", "CMX"), "venue": "CME_GLOBEX", "underlying_desk": "GOLD",
           "cftc": ("GOLD", "XAU"), "fee": 0.0004, "slip": 0.0003, "tv": "COMEX:GC1!", "tv_root": "COMEX:GC"},
    "ES": {"yahoo": "ES=F", "root": ("ES", "CME"), "venue": "CME_GLOBEX", "underlying_desk": "US_EQUITIES",
           "cftc": None, "fee": 0.0003, "slip": 0.0002, "tv": "CME_MINI:ES1!", "tv_root": "CME_MINI:ES",
           "stooq": "es.f"},
    "NQ": {"yahoo": "NQ=F", "root": ("NQ", "CME"), "venue": "CME_GLOBEX", "underlying_desk": "US_EQUITIES",
           "cftc": None, "fee": 0.0003, "slip": 0.0002, "tv": "CME_MINI:NQ1!", "tv_root": "CME_MINI:NQ",
           "stooq": "nq.f"},
    "NKD": {"yahoo": "NKD=F", "root": ("NKD", "CME"), "venue": "CME_GLOBEX", "underlying_desk": "ASIA_EQUITIES",
            "cftc": None, "fee": 0.0004, "slip": 0.0003, "tv": "CME:NKD1!", "tv_root": "CME:NKD",
            "stooq": "nkd.f"},
}
# Cash books already download these Yahoo series. The listed book reuses that print.
CASH_QUOTE = {"CL": "WTI", "BZ": "BRENT", "GC": "XAU"}
OMITTED = {
    "FDAX": "Yahoo has no free continuous FDAX or FDXS ticker. A TradingView print alone is not the execution feed.",
}
PIPELINE = {
    "OIL": "OIL_DESK",
    "GOLD": "GOLD_DESK",
    "US_EQUITIES": "US_EQUITIES_DESK",
    "ASIA_EQUITIES": "ASIA_EQUITIES_DESK",
}


def signal_desk(symbol: str) -> str | None:
    spec = SPECS.get(symbol)
    return None if spec is None else str(spec["underlying_desk"])


def cftc_pair(symbol: str) -> tuple[str, str] | None:
    spec = SPECS.get(symbol)
    pair = None if spec is None else spec.get("cftc")
    if not pair:
        return None
    return str(pair[0]), str(pair[1])


def overlay_cash_witnesses(book: dict[str, Any]) -> None:
    """CL, BZ, and GC share the cash book's second source. ES, NQ, and NKD do not."""
    for listed, cash in CASH_QUOTE.items():
        if listed not in book and cash in book:
            book[listed] = dict(book[cash])


def liquidation_price(side: str, entry: float, leverage: float = LEVERAGE_CAP,
                      mmr: float = MAINTENANCE_MARGIN_RATE) -> float | None:
    """Isolated mark where posted margin minus maintenance is gone. At 1x that is a deep move."""
    if leverage <= 0 or entry <= 0:
        return None
    buf = (1.0 / leverage) - mmr
    if buf <= 0:
        return None
    if side == "LONG":
        return entry * (1.0 - buf)
    if side == "SHORT":
        return entry * (1.0 + buf)
    return None


def simulated_liquidation(side: str, price: float, liq: Any) -> bool:
    if not isinstance(liq, (int, float)) or not isinstance(price, (int, float)):
        return False
    if side == "LONG":
        return price <= float(liq)
    if side == "SHORT":
        return price >= float(liq)
    return False


def scorecard_span_days(root: Path) -> float | None:
    path = Path(root) / OBS_REL
    if not path.is_file():
        return None
    stamps: list[datetime] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            raw = json.loads(line).get("ts")
            dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except (ValueError, TypeError, json.JSONDecodeError):
            continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        stamps.append(dt)
    if len(stamps) < 2:
        return None
    return (max(stamps) - min(stamps)).total_seconds() / 86400.0


def leverage_decision(root: Path, requested: float = 5.0, trades: list[dict[str, Any]] | None = None,
                      unrealized: float = 0.0, stamp: str = "") -> dict[str, Any]:
    """Live rung from the evidence ladder. A scorecard week does not raise it by itself."""
    from architecture.markets.leverage_ladder import live_rung

    decision = live_rung(root, DESK, trades or [], unrealized=unrealized, stamp=stamp)
    decision["applied"] = min(float(decision["applied"]), float(requested))
    decision["requested"] = float(requested)
    decision["equity_cap"] = EQUITY_CAP
    decision["maintenance_margin_rate"] = MAINTENANCE_MARGIN_RATE
    decision["span_days"] = scorecard_span_days(root)
    return decision


def book_notional_cap(equity: float, open_notional: float) -> float:
    return max(0.0, EQUITY_CAP * float(equity) - float(open_notional))


def _prev_month(year: int, month: int) -> tuple[int, int]:
    return (year - 1, 12) if month == 1 else (year, month - 1)


def _is_business_day(d: date, venue: str) -> bool:
    return d.weekday() < 5 and holiday_name(venue, d) is None


def _subtract_business_days(anchor: date, n: int, venue: str) -> date:
    d = anchor
    left = n
    while left:
        d -= timedelta(days=1)
        if _is_business_day(d, venue):
            left -= 1
    return d


def _on_or_before_business_day(d: date, venue: str) -> date:
    while not _is_business_day(d, venue):
        d -= timedelta(days=1)
    return d


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    first = date(year, month, 1)
    shift = (weekday - first.weekday()) % 7
    return first + timedelta(days=shift + 7 * (n - 1))


def _nth_last_business_day(year: int, month: int, n: int, venue: str) -> date:
    d = date(year, month, monthrange(year, month)[1])
    seen = 0
    while True:
        if _is_business_day(d, venue):
            seen += 1
            if seen == n:
                return d
        d -= timedelta(days=1)


def last_trade_date(symbol: str, year: int, month: int) -> date | None:
    """Paper last-trade date. Weekends and the modeled exchange holidays are not business days."""
    if symbol in ("ES", "NQ"):
        return _on_or_before_business_day(_nth_weekday(year, month, 4, 3), "CME_GLOBEX")
    if symbol == "NKD":
        return _subtract_business_days(_nth_weekday(year, month, 4, 2), 1, "CME_GLOBEX")
    if symbol == "CL":
        y, m = _prev_month(year, month)
        anchor = date(y, m, 25)
        n = 3 if _is_business_day(anchor, "CME_GLOBEX") else 4
        return _subtract_business_days(anchor, n, "CME_GLOBEX")
    if symbol == "BZ":
        y, m = _prev_month(*_prev_month(year, month))
        return _on_or_before_business_day(date(y, m, monthrange(y, m)[1]), "ICE_BRENT")
    if symbol == "GC":
        return _nth_last_business_day(year, month, 3, "CME_GLOBEX")
    return None


def _candidate_months(now_ts: float, n: int = 6) -> list[tuple[int, int]]:
    d = datetime.fromtimestamp(now_ts, tz=timezone.utc)
    out: list[tuple[int, int]] = []
    year, month = d.year, d.month
    for _ in range(n):
        out.append((year, month))
        month += 1
        if month > 12:
            year, month = year + 1, 1
    return out


def near_contract_month(symbol: str, continuous: dict[str, Any], *, fetch: Any,
                        now_ts: float, tol: float) -> dict[str, Any] | None:
    """Pick the Yahoo contract that matches the continuous print.

    The match is Yahoo against itself. A unique contract inside ``tol`` and 60
    seconds is the month. Two matches, or none, stay unknown so the book does
    not invent an expiry.
    """
    spec = SPECS.get(symbol)
    price = continuous.get("price")
    mt = continuous.get("_regular_market_time")
    if spec is None or not isinstance(price, (int, float)) or price <= 0 or not isinstance(mt, (int, float)):
        return None
    root, venue = spec["root"]
    months = "FGHJKMNQUVXZ"
    hits: list[dict[str, Any]] = []
    for year, month in _candidate_months(now_ts):
        code = f"{root}{months[month - 1]}{year % 100:02d}.{venue}"
        try:
            data = fetch(code)
            meta = data["chart"]["result"][0]["meta"]
            px = float(meta.get("regularMarketPrice"))
            ts = float(meta.get("regularMarketTime"))
        except (TypeError, ValueError, KeyError, IndexError):
            continue
        if px <= 0 or abs(ts - float(mt)) > 60:
            continue
        if abs(px - float(price)) / float(price) <= tol:
            hits.append({
                "contract_month": f"{year:04d}-{month:02d}",
                "contract_symbol": code,
                "price": px,
                "method": "yahoo_self_near(price within tolerance + regularMarketTime)",
            })
    if len(hits) != 1:
        return None
    return hits[0]


def parse_contract_month(contract_month: Any) -> tuple[int, int] | None:
    if not isinstance(contract_month, str) or len(contract_month) != 7 or contract_month[4] != "-":
        return None
    try:
        year, month = int(contract_month[:4]), int(contract_month[5:])
    except ValueError:
        return None
    if not 1 <= month <= 12:
        return None
    return year, month


def roll_due(symbol: str, contract_month: Any, asof: date) -> bool:
    parsed = parse_contract_month(contract_month)
    if parsed is None:
        return False
    last = last_trade_date(symbol, parsed[0], parsed[1])
    if last is None:
        return False
    return asof >= last - timedelta(days=ROLL_LEAD_DAYS)


def coverage_rows() -> list[dict[str, Any]]:
    from architecture.markets.paper_trade_gates import INDEPENDENT_VOTE_FAMILIES

    rows: list[dict[str, Any]] = []
    for family, members in INDEPENDENT_VOTE_FAMILIES.items():
        base: dict[str, Any] = {"desk": DESK, "family": family, "members": list(members)}
        if family == "research":
            rows.append({
                **base,
                "status": "ADVISORY_VOTE",
                "composite_weight": "0 unless PASS_STATS+SURVIVED_RED_TEAM",
                "source": "same pipeline as the underlying cash desk",
                "pipeline_by_symbol": {sym: PIPELINE[str(spec["underlying_desk"])] for sym, spec in SPECS.items()},
            })
        elif family == "whales":
            rows.append({
                **base,
                "status": "CFTC_COT",
                "composite_weight": 0,
                "symbols_on_cftc": {sym: list(spec["cftc"]) for sym, spec in SPECS.items() if spec.get("cftc")},
                "absent_by_design": [sym for sym, spec in SPECS.items() if not spec.get("cftc")],
                "omitted_no_yahoo_continuous": OMITTED,
                "reason": "ES, NQ, and NKD have no verified free public positioning file. Oil and gold use the existing CFTC contract.",
            })
        else:
            rows.append({
                **base,
                "status": "IN_CYCLE",
                "source": "same family as the underlying cash desk",
                "underlying_desk": {sym: spec["underlying_desk"] for sym, spec in SPECS.items()},
            })
    return rows
