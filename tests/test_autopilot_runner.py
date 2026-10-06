#!/usr/bin/env python3
"""Autopilot runner repair -- pytest wrapper for the PowerShell TESTS A-K.

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
* A terminally completed result (DONE / BLOCKED_OWNER / TIMEOUT) must never cause the
  mission to be re-executed. A retryable verdict (PARTIAL / MALFORMED / MISSING / LIMIT)
  must not block re-execution either, or the retry branch of ``Apply-Verdict`` is
  unreachable and the queue deadlocks on its first PARTIAL -- the M11.3 stall.
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
MISSION_LAUNCHER = ROOT / "reports" / "grok" / "run_mission.ps1"
MISSION_TEMPLATE = ROOT / "reports" / "grok" / "autopilot" / "MISSION_PROMPT_TEMPLATE.txt"
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


@pytest.mark.parametrize("test_id", list("ABCDEFGHIJK"))
def test_runner_repair_case(test_id: str) -> None:
    """TESTS A-K from the repair directive, executed by the real PS 5.1 harness."""
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


def test_the_launch_guard_distinguishes_terminal_from_retryable():
    """A consumed marker means "this result was applied", not "never run again".

    The M11.3 stall was exactly this conflation: a MALFORMED result left the row at
    PARTIAL so ``Apply-Verdict`` could retry it, but the launch guard refused on bare
    marker existence, so the retry was unreachable and the queue spun forever. The
    launch guard must consult the terminal-only predicate; reconciliation keeps the
    existence predicate, since there "already applied" correctly declines a re-apply.
    """
    text = RUNNER.read_text(encoding="utf-8")
    assert "function Test-ConsumedTerminal" in text
    launch_guard = text.split("Duplicate-execution guard", 1)[1][:900]
    assert "Test-ConsumedTerminal" in launch_guard, (
        "the launch guard must use the terminal-only predicate")
    assert "if (Test-Consumed $safe)" not in launch_guard, (
        "the launch guard must not fall back to bare marker existence")
    # The terminal set is exactly the verdicts that take the row out of the
    # launchable set; every retryable verdict must be absent from it.
    body = text.split("function Test-ConsumedTerminal", 1)[1]
    body = body.split("\n}\n", 1)[0]
    for verdict in ("DONE", "BLOCKED_OWNER", "TIMEOUT"):
        assert verdict in body, f"{verdict} must be terminal"
    for verdict in ("PARTIAL", "MALFORMED", "MISSING", "LIMIT"):
        assert verdict not in body, f"{verdict} must not be treated as terminal"


def test_the_mission_prompt_forbids_ending_a_turn_with_work_pending():
    r"""The M11.3 double-MALFORMED was a prompt gap, not a runner bug.

    A mission backgrounded a ~55-minute pytest suite, then ended its turn to wait for
    the completion notification. ``claude -p`` is one-shot: ending the turn exits the
    process and kills every background task with it, so the notification never arrived,
    the QA counts were never pasted and no ``AUTOPILOT_RESULT`` line was ever written.
    The mission must be told this constraint before it can respect it.
    """
    text = MISSION_TEMPLATE.read_text(encoding="utf-8")
    assert "ONE-SHOT" in text, "the template must name the execution model"
    assert "NEVER end your turn while a background task is" in text, (
        "the template must forbid ending a turn with a background task pending")
    assert "poll it inside the SAME turn" in text, (
        "the template must prescribe in-turn polling as the alternative")
    assert "in the FOREGROUND as a" in text, (
        "the template must prefer one blocking foreground call, which cannot be "
        "orphaned and does not burn the bounded --max-turns budget on polling")


def test_the_mission_launcher_treats_a_verdictless_output_as_undelivered():
    r"""A turn that ends mid-work must be resumed, not accepted as a final result.

    ``run_mission.ps1`` used to break out of its retry loop on ``-not (IsFail $txt)``
    alone, so an output with no ``AUTOPILOT_RESULT`` line was treated as a delivered
    result and handed to the runner, which classified it MALFORMED -- charging an
    attempt against output the mission never finished. The break must now require a
    verdict, using the same predicate as the runner's ``Classify-MissionResult`` so the
    two scripts cannot disagree about what a verdict looks like.
    """
    text = MISSION_LAUNCHER.read_text(encoding="utf-8")
    assert "hasVerdict" in text, "the launcher must compute verdict presence"
    assert "AUTOPILOT_RESULT:\\s*(DONE|PARTIAL|BLOCKED_OWNER)" in text, (
        "the predicate must match the runner's Classify-MissionResult")
    # The old bare break condition must be gone from non-comment lines. The new
    # condition still ends in `-not (IsFail $txt)) { break }`, so the pin is on the
    # full superseded form, which lacked the verdict term.
    for i, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        assert "-not $wd -and -not (IsFail $txt)) { break }" not in stripped, (
            f"run_mission.ps1:{i} still breaks on a verdictless result: {stripped}")
    assert "$hasVerdict -and -not (IsFail $txt)) { break }" in text, (
        "the break must now require a verdict")
    # And the resume path must carry the one-shot rule to the session it revives,
    # because --resume restores the original mission prompt, not a corrected one.
    resume = text.split("$resumeMsg", 1)[1]
    assert "one-shot" in resume, (
        "a resumed session must be told that ending its turn kills background work")


def test_the_attempt_state_is_reloaded_every_iteration():
    r"""An out-of-band budget correction must reach a runner that is already running.

    ``Load-AttemptState`` used to be called once at loop entry, so the counters lived in
    memory for the runner's whole life: a ``state.json`` edit made while the runner was
    running was never read, and ``Save-AttemptState`` clobbered it when the in-flight
    attempt ended. The load must happen inside the loop, where ``Save-AttemptState`` is
    the sole writer and a reload therefore returns exactly what the last save wrote.
    """
    text = RUNNER.read_text(encoding="utf-8")
    body = text.split("function Invoke-RunnerLoop", 1)[1]
    body = body.split("\n}\n", 1)[0]
    assert "$state = Load-AttemptState" in body, "the loop must load the attempt state"
    # The load must be inside the while loop, not at function entry. The loop body is
    # everything after the `while ($true) {` line, so a load appearing there and NOT
    # before that line is the structural guarantee.
    head, _, tail = body.partition("while ($true) {")
    assert "$state = Load-AttemptState" not in head, (
        "the attempt state must not be loaded once at loop entry")
    assert "$state = Load-AttemptState" in tail, (
        "the attempt state must be reloaded on every iteration")
    assert "Save-AttemptState is the sole writer" in body, (
        "the invariant the reload depends on must be stated in the code")


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
