#!/usr/bin/env python3
"""Paper Trading Lab — Wave-8 CONTINUATION engine (PT-BANKROLL-v2 entries + PT-X3-v2 management; PT-X3-v1 logic frozen as decide_v1).

Autonomous position management per owner directive 2026-08-12T08:1xZ (register R-26):
  HOLD / PARTIAL_EXIT / RISK_EXIT / TRAPPED / TOTAL_LOSS decided on CURRENT evidence each cycle,
  never on the timing of user messages. Entries are unchanged (PT-BANKROLL-v2 card untouched).
Order per cycle: entries (v2 gates) → per-open-position realizable snapshot → §5 categorical
decision evidence → v3 exits (partial-capable) → post-trade lesson at close → §11 stats snapshot.
Track-A discovery store is opened READ-ONLY; v1 legacy trades are NOT touched here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from discovery.pal import PAL
from . import bankroll, cost_model as cm, entry_rules, exit_rules, ledger, lessons, realizable as rz
from . import decision_v3 as dv3
from . import engine_v2 as ev2
from . import risk, security_multi as sec
from .position_monitor import latest_observation, obs_path

MAX_SECURITY_CALLS = 15
MAX_CANDIDATES_SCANNED = 400
DEFAULT_STORE = Path(__file__).resolve().parents[1] / "data" / "paper_trading.sqlite"
SCHEMA_V3 = Path(__file__).resolve().parent / "schema_v3.sql"
RULE_VERSION = dv3.EXIT_V32["version"]          # PT-X3-v2 (R-C3 closure; v1 logic preserved)


def _utc(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).isoformat(timespec="seconds")


def _sha(*p) -> str:
    return hashlib.sha256(":".join(str(x) for x in p).encode()).hexdigest()[:24]


def ensure_v3_schema(conn) -> None:
    conn.executescript(SCHEMA_V3.read_text())


# ------------------------------------------------------------------ position bookkeeping
def exits_of(paper, trade_id: str) -> list:
    return paper.execute("SELECT * FROM paper_exit_v3 WHERE trade_id=? ORDER BY exit_seq",
                         (trade_id,)).fetchall()


def remaining_qty(paper, tr) -> float:
    sold = sum(x["qty_sold"] for x in exits_of(paper, tr["trade_id"]))
    return tr["qty"] - sold


def remaining_alloc(paper, tr) -> float:
    retired = sum(x["allocated_retired_usd"] for x in exits_of(paper, tr["trade_id"]))
    return tr["amount_allocated"] - retired


def is_closed(paper, trade_id: str) -> bool:
    return paper.execute("SELECT 1 FROM paper_exit_v3 WHERE trade_id=? AND exit_kind='FULL'",
                         (trade_id,)).fetchone() is not None


def record_realizable(paper, trade_id, now, obs_ts, qty_rem, a: dict) -> None:
    paper.execute(
        """INSERT INTO realizable_snapshot(trade_id,ts,obs_ts,qty_remaining,price_observed,
               liquidity_usd,displayed_value_usd,max_executable_notional_usd,
               requested_exit_notional_usd,executable_exit_notional_usd,exit_slippage_bps,
               exit_fee_usd,sell_tax_usd,gas_cost_usd,realizable_value_usd,
               unexited_displayed_usd,route_status,model_version,detail,created_utc)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (trade_id, now, obs_ts, qty_rem, a["price_observed"], a["liquidity_usd"],
         a["displayed_value_usd"], a["max_executable_notional_usd"],
         a["requested_exit_notional_usd"], a["executable_exit_notional_usd"],
         a["exit_slippage_bps"], a["exit_fee_usd"], a["sell_tax_usd"], a["gas_cost_usd"],
         a["realizable_value_usd"], a["unexited_displayed_usd"], a["route_status"],
         a["model_version"], a.get("why", ""), _utc(time.time())))
    paper.commit()


def record_decision(paper, trade_id, now, action, reason, rule_version, factors: dict) -> None:
    paper.execute(
        """INSERT INTO position_decision_event(trade_id,ts,action,reason,rule_version,
               momentum_class,continuation_prob,reversal_prob,security_risk,exitability,
               realizable_value_usd,displayed_value_usd,execution_cost_usd,liquidity_risk,
               news_risk,scam_risk,opportunity_cost,evidence_json,created_utc)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (trade_id, now, action, reason, rule_version,
         factors.get("momentum_class"), "NOT_ESTIMABLE", "NOT_ESTIMABLE",
         factors.get("security_risk"), factors.get("exitability"),
         factors.get("realizable_value_usd"), factors.get("displayed_value_usd"),
         factors.get("execution_cost_usd"), factors.get("liquidity_risk"),
         "UNAVAILABLE_NO_FEED", factors.get("scam_risk"),
         factors.get("opportunity_cost"), json.dumps(factors.get("evidence", {}), default=str)[:4000],
         _utc(time.time())))
    paper.commit()


# ------------------------------------------------------------------ settlement
def _settle(paper, tr, now, obs_ts, obs_price, decision, st) -> bool:
    """Book one exit chunk (PARTIAL or FULL) from a decision. Bankroll truth moves here.
    PT-X3-v2 hard guard: stale observation ⇒ refuse settlement unless the close is
    price-INDEPENDENT (confirmed honeypot / confirmed unexitsable ⇒ recoverable 0, no price)."""
    tid = tr["trade_id"]
    a = decision["assess"]
    qty_rem = remaining_qty(paper, tr)
    alloc_rem = remaining_alloc(paper, tr)
    if dv3.stale(now, obs_ts) and not decision.get("price_independent"):
        return False                                # belt:suspenders — decide() gates first
    if decision.get("price_independent"):
        if qty_rem <= 0:
            return False
        qty_sold = qty_rem                          # write-off; no market pricing consulted
        notional = slip = gross = fee = 0.0
        tax = None
        gas = 0.0
        net = 0.0
        price_used = None                           # NULL — never a stale price in the ledger
    else:
        if qty_rem <= 0 or obs_price is None or obs_price <= 0:
            return False
        chunk = decision["kind"]
        notional = (qty_rem * obs_price) if chunk == "FULL" else a["executable_exit_notional_usd"]
        if notional is None or notional <= 0:
            return False
        qty_sold = min(qty_rem, notional / obs_price)
        notional = qty_sold * obs_price                       # re-derive after clamp (exactness)
        slip = cm.slippage_bps(notional, a["liquidity_usd"])
        if slip is None:
            return False
        gross = notional * (1 - slip / 1e4)
        fee = gross * cm.FEE_BPS / 1e4
        tax_bps = a["sell_tax_bps"]
        tax = gross * tax_bps / 1e4 if tax_bps else None
        gas = a["gas_cost_usd"]
        net = max(0.0, gross - fee - (tax or 0.0) - gas)
        price_used = obs_price
    alloc_retired = alloc_rem * (qty_sold / qty_rem)      # proportional basis (§7 accounting)
    realized = net - alloc_retired
    kind = "FULL" if qty_rem - qty_sold <= 1e-12 or decision["kind"] == "FULL" else "PARTIAL"
    seq = len(exits_of(paper, tid)) + 1
    hold_h = round((now - tr["entry_ts"]) / 3600.0, 3)
    cap_loss = max(0.0, alloc_retired - net) if kind == "FULL" else max(0.0, -realized)
    paper.execute(
        """INSERT INTO paper_exit_v3(exit_id,trade_id,exit_seq,exit_kind,exit_ts,exit_reason,
               rule_version,exit_obs_ts,exit_price_observed,qty_sold,qty_remaining_after,
               requested_notional_usd,executable_notional_usd,gross_proceeds_usd,exit_fee_usd,
               exit_slippage_usd,sell_tax_usd,gas_cost_usd,net_proceeds_usd,
               allocated_retired_usd,realized_pnl_usd,capital_loss_usd,displayed_value_pre_usd,
               realizable_value_pre_usd,hold_hours,closed_utc)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (_sha("X3", tid, seq, now, decision["reason"]), tid, seq, kind, now,
         decision["reason"], RULE_VERSION, obs_ts, price_used, qty_sold,
         max(0.0, qty_rem - qty_sold), a["requested_exit_notional_usd"] or notional,
         notional, gross, fee, 0.0 if decision.get("price_independent") else notional * slip / 1e4,
         tax, gas, net, alloc_retired,
         realized, cap_loss, a["displayed_value_usd"], a["realizable_value_usd"],
         hold_h, _utc(time.time())))
    bankroll.reclaim(paper, now, tid, net,
                     f"{kind} exit {decision['reason']} (chunk {seq})"
                     + (f" @ {price_used:.6g}" if price_used else " [price-ind: no price used]"))
    if kind == "FULL" and cap_loss > 1e-12:
        bankroll.recognize_loss(paper, now, tid,
                                f"{decision['reason']}: capital_loss {cap_loss:.4f}")
    return True


_FINAL = {"TAKE_PROFIT": "EXITED_PROFIT", "STOP_LOSS": "EXITED_LOSS", "TIME_EXIT": None,
          "EXIT_RISK": None, "LIQUIDITY_COLLAPSE": "EXITED_LOSS", "SECURITY_EVENT": None,
          "DIVERGENCE_PROFIT_LOCK": None, "DECAY_PROFIT_LOCK": None,
          "TRAPPED": "TRAPPED", "TOTAL_LOSS": "TOTAL_LOSS"}


def _final_state(paper, tr, reason, now) -> str:
    fixed = _FINAL.get(reason)
    if fixed:
        return fixed
    rows = exits_of(paper, tr["trade_id"])
    proceeds = sum(x["net_proceeds_usd"] or 0.0 for x in rows)
    return "EXITED_PROFIT" if proceeds > tr["amount_allocated"] else "EXITED_LOSS"


# ------------------------------------------------------------------ one monitoring pass
def _monitor_position(paper, disc, pal, tr, now, st, budget) -> None:
    tid = tr["trade_id"]
    st["monitored"] += 1
    obs = latest_observation(disc, tr["token_id"], now)
    if obs is None:
        ledger.monitor(paper, tid, now, None, None, None, None, "NO_DATA", "no observation ≤ now")
        bankroll.state_event(paper, tid, now, "NO_DATA", "no observation ≤ now")
        record_decision(paper, tid, now, "NO_DATA", "no observation ≤ now", RULE_VERSION,
                        {"security_risk": tr["security_class"], "exitability": "UNPRICED",
                         "opportunity_cost": st["cash_state"]})
        return
    ledger.monitor(paper, tid, now, obs["retrieved_ts"], obs["price_usd"], obs["liquidity_usd"],
                   obs["volume_24h"], "OBSERVED", "")
    qty_rem = remaining_qty(paper, tr)
    alloc_rem = remaining_alloc(paper, tr)

    # monitor peak / momentum (observed evidence only)
    mons = paper.execute(
        """SELECT obs_ts, price_usd FROM monitor_event WHERE trade_id=? AND event='OBSERVED'
           AND price_usd IS NOT NULL ORDER BY obs_ts""", (tid,)).fetchall()
    prices = [m["price_usd"] for m in mons]
    peak = max(prices) if prices else None
    prev = prices[-2] if len(prices) >= 2 else None
    momentum = dv3.momentum_class(prev, obs["price_usd"])

    # liquidity-collapse consecutive counter (X1/X2 law)
    consec = 0
    for ev in paper.execute(
            """SELECT liquidity_usd FROM monitor_event WHERE trade_id=? AND event='OBSERVED'
               ORDER BY obs_ts DESC LIMIT ?""",
            (tid, exit_rules.EXIT_V1["liq_collapse_consecutive"])).fetchall():
        if ev["liquidity_usd"] is not None and ev["liquidity_usd"] < exit_rules.EXIT_V1["liq_collapse_floor_usd"]:
            consec += 1
        else:
            break

    # security recheck (budgeted) — live rug defense
    recheck_cls, recheck_tax = None, None
    if pal is not None and st["security_calls"] < budget[0]:
        st["security_calls"] += 1
        re_ev = sec.evaluate_candidate(pal, tr["chain"], tr["address"], now, None, None)
        recheck_cls, rs = risk.classify(re_ev["checks"], re_ev["verdict"], re_ev.get("sources"))
        recheck_tax = (re_ev.get("taxes") or {}).get("sell_tax_bps")
        if recheck_cls != tr["security_class"]:
            ev2._assess(paper, tr["token_id"], now, recheck_cls, rs,
                        {"recheck": True, "trade_id": tid, "sources": re_ev.get("sources")})
    cur_cls = recheck_cls or tr["security_class"]
    sell_tax = recheck_tax if recheck_tax is not None else tr["sell_tax_bps"]

    # PT-X3-v2: stale observation ⇒ market-derived escalation inputs suppressed (liq/price from
    # a stale obs may never ground danger/exit claims); provider-fresh classifications still act.
    fresh_obs = not dv3.stale(now, obs["retrieved_ts"])
    esc = risk.risk_escalation(entry_liq=tr["liq_at_entry"],
                               obs_liq=obs["liquidity_usd"] if fresh_obs else None,
                               entry_price=tr["entry_price_exec"],
                               obs_price=obs["price_usd"] if fresh_obs else None,
                               recheck_classification=recheck_cls, prior_escalated=False)
    if esc:
        st["escalations"] += 1
        bankroll.state_event(paper, tid, now, "RISK_ESCALATION", " | ".join(esc))

    base_hit = exit_rules.check_exits(
        entry_exec=tr["entry_price_exec"], entry_ts=tr["entry_ts"], now=now,
        obs_price=obs["price_usd"], obs_liq=obs["liquidity_usd"], obs_ts=obs["retrieved_ts"],
        consec_liq_breaches=consec, security_recheck=None, cfg=exit_rules.EXIT_V1)

    decision = dv3.decide(now=now, allocated=alloc_rem, qty_remaining=qty_rem,
                          entry_price_exec=tr["entry_price_exec"], entry_ts=tr["entry_ts"],
                          obs_price=obs["price_usd"], obs_liq=obs["liquidity_usd"],
                          obs_ts=obs["retrieved_ts"], consec_liq_breaches=consec,
                          sec_veto_now=recheck_cls in ("CONFIRMED_HONEYPOT", "CRITICAL_RISK",
                                                       "CONFIRMED_RUG", "CONFIRMED_UNEXITSABLE"),
                          escalations=esc, sell_tax_bps=sell_tax, chain=tr["chain"],
                          classification=cur_cls, monitor_peak_price=peak,
                          monitor_obs_count=len(prices), base_hit=base_hit)
    a = decision["assess"]
    record_realizable(paper, tid, now, obs["retrieved_ts"], qty_rem, a)
    st["realizable_rows"] += 1
    st["decisions"][decision["action"]] = st["decisions"].get(decision["action"], 0) + 1
    cost = (a["exit_fee_usd"] or 0) + (a["exit_slippage_usd"] or 0) + (a["sell_tax_usd"] or 0) \
        + a["gas_cost_usd"]
    record_decision(paper, tid, now, decision["action"], decision["reason"],
                    RULE_VERSION,
                    {"momentum_class": momentum, "security_risk": cur_cls,
                     "exitability": a["route_status"], "realizable_value_usd": a["realizable_value_usd"],
                     "displayed_value_usd": a["displayed_value_usd"], "execution_cost_usd": round(cost, 6),
                     "liquidity_risk": dv3.liquidity_risk(obs["liquidity_usd"]),
                     "scam_risk": cur_cls, "opportunity_cost": st["cash_state"],
                     "evidence": {"why": decision["why"], "escalations": esc,
                                  "obs_ref": obs["obs_id"], "obs_ts": obs["retrieved_ts"]}})

    if decision["action"] in ("HOLD", "NO_DATA"):
        if decision["action"] == "NO_DATA":
            bankroll.state_event(paper, tid, now, "NO_DATA", decision["why"][:180])
        elif obs["price_usd"] is not None:
            side = "PROFITABLE" if obs["price_usd"] >= tr["entry_price_exec"] else "LOSING"
            bankroll.state_event(paper, tid, now, side,
                                 f"realizable {a['realizable_value_usd']} vs displayed "
                                 f"{a['displayed_value_usd']}")
        return
    if decision["action"] == "INVALID":
        ledger.invalidate(paper, "TRADE", tid, decision["why"])
        st["invalidations"] += 1
        return
    if not _settle(paper, tr, now, obs["retrieved_ts"], obs["price_usd"], decision, st):
        bankroll.state_event(paper, tid, now, "NO_DATA", "settlement unmodelable — position kept open")
        return
    if decision["kind"] == "PARTIAL":
        st["partials"] += 1
        bankroll.state_event(paper, tid, now, "PARTIAL_EXIT",
                             f"{decision['reason']}: chunk sold, remainder monitored")
    else:
        st["exits"] += 1
        final = _final_state(paper, tr, decision["reason"], now)
        bankroll.state_event(paper, tid, now, final, decision["why"][:180])
        if final in ("TRAPPED", "TOTAL_LOSS"):
            st["trapped"] += 1
        if lessons.record_lesson(paper, disc, tid):
            st["lessons_new"] += 1
    paper.commit()


# ------------------------------------------------------------------ the cycle
def run_cycle_v3(paper_db, discovery_db, now=None, pal=None,
                 security_budget=MAX_SECURITY_CALLS) -> dict:
    """Entries: PT-BANKROLL-v2 (unchanged). Management: PT-X3-v2 (freshness-gated)."""
    now = time.time() if now is None else now
    disc = ledger.open_discovery_ro(discovery_db)
    paper = ledger.open_paper(paper_db)
    bankroll.ensure_v2_schema(paper)
    ensure_v3_schema(paper)
    bankroll.init_bankroll(paper, now)
    ledger.seed_strategy(paper, entry_rules.BANKROLL_V2,
                         dv3.EXIT_V32["additions"] | {"version": dv3.EXIT_V32["version"],
                                                      "created": dv3.EXIT_V32["created"]},
                         {"version": cm.COST_MODEL_VERSION, "fee_bps": cm.FEE_BPS,
                          "realizable_model": rz.MODEL_VERSION})
    st = {"now": now, "engine": "v3", "scanned": 0, "snapshot_v2": 0, "security_calls": 0,
          "defers_budget": 0, "rejected": {}, "qualified_skipped_no_cash": 0, "entries": 0,
          "monitored": 0, "escalations": 0, "exits": 0, "partials": 0, "trapped": 0,
          "invalidations": 0, "realizable_rows": 0, "lessons_new": 0, "decisions": {},
          "cash_state": "CASH_AVAILABLE"}

    def bump(reason):
        st["rejected"][reason] = st["rejected"].get(reason, 0) + 1

    # ------------------------------------------------ entries (PT-BANKROLL-v2 card, verbatim gates)
    cands = disc.execute(
        """SELECT t.token_id, t.chain_id, t.address, t.symbol, s.first_seen_ts,
                  (SELECT MIN(p.pair_created_ts) FROM pairs p WHERE p.token_id=t.token_id
                    AND p.pair_created_ts IS NOT NULL) AS pair_created_ts
           FROM tokens t JOIN observation_state s ON s.token_id=t.token_id
           WHERE s.state != 'RESOLVED' ORDER BY s.first_seen_ts DESC LIMIT ?""",
        (MAX_CANDIDATES_SCANNED,)).fetchall()
    cfg = entry_rules.BANKROLL_V2
    for c in cands:
        st["scanned"] += 1
        if paper.execute("SELECT 1 FROM decision_snapshot_v2 WHERE token_id=?",
                         (c["token_id"],)).fetchone():
            continue
        obs = latest_observation(disc, c["token_id"], now)
        if obs is None:
            ev2._snap_v2(paper, token_id=c["token_id"], chain=c["chain_id"], address=c["address"],
                         symbol=c["symbol"], cohort=None, discovered_ts=c["first_seen_ts"],
                         decision_ts=now, features={"as_of": now, "obs_ref": None},
                         security={"state": "NO_OBSERVATION"}, decision="NOT_QUALIFIED",
                         reason="no observation ≤ decision time", cfg=cfg)
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
            cfg=entry_rules.BASELINE_V1 | {"max_token_age_hours": cfg["max_age_hours"],
                                           "min_liquidity_usd": cfg["min_liquidity_usd"]})
        if cheap != "QUALIFIED_ENTRY":
            ev2._snap_v2(paper, token_id=c["token_id"], chain=c["chain_id"], address=c["address"],
                         symbol=c["symbol"], cohort=cohort, discovered_ts=c["first_seen_ts"],
                         decision_ts=now, features=feat, security={"state": "PRE_REJECT"},
                         decision="NOT_QUALIFIED", reason=cheap_reason, cfg=cfg)
            st["snapshot_v2"] += 1
            bump(cheap_reason)
            continue
        cash = bankroll.cash_now(paper)
        alloc = min(2.00, 0.25 * cash)
        est_slip = cm.slippage_bps(alloc, obs["liquidity_usd"])
        if est_slip is None or est_slip > cfg["max_exit_impact_bps"]:
            reason = (f"expected exit impact UNKNOWN/too high "
                      f"({est_slip if est_slip is None else round(est_slip)}bps > "
                      f"{cfg['max_exit_impact_bps']:.0f}) → exit not guaranteed absorbable")
            ev2._snap_v2(paper, token_id=c["token_id"], chain=c["chain_id"], address=c["address"],
                         symbol=c["symbol"], cohort=cohort, discovered_ts=c["first_seen_ts"],
                         decision_ts=now, features=feat, security={"state": "PRE_REJECT"},
                         decision="NOT_QUALIFIED", reason=reason, cfg=cfg)
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
        classification, class_reasons = risk.classify(evaluation["checks"], evaluation["verdict"],
                                                      evaluation.get("sources"))
        evaluation["classification"] = classification
        evaluation["classification_reasons"] = class_reasons
        ok_cov, cov_reason = sec.coverage_sufficient(c["chain_id"], evaluation)
        if classification in ("CONFIRMED_HONEYPOT", "CRITICAL_RISK"):
            ev2._assess(paper, c["token_id"], now, classification, class_reasons,
                        {"sources": evaluation.get("sources"), "decision_ts": now})
        if classification in ("CONFIRMED_HONEYPOT", "CRITICAL_RISK") or \
           evaluation["verdict"] == "SECURITY_VETO" or not ok_cov:
            reason = (class_reasons[0] if classification in ("CONFIRMED_HONEYPOT", "CRITICAL_RISK")
                      else ("security veto: " + ",".join(evaluation.get("veto_reasons", [])))
                      if evaluation["verdict"] == "SECURITY_VETO" else cov_reason)
            ev2._snap_v2(paper, token_id=c["token_id"], chain=c["chain_id"], address=c["address"],
                         symbol=c["symbol"], cohort=cohort, discovered_ts=c["first_seen_ts"],
                         decision_ts=now, features=feat, security=evaluation,
                         decision="NOT_QUALIFIED", reason=reason, cfg=cfg)
            st["snapshot_v2"] += 1
            bump(f"{classification if classification != 'UNKNOWN' else 'security'}: {reason[:60]}")
            continue
        if c["chain_id"] != "solana":
            want = {("honeypot", "FALSE"), ("sell_tax_extreme", "FALSE")}
            have = {(ch["check_key"], ch["value"]) for ch in evaluation["checks"]}
            if not want <= have:
                reason = "EVM gate: honeypot/sell-tax not both resolved clean (UNKNOWN≠PASS)"
                ev2._snap_v2(paper, token_id=c["token_id"], chain=c["chain_id"], address=c["address"],
                             symbol=c["symbol"], cohort=cohort, discovered_ts=c["first_seen_ts"],
                             decision_ts=now, features=feat, security=evaluation,
                             decision="NOT_QUALIFIED", reason=reason, cfg=cfg)
                st["snapshot_v2"] += 1
                bump("security: " + reason[:50])
                continue
        if alloc < cfg["min_ticket_usd"]:
            ev2._snap_v2(paper, token_id=c["token_id"], chain=c["chain_id"], address=c["address"],
                         symbol=c["symbol"], cohort=cohort, discovered_ts=c["first_seen_ts"],
                         decision_ts=now, features=feat, security=evaluation,
                         decision="QUALIFIED_SKIPPED_NO_CASH",
                         reason=f"cash {cash:.2f} below min ticket — missed-opportunity evidence",
                         cfg=cfg)
            st["qualified_skipped_no_cash"] += 1
            continue
        exe = cm.buy(alloc, obs["price_usd"], obs["liquidity_usd"])
        if exe is None:
            ledger.invalidate(paper, "TRADE", c["token_id"], "v3 entry execution unmodelable — §15")
            st["invalidations"] += 1
            continue
        sid = ev2._snap_v2(paper, token_id=c["token_id"], chain=c["chain_id"], address=c["address"],
                           symbol=c["symbol"], cohort=cohort, discovered_ts=c["first_seen_ts"],
                           decision_ts=now, features=feat, security=evaluation,
                           decision="QUALIFIED_ENTRY", reason="v2 gates passed", cfg=cfg)
        if sid is None:
            continue
        tid = _sha("TRADE3", c["token_id"], now, cfg["version"])
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
            (tid, cfg["version"], sid, c["token_id"], c["chain_id"], c["address"], c["symbol"],
             cohort, c["first_seen_ts"], now, obs["retrieved_ts"], obs["price_usd"],
             cash, alloc, exe["qty"], exe["fee_entry_usd"], exe["slippage_bps"], exe["exec_price"],
             obs["liquidity_usd"], obs["liquidity_usd"],
             taxes["buy_tax_bps"], taxes["sell_tax_bps"], taxes["transfer_tax_bps"],
             cost_complete, classification,
             "EXECUTABLE_OK" if est_slip <= 500 else "EXECUTABLE_THIN",
             entry_rules.opportunity_class(obs), RULE_VERSION,
             now + exit_rules.EXIT_V1["max_hold_hours"] * 3600, _utc(time.time())))
        bankroll.allocate(paper, now, tid, alloc,
                          f"allocated to {c['symbol']} ({classification}, impact {est_slip:.0f}bps)")
        bankroll.state_event(paper, tid, now, "QUALIFIED", "v2 gates passed")
        bankroll.state_event(paper, tid, now, "ENTRY", f"exec {exe['exec_price']:.8g}")
        bankroll.state_event(paper, tid, now, "OPEN", f"cohort={cohort}; exit rules PT-X3-v2")
        ledger.monitor(paper, tid, now, obs["retrieved_ts"], obs["price_usd"],
                       obs["liquidity_usd"], obs["volume_24h"], "ENTRY", cfg["version"])
        a0 = rz.assess(qty=exe["qty"], price_obs=obs["price_usd"], liq_now=obs["liquidity_usd"],
                       sell_tax_bps=taxes["sell_tax_bps"], chain=c["chain_id"],
                       classification=classification)
        record_realizable(paper, tid, now, obs["retrieved_ts"], exe["qty"], a0)
        st["realizable_rows"] += 1
        paper.commit()
        st["entries"] += 1
        cash_after = bankroll.cash_now(paper)
        st["cash_state"] = "CASH_CONSTRAINED" if cash_after < cfg["min_ticket_usd"] else "CASH_AVAILABLE"

    # ------------------------------------------------ autonomous management (PT-X3-v2)
    open_rows = paper.execute(
        """SELECT * FROM paper_trade_v2 t
           WHERE t.trade_id NOT IN (SELECT trade_id FROM paper_exit_v3 WHERE exit_kind='FULL')
             AND t.trade_id NOT IN (SELECT trade_id FROM paper_exit_v2)
             AND t.trade_id NOT IN (SELECT ref_id FROM invalidation WHERE scope='TRADE')""").fetchall()
    budget_box = [security_budget]
    for tr in open_rows:
        _monitor_position(paper, disc, pal, tr, now, st, budget_box)

    st["learning"] = lessons.snapshot_stats(paper, disc, now)
    st["cash"] = bankroll.cash_now(paper)
    disc.close()
    paper.close()
    return st


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default=str(DEFAULT_STORE))
    ap.add_argument("--discovery", default=str(Path(__file__).resolve().parents[1]
                                               / "data" / "e01_discovery.sqlite"))
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--budget", type=int, default=MAX_SECURITY_CALLS)
    ap.add_argument("--report", default=None)
    args = ap.parse_args(argv)
    pal = None if args.offline else PAL()
    st = run_cycle_v3(args.store, args.discovery, pal=pal, security_budget=args.budget)
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(st, indent=1, default=str))
    print(json.dumps(st, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
