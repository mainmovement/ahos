from architecture.markets.desk_news import (
    DROPPED,
    SOURCE_WEIGHT,
    attach_latency,
    build_snapshot,
    pump_news_block,
    reliability_from_scorecard,
)
from architecture.markets.paper_trade_gates import MIN_AGREEING_FAMILIES, MIN_EXPECTED_PROFIT_TO_FEE_RATIO


def _rss(title: str, when: str = "Thu, 30 Oct 2026 04:00:00 GMT") -> str:
    return f"<rss><channel><item><title>{title}</title><pubDate>{when}</pubDate></item></channel></rss>"


def test_two_publishers_make_a_shadow_sign_and_one_publisher_does_not():
    bodies = {
        "fed_press": _rss("Gold surges after the statement"),
        "fed_monetary": _rss("Gold surges after the statement"),
        "fxstreet": _rss("Gold surges on bullion demand"),
    }
    doc = build_snapshot(bodies)
    gold = next(row for row in doc["shadow_signs"] if row["symbol"] == "XAU")
    assert gold["sign"] == "LONG"
    assert gold["publishers"] == ["federalreserve", "fxstreet"]
    assert gold["source_weight"] == 0.0
    assert gold["counts_toward_entry_gate"] is False
    assert doc["source_weight"] == SOURCE_WEIGHT == 0.0
    alone = build_snapshot({"fxstreet": _rss("Gold plunges")})
    assert next(row for row in alone["shadow_signs"] if row["symbol"] == "XAU")["sign"] == "FLAT"


def test_oil_equities_and_crypto_map_symbols_and_drop_blocked_feeds():
    bodies = {
        "oilprice": _rss("Brent plunges as crude demand falls"),
        "rigzone": _rss("Brent plunges after a supply slump"),
        "cnbc": _rss("Nasdaq surges to a record high"),
        "marketwatch": _rss("Nasdaq surges with the rally"),
        "coindesk": _rss("Bitcoin surges on ETF inflows"),
        "decrypt": _rss("Bitcoin surges again"),
    }
    doc = build_snapshot(bodies)
    signs = {row["symbol"]: row["sign"] for row in doc["shadow_signs"]}
    assert signs["BRENT"] == "SHORT" and signs["BZ"] == "SHORT"
    assert signs["NDX"] == "LONG" and signs["NQ"] == "LONG"
    assert signs["BTC"] == "LONG"
    assert "ecb_press" in DROPPED and "opec_press" in DROPPED
    assert "reuters_rss" in DROPPED and "dexscreener_boosts" in DROPPED
    assert "pumpfun_api" in DROPPED and "coingecko_new_coins" in DROPPED
    assert doc["eia_release_clock"]["weekday"] is None
    assert doc["eia_release_clock"]["text"].startswith("Released at 10:30 a.m.")


def test_listings_stay_off_the_gate_and_a_scorecard_rate_does_not_change_the_weight():
    bodies = {
        "binance_listings": '{"data":{"articles":[{"title":"Binance Will List Predict (PREDICT)","publishDate":1761800000000}]}}',
        "gecko_new_pools": '{"data":[{"attributes":{"name":"ENA / WETH","pool_created_at":"2026-10-30T04:50:23Z"}}]}',
        "telegram_binance": '<div class="tgme_widget_message_text">Binance Will List Predict (PREDICT)</div>'
        '<time datetime="2026-10-30T04:00:00+00:00"></time>',
    }
    # telegram parser zips times then texts; the fixture order above has text before time.
    bodies["telegram_binance"] = (
        '<div class="tgme_widget_message_wrap"><time datetime="2026-10-30T04:00:00+00:00"></time>'
        '<div class="tgme_widget_message_text">Gold surges is not a listing keyword (PREDICT)</div></div>'
    )
    doc = build_snapshot(bodies, {"families": {"news": {"24h": {"hits": 8, "misses": 2, "hit_rate": 0.8}}}})
    tickers = {sym for row in doc["items"] for sym in row["symbols"]}
    assert "PREDICT" in tickers and "ENA" in tickers
    assert all(row["counts_toward_entry_gate"] is False for row in doc["items"])
    assert all(row["listing"] is True for row in doc["items"])
    assert doc["shadow_signs"] == []
    assert doc["reliability"]["hit_rate_24h"] == 0.8
    assert doc["reliability"]["source_weight"] == 0.0
    assert reliability_from_scorecard(None)["hit_rate_24h"] is None


def test_latency_is_logged_and_a_missing_later_price_is_not_a_move():
    item = {"ts": 1_000.0, "source": "cnbc"}
    row = attach_latency(item, price_ts=1_300.0, price=100.0, later_price=None)
    assert row["latency_s"] == 300.0
    assert row["price_move_pct"] is None
    moved = attach_latency(item, price_ts=1_300.0, price=100.0, later_price=101.0)
    assert moved["price_move_pct"] == 1.0


def test_pump_news_needs_another_family_and_a_passing_safety_check():
    news_only = {"votes": [{"family": "news", "vote": "AGREE"}]}
    assert pump_news_block(news_only, {"allowed": True}) == "PUMP_NEWS_ALONE"
    paired = {"votes": [{"family": "news", "vote": "AGREE"}, {"family": "candle_wicks", "vote": "AGREE"}]}
    assert pump_news_block(paired, {"allowed": False}) == "PUMP_NEWS_NEEDS_SAFETY"
    assert pump_news_block(paired, {"allowed": True}) is None
    assert MIN_AGREEING_FAMILIES == 2
    assert MIN_EXPECTED_PROFIT_TO_FEE_RATIO == 2.0


def test_a_getter_builds_the_snapshot_without_a_live_fetch(tmp_path):
    from architecture.markets.desk_news import load_live_snapshot

    seen = []

    def getter(url: str) -> str:
        seen.append(url)
        if "fxstreet" in url:
            return _rss("Gold surges")
        return ""

    doc = load_live_snapshot(tmp_path, {"XAU": {"price": 100.0, "market_time": "2026-10-30T05:00:00Z"}}, getter=getter)
    assert seen
    assert doc["counts_toward_entry_gate"] is False
    gold = next(row for row in doc["items"] if "XAU" in row["symbols"])
    assert gold["latency_s"] is not None
    assert gold["price_move_pct"] is None


def test_news_alone_does_not_open_a_pump_token(tmp_path):
    import json
    import time as _t

    from architecture.markets import paper_trader as pt

    t0 = 1_800_000_000.0
    mt = _t.strftime("%Y-%m-%dT%H:%M:%SZ", _t.gmtime(t0))
    bars = [[1 + i * 0.01, 1.01 + i * 0.01, 0.99 + i * 0.01, 1 + i * 0.01, 10.0] for i in range(40)]

    def feed(root, positions):
        good = ({"price": 1.4, "market_time": mt, "ohlcv_5m": bars, "token_address": "0xabc", "source": "gt"},
                {"verdict": "VERIFIED", "source_a": "gt", "price_a": 1.4, "source_b": "ds", "price_b": 1.401, "gap": 0.001})
        return {"DEX_GOOD": good}

    def sig(sym, desk, q):
        return [
            {"name": "mtf_trend", "score": 0.8, "available": True, "source": "t", "spec": "t",
             "evidence": {"higher_tf_sign": 1}},
            {"name": "news", "score": 0.8, "available": True, "source": "rss", "spec": "t", "evidence": {}},
            {"name": "candles", "score": 0.8, "available": True, "source": "t", "spec": "t", "evidence": {}},
        ]

    pt.run_cycle(tmp_path, fetch=lambda: {"quotes": {}}, fetch_b=lambda: {}, signals_fn=sig, now=lambda: t0,
                 use_ledger=False, dex_feed=feed)
    rows = [json.loads(line) for line in (tmp_path / "reports/grok/PAPER/paper_trades.jsonl").read_text().splitlines()]
    assert not any(row.get("event") == "OPEN" for row in rows)
    assert any(row.get("reason") == "PUMP_NEWS_NEEDS_SAFETY" for row in rows)
