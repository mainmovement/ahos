from __future__ import annotations

import ast
import os
import platform
import unittest
from pathlib import Path

import agent_org


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "agent_org"


class BoundaryAndWindowsTests(unittest.TestCase):
    @unittest.skipUnless(
        os.name == "nt",
        "authoritative gate: the certified test environment is Windows; "
        "this sentinel runs on Windows only and visibly skips elsewhere. "
        "A green non-Windows run is useful signal but never authoritative "
        "evidence for the Windows-first production target.",
    )
    def test_actual_test_environment_is_windows(self) -> None:
        self.assertEqual(os.name, "nt")
        self.assertEqual(platform.system(), "Windows")
        self.assertEqual(ROOT.resolve(), Path.cwd().resolve())

    def test_slice2b_has_no_protected_absolute_path(self) -> None:
        forbidden = (
            "G:" + "\\robat\\ahos",
            "G:/robat/ahos",
            "g:" + "\\robat\\ahos",
            "g:/robat/ahos",
        )
        for path in PACKAGE.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for value in forbidden:
                self.assertNotIn(value, text, path)

    def test_slice2b_imports_no_network_database_process_or_browser_modules(self) -> None:
        forbidden = {
            "requests",
            "httpx",
            "aiohttp",
            "urllib",
            "http",
            "socket",
            "sqlite3",
            "subprocess",
            "selenium",
            "playwright",
            "telegram",
            "n8n",
        }
        for path in PACKAGE.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imported = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module.split(".")[0])
            self.assertFalse(imported & forbidden, (path, imported & forbidden))

    def test_no_credentials_or_environment_access(self) -> None:
        for path in PACKAGE.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("os.environ", text, path)
            self.assertNotIn("getenv(", text, path)
            self.assertNotIn("keyring", text.lower(), path)

    def test_agent_one_runtime_is_not_implemented(self) -> None:
        self.assertEqual(agent_org.AGENT_ONE_STATUS, "FUTURE_NON_AUTHORITY_ROOT")
        for path in PACKAGE.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            class_names = {
                node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
            }
            self.assertNotIn("AgentOne", class_names)

    def test_public_api_does_not_export_store_or_mutation_permit(self) -> None:
        self.assertFalse(
            {"GovernedStore", "_GovernedState", "_MutationPermit", "AuditLedger"}
            & set(agent_org.__all__)
        )
