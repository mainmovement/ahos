#!/usr/bin/env python3
"""Phase 18 — Windows launcher regressions.

`start_ahos.ps1` and `start_ahos.bat` are the double-click entry points. Before
Phase 18 they started the daemon WITHOUT `--observation-cycle` and without
declaring the `local` evidence namespace, so an operator would watch a healthy
daemon log cycles while it produced no outcome labels and no calibration-
eligible predictions.

These tests pin the corrected form. They are deliberately strict: a launcher is
the one surface where a silent regression costs the operator real days.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LAUNCHERS = ("start_ahos.ps1", "start_ahos.bat")

CANONICAL = "--daemon --interval-sec 60 --observation-cycle"


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


@pytest.mark.parametrize("name", LAUNCHERS)
def test_launcher_exists(name):
    assert (ROOT / name).is_file(), f"missing launcher: {name}"


@pytest.mark.parametrize("name", LAUNCHERS)
def test_launcher_uses_the_canonical_daemon_command(name):
    """The exact command the directive mandates."""
    assert CANONICAL in _read(name), (
        f"{name} must invoke `{CANONICAL}`")


@pytest.mark.parametrize("name", LAUNCHERS)
def test_launcher_never_starts_daemon_without_observation_cycle(name):
    """Guards the specific regression: --daemon present, flag absent.

    Without --observation-cycle the E-01 poller and the frozen Lane-A outcome
    labeler never run, so calibration can never produce a pair regardless of
    uptime (M-GAP-014).
    """
    for i, line in enumerate(_read(name).splitlines(), 1):
        if "architecture.runtime" not in line or "--daemon" not in line:
            continue
        if line.lstrip().startswith(("REM", "#")):
            continue                       # commentary, not an invocation
        assert "--observation-cycle" in line, (
            f"{name}:{i} starts the daemon without --observation-cycle: {line.strip()}")


@pytest.mark.parametrize("name", LAUNCHERS)
def test_launcher_declares_the_local_evidence_namespace(name):
    """Only `local` rows are calibration-eligible; the runtime default is `sandbox`."""
    text = _read(name)
    assert "AHOS_EVIDENCE_SOURCE" in text and "local" in text
    # Belt and braces: the explicit flag outranks the environment variable.
    assert "--evidence-source local" in text


@pytest.mark.parametrize("name", LAUNCHERS)
def test_launcher_initializes_databases_before_starting(name):
    """A fresh clone has no stores; the daemon must not be first to touch them."""
    assert "init_databases.py --with-guards" in _read(name)


@pytest.mark.parametrize("name", LAUNCHERS)
def test_launcher_has_crlf_line_endings(name):
    """cmd.exe mis-parses LF-only .bat files; the pair is pinned together."""
    raw = (ROOT / name).read_bytes()
    crlf = raw.count(b"\r\n")
    bare_lf = raw.count(b"\n") - crlf
    assert crlf > 0, f"{name} has no CRLF line endings"
    assert bare_lf == 0, f"{name} contains {bare_lf} bare LF line endings"


def test_gitattributes_pins_launcher_line_endings():
    """Without this, a Linux checkout would silently rewrite them to LF."""
    attrs = _read(".gitattributes")
    assert re.search(r"\*\.bat\s+text\s+eol=crlf", attrs)
    assert re.search(r"\*\.ps1\s+text\s+eol=crlf", attrs)


@pytest.mark.parametrize("name", LAUNCHERS)
def test_launcher_declares_paper_only(name):
    text = _read(name)
    assert "AHOS_PAPER_ONLY" in text
    assert "OPERATOR_READY" in text or "pre_soak_entry_ok" in text or "NOT_VERIFIED" in text or "WINDOWS_OPERATOR_HANDOFF" in text


def test_install_windows_is_operator_prep_not_readiness():
    """install_windows.ps1 must prep the host without inventing OPERATOR_READY."""
    text = _read("install_windows.ps1")
    assert "requirements.txt" in text
    assert "npm install" in text
    assert "init_databases.py --with-guards" in text
    assert "AHOS_PAPER_ONLY" in text
    assert ".env.example" in text
    assert "operator_validation_gate.py" in text
    assert "OPERATOR_READY" in text and "NOT_VERIFIED" in text
    # Must not auto-start soak daemon or claim production.
    assert "--daemon" not in text or "do NOT" in text.lower() or "NOT start" in text or "pre_soak" in text.lower()
    assert "deployment\\.env" not in text or "NOT the" in text or "not the" in text.lower()
    # Default path must not force a live single-cycle (SeedEvidence is opt-in).
    assert "SeedEvidence" in text
    assert "PRODUCTION_READY" not in text or "never" in text.lower()


def test_install_windows_has_crlf_line_endings():
    raw = (ROOT / "install_windows.ps1").read_bytes()
    crlf = raw.count(b"\r\n")
    bare_lf = raw.count(b"\n") - crlf
    assert crlf > 0, "install_windows.ps1 has no CRLF line endings"
    assert bare_lf == 0, f"install_windows.ps1 contains {bare_lf} bare LF line endings"


def test_launcher_flags_are_accepted_by_the_runtime():
    """Every flag the launchers pass must really exist on the CLI."""
    proc = subprocess.run(
        [sys.executable, "-B", "-m", "architecture.runtime", "--help"],
        capture_output=True, text=True, timeout=120, cwd=str(ROOT))
    assert proc.returncode == 0, proc.stderr[-300:]
    for flag in ("--daemon", "--interval-sec", "--observation-cycle",
                 "--evidence-source"):
        assert flag in proc.stdout, f"runtime does not accept {flag}"


def test_evidence_source_local_is_a_valid_choice():
    from architecture.learning.score_ledger import (
        CALIBRATION_ELIGIBLE_SOURCES, resolve_source)

    assert resolve_source("local") == "local"
    assert "local" in CALIBRATION_ELIGIBLE_SOURCES


def test_documentation_no_longer_calls_the_launchers_unsuitable():
    """Phase 17 warned they were unusable; that guidance is now stale."""
    for doc in ("README.md", "AHOS_WINDOWS_DEPLOYMENT_GUIDE.md"):
        flat = " ".join(_read(doc).split())
        assert "do NOT use the one-click launchers" not in flat, (
            f"{doc} still carries the pre-Phase-18 warning")
        assert "omit `--observation-cycle`" not in flat, (
            f"{doc} still claims the launchers omit the flag")


def test_documentation_still_requires_the_gated_soak_procedure():
    """Fixing the launchers must not imply double-clicking starts a valid soak."""
    for doc in ("README.md", "AHOS_WINDOWS_DEPLOYMENT_GUIDE.md"):
        flat = " ".join(_read(doc).split())
        assert "AHOS_OPERATOR_QUICKSTART_WINDOWS.md" in flat, (
            f"{doc} must still point at the gated procedure")
