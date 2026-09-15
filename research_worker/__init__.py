"""Untrusted research worker process package.

This package must not import agent_org.tcb, governance, identity, or the
research host. The child process talks only through versioned JSON IPC.
"""

from research_worker.protocol import (
    IPC_PROTOCOL,
    MAX_MESSAGE_BYTES,
    PROTOCOL_VERSION,
    SERIALIZATION,
    WINDOWS_PROCESS_MODEL,
)

__all__ = [
    "IPC_PROTOCOL",
    "MAX_MESSAGE_BYTES",
    "PROTOCOL_VERSION",
    "SERIALIZATION",
    "WINDOWS_PROCESS_MODEL",
]
