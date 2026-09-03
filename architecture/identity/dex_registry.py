#!/usr/bin/env python3
"""Versioned DEX deployment registry (Lane B)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from architecture.identity.types import DexDeployment

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "config" / "dex_registry.yaml"


@lru_cache(maxsize=1)
def load_dex_registry() -> tuple[str, tuple[DexDeployment, ...]]:
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8")) or {}
    version = str(data.get("version") or "unknown")
    rows = []
    for item in data.get("deployments") or []:
        rows.append(
            DexDeployment(
                dex_id=str(item["dex_id"]).strip().lower(),
                chain=str(item["chain"]).strip().lower(),
                version=str(item["version"]),
                factory=item.get("factory"),
                router=item.get("router"),
            )
        )
    return version, tuple(rows)


def registry_version() -> str:
    version, _rows = load_dex_registry()
    return version


def lookup_dex(
    chain: str | None,
    dex_id: str | None,
    version: str | None = None,
) -> DexDeployment | None:
    """Return a deployment only when the (chain, dex, version) key is unique.

    Unknown dex_id is allowed as a string label on PoolIdentity but is not a
    verified DexDeployment. Ambiguous uniswap v2/v3 without a version is None.
    """
    if not chain or not dex_id:
        return None
    _ver, rows = load_dex_registry()
    wanted = dex_id.strip().lower()
    ch = chain.strip().lower()
    matches = [r for r in rows if r.dex_id == wanted and r.chain == ch]
    if version is not None:
        wanted_ver = str(version).strip()
        matches = [r for r in matches if r.version == wanted_ver]
    if len(matches) == 1:
        return matches[0]
    return None


def clear_dex_registry_cache() -> None:
    load_dex_registry.cache_clear()
