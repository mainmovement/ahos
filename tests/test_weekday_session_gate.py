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
        measure_conflict_anatomy, measure_dex_roundtrip,
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
    assert conflict["mapped_rows"] == 2 and conflict["dex_rows"] == 0
    with (paper / "paper_trades.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(
            '{"event":"OPEN","symbol":"DEX_LINK","desk":"PB_TOKEN","notional_usd":25}\n'
            '{"event":"CLOSE","symbol":"DEX_LINK","desk":"PB_TOKEN","reason":"WITNESS_CONFLICT_EXIT",'
            '"realized_pnl_usd":-0.02,"opened_at":"2026-10-24T00:00:00Z","closed_at":"2026-10-24T01:00:00Z",'
            '"witness":{"verdict":"CONFLICT","gap":0.008,"source_b":"dexscreener:pool"}}\n')
    pool = measure_conflict_anatomy(tmp_path)
    assert pool["within_tolerance"] == 2 and pool["within_spot_default"] == 1
    assert pool["dex_rows"] == 1 and pool["inconsistent_with_current_tolerance"] == 2
    assert pool["source_kinds"]["dexscreener"] == 1
    trip = measure_dex_roundtrip(tmp_path)
    assert trip["flat"] is True and trip["realized_pnl_usd"] == -0.02 and trip["edge_claimed"] is False
    reversal = write_reversal_anatomy(tmp_path)
    assert reversal["status"] == "MATCHES_RECORDED_THRESHOLD"
    assert reversal["signed_composite_min"] == -0.3 and reversal["exit_rule_changed"] is False
    skips = write_skip_census(tmp_path)
    assert skips["dominant_reason"] == "MARKET_CLOSED_OR_STALE" and skips["event_rows"] == 1


def test_symbol_book_keeps_opposite_signs_and_open_rows_are_not_exits(tmp_path):
    import json
    from datetime import datetime, timezone

    from architecture.markets.paper_trade_audit import (
        measure_open_book, measure_stored_witness_fields, measure_symbol_book,
    )
    from architecture.markets.paper_trader import logged_witness

    paper = tmp_path / "reports" / "grok" / "PAPER"
    paper.mkdir(parents=True)
    (paper / "paper_trades.jsonl").write_text("\n".join([
        json.dumps({"event": "OPEN", "symbol": "UNI", "desk": "PB_TOKEN", "side": "LONG",
                    "opened_at": "2026-10-25T00:00:00Z"}),
        json.dumps({"event": "CLOSE", "symbol": "UNI", "desk": "PB_TOKEN", "reason": "TAKE_PROFIT",
                    "realized_pnl_usd": 0.1746}),
        json.dumps({"event": "OPEN", "symbol": "DEX_LINK", "desk": "PB_TOKEN", "side": "LONG",
                    "opened_at": "2026-10-25T01:00:00Z"}),
        json.dumps({"event": "CLOSE", "symbol": "DEX_LINK", "desk": "PB_TOKEN", "reason": "WITNESS_CONFLICT_EXIT",
                    "realized_pnl_usd": -0.1231, "witness": {"verdict": "CONFLICT", "gap": 0.0102}}),
        json.dumps({"event": "OPEN", "symbol": "ETH", "desk": "CRYPTO", "side": "SHORT",
                    "opened_at": "2026-10-25T06:00:00Z"}),
    ]) + "\n", encoding="utf-8")
    (paper / "paper_positions.json").write_text(json.dumps({"positions": {"ETH": {"desk": "CRYPTO"}}}), encoding="utf-8")
    book = measure_symbol_book(tmp_path)
    by_symbol = {item["symbol"]: item["realized_pnl_usd"] for item in book["symbols"]}
    assert by_symbol["UNI"] == 0.1746 and by_symbol["DEX_LINK"] == -0.1231
    assert book["account_realized_pnl_usd"] == 0.0515 and book["edge_claimed"] is False
    assert book["unassigned_desks"] == 0
    pb = next(item for item in book["desks"] if item["desk"] == "PB_TOKEN")
    assert pb["realized_pnl_usd"] == 0.0515 and pb["rounded_usd"] == 0.05
    opened = measure_open_book(tmp_path, now=datetime(2026, 10, 25, 8, 0, tzinfo=timezone.utc))
    assert opened["status"] == "INSIDE_BOTH_LIMITS" and opened["exit_inferred"] is False
    assert opened["open_rows"] == [{"symbol": "ETH", "desk": "CRYPTO", "side": "SHORT", "open_time": "2026-10-25T06:00:00Z"}]
    assert opened["log_matches_positions_file"] is True and opened["unmatched_closes"] == 0
    stored = measure_stored_witness_fields(tmp_path)
    assert stored["tolerance_stored"] == 0 and stored["pair_stored"] == 0 and stored["exit_rule_changed"] is False
    copied = logged_witness({
        "verdict": "CONFLICT", "source_b": "dexscreener:pool", "price_b": 1.0, "gap": 0.011,
        "tolerance": 0.01, "pair": "POOL-POOL", "diagnostics": {"pool": "0xabc"},
    })
    assert copied["tolerance"] == 0.01 and copied["pair"] == "POOL-POOL" and "diagnostics" not in copied
    hidden = logged_witness({
        "verdict": "CONFLICT", "source_b": "dexscreener:pool", "price_b": 1.0, "gap": 0.011,
        "pair": "pool32:0123456789abcdef",
    })
    assert "pair" not in hidden and "tolerance" not in hidden


def test_entry_gate_is_not_a_probability_and_kelly_stays_off(tmp_path):
    import json

    from architecture.markets.paper_trade_audit import (
        measure_entry_gate, measure_fee_identity, measure_kelly_label, measure_weight_vintage,
    )

    paper = tmp_path / "reports" / "grok" / "PAPER"
    paper.mkdir(parents=True)
    (paper / "paper_trades.jsonl").write_text("\n".join([
        json.dumps({"event": "OPEN", "symbol": "ETH", "side": "LONG", "fee_usd": 0.01,
                    "kelly": "OFF (n<30 closed trades, §6)"}),
        json.dumps({"event": "CLOSE", "symbol": "ETH", "side": "LONG", "reason": "TAKE_PROFIT",
                    "realized_pnl_usd": 0.02, "fees_usd": 0.03,
                    "entry_brain": {"composite": 0.3, "weights_version": 1}}),
        json.dumps({"event": "OPEN", "symbol": "BTC", "side": "SHORT", "fee_usd": 0.02,
                    "kelly": "OFF (n<30 closed trades, §6)"}),
        json.dumps({"event": "CLOSE", "symbol": "BTC", "side": "SHORT", "reason": "SIGNAL_REVERSAL",
                    "realized_pnl_usd": -0.05, "fees_usd": 0.04,
                    "entry_brain": {"composite": -0.4, "weights_version": 1}}),
        json.dumps({"event": "OPEN", "symbol": "SOL", "side": "SHORT", "fee_usd": 0.01,
                    "kelly": "OFF (n<30 closed trades, §6)"}),
    ]) + "\n", encoding="utf-8")
    gate = measure_entry_gate(tmp_path)
    assert gate["status"] == "GATE_HELD_NOT_A_PROBABILITY" and gate["brier"] is None
    assert gate["signed_min"] == 0.3 and gate["signed_max"] == 0.4
    assert gate["wins"] == 1 and gate["losses"] == 1 and gate["raw_outside_unit_interval"] == 1
    assert gate["edge_claimed"] is False and gate["gate_changed"] is False
    kelly = measure_kelly_label(tmp_path)
    assert kelly["status"] == "UNIFORM_OFF_LABEL" and kelly["kelly_switched_on"] is False
    assert kelly["numeric_rows"] == 0 and kelly["open_rows"] == 3
    fees = measure_fee_identity(tmp_path)
    assert fees["added_to_cash_gap"] is False and fees["status"] == "IDENTITY_OF_THE_LOG"
    assert fees["net_pnl_usd"] == -0.03 and fees["close_fees_usd"] == 0.07
    assert fees["implied_gross_usd"] == 0.04 and fees["still_open_entry_fee_usd"] == 0.01
    assert fees["closed_entry_fee_usd"] == 0.03 and fees["edge_claimed"] is False
    vintage = measure_weight_vintage(tmp_path)
    assert vintage["status"] == "TOO_SMALL_TO_COMPARE" and vintage["comparison_claimed"] is False
    assert vintage["largest_cell"] == 2 and vintage["versions"][0]["realized_pnl_usd"] == -0.03
