#!/usr/bin/env python3
"""Tests for Production Runtime Layer (Phase XX)."""
import sys, os, time, sqlite3
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from architecture.runtime.lifecycle import (
    RuntimeState, HealthReport, HealthCheckRegistry, StartupValidator, ApplicationLifecycleManager
)
from architecture.runtime.logging import get_logger, JsonFormatter


def test_runtime_state_enum():
    assert RuntimeState.INITIALIZING.value == "INITIALIZING"
    assert RuntimeState.RUNNING.value == "RUNNING"
    assert RuntimeState.DEGRADED.value == "DEGRADED"
    assert RuntimeState.STOPPED.value == "STOPPED"
    assert RuntimeState.FAILED.value == "FAILED"


def test_health_check_registry_all_ok():
    reg = HealthCheckRegistry()
    reg.register("p1", lambda: (True, {"lat": 10}))
    reg.register("p2", lambda: (True, {"lat": 20}))
    rep = reg.run_checks()
    assert rep.healthy is True
    assert rep.status == "OK"
    assert "p1" in rep.details and rep.details["p1"]["ok"] is True
    assert "p2" in rep.details and rep.details["p2"]["ok"] is True
    assert rep.duration_ms >= 0


def test_health_check_registry_failure():
    reg = HealthCheckRegistry()
    reg.register("p1", lambda: (True, {"lat": 10}))
    reg.register("p2", lambda: (False, {"error": "down"}))
    rep = reg.run_checks()
    assert rep.healthy is False
    assert rep.status == "DEGRADED"
    assert rep.details["p2"]["ok"] is False


def test_health_check_registry_exception_handled():
    reg = HealthCheckRegistry()
    def _crasher():
        raise RuntimeError("boom")
    reg.register("p_crash", _crasher)
    rep = reg.run_checks()
    assert rep.healthy is False
    assert "boom" in rep.details["p_crash"]["error"]


def test_startup_validator_success():
    validator = StartupValidator(ROOT_DIR)
    res = validator.validate()
    assert res["valid"] is True
    assert res["checks"]["env_safety"]["ok"] is True
    assert res["checks"]["master_directive_hash"]["ok"] is True
    assert res["checks"]["db_e01_discovery.sqlite"]["ok"] is True


def test_startup_validator_missing_db(tmp_path):
    validator = StartupValidator(tmp_path)
    res = validator.validate()
    assert res["valid"] is False
    assert res["checks"]["db_e01_discovery.sqlite"]["ok"] is False


def test_lifecycle_manager_startup_and_shutdown(tmp_path):
    # Setup mock workspace structure
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "canonical").mkdir(parents=True, exist_ok=True)

    src = ROOT_DIR / "docs" / "canonical" / "MASTER_DIRECTIVE_v1.md"
    dst = tmp_path / "docs" / "canonical" / "MASTER_DIRECTIVE_v1.md"
    dst.write_bytes(src.read_bytes())

    for db_name in ["e01_discovery.sqlite", "paper_trading.sqlite", "ahos_local.sqlite"]:
        c = sqlite3.connect(tmp_path / "data" / db_name)
        c.execute("CREATE TABLE IF NOT EXISTS test (id INT)")
        c.commit()
        c.close()

    app = ApplicationLifecycleManager(workspace_root=tmp_path)
    assert app.state == RuntimeState.INITIALIZING

    hook_called = []
    app.register_shutdown_hook(lambda: hook_called.append(True))

    ok = app.startup()
    assert ok is True
    assert app.state in (RuntimeState.RUNNING, RuntimeState.DEGRADED)

    app.shutdown(reason="Test clean finish")
    assert app.state == RuntimeState.STOPPED
    assert hook_called == [True]


def test_structured_logger_formatting():
    logger = get_logger("test.runtime", run_id="run_12345")
    assert logger.extra["run_id"] == "run_12345"
