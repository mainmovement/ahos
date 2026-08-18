#!/usr/bin/env python3
"""Phase 13 — laptop operation gate regressions.

The value of this phase is entirely in what the tooling REFUSES to certify.
These tests pin those refusals so a later change cannot quietly turn a sandbox
run into "the official soak", which would silently invalidate every downstream
claim about uptime, provider success and calibration.
"""
from __future__ import annotations

import json
import platform
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import record_local_laptop_baseline as baseline  # noqa: E402
from scripts import soak_t0_snapshot as t0  # noqa: E402


# ------------------------------------------------------------ baseline gate

def test_non_windows_host_can_never_be_eligible():
    """The core Phase 13 refusal: sandbox hours must never count."""
    report = baseline.build()

    if platform.system() != "Windows":
        assert report["official_168h_eligible"] is False
        assert report["checks"]["windows_host"] is False


def test_baseline_names_every_failed_check():
    """A refusal without a reason is not actionable evidence."""
    report = baseline.build()
    failed = [k for k, v in report["checks"].items() if not v]

    if not report["official_168h_eligible"]:
        assert failed, "ineligible baseline must name at least one failed check"


def test_baseline_records_the_mandated_fields():
    """Task 1 fields must come from the artifact, not from prose."""
    report = baseline.build()

    assert report["os"]["system"]
    assert report["python"]["version"]
    assert report["dependency_hash"]["requirements_txt_sha256"]
    assert report["dependency_hash"]["lane_a_freeze_sha256"]
    assert set(report["databases"]["integrity"]) == {
        "e01_discovery", "paper_trading", "ahos_local", "ahos_knowledge"}
    assert report["safety"]["mode"] == "observation-only"


def test_live_trading_env_flags_block_eligibility(monkeypatch):
    monkeypatch.setenv("AHOS_EXECUTE_LIVE_TRADES", "1")
    report = baseline.build()

    assert report["checks"]["execution_flags_disabled"] is False
    assert report["official_168h_eligible"] is False


# ------------------------------------------------------------------ t0 gate

def _valid_context():
    """Patches representing a correctly-prepared Windows laptop."""
    return (
        patch.object(platform, "system", return_value="Windows"),
        patch.object(t0, "_baseline_status",
                     return_value={"present": True, "official_168h_eligible": True,
                                   "failed_checks": []}),
        patch.object(t0, "_watchdog_status",
                     return_value={"status": "OK", "stale_components": []}),
        patch.object(t0, "_provider_status",
                     return_value={"probed": True, "any_success": True,
                                   "status_counts": {"SUCCESS": 2}}),
    )


def test_t0_is_invalid_on_this_sandbox():
    snap = t0.build_snapshot(do_probe=False)

    if platform.system() != "Windows":
        assert snap["t0_valid"] is False
        assert snap["soak_status"] == "NOT_STARTED"
        assert any("not Windows" in r for r in snap["t0_invalid_reasons"])


def test_t0_contains_every_mandated_field():
    """Task 5 names the required contents explicitly."""
    snap = t0.build_snapshot(do_probe=False)

    for key in ("timestamp_utc", "git", "environment", "watchdog",
                "heartbeats", "providers"):
        assert key in snap, f"t0 snapshot missing mandated field: {key}"
    assert snap["git"]["commit_sha"]
    assert snap["environment"]["fingerprint_sha256"]


def test_t0_valid_only_when_all_four_conditions_hold(monkeypatch):
    monkeypatch.setenv("AHOS_EVIDENCE_SOURCE", "local")
    p1, p2, p3, p4 = _valid_context()
    with p1, p2, p3, p4:
        snap = t0.build_snapshot()

    assert snap["t0_valid"] is True
    assert snap["soak_status"] == "LOCAL_SOAK_RUNNING"
    assert snap["t0_invalid_reasons"] == []


@pytest.mark.parametrize("broken", ["windows", "baseline", "watchdog", "source"])
def test_each_missing_condition_alone_invalidates_t0(monkeypatch, broken):
    """No single condition may be dropped without invalidating t0."""
    monkeypatch.setenv("AHOS_EVIDENCE_SOURCE",
                       "sandbox" if broken == "source" else "local")

    sys_val = "Linux" if broken == "windows" else "Windows"
    base_val = ({"present": True, "official_168h_eligible": False,
                 "failed_checks": ["windows_host"]}
                if broken == "baseline"
                else {"present": True, "official_168h_eligible": True,
                      "failed_checks": []})
    wd_val = ({"status": "NO_HEARTBEATS"} if broken == "watchdog"
              else {"status": "OK", "stale_components": []})

    with patch.object(platform, "system", return_value=sys_val), \
         patch.object(t0, "_baseline_status", return_value=base_val), \
         patch.object(t0, "_watchdog_status", return_value=wd_val), \
         patch.object(t0, "_provider_status",
                      return_value={"probed": True, "any_success": True,
                                    "status_counts": {"SUCCESS": 2}}):
        snap = t0.build_snapshot()

    assert snap["t0_valid"] is False, f"t0 wrongly valid with {broken} broken"
    assert snap["soak_status"] == "NOT_STARTED"


def test_t0_writes_an_artifact_even_when_refusing(tmp_path):
    """A refusal that leaves no record is not evidence."""
    out = tmp_path / "soak" / "system_state_t0.json"
    rc = t0.main(["--no-probe", "--out", str(out)])

    assert out.is_file()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["schema"] == "ahos.soak_t0.v1"
    if platform.system() != "Windows":
        assert rc == 3 and payload["t0_valid"] is False


def test_t0_snapshot_is_read_only():
    import hashlib
    from config.paths import get_discovery_db_path, get_local_db_path

    def digest(p: str) -> bytes:
        return hashlib.sha256(Path(p).read_bytes()).digest()

    before = (digest(get_local_db_path()), digest(get_discovery_db_path()))
    t0.build_snapshot(do_probe=False)
    assert (digest(get_local_db_path()), digest(get_discovery_db_path())) == before


# --------------------------------------------------------- operation report

def test_operation_report_exists_and_covers_mandated_sections():
    doc = ROOT / "AHOS_LAPTOP_OPERATION_REPORT.md"
    assert doc.is_file()
    text = doc.read_text(encoding="utf-8")

    for section in ("Hardware environment", "Operating system", "Python version",
                    "Dependency hash", "Database integrity", "Lane-A freeze",
                    "Evidence source"):
        assert section in text, f"operation report missing section: {section}"


def test_operation_report_does_not_claim_a_running_soak():
    text = (ROOT / "AHOS_LAPTOP_OPERATION_REPORT.md").read_text(encoding="utf-8")
    flat = " ".join(text.split())

    assert "AWAITING_LAPTOP_EXECUTION" in flat
    for forbidden in ("PRODUCTION_READY", "LOCAL_PRODUCTION_READY"):
        assert forbidden not in flat
    # It must state plainly that the daemon was not started.
    assert "NOT PERFORMED" in flat


def test_operation_report_dependency_hashes_are_real():
    """Documented hashes must match the repository, not be placeholders."""
    import hashlib

    text = (ROOT / "AHOS_LAPTOP_OPERATION_REPORT.md").read_text(encoding="utf-8")
    for rel in ("requirements.txt", "config/lane_a_freeze.sha256"):
        digest = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        assert digest in text, f"operation report lacks the real sha256 of {rel}"


def test_progress_snapshot_has_not_advanced_to_running_soak():
    """LOCAL_SOAK_RUNNING may only appear once the laptop actually runs it."""
    text = (ROOT / "AHOS_PHASE_PROGRESS_SNAPSHOT.md").read_text(encoding="utf-8")
    flat = " ".join(text.split())

    assert "READY_FOR_REAL_LOCAL_DATA" in flat
    # The phrase may be discussed, but never asserted as the current state.
    assert "Classification:** `LOCAL_SOAK_RUNNING`" not in flat


def test_no_fake_calibration_on_this_host():
    """Phase 13 acceptance: no calibration may be manufactured."""
    from architecture.learning.calibration import CalibrationHarness

    report = CalibrationHarness().run()
    assert report.verdict == "INSUFFICIENT_DATA"
    assert report.joined_pairs == 0
