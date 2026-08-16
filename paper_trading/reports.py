#!/usr/bin/env python3
"""Paper Trading Lab — reports. Two-track separated output (Research Track is NOT recomputed
here — cited from E-01 counters only). All figures from the append-only ledger.

Laws: GROSS/COST/SLIPPAGE/NET distinguished always; gross-win/net-loss = LOSS;
illiquid +100% ≠ liquid +100% (liquidity band segmentation is always printed);
no strategy is called profitable — expectancy statements gate on ≥30 closed trades.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

MIN_CLOSED_FOR_EXPECTANCY = 30   # descriptive gate — cannot be lowered post-hoc (§7/§9)


def _equity_max_drawdown(nets: list[float]) -> float:
    peak, mdd, eq = 0.0, 0.0, 0.0
    for n in nets:
        eq += n
        peak = max(peak, eq)
        mdd = min(mdd, eq - peak)
    return mdd


def paper_report(paper_db: str, strategy_version: str | None = None) -> dict:
    conn = sqlite3.connect(paper_db)
    conn.row_factory = sqlite3.Row
    where = "WHERE t.strategy_version=?" if strategy_version else ""
    args = (strategy_version,) if strategy_version else ()
    trades = conn.execute(
        f"""SELECT t.*, x.exit_reason, x.net_pnl_usd, x.gross_pnl_usd, x.slippage_usd,
                   x.cost_total_usd, x.mfe_pct, x.mae_pct, x.hold_hours
            FROM paper_trade t LEFT JOIN paper_exit x ON x.trade_id=t.trade_id {where}""",
        args).fetchall()
    snaps = conn.execute("SELECT decision, COUNT(*) c FROM decision_snapshot GROUP BY decision").fetchall()
    inv = [dict(r) for r in conn.execute("SELECT scope,ref_id,reason,created_utc FROM invalidation")]
    closed = [t for t in trades if t["net_pnl_usd"] is not None]
    open_ = [t for t in trades if t["net_pnl_usd"] is None]
    nets = [t["net_pnl_usd"] for t in closed]
    gross = sum(t["gross_pnl_usd"] for t in closed)
    slip = sum(t["slippage_usd"] for t in closed)
    cost = sum(t["cost_total_usd"] for t in closed)
    wins = [n for n in nets if n > 0]
    losses = [n for n in nets if n <= 0]
    pf = (sum(wins) / abs(sum(losses))) if losses and sum(losses) != 0 else None
    thin = [t for t in closed if (t["liq_at_entry"] or 0) < 25_000]
    rep = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "strategy": strategy_version or "ALL",
        "candidates_decided": {r["decision"]: r["c"] for r in snaps},
        "paper_entries": len(trades),
        "open_positions": len(open_),
        "closed_positions": len(closed),
        "invalidated": [i for i in inv],
        "gross_pnl_usd": round(gross, 4), "slippage_usd": round(slip, 4),
        "cost_usd": round(cost, 4), "net_pnl_usd": round(gross - slip - cost, 4),
        "win_rate": (len(wins) / len(closed)) if closed else None,
        "avg_winner_usd": (sum(wins) / len(wins)) if wins else None,
        "avg_loser_usd": (sum(losses) / len(losses)) if losses else None,
        "expectancy_usd": (sum(nets) / len(nets)) if nets else None,
        "profit_factor": pf,
        "max_drawdown_usd": _equity_max_drawdown(nets),
        "avg_hold_hours": (sum(t["hold_hours"] for t in closed) / len(closed)) if closed else None,
        "exposure_open_usd": sum(t["notional_usd"] for t in open_),
        "liq_bands": {"THIN(<25k)_closed": len(thin),
                      "THIN_net_pnl_usd": round(sum(t["net_pnl_usd"] for t in thin), 4),
                      "REST_closed": len(closed) - len(thin),
                      "REST_net_pnl_usd": round(sum(t["net_pnl_usd"] for t in closed
                                                    if (t["liq_at_entry"] or 0) >= 25_000), 4)},
        "gross_win_but_net_loss_count": sum(1 for t in closed
                                            if t["gross_pnl_usd"] > 0 and t["net_pnl_usd"] <= 0),
    }
    if len(closed) < MIN_CLOSED_FOR_EXPECTANCY:
        rep["expectancy_gate"] = (f"INSUFFICIENT_CLOSED_TRADES ({len(closed)}<{MIN_CLOSED_FOR_EXPECTANCY})"
                                  " — no expectancy/profitability language permitted")
    conn.close()
    return rep


def render_two_track(research: dict, paper: dict) -> str:
    L = ["═" * 64, "AHOS PERIODIC REPORT — TWO TRACKS (separated by law)", "═" * 64, "",
         "RESEARCH TRACK (E-01 / H14–H20)"]
    for k in ("tokens", "observations", "resolved", "cohort_readiness", "h14_h20_gate"):
        L.append(f"  {k}: {research.get(k)}")
    L += ["", "PAPER TRACK (isolated; PT results are NOT research-gate evidence — §10)"]
    for k in ("candidates_decided", "paper_entries", "open_positions", "closed_positions",
              "gross_pnl_usd", "slippage_usd", "cost_usd", "net_pnl_usd", "win_rate",
              "profit_factor", "max_drawdown_usd", "avg_hold_hours", "exposure_open_usd",
              "liq_bands", "gross_win_but_net_loss_count", "invalidated"):
        L.append(f"  {k}: {paper.get(k)}")
    if paper.get("expectancy_gate"):
        L.append(f"  ⛔ {paper['expectancy_gate']}")
    L += ["", "Allowed language: 'PT-BASELINE-v1 entered because conditions X/Y/Z were observed at T.'",
          "Forbidden: predictions, probabilities, investment directives. تصمیم نهایی با کاربر است."]
    return "\n".join(L)


# ---------------------------------------------------------------- Wave-8 experiment view
def paper_report_experiment(paper_db: str) -> dict:
    """§F/§O aggregation for the $20 experiment. Pure read of append-only stores."""
    conn = sqlite3.connect(paper_db)
    conn.row_factory = sqlite3.Row
    def one(q, a=()):
        r = conn.execute(q, a).fetchone()
        return dict(r) if r else {}
    # v2 experiment counters
    snaps = conn.execute("SELECT decision, reject_class, COUNT(*) c FROM decision_snapshot_v2"
                         " GROUP BY decision, reject_class").fetchall()
    rej = {}
    for s in snaps:
        if s["decision"] == "NOT_QUALIFIED":
            rej[s["reject_class"] or "other"] = rej.get(s["reject_class"] or "other", 0) + s["c"]
    entries = conn.execute("SELECT * FROM paper_trade_v2").fetchall()
    exits = conn.execute("SELECT * FROM paper_exit_v2").fetchall()
    open_ids = {e["trade_id"] for e in entries} - {x["trade_id"] for x in exits}
    cash = one("SELECT cash_after FROM portfolio_ledger ORDER BY id DESC LIMIT 1")
    by_state = conn.execute(
        """SELECT state, COUNT(*) c FROM (SELECT trade_id, state FROM position_state_event
             WHERE id IN (SELECT MAX(id) FROM position_state_event GROUP BY trade_id)) GROUP BY state""").fetchall()
    fees = sum(e["fee_entry_usd"] for e in entries) + sum((x["exit_fee_usd"] or 0) for x in exits)
    slip = sum(x["exit_slippage_usd"] or 0 for x in exits) + \
        sum(e["qty"] * (e["entry_price_exec"] - e["entry_price_observed"]) for e in entries)
    taxes = sum(x["sell_tax_usd"] or 0 for x in exits)
    realized = sum(x["realized_pnl_usd"] or 0 for x in exits)
    cap_lost = sum(x["capital_loss_usd"] or 0 for x in exits)
    wins = [x for x in exits if (x["realized_pnl_usd"] or 0) > 0]
    losses = [x for x in exits if x["exit_reason"] not in ("TRAPPED", "TOTAL_LOSS")
              and (x["realized_pnl_usd"] or 0) <= 0]
    trapped = [x for x in exits if x["exit_reason"] in ("TRAPPED", "TOTAL_LOSS")]
    nets = [x["realized_pnl_usd"] or 0 for x in exits]
    cohort_rows = conn.execute(
        """SELECT t.cohort, COUNT(*) trades, SUM(x.realized_pnl_usd) pnl FROM paper_trade_v2 t
           JOIN paper_exit_v2 x ON x.trade_id=t.trade_id GROUP BY t.cohort""").fetchall()
    best = max(exits, key=lambda x: x["realized_pnl_usd"] or -9e9, default=None)
    worst = min(exits, key=lambda x: x["realized_pnl_usd"] or 9e9, default=None)
    scam = conn.execute("SELECT classification, COUNT(*) c FROM scam_assessment GROUP BY classification").fetchall()
    rep = {
        "bankroll_start_usd": 20.00,
        "cash_now_usd": round(cash.get("cash_after", 20.0), 4),
        "capital_at_risk_usd": round(sum(e["amount_allocated"] for e in entries
                                         if e["trade_id"] in open_ids), 4),
        "candidates_decided": len(snaps_rows := conn.execute("SELECT 1 FROM decision_snapshot_v2").fetchall()),
        "rejected_by_class": rej,
        "scam_assessments": {r["classification"]: r["c"] for r in scam},
        "qualified_skipped_no_cash": sum(s["c"] for s in snaps
                                         if s["decision"] == "QUALIFIED_SKIPPED_NO_CASH"),
        "paper_entries": len(entries), "open_positions": len(open_ids),
        "paper_exits": len(exits),
        "state_counts": {r["state"]: r["c"] for r in by_state},
        "winning_trades": len(wins), "losing_trades": len(losses),
        "trapped_positions": len(trapped),
        "total_fees_usd": round(fees, 4), "total_slippage_usd": round(slip, 4),
        "total_token_taxes_usd": round(taxes, 4),
        "realized_pnl_usd": round(realized, 4),
        "capital_lost_trapped_usd": round(cap_lost, 4),
        "max_drawdown_usd": _equity_max_drawdown(nets),
        "best_trade": (dict(best) if best else None),
        "worst_trade": (dict(worst) if worst else None),
        "cohorts": {r["cohort"]: {"trades": r["trades"], "realized_pnl": r["pnl"]} for r in cohort_rows},
        "expectancy_gate": ("INSUFFICIENT_CLOSED_TRADES — no expectancy/profitability language permitted"
                            if len(exits) < MIN_CLOSED_FOR_EXPECTANCY else "descriptive-n-ok"),
    }
    conn.close()
    return rep


def render_experiment_24h(rep: dict, unrealized: dict | None = None) -> str:
    """§O renderer — answers REQUIRED questions from evidence only."""
    L = ["═" * 66, "24H EXPERIMENT — IF THIS HAD BEEN REAL MONEY ($20.00)", "═" * 66]
    end_cash = rep["cash_now_usd"]
    start = rep["bankroll_start_usd"]
    total_now = end_cash + rep["capital_at_risk_usd"]
    L += [f"  starting bankroll: ${start:.2f}",
          f"  ending cash: ${end_cash:.4f}",
          f"  capital at risk (open, allocated): ${rep['capital_at_risk_usd']:.4f}",
          f"  trapped capital lost: ${rep['capital_lost_trapped_usd']:.4f}",
          f"  total fees: ${rep['total_fees_usd']:.4f} | slippage: ${rep['total_slippage_usd']:.4f}"
          f" | token taxes (known): ${rep['total_token_taxes_usd']:.4f}",
          f"  realized PnL: ${rep['realized_pnl_usd']:+.4f}",
          f"  net position vs start (cash+risk − 20): ${total_now - start:+.4f}"
          f"  ({100*(total_now-start)/start:+.2f}%)",
          f"  max drawdown (realized eq. curve): ${rep['max_drawdown_usd']:.4f}",
          f"  trades: {rep['paper_entries']} | exits: {rep['paper_exits']}"
          f" | wins {rep['winning_trades']} / losses {rep['losing_trades']} / trapped {rep['trapped_positions']}",
          f"  scam defense: {rep['scam_assessments']} | rejects by class: {rep['rejected_by_class']}",
          f"  cohorts (NEW/EARLY/ESTABLISHED): {rep['cohorts']}", ""]
    if unrealized is not None:
        L.append(f"  unrealized (mark-to-model, fresh obs only): {unrealized}")
    L += ["  ⛔ " + rep["expectancy_gate"] if not rep["expectancy_gate"].startswith("desc")
          else "  descriptive gate: PASSED",
          "  Language law: this is PAPER evidence about a deterministic policy, not a prediction.",
          "  تصمیم نهایی با کاربر است."]
    return "\n".join(L)


# ------------------------------------------------- Wave-8 continuation: realizable equity truth
def experiment_equity(paper_db: str) -> dict:
    """§13 capital discipline: every dollar accounted; DISPLAYED vs REALIZABLE kept separate.
    Derived purely from append-only stores (latest realizable_snapshot per open trade)."""
    conn = sqlite3.connect(paper_db)
    conn.row_factory = sqlite3.Row
    def one(q, a=()):
        r = conn.execute(q, a).fetchone()
        return r[0] if r else 0.0
    open_rows = conn.execute(
        """SELECT t.trade_id, t.amount_allocated, t.symbol, t.chain,
                  COALESCE((SELECT SUM(x.allocated_retired_usd) FROM paper_exit_v3 x
                            WHERE x.trade_id=t.trade_id),0) AS retired
           FROM paper_trade_v2 t
           WHERE t.trade_id NOT IN (SELECT trade_id FROM paper_exit_v3 WHERE exit_kind='FULL')
             AND t.trade_id NOT IN (SELECT trade_id FROM paper_exit_v2)
             AND t.trade_id NOT IN (SELECT ref_id FROM invalidation WHERE scope='TRADE')""").fetchall()
    disp = realz = trapped_open = 0.0
    per = []
    for t in open_rows:
        snap = conn.execute(
            """SELECT * FROM realizable_snapshot WHERE trade_id=? ORDER BY id DESC LIMIT 1""",
            (t["trade_id"],)).fetchone()
        d = (snap["displayed_value_usd"] or 0.0) if snap else 0.0
        rz = (snap["realizable_value_usd"] or 0.0) if snap else 0.0
        route = snap["route_status"] if snap else "UNPRICED"
        alloc_rem = t["amount_allocated"] - t["retired"]
        disp += d
        realz += rz
        if not route.startswith(("EXECUTABLE", "SECURITY")):
            trapped_open += alloc_rem
        per.append({"trade": t["symbol"], "displayed": round(d, 4), "realizable": round(rz, 4),
                    "route": route, "alloc_remaining": round(alloc_rem, 4)})
    alloc_rem_total = sum(t["amount_allocated"] - t["retired"] for t in open_rows)
    fees = one("SELECT COALESCE(SUM(fee_entry_usd),0) FROM paper_trade_v2") \
        + one("SELECT COALESCE(SUM(exit_fee_usd),0) FROM paper_exit_v3")
    gas = one("SELECT COALESCE(SUM(gas_cost_usd),0) FROM paper_exit_v3")
    taxes = one("SELECT COALESCE(SUM(sell_tax_usd),0) FROM paper_exit_v3")
    slip = one("SELECT COALESCE(SUM(qty*(entry_price_exec-entry_price_observed)),0) FROM paper_trade_v2") \
        + one("SELECT COALESCE(SUM(exit_slippage_usd),0) FROM paper_exit_v3")
    realized = one("SELECT COALESCE(SUM(realized_pnl_usd),0) FROM paper_exit_v3")
    cap_lost = one("SELECT COALESCE(SUM(capital_loss_usd),0) FROM paper_exit_v3 WHERE exit_kind='FULL'")
    cash = one("SELECT cash_after FROM portfolio_ledger ORDER BY id DESC LIMIT 1") or 20.0
    out = {
        "bankroll_start_usd": 20.00, "cash_usd": round(cash, 4),
        "open_displayed_value_usd": round(disp, 4),
        "open_realizable_value_usd": round(realz, 4),
        "open_alloc_remaining_usd": round(alloc_rem_total, 4),
        "realized_pnl_usd": round(realized, 4),
        "unrealized_pnl_displayed_basis_usd": round(disp - alloc_rem_total, 4),
        "unrealized_pnl_realizable_basis_usd": round(realz - alloc_rem_total, 4),
        "trapped_capital_open_usd": round(trapped_open, 4),
        "total_loss_booked_usd": round(cap_lost, 4),
        "fees_total_usd": round(fees, 4), "gas_total_usd": round(gas, 4),
        "taxes_known_total_usd": round(taxes, 4), "slippage_total_usd": round(slip, 4),
        "net_equity_displayed_usd": round(cash + disp, 4),
        "net_equity_realizable_usd": round(cash + realz, 4),
        "equity_truth": ("NET_EQUITY_REALIZABLE is the economically meaningful number; "
                         "DISPLAYED is what a naive UI would show — never used for decisions"),
        "open_positions": per,
    }
    conn.close()
    return out


def render_autonomous_status(equity: dict, learning: dict, n_lessons: int) -> str:
    """Wave-8 continuation status block — appended to the periodic two-track report."""
    L = ["", "AUTONOMOUS POSITION MANAGEMENT (PT-X3-v1, realizable truth)", "  " + "─" * 56]
    for k in ("bankroll_start_usd", "cash_usd", "open_displayed_value_usd",
              "open_realizable_value_usd", "realized_pnl_usd",
              "unrealized_pnl_displayed_basis_usd", "unrealized_pnl_realizable_basis_usd",
              "trapped_capital_open_usd", "total_loss_booked_usd", "fees_total_usd",
              "gas_total_usd", "taxes_known_total_usd", "slippage_total_usd",
              "net_equity_displayed_usd", "net_equity_realizable_usd"):
        L.append(f"  {k}: {equity.get(k)}")
    L.append(f"  open positions: {equity.get('open_positions')}")
    L.append(f"  lessons recorded: {n_lessons}")
    if learning:
        keep = ("closed_trades", "profitable_trades", "losing_trades", "trapped_or_total_loss",
                "honeypots_avoided", "honeypots_missed", "false_security_pass",
                "false_security_reject", "scams_avoided_validated", "missed_opportunity_validated",
                "partial_exits_taken", "news_social_signal_accuracy")
        L.append("  learning counters (§11): " +
                 str({k: learning.get(k) for k in keep if k in learning}))
    L.append("  law: probability language replaced by NOT_ESTIMABLE/categorical evidence (frozen law).")
    return "\n".join(L)
