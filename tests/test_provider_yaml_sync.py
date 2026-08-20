#!/usr/bin/env python3
"""Month 2 roadmap: rate/breaker sync between the frozen PAL registry and the
architecture adapters.

`discovery/providers.yaml` is the binding PAL contract and is Lane-A frozen
(hash-pinned, never edited here). The acceptance criterion from ROADMAP_v3 §2:

    "Rate-limit registry sync with discovery/providers.yaml (PAL side stays
     frozen) — Cross-check test: no rate/breaker divergence between PAL yaml
     and architecture adapters."

Direction of the law (this test pins it): the architecture pipeline must never
be MORE aggressive than the frozen PAL contract for the same provider_id —
  * request rate  <= PAL's most conservative rpm budget for that provider;
  * breaker opens no later  (failure_threshold <= PAL's);
  * breaker recovers no sooner (recovery_timeout_sec >= PAL's cooldown_sec).

A divergence here means the architecture side would consume budget the PAL
contract does not grant, so the test fails loudly instead of degrading.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
PAL_YAML = ROOT / "discovery" / "providers.yaml"

from architecture.collector.engine import CollectorEngine
from architecture.providers.adapters import (
    DexScreenerAdapter,
    GeckoTerminalAdapter,
    GoPlusSecurityAdapter,
    RugCheckSecurityAdapter,
)


def _pal_contract() -> dict[str, dict]:
    """provider_id -> {'min_rpm', 'min_fail_threshold', 'max_cooldown_sec'}."""
    cfg = yaml.safe_load(PAL_YAML.read_text(encoding="utf-8"))
    by_provider: dict[str, list[dict]] = {}
    for entry in (cfg.get("providers") or {}).values():
        prov = (entry or {}).get("provider_id")
        if not prov:
            continue
        by_provider.setdefault(prov, []).append(entry)
    out = {}
    for prov, entries in by_provider.items():
        rpms = [e["rate"]["rpm"] for e in entries if (e.get("rate") or {}).get("rpm")]
        thresholds = [e["breaker"]["fail_threshold"]
                      for e in entries if (e.get("breaker") or {}).get("fail_threshold")]
        cooldowns = [e["breaker"]["cooldown_sec"]
                     for e in entries if (e.get("breaker") or {}).get("cooldown_sec")]
        out[prov] = {
            "min_rpm": min(rpms) if rpms else None,
            "min_fail_threshold": min(thresholds) if thresholds else None,
            "max_cooldown_sec": max(cooldowns) if cooldowns else None,
        }
    return out


CONTRACT = _pal_contract()


def _assert_rate_within_pal(provider_id: str, adapter) -> None:
    pal = CONTRACT.get(provider_id)
    assert pal is not None, f"{provider_id} missing from PAL providers.yaml"
    adapter_rpm = adapter._rate_limit_rps * 60.0
    assert adapter_rpm <= pal["min_rpm"], (
        f"{provider_id} architecture rate {adapter_rpm:.1f} rpm exceeds PAL "
        f"budget {pal['min_rpm']} rpm — align to the frozen registry, never edit PAL")


def test_dexscreener_rate_within_pal_budget():
    _assert_rate_within_pal("dexscreener", DexScreenerAdapter())


def test_geckoterminal_rate_within_pal_budget():
    _assert_rate_within_pal("geckoterminal", GeckoTerminalAdapter())


def test_goplus_rate_within_pal_budget():
    _assert_rate_within_pal("goplus", GoPlusSecurityAdapter())


def test_rugcheck_rate_within_pal_budget():
    _assert_rate_within_pal("rugcheck", RugCheckSecurityAdapter())


def test_rate_law_covers_every_adapted_pal_provider():
    """If the PAL registry defines a budget for a provider we adapt and the
    rate law does not yet cover it, fail loudly instead of silently skipping."""
    adapted = {"dexscreener", "geckoterminal", "goplus", "rugcheck"}
    for pid in adapted:
        assert pid in CONTRACT, f"PAL registry no longer defines {pid}"
    uncovered = sorted(adapted - set(CONTRACT))
    assert not uncovered, f"rate/breaker law refers to providers missing from PAL: {uncovered}"


def test_collector_breakers_never_more_aggressive_than_pal():
    engine = CollectorEngine(db_path=":memory:")
    for pid in ("dexscreener", "geckoterminal", "goplus", "rugcheck"):
        pal = CONTRACT[pid]
        cb = engine.circuit_breakers[pid]
        assert cb.config.failure_threshold <= pal["min_fail_threshold"], (
            f"{pid} opens after {cb.config.failure_threshold} failures; PAL "
            f"contract opens after {pal['min_fail_threshold']}")
        assert cb.config.recovery_timeout_sec >= pal["max_cooldown_sec"], (
            f"{pid} recovers after {cb.config.recovery_timeout_sec}s; PAL "
            f"contract cools down {pal['max_cooldown_sec']}s")


# ------------------------------------------------------- external ceilings
# Providers absent from the frozen PAL yaml still have documented external
# ceilings; the adapters must stay under them (same law, different source).

def test_coinmarketcap_rate_within_free_tier_ceiling():
    """CMC free tier = 30 credits/min (info + quotes are 1 credit each)."""
    from architecture.providers.coinmarketcap import CoinMarketCapAdapter
    adapter_rpm = CoinMarketCapAdapter()._rate_limit_rps * 60.0
    assert adapter_rpm <= 30.0, (
        f"coinmarketcap at {adapter_rpm:.1f} rpm exceeds CMC free-tier ceiling "
        f"of 30 credits/min")


def test_pumpfun_rate_is_conservative_undocumented_feed():
    """pump.fun frontend budget is undocumented -> conservative by law."""
    from architecture.providers.pumpfun import PumpFunLaunchpadAdapter
    adapter_rpm = PumpFunLaunchpadAdapter()._rate_limit_rps * 60.0
    assert adapter_rpm <= 30.0, "undocumented feed must stay conservative"
