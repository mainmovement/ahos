"""DEPRECATED PARALLEL SUBSYSTEM (PR #14). Not imported by canonical AHOS.

Previously: Pydantic BaseSettings with a hardcoded SECRET_KEY default,
import-time directory creation, Redis URL, yfinance/stock/forex keys —
a parallel config plane that duplicated `.env.example` and `config/paths.py`.

Neutralized: no secrets, no mkdir, no third-party settings framework.
Canonical env keys are documented in `.env.example` and pinned by
`tests/test_config_validation.py`.
"""
from __future__ import annotations

from typing import Any


class Settings:
    """Inert placeholder. Reading a secret attribute returns None."""

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        return None


# Do not instantiate a process-wide settings object that touches the filesystem.
settings = Settings()
