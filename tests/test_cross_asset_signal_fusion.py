from __future__ import annotations

from architecture.mission.cross_asset_signal_fusion import build_cross_asset_signal_fusion_snapshot


def test_fusion_matrix_long_short_and_leverage() -> None:
    snap = build_cross_asset_signal_fusion_snapshot()
    assert snap["pilot_capital_usd"] == 100.0
    assert set(snap["supported_directions"]) == {"LONG", "SHORT"}
    opps = snap["confluence_opportunities"]
    assert len(opps) >= 6
    sides = {o["side"] for o in opps}
    assert "LONG" in sides and "SHORT" in sides
    symbols = {o["symbol"] for o in opps}
    assert "MGC" in symbols and "MCL" in symbols
    for o in opps:
        assert o["leverage"] >= 10
        assert o["statistical_edge_e"] > 0
        assert o["isolated_margin_usd"] <= 20.0
    assert "macro_alignment_matrix" in snap
