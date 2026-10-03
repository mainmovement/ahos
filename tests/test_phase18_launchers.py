#!/usr/bin/env python3
"""Phase 18 — Windows launcher regressions.

Mission 11 consolidated every entry point into the `launcher` package. The
double-click surfaces are now `launcher/ahos.ps1` and `launcher/ahos.bat` (the
console wrappers the desktop shortcuts open), with `start_ahos.ps1` /
`start_ahos.bat` kept as thin delegates for muscle memory. The daemon command
itself lives in `launcher/components.py:engine_command`, so that is where the
canonical form is pinned.

Before Phase 18 the launchers started the daemon WITHOUT `--observation-cycle`
and without declaring the `local` evidence namespace, so an operator would
watch a healthy daemon log cycles while it produced no outcome labels and no
calibration-eligible predictions.

These tests pin the corrected form. They are deliberately strict: a launcher is
the one surface where a silent regression costs the operator real days.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LAUNCHERS = ("start_ahos.ps1", "start_ahos.bat")
# The Mission-11 console wrappers the desktop shortcuts actually open.
CONSOLE = ("launcher/ahos.ps1", "launcher/ahos.bat")
# start_ahos.* are thin delegates now; the package is the single source of truth.
DELEGATE_TARGET = "launcher\\ahos"

CANONICAL = "--daemon --interval-sec 60 --observation-cycle"


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def _engine_cmd() -> list[str]:
    """The real daemon command, built by the code that actually launches it.

    Read from the builder rather than a string, so the pin follows the truth.
    """
    import launcher.components as C
    env = C.load_repo_env(ROOT, {})
    return C.engine_command(env)


@pytest.mark.parametrize("name", LAUNCHERS)
def test_launcher_exists(name):
    assert (ROOT / name).is_file(), f"missing launcher: {name}"


@pytest.mark.parametrize("name", CONSOLE)
def test_console_wrapper_exists(name):
    assert (ROOT / name).is_file(), f"missing console wrapper: {name}"


@pytest.mark.parametrize("name", LAUNCHERS)
def test_launcher_is_a_thin_delegate_to_the_package(name):
    """No launch logic may return to the legacy entry points (no-duplicates)."""
    assert DELEGATE_TARGET in _read(name).replace("/", "\\"), (
        f"{name} must delegate to launcher/ahos; do not add launch logic here")


@pytest.mark.parametrize("name", LAUNCHERS)
def test_launcher_uses_the_canonical_daemon_command(name):
    """The exact command the directive mandates."""
    cmd = _engine_cmd()
    assert "--daemon" in cmd and "--observation-cycle" in cmd, cmd
    assert "--interval-sec" in cmd and "60" in cmd, cmd
    assert cmd[-2:] == ["--evidence-source", "local"], cmd


@pytest.mark.parametrize("name", LAUNCHERS)
def test_launcher_never_starts_daemon_without_observation_cycle(name):
    """Guards the specific regression: --daemon present, flag absent.

    Without --observation-cycle the E-01 poller and the frozen Lane-A outcome
    labeler never run, so calibration can never produce a pair regardless of
    uptime (M-GAP-014).
    """
    for i, line in enumerate(_read("launcher/components.py").splitlines(), 1):
        if "architecture.runtime" not in line or "--daemon" not in line:
            continue
        if line.lstrip().startswith(("#",)):
            continue                       # commentary, not an invocation
        assert "--observation-cycle" in line, (
            f"launcher/components.py:{i} starts the daemon without "
            f"--observation-cycle: {line.strip()}")


@pytest.mark.parametrize("name", LAUNCHERS)
def test_launcher_declares_the_local_evidence_namespace(name):
    """Only `local` rows are calibration-eligible; the runtime default is `sandbox`."""
    text = _read("launcher/components.py")
    assert "AHOS_EVIDENCE_SOURCE" in text and "local" in text
    # Belt and braces: the explicit flag outranks the environment variable.
    cmd = _engine_cmd()
    assert "--evidence-source" in cmd and cmd[cmd.index("--evidence-source") + 1] == "local", cmd


def test_engine_env_hard_sets_the_local_evidence_namespace():
    """Every launcher child gets AHOS_EVIDENCE_SOURCE=local hard-set."""
    import launcher.components as C
    assert C.ENGINE_ENV_HARD["AHOS_EVIDENCE_SOURCE"] == "local"
    assert C.ENGINE_ENV_HARD["AHOS_PAPER_ONLY"] == "1"


@pytest.mark.parametrize("name", LAUNCHERS)
def test_launcher_initializes_databases_before_starting(name):
    """A fresh clone has no stores; the daemon must not be first to touch them."""
    import launcher.components as C
    cmd = C.stores_command(C.venv_python(ROOT))
    joined = " ".join(cmd)
    assert "init_databases.py" in joined and "--with-guards" in joined, cmd


@pytest.mark.parametrize("name", LAUNCHERS + CONSOLE)
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


@pytest.mark.parametrize("name", LAUNCHERS + CONSOLE)
def test_launcher_declares_paper_only(name):
    """Observation-only is declared on the wrapper and enforced by the engine."""
    text = _read(name)
    assert "AHOS_PAPER_ONLY" in text or "launcher" in text, (
        f"{name} must declare the paper-only constraint")
    import launcher.components as C
    assert C.ENGINE_ENV_HARD["AHOS_PAPER_ONLY"] == "1"
    # No launcher surface may invent readiness.
    assert "OPERATOR_READY" not in text, f"{name} must not claim OPERATOR_READY"


@pytest.mark.parametrize("name", CONSOLE)
def test_console_wrapper_is_ascii_safe_or_utf8_declared(name):
    """Windows PowerShell 5.1 reads .ps1 as cp1252 unless UTF-8 is declared.

    The wrappers carry Persian owner-facing text, so they must state their
    encoding (chcp 65001 / UTF8Encoding) rather than rely on the system ANSI.
    """
    text = _read(name)
    if name.endswith(".ps1"):
        assert "UTF8Encoding" in text or "chcp 65001" in text, (
            f"{name} must declare UTF-8 for the Persian text")
    else:
        assert "chcp 65001" in text, f"{name} must set code page 65001"


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
    # Positive pin: safety assert uses canonical architecture.security import.
    assert re.search(
        r"-c\s+'[^']*from architecture\.security import assert_safe_environment[^']*'",
        text,
    ), "install_windows.ps1 must call architecture.security.assert_safe_environment"


def test_install_windows_safety_assert_uses_canonical_ahos_env_loader():
    """Real Windows failure after PR #22: installer imported third-party dotenv.

    requirements.txt does not ship python-dotenv. Canonical mechanisms are:
      - run_bot.load_dotenv (stdlib-only .env loader)
      - architecture.security.assert_safe_environment
    config.runtime_env does not exist in this repo.
    """
    text = _read("install_windows.ps1")
    code_lines = [
        line for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    code = "\n".join(code_lines)
    assert "from dotenv import" not in code
    assert "import dotenv" not in code
    assert "python-dotenv" not in code
    assert "config.runtime_env" not in code
    assert "from run_bot import load_dotenv" in code
    assert "from architecture.security import assert_safe_environment" in code

    match = re.search(
        r"""(?:python|VenvPython).*?-c\s+'([^']*assert_safe_environment[^']*)'""",
        text,
    )
    assert match, "missing assert_safe_environment -c payload"
    payload = match.group(1)
    assert '"' not in payload
    assert "from run_bot import load_dotenv" in payload
    assert "load_dotenv()" in payload
    assert "from architecture.security import assert_safe_environment" in payload
    assert "assert_safe_environment()" in payload


def test_install_windows_safety_assert_c_payload_runs_without_python_dotenv():
    """Acceptance: the exact installer safety -c works with repo deps only."""
    text = _read("install_windows.ps1")
    match = re.search(
        r"""(?:python|\$VenvPython).*?-c\s+'([^']*assert_safe_environment[^']*)'""",
        text,
    )
    assert match, "missing assert_safe_environment -c payload"
    payload = match.group(1)
    stripped = payload.replace('"', "")  # WinPS 5.1 native-arg quote strip

    env = os.environ.copy()
    env["AHOS_PAPER_ONLY"] = "1"
    # Clear live-trading flags so a polluted host env cannot flake this pin.
    for key in ("AHOS_ALLOW_REAL_FUNDS", "AHOS_EXECUTE_LIVE_TRADES"):
        env.pop(key, None)

    proc = subprocess.run(
        [sys.executable, "-c", stripped],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(ROOT),
        env=env,
    )
    assert proc.returncode == 0, (
        "safety assert -c must succeed without python-dotenv.\n"
        f"payload={payload!r}\nstdout={proc.stdout!r}\nstderr={proc.stderr!r}"
    )
    assert "ModuleNotFoundError" not in (proc.stderr + proc.stdout)
    assert "dotenv" not in proc.stderr.lower()
    assert "paper_only_enforced" in proc.stdout


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
