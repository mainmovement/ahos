#!/usr/bin/env python3
"""M-GAP-037 pins: the ARTIFACTS check protects the *committed* tree, not the
working tree.

AHOS_LOCAL_SOAK_PROTOCOL.md:79 requires `scripts/validate_imports.py` to pass
before a soak may start. On a warm host every Python invocation leaves
`__pycache__`/`.pytest_cache` behind, and the old check walked the filesystem
git-blind, so the gate failed on 44 transient caches with zero substantive
violations -- in exactly the context the gate exists for. Running pytest, which
the protocol mandates one line earlier, is enough to trip it.

The fix consults git's own ignore state: ignored caches are transient and
excluded; a cache git would stage still fails. These pins lock both halves of
that contract so it cannot regress in either direction:

  * a gitignored __pycache__ on disk produces NO artifact failure;
  * a __pycache__ that is NOT ignored (git would stage it) DOES fail.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.validate_imports as gate  # noqa: E402


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=str(root), capture_output=True, text=True)


def _make_repo(tmp_path: Path) -> Path:
    """A real git repo with one ignored and one tracked package."""
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "Test")
    (root / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n", encoding="utf-8")
    (root / "pkg").mkdir()
    (root / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "init")
    return root


def _check_on(root: Path, monkeypatch) -> tuple[list[str], list[str]]:
    monkeypatch.setattr(gate, "ROOT", root)
    return gate.check_artifacts()


def test_gitignored_pycache_is_not_a_failure(tmp_path, monkeypatch):
    """An ignored transient cache (any warm host) must not fail the gate."""
    root = _make_repo(tmp_path)
    warm = root / "pkg" / "__pycache__"
    warm.mkdir()
    (warm / "__init__.cpython-311.pyc").write_text("X", encoding="utf-8")

    ignored = _git(root, "check-ignore", "-q", "--", "pkg/__pycache__").returncode
    assert ignored == 0, "precondition: git must ignore this __pycache__"

    failures, _notes = _check_on(root, monkeypatch)
    assert failures == [], (
        f"gitignored transient cache must not fail the soak gate: {failures}. "
        "A warm host accumulates these merely by running Python; the check "
        "protects the committed tree, not the working tree (M-GAP-037)."
    )


def test_non_ignored_pycache_still_fails(tmp_path, monkeypatch):
    """A cache git would stage must still fail -- the guarantee is preserved."""
    root = _make_repo(tmp_path)
    (root / ".gitignore").write_text("", encoding="utf-8")  # ignore nothing
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "drop ignores")

    leaked = root / "pkg" / "__pycache__"
    leaked.mkdir()
    (leaked / "__init__.cpython-311.pyc").write_text("X", encoding="utf-8")

    not_ignored = _git(root, "check-ignore", "-q", "--", "pkg/__pycache__").returncode
    assert not_ignored == 1, "precondition: git must NOT ignore this __pycache__"

    failures, _notes = _check_on(root, monkeypatch)
    assert len(failures) == 1, f"exactly one failure expected, got {failures}"
    # separator-agnostic: the message uses the OS separator (pkg\__pycache__ on Windows)
    assert failures[0].replace("\\", "/").endswith("pkg/__pycache__/"), failures[0]
    assert "not gitignored" in failures[0], (
        "the failure must say the artifact is not gitignored, so the operator "
        "knows git would stage it -- that is the real defect being caught."
    )


def test_pytest_cache_follows_the_same_rule(tmp_path, monkeypatch):
    """.pytest_cache is the other half of the check; it must behave the same way."""
    root = _make_repo(tmp_path)
    cache = root / ".pytest_cache"
    cache.mkdir()
    (cache / "v").mkdir()
    (cache / "v" / "cache").write_text("last", encoding="utf-8")

    assert _git(root, "check-ignore", "-q", "--", ".pytest_cache").returncode == 0
    failures, _notes = _check_on(root, monkeypatch)
    assert failures == [], f"ignored .pytest_cache must not fail: {failures}"


def test_skip_dirs_still_excluded(tmp_path, monkeypatch):
    """A cache inside a vendored dir is reported as before only if not ignored;
    the pre-existing skip-set behaviour is unchanged for ignored content."""
    root = _make_repo(tmp_path)
    (root / "node_modules").mkdir()
    (root / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "nm")
    (root / "node_modules" / "__pycache__").mkdir()

    failures, _notes = _check_on(root, monkeypatch)
    assert failures == [], (
        f"node_modules cache must be excluded by ARTIFACT_SKIP_DIRS: {failures}"
    )
