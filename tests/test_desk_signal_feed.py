from __future__ import annotations

import json
from pathlib import Path

from architecture.university.desk_signal_feed import build_desk_signal_feed, export_desk_signal_feed
from architecture.university.science_to_desk_pipeline import run_science_to_desk_pipeline


def test_desk_signal_feed_lists_research_overlay(tmp_path: Path):
    sw = tmp_path / "reports/grok/PAPER/strategy_switch.json"
    sw.parent.mkdir(parents=True, exist_ok=True)
    sw.write_text(
        json.dumps({"version": 1, "active": {"H14:mtf": 0.1}, "paper_only": True}),
        encoding="utf-8",
    )
    feed = export_desk_signal_feed(tmp_path)
    assert feed["schema"] == "ahos.desk_signal_feed.v1"
    crypto = next(d for d in feed["desks"] if d["paper_desk"] == "CRYPTO")
    assert crypto["pipeline_desk"] == "CRYPTO_UNIVERSE_DESK"
    assert "notional_mult" in crypto
    assert (tmp_path / "reports/grok/PAPER/desk_signal_feed.json").is_file()


def test_pipeline_attaches_feed_receipt(tmp_path: Path):
    doc = run_science_to_desk_pipeline(tmp_path)
    assert doc.get("desk_signal_feed", {}).get("desks_count", 0) >= 7
    assert build_desk_signal_feed(tmp_path)["desks"]
