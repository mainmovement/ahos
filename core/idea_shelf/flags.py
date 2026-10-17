"""Auto-enable shelf ideas when hardware tier and dependencies allow."""
from __future__ import annotations

from dataclasses import dataclass

from core.idea_shelf.registry import ShelfIdea, hardware_ordinal, load_registry
from core.idea_shelf.hardware import HardwareProbe


@dataclass(frozen=True, slots=True)
class FlagDecision:
    idea_id: str
    enabled: bool
    reason: str


def evaluate_flags(probe: HardwareProbe, registry_ideas: tuple[ShelfIdea, ...]) -> tuple[FlagDecision, ...]:
    mine = hardware_ordinal(probe.tier)
    enabled_ids: set[str] = set()
    decisions: list[FlagDecision] = []

    pending = {i.id: i for i in registry_ideas}
    decisions_map: dict[str, FlagDecision] = {}

    for _ in range(len(registry_ideas) + 1):
        progress = False
        for idea in sorted(pending.values(), key=lambda i: (-i.priority, i.id)):
            if mine is None or idea.tier is None:
                decisions_map[idea.id] = FlagDecision(idea.id, False, "UNKNOWN tier")
                pending.pop(idea.id, None)
                progress = True
                continue
            need = hardware_ordinal(idea.tier)
            if need is None or need > mine:
                decisions_map[idea.id] = FlagDecision(idea.id, False, "awaiting upgrade")
                pending.pop(idea.id, None)
                progress = True
                continue
            if idea.depends_on and not all(d in enabled_ids for d in idea.depends_on):
                continue
            enabled_ids.add(idea.id)
            decisions_map[idea.id] = FlagDecision(idea.id, True, "tier fits")
            pending.pop(idea.id, None)
            progress = True
        if not progress:
            break
    for idea_id in pending:
        decisions_map[idea_id] = FlagDecision(idea_id, False, "dependency missing")

    return tuple(decisions_map[i.id] for i in sorted(registry_ideas, key=lambda i: i.id))


def load_and_evaluate(probe: HardwareProbe) -> tuple[FlagDecision, ...]:
    reg = load_registry()
    if reg.status != "OK":
        return ()
    return evaluate_flags(probe, reg.ideas)
