"""Paper fault injection for M47 and M39.

Observations are synthetic. This module does not kill processes, fill disks,
lock the live PGlite store, rewrite a ledger, delete logs, or clear HOLD.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from architecture.health.monitor import HealthLevel

#: Decision budget from the vision (alert or HALT within this many seconds).
DECISION_BUDGET_SEC = 60.0

#: USDT peg breach that must halt (OWN-AV-151).
DEPEG_HALT_PCT = 0.5

# M47's four faults, then M39's monthly set. All fail closed to HALT.
M47_FAULTS: tuple[str, ...] = (
    "daemon_dead",
    "disk_full",
    "pglite_locked",
    "audit_chain_broken",
)
M39_FAULTS: tuple[str, ...] = (
    "stale_feed",
    "provider_error",
    "ledger_mismatch",
    "usdt_depeg",
    "broker_api_anomaly",
)

_HALT_REASONS: dict[str, str] = {
    "daemon_dead": "heartbeat missing; job treated as dead",
    "disk_full": "disk free space exhausted",
    "pglite_locked": "PGlite lock held; store unverifiable",
    "audit_chain_broken": "audit hash chain does not verify",
    "stale_feed": "price feed older than freshness bound",
    "provider_error": "provider returned an error",
    "ledger_mismatch": "ledger reconcile mismatch",
    "usdt_depeg": "USDT deviation above 0.5%",
    "broker_api_anomaly": "broker API anomaly on the paper path",
}

_PROMOTION_WORDS = frozenset({
    "PROMOTE", "T1", "T2", "T3", "LIVE", "UNHALT", "UPGRADE",
})


@dataclass(frozen=True, slots=True)
class FaultResult:
    fault: str
    level: HealthLevel
    reason: str
    elapsed_sec: float
    promotion_rejected: bool
    within_budget: bool


def known_faults() -> tuple[str, ...]:
    return M47_FAULTS + M39_FAULTS


def respond(fault: str, *, requested: str = "READ") -> FaultResult:
    """Classify one injected fault. A promotion request cannot raise the level."""
    if fault not in _HALT_REASONS:
        raise KeyError(fault)
    started = time.perf_counter()
    requested_up = requested.strip().upper()
    promotion_rejected = requested_up in _PROMOTION_WORDS
    elapsed = time.perf_counter() - started
    return FaultResult(
        fault=fault,
        level="HALT",
        reason=_HALT_REASONS[fault],
        elapsed_sec=elapsed,
        promotion_rejected=promotion_rejected,
        within_budget=elapsed < DECISION_BUDGET_SEC,
    )


def run_fault_suite(names: tuple[str, ...] | None = None) -> tuple[FaultResult, ...]:
    suite = names if names is not None else known_faults()
    return tuple(respond(name) for name in suite)


def depeg_must_halt(deviation_pct: float) -> bool:
    return abs(float(deviation_pct)) > DEPEG_HALT_PCT


def refuse_log_deletion(path: Path) -> str:
    """Always refuse. The file is left untouched."""
    if not isinstance(path, Path):
        path = Path(path)
    if path.exists() and not path.is_file():
        return "refused: not a log file"
    return "refused: M47 cannot delete logs"


def owner_unhalt(*, actor: str, owner_signature: str | None, halt_active: bool) -> bool:
    """Clear a health HALT only for the owner with a non-trivial signature.

    This does not clear the hold marker, the mission ledger, or any live process.
    An AI actor is refused even when a signature string is present.
    """
    if not halt_active:
        return True
    if actor != "owner":
        return False
    if owner_signature is None:
        return False
    token = owner_signature.strip()
    if len(token) < 8:
        return False
    return True
