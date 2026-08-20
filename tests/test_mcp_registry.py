"""Tests for AHOS FastMCP-compatible Tool Registry and Security Sandbox (OSS-008).

HONESTY LAW (P0 data integrity): the default `market_data_query` handler must
NEVER fabricate prices. It resolves real provider data through the unified
ProviderCollector and returns `data_status: "OK"` only when at least one field
was actually observed; otherwise every field is None with `data_status:
"UNKNOWN"` and the per-provider statuses are returned. Symbols are refused
(no fabricated symbol->price mapping).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from architecture.tools.mcp_registry import MCPToolRegistry
from architecture.tools.sandbox import SecuritySandbox, SecuritySandboxViolation
from architecture.providers.collect import ProviderCollector

SOL_ADDR = "So11111111111111111111111111111111111111112"


class _MockResp:
    def __init__(self, data, status: int = 200):
        self._data = json.dumps(data).encode("utf-8")
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self._data


class _RoutingTransport:
    """Routes by URL substring; raises on any unexpected URL."""

    def __init__(self, routes):
        self.routes = routes

    def __call__(self, req, timeout=None):
        url = req.full_url
        for substring, payload in self.routes.items():
            if substring in url:
                return _MockResp(payload)
        raise AssertionError(f"unexpected url: {url}")


class _ExplodingTransport:
    def __call__(self, req, timeout=None):
        raise OSError("TLS/SSL connection has been closed (EOF) (injected)")


DEXSCREENER_PAYLOAD = {
    "pairs": [{
        "chainId": "solana",
        "dexId": "raydium",
        "pairAddress": "0xPair",
        "baseToken": {"symbol": "TEST", "name": "Test Token"},
        "priceUsd": "0.42",
        "liquidity": {"usd": 123456.0},
        "volume": {"h1": 9999.0, "h24": 45000.0},
        "pairCreatedAt": 1755000000000,
    }]
}


def _fixture_registry() -> MCPToolRegistry:
    """Registry whose market-data tool is backed by a fixture transport, so
    collect() returns REAL parsed values (no network)."""
    routes = {"api.dexscreener.com": DEXSCREENER_PAYLOAD}
    collector = ProviderCollector(transport=_RoutingTransport(routes))
    return MCPToolRegistry(collector=collector)


# ---------------------------------------------------------------- tool listing

def test_mcp_list_tools():
    registry = MCPToolRegistry()
    tools = registry.list_tools()

    assert len(tools) >= 2
    tool_names = [t["name"] for t in tools]
    assert "market_data_query" in tool_names
    assert "risk_assessment" in tool_names


# ------------------------------------------------- market data: honest values

def test_mcp_market_data_returns_real_provider_values():
    registry = _fixture_registry()
    res = registry.call_tool("market_data_query", {"token": SOL_ADDR})

    assert res["isError"] is False
    data = res["structured_data"]
    assert data["token"] == SOL_ADDR
    assert data["data_status"] == "OK"
    # values come from the provider fixture, not a hardcoded symbol table
    assert data["price_usd"] == 0.42
    assert data["liquidity_usd"] == 123456.0
    assert data["24h_volume_usd"] == 45000.0
    # provenance travels with the answer
    assert data["field_sources"]["metrics.price_usd"] == "dexscreener"
    assert data["provider_statuses"]["dexscreener"] == "OK"


def test_mcp_market_data_unknown_when_no_provider_data():
    """No provider data => honest UNKNOWN with null fields, never a fabricated
    price. The previous hardcoded `185.50 if SOL` behavior is forbidden."""
    collector = ProviderCollector(transport=_ExplodingTransport())
    registry = MCPToolRegistry(collector=collector)
    res = registry.call_tool("market_data_query", {"token": SOL_ADDR})

    assert res["isError"] is False  # an honest answer, not an error
    data = res["structured_data"]
    assert data["data_status"] == "UNKNOWN"
    assert data["price_usd"] is None
    assert data["liquidity_usd"] is None
    assert data["24h_volume_usd"] is None
    assert data["market_cap_usd"] is None
    assert all(s in ("DOWN", "ERROR", "UNSUPPORTED", "NO_KEY")
               for s in data["provider_statuses"].values())
    assert data["confidence_level"] == "LOW"


def test_mcp_market_data_refuses_symbols_honestly():
    """A symbol like 'SOL' cannot be resolved to a contract address; the tool
    must refuse with UNKNOWN rather than inventing a price."""
    registry = _fixture_registry()
    res = registry.call_tool("market_data_query", {"token": "SOL"})

    assert res["isError"] is False
    data = res["structured_data"]
    assert data["data_status"] == "UNKNOWN"
    assert data["price_usd"] is None
    assert "contract address" in (data.get("note") or "")
    # the fixture transport must never have been hit for a symbol
    assert data["provider_statuses"] == {}


def test_mcp_market_data_chain_parameter():
    registry = _fixture_registry()
    res = registry.call_tool(
        "market_data_query", {"token": SOL_ADDR, "chain": "solana"})
    assert res["structured_data"]["chain"] == "solana"


def test_mcp_market_data_missing_token_refused():
    registry = _fixture_registry()
    res = registry.call_tool("market_data_query", {})
    assert res["isError"] is False
    assert res["structured_data"]["data_status"] == "UNKNOWN"


# ---------------------------------------------------------------- risk tool

def test_mcp_risk_assessment_is_formula_from_inputs():
    registry = MCPToolRegistry()
    res = registry.call_tool("risk_assessment", {"capital_usd": 10000.0, "risk_pct": 2.0})
    assert res["isError"] is False
    data = res["structured_data"]
    assert data["recommended_position_usd"] == 200.0
    assert data["portfolio_exposure_pct"] == 2.0
    assert data["max_drawdown_limit_usd"] == 500.0  # documented 5% model param


# ---------------------------------------------------------------- security gate

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
        "market_data_query", {"token": "SOL; rm -rf database"})
    assert res["isError"] is True
    assert "SECURITY_VIOLATION" in res["content"][0]["text"]


def test_mcp_audit_log_records_invocations():
    registry = _fixture_registry()
    registry.call_tool("market_data_query", {"token": SOL_ADDR})
    assert len(registry.sandbox.audit_log) == 1
    entry = registry.sandbox.audit_log[0]
    assert entry["tool_name"] == "market_data_query"
    assert entry["status"] == "SUCCESS"
