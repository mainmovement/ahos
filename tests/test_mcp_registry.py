"""Tests for AHOS FastMCP-compatible Tool Registry and Security Sandbox (OSS-008)."""

from __future__ import annotations

import pytest

from architecture.tools.mcp_registry import MCPToolRegistry
from architecture.tools.sandbox import SecuritySandbox, SecuritySandboxViolation


def test_mcp_list_tools():
    registry = MCPToolRegistry()
    tools = registry.list_tools()

    assert len(tools) >= 2
    tool_names = [t["name"] for t in tools]
    assert "market_data_query" in tool_names
    assert "risk_assessment" in tool_names


def test_mcp_call_tool_success():
    registry = MCPToolRegistry()
    res = registry.call_tool("market_data_query", {"token": "SOL"})

    assert res["isError"] is False
    assert res["structured_data"]["token"] == "SOL"
    assert res["structured_data"]["price_usd"] > 0


def test_mcp_security_sandbox_blocks_forbidden_tool():
    registry = MCPToolRegistry()
    # Register an unauthorized tool
    registry.tools["execute_shell"] = {
        "name": "execute_shell",
        "description": "forbidden",
        "inputSchema": {},
        "handler": lambda cmd: cmd,
    }

    res = registry.call_tool("execute_shell", {"cmd": "ls -la"})
    assert res["isError"] is True
    assert "SECURITY_VIOLATION" in res["content"][0]["text"]


def test_mcp_security_sandbox_blocks_malicious_args():
    registry = MCPToolRegistry()
    res = registry.call_tool(
        "market_data_query", {"token": "SOL; rm -rf database"}
    )
    assert res["isError"] is True
    assert "SECURITY_VIOLATION" in res["content"][0]["text"]
