from __future__ import annotations

from pathlib import Path

from architecture.continuation.next_tranche import (
    build_didehban_receipt,
    build_ideas_shelf_receipt,
    build_m58_promote_loop_receipt,
    build_scheduling_receipt,
    run_next_tranche,
)


def test_next_tranche_receipt(tmp_path: Path):
    # minimal roots for receipts
    (tmp_path / "proposals").mkdir(exist_ok=True)
    (tmp_path / "proposals" / "prop_test.json").write_text('{"title":"t","status":"PROPOSED"}', encoding="utf-8")
    (tmp_path / "strategy_lab").mkdir(exist_ok=True)
    (tmp_path / "strategy_lab" / "registry.json").write_text('{"candidates":{}}', encoding="utf-8")
    (tmp_path / "reports" / "grok" / "M18").mkdir(parents=True, exist_ok=True)
    (tmp_path / "reports" / "grok" / "M18" / "newsroom_snapshot.json").write_text(
        '{"rssClusters":[],"generated_at":"2026-01-01T00:00:00Z"}', encoding="utf-8"
    )
    doc = run_next_tranche(tmp_path)
    assert doc["schema"] == "ahos.next_tranche_receipt.v1"
    assert "scheduling" in doc["tracks"]
    assert (tmp_path / "reports" / "grok" / "CONTINUATION" / "next_tranche_receipt.json").is_file()


def test_m58_promote_loop_auto_promote_false(tmp_path: Path):
    (tmp_path / "reports" / "grok" / "PAPER").mkdir(parents=True, exist_ok=True)
    (tmp_path / "reports" / "grok" / "PAPER" / "strategy_switch.json").write_text(
        '{"version":0,"active":{},"paper_only":true}', encoding="utf-8"
    )
    r = build_m58_promote_loop_receipt(tmp_path)
    assert r["auto_promote_enabled"] is False
