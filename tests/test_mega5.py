"""MEGA 5: edge split stays shadow, and a vision row needs its own proof."""
from __future__ import annotations

from pathlib import Path

from architecture.markets.edge_decomposition import bucket, decompose, shadow_dominant
from architecture.mission.close_reason_fa import close_reason_fa
from architecture.mission.vision_steps import build_overlay
from architecture.persistence.store_integrity import integrity_check


def _close(desk: str, pnl: float, reason: str, i: int, fees: float = 0.01) -> dict:
    return {
        "symbol": "XAU",
        "desk": desk,
        "side": "LONG",
        "reason": reason,
        "closed_at": f"2026-10-{i:02d}T00:00:00Z",
        "realized_pnl_usd": pnl,
        "fees_usd": fees,
        "entry_brain": {"signals": []},
    }


def test_a_fee_only_loss_is_fees_and_a_time_stop_is_timing():
    assert bucket(_close("GOLD", -0.01, "STOP_LOSS", 1, fees=0.02)) == "FEES"
    assert bucket(_close("GOLD", -0.2, "TIME_STOP", 2, fees=0.01)) == "TIMING"
    assert bucket(_close("GOLD", 0.2, "TAKE_PROFIT", 3)) == "WIN"


def test_shadow_drop_is_not_applied():
    closes = [_close("GOLD", -0.2, "TIME_STOP", i) for i in range(1, 28)]
    closes += [_close("GOLD", 0.05, "TAKE_PROFIT", i) for i in range(1, 13)]
    shadow = shadow_dominant(closes)
    assert shadow["applied_to_live_weights"] is False
    assert shadow["decision"] == "KEEP_SHADOW"
    assert "RED_TEAM_ABSENT" in shadow["reasons"]
    doc = decompose(closes)
    assert doc["desks"][0]["desk"] == "GOLD"
    assert doc["desks"][0]["expectancy_usd"] < 0


def test_the_persian_sentence_cites_the_logged_reason():
    row = _close("OIL", -0.1, "SIGNAL_REVERSAL", 4)
    sentence = close_reason_fa(row)
    assert "SIGNAL_REVERSAL" in sentence
    assert "حکم جدیدی نیست" in sentence


def test_new_vision_rows_stay_off_without_proof_and_count_with_it():
    empty = build_overlay({})
    assert empty["current_impl"] == 0
    full = build_overlay({
        "lesson_shadow": True,
        "safety_veto_rows": 1,
        "news_weight_zero": True,
        "news_blocks_entry": True,
        "paper_book": True,
        "pause_armed": True,
        "soak_clock_kept": True,
        "kian_cited": True,
        "whale_score": True,
        "liquidity_attached": True,
        "paper_reads_opens": True,
        "witnesses_agreed": True,
        "close_reasons_cited": True,
        "calibration_measured": True,
        "calibration_applied": False,
        "sourced_quotes": True,
        "token_veto_rows": 2,
        "recall_cited": True,
        "recall_unknown": True,
        "kill_drill_passed": True,
        "live_book_edited": False,
        "provider_probe_recorded": True,
    })
    assert full["current_impl"] == 17
    assert full["current_impl_pct"] == round(100 * 17 / 26, 1)
    applied = build_overlay({"calibration_measured": True, "calibration_applied": True})
    assert all(row["id"] != "calibration" or row["current_impl"] is False for row in applied["rows"])


def test_a_missing_store_is_not_ok(tmp_path: Path):
    assert integrity_check(tmp_path / "missing.sqlite") == "NO_DATA"


def test_snapshot_copy_of_a_small_store_is_ok(tmp_path: Path):
    import sqlite3
    from architecture.persistence.store_integrity import snapshot_integrity
    source = tmp_path / "live.sqlite"
    conn = sqlite3.connect(source)
    conn.execute("CREATE TABLE t(x INTEGER)")
    conn.execute("INSERT INTO t VALUES (1)")
    conn.commit()
    conn.close()
    assert snapshot_integrity(source, tmp_path / "copy.sqlite", timeout_s=30) == "ok"
    assert not (tmp_path / "copy.sqlite").exists()


def test_an_interrupted_large_store_is_not_kept_as_fresh():
    from architecture.persistence.store_integrity import merge_store_integrity
    previous = {"store_integrity": {
        "checked_at": "2026-10-30T14:47:34Z",
        "stores": {"ahos_local": "INTERRUPTED", "e01_discovery": "INTERRUPTED", "paper_trading": "ok"},
    }}
    merged = merge_store_integrity(
        previous, None, {"paper_trading": "ok", "ahos_knowledge": "ok"}, now="2026-10-30T16:00:00Z",
    )
    assert merged["stores"]["ahos_local"] == "RUNNING"
    assert merged["stores"]["e01_discovery"] == "RUNNING"
    ready = merge_store_integrity(
        previous,
        {"checked_at": "2099-01-01T00:00:00Z", "stores": {"ahos_local": "ok", "e01_discovery": "ok"}},
        {"paper_trading": "ok", "ahos_knowledge": "ok"},
        now="2099-01-01T00:00:01Z",
    )
    assert ready["stores"]["ahos_local"] == "ok"
    assert ready["stores"]["e01_discovery"] == "ok"
