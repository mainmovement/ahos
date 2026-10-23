"""M64 & M80 Part B (Negahban) security audit unit tests."""
from __future__ import annotations

from pathlib import Path
from architecture.security.negahban import run_whitehat_security_audit, scan
from architecture.security.whitehat import task


def test_negahban_secret_scan_and_whitehat_allowlist():
    assert scan("sk-1234567890abcdef").level == "HALT"
    assert scan("risk-adjusted return task-relevant").level == "READ"
    assert task("public_header_check") == "ALLOWED"
    assert task("exploit_target") == "REFUSED"


def test_full_whitehat_security_audit_is_clean():
    root = Path(__file__).resolve().parents[1]
    res = run_whitehat_security_audit(root)
    assert res["paper_only"] is True
    assert res["overall_verdict"] == "CLEAN"
    by_name = {c["check"]: c for c in res["checks"]}
    assert by_name["loopback_bind_127_0_0_1"]["verdict"] == "CLEAN"
    assert by_name["hold_flag_presence"]["verdict"] == "CLEAN"
    assert by_name["secret_hygiene_scan"]["verdict"] == "CLEAN"
    assert by_name["lane_a_freeze_sha256"]["verdict"] == "CLEAN"
    assert by_name["lane_a_freeze_sha256"]["verified_present"] == 36
