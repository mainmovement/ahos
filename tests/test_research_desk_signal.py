import json

from architecture.markets.research_desk_signal import append_research_signal, research_overlay_for_desk


def test_research_overlay_reads_strategy_switch(tmp_path):
    sw = tmp_path / "reports" / "grok" / "PAPER" / "strategy_switch.json"
    sw.parent.mkdir(parents=True, exist_ok=True)
    sw.write_text(
        json.dumps({"version": 3, "active": {"H14:btc_mr": 0.4, "H16:us_mom": -0.2}}, ensure_ascii=False),
        encoding="utf-8",
    )
    crypto = research_overlay_for_desk(tmp_path, "CRYPTO")
    assert crypto["name"] == "research_overlay"
    assert crypto["available"] is True
    us = research_overlay_for_desk(tmp_path, "US_EQUITIES")
    assert us["available"] is True
    sigs = append_research_signal(tmp_path, "CRYPTO", [{"name": "mtf_trend", "score": 0.5, "available": True}])
    assert any(s["name"] == "research_overlay" for s in sigs)


def test_research_overlay_includes_batch_pass_stats(tmp_path):
    b5 = tmp_path / "reports" / "grok" / "M28" / "batch5_research.json"
    b5.parent.mkdir(parents=True, exist_ok=True)
    b5.write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "strategy_id": "b5-H14-ETH",
                        "gate": "PASS_STATS",
                        "oos_sharpe": 0.6,
                        "deflated_sharpe": 0.12,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    overlay = research_overlay_for_desk(tmp_path, "CRYPTO")
    assert overlay["available"] is True
    assert overlay["score"] is not None
    assert "batch_research" in (overlay.get("evidence") or {}).get("overlay_sources", [])
