#!/usr/bin/env python3
"""AHOS Observation Runtime (Phase 6 — runtime hardening).

WHY THIS MODULE EXISTS
----------------------
`discovery/observe_active.py` (frozen Lane-A, F12-O2a) is the only lawful
observation poller, but it is a standalone CLI. `python -m architecture.runtime`
never ran it, so a deployed daemon could execute opportunity cycles for hours
while the E-01 observation grid silently fell behind. This module closes that
gap WITHOUT a second poller and WITHOUT touching any intelligence layer:

  * it WRAPS `discovery.observe_active.run_observe_active` — selection, the
    frozen coverage law, dedup, rate-limit abort and gap rules all stay
    byte-frozen inside Lane A (this module owns zero selection/persistence
    logic of its own);
  * it executes under the EXISTING laws: `architecture.security.
    assert_safe_environment` (paper-only / zero-live-trading veto) is re-asserted
    before EVERY cycle, and the Lane-A freeze manifest (scripts/freeze_lane_a)
    is verified so observations can never be harvested from a drifted
    scientific surface;
  * every cycle lands in the EXISTING observability surface
    (`OperationalMetricsTracker`, `architecture.observability.Tracer`) with the
    same run_id discipline as pipeline cycles.

LAWS (operational directive §2/§4 + MASTER_DIRECTIVE_v1):
  * fail-closed — a safety violation BLOCKS the cycle (never downgrades the law)
  * honest — provider failures are DEGRADED with explicit counts; nothing is
    fabricated, no error is substituted, no gap is touched by this module
  * no parallel architecture — one poller, wrapped; no duplicate runtime
  * zero live trading — only the read-only observation path ever executes
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from config.paths import (
    get_discovery_db_path,
    get_local_db_path,
    get_paper_trading_db_path,
    get_project_root,
)

from ..observability import Tracer, OperationTrace, generate_run_id
from ..security import assert_safe_environment
from .metrics import OperationalMetricsTracker

from discovery import observations as obs                       # frozen Lane-A store (reuse)
from discovery.observe_active import (                          # frozen Lane-A poller (reuse)
    load_open_tracked_tokens,
    run_observe_active,
)

OBSERVATION_RUNTIME_VERSION = "observation_runtime:v1"

# Report statuses — the runtime's own vocabulary, distinct from scheduler status.
STATUS_SUCCESS = "SUCCESS"
STATUS_DEGRADED = "DEGRADED"
STATUS_BLOCKED = "BLOCKED"
STATUS_FAILED = "FAILED"


@dataclass
class SafetyVerdict:
    """Outcome of the fail-closed pre-flight gate."""
    ok: bool
    checks: dict[str, dict[str, Any]] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "checks": self.checks, "reasons": self.reasons}


class _PalFetcher:
    """Lazy PAL-backed fetch (same wiring as observe_active.main — reused, not copied)."""

    def __init__(self) -> None:
        self._pal = None

    def __call__(self, chain: str, address: str, now: float) -> dict[str, Any]:
        if self._pal is None:
            from discovery.pal import PAL
            self._pal = PAL()
        return self._pal.clients["dexscreener_tokens"].fetch(
            "token_pairs", "pair_enrich", chain=chain, address=address, now=now)


def _freeze_check(root) -> tuple[bool, str]:
    """Verify the Lane-A scientific surface against the frozen manifest.

    Reuses scripts/freeze_lane_a — no duplicate hashing logic exists here.
    """
    try:
        sys.path.insert(0, str(root))
        from scripts import freeze_lane_a as freeze_lane
        drift, missing, _untracked = freeze_lane.verify(root=root)
        if drift or missing:
            detail = (f"lane_a_freeze_drift: drift={sorted(drift)}"
                      if drift else f"lane_a_freeze_missing: {sorted(missing)}")
            return False, detail
        return True, "lane_a_freeze_ok"
    except Exception as e:  # unverifiable freeze => fail closed, never assume intact
        return False, f"lane_a_freeze_unverifiable: {type(e).__name__}: {e}"


class RuntimeSafetyGate:
    """Fail-closed pre-flight checks executed before every observation cycle.

    Re-declares nothing: both laws already exist and are reused.
      1. environment safety  -> architecture.security.assert_safe_environment
                                (paper-only veto, forbidden live-trading vars)
      2. Lane-A integrity    -> scripts.freeze_lane_a (frozen scientific surface)
    """

    def __init__(self, root=None):
        self.root = root if root is not None else get_project_root()

    def check(self) -> SafetyVerdict:
        verdict = SafetyVerdict(ok=True)
        try:
            env = assert_safe_environment()
            verdict.checks["env_safety"] = {"ok": True, "detail": env}
        except Exception as e:
            verdict.checks["env_safety"] = {"ok": False, "error": str(e)}
            verdict.ok = False
            verdict.reasons.append(f"env_safety_veto: {e}")

        ok, detail = _freeze_check(self.root)
        verdict.checks["lane_a_freeze"] = {"ok": ok, "detail": detail}
        if not ok:
            verdict.ok = False
            verdict.reasons.append(detail)
        return verdict


@dataclass
class ObservationCycleReport:
    """One observation cycle, honestly reported (nothing fabricated)."""
    run_id: str
    started_ts: float
    duration_ms: float
    status: str                                   # SUCCESS | DEGRADED | BLOCKED | FAILED
    safety: SafetyVerdict
    attempted: int = 0
    recorded: int = 0
    failures: int = 0
    eligible_total: int = 0
    rate_aborted: bool = False
    tracked_size: int = 0
    tracked_note: str | None = None
    obs_ids: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)
    trace: OperationTrace | None = None


class ObservationRuntime:
    """Runs one observation cycle through the frozen Lane-A poller under the runtime laws.

    Owns NO selection, coverage, scheduling or persistence logic — it wires the
    existing frozen poller into the managed runtime and reports it.
    """

    def __init__(self, *, workspace_root=None, discovery_db_path: str | None = None,
                 tracked_store_path: str | None = None,
                 metrics_tracker: OperationalMetricsTracker | None = None,
                 fetch: Callable | None = None, gate: RuntimeSafetyGate | None = None):
        self.root = workspace_root if workspace_root is not None else get_project_root()
        self.discovery_db_path = discovery_db_path or get_discovery_db_path()
        self.tracked_store_path = (get_paper_trading_db_path()
                                   if tracked_store_path is None else tracked_store_path)
        self.metrics = metrics_tracker or OperationalMetricsTracker(db_path=get_local_db_path())
        self.fetch = fetch or _PalFetcher()
        self.gate = gate or RuntimeSafetyGate(root=self.root)
        self.tracer = Tracer("observation_runtime", version=OBSERVATION_RUNTIME_VERSION)

    def run_cycle(self, now: float | None = None, *, max_tokens: int = 40,
                  dry_run: bool = False, min_interval: float = 240.0,
                  run_id: str | None = None) -> ObservationCycleReport:
        started = time.time() if now is None else now
        rid = run_id or generate_run_id("obs")
        trace_ctx = self.tracer.trace_operation(
            "run_observation_cycle",
            {"max_tokens": max_tokens, "dry_run": dry_run, "min_interval": min_interval},
            run_id=rid)

        # 1. Fail-closed pre-flight: a veto means the cycle NEVER executes.
        verdict = self.gate.check()
        if not verdict.ok:
            rep = self._report(rid, started, STATUS_BLOCKED, verdict,
                               trace=trace_ctx.failure(
                                   PermissionError("; ".join(verdict.reasons)),
                                   error_class="SAFETY_VETO",
                                   meta={"safety": verdict.as_dict()}))
            self._record_metrics(rid, STATUS_BLOCKED, rep)
            return rep

        # 2. One pass through the FROZEN Lane-A poller (reused, never reimplemented).
        conn = None
        try:
            tracked, tracked_note = load_open_tracked_tokens(self.tracked_store_path)
            conn = obs.open_store(self.discovery_db_path)
            poll = run_observe_active(conn, now=started, fetch=self.fetch,
                                      dry_run=dry_run, max_tokens=max_tokens,
                                      min_interval=min_interval,
                                      tracked=tracked, tracked_note=tracked_note)
            failed = len(poll.get("failures", []))
            status = STATUS_SUCCESS if (not failed and not poll.get("aborted")) else STATUS_DEGRADED
            details = {k: v for k, v in poll.items()
                       if k not in ("selected", "obs_ids", "failures")}
            rep = self._report(
                rid, started, status, verdict,
                attempted=int(poll.get("attempted", 0)),
                recorded=int(poll.get("recorded", 0)),
                failures=failed,
                eligible_total=int(poll.get("eligible_total", 0)),
                rate_aborted=bool(poll.get("aborted")),
                tracked_size=int(poll.get("tracked_size", 0)),
                tracked_note=tracked_note,
                obs_ids=list(poll.get("obs_ids", [])),
                details=details,
                trace=trace_ctx.success({"status": status, "failures": failed}, meta=details))
            self._record_metrics(rid, status, rep)
            return rep
        except Exception as e:
            rep = self._report(rid, started, STATUS_FAILED, verdict,
                               trace=trace_ctx.failure(e, meta={"phase": "poll"}))
            self._record_metrics(rid, STATUS_FAILED, rep)
            return rep
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _report(rid, started, status, verdict, *, attempted=0, recorded=0, failures=0,
                eligible_total=0, rate_aborted=False, tracked_size=0, tracked_note=None,
                obs_ids=None, details=None, trace=None) -> ObservationCycleReport:
        return ObservationCycleReport(
            run_id=rid,
            started_ts=started,
            duration_ms=round((time.time() - started) * 1000.0, 2),
            status=status,
            safety=verdict,
            attempted=attempted,
            recorded=recorded,
            failures=failures,
            eligible_total=eligible_total,
            rate_aborted=rate_aborted,
            tracked_size=tracked_size,
            tracked_note=tracked_note,
            obs_ids=obs_ids or [],
            details=details or {},
            trace=trace)

    def _record_metrics(self, run_id: str, status: str, rep: ObservationCycleReport) -> None:
        metric_status = {
            STATUS_SUCCESS: "OK",
            STATUS_DEGRADED: "WARN",
            STATUS_BLOCKED: "ERROR",
            STATUS_FAILED: "ERROR",
        }.get(status, "ERROR")
        common = {"run_id": run_id, "status": metric_status,
                  "evidence_refs": [rep.run_id]}
        self.metrics.record_metric(component="observation", metric_name="cycle_status",
                                   metric_value=0.0 if metric_status != "ERROR" else 1.0,
                                   meta={"report_status": status}, **common)
        if status == STATUS_BLOCKED:
            return
        self.metrics.record_metric(component="observation", metric_name="attempted",
                                   metric_value=float(rep.attempted), **common)
        self.metrics.record_metric(component="observation", metric_name="recorded",
                                   metric_value=float(rep.recorded), **common)
        self.metrics.record_metric(component="observation", metric_name="failures",
                                   metric_value=float(rep.failures), **common)
        self.metrics.record_metric(component="observation", metric_name="cycle_duration_ms",
                                   metric_value=float(rep.duration_ms), **common)
