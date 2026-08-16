#!/usr/bin/env python3
"""AHOS Logical AI Assistant Roles Loader & Governance Validator (Phase XXIV)."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.paths import get_config_dir


def load_assistant_roles(config_path: Path | str | None = None) -> dict[str, Any]:
    p = Path(config_path) if config_path else (get_config_dir() / "ai_assistants.yaml")
    if not p.exists():
        return {}
    data = yaml.safe_load(p.read_text(encoding='utf-8'))
    return data.get("assistants", {})


def get_assistant(role_name: str, config_path: Path | str | None = None) -> dict[str, Any] | None:
    assistants = load_assistant_roles(config_path)
    return assistants.get(role_name.lower())
