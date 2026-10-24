import json, time
from architecture.markets import paper_trader as pt
from architecture.markets.paper_account import paper_account_summary

def _bars(start, step, n=40):
    out, p = [], start
    for _ in range(n):
        out.append([p, p + step * 1.2 if step > 0 else p + 0.01, p - 0.01 if step > 0 else p + step * 1.2, p + step, 10.0]); p += step
    return out

def _sig(score):
    return lambda sym, desk, q: [{"name": "mtf_trend", "score": score, "available": True, "source": "fx", "spec": "§2",
                                 "evidence": {"higher_tf_sign": 1 if score > 0 else -1}}]

def _rows(root):
    return [json.loads(l) for l in (root / "reports/grok/PAPER/paper_trades.jsonl").read_text().splitlines()]

def test_two_source_gate_open_close_compounds(tmp_path):
    t = [1_800_000_000.0]; px = {"p": 120.0}
    mt = lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t[0]))
    fetch = lambda: {"quotes": {"BTC": {"price": px["p"], "source": "A", "market_time": mt(), "ohlcv_5m": _bars(100, 0.5)},
                                "ETH": {"price": 50.0, "source": "A", "market_time": mt(), "ohlcv_5m": _bars(50, 0.1)},
                                "XAU": {"price": 10.0, "source": "A", "market_time": "2026-01-01T00:00:00Z"}}}
    fb = lambda: {"BTC": {"price": px["p"] * 1.0005, "source": "B"}, "ETH": {"price": 60.0, "source": "B"}}
    pt.run_cycle(tmp_path, fetch=fetch, fetch_b=fb, signals_fn=_sig(0.8), now=lambda: t[0], use_ledger=False)
    r = _rows(tmp_path)
    o = [x for x in r if x["event"] == "OPEN"]
    assert len(o) == 1 and o[0]["symbol"] == "BTC" and o[0]["fill_price"] > 120.0 and o[0]["brain"]["contributions"]
    assert any(x["symbol"] == "ETH" and x["reason"] == "WITNESS_CONFLICT" for x in r)
    assert any(x["symbol"] == "XAU" and x["reason"] == "MARKET_CLOSED_OR_STALE" for x in r)
    assert paper_account_summary(tmp_path)["current_equity_usd"] == 100.0
    t[0] += 300; px["p"] = 130.0
    st = pt.run_cycle(tmp_path, fetch=fetch, fetch_b=fb, signals_fn=_sig(0.8), now=lambda: t[0], use_ledger=False)
    c = [x for x in _rows(tmp_path) if x["event"] == "CLOSE"]
    assert c and c[0]["reason"] == "TAKE_PROFIT" and c[0]["fees_usd"] > 0 and c[0]["realized_pnl_usd"] > 0
    assert st["realized_equity_usd"] > 100.0 and st["performance"]["n"] == 1
    assert (tmp_path / "reports/grok/PAPER/signal_lessons.jsonl").is_file()

def test_kill_switch_blocks_new_risk():
    now = 1_800_000_000.0
    trades = [{"realized_pnl_usd": -4.0, "closed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now - 60))}]
    assert pt.kill_switch(trades, 100.0, now)[0] is True

def test_witness_verdicts():
    from architecture.markets.second_source import witness
    assert witness("BTC", {"price": 100}, {"price": 100.2})["verdict"] == "VERIFIED"
    assert witness("BTC", {"price": 100}, {"price": 102})["verdict"] == "CONFLICT"
    assert witness("BTC", {"price": 100}, None)["verdict"] == "UNRESOLVED"
