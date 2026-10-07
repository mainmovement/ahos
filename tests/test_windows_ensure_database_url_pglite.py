#!/usr/bin/env python3
"""Structural regression gate for scripts/windows_ensure_database_url.ps1 (M10).

Mission 10 Stage 4a gave the G2 operator entry point a first-class native
embedded backend (``pglite:<dataDir>``) alongside the Postgres path it already
had. Running the script is an operator act that rewrites ``.env``, so this gate
asserts the *branch structure* statically instead of executing it: the ordering
of the decisions is the safety property, and it can be checked without touching
a secret or flipping a backend.

What must hold:

* a URL that already works is never overwritten, on either backend;
* a failing ``pglite:`` URL is never replaced by a Postgres URL — that would
  silently undo the owner's flip and point the gateway at a dead port;
* an empty DATABASE_URL prefers the native backend and only falls back to the
  POSTGRES_* synthesis when the native path is unavailable;
* a store is never fabricated: an empty directory is not a store, and the
  schema-only init is opt-in;
* the Postgres realign path (ALTER ROLE via docker exec) survives intact;
* no password is ever printed.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "windows_ensure_database_url.ps1"


def _text() -> str:
    return SCRIPT.read_text(encoding="utf-8-sig")


def test_script_present_and_parsable():
    assert SCRIPT.is_file(), "scripts/windows_ensure_database_url.ps1 missing"
    # PowerShell is not Python; a cheap structural check is enough here — the
    # content assertions below are what actually pin the behaviour.
    text = _text()
    assert text.strip(), "script is empty"


def test_postgres_realign_path_survives():
    """The pre-existing STATE B recovery path must not be lost in the rewrite."""
    text = _text()
    assert "ALTER ROLE" in text
    assert "docker exec" in text
    assert "db:migrate" in text.lower()
    assert "ahos_postgres_win" in text


def test_native_backend_is_documented_and_first_choice():
    text = _text()
    assert "pglite:<dataDir>" in text, "the native scheme must be documented in the header"
    # The empty-URL branch prefers the native backend and says so out loud.
    assert "native embedded backend preferred" in text
    # Fall-back, not fall-forward: Postgres is reached only when native is out.
    assert "falling back to the Postgres (POSTGRES_*) synthesis" in text


def test_failing_pglite_url_is_never_replaced_by_postgres():
    """The anti-clobber guard is the one behaviour that cannot regress silently.

    The Postgres synthesis predates M10 and is correct for an *unset* URL. If it
    were also used as a repair path for a native store that will not open, the
    script would rewrite ``pglite:`` -> ``postgresql://`` behind the owner's
    back and the gateway would silently start talking to a dead port again.
    """
    text = _text()
    assert "NOT falling back to the Postgres synthesis" in text
    assert "would silently switch backends" in text
    # And the guard must be reached only on the pglite branch, guarded by the
    # scheme test rather than by probe error text.
    assert "Test-IsPgliteUrl" in text
    assert re.search(r"if \(\s*\$isPglite\s*\)", text)


def test_probe_is_dispatched_by_backend_not_by_container():
    """An embedded store has no container, so a container probe could not
    evidence it — the probe must go to the node module that shares the
    canonical URL parser with db/index.ts."""
    text = _text()
    assert "cannot evidence it" in text
    assert r"scripts\ahos_pg_probe.mjs" in text
    assert "IsPglite" in text


def test_empty_url_never_fabricates_a_store():
    """Only PG_VERSION proves PGlite initialised a store (M10.1's gate)."""
    text = _text()
    assert "no PG_VERSION" in text
    assert "An empty directory is not a store" in text
    # Init is opt-in: the default empty-URL path reports and points at it.
    assert "-InitializePglite" in text
    assert "Initialize-PgliteStore" in text
    # And the URL is only written after init actually produced PG_VERSION.
    assert re.search(r"\$initOk\s*-and\s*\(Test-PgliteStoreInitialized", text)


def test_data_dir_resolution_order_and_default():
    """Process env wins over .env, and the default lives outside the repo."""
    text = _text()
    assert "AHOS_PGLITE_DATA_DIR" in text
    assert 'GetEnvironmentVariable("AHOS_PGLITE_DATA_DIR", "Process")' in text
    assert "G:/robat/ahos_runtime/pglite/ahos" in text
    assert "outside the repo" in text or "never committed" in text


def test_no_write_switch_is_honoured_on_every_branch():
    text = _text()
    # The existing Postgres guard, plus the two new native ones.
    assert "WARN: NoWrite set; not updating DATABASE_URL" in text
    assert "NoWrite set; would have written DATABASE_URL" in text
    assert re.search(r"if \(\$NoWrite\) \{ exit 2 \}", text)


def test_no_password_is_printed():
    """The Postgres URL is always redacted before it reaches the console."""
    text = _text()
    assert "redactedExpected" in text
    assert "-replace '(:[^:@/]+)@', ':***@'" in text
    assert "never prints a password" in text.lower()


def test_no_migrate_and_no_wipe_promises_kept():
    text = _text()
    assert "do NOT db:migrate / db:push" in text
    assert "Never wipe a store" in text
    assert "do NOT delete the store directory" in text


def test_runbook_is_referenced_for_the_owner_flip():
    """The operator path points at the owner-gated flip document, not at an
    action the script takes on the owner's behalf."""
    text = _text()
    assert "M10_STAGE4_FLIP_RUNBOOK.md" in text
    assert "owner-gated" in text


def test_pglite_url_parser_is_the_single_source_of_truth():
    """The probe must not carry its own copy of the URL parser (Stage 4b guard)."""
    probe = (ROOT / "scripts" / "ahos_pg_probe.mjs").read_text(encoding="utf-8")
    assert 'from "../db/pglite_url.mjs"' in probe
    # A local re-definition would let a green probe describe a store the
    # gateway never opens.
    assert "export function isPgliteBackend" not in probe
    assert "export function pgliteDataDir" not in probe


@pytest.mark.parametrize(
    "url, expect_pglite",
    [
        ("pglite:G:/robat/ahos_runtime/pglite/ahos", True),
        ("pglite:/G:/somewhere/db", True),
        ("pglite://G:/somewhere/db", True),
        ("pglite:/var/lib/ahos/pglite", True),
        ("postgresql://ahos_user:pw@127.0.0.1:5432/ahos", False),
        ("", False),
    ],
)
def test_canonical_parser_classifies_backend_consistently(url, expect_pglite):
    """The .mjs parser is what both the gateway and the probe use."""
    import subprocess

    # A file:// URL is the form node ESM accepts for an absolute Windows path.
    module_uri = (ROOT / "db" / "pglite_url.mjs").as_uri()
    snippet = (
        f"import {{ isPgliteBackend, pgliteDataDir }} from {module_uri!r};\n"
        f"console.log(JSON.stringify({{backend: isPgliteBackend({url!r}), "
        f"dir: pgliteDataDir({url!r})}}));\n"
    )
    out = subprocess.run(
        ["node", "--input-type=module", "-e", snippet],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        timeout=60,
    )
    assert out.returncode == 0, out.stderr
    import json

    got = json.loads(out.stdout.strip().splitlines()[-1])
    assert got["backend"] is expect_pglite
    if expect_pglite:
        # Windows drive forms normalise to the bare drive; POSIX stays absolute.
        assert got["dir"].startswith(("G:", "/"))


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
