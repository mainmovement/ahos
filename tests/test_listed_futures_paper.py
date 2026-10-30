"""Listed futures stay a paper book: 1x, 10% equity, Yahoo plus a second witness."""
from __future__ import annotations

import json
import time
from datetime import date, datetime, timezone
from pathlib import Path

from architecture.markets import paper_trader as pt
from architecture.markets.listed_futures_paper import (
    EQUITY_CAP,
    LEVERAGE_CAP,
    OMITTED,
    book_notional_cap,
    last_trade_date,
    leverage_decision,
    liquidation_price,
    overlay_cash_witnesses,
    roll_due,
    simulated_liquidation,
)
from architecture.markets.paper_trade_gates import MIN_AGREEING_FAMILIES, MIN_EXPECTED_PROFIT_TO_FEE_RATIO
from architecture.markets.paper_trader import CLUSTER_CAPS, DESK_WEIGHTS, INSTRUMENTS
from architecture.markets.second_source import TV_FUTURES_ROOT, TV_MAP
from architecture.markets.weekday_session_gate import symbol_session


def _bars(start: float, n: int = 40) -> list[list[float]]:
    return [[start, start + 0.2, start - 0.2, start, 10.0] for _ in range(n)]


def _quote(ts: float, price: float, month: str | None) -> dict:
    mt = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))
    q = {"price": price, "source": "yahoo_finance:ES=F", "market_time": mt, "ohlcv_5m": _bars(price)}
    if month:
        q["contract_month"] = month
    return q


def test_near_month_needs_one_yahoo_contract() -> None:
    from architecture.markets.listed_futures_paper import near_contract_month

    cont = {"price": 7675.0, "_regular_market_time": 1_700_000_000.0}

    def fetch(code: str):
        px = 7675.5 if code.startswith("ESZ") else 7600.0
        return {"chart": {"result": [{"meta": {"regularMarketPrice": px, "regularMarketTime": 1_700_000_000.0}}]}}

    hit = near_contract_month("ES", cont, fetch=fetch, now_ts=1_700_000_000.0, tol=0.0035)
    assert hit is not None and hit["contract_month"].endswith("-12")

    def both(code: str):
        return {"chart": {"result": [{"meta": {"regularMarketPrice": 7675.2, "regularMarketTime": 1_700_000_000.0}}]}}

    assert near_contract_month("ES", cont, fetch=both, now_ts=1_700_000_000.0, tol=0.0035) is None


def test_calendar_roll_and_omitted_fdax() -> None:
    assert last_trade_date("CL", 2026, 12) == date(2026, 11, 20)
    assert last_trade_date("BZ", 2026, 12) == date(2026, 10, 30)
    assert last_trade_date("GC", 2026, 12) == date(2026, 12, 29)
    assert last_trade_date("ES", 2026, 12) == date(2026, 12, 18)
    assert last_trade_date("NQ", 2026, 12) == date(2026, 12, 18)
    assert last_trade_date("NKD", 2026, 12) == date(2026, 12, 10)
    assert roll_due("CL", "2026-12", date(2026, 11, 15)) is True
    assert roll_due("CL", "2026-12", date(2026, 11, 14)) is False
    assert roll_due("ES", None, date(2026, 12, 1)) is False
    assert "FDAX" in OMITTED
    assert "FDAX" not in INSTRUMENTS
    assert "NKD" in INSTRUMENTS
    assert INSTRUMENTS["WTI"][0] == "OIL"
    assert INSTRUMENTS["CL"][0] == "LISTED_FUTURES"
    assert DESK_WEIGHTS["LISTED_FUTURES"] == EQUITY_CAP == 0.10
    assert CLUSTER_CAPS["listed_futures"] == 0.10
    assert CLUSTER_CAPS["crypto_futures"] == 0.10
    assert TV_MAP["ES"] == "CME_MINI:ES1!"
    assert TV_MAP["NQ"] == "CME_MINI:NQ1!"
    assert TV_MAP["NKD"] == "CME:NKD1!"
    assert "CL" not in TV_MAP
    assert TV_FUTURES_ROOT["ES"] == "CME_MINI:ES"
    book = {"WTI": {"price": 100.0, "source": "tradingview:NYMEX:CL1!"}}
    overlay_cash_witnesses(book)
    assert book["CL"]["source"] == "tradingview:NYMEX:CL1!"
    assert "ES" not in book


def test_overnight_session_is_not_the_cash_index_session() -> None:
    # Wednesday 22:00 America/New_York. NYSE cash is closed. Globex is in its overnight session.
    moment = datetime(2026, 10, 29, 2, 0, tzinfo=timezone.utc)
    es = symbol_session("ES", moment)
    spx = symbol_session("SPX", moment)
    assert es["venue"] == "CME_GLOBEX" and es["open"] is True
    assert spx["venue"] == "NYSE" and spx["open"] is False
    assert symbol_session("BZ", moment)["venue"] == "ICE_BRENT"
    weekend = datetime(2026, 10, 31, 16, 0, tzinfo=timezone.utc)
    assert symbol_session("ES", weekend)["open"] is False
    assert symbol_session("NKD", weekend)["open"] is False


def test_leverage_stays_one_and_liquidation_is_a_deep_move(tmp_path: Path) -> None:
    fresh = leverage_decision(tmp_path, requested=3.0)
    assert fresh["applied"] == LEVERAGE_CAP == 1.0
    assert fresh["lock"] == "EVIDENCE_INCOMPLETE"
    obs = tmp_path / "reports" / "grok" / "PAPER" / "family_vote_observations.jsonl"
    obs.parent.mkdir(parents=True, exist_ok=True)
    obs.write_text(
        "\n".join([
            json.dumps({"ts": "2026-10-01T00:00:00Z"}),
            json.dumps({"ts": "2026-10-09T00:00:00Z"}),
        ]),
        encoding="utf-8",
    )
    held = leverage_decision(tmp_path, requested=2.0)
    assert held["applied"] == 1.0
    assert held["lock"] == "EVIDENCE_INCOMPLETE"
    assert book_notional_cap(100.0, 9.5) == 0.5
    assert round(liquidation_price("LONG", 100.0) or 0, 10) == 5.0
    assert round(liquidation_price("SHORT", 100.0) or 0, 10) == 195.0
    assert simulated_liquidation("LONG", 4.0, 5.0) is True
    assert simulated_liquidation("SHORT", 196.0, 195.0) is True
    src = Path("architecture/markets/listed_futures_paper.py").read_text(encoding="utf-8")
    assert "high_leverage_futures_engine" not in src
    assert "architecture.markets.margin" not in src
    assert MIN_AGREEING_FAMILIES == 2
    assert MIN_EXPECTED_PROFIT_TO_FEE_RATIO == 2.0


def test_listed_open_is_capped_and_rolls_or_liquidates(tmp_path: Path) -> None:
    t = [datetime(2026, 10, 29, 2, 0, tzinfo=timezone.utc).timestamp()]
    px = {"p": 100.0, "month": "2026-12"}

    def fetch():
        return {"quotes": {"CL": _quote(t[0], px["p"], px["month"]) | {"source": "yahoo_finance:CL=F"}}}

    def fb():
        return {"CL": {"price": px["p"], "source": "tradingview:NYMEX:CL1!"}}

    def sig(sym, desk, q):
        return [{"name": "mtf_trend", "score": 0.8, "available": True, "source": "listed", "spec": "paper",
                 "evidence": {"higher_tf_sign": 1}}]

    pt.run_cycle(tmp_path, fetch=fetch, fetch_b=fb, signals_fn=sig, now=lambda: t[0], use_ledger=False)
    rows = [json.loads(line) for line in (tmp_path / "reports/grok/PAPER/paper_trades.jsonl").read_text(encoding="utf-8").splitlines()]
    opened = [r for r in rows if r["event"] == "OPEN" and r["symbol"] == "CL"]
    assert len(opened) == 1
    assert opened[0]["side"] == "LONG"
    assert opened[0]["notional_usd"] <= 10.0
    assert opened[0]["brain"]["listed_futures"]["applied"] == 1.0
    state = json.loads((tmp_path / "reports/grok/PAPER/paper_positions.json").read_text(encoding="utf-8"))
    pos = state["positions"]["CL"]
    assert pos["leverage"] == 1.0
    assert pos["contract_month"] == "2026-12"
    assert pos["initial_margin_usd"] == pos["notional_usd"]
    assert "WTI" not in state["positions"]
    t[0] = datetime(2026, 11, 16, 18, 0, tzinfo=timezone.utc).timestamp()
    pt.run_cycle(tmp_path, fetch=fetch, fetch_b=fb, signals_fn=sig, now=lambda: t[0], use_ledger=False)
    closed = [json.loads(line) for line in (tmp_path / "reports/grok/PAPER/paper_trades.jsonl").read_text(encoding="utf-8").splitlines()]
    close = next(r for r in closed if r["event"] == "CLOSE" and r["symbol"] == "CL")
    assert close["reason"] == "CONTRACT_ROLL"


def test_missing_month_and_weekend_do_not_open(tmp_path: Path) -> None:
    t = [datetime(2026, 10, 29, 2, 0, tzinfo=timezone.utc).timestamp()]

    def fetch():
        return {"quotes": {"NQ": _quote(t[0], 20000.0, None)}}

    def fb():
        return {"NQ": {"price": 20000.0, "source": "tradingview:CME_MINI:NQ1!"}}

    def sig(sym, desk, q):
        return [{"name": "mtf_trend", "score": -0.8, "available": True, "source": "listed", "spec": "paper",
                 "evidence": {"higher_tf_sign": -1}}]

    pt.run_cycle(tmp_path, fetch=fetch, fetch_b=fb, signals_fn=sig, now=lambda: t[0], use_ledger=False)
    rows = [json.loads(line) for line in (tmp_path / "reports/grok/PAPER/paper_trades.jsonl").read_text(encoding="utf-8").splitlines()]
    nq = next(r for r in rows if r["symbol"] == "NQ" and r["event"] == "NO_TRADE")
    assert nq["reason"] == "CONTRACT_MONTH_UNKNOWN"
    t[0] = datetime(2026, 10, 31, 16, 0, tzinfo=timezone.utc).timestamp()

    def fetch_es():
        return {"quotes": {"ES": _quote(t[0], 7000.0, "2026-12")}}

    def fb_es():
        return {"ES": {"price": 7000.0, "source": "tradingview:CME_MINI:ES1!"}}

    pt.run_cycle(tmp_path, fetch=fetch_es, fetch_b=fb_es, signals_fn=sig, now=lambda: t[0], use_ledger=False)
    rows = [json.loads(line) for line in (tmp_path / "reports/grok/PAPER/paper_trades.jsonl").read_text(encoding="utf-8").splitlines()]
    es = [r for r in rows if r["symbol"] == "ES" and r["event"] == "SKIP"][-1]
    assert es["reason"] == "SESSION_CLOSED"


def test_simulated_liquidation_flattens_without_touching_the_cash_book(tmp_path: Path) -> None:
    t = [datetime(2026, 10, 29, 2, 0, tzinfo=timezone.utc).timestamp()]
    px = {"p": 100.0}

    def fetch():
        q = _quote(t[0], px["p"], "2026-12")
        q["source"] = "yahoo_finance:GC=F"
        return {"quotes": {"GC": q}}

    def fb():
        return {"GC": {"price": px["p"], "source": "tradingview:COMEX:GC1!"}}

    def sig(sym, desk, q):
        return [{"name": "mtf_trend", "score": -0.8, "available": True, "source": "listed", "spec": "paper",
                 "evidence": {"higher_tf_sign": -1}}]

    pt.run_cycle(tmp_path, fetch=fetch, fetch_b=fb, signals_fn=sig, now=lambda: t[0], use_ledger=False)
    state = json.loads((tmp_path / "reports/grok/PAPER/paper_positions.json").read_text(encoding="utf-8"))
    pos = state["positions"]["GC"]
    assert pos["side"] == "SHORT"
    assert "XAU" not in state["positions"]
    t[0] += 300
    px["p"] = pos["liquidation_price"] + 1.0
    pt.run_cycle(tmp_path, fetch=fetch, fetch_b=fb, signals_fn=sig, now=lambda: t[0], use_ledger=False)
    closed = [json.loads(line) for line in (tmp_path / "reports/grok/PAPER/paper_trades.jsonl").read_text(encoding="utf-8").splitlines()]
    close = next(r for r in closed if r["event"] == "CLOSE" and r["symbol"] == "GC")
    assert close["reason"] == "SIMULATED_LIQUIDATION"
