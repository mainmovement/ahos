#!/usr/bin/env python3
"""PT-X3-v2 regression + fault-injection battery (R-C3 closure evidence).

Laws under test:
  - obs older than 6h at decision time must NEVER ground an exit/settlement/realizable
    realization → NO_DATA (or INVALID via inherited base law); belt: _settle refuses.
  - price-INDEPENDENT closes (confirmed honeypot/unexitsable) stay allowed with NULL price.
  - PT-X3-v1 logic is byte-preserved behind the gate (fresh-data behavior identical).
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_paper_trading_v3 import (T0, ROOT, add_obs, decide_kw, mk_discovery, mk_paper,
                                   mk_trade)  # reuse fixtures/helpers (no duplication)

from paper_trading import decision_v3 as dv3, engine_v3, exit_rules

STALE_6H = 21_601
STALE_16H = 16 * 3600


# ---------------------------------------------------------------- pure decision gate
def test_rc3_core_stale_trap_values_become_no_data_not_total_loss():
    """v1 would call TOTAL_LOSS here (gas trap); on a 16h-stale obs v2 must say NO_DATA."""
    stale_ts = T0 + 60 - STALE_16H
    d1 = dv3.decide_v1(**decide_kw(obs_price=0.075, chain="ethereum", obs_ts=T0 + 30))
    assert d1["action"] == "TOTAL_LOSS"                       # v1 logic proven live on fresh obs
    d2 = dv3.decide(**decide_kw(obs_price=0.075, chain="ethereum", obs_ts=stale_ts))
    assert d2["action"] == "NO_DATA" and d2["reason"] == "STALE_OBSERVATION"
    assert d2["kind"] == "NONE"


def test_stale_divergence_values_never_profit_lock():
    stale_ts = T0 + 60 - STALE_16H
    fresh = dv3.decide(**decide_kw(obs_price=3.4, obs_liq=1e6, obs_ts=T0 + 30,
                                   monitor_peak_price=3.5, monitor_obs_count=2))
    assert fresh["reason"] == "DIVERGENCE_PROFIT_LOCK"
    blocked = dv3.decide(**decide_kw(obs_price=3.4, obs_liq=1e6, obs_ts=stale_ts,
                                     monitor_peak_price=3.5, monitor_obs_count=2))
    assert blocked["action"] == "NO_DATA" and blocked["reason"] == "STALE_OBSERVATION"


def test_freshness_boundary_21600_fresh_21601_stale():
    kw_fresh = decide_kw(obs_price=2.2, obs_liq=None, obs_ts=T0 + 60 - 21_600)
    assert dv3.decide(**kw_fresh)["action"] == "NO_DATA"      # liq None → v1 unpriceable guard
    kw_edge = decide_kw(obs_price=3.4, obs_liq=1e6, obs_ts=T0 + 60 - 21_600,
                        monitor_peak_price=3.5, monitor_obs_count=2)
    assert dv3.decide(**kw_edge)["reason"] == "DIVERGENCE_PROFIT_LOCK"      # ≤6h ⇒ fresh path
    kw_over = decide_kw(obs_price=3.4, obs_liq=1e6, obs_ts=T0 + 60 - 21_601,
                        monitor_peak_price=3.5, monitor_obs_count=2)
    assert dv3.decide(**kw_over)["reason"] == "STALE_OBSERVATION"           # >6h ⇒ blocked


def test_stale_confirmed_honeypot_closes_without_any_price():
    d = dv3.decide(**decide_kw(obs_price=777.0, obs_liq=9e9, obs_ts=T0 + 60 - STALE_16H,
                               classification="CONFIRMED_HONEYPOT", sec_veto_now=True))
    assert d["action"] == "TOTAL_LOSS" and d["price_independent"] is True
    assert "no price used" in d["why"]


def test_stale_critical_risk_needs_price_therefore_no_data():
    d = dv3.decide(**decide_kw(obs_ts=T0 + 60 - STALE_6H, classification="CRITICAL_RISK",
                               sec_veto_now=True))
    assert d["action"] == "NO_DATA"                           # salvage needs a fresh price


def test_stale_base_trigger_follows_inherited_invalid_law():
    """Frozen PT-X1-v1 semantics, verified not assumed: (a) a stale SL-looking print is NOT an
    exit signal at all (check_exits returns None — SL/TP need a usable price) ⇒ v2 says NO_DATA;
    (b) a hard obligation that can't be priced (48h horizon + stale obs) ⇒ INVALID per X1 law."""
    hit_none = exit_rules.check_exits(entry_exec=1.0, entry_ts=T0, now=T0 + STALE_16H,
                                      obs_price=0.5, obs_liq=1e6, obs_ts=T0 + 30,
                                      consec_liq_breaches=0, security_recheck=None)
    assert hit_none is None                                     # frozen law prices nothing stale
    d = dv3.decide(**decide_kw(now=T0 + STALE_16H, obs_price=0.5, obs_ts=T0 + 30,
                               base_hit=hit_none))
    assert d["action"] == "NO_DATA"
    hit_inv = exit_rules.check_exits(entry_exec=1.0, entry_ts=T0, now=T0 + 49 * 3600,
                                     obs_price=0.5, obs_liq=1e6, obs_ts=T0 + 30,
                                     consec_liq_breaches=0, security_recheck=None)
    assert hit_inv["reason"].startswith("INVALID_DATA_UNAVAILABLE")
    d2 = dv3.decide(**decide_kw(now=T0 + 49 * 3600, obs_price=0.5, obs_ts=T0 + 30, base_hit=hit_inv))
    assert d2["action"] == "INVALID"


def test_v1_card_and_logic_are_immutable_artifacts():
    cards = json.loads((ROOT / "paper_trading" / "strategies.json").read_text())["strategies"]
    vers = {c["version"] for c in cards}
    assert {"PT-X3-v1", "PT-X3-v2"} <= vers
    assert dv3.EXIT_V3["version"] == "PT-X3-v1"               # frozen object still present
    assert dv3.EXIT_V32["version"] == "PT-X3-v2"
    assert dv3.decide_v1 is not None                          # v1 logic preserved verbatim


# ---------------------------------------------------------------- engine fault injection
def _single_trade_store(tmp_path, token, **mk):
    disc = mk_discovery(tmp_path)
    conn = mk_paper(tmp_path)
    tid = mk_trade(conn, token_id=token, **mk)
    conn.close()
    return disc, tid


def test_fault_16h_stale_obs_zero_writes_no_settlement(tmp_path):
    disc, tid = _single_trade_store(tmp_path, "S1", qty=2.0, price=1.0, alloc=2.0)
    add_obs(tmp_path, disc, "S1", T0 + 30, price=0.40, liq=1e6)   # SL-looking but STALE at run
    now = T0 + 30 + STALE_16H
    st = engine_v3.run_cycle_v3(str(tmp_path / "paper.sqlite"), str(disc), now=now, pal=None)
    assert st["exits"] == 0 and st["partials"] == 0 and st["invalidations"] == 0
    p = sqlite3.connect(str(tmp_path / "paper.sqlite")); p.row_factory = sqlite3.Row
    assert p.execute("SELECT COUNT(*) FROM paper_exit_v3").fetchone()[0] == 0
    assert p.execute("SELECT COUNT(*) FROM portfolio_ledger WHERE event='RECLAIM'").fetchone()[0] == 0
    dec = p.execute("SELECT action, reason FROM position_decision_event WHERE trade_id=?",
                    (tid,)).fetchone()
    assert (dec["action"], dec["reason"]) == ("NO_DATA", "STALE_OBSERVATION")
    state = p.execute("SELECT state FROM position_state_event WHERE trade_id=? ORDER BY id DESC "
                      "LIMIT 1", (tid,)).fetchone()[0]
    assert state == "NO_DATA"
    assert p.execute("SELECT cash_after FROM portfolio_ledger ORDER BY id DESC LIMIT 1"
                     ).fetchone()[0] == pytest.approx(18.0)      # cash untouched
    snap = p.execute("SELECT obs_ts FROM realizable_snapshot WHERE trade_id=?",
                     (tid,)).fetchone()
    assert snap and snap["obs_ts"] == T0 + 30                    # telemetry kept, marked stale
    p.close()


def test_recovery_after_stale_gap_settles_normally_on_fresh_obs(tmp_path):
    disc, tid = _single_trade_store(tmp_path, "S2", qty=2.0, price=1.0, alloc=2.0)
    add_obs(tmp_path, disc, "S2", T0 + 30, price=1.0, liq=1e6)
    engine_v3.run_cycle_v3(str(tmp_path / "paper.sqlite"), str(disc), now=T0 + 30 + STALE_16H,
                           pal=None)                            # stale pass: nothing priced
    fresh_ts = T0 + 30 + STALE_16H + 60
    add_obs(tmp_path, disc, "S2", fresh_ts, price=2.0, liq=20.0)  # fresh TP print
    st = engine_v3.run_cycle_v3(str(tmp_path / "paper.sqlite"), str(disc), now=fresh_ts + 30,
                                pal=None)
    assert st["partials"] == 1                                    # v1 partial math intact
    p = sqlite3.connect(str(tmp_path / "paper.sqlite")); p.row_factory = sqlite3.Row
    x = p.execute("SELECT * FROM paper_exit_v3 WHERE trade_id=?", (tid,)).fetchone()
    assert x["rule_version"] == "PT-X3-v2" and x["exit_reason"] == "TAKE_PROFIT"
    assert x["net_proceeds_usd"] == pytest.approx(2.55 - 0.0255 - 0.02)   # unchanged v1 math
    assert x["exit_obs_ts"] == fresh_ts
    p.close()


def test_price_independent_total_loss_on_stale_obs(tmp_path):
    disc, tid = _single_trade_store(tmp_path, "S3", qty=2.0, price=1.0, alloc=2.0,
                                    security_class="CONFIRMED_HONEYPOT")
    add_obs(tmp_path, disc, "S3", T0 + 30, price=999.0, liq=9e9)  # absurd stale price must be ignored
    st = engine_v3.run_cycle_v3(str(tmp_path / "paper.sqlite"), str(disc),
                                now=T0 + 30 + STALE_16H, pal=None)
    assert st["exits"] == 1 and st["trapped"] == 1
    p = sqlite3.connect(str(tmp_path / "paper.sqlite")); p.row_factory = sqlite3.Row
    x = p.execute("SELECT * FROM paper_exit_v3 WHERE trade_id=?", (tid,)).fetchone()
    assert x["exit_reason"] == "TOTAL_LOSS"
    assert x["exit_price_observed"] is None                       # never a stale price in ledger
    assert x["net_proceeds_usd"] == 0.0 and x["capital_loss_usd"] == pytest.approx(2.0)
    p.close()
