"""Load and validate config/idea_shelf.json (shared with dashboard)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from config.paths import get_project_root

HardwareTier = Literal["T8", "T16", "T32", "GPU"]
HARDWARE_TIERS: tuple[HardwareTier, ...] = ("T8", "T16", "T32", "GPU")


@dataclass(frozen=True, slots=True)
class ShelfIdea:
    id: str
    title: str
    tier: HardwareTier | None
    core: bool = False
    flag: str | None = None
    est_ram_mb: int | None = None
    priority: int = 0
    depends_on: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class RegistryLoad:
    status: Literal["OK", "UNAVAILABLE"]
    ideas: tuple[ShelfIdea, ...] = ()
    reason: str = ""


def default_registry_path() -> Path:
    return get_project_root() / "config" / "idea_shelf.json"


def _parse_idea(raw: dict[str, Any]) -> ShelfIdea | None:
    id_ = raw.get("id")
    title = raw.get("title")
    if not isinstance(id_, str) or not isinstance(title, str):
        return None
    tier_raw = raw.get("tier")
    tier: HardwareTier | None = None
    if isinstance(tier_raw, str) and tier_raw in HARDWARE_TIERS:
        tier = tier_raw  # type: ignore[assignment]
    deps = raw.get("depends_on")
    dep_tuple: tuple[str, ...] = ()
    if isinstance(deps, list):
        dep_tuple = tuple(d for d in deps if isinstance(d, str))
    est = raw.get("est_ram_mb")
    est_mb = int(est) if isinstance(est, (int, float)) and est == est else None
    pri = raw.get("priority")
    priority = int(pri) if isinstance(pri, (int, float)) else 0
    flag = raw.get("flag")
    flag_s = flag if isinstance(flag, str) else None
    return ShelfIdea(
        id=id_,
        title=title,
        tier=tier,
        core=raw.get("core") is True,
        flag=flag_s,
        est_ram_mb=est_mb,
        priority=priority,
        depends_on=dep_tuple,
    )


def parse_registry_text(raw: str | None) -> RegistryLoad:
    if raw is None or raw.strip() == "":
        return RegistryLoad(status="UNAVAILABLE", reason="missing")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return RegistryLoad(status="UNAVAILABLE", reason=f"unparseable: {exc}")
    if not isinstance(parsed, dict):
        return RegistryLoad(status="UNAVAILABLE", reason="not an object")
    ideas_raw = parsed.get("ideas")
    if not isinstance(ideas_raw, list):
        return RegistryLoad(status="UNAVAILABLE", reason="no ideas array")
    seen: set[str] = set()
    ideas: list[ShelfIdea] = []
    for entry in ideas_raw:
        if not isinstance(entry, dict):
            continue
        idea = _parse_idea(entry)
        if idea is None or idea.id in seen:
            continue
        seen.add(idea.id)
        ideas.append(idea)
    return RegistryLoad(status="OK", ideas=tuple(ideas))


def load_registry(path: Path | None = None) -> RegistryLoad:
    p = path or default_registry_path()
    if not p.is_file():
        return RegistryLoad(status="UNAVAILABLE", reason="missing")
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        return RegistryLoad(status="UNAVAILABLE", reason=f"unreadable: {exc}")
    return parse_registry_text(text)


def hardware_ordinal(tier: HardwareTier | None) -> int | None:
    if tier is None:
        return None
    try:
        return HARDWARE_TIERS.index(tier)
    except ValueError:
        return None


def awaiting_upgrade(ideas: tuple[ShelfIdea, ...], machine: HardwareTier | None) -> tuple[ShelfIdea, ...]:
    mine = hardware_ordinal(machine)
    if mine is None:
        return ()
    blocked = [i for i in ideas if (need := hardware_ordinal(i.tier)) is not None and need > mine]
    blocked.sort(key=lambda i: (-(hardware_ordinal(i.tier) or -1), -i.priority))
    return tuple(blocked)
