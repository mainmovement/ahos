"""M60.C 4-Brain Autonomous Coder bridge tests."""
from __future__ import annotations

from pathlib import Path

from architecture.cognitive.autonomous_coder_bridge import (
    probe_cloud_bridge_8787,
    resolve_local_coder_tier,
    run_autonomous_coder_cycle,
    synthesize_persian_brief_fa,
    verify_python_patch_in_sandbox,
)


def test_brain1_bridge_probe_offline_fallback_fast() -> None:
    status, err = probe_cloud_bridge_8787(url="http://127.0.0.1:1/health", timeout_s=0.2)
    assert status == "OFFLINE"
    assert err is not None


def test_brain2_tier_8gb_safe_offload() -> None:
    tier = resolve_local_coder_tier(ram_gb=7.93)
    assert tier["tier_id"] == "8GB_SAFE_API_OFFLOAD"
    assert tier["local_weights_loaded"] is False


def test_brain3_ast_parse_and_m70_6_refusal(tmp_path: Path) -> None:
    good = 'def ok() -> int:\n    return 1\n'
    bad = "def broken(\n"
    repo = tmp_path
    ok = verify_python_patch_in_sandbox(good, target_path="proposals/x.py", root=repo)
    assert ok["syntax_ok"] is True
    assert ok["sandbox_test_status"] == "SANDBOX_SINGLE_FILE_PYTEST_PASS"

    fail = verify_python_patch_in_sandbox(bad, target_path="proposals/x.py", root=repo)
    assert fail["syntax_ok"] is False
    assert fail["rollback_triggered"] is True

    blocked = verify_python_patch_in_sandbox(good, target_path="core/safety_lock.py", root=repo)
    assert blocked["m70_6_allowed"] is False
    assert blocked["rolled_back_count"] == 1


def test_brain4_cycle_snapshot_four_brains_and_persian_brief(tmp_path: Path) -> None:
    snap = run_autonomous_coder_cycle(root=tmp_path)
    assert snap["paper_only"] is True
    assert len(snap["fourBrains"]) == 4
    eng = snap["four_brain_engine"]
    assert eng["persian_briefs_generated"] >= 1
    assert eng["brain_2_local_oss_tier"] == "8GB_SAFE_API_OFFLOAD"
    assert snap["recentPersianTexts"]
    brief = synthesize_persian_brief_fa(bridge_status="OFFLINE", tier=resolve_local_coder_tier(7.0))
    assert "PAPER_ONLY" in brief
