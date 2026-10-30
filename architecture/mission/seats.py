"""GOLD-SCI and GUARD-2 bound to modules that already have tests.

These seats are not new agents in the 43-agent registry. Adding ids there
would break the count the registry tests lock. Neither seat can promote.
"""
from __future__ import annotations

from architecture.intel.regimes import MarketRegimeClassifier
from architecture.markets.token_safety_live import MAX_SINGLE_HOLDER_PCT, MAX_TAX, veto_check

SEATS = {
    "GOLD-SCI": {
        "module": "architecture.intel.regimes",
        "callable": "MarketRegimeClassifier.predict_regime_probabilities",
        "authority": "OBSERVE",
        "applied_to_live_weights": False,
    },
    "GUARD-2": {
        "module": "architecture.markets.token_safety_live",
        "callable": "veto_check",
        "authority": "VETO_PAPER_TOKEN_ONLY",
        "max_wallet_pct": MAX_SINGLE_HOLDER_PCT,
        "max_tax": MAX_TAX,
        "applied_to_live_weights": False,
    },
}


def probe() -> dict[str, str]:
    """One real call per seat. A missing contract fail-closes without a network call."""
    regime = MarketRegimeClassifier().predict_regime_probabilities([0.01, 0.02, -0.05, 0.2, -0.2])
    veto = veto_check("MEGA7-SEAT-PROBE", address=None, strict=True)
    return {
        "GOLD-SCI": str(regime.get("active_regime")),
        "GUARD-2": str(veto.get("verdict")),
    }
