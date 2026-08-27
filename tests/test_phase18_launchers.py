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


def test_install_windows_is_ascii_only():
    """Windows PowerShell 5.1 often reads UTF-8 .ps1 as system ANSI (cp1252).

    UTF-8 em-dash bytes E2 80 94 become â€\" under that misread: the 0x94 byte
    is a curly quote in cp1252 and terminates double-quoted strings early, which
    is exactly the real Windows ParserError cascade (expression after '(', etc.).
    ASCII-only punctuation prevents that class of failure.
    """
    raw = (ROOT / "install_windows.ps1").read_bytes()
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        pytest.fail(f"install_windows.ps1 contains non-ASCII bytes: {exc}")
    assert all(ord(c) < 128 for c in text)


def test_install_windows_python_c_payloads_are_single_quoted():
    """Defense in depth: Python -c with () must not sit in PS double quotes."""
    text = _read("install_windows.ps1")
    # Flag any -c "..." form that embeds a Python call with parentheses.
    dangerous = re.findall(
        r"""-c\s+"[^"]*\([^"]*" """,
        text,
    )
    assert not dangerous, (
        "install_windows.ps1 must use single-quoted -c payloads when Python "
        f"code contains (); found: {dangerous!r}"
    )
    # Positive pin: safety assert uses single quotes.
    assert "-c 'from dotenv import load_dotenv" in text or (
        "-c 'from architecture.security import assert_safe_environment" in text
    ) or re.search(r"-c\s+'[^']*assert_safe_environment[^']*'", text)


def _install_windows_single_quoted_c_payloads() -> list[str]:
    """Extract every single-quoted python -c payload from the installer."""
    text = _read("install_windows.ps1")
    return re.findall(r"""-c\s+'([^']*)'""", text)


def test_install_windows_python_c_payloads_have_no_embedded_double_quotes():
    """WinPS 5.1 strips embedded \" when calling native python.exe.

    Real laptop failure after PR #21:
      print("%d.%d.%d" % sys.version_info[:3])
    arrived at Python as:
      print(%d.%d.%d % sys.version_info[:3])
    """
    payloads = _install_windows_single_quoted_c_payloads()
    assert payloads, "expected at least one single-quoted -c payload"
    for payload in payloads:
        assert '"' not in payload, (
            "install_windows.ps1 -c payloads must not embed double quotes "
            f"(WinPS 5.1 strips them): {payload!r}"
        )


def test_install_windows_python_version_check_survives_winps51_quote_stripping():
    """Acceptance criterion: version -c must work after WinPS 5.1 quote strip."""
    text = _read("install_windows.ps1")
    match = re.search(
        r"""python\s+-c\s+'([^']*sys\.version[^']*)'""",
        text,
    )
    assert match, "missing python -c version-check payload in install_windows.ps1"
    payload = match.group(1)
    assert "sys.version" in payload
    assert '"' not in payload

    # Simulate WinPS 5.1 native-arg quoting: strip every embedded ".
    stripped = payload.replace('"', "")
    proc = subprocess.run(
        [sys.executable, "-c", stripped],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, (
        "version-check -c failed under WinPS 5.1 quote-stripping simulation.\n"
        f"payload={payload!r}\nstripped={stripped!r}\n"
        f"stdout={proc.stdout!r}\nstderr={proc.stderr!r}"
    )
    version = proc.stdout.strip()
    assert re.fullmatch(r"\d+\.\d+\.\d+([a-zA-Z0-9.+_]*)?", version), (
        f"version-check must print a usable Python version, got {version!r}"
    )
    parts = version.split(".")
    assert len(parts) >= 2
    int(parts[0])
    int(parts[1])


def test_install_windows_python_version_check_via_pwsh_call():
    """Run the exact installer -c line through pwsh -> python (runtime path)."""
    pwsh = _find_pwsh()
    if pwsh is None:
        pytest.skip("pwsh not available for version-check runtime verification")

    text = _read("install_windows.ps1")
    match = re.search(
        r"""python\s+-c\s+'([^']*sys\.version[^']*)'""",
        text,
    )
    assert match, "missing python -c version-check payload"
    payload = match.group(1)
    # Prefer the same interpreter the test host uses; still goes through pwsh -c.
    py = sys.executable.replace("'", "''")
    # Single-quoted -c payload for pwsh, matching installer style.
    ps_payload = payload.replace("'", "''")
    proc = subprocess.run(
        [
            pwsh,
            "-NoProfile",
            "-Command",
            f"& '{py}' -c '{ps_payload}'",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, (
        f"pwsh->python version check failed.\nstdout={proc.stdout}\nstderr={proc.stderr}"
    )
    version = proc.stdout.strip()
    assert re.fullmatch(r"\d+\.\d+\.\d+([a-zA-Z0-9.+_]*)?", version), (
        f"expected version string, got {version!r}"
    )


def test_install_windows_survives_cp1252_misread_parse(tmp_path):
    """Regression for the real Windows laptop ParserError on PR #20 main.

    Simulate PS 5.1 opening a UTF-8 script as Windows-1252, then require the
    PowerShell AST parser to accept the result. Skips only if pwsh is absent.
    """
    pwsh = _find_pwsh()
    if pwsh is None:
        pytest.skip("pwsh not available for AST parse verification")

    raw = (ROOT / "install_windows.ps1").read_bytes()
    # Misread UTF-8 bytes as cp1252 (what Windows 5.1 does without BOM).
    misread = raw.decode("cp1252", errors="replace")
    victim = tmp_path / "install_windows_cp1252_misread.ps1"
    victim.write_text(misread, encoding="utf-8", newline="\n")

    proc = subprocess.run(
        [
            pwsh,
            "-NoProfile",
            "-Command",
            (
                "$t=$null; $e=$null; "
                "[void][System.Management.Automation.Language.Parser]::ParseFile("
                f"'{victim.as_posix()}', [ref]$t, [ref]$e); "
                "if ($e -and $e.Count) { $e | ForEach-Object { $_.ToString() }; exit 1 }; "
                "Write-Output 'PARSE_OK'"
            ),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, (
        "install_windows.ps1 must still parse after a cp1252 misread "
        f"(Windows 5.1 failure mode).\nstdout={proc.stdout}\nstderr={proc.stderr}"
    )
    assert "PARSE_OK" in proc.stdout


def test_install_windows_parses_under_pwsh():
    """Direct AST parse of the committed installer (CRLF, as in the repo)."""
    pwsh = _find_pwsh()
    if pwsh is None:
        pytest.skip("pwsh not available for AST parse verification")
    path = (ROOT / "install_windows.ps1").resolve()
    proc = subprocess.run(
        [
            pwsh,
            "-NoProfile",
            "-Command",
            (
                "$t=$null; $e=$null; "
                "[void][System.Management.Automation.Language.Parser]::ParseFile("
                f"'{path.as_posix()}', [ref]$t, [ref]$e); "
                "if ($e -and $e.Count) { $e | ForEach-Object { $_.ToString() }; exit 1 }; "
                "Write-Output ('PARSE_OK tokens=' + $t.Count)"
            ),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PARSE_OK" in proc.stdout


def _find_pwsh() -> str | None:
    from shutil import which

    return which("pwsh") or which("powershell")


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
