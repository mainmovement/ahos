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

def test_close_writes_m49_lesson_and_oms(tmp_path):
    from architecture.learning.lessons_ledger import LessonsLedger
    t = [1_800_000_000.0]; px = {"p": 120.0}
    mt = lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t[0]))
    fetch = lambda: {"quotes": {"BTC": {"price": px["p"], "source": "A", "market_time": mt(), "ohlcv_5m": _bars(100, 0.5)}}}
    fb = lambda: {"BTC": {"price": px["p"], "source": "B"}}
    pt.run_cycle(tmp_path, fetch=fetch, fetch_b=fb, signals_fn=_sig(0.8), now=lambda: t[0], use_ledger=False)
    assert [r for r in _rows(tmp_path) if r["event"] == "OPEN"][0]["oms"] == "ACCEPTED_PAPER"
    t[0] += 300; px["p"] = 100.0
    pt.run_cycle(tmp_path, fetch=fetch, fetch_b=fb, signals_fn=_sig(0.8), now=lambda: t[0], use_ledger=False)
    st = LessonsLedger(tmp_path / "data/mission_ledger/m49_lessons.sqlite")
    rows = st.all_rows(); assert len(rows) == 1 and rows[0].status == "UNVERIFIED" and "lost" in rows[0].claim and st.verify()
    assert rows[0].counterfactual == pt.LESSON_COUNTERFACTUAL
    assert "agreed" not in rows[0].counterfactual
    st.close()


def test_range_vol_matches_the_textbook_estimators_and_refuses_a_short_sample():
    from architecture.markets.signal_brain import book_depth_features, funding_zscore, range_vol
    import math
    bars = [[100.0, 102.0, 99.0, 101.0, 1.0] for _ in range(8)]
    got = range_vol(bars)
    hl = math.log(102.0 / 99.0)
    park = math.sqrt((hl * hl) / (4.0 * math.log(2.0)))
    co = math.log(101.0 / 100.0)
    gk = math.sqrt(0.5 * hl * hl - (2.0 * math.log(2.0) - 1.0) * co * co)
    assert abs(got["parkinson_vol"] - park) < 1e-8
    assert abs(got["garman_klass_vol"] - gk) < 1e-8
    assert range_vol(bars[:3])["parkinson_vol"] is None
    book = book_depth_features(
        [[100, 2], [99, 2], [98, 2], [97, 2], [96, 2]],
        [[101, 1], [102, 1], [103, 1], [104, 1], [105, 1]] + [[110, 20]] * 15,
    )
    assert book["imbalance_top5"] > 0 and book["imbalance_top20"] < 0 and book["depth_disagreement"] is True
    assert book["bid_slope_log"] is not None
    assert funding_zscore(0.01, [0.0] * 7) is None
    z = funding_zscore(0.03, [0.0, 0.01] * 4)
    assert z is not None and z > 0


def test_chandelier_only_tightens_and_a_single_mark_is_not_an_excursion(tmp_path):
    from architecture.markets.execution_microstructure_audit import build_microstructure_audit
    pos = {"side": "LONG", "entry_price": 100.0, "stop_pct": 0.01, "qty": 1.0, "notional_usd": 100.0,
           "entry_fee_usd": 0.1, "opened_ts": 0.0, "opened_at": "t0"}
    pt._mark_excursion(pos, 103.0, 0.005)
    assert pos["chandelier_stop"] > 100.0 * 0.99
    first = pos["chandelier_stop"]
    pt._mark_excursion(pos, 102.0, 0.005)
    assert pos["chandelier_stop"] >= first - 1e-9
    assert pt._chandelier_hit(pos, pos["chandelier_stop"] - 0.01) is True
    flat = {"side": "LONG", "entry_price": 100.0, "stop_pct": 0.01, "qty": 1.0, "notional_usd": 10.0,
            "entry_fee_usd": 0.01, "opened_ts": 0.0, "opened_at": "t0", "partial_taken": False}
    move = pt._mark_excursion(flat, 100.05, 0.005)
    assert abs(move) < pt.TIME_STOP_MOVE_FRAC * flat["stop_pct"]
    audit = build_microstructure_audit(tmp_path)
    assert audit["paper_only"] is True and audit["closed_count"] == 0
    (tmp_path / "reports/grok/PAPER").mkdir(parents=True)
    (tmp_path / "reports/grok/PAPER/paper_trades.jsonl").write_text(
        json.dumps({"event": "CLOSE", "symbol": "BTC", "realized_pnl_usd": 0.2, "fees_usd": 0.05,
                    "slippage_pct": 0.001, "notional_usd": 10.0, "mae": -0.01, "mfe": 0.02, "path_points": 1}) + "\n",
        encoding="utf-8")
    audited = build_microstructure_audit(tmp_path)
    assert audited["rows"][0]["mae_mfe_status"] == "UNAVAILABLE_NO_INTRATRADE_PATH"
    assert audited["rows"][0]["mae"] is None and audited["fee_drag_usd"] == 0.05

