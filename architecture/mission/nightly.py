"""M31 / M35.4 nightly paper report. A short sample is not a profit claim."""
from __future__ import annotations


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
