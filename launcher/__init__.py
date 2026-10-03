"""M11 — one-click AHOS launcher.

Single entry point that brings the whole system up without Docker:

    python -m launcher preflight
    python -m launcher start     # idempotent: re-running is a no-op
    python -m launcher status
    python -m launcher stop      # stops only AHOS-owned processes
    python -m launcher restart

The orchestrator is the one place startup logic lives; `start_ahos.bat` /
`start_ahos.ps1` delegate here and the desktop shortcuts call the PowerShell
wrapper in `launcher/ahos.ps1`. Runtime lifecycle is recorded through
`architecture.control_plane.ControlPlane` (CC-1), so START/STOP/STATUS are the
documented operator surface with an append-only ledger, not a second plane.

PAPER_ONLY is enforced: the engine is launched with AHOS_PAPER_ONLY=1 and any
component that cannot be started is reported honestly (BLOCKED / DEGRADED)
rather than silently skipped.
"""
from __future__ import annotations

__version__ = "1.0.0"

__all__ = ["orchestrator", "persian", "processkit"]
