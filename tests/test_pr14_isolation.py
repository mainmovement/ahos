#!/usr/bin/env python3
"""PR #14 (core / infrastructure / utils) is a non-canonical parallel subsystem.

Pins:
  * canonical runtime packages never import core/infrastructure/utils/ahos.*
  * the neutralized utils.cache path does not use eval()
  * settings expose no hardcoded SECRET_KEY
  * Token stub refuses to masquerade as the canonical candidate
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CANONICAL = (
    "architecture", "discovery", "telegram_ai", "engine",
    "paper_trading", "strategy_lab", "scripts",
)
FORBIDDEN_PREFIXES = (
    "core", "infrastructure", "utils", "ahos.core",
    "ahos.infrastructure", "ahos.utils", "ahos.",
)


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.append(node.module)
    return out


def test_canonical_packages_do_not_import_pr14():
    offenders: list[str] = []
    for pkg in CANONICAL:
        base = ROOT / pkg
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            for mod in _imports(path):
                if any(mod == p or mod.startswith(p + ".") for p in FORBIDDEN_PREFIXES):
                    # relative imports inside utils itself are irrelevant; we
                    # are iterating canonical packages only.
                    offenders.append(f"{path.relative_to(ROOT)} imports {mod}")
    assert offenders == []


def test_utils_decorators_has_no_eval_and_no_redis():
    src = (ROOT / "utils" / "decorators.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Name) and n.func.id == "eval"]
    assert calls == []
    assert "import redis" not in src.lower()
    from utils.decorators import cache

    @cache(ttl=60)
    def add(a, b):
        return a + b

    assert add(1, 2) == 3
    assert add(1, 2) == 3          # in-process memo, not eval(repr)


def test_settings_has_no_default_secret_key():
    src = (ROOT / "infrastructure" / "config" / "settings.py").read_text(encoding="utf-8")
    assert "change-me-in-production" not in src
    from infrastructure.config.settings import settings
    assert getattr(settings, "SECRET_KEY", None) is None


def test_core_token_refuses_to_construct():
    import pytest
    from core.models.token import Token
    with pytest.raises(RuntimeError):
        Token(id="x", name="n", symbol="s")


def test_gitignore_covers_secret_material():
    gi = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for token in (".env", "*.pem", "*.key", "wallet.json", "secrets.json"):
        assert token in gi
