"""Crypto futures stay a paper swap book: 1x, 10% equity, public marks only."""
from __future__ import annotations

import json
import time
from pathlib import Path

from architecture.markets import paper_trader as pt
from architecture.markets.crypto_futures_paper import (
    EQUITY_CAP,
    FEE,
    LEVERAGE_CAP,
    SLIP,
    book_notional_cap,
    funding_cashflow,
    leverage_decision,
    liquidation_price,
    parse_binance_mark,
    parse_okx_funding,
    parse_okx_mark,
    simulated_liquidation,
)
from architecture.markets.paper_trade_gates import MIN_AGREEING_FAMILIES, MIN_EXPECTED_PROFIT_TO_FEE_RATIO
from architecture.markets.paper_trader import INSTRUMENTS


def _bars(start: float, n: int = 40) -> list[list[float]]:
    return [[start, start + 0.2, start - 0.2, start, 10.0] for _ in range(n)]


def test_futures_news_uses_the_same_crypto_terms() -> None:
    from architecture.markets.signal_brain import ASSET_TERMS, news_signal

    assert ASSET_TERMS["CRYPTO_FUTURES"] == ASSET_TERMS["CRYPTO"]
    sig = news_signal("CRYPTO_FUTURES", [])
    assert sig["name"] == "news"


def test_leverage_stays_one_and_the_book_cap_is_ten_percent(tmp_path: Path) -> None:
    fresh = leverage_decision(tmp_path, requested=1.5)
    assert fresh["applied"] == 1.0
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
    assert held["applied"] == LEVERAGE_CAP == 1.0
    assert held["lock"] == "EVIDENCE_INCOMPLETE"
    assert book_notional_cap(100.0, 9.5) == 0.5
    assert EQUITY_CAP == 0.10
    assert "architecture.markets.margin" not in Path("architecture/markets/crypto_futures_paper.py").read_text(encoding="utf-8")


def test_funding_sign_and_liquidation_price_are_fixed() -> None:
    assert funding_cashflow("LONG", 10.0, 0.0001, 8 * 3600) == -0.001
    assert funding_cashflow("SHORT", 10.0, 0.0001, 8 * 3600) == 0.001
    assert round(liquidation_price("LONG", 100.0) or 0, 10) == 0.5
    assert round(liquidation_price("SHORT", 100.0) or 0, 6) == 199.5
    assert simulated_liquidation("LONG", 0.4, 0.5) is True
    assert simulated_liquidation("SHORT", 200.0, 199.5) is True
    px, _ts = parse_okx_mark({"data": [{"markPx": "100.5", "ts": "1760000000000"}]})
    assert px == 100.5
    assert parse_okx_funding({"data": [{"fundingRate": "0.0001"}]}) == 0.0001
    assert parse_binance_mark({"markPrice": "100.4"}) == 100.4
    assert INSTRUMENTS["BTC"][0] == "CRYPTO"
    assert INSTRUMENTS["BTC-SWAP"] == ("CRYPTO_FUTURES", FEE, SLIP)
    assert MIN_AGREEING_FAMILIES == 2
    assert MIN_EXPECTED_PROFIT_TO_FEE_RATIO == 2.0


def test_swap_open_is_capped_and_liquidation_is_paper(tmp_path: Path) -> None:
    t = [1_800_000_000.0]
    px = {"p": 100.0, "rate": 0.0001}

    def fetch():
        mt = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t[0]))
        return {"quotes": {"BTC-SWAP": {
            "price": px["p"], "source": "okx:BTC-USDT-SWAP", "market_time": mt,
            "ohlcv_5m": _bars(px["p"]), "funding_rate_8h": px["rate"],
        }}}

    def fb():
        return {"BTC-SWAP": {"price": px["p"] * 1.0001, "source": "binance:BTCUSDT"}}

    def sig(sym, desk, q):
        return [{"name": "mtf_trend", "score": 0.8, "available": True, "source": "swap", "spec": "paper",
                 "evidence": {"higher_tf_sign": 1}}]

    pt.run_cycle(tmp_path, fetch=fetch, fetch_b=fb, signals_fn=sig, now=lambda: t[0], use_ledger=False)
    rows = [json.loads(line) for line in (tmp_path / "reports/grok/PAPER/paper_trades.jsonl").read_text(encoding="utf-8").splitlines()]
    opened = [r for r in rows if r["event"] == "OPEN" and r["symbol"] == "BTC-SWAP"]
    assert len(opened) == 1
    assert opened[0]["side"] == "LONG"
    assert opened[0]["notional_usd"] <= 10.0
    assert opened[0]["brain"]["futures"]["applied"] == 1.0
    assert opened[0]["brain"]["futures"]["lock"] == "EVIDENCE_INCOMPLETE"
    state = json.loads((tmp_path / "reports/grok/PAPER/paper_positions.json").read_text(encoding="utf-8"))
    pos = state["positions"]["BTC-SWAP"]
    assert pos["leverage"] == 1.0
    assert pos["liquidation_price"] < 1.0
    t[0] += 8 * 3600
    px["p"] = pos["liquidation_price"] * 0.5
    pt.run_cycle(tmp_path, fetch=fetch, fetch_b=fb, signals_fn=sig, now=lambda: t[0], use_ledger=False)
    closed = [json.loads(line) for line in (tmp_path / "reports/grok/PAPER/paper_trades.jsonl").read_text(encoding="utf-8").splitlines()]
    close = next(r for r in closed if r["event"] == "CLOSE" and r["symbol"] == "BTC-SWAP")
    assert close["reason"] == "SIMULATED_LIQUIDATION"
    assert close["funding_usd"] < 0
    after = json.loads((tmp_path / "reports/grok/PAPER/paper_positions.json").read_text(encoding="utf-8"))
    assert "BTC-SWAP" not in after["positions"]
    assert "BTC" not in after["positions"]
