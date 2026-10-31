from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import importlib.util

from architecture.markets.free_data_cache import classify, last_z, parse_fred_csv, parse_french_factors
from architecture.markets.gold_path_sidecar import atr_pct_from_bars, log_open_positions
from architecture.markets.mega14_restart import due, is_restart_target
from architecture.markets.spread_sampler import estimate_row, sample

_SPEC = importlib.util.spec_from_file_location(
    "mega14_restart_checklist",
    Path(__file__).resolve().parents[1] / "scripts" / "mega14_restart_checklist.py",
)
_RESTART = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_RESTART)


def test_one_print_is_not_a_z_and_eight_are():
    assert last_z([0.1, 0.2]) is None
    score = last_z([0.01, 0.02, 0.01, 0.02, 0.01, 0.015, 0.012, 0.05])
    assert score is not None and score > 0


def test_french_and_fred_parsers_do_not_invent_a_loading_or_a_consensus():
    factors = parse_french_factors("junk\n,Mkt-RF,SMB,HML,RF\n192607,2.62,-2.16,-2.23,0.22\n")
    assert factors == [{"mkt_rf": 2.62, "smb": -2.16, "hml": -2.23}]
    assert parse_fred_csv("DATE,CPIAUCSL\n2020-01-01,257.9\n") == [("2020-01-01", 257.9)]
    rows = classify({
        "french": {"n": 3},
        "fred": {"n": 4},
        "cot": {"status": "READY"},
        "funding": {"funding_z": 1.2, "oi_z": -0.4},
        "ohlc": {"bars": 2, "reason": "NO_INTRADAY_OHLC"},
        "earnings": {"dates": ["2026-01-01"]},
        "liquidations": {"reason": "NO_KEYLESS_LIQUIDATION_PRINT"},
        "second_contract": {"reason": "NO_SECOND_CONTRACT"},
    })
    by = {row["strategy"]: row for row in rows}
    assert by["fama_french"]["data"] == "UNAVAILABLE"
    assert by["fama_french"]["reason"] == "FACTORS_HAVE_NO_NAME_LOADING"
    assert by["macro_surprise"]["reason"] == "FRED_HAS_ACTUAL_NOT_CONSENSUS"
    assert by["cot_extreme"]["data"] == "READY"
    assert by["funding_oi_squeeze"]["data"] == "READY"
    assert by["pead"]["reason"] == "NO_EARNINGS_SURPRISE"
    assert all(row["promoted"] is False for row in rows)


def test_sidecar_logs_path_without_writing_positions(tmp_path):
    positions_path = tmp_path / "reports" / "grok" / "PAPER" / "paper_positions.json"
    positions_path.parent.mkdir(parents=True)
    positions_path.write_text('{"positions":{"XAU":{"desk":"GOLD","side":"LONG","entry_price":1}}}', encoding="utf-8")
    before = positions_path.read_bytes()
    highs = [10, 11, 12, 11, 13]
    lows = [9, 10, 11, 10, 12]
    closes = [9.5, 10.5, 11.5, 10.5, 12.5]
    rows = log_open_positions(
        tmp_path,
        {"XAU": {"desk": "GOLD", "side": "LONG", "entry_price": 10.0, "mark_price": 12.5}},
        bars={"XAU": {"highs": highs, "lows": lows, "closes": closes, "bid": 12.4, "ask": 12.6}},
        pid=1,
    )
    assert positions_path.read_bytes() == before
    assert rows[0]["mid"] == 12.5
    assert rows[0]["atr_pct"] == atr_pct_from_bars(highs, lows, closes)
    assert rows[0]["writes_positions"] is False
    ledger = (tmp_path / "reports" / "grok" / "PAPER" / "gold_path_ledger.jsonl").read_text(encoding="utf-8")
    assert json.loads(ledger)["desk"] == "GOLD"


def test_spread_row_is_an_unquoted_estimate(tmp_path):
    row = estimate_row("NASDAQ:INTC", 10.0, 9.0, 9.5)
    assert row["quoted"] is False
    doc = sample(tmp_path, {"NASDAQ:INTC": {"high": 10, "low": 9, "close": 9.5}}, symbols=["NASDAQ:INTC"])
    assert doc["rows"][0]["source"] == "tradingview_session_range"
    assert doc["applied_to_live"] is False


def test_restart_checklist_waits_and_spares_the_listener(capsys):
    assert due(datetime(2026, 10, 31, tzinfo=timezone.utc)) == "WAIT"
    assert _RESTART.main(now=datetime(2026, 10, 31, tzinfo=timezone.utc)) == 0
    assert capsys.readouterr().out.strip() == "WAIT"
    assert is_restart_target(r"G:\robat\ahos\scripts\m13_gold_soak.py") is True
    assert is_restart_target(r"G:\robat\ahos\run_bot.py") is False
