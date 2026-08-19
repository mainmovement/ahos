#!/usr/bin/env python3
"""Small, dependency-free loader for the repository-local ``.env`` file.

Environment variables supplied by the process always win. The loader does not
perform interpolation or execute shell syntax; it only accepts ``KEY=VALUE``
lines. This keeps the Windows launchers and native Python runtime consistent
with Docker Compose without adding python-dotenv to the deterministic floor.
"""
from __future__ import annotations

import os
from pathlib import Path

from .paths import get_project_root


def load_dotenv(path: str | Path | None = None) -> dict[str, str]:
    """Load unset variables from ``path`` and return the values encountered."""
    env_path = Path(path) if path is not None else get_project_root() / ".env"
    loaded: dict[str, str] = {}
    try:
        lines = env_path.read_text(encoding="utf-8-sig").splitlines()
    except (FileNotFoundError, OSError):
        return loaded

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or not key.replace("_", "a").isalnum() or key[0].isdigit():
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        loaded[key] = value
        os.environ.setdefault(key, value)
    return loaded
