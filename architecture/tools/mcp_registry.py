"""AHOS Model Context Protocol (MCP) Tool Registry (FastMCP Pattern).

Standardized JSON-RPC tool interface exposing AHOS analytical, backtesting,
and market intelligence tools to agents within strict sandbox boundaries.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from architecture.tools.sandbox import SecuritySandbox, SecuritySandboxViolation


class MCPToolRegistry:
    """Registry and dispatcher for MCP-compliant agent tools."""

    def __init__(self, sandbox: Optional[SecuritySandbox] = None) -> None:
        self.sandbox = sandbox or SecuritySandbox()
        self.tools: Dict[str, Dict[str, Any]] = {}
        self._register_default_tools()

    def register_tool(
        self,
        name: str,
        description: str,
        parameters_schema: Dict[str, Any],
        handler: Callable[..., Any],
    ) -> None:
        """Registers a new tool into the MCP registry."""
        self.tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": parameters_schema,
            "handler": handler,
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        """Returns the list of available tools formatted for MCP tools/list."""
        return [
            {
                "name": t["name"],
                "description": t["description"],
                "inputSchema": t["inputSchema"],
            }
            for t in self.tools.values()
        ]

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches an MCP tools/call request through the security sandbox."""
        if name not in self.tools:
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Tool '{name}' not found."}],
            }

        try:
            self.sandbox.validate_tool_invocation(name, arguments)
            handler = self.tools[name]["handler"]
            result = handler(**arguments)
            self.sandbox.log_invocation(name, arguments, status="SUCCESS")
            return {
                "isError": False,
                "content": [{"type": "text", "text": str(result)}],
                "structured_data": result,
            }
        except SecuritySandboxViolation as e:
            self.sandbox.log_invocation(name, arguments, status="SECURITY_BLOCKED")
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"SECURITY_VIOLATION: {str(e)}"}],
            }
        except Exception as e:
            self.sandbox.log_invocation(name, arguments, status="EXECUTION_ERROR")
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"EXECUTION_ERROR: {str(e)}"}],
            }

    def _register_default_tools(self) -> None:
        """Registers core AHOS analytical and risk tools."""

        def _market_data_query(token: str) -> Dict[str, Any]:
            return {
                "token": token,
                "price_usd": 185.50 if token.upper() == "SOL" else 1.00,
                "liquidity_usd": 1200000.0,
                "24h_volume_usd": 450000.0,
            }

        def _risk_assessment(
            capital_usd: float, risk_pct: float
        ) -> Dict[str, Any]:
            max_pos = capital_usd * (risk_pct / 100.0)
            return {
                "recommended_position_usd": round(max_pos, 2),
                "portfolio_exposure_pct": risk_pct,
                "max_drawdown_limit_usd": round(capital_usd * 0.05, 2),
            }

        self.register_tool(
            name="market_data_query",
            description="Queries current market price and liquidity for a token symbol or address.",
            parameters_schema={
                "type": "object",
                "properties": {
                    "token": {"type": "string", "description": "Token symbol or address"}
                },
                "required": ["token"],
            },
            handler=_market_data_query,
        )

        self.register_tool(
            name="risk_assessment",
            description="Calculates risk limits and recommended position sizes.",
            parameters_schema={
                "type": "object",
                "properties": {
                    "capital_usd": {"type": "number"},
                    "risk_pct": {"type": "number"},
                },
                "required": ["capital_usd", "risk_pct"],
            },
            handler=_risk_assessment,
        )
