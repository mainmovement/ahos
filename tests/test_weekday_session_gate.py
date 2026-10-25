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


def test_contribution_identity_and_side_split_claim_no_edge(tmp_path):
    import json

    from architecture.markets.paper_trade_audit import (
        measure_contribution_identity, measure_dominant_signal, measure_entry_regime, measure_side_book,
    )

    paper = tmp_path / "reports" / "grok" / "PAPER"
    paper.mkdir(parents=True)
    (paper / "paper_trades.jsonl").write_text("\n".join([
        json.dumps({"event": "CLOSE", "symbol": "ETH", "side": "LONG", "realized_pnl_usd": 0.02,
                    "entry_brain": {"composite": 0.3, "contributions": [
                        {"signal": "mtf_trend", "score": 0.3, "weight": 1.0, "contribution": 0.3}],
                        "regime": {"hmm_state": "HIGH", "ratio": 1.0}}}),
        json.dumps({"event": "CLOSE", "symbol": "BTC", "side": "SHORT", "realized_pnl_usd": -0.05,
                    "entry_brain": {"composite": -0.4, "contributions": [
                        {"signal": "large_trades", "score": -0.4, "weight": 1.0, "contribution": -0.4}],
                        "regime": {"hmm_state": "HIGH", "ratio": 1.0}}}),
    ]) + "\n", encoding="utf-8")
    identity = measure_contribution_identity(tmp_path)
    assert identity["status"] == "IDENTITY_WITHIN_ROUNDING" and identity["max_abs_gap"] == 0.0
    assert identity["beyond_rounding"] == 0 and identity["edge_claimed"] is False
    dominant = measure_dominant_signal(tmp_path)
    assert dominant["status"] == "LARGEST_TERM_SHARES_THE_SIDE" and dominant["skill_claimed"] is False
    assert dominant["sign_matches_side"] == 2
    assert {item["signal"] for item in dominant["signals"]} == {"mtf_trend", "large_trades"}
    sides = measure_side_book(tmp_path)
    assert sides["edge_claimed"] is False and sides["realized_pnl_usd"] == -0.03
    assert sides["sides"][0]["side"] == "LONG" and sides["sides"][0]["wins"] == 1
    regime = measure_entry_regime(tmp_path)
    assert regime["status"] == "TOO_SMALL_TO_COMPARE" and regime["comparison_claimed"] is False
    assert regime["largest_hmm_cell"] == 2
    assert regime["schemas"] == [{"schema": "HMM_WITH_RATIO", "rows": 2}]


def test_conflict_exit_can_stay_positive_without_becoming_a_reversal(tmp_path):
    import json

    from architecture.markets.paper_trade_audit import (
        measure_exit_score_path, measure_hold_by_reason, measure_signal_breadth,
    )

    paper = tmp_path / "reports" / "grok" / "PAPER"
    paper.mkdir(parents=True)
    (paper / "paper_trades.jsonl").write_text("\n".join([
        json.dumps({
            "event": "CLOSE", "symbol": "ETH", "side": "LONG", "reason": "WITNESS_CONFLICT_EXIT",
            "exit_composite": 0.11, "opened_at": "2026-10-25T00:00:00Z", "closed_at": "2026-10-25T01:00:00Z",
            "entry_brain": {"composite": 0.3, "contributions": [
                {"signal": "a", "weight": 0.4, "contribution": 0.12},
                {"signal": "b", "weight": 0.4, "contribution": 0.12}]}}),
        json.dumps({
            "event": "CLOSE", "symbol": "BTC", "side": "SHORT", "reason": "SIGNAL_REVERSAL",
            "exit_composite": 0.3, "opened_at": "2026-10-25T00:00:00Z", "closed_at": "2026-10-25T02:00:00Z",
            "entry_brain": {"composite": -0.4, "contributions": [
                {"signal": "a", "weight": 0.4, "contribution": -0.16}]}}),
    ]) + "\n", encoding="utf-8")
    path = measure_exit_score_path(tmp_path)
    assert path["status"] == "PATH_RECORDED" and path["exit_rule_changed"] is False and path["edge_claimed"] is False
    by_reason = {item["reason"]: item for item in path["reasons"]}
    assert by_reason["WITNESS_CONFLICT_EXIT"]["positive_below_entry"] == 1
    assert by_reason["WITNESS_CONFLICT_EXIT"]["at_or_above_entry"] == 0
    assert by_reason["SIGNAL_REVERSAL"]["at_or_beyond_reversal"] == 1
    assert by_reason["SIGNAL_REVERSAL"]["delta_min"] == -0.7
    held = measure_hold_by_reason(tmp_path)
    assert held["exit_inferred"] is False and held["status"] == "ALL_TIMESTAMPS_PRESENT"
    assert {item["reason"]: item["hold_hours_max"] for item in held["reasons"]} == {
        "SIGNAL_REVERSAL": 2.0, "WITNESS_CONFLICT_EXIT": 1.0}
    breadth = measure_signal_breadth(tmp_path)
    assert breadth["minimum_changed"] is False and breadth["edge_claimed"] is False
    assert breadth["signal_count_min"] == 1 and breadth["signal_count_max"] == 2
    assert breadth["weight_sum_below_1"] == 2 and breadth["weight_sum_below_half"] == 1


def test_take_profit_uses_the_quote_and_dissent_removes_nothing(tmp_path):
    import json

    from architecture.markets.paper_trade_audit import (
        measure_exit_slippage, measure_exit_trigger, measure_signal_dissent,
    )

    paper = tmp_path / "reports" / "grok" / "PAPER"
    paper.mkdir(parents=True)
    (paper / "paper_trades.jsonl").write_text("\n".join([
        json.dumps({"event": "OPEN", "symbol": "ETH", "stop_pct": 0.02}),
        json.dumps({
            "event": "CLOSE", "symbol": "ETH", "side": "LONG", "reason": "TAKE_PROFIT",
            "entry_price": 100.0, "quote_price": 103.0, "fill_price": 102.5,
            "entry_brain": {"contributions": [
                {"signal": "mtf_trend", "score": 0.5, "weight": 0.5},
                {"signal": "macro_event", "score": 0.0, "weight": 0.3},
                {"signal": "zscore_mr", "score": -0.2, "weight": 0.2}]}}),
        json.dumps({"event": "OPEN", "symbol": "BTC", "stop_pct": 0.02}),
        json.dumps({
            "event": "CLOSE", "symbol": "BTC", "side": "LONG", "reason": "WITNESS_CONFLICT_EXIT",
            "entry_price": 100.0, "quote_price": 100.5, "fill_price": 100.4,
            "entry_brain": {"contributions": [
                {"signal": "mtf_trend", "score": 0.4, "weight": 0.6},
                {"signal": "exchange_netflow", "score": -0.1, "weight": 0.4}]}}),
    ]) + "\n", encoding="utf-8")
    trigger = measure_exit_trigger(tmp_path)
    assert trigger["status"] == "RULE_CONSISTENT" and trigger["exit_rule_changed"] is False
    assert trigger["take_profit_quote_beyond"] == 1 and trigger["fill_inside_take_line"] == 1
    assert trigger["other_quote_beyond"] == 0 and trigger["stop_crossed"] == 0
    dissent = measure_signal_dissent(tmp_path)
    assert dissent["signals_removed"] is False and dissent["skill_claimed"] is False
    assert dissent["contribution_agree"] == 2 and dissent["contribution_oppose"] == 2
    assert dissent["contribution_zero"] == 1 and dissent["closes_with_opposition"] == 2
    assert dissent["always_zero"] == ["macro_event"]
    assert dissent["always_opposes"] == ["exchange_netflow", "zscore_mr"]
    slip = measure_exit_slippage(tmp_path)
    assert slip["added_to_cash_gap"] is False and slip["edge_claimed"] is False
    assert slip["drag_sum"] == 0.006 and slip["status"] == "DRAG_RECORDED"


def test_missing_path_is_not_zero_and_the_cost_table_holds(tmp_path):
    import json

    from architecture.markets.paper_trade_audit import (
        measure_cost_schedule, measure_path_storage, measure_take_field,
    )

    paper = tmp_path / "reports" / "grok" / "PAPER"
    paper.mkdir(parents=True)
    (paper / "paper_trades.jsonl").write_text("\n".join([
        json.dumps({
            "event": "OPEN", "symbol": "ETH", "notional_usd": 10.0, "fee_usd": 0.01,
            "slippage_pct": 0.0005, "stop_pct": 0.01014, "take_pct": 0.0152}),
        json.dumps({"event": "HOLD", "symbol": "ETH"}),
        json.dumps({
            "event": "CLOSE", "symbol": "ETH", "side": "LONG", "reason": "TAKE_PROFIT",
            "slippage_pct": 0.0005}),
        json.dumps({
            "event": "OPEN", "symbol": "DEX_LINK", "notional_usd": 8.0, "fee_usd": 0.024,
            "slippage_pct": 0.002, "stop_pct": 0.02, "take_pct": 0.03}),
        json.dumps({
            "event": "CLOSE", "symbol": "DEX_LINK", "side": "SHORT", "reason": "SIGNAL_REVERSAL",
            "slippage_pct": 0.002}),
    ]) + "\n", encoding="utf-8")
    path = measure_path_storage(tmp_path)
    assert path["status"] == "PATH_NOT_STORED" and path["path_backfilled"] is False
    assert path["missing_mae"] == 2 and path["missing_path_points"] == 2
    assert path["hold_rows"] == 1 and path["hold_with_mfe"] == 0 and path["exit_inferred"] is False
    take = measure_take_field(tmp_path)
    assert take["status"] == "WITHIN_STORAGE_PRECISION" and take["multiple_changed"] is False
    assert take["within_storage"] == 2 and take["beyond_storage"] == 0
    cost = measure_cost_schedule(tmp_path)
    assert cost["status"] == "SCHEDULE_HELD" and cost["schedule_changed"] is False
    assert cost["edge_claimed"] is False and cost["close_fee_compared"] is False
    assert cost["open_fee_mismatch"] == 0 and cost["close_slip_mismatch"] == 0


def test_witness_reason_matches_and_the_fee_splits(tmp_path):
    import json

    from architecture.markets.paper_trade_audit import (
        measure_equity_replay, measure_fee_decomposition, measure_witness_reason,
    )

    paper = tmp_path / "reports" / "grok" / "PAPER"
    paper.mkdir(parents=True)
    (paper / "paper_trades.jsonl").write_text("\n".join([
        json.dumps({
            "event": "OPEN", "symbol": "ETH", "notional_usd": 10.0, "fee_usd": 0.01,
            "equity_at_open_usd": 100.0, "witness": {"verdict": "VERIFIED"}}),
        json.dumps({
            "event": "CLOSE", "symbol": "ETH", "side": "LONG", "reason": "TAKE_PROFIT",
            "notional_usd": 10.0, "qty": 0.1, "fill_price": 102.0, "fees_usd": 0.0202,
            "realized_pnl_usd": -0.02, "witness": {"verdict": "VERIFIED"}}),
        json.dumps({
            "event": "OPEN", "symbol": "BTC", "notional_usd": 10.0, "fee_usd": 0.01,
            "equity_at_open_usd": 99.98, "witness": {"verdict": "VERIFIED"}}),
        json.dumps({
            "event": "CLOSE", "symbol": "BTC", "side": "LONG", "reason": "WITNESS_CONFLICT_EXIT",
            "notional_usd": 10.0, "qty": 0.2, "fill_price": 50.0, "fees_usd": 0.02,
            "realized_pnl_usd": -0.01, "witness": {"verdict": "CONFLICT"}}),
    ]) + "\n", encoding="utf-8")
    witness = measure_witness_reason(tmp_path)
    assert witness["status"] == "VERDICT_MATCHES_REASON" and witness["exit_rule_changed"] is False
    assert witness["conflict_rows"] == 1 and witness["conflict_verdict_conflict"] == 1
    assert witness["other_verdict_verified"] == 1 and witness["open_verified"] == 2
    fee = measure_fee_decomposition(tmp_path)
    assert fee["status"] == "FEE_DECOMPOSED" and fee["added_to_cash_gap"] is False
    assert fee["within_band"] == 2 and fee["beyond_band"] == 0 and fee["edge_claimed"] is False
    equity = measure_equity_replay(tmp_path)
    assert equity["status"] == "WITHIN_ONE_CENT" and equity["equity_rewritten"] is False
    assert equity["beyond_cent"] == 0 and equity["max_abs_gap"] == 0.0
    assert equity["end_equity_usd"] == 99.97 and equity["added_to_cash_gap"] is False


def test_quote_age_stays_inside_the_gate_and_addresses_are_not_copied(tmp_path):
    import json

    from architecture.markets.paper_trade_audit import (
        measure_book_overlap, measure_quote_age, measure_source_address,
    )
    from architecture.markets.paper_trader import logged_source

    paper = tmp_path / "reports" / "grok" / "PAPER"
    paper.mkdir(parents=True)
    (paper / "paper_trades.jsonl").write_text("\n".join([
        json.dumps({
            "event": "OPEN", "symbol": "BTC", "ts": "2026-10-25T00:00:00Z",
            "market_time": "2026-10-25T00:00:10Z", "source": "coingecko:bitcoin"}),
        json.dumps({
            "event": "CLOSE", "symbol": "BTC", "ts": "2026-10-25T00:10:00Z",
            "market_time": "2026-10-25T00:09:00Z", "opened_at": "2026-10-25T00:00:00Z",
            "closed_at": "2026-10-25T00:10:00Z", "source": "coingecko:bitcoin"}),
        json.dumps({
            "event": "OPEN", "symbol": "DEX_LINK", "ts": "2026-10-25T00:20:00Z",
            "market_time": "2026-10-25T00:20:00Z", "source": "geckoterminal:0xabc"}),
    ]) + "\n", encoding="utf-8")
    age = measure_quote_age(tmp_path)
    assert age["status"] == "WITHIN_STALE_GATE" and age["gate_changed"] is False
    assert age["open_over_gate"] == 0 and age["close_over_gate"] == 0
    assert age["open_clock_ahead"] == 1 and age["open_ahead_max_s"] == 10.0
    source = measure_source_address(tmp_path)
    assert source["status"] == "ADDRESS_ON_LOG" and source["log_rewritten"] is False
    assert source["open_with_address"] == 1 and source["close_with_address"] == 0
    assert "0x" not in json.dumps(source).lower()
    book = measure_book_overlap(tmp_path)
    assert book["status"] == "NO_OVERLAP" and book["positions_closed"] is False
    assert book["overlap_opens"] == 0 and book["still_open"] == ["DEX_LINK"]
    assert book["opened_at_matches_open_ts"] == 1 and book["closed_at_matches_ts"] == 1
    assert logged_source("geckoterminal:0xabc") == "geckoterminal"
    assert logged_source("coingecko:bitcoin") == "coingecko:bitcoin"
    assert logged_source(None) is None


def test_refusals_stay_on_their_side_of_the_gate_and_size_stays_inside(tmp_path):
    import json

    from architecture.markets.paper_trade_audit import (
        measure_quantity_identity, measure_refusal_gate, measure_size_cap,
    )

    paper = tmp_path / "reports" / "grok" / "PAPER"
    paper.mkdir(parents=True)
    (paper / "paper_trades.jsonl").write_text("\n".join([
        json.dumps({"event": "NO_TRADE", "reason": "COMPOSITE_BELOW_ENTRY", "composite": 0.2}),
        json.dumps({"event": "NO_TRADE", "reason": "HIGHER_TF_DISAGREES", "composite": -0.3}),
        json.dumps({
            "event": "OPEN", "symbol": "BTC", "desk": "CRYPTO", "qty": 0.01, "fill_price": 100.0,
            "notional_usd": 1.0, "equity_at_open_usd": 100.0, "stop_pct": 0.02,
            "brain": {"regime": {"size_mult": 1.0}}}),
        json.dumps({
            "event": "CLOSE", "symbol": "BTC", "qty": 0.1, "entry_price": 100.0, "notional_usd": 10.0}),
    ]) + "\n", encoding="utf-8")
    refusal = measure_refusal_gate(tmp_path)
    assert refusal["status"] == "GATE_HELD" and refusal["gate_changed"] is False
    assert refusal["below_inside"] == 1 and refusal["below_outside"] == 0
    assert refusal["other_at_or_above"] == 1 and refusal["below_abs_max"] == 0.2
    qty = measure_quantity_identity(tmp_path)
    assert qty["status"] == "QTY_MATCHES" and qty["added_to_cash_gap"] is False
    assert qty["within_band"] == 2 and qty["beyond_band"] == 0 and qty["max_abs_gap"] == 0.0
    size = measure_size_cap(tmp_path)
    assert size["status"] == "INSIDE_DESK_AND_RISK" and size["caps_changed"] is False
    assert size["kelly_switched_on"] is False and size["event_size_defaulted"] == 1
    assert size["risk_above"] == 0 and size["desk_above"] == 0


def test_adv_cap_and_regime_multiple_match_the_stored_open(tmp_path):
    import json

    from architecture.markets.paper_trade_audit import (
        measure_adv_cap, measure_higher_tf, measure_regime_multiple,
    )

    paper = tmp_path / "reports" / "grok" / "PAPER"
    paper.mkdir(parents=True)
    (paper / "paper_trades.jsonl").write_text("\n".join([
        json.dumps({
            "event": "OPEN", "symbol": "BTC", "side": "LONG",
            "brain": {
                "regime": {"regime": "NORMAL", "size_mult": 1.0},
                "adv_cap": {
                    "allowed": True, "notional_usd": 1.0, "cap_1pct_usd": 100.0,
                    "adv_source": "vendor_24h_volume", "participation_rate": 0.0001,
                },
                "signals": [{"name": "mtf_trend", "evidence": {"higher_tf_sign": 1}}],
            }}),
        json.dumps({
            "event": "OPEN", "symbol": "ETH", "side": "SHORT",
            "brain": {"regime": {"regime": "UNKNOWN", "size_mult": 0.5}}}),
    ]) + "\n", encoding="utf-8")
    adv = measure_adv_cap(tmp_path)
    assert adv["status"] == "CAP_HELD" and adv["cap_changed"] is False and adv["edge_claimed"] is False
    assert adv["stored_rows"] == 1 and adv["missing_object"] == 1 and adv["assumed_floor_rows"] == 0
    assert adv["allowed_mismatch"] == 0 and "0x" not in json.dumps(adv).lower()
    regime = measure_regime_multiple(tmp_path)
    assert regime["status"] == "MULTIPLE_MATCHES" and regime["multiple_changed"] is False
    assert regime["matched_rows"] == 2 and regime["unknown_rows"] == 1 and regime["haircut_rows"] == 0
    higher = measure_higher_tf(tmp_path)
    assert higher["status"] == "SIGN_AGREES" and higher["rule_changed"] is False
    assert higher["agree_rows"] == 1 and higher["disagree_rows"] == 0 and higher["missing_rows"] == 1


def test_pnl_matches_gross_minus_fees_and_a_stored_approval_is_not_authority(tmp_path):
    import json

    from architecture.markets.paper_trade_audit import (
        measure_debate_claim, measure_gross_sign, measure_pnl_identity,
    )

    paper = tmp_path / "reports" / "grok" / "PAPER"
    paper.mkdir(parents=True)
    rows = [
        {
            "event": "OPEN", "symbol": "BTC", "side": "LONG",
            "brain": {"council_debate": {
                "approved_paper": True, "swap_gate_passed": True,
                "brier_judge": 0.2, "ece_judge": 0.1, "status": "APPROVED_SOROUSH_BL",
            }},
        },
        {"event": "OPEN", "symbol": "ETH", "side": "SHORT"},
        {"event": "CLOSE", "symbol": "BTC", "side": "LONG", "reason": "TAKE_PROFIT",
         "entry_price": 100.0, "fill_price": 110.0, "qty": 0.01, "fees_usd": 0.001,
         "realized_pnl_usd": 0.099},
        {"event": "CLOSE", "symbol": "ETH", "side": "SHORT", "reason": "SIGNAL_REVERSAL",
         "entry_price": 100.0, "fill_price": 90.0, "qty": 0.01, "fees_usd": 0.002,
         "realized_pnl_usd": 0.098},
        {"event": "CLOSE", "symbol": "SOL", "side": "SHORT", "reason": "WITNESS_CONFLICT_EXIT",
         "entry_price": 100.0, "fill_price": 110.0, "qty": 0.01, "fees_usd": 0.001,
         "realized_pnl_usd": -0.101},
    ]
    (paper / "paper_trades.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    pnl = measure_pnl_identity(tmp_path)
    assert pnl["status"] == "PNL_IDENTITY" and pnl["added_to_cash_gap"] is False
    assert pnl["edge_claimed"] is False and pnl["beyond_band"] == 0 and pnl["max_abs_gap"] == 0.0
    gross = measure_gross_sign(tmp_path)
    assert gross["status"] == "GROSS_RECORDED" and gross["edge_claimed"] is False
    assert gross["exit_rule_changed"] is False
    assert gross["gross_positive"] == 2 and gross["gross_negative"] == 1
    debate = measure_debate_claim(tmp_path)
    assert debate["status"] == "STORED_CLAIM_NOT_AUTHORITY"
    assert debate["authority_used"] is False and debate["log_rewritten"] is False
    assert debate["stored_rows"] == 1 and debate["missing_rows"] == 1
    assert debate["approved_true"] == 1 and debate["brier_present"] == 1
    assert "0x" not in json.dumps(debate).lower()
