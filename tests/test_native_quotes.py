"""Exchange-native prices win only when the second print agrees. Yahoo stays otherwise."""
from __future__ import annotations

import json

from architecture.markets.native_quotes import (
    apply_native_quotes,
    feed_status,
    overlay_native_witnesses,
    parse_alpaca_snapshots,
    parse_binance_ticker,
    parse_oanda_candles,
    redact,
    resolve_native,
)
from architecture.markets.paper_trade_gates import MIN_AGREEING_FAMILIES, MIN_EXPECTED_PROFIT_TO_FEE_RATIO


def _yahoo(price: float, source: str = "yahoo_finance:BTC-USD") -> dict:
    return {"price": price, "source": source, "ohlcv_5m": [[price, price, price, price, 1.0]], "latency_ms": 40}


def test_two_exchange_prints_must_agree_before_the_native_fill() -> None:
    agreed = resolve_native(
        {"price": 100.0, "source": "binance:BTCUSDT", "latency_ms": 20, "transport": "rest"},
        {"price": 100.2, "source": "okx:BTC-USDT", "latency_ms": 35},
        _yahoo(101.0),
        tol=0.004,
    )
    assert agreed["source"] == "binance:BTCUSDT"
    assert agreed["source_role"] == "native"
    assert agreed["native_verdict"] == "AGREE"
    assert agreed["native_witness"]["source"] == "okx:BTC-USDT"
    assert agreed["latency_ms"] == 20
    conflict = resolve_native(
        {"price": 100.0, "source": "binance:BTCUSDT"},
        {"price": 102.0, "source": "okx:BTC-USDT"},
        _yahoo(100.4),
        tol=0.004,
    )
    assert conflict["source"].startswith("yahoo")
    assert conflict["source_role"] == "yahoo_fallback"
    assert conflict["native_verdict"] == "CONFLICT"
    assert "native_witness" not in conflict
    alone = resolve_native(None, None, _yahoo(50.0), tol=0.004)
    assert alone["source_role"] == "yahoo"
    assert MIN_AGREEING_FAMILIES == 2
    assert MIN_EXPECTED_PROFIT_TO_FEE_RATIO == 2.0


def test_missing_keys_keep_yahoo_and_indexes_are_not_iex() -> None:
    status = feed_status({})
    assert status == {"alpaca": "ABSENT_NO_KEY", "oanda": "ABSENT_NO_KEY", "crypto": "PUBLIC_REST"}
    quotes = {
        "BTC": {"price": 10.0, "source": "coingecko"},
        "BTC_YAHOO": _yahoo(10.01),
        "QQQ": _yahoo(490.0, "yahoo_finance:QQQ"),
        "SPX": _yahoo(5000.0, "yahoo_finance:^GSPC"),
        "NDX": _yahoo(20000.0, "yahoo_finance:^NDX"),
        "EURUSD": _yahoo(1.1, "yahoo_finance:EURUSD=X"),
        "XAU": _yahoo(2300.0, "yahoo_finance:GC=F"),
        "DAX": _yahoo(18000.0, "yahoo_finance:^GDAXI"),
        "N225": _yahoo(38000.0, "yahoo_finance:^N225"),
        "HSI": _yahoo(20000.0, "yahoo_finance:^HSI"),
    }
    spot = {"BTC": {
        "binance": {"price": 10.0, "source": "binance:BTCUSDT", "latency_ms": 12, "ohlcv_5m": []},
        "okx": {"price": 10.01, "source": "okx:BTC-USDT", "latency_ms": 18},
    }}
    apply_native_quotes(quotes, spot=spot, status=status)
    assert quotes["BTC"]["source"] == "binance:BTCUSDT"
    assert quotes["BTC"]["ohlcv_5m"]
    assert quotes["QQQ"]["native_note"] == "ABSENT_NO_KEY"
    assert quotes["QQQ"]["source"].startswith("yahoo")
    assert quotes["NDX"]["native_note"] == "ABSENT_NO_KEY"
    assert quotes["SPX"]["source"].startswith("yahoo")
    assert quotes["EURUSD"]["native_note"] == "ABSENT_NO_KEY"
    assert quotes["XAU"]["source"].startswith("yahoo")
    assert quotes["DAX"]["native_note"] == "YAHOO_PLUS_SECOND_WITNESS"
    assert quotes["N225"]["price"] == 38000.0
    assert quotes["HSI"]["source"].startswith("yahoo")


def test_configured_iex_and_oanda_replace_yahoo_only_when_they_agree() -> None:
    token = "unit-test-token"
    status = feed_status({"APCA_API_KEY_ID": "id", "APCA_API_SECRET_KEY": token, "OANDA_PRACTICE_TOKEN": token})
    assert status["alpaca"] == "CONFIGURED" and status["oanda"] == "CONFIGURED"
    assert token not in json.dumps(status)
    iex = parse_alpaca_snapshots({"QQQ": {"latestTrade": {"p": 490.2, "t": "2026-10-30T14:30:00.123Z"}}}, latency_ms=15)
    oanda = {
        "EURUSD": parse_oanda_candles(
            {"candles": [{"time": "2026-10-30T14:30:00.000000000Z", "mid": {"o": "1.1", "h": "1.11", "l": "1.09", "c": "1.1002"}}]},
            inst="EUR_USD", latency_ms=22,
        )
    }
    quotes = {
        "QQQ": _yahoo(490.0, "yahoo_finance:QQQ"),
        "NDX": _yahoo(20000.0, "yahoo_finance:^NDX"),
        "EURUSD": _yahoo(1.1, "yahoo_finance:EURUSD=X"),
        "DAX": _yahoo(18000.0, "yahoo_finance:^GDAXI"),
    }
    apply_native_quotes(quotes, iex=iex, oanda=oanda, status=status)
    assert quotes["QQQ"]["source"] == "alpaca:iex:QQQ"
    assert quotes["QQQ"]["native_witness"]["source"].startswith("yahoo")
    assert quotes["QQQ"]["latency_ms"] == 15
    assert quotes["NDX"]["native_note"] == "IEX_DOES_NOT_PRINT_INDEX"
    assert quotes["NDX"]["source"].startswith("yahoo")
    assert quotes["EURUSD"]["source"] == "oanda:EUR_USD"
    assert quotes["DAX"]["source"].startswith("yahoo")
    blob = json.dumps(quotes)
    assert token not in blob
    assert redact(f"Bearer {token} failed", [token]) == "Bearer [redacted] failed"
    second = overlay_native_witnesses({"QQQ": {"price": 1.0, "source": "kraken"}}, quotes, ["QQQ", "DAX"])
    assert second["QQQ"]["source"].startswith("yahoo")
    assert "DAX" not in second


def test_parsers_read_public_payloads() -> None:
    q = parse_binance_ticker({"symbol": "BTCUSDT", "lastPrice": "100.5", "closeTime": 1760000000000}, latency_ms=9)
    assert q["price"] == 100.5 and q["source"] == "binance:BTCUSDT" and q["latency_ms"] == 9
    assert q["market_time"].endswith("Z") and len(q["market_time"]) == 20
