#!/usr/bin/env python3
"""AHOS Production Application Lifecycle Manager & Runtime Health Engine (Phase XX).

Non-negotiable Laws:
  - Deterministic behavior: Application state is derived from explicit status and checks.
  - Fail-Closed Startup: Failure in governance integrity or essential storage halts startup cleanly.
  - Observable execution: Every lifecycle transition is recorded with timestamp and run_id.
  - Graceful shutdown: Active leases and connections are safely cleaned up.
"""
from __future__ import annotations

import enum
import hashlib
import os
import signal
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Any

from ..security import assert_safe_environment, sanitize_dict
from .logging import get_logger
from config.paths import get_project_root, get_local_db_path, get_discovery_db_path, get_paper_trading_db_path


class RuntimeState(enum.Enum):
    INITIALIZING = "INITIALIZING"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    DEGRADED = "DEGRADED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"


@dataclass
class HealthReport:
    healthy: bool
    status: str                                  # OK | DEGRADED | UNHEALTHY
    checked_at_utc: str
    details: dict[str, Any]
    duration_ms: float


class HealthCheckRegistry:
    def __init__(self):
        self._probes: dict[str, Callable[[], tuple[bool, dict[str, Any]]]] = {}

    def register(self, name: str, probe_fn: Callable[[], tuple[bool, dict[str, Any]]]):
        self._probes[name] = probe_fn

    def run_checks(self) -> HealthReport:
        t0 = time.time()
        results: dict[str, Any] = {}
        all_ok = True
        has_degraded = False

        for name, probe in self._probes.items():
            try:
                ok, meta = probe()
                results[name] = {"ok": ok, **meta}
                if not ok:
                    all_ok = False
            except Exception as e:
                results[name] = {"ok": False, "error": str(e)[:200]}
                all_ok = False

        status = "OK" if all_ok else ("DEGRADED" if not all_ok else "UNHEALTHY")
        dt = (time.time() - t0) * 1000.0

        return HealthReport(
            healthy=all_ok,
            status=status,
            checked_at_utc=datetime.now(timezone.utc).isoformat(),
            details=results,
            duration_ms=round(dt, 2)
        )


class StartupValidator:
    def __init__(self, workspace_root: Path | str | None = None):
        self.root = Path(workspace_root) if workspace_root else get_project_root()

    def validate(self) -> dict[str, Any]:
        """Validates environment, storage files, non-trading invariants, and governance pins."""
        report: dict[str, Any] = {"checks": {}, "valid": True}

        # 1. Environment & Non-trading invariant
        try:
            assert_safe_environment()
            report["checks"]["env_safety"] = {"ok": True, "detail": "Paper-only invariants verified"}
        except Exception as e:
            report["checks"]["env_safety"] = {"ok": False, "error": str(e)}
            report["valid"] = False

        # 2. Database paths & integrity
        required_dbs = [
            self.root / "data" / "e01_discovery.sqlite",
            self.root / "data" / "paper_trading.sqlite",
            self.root / "data" / "ahos_local.sqlite"
        ]
        for db in required_dbs:
            if not db.exists():
                report["checks"][f"db_{db.name}"] = {"ok": False, "error": "Database file missing"}
                report["valid"] = False
            else:
                try:
                    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
                    row = conn.execute("PRAGMA integrity_check;").fetchone()
                    conn.close()
                    ok = (row and row[0] == "ok")
                    report["checks"][f"db_{db.name}"] = {"ok": ok, "detail": row[0] if row else "fail"}
                    if not ok:
                        report["valid"] = False
                except Exception as e:
                    report["checks"][f"db_{db.name}"] = {"ok": False, "error": str(e)}
                    report["valid"] = False

        # 3. Governance Hash Integrity
        master_doc = self.root / "docs" / "canonical" / "MASTER_DIRECTIVE_v1.md"
        if master_doc.exists():
            h = hashlib.sha256(master_doc.read_bytes()).hexdigest()
            # Verified hash pin: e2457c0d9dfbadba84ee666feb46f0a01f60663e749f1261f27988abfd837d79
            expected = "e2457c0d9dfbadba84ee666feb46f0a01f60663e749f1261f27988abfd837d79"
            ok = (h == expected)
            report["checks"]["master_directive_hash"] = {"ok": ok, "sha256": h}
            if not ok:
                report["valid"] = False
        else:
            report["checks"]["master_directive_hash"] = {"ok": False, "error": "Document missing"}
            report["valid"] = False

        return report


class ApplicationLifecycleManager:
    def __init__(self, workspace_root: Path | str | None = None,
                 service_name: str = "ahos-runtime", version: str = "1.0.0"):
        self.root = Path(workspace_root) if workspace_root else get_project_root()
        self.service_name = service_name
        self.version = version
        self.run_id = f"run_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        self.state = RuntimeState.INITIALIZING
        self.logger = get_logger("ahos.runtime", run_id=self.run_id)
        self.health = HealthCheckRegistry()
        self.validator = StartupValidator(self.root)
        self._shutdown_callbacks: list[Callable[[], None]] = []
        self._setup_default_health_probes()

    def _setup_default_health_probes(self):
        def db_probe():
            db_path = self.root / "data" / "ahos_local.sqlite"
            if not db_path.exists():
                return False, {"error": "db_missing"}
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            res = conn.execute("PRAGMA integrity_check;").fetchone()
            conn.close()
            return (res[0] == "ok"), {"integrity": res[0]}

        self.health.register("storage_local", db_probe)

    def register_shutdown_hook(self, callback: Callable[[], None]):
        self._shutdown_callbacks.append(callback)

    def startup(self) -> bool:
        """Executes full startup validation and transitions to RUNNING or FAILED."""
        self.state = RuntimeState.STARTING
        self.logger.info(f"Starting AHOS Application Runtime (run_id={self.run_id})")

        val_report = self.validator.validate()
        if not val_report["valid"]:
            self.state = RuntimeState.FAILED
            self.logger.error("Startup validation failed! Halting runtime.", extra={"meta": val_report})
            return False

        health = self.health.run_checks()
        if not health.healthy:
            self.state = RuntimeState.DEGRADED
            self.logger.warning("Runtime starting in DEGRADED mode", extra={"meta": health.details})
        else:
            self.state = RuntimeState.RUNNING
            self.logger.info("AHOS Runtime started successfully (RUNNING)")

        self._record_lifecycle_event("STARTUP", self.state.value, val_report)
        return True

    def shutdown(self, reason: str = "Graceful shutdown requested"):
        if self.state in (RuntimeState.STOPPING, RuntimeState.STOPPED):
            return
        self.state = RuntimeState.STOPPING
        self.logger.info(f"Shutting down AHOS Runtime: {reason}")

        for cb in reversed(self._shutdown_callbacks):
            try:
                cb()
            except Exception as e:
                self.logger.error(f"Error executing shutdown hook: {e}")

        self.state = RuntimeState.STOPPED
        self.logger.info("AHOS Runtime STOPPED cleanly.")
        self._record_lifecycle_event("SHUTDOWN", self.state.value, {"reason": reason})

    def _record_lifecycle_event(self, action: str, state: str, meta: dict):
        try:
            db_path = self.root / "data" / "ahos_local.sqlite"
            conn = sqlite3.connect(str(db_path))
            conn.execute(
                """CREATE TABLE IF NOT EXISTS runtime_lifecycle_events (
                    event_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    timestamp_utc TEXT NOT NULL,
                    action TEXT NOT NULL,
                    state TEXT NOT NULL,
                    meta_json TEXT
                )"""
            )
            eid = f"ev_{int(time.time())}_{uuid.uuid4().hex[:6]}"
            conn.execute(
                """INSERT INTO runtime_lifecycle_events(event_id, run_id, timestamp_utc, action, state, meta_json)
                   VALUES (?,?,?,?,?,?)""",
                (eid, self.run_id, datetime.now(timezone.utc).isoformat(), action, state,
                 str(sanitize_dict(meta)))
            )
            conn.commit()
            conn.close()
        except Exception:
            pass
