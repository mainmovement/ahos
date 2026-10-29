from architecture.markets.trade_signal_provenance import build_signal_provenance, explain_paper_trade_fa


def test_provenance_categories_and_persian_explain():
    brain = {
        "composite": -0.42,
        "switch_version": 0,
        "contributions": [{"signal": "mtf_trend", "weight": 0.4, "score": -0.8, "contribution": -0.32}],
        "signals": [
            {"name": "news", "score": -0.2, "available": True, "source": "rss", "spec": "news"},
            {"name": "macro", "score": 0.1, "available": True, "source": "cnbc", "spec": "macro"},
            {"name": "large_trades", "score": -0.15, "available": True, "source": "okx", "spec": "whale"},
            {"name": "candles", "score": -0.3, "available": True, "source": "yahoo", "spec": "wick"},
            {"name": "research_hypothesis", "score": 0.0, "available": False, "source": "n/a", "spec": "research"},
        ],
    }
    prov = build_signal_provenance(brain)
    assert prov["schema"] == "ahos.trade_signal_provenance.v1"
    assert "news" in prov["by_category"]
    assert "whales_flow" in prov["by_category"]
    assert "research" in prov["missing_families"]
    fa = explain_paper_trade_fa(symbol="BTC", side="SHORT", desk="CRYPTO", brain=brain, composite=-0.42)
    assert "معامله کاغذی BTC" in fa
    assert "UNPROVEN_EDGE" in fa
    assert "mtf_trend" in fa


def test_explain_mentions_desk_size_policy():
    brain = {
        "composite": 0.5,
        "contributions": [],
        "signals": [{"name": "mtf_trend", "score": 0.5, "available": True, "source": "x", "spec": "§2"}],
        "desk_notional_mult": 0.25,
        "desk_notional_mult_source": "edge_merged",
    }
    fa = explain_paper_trade_fa(symbol="BTC", side="LONG", desk="CRYPTO", brain=brain, composite=0.5)
    assert "0.250" in fa or "0.25" in fa
    assert "edge_merged" in fa
