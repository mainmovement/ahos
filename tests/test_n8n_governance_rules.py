"""GM-06 - n8n workflow governance rules + ahos_03 quarantine.

Static checks only: no workflow is imported or executed, no DB touched.
Self-tests, not independent verification.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests import validate_n8n as v  # noqa: E402

WF = ROOT / "n8n" / "workflows"
AHOS03 = WF / "ahos_03_telegram_control.json"


def _wf(query: str, trigger: str = "n8n-nodes-base.scheduleTrigger", disabled: bool = False) -> dict:
    return {"nodes": [
        {"name": "T", "type": trigger, "parameters": {}},
        {"name": "Q", "type": "n8n-nodes-base.postgres", "disabled": disabled,
         "parameters": {"operation": "executeQuery", "query": query}},
    ]}


def _write(tmp_path: Path, name: str, wf: dict) -> Path:
    full = {"nodes": [], "connections": {}}
    for i, n in enumerate(wf["nodes"]):
        full["nodes"].append({**n, "id": str(i), "typeVersion": 1, "position": [0, i]})
    full["connections"] = {"T": {"main": [[{"node": "Q", "type": "main", "index": 0}]]}}
    p = tmp_path / name
    p.write_text(json.dumps(full), encoding="utf-8")
    return p


# ---------------------------------------------------------------- rules --

@pytest.mark.parametrize("sql", [
    "DELETE FROM agent_audit_trail WHERE 1=1",
    "=delete   from public.agent_audit_trail where action='X'",
    'TRUNCATE TABLE "agent_audit_trail"',
    "truncate agent_audit_trail",
    "UPDATE agent_audit_trail SET result='OK'",
    "INSERT INTO x VALUES (1); DELETE FROM agent_audit_trail;",
])
def test_audit_tamper_is_error(sql):
    errs, _ = v.governance_findings(_wf(sql))
    assert any(e.startswith("AUDIT_TAMPER") for e in errs), errs


@pytest.mark.parametrize("sql", [
    "UPDATE trade_decisions SET execution_status='PAPER' WHERE id=1",
    "=update public.trade_decisions\n set confidence_score=1, execution_status = 'CANCELLED'",
    'UPDATE "trade_decisions" SET execution_status = CASE 1 WHEN 1 THEN \'PAPER\' END',
])
def test_execution_status_mutation_is_authority_bypass(sql):
    errs, _ = v.governance_findings(_wf(sql))
    assert any(e.startswith("AUTHORITY_BYPASS") for e in errs), errs


def test_interpolation_external_trigger_is_error_internal_is_warning():
    q = "=INSERT INTO agent_audit_trail (reason) VALUES ('{{ $json.text }}')"
    errs, _ = v.governance_findings(_wf(q, trigger="n8n-nodes-base.telegramTrigger"))
    assert any(e.startswith("SQL_INTERPOLATION_FROM_EXTERNAL_TRIGGER") for e in errs)
    errs, _ = v.governance_findings(_wf(q, trigger="n8n-nodes-base.webhook"))
    assert any(e.startswith("SQL_INTERPOLATION_FROM_EXTERNAL_TRIGGER") for e in errs)
    errs, warns = v.governance_findings(_wf(q))
    assert not errs and any(w.startswith("SQL_INTERPOLATION:") for w in warns)


@pytest.mark.parametrize("sql", [
    "SELECT * FROM agent_audit_trail WHERE action='DELETE FROM'",   # read only
    "INSERT INTO agent_audit_trail (agent_id) VALUES ('A')",         # append is fine
    "SELECT execution_status FROM trade_decisions",                  # read only
    "UPDATE agent_registry SET enabled=false",                       # other table
    "SELECT * FROM agent_audit_trail_archive",                       # different table
])
def test_benign_sql_is_not_flagged(sql):
    errs, _ = v.governance_findings(_wf(sql))
    assert errs == [], errs


def test_disabled_nodes_are_ignored():
    errs, _ = v.governance_findings(_wf("DELETE FROM agent_audit_trail", disabled=True))
    assert errs == []


def test_decision_insert_is_warning():
    _, warns = v.governance_findings(_wf("INSERT INTO trade_decisions (symbol) VALUES ('X')"))
    assert any(w.startswith("DECISION_WRITE_OUTSIDE_CANONICAL_AUTHORITY") for w in warns)


# ---------------------------------------------------- validate() wiring --

def test_non_quarantined_violation_fails_validate(tmp_path):
    p = _write(tmp_path, "ahos_99_bad.json", _wf("DELETE FROM agent_audit_trail"))
    errs, _ = v.validate(str(p))
    assert any("AUDIT_TAMPER" in e for e in errs)


def test_quarantine_is_by_exact_filename_only(tmp_path):
    # A look-alike name must not inherit the quarantine demotion.
    p = _write(tmp_path, "ahos_03_telegram_control.json.bak", _wf("DELETE FROM agent_audit_trail"))
    errs, _ = v.validate(str(p))
    assert errs


def test_ahos03_is_quarantined_not_deleted():
    assert AHOS03.is_file(), "GM-06 must not delete the workflow file"
    assert AHOS03.name in v.QUARANTINED_WORKFLOWS
    errs, warns = v.validate(str(AHOS03))
    assert errs == []                      # structural G12 result unchanged
    joined = "\n".join(warns)
    assert "DO NOT IMPORT" in joined
    for rule in ("AUDIT_TAMPER", "AUTHORITY_BYPASS", "SQL_INTERPOLATION_FROM_EXTERNAL_TRIGGER"):
        assert f"QUARANTINED {rule}" in joined, rule


def test_ahos03_would_fail_without_quarantine(monkeypatch):
    monkeypatch.setattr(v, "QUARANTINED_WORKFLOWS", {})
    errs, _ = v.validate(str(AHOS03))
    rules = {e.split(":", 1)[0] for e in errs}
    assert {"AUDIT_TAMPER", "AUTHORITY_BYPASS", "SQL_INTERPOLATION_FROM_EXTERNAL_TRIGGER"} <= rules


def test_no_other_shipped_workflow_has_hard_governance_errors():
    for p in sorted(WF.glob("*.json")):
        if p.name in v.QUARANTINED_WORKFLOWS:
            continue
        errs, _ = v.governance_findings(json.loads(p.read_text(encoding="utf-8")))
        assert errs == [], (p.name, errs)


def test_cli_marks_quarantine_and_keeps_exit_zero():
    out = subprocess.run([sys.executable, str(ROOT / "tests" / "validate_n8n.py")],
                         capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert out.returncode == 0, out.stdout + out.stderr
    assert "[QUARANTINED(do-not-import)] ahos_03_telegram_control.json" in out.stdout


def test_quarantine_doc_exists():
    doc = ROOT / "reports" / "grok" / "GM06_N8N_QUARANTINE.md"
    text = doc.read_text(encoding="utf-8")
    assert "ahos_03_telegram_control.json" in text and "QUARANTINED" in text
