from __future__ import annotations

from architecture.mission.organ_telemetry_and_icon_audit import build_organ_telemetry_and_icon_audit_snapshot


def test_eight_organs_and_g_drive_icons() -> None:
    snap = build_organ_telemetry_and_icon_audit_snapshot()
    assert snap["organs_count"] == 8
    assert len(snap["organ_telemetry"]) == 8
    assert snap["zero_c_drive_dependency"] is True
    assert snap["organ_telemetry"][0]["ram_tier"] == "TIER_8GB_SAFE"
