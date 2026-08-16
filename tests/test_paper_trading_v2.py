#!/usr/bin/env python3
"""Wave-8 Paper Lab tests — $20 bankroll, scam defense, trapped capital, multi-signal security.
Deterministic fixtures only (fake PAL envelopes). Live behavior is covered by run evidence."""
import sys, sqlite3
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from discovery import observations as obs, lifecycle
from paper_trading import bankroll, engine_v2, entry_rules, risk, security_multi as sec
from paper_trading.ledger import open_paper

T0 = 1_756_400_000.0

GOPLUS_CLEAN = {"code": 1, "result": {"0xabc": {
    "is_honeypot": "0", "is_blacklisted": "0", "is_mintable": "0", "is_proxy": "0",
    "hidden_owner": "0", "buy_tax": "0", "sell_tax": "0", "transfer_tax": "0"}}}
GOPLUS_TAXED = {"code": 1, "result": {"0xabc": {
    "is_honeypot": "0", "is_blacklisted": "0", "is_mintable": "0", "is_proxy": "0",
    "hidden_owner": "0", "buy_tax": "0", "sell_tax": "0.05", "transfer_tax": "0"}}}
GOPLUS_HP = {"code": 1, "result": {"0xabc": {
    "is_honeypot": "1", "is_blacklisted": "0", "is_mintable": "0", "is_proxy": "0",
    "hidden_owner": "0", "buy_tax": "0", "sell_tax": "0", "transfer_tax": "0"}}}
RUGCHECK_CLEAN = {"mintAuthority": None, "freezeAuthority": None, "lpLockedPct": 100.0, "risks": []}


class FakePAL:
    def __init__(self, payloads: dict, availability="OK"):
        self.payloads, self.availability = payloads, availability

    def call(self, capability, path_key, chain=None, data_type="json", now=None, **fmt):
        if self.availability != "OK":
            return {"availability": self.availability, "payload": None, "endpoint": "fake://",
                    "raw_sha256": None, "attempts": [], "error_state": {"kind": "fake_down"}}
        return {"availability": "OK", "payload": self.payloads.get(capability),
                "endpoint": "fake://multi", "raw_sha256": "f" * 64, "attempts": [],
                "error_state": {"kind": "cache_served"}}


def _disc(tmp_path) -> Path:
    p = tmp_path / "disc.sqlite"
    c = obs.open_store(p); c.commit(); c.close()
    return p


def _token(db, sym, first_seen, chain):
    conn = sqlite3.connect(str(db)); conn.row_factory = sqlite3.Row
    tid = obs.upsert_token(conn, chain, f"addr-{sym}", first_seen, "fx")
    lifecycle.register_discovery(conn, tid, first_seen)
    conn.execute("UPDATE observation_state SET state='OBSERVING' WHERE token_id=?", (tid,))
    conn.commit(); conn.close()
    return tid


def _obs(db, tid, ts, price, liq):
    conn = sqlite3.connect(str(db)); conn.row_factory = sqlite3.Row
    raw = obs.store_raw(conn, "fx", f"fx://{tid}/{ts}", ts, 200, {})
    obs.record_observation(conn, tid, "fx", ts, raw, pair="P",
                           metrics={"price_usd": price, "liquidity_usd": liq, "volume_24h": 9000.0,
                                    "market_cap": 2e6, "txns_5m_buys": 30, "txns_5m_sells": 10})
    conn.commit(); conn.close()


def _paper(tmp_path) -> Path:
    p = tmp_path / "paper.sqlite"
    c = open_paper(p); conn = sqlite3.connect(str(p)); bankroll.ensure_v2_schema(conn)
    conn.commit(); conn.close(); c.close()
    return p


# ------------------------------------------------------------- security normalizer & gates
def test_goplus_normalizer_mapping_and_unknown_law():
    checks = {c["check_key"]: c["value"] for c in sec.checks_from_goplus(GOPLUS_CLEAN)}
    assert checks["honeypot"] == "FALSE" and checks["sell_tax_extreme"] == "FALSE"
    assert checks["mint_authority_active"] == "FALSE"
    assert checks["deployer_prior_rug"] == "UNKNOWN"          # never inferred
    bad = sec.checks_from_goplus({"code": 0})                  # malformed → all UNKNOWN
    assert all(c["value"] == "UNKNOWN" for c in bad)
    taxed = {c["check_key"]: c["value"] for c in sec.checks_from_goplus(
        {"result": {"x": {"is_honeypot": "0", "sell_tax": "0.25"}}})}
    assert taxed["sell_tax_extreme"] == "TRUE"                 # >= locked 20% threshold


def test_coverage_laws():
    assert sec.coverage_sufficient("base", {"sources": {"goplus": "DOWN"},
                                            "resolved_critical": 5})[0] is False
    assert sec.coverage_sufficient("solana", {"sources": {"rugcheck": "OK"},
                                              "resolved_critical": 1})[0] is False
    assert sec.coverage_sufficient("solana", {"sources": {"rugcheck": "OK"},
                                              "resolved_critical": 3})[0] is True


def test_classifier_reasons_and_no_safe():
    cls, why = risk.classify([{"check_key": "honeypot", "value": "TRUE"}], "PASS", {"rugcheck": "OK"})
    assert cls == "CONFIRMED_HONEYPOT" and why
    cls2, _ = risk.classify([], "PASS_WITH_UNKNOWN", {"rugcheck": "DOWN"})
    assert cls2 == "UNKNOWN"                                    # no source ⇒ UNKNOWN (not PASS)
    cls3, _ = risk.classify([{"check_key": "mint_authority_active", "value": "TRUE"}],
                            "SECURITY_VETO", {"rugcheck": "OK"})
    assert cls3 == "CRITICAL_RISK"


def test_trapped_model_math():
    r = risk.recoverable_value(classification="CONFIRMED_HONEYPOT", qty=100, price_obs=1.0,
                               liq_now=50_000, sell_tax_bps=None, slippage_bps=25, fee_bps=100)
    assert r["recoverable"] == 0.0 and r["sellable"] is False
    r2 = risk.recoverable_value(classification="MEDIUM_RISK", qty=100, price_obs=1.0,
                                liq_now=50_000, sell_tax_bps=500, slippage_bps=25, fee_bps=100)
    # 100*0.9975=99.75 gross − tax 5% (4.9875) − fee 1% (0.9975) = 93.765
    assert r2["recoverable"] == pytest.approx(93.76, abs=0.01)
    t = risk.trapped_status(allocated=2.0, recoverable=0.10)    # 5% < 10% meaningful floor
    assert t["state"] == "TRAPPED" and t["capital_loss"] == pytest.approx(1.90)
    t2 = risk.trapped_status(allocated=2.0, recoverable=0.0)
    assert t2["state"] == "TOTAL_LOSS" and t2["capital_loss"] == 2.0
    t3 = risk.trapped_status(allocated=2.0, recoverable=1.50)
    assert t3["state"] is None


# ------------------------------------------------------------- bankroll ledger
def test_bankroll_accounting_and_immutability(tmp_path):
    p = _paper(tmp_path)
    conn = sqlite3.connect(str(p))
    bankroll.init_bankroll(conn, T0)
    assert bankroll.cash_now(conn) == 20.00
    assert bankroll.allocate(conn, T0, "t1", 2.00, "entry") is True
    assert bankroll.allocate(conn, T0, "t2", 21.00, "too much") is False   # over cash refused
    assert bankroll.cash_now(conn) == 18.00
    bankroll.reclaim(conn, T0 + 1, "t1", 1.37, "partial recovery")
    assert bankroll.cash_now(conn) == 19.37
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("UPDATE portfolio_ledger SET amount=999")
    conn.rollback(); conn.close()


# ------------------------------------------------------------- engine v2 end-to-end
def test_v2_entry_bankroll_states_and_snapshot(tmp_path):
    d, p = _disc(tmp_path), _paper(tmp_path)
    tid = _token(d, "EVMOK", T0 - 1800, "base")              # age 0.5h → NEW_LAUNCH
    _obs(d, tid, T0 - 600, 1.0, 50_000)
    pal = FakePAL({"security_evm": GOPLUS_CLEAN})
    st = engine_v2.run_cycle_v2(p, d, now=T0, pal=pal)
    assert st["entries"] == 1 and st["cash"] == 18.00
    conn = sqlite3.connect(str(p)); conn.row_factory = sqlite3.Row
    tr = conn.execute("SELECT * FROM paper_trade_v2").fetchone()
    assert tr["cohort"] == "NEW_LAUNCH" and tr["bankroll_before"] == 20.00
    assert tr["amount_allocated"] == 2.00 and tr["cost_completeness"] == "FULL"
    assert tr["security_class"] in ("LOW_RISK", "MEDIUM_RISK")   # never 'safe'
    assert tr["sell_tax_bps"] == 0.0
    states = [r["state"] for r in conn.execute(
        "SELECT state FROM position_state_event ORDER BY id")]
    assert states[:3] == ["QUALIFIED", "ENTRY", "OPEN"]
    snap = conn.execute("SELECT features_json, security_json FROM decision_snapshot_v2").fetchone()
    assert '"price_usd": 1.0' in snap["features_json"] and "goplus" in snap["security_json"]
    conn.close()


def test_offline_mode_blocks_entries_insufficient_coverage(tmp_path):
    d, p = _disc(tmp_path), _paper(tmp_path)
    tid = _token(d, "OFFL", T0 - 1800, "solana")
    _obs(d, tid, T0 - 600, 1.0, 50_000)
    st = engine_v2.run_cycle_v2(p, d, now=T0, pal=None)      # offline = no evidence
    assert st["entries"] == 0
    conn = sqlite3.connect(str(p)); conn.row_factory = sqlite3.Row
    r = conn.execute("SELECT decision, reject_class, reason FROM decision_snapshot_v2").fetchone()
    assert r["decision"] == "NOT_QUALIFIED" and r["reject_class"] == "security"
    assert "insufficient coverage" in r["reason"] or "unavailable" in r["reason"]
    conn.close()


def test_honeypot_flip_after_entry_total_loss(tmp_path):
    d, p = _disc(tmp_path), _paper(tmp_path)
    tid = _token(d, "HPX", T0 - 1800, "base")
    _obs(d, tid, T0 - 600, 1.0, 50_000)
    engine_v2.run_cycle_v2(p, d, now=T0, pal=FakePAL({"security_evm": GOPLUS_CLEAN}))
    _obs(d, tid, T0 + 300, 1.30, 50_000)                     # price UP but honeypot flips TRUE
    pal2 = FakePAL({"security_evm": GOPLUS_HP})
    st = engine_v2.run_cycle_v2(p, d, now=T0 + 600, pal=pal2)
    assert st["trapped"] == 1 and st["exits"] == 1 and st["cash"] == 18.00
    conn = sqlite3.connect(str(p)); conn.row_factory = sqlite3.Row
    x = conn.execute("SELECT * FROM paper_exit_v2").fetchone()
    assert x["exit_reason"] == "TOTAL_LOSS" and x["recoverable_value_usd"] == 0.0
    assert x["capital_loss_usd"] == pytest.approx(2.00)      # not "price down" — whole allocation lost
    assert x["realized_pnl_usd"] == pytest.approx(-2.00)
    st_now = conn.execute("SELECT state FROM position_state_event ORDER BY id DESC LIMIT 1").fetchone()
    assert st_now["state"] == "TOTAL_LOSS"
    conn.close()


def test_exit_risk_on_liquidity_halving(tmp_path):
    d, p = _disc(tmp_path), _paper(tmp_path)
    tid = _token(d, "LQD", T0 - 1800, "base")
    _obs(d, tid, T0 - 600, 1.0, 50_000)
    engine_v2.run_cycle_v2(p, d, now=T0, pal=FakePAL({"security_evm": GOPLUS_CLEAN}))
    _obs(d, tid, T0 + 300, 1.05, 20_000)                     # liq -60% ⇒ escalation; still sellable
    st = engine_v2.run_cycle_v2(p, d, now=T0 + 600, pal=FakePAL({"security_evm": GOPLUS_CLEAN}))
    conn = sqlite3.connect(str(p)); conn.row_factory = sqlite3.Row
    x = conn.execute("SELECT exit_reason, recoverable_value_usd FROM paper_exit_v2").fetchone()
    assert st["escalations"] >= 1 and x["exit_reason"] == "EXIT_RISK"
    assert x["recoverable_value_usd"] > 0                    # recovered most of the allocation
    conn.close()


def test_tp_exit_with_sell_tax_accounting(tmp_path):
    d, p = _disc(tmp_path), _paper(tmp_path)
    tid = _token(d, "TAX", T0 - 1800, "base")
    _obs(d, tid, T0 - 600, 1.0, 50_000)
    engine_v2.run_cycle_v2(p, d, now=T0, pal=FakePAL({"security_evm": GOPLUS_TAXED}))
    conn = sqlite3.connect(str(p)); conn.row_factory = sqlite3.Row
    tr = conn.execute("SELECT qty, entry_price_exec, sell_tax_bps FROM paper_trade_v2").fetchone()
    assert tr["sell_tax_bps"] == 500.0
    _obs(d, tid, T0 + 300, 1.60, 50_000)                     # crosses TP (exec*1.5)
    st = engine_v2.run_cycle_v2(p, d, now=T0 + 600, pal=FakePAL({"security_evm": GOPLUS_TAXED}))
    x = conn.execute("SELECT * FROM paper_exit_v2").fetchone()
    assert x["exit_reason"] == "TAKE_PROFIT"
    assert x["sell_tax_usd"] == pytest.approx((x["gross_proceeds_usd"] - x["exit_slippage_usd"])
                                              * 0.05, rel=1e-6)
    assert x["realized_pnl_usd"] > 0                         # +60% gross survives 5% tax + costs
    conn.close()


def test_no_cash_means_missed_opportunity_evidence(tmp_path):
    d, p = _disc(tmp_path), _paper(tmp_path)
    conn = sqlite3.connect(str(p))
    bankroll.init_bankroll(conn, T0 - 100)
    bankroll.allocate(conn, T0 - 99, "legacy", 19.60, "drain")   # cash 0.40 < min ticket
    conn.close()
    tid = _token(d, "NOCASH", T0 - 1800, "base")
    _obs(d, tid, T0 - 600, 1.0, 50_000)
    st = engine_v2.run_cycle_v2(p, d, now=T0, pal=FakePAL({"security_evm": GOPLUS_CLEAN}))
    assert st["entries"] == 0 and st["qualified_skipped_no_cash"] == 1
    conn = sqlite3.connect(str(p)); conn.row_factory = sqlite3.Row
    r = conn.execute("SELECT decision, reject_class FROM decision_snapshot_v2").fetchone()
    assert r["decision"] == "QUALIFIED_SKIPPED_NO_CASH"      # recorded, never forced
    conn.close()


def test_evm_gate_requires_clean_honeypot_and_tax_resolution(tmp_path):
    d, p = _disc(tmp_path), _paper(tmp_path)
    tid = _token(d, "EVMUNK", T0 - 1800, "base")
    _obs(d, tid, T0 - 600, 1.0, 50_000)
    # mint+blacklist resolve (coverage gate passes) but honeypot/sell_tax stay UNKNOWN ⇒ EVM gate
    payload = {"result": {"0xabc": {"is_mintable": "0", "is_blacklisted": "0", "buy_tax": "0"}}}
    st = engine_v2.run_cycle_v2(p, d, now=T0, pal=FakePAL({"security_evm": payload}))
    assert st["entries"] == 0
    conn = sqlite3.connect(str(p)); conn.row_factory = sqlite3.Row
    r = conn.execute("SELECT reason FROM decision_snapshot_v2").fetchone()
    assert "UNKNOWN" in r["reason"] and "EVM gate" in r["reason"]   # UNKNOWN≠PASS enforced
    conn.close()
