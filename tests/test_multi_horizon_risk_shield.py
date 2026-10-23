from __future__ import annotations

from architecture.mission.multi_horizon_risk_shield import build_multi_horizon_risk_shield_snapshot


def test_horizon_breakers_and_directional_balance() -> None:
    snap = build_multi_horizon_risk_shield_snapshot()
    assert snap["pilot_capital_usd"] == 100.0
    assert snap["shield_verdict"] == "ARMED_GREEN"
    assert len(snap["horizon_breakers"]) == 3
    assert snap["horizon_breakers"][0]["max_drawdown_usd"] == 3.0
    bal = snap["directional_balance"]
    assert bal["wallet_reserve_min_pct"] >= 40.0
    assert bal["active_long_slices"] >= 1 and bal["active_short_slices"] >= 1
