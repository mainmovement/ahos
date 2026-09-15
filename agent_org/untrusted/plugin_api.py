"""Minimal future plugin-facing contract surface; no plugin runtime exists."""

from agent_org.public import (
    Capability,
    CommandEnvelope,
    CommandResult,
    CommandType,
    Operation,
    ReadOnlyProjections,
    Resource,
)

__all__ = [
    "Capability",
    "CommandEnvelope",
    "CommandResult",
    "CommandType",
    "Operation",
    "ReadOnlyProjections",
    "Resource",
]
