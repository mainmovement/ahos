"""Public primaries fall back to Yahoo, and a witness gap above 0.5% skips the symbol."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from architecture.markets import paper_trader as pt
from architecture.markets.cnbc_quotes import SYMBOLS as CNBC_SYMBOLS
from architecture.markets.paper_trader import INSTRUMENTS
from architecture.markets.quote_router import independent_witness, route_public_quotes


def _yahoo(price, source="yahoo:test"):
    return {"price": price, "source": source, "market_time": "2026-10-29T20:00:00Z", "ohlcv_5m": [[1, 1, 1, 1, 1]]}


def _empty():
    return {}


def test_cnbc_replaces_yahoo_and_a_failure_keeps_yahoo() -> None:
    asof = datetime(2026, 10, 29, 20, 33, tzinfo=timezone.utc).timestamp()
    quotes = {"SPX": _yahoo(7720.0), "NVDA": _yahoo(208.0, "yahoo:NVDA")}
    route_public_quotes(quotes, asof=asof, tv=_empty, hl=_empty, gold=_empty, fx=_empty, cnbc=lambda: {
        "SPX": {"price": 7720.39, "source": "cnbc:.SPX", "source_timestamp": "2026-10-29T16:32:47.000-0400",
                "latency_ms": 40, "delay_flag": "realtime", "delay_s": 0},
    })
    assert quotes["SPX"]["source"] == "cnbc:.SPX"
    assert quotes["SPX"]["market_time"] == "2026-10-29T20:32:47Z"
    assert quotes["SPX"]["source_timestamp"] == "2026-10-29T20:32:47Z"
    assert quotes["SPX"]["latency_ms"] == 40
    assert quotes["SPX"]["delay_flag"] == "realtime"
    assert quotes["SPX"]["yahoo_price"] == 7720.0
    assert quotes["SPX"]["ohlcv_5m"]
    assert quotes["SPX"]["divergence_skip"] is False
    assert quotes["NVDA"]["source"] == "yahoo:NVDA"
    assert quotes["NVDA"]["source_role"] == "yahoo_fallback"
    assert "BRENT" not in CNBC_SYMBOLS


def test_perp_basis_uses_the_future_and_a_wide_gap_skips() -> None:
    asof = datetime(2026, 10, 29, 20, 33, tzinfo=timezone.utc).timestamp()
    quotes = {"SPX": _yahoo(7720.0), "ES": _yahoo(7676.0)}
    route_public_quotes(quotes, asof=asof, cnbc=lambda: {
        "SPX": {"price": 7720.0, "source": "cnbc:.SPX", "delay_flag": "realtime", "delay_s": 0, "latency_ms": 5},
    }, tv=lambda: {
        "ES": {"price": 7676.0, "source": "tradingview:CME_MINI:ES1!", "delay_flag": "delayed_600s", "delay_s": 600, "latency_ms": 8},
    }, hl=lambda: {
        "SPX": {"price": 7647.25, "source": "hyperliquid:xyz:SP500", "basis_future": "ES"},
    }, gold=_empty, fx=_empty)
    assert quotes["SPX"]["divergence_skip"] is False
    assert quotes["SPX"]["witness_deviation_pct"] < 0.5
    assert quotes["ES"]["delay_flag"] == "delayed_600s"

    wide = {"SPX": _yahoo(7720.0), "ES": _yahoo(7676.0)}
    route_public_quotes(wide, asof=asof, cnbc=lambda: {
        "SPX": {"price": 7720.0, "source": "cnbc:.SPX", "delay_flag": "realtime", "delay_s": 0},
    }, tv=lambda: {
        "ES": {"price": 7676.0, "source": "tradingview:CME_MINI:ES1!", "delay_flag": "delayed_600s", "delay_s": 600},
    }, hl=lambda: {
        "SPX": {"price": 7500.0, "source": "hyperliquid:xyz:SP500", "basis_future": "ES"},
    }, gold=_empty, fx=_empty)
    assert wide["SPX"]["divergence_skip"] is True
    assert wide["SPX"]["witness_deviation_pct"] > 0.5


def test_frankfurter_is_a_daily_check_and_the_fx_skip_uses_the_perp() -> None:
    asof = datetime(2026, 10, 30, 12, 0, tzinfo=timezone.utc).timestamp()
    quotes = {"EURUSD": _yahoo(1.1189), "DAX": _yahoo(26040.0)}
    route_public_quotes(quotes, asof=asof, cnbc=_empty, gold=_empty, tv=lambda: {
        "EURUSD": {"price": 1.1189, "source": "tradingview:FX:EURUSD", "delay_flag": "streaming", "delay_s": 0, "latency_ms": 12},
        "DAX": {"price": 26039.68, "source": "tradingview:XETR:DAX", "delay_flag": "delayed_900s", "delay_s": 900, "latency_ms": 12},
        "FDAX": {"price": 26099.0, "source": "tradingview:EUREX:FDAX1!", "delay_flag": "delayed_900s", "delay_s": 900},
    }, hl=lambda: {
        "EURUSD": {"price": 1.1193, "source": "hyperliquid:xyz:EUR"},
    }, fx=lambda: {"EURUSD": {"price": 1.1130, "source": "frankfurter:USD", "delay_flag": "daily"}})
    assert quotes["EURUSD"]["delay_flag"] == "streaming"
    assert quotes["EURUSD"]["divergence_skip"] is False
    assert quotes["EURUSD"]["witness_deviation_pct"] < 0.5
    assert quotes["EURUSD"]["daily_sanity"] == "PASS"
    assert quotes["EURUSD"]["frankfurter_deviation_pct"] > 0.5
    assert quotes["DAX"]["delay_flag"] == "delayed_900s"
    assert quotes["FDAX"]["omitted_from_book"] is True
    assert "FDAX" not in INSTRUMENTS

    wide = {"EURUSD": _yahoo(1.1189)}
    route_public_quotes(wide, asof=asof, cnbc=_empty, gold=_empty, tv=lambda: {
        "EURUSD": {"price": 1.1189, "source": "tradingview:FX:EURUSD", "delay_flag": "streaming", "delay_s": 0},
    }, hl=lambda: {"EURUSD": {"price": 1.1300, "source": "hyperliquid:xyz:EUR"}},
       fx=lambda: {"EURUSD": {"price": 1.0900, "source": "frankfurter:USD"}})
    assert wide["EURUSD"]["divergence_skip"] is True
    assert wide["EURUSD"]["daily_sanity"] == "FAIL"
    assert 0.5 < wide["EURUSD"]["witness_deviation_pct"] < 2.0
    assert wide["EURUSD"]["frankfurter_deviation_pct"] > wide["EURUSD"]["witness_deviation_pct"]


def test_cash_oil_and_gold_take_the_tradingview_primary() -> None:
    asof = datetime(2026, 10, 30, 12, 0, tzinfo=timezone.utc).timestamp()
    quotes = {
        "WTI": _yahoo(103.2, "yahoo_finance:CL=F"),
        "BRENT": _yahoo(112.1, "yahoo_finance:BZ=F"),
        "GC": _yahoo(4002.0, "yahoo_finance:GC=F"),
    }
    route_public_quotes(quotes, asof=asof, cnbc=_empty, fx=_empty, tv=lambda: {
        "WTI": {"price": 103.16, "source": "tradingview:NYMEX:CL1!", "delay_flag": "delayed_600s", "delay_s": 600},
        "BRENT": {"price": 112.08, "source": "tradingview:ICEEUR:BRN1!", "delay_flag": "delayed_600s", "delay_s": 600},
        "GC": {"price": 4001.5, "source": "tradingview:COMEX:GC1!", "delay_flag": "delayed_600s", "delay_s": 600},
    }, hl=lambda: {
        "CL": {"price": 103.18, "source": "hyperliquid:xyz:CL"},
        "BZ": {"price": 112.10, "source": "hyperliquid:xyz:BRENTOIL"},
        "XAU": {"price": 3998.0, "source": "hyperliquid:xyz:GOLD"},
    }, gold=lambda: {"XAU": {"price": 3996.0, "source": "gold-api:XAU", "delay_flag": "realtime"}})
    assert quotes["WTI"]["source"] == "tradingview:NYMEX:CL1!"
    assert quotes["BRENT"]["source"] == "tradingview:ICEEUR:BRN1!"
    assert quotes["GC"]["source"] == "tradingview:COMEX:GC1!"
    assert quotes["WTI"]["divergence_skip"] is False
    assert quotes["BRENT"]["divergence_skip"] is False
    assert quotes["GC"]["divergence_skip"] is False
    assert any(w["source"] == "gold-api:XAU" for w in quotes["GC"]["witnesses"])
    assert any(w["source"] == "hyperliquid:xyz:CL" for w in quotes["WTI"]["witnesses"])


def test_same_vendor_witness_is_replaced_by_yahoo() -> None:
    quote = {"price": 1.12, "source": "tradingview:FX:EURUSD", "yahoo_witness": {"price": 1.10, "source": "yahoo:EURUSD=X"}}
    got = independent_witness(quote, {"price": 1.12, "source": "tradingview:FX:EURUSD"})
    assert got["source"] == "yahoo:EURUSD=X"
    kept = independent_witness(
        {"price": 100.0, "source": "cnbc:.SPX", "yahoo_witness": {"price": 100.0, "source": "yahoo"}},
        {"price": 100.0, "source": "tradingview:SP:SPX"},
    )
    assert kept["source"] == "tradingview:SP:SPX"
    book = pt.gather_witness(
        {"EURUSD": quote},
        fetch_b=lambda: {"EURUSD": {"price": 1.12, "source": "tradingview:FX:EURUSD"}},
        fetch_c=lambda _syms: {},
    )
    assert book["EURUSD"]["source_b"] == "yahoo:EURUSD=X"
    assert book["EURUSD"]["verdict"] == "CONFLICT"


def test_divergence_skips_the_symbol_and_does_not_mark_an_open_position(tmp_path) -> None:
    moment = datetime(2026, 10, 26, 15, 0, tzinfo=timezone.utc).timestamp()
    stamp = datetime.fromtimestamp(moment, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    state = tmp_path / "reports" / "grok" / "PAPER" / "paper_positions.json"
    state.parent.mkdir(parents=True)
    state.write_text(json.dumps({"positions": {"EURUSD": {
        "side": "LONG", "entry_price": 1.1, "qty": 1.0, "entry_fee_usd": 0.0,
    }}, "brain": {}}), encoding="utf-8")
    fetch = lambda: {"quotes": {"EURUSD": {
        "price": 1.1189, "source": "tradingview:FX:EURUSD", "source_role": "primary",
        "market_time": stamp, "source_timestamp": stamp, "latency_ms": 12, "delay_flag": "streaming",
        "witness_deviation_pct": 0.53, "divergence_skip": True, "ohlcv_5m": [[1, 1, 1, 1, 1]],
    }}}
    pt.run_cycle(tmp_path, fetch=fetch, fetch_b=lambda: {"EURUSD": {"price": 1.1189, "source": "B"}},
                 signals_fn=lambda s, d, q: [], now=lambda: moment, use_ledger=False)
    rows = [json.loads(line) for line in (tmp_path / "reports/grok/PAPER/paper_trades.jsonl").read_text(encoding="utf-8").splitlines()]
    skipped = [r for r in rows if r.get("symbol") == "EURUSD" and r.get("reason") == "DIVERGENCE"]
    assert skipped and skipped[0]["delay_flag"] == "streaming"
    assert skipped[0]["witness_deviation_pct"] == 0.53
    assert skipped[0]["quote_latency_ms"] == 12
    assert skipped[0]["source_timestamp"] == stamp
    assert not any(r.get("symbol") == "EURUSD" and r.get("event") in ("OPEN", "CLOSE") for r in rows)
    kept = json.loads(state.read_text(encoding="utf-8"))["positions"]["EURUSD"]
    assert kept["side"] == "LONG"
