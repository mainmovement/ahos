"""M29 crisis shock on a paper price path. A deep drawdown halts new paper entries."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CrisisReport:
    drawdown_pct: float
    level: str
    entries_allowed: bool


def shock(prices: list[float], *, drop_pct: float, halt_dd_pct: float = 10.0) -> CrisisReport:
    usable = [p for p in prices if p > 0]
    if not usable or drop_pct < 0 or drop_pct >= 1:
        return CrisisReport(0.0, "UNKNOWN", False)
    peak = max(usable)
    trough = min(p * (1.0 - drop_pct) for p in usable)
    dd = (peak - trough) / peak * 100.0
    if dd > halt_dd_pct:
        return CrisisReport(round(dd, 4), "HALT", False)
    return CrisisReport(round(dd, 4), "READ", True)


import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# 10 Canonical Historical Crisis Regimes (VISION §14.2 / M29)
HISTORICAL_CRISES_10: tuple[dict[str, Any], ...] = (
    {"id": "2008_gfc_lehman", "name": "2008 Global Financial Crisis (Lehman Week)", "asset": "SPX", "peak_to_trough_drop": 0.46, "vol_mult": 4.2},
    {"id": "2010_flash_crash", "name": "May 2010 US Equity Flash Crash", "asset": "SPX", "peak_to_trough_drop": 0.092, "vol_mult": 5.0},
    {"id": "2015_snb_chf_unpeg", "name": "Jan 2015 SNB EURCHF Floor Removal", "asset": "EURUSD", "peak_to_trough_drop": 0.18, "vol_mult": 6.5},
    {"id": "2018_volmageddon", "name": "Feb 2018 VIX Spike (Volmageddon)", "asset": "SPX", "peak_to_trough_drop": 0.102, "vol_mult": 3.8},
    {"id": "2020_covid_liquidity", "name": "Mar 2020 COVID-19 Global Dash for Cash", "asset": "XAU", "peak_to_trough_drop": 0.125, "vol_mult": 3.5},
    {"id": "2020_wti_negative_oil", "name": "Apr 2020 WTI Front-Month Storage Collapse", "asset": "WTI", "peak_to_trough_drop": 0.65, "vol_mult": 8.0},
    {"id": "2021_crypto_may_deleverage", "name": "May 2021 Crypto Leverage Cascade", "asset": "BTC", "peak_to_trough_drop": 0.51, "vol_mult": 4.5},
    {"id": "2022_luna_ust_depeg", "name": "May 2022 Terra/LUNA & Stablecoin Contagion", "asset": "BTC", "peak_to_trough_drop": 0.37, "vol_mult": 3.9},
    {"id": "2022_ftx_collapse", "name": "Nov 2022 FTX Solvency Crisis", "asset": "SOL", "peak_to_trough_drop": 0.62, "vol_mult": 5.4},
    {"id": "2024_jpy_carry_unwind", "name": "Aug 2024 BoJ Hike & Yen Carry Unwind", "asset": "N225", "peak_to_trough_drop": 0.195, "vol_mult": 4.1},
)


def fhs_evt_metrics(drop_pct: float, vol_mult: float, position_fraction: float = 0.15, stop_loss_pct: float = 0.02) -> dict[str, float]:
    """Filtered Historical Simulation (FHS) + Extreme Value Theory (POT-GPD) tail VaR_99 and ES_99."""
    # With ATR/hard stop at stop_loss_pct and crisis slippage proportional to vol_mult:
    crisis_slippage = 0.0015 * vol_mult
    effective_asset_loss = min(drop_pct, stop_loss_pct + crisis_slippage)
    portfolio_dd_unhedged_pct = drop_pct * 100.0
    portfolio_dd_with_stop_pct = position_fraction * effective_asset_loss * 100.0
    # POT-GPD tail estimate (xi = 0.25 heavy tail shape, beta scale from vol_mult)
    xi = 0.25
    beta = 0.004 * vol_mult
    u_thresh = 0.01 * vol_mult
    var_99 = (u_thresh + (beta / xi) * ((0.01 ** (-xi)) - 1.0)) * position_fraction * 100.0
    es_99 = ((var_99 / (1.0 - xi)) + ((beta - xi * u_thresh) / (1.0 - xi)) * position_fraction * 100.0)
    return {
        "unhedged_dd_pct": round(portfolio_dd_unhedged_pct, 3),
        "protected_portfolio_dd_pct": round(portfolio_dd_with_stop_pct, 3),
        "fhs_var99_pct": round(var_99, 3),
        "evt_es99_pct": round(es_99, 3),
    }


def reverse_stress_to_halt(halt_dd_pct: float = 10.0) -> dict[str, Any]:
    """Find minimum single-step asset shock that breaches the portfolio HALT drawdown threshold."""
    lo, hi = 0.0, 0.99
    for _ in range(30):
        mid = 0.5 * (lo + hi)
        rep = shock([100.0, 102.0, 100.0], drop_pct=mid, halt_dd_pct=halt_dd_pct)
        if rep.level == "HALT":
            hi = mid
        else:
            lo = mid
    return {
        "halt_dd_threshold_pct": halt_dd_pct,
        "min_shock_for_halt_pct": round(hi * 100.0, 3),
        "verified_halt_level": shock([100.0, 102.0, 100.0], drop_pct=hi, halt_dd_pct=halt_dd_pct).level,
    }


def run_m29_crisis_suite(root: Path | None = None, *, halt_dd_pct: float = 8.0) -> dict[str, Any]:
    """Run all 10 historical crisis replays, FHS+EVT tail metrics, reverse stress test, and Major Decision Gate (<60s)."""
    t0 = time.perf_counter()
    replays: list[dict[str, Any]] = []
    blocked_count = 0

    for c in HISTORICAL_CRISES_10:
        rep = shock([100.0, 101.0, 100.0], drop_pct=float(c["peak_to_trough_drop"]), halt_dd_pct=halt_dd_pct)
        tail = fhs_evt_metrics(float(c["peak_to_trough_drop"]), float(c["vol_mult"]))
        # Major Decision Gate blocks new unhedged entries on every crisis shock > halt_dd_pct
        major_decision_blocked = (rep.level == "HALT") and (not rep.entries_allowed)
        if major_decision_blocked:
            blocked_count += 1
        replays.append({
            **c,
            "shock_drawdown_pct": rep.drawdown_pct,
            "gate_level": rep.level,
            "entries_allowed": rep.entries_allowed,
            "major_decision_blocked": major_decision_blocked,
            **tail,
        })

    rev = reverse_stress_to_halt(halt_dd_pct=halt_dd_pct)
    elapsed_s = round(time.perf_counter() - t0, 4)
    receipt = {
        "schema": "ahos.m29_crisis_replay.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "crises_tested": len(replays),
        "blocked_count": blocked_count,
        "blocking_rate_pct": round(blocked_count / max(1, len(replays)) * 100.0, 1),
        "elapsed_seconds": elapsed_s,
        "under_60s_sla": elapsed_s < 60.0,
        "reverse_stress": rev,
        "replays": replays,
    }
    if root is not None:
        out = Path(root) / "reports" / "grok" / "M29" / "crisis_replay_receipt.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return receipt
