"""Funding and open-interest change are logged and do not move the composite weight."""
from architecture.markets import signal_brain as sb
from architecture.markets.crypto_futures_context import build_futures_context


def test_both_venues_are_kept_and_the_weight_stays() -> None:
    ctx = build_futures_context({
        "BTC": {
            "binance_funding": {"lastFundingRate": "0.00001529"},
            "binance_oi": [
                {"timestamp": 1000, "sumOpenInterestValue": "100"},
                {"timestamp": 2000, "sumOpenInterestValue": "110"},
            ],
            "okx_funding": {"data": [{"fundingRate": "0.0001"}]},
            "okx_oi": {"data": [{"oiUsd": "2694479905"}]},
            "okx_oi_hist": {"data": [
                ["2000", "1", "1", "90"],
                ["1000", "1", "1", "100"],
            ]},
        },
        "ETH": {"binance_funding": {"lastFundingRate": "0.0001"}, "okx_funding": {"data": [{"fundingRate": "-0.0002"}]}},
    })
    btc = ctx["symbols"]["BTC"]
    assert btc["funding_agreement"] == "agree"
    assert btc["binance_oi_change"] == 0.1
    assert btc["okx_oi_change"] == -0.1
    assert btc["oi_agreement"] == "conflict"
    assert ctx["symbols"]["ETH"]["funding_agreement"] == "conflict"
    assert ctx["symbols"]["SOL"]["funding_agreement"] == "incomplete"
    assert ctx["changes_funding_oi_weight"] is False
    assert sb.DEFAULT_WEIGHTS["funding_oi"] == 0.06
