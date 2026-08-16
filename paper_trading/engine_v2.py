#!/usr/bin/env python3
"""Paper Trading Lab — Wave-8 engine (PT-BANKROLL-v2 + PT-X2-v2). 24h realistic experiment.

Order per cycle: candidates → §C security gate → §D hard no-entry → bankroll allocation →
append-only trade/state/risk events → §E post-entry rug monitoring → exits (incl. TRAPPED).
Never forces a trade. "No trade" is a valid outcome. Track-A stores stay READ-ONLY.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from discovery.pal import PAL
from . import bankroll, cost_model as cm, entry_rules, exit_rules, ledger, risk
from . import security_multi as sec
from .position_monitor import latest_observation, obs_path

MAX_SECURITY_CALLS = 15            # v2 share per cycle (v1 monitor budget is governed by cycle.py)
MAX_CANDIDATES_SCANNED = 400
DEFAULT_STORE = Path(__file__).resolve().parents[1] / "data" / "paper_trading.sqlite"


def _utc(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).isoformat(timespec="seconds")


def _sha(*p) -> str:
    return hashlib.sha256(":".join(str(x) for x in p).encode()).hexdigest()[:24]


def _reject_class(reason: str) -> str:
    r = reason.lower()
    if "honeypot" in r:
        return "honeypot"
    if "veto" in r or "coverage" in r or "security" in r or "critical" in r:
        return "security"
    if "liquidity" in r or "impact" in r:
        return "liquidity"
    if "unknown" in r or "no observation" in r:
        return "insufficient_data"
    return "other"


def _snap_v2(conn, *, token_id, chain, address, symbol, cohort, discovered_ts, decision_ts,
             features, security, decision, reason, cfg) -> str | None:
    sid = _sha("V2", token_id, decision_ts, cfg["version"])
    try:
        conn.execute(
            """INSERT INTO decision_snapshot_v2(snapshot_id,token_id,chain,address,symbol,cohort,
                   discovered_ts,decision_ts,features_json,security_json,rule_version,decision,
                   reject_class,reason,created_utc)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (sid, token_id, chain, address, symbol, cohort, discovered_ts, decision_ts,
             json.dumps(features, sort_keys=True, default=str),
             json.dumps(security, sort_keys=True, default=str),
             cfg["version"], decision, _reject_class(reason), reason, _utc(time.time())))
        conn.commit()
        return sid
    except Exception:
        conn.rollback()
        return None


def _assess(conn, token_id, ts, classification, reasons, evidence: dict) -> None:
    conn.execute(
        "INSERT INTO scam_assessment(token_id,ts,classification,reasons,evidence_json,created_utc)"
        " VALUES (?,?,?,?,?,?)",
        (token_id, ts, classification, json.dumps(reasons, ensure_ascii=False),
         json.dumps(evidence, sort_keys=True, default=str)[:4000], _utc(time.time())))
    conn.commit()


def run_cycle_v2(paper_db, discovery_db, now=None, pal=None,
                 security_budget=MAX_SECURITY_CALLS,
                 entry_cfg=entry_rules.BANKROLL_V2, exit_cfg=exit_rules.EXIT_V2) -> dict:
    now = time.time() if now is None else now
    disc = ledger.open_discovery_ro(discovery_db)
    paper = ledger.open_paper(paper_db)
    bankroll.ensure_v2_schema(paper)
    bankroll.init_bankroll(paper, now)
    ledger.seed_strategy(paper, entry_cfg, exit_cfg["additions"] | {"version": exit_cfg["version"]},
                         {"version": cm.COST_MODEL_VERSION, "fee_bps": cm.FEE_BPS,
                          "taxes": "provider-known only; UNKNOWN never zero-filled"})
    st = {"now": now, "scanned": 0, "snapshot_v2": 0, "security_calls": 0, "defers_budget": 0,
          "rejected": {}, "qualified_skipped_no_cash": 0, "entries": 0, "monitored": 0,
          "escalations": 0, "exits": 0, "trapped": 0, "invalidations": 0}

    def bump(reason):
        st["rejected"][reason] = st["rejected"].get(reason, 0) + 1

    # ---------------------------------------------------------------- candidates → entries
    cands = disc.execute(
        """SELECT t.token_id, t.chain_id, t.address, t.symbol, s.first_seen_ts,
                  (SELECT MIN(p.pair_created_ts) FROM pairs p WHERE p.token_id=t.token_id
                    AND p.pair_created_ts IS NOT NULL) AS pair_created_ts
           FROM tokens t JOIN observation_state s ON s.token_id=t.token_id
           WHERE s.state != 'RESOLVED' ORDER BY s.first_seen_ts DESC LIMIT ?""",
        (MAX_CANDIDATES_SCANNED,)).fetchall()
    for c in cands:
        st["scanned"] += 1
        if paper.execute("SELECT 1 FROM decision_snapshot_v2 WHERE token_id=?",
                         (c["token_id"],)).fetchone():
            continue
        obs = latest_observation(disc, c["token_id"], now)
        base_feat = {"as_of": now, "obs_ref": None}
        if obs is None:
            _snap_v2(paper, token_id=c["token_id"], chain=c["chain_id"], address=c["address"],
                     symbol=c["symbol"], cohort=None, discovered_ts=c["first_seen_ts"],
                     decision_ts=now, features=base_feat, security={"state": "NO_OBSERVATION"},
                     decision="NOT_QUALIFIED", reason="no observation ≤ decision time", cfg=entry_cfg)
            st["snapshot_v2"] += 1
            bump("no observation ≤ decision time (insufficient_data)")
            continue
        age_h = (now - c["first_seen_ts"]) / 3600.0
        cohort = entry_rules.cohort_of(max(0.0, age_h))
        feat = {"as_of": now, "obs_ref": obs["obs_id"], "obs_ts": obs["retrieved_ts"],
                "price_usd": obs["price_usd"], "liquidity_usd": obs["liquidity_usd"],
                "volume_24h": obs["volume_24h"], "market_cap": obs["market_cap"],
                "txns_5m_buys": obs["txns_5m_buys"], "txns_5m_sells": obs["txns_5m_sells"],
                "age_hours": round(age_h, 4), "cohort": cohort,
                "law": "only retrieved_ts <= decision_ts"}
        cheap, cheap_reason = entry_rules.evaluate_entry(
            now=now, first_seen_ts=c["first_seen_ts"], price_usd=obs["price_usd"],
            liquidity_usd=obs["liquidity_usd"], security={"verdict": "PASS"},
            cfg=entry_rules.BASELINE_V1 | {"max_token_age_hours": entry_cfg["max_age_hours"],
                                           "min_liquidity_usd": entry_cfg["min_liquidity_usd"]})
        if cheap != "QUALIFIED_ENTRY":
            _snap_v2(paper, token_id=c["token_id"], chain=c["chain_id"], address=c["address"],
                     symbol=c["symbol"], cohort=cohort, discovered_ts=c["first_seen_ts"],
                     decision_ts=now, features=feat, security={"state": "PRE_REJECT"},
                     decision="NOT_QUALIFIED", reason=cheap_reason, cfg=entry_cfg)
            st["snapshot_v2"] += 1
            bump(cheap_reason)
            continue
        cash = bankroll.cash_now(paper)
        alloc = min(2.00, 0.25 * cash)      # locked rule; evaluated pre-security to size impact est
        est_slip = cm.slippage_bps(alloc, obs["liquidity_usd"])
        if est_slip is None or est_slip > entry_cfg["max_exit_impact_bps"]:
            reason = (f"expected exit impact UNKNOWN/too high "
                      f"({est_slip if est_slip is None else round(est_slip)}bps > "
                      f"{entry_cfg['max_exit_impact_bps']:.0f}) → exit not guaranteed absorbable")
            _snap_v2(paper, token_id=c["token_id"], chain=c["chain_id"], address=c["address"],
                     symbol=c["symbol"], cohort=cohort, discovered_ts=c["first_seen_ts"],
                     decision_ts=now, features=feat, security={"state": "PRE_REJECT"},
                     decision="NOT_QUALIFIED", reason=reason, cfg=entry_cfg)
            st["snapshot_v2"] += 1
            bump("liquidity: exit-impact gate")
            continue
        if st["security_calls"] >= security_budget:
            st["defers_budget"] += 1
            continue
        st["security_calls"] += 1
        if pal is None:
            evaluation = {"verdict": "PASS_WITH_UNKNOWN", "veto_reasons": [], "coverage": 0.0,
                          "resolved_critical": 0, "sources": {"offline": "SKIPPED"},
                          "taxes": {"buy_tax_bps": None, "sell_tax_bps": None,
                                    "transfer_tax_bps": None}, "checks": [],
                          "sell_simulation": "UNKNOWN (offline mode)"}
        else:
            evaluation = sec.evaluate_candidate(pal, c["chain_id"], c["address"], now,
                                                c["pair_created_ts"], obs["liquidity_usd"])
        classification, class_reasons = risk.classify(evaluation["checks"],
                                                      evaluation["verdict"],
                                                      evaluation.get("sources"))
        evaluation["classification"] = classification
        evaluation["classification_reasons"] = class_reasons
        ok_cov, cov_reason = sec.coverage_sufficient(c["chain_id"], evaluation)
        if classification in ("CONFIRMED_HONEYPOT", "CRITICAL_RISK"):
            _assess(paper, c["token_id"], now, classification, class_reasons,
                    {"sources": evaluation.get("sources"), "decision_ts": now})
        if classification in ("CONFIRMED_HONEYPOT", "CRITICAL_RISK") or \
           evaluation["verdict"] == "SECURITY_VETO" or not ok_cov:
            reason = (class_reasons[0] if classification in ("CONFIRMED_HONEYPOT", "CRITICAL_RISK")
                      else ("security veto: " + ",".join(evaluation.get("veto_reasons", [])))
                      if evaluation["verdict"] == "SECURITY_VETO" else cov_reason)
            _snap_v2(paper, token_id=c["token_id"], chain=c["chain_id"], address=c["address"],
                     symbol=c["symbol"], cohort=cohort, discovered_ts=c["first_seen_ts"],
                     decision_ts=now, features=feat, security=evaluation,
                     decision="NOT_QUALIFIED", reason=reason, cfg=entry_cfg)
            st["snapshot_v2"] += 1
            bump(f"{classification if classification != 'UNKNOWN' else 'security'}: {reason[:60]}")
            continue
        if c["chain_id"] != "solana":
            want = {("honeypot", "FALSE"), ("sell_tax_extreme", "FALSE")}
            have = {(ch["check_key"], ch["value"]) for ch in evaluation["checks"]}
            if not want <= have:
                reason = "EVM gate: honeypot/sell-tax not both resolved clean (UNKNOWN≠PASS)"
                _snap_v2(paper, token_id=c["token_id"], chain=c["chain_id"], address=c["address"],
                         symbol=c["symbol"], cohort=cohort, discovered_ts=c["first_seen_ts"],
                         decision_ts=now, features=feat, security=evaluation,
                         decision="NOT_QUALIFIED", reason=reason, cfg=entry_cfg)
                st["snapshot_v2"] += 1
                bump("security: " + reason[:50])
                continue
        # ---- qualified → allocation discipline (never force)
        if alloc < entry_cfg["min_ticket_usd"]:
            _snap_v2(paper, token_id=c["token_id"], chain=c["chain_id"], address=c["address"],
                     symbol=c["symbol"], cohort=cohort, discovered_ts=c["first_seen_ts"],
                     decision_ts=now, features=feat, security=evaluation,
                     decision="QUALIFIED_SKIPPED_NO_CASH",
                     reason=f"cash {cash:.2f} below min ticket — missed-opportunity evidence",
                     cfg=entry_cfg)
            st["qualified_skipped_no_cash"] += 1
            continue
        exe = cm.buy(alloc, obs["price_usd"], obs["liquidity_usd"])
        if exe is None:
            ledger.invalidate(paper, "TRADE", c["token_id"], "v2 entry execution unmodelable — §15")
            st["invalidations"] += 1
            continue
        sid = _snap_v2(paper, token_id=c["token_id"], chain=c["chain_id"], address=c["address"],
                       symbol=c["symbol"], cohort=cohort, discovered_ts=c["first_seen_ts"],
                       decision_ts=now, features=feat, security=evaluation,
                       decision="QUALIFIED_ENTRY", reason="v2 gates passed", cfg=entry_cfg)
        if sid is None:
            continue
        tid = _sha("TRADE2", c["token_id"], now, entry_cfg["version"])
        taxes = evaluation["taxes"]
        cost_complete = "PARTIAL(taxes UNKNOWN)" if taxes["sell_tax_bps"] is None else "FULL"
        paper.execute(
            """INSERT INTO paper_trade_v2(trade_id,strategy_version,snapshot_id,token_id,chain,
                   address,symbol,cohort,discovered_ts,entry_decision_ts,entry_ts,
                   entry_price_observed,bankroll_before,amount_allocated,qty,fee_entry_usd,
                   entry_slippage_bps,entry_price_exec,liq_at_entry,expected_exit_liquidity_usd,
                   buy_tax_bps,sell_tax_bps,transfer_tax_bps,cost_completeness,security_class,
                   execution_class,opportunity_class,exit_rule_version,monitoring_horizon_ts,
                   created_utc)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (tid, entry_cfg["version"], sid, c["token_id"], c["chain_id"], c["address"], c["symbol"],
             cohort, c["first_seen_ts"], now, obs["retrieved_ts"], obs["price_usd"],
             cash, alloc, exe["qty"], exe["fee_entry_usd"], exe["slippage_bps"], exe["exec_price"],
             obs["liquidity_usd"], obs["liquidity_usd"],
             taxes["buy_tax_bps"], taxes["sell_tax_bps"], taxes["transfer_tax_bps"],
             cost_complete, classification,
             "EXECUTABLE_OK" if est_slip <= 500 else "EXECUTABLE_THIN",
             entry_rules.opportunity_class(obs), exit_cfg["version"],
             now + exit_cfg["max_hold_hours"] * 3600, _utc(time.time())))
        bankroll.allocate(paper, now, tid, alloc,
                          f"allocated to {c['symbol']} ({classification}, impact {est_slip:.0f}bps)")
        bankroll.state_event(paper, tid, now, "QUALIFIED", "v2 gates passed")
        bankroll.state_event(paper, tid, now, "ENTRY", f"exec {exe['exec_price']:.8g}")
        bankroll.state_event(paper, tid, now, "OPEN", f"cohort={cohort}")
        ledger.monitor(paper, tid, now, obs["retrieved_ts"], obs["price_usd"],
                       obs["liquidity_usd"], obs["volume_24h"], "ENTRY", entry_cfg["version"])
        paper.commit()
        st["entries"] += 1

    # ---------------------------------------------------------------- monitoring / rug defense
    open_rows = paper.execute(
        """SELECT * FROM paper_trade_v2 t WHERE t.trade_id NOT IN (SELECT trade_id FROM paper_exit_v2)
           AND t.trade_id NOT IN (SELECT ref_id FROM invalidation WHERE scope='TRADE')""").fetchall()
    for tr in open_rows:
        st["monitored"] += 1
        obs = latest_observation(disc, tr["token_id"], now)
        if obs is None:
            ledger.monitor(paper, tr["trade_id"], now, None, None, None, None, "NO_DATA",
                           "no observation ≤ now")
            bankroll.state_event(paper, tr["trade_id"], now, "NO_DATA", "no observation ≤ now")
            continue
        ledger.monitor(paper, tr["trade_id"], now, obs["retrieved_ts"], obs["price_usd"],
                       obs["liquidity_usd"], obs["volume_24h"], "OBSERVED", "")
        if obs["price_usd"] is None:
            bankroll.state_event(paper, tr["trade_id"], now, "NO_DATA",
                                 "observation present but price NULL — UNKNOWN, not guessed")
            continue
        consec = 0
        for ev in paper.execute(
                """SELECT liquidity_usd FROM monitor_event WHERE trade_id=? AND event='OBSERVED'
                   ORDER BY obs_ts DESC LIMIT ?""",
                (tr["trade_id"], exit_cfg["liq_collapse_consecutive"])).fetchall():
            if ev["liquidity_usd"] is not None and ev["liquidity_usd"] < exit_cfg["liq_collapse_floor_usd"]:
                consec += 1
            else:
                break
        recheck_cls = None
        if pal is not None and st["security_calls"] < security_budget:
            st["security_calls"] += 1
            re_ev = sec.evaluate_candidate(pal, tr["chain"], tr["address"], now, None, None)
            recheck_cls, rs = risk.classify(re_ev["checks"], re_ev["verdict"],
                                            re_ev.get("sources"))
            if recheck_cls != tr["security_class"]:
                _assess(paper, tr["token_id"], now, recheck_cls, rs,
                        {"recheck": True, "sources": re_ev.get("sources")})
            recheck_sec = re_ev
        else:
            recheck_sec = None
        esc = risk.risk_escalation(entry_liq=tr["liq_at_entry"], obs_liq=obs["liquidity_usd"],
                                   entry_price=tr["entry_price_observed"],
                                   obs_price=obs["price_usd"],
                                   recheck_classification=recheck_cls, prior_escalated=False)
        if esc:
            st["escalations"] += 1
            bankroll.state_event(paper, tr["trade_id"], now, "RISK_ESCALATION", " | ".join(esc))
        # ---- exit determination (executability-first)
        slip_now = cm.slippage_bps(tr["qty"] * (obs["price_usd"] or 0), obs["liquidity_usd"])
        if obs["liquidity_usd"] is None and recheck_cls not in ("CONFIRMED_HONEYPOT",):
            bankroll.state_event(paper, tr["trade_id"], now, "NO_DATA",
                                 "liquidity NULL at monitoring — UNKNOWN; TRAP not guessed")
            continue
        rec = risk.recoverable_value(classification=recheck_cls or tr["security_class"],
                                     qty=tr["qty"], price_obs=obs["price_usd"],
                                     liq_now=obs["liquidity_usd"],
                                     sell_tax_bps=tr["sell_tax_bps"], slippage_bps=slip_now,
                                     fee_bps=cm.FEE_BPS)
        trap = risk.trapped_status(allocated=tr["amount_allocated"],
                                   recoverable=rec["recoverable"])
        hit = exit_rules.check_exits(
            entry_exec=tr["entry_price_exec"], entry_ts=tr["entry_ts"], now=now,
            obs_price=obs["price_usd"], obs_liq=obs["liquidity_usd"],
            obs_ts=obs["retrieved_ts"], consec_liq_breaches=consec,
            security_recheck={"verdict": "SECURITY_VETO"} if recheck_cls in
            ("CONFIRMED_HONEYPOT", "CRITICAL_RISK", "CONFIRMED_RUG") else None,
            cfg=exit_rules.EXIT_V1)   # base thresholds identical; X2 adds risk overlay
        reason = None
        if trap["state"] in ("TRAPPED", "TOTAL_LOSS") and rec["why"] != "exit meaningful":
            reason = trap["state"]
        elif esc and rec["sellable"]:
            reason = "EXIT_RISK"
        elif hit is not None:
            reason = hit["reason"]
        if reason is None:
            if obs["price_usd"] is not None:
                side = "PROFITABLE" if obs["price_usd"] >= tr["entry_price_exec"] else "LOSING"
                bankroll.state_event(paper, tr["trade_id"], now, side, "mark vs entry exec")
            continue
        if reason.startswith("INVALID"):
            ledger.invalidate(paper, "TRADE", tr["trade_id"],
                              hit.get("detail") if hit else reason)
            st["invalidations"] += 1
            continue
        # ---- settle (bankroll truth: RECLAIM recoverable, LOSS_RECOGNIZED for the rest)
        recoverable = trap["recoverable"] if trap["state"] in ("TRAPPED", "TOTAL_LOSS") \
            else rec["recoverable"] if rec["recoverable"] is not None else 0.0
        gross = tr["qty"] * obs["price_usd"] if obs["price_usd"] else 0.0
        slip = (slip_now or 0) / 1e4 * gross
        tax = (gross - slip) * tr["sell_tax_bps"] / 1e4 if tr["sell_tax_bps"] else None
        fee_exit = (gross - slip) * cm.FEE_BPS / 1e4
        total_cost = tr["fee_entry_usd"] + slip + (tax or 0.0) + fee_exit
        realized = recoverable - tr["amount_allocated"]
        cap_loss = max(0.0, tr["amount_allocated"] - recoverable) \
            if trap["state"] in ("TRAPPED", "TOTAL_LOSS") else max(0.0, -realized)
        path = obs_path(disc, tr["token_id"], tr["entry_ts"], obs["retrieved_ts"])
        prices = [p["price_usd"] for p in path if p["price_usd"] and p["price_usd"] > 0]
        mfe = (max(prices) / tr["entry_price_observed"] - 1) if prices else None
        mae = (min(prices) / tr["entry_price_observed"] - 1) if prices else None
        paper.execute(
            """INSERT INTO paper_exit_v2(trade_id,exit_ts,exit_reason,exit_obs_ts,
                   exit_price_observed,qty_sold,gross_proceeds_usd,exit_fee_usd,
                   exit_slippage_usd,sell_tax_usd,recoverable_value_usd,total_trade_cost_usd,
                   realized_pnl_usd,realized_pnl_pct,capital_loss_usd,mfe_pct,mae_pct,hold_hours,
                   closed_utc)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (tr["trade_id"], now, reason, obs["retrieved_ts"], obs["price_usd"], tr["qty"],
             gross, fee_exit, slip, tax, recoverable, total_cost, realized,
             (realized / tr["amount_allocated"] * 100) if tr["amount_allocated"] else None,
             cap_loss, mfe, mae, round((now - tr["entry_ts"]) / 3600.0, 3), _utc(time.time())))
        bankroll.reclaim(paper, now, tr["trade_id"], recoverable, f"exit {reason} @ {obs['price_usd']:.6g}")
        if cap_loss > 0:
            bankroll.recognize_loss(paper, now, tr["trade_id"],
                                    f"{reason}: capital_loss {cap_loss:.4f} of {tr['amount_allocated']:.2f}")
        final = {"TAKE_PROFIT": "EXITED_PROFIT", "STOP_LOSS": "EXITED_LOSS",
                 "TIME_EXIT": "EXITED_PROFIT" if realized > 0 else "EXITED_LOSS",
                 "EXIT_RISK": "EXITED_PROFIT" if realized > 0 else "EXITED_LOSS",
                 "LIQUIDITY_COLLAPSE": "EXITED_LOSS",
                 "TRAPPED": "TRAPPED", "TOTAL_LOSS": "TOTAL_LOSS",
                 "SECURITY_EVENT": "EXITED_LOSS"}.get(reason, "EXITED_LOSS")
        bankroll.state_event(paper, tr["trade_id"], now, final,
                             f"realized {realized:+.4f} USD; recoverable {recoverable:.4f}")
        paper.commit()
        st["exits"] += 1
        if trap["state"] in ("TRAPPED", "TOTAL_LOSS"):
            st["trapped"] += 1

    st["cash"] = bankroll.cash_now(paper)
    disc.close(); paper.close()
    return st


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default=str(DEFAULT_STORE))
    ap.add_argument("--discovery", default=str(Path(__file__).resolve().parents[1] / "data" / "e01_discovery.sqlite"))
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--budget", type=int, default=MAX_SECURITY_CALLS)
    ap.add_argument("--report", default=None)
    args = ap.parse_args(argv)
    pal = None if args.offline else PAL()
    st = run_cycle_v2(args.store, args.discovery, pal=pal, security_budget=args.budget)
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(st, indent=1, default=str))
    print(json.dumps(st, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
