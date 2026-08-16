#!/usr/bin/env python3
"""AHOS Offline-First & Network Resilience Configuration (Phase XXIV).

Designed specifically for restricted network environments (Iran/Sanctions/VPN instability):
  - 100% functional on local SQLite databases without external cloud DB dependencies.
  - Zero-cost ceiling ($0/month): Free public endpoints + local Ollama inference + deterministic floor.
  - Delayed queueing: Network failures queue observations and metrics locally for later synchronization.
  - Fallback Hierarchy: Deterministic Core -> Local AI -> Free Public Data -> Filtered Gateway.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class OfflineModeConfig:
    offline_mode_active: bool = False
    allow_external_http: bool = True
    use_local_ai_only: bool = True
    queue_failed_requests_locally: bool = True
    cost_ceiling_usd: float = 0.0
    deterministic_fallback_always_on: bool = True


def get_offline_config() -> OfflineModeConfig:
    is_offline = os.environ.get("AHOS_OFFLINE_MODE", "0") == "1"
    return OfflineModeConfig(
        offline_mode_active=is_offline,
        allow_external_http=not is_offline,
        use_local_ai_only=True,
        queue_failed_requests_locally=True,
        cost_ceiling_usd=0.0,
        deterministic_fallback_always_on=True
    )
