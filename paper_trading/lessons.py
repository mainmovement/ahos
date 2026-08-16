#!/usr/bin/env python3
"""Paper Trading Lab — LEARNING LOOP (Wave-8 continuation §10/§11).

"Every trade must teach us something." A lesson is EVIDENCE, not a rule change:
frozen cards are never silently modified. Output structure per trade:
  LESSON / HYPOTHESIS / EVIDENCE / PROPOSED_IMPROVEMENT  (+ full §10 question answers).
§11 counters are RECOMPUTED from the append-only tables each cycle (no drifting state),
then snapshotted for audit. Track-A discovery store is consulted READ-ONLY for outcome
review of REJECTED tokens (missed-opportunity / false-positive-false-negative evidence).
Out-of-sample post-close review is explicitly allowed for learning (§9: never to justify
an earlier decision — lessons are labeled OUT_OF_SAMPLE_REVIEW).
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone

from . import ledger
from .bankroll import _utc

OUT_OF_SAMPLE_NOTE = ("OUT_OF_SAMPLE_REVIEW — post-close data may judge the decision, "
                      "never retroactively justify it (§9)")

# Locked review bands for outcome review of rejected/skipped tokens (pre-registered here):
REVIEW_TOKENS_DEAD_LIQ = 500.0       # later liq < this ⇒ "we would have been stuck" evidence
REVIEW_DOUBLED = 2.0                 # later price ≥ 2× decision-time price ⇒ missed-opportunity band
REVIEW_DUMPED = 0.20                 # later price ≤ 20% of decision-time price ⇒ avoidance validated


def _j(x) -> str:
    return json.dumps(x, sort_keys=True, default=str, ensure_ascii=False)


def build_lesson(paper, discovery, trade_id: str) -> dict | None:
    """Assemble the §10 structured lesson for a CLOSED trade. Read-only assembly."""
    tr = paper.execute("SELECT * FROM paper_trade_v2 WHERE trade_id=?", (trade_id,)).fetchone()
    if tr is None:
        return None
    exits = paper.execute(
        "SELECT * FROM paper_exit_v3 WHERE trade_id=? ORDER BY exit_seq", (trade_id,)).fetchall()
    if not exits:
        return None
    final = exits[-1]
    events = paper.execute(
        "SELECT ts,state,reason FROM position_state_event WHERE trade_id=? ORDER BY id",
        (trade_id,)).fetchall()
    monitors = paper.execute(
        "SELECT obs_ts,price_usd,liquidity_usd FROM monitor_event"
        " WHERE trade_id=? AND event='OBSERVED' ORDER BY obs_ts", (trade_id,)).fetchall()
    snap = paper.execute("SELECT * FROM decision_snapshot_v2 WHERE snapshot_id=?",
                         (tr["snapshot_id"],)).fetchone()
    rz_last = paper.execute(
        "SELECT * FROM realizable_snapshot WHERE trade_id=? ORDER BY id DESC LIMIT 1",
        (trade_id,)).fetchone()

    realized = sum(x["net_proceeds_usd"] or 0.0 for x in exits) - tr["amount_allocated"]
    reason = final["exit_reason"]
    if reason in ("TRAPPED", "TOTAL_LOSS"):
        outcome = reason
    elif reason == "SECURITY_EVENT" and tr["security_class"] == "MEDIUM_RISK":
        outcome = "RUG" if "RUG" in (final["exit_reason"] or "") else "LOSS"
    else:
        outcome = "PROFIT" if realized > 0 else "LOSS"

    entry_feat = json.loads(snap["features_json"]) if snap else {}
    entry_sec = json.loads(snap["security_json"]) if snap else {}
    prices = [m["price_usd"] for m in monitors if m["price_usd"] and m["price_usd"] > 0]
    entry_p = tr["entry_price_exec"]
    peak_gain = (max(prices) / entry_p - 1) if prices else None
    exit_p = final["exit_price_observed"]

    # ---- timing review (OUT-OF-SAMPLE, honest): could earlier/later have been better?
    too_late_exit = bool(peak_gain is not None and peak_gain >= 0.5
                         and exit_p is not None and exit_p < entry_p * (1 + 0.5 * 0.5))
    decisions = [e for e in events if e["state"] in ("RISK_ESCALATION",)]
    first_escalation_before_exit = bool(decisions and decisions[-1]["ts"] < final["exit_ts"])

    miss_fields = sorted(k for k, v in (entry_sec.get("taxes") or {}).items() if v is None)
    unknown_checks = [c["check_key"] for c in entry_sec.get("checks", [])
                      if c["value"] in (None, "UNKNOWN")] if entry_sec.get("checks") else []

    displayed_pre = final["displayed_value_pre_usd"]
    realizable_pre = final["realizable_value_pre_usd"]
    liq_est_error = None
    if displayed_pre and realizable_pre is not None and displayed_pre > 1e-9:
        liq_est_error = round(1 - realizable_pre / displayed_pre, 4)

    answers = {
        "what_we_believed_before_entry": {
            "cohort": tr["cohort"], "opportunity_class": tr["opportunity_class"],
            "security_class_at_entry": tr["security_class"],
            "execution_class": tr["execution_class"],
            "liq_at_entry": tr["liq_at_entry"],
            "belief": ("token passed all v2 gates at entry time; risk class "
                       f"{tr['security_class']} — never 'safe'")},
        "evidence_supporting_entry": {
            "price": entry_feat.get("price_usd"), "liquidity": entry_feat.get("liquidity_usd"),
            "age_hours": entry_feat.get("age_hours"),
            "security_verdict": entry_sec.get("verdict"),
            "coverage_resolved_critical": entry_sec.get("resolved_critical")},
        "evidence_missing_at_entry": {
            "tax_fields_unknown": miss_fields, "checks_unknown": unknown_checks,
            "sell_simulation": entry_sec.get("sell_simulation"),
            "holder_deployer": "source-blocked (free-tier refutation stands)",
            "social_news": "NO FEED in lab — UNKNOWN by construction"},
        "what_actually_happened": {
            "outcome": outcome, "exit_reason_final": reason,
            "n_exit_chunks": len(exits), "realized_pnl_usd": round(realized, 6),
            "peak_gain_vs_entry_entry_exec": round(peak_gain, 4) if peak_gain is not None else None,
            "hold_hours": final["hold_hours"]},
        "which_signal_worked": (reason if realized > 0 else
                                "none produced profit" if realized <= 0 else None),
        "which_signal_failed": (f"final exit reason {reason} realized {realized:+.4f}"
                                if realized <= 0 else None),
        "was_entry_too_early": ("UNKNOWN — no counterfactual protocol exists yet "
                                "(proposed improvement logged)"),
        "was_entry_too_late": "UNKNOWN — same as above",
        "was_exit_too_early": ("evidence: peak gain " +
                               (f"{peak_gain:+.1%} observed; exit captured less" if too_late_exit
                                else "no peak-above-TP was observed in-sample")
                               if peak_gain is not None else "UNKNOWN (no price path)"),
        "was_exit_too_late": ("escalation fired BEFORE exit — earlier exit was signalled"
                              if first_escalation_before_exit else "no prior escalation"),
        "liquidity_correctly_estimated": (f"impact-model error vs displayed at exit: {liq_est_error}"
                                          if liq_est_error is not None else "UNKNOWN"),
        "executable_value_correctly_estimated": (
            f"displayed_pre_exit {displayed_pre} vs realizable_pre_exit {realizable_pre}"
            if displayed_pre is not None else "UNKNOWN"),
        "fees_slippage_underestimated": (
            f"exit chunk costs: fee {final['exit_fee_usd']}, slip {final['exit_slippage_usd']}, "
            f"tax {final['sell_tax_usd']}, gas {final['gas_cost_usd']} "
            f"vs allocated {tr['amount_allocated']:.2f}"),
        "did_security_miss_anything": (
            f"entry class {tr['security_class']} → final reason {reason}" +
            (" — entry filter did NOT see this (missed-scam evidence)"
             if outcome in ("RUG", "HONEYPOT", "TRAPPED", "TOTAL_LOSS") else "")),
        "did_social_news_help_or_mislead": "UNAVAILABLE_NO_FEED — cannot answer, honestly recorded",
        "could_scam_be_detected_earlier": (
            decisions[-1]["reason"] if decisions else "no escalation evidence before final exit"),
        "note": OUT_OF_SAMPLE_NOTE,
    }

    # ---- LESSON / HYPOTHESIS / EVIDENCE / PROPOSED_IMPROVEMENT
    lessons, hyps, props = [], [], []
    alloc = tr["amount_allocated"]
    gas_share = ((final["gas_cost_usd"] or 0) + tr["fee_entry_usd"]) / alloc if alloc else 0
    if gas_share > 0.25:
        lessons.append(f"fee+gas drag consumed {gas_share:.0%} of a ${alloc:.2f} ticket on {tr['chain']}")
        hyps.append("H-PT-DRAG: tickets below ~$10 on high-gas chains cannot overcome fixed exit costs")
        props.append("test chain-aware min_ticket (e.g. higher floor on ethereum) as a NEW card")
    if outcome in ("TRAPPED", "TOTAL_LOSS"):
        lessons.append("displayed value was fiction: exit route did not exist at decision time")
        hyps.append("H-PT-EXIT: entry-time min liquidity is not sufficient for exitability at tiny size")
        props.append("test entry gate 'expected realizable recovery ≥ 50% of alloc at entry obs' — NEW card")
    if displayed_pre and realizable_pre and displayed_pre >= 2 * max(realizable_pre, 1e-9) \
            and realized > 0:
        lessons.append("displayed/realizable divergence was real; locking realizable preserved value")
    if liq_est_error is not None and liq_est_error > 0.30:
        lessons.append(f"liquidity model overestimated exitability by {liq_est_error:.0%} at exit")
        props.append("collect cross-check of impact model vs realized slippage across ≥10 exits before any tuning")
    if realized <= 0 and peak_gain is not None and peak_gain >= 0.5:
        lessons.append("position saw ≥+50% in-sample yet closed non-profit — profit-lock rules need evidence")
        hyps.append("H-PT-LOCK: profit-lock thresholds may be mistuned — accumulate ≥10 cases before any change")
    if not lessons:
        lessons.append("trade executed and closed per card; no anomaly beyond recorded costs")
    if not hyps:
        hyps.append("no new hypothesis — single observations are not evidence for rule change")
    if not props:
        props.append("none — frozen rules unchanged; continue accumulating evidence")

    now = time.time()
    return {
        "trade_id": trade_id, "closed_ts": final["exit_ts"], "outcome_class": outcome,
        "answers": answers, "lesson": " | ".join(lessons), "hypothesis": " | ".join(hyps),
        "evidence": _j({"exits": len(exits), "final_reason": reason, "realized": round(realized, 6),
                        "monitor_obs": len(prices)}),
        "proposed_improvement": " | ".join(props),
        "model_versions": _j({"entry": tr["strategy_version"], "exit": final["rule_version"],
                              "cost": "PT-COST-v1", "realizable": (rz_last or {}).get("model_version")
                              if isinstance(rz_last, dict) else "PT-REALIZABLE-v1"}),
        "created_utc": _utc(now),
    }


def record_lesson(paper, discovery, trade_id: str) -> bool:
    lesson = build_lesson(paper, discovery, trade_id)
    if lesson is None:
        return False
    if paper.execute("SELECT 1 FROM post_trade_lesson WHERE trade_id=?", (trade_id,)).fetchone():
        return False                                    # one lesson per closed trade (idempotent)
    paper.execute(
        """INSERT INTO post_trade_lesson(trade_id,closed_ts,outcome_class,answers_json,lesson,
               hypothesis,evidence,proposed_improvement,model_versions,created_utc)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (lesson["trade_id"], lesson["closed_ts"], lesson["outcome_class"],
         _j(lesson["answers"]), lesson["lesson"], lesson["hypothesis"], lesson["evidence"],
         lesson["proposed_improvement"], lesson["model_versions"], lesson["created_utc"]))
    paper.commit()
    return True


# ----------------------------------------------------------------- §11 adaptive statistics
def _rejected_outcome_review(paper, discovery) -> dict:
    """READ-ONLY outcome review of NOT_QUALIFIED / SKIPPED tokens vs latest discovery obs.
    Bands locked at module top. Returns evidence counters; unknown stays unknown."""
    out = {"avoidance_validated": 0, "false_security_reject": 0, "missed_opportunity": 0,
           "review_pending": 0, "not_reviewable": 0}
    rows = paper.execute(
        """SELECT token_id, decision, reject_class, features_json, decision_ts
           FROM decision_snapshot_v2 WHERE decision != 'QUALIFIED_ENTRY'""").fetchall()
    for r in rows:
        feat = json.loads(r["features_json"])
        p0 = feat.get("price_usd")
        obs = None
        if discovery is not None:
            try:
                row = discovery.execute(
                    """SELECT price_usd, liquidity_usd FROM discovery_observations
                       WHERE token_id=? AND error_state IS NULL AND retrieved_ts>=?
                       ORDER BY retrieved_ts DESC LIMIT 1""", (r["token_id"], r["decision_ts"])).fetchone()
                obs = dict(row) if row else None
            except Exception:
                obs = None
        if obs is None or p0 is None or p0 <= 0 or obs["price_usd"] in (None, 0):
            out["not_reviewable"] += 1
            continue
        ratio = obs["price_usd"] / p0
        if obs["liquidity_usd"] is not None and obs["liquidity_usd"] < REVIEW_TOKENS_DEAD_LIQ \
                or ratio <= REVIEW_DUMPED:
            if r["reject_class"] in ("security", "honeypot"):
                out["avoidance_validated"] += 1
            else:
                out["_liq_reject_valid"] = out.get("_liq_reject_valid", 0) + 1
        elif ratio >= REVIEW_DOUBLED:
            if r["reject_class"] in ("security", "honeypot"):
                out["false_security_reject"] += 1          # security said no; market said 2x
            if r["decision"] == "QUALIFIED_SKIPPED_NO_CASH":
                out["missed_opportunity"] += 1
        else:
            out["review_pending"] += 1
    return out


def learning_stats(paper, discovery=None) -> dict:
    """§11 counters — recomputed from tables every call (single source of truth)."""
    def c(q, a=()):
        return paper.execute(q, a).fetchone()[0]
    closed = c("SELECT COUNT(DISTINCT trade_id) FROM paper_exit_v3 WHERE exit_kind='FULL'")
    stats = {
        "closed_trades": closed,
        "profitable_trades": None,          # computed in the aggregate loop below
        "losing_trades": None, "trapped_or_total_loss": None,
        "scams_avoided_validated": 0, "scams_avoided_pending": 0, "scams_missed": 0,
        "honeypots_avoided": c("""SELECT COUNT(*) FROM decision_snapshot_v2
            WHERE decision='NOT_QUALIFIED' AND reject_class='honeypot'"""),
        "honeypots_missed": c("""SELECT COUNT(DISTINCT x.trade_id) FROM paper_exit_v3 x
            JOIN paper_trade_v2 t ON t.trade_id=x.trade_id
            WHERE x.exit_reason IN ('TRAPPED','TOTAL_LOSS')
            AND (SELECT classification FROM scam_assessment s WHERE s.token_id=t.token_id
                 ORDER BY id DESC LIMIT 1)='CONFIRMED_HONEYPOT'"""),
        "false_security_pass": c("""SELECT COUNT(DISTINCT x.trade_id) FROM paper_exit_v3 x
            WHERE x.exit_reason IN ('TRAPPED','TOTAL_LOSS','SECURITY_EVENT')"""),
        "partial_exits_taken": c("SELECT COUNT(*) FROM paper_exit_v3 WHERE exit_kind='PARTIAL'"),
        "liquidity_estimation_errors_gt30pct": 0,
        "slippage_estimation_errors": 0,
        "news_social_signal_accuracy": "UNAVAILABLE_NO_FEED — UNKNOWN by construction",
        "early_entry_accuracy": "NO_COUNTERFACTUAL_PROTOCOL_YET",
        "late_entry_mistakes": "NO_COUNTERFACTUAL_PROTOCOL_YET",
    }
    rows = paper.execute(
        """SELECT x.trade_id, SUM(x.net_proceeds_usd) proceeds, t.amount_allocated alloc,
                  MAX(CASE WHEN x.exit_kind='FULL' THEN x.exit_reason END) final_reason,
                  MAX(x.displayed_value_pre_usd) disp, MAX(x.realizable_value_pre_usd) realz
           FROM paper_exit_v3 x JOIN paper_trade_v2 t ON t.trade_id=x.trade_id
           GROUP BY x.trade_id
           HAVING SUM(CASE WHEN x.exit_kind='FULL' THEN 1 ELSE 0 END) > 0""").fetchall()
    prof = loss = trapped = liq_err = 0
    for r in rows:
        net = (r["proceeds"] or 0.0) - r["alloc"]
        if r["final_reason"] in ("TRAPPED", "TOTAL_LOSS"):
            trapped += 1
        elif net > 0:
            prof += 1
        else:
            loss += 1
        if r["disp"] and r["realz"] is not None and r["disp"] > 1e-9 \
                and 1 - r["realz"] / r["disp"] > 0.30:
            liq_err += 1
    stats["profitable_trades"] = prof
    stats["losing_trades"] = loss
    stats["trapped_or_total_loss"] = trapped
    stats["liquidity_estimation_errors_gt30pct"] = liq_err
    review = _rejected_outcome_review(paper, discovery)
    stats["scams_avoided_validated"] = review["avoidance_validated"]
    stats["false_security_reject"] = review["false_security_reject"]
    stats["missed_opportunity_validated"] = review["missed_opportunity"]
    stats["rejected_review_pending"] = review["review_pending"]
    stats["rejected_not_reviewable"] = review["not_reviewable"]
    stats["lessons_recorded"] = c("SELECT COUNT(*) FROM post_trade_lesson")
    stats["note"] = ("counters recomputed from append-only tables each cycle; "
                     "one trade never changes a frozen rule; improvements require accumulated evidence")
    return stats


def snapshot_stats(paper, discovery, ts: float | None = None) -> dict:
    ts = time.time() if ts is None else ts
    stats = learning_stats(paper, discovery)
    paper.execute("INSERT INTO learning_stats_snapshot(ts,stats_json,created_utc) VALUES (?,?,?)",
                  (ts, _j(stats), _utc(time.time())))
    paper.commit()
    return stats
