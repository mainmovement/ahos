"""MISSION P0-001 — Import safety and tracked-evidence integrity.

THE INVARIANT
-------------
    IMPORTING_A_MODULE_MUST_NOT_MUTATE_TRACKED_EVIDENCE

Importing a module may define names. It may not write files, contact the
network, or mutate tracked evidence under ``reports/``.

WHY THIS FILE EXISTS
--------------------
``engine/data_audit.py``, ``engine/dryrun_simulation.py`` and
``engine/telegram_live_test.py`` each ran their entire workload -- including
the ``reports/`` write and ``sys.exit()`` -- at module scope. Because
``scripts/validate_imports.py`` imports every module in a fresh interpreter to
prove it imports cleanly, running the gate silently overwrote three tracked
evidence artifacts. One was replaced with an audit of a *different* dataset
that reported FAIL, destroying a recorded PASS with no warning.

These modules are legitimate CLI scripts (``engine/run_all_checks.sh``
stages 1/4/5, ``docs/TELEGRAM_TEST_PROCEDURE.md``). The fix is therefore not
to stop calling them, and not to exclude them from the gate -- it is to make
them import-safe while preserving CLI semantics exactly.

TEST STRATEGY
-------------
1. Import-safety: hash every tracked ``reports/`` file, import, hash again.
   Any delta is a failure.
2. Adversarial: repeat the import with Telegram credentials exported and a
   socket tripwire installed, so a network attempt or a real send fails loudly
   instead of passing quietly.
3. CLI contract: exit code and stdout shape still usable by run_all_checks.sh.
   ``AHOS_ROOT`` redirects the write to a temp dir so the test itself never
   touches tracked evidence.
4. Exit-code-1 contract: the CI gate runs under ``set -euo pipefail``, so the
   failure signal must survive. Forcing a scenario failure must still return 1
   after the refactor -- this is the single highest-risk regression.
5. Structural guard: an AST check so the defect class cannot silently return.
"""
from __future__ import annotations

import ast
import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ENGINE = ROOT / "engine"

# Modules refactored under MISSION P0-001.
REFACTORED = ["engine.data_audit", "engine.dryrun_simulation", "engine.telegram_live_test"]
# Same defect class, still unfixed at the time this file was written.
KNOWN_RELATED = ["engine.run_validation"]


# --------------------------------------------------------------------- helpers
def _tracked_reports_snapshot() -> dict[str, str]:
    """sha256 of every tracked file under reports/ (the historical record)."""
    proc = subprocess.run(["git", "ls-files", "reports/"], cwd=ROOT,
                          capture_output=True, text=True)
    snap: dict[str, str] = {}
    for rel in proc.stdout.split():
        path = ROOT / rel
        if path.is_file():
            snap[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return snap


def _import_code(module: str) -> str:
    """Import `module` with outbound networking booby-trapped."""
    return (
        "import sys, socket\n"
        "sys.path.insert(0, %r)\n"
        "def _tripwire(*a, **k):\n"
        "    raise AssertionError('NETWORK CONTACT DURING IMPORT')\n"
        "socket.socket.connect = _tripwire\n"
        "socket.create_connection = _tripwire\n"
        "import %s\n"
        "print('IMPORTED_OK')\n" % (str(ROOT), module)
    )


# ------------------------------------------------- 1. import must not mutate
@pytest.mark.parametrize("module", REFACTORED)
def test_import_does_not_mutate_tracked_evidence(module: str) -> None:
    """The invariant, stated directly.

    Deliberately runs with Telegram credentials exported: that is the
    condition under which the old code performed real network sends.
    """
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["TELEGRAM_BOT_TOKEN"] = "000000000:IMPORT_SAFETY_TEST_NOT_A_REAL_TOKEN"
    env["TELEGRAM_ADMIN_CHAT_ID"] = "1"

    before = _tracked_reports_snapshot()
    proc = subprocess.run([sys.executable, "-B", "-c", _import_code(module)],
                          cwd=ROOT, env=env, capture_output=True, text=True, timeout=180)
    after = _tracked_reports_snapshot()

    combined = proc.stdout + proc.stderr
    assert "NETWORK CONTACT" not in combined, f"{module} contacted the network on import"
    assert "IMPORTED_OK" in proc.stdout, (
        f"{module} failed to import (rc={proc.returncode}):\n{combined[-800:]}"
    )
    mutated = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    assert not mutated, f"{module} mutated tracked evidence on import: {mutated}"


@pytest.mark.parametrize("module", REFACTORED)
def test_import_does_not_exit_the_interpreter(module: str) -> None:
    """A script's pass/fail result must not become an import result."""
    proc = subprocess.run([sys.executable, "-B", "-c", f"import sys; sys.path.insert(0, {str(ROOT)!r}); import {module}"],
                          cwd=ROOT, capture_output=True, text=True, timeout=180)
    assert proc.returncode == 0, (
        f"{module} exited non-zero on import; its scenario result is leaking "
        f"into import semantics: {proc.stderr[-500:]}"
    )


# ------------------------------------------------------------ 2. CLI contract
@pytest.mark.parametrize("script", ["data_audit.py", "dryrun_simulation.py", "telegram_live_test.py"])
def test_cli_still_runs_and_exits_zero(tmp_path: Path, script: str) -> None:
    """AHOS_ROOT redirects the reports write so this test stays read-only.

    AHOS_ROOT relocates BOTH the reports output and ``get_research_dir()``, so
    the dataset the scripts read has to be reachable from the temp root too.
    Symlinking keeps the input real while the output stays disposable --
    otherwise the test would be asserting against fabricated data.
    """
    research_src = ROOT / "research"
    if research_src.is_dir():
        (tmp_path / "research").symlink_to(research_src, target_is_directory=True)

    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["AHOS_ROOT"] = str(tmp_path)
    proc = subprocess.run([sys.executable, str(ENGINE / script), "--simulate"],
                          cwd=ROOT, env=env, capture_output=True, text=True, timeout=300)
    assert proc.returncode == 0, f"{script} CLI failed: {proc.stderr[-800:]}"
    assert proc.stdout.strip(), f"{script} CLI produced no stdout"
    # The redirected write must have landed in temp, not in the repo.
    assert (tmp_path / "reports").is_dir(), f"{script} did not write under AHOS_ROOT"


# ------------------------------------------------- 3. exit-code-1 must survive
def test_dryrun_returns_one_when_a_scenario_fails(tmp_path: Path, monkeypatch) -> None:
    """Highest-risk regression: `set -e` in run_all_checks.sh depends on this."""
    import engine.dryrun_simulation as dryrun

    monkeypatch.setattr(dryrun, "get_reports_dir", lambda **kw: tmp_path)
    monkeypatch.setattr(dryrun, "position_size", lambda *a, **k: 0.0)  # breaks S7_risk_caps
    dryrun.LOG.clear()
    assert dryrun.main() == 1
    assert any(entry["result"] == "FAIL" for entry in dryrun.LOG)


def test_telegram_returns_one_when_a_check_fails(tmp_path: Path, monkeypatch) -> None:
    """Same contract for the harness: failures must still abort the CI gate."""
    import engine.telegram_live_test as tgh

    def _dead_transport(method, **params):
        raise RuntimeError("simulated transport failure for exit-code test")

    monkeypatch.setattr(tgh, "get_reports_dir", lambda **kw: tmp_path)
    monkeypatch.setattr(tgh, "AUDIT_DB", str(tmp_path / "audit.sqlite"))
    monkeypatch.setattr(tgh, "TOKEN", None)      # force SIMULATED
    monkeypatch.setattr(tgh, "CHAT_ID", None)
    monkeypatch.setattr(tgh, "tg_mock", _dead_transport)
    tgh.RESULTS.clear()
    assert tgh.main() == 1
    assert any(r["status"] == "FAIL" for r in tgh.RESULTS)


# --------------------------------------------------------- 4. structural guard
@pytest.mark.parametrize("module", REFACTORED)
def test_module_scope_has_no_execution_or_writes(module: str) -> None:
    """AST guard so this defect class cannot quietly return.

    Allows constants, imports, function/class definitions and `if __name__`
    blocks. Rejects calls, `with open(...)` and bare writes at module scope.
    """
    tree = ast.parse((ENGINE / module.split(".")[-1]).with_suffix(".py").read_text(encoding="utf-8"))
    offenders: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            offenders.append(f"L{node.lineno}: bare call")
        elif isinstance(node, ast.With):
            offenders.append(f"L{node.lineno}: module-level `with`")
        elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            name = getattr(node.value.func, "id", getattr(node.value.func, "attr", "?"))
            if name in {"open", "connect"}:
                offenders.append(f"L{node.lineno}: module-level {name}()")
    assert not offenders, f"{module} has module-scope execution: {offenders}"


@pytest.mark.parametrize("module", REFACTORED)
def test_reusable_api_survives_the_refactor(module: str) -> None:
    """Shape C: pure helpers stay importable; that was the point."""
    mod = __import__(module, fromlist=["main"])
    assert callable(getattr(mod, "main", None)), f"{module}.main() missing"

    expected = {
        "engine.data_audit": ["sha256", "audit_file"],
        "engine.dryrun_simulation": ["signal_eval", "guard", "record"],
        "engine.telegram_live_test": ["classify", "audit", "tg_mock", "tg_real"],
    }[module]
    for name in expected:
        assert callable(getattr(mod, name, None)), f"{module}.{name}() is not importable"


# ------------------------------------------------- 5. related, still-unfixed
@pytest.mark.xfail(reason="engine/run_validation.py still runs + writes at module scope", strict=True)
def test_related_pattern_run_validation_is_import_safe() -> None:
    """Pins the neighbouring instance of the same defect.

    It is excluded from validate_imports' probe, which hides it rather than
    fixes it. When someone applies the same treatment, this test flips to
    XPASS and strict=True makes that a failure -- prompting removal of the
    xfail marker and of the IMPORT_EXCLUDE entry.
    """
    before = _tracked_reports_snapshot()
    subprocess.run([sys.executable, "-B", "-c", _import_code("engine.run_validation")],
                   cwd=ROOT, capture_output=True, text=True, timeout=180)
    after = _tracked_reports_snapshot()
    mutated = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    assert not mutated, f"engine.run_validation mutated tracked evidence: {mutated}"
