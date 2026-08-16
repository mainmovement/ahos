#!/usr/bin/env python3
"""Paper Trading Lab tests — anti-bias laws pinned (directive §8/§14.8).
All fixtures synthetic; discovery store opened READ-ONLY by the lab itself."""
import sys, sqlite3
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from discovery import observations as obs, lifecycle
from paper_trading import ledger, engine, entry_rules, exit_rules, cost_model as cm, reports

T0 = 1_756_300_000.0


def _disc(tmp_path) -> Path:
    p = tmp_path / "disc.sqlite"
    conn = obs.open_store(p)
    conn.commit(); conn.close()
    return p


def _token(db, sym, first_seen, chain="solana"):
    conn = sqlite3.connect(str(db)); conn.row_factory = sqlite3.Row
    tid = obs.upsert_token(conn, chain, f"addr-{sym}", first_seen, "fixture")
    lifecycle.register_discovery(conn, tid, first_seen)
    conn.execute("UPDATE observation_state SET state='OBSERVING' WHERE token_id=?", (tid,))
    conn.commit(); conn.close()
    return tid


def _obs(db, tid, ts, price, liq):
    conn = sqlite3.connect(str(db)); conn.row_factory = sqlite3.Row
    raw = obs.store_raw(conn, "fx", f"fx://{tid}/{ts}", ts, 200, {})
    obs.record_observation(conn, tid, "fx", ts, raw, pair="P",
                           metrics={"price_usd": price, "liquidity_usd": liq,
                                    "volume_24h": 5000.0, "market_cap": 1e6,
                                    "txns_5m_buys": 10, "txns_5m_sells": 5})
    conn.commit(); conn.close()


def _paper(tmp_path) -> Path:
    return tmp_path / "paper.sqlite"


# ------------------------------------------------------------- leakage / look-ahead
def test_decision_uses_only_asof_data_future_pollution_ignored(tmp_path):
    d1, p1 = _disc(tmp_path), _paper(tmp_path)
    tid = _token(d1, "FULL", T0 - 3600)
    _obs(d1, tid, T0 - 600, price=1.0, liq=50_000)
    _obs(d1, tid, T0 + 3600, price=9.9, liq=50_000)      # FUTURE row — must not influence decision
    st1 = engine.run_cycle(p1, d1, now=T0, pal=None)
    conn = sqlite3.connect(str(p1)); conn.row_factory = sqlite3.Row
    tr = conn.execute("SELECT * FROM paper_trade").fetchone()
    assert st1["entries"] == 1 and tr["entry_price_observed"] == 1.0 and tr["entry_ts"] == T0 - 600
    snap = conn.execute("SELECT features_json FROM decision_snapshot").fetchone()
    assert '"price_usd": 1.0' in snap["features_json"] and "9.9" not in snap["features_json"]
    conn.close()
    # rebuild identical history WITHOUT the future row → identical entry (leakage impossibility proof)
    sub = tmp_path / "nofuture"; sub.mkdir()
    d2, p2 = _disc(sub), _paper(sub)
    tid2 = _token(d2, "FULL", T0 - 3600)
    _obs(d2, tid2, T0 - 600, price=1.0, liq=50_000)
    engine.run_cycle(p2, d2, now=T0, pal=None)
    c2 = sqlite3.connect(str(p2)); c2.row_factory = sqlite3.Row
    tr2 = c2.execute("SELECT entry_price_observed, entry_price_exec, qty FROM paper_trade").fetchone()
    assert dict(tr2)["entry_price_observed"] == tr2["entry_price_observed"]
    assert abs(tr["entry_price_exec"] - tr2["entry_price_exec"]) < 1e-12
    assert abs(tr["qty"] - tr2["qty"]) < 1e-9
    c2.close()


def test_no_duplicate_trades_per_token(tmp_path):
    d, p = _disc(tmp_path), _paper(tmp_path)
    tid = _token(d, "DUP", T0 - 3600)
    _obs(d, tid, T0 - 600, 1.0, 50_000)
    engine.run_cycle(p, d, now=T0, pal=None)
    st2 = engine.run_cycle(p, d, now=T0, pal=None)        # same instant re-run
    assert st2["entries"] == 0
    conn = sqlite3.connect(str(p))
    assert conn.execute("SELECT COUNT(*) FROM paper_trade").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM decision_snapshot").fetchone()[0] == 1
    conn.close()


def test_invalid_and_unknown_data_never_enter(tmp_path):
    d, p = _disc(tmp_path), _paper(tmp_path)
    t1 = _token(d, "NEG", T0 - 3600); _obs(d, t1, T0 - 600, -1.0, 50_000)     # invalid price
    t2 = _token(d, "NOLIQ", T0 - 3600); _obs(d, t2, T0 - 600, 1.0, None)      # UNKNOWN liq
    t3 = _token(d, "DUST", T0 - 3600); _obs(d, t3, T0 - 600, 1.0, -7.4e-15)   # R-23 EPS dust
    st = engine.run_cycle(p, d, now=T0, pal=None)
    assert st["entries"] == 0 and st["not_qualified"] == 3
    conn = sqlite3.connect(str(p)); conn.row_factory = sqlite3.Row
    reasons = {r["reason"] for r in conn.execute("SELECT reason FROM decision_snapshot")}
    assert any("non-positive" in r for r in reasons)
    assert any("liquidity UNKNOWN" in r for r in reasons)
    assert any("liquidity" in r and "< min" in r for r in reasons)           # dust cannot qualify
    conn.close()


# ------------------------------------------------------------- ledger law
def _one_trade(p, d):
    tid = _token(d, "IMM", T0 - 3600)
    _obs(d, tid, T0 - 600, 1.0, 50_000)
    engine.run_cycle(p, d, now=T0, pal=None)


def test_ledger_immutable_by_construction(tmp_path):
    d, p = _disc(tmp_path), _paper(tmp_path)
    _one_trade(p, d)
    conn = sqlite3.connect(str(p))
    for table, col in (("paper_trade", "created_utc"), ("decision_snapshot", "created_utc"),
                       ("monitor_event", "event"), ("strategy_version", "created_utc")):
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            conn.execute(f"UPDATE {table} SET {col}='HACK'")
        conn.rollback()
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        conn.execute("DELETE FROM paper_trade")
    conn.rollback(); conn.close()


def test_security_veto_blocks_entry_pure_fn():
    dec, reason = entry_rules.evaluate_entry(
        now=T0, first_seen_ts=T0 - 3600, price_usd=1.0, liquidity_usd=50_000,
        security={"verdict": "SECURITY_VETO", "veto_reasons": ["honeypot"]})
    assert dec == "NOT_QUALIFIED" and "honeypot" in reason
    dec2, _ = entry_rules.evaluate_entry(  # PASS_WITH_UNKNOWN allowed but recorded honestly
        now=T0, first_seen_ts=T0 - 3600, price_usd=1.0, liquidity_usd=50_000,
        security={"verdict": "PASS_WITH_UNKNOWN", "coverage": 0.0})
    assert dec2 == "QUALIFIED_ENTRY"


# ------------------------------------------------------------- exits & accounting
def test_stop_loss_exit_and_exact_accounting(tmp_path):
    d, p = _disc(tmp_path), _paper(tmp_path)
    _one_trade(p, d)
    conn = sqlite3.connect(str(p)); conn.row_factory = sqlite3.Row
    tr = conn.execute("SELECT * FROM paper_trade").fetchone(); tid_ = tr["token_id"]
    conn.close()
    _obs(d, tid_, T0, price=0.5, liq=50_000)               # fresh crash observation
    st = engine.run_cycle(p, d, now=T0 + 60, pal=None)
    conn = sqlite3.connect(str(p)); conn.row_factory = sqlite3.Row
    x = conn.execute("SELECT * FROM paper_exit").fetchone()
    assert st["exits"] == 1 and x["exit_reason"] == "STOP_LOSS"
    # exact decomposition identity: net == gross - slippage - cost
    assert abs(x["net_pnl_usd"] - (x["gross_pnl_usd"] - x["slippage_usd"] - x["cost_total_usd"])) < 1e-9
    assert x["gross_pnl_usd"] < 0 and x["net_pnl_usd"] < x["gross_pnl_usd"]
    # observed path has exactly one post-entry print (0.5): MFE==MAE==-0.5 is the HONEST
    # sparse-data measurement — we do not interpolate candles that were never observed
    assert x["mfe_pct"] == pytest.approx(-0.5) and x["mae_pct"] == pytest.approx(-0.5)
    conn.close()


def test_gap_ambiguity_sl_before_tp_pure_fn():
    hit = exit_rules.check_exits(entry_exec=1.02, entry_ts=T0, now=T0 + 600,
                                 obs_price=0.5, obs_liq=50_000, obs_ts=T0 + 600,
                                 consec_liq_breaches=0, security_recheck=None)
    assert hit["reason"] == "STOP_LOSS"
    hit2 = exit_rules.check_exits(entry_exec=1.02, entry_ts=T0, now=T0 + 600,
                                  obs_price=1.60, obs_liq=50_000, obs_ts=T0 + 600,
                                  consec_liq_breaches=0, security_recheck=None)
    assert hit2["reason"] == "TAKE_PROFIT"


def test_horizon_without_fresh_observation_is_invalid_never_stale_exit(tmp_path):
    d, p = _disc(tmp_path), _paper(tmp_path)
    _one_trade(p, d)                                       # entry obs at T0-600
    st = engine.run_cycle(p, d, now=T0 + 49 * 3600, pal=None)   # 49h later, no new data
    assert st["exits"] == 0 and st["invalidations"] == 1
    conn = sqlite3.connect(str(p)); conn.row_factory = sqlite3.Row
    assert conn.execute("SELECT COUNT(*) c FROM paper_exit").fetchone()["c"] == 0
    inv = conn.execute("SELECT reason FROM invalidation").fetchone()
    assert "no observation within" in inv["reason"]        # honest, preserved
    conn.close()


def test_time_exit_with_fresh_observation(tmp_path):
    d, p = _disc(tmp_path), _paper(tmp_path)
    _one_trade(p, d)
    conn = sqlite3.connect(str(p)); conn.row_factory = sqlite3.Row
    tkn = conn.execute("SELECT token_id FROM paper_trade").fetchone()["token_id"]; conn.close()
    now2 = T0 - 600 + 49 * 3600                             # 30 min past horizon
    _obs(d, tkn, now2 - 300, price=1.10, liq=50_000)      # fresh, between SL and TP
    st = engine.run_cycle(p, d, now=now2, pal=None)
    conn = sqlite3.connect(str(p)); conn.row_factory = sqlite3.Row
    x = conn.execute("SELECT * FROM paper_exit").fetchone()
    assert st["exits"] == 1 and x["exit_reason"] == "TIME_EXIT"
    assert x["exit_obs_ts"] == now2 - 300 and abs(x["exit_price_observed"] - 1.10) < 1e-12
    conn.close()


def test_gross_win_net_loss_reported_as_loss(tmp_path):
    d, p = _disc(tmp_path), _paper(tmp_path)
    _one_trade(p, d)                                       # entry ~1.0 with 200bps impact
    conn = sqlite3.connect(str(p)); conn.row_factory = sqlite3.Row
    tkn = conn.execute("SELECT token_id FROM paper_trade").fetchone()["token_id"]; conn.close()
    now2 = T0 - 600 + 49 * 3600
    _obs(d, tkn, now2 - 300, price=1.005, liq=50_000)     # +0.5% gross — below round-trip costs
    engine.run_cycle(p, d, now=now2, pal=None)
    rep = reports.paper_report(str(p))
    assert rep["closed_positions"] == 1
    assert rep["gross_pnl_usd"] > 0
    assert rep["net_pnl_usd"] < 0                          # loss after costs — reported as loss
    assert rep["gross_win_but_net_loss_count"] == 1
    assert rep["win_rate"] == 0.0
    assert "INSUFFICIENT_CLOSED_TRADES" in rep["expectancy_gate"]


def test_liquidity_collapse_two_consecutive(tmp_path):
    d, p = _disc(tmp_path), _paper(tmp_path)
    _one_trade(p, d)
    conn = sqlite3.connect(str(p)); conn.row_factory = sqlite3.Row
    tkn = conn.execute("SELECT token_id FROM paper_trade").fetchone()["token_id"]; conn.close()
    _obs(d, tkn, T0 + 600, price=1.0, liq=1_500)           # breach 1 — no exit yet
    st1 = engine.run_cycle(p, d, now=T0 + 660, pal=None)
    assert st1["exits"] == 0
    _obs(d, tkn, T0 + 1200, price=1.0, liq=1_200)          # breach 2 consecutive → out
    st2 = engine.run_cycle(p, d, now=T0 + 1260, pal=None)
    conn = sqlite3.connect(str(p)); conn.row_factory = sqlite3.Row
    x = conn.execute("SELECT exit_reason FROM paper_exit").fetchone()
    assert st2["exits"] == 1 and x["exit_reason"] == "LIQUIDITY_COLLAPSE"
    conn.close()


def test_chronology_violation_invalidates_and_preserves(tmp_path):
    d, p = _disc(tmp_path), _paper(tmp_path)
    real = _token(d, "C", T0)                              # discovery token first
    _obs(d, real, T0 - 600, 1.0, 50_000)                   # only observation is BEFORE crafted entry
    conn = ledger.open_paper(p)
    sid = ledger.record_snapshot(conn, token_id=real, chain="solana", address="a", symbol="C",
                                 discovered_ts=T0, decision_ts=T0, features={}, security={},
                                 rule_version="PT-BASELINE-v1", decision="QUALIFIED_ENTRY", reason="fx")
    ledger.open_trade(conn, strategy_version="PT-BASELINE-v1", snapshot_id=sid, token_id=real,
                      chain="solana", address="a", symbol="C", discovered_ts=T0,
                      entry_decision_ts=T0, entry_ts=T0 + 1000,   # entry AFTER the only observation
                      entry_price_observed=1.0, fee_bps=100, entry_slippage_bps=25,
                      entry_price_exec=1.0025, notional_usd=1000, qty=900, fee_entry_usd=10,
                      liq_at_entry=50_000, exit_rule_version="PT-X1-v1",
                      monitoring_horizon_ts=T0 + 1000 + 48 * 3600)
    conn.close()
    st = engine.run_cycle(p, d, now=T0 + 2000, pal=None)
    assert st["invalidations"] == 1
    conn = sqlite3.connect(str(p)); conn.row_factory = sqlite3.Row
    assert "chronology" in conn.execute("SELECT reason FROM invalidation").fetchone()["reason"]
    assert conn.execute("SELECT COUNT(*) c FROM paper_exit").fetchone()["c"] == 0
    conn.close()


def test_cost_model_identities():
    b = cm.buy(1000.0, 1.0, 50_000)
    assert abs(b["slippage_bps"] - 200.0) < 1e-9           # impact 1000/50k*1e4 = 200 > floor 25
    assert abs(b["exec_price"] - 1.02) < 1e-12
    assert b["slippage_bps"] == cm.slippage_bps(1000.0, 50_000)
    assert cm.slippage_bps(1000.0, None) is None           # UNKNOWN liq → UNKNOWN slippage
    assert cm.slippage_bps(1000.0, 0) is None              # dust/zero → UNKNOWN, never guessed
    s = cm.sell(b["qty"], 1.10, 50_000)
    d = cm.pnl_decomposition(b["qty"], 1.0, b["exec_price"], b["fee_entry_usd"],
                             1.10, s["exec_price"], s["fee_exit_usd"])
    assert d["gross_pnl_usd"] > 0 and abs(d["net_pnl_usd"] -
        (d["gross_pnl_usd"] - d["slippage_usd"] - d["cost_total_usd"])) < 1e-9


def test_report_structure_and_gates(tmp_path):
    p = _paper(tmp_path)
    conn = ledger.open_paper(p); conn.close()              # schema-init (no data)
    rep = reports.paper_report(str(p))
    for k in ("gross_pnl_usd", "slippage_usd", "cost_usd", "net_pnl_usd", "liq_bands",
              "candidates_decided", "invalidated"):
        assert k in rep
    assert "INSUFFICIENT_CLOSED_TRADES" in rep["expectancy_gate"]  # no profitability language below n
    txt = reports.render_two_track({"tokens": 1, "observations": 2, "resolved": 0,
                                    "cohort_readiness": "gated", "h14_h20_gate": "pre-registered only"}, rep)
    assert "RESEARCH TRACK" in txt and "PAPER TRACK" in txt and "تصمیم نهایی با کاربر است" in txt
