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


def _strip_ps_comments(text: str) -> str:
    """Drop PowerShell comments, so a structural test never matches a word that
    only appears in prose explaining the rule.

    Both forms: ``<# ... #>`` blocks and ``#`` to end-of-line. Inside a string
    literal a ``#`` is not a comment, but the wrapper has none, and the check is
    only ever applied to files that must not hide a prompt either way.
    """
    text = re.sub(r"<#.*?#>", "", text, flags=re.S)
    return "\n".join(line for line in text.splitlines()
                     if not line.lstrip().startswith("#"))


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


# ------------------------------------------------------- no visible console ---
class TestNoVisibleConsole:
    """M11.1 scope (b): no path the one-click launcher takes may flash a console.

    On Windows a subprocess that lacks ``CREATE_NO_WINDOW`` allocates its own
    console; ``DETACHED_PROCESS`` makes Windows *ignore* ``CREATE_NO_WINDOW``,
    which was the original defect. This is an AST-level scan so a new call site
    cannot slip through unnoticed.
    """

    LAUNCHER_MODULES = ("launcher/",)

    def _call_sites(self):
        """(file, call_node, enclosing_function) for every child-process call.

        The enclosing name comes from a parent map, so nested and sibling
        functions are both resolved correctly (``ast.walk`` alone cannot answer
        "who contains this node" without one).
        """
        import ast
        CALL_FUNCS = ("run", "Popen", "call", "check_call", "check_output",
                      "system", "popen")
        for py in ROOT.glob("launcher/**/*.py"):
            if "__pycache__" in py.parts:
                continue
            tree = ast.parse(py.read_text(encoding="utf-8"))
            parents: dict[int, ast.AST] = {}
            for node in ast.walk(tree):
                for child in ast.iter_child_nodes(node):
                    parents[id(child)] = node
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                fn = node.func
                qual = []
                while isinstance(fn, ast.Attribute):
                    qual.append(fn.attr)
                    fn = fn.value
                if isinstance(fn, ast.Name):
                    qual.append(fn.id)
                qual = ".".join(reversed(qual))
                if qual.rsplit(".", 1)[-1] not in CALL_FUNCS:
                    continue
                if not (qual.startswith("subprocess.") or qual in
                        ("os.system", "os.popen")):
                    continue
                enclosing, cur = None, node
                while cur is not None:
                    cur = parents.get(id(cur))
                    if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        enclosing = cur.name
                        break
                yield py, node, enclosing

    # Call sites that may legitimately omit the flag. Kept explicit and tiny so
    # a new entry is a visible decision, not an accident: open_url's branch runs
    # only on POSIX and launches a GUI browser, never a console.
    FLAG_ALLOWLIST = {"open_url"}

    def test_every_subprocess_call_suppresses_a_window(self):
        names = {"creationflags", "shell", "windowsHide"}
        bad = []
        for py, node, enclosing in self._call_sites():
            kw = {k.arg for k in node.keywords if isinstance(k.arg, str)}
            if not names.isdisjoint(kw) or enclosing in self.FLAG_ALLOWLIST:
                continue
            bad.append(f"{py}:{node.lineno} {ast.unparse(node)[:90]}")
        assert not bad, ("subprocess without a window-suppressing flag: "
                         + "; ".join(bad))

    def test_spawn_detached_does_not_combine_detached_with_no_window(self):
        """The exact Windows defect: DETACHED_PROCESS makes CREATE_NO_WINDOW a
        no-op, so a console-less npm child allocates a *visible* console."""
        import launcher.processkit as pk
        flags = pk.CREATE_NEW_PROCESS_GROUP | pk.CREATE_NO_WINDOW
        assert not flags & pk.DETACHED_PROCESS

    def test_shortcut_and_wrapper_carry_windowstyle_hidden(self):
        assert "-WindowStyle Hidden" in _read("launcher/shortcuts.py")
        assert "-WindowStyle Hidden" in _read("launcher/ahos.ps1")

    def test_hidden_wrapper_path_never_blocks_on_read_host(self):
        """A hidden window has no keyboard; a Read-Host there pins the process
        forever and the dashboard's next action finds the module lock held."""
        text = _read("launcher/ahos.ps1")
        assert "$Console" in text, "the interactive prompt must be opt-in"
        # Structural check: delete every `if ($Console) { ... }` block by brace
        # matching, then no Read-Host may remain anywhere.
        marker = "if ($Console) {"
        out = text
        while marker in out:
            start = out.index(marker) + len(marker)
            depth = 1
            i = start
            while i < len(out) and depth:
                if out[i] == "{":
                    depth += 1
                elif out[i] == "}":
                    depth -= 1
                i += 1
            assert depth == 0, "unbalanced braces in the $Console guard"
            out = out[: out.index(marker)] + out[i:]
        assert "Read-Host" not in _strip_ps_comments(
            out), "a Read-Host lives outside the -Console guard"
        # and the hidden path must tee to a log instead of discarding output
        assert "launcher.log" in text

    def test_ahos_ps1_does_not_shadow_the_automatic_args_variable(self):
        """Shadowing ``$args`` breaks splatting of the real arguments."""
        source = _strip_ps_comments(_read("launcher/ahos.ps1"))
        assert "$args = " not in source
        assert "$PyArgs = " in source


# --------------------------------------------- M11.2: PS 5.1 hidden-path log ---
class TestM11_2_Ps51HiddenPath:
    r"""M11.2 — the hidden path must log under the real .lnk target.

    The desktop shortcut runs ``C:\Windows\System32\WindowsPowerShell\v1.0\
    powershell.exe``, i.e. Windows PowerShell 5.1, not PowerShell 7. Two 5.1
    specifics broke the original hidden path there and are pinned here:

    * ``Tee-Object -Encoding`` is a 7.2+ parameter (CHANGELOG 7.2 / #12135), so
      it threw under 5.1 and the log was never written;
    * ``$ErrorActionPreference = 'Stop'`` turns a redirected native ``stderr``
      line into a terminating ``NativeCommandError``, which re-entered a
      ``catch`` and ran the action a second time.

    Both were resolved structurally by M11.1 (commit ``d0141a9``, Finding R6 in
    ``docs/ONE_CLICK.md``): python owns the log file, so the shell runs a plain
    ``& $Python @PyArgs`` with no pipe and no redirection. These tests pin that
    shape so it cannot come back, plus the one defect M11.2's scope still held:
    the script is UTF-8 *with a BOM*, because Windows PowerShell 5.1 decodes a
    BOM-less file with the system ANSI codepage and its own Persian literals
    arrive as mojibake.
    """

    def test_ahos_ps1_is_utf8_with_a_bom(self):
        """WinPS 5.1 has no encoding sniffing: no BOM means cp1252 decoding.

        The fatal no-venv branch prints Persian from the shell itself -- python
        cannot be started to print it -- so the file must declare its encoding.
        Verified against the real 5.1 binary on the owner host: without the BOM
        ``محیط پایتون پیدا نشد`` arrived as
        ``Ù…Ø­ÛŒØ· Ù¾Ø§ÛŒØªÙˆÙ† Ù¾ÛŒØ¯Ø§ Ù†Ø´Ø¯``; with it, correctly.
        """
        raw = (ROOT / "launcher/ahos.ps1").read_bytes()
        assert raw[:3] == b"\xef\xbb\xbf", (
            "launcher/ahos.ps1 must start with a UTF-8 BOM so Windows "
            "PowerShell 5.1 decodes its Persian literals instead of reading "
            "them as the system ANSI codepage")

    def test_no_tee_object_encoding_in_the_launcher(self):
        """``-Encoding`` on Tee-Object is 7.2+ and threw under PS 5.1.

        Stronger than the spec's wording: ``Tee-Object`` is absent from the
        whole launcher tree, so neither the parameter nor the cmdlet can return.
        """
        for py in ROOT.glob("launcher/**/*.ps1"):
            text = py.read_text(encoding="utf-8")
            assert "Tee-Object" not in text, (
                f"{py}: Tee-Object is a PS 7.2+ surface in the one-click path; "
                "python writes the log itself (M11.1 Finding R6)")

    def test_the_python_action_is_never_re_run_from_a_catch(self):
        """A ``catch`` must never re-invoke python.

        Under ``$ErrorActionPreference = 'Stop'`` a redirected stderr line
        throws; a python call in the handler would run the action twice -- a
        double start, or a stop followed by a start. Brace-match every
        ``catch`` and require the handler body to be python-free.
        """
        text = _strip_ps_comments(_read("launcher/ahos.ps1"))
        for body in _ps_catch_bodies(text):
            assert "$Python" not in body, (
                "a catch block must not invoke python (double-run risk under "
                f"$ErrorActionPreference='Stop'): {body.strip()[:80]!r}")

    def test_no_powershell_pipe_wraps_the_python_call(self):
        """The R6 defect: a pipe outlives python and wedges the hidden shell.

        A PowerShell pipe ends when its *write* end closes, not when python
        exits, and the launcher's detached children inherit that handle. A
        restart stops the gateway that spawned the shell, python exits, and the
        shell stays pinned on the pipe reader forever, holding the module lock
        the dashboard's next stop/restart needs. So the hidden path must not
        wrap the python call in a pipe.
        """
        text = _strip_ps_comments(_read("launcher/ahos.ps1"))
        assert "Tee-Object" not in text
        # No `| Out-File` / `| Tee-Object` redirecting python's output.
        assert not re.search(r"\|\s*(Out-File|Tee-File|Tee-Object)", text), (
            "the hidden path must not capture python through a PowerShell pipe")
        assert not re.search(r"&\s*\$Python[^|\r\n]*\|", text), (
            "python must be invoked bare; a pipe outlives it and wedges the shell")

    def test_hidden_path_names_the_log_python_writes(self):
        """The hidden path's log contract: the ps1 names the file, python writes it.

        The spec lists ``[IO.File]::AppendAllText`` / ``Out-File -Encoding utf8``
        as the mechanism. That was the R5 design, superseded by R6 in M11.1:
        the ps1 now exports ``AHOS_LAUNCHER_LOG`` and
        ``launcher/__main__.py:_install_log_tee`` appends to it from Python,
        file-first and UTF-8. Pinning the R5 cmdlets would re-forbid the fix.
        """
        text = _strip_ps_comments(_read("launcher/ahos.ps1"))
        # The contract: the hidden (non-Console) branch sets the env var.
        assert "AHOS_LAUNCHER_LOG" in text, (
            "the hidden path must name the log file so python can write it")
        assert re.search(r"if\s*\(\s*-not\s+\$Console\s*\)", text), (
            "the log contract belongs to the hidden path, not -Console")
        # The writer, on the python side: file-first so a bad console codepage
        # can never cost the log line.
        py = _read("launcher/__main__.py")
        assert "AHOS_LAUNCHER_LOG" in py, (
            "launcher/__main__.py must honour the AHOS_LAUNCHER_LOG contract")
        assert 'encoding="utf-8"' in py, "the log must be written as UTF-8"
        assert "_install_log_tee" in py

    def test_pythons_exit_code_reaches_the_shell_exit(self):
        """``$LASTEXITCODE`` must propagate so a failed start is not reported OK."""
        text = _strip_ps_comments(_read("launcher/ahos.ps1"))
        assert re.search(r"\$rc\s*=\s*\$LASTEXITCODE", text), (
            "the shell must capture python's exit code")
        assert re.search(r"exit\s+\$rc", text), (
            "the shell must exit with python's exit code")

    def test_ps51_renders_the_fatal_message_correctly(self, tmp_path):
        r"""Acceptance: the real PS 5.1 binary decodes the committed script.

        The script is copied into a venv-less ``sub/`` so ``$PSScriptRoot\..``
        has no ``.venv\Scripts\python.exe``; that is the fatal branch, where
        python cannot print anything and the shell's own Persian message is the
        only diagnostic the owner ever sees. Skips only where no PowerShell
        exists (the Linux CI box).
        """
        pwsh = _find_pwsh()
        if pwsh is None:
            pytest.skip("no powershell/pwsh available to run the wrapper")

        sub = tmp_path / "sub"
        sub.mkdir()
        victim = sub / "ahos.ps1"
        # Copy bytes so the BOM and the CRLF both survive.
        victim.write_bytes((ROOT / "launcher/ahos.ps1").read_bytes())

        proc = subprocess.run(
            [pwsh, "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", str(victim), "-Action", "start"],
            capture_output=True, timeout=120,
        )
        # exit 3 is the documented no-venv code; the message must be intact.
        assert proc.returncode == 3, (
            f"expected exit 3 on the missing-venv path, got "
            f"{proc.returncode}\nstdout={proc.stdout!r}\nstderr={proc.stderr!r}")
        text = proc.stdout.decode("utf-8", "replace")
        assert "محیط پایتون پیدا نشد" in text, (
            "the fatal no-venv message arrived as mojibake under this "
            f"PowerShell (a missing UTF-8 BOM): {text[:120]!r}")


def _ps_catch_bodies(text: str):
    """Yield the body of every ``catch { ... }`` block in a PowerShell script.

    Brace-matched from the handler's own opening brace (depth starts at 1), so
    a nested ``try { }`` inside the handler does not end the match early. A
    ``catch`` may carry a filter (``catch [System.Exception] {``).
    """
    for m in re.finditer(r"\bcatch\b", text):
        i = m.end()
        # Skip an optional exception filter, which may itself brace-balance.
        while i < len(text) and text[i] not in "{":
            i += 1
        if i >= len(text):
            break
        depth, start, j = 1, i + 1, i + 1
        while j < len(text) and depth:
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    yield text[start:j]
                    break
            j += 1
