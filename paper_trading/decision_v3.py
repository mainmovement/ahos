#!/usr/bin/env python3
"""Paper Trading Lab — EXIT DECISION ENGINE v3 (PT-X3-v1, Wave-8 continuation §1/§5/§6/§7/§8).

Owner-mandated management upgrade, EFFECTIVE forward-only from 2026-08-12T08:20Z for ALL open
v2 positions (register R-26): X2/X1 triggers are inherited untouched; v3 ADDS:
  E0  exitability gate first       — "can this actually be exited NOW?" prices every decision
  E8  scam/rug escalation set      — security recheck flip / liq−50% / divergence (X2) unchanged
  A   trapped test on realizable   — realizable < 10% of allocated ⇒ TRAPPED/TOTAL_LOSS even if
                                      displayed looks rich (mark-price fiction stays banned)
  B   DIVERGENCE_PROFIT_LOCK (§6)  — displayed ≥ DIVERGENCE_DISPLAYED_MULT × allocated AND
                                      realizable ≥ DIVERGENCE_REALIZABLE_MULT × allocated
                                      ⇒ take the REAL money now (apparent gain largely illusory)
  C   DECAY_PROFIT_LOCK            — realizable ≥ DECAY_LOCK_MULT × allocated AND price ≤
                                      (1−DECAY_DRAWDOWN) × observed monitor peak ⇒ bank the
                                      realizable profit instead of round-tripping it
  §7  PARTIAL exits                — liquidity-capped chunks; remainder monitored independently
Priority (deterministic, worst-case-first): SECURITY/veto(→RISK or TRAP) · TRAPPED/TOTAL_LOSS ·
LIQUIDITY_COLLAPSE · risk-escalation EXIT_RISK · inherited TP/SL/TIME · DIVERGENCE_PROFIT_LOCK ·
DECAY_PROFIT_LOCK · HOLD.  §5 probability fields are recorded as NOT_ESTIMABLE (frozen law);
momentum/news/etc. are categorical evidence classes, never numeric scores.
"""
from __future__ import annotations

from . import cost_model as cm
from . import realizable as rz
from .exit_rules import EXIT_V1 as _BASE_LAW

EXIT_V3 = {
    "version": "PT-X3-v1",
    "created": "2026-08-12",
    "inherits": "PT-X2-v2 ⇒ PT-X1-v1 (TP50/SL35/48h/liq-collapse 2x<2000/SL-first/6h freshness/"
                "escalations/trapped-model)",
    "additions": {
        "exitability_gate_first": "every exit decision priced through PT-REALIZABLE-v1",
        "partial_exits": {"min_partial_notional_usd": rz.MIN_PARTIAL_NOTIONAL_USD,
                          "cap": "impact ≤ 1500bps per chunk (inherits entry gate)"},
        "divergence_profit_lock": {"displayed_mult": 3.0, "realizable_mult": 2.0},
        "decay_profit_lock": {"realizable_mult": 1.5, "drawdown_from_monitor_peak": 0.15,
                              "min_monitor_obs": 2},
        "trapped_test": "on realizable-after-all-costs (incl. MODEL gas)",
        "probability_fields": "NOT_ESTIMABLE (no-probability law) — categorical only",
    },
    "effective_utc": "2026-08-12T08:20:00Z (forward-only; prior X2 decisions unmodified)",
    "superseded_by": "PT-X3-v2 (freshness gate added 2026-08-13; v1 rows/card immutable)",
}

# PT-X3-v2 (R-C3 closure, owner-authorized 2026-08-13): identical thresholds and branch order
# as v1; the ONLY change is the stale-observation law made structural. A stale observation
# (>6h at decision time, inherited PT-X1-v1 constant) must NEVER be the basis of an exit,
# settlement or realizable realization: market-price-derived branches convert to NO_DATA
# (nothing priced) or INVALID (a base trigger fired but is unpriceable — inherited X1 law).
# Price-INDEPENDENT closes stay allowed: confirmed honeypot / confirmed unexitsable mean
# recoverable 0 by contract evidence, no price is consulted.
EXIT_V32 = {
    "version": "PT-X3-v2",
    "created": "2026-08-13",
    "inherits": "PT-X3-v1 identical thresholds, branch order, constants",
    "additions": {"stale_observation_law":
                  "obs_age > exit_reference_max_age_sec ⇒ trapped/divergence/decay/risk-exit/"
                  "realizable-realization FORBIDDEN → NO_DATA (or INVALID via base law); "
                  "CONFIRMED_HONEYPOT/CONFIRMED_UNEXITSABLE closes remain (price-independent)",
                  "gate_rationale": "R-29 ADJACENT anomaly (16–17.7h stale obs reached decisions; "
                                    "zero contamination) — hole closed before it could fire",
                  "evidence": "AHOS_ISSUE_REGISTER R-29; tests test_paper_trading_v32.py"},
    "effective_utc": "2026-08-13T01:05:00Z (forward-only)",
}
STALE_MAX_AGE_SEC = _BASE_LAW["exit_reference_max_age_sec"]
PRICE_INDEPENDENT_CLOSE = ("CONFIRMED_HONEYPOT", "CONFIRMED_UNEXITSABLE")
DIVERGENCE_DISPLAYED_MULT = 3.0
DIVERGENCE_REALIZABLE_MULT = 2.0
DECAY_LOCK_MULT = 1.5
DECAY_DRAWDOWN = 0.15
DECAY_MIN_OBS = 2
MOMENTUM_BAND = 0.10            # ±10% vs previous monitor obs ⇒ IMPROVING / DETERIORATING
MEANINGFUL_RECOVERY_FRAC = 0.10  # inherits PT-X2-v2 (risk.MEANINGFUL_RECOVERY_FRAC)


def momentum_class(prev_price: float | None, cur_price: float | None) -> str:
    if prev_price is None or cur_price is None or prev_price <= 0:
        return "UNKNOWN"
    chg = cur_price / prev_price - 1.0
    if chg >= MOMENTUM_BAND:
        return "IMPROVING"
    if chg <= -MOMENTUM_BAND:
        return "DETERIORATING"
    return "FLAT"


def liquidity_risk(liq_now: float | None, floor: float = 2_000.0) -> str:
    if liq_now is None or liq_now <= 0:
        return "UNKNOWN"
    if liq_now < floor:
        return "COLLAPSED"
    if liq_now < 25_000:
        return "THIN"
    return "OK"


def trapped_test(allocated: float, realizable_now: float) -> tuple[str | None, str]:
    """Trapped determination on FULLY-COSTED realizable value (directive §2 example math)."""
    if realizable_now <= 1e-12:
        return "TOTAL_LOSS", f"realizable {realizable_now:.4f} ≈ 0 — exit void"
    if realizable_now < allocated * MEANINGFUL_RECOVERY_FRAC:
        return "TRAPPED", (f"realizable {realizable_now:.4f} < "
                           f"{MEANINGFUL_RECOVERY_FRAC:.0%} of allocated {allocated:.2f}")
    return None, "exit meaningful"


def stale(now: float, obs_ts: float | None) -> bool:
    """PT-X3-v2 structural freshness law: obs older than the inherited 6h constant is STALE."""
    return obs_ts is None or (now - obs_ts) > STALE_MAX_AGE_SEC


def decide(*, now: float, allocated: float, qty_remaining: float, entry_price_exec: float,
           entry_ts: float, obs_price: float | None, obs_liq: float | None, obs_ts: float | None,
           consec_liq_breaches: int, sec_veto_now: bool, escalations: list[str],
           sell_tax_bps: float | None, chain: str, classification: str,
           monitor_peak_price: float | None, monitor_obs_count: int,
           base_hit: dict | None, fee_bps: float = cm.FEE_BPS) -> dict:
    """PT-X3-v2: stale-observation gate FIRST, then byte-identical v1 logic on fresh data."""
    if stale(now, obs_ts):
        a = rz.assess(qty=qty_remaining, price_obs=obs_price, liq_now=obs_liq,
                      sell_tax_bps=sell_tax_bps, chain=chain, classification=classification,
                      fee_bps=fee_bps)
        if classification in PRICE_INDEPENDENT_CLOSE:
            # contract evidence says recoverable = 0 without consulting any price
            return {"action": "TOTAL_LOSS", "reason": "TOTAL_LOSS", "assess": a, "kind": "FULL",
                    "price_independent": True,
                    "why": f"{classification} — recoverable 0 by contract evidence (no price used; "
                           f"obs age exempt by design: price-independent close)"}
        if base_hit is not None and base_hit["reason"].startswith("INVALID"):
            return {"action": "INVALID", "reason": base_hit["reason"], "assess": a, "kind": "FULL",
                    "price_independent": False, "why": base_hit.get("detail", base_hit["reason"])}
        age_h = "None" if obs_ts is None else f"{(now - obs_ts)/3600:.2f}h"
        return {"action": "NO_DATA", "reason": "STALE_OBSERVATION", "assess": a, "kind": "NONE",
                "price_independent": False,
                "why": (f"obs age {age_h} > {STALE_MAX_AGE_SEC/3600:.0f}h freshness law — "
                        "stale observation may never ground exit/settlement/realizable realization "
                        "(PT-X3-v2, R-C3 closure); monitoring continues, nothing priced")}
    return decide_v1(now=now, allocated=allocated, qty_remaining=qty_remaining,
                     entry_price_exec=entry_price_exec, entry_ts=entry_ts, obs_price=obs_price,
                     obs_liq=obs_liq, obs_ts=obs_ts, consec_liq_breaches=consec_liq_breaches,
                     sec_veto_now=sec_veto_now, escalations=escalations, sell_tax_bps=sell_tax_bps,
                     chain=chain, classification=classification,
                     monitor_peak_price=monitor_peak_price, monitor_obs_count=monitor_obs_count,
                     base_hit=base_hit, fee_bps=fee_bps)


def decide_v1(*, now: float, allocated: float, qty_remaining: float, entry_price_exec: float,
           entry_ts: float, obs_price: float | None, obs_liq: float | None, obs_ts: float | None,
           consec_liq_breaches: int, sec_veto_now: bool, escalations: list[str],
           sell_tax_bps: float | None, chain: str, classification: str,
           monitor_peak_price: float | None, monitor_obs_count: int,
           base_hit: dict | None, fee_bps: float = cm.FEE_BPS) -> dict:
    """IMMUTABLE PT-X3-v1 logic (frozen 2026-08-12; reachable only via the v2 freshness gate).

    `base_hit` = exit_rules.check_exits(...) result under inherited PT-X1-v1 numbers (may embed
    SECURITY_EVENT / LIQUIDITY_COLLAPSE / STOP_LOSS / TAKE_PROFIT / TIME_EXIT / INVALID_*).
    """
    a = rz.assess(qty=qty_remaining, price_obs=obs_price, liq_now=obs_liq,
                  sell_tax_bps=sell_tax_bps, chain=chain, classification=classification,
                  fee_bps=fee_bps)
    route = a["route_status"]
    realizable = a["realizable_value_usd"] or 0.0
    displayed = a["displayed_value_usd"] or 0.0

    # 1) confirmed sells-blocked ⇒ money is gone regardless of displayed price (§2/§8)
    if route == "UNEXITABLE_HONEYPOT":
        return {"action": "TOTAL_LOSS", "reason": "TOTAL_LOSS", "assess": a, "kind": "FULL",
                "why": "confirmed honeypot — recoverable 0 by evidence"}

    # 2) unpriceable ⇒ NO_DATA (v2 law mirror: UNKNOWN is never converted into a TRAP guess)
    if route in ("UNEXITABLE_NO_PRICE", "UNEXITABLE_NO_LIQUIDITY"):
        return {"action": "NO_DATA", "reason": "NO_DATA", "assess": a, "kind": "NONE",
                "why": a["why"] + " — UNKNOWN stays UNKNOWN; no exit forced, no trap guessed"}

    # routes from here are priced: EXECUTABLE_* | SECURITY_RECHECK_CRITICAL | UNEXITABLE_DUST
    # 3) trapped test on FULLY-COSTED realizable value (worst-case-first)
    trap, trap_why = trapped_test(allocated, realizable)
    if trap:
        return {"action": trap, "reason": trap, "assess": a, "kind": "FULL", "why": trap_why}

    # 4) security flipped post-entry but still sellable ⇒ leave NOW (§8: don't wait for collapse)
    veto_close = classification in ("CONFIRMED_RUG", "CONFIRMED_UNEXITSABLE", "CRITICAL_RISK")
    if veto_close or sec_veto_now:
        kind = rz.executable_chunk(a)["kind"]
        return {"action": "RISK_EXIT" if kind == "FULL" else "PARTIAL_EXIT",
                "reason": "SECURITY_EVENT", "assess": a, "kind": kind,
                "why": f"security state {classification} post-entry — exiting while executable"}

    # 5) inherited base triggers (LIQUIDITY_COLLAPSE / SL / TP / TIME / INVALID), SL-before-TP
    if base_hit is not None:
        r = base_hit["reason"]
        if r.startswith("INVALID"):
            return {"action": "INVALID", "reason": r, "assess": a, "kind": "FULL",
                    "why": base_hit.get("detail", r)}
        kind = rz.executable_chunk(a)["kind"]
        return {"action": "FULL_EXIT" if kind == "FULL" else "PARTIAL_EXIT",
                "reason": r, "assess": a, "kind": kind,
                "why": base_hit.get("detail", r)}

    if escalations:
        kind = rz.executable_chunk(a)["kind"]
        return {"action": "RISK_EXIT" if kind == "FULL" else "PARTIAL_EXIT",
                "reason": "EXIT_RISK", "assess": a, "kind": kind,
                "why": "escalation: " + " | ".join(escalations)}

    if (displayed >= DIVERGENCE_DISPLAYED_MULT * allocated
            and realizable >= DIVERGENCE_REALIZABLE_MULT * allocated):
        kind = rz.executable_chunk(a)["kind"]
        return {"action": "FULL_EXIT" if kind == "FULL" else "PARTIAL_EXIT",
                "reason": "DIVERGENCE_PROFIT_LOCK", "assess": a, "kind": kind,
                "why": (f"displayed {displayed:.2f} ≥ {DIVERGENCE_DISPLAYED_MULT}×alloc but only "
                        f"{realizable:.2f} real — take real value (≥{DIVERGENCE_REALIZABLE_MULT}×alloc)")}

    if (monitor_obs_count >= DECAY_MIN_OBS and monitor_peak_price and obs_price is not None
            and realizable >= DECAY_LOCK_MULT * allocated
            and obs_price <= monitor_peak_price * (1 - DECAY_DRAWDOWN)):
        kind = rz.executable_chunk(a)["kind"]
        return {"action": "FULL_EXIT" if kind == "FULL" else "PARTIAL_EXIT",
                "reason": "DECAY_PROFIT_LOCK", "assess": a, "kind": kind,
                "why": (f"realizable {realizable:.2f} ≥ {DECAY_LOCK_MULT}×alloc but price "
                        f"{obs_price:.6g} ≤ {1-DECAY_DRAWDOWN:.0%}×peak {monitor_peak_price:.6g}")}

    return {"action": "HOLD", "reason": "HOLD", "assess": a, "kind": "NONE",
            "why": "no trigger fired; monitoring continues (no hold-by-default inertia claimed)"}
