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
        "kian_cited": True,
        "whale_score": True,
        "liquidity_attached": True,
        "paper_reads_opens": True,
        "witnesses_agreed": True,
    })
    assert full["current_impl"] == 10
    assert full["current_impl_pct"] == 38.5


def test_the_lesson_stays_shadow_until_thirty_newer_closes_and_a_red_team():
    from architecture.university.lesson_shadow import decide_promotion, export_promotion, lesson_is_live

    base = [_close("GOLD", 0.2, "TAKE_PROFIT", i, news=0.0) for i in range(1, 8)]
    held = decide_promotion(base, baseline_closed_at="2026-10-07T00:00:00Z", red_team="SURVIVED_RED_TEAM")
    assert held["decision"] == "KEEP_SHADOW"
    assert "AWAITING_30_FURTHER_CLOSES" in held["reasons"]
    assert held["applied_to_live_weights"] is False
    newer = [_close("GOLD", 0.2, "TAKE_PROFIT", i, news=0.0) for i in range(1, 41)]
    no_team = decide_promotion(newer, baseline_closed_at="2026-09-01T00:00:00Z", red_team=None)
    assert no_team["decision"] == "KEEP_SHADOW"
    assert "RED_TEAM_ABSENT" in no_team["reasons"]
    losses = [_close("GOLD", -0.2, "STOP", i, news=0.0) for i in range(1, 41)]
    negative = decide_promotion(losses, baseline_closed_at="2026-09-01T00:00:00Z", red_team="SURVIVED_RED_TEAM")
    assert negative["promote_to_live_weights"] is False
    promoted = decide_promotion(newer, baseline_closed_at="2026-09-01T00:00:00Z", red_team="SURVIVED_RED_TEAM")
    assert promoted["decision"] == "PROMOTED"
    assert promoted["oos_further_expectancy_usd"] > 0
    repo = Path(__file__).resolve().parents[1]
    assert lesson_is_live(repo) is False
    scratch = repo / "reports" / "_scratch_lesson_promo_test"
    # The live book is not this directory. The write below is removed.
    scratch.mkdir(parents=True, exist_ok=True)
    try:
        seed = scratch / "reports" / "grok" / "PAPER" / "lesson_promotion.json"
        seed.parent.mkdir(parents=True, exist_ok=True)
        seed.write_text('{"baseline_closed_at": "2026-09-01T00:00:00Z"}\n', encoding="utf-8")
        written = export_promotion(scratch, newer, red_team="SURVIVED_RED_TEAM")
        assert written["applied_to_live_weights"] is True
        assert lesson_is_live(scratch) is True
        export_promotion(scratch, newer, red_team=None)
        assert lesson_is_live(scratch) is False
    finally:
        import shutil
        shutil.rmtree(scratch, ignore_errors=True)


def test_half_size_needs_ten_closes_and_a_loss_worse_than_two_fees():
    mild = [{"desk": "PB_TOKEN", "realized_pnl_usd": -0.01, "fees_usd": 0.011} for _ in range(14)]
    sharp = [{"desk": "GOLD", "realized_pnl_usd": -0.03, "fees_usd": 0.008} for _ in range(14)]
    doc = assess(mild + sharp)
    by_desk = {row["desk"]: row for row in doc["desks"]}
    assert by_desk["PB_TOKEN"]["size_factor"] == 1.0
    assert by_desk["GOLD"]["size_factor"] == 0.5
    assert "GOLD" in doc["early_warning_desks"]
    assert "PB_TOKEN" not in doc["early_warning_desks"]


def test_the_data_walk_skips_large_directories_and_stops_on_the_clock(tmp_path):
    from architecture.persistence.bounded_walk import find_files

    data = tmp_path / "data"
    nested = data / "mission_ledger"
    skipped = data / "node_modules" / "pkg"
    nested.mkdir(parents=True)
    skipped.mkdir(parents=True)
    (nested / "book.sqlite").write_bytes(b"ok")
    (skipped / "hidden.sqlite").write_bytes(b"no")
    found = find_files(data, (".sqlite",), max_depth=3, timeout_s=5.0)
    assert any(name.endswith("book.sqlite") for name in found["files"])
    assert not any("node_modules" in name for name in found["files"])
    stopped = find_files(data, (".sqlite",), timeout_s=0.0)
    assert stopped["timed_out"] is True


def test_kian_cites_a_close_or_returns_unknown():
    from architecture.mission.vision_live import agreed_witness, kian_answer

    closes = [_close("OIL", -1.0, "STOP", 3)]
    cited = kian_answer(closes, "why OIL close")
    assert cited["status"] == "CITED"
    assert "OIL" in cited["citations"][0]
    unknown = kian_answer(closes, "zebra quilt mosaic")
    assert unknown["status"] == "UNKNOWN"
    assert unknown["answer"] == "UNKNOWN"
    missing = agreed_witness({"symbol": "BTC", "source": "a", "witness": {"verdict": "CONFLICT", "source_b": "b"}})
    assert missing is None
    agreed = agreed_witness({
        "symbol": "NKD",
        "source": "tradingview:CME:NKD1!",
        "ts": "2026-10-30T12:13:46Z",
        "witness": {"verdict": "VERIFIED", "source_b": "yahoo_finance:NKD=F", "gap": 0.00056},
    })
    assert agreed["identity_id"].startswith("witness:NKD:")
    assert agreed["source_a"] != agreed["source_b"]


def test_the_drills_trip_a_fake_loss_and_refuse_a_broken_ledger():
    kill = kill_switch_drill([], 100.0, datetime.now(timezone.utc).timestamp())
    assert kill["passed"] is True
    assert kill["live_book_edited"] is False
    judge = judge_drill()
    assert judge["passed"] is True
    assert judge["promoted"] is False
