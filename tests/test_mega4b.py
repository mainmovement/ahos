from datetime import datetime, timezone
from pathlib import Path

from architecture.markets.desk_expectancy_pause import assess
from architecture.mission.operator_drills import judge_drill, kill_switch_drill
from architecture.persistence.sqlite_wal import apply_wal
from architecture.university.lesson_shadow import measure
from scripts.m13_gold_soak import _keep_window_start


def _close(desk, pnl, cause_reason, i, news=0.4):
    return {
        "desk": desk,
        "side": "LONG",
        "realized_pnl_usd": pnl,
        "fees_usd": 0.0,
        "closed_at": f"2026-10-{i:02d}T00:00:00Z",
        "reason": cause_reason,
        "entry_brain": {"signals": [{"name": "news", "score": news, "available": True, "evidence": {}}]},
    }


def test_shadow_lessons_change_expectancy_and_not_the_live_weight():
    closes = [
        _close("CRYPTO", -1.0, "STOP", 1),
        _close("CRYPTO", -1.0, "TIME_STOP", 2, news=0.0),
        _close("CRYPTO", 2.0, "TAKE_PROFIT", 3, news=0.4),
    ]
    doc = measure(closes)
    assert doc["applied_to_live_weights"] is False
    assert doc["n_dropped"] >= 1
    assert doc["delta_expectancy_usd"] is not None


def test_a_desk_pauses_only_after_twenty_negative_closes():
    short = [{"desk": "OIL", "realized_pnl_usd": -0.1} for _ in range(19)]
    assert assess(short)["paused_desks"] == []
    long = [{"desk": "CRYPTO", "realized_pnl_usd": -0.2} for _ in range(20)]
    long.append({"desk": "EU_EQUITIES", "realized_pnl_usd": 0.4})
    doc = assess(long)
    assert doc["paused_desks"] == ["CRYPTO"]
    assert doc["carrying_desks"] == ["EU_EQUITIES"]


def test_wal_survives_an_integrity_check(tmp_path: Path):
    import sqlite3

    path = tmp_path / "book.sqlite"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE t(x)")
    conn.execute("INSERT INTO t VALUES (1)")
    conn.commit()
    conn.close()
    doc = apply_wal(path)
    assert doc["applied"] is True
    assert doc["journal_mode"].lower() == "wal"
    assert doc["integrity"] == "ok"


def test_a_fresh_heartbeat_does_not_move_the_window_start():
    previous = {
        "window_started_utc": "2026-10-28T00:00:00Z",
        "last_cycle": {"ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")},
    }
    assert _keep_window_start(previous, 900) == "2026-10-28T00:00:00Z"
    stale = {
        "window_started_utc": "2026-10-28T00:00:00Z",
        "last_cycle": {"ts": "2026-10-01T00:00:00Z"},
    }
    assert _keep_window_start(stale, 900) != "2026-10-28T00:00:00Z"


def test_vision_overlay_counts_only_rows_with_proof():
    from architecture.mission.vision_steps import AUDIT_ROWS, build_overlay

    empty = build_overlay({})
    assert empty["audit_operational_impl"] == 0
    assert empty["current_impl"] == 0
    assert len(empty["rows"]) == AUDIT_ROWS
    assert empty["live_switch"] is False
    full = build_overlay({
        "lesson_shadow": True,
        "safety_veto_rows": 9,
        "news_weight_zero": True,
        "news_blocks_entry": True,
        "paper_book": True,
        "pause_armed": True,
        "soak_clock_kept": True,
    })
    assert full["current_impl"] == 5
    assert full["current_impl_pct"] == 19.2


def test_the_drills_trip_a_fake_loss_and_refuse_a_broken_ledger():
    kill = kill_switch_drill([], 100.0, datetime.now(timezone.utc).timestamp())
    assert kill["passed"] is True
    assert kill["live_book_edited"] is False
    judge = judge_drill()
    assert judge["passed"] is True
    assert judge["promoted"] is False
