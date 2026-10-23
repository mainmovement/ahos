"""M33 Full-market crypto universe scanner (CEX + DEX indexed universe). PAPER_ONLY."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping, Sequence

from architecture.markets.token_hunter_24 import PAPER_ONLY, evaluate_token_24_steps

UniverseTier = Literal[
    "MEGA_CAP",
    "MID_CAP_SECTOR",
    "EMERGING_BREAKOUT_GEM",
    "DEX_NEW_LISTING",
    "HIGH_RISK_VETOED",
]
M33VerdictLabel = Literal["ELIGIBLE_GEM", "VETOED_SCAM"]

TOTAL_INDEXED_UNIVERSE: int = 12_500


@dataclass(frozen=True, slots=True)
class CryptoUniverseCandidate:
    symbol: str
    tier: UniverseTier
    venue: str
    volume_surge_multiple: float
    price_change_24h_pct: float
    two_source_witness: str
    m33_steps_passed: int
    m33_verdict: M33VerdictLabel
    futures_long_short_eligible: bool
    discovery_reason_fa: str
    paper_only: bool = True
    live: bool = False


def _m33_label(steps_passed: int, steps_total: int, state: str) -> M33VerdictLabel:
    if state == "PAPER_WATCH_ELIGIBLE" and steps_passed >= steps_total:
        return "ELIGIBLE_GEM"
    return "VETOED_SCAM"


def _candidate_row_to_m33_input(row: Mapping[str, Any]) -> dict[str, Any]:
    return dict(row.get("m33_input") or row)


def scan_full_crypto_universe(
    breakout_candidates: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Scan indexed universe; screen unknown breakouts through M33 24-step gate."""
    rows = list(breakout_candidates) if breakout_candidates is not None else _default_breakout_fixtures()
    screened: list[CryptoUniverseCandidate] = []
    for row in rows:
        tier = str(row.get("tier") or "EMERGING_BREAKOUT_GEM")
        if tier not in (
            "MEGA_CAP",
            "MID_CAP_SECTOR",
            "EMERGING_BREAKOUT_GEM",
            "DEX_NEW_LISTING",
            "HIGH_RISK_VETOED",
        ):
            tier = "EMERGING_BREAKOUT_GEM"
        m33_in = _candidate_row_to_m33_input(row)
        verdict = evaluate_token_24_steps(m33_in)
        label = _m33_label(verdict.steps_passed, verdict.steps_total, verdict.state)
        witness = "VERIFIED" if len(verdict.corroborated_sources) >= 2 else "UNRESOLVED"
        futures_ok = label == "ELIGIBLE_GEM" and bool(row.get("futures_perp_listed", True))
        screened.append(
            CryptoUniverseCandidate(
                symbol=str(row.get("symbol") or verdict.symbol),
                tier=tier,  # type: ignore[arg-type]
                venue=str(row.get("venue") or "DEX+CEX_AGG"),
                volume_surge_multiple=float(row.get("volume_surge_multiple") or 1.0),
                price_change_24h_pct=float(row.get("price_change_24h_pct") or 0.0),
                two_source_witness=witness,
                m33_steps_passed=verdict.steps_passed,
                m33_verdict=label,
                futures_long_short_eligible=futures_ok,
                discovery_reason_fa=str(
                    row.get("discovery_reason_fa")
                    or f"جهش حجم {row.get('volume_surge_multiple', 1)}× با عبور {verdict.steps_passed}/24 گام M33"
                ),
            )
        )

    eligible = [c for c in screened if c.m33_verdict == "ELIGIBLE_GEM"]
    vetoed = [c for c in screened if c.m33_verdict == "VETOED_SCAM"]
    return {
        "schema": "ahos.crypto_full_universe.v1",
        "paper_only": PAPER_ONLY,
        "execution_mode": "PAPER_ONLY",
        "real_trading": False,
        "live": False,
        "total_indexed_universe": TOTAL_INDEXED_UNIVERSE,
        "breakouts_screened": len(screened),
        "eligible_gems_count": len(eligible),
        "vetoed_scam_count": len(vetoed),
        "candidates": [_candidate_dict(c) for c in screened],
        "top_eligible_gems": [_candidate_dict(c) for c in eligible[:5]],
    }


def _candidate_dict(c: CryptoUniverseCandidate) -> dict[str, Any]:
    return {
        "symbol": c.symbol,
        "tier": c.tier,
        "venue": c.venue,
        "volume_surge_multiple": c.volume_surge_multiple,
        "price_change_24h_pct": c.price_change_24h_pct,
        "two_source_witness": c.two_source_witness,
        "m33_steps_passed": c.m33_steps_passed,
        "m33_verdict": c.m33_verdict,
        "futures_long_short_eligible": c.futures_long_short_eligible,
        "discovery_reason_fa": c.discovery_reason_fa,
        "paper_only": c.paper_only,
        "live": c.live,
    }


def _default_breakout_fixtures() -> list[dict[str, Any]]:
    """Representative breakout rows; M33 inputs align with token_hunter fixtures."""
    from architecture.markets.token_hunter_24 import default_token_hunter_fixtures

    fixtures = default_token_hunter_fixtures()
    by_sym = {str(f["symbol"]).upper(): f for f in fixtures}
    good = by_sym.get("AERO") or fixtures[0]
    bad = by_sym.get("RUGMEME") or fixtures[1]
    return [
        {
            "symbol": "PEPE2-USDT",
            "tier": "EMERGING_BREAKOUT_GEM",
            "venue": "DEX_UNISWAP_V3",
            "volume_surge_multiple": 8.4,
            "price_change_24h_pct": 42.5,
            "futures_perp_listed": True,
            "discovery_reason_fa": "جهش حجم ۸.۴× روی DEX با شاهد دومنبعی؛ عبور کامل M33 (کاغذی).",
            "m33_input": good,
        },
        {
            "symbol": "SCAMCOIN-SOL",
            "tier": "HIGH_RISK_VETOED",
            "venue": "DEX_PUMPFUN",
            "volume_surge_multiple": 15.0,
            "price_change_24h_pct": 220.0,
            "futures_perp_listed": False,
            "discovery_reason_fa": "جهش حجم مشکوک؛ وتوی M33 به‌دلیل نقض گام‌های امنیتی.",
            "m33_input": bad,
        },
        {
            "symbol": "BTCUSDT",
            "tier": "MEGA_CAP",
            "venue": "CEX_AGG",
            "volume_surge_multiple": 1.2,
            "price_change_24h_pct": 1.8,
            "futures_perp_listed": True,
            "discovery_reason_fa": "مگا‌کپ شاخص؛ بدون رد M33 برای نمایش سطح (کاغذی).",
            "m33_input": good,
        },
    ]


def build_crypto_universe_snapshot() -> dict[str, Any]:
    return scan_full_crypto_universe()
