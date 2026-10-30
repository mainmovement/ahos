"""Breadth is advisory. One venue, or a split, does not produce a sign."""
from datetime import datetime, timezone

from architecture.markets import signal_brain as sb
from architecture.markets.crypto_breadth import advisory_signal, build_breadth_snapshot, load_cycle_snapshot, lock_shadow_weight
from architecture.markets.family_coverage import family_coverage
from architecture.markets.family_vote_scorecard import build_weekly_family_scorecard, record_family_votes
from architecture.markets.paper_trade_gates import independent_vote_gate


def test_two_venues_agree_and_a_split_does_not_score() -> None:
    binance = [
        {"symbol": "BTCUSDT", "priceChangePercent": "4", "quoteVolume": "100"},
        {"symbol": "ETHUSDT", "priceChangePercent": "2", "quoteVolume": "50"},
        {"symbol": "USDCUSDT", "priceChangePercent": "0.01", "quoteVolume": "9000"},
        {"symbol": "BTCUPUSDT", "priceChangePercent": "20", "quoteVolume": "10"},
    ]
    okx = {"data": [
        {"instType": "SPOT", "instId": "BTC-USDT", "last": "104", "open24h": "100", "volCcy24h": "80"},
        {"instType": "SPOT", "instId": "ETH-USDT", "last": "98", "open24h": "100", "volCcy24h": "20"},
    ]}
    cg = [
        {"symbol": "btc", "total_volume": 70, "price_change_percentage_1h_in_currency": 1.0,
         "price_change_percentage_24h_in_currency": 3.0, "price_change_percentage_7d_in_currency": -2.0},
        {"symbol": "eth", "total_volume": 30, "price_change_percentage_1h_in_currency": -0.5,
         "price_change_percentage_24h_in_currency": 1.0, "price_change_percentage_7d_in_currency": 4.0},
    ]
    snap = build_breadth_snapshot(binance=binance, okx=okx, coingecko=cg)
    assert snap["agreement"] == "agree"
    assert snap["advisory_score"] > 0
    assert snap["composite_weight"] == 0.0
    assert snap["venues"]["binance"]["n"] == 2
    assert snap["venues"]["coingecko"]["1h"]["n"] == 2
    assert snap["venues"]["coingecko"]["7d"]["n"] == 2
    assert snap["dropped_sources"]["dexscreener"] == "HTTP 403"
    signal = advisory_signal(snap)
    assert signal["available"] is False
    assert signal["evidence"]["advisory_vote_score"] == snap["advisory_score"]

    split = build_breadth_snapshot(
        binance=[{"symbol": "BTCUSDT", "priceChangePercent": "5", "quoteVolume": "10"}],
        okx={"data": [{"instType": "SPOT", "instId": "BTC-USDT", "last": "90", "open24h": "100", "volCcy24h": "10"}]},
    )
    assert split["advisory_score"] is None
    assert split["agreement"] == "conflict"


def test_a_volume_spike_is_logged_and_not_a_score() -> None:
    rows = [
        {"symbol": "BTCUSDT", "priceChangePercent": "1", "quoteVolume": "10"},
        {"symbol": "ETHUSDT", "priceChangePercent": "1", "quoteVolume": "10"},
        {"symbol": "SOLUSDT", "priceChangePercent": "30", "quoteVolume": "100"},
    ]
    snap = build_breadth_snapshot(binance=rows)
    movers = snap["venues"]["binance"]["top_movers"]
    assert movers and movers[0]["symbol"] == "SOL"
    assert snap["advisory_score"] is None


def test_shadow_breadth_does_not_complete_the_entry_gate(tmp_path) -> None:
    breadth = advisory_signal(build_breadth_snapshot(
        binance=[{"symbol": "BTCUSDT", "priceChangePercent": "5", "quoteVolume": "10"}],
        okx={"data": [{"instType": "SPOT", "instId": "BTC-USDT", "last": "105", "open24h": "100", "volCcy24h": "10"}]},
    ))
    assert breadth["evidence"]["advisory_vote_score"] > 0
    news = {"name": "news", "score": -0.4, "available": True}
    candles = {"name": "candles", "score": 0.3, "available": True}
    ok, audit = independent_vote_gate([news, candles, breadth], "LONG")
    assert ok is False
    assert audit["agreeing_families"] == 1
    assert "crypto_breadth" not in audit["families_present"]
    weights = {"news": 0.09, "crypto_breadth": 0.5}
    locked = lock_shadow_weight(dict(weights))
    base = [{"name": "news", "score": 0.4, "available": True}]
    turned_on = {**breadth, "available": True, "score": 1.0}
    assert sb.combine(base + [turned_on], locked)["composite"] == sb.combine(base, locked)["composite"]
    record_family_votes(tmp_path, ts="2026-10-26T00:00:00Z", symbol="BTC", desk="CRYPTO", price=100.0, sigs=[breadth])
    record_family_votes(tmp_path, ts="2026-10-26T04:10:00Z", symbol="BTC", desk="CRYPTO", price=110.0, sigs=[breadth])
    card = build_weekly_family_scorecard(tmp_path, now=datetime(2026, 10, 27, tzinfo=timezone.utc))
    assert card["families"]["crypto_breadth"]["4h"]["hits"] == 1
    assert card["composite_weight"] == 0.0
    rows = {(row["desk"], row["family"]): row for row in family_coverage()["rows"]}
    assert rows[("CRYPTO", "crypto_breadth")]["counts_toward_entry_gate"] is False
    assert rows[("PB_TOKEN", "crypto_breadth")]["status"] == "DISCOVERY_ONLY"


def test_cycle_loader_uses_the_injected_getter_and_logs_futures() -> None:
    def getter(url: str, source: str):
        if source == "binance_breadth":
            return [{"symbol": "BTCUSDT", "priceChangePercent": "4", "quoteVolume": "10"}], 4
        if source == "okx_breadth":
            return {"data": [{"instType": "SPOT", "instId": "BTC-USDT", "last": "104", "open24h": "100", "volCcy24h": "10"}]}, 5
        if source == "binance_funding_BTC":
            return {"lastFundingRate": "0.0001"}, 1
        if source == "okx_funding_BTC":
            return {"data": [{"fundingRate": "0.0002"}]}, 1
        return None, 0

    pack = load_cycle_snapshot(getter=getter)
    assert pack["signal"]["available"] is False
    assert pack["log"]["agreement"] == "agree"
    assert pack["log"]["futures"]["symbols"]["BTC"]["funding_agreement"] == "agree"
    assert pack["log"]["composite_weight"] == 0.0
    assert "fapi.binance.com" not in str(pack["log"].get("dropped_sources"))


def test_one_venue_stays_unscored() -> None:
    snap = build_breadth_snapshot(binance=[{"symbol": "BTCUSDT", "priceChangePercent": "5", "quoteVolume": "10"}])
    assert snap["agreement"] == "single_source"
    assert snap["advisory_score"] is None
    assert snap["venues"]["binance"]["pct_up"] == 1.0
