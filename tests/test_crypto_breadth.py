"""Breadth is advisory. One venue, or a split, does not produce a sign."""
from architecture.markets.crypto_breadth import advisory_signal, build_breadth_snapshot


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


def test_one_venue_stays_unscored() -> None:
    snap = build_breadth_snapshot(binance=[{"symbol": "BTCUSDT", "priceChangePercent": "5", "quoteVolume": "10"}])
    assert snap["agreement"] == "single_source"
    assert snap["advisory_score"] is None
    assert snap["venues"]["binance"]["pct_up"] == 1.0
