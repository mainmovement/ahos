"""M9 part B regression: import-time side effects must stay fixed.

Two defects found by scripts/audit_import_side_effects.py and fixed:

* engine/bot_skeleton.py called sys.exit(2) at module scope when the Telegram
  credentials were absent, so merely importing it terminated the interpreter.
* engine/run_validation.py ran the entire backtest pipeline and wrote
  reports/validation_results.json at module scope, so importing it recomputed
  (and could overwrite) recorded evidence.

Both now import clean. These tests pin that.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "engine"


def _import_in_subprocess(module: str, env_extra: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    code = (
        "import sys\n"
        "sys.path.insert(0, %r)\n"
        "import %s\n"
        "print('IMPORTED_OK')\n" % (str(ROOT), module)
    )
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("TELEGRAM_BOT_TOKEN", None)
    env.pop("TELEGRAM_ADMIN_CHAT_ID", None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT,
                          capture_output=True, text=True, timeout=180)


def test_bot_skeleton_import_does_not_exit_interpreter() -> None:
    """With credentials absent the module must import, not sys.exit(2)."""
    proc = _import_in_subprocess("engine.bot_skeleton")
    assert "IMPORTED_OK" in proc.stdout, \
        f"import terminated early: rc={proc.returncode} err={proc.stderr[-300:]}"
    assert proc.returncode == 0


def test_bot_skeleton_still_refuses_to_run_without_credentials() -> None:
    """The guard moved into main(), not removed: launching still refuses."""
    code = (
        "import sys\n"
        "sys.path.insert(0, %r)\n"
        "sys.argv = ['bot_skeleton']\n"
        "import engine.bot_skeleton as b\n"
        "try:\n"
        "    b.main()\n"
        "    print('NO_EXIT')\n"
        "except SystemExit as e:\n"
        "    print('EXIT_' + str(e.code))\n" % str(ROOT)
    )
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("TELEGRAM_BOT_TOKEN", None)
    env.pop("TELEGRAM_ADMIN_CHAT_ID", None)
    proc = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT,
                          capture_output=True, text=True, env=env, timeout=180)
    assert "EXIT_2" in proc.stdout, \
        f"main() must exit(2) without credentials: {proc.stdout[-200:]} {proc.stderr[-200:]}"


def test_run_validation_exposes_pure_entry_points() -> None:
    """The pipeline is reachable as functions, not as import-time execution."""
    code = (
        "import sys\n"
        "sys.path.insert(0, %r)\n"
        "from engine import run_validation as rv\n"
        "assert callable(rv.build_report), 'build_report missing'\n"
        "assert callable(rv.print_report), 'print_report missing'\n"
        "assert callable(rv.main), 'main missing'\n"
        "print('ENTRYPOINTS_OK')\n" % str(ROOT)
    )
    proc = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT,
                          capture_output=True, text=True, timeout=180)
    assert "ENTRYPOINTS_OK" in proc.stdout, proc.stderr[-400:]
