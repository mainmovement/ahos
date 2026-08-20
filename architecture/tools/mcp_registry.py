"""AHOS Model Context Protocol (MCP) Tool Registry (FastMCP Pattern).

Standardized JSON-RPC tool interface exposing AHOS analytical, backtesting,
and market intelligence tools to agents within strict sandbox boundaries.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from architecture.tools.sandbox import SecuritySandbox, SecuritySandboxViolation


class MCPToolRegistry:
    """Registry and dispatcher for MCP-compliant agent tools."""

    def __init__(self, sandbox: Optional[SecuritySandbox] = None,
                 collector: Optional[Any] = None) -> None:
        self.sandbox = sandbox or SecuritySandbox()
        self._collector = collector
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
        """Registers core AHOS analytical and risk tools.

        HONESTY LAW: the market-data tool must never fabricate numbers. It
        resolves real provider data through the unified ProviderCollector and
        reports `data_status: "OK"` only when at least one field was actually
        observed; otherwise every field stays None with `data_status:
        "UNKNOWN"` and the per-provider statuses/provenance are returned so an
        agent can see exactly why nothing is known (M-GAP-016 discipline).
        """

        def _market_data_query(token: str = "", chain: str = "solana") -> Dict[str, Any]:
            collector = self._collector
            if collector is None:
                from ..providers.collect import ProviderCollector
                collector = ProviderCollector()

            # Symbols cannot be resolved to a contract address by the provider
            # layer; answering with a fabricated price would violate the
            # UNKNOWN-over-invention law. Addresses (Solana base58 / EVM hex)
            # are >= 32 chars; anything shorter is treated as a symbol and
            # honestly refused.
            if not token or len(token) < 32:
                return {
                    "token": token,
                    "chain": chain,
                    "data_status": "UNKNOWN",
                    "note": ("a contract address is required for provider "
                             "resolution; symbols cannot be mapped without a "
                             "local registry (never fabricated)"),
                    "price_usd": None,
                    "liquidity_usd": None,
                    "24h_volume_usd": None,
                    "market_cap_usd": None,
                    "fdv_usd": None,
                    "provider_statuses": {},
                    "unknown_fields": ["address"],
                }
            try:
                outcome = collector.collect(chain=chain, address=token)
            except Exception as e:
                # Fail-closed: an exception is evidence, never a reason to
                # invent data.
                return {
                    "token": token,
                    "chain": chain,
                    "data_status": "UNKNOWN",
                    "note": f"provider collection failed: {type(e).__name__}: {str(e)[:200]}",
                    "price_usd": None,
                    "liquidity_usd": None,
                    "24h_volume_usd": None,
                    "market_cap_usd": None,
                    "fdv_usd": None,
                    "provider_statuses": {},
                    "unknown_fields": [],
                }

            cand = outcome.candidate
            known = bool(outcome.field_sources)
            return {
                "token": token,
                "chain": chain,
                "data_status": "OK" if known else "UNKNOWN",
                "note": None if known else (
                    "no provider returned data for this address; all fields "
                    "are UNKNOWN (never fabricated)"),
                "price_usd": cand.metrics.price_usd,
                "liquidity_usd": cand.metrics.liquidity_usd,
                "24h_volume_usd": cand.metrics.volume_24h,
                "market_cap_usd": cand.metrics.market_cap_usd,
                "fdv_usd": cand.metrics.fdv_usd,
                "provider_statuses": outcome.provider_statuses,
                "field_sources": outcome.field_sources,
                "unknown_fields": outcome.unknown_fields,
                "confidence_level": cand.confidence_level,
            }

        def _risk_assessment(
            capital_usd: float, risk_pct: float
        ) -> Dict[str, Any]:
            # Deterministic sizing formula from PROVIDED inputs only — no
            # market data is invented here. The drawdown guard is a fixed
            # model parameter (5% of capital), documented as such.
            max_pos = capital_usd * (risk_pct / 100.0)
            return {
                "recommended_position_usd": round(max_pos, 2),
                "portfolio_exposure_pct": risk_pct,
                "max_drawdown_limit_usd": round(capital_usd * 0.05, 2),
            }

        self.register_tool(
            name="market_data_query",
            description=("Queries market price, liquidity and volume for a "
                         "token CONTRACT ADDRESS via the provider layer. "
                         "Returns data_status UNKNOWN with null fields when "
                         "no provider data is available — never fabricated."),
            parameters_schema={
                "type": "object",
                "properties": {
                    "token": {"type": "string",
                              "description": "Token contract address (required; symbols are not resolvable)"},
                    "chain": {"type": "string", "description": "Chain: solana, ethereum, bsc, base, ...",
                              "default": "solana"},
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
