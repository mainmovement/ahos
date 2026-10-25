"""Stage 6 deepening: month-aligned 3-vendor witness, DEX discovery funnel, causal event matrix, Batch-5 lab,
shadow scorecard, session drill, organism radar, held-out exam, cross-surface unification. Offline (no network)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from architecture.markets import second_source as ss
from architecture.markets.live_price_feed import resolve_yahoo_contract_month


# ---------------- WP-1a: contract-month aligned 3-vendor witness ----------------
def test_brent_roll_mismatch_resolves_on_same_month_and_logs_basis():
    a = {"price": 111.70, "contract_month": "2027-01", "source": "yahoo_finance:BZ=F"}
    b = {"price": 111.70, "contract_month": "2027-01", "source": "tradingview:ICEEUR:BRNF2027",
         "continuous_front": {"price": 116.72, "source": "tradingview:ICEEUR:BRN1!"}}
    c = {"price": 116.72, "contract_month": None, "source": "stooq:cb.f"}
    w = ss.witness("BRENT", a, b, c)
    assert w["verdict"] == "VERIFIED" and w["pair"] == "A-B"
    assert w["diagnostics"]["futures_roll_basis_bps"] == pytest.approx(449.4, abs=0.2)
    assert w["diagnostics"]["front_vs_a_bps"] == pytest.approx(449.4, abs=0.2)


def test_mismatched_contract_month_is_not_comparable_fail_closed():
    a = {"price": 111.70, "contract_month": "2027-01"}
    b = {"price": 116.72, "contract_month": "2026-12"}
    assert ss.witness("BRENT", a, b)["verdict"] == "UNRESOLVED"
    c = {"price": 111.90, "contract_month": None}
    w = ss.witness("BRENT", a, b, c)
    assert w["verdict"] == "VERIFIED" and w["pair"] == "A-C"


def test_all_three_disagree_is_conflict_and_a_outlier_is_flagged():
    w = ss.witness("WTI", {"price": 100.0}, {"price": 102.0}, {"price": 98.0})
    assert w["verdict"] == "CONFLICT"
    w2 = ss.witness("WTI", {"price": 100.0}, {"price": 103.0}, {"price": 103.1})
    assert w2["verdict"] == "CONFLICT" and w2["diagnostics"]["a_outlier"] is True


def test_tolerances_oil_50bps_fx_35bps():
    assert ss.witness("WTI", {"price": 100.0}, {"price": 100.45})["verdict"] == "VERIFIED"
    assert ss.witness("WTI", {"price": 100.0}, {"price": 100.6})["verdict"] == "CONFLICT"
    assert ss.witness("EURUSD", {"price": 1.0}, {"price": 1.003})["verdict"] == "VERIFIED"
    assert ss.witness("EURUSD", {"price": 1.0}, {"price": 1.0040})["verdict"] == "CONFLICT"
    assert ss.witness("BTC", {"price": 100}, None)["verdict"] == "UNRESOLVED"


def test_spot_token_is_never_a_same_contract_witness_for_gold_futures():
    w = ss.witness("XAU", {"price": 4000.0}, {"price": 4001.0, "instrument_basis": "spot_token"})
    assert w["verdict"] == "UNRESOLVED"


def test_delayed_vendor_is_compared_at_its_effective_time():
    t_now = datetime(2026, 10, 26, 14, 0, tzinfo=timezone.utc).timestamp()
    stamps = [int(t_now - 1800 + 300 * i) for i in range(6)]
    bars = [[100, 100, 100, 100.0, 0], [100, 100, 100, 100.0, 0], [100, 100, 100, 100.0, 0],
            [100, 100, 100, 100.0, 0], [101, 101, 101, 101.0, 0], [101.5, 101.5, 101.5, 101.5, 0]]
    a = {"price": 101.5, "ohlcv_5m": bars, "ohlcv_5m_ts": stamps,
         "market_time": datetime.fromtimestamp(t_now, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    b = {"price": 100.0, "delay_s": 600,
         "fetched_at": datetime.fromtimestamp(t_now, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    w = ss.witness("SPX", a, b)
    assert w["verdict"] == "VERIFIED" and w["diagnostics"].get("time_aligned_ab") is True


def test_tv_contract_ticker_and_stooq_parser():
    assert ss.tv_contract_ticker("BRENT", "2027-01") == "ICEEUR:BRNF2027"
    assert ss.tv_contract_ticker("XAU", "2026-12") == "COMEX:GCZ2026"
    assert ss.tv_contract_ticker("SPX", "2026-12") is None
    page = "- [x] ▼**Quotes****Crude Oil Brent - ICE (CB.F)**23 Oct, 23:00**116.72+3.55(+3.14%)** **My**"
    q = ss.parse_stooq_page(page, "cb.f", now=datetime(2026, 10, 24, 9, 0, tzinfo=timezone.utc))
    assert q["price"] == 116.72 and q["market_time"] == "2026-10-23T21:00:00Z" and q["vendor"] == "stooq"
    assert ss.parse_stooq_page("Symbol ^SPX nie istnieje", "^spx") is None


def test_yahoo_contract_month_resolution_uses_only_yahoo_identity():
    cont = {"price": 111.7, "_regular_market_time": 1792789159}
    def fake(sym):
        prices = {"BZX26.NYM": 118.0, "BZZ26.NYM": 116.72, "BZF27.NYM": 111.7}
        p = prices.get(sym)
        return {"chart": {"result": [{"meta": {"regularMarketPrice": p, "regularMarketTime": 1792789159}}]}} if p else None
    now = datetime(2026, 10, 24, tzinfo=timezone.utc).timestamp()
    res = resolve_yahoo_contract_month("BRENT", cont, fetch=fake, now_ts=now)
    assert res["contract_month"] == "2027-01" and res["contract_symbol"] == "BZF27.NYM"
    assert resolve_yahoo_contract_month("BRENT", {"price": 99.0, "_regular_market_time": 1}, fetch=fake, now_ts=now) is None


def test_gather_witness_uses_lazy_third_source_only_where_needed():
    from architecture.markets.paper_trader import gather_witness
    quotes = {"BRENT": {"price": 100.0}, "BTC": {"price": 50000.0}}
    asked: list[list[str]] = []
    def fc(syms):
        asked.append(list(syms))
        return {"BRENT": {"price": 100.2, "source": "stooq:cb.f"}}
    wit = gather_witness(quotes, fetch_b=lambda: {"BTC": {"price": 50010.0}}, fetch_c=fc, symbols={"BRENT", "BTC"})
    assert wit["BTC"]["verdict"] == "VERIFIED" and wit["BRENT"]["verdict"] == "VERIFIED" and wit["BRENT"]["pair"] == "A-C"
    assert asked and "BTC" not in asked[0]


# ---------------- WP-1b: DEX discovery funnel + 3-source veto + distinct-pool witness ----------------
TOK = "0x00000000000000000000000000000000000000aa"
POOL1, POOL2 = "0x00000000000000000000000000000000000000p1", "0x00000000000000000000000000000000000000p2"


def _gp(**over):
    row = {"is_honeypot": "0", "buy_tax": "0", "sell_tax": "0", "is_open_source": "1", "is_mintable": "0",
           "holders": [{"address": POOL1, "percent": "0.40", "is_locked": 0, "is_contract": 1},
                       {"address": "0xbb", "percent": "0.05", "is_locked": 0, "is_contract": 0}]}
    row.update({k: "0" for k in ("is_proxy", "hidden_owner", "can_take_back_ownership", "owner_change_balance",
                                 "selfdestruct", "cannot_sell_all", "transfer_pausable", "slippage_modifiable",
                                 "personal_slippage_modifiable", "cannot_buy")})
    row.update(over)
    return {"result": {TOK: row}}


def _getter(gp=None, hp=True, pools=2, p2=1.0):
    def g(url):
        if "gopluslabs" in url:
            return gp if gp is not None else _gp()
        if "honeypot.is" in url:
            return {"simulationSuccess": True, "honeypotResult": {"isHoneypot": False},
                    "simulationResult": {"buyTax": 0.2, "sellTax": 0.3}, "contractCode": {"openSource": True}} if hp else None
        if "dexscreener.com/latest" in url:
            ps = [{"pairAddress": POOL1, "dexId": "uniswap", "baseToken": {"address": TOK}, "priceUsd": "1.0",
                   "liquidity": {"usd": 400000}, "volume": {"h24": 900000}, "fdv": 5_000_000}]
            if pools > 1:
                ps.append({"pairAddress": POOL2, "dexId": "sushiswap", "baseToken": {"address": TOK}, "priceUsd": str(p2),
                           "liquidity": {"usd": 120000}, "volume": {"h24": 200000}})
            return {"pairs": ps}
        if "trending_pools" in url:
            return {"data": [
                {"attributes": {"name": "GOOD / WETH", "address": POOL1, "pool_created_at": "2026-09-01T00:00:00Z",
                                "volume_usd": {"h24": "900000"}, "reserve_in_usd": "400000", "fdv_usd": "5000000",
                                "price_change_percentage": {"h6": "2"}, "transactions": {"h24": {"buys": 60, "sells": 40}}},
                 "relationships": {"base_token": {"data": {"id": f"eth_{TOK}"}}}},
                {"attributes": {"name": "NEW / WETH", "address": "0xnew", "pool_created_at": "2026-10-23T00:00:00Z",
                                "volume_usd": {"h24": "5000000"}, "reserve_in_usd": "900000"},
                 "relationships": {"base_token": {"data": {"id": "eth_0xnewtoken"}}}}]}
        if "token-boosts" in url:
            return [{"chainId": "solana", "tokenAddress": "So1"}]
        if "ohlcv" in url:
            return {"data": {"attributes": {"ohlcv_list": [[1792800000 - 300 * i, 1.0, 1.01, 0.99, 1.0, 1000] for i in range(40)]}}}
        return None
    return g


def test_strict_veto_classifies_breach_vs_missing_evidence():
    from architecture.markets.token_safety_live import veto_check
    clean = veto_check("GOOD", TOK, getter=_getter(), strict=True)
    assert clean["verdict"] == "ELIGIBLE_PAPER_TOKEN", clean["reasons"]
    assert clean["goplus"]["holder_concentration"]["top1_pct"] == 0.05  # LP pool excluded from concentration
    proxy = veto_check("GOOD", TOK, getter=_getter(gp=_gp(is_proxy="1")), strict=True)
    assert proxy["verdict"] == "ELIGIBLE_INSTITUTIONAL_PROXY" and "goplus:is_proxy" not in proxy["reasons"]
    thin = _getter(gp=_gp(is_proxy="1"), pools=1)
    assert veto_check("GOOD", TOK, getter=thin, strict=True)["verdict"] == "VETOED_SECURITY"
    gp = _gp(); del gp["result"][TOK]["hidden_owner"]
    missing = veto_check("GOOD", TOK, getter=_getter(gp=gp), strict=True)
    assert missing["verdict"] == "VETOED_FAIL_CLOSED" and "goplus:missing_hidden_owner" in missing["reasons"]
    gp2 = _gp(); del gp2["result"][TOK]["sell_tax"]
    assert veto_check("GOOD", TOK, getter=_getter(gp=gp2))["allowed"] is False
    assert veto_check("GOOD", TOK, getter=_getter(hp=False), strict=True)["verdict"] == "VETOED_FAIL_CLOSED"
    conc = _gp(holders=[{"address": "0xwhale", "percent": "0.45", "is_locked": 0, "is_contract": 0}])
    assert veto_check("GOOD", TOK, getter=_getter(gp=conc), strict=True)["verdict"] == "VETOED_SECURITY"


def test_honeypot_missing_open_source_is_not_safe():
    from architecture.markets.token_safety_live import fetch_honeypot_is
    hp = fetch_honeypot_is(TOK, getter=lambda u: {"simulationSuccess": True, "honeypotResult": {"isHoneypot": False},
                                                   "simulationResult": {"buyTax": 1, "sellTax": 1}})
    assert hp["is_open_source"] is None and hp["buy_tax"] == 0.01


def test_discovery_funnel_filters_age_volume_liquidity_and_ranks():
    from architecture.markets.token_safety_live import run_discovery_funnel
    f = run_discovery_funnel(_getter(), now=datetime(2026, 10, 24, tzinfo=timezone.utc))
    assert f["funnel_passed"] == 1 and f["funnel_rejected"] == 1
    assert "pool_age<7d_or_unknown" in f["funnel_rejected_sample"][0]["funnel_reasons"]
    v = f["vetted"][0]
    assert v["allowed"] and v["pool_witness"]["verdict"] == "POOL_WITNESS_VERIFIED" and v["paper_tradable"]


def test_single_pool_token_price_is_never_verified():
    from architecture.markets.token_safety_live import dex_paper_quote, fetch_dexscreener, pool_price_witness
    assert pool_price_witness(fetch_dexscreener(TOK, getter=_getter(pools=1)))["verdict"] == "SINGLE_POOL_UNRESOLVED"
    tok = {"symbol": "GOOD", "address": TOK, "pool": POOL1}
    q, w = dex_paper_quote(tok, getter=_getter(pools=1))
    assert q["price"] == 1.0 and w["verdict"] == "UNRESOLVED"
    _, w2 = dex_paper_quote(tok, getter=_getter(pools=2, p2=1.005))
    assert w2["verdict"] == "VERIFIED"
    _, w3 = dex_paper_quote(tok, getter=_getter(pools=2, p2=1.05))
    assert w3["verdict"] == "CONFLICT"


def test_paper_trader_dex_feed_trades_only_verified_and_keeps_exit_path(tmp_path):
    import time as _t
    from architecture.markets import paper_trader as pt
    t0 = 1_800_000_000.0
    mt = _t.strftime("%Y-%m-%dT%H:%M:%SZ", _t.gmtime(t0))
    bars = [[1 + i * 0.01, 1.01 + i * 0.01, 0.99 + i * 0.01, 1 + i * 0.01, 10.0] for i in range(40)]
    def feed(root, positions):
        good = ({"price": 1.4, "market_time": mt, "ohlcv_5m": bars, "token_address": TOK, "dex_pool": POOL1, "source": "gt"},
                {"verdict": "VERIFIED", "source_a": "gt", "price_a": 1.4, "source_b": "ds", "price_b": 1.401, "gap": 0.001})
        bad = ({"price": 2.0, "market_time": mt, "ohlcv_5m": bars, "token_address": "0xbad", "dex_pool": "0xp", "source": "gt"},
               {"verdict": "UNRESOLVED", "source_a": "gt", "price_a": 2.0, "source_b": None, "price_b": None, "gap": None})
        return {"DEX_GOOD": good, "DEX_BAD": bad}
    sig = lambda sym, desk, q: [{"name": "mtf_trend", "score": 0.8, "available": True, "source": "fx", "spec": "§2",
                                 "evidence": {"higher_tf_sign": 1}}]
    pt.run_cycle(tmp_path, fetch=lambda: {"quotes": {}}, fetch_b=lambda: {}, signals_fn=sig, now=lambda: t0,
                 use_ledger=False, dex_feed=feed)
    rows = [json.loads(l) for l in (tmp_path / "reports/grok/PAPER/paper_trades.jsonl").read_text().splitlines()]
    assert any(r["symbol"] == "DEX_BAD" and r["reason"] == "WITNESS_UNRESOLVED" for r in rows)
    opened = [r for r in rows if r["event"] == "OPEN"]
    assert [r["symbol"] for r in opened] == ["DEX_GOOD"] and opened[0]["desk"] == "PB_TOKEN"
    pos = json.loads((tmp_path / "reports/grok/PAPER/paper_positions.json").read_text())["positions"]["DEX_GOOD"]
    assert pos["token_address"] == TOK and pos["dex_pool"] == POOL1


# ---------------- WP-2a: causal event / news impact matrix ----------------
NOW = datetime(2026, 10, 28, 13, 30, tzinfo=timezone.utc)
CAL = {"events": [
    {"event": "EIA_WPSR", "at_utc": "2026-10-28T14:30:00+00:00", "desks": ["OIL"]},
    {"event": "FOMC_STATEMENT", "at_utc": "2026-10-28T18:00:00+00:00", "desks": ["US", "FX", "GOLD", "CRYPTO", "EU", "ASIA", "OIL"]},
    {"event": "ECB_GOV_COUNCIL", "at_utc": "2026-12-10T13:15:00+00:00", "desks": ["EU", "FX", "GOLD"]}]}


def test_trader_desk_names_map_to_calendar_desks():
    from architecture.markets import macro_calendar as mc
    up = mc.upcoming(CAL, "US_EQUITIES", now=NOW, horizon_h=48)
    assert [e["event"] for e in up] == ["FOMC_STATEMENT"]
    assert mc.upcoming(CAL, "FOREX", now=NOW, horizon_h=48) and mc.upcoming(CAL, "US", now=NOW, horizon_h=48)


def test_event_window_uses_measured_vol_only_and_documented_drift_only():
    from architecture.markets import macro_calendar as mc
    mat = {"matrix": {"EIA_WPSR": {"WTI": {"status": "MEASURED", "vol_ratio": 1.8}}}}
    wti = mc.event_window_state(CAL, "WTI", now=NOW, matrix=mat)
    assert wti["vol_mult"] == 1.8 and wti["documented_drift"] == 0.0
    assert mc.event_window_state(CAL, "WTI", now=NOW, matrix={})["vol_mult"] == 1.0
    spx = mc.event_window_state(CAL, "SPX", now=NOW, matrix={})
    assert spx["documented_drift"] == 0.5 and spx["active_events"][0]["phase"] == "PRE_EVENT"
    assert mc.event_window_state(CAL, "DAX", now=NOW, matrix={})["active_events"] == []


def test_measure_event_impact_detects_event_day_vol():
    from architecture.markets import macro_calendar as mc
    t0 = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
    bars, px, days = [], 100.0, []
    for i in range(400):
        ts = t0 + i * 86400
        big = i % 20 == 0 and i > 0
        px *= 1 + (0.03 if big else (0.002 if i % 2 else -0.002))
        bars.append((ts, px, px, px, px))
        if big:
            days.append(datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT14:30:00+00:00"))
    cal = {"events": [{"event": "EIA_WPSR", "at_utc": d} for d in days]}
    m = mc.measure_event_impact(cal, {"WTI": bars, "BRENT": bars[:100]})
    cell = m["matrix"]["EIA_WPSR"]["WTI"]
    assert cell["status"] == "MEASURED" and cell["vol_ratio"] > 5 and cell["n_events"] == 19
    assert m["matrix"]["EIA_WPSR"]["BRENT"]["status"] == "INSUFFICIENT_EVENTS" if "BRENT" in m["matrix"]["EIA_WPSR"] else True


def test_causal_news_transmission_signs_and_corroboration_gate():
    from architecture.markets.news_desk import causal_news_impact
    ts = (NOW.replace(hour=12)).strftime("%Y-%m-%dT%H:%M:%SZ")
    hawk = [{"state": "CORROBORATED", "sourceIds": ["reuters", "ft"], "publishedAt": ts,
             "headlineEn": "Fed's Powell signals higher for longer as inflation jumps"}]
    assert causal_news_impact(hawk, "XAU", now=NOW)["drift"] < 0
    assert causal_news_impact(hawk, "USDJPY", now=NOW)["drift"] > 0
    assert causal_news_impact(hawk, "DAX", now=NOW)["clusters_used"] == 0
    single = [{**hawk[0], "state": "SINGLE_SOURCE", "sourceIds": ["blog"]}]
    assert causal_news_impact(single, "XAU", now=NOW)["clusters_used"] == 0
    opec = [{"state": "CORROBORATED", "sourceIds": ["a", "b"], "publishedAt": ts, "headlineEn": "OPEC+ agrees deeper output cuts"}]
    assert causal_news_impact(opec, "WTI", now=NOW)["drift"] > 0
    old = [{**hawk[0], "publishedAt": "2026-10-20T00:00:00Z"}]
    assert causal_news_impact(old, "XAU", now=NOW)["clusters_used"] == 0


def test_event_shock_only_shrinks_size_and_is_shadow():
    from architecture.markets import signal_brain as sb
    mat = {"matrix": {"EIA_WPSR": {"WTI": {"status": "MEASURED", "vol_ratio": 2.0}}}}
    s = sb.event_shock("OIL", "WTI", now=NOW, calendar=CAL, stories=[], matrix=mat)
    assert s["available"] and s["evidence"]["size_mult"] == 0.5 and s["evidence"]["vol_mult"] == 2.0
    calm = sb.event_shock("OIL", "WTI", now=NOW, calendar={"events": []}, stories=[], matrix=mat)
    assert calm["evidence"]["size_mult"] == 1.0
    assert sb.DEFAULT_WEIGHTS["event_shock"] == 0.0


# ---------------- WP-2b: Batch-5 lab machinery (synthetic, offline) ----------------
import math as _m
import random as _rnd


def _walk(n, seed, drift=0.0, vol=0.01, t0=1_500_000_000, vol_series=True):
    rng, px, out = _rnd.Random(seed), 100.0, []
    for i in range(n):
        o = px
        px *= 1 + drift + rng.gauss(0, vol)
        h, l = max(o, px) * (1 + abs(rng.gauss(0, vol / 3))), min(o, px) * (1 - abs(rng.gauss(0, vol / 3)))
        out.append((t0 + i * 86400 + 48600, o, h, l, px, 1e6 * (1 + rng.random()) if vol_series else 0.0))
    return out


def test_batch5_preregistered_before_run():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "strategy_lab"))
    import hypotheses as H
    src = (Path(__file__).resolve().parents[1] / "strategy_lab" / "hypotheses.py").read_text(encoding="utf-8")
    assert "BATCH 5 (registered 2026-10-24 13:17 Tehran — PRE-REGISTERED BEFORE ANY RUN)" in src
    for hid in ("H23", "H24", "H25", "H26", "H27", "H28"):
        h = H.get(hid)
        assert h["batch"] == 5 and h["status"] == "TESTABLE" and h["expected_failure_mode"]


def test_ledoit_wolf_shrinks_and_stays_psd():
    import numpy as np
    from architecture.learning.walk_forward import ledoit_wolf
    rng = np.random.default_rng(1)
    few = rng.normal(0, 0.01, (30, 8))
    many = rng.normal(0, 0.01, (3000, 8))
    s_few, sh_few = ledoit_wolf(few)
    _, sh_many = ledoit_wolf(many)
    assert 0 <= sh_many < sh_few <= 1
    assert np.linalg.eigvalsh(s_few).min() > 0


def test_annualized_dsr_matches_per_obs_at_unit_frequency_and_punishes_noise():
    from architecture.learning.walk_forward import deflated_sharpe, deflated_sharpe_annualized
    rng = _rnd.Random(3)
    r = [rng.gauss(0.001, 0.01) for _ in range(200)]
    trials = [rng.gauss(0, 0.1) for _ in range(60)]
    assert deflated_sharpe(r, 60, trials) == deflated_sharpe_annualized(r, 1.0, 60, trials)
    noise = [rng.gauss(0, 0.01) for _ in range(60)]
    ann = [s * _m.sqrt(52) for s in trials]
    assert deflated_sharpe_annualized(noise, 52.0, 60, ann) < 0.95


def test_purged_folds_drop_trades_straddling_fold_edges():
    from architecture.learning.walk_forward import _purged_folds
    d = 86400
    trades = [{"ts_open": 0, "ts_close": 3 * d, "ret": 0.01}, {"ts_open": 24 * d, "ts_close": 27 * d, "ret": 0.01},
              {"ts_open": 50 * d, "ts_close": 52 * d, "ret": -0.01}]
    f = _purged_folds(trades, 0, 100 * d, k=4)
    assert f["purged_trades"] == 1 and sum(x["n"] for x in f["folds"]) == 2


def test_time_aligned_pbo_uses_calendar_blocks_and_excludes_late_starters():
    from architecture.learning.walk_forward import time_aligned_pbo
    d = 86400
    rng = _rnd.Random(5)
    cands = [{"strategy_id": f"s{k}", "_trades": [(i * 7 * d, i * 7 * d + d, rng.gauss(0, 0.01)) for i in range(300)]}
             for k in range(6)]
    cands.append({"strategy_id": "late", "_trades": [((250 + i) * 7 * d, (250 + i) * 7 * d + d, 0.01) for i in range(40)]})
    out = time_aligned_pbo(cands)
    assert "late" in out["excluded_short_history"] and len(out["included"]) == 6
    assert out["pbo"] is not None and 0 <= out["pbo"] <= 1 and out["blocks"] == 16


def test_h24_wick_skips_volume_free_fx_and_fires_on_sweep():
    from architecture.learning import walk_forward as wf
    bars = _walk(400, 7)
    ts, o, h, l, c, v = bars[300]
    bars[300] = (ts, o, h, o * 0.80, o * 1.001, v * 5)
    daily = {"SPX": bars, "EURUSD": _walk(400, 8, vol_series=False)}
    cands, skipped = wf.h24_wick(daily)
    assert "EURUSD" in skipped and [c["strategy_id"] for c in cands] == ["b5-H24-SPX"]
    assert cands[0]["is_trades"] + cands[0]["oos_trades"] >= 1


def test_h28_without_is_survivors_reports_no_edge_instead_of_inventing_one():
    from architecture.learning.walk_forward import h28_voltarget
    d = 86400
    losing = [{"strategy_id": "b5-X-1", "_trades": [(i * 5 * d, i * 5 * d + 2 * d, -0.002) for i in range(200)]}]
    out = h28_voltarget(losing)
    assert out["status"] == "NO_IS_SURVIVORS" and out["returns"] == [] and out["streams_selected_on_is"] == []


def test_h27_black_litterman_without_skill_returns_equal_weight_prior():
    from architecture.learning import walk_forward as wf
    daily = {a: _walk(1400, 20 + k) for k, a in enumerate(wf.BL_ASSETS)}
    c = wf.h27_black_litterman(daily)
    assert c is not None and c["rebalances"] >= 40
    if c["rebalances_with_active_views"] == 0:
        assert c["mean_abs_tilt_vs_equal_weight"] < 1e-9


def test_switch_refuses_batch5_candidates_without_full_gate(tmp_path):
    from architecture.learning import strategy_switch as sw
    (tmp_path / "reports/grok/M28").mkdir(parents=True)
    (tmp_path / "reports/grok/M56").mkdir(parents=True)
    (tmp_path / sw.B5_REL).write_text(json.dumps({"candidates": [
        {"strategy_id": "b5-H25-ROT3", "gate": "FAIL", "gate_detail": "DSR=0.4"},
        {"strategy_id": "b5-H27-BL8", "gate": "PASS_STATS", "oos_trades": 12}]}), encoding="utf-8")
    (tmp_path / sw.RED_REL).write_text(json.dumps({"reports": [{"strategy_id": "b5-H27-BL8", "verdict": "SURVIVED_RED_TEAM"}]}), encoding="utf-8")
    for sid in ("b5-H25-ROT3", "b5-H27-BL8"):
        with pytest.raises(PermissionError):
            sw.promote(tmp_path, sid, "x", 0.1, actor="test")
    assert not (tmp_path / sw.SWITCH_REL).exists()


def test_h27_records_preregistration_deviation_for_negative_wti():
    from architecture.learning import walk_forward as wf
    daily = {a: _walk(1400, 40 + k) for k, a in enumerate(wf.BL_ASSETS + ("BRENT",))}
    ts, o, h, l, c, v = daily["WTI"][900]
    daily["WTI"][900] = (ts, o, h, -37.63, -37.63, v)
    wf.DEVIATIONS.clear()
    cand = wf.h27_run(daily)
    assert "BRENT" in cand["assets"] and "WTI" not in cand["assets"]
    assert "WTI" in wf.DEVIATIONS["H27"]
    wf.DEVIATIONS.clear()


# ---------------- WP-3: shadow scorecard + per-venue sessions + preflight ----------------
def test_shadow_scorecard_horizons_rank_ic_bss_and_closed_trade_gate(tmp_path):
    from architecture.learning.shadow_forward_scorecard import build_shadow_forward_scorecard, spearman
    led = tmp_path / "reports" / "grok" / "PAPER"
    led.mkdir(parents=True)
    rows, t0, px = [], datetime(2026, 10, 26, 0, 0, tzinfo=timezone.utc).timestamp(), 100.0
    rng = __import__("random").Random(9)
    for k in range(400):
        t = t0 + k * 300
        drift = rng.choice([-1, 1])
        rows.append({"ts": datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "event": "HOLD", "symbol": "BTC",
                     "price": px, "signal_scores": {"news": 0.6 * drift, "mtf_trend": 0.0}})
        px *= 1 + 0.002 * drift
    rows.append({"ts": "2026-10-26T12:00:00Z", "event": "CLOSE", "symbol": "BTC", "fill_price": px})
    (led / "paper_trades.jsonl").write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    out = build_shadow_forward_scorecard(tmp_path)
    news = next(s for s in out["signals"] if s["signal"] == "news")
    assert set(news["horizons"]) == {"15m", "1h", "4h", "24h"}
    h15 = news["horizons"]["15m"]
    assert h15["n_eff"] < h15["n"] and h15["n_eff"] >= 30
    assert out["closed_trades_count"] == 1 and out["trades_remaining_to_30_gate"] == 29
    assert news["trades_remaining_to_gate"] == 29 and news["promotion_eligible"] is False
    assert next(s for s in out["signals"] if s["signal"] == "macro_event")["hypothesis_id"] == "H16"
    assert spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)


def test_shadow_scorecard_rejects_late_forward_prices(tmp_path):
    from architecture.learning.shadow_forward_scorecard import _forward_return
    series = [(0.0, 100.0), (3 * 3600.0, 110.0)]
    assert _forward_return(series, 0.0, 3600) is None
    assert _forward_return(series, 0.0, 2 * 3600) == pytest.approx(0.1)
    assert _forward_return(series, 0.0, 4 * 3600) is None


def test_venue_sessions_are_dst_aware_and_friday_evening_is_closed():
    from architecture.markets.weekday_session_gate import session_report, venue_status
    mon = datetime(2026, 10, 26, 14, 0, tzinfo=timezone.utc)
    assert venue_status("NYSE", mon)["open"] is True and venue_status("XETRA", mon)["open"] is True
    assert venue_status("TSE", mon)["open"] is False
    fri = datetime(2026, 10, 23, 21, 30, tzinfo=timezone.utc)
    assert session_report(fri)["venues_open_now"] == ["ICE_BRENT"]
    fri_late = datetime(2026, 10, 23, 22, 30, tzinfo=timezone.utc)
    assert not any(v["open"] for v in session_report(fri_late)["venues"].values())
    assert venue_status("CME_GLOBEX", datetime(2026, 11, 8, 22, 30, tzinfo=timezone.utc))["open"] is False
    assert venue_status("CME_GLOBEX", datetime(2026, 11, 8, 23, 30, tzinfo=timezone.utc))["open"] is True
    assert venue_status("CME_GLOBEX", datetime(2026, 10, 25, 22, 30, tzinfo=timezone.utc))["open"] is True
    sat = datetime(2026, 10, 24, 10, 0, tzinfo=timezone.utc)
    ny = venue_status("NYSE", sat)
    assert ny["open"] is False and ny["next_open_utc"] == "2026-10-26T13:30:00Z" and ny["next_open_tehran"] == "2026-10-26 17:00"
    assert ny["minutes_until_open"] == (2 * 24 * 60 + 3 * 60 + 30)
    after_dst = venue_status("NYSE", datetime(2026, 11, 7, 10, 0, tzinfo=timezone.utc))
    assert after_dst["next_open_utc"] == "2026-11-09T14:30:00Z"


def test_session_drill_preflight_negative_controls_and_minutes(tmp_path):
    from architecture.markets.session_readiness_drill import build_session_readiness_drill
    sat = datetime(2026, 10, 24, 10, 0, tzinfo=timezone.utc)
    p = build_session_readiness_drill(tmp_path, quotes={"SPX": {"price": 5000.0}}, now=sat)
    pre = p["adapters"]["preflight"]
    assert pre["verdict"] == "PREFLIGHT_PASS" and pre["live_paths_refused"] is True
    assert pre["broker_connectivity"] == "NOT_VERIFIED"
    tokyo = p["cash_sessions"][0]
    assert tokyo["minutes_until_open"] > 0 and tokyo["next_open_tehran"].startswith("2026-10-26")
    assert p["adv_cap_checks"]["SPX"]["adv_source"] == "ASSUMED_FLOOR_50M_NO_VOLUME_IN_FEED"
    assert p["adv_cap_checks"]["BTC"]["status"] == "NO_QUOTE"
    assert p["daemon_heartbeat"]["status"] == "UNKNOWN"


# ---------------- WP-4: live held-out exam, AskU provenance, M57/M58, M65 sources ----------------
def _paper_rows(path, rows):
    path.mkdir(parents=True, exist_ok=True)
    (path / "paper_trades.jsonl").write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")


def _iso(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def test_live_exam_answer_key_is_the_market_outcome_and_the_split_is_causal(tmp_path):
    from architecture.learning.exam import EXAM_HORIZON_S, synthesize_live_conflict_exam_items
    rng, px, t0, rows = _rnd.Random(4), 100.0, 1_790_000_000, []
    for k in range(80):
        t = t0 + k * 3600
        rows.append({"ts": _iso(t), "event": "HOLD", "symbol": "BTC", "desk": "CRYPTO", "side": "SHORT", "price": px})
        rows.append({"ts": _iso(t + 60), "event": "SKIP", "symbol": "BTC", "reason": "WITNESS_UNRESOLVED"})
        px *= 1 + rng.choice([-1, 1]) * rng.uniform(0.001, 0.01)
    _paper_rows(tmp_path / "reports" / "grok" / "PAPER", rows)
    out = synthesize_live_conflict_exam_items(tmp_path)
    held = out["items"]
    assert held and out["leaked"] is False and out["compliance_checks"]["abstained"] == 80
    for it in held:
        assert it["correct"] == (it["direction"] * it["forward_1h_ret"] > 0)
        assert it["b_source"] == "calibration_half" and it["split"] == "held_out"
    assert out["heldout_accuracy"] + out["abstain_baseline_accuracy"] == pytest.approx(1.0)
    assert out["independent_episodes"] == len(held) >= 10
    assert out["status"] in ("MEASURED", "THETA_AT_BOUND_NOT_IDENTIFIED")
    first_held = min(datetime.strptime(i["ts"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp() for i in held)
    assert first_held >= t0 + (out["n_calibration_items"] - 1) * 3600 + EXAM_HORIZON_S


def test_live_exam_correlated_burst_is_not_reported_as_measured(tmp_path):
    from architecture.learning.exam import synthesize_live_conflict_exam_items
    t0, rows = 1_790_000_000, []
    for k in range(8):
        for sym in ("BTC", "ETH", "SOL", "UNI"):
            rows.append({"ts": _iso(t0 + k * 3600), "event": "HOLD", "symbol": sym, "desk": "CRYPTO",
                         "side": "SHORT", "price": 100.0 * (1 - 0.003 * k)})
    _paper_rows(tmp_path / "reports" / "grok" / "PAPER", rows)
    out = synthesize_live_conflict_exam_items(tmp_path)
    assert out["n_heldout_items"] >= 10 and out["heldout_accuracy"] == 1.0
    assert out["independent_episodes"] < out["min_independent_episodes"]
    assert out["status"] == "INSUFFICIENT_INDEPENDENT_EPISODES"


def test_ask_university_has_no_padding_claims(tmp_path):
    from architecture.university.registry import ask_university
    res = ask_university("zzqx nothing matches this", root=tmp_path)
    assert res["padding"].startswith("NONE")
    assert not any(str(c.get("claim_id", "")).startswith("univ-core") for c in res["top_claims"])
    assert res["sufficient_claims"] == (res["ranked_claims_count"] >= 10)


def test_m57_m58_propose_only_and_claim_no_capability(tmp_path):
    from architecture.university.science_to_desk_pipeline import build_aci_agi_si_loop_status, build_organism_science_matrix
    scout = tmp_path / "reports" / "grok" / "M44"
    scout.mkdir(parents=True)
    paper = {"arxiv_id": "2610.00001", "title": "Regime-aware execution", "url": "https://arxiv.org/abs/2610.00001",
             "published": "2026-10-01"}
    (scout / "arxiv_scout.json").write_text(json.dumps({"generated_at": "2026-10-24T00:00:00Z", "paper_count": 1,
                                                        "pillar_paper_count": 1,
                                                        "papers_by_pillar": {"P1_MARKETS_QUANT": [paper]}}), encoding="utf-8")
    m57 = build_organism_science_matrix(tmp_path)
    assert m57["pillars_live"] == 1 and m57["validated_claims_total"] == 0
    assert m57["organ_static_curricula"].startswith("STATIC_UNVERIFIED")
    prop = next(r for r in m57["matrix"] if r["pillar"] == "P1_MARKETS_QUANT")["proposed_hypotheses"][0]
    assert prop["asku_ref"].startswith("asku_") and prop["status"] == "PROPOSED_NOT_PREREGISTERED"
    m58 = build_aci_agi_si_loop_status(tmp_path)
    assert m58["capability_claims"].startswith("NONE") and m58["loop_closed"] is False
    assert m58["loop_status"].startswith("OPEN_AT_") and m58["edge_status"] == "UNPROVEN_EDGE"
    assert next(s for s in m58["stages"] if s["stage"] == "PROMOTE")["status"] == "EMPTY"


def test_teaching_lessons_carry_their_evidence_source(tmp_path):
    from architecture.learning.teaching_mode_m65 import generate_teaching_journal_snapshot
    snap = generate_teaching_journal_snapshot(root=tmp_path)
    allowed = {"LIVE_HELDOUT_EXAM", "LIVE_PAPER_STATE", "FIXTURE_ILLUSTRATIVE", "CALLER_SUPPLIED_CYCLE", "HISTORICAL_OOS"}
    assert snap["lessons"] and all(lesson["source"] in allowed for lesson in snap["lessons"])
    assert snap["lesson_sources"].get("LIVE_HELDOUT_EXAM", 0) == 0
    assert snap["live_anomaly_exam"]["status"] == "NOT_RUN"


def test_static_scores_and_fixture_tournament_are_labeled():
    from architecture.learning.strategy_tournament import run_strategy_tournament
    from architecture.university.whole_ahos_organ_evolution import build_whole_ahos_organ_evolution_snapshot
    organs = build_whole_ahos_organ_evolution_snapshot()
    assert organs["exam_score_evidence"].startswith("STATIC_UNVERIFIED")
    tour = run_strategy_tournament()
    assert tour["data_source"] == "FIXTURE_ILLUSTRATIVE" and "NOT the Bailey" in tour["dsr_semantics"]


# ---------------- WP-5a: unification audit ----------------
def _ua_write(root, rel, payload):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _ua_root(tmp_path):
    from architecture.mission.ledger import MissionLedger
    led = MissionLedger(tmp_path / "data" / "mission_ledger" / "mission_ledger.jsonl")
    fill = led.decision({"market": "PAPER_TRADER:BTC", "type": "PAPER_FILL", "event": "OPEN", "symbol": "BTC",
                         "ts": "2026-10-24T00:36:00Z"}, agent="agent:paper_trader")
    led.start("M13-GOLD-PAPER", phase="paper_trading", task="gold soak fixture", agent="agent:gold_fixture")
    led.checkpoint("M13-GOLD-PAPER", {"bankroll_usd": 10000.0, "equity_usd": 10000.0})
    _paper_rows(tmp_path / "reports" / "grok" / "PAPER", [
        {"ts": "2026-10-24T00:36:00Z", "event": "OPEN", "symbol": "BTC", "ledger_hash": fill["entry_hash"]},
        {"ts": "2026-10-24T00:41:00Z", "event": "HOLD", "symbol": "BTC"}])
    w = lambda rel, payload: _ua_write(tmp_path, rel, payload)  # noqa: E731
    w("reports/grok/PAPER/paper_trader_status.json", {
        "initial_capital_usd": 100.0, "realized_equity_usd": 100.0, "unrealized_pnl_usd": 0.0,
        "mark_to_market_equity_usd": 100.0, "closed_trades": 0, "open_positions": {"BTC": {}},
        "edge_status": "UNPROVEN_EDGE", "strategy_switch_version": 0})
    w("reports/grok/PAPER/paper_positions.json", {"positions": {"BTC": {}}})
    w("reports/grok/PAPER/paper_trade_audit.json", {"unproven_edge": True, "trades": {"closes": 0},
                                                    "mission_ledger": {"paper_trader_refs": 1}})
    cycle = {"ts": "2026-10-24T10:05:40Z", "kind": "cycle", "cycle": 9, "witness_state": "UNRESOLVED",
             "witness_reason": "insufficient_independent_sources (only ['goldapi_spot'] answered fresh)", "price_usd": None}
    w("reports/grok/M13_SOAK/soak_status.json", {"last_cycle": cycle})
    (tmp_path / "reports/grok/M13_SOAK/soak_runlog.jsonl").write_text(json.dumps(cycle) + "\n", encoding="utf-8")
    w("reports/grok/M13_SOAK/2026-10-24_digest.json", {"paper_only": True})
    w("reports/grok/M19/macro_calendar.json", {"status": {b: "OK 1" for b in ("FOMC", "EIA", "BOE", "BOJ", "ECB", "OPEC")}})
    w("reports/grok/M18/newsroom_snapshot.json", {"rssClusters": [{"topic": "OIL", "state": "CORROBORATED",
                                                                   "independent_domains": ["a.com", "b.com"]}]})
    w("reports/grok/M33/token_hunter_snapshot.json", {"candidates_screened": 1, "paper_watch_eligible_count": 1, "candidates": [
        {"symbol": "AERO", "state": "PAPER_WATCH_ELIGIBLE", "corroborated_sources": ["dexscreener", "geckoterminal"],
         "veto_reasons": [], "steps_passed": 24, "steps_total": 24}]})
    w("reports/grok/M28/batch5_research.json", {"n_trials_counted_in_dsr": 89, "pbo_cscv": 0.44, "candidates": [
        {"strategy_id": "b5-H23-ETH", "deflated_sharpe": 0.1, "gate": "FAIL", "oos_trades": 30}]})
    w("reports/grok/M56/red_team_audit.json", {"n_trials_counted_in_dsr": 89, "pbo_cscv": 0.44, "promotion_eligible": []})
    w("strategy_lab/registry.json", {"candidates": {"H23": {"verdict": "REJECTED", "detail": {"b5-H23-ETH": {}},
                                                            "evidence": "reports/grok/M28/batch5_research.json @ t"}}})
    w("reports/grok/M28/shadow_forward_scorecard.json", {"unproven_edge": True, "closed_trades_count": 0,
                                                         "trades_remaining_to_30_gate": 30})
    w("reports/grok/M56/tournament_snapshot.json", {"leader_dsr": 16.75, "data_source": "FIXTURE_ILLUSTRATIVE",
                                                    "dsr_semantics": "HAIRCUT_ANNUALIZED_SHARPE"})
    w("reports/grok/M57/whole_ahos_organ_evolution.json", {"exam_score_evidence": "STATIC_UNVERIFIED: constants"})
    w("reports/grok/M28/batch6_research.json", {"n_trials_prior": 89, "n_trials_counted_in_dsr": 89, "candidates": [],
                                                "screened": [{"hypothesis_id": "H30", "counted_in_dsr": False}]})
    w("reports/grok/M28/map_elites_grid.json", {"cells_occupied": 0, "grid": {"macro_weekly": {"crisis_defensive": None}}})
    w("reports/grok/M28/batch7_research.json", {"n_trials_prior": 93, "n_trials_counted_in_dsr": 93, "candidates": [],
                                                "screened": [{"hypothesis_id": "H36", "counted_in_dsr": False}]})
    w("reports/grok/M28/batch8_research.json", {"n_trials_prior": 96, "n_trials_counted_in_dsr": 96, "candidates": [],
                                                "screened": [{"hypothesis_id": "H40", "counted_in_dsr": False}]})
    w("reports/grok/CONTINUATION_STATE.json", {"paper_only": True, "current_stage": "Stage 9",
                                               "completed_stages": [], "next_wave_queue": ["Stage 10"]})
    w("reports/grok/PAPER/microstructure_audit.json", {"paper_only": True, "closed_count": 0, "rows": [],
                                                       "fee_drag_usd": 0.0})
    from architecture.markets.council_gate import COUNCIL_SYMBOLS
    w("reports/grok/M15/council_debate_matrix.json", {
        "paper_only": True, "judge_brier": None, "ece_judge": None,
        "rows": [{"symbol": s, "paper_only": True, "approved_paper": False, "brier_judge": None, "ece_judge": None,
                  "swap_gate_passed": False, "bl_prior_status": "ASSUMED_SCALAR_PRIOR_NOT_A_FORECAST",
                  "calibration_status": "NOT_MEASURED_NO_HELD_OUT_SCORECARD", "seats": [{}, {}, {}, {}, {}]}
                 for s in COUNCIL_SYMBOLS]})
    w("reports/grok/M46/stage12_ast_diagnostics.json", {
        "paper_only": True, "n": 3, "candidates_tested": 3, "applied_to_main": False, "pushed": False,
        "candidates": [
            {"reason": "syntax_error:1", "pytest_passed": False, "applied_to_main": False, "pushed": False},
            {"reason": "lane_a_import", "pytest_passed": False, "applied_to_main": False, "pushed": False},
            {"reason": "isolated_worktree_pytest_pass", "pytest_passed": True, "applied_to_main": False, "pushed": False},
        ]})
    from architecture.markets.paper_trader import INSTRUMENTS
    w("reports/grok/PAPER/paper_cash_double_entry.json", {
        "paper_only": True, "recorded_on_ledger": False, "verdict": "MEASURED_ZERO",
        "discrepancy_usd": 0.0, "unlinked_rows": 0, "orphan_fills": 0})
    w("reports/grok/PAPER/weekday_two_source_audit.json", {
        "paper_only": True, "network_fetch": False, "weekend_tehran": True,
        "rows": [{"symbol": s, "desk": desk, "session_open": False, "tradable_for_paper": False,
                  "probe_stale": True, "live_witness": "NO_STORED_PROBE"}
                 for s, (desk, _fee, _slip) in INSTRUMENTS.items()]})
    w("reports/grok/PAPER/fee_coverage.json", {
        "paper_only": True, "rewritten": False, "open_rows_with_fee": 0, "open_fee_usd_sum": 0.0,
        "close_rows_with_fees": 0, "close_fees_usd_sum": 0.0, "ledger_fills_with_fee_usd": 0,
        "ledger_fills_with_fees_usd": 0, "coverage_status": "NO_FILLS"})
    w("reports/grok/PAPER/exit_reason_census.json", {
        "paper_only": True, "close_rows": 0, "partial_rows": 0, "reason_counts": {},
        "daemon_restarted": False, "absence_note": "not observed in this log"})
    w("reports/grok/PAPER/witness_conflict_anatomy.json", {
        "paper_only": True, "exit_rule_changed": False, "rule": "FAIL_CLOSED_ON_RECORDED_DISAGREEMENT",
        "rows": 0, "gap_missing": 0, "gap_min": None, "gap_max": None, "gap_upper_median": None,
        "within_tolerance": 0, "within_spot_default": 0, "inconsistent_with_current_tolerance": 0,
        "dex_rows": 0, "mapped_rows": 0, "source_kinds": {}, "pool_price_tolerance": 0.01,
        "tolerance_source": "INFERRED_FROM_CURRENT_CODE_NOT_STORED_ON_THE_ROW",
        "prior_conflict_zero": 0, "prior_conflict_one": 0, "prior_conflict_more": 0,
        "symbols": {}})
    w("reports/grok/PAPER/dex_roundtrip.json", {
        "paper_only": True, "edge_claimed": False, "symbols": [], "flat": True, "realized_pnl_usd": 0.0})
    w("reports/grok/PAPER/symbol_book.json", {
        "paper_only": True, "edge_claimed": False, "close_rows": 0, "symbols": [], "desks": [],
        "account_realized_pnl_usd": 0.0, "rounded_desk_sum_usd": 0.0, "unassigned_desks": 0})
    w("reports/grok/PAPER/open_book.json", {
        "paper_only": True, "exit_inferred": False, "time_stop_hours": 12.0, "max_hold_hours": 24.0,
        "open_rows": [{"symbol": "BTC", "desk": None, "side": None, "open_time": "2026-10-24T00:36:00Z"}],
        "unmatched_closes": 0, "status": "AT_OR_BEYOND_A_HOLD_LIMIT",
        "positions_file_symbols": ["BTC"], "log_matches_positions_file": True})
    w("reports/grok/PAPER/stored_witness_fields.json", {
        "paper_only": True, "exit_rule_changed": False, "close_rows": 0,
        "tolerance_stored": 0, "pair_stored": 0, "address_shaped_pair_stored": 0})
    w("reports/grok/PAPER/entry_gate.json", {
        "paper_only": True, "edge_claimed": False, "close_rows": 0, "scored_rows": 0,
        "signed_min": None, "signed_max": None, "at_or_above_threshold": 0, "wins": 0, "losses": 0,
        "realized_pnl_usd": 0.0, "raw_outside_unit_interval": 0, "brier": None,
        "brier_status": "NOT_RUN", "status": "NO_CLOSED_ROWS"})
    w("reports/grok/PAPER/kelly_label.json", {
        "paper_only": True, "kelly_switched_on": False, "open_rows": 1, "label_counts": {},
        "numeric_rows": 0, "missing_rows": 1, "status": "KELLY_FIELD_ABSENT"})
    w("reports/grok/PAPER/fee_identity.json", {
        "paper_only": True, "edge_claimed": False, "added_to_cash_gap": False,
        "open_fee_usd": 0.0, "closed_entry_fee_usd": 0.0, "still_open_entry_fee_usd": 0.0,
        "close_fees_usd": 0.0, "net_pnl_usd": 0.0, "implied_gross_usd": 0.0, "status": "NO_CLOSES"})
    w("reports/grok/PAPER/weight_vintage.json", {
        "paper_only": True, "comparison_claimed": False, "close_rows": 0, "largest_cell": 0,
        "versions": [], "status": "NO_CLOSED_ROWS", "sample_gate": 30})
    w("reports/grok/PAPER/contribution_identity.json", {
        "paper_only": True, "edge_claimed": False, "close_rows": 0, "scored_rows": 0, "missing_rows": 0,
        "max_abs_gap": None, "beyond_rounding": 0, "status": "NO_CLOSED_ROWS"})
    w("reports/grok/PAPER/dominant_signal.json", {
        "paper_only": True, "skill_claimed": False, "close_rows": 0, "scored_rows": 0,
        "sign_matches_side": 0, "signals": [], "status": "NO_CLOSED_ROWS"})
    w("reports/grok/PAPER/side_book.json", {
        "paper_only": True, "edge_claimed": False, "close_rows": 0, "sides": [],
        "realized_pnl_usd": 0.0, "status": "NO_CLOSED_ROWS"})
    w("reports/grok/PAPER/entry_regime.json", {
        "paper_only": True, "comparison_claimed": False, "close_rows": 0, "schemas": [],
        "hmm_states": [], "largest_hmm_cell": 0, "status": "NO_CLOSED_ROWS", "sample_gate": 30})
    w("reports/grok/PAPER/exit_score_path.json", {
        "paper_only": True, "edge_claimed": False, "exit_rule_changed": False, "threshold": 0.25,
        "close_rows": 0, "missing_rows": 0, "reasons": [], "status": "NO_CLOSED_ROWS"})
    w("reports/grok/PAPER/hold_by_reason.json", {
        "paper_only": True, "exit_inferred": False, "close_rows": 0, "missing_rows": 0,
        "reasons": [], "status": "NO_CLOSED_ROWS"})
    w("reports/grok/PAPER/signal_breadth.json", {
        "paper_only": True, "edge_claimed": False, "minimum_changed": False, "close_rows": 0,
        "signal_count_min": None, "signal_count_max": None, "signal_counts": [],
        "weight_sum_min": None, "weight_sum_max": None, "weight_sum_below_1": 0,
        "weight_sum_below_half": 0, "status": "NO_CLOSED_ROWS"})
    w("reports/grok/PAPER/exit_trigger.json", {
        "paper_only": True, "exit_rule_changed": False, "take_multiple": 1.5, "close_rows": 0,
        "take_profit_rows": 0, "take_profit_quote_beyond": 0, "fill_inside_take_line": 0,
        "other_quote_beyond": 0, "stop_crossed": 0, "status": "NO_CLOSED_ROWS"})
    w("reports/grok/PAPER/signal_dissent.json", {
        "paper_only": True, "signals_removed": False, "close_rows": 0, "contribution_agree": 0,
        "contribution_oppose": 0, "contribution_zero": 0, "closes_with_opposition": 0,
        "always_zero": [], "always_opposes": [], "never_agrees": [], "status": "NO_CLOSED_ROWS"})
    w("reports/grok/PAPER/exit_slippage.json", {
        "paper_only": True, "added_to_cash_gap": False, "edge_claimed": False, "close_rows": 0,
        "drag_sum": 0.0, "reasons": [], "status": "NO_CLOSED_ROWS"})
    w("reports/grok/PAPER/path_storage.json", {
        "paper_only": True, "path_backfilled": False, "exit_inferred": False, "close_rows": 0,
        "path_stored_rows": 0, "missing_mae": 0, "missing_mfe": 0, "missing_path_points": 0,
        "missing_partial": 0, "hold_rows": 1, "hold_with_mfe": 0, "hold_with_chandelier": 0,
        "status": "NO_CLOSED_ROWS"})
    w("reports/grok/PAPER/take_field.json", {
        "paper_only": True, "multiple_changed": False, "take_multiple": 1.5, "storage_unit": 1e-5,
        "open_rows": 1, "missing_rows": 1, "within_storage": 0, "beyond_storage": 0,
        "max_abs_gap": None, "status": "INCOMPLETE"})
    w("reports/grok/PAPER/cost_schedule.json", {
        "paper_only": True, "edge_claimed": False, "schedule_changed": False, "open_rows": 1,
        "close_rows": 0, "missing_rows": 1, "open_fee_mismatch": 0, "open_slip_mismatch": 0,
        "close_slip_mismatch": 0, "status": "INCOMPLETE"})
    w("reports/grok/PAPER/reversal_anatomy.json", {
        "paper_only": True, "exit_rule_changed": False, "threshold": 0.25, "rows": 0,
        "signed_composite_n": 0, "all_at_or_beyond_threshold": True, "signed_composite_min": None,
        "signed_composite_max": None, "status": "NO_REVERSAL_ROWS"})
    w("reports/grok/PAPER/skip_census.json", {
        "paper_only": True, "event_rows": 0, "reason_counts": {}, "dominant_reason": None})
    w("reports/grok/M57/science_to_desk_snapshot.json", {
        "paper_only": True, "pillars_total": 7, "validated_claims_total": 0,
        "matrix": [{"validated_claims": 0,
                    "proposed_hypotheses": [{"asku_ref": "asku_abc", "status": "PROPOSED_NOT_PREREGISTERED"}]}
                   for _ in range(7)],
        "organ_static_curricula": "STATIC_UNVERIFIED_CLAIM"})
    w("reports/grok/M12/cognitive_graph_snapshot.json", {"registry_agents": 1, "authority_violations": [],
                                                         "verdict_counts": {"HOLD": 1}, "agents": [
        {"agent_id": "AG-01", "verdict": "HOLD", "authority_ok": True}]})
    (tmp_path / "config").mkdir(parents=True, exist_ok=True)
    (tmp_path / "config" / "agent_registry.yaml").write_text("agents:\n  - agent_id: AG-01\n    allowed_authority: [OBSERVE]\n", encoding="utf-8")
    return tmp_path


def _ua_edit(root, rel, **changes):
    p = root / rel
    d = json.loads(p.read_text(encoding="utf-8"))
    d.update(changes)
    p.write_text(json.dumps(d), encoding="utf-8")


def test_unification_audit_consistent_fixture_is_unified_clean(tmp_path):
    from architecture.health.unification_audit import build_unification_audit
    a = build_unification_audit(_ua_root(tmp_path))
    assert a["overall_status"] == "UNIFIED_CLEAN", [c for c in a["checks"] if c["status"] != "PASS"]
    assert a["read_only"] is True and a["open_gaps"]


def test_unification_audit_detects_cross_surface_drift(tmp_path):
    from architecture.health.unification_audit import build_unification_audit
    root = _ua_root(tmp_path)
    _ua_edit(root, "reports/grok/PAPER/paper_trader_status.json", closed_trades=1, realized_equity_usd=101.0)
    _ua_edit(root, "reports/grok/M13_SOAK/soak_status.json", last_cycle={
        "cycle": 9, "witness_state": "VERIFIED", "price_usd": 4007.9,
        "witness_reason": "insufficient_independent_sources (only ['goldapi_spot'] answered fresh)"})
    _ua_edit(root, "reports/grok/M56/tournament_snapshot.json", dsr_semantics=None)
    _ua_edit(root, "strategy_lab/registry.json", candidates={"H23": {
        "verdict": "SHADOW_FORWARD_TEST", "detail": {"b5-H23-ETH": {}}, "evidence": "reports/grok/M28/batch5_research.json"}})
    a = build_unification_audit(root)
    assert a["overall_status"] == "DRIFT_DETECTED"
    assert {"paper.closed_trades", "paper.equity", "gold.soak_witness", "research.dsr_is_probability",
            "research.batch5_registry_switch", "edge.unproven_consistency"} <= set(a["drift"])


def test_unification_audit_missing_input_is_incomplete_and_tamper_is_drift(tmp_path):
    from architecture.health.unification_audit import build_unification_audit
    root = _ua_root(tmp_path)
    (root / "reports/grok/M19/macro_calendar.json").unlink()
    a = build_unification_audit(root)
    assert a["overall_status"] == "INCOMPLETE" and a["unknown"] == ["macro.calendar_6_banks"]
    led = root / "data" / "mission_ledger" / "mission_ledger.jsonl"
    led.write_text(led.read_text(encoding="utf-8").replace("PAPER_TRADER:BTC", "PAPER_TRADER:ETH", 1), encoding="utf-8")
    b = build_unification_audit(root)
    assert b["overall_status"] == "DRIFT_DETECTED" and "ledger.chain" in b["drift"]


def test_exchange_holidays_2026_2027_modeled_and_skipped():
    from datetime import date, datetime, timezone
    from architecture.markets.weekday_session_gate import is_holiday, holiday_name, venue_status
    # Thanksgiving 2026-11-26 (Thursday) -> NYSE closed, next open is Friday 2026-11-27 09:30 ET (14:30 UTC / 18:00 Tehran)
    assert is_holiday("NYSE", date(2026, 11, 26)) is True
    assert holiday_name("NYSE", date(2026, 11, 26)) == "Thanksgiving Day"
    thx = datetime(2026, 11, 26, 15, 0, tzinfo=timezone.utc)
    st_ny = venue_status("NYSE", thx)
    assert st_ny["open"] is False
    assert st_ny["holidays_modeled"] is True
    assert st_ny["holiday_today"] is True
    assert st_ny["next_open_utc"] == "2026-11-27T14:30:00Z"
    assert st_ny["next_open_tehran"] == "2026-11-27 18:00"
    # Good Friday 2026-04-03 -> XETRA closed, Easter Monday 2026-04-06 -> also closed, next open Tuesday 2026-04-07 09:00 CEST (07:00 UTC)
    gf = datetime(2026, 4, 3, 10, 0, tzinfo=timezone.utc)
    st_xe = venue_status("XETRA", gf)
    assert st_xe["open"] is False and st_xe["next_open_utc"] == "2026-04-07T07:00:00Z"
    # TSE Culture Day 2026-11-03 (Tuesday) -> closed, next open Wednesday 2026-11-04 09:00 JST (00:00 UTC)
    cul = datetime(2026, 11, 3, 2, 0, tzinfo=timezone.utc)
    st_tse = venue_status("TSE", cul)
    assert st_tse["open"] is False and st_tse["next_open_utc"] == "2026-11-04T00:00:00Z"
    # CME Globex Christmas 2026-12-25 (Friday) -> Thursday 17:00 CT session is skipped
    xmas_eve = datetime(2026, 12, 24, 23, 30, tzinfo=timezone.utc)
    st_cme = venue_status("CME_GLOBEX", xmas_eve)
    assert st_cme["open"] is False


def test_m13_gold_soak_enforce_witness_invariant_blocks_single_source_verified():
    from scripts.m13_gold_soak import _enforce_witness_invariant
    status = {
        "last_cycle": {
            "cycle": 929,
            "witness_state": "VERIFIED",
            "witness_reason": "insufficient_independent_sources (only ['goldapi_spot'] answered fresh)",
            "price_usd": 4007.9,
        },
        "ledger_state": {
            "price_usd": 4007.9,
            "witness": {
                "state": "UNRESOLVED",
                "quotes": [{"provider_id": "goldapi_spot", "price_usd": 4007.9}],
            },
        },
    }
    _enforce_witness_invariant(status)
    assert status["last_cycle"]["witness_state"] == "UNRESOLVED"
    assert status["last_cycle"]["price_usd"] is None
    assert status["ledger_state"]["price_usd"] is None


def test_batch6_screen_refuses_a_clone_and_a_flat_book():
    from architecture.learning.walk_forward import atr_normalized_return, safe_simple_return
    from architecture.markets.map_elites_lab import active_share, screen_book
    assert safe_simple_return(-37.0, -20.0) is None
    assert atr_normalized_return(-37.0, -20.0, 5.0) == 3.4
    assert active_share([1, 1, 1, 1]) == 0.0
    series = [0.01 * ((i % 7) - 3) for i in range(40)]
    refused, why = screen_book(series, {"tsmom_12m": list(series)}, {}, 0.4, 0.25)
    assert refused is False and "rho" in why
    flat, why = screen_book(series, {}, {}, 0.1, 0.25)
    assert flat is False and "active_share" in why


def test_discovery_source_is_partial_when_only_one_feed_returns_tokens():
    from architecture.markets.token_safety_live import discover_candidates
    out = discover_candidates(_getter(), now=datetime(2026, 10, 24, tzinfo=timezone.utc))
    assert out["discovery_source"] == "PARTIAL_LIVE"
    assert out["address_form"] == "EIP55_CHECKSUM"
    assert any(e["tokens"] > 0 for e in out["endpoints"])
    assert sum(1 for e in out["endpoints"] if e["tokens"] > 0) == 1


def test_exam_receipt_keeps_live_and_historical_scores_apart(tmp_path):
    from architecture.learning.exam import build_live_exam_receipt
    _paper_rows(tmp_path / "reports" / "grok" / "PAPER", [
        {"ts": "2026-10-24T01:00:00Z", "event": "HOLD", "symbol": "BTC", "desk": "CRYPTO", "side": "SHORT", "price": 100.0},
        {"ts": "2026-10-24T02:00:00Z", "event": "HOLD", "symbol": "ETH", "desk": "CRYPTO", "side": "SHORT", "price": 100.0}])
    rec = build_live_exam_receipt(tmp_path)
    assert rec["live_daemon_episodes"]["status"] == "ACCUMULATING"
    assert rec["live_daemon_episodes"]["count"] == 1
    assert rec["historical_oos_episodes"]["status"] == "INSUFFICIENT_LOCAL_HISTORY"


def test_cognitive_graph_lists_every_registry_agent_without_inventing_pass(tmp_path):
    from architecture.mission.cognitive_graph_m12 import build_cognitive_graph
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "agent_registry.yaml").write_text(
        "agents:\n  - agent_id: AG-01\n    name: Solo\n    allowed_authority: [OBSERVE]\n    forbidden_authority: [PROMOTE]\n",
        encoding="utf-8")
    g = build_cognitive_graph(tmp_path)
    assert g["registry_agents"] == 1
    assert g["agents"][0]["verdict"] == "UNRESOLVED" and g["agents"][0]["authority_ok"] is True
    (tmp_path / "reports/grok/M64").mkdir(parents=True)
    (tmp_path / "reports/grok/M64/whitehat_security_audit.json").write_text('{"overall_verdict": "CLEAN"}', encoding="utf-8")
    (tmp_path / "config/agent_registry.yaml").write_text(
        "agents:\n  - agent_id: AG-09\n    name: Security\n    allowed_authority: [OBSERVE, VETO]\n",
        encoding="utf-8")
    g2 = build_cognitive_graph(tmp_path)
    assert g2["agents"][0]["verdict"] == "PASS" and g2["agents"][0]["authority_ok"] is True


def test_eip55_checksum_official_vectors_and_pool32_normalization():
    from architecture.markets.token_safety_live import _normalize_pool_id, to_eip55_checksum, VETTED_TOKEN_CONTRACTS
    vectors = [
        "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed",
        "0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359",
        "0xdbF03B407c01E7cD3CBea99509d93f8DDDC8C6FB",
        "0xD1220A0cf47c7B9Be7A2E6BA89F429762e7b9aDb",
    ]
    for vec in vectors:
        assert to_eip55_checksum(vec.lower()) == vec
        assert to_eip55_checksum(vec.upper().replace("0X", "0x")) == vec
    assert VETTED_TOKEN_CONTRACTS["UNI"]["address"] == "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984"
    pool32 = "0x053f6a47ccba79e7d5d623173ed6dd5a31cf19c28bae0fb8276f4506295f90da"
    assert _normalize_pool_id(pool32) == "pool32:" + pool32[2:]
    pool20 = "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984"
    assert _normalize_pool_id(pool20) == pool20


def test_validate_imports_secret_scanner_strict_on_keys_and_allows_public_pool_and_rss_urls():
    from scripts.validate_imports import scan_text_for_secrets
    priv_hex = "0x" + "a1b2c3d4" * 8
    sol_key = "5" * 88
    openai_key = "sk-" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4"
    # Real secrets must fail in code, config, and JSON private/config fields
    assert scan_text_for_secrets(f"PRIVATE_KEY = '{priv_hex}'", suffix=".py")
    assert scan_text_for_secrets(f"{{\"private_key\": \"{priv_hex}\"}}", suffix=".json")
    assert scan_text_for_secrets(f"{{\"wallet_secret\": \"{sol_key}\"}}", suffix=".json")
    assert scan_text_for_secrets(f"{{\"url\": \"https://api.example.com?key={openai_key}\"}}", suffix=".json")
    # Public Uniswap v4 32-byte pool key hash in explicit pool field and Google News RSS URL path must pass
    assert scan_text_for_secrets(f"{{\"source_b\": \"{priv_hex}\"}}", suffix=".json")
    assert not scan_text_for_secrets(f"{{\"pool\": \"{priv_hex}\"}}", suffix=".json")
    assert not scan_text_for_secrets(
        f"{{\"source_b\": \"dexscreener:uniswap:{priv_hex}\"}}", suffix=".json")
    assert not scan_text_for_secrets(
        f"{{\"source_b\": \"dexscreener:uniswap:pool32:{priv_hex[2:]}\"}}", suffix=".json")
    assert not scan_text_for_secrets(
        f"{{\"links\": [\"https://news.google.com/rss/articles/{sol_key}\"]}}",
        suffix=".json",
    )


def test_cognitive_graph_full_43_agent_repo_wiring():
    from architecture.mission.cognitive_graph_m12 import _ARTIFACTS, build_cognitive_graph
    assert len(_ARTIFACTS) == 43
    root = Path(__file__).resolve().parents[1]
    snap = build_cognitive_graph(root)
    assert snap["registry_agents"] == 43
    assert snap["authority_violations"] == []
    by_id = {a["agent_id"]: a for a in snap["agents"]}
    assert by_id["AG-08"]["verdict"] in ("PASS", "HOLD")
    assert by_id["AG-09"]["verdict"] == "PASS"
    assert by_id["AG-14"]["verdict"] == "VETO"
    for eq_id in ("AG-29", "AG-30", "AG-31"):
        assert by_id[eq_id]["verdict"] in ("PASS", "HOLD")
    assert snap["critical_path_blockers"] and snap["dependency_edges"]
    assert set(snap["pillar_owners"]) == {
        "P1_MARKETS_QUANT", "P2_CORE_BRAIN_REASONING", "P3_LEARNING_FORECASTING",
        "P4_SECURITY_WHITE_HATS", "P5_SYSTEM_PERFORMANCE_BODY", "P6_STATISTICS_VALIDATION",
        "P7_MACRO_EVENTS_OSINT"}


def test_hysteresis_holds_a_small_weight_change_and_the_cost_hurdle_blocks_a_tiny_edge():
    from architecture.learning.walk_forward import apply_weight_hysteresis, clears_cost_hurdle
    assert apply_weight_hysteresis([0.5, 0.5], [0.52, 0.48], 0.05) == [0.5, 0.5]
    moved = apply_weight_hysteresis([0.5, 0.5], [0.8, 0.2], 0.05)
    assert abs(sum(moved) - 1) < 1e-9 and moved[0] > 0.7
    assert clears_cost_hurdle(0.0001, 0.5, 15.0) is False
    assert clears_cost_hurdle(0.02, 0.5, 15.0) is True
    assert clears_cost_hurdle(0.0, 0.0, 15.0) is True


def test_calibration_refuses_a_training_row_that_is_not_strictly_before_the_test():
    from architecture.learning.calibration import brier_score, fit_and_apply
    train = [{"ts": "2020-01-02", "y": True, "features": {"vol_ratio": 1.0}}]
    test = [{"ts": "2020-01-02", "y": False, "features": {"vol_ratio": 1.0}}]
    leaked = fit_and_apply(train, test, ("vol_ratio",))
    assert leaked["leaked"] is True and leaked["probs"] == []
    train = [{"ts": f"2020-01-{i:02d}", "y": i % 2 == 0, "features": {"vol_ratio": 0.5 + (i % 3) * 0.2}} for i in range(1, 21)]
    test = [{"ts": "2020-02-01", "y": True, "features": {"vol_ratio": 0.8}}]
    fit = fit_and_apply(train, test, ("vol_ratio",))
    assert fit["leaked"] is False and fit["status"] == "FIT" and 0.0 < fit["probs"][0] < 1.0
    assert brier_score([0.5, 0.5], [0.0, 1.0]) == 0.25


def test_portfolio_l1_gate_holds_when_only_one_name_moves_a_little():
    from architecture.learning.walk_forward import apply_portfolio_l1_gate, portfolio_l1_turnover
    assert portfolio_l1_turnover([0.5, 0.5], [0.62, 0.38]) == pytest.approx(0.12)
    assert apply_portfolio_l1_gate([0.5, 0.5], [0.62, 0.38], 0.25) == [0.5, 0.5]
    moved = apply_portfolio_l1_gate([0.5, 0.5], [0.9, 0.1], 0.25)
    assert moved[0] == pytest.approx(0.9) and sum(moved) == pytest.approx(1.0)


def test_institutional_proxy_requires_every_listed_condition():
    from architecture.markets.token_safety_live import institutional_proxy_ok
    gp = {"is_open_source": True, "is_honeypot": False, "is_mintable": None, "buy_tax": 0, "sell_tax": 0.0,
          "authority": {"is_proxy": True, "owner_change_balance": False, "hidden_owner": False,
                        "can_take_back_ownership": False}}
    assert institutional_proxy_ok(gp, 600_000) is True
    assert institutional_proxy_ok(gp, 100_000) is False
    assert institutional_proxy_ok({**gp, "is_mintable": True}, 600_000) is False
    eoa = {**gp, "authority": {**gp["authority"], "owner_change_balance": True}}
    assert institutional_proxy_ok(eoa, 600_000) is False
    bare = {**gp, "authority": {**gp["authority"], "is_proxy": False}}
    assert institutional_proxy_ok(bare, 600_000) is False
