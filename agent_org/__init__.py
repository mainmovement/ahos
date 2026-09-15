"""Slice 2B epistemic core and Trusted Command Boundary.

This package is an isolated control plane.  It contains no executor, provider,
network, credential, trading, AHOS, browser, or Agent One runtime.
"""

from agent_org.commands import CommandEnvelope
from agent_org.contracts import (
    Capability,
    CommandResult,
    CommandStatus,
    CommandType,
    Decision,
    Operation,
    POLICY_VERSION,
    Resource,
)
from agent_org.projections import ReadOnlyProjections
from agent_org.tcb import (
    CommandIngress,
    LocalControlPlane,
    TrustedCommandBoundary,
    build_local_control_plane,
)

__all__ = [
    "Capability",
    "CommandEnvelope",
    "CommandIngress",
    "CommandResult",
    "CommandStatus",
    "CommandType",
    "Decision",
    "LocalControlPlane",
    "Operation",
    "POLICY_VERSION",
    "ReadOnlyProjections",
    "Resource",
    "TrustedCommandBoundary",
    "build_local_control_plane",
]

AGENT_ONE_STATUS = "FUTURE_NON_AUTHORITY_ROOT"
SLICE_2B_CLAIM = "IMPLEMENTED_NOT_YET_VERIFIED"
