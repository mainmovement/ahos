"""AHOS Security Sandbox Gate for Agent Tool Execution.

Enforces strict security boundaries on tool execution:
- Blocks arbitrary shell / command execution
- Blocks private key and wallet transactions
- Blocks destructive file operations
- Logs all tool execution audit traces
"""

from __future__ import annotations

from typing import Any, Dict, List, Set


class SecuritySandboxViolation(Exception):
    """Raised when an agent attempts an unauthorized or unsafe operation."""


class SecuritySandbox:
    """Read-only and deterministic compute execution sandbox."""

    FORBIDDEN_OPERATIONS: Set[str] = {
        "execute_shell",
        "subprocess_exec",
        "sign_transaction",
        "transfer_wallet",
        "private_key_export",
        "delete_database",
        "rm_rf",
    }

    def __init__(self) -> None:
        self.audit_log: List[Dict[str, Any]] = []

    def validate_tool_invocation(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> None:
        """Validates that a tool invocation does not breach security boundaries."""
        if tool_name in self.FORBIDDEN_OPERATIONS:
            raise SecuritySandboxViolation(
                f"Security Gate: Tool '{tool_name}' is forbidden by sandbox policy."
            )

        # Check for dangerous arguments
        for k, v in arguments.items():
            if isinstance(v, str):
                lower_v = v.lower()
                if any(
                    bad in lower_v
                    for bad in ["rm -rf", "drop table", "private_key", "secret"]
                ):
                    raise SecuritySandboxViolation(
                        f"Security Gate: Argument '{k}' contains prohibited pattern: {v}"
                    )

    def log_invocation(
        self, tool_name: str, arguments: Dict[str, Any], status: str
    ) -> None:
        """Records execution trace in audit log."""
        self.audit_log.append(
            {
                "tool_name": tool_name,
                "arguments": arguments,
                "status": status,
            }
        )
