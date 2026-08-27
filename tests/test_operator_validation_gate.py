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


def test_agent_host_never_auto_operator_ready():
    gates = [
        {"id": f"G{i}", "status": "PASS", "name": "x", "detail": ""}
        for i in range(1, 13)
    ]
    # Even if all PASS, non-windows platform cannot be OPERATOR_READY
    summary = classify("agent-host", gates)
    assert summary["operator_ready"] is False
    assert summary["classification"] == "INTEGRATION_READY"


def test_windows_requires_g11_pass():
    gates = [
        {"id": f"G{i}", "status": "PASS", "name": "x", "detail": ""}
        for i in range(1, 12)
    ]
    gates.append({"id": "G12", "status": "STRUCTURAL_VALID", "name": "n8n", "detail": ""})
    gates = [g for g in gates if g["id"] != "G11"]
    gates.append({"id": "G11", "status": "OWNER_ACTION_REQUIRED", "name": "tg", "detail": ""})
    summary = classify("windows", gates)
    assert summary["operator_ready"] is False
    assert any("G11" in m for m in summary["missing"])


def test_runner_writes_report(tmp_path):
    out = tmp_path / "r.json"
    rc = main(["--platform", "agent-host", "--skip-network", "--json-out", str(out)])
    assert rc == 0
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["schema"] == "ahos.operator_validation_report.v1"
    assert doc["summary"]["operator_ready"] is False
    ids = {g["id"] for g in doc["gates"]}
    assert ids >= {f"G{i}" for i in range(1, 13)}
