#!/usr/bin/env python3
"""Phase 14 — operator documentation audit regressions.

The operator follows these documents on a Windows laptop with no one to ask.
A single bash-only command, stale flag, or missing script strands them mid-soak,
so these tests treat the docs as an interface and pin it:

  * every referenced script exists
  * every documented CLI flag is really accepted by that CLI
  * no bash-only construct, Linux-only path, VPS instruction, or production claim
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

OPERATOR_DOCS = (
    "AHOS_OPERATOR_QUICKSTART_WINDOWS.md",
    "AHOS_SOAK_OPERATOR_START.md",
    "AHOS_LAPTOP_OPERATION_REPORT.md",
    "AHOS_LOCAL_ACTIVATION_CHECKLIST.md",
)

# Scripts the operator is told to run, with the flags the docs promise.
DOCUMENTED_CLIS: dict[str, tuple[str, ...]] = {
    "scripts/freeze_lane_a.py": (),
    "scripts/validate_imports.py": (),
    "scripts/init_databases.py": ("--with-guards",),
    "scripts/record_local_laptop_baseline.py": (),
    "scripts/local_activation_report.py": ("--no-probe", "--out"),
    "scripts/soak_t0_snapshot.py": ("--no-probe", "--out"),
    "scripts/soak_snapshot.py": ("--window-hours",),
    "scripts/system_state_snapshot.py": ("--probe-providers",),
    "scripts/sqlite_backup_restore.py": (),
    "scripts/calibration_report.py": ("--horizon", "--event-class"),
}

DOCUMENTED_RUNTIME_FLAGS = (
    "--probe-providers", "--daemon", "--interval-sec",
    "--observation-cycle", "--evidence-source",
    "--snapshot-interval-hours", "--snapshot-probe-providers",
)


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def _all_docs_text() -> str:
    return "\n".join(_read(name) for name in OPERATOR_DOCS)


# ------------------------------------------------------------- doc existence

@pytest.mark.parametrize("name", OPERATOR_DOCS)
def test_operator_document_exists(name):
    assert (ROOT / name).is_file(), f"operator document missing: {name}"


def test_windows_quickstart_covers_every_mandated_step():
    """Task 3 names the required contents explicitly."""
    text = _read("AHOS_OPERATOR_QUICKSTART_WINDOWS.md")

    for step in ("git clone", "git pull", "python -m venv .venv",
                 "Activate.ps1", "pip install -r requirements.txt",
                 "record_local_laptop_baseline.py", "--probe-providers",
                 "--daemon", "soak_snapshot.py", "soak_t0_snapshot.py",
                 "sqlite_backup_restore.py"):
        assert step in text, f"quickstart missing mandated step: {step}"


# --------------------------------------------------------- referenced scripts

def test_every_script_referenced_by_the_docs_exists():
    """A documented command that does not exist strands the operator."""
    text = _all_docs_text()
    referenced = set(re.findall(r"scripts[\\/]([A-Za-z0-9_]+\.py)", text))
    assert referenced, "no scripts referenced — extraction regex is wrong"

    missing = [s for s in sorted(referenced) if not (ROOT / "scripts" / s).is_file()]
    assert not missing, f"docs reference non-existent scripts: {missing}"


@pytest.mark.parametrize("rel", sorted(DOCUMENTED_CLIS))
def test_documented_script_exposes_its_documented_flags(rel):
    """Flags are promises; verify them against the CLI's own --help."""
    proc = subprocess.run(
        [sys.executable, "-B", str(ROOT / rel), "--help"],
        capture_output=True, text=True, timeout=120, cwd=str(ROOT),
    )
    assert proc.returncode == 0, f"{rel} --help failed: {proc.stderr[-300:]}"
    for flag in DOCUMENTED_CLIS[rel]:
        assert flag in proc.stdout, f"{rel} does not accept documented flag {flag}"


def test_runtime_module_exposes_its_documented_flags():
    proc = subprocess.run(
        [sys.executable, "-B", "-m", "architecture.runtime", "--help"],
        capture_output=True, text=True, timeout=120, cwd=str(ROOT),
    )
    assert proc.returncode == 0
    for flag in DOCUMENTED_RUNTIME_FLAGS:
        assert flag in proc.stdout, f"runtime does not accept documented flag {flag}"


def test_watchdog_exposes_status_and_json():
    proc = subprocess.run(
        [sys.executable, "-B", "-m", "architecture.scheduling.watchdog", "--help"],
        capture_output=True, text=True, timeout=120, cwd=str(ROOT),
    )
    assert proc.returncode == 0
    assert "--status" in proc.stdout and "--json" in proc.stdout


def test_backup_tool_exposes_the_nightly_subcommand():
    proc = subprocess.run(
        [sys.executable, "-B", str(ROOT / "scripts" / "sqlite_backup_restore.py"), "--help"],
        capture_output=True, text=True, timeout=120, cwd=str(ROOT),
    )
    assert proc.returncode == 0
    for sub in ("nightly", "drill", "backup", "restore"):
        assert sub in proc.stdout, f"backup tool missing subcommand: {sub}"


# ------------------------------------------------------- Windows portability

@pytest.mark.parametrize("name", OPERATOR_DOCS)
def test_no_bash_only_commands(name):
    """Task 4: these run in PowerShell, where bash builtins do not exist."""
    forbidden = re.compile(
        r"^\s*(export |source |sudo |chmod |chown |apt(-get)? |yum |brew |"
        r"systemctl |journalctl |crontab |caffeinate |gsettings |pmset )",
        re.MULTILINE)
    hits = forbidden.findall(_read(name))
    assert not hits, f"{name} contains bash-only commands: {hits}"


@pytest.mark.parametrize("name", OPERATOR_DOCS)
def test_no_kill_dash_nine_as_an_instruction(name):
    """`kill -9` has no Windows equivalent; Stop-Process -Force is the answer.

    Naming it while pointing at the Windows equivalent is fine ("the Windows
    equivalent of `kill -9`"); telling the operator to *run* it is not.
    """
    for i, line in enumerate(_read(name).splitlines(), 1):
        if "kill -9" not in line:
            continue
        assert re.search(r"equivalent|instead of|not\b|Windows", line, re.IGNORECASE), \
            f"{name}:{i} instructs a bash-only kill: {line.strip()}"


@pytest.mark.parametrize("name", OPERATOR_DOCS)
def test_no_linux_only_absolute_paths(name):
    """A POSIX path in a Windows instruction is a dead end."""
    hits = re.findall(r"(?<![\w.])/(?:home|opt|etc|var|usr)/[A-Za-z0-9_./-]*",
                      _read(name))
    assert not hits, f"{name} contains Linux-only paths: {hits}"


@pytest.mark.parametrize("name", OPERATOR_DOCS)
def test_no_vps_or_cloud_deployment_instructions(name):
    """VPS may only appear as an explicit disclaimer, never as a step."""
    for line in _read(name).splitlines():
        if not re.search(r"\b(vps|droplet|ec2)\b", line, re.IGNORECASE):
            continue
        # Allowed only as a negation/disclaimer, never as a step.
        assert re.search(r"\b(no|not|never|nothing|does not|without)\b",
                         line, re.IGNORECASE), \
            f"{name} appears to instruct VPS deployment: {line.strip()}"


@pytest.mark.parametrize("name", OPERATOR_DOCS)
def test_no_production_claims(name):
    text = _read(name)
    for forbidden in ("PRODUCTION_READY", "LOCAL_PRODUCTION_READY"):
        assert forbidden not in text, f"{name} claims {forbidden}"


def test_quickstart_gives_a_windows_hard_kill_recipe():
    """Recovery drills require a hard kill; it must be a real Windows command."""
    text = _read("AHOS_OPERATOR_QUICKSTART_WINDOWS.md")
    assert "Stop-Process" in text and "-Force" in text
    assert "Get-Process" in text


def test_quickstart_mandates_the_local_evidence_namespace():
    text = _read("AHOS_OPERATOR_QUICKSTART_WINDOWS.md")
    assert 'AHOS_EVIDENCE_SOURCE = "local"' in text
    # and warns about the sandbox default
    assert "NOT calibration-eligible" in text


def test_quickstart_does_not_lower_calibration_guards():
    text = _read("AHOS_OPERATOR_QUICKSTART_WINDOWS.md")
    assert "Never lower them" in text
    assert "INSUFFICIENT_DATA" in text


def test_quickstart_refuses_tls_bypass():
    flat = " ".join(_read("AHOS_OPERATOR_QUICKSTART_WINDOWS.md").split())
    assert "Do **not** disable TLS verification" in flat


def test_powershell_blocks_do_not_use_posix_line_continuations():
    """A trailing backslash continues a line in bash, not in PowerShell."""
    for name in OPERATOR_DOCS:
        for i, line in enumerate(_read(name).splitlines(), 1):
            stripped = line.rstrip()
            if stripped.endswith("\\") and not stripped.lstrip().startswith((">", "|", "#")):
                # Windows path fragments legitimately end in a backslash only
                # inside prose/tables; a code continuation is the risk.
                assert not stripped.lstrip().startswith("python"), \
                    f"{name}:{i} uses a bash line continuation: {stripped}"
