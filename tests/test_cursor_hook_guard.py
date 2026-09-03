"""Unit tests for the AHOS Cursor hook guard (defense in depth)."""
from __future__ import annotations

import io
import json
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "ahos_guard", ROOT / ".cursor" / "hooks" / "ahos-guard.py"
)
assert _spec and _spec.loader
guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guard)


def test_protected_lane_a_and_secrets():
    assert guard.is_protected_path("discovery/identity.py")
    assert guard.is_protected_path("paper_trading/ledger.py")
    assert guard.is_protected_path("config/lane_a_freeze.sha256")
    assert guard.is_protected_path(".env")
    assert guard.is_protected_path("data/e01_discovery.sqlite")
    assert guard.is_protected_path("foo.sqlite")
    assert not guard.is_protected_path(".env.example")
    assert not guard.is_protected_path("architecture/decision/advisor.py")
    assert not guard.is_protected_path("AGENTS.md")


def test_pre_tool_use_denies_lane_a_write():
    d = guard.decide_pre_tool_use(
        {"tool_input": {"path": str(ROOT / "discovery" / "collect.py")}}
    )
    assert d["permission"] == "deny"


def test_pre_tool_use_allows_lane_b():
    d = guard.decide_pre_tool_use(
        {"tool_input": {"path": str(ROOT / "architecture" / "decision" / "advisor.py")}}
    )
    assert d["permission"] == "allow"


def test_shell_denies_freeze_write_and_force_push():
    assert (
        guard.decide_before_shell(
            {"command": "python scripts/freeze_lane_a.py --write"}
        )["permission"]
        == "deny"
    )
    assert (
        guard.decide_before_shell(
            {"command": "git push --force origin main"}
        )["permission"]
        == "deny"
    )
    assert (
        guard.decide_before_shell({"command": "python3 -m pytest tests/ -q"})[
            "permission"
        ]
        == "allow"
    )


def test_cli_fail_closed_on_bad_json(monkeypatch, capsys):
    monkeypatch.setattr(guard.sys, "stdin", io.StringIO("{not-json"))
    rc = guard.main(["ahos-guard.py", "preToolUse"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["permission"] == "deny"
