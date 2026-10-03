"""CC-1 resolution: the launcher IS the operator surface for the runtime.

`architecture.control_plane.ControlPlane` documents itself as the ONE operator
surface (START/STOP/STATUS/SAFE_HALT/RESUME, idempotent, ledger-resumable,
stale-lock recovery) but was only ever instantiated from tests — the daemon was
started directly by `start_ahos.*`, bypassing it entirely.

Rather than adding a second plane, the launcher drives the existing engine. It
builds a *launcher-scoped* configuration (the repository-wide
`config/control_plane.yaml` describes the 2026-08 sandbox topology — Docker
Postgres BLOCKED_NO_HOST, n8n, Temporal — which is no longer the real topology
after M10 and is governance-owned, so it is left untouched) and injects real
probers for the five components it actually manages. Every START/STOP/STATUS is
recorded in the same append-only ledger the control plane always used.

What the bridge deliberately does NOT do: it does not change the daemon CLI (the
daemon still writes no ledger rows itself — a future mission's job) and it does
not touch `config/control_plane.yaml` or `config/agent_registry.yaml`.
"""
from __future__ import annotations

import time
from pathlib import Path

from architecture.control_plane import ControlPlane, Ledger  # noqa: F401 (public re-export)

LAUNCHER_MATRIX = "M11-LAUNCHER-1"

# Phases kept compatible with the control-plane engine's expectations so the
# health snapshot is actually taken during start().
PHASES = [
    "env_validation",
    "locks",
    "dependency_graph",
    "infra_discovery",
    "postgres_health",
    "engine_health",
    "health_verify",
]

LEDGER_FILE = "control_plane_ledger.sqlite"


def build_config() -> dict:
    """Launcher-scoped control-plane config (dependency reality, not prose)."""
    return {
        "matrix_version": LAUNCHER_MATRIX,
        "contract": "control_plane_contract_v1",
        "operator_surface": ["START", "STOP", "STATUS", "SAFE_HALT", "RESUME"],
        "phases": list(PHASES),
        "ledger": {"heartbeat_ttl_s": 180},
        # requires = real runtime dependency (the engine needs the stores; the
        # gateway and bot are edges on top of them).
        "infrastructure": [
            {"component": "stores", "boot_class": "CRITICAL", "requires": [],
             "availability": "LIVE"},
            {"component": "db_backend", "boot_class": "OPTIONAL",
             "requires": ["stores"], "availability": "CONFIG_DEPENDENT"},
            {"component": "gateway", "boot_class": "OPTIONAL",
             "requires": ["stores"], "availability": "LIVE_IF_BUILT"},
            {"component": "telegram", "boot_class": "OPTIONAL",
             "requires": ["gateway"], "availability": "LIVE_IF_TOKEN"},
            {"component": "engine", "boot_class": "CRITICAL",
             "requires": ["stores"], "availability": "LIVE_PAPER"},
        ],
    }


class LauncherControlPlane:
    """ControlPlane wired with the launcher's live probes."""

    def __init__(self, probers: dict, *, ledger_path: str | Path | None = None,
                 clock=time.time):
        cfg = build_config()
        reg = {"agents": []}  # agent lifecycle is a later mission (M12); not faked here
        self.cp = ControlPlane(cfg=cfg, reg=reg,
                               ledger_path=ledger_path or _default_ledger_path(),
                               probers=probers, clock=clock)

    # ------------------------------------------------------------- operator ---
    def start(self, *, now: float | None = None) -> dict:
        return self.cp.start(now=now)

    def resume(self, *, now: float | None = None) -> dict:
        return self.cp.resume(now=now)

    def stop(self, *, now: float | None = None) -> dict:
        return self.cp.stop(now=now)

    def safe_halt(self, reason: str, *, now: float | None = None) -> dict:
        return self.cp.safe_halt(reason, now=now)

    def status(self, *, now: float | None = None) -> dict:
        return self.cp.status(now=now)

    @property
    def ledger(self) -> Ledger:
        return self.cp.ledger


def _default_ledger_path() -> Path:
    from config.paths import get_data_dir
    return Path(get_data_dir()) / LEDGER_FILE
