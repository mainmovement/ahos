import json

from architecture.markets import signal_brain as sb
from architecture.markets.research_desk_signal import (
    append_research_signal,
    research_overlay_for_desk,
    research_predictions_for_trade,
)


def test_research_overlay_reads_strategy_switch(tmp_path):
    sw = tmp_path / "reports" / "grok" / "PAPER" / "strategy_switch.json"
    sw.parent.mkdir(parents=True, exist_ok=True)
    sw.write_text(
        json.dumps({"version": 3, "active": {"H14:btc_mr": 0.4, "H16:us_mom": -0.2}}, ensure_ascii=False),
        encoding="utf-8",
    )
    crypto = research_overlay_for_desk(tmp_path, "CRYPTO")
    assert crypto["name"] == "research_overlay"
    assert crypto["available"] is False
    pred = research_predictions_for_trade(tmp_path, "CRYPTO")
    assert any(p.get("switch_key") == "H14:btc_mr" for p in pred["predictions"])
    sigs = append_research_signal(tmp_path, "CRYPTO", [{"name": "mtf_trend", "score": 0.5, "available": True}])
    assert any(s["name"] == "research_overlay" for s in sigs)


def test_shadow_registry_does_not_move_composite(tmp_path):
    reg = tmp_path / "strategy_lab" / "registry.json"
    reg.parent.mkdir(parents=True, exist_ok=True)
    reg.write_text(
        json.dumps(
            {
                "candidates": {
                    "H15": {
                        "verdict": "SHADOW_FORWARD_TEST",
                        "detail": {"b4-H15-BTC": {"oos_sharpe": 0.3}},
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    base = [{"name": "mtf_trend", "score": 0.4, "available": True}]
    w = dict(sb.DEFAULT_WEIGHTS)
    without = sb.combine(base, w)
    with_research = sb.combine(append_research_signal(tmp_path, "CRYPTO", list(base)), w)
    assert with_research["composite"] == without["composite"]
    overlay = research_overlay_for_desk(tmp_path, "CRYPTO")
    assert overlay["available"] is False
    assert (overlay.get("evidence") or {}).get("composite_weight") == 0.0
    preds = research_predictions_for_trade(tmp_path, "CRYPTO")
    h15 = next(p for p in preds["predictions"] if p["hypothesis_id"] == "H15")
    assert h15["composite_weight"] == 0.0
    assert h15["predicted_direction"] == "LONG"


def test_pass_stats_survived_can_weight_overlay(tmp_path):
    b5 = tmp_path / "reports" / "grok" / "M28" / "batch5_research.json"
    b5.parent.mkdir(parents=True, exist_ok=True)
    sid = "b5-H14-ETH"
    b5.write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "strategy_id": sid,
                        "gate": "PASS_STATS",
                        "oos_sharpe": 0.5,
                        "deflated_sharpe": 0.12,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    red = tmp_path / "reports" / "grok" / "M56" / "strategy_red_team_snapshot.json"
    red.parent.mkdir(parents=True, exist_ok=True)
    red.write_text(json.dumps({"reports": [{"strategy_id": sid, "verdict": "SURVIVED_RED_TEAM"}]}), encoding="utf-8")
    overlay = research_overlay_for_desk(tmp_path, "CRYPTO")
    assert overlay["available"] is True
    assert overlay["score"] is not None
    base = [{"name": "mtf_trend", "score": 0.0, "available": True}]
    w = dict(sb.DEFAULT_WEIGHTS)
    c0 = sb.combine(base, w)
    c1 = sb.combine(append_research_signal(tmp_path, "CRYPTO", list(base)), w)
    assert c1["composite"] != c0["composite"]
