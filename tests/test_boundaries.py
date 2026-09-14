from __future__ import annotations

import ast
import importlib
import sys
import unittest
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "ahos_org"

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
        for name in ("requests", "httpx", "telegram", "n8n"):
            self.assertNotIn(name, sys.modules)
        importlib.import_module("ahos_org")
        for name in ("requests", "httpx", "telegram", "n8n", "sqlite3"):
            self.assertNotIn(name, sys.modules)

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
