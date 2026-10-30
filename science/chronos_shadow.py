"""Lazy Chronos-Bolt hook. Weights are not downloaded. Moirai is refused."""
from __future__ import annotations

from typing import Any

from science.memory import peak_rss_mb


def load_model() -> None:
    """Do not fetch weights. A missing package stays missing."""
    return None


def run_shadow() -> dict[str, Any]:
    model = load_model()
    return {
        "id": "M9-12",
        "state": "OPEN",
        "library": "chronos-bolt-tiny",
        "license": "Apache-2.0",
        "library_present": model is not None,
        "moirai": "REFUSED_CC_BY_NC",
        "reason": "WEIGHTS_NOT_LOADED",
        "crps": None,
        "metric": "crps_better_than_baseline",
        "observed": None,
        "threshold": 1,
        "threshold_met_on_fixture": False,
        "promoted": False,
        "cpu_only": True,
        "peak_mb": peak_rss_mb(),
        "applied_to_live": False,
    }
