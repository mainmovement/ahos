"""Session-wide test bootstrap.

Why this file exists
--------------------
The SQLite stores under `data/` are gitignored, which is correct -- they are
generated state, not source. But 21 tests assert against a live database, so a
fresh `git clone` followed by `pytest` produced 21 failures on a repo that is
in fact perfectly healthy. The first thing a new user does is clone and run the
tests, so the first thing they saw was a broken project.

Two ways to fix that: make the tests skip when the databases are absent, or
make them present. Skipping is worse -- it silently drops real coverage of the
startup validator and the operational read-only intents, and a green run that
quietly tested less than it claims is exactly the kind of comfortable lie this
project's test suite is supposed to refuse.

So this creates the stores instead, once per session, by calling the same
idempotent bootstrap the quickstart tells the user to run
(`scripts/init_databases.py --with-guards`). If they already exist it is a
no-op, so a normal local run is unaffected.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# The stores the runtime's StartupValidator requires before it reports healthy.
REQUIRED_DATABASES = (
    "e01_discovery.sqlite",
    "paper_trading.sqlite",
    "ahos_local.sqlite",
    "ahos_knowledge.sqlite",
)


def _missing_databases() -> list[str]:
    data_dir = ROOT / "data"
    return [name for name in REQUIRED_DATABASES if not (data_dir / name).exists()]


@pytest.fixture(scope="session", autouse=True)
def ensure_databases_exist():
    """Guarantee the SQLite stores exist before any test runs.

    Runs the project's own bootstrap script rather than reimplementing the
    schema here -- duplicating DDL in a conftest is how test and production
    schemas drift apart.
    """
    missing = _missing_databases()
    if not missing:
        return

    script = ROOT / "scripts" / "init_databases.py"
    if not script.exists():  # pragma: no cover - repo layout guard
        pytest.exit(f"bootstrap script not found at {script}", returncode=1)

    result = subprocess.run(
        [sys.executable, str(script), "--with-guards"],
        cwd=str(ROOT), capture_output=True, text=True, timeout=300,
    )

    still_missing = _missing_databases()
    if still_missing:  # pragma: no cover - only on a genuinely broken bootstrap
        pytest.exit(
            "database bootstrap did not produce the required stores: "
            f"{still_missing}\n"
            f"exit={result.returncode}\n"
            f"stdout:\n{result.stdout[-2000:]}\n"
            f"stderr:\n{result.stderr[-2000:]}",
            returncode=1,
        )
