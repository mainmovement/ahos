#!/usr/bin/env python3
"""Paper Trading Lab — engine. One run_cycle(now) = candidates → snapshots → entries → monitoring.

Budget law: security provider calls are capped per cycle (MAX_SECURITY_CALLS) — PAL discipline.
Candidates beyond budget are simply not snapshotted yet (they will be re-proposed next cycle —
one decision per token, enforced by UNIQUE(token_id) in decision_snapshot).

Anti-bias construction (all test-pinned):
  - entry features come from latest_observation(..., as_of=now) only;
  - security is evaluated LIVE at decision time and frozen into the snapshot;
  - monitoring consumes observations chronologically; exit prices come from the same observations
    that triggered the exit (never future, never interpolated);
  - SL beats TP when a single observation can't disambiguate (worst-case rule, PT-X1-v1);
  - horizon exit without an observation ⇒ INVALID_DATA_UNAVAILABLE (evidence preserved).
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from discovery.pal import PAL
from . import cost_model as cm
from . import entry_rules, exit_rules, ledger
from .position_monitor import latest_observation, obs_path, security_now, security_recheck

MAX_SECURITY_CALLS = 15        # per cycle — PAL budget discipline
MAX_CANDIDATES_SCANNED = 400


def _feature_snapshot(obs: dict, first_seen_ts: float, now: float) -> dict:
    return {"as_of": now,
            "obs_ref": obs["obs_id"], "obs_ts": obs["retrieved_ts"],
            "price_usd": obs["price_usd"], "liquidity_usd": obs["liquidity_usd"],
            "volume_24h": obs["volume_24h"], "market_cap": obs["market_cap"],
            "txns_5m_buys": obs["txns_5m_buys"], "txns_5m_sells": obs["txns_5m_sells"],
            "age_hours_at_decision": round((now - first_seen_ts) / 3600.0, 4),
            "law": "features strictly from observations with retrieved_ts <= decision_ts"}


def run_cycle(paper_db: str | Path, discovery_db: str | Path, now: float | None = None,
              pal: PAL | None = None, security_budget: int = MAX_SECURITY_CALLS,
              entry_cfg: dict = entry_rules.BASELINE_V1, exit_cfg: dict = exit_rules.EXIT_V1,
              allow_new_entries: bool = True) -> dict:
    now = time.time() if now is None else now
    disc = ledger.open_discovery_ro(discovery_db)
    paper = ledger.open_paper(paper_db)
    ledger.seed_strategy(paper, entry_cfg, exit_cfg,
                         {"version": cm.COST_MODEL_VERSION, "fee_bps": cm.FEE_BPS,
                          "min_slippage_bps": cm.MIN_SLIPPAGE_BPS, "impact_factor": cm.IMPACT_FACTOR})

    stats = {"now": now, "scanned": 0, "snapshots": 0, "entries": 0, "defers_budget": 0,
             "not_qualified": 0, "monitored": 0, "exits": 0, "invalidations": 0, "security_calls": 0}

    # ---- 1) candidate scan & entry decisions -------------------------------------------
    cands = [] if not allow_new_entries else disc.execute(
        """SELECT t.token_id, t.chain_id, t.address, t.symbol, s.first_seen_ts
           FROM tokens t JOIN observation_state s ON s.token_id=t.token_id
           WHERE s.state != 'RESOLVED'
           ORDER BY s.first_seen_ts DESC LIMIT ?""", (MAX_CANDIDATES_SCANNED,)).fetchall()
    for c in cands:
        stats["scanned"] += 1
        already = paper.execute("SELECT 1 FROM decision_snapshot WHERE token_id=?",
                                (c["token_id"],)).fetchone()
        if already:
            continue
        obs = latest_observation(disc, c["token_id"], now)
        if obs is None:
            ledger.record_snapshot(paper, token_id=c["token_id"], chain=c["chain_id"],
                                   address=c["address"], symbol=c["symbol"],
                                   discovered_ts=c["first_seen_ts"], decision_ts=now,
                                   features={"as_of": now, "obs_ref": None},
                                   security={"state": "NO_OBSERVATION"},
                                   rule_version=entry_cfg["version"], decision="NOT_QUALIFIED",
                                   reason="no observation ≤ decision time (data UNKNOWN)")
            stats["snapshots"] += 1
            stats["not_qualified"] += 1
            continue
        # cheap gates first (no provider budget burned on clear rejects)
        cheap, cheap_reason = entry_rules.evaluate_entry(
            now=now, first_seen_ts=c["first_seen_ts"], price_usd=obs["price_usd"],
            liquidity_usd=obs["liquidity_usd"], security={"verdict": "PASS"})
        if cheap != "QUALIFIED_ENTRY":
            feats = _feature_snapshot(obs, c["first_seen_ts"], now)
            ledger.record_snapshot(paper, token_id=c["token_id"], chain=c["chain_id"],
                                   address=c["address"], symbol=c["symbol"],
                                   discovered_ts=c["first_seen_ts"], decision_ts=now,
                                   features=feats, security={"state": "NOT_EVALUATED_PRE_REJECT"},
                                   rule_version=entry_cfg["version"], decision="NOT_QUALIFIED",
                                   reason=cheap_reason)
            stats["snapshots"] += 1
            stats["not_qualified"] += 1
            continue
        if stats["security_calls"] >= security_budget:
            stats["defers_budget"] += 1
            continue                       # NOT snapshotted → retried next cycle (budget honesty)
        stats["security_calls"] += 1
        if pal is None:                    # offline/deterministic mode: security honestly UNKNOWN
            sec = {"verdict": "PASS_WITH_UNKNOWN", "veto_reasons": [], "coverage": 0.0,
                   "state": "OFFLINE_MODE", "checks": []}
        else:
            sec = security_now(pal, c["chain_id"], c["address"], now)
        decision, reason = entry_rules.evaluate_entry(
            now=now, first_seen_ts=c["first_seen_ts"], price_usd=obs["price_usd"],
            liquidity_usd=obs["liquidity_usd"], security=sec)
        feats = _feature_snapshot(obs, c["first_seen_ts"], now)
        sid = ledger.record_snapshot(paper, token_id=c["token_id"], chain=c["chain_id"],
                                     address=c["address"], symbol=c["symbol"],
                                     discovered_ts=c["first_seen_ts"], decision_ts=now,
                                     features=feats, security=sec,
                                     rule_version=entry_cfg["version"], decision=decision,
                                     reason=reason)
        stats["snapshots"] += 1
        if decision != "QUALIFIED_ENTRY" or sid is None:
            stats["not_qualified"] += 1
            continue
        exe = cm.buy(entry_cfg["notional_usd"], obs["price_usd"], obs["liquidity_usd"])
        if exe is None:
            ledger.invalidate(paper, "TRADE", c["token_id"],
                              "execution price unreconstructable (slippage UNKNOWN) — §15 stop")
            stats["invalidations"] += 1
            continue
        tid = ledger.open_trade(
            paper, strategy_version=entry_cfg["version"], snapshot_id=sid,
            token_id=c["token_id"], chain=c["chain_id"], address=c["address"], symbol=c["symbol"],
            discovered_ts=c["first_seen_ts"], entry_decision_ts=now, entry_ts=obs["retrieved_ts"],
            entry_price_observed=obs["price_usd"], fee_bps=cm.FEE_BPS,
            entry_slippage_bps=exe["slippage_bps"], entry_price_exec=exe["exec_price"],
            notional_usd=entry_cfg["notional_usd"], qty=exe["qty"],
            fee_entry_usd=exe["fee_entry_usd"], liq_at_entry=obs["liquidity_usd"],
            exit_rule_version=exit_cfg["version"],
            monitoring_horizon_ts=now + exit_cfg["max_hold_hours"] * 3600)
        if tid:
            stats["entries"] += 1
            ledger.monitor(paper, tid, now, obs["retrieved_ts"], obs["price_usd"],
                           obs["liquidity_usd"], obs["volume_24h"], "ENTRY",
                           f"{entry_cfg['version']} {reason}")

    # ---- 2) monitoring of open positions ------------------------------------------------
    for tr in ledger.open_trades(paper):
        stats["monitored"] += 1
        obs = latest_observation(disc, tr["token_id"], now)
        if obs is None:
            ledger.monitor(paper, tr["trade_id"], now, None, None, None, None,
                           "NO_NEW_DATA", "no observation ≤ now")
        else:
            if obs["retrieved_ts"] < tr["entry_ts"]:
                ledger.invalidate(paper, "TRADE", tr["trade_id"],
                                  "monitor chronology violation: observed before entry_ts")
                stats["invalidations"] += 1
                continue
            ledger.monitor(paper, tr["trade_id"], now, obs["retrieved_ts"], obs["price_usd"],
                           obs["liquidity_usd"], obs["volume_24h"], "OBSERVED", "")
        consec = 0
        for ev in paper.execute(
                """SELECT liquidity_usd FROM monitor_event WHERE trade_id=? AND event='OBSERVED'
                   ORDER BY obs_ts DESC LIMIT ?""",
                (tr["trade_id"], exit_cfg["liq_collapse_consecutive"])).fetchall():
            if ev["liquidity_usd"] is not None and ev["liquidity_usd"] < exit_cfg["liq_collapse_floor_usd"]:
                consec += 1
            else:
                break
        if stats["security_calls"] < security_budget:
            stats["security_calls"] += 1
            sec_check = security_recheck(pal, tr["chain"], tr["address"], now, {}) \
                if pal is not None else {"state": "UNKNOWN", "verdict": "UNKNOWN"}
        else:
            sec_check = None
        hit = exit_rules.check_exits(
            entry_exec=tr["entry_price_exec"], entry_ts=tr["entry_ts"], now=now,
            obs_price=None if obs is None else obs["price_usd"],
            obs_liq=None if obs is None else obs["liquidity_usd"],
            obs_ts=None if obs is None else obs["retrieved_ts"],
            consec_liq_breaches=consec,
            security_recheck=sec_check, cfg=exit_cfg)
        if hit is None:
            continue
        if hit["reason"].startswith("INVALID"):
            # an exit we cannot price honestly NEVER writes a paper_exit — evidence instead
            ledger.invalidate(paper, "TRADE", tr["trade_id"], hit.get("detail", hit["reason"]))
            stats["invalidations"] += 1
            continue
        if obs is None or obs.get("price_usd") is None:
            ledger.invalidate(paper, "TRADE", tr["trade_id"],
                              f"exit '{hit['reason']}' but exit price unreconstructable — §15")
            stats["invalidations"] += 1
            continue
        exe_out = cm.sell(tr["qty"], obs["price_usd"], obs["liquidity_usd"])
        if exe_out is None:
            ledger.invalidate(paper, "TRADE", tr["trade_id"],
                              f"exit '{hit['reason']}' slippage UNKNOWN (liq missing) — §15")
            stats["invalidations"] += 1
            continue
        path = obs_path(disc, tr["token_id"], tr["entry_ts"], obs["retrieved_ts"])
        prices = [p["price_usd"] for p in path if p["price_usd"] and p["price_usd"] > 0]
        mfe = (max(prices) / tr["entry_price_observed"] - 1) if prices else None
        mae = (min(prices) / tr["entry_price_observed"] - 1) if prices else None
        pnl = cm.pnl_decomposition(tr["qty"], tr["entry_price_observed"], tr["entry_price_exec"],
                                   tr["fee_entry_usd"], obs["price_usd"], exe_out["exec_price"],
                                   exe_out["fee_exit_usd"])
        ok = ledger.close_trade(
            paper, trade_id=tr["trade_id"], exit_ts=now, exit_reason=hit["reason"],
            exit_obs_ts=obs["retrieved_ts"], exit_price_observed=obs["price_usd"],
            exit_slippage_bps=exe_out["slippage_bps"], exit_price_exec=exe_out["exec_price"],
            pnl=pnl, fee_exit_usd=exe_out["fee_exit_usd"], mfe_pct=mfe, mae_pct=mae,
            hold_hours=round((now - tr["entry_ts"]) / 3600.0, 3))
        if ok:
            stats["exits"] += 1
            ledger.monitor(paper, tr["trade_id"], now, obs["retrieved_ts"], obs["price_usd"],
                           obs["liquidity_usd"], obs["volume_24h"], "EXIT", hit["reason"])

    paper.commit()
    disc.close()
    paper.close()
    return stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default=str(Path(__file__).resolve().parents[1] / "data" / "paper_trading.sqlite"))
    ap.add_argument("--discovery", default=str(Path(__file__).resolve().parents[1] / "data" / "e01_discovery.sqlite"))
    ap.add_argument("--offline", action="store_true", help="no provider calls (security UNKNOWN — recorded)")
    ap.add_argument("--report", default=None)
    args = ap.parse_args(argv)
    pal = None if args.offline else PAL()
    st = run_cycle(args.store, args.discovery, pal=pal)
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(st, indent=1))
    print(json.dumps(st, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
