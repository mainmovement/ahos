"""M59.S — idea shelf: registry, hardware probe, feature flags, RAM guard."""

from core.idea_shelf.flags import FlagDecision, evaluate_flags
from core.idea_shelf.hardware import HardwareProbe, detect_hardware
from core.idea_shelf.ram_guard import RamGuardDecision, evaluate_ram_guard
from core.idea_shelf.registry import ShelfIdea, load_registry

__all__ = [
    "FlagDecision",
    "HardwareProbe",
    "RamGuardDecision",
    "ShelfIdea",
    "detect_hardware",
    "evaluate_flags",
    "evaluate_ram_guard",
    "load_registry",
]
