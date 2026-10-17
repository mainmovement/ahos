"""M59.S idea shelf core — registry, hardware, flags, RAM guard."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.idea_shelf.flags import evaluate_flags
from core.idea_shelf.hardware import detect_hardware, probe_from_fixture
from core.idea_shelf.ram_guard import RAM_FLOOR_GB, evaluate_ram_guard, ram_band
from core.idea_shelf.registry import (
    ShelfIdea,
    awaiting_upgrade,
    load_registry,
    parse_registry_text,
)


def test_registry_missing_is_unavailable():
    assert load_registry(Path("/nonexistent/idea_shelf.json")).status == "UNAVAILABLE"


def test_registry_parses_committed_seed():
    reg = load_registry()
    assert reg.status == "OK", reg.reason
    assert len(reg.ideas) >= 5
    assert all(i.id and i.title for i in reg.ideas)


def test_parse_drops_invalid_entries():
    raw = json.dumps({"ideas": [{"id": "a"}, {"title": "no id"}, {"id": "ok", "title": "Ok", "tier": "T8"}]})
    reg = parse_registry_text(raw)
    assert reg.status == "OK"
    assert len(reg.ideas) == 1
    assert reg.ideas[0].id == "ok"


def test_awaiting_upgrade_t8_machine():
    ideas = (
        ShelfIdea("a", "A", "T16"),
        ShelfIdea("b", "B", "T8"),
        ShelfIdea("c", "C", None),
    )
    waiting = awaiting_upgrade(ideas, "T8")
    assert [i.id for i in waiting] == ["a"]


def test_hardware_override():
    p = detect_hardware(override="T32")
    assert p.tier == "T32"
    assert p.source == "override"


def test_flags_tier_and_deps():
    ideas = (
        ShelfIdea("base", "Base", "T8", priority=1),
        ShelfIdea("child", "Child", "T8", priority=2, depends_on=("base",)),
        ShelfIdea("heavy", "Heavy", "T32", priority=3),
    )
    probe = probe_from_fixture({"tier": "T8", "ram_gb": 8})
    decisions = {d.idea_id: d for d in evaluate_flags(probe, ideas)}
    assert decisions["base"].enabled
    assert decisions["child"].enabled
    assert not decisions["heavy"].enabled
    assert decisions["heavy"].reason == "awaiting upgrade"


def test_ram_guard_core_never_shed():
    ideas = (
        ShelfIdea("core1", "Core", "T8", core=True, priority=0),
        ShelfIdea("opt", "Opt", "T8", core=False, priority=1),
    )
    enabled = {"core1", "opt"}
    hard = evaluate_ram_guard(92.0, ideas, enabled)
    assert hard.pressure == "HARD"
    assert "core1" not in hard.shed_ids
    assert "opt" in hard.shed_ids


def test_ram_guard_soft_sheds_lowest_priority():
    ideas = (
        ShelfIdea("a", "A", "T8", priority=5),
        ShelfIdea("b", "B", "T8", priority=1),
    )
    soft = evaluate_ram_guard(85.0, ideas, {"a", "b"})
    assert soft.pressure == "SOFT"
    assert soft.shed_ids == ("b",)


def test_ram_band_floor():
    assert ram_band(7.5) == "UNDER_FLOOR"
    assert ram_band(RAM_FLOOR_GB) == "AT_FLOOR"
    assert ram_band(16) == "ABOVE_FLOOR"
    assert ram_band(None) == "UNKNOWN"
