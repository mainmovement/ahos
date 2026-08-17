"""
providers — AHOS v2 Provider Abstraction (top-level, core-friendly)

This package provides the minimal contract that every data provider
(market, security, narrative) must satisfy:

    fetch(chain, limit)  → ProviderResult
    health_check()       → dict  {ok, latency_ms, ...}
    normalize(raw)       → list[core.models.observation.Observation]

Existing adapters in architecture/providers/ remain untouched; new v2
providers implement this interface and are validated by
tests.test_provider_abstraction_v2 (contract compliance).

Paper-only: providers are read-only intelligence sources, never trading venues.
"""

from .base_provider import BaseProvider, ProviderResult, ProviderHealth

__all__ = ["BaseProvider", "ProviderResult", "ProviderHealth"]
