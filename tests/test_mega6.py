"""MEGA 6 shadow rules stay off the live book and off closes from before the stamp."""
from __future__ import annotations

import json
from pathlib import Path

from architecture.markets.entry_shadow import (
    SHADOW_MIN_AGREEING_FAMILIES,
    SHADOW_VOTE_SCORE_FLOOR,
    evaluate,
    filter_verdicts,
    note_gold_path,
    predicted_probability,
    stamp_open,
    write_registry,
)
from architecture.markets.paper_account import LEDGER_REL
from architecture.markets.paper_trade_gates import MIN_AGREEING_FAMILIES, VOTE_SCORE_FLOOR
from scripts.m13_gold_soak import _resume_soak_state
from datetime import datetime, timezone


def test_live_floors_stay_put() -> None:
    assert VOTE_SCORE_FLOOR == 0.05
    assert MIN_AGREEING_FAMILIES == 2
    assert SHADOW_VOTE_SCORE_FLOOR == 0.15
    assert SHADOW_MIN_AGREEING_FAMILIES == 3


def test_probability_is_a_bounded_uncalibrated_map() -> None:
    value = predicted_probability(0.5, "LONG")
    assert 0.05 <= value <= 0.95
    assert value == 0.7
    features = stamp_open(
        composite=0.5, side="LONG", vote_audit={"agreeing_families": 2, "votes": [
            {"vote": "AGREE", "mean_score": 0.08},
            {"vote": "AGREE", "mean_score": 0.2},
        ]},
        spread_pct=0.1, atr_pct=0.01, symbol="BTCUSDT",
        moment=datetime(2026, 10, 30, 15, tzinfo=timezone.utc),
        fee_rate=0.001, desk="CRYPTO",
    )
    assert features["calibrated"] is False
    assert features["applied_to_decision"] is False
    assert features["filters"]["VOTE_SCORE_FLOOR_0_15"] == "DROP"
    assert features["filters"]["THREE_FAMILIES"] == "DROP"
    assert features["filters"]["SESSION_EDGE_30M"] == "KEEP"


def test_registry_does_not_move_and_old_closes_are_excluded(tmp_path: Path) -> None:
    first = write_registry(tmp_path, moment=datetime(2026, 10, 30, 12, tzinfo=timezone.utc))
    second = write_registry(tmp_path, moment=datetime(2026, 10, 30, 18, tzinfo=timezone.utc))
    assert second["registered_at"] == first["registered_at"]
    ledger = tmp_path / LEDGER_REL
    ledger.parent.mkdir(parents=True, exist_ok=True)
    old = {
        "event": "CLOSE", "desk": "CRYPTO", "opened_at": "2026-10-30T11:00:00Z",
        "closed_at": "2026-10-30T11:30:00Z", "realized_pnl_usd": -1.0, "side": "LONG",
    }
    fresh = {
        "event": "CLOSE", "desk": "CRYPTO", "opened_at": "2026-10-30T13:00:00Z",
        "closed_at": "2026-10-30T13:30:00Z", "realized_pnl_usd": 0.4, "side": "LONG",
        "entry_price": 100, "qty": 1, "entry_features": filter_verdicts({
            "desk": "CRYPTO", "agreeing_families": 3, "agree_abs_min": 0.2,
            "spread_pct": 0.1, "atr_pct": 0.01,
            "session": {"applicable": False, "near_edge": False},
        }) and {
            "desk": "CRYPTO", "agreeing_families": 3, "agree_abs_min": 0.2,
            "spread_pct": 0.1, "atr_pct": 0.01, "fee_rate": 0.001,
            "session": {"applicable": False, "near_edge": False},
            "filters": filter_verdicts({
                "desk": "CRYPTO", "agreeing_families": 3, "agree_abs_min": 0.2,
                "spread_pct": 0.1, "atr_pct": 0.01,
                "session": {"applicable": False, "near_edge": False},
            }),
        },
    }
    ledger.write_text(json.dumps(old) + "\n" + json.dumps(fresh) + "\n", encoding="utf-8")
    # The helper above registered "now", which is after the fixture closes.
    # Rewrite the stamp to noon so only the 13:00 close is fresh.
    path = tmp_path / "reports" / "grok" / "PAPER" / "mega6_preregistration.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["registered_at"] = "2026-10-30T12:00:00Z"
    path.write_text(json.dumps(doc), encoding="utf-8")
    score = evaluate(tmp_path)
    assert score["fresh_closes"] == 1
    assert score["book_closes"] == 2
    assert score["promoted"] is False
    rule = next(row for row in score["rules"] if row["rule"] == "ALL_ENTRY_FILTERS")
    assert rule["fresh_evaluable"] == 1
    assert rule["pass_stats"] is False
    assert rule["red_team"] == "NOT_SURVIVED"
    assert "SURVIVED_RED_TEAM" not in rule["reasons"]
    text = (tmp_path / "reports" / "grok" / "PAPER" / "mega6_red_team.json").read_text(encoding="utf-8")
    assert "SURVIVED_RED_TEAM" not in text


def test_gold_trail_records_a_price_and_does_not_set_a_reason(tmp_path: Path) -> None:
    registry = tmp_path / "reports" / "grok" / "PAPER" / "mega6_preregistration.json"
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(json.dumps({"registered_at": "2026-10-30T12:00:00Z"}), encoding="utf-8")
    pos = {
        "desk": "GOLD", "side": "LONG", "entry_price": 100.0, "stop_pct": 0.01,
        "opened_at": "2026-10-30T15:00:00Z", "opened_ts": 1_000_000,
    }
    note_gold_path(tmp_path, pos, 102.0, 1_000_100)
    assert "shadow_trail_exit_price" not in pos
    note_gold_path(tmp_path, pos, 100.5, 1_000_200)
    assert pos["shadow_trail_exit_price"] == 100.5
    assert "reason" not in pos
    note_gold_path(tmp_path, pos, 101.0, 1_000_000 + 6 * 3600 + 1)
    assert pos["shadow_time_exit_price"] == 101.0


def test_soak_resume_keeps_the_halt_and_the_counters() -> None:
    resumed = _resume_soak_state({
        "cycles_ok": 10,
        "cycles_failed": 1,
        "last_day_report": "2026-10-30",
        "health": {"latched": True},
        "last_tier_gate": {"tier": "T0"},
        "window_started_utc": "2026-10-29T00:45:31Z",
    })
    assert resumed["cycles_ok"] == 10
    assert resumed["latched_halt"] is True
    assert resumed["last_day"] == "2026-10-30"
    assert resumed["tier"]["tier"] == "T0"
