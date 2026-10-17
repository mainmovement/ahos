"""Hardware probe for M59.S (psutil when available, fail-safe without GPU)."""
from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from typing import Any, Literal

from core.idea_shelf.registry import HARDWARE_TIERS, HardwareTier

HardwareTierSource = Literal["measured", "override", "unknown"]


@dataclass(frozen=True, slots=True)
class HardwareProbe:
    ram_gb: float | None
    vram_gb: float | None
    cpu_cores: int | None
    os_name: str
    tier: HardwareTier | None
    source: HardwareTierSource
    log: tuple[str, ...] = ()


def _clamp_tier_from_ram(ram_gb: float | None, has_discrete_gpu: bool) -> HardwareTier | None:
    if has_discrete_gpu:
        return "GPU"
    if ram_gb is None:
        return None
    if ram_gb >= 28:
        return "T32"
    if ram_gb >= 14:
        return "T16"
    if ram_gb >= 6:
        return "T8"
    return "T8"


def detect_hardware(override: HardwareTier | None = None) -> HardwareProbe:
    """Measure machine band; optional override from config (logged)."""
    logs: list[str] = []
    if override is not None and override in HARDWARE_TIERS:
        logs.append(f"tier override={override}")
        return HardwareProbe(
            ram_gb=None,
            vram_gb=None,
            cpu_cores=None,
            os_name=platform.system(),
            tier=override,
            source="override",
            log=tuple(logs),
        )

    ram_gb: float | None = None
    vram_gb: float | None = None
    cores: int | None = None
    has_gpu = False

    try:
        import psutil  # type: ignore

        vm = psutil.virtual_memory()
        ram_gb = round(vm.total / (1024**3), 2)
        cores = psutil.cpu_count(logical=True) or None
        logs.append(f"psutil ram_gb={ram_gb} cores={cores}")
    except Exception as exc:  # noqa: BLE001 — probe must not crash soak
        logs.append(f"psutil unavailable: {exc}")

    env_vram = os.environ.get("AHOS_VRAM_GB")
    if env_vram:
        try:
            vram_gb = float(env_vram)
            has_gpu = vram_gb > 0.5
            logs.append(f"AHOS_VRAM_GB={vram_gb}")
        except ValueError:
            logs.append("AHOS_VRAM_GB invalid")

    tier = _clamp_tier_from_ram(ram_gb, has_gpu)
    if tier is None:
        logs.append("tier unknown")
        return HardwareProbe(
            ram_gb=ram_gb,
            vram_gb=vram_gb,
            cpu_cores=cores,
            os_name=platform.system(),
            tier=None,
            source="unknown",
            log=tuple(logs),
        )
    logs.append(f"tier measured={tier}")
    return HardwareProbe(
        ram_gb=ram_gb,
        vram_gb=vram_gb,
        cpu_cores=cores,
        os_name=platform.system(),
        tier=tier,
        source="measured",
        log=tuple(logs),
    )


def probe_from_fixture(data: dict[str, Any]) -> HardwareProbe:
    """Test helper: build a probe from plain dict."""
    tier = data.get("tier")
    t: HardwareTier | None = tier if tier in HARDWARE_TIERS else None
    return HardwareProbe(
        ram_gb=data.get("ram_gb"),
        vram_gb=data.get("vram_gb"),
        cpu_cores=data.get("cpu_cores"),
        os_name=str(data.get("os_name", "test")),
        tier=t,
        source="measured" if t else "unknown",
        log=tuple(data.get("log", ())),
    )
