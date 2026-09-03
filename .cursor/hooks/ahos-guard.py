#!/usr/bin/env python3
"""AHOS Cursor hook guard — defense in depth, not a security boundary.

Reads one JSON object from stdin. Prints a permission decision to stdout.
Fails closed when invoked by Cursor hooks (`failClosed: true`).

This script cannot see every indirect write. Lane A hashes, CODEOWNERS,
`scripts/validate_imports.py`, and human review remain authoritative.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

PROTECTED_PREFIXES = (
    "discovery/",
    "paper_trading/",
    "data/",
)

PROTECTED_FILES = {
    "config/lane_a_freeze.sha256",
    "docs/canonical/MASTER_DIRECTIVE_v1.md",
}

PROTECTED_SUFFIXES = (".sqlite", ".db")

SHELL_DENY = (
    re.compile(r"freeze_lane_a\.py\s+[^\n]*--write"),
    re.compile(r"drizzle-kit\s+(push|drop)\b"),
    re.compile(r"\bnpm\s+run\s+db:(migrate|push)\b"),
    re.compile(r"\bgit\s+push\b[^\n]*(\s--force\b|\s-f\b)"),
    re.compile(r"\bgit\s+push\b[^\n]*\borigin\s+main\b"),
    re.compile(r"\bgit\s+reset\s+--hard\b"),
    re.compile(r"\bgit\s+clean\s+-[a-zA-Z]*f"),
    re.compile(r"\bgh\s+pr\s+merge\b"),
    re.compile(r"\b(DROP|TRUNCATE)\s+(TABLE|DATABASE)\b", re.I),
    re.compile(r"ALTER\s+USER\b", re.I),
    re.compile(r"api\.telegram\.org"),
    re.compile(r"AHOS_PAPER_ONLY\s*=\s*0"),
    re.compile(r"run_sun_sniper_bot\.py"),
    re.compile(r"docker\s+compose\s+up\b"),
    re.compile(r"docker-compose\s+up\b"),
)


def _repo_relative(path: str, cwd: str | None = None) -> str:
    raw = (path or "").strip().replace("\\", "/")
    if not raw:
        return ""
    p = Path(raw)
    try:
        if p.is_absolute():
            root = Path(cwd).resolve() if cwd else Path.cwd()
            # Walk up to the repo root if cwd is a worktree subdirectory.
            for candidate in (root, *root.parents):
                if (candidate / "scripts" / "freeze_lane_a.py").is_file():
                    root = candidate
                    break
            return p.resolve().relative_to(root).as_posix()
    except Exception:
        pass
    rel = raw.replace("\\", "/")
    while rel.startswith("./"):
        rel = rel[2:]
    return rel


def is_protected_path(rel: str) -> bool:
    rel = rel.replace("\\", "/")
    while rel.startswith("./"):
        rel = rel[2:]
    if not rel:
        return False
    if rel in PROTECTED_FILES:
        return True
    if rel == ".env" or (rel.startswith(".env.") and not rel.startswith(".env.example")):
        return True
    if any(rel == p.rstrip("/") or rel.startswith(p) for p in PROTECTED_PREFIXES):
        return True
    name = rel.split("/")[-1]
    return name.endswith(PROTECTED_SUFFIXES)


def extract_paths(payload: dict[str, Any]) -> list[str]:
    cwd = payload.get("cwd")
    found: list[str] = []
    tool_input = payload.get("tool_input") or payload.get("arguments") or {}
    if isinstance(tool_input, dict):
        for key in ("path", "file_path", "target_notebook", "to", "dest"):
            val = tool_input.get(key)
            if isinstance(val, str):
                found.append(_repo_relative(val, cwd))
    for key in ("file_path", "path"):
        val = payload.get(key)
        if isinstance(val, str):
            found.append(_repo_relative(val, cwd))
    return [p for p in found if p]


def deny(agent_message: str, user_message: str | None = None) -> dict[str, str]:
    out = {
        "permission": "deny",
        "agent_message": agent_message,
        "user_message": user_message or agent_message,
    }
    return out


def allow() -> dict[str, str]:
    return {"permission": "allow"}


def decide_pre_tool_use(payload: dict[str, Any]) -> dict[str, str]:
    for rel in extract_paths(payload):
        if is_protected_path(rel):
            return deny(
                f"AHOS hook denied write to protected path `{rel}`. "
                "Lane A, freeze manifest, secrets, and runtime databases are off-limits."
            )
    return allow()


def decide_before_shell(payload: dict[str, Any]) -> dict[str, str]:
    command = str(payload.get("command") or payload.get("tool_input") or "")
    if isinstance(payload.get("tool_input"), dict):
        command = str(payload["tool_input"].get("command") or command)
    for pattern in SHELL_DENY:
        if pattern.search(command):
            return deny(
                "AHOS hook denied a dangerous shell command. "
                "Lane A freeze re-anchor, live trading, force-push, auto-merge, "
                "destructive DB, and secret exfil are forbidden."
            )
    # Catch obvious direct edits to frozen trees.
    if re.search(r"\b(discovery|paper_trading)/", command) and re.search(
        r"\b(rm|mv|sed|tee|python|printf|>|>>)\b", command
    ):
        if "freeze_lane_a.py" not in command and "pytest" not in command:
            if re.search(r"(>|>>|rm\s+|mv\s+|tee\s+)", command):
                return deny(
                    "AHOS hook denied a shell command that appears to mutate Lane A."
                )
    return allow()


def main(argv: list[str]) -> int:
    event = argv[1] if len(argv) > 1 else "preToolUse"
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        json.dump(
            deny("AHOS hook received invalid JSON; fail closed."),
            sys.stdout,
        )
        return 0

    if event == "beforeShellExecution":
        decision = decide_before_shell(payload)
    else:
        decision = decide_pre_tool_use(payload)
    json.dump(decision, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
