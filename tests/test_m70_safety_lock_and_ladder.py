"""M70.1–M70.6 AGI v2 Ladder & Cryptographic Safety Lock tests."""
from __future__ import annotations

from pathlib import Path
import pytest

from core.safety_lock import (
    PROTECTED_SAFETY_FILES,
    compute_safety_manifest,
    guard_autonomous_write,
    verify_safety_lock,
)


def test_safety_lock_verifies_all_protected_files():
    root = Path(__file__).resolve().parents[1]
    manifest = compute_safety_manifest(root)
    assert len(manifest) == len(PROTECTED_SAFETY_FILES)
    res = verify_safety_lock(root, expected=manifest)
    assert res["status"] == "LOCKED_CLEAN"
    assert res["ok"] is True

    tampered = dict(manifest)
    tampered["architecture/markets/risk.py"] = "0" * 64
    bad = verify_safety_lock(root, expected=tampered)
    assert bad["status"] == "HALT_TAMPERED"
    assert bad["ok"] is False


def test_autonomous_write_guard_blocks_safety_files_and_lane_a():
    root = Path(__file__).resolve().parents[1]
    for protected in (
        "architecture/markets/risk.py",
        "architecture/markets/judge.py",
        "core/safety_lock.py",
        "HOLD.flag",
        ".env",
        "discovery/collect.py",
        "paper_trading/engine.py",
    ):
        with pytest.raises(PermissionError):
            guard_autonomous_write(protected, actor="M51_self_improvement", root=root)

    assert guard_autonomous_write("proposals/prop_m51_test.json", actor="M51_self_improvement", root=root) is True


def test_agi_docs_exist_and_declare_human_gated_ladder():
    root = Path(__file__).resolve().parents[1]
    roadmap = (root / "docs" / "agi" / "AGI_ROADMAP.md").read_text(encoding="utf-8")
    sources = (root / "docs" / "agi" / "SOURCES.md").read_text(encoding="utf-8")
    assert "L0" in roadmap and "L6" in roadmap
    assert "M70.6" in roadmap and "M70.6" in sources
