#!/usr/bin/env python3
"""Runtime Hardening & Failure Recovery Matrix Tests (Phase XXI)."""
import sys, os, time, sqlite3, logging
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from architecture.runtime.lifecycle import (
    RuntimeState, HealthReport, HealthCheckRegistry, StartupValidator, ApplicationLifecycleManager
)
from architecture.runtime.logging import JsonFormatter, get_logger


def test_runtime_health_registry_multiple_probes():
    reg = HealthCheckRegistry()
    reg.register("p1", lambda: (True, {"metric": 100}))
    reg.register("p2", lambda: (True, {"metric": 200}))
    reg.register("p3", lambda: (True, {"metric": 300}))
    rep = reg.run_checks()
    assert rep.healthy is True
    assert rep.status == "OK"
    assert len(rep.details) == 3


def test_runtime_health_registry_degraded_state():
    reg = HealthCheckRegistry()
    reg.register("ok1", lambda: (True, {}))
    reg.register("fail1", lambda: (False, {"reason": "degraded response"}))
    rep = reg.run_checks()
    assert rep.healthy is False
    assert rep.status == "DEGRADED"


def test_runtime_shutdown_hooks_error_isolation(tmp_path):
    # Setup test workspace
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "canonical").mkdir(parents=True, exist_ok=True)
    master_doc = Path(str(ROOT_DIR / "docs" / "canonical" / "MASTER_DIRECTIVE_v1.md")).read_text()
    (tmp_path / "docs" / "canonical" / "MASTER_DIRECTIVE_v1.md").write_text(master_doc)

    for db_name in ["e01_discovery.sqlite", "paper_trading.sqlite", "ahos_local.sqlite"]:
        c = sqlite3.connect(tmp_path / "data" / db_name)
        c.execute("CREATE TABLE IF NOT EXISTS test (id INT)")
        c.commit()
        c.close()

    app = ApplicationLifecycleManager(workspace_root=tmp_path)
    app.startup()

    executed = []
    def _crashing_hook():
        raise RuntimeError("Hook crashed")
    def _good_hook():
        executed.append("good")

    app.register_shutdown_hook(_crashing_hook)
    app.register_shutdown_hook(_good_hook)

    # Shutdown should isolate the crashing hook and still execute good hook
    app.shutdown(reason="Testing hook isolation")
    assert app.state == RuntimeState.STOPPED
    assert executed == ["good"]


def test_json_formatter_with_meta_and_exception():
    formatter = JsonFormatter(service_name="test-svc", version="2.0.0")
    record = logging.LogRecord(
        name="test_logger",
        level=logging.ERROR,
        pathname="test.py",
        lineno=42,
        msg="Critical error with token 123456789:ABCdefGHIjklMNOpqrsTUVwxyz1234567",
        args=(),
        exc_info=None
    )
    record.run_id = "run_abc123"
    record.meta = {"secret_key": "sk-secret12345", "public_info": "public"}

    out = formatter.format(record)
    assert "123456789:ABCdef" not in out
    assert "sk-secret12345" not in out
    assert "[REDACTED_SECRET]" in out
    assert "run_abc123" in out
    assert "test-svc" in out


def test_startup_validator_corrupted_database(tmp_path):
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "canonical").mkdir(parents=True, exist_ok=True)
    master_doc = Path(str(ROOT_DIR / "docs" / "canonical" / "MASTER_DIRECTIVE_v1.md")).read_text()
    (tmp_path / "docs" / "canonical" / "MASTER_DIRECTIVE_v1.md").write_text(master_doc)

    # Create corrupted file
    corrupt_db = tmp_path / "data" / "e01_discovery.sqlite"
    corrupt_db.write_bytes(b"NOT A VALID SQLITE DATABASE FILE HEADER")

    validator = StartupValidator(tmp_path)
    res = validator.validate()
    assert res["valid"] is False
    assert res["checks"]["db_e01_discovery.sqlite"]["ok"] is False
