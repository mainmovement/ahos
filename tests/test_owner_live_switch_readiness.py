from __future__ import annotations

from architecture.mission.owner_live_switch_readiness import build_owner_live_switch_readiness_snapshot


def test_six_gates_hold_locked() -> None:
    snap = build_owner_live_switch_readiness_snapshot()
    assert snap["gates_total"] == 6
    assert len(snap["gates"]) == 6
    assert snap["owner_unlock_allowed"] is False
    assert snap["hold_flag_active"] is True
    assert snap["live_gateway_status"] == "READY_LOCKED_BY_HOLD_FLAG"
    assert snap["day_1_agi_claimed"] is False
    hold_gate = next(g for g in snap["gates"] if g["gate_id"] == "GATE_6_OWNER_HOLD_FLAG_LOCK")
    assert hold_gate["status"] == "GREEN"
    assert snap["gates_green_count"] == 6
    assert "۶/۶ GREEN" in snap["persian_owner_guide_fa"] or "6/6 GREEN" in snap["persian_owner_guide_fa"]
