"""AHOS Explanation Engine (Phase 4) — WHY-law answers from Evidence."""

__all__ = ["ExplanationEngine", "ExplanationPack", "InvalidationCondition"]


def __getattr__(name: str):
    if name in ("ExplanationEngine", "ExplanationPack"):
        from .engine import ExplanationEngine, ExplanationPack
        return ExplanationEngine if name == "ExplanationEngine" else ExplanationPack
    if name == "InvalidationCondition":
        from ..scoring.engine import InvalidationCondition
        return InvalidationCondition
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
