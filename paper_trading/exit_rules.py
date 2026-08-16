#!/usr/bin/env python3
"""Paper Trading Lab — EXIT RULES. All thresholds known BEFORE outcomes are observed.

PT-X1-v1 (locked 2026-08-12). Priority order is deterministic and conservative:
  1 SECURITY_EVENT   — new CRITICAL veto evidence after entry
  2 LIQUIDITY_COLLAPSE — liquidity < LIQ_FLOOR on LIQ_CONSEC consecutive monitor observations
  3 STOP_LOSS        — conservative tie-break: if an observation gap could contain BOTH TP and SL,
                       SL is assumed first (worst-case honesty, never best-case)
  4 TAKE_PROFIT
  5 TIME_EXIT        — fixed horizon; if no observation exists to reconstruct an exit price,
                       the trade is INVALIDATED (price unreconstructable), evidence preserved.
"""
from __future__ import annotations

EXIT_V1 = {
    "version": "PT-X1-v1",
    "created": "2026-08-12",
    "take_profit_pct": 0.50,
    "stop_loss_pct": 0.35,
    "max_hold_hours": 48.0,
    "liq_collapse_floor_usd": 2_000.0,
    "liq_collapse_consecutive": 2,
    "sl_first_on_gap_ambiguity": True,
    "time_exit_requires_observation": True,
    "exit_reference_max_age_sec": 21_600,   # exit may only be priced on obs ≤6h old at exit time;
                                            # else INVALID_DATA_UNAVAILABLE (never a stale-price exit)
}


def check_exits(*, entry_exec: float, entry_ts: float, now: float,
                obs_price: float | None, obs_liq: float | None, obs_ts: float | None,
                consec_liq_breaches: int, security_recheck: dict | None,
                cfg: dict = EXIT_V1) -> dict | None:
    """Returns None (keep monitoring) or {reason, urgency} using ONLY data ≤ now.
    `consec_liq_breaches` counts consecutive breach observations INCLUDING the current one."""
    price_usable = (obs_price is not None and obs_ts is not None
                    and (now - obs_ts) <= cfg["exit_reference_max_age_sec"])
    if security_recheck and security_recheck.get("verdict") == "SECURITY_VETO":
        if not price_usable:
            return {"reason": "INVALID_DATA_UNAVAILABLE",
                    "detail": "SECURITY_EVENT but no fresh observation to price the exit honestly"}
        return {"reason": "SECURITY_EVENT",
                "detail": "veto after entry: " + ",".join(security_recheck.get("veto_reasons", []))}
    if obs_liq is not None and obs_liq < cfg["liq_collapse_floor_usd"]:
        if consec_liq_breaches >= cfg["liq_collapse_consecutive"]:
            if not price_usable:
                return {"reason": "INVALID_DATA_UNAVAILABLE",
                        "detail": "LIQUIDITY_COLLAPSE but no fresh observation to price the exit"}
            return {"reason": "LIQUIDITY_COLLAPSE",
                    "detail": f"liq {obs_liq:.0f} < floor {cfg['liq_collapse_floor_usd']:.0f} x{consec_liq_breaches}"}
    if price_usable:
        tp = entry_exec * (1 + cfg["take_profit_pct"])
        sl = entry_exec * (1 - cfg["stop_loss_pct"])
        if obs_price <= sl:
            return {"reason": "STOP_LOSS", "detail": f"price {obs_price:.6g} <= SL {sl:.6g}"}
        if obs_price >= tp:
            return {"reason": "TAKE_PROFIT", "detail": f"price {obs_price:.6g} >= TP {tp:.6g}"}
    if now >= entry_ts + cfg["max_hold_hours"] * 3600:
        if not price_usable:
            return {"reason": "INVALID_DATA_UNAVAILABLE",
                    "detail": "horizon reached but no observation within "
                              f"{cfg['exit_reference_max_age_sec']}s to reconstruct an honest exit price"}
        return {"reason": "TIME_EXIT", "detail": f"horizon {cfg['max_hold_hours']:.0f}h reached"}
    return None


# ---------------------------------------------------------------- Wave-8 experiment
EXIT_V2 = {
    "version": "PT-X2-v2",
    "created": "2026-08-12",
    "inherits": "PT-X1-v1 (TP 50% / SL 35% / time 48h / liq-collapse 2x<2000 / SL-first / 6h freshness)",
    "take_profit_pct": 0.50, "stop_loss_pct": 0.35, "max_hold_hours": 48.0,
    "liq_collapse_floor_usd": 2_000.0, "liq_collapse_consecutive": 2,
    "sl_first_on_gap_ambiguity": True, "time_exit_requires_observation": True,
    "exit_reference_max_age_sec": 21_600,
    "additions": {
        "risk_escalation_rules": ["security recheck flips to CONFIRMED_*/CRITICAL_RISK",
                                  "liquidity halves vs entry", "price x2 while liq halves (divergence)"],
        "exit_risk": "on escalation: if sellable, exit immediately at modeled executable value",
        "trapped_model": "recoverable < 10% of allocated (or unmodelable) => TRAPPED/TOTAL_LOSS; "
                         "capital_loss = allocated - recoverable; never mark-price fiction",
        "meaningful_recovery_frac": 0.10,
    },
}

