"""M31 / M35.4 nightly paper report. A short sample is not a profit claim."""
from __future__ import annotations

from typing import Any, Mapping


def render(*, day: str, trades: int, pnl_usd: float) -> str:
    verdict = "NO_PROVEN_EDGE" if trades < 30 else "SAMPLE_ONLY"
    return (
        f"# Nightly {day}\n"
        f"trades: {trades}\n"
        f"paper_pnl_usd: {pnl_usd}\n"
        f"verdict: {verdict}\n"
        "live: false\n"
    )


def render_fa(*, day: str, trades: int, pnl_usd: float) -> str:
    body = render(day=day, trades=trades, pnl_usd=pnl_usd)
    return body + "یادداشت: این عدد کاغذی است و سود ثابت‌شده نیست.\n"


def _witness_verified_count(multi_market: Mapping[str, Any]) -> int:
    if "verified_instruments" in multi_market:
        return int(multi_market["verified_instruments"])
    instruments = multi_market.get("instruments") or ()
    return sum(1 for row in instruments if row.get("witness_state") == "VERIFIED")


def build_comprehensive_nightly_digest_fa(
    *,
    day: str,
    trades: int,
    pnl_usd: float,
    gold_soak: Mapping[str, Any] | None = None,
    oil_soak: Mapping[str, Any] | None = None,
    multi_market: Mapping[str, Any] | None = None,
    tournament: Mapping[str, Any] | None = None,
    astra: Mapping[str, Any] | None = None,
) -> str:
    """Persian executive digest for M31/M35.4 (backward-compatible; optional snapshot inputs)."""
    base = render_fa(day=day, trades=trades, pnl_usd=pnl_usd)

    if multi_market is None:
        from architecture.markets.multi_market_desks import DESK_SPECS, evaluate_all_desks

        cycles = evaluate_all_desks()
        multi_market = {
            "desks_count": len(DESK_SPECS),
            "verified_instruments": sum(1 for c in cycles if c.witness.state == "VERIFIED"),
        }
    if tournament is None:
        from architecture.learning.strategy_tournament import run_strategy_tournament

        tournament = run_strategy_tournament()
    if astra is None:
        from pathlib import Path

        from architecture.learning.astra_engine import run_astra_evolution_cycle

        astra = run_astra_evolution_cycle(root=Path(__file__).resolve().parents[2])

    gold_status = str((gold_soak or {}).get("status") or (gold_soak or {}).get("overall_status") or "UNKNOWN")
    oil_status = str((oil_soak or {}).get("status") or (oil_soak or {}).get("overall_status") or "UNKNOWN")
    desks_n = int(multi_market.get("desks_count") or 7)
    verified_n = _witness_verified_count(multi_market)
    leader = tournament.get("leader_title") or tournament.get("leader_id") or "—"
    leader_dsr = tournament.get("leader_dsr")
    astra_status = str(astra.get("overall_status") or astra.get("shadow_status") or "UNKNOWN")

    lines = [
        "",
        "## خلاصهٔ اجرایی شبانه (M31 · M35.4)",
        f"- طلا (M13): وضعیت ساک {gold_status} — فقط کاغذی.",
        f"- نفت (M13.1): وضعیت ساک {oil_status} — فقط کاغذی.",
        f"- میزهای M19: {verified_n} نماد با شاهد VERIFIED از {desks_n} میز (قانون دو منبع).",
        f"- تورنمنت M56: پیشتاز «{leader}»" + (f" (DSR={leader_dsr})" if leader_dsr is not None else "") + ".",
        f"- آسترا M60: وضعیت سایه {astra_status} — بدون ارتقای زنده.",
        "- یادآوری: نمونهٔ کوتاه ≠ لبهٔ ثابت‌شده؛ live=false.",
    ]
    return base + "\n".join(lines) + "\n"
