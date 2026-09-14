from __future__ import annotations

import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "ahos_org"

FORBIDDEN_PATH_FRAGMENTS = (
    r"G:\robat\ahos",
    r"G:/robat/ahos",
    r"g:\robat\ahos",
    r"g:/robat/ahos",
)

FORBIDDEN_IMPORTS = {
    "requests",
    "httpx",
    "aiohttp",
    "urllib",
    "urllib.request",
    "http.client",
    "socket",
    "subprocess",
    "sqlite3",
    "telebot",
    "telegram",
    "n8n",
}


# Modules the runtime must not drag in when `ahos_org` is imported.
#
# Deliberately EXCLUDES bare `urllib`, unlike FORBIDDEN_IMPORTS above.
# Evidence: CPython 3.11 `pathlib.py:13` executes
# `from urllib.parse import quote_from_bytes`, so `ahos_org/organization.py:5`
# (`from pathlib import Path`) transitively pulls in the `urllib` package with
# no network intent at all. `urllib.parse` is a pure string module; the real
# HTTP client is `urllib.request`, and THAT stays in the watched set.
# Watching bare `urllib` measured CPython rather than AHOS -- a false positive.
RUNTIME_IO_MODULES = FORBIDDEN_IMPORTS - {"urllib"}


def _iter_package_files() -> list[Path]:
    return sorted(PACKAGE_ROOT.glob("*.py"))


class BoundaryTests(unittest.TestCase):
    def test_package_has_no_ahos_filesystem_path(self) -> None:
        for path in _iter_package_files():
            text = path.read_text(encoding="utf-8")
            for fragment in FORBIDDEN_PATH_FRAGMENTS:
                self.assertNotIn(fragment, text, msg=f"{path.name} contains {fragment}")

    def test_package_imports_are_stdlib_only_and_offline(self) -> None:
        for path in _iter_package_files():
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        root = alias.name.split(".")[0]
                        self.assertNotIn(alias.name, FORBIDDEN_IMPORTS, path.name)
                        self.assertNotIn(root, FORBIDDEN_IMPORTS, path.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    self.assertNotIn(node.module, FORBIDDEN_IMPORTS, path.name)
                    self.assertNotIn(node.module.split(".")[0], FORBIDDEN_IMPORTS, path.name)

    def test_importing_runtime_does_not_require_network_modules(self) -> None:
        """Importing ahos_org must not pull in any I/O module.

        HERMETICITY (P0-002)
        --------------------
        This asserted against the *shared* interpreter's sys.modules. Any test
        that ran earlier in the same session could import sqlite3 first, so the
        check passed or failed depending on collection order -- a boundary
        guarantee CI was silently not proving. `ahos_org` really does avoid
        these imports (verified in a bare interpreter); what was broken was the
        measurement, not the code under test.

        The import now runs in a fresh subprocess, so the result reflects
        `ahos_org` alone and the whole FORBIDDEN_IMPORTS set is covered rather
        than the five names the old check remembered to list.
        """
        code = (
            "import sys, json\n"
            "sys.path.insert(0, %r)\n"
            "import ahos_org\n"
            "watch = %r\n"
            "print(json.dumps(sorted(m for m in watch if m in sys.modules)))\n"
        ) % (str(REPO_ROOT), sorted(RUNTIME_IO_MODULES))
        proc = subprocess.run([sys.executable, "-B", "-c", code], cwd=REPO_ROOT,
                              capture_output=True, text=True, timeout=120)
        self.assertEqual(proc.returncode, 0,
                         msg=f"ahos_org failed to import cleanly:\n{proc.stderr[-800:]}")
        self.assertEqual(proc.stdout.strip(), "[]",
                         msg=f"ahos_org pulled I/O modules at import: {proc.stdout.strip()}")

    def test_no_credential_env_access_in_package(self) -> None:
        for path in _iter_package_files():
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("os.environ", text, path.name)
            self.assertNotIn("getenv", text, path.name)
            self.assertNotIn(".env", text, path.name)
            self.assertNotIn("api_key", text.lower(), path.name)
            self.assertNotIn("password", text.lower(), path.name)

    def test_symbolic_ahos_entries_are_not_connections(self) -> None:
        from ahos_org.organization import AgentOrganization
        from tests.support import new_org

        org = new_org()
        resource = org.resources.get("AHOS_REPOSITORY")
        self.assertEqual(resource.allowed_operations, ())
        self.assertIn("does not open", resource.notes.lower())
        self.assertIsInstance(org, AgentOrganization)
