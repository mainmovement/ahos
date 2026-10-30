"""Dynamic tokens: fresh safety snapshot, locked or burned LP, one name, shock exits."""
from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from architecture.markets import paper_trader as pt
from architecture.markets.paper_trade_gates import MIN_AGREEING_FAMILIES, MIN_EXPECTED_PROFIT_TO_FEE_RATIO
from architecture.markets.token_safety_live import (
    DEX_MAX_HOLD_S,
    DYNAMIC_TOKEN_EQUITY,
    SNAPSHOT_REL,
    dex_risk_exit,
    dynamic_token_block,
    lp_lock_or_burn,
    refresh_safety_snapshot_if_due,
    veto_check,
)


TOK = "0x00000000000000000000000000000000000000aa"


def _gp(**over):
    row = {
        "is_honeypot": "0", "buy_tax": "0", "sell_tax": "0", "is_open_source": "1", "is_mintable": "0",
        "holders": [{"address": "0xbb", "percent": "0.05", "is_locked": 0, "is_contract": 0}],
        "lp_holders": [{"address": "0x000000000000000000000000000000000000dead", "percent": "0.80", "is_locked": "1"}],
    }
    row.update({k: "0" for k in (
        "is_proxy", "hidden_owner", "can_take_back_ownership", "owner_change_balance",
        "selfdestruct", "cannot_sell_all", "transfer_pausable", "slippage_modifiable",
        "personal_slippage_modifiable", "cannot_buy")})
    row.update(over)
    return {"result": {TOK: row}}


def _getter(gp):
    def g(url):
        if "gopluslabs" in url:
            return gp
        if "honeypot.is" in url:
            return {"simulationSuccess": True, "honeypotResult": {"isHoneypot": False},
                    "simulationResult": {"buyTax": 0.2, "sellTax": 0.3}, "contractCode": {"openSource": True}}
        if "dexscreener.com/latest" in url:
            return {"pairs": [
                {"pairAddress": "0x00000000000000000000000000000000000000p1", "dexId": "uniswap",
                 "baseToken": {"address": TOK}, "priceUsd": "1.0", "liquidity": {"usd": 400000},
                 "volume": {"h24": 900000}, "fdv": 5_000_000},
                {"pairAddress": "0x00000000000000000000000000000000000000p2", "dexId": "sushiswap",
                 "baseToken": {"address": TOK}, "priceUsd": "1.0", "liquidity": {"usd": 120000},
                 "volume": {"h24": 200000}},
            ]}
        return None
    return g


def test_live_defaults_refresh_the_snapshot_before_quotes(monkeypatch, tmp_path: Path) -> None:
    order: list[str] = []

    def refresh(root, **kwargs):
        order.append("refresh")
        return {"refreshed": False}

    def fetch():
        order.append("fetch")
        return {"quotes": {}}

    monkeypatch.setattr("architecture.markets.token_safety_live.refresh_safety_snapshot_if_due", refresh)
    monkeypatch.setattr("architecture.markets.live_price_feed.fetch_live_market_prices", fetch)
    monkeypatch.setattr(
        pt, "gather_witness",
        lambda quotes, **k: {
            s: {"verdict": "UNRESOLVED", "source_b": None, "price_b": None, "gap": None}
            for s in set(quotes) | set(pt.INSTRUMENTS)
        },
    )
    monkeypatch.setattr(pt, "live_dex_feed", lambda root, positions: {})
    monkeypatch.setattr("architecture.markets.signal_brain.fetch_news", lambda *a, **k: [])
    pt.run_cycle(tmp_path, now=lambda: 1_800_000_000.0, use_ledger=False)
    assert order[:2] == ["refresh", "fetch"]


def test_strict_path_requires_locked_or_burned_lp() -> None:
    locked = veto_check("GOOD", TOK, getter=_getter(_gp()), strict=True)
    assert locked["verdict"] == "ELIGIBLE_PAPER_TOKEN", locked["reasons"]
    burned = lp_lock_or_burn([{"address": "0x000000000000000000000000000000000000dead", "percent": "60", "is_locked": "0"}])
    assert burned["ok"] is True and burned["share"] == 0.6
    unlocked = veto_check(
        "GOOD", TOK,
        getter=_getter(_gp(lp_holders=[{"address": "0xabc", "percent": "1", "is_locked": "0"}])),
        strict=True,
    )
    assert unlocked["verdict"] == "VETOED_SECURITY"
    assert any("lp_not_locked_or_burned" in r for r in unlocked["reasons"])
    missing = veto_check("GOOD", TOK, getter=_getter(_gp(lp_holders=[])), strict=True)
    assert missing["verdict"] == "VETOED_FAIL_CLOSED"
    assert "goplus:lp_lock_or_burn_missing" in missing["reasons"]
    assert MIN_AGREEING_FAMILIES == 2
    assert MIN_EXPECTED_PROFIT_TO_FEE_RATIO == 2.0
    assert DYNAMIC_TOKEN_EQUITY == 0.02


def test_stale_snapshot_refreshes_and_a_failed_refresh_stays_closed(tmp_path: Path) -> None:
    now = datetime(2026, 10, 30, 12, 0, tzinfo=timezone.utc)
    path = tmp_path / SNAPSHOT_REL
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"generated_at": "2026-10-30T11:00:00Z", "paper_tradable_dynamic": []}), encoding="utf-8")
    called = {"n": 0}

    def getter(url):
        called["n"] += 1
        return None

    fresh = refresh_safety_snapshot_if_due(tmp_path, getter=getter, now=now)
    assert fresh["refreshed"] is False and called["n"] == 0
    stale = refresh_safety_snapshot_if_due(tmp_path, getter=getter, now=now + timedelta(hours=5))
    assert stale["refreshed"] is True and called["n"] > 0

    def boom(url):
        raise RuntimeError("down")

    path.write_text(json.dumps({"generated_at": "2026-10-30T00:00:00Z"}), encoding="utf-8")
    failed = refresh_safety_snapshot_if_due(tmp_path, getter=boom, now=now)
    assert failed["refreshed"] is False and failed["error"] == "REFRESH_FAILED"
    assert "2026-10-30T00:00:00Z" in path.read_text(encoding="utf-8")


def test_one_dynamic_name_and_shock_exits(tmp_path: Path) -> None:
    assert dynamic_token_block("UNI", {"DEX_AAA": {}}) is None
    assert dynamic_token_block("DEX_BBB", {"DEX_AAA": {}}) == "ONE_DYNAMIC_TOKEN"
    pos = {"entry_liquidity_usd": 100000.0, "entry_dev_balance": 1000.0}
    assert dex_risk_exit("DEX_AAA", pos, {"liquidity_usd": 40000, "dev_balance": 1000}, 10) == "LIQUIDITY_DROP"
    assert dex_risk_exit("DEX_AAA", pos, {"liquidity_usd": 100000, "dev_balance": 800}, 10) == "DEV_WALLET_SELL"
    assert dex_risk_exit("DEX_AAA", pos, {"liquidity_usd": 100000, "dev_balance": None}, 10) is None
    assert dex_risk_exit("DEX_AAA", pos, {"liquidity_usd": 100000, "dev_balance": 1000}, DEX_MAX_HOLD_S + 1) == "MAX_HOLD"
    assert dex_risk_exit("UNI", pos, {"liquidity_usd": 1}, DEX_MAX_HOLD_S + 1) is None

    t = [1_800_000_000.0]
    mt = lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t[0]))
    state_path = tmp_path / "reports/grok/PAPER/paper_positions.json"
    state_path.parent.mkdir(parents=True)
    state_path.write_text(json.dumps({"positions": {"DEX_AAA": {
        "side": "LONG", "entry_price": 1.0, "qty": 1.0, "notional_usd": 1.0, "entry_fee_usd": 0.001,
        "opened_at": mt(), "opened_ts": t[0] - 60, "desk": "PB_TOKEN", "stop_pct": 0.05,
        "entry_liquidity_usd": 100000.0, "entry_dev_balance": 1000.0,
    }}, "brain": {}}), encoding="utf-8")

    def feed(root, positions):
        q = {"price": 1.0, "source": "dex", "market_time": mt(), "ohlcv_5m": [[1, 1.01, 0.99, 1, 10]] * 40,
             "liquidity_usd": 100000, "dev_balance": 1000}
        w = {"verdict": "VERIFIED", "source_a": "a", "price_a": 1.0, "source_b": "b", "price_b": 1.0, "gap": 0.0}
        return {"DEX_BBB": (q, w)}

    def sig(sym, desk, q):
        return [{"name": "mtf_trend", "score": 0.8, "available": True, "source": "dex", "spec": "paper",
                 "evidence": {"higher_tf_sign": 1}}]

    pt.run_cycle(tmp_path, fetch=lambda: {"quotes": {}}, fetch_b=lambda: {}, signals_fn=sig,
                 dex_feed=feed, now=lambda: t[0], use_ledger=False)
    rows = [json.loads(line) for line in (tmp_path / "reports/grok/PAPER/paper_trades.jsonl").read_text(encoding="utf-8").splitlines()]
    assert any(r["symbol"] == "DEX_BBB" and r["reason"] == "ONE_DYNAMIC_TOKEN" for r in rows)
    assert not any(r["event"] == "OPEN" and r["symbol"] == "DEX_BBB" for r in rows)
