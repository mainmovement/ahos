"""Safe sandbox boundaries for Lane-B cognitive / evolution work."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SandboxPolicy:
    """Hard constraints. Cognitive code must not violate these."""

    paper_only: bool = True
    may_start_runtime_daemon: bool = False
    may_stop_runtime_daemon: bool = False
    may_reset_soak_t0: bool = False
    may_write_lane_a: bool = False
    may_self_approve_evolution: bool = False
    may_enable_live_trading: bool = False
    may_run_uncontrolled_migrations: bool = False
    may_delete_negative_evidence: bool = False
    autonomy_ceiling: str = "L1_ANALYZE"

    def as_dict(self) -> dict[str, Any]:
        return {
            "paper_only": self.paper_only,
            "may_start_runtime_daemon": self.may_start_runtime_daemon,
            "may_stop_runtime_daemon": self.may_stop_runtime_daemon,
            "may_reset_soak_t0": self.may_reset_soak_t0,
            "may_write_lane_a": self.may_write_lane_a,
            "may_self_approve_evolution": self.may_self_approve_evolution,
            "may_enable_live_trading": self.may_enable_live_trading,
            "may_run_uncontrolled_migrations": self.may_run_uncontrolled_migrations,
            "may_delete_negative_evidence": self.may_delete_negative_evidence,
            "autonomy_ceiling": self.autonomy_ceiling,
        }


DEFAULT_SANDBOX = SandboxPolicy()


def assert_sandbox_holds(policy: SandboxPolicy = DEFAULT_SANDBOX) -> None:
    if not policy.paper_only:
        raise RuntimeError("Sandbox requires PAPER_ONLY")
    if policy.may_start_runtime_daemon or policy.may_stop_runtime_daemon:
        raise RuntimeError("Sandbox must not control the soak runtime daemon")
    if policy.may_reset_soak_t0:
        raise RuntimeError("Sandbox must not reset soak T0")
    if policy.may_write_lane_a:
        raise RuntimeError("Sandbox must not write Lane A")
    if policy.may_self_approve_evolution:
        raise RuntimeError("Sandbox must not self-approve evolution")
    if policy.may_enable_live_trading:
        raise RuntimeError("Sandbox must not enable live trading")
    if policy.may_run_uncontrolled_migrations:
        raise RuntimeError("Sandbox must not run uncontrolled migrations")
    if policy.may_delete_negative_evidence:
        raise RuntimeError("Sandbox must not delete negative evidence")
