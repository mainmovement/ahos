"""M13.1-M13.6 & M19 Multi-Market Paper Desks (Gold, Oil, Crypto, US/EU/Asia Equities, Forex).
Enforces the Two-Source Witness Law across all desks:
- VERIFIED when >=2 independent sources agree within tolerance (default 0.5% spread)
- UNRESOLVED when <2 valid sources are available
- CONFLICT when >=2 sources disagree beyond tolerance
Strictly PAPER_ONLY = True with zero live order execution paths.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from architecture.execution.gateway import PaperOrder
from architecture.markets.margin import assess
from architecture.markets.oms import route

PAPER_ONLY: bool = True
LIVE_TRADING: bool = False

VERIFIED = "VERIFIED"
UNRESOLVED = "UNRESOLVED"
CONFLICT = "CONFLICT"


@dataclass(frozen=True, slots=True)
class SourceQuote:
    source: str
    symbol: str
    price: float
    timestamp_iso: str = "2026-10-23T18:00:00Z"


@dataclass(frozen=True, slots=True)
class WitnessVerdict:
    desk: str
    symbol: str
    state: str
    consensus_price: float | None
    spread_pct: float | None
    spread_bps: float | None
    sources: tuple[str, ...]
    reason: str
    paper_only: bool = True
    live: bool = False


@dataclass(frozen=True, slots=True)
class DeskPaperCycle:
    desk: str
    symbol: str
    mission_id: str
    witness: WitnessVerdict
    oms_state: str
    margin_event: str
    notional_usd: float
    bankroll_usd: float
    paper_only: bool = True
    live: bool = False


DESK_SPECS: dict[str, dict[str, Any]] = {
    "GOLD": {
        "mission_id": "M13-GOLD-SOAK",
        "symbols": ("XAUUSD",),
        "primary_sources": ("goldapi_spot", "yahoo_gc_futures"),
        "max_spread_pct": 0.5,
        "paper_notional_usd": 100.0,
        "paper_bankroll_usd": 10_000.0,
    },
    "OIL": {
        "mission_id": "M13.1-OIL-PAPER",
        "symbols": ("WTI", "BRENT"),
        "primary_sources": ("eia_spot", "yahoo_cl_futures"),
        "max_spread_pct": 0.6,
        "paper_notional_usd": 100.0,
        "paper_bankroll_usd": 10_000.0,
    },
    "CRYPTO": {
        "mission_id": "M13.3-CRYPTO-PAPER",
        "symbols": ("BTCUSDT", "ETHUSDT"),
        "primary_sources": ("binance_public", "coingecko_public"),
        "max_spread_pct": 0.5,
        "paper_notional_usd": 150.0,
        "paper_bankroll_usd": 10_000.0,
    },
    "US_EQUITIES": {
        "mission_id": "M13.4-US-EQ-PAPER",
        "symbols": ("SPY", "QQQ", "NVDA"),
        "primary_sources": ("stooq_us", "yahoo_us"),
        "max_spread_pct": 0.35,
        "paper_notional_usd": 200.0,
        "paper_bankroll_usd": 10_000.0,
    },
    "EU_EQUITIES": {
        "mission_id": "M13.5-EU-EQ-PAPER",
        "symbols": ("EXW1.DE", "DAX"),
        "primary_sources": ("stooq_eu", "yahoo_eu"),
        "max_spread_pct": 0.4,
        "paper_notional_usd": 150.0,
        "paper_bankroll_usd": 10_000.0,
    },
    "ASIA_EQUITIES": {
        "mission_id": "M13.6-ASIA-EQ-PAPER",
        "symbols": ("N225", "HSI"),
        "primary_sources": ("stooq_asia", "yahoo_asia"),
        "max_spread_pct": 0.45,
        "paper_notional_usd": 150.0,
        "paper_bankroll_usd": 10_000.0,
    },
    "FOREX": {
        "mission_id": "M19-FOREX-PAPER",
        "symbols": ("EURUSD", "USDJPY"),
        "primary_sources": ("ecb_ref", "fred_stooq_fx"),
        "max_spread_pct": 0.25,
        "paper_notional_usd": 200.0,
        "paper_bankroll_usd": 10_000.0,
    },
}


def verify_two_source_witness(
    desk: str,
    symbol: str,
    quotes: Sequence[SourceQuote | Mapping[str, Any]],
    *,
    max_spread_pct: float | None = None,
) -> WitnessVerdict:
    """Evaluate quotes under the strict Two-Source Witness Law."""
    desk_key = desk.strip().upper()
    spec = DESK_SPECS.get(desk_key, {})
    tol = float(max_spread_pct if max_spread_pct is not None else spec.get("max_spread_pct", 0.5))

    by_source: dict[str, float] = {}
    for q in quotes:
        if isinstance(q, SourceQuote):
            src = q.source.strip().lower()
            price = float(q.price)
        else:
            src = str(q.get("source") or "").strip().lower()
            raw_p = q.get("price")
            price = float(raw_p) if raw_p is not None else -1.0
        if src and price > 0:
            by_source[src] = price

    sources = tuple(sorted(by_source.keys()))
    if len(sources) < 2:
        return WitnessVerdict(
            desk=desk_key,
            symbol=symbol,
            state=UNRESOLVED,
            consensus_price=None,
            spread_pct=None,
            spread_bps=None,
            sources=sources,
            reason="fewer_than_two_independent_sources",
            paper_only=True,
            live=False,
        )

    prices = [by_source[s] for s in sources]
    lo, hi = min(prices), max(prices)
    mid = sum(prices) / len(prices)
    spread_pct = ((hi - lo) / mid) * 100.0 if mid > 0 else 999.0
    spread_bps = spread_pct * 100.0

    if spread_pct > tol:
        return WitnessVerdict(
            desk=desk_key,
            symbol=symbol,
            state=CONFLICT,
            consensus_price=None,
            spread_pct=round(spread_pct, 4),
            spread_bps=round(spread_bps, 2),
            sources=sources,
            reason=f"spread_{spread_pct:.4f}pct_exceeds_tolerance_{tol:.4f}pct",
            paper_only=True,
            live=False,
        )

    return WitnessVerdict(
        desk=desk_key,
        symbol=symbol,
        state=VERIFIED,
        consensus_price=round(mid, 4),
        spread_pct=round(spread_pct, 4),
        spread_bps=round(spread_bps, 2),
        sources=sources,
        reason="two_source_witness_verified",
        paper_only=True,
        live=False,
    )


def evaluate_desk_paper_cycle(
    desk: str,
    symbol: str,
    quotes: Sequence[SourceQuote | Mapping[str, Any]],
    *,
    side: str = "buy",
    max_spread_pct: float | None = None,
) -> DeskPaperCycle:
    """Run one deterministic paper evaluation cycle on a desk without touching the live gold soak."""
    desk_key = desk.strip().upper()
    spec = DESK_SPECS.get(desk_key, {})
    mission_id = str(spec.get("mission_id", f"M19-{desk_key}-PAPER"))
    notional = float(spec.get("paper_notional_usd", 100.0))
    bankroll = float(spec.get("paper_bankroll_usd", 10_000.0))

    witness = verify_two_source_witness(desk_key, symbol, quotes, max_spread_pct=max_spread_pct)
    oms_state = "NO_ENTRY_WITNESS_GATE"
    if witness.state == VERIFIED:
        order = PaperOrder(market=f"{desk_key}:{symbol}", side=side, notional_usd=notional, live=False)
        oms_res = route(order, "ELIGIBLE")
        oms_state = oms_res.state if oms_res.state == "ACCEPTED_PAPER" else "REJECTED"

    margin_res = assess(equity_usd=bankroll, notional_usd=notional)
    return DeskPaperCycle(
        desk=desk_key,
        symbol=symbol,
        mission_id=mission_id,
        witness=witness,
        oms_state=oms_state,
        margin_event=margin_res.event,
        notional_usd=notional,
        bankroll_usd=bankroll,
        paper_only=True,
        live=False,
    )


def default_multi_market_fixtures() -> list[dict[str, Any]]:
    """Canonical two-source fixtures across all 7 multi-market desks for deterministic paper evaluation."""
    return [
        {
            "desk": "GOLD",
            "symbol": "XAUUSD",
            "quotes": [
                {"source": "goldapi_spot", "price": 2748.40},
                {"source": "yahoo_gc_futures", "price": 2749.10},
            ],
        },
        {
            "desk": "OIL",
            "symbol": "WTI",
            "quotes": [
                {"source": "eia_spot", "price": 71.35},
                {"source": "yahoo_cl_futures", "price": 71.45},
            ],
        },
        {
            "desk": "CRYPTO",
            "symbol": "BTCUSDT",
            "quotes": [
                {"source": "binance_public", "price": 68420.00},
                {"source": "coingecko_public", "price": 68465.00},
            ],
        },
        {
            "desk": "CRYPTO",
            "symbol": "ETHUSDT",
            "quotes": [
                {"source": "binance_public", "price": 2645.50},
                {"source": "coingecko_public", "price": 2648.00},
            ],
        },
        {
            "desk": "US_EQUITIES",
            "symbol": "SPY",
            "quotes": [
                {"source": "stooq_us", "price": 584.20},
                {"source": "yahoo_us", "price": 584.35},
            ],
        },
        {
            "desk": "US_EQUITIES",
            "symbol": "QQQ",
            "quotes": [
                {"source": "stooq_us", "price": 496.80},
                {"source": "yahoo_us", "price": 497.00},
            ],
        },
        {
            "desk": "US_EQUITIES",
            "symbol": "NVDA",
            "quotes": [
                {"source": "stooq_us", "price": 141.50},
                {"source": "yahoo_us", "price": 141.62},
            ],
        },
        {
            "desk": "EU_EQUITIES",
            "symbol": "EXW1.DE",
            "quotes": [
                {"source": "stooq_eu", "price": 50.82},
                {"source": "yahoo_eu", "price": 50.86},
            ],
        },
        {
            "desk": "EU_EQUITIES",
            "symbol": "DAX",
            "quotes": [
                {"source": "stooq_eu", "price": 19480.0},
                {"source": "yahoo_eu", "price": 19492.0},
            ],
        },
        {
            "desk": "ASIA_EQUITIES",
            "symbol": "N225",
            "quotes": [
                {"source": "stooq_asia", "price": 38910.0},
                {"source": "yahoo_asia", "price": 38935.0},
            ],
        },
        {
            "desk": "ASIA_EQUITIES",
            "symbol": "HSI",
            "quotes": [
                {"source": "stooq_asia", "price": 20590.0},
                {"source": "yahoo_asia", "price": 20612.0},
            ],
        },
        {
            "desk": "FOREX",
            "symbol": "EURUSD",
            "quotes": [
                {"source": "ecb_ref", "price": 1.0842},
                {"source": "fred_stooq_fx", "price": 1.0845},
            ],
        },
        {
            "desk": "FOREX",
            "symbol": "USDJPY",
            "quotes": [
                {"source": "ecb_ref", "price": 151.82},
                {"source": "fred_stooq_fx", "price": 151.88},
            ],
        },
    ]


def evaluate_all_desks(fixtures: Sequence[Mapping[str, Any]] | None = None) -> list[DeskPaperCycle]:
    rows = fixtures if fixtures is not None else default_multi_market_fixtures()
    results: list[DeskPaperCycle] = []
    for row in rows:
        results.append(
            evaluate_desk_paper_cycle(
                desk=str(row["desk"]),
                symbol=str(row["symbol"]),
                quotes=row.get("quotes") or (),
            )
        )
    return results
