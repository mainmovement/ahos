"""Supported API surface for untrusted callers.

Only immutable command contracts, result contracts, and read-only projections
are exposed.  Governed stores and mutation permits are intentionally absent.
"""

from agent_org.commands import CommandEnvelope
from agent_org.contracts import (
    Capability,
    CommandResult,
    CommandType,
    Operation,
    Resource,
)
from agent_org.projections import ReadOnlyProjections

__all__ = [
    "Capability",
    "CommandEnvelope",
    "CommandResult",
    "CommandType",
    "Operation",
    "ReadOnlyProjections",
    "Resource",
]
