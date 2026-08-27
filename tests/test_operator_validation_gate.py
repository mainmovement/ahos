#!/usr/bin/env python3
"""Smoke tests for operator_validation_gate runner — honesty invariants."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.operator_validation_gate import classify, main  # noqa: E402


def _pass_gates(n_end: int = 12) -> list[dict]:
    return [
        {"id": f"G{i}", "status": "PASS", "name": "x", "detail": ""}
        for i in range(1, n_end + 1)
    ]


def test_agent_host_never_auto_operator_ready():
    gates = _pass_gates(12)
    summary = classify("agent-host", gates)
    assert summary["operator_ready"] is False
    assert summary["classification"] == "INTEGRATION_READY"
    assert summary["pre_soak_entry_ok"] is False


def test_windows_requires_g11_pass_for_operator_ready():
    gates = _pass_gates(10)
    gates.append({"id": "G11", "status": "OWNER_ACTION_REQUIRED", "name": "tg", "detail": ""})
    gates.append({"id": "G12", "status": "STRUCTURAL_VALID", "name": "n8n", "detail": ""})
    summary = classify("windows", gates)
    assert summary["operator_ready"] is False
    assert summary["g1_g10_all_pass"] is True
    assert summary["pre_soak_entry_ok"] is True
    assert any("G11" in m for m in summary["missing"])


def test_windows_full_pass_operator_ready():
    gates = _pass_gates(11)
    gates.append({"id": "G12", "status": "STRUCTURAL_VALID", "name": "n8n", "detail": ""})
    summary = classify("windows", gates)
    assert summary["operator_ready"] is True
    assert summary["classification"] == "OPERATOR_READY"
    assert summary["pre_soak_entry_ok"] is True


def test_runner_writes_report(tmp_path):
    out = tmp_path / "r.json"
    rc = main(["--platform", "agent-host", "--skip-network", "--json-out", str(out)])
    assert rc == 0
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["schema"] == "ahos.operator_validation_report.v1"
    assert doc["summary"]["operator_ready"] is False
    assert "pre_soak_entry_ok" in doc["summary"]
    ids = {g["id"] for g in doc["gates"]}
    assert ids >= {f"G{i}" for i in range(1, 13)}


def test_runner_exit_3_on_windows_without_operator_ready(tmp_path):
    out = tmp_path / "w.json"
    rc = main([
        "--platform", "windows",
        "--skip-network",
        "--json-out", str(out),
    ])
    # Without probe/backup/gateway: no artificial PASS; expect FAIL and/or not ready.
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["summary"]["operator_ready"] is False
    statuses = {g["id"]: g["status"] for g in doc["gates"]}
    if any(s == "FAIL" for s in statuses.values()):
        assert rc == 2
    else:
        assert rc == 3
