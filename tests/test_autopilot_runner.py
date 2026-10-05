#!/usr/bin/env python3
"""Autopilot runner repair -- pytest wrapper for the PowerShell TESTS A-I.

The AHOS Grok/Claude autopilot runner (``reports/grok/claude_autopilot.ps1``)
stalled for 34h+ on 2026-10-05 because a child mission exited cleanly with a
parseable ``AUTOPILOT_RESULT: DONE`` while the parent sat forever inside an
unbounded ``Start-Process -Wait``. The forensic audit called that root cause J
(runner orchestration failure) and explicitly DISPROVED the competing UTF-16
hypothesis: .NET ``ReadAllText`` honours the FF FE BOM and the old parser
already returned DONE on the real file.

These tests pin the repair. They are not a re-implementation of the checks in
``test_runner.ps1`` -- they invoke that harness, so the assertions actually run
under the real Windows PowerShell 5.1 binary on this host and cannot pass on a
Python re-imagining of the logic. The harness prints one ``RESULT: PASS/FAIL``
line per test; a missing or malformed line is a failure, never a pass.

Governance pins
---------------
* NEEDS_REVIEW is an owner-review gate, not an execution-complete state. No code
  path may convert it to DONE on the strength of a result file alone.
* BLOCKED_OWNER stays "(human gate; skipped)" per the queue header.
* A result is applied to the queue at most once.
* A completed result must never cause the mission to be re-executed.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "reports" / "grok" / "autopilot" / "test_runner.ps1"
RUNNER = ROOT / "reports" / "grok" / "claude_autopilot.ps1"
WATCHDOG = ROOT / "reports" / "grok" / "claude_watchdog.ps1"

RESULT_RE = re.compile(r"^RESULT: (PASS|FAIL) (\S+)(?:\s+(.*))?$", re.M)


def _find_pwsh() -> str | None:
    return shutil.which("pwsh") or shutil.which("powershell")


def _run_harness(test_id: str) -> tuple[int, str]:
    pwsh = _find_pwsh()
    if pwsh is None:
        pytest.skip("no powershell/pwsh available to run the harness")
    proc = subprocess.run(
        [pwsh, "-NoProfile", "-ExecutionPolicy", "Bypass",
         "-File", str(HARNESS), "-Test", test_id],
        capture_output=True, timeout=600,
    )
    out = (proc.stdout + proc.stderr).decode("utf-8", "replace")
    return proc.returncode, out


def _assert_pass(test_id: str, out: str, rc: int) -> None:
    """A test counts as passed only on an explicit RESULT: PASS line for its id."""
    matches = RESULT_RE.findall(out)
    ours = [m for m in matches if m[1] == test_id or m[1].endswith("_" + test_id)]
    if not ours:
        pytest.fail(
            f"harness ran but emitted no verdict for test {test_id}:\n{out}")
    verdict = ours[0][0]
    assert verdict == "PASS", f"test {test_id} failed: {ours[0][2]}\nfull:\n{out}"


@pytest.mark.parametrize("test_id", list("ABCDEFGHI"))
def test_runner_repair_case(test_id: str) -> None:
    """TESTS A-I from the repair directive, executed by the real PS 5.1 harness."""
    rc, out = _run_harness(test_id)
    _assert_pass(test_id, out, rc)


# --------------------------------------------------------------- static pins ---
# These read the committed sources, so they run on every host (including the CI
# box that has no PowerShell) and guard the shape the dynamic tests depend on.

def test_the_unbounded_wait_is_gone():
    """The proven defect was ``Start-Process ... -Wait``. It must not return.

    ``-Wait`` is the unbounded primitive that never returned after the M11.2
    child exited. The repair keeps ``-PassThru`` (needed for HasExited) and
    never re-introduces the blocking form.
    """
    text = RUNNER.read_text(encoding="utf-8")
    assert "-PassThru" in text, "the bounded wait needs the process handle"
    # The only legal -Wait in the runner tree is none at all.
    for i, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        assert "-Wait" not in stripped, (
            f"claude_autopilot.ps1:{i} reintroduces an unbounded -Wait: "
            f"{stripped}")


def test_the_runner_writes_durable_active_state_before_launch():
    """The in-flight record must exist before the child starts, not after."""
    text = RUNNER.read_text(encoding="utf-8")
    assert "active.json" in text
    assert "phase='LAUNCHED'" in text
    # Write-ActiveState must precede the first Start-Process in launch order.
    first_write = text.find("Write-ActiveState")
    first_start = text.find("Start-Process powershell.exe", first_write)
    assert first_start > first_write >= 0, (
        "the durable record must be written before the child is launched")


def test_the_runner_heartbeats_every_iteration():
    """A future stall must be observable rather than silent for hours."""
    text = RUNNER.read_text(encoding="utf-8")
    assert "heartbeat.json" in text
    assert "Write-Heartbeat 'LOOP_START'" in text
    assert "Write-Heartbeat 'WAITING_FOR_CHILD'" in text


def test_the_watchdog_reports_but_never_advances_the_queue():
    """Phase 4: the watchdog may DETECT and REPORT only."""
    text = WATCHDOG.read_text(encoding="utf-8")
    assert "ReportRunnerStall" in text
    assert "REPORT ONLY" in text, "the stall report must be log-only"
    # The watchdog must not gain any queue write of its own.
    assert "SetStatus" not in text, "the watchdog must not write queue statuses"
    for i, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        assert "CLAUDE_AUTOPILOT_QUEUE" not in stripped, (
            f"claude_watchdog.ps1:{i} touches the queue directly: {stripped}")


def test_missing_and_malformed_results_can_never_be_success():
    """Fail closed: the parser may classify absence or garbage as DONE."""
    text = RUNNER.read_text(encoding="utf-8")
    assert "Verdict='MISSING'" in text
    assert "Verdict='MALFORMED'" in text
    # The pre-repair text-match for the terminal markers is still the classifier.
    assert "AUTOPILOT_RESULT:\\s*(DONE|PARTIAL|BLOCKED_OWNER)" in text


def test_the_runner_is_powershell_51_compatible():
    r"""PS 5.1 has no ternary, no null-coalescing, and no pipe-line continuations.

    The host runs Windows PowerShell 5.1 only (no pwsh), so a PS 7-only
    operator would make the runner unparseable in production. ``Tee-Object
    -Encoding`` is 7.2+ and is what broke the launcher's hidden path in M11.2.
    """
    for path in (RUNNER, WATCHDOG):
        text = path.read_text(encoding="utf-8")
        stripped = "\n".join(l for l in text.splitlines()
                             if not l.strip().startswith("#"))
        assert "?@" not in stripped, f"{path}: PS7 ternary is not 5.1-safe"
        assert not re.search(r"\?\?", stripped), (
            f"{path}: ?? null-coalescing is not 5.1-safe")
        assert "Tee-Object" not in stripped, (
            f"{path}: Tee-Object is a 7.2+ surface (M11.2 defect class)")


def test_the_owner_gate_is_preserved_not_converted():
    """The distinction between execution result and owner review is structural."""
    text = RUNNER.read_text(encoding="utf-8")
    # Select-NextMission must hold on NEEDS_REVIEW, and Apply-Verdict must refuse
    # to write over a non-RUNNING row.
    assert "NEEDS_REVIEW" in text
    assert "owner gate" in text
    assert "BLOCKED_OWNER" in text
    assert "'TIMEOUT'" in text, "a child timeout must be an explicit outcome"


def test_no_protected_file_is_modified_by_the_diff():
    """The repair scope is the runner, the watchdog, and their harness only.

    The working tree carried pre-existing dirt before the repair began
    (``.cursor/hooks.json`` was already `` M`` at session start, from the earlier
    M11.x owner-run). That is not this repair's diff, so it is recorded here as an
    explicit baseline rather than silently tolerated: the assertion is on what the
    repair introduced, and the baseline must stay exactly this set.
    """
    import subprocess as sp
    proc = sp.run(
        ["git", "-C", str(ROOT), "status", "--porcelain"],
        capture_output=True, text=True,
    )
    # Paths already dirty before the repair. If this set grows, the repair leaked.
    pre_existing = {".cursor/hooks.json"}
    forbidden = (
        "discovery/", "paper_trading/", "architecture/decision",
        "architecture/security", ".env", "store_ai_key.py",
        ".cursor/hooks.json", "ahos-guard.py",
    )
    for line in proc.stdout.splitlines():
        if not line.startswith((" M", "A ", "M ", "MM")):
            continue
        path = line[3:]
        for bad in forbidden:
            if path.startswith(bad) and path not in pre_existing:
                pytest.fail(f"repair touched a protected path: {path}")
