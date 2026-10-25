from __future__ import annotations

from datetime import datetime, timezone

from architecture.markets.weekday_session_gate import is_weekend_tehran, session_report, tehran_now


def test_saturday_tehran_is_weekend():
    # 2026-10-24 08:00 UTC = 11:30 Tehran Saturday
    u = datetime(2026, 10, 24, 8, 0, tzinfo=timezone.utc)
    assert is_weekend_tehran(u) is True
    rep = session_report(u)
    assert rep["weekend_tehran"] is True
    assert rep["cash_desks_expected"] == "CLOSED_OR_STALE"


def test_tehran_offset():
    u = datetime(2026, 10, 24, 4, 30, tzinfo=timezone.utc)
    t = tehran_now(u)
    assert t.hour == 8


def test_sunday_stale_probe_does_not_open_a_cash_desk(tmp_path):
    import json
    from architecture.markets.weekday_witness_probe import build_weekday_two_source_audit
    moment = datetime(2026, 10, 25, 7, 38, tzinfo=timezone.utc)
    probe = tmp_path / "reports" / "grok" / "PAPER" / "weekday_witness_probe.json"
    probe.parent.mkdir(parents=True)
    probe.write_text(json.dumps({
        "session_gate": {"utc": "2026-10-24T18:08:00Z"},
        "by_desk": {"CRYPTO": [{"symbol": "BTC", "verdict": "VERIFIED"}],
                    "GOLD": [{"symbol": "XAU", "verdict": "VERIFIED"}]},
    }), encoding="utf-8")
    snap = build_weekday_two_source_audit(tmp_path, moment)
    assert snap["weekend_tehran"] is True and snap["network_fetch"] is False
    assert snap["tradable_symbols"] == []
    btc = next(row for row in snap["rows"] if row["symbol"] == "BTC")
    xau = next(row for row in snap["rows"] if row["symbol"] == "XAU")
    assert btc["stored_verdict"] == "VERIFIED" and btc["live_witness"] == "STALE_STORED_PROBE"
    assert xau["session_open"] is False and xau["tradable_for_paper"] is False


def test_linked_close_cash_is_zero_and_a_different_pnl_is_not(tmp_path):
    import json
    from architecture.mission.ledger import MissionLedger
    from architecture.treasury.reconcile import paper_cash_double_entry
    ledger_path = tmp_path / "data" / "mission_ledger" / "mission_ledger.jsonl"
    ledger_path.parent.mkdir(parents=True)
    ledger = MissionLedger(ledger_path)
    entry = ledger.decision({"type": "PAPER_FILL", "event": "CLOSE", "symbol": "BTC", "side": "LONG",
                             "realized_pnl_usd": 1.25}, agent="agent:paper_trader")
    paper = tmp_path / "reports" / "grok" / "PAPER"
    paper.mkdir(parents=True)
    (paper / "paper_trades.jsonl").write_text(json.dumps({
        "event": "CLOSE", "symbol": "BTC", "side": "LONG", "ledger_hash": entry["entry_hash"],
        "realized_pnl_usd": 1.25,
    }) + "\n", encoding="utf-8")
    snap = paper_cash_double_entry(tmp_path)
    assert snap["verdict"] == "MEASURED_ZERO" and snap["discrepancy_usd"] == 0.0
    assert snap["recorded_on_ledger"] is False
    (paper / "paper_trades.jsonl").write_text(json.dumps({
        "event": "CLOSE", "symbol": "BTC", "side": "LONG", "ledger_hash": entry["entry_hash"],
        "realized_pnl_usd": 2.0,
    }) + "\n", encoding="utf-8")
    drifted = paper_cash_double_entry(tmp_path)
    assert drifted["verdict"] == "MEASURED_NONZERO" and drifted["discrepancy_usd"] == 0.75


def test_fee_coverage_stays_a_label_and_pb_token_joins_the_desk_map(tmp_path):
    import json
    from architecture.markets.paper_account import paper_account_summary
    from architecture.markets.paper_trade_audit import write_exit_reason_census
    from architecture.treasury.reconcile import write_fee_coverage
    paper = tmp_path / "reports" / "grok" / "PAPER"
    paper.mkdir(parents=True)
    (paper / "paper_trades.jsonl").write_text(
        json.dumps({"event": "OPEN", "symbol": "UNI", "desk": "PB_TOKEN", "fee_usd": 0.1}) + "\n"
        + json.dumps({"event": "CLOSE", "symbol": "UNI", "desk": "PB_TOKEN", "reason": "SIGNAL_REVERSAL",
                      "fees_usd": 0.2, "realized_pnl_usd": -0.05, "partial": False}) + "\n",
        encoding="utf-8")
    fee = write_fee_coverage(tmp_path)
    assert fee["coverage_status"] == "ITEMIZED_ON_JSONL_NOT_ON_LEDGER"
    assert fee["open_fee_usd_sum"] == 0.1 and fee["close_fees_usd_sum"] == 0.2
    assert fee["rewritten"] is False and fee["ledger_fills_with_fee_usd"] == 0
    census = write_exit_reason_census(tmp_path)
    assert census["close_rows"] == 1 and census["reason_counts"] == {"SIGNAL_REVERSAL": 1}
    assert census["partial_rows"] == 0 and census["daemon_restarted"] is False
    summary = paper_account_summary(tmp_path)
    assert "PB_TOKEN" in summary["per_desk_realized_pnl_usd"]
    assert summary["per_desk_realized_pnl_usd"]["PB_TOKEN"] == -0.05
    assert abs(sum(summary["per_desk_realized_pnl_usd"].values()) - summary["realized_pnl_usd"]) <= 0.02


def test_conflict_and_reversal_anatomies_match_the_log(tmp_path):
    import json
    from architecture.markets.paper_trade_audit import (
        write_conflict_anatomy, write_reversal_anatomy, write_skip_census,
    )
    paper = tmp_path / "reports" / "grok" / "PAPER"
    paper.mkdir(parents=True)
    (paper / "paper_trades.jsonl").write_text("\n".join([
        json.dumps({"event": "HOLD", "symbol": "BTC", "witness": {"verdict": "VERIFIED", "gap": 0.001}}),
        json.dumps({"event": "CLOSE", "symbol": "BTC", "reason": "WITNESS_CONFLICT_EXIT", "side": "LONG",
                    "opened_at": "2026-10-25T00:00:00Z", "closed_at": "2026-10-25T01:00:00Z",
                    "witness": {"verdict": "CONFLICT", "gap": 0.01}}),
        json.dumps({"event": "CLOSE", "symbol": "ETH", "reason": "WITNESS_CONFLICT_EXIT", "side": "LONG",
                    "opened_at": "2026-10-25T00:00:00Z", "closed_at": "2026-10-25T02:00:00Z",
                    "witness": {"verdict": "CONFLICT", "gap": 0.001}}),
        json.dumps({"event": "CLOSE", "symbol": "BTC", "reason": "SIGNAL_REVERSAL", "side": "LONG",
                    "exit_composite": -0.3, "entry_price": 100.0, "fill_price": 99.0,
                    "opened_at": "2026-10-25T00:00:00Z", "closed_at": "2026-10-25T03:00:00Z"}),
        json.dumps({"event": "SKIP", "symbol": "SPX", "reason": "MARKET_CLOSED_OR_STALE"}),
    ]) + "\n", encoding="utf-8")
    conflict = write_conflict_anatomy(tmp_path)
    assert conflict["rows"] == 2 and conflict["exit_rule_changed"] is False
    assert conflict["prior_conflict_zero"] == 2 and conflict["within_tolerance"] == 1
    assert conflict["gap_min"] == 0.001 and conflict["gap_max"] == 0.01
    assert conflict["symbols"] == {"BTC": 1, "ETH": 1}
    reversal = write_reversal_anatomy(tmp_path)
    assert reversal["status"] == "MATCHES_RECORDED_THRESHOLD"
    assert reversal["signed_composite_min"] == -0.3 and reversal["exit_rule_changed"] is False
    skips = write_skip_census(tmp_path)
    assert skips["dominant_reason"] == "MARKET_CLOSED_OR_STALE" and skips["event_rows"] == 1
