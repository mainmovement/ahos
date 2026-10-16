"""Kian typed tool allowlist (M35.1).

Tool allowlist: status.read, ledger.read, registry.read, missions.read,
agents.summarize, route.request (bus, QUEUED→TRIAGED only),
action.propose, gate.request.

All tools are READ-ONLY. No write-tool calls in acceptance K-4.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class ToolCallError(Exception):
    """Raised when a tool call fails or is denied."""
    pass


class InvalidToolError(ToolCallError):
    """Raised when an unknown or invalid tool is called."""
    pass


class DeniedToolError(ToolCallError):
    """Raised when a tool is called without proper authorization."""
    pass


class KianTools:
    """Kian's tool registry with strict allowlist.

    Tools are only READ-ONLY. No write-tool calls in acceptance K-4.
    """

    # Allowed tools (READ only)
    ALLOWED_TOOLS = frozenset({
        "status.read",
        "ledger.read",
        "registry.read",
        "missions.read",
        "agents.summarize",
        "route.request",
        "action.propose",
        "gate.request",
    })

    # Tool implementations (mock for now)
    TOOLS: Dict[str, Any] = {
        "status.read": {
            "description": "Read AHOS system status (READ only)",
            "parameters": {
                "type": "object",
                "properties": {
                    "component": {
                        "type": "string",
                        "enum": ["engine", "gateway", "telegram", "database"],
                        "description": "Component to read status for"
                    },
                },
                "required": ["component"],
            },
        },
        "ledger.read": {
            "description": "Read mission ledger records (READ only)",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100,
                        "description": "Number of records to return"
                    },
                    "filter": {
                        "type": "object",
                        "description": "Filter criteria"
                    },
                },
            },
        },
        "registry.read": {
            "description": "Read agent registry (READ only)",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Agent ID to read (omitted = list all)"
                    },
                },
            },
        },
        "missions.read": {
            "description": "Read dev mission queue (READ only)",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["QUEUED", "TRIAGED", "RUNNING", "COMPLETED"],
                        "description": "Filter by status"
                    },
                },
            },
        },
        "agents.summarize": {
            "description": "Summarize agent capabilities and status (READ only)",
            "parameters": {
                "type": "object",
                "properties": {
                    "capabilities": {
                        "type": "boolean",
                        "description": "Include capability lists"
                    },
                },
            },
        },
        "route.request": {
            "description": "Request dev mission queue routing (READ-ONLY, bus, QUEUED→TRIAGED only)",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["TRIAGE"],
                        "description": "Only TRIAGE action allowed"
                    },
                    "missions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Mission IDs to triage"
                    },
                },
            },
        },
        "action.propose": {
            "description": "Propose a dev mission action (READ-ONLY; must be confirmed-gated via pending action store)",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["SUBMIT", "CANCEL"],
                        "description": "Action to propose"
                    },
                    "mission_id": {
                        "type": "string",
                        "description": "Mission ID to propose action on"
                    },
                },
            },
        },
        "gate.request": {
            "description": "Request gate verification for an action (READ-ONLY; code must be provided)",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action to gate verify"
                    },
                    "summary_fa": {
                        "type": "string",
                        "description": "Persian summary of the action"
                    },
                },
            },
        },
    }

    @classmethod
    def execute(
        cls,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Any:
        """Execute a Kian tool. All tools are READ-ONLY."""
        if tool_name not in cls.ALLOWED_TOOLS:
            raise InvalidToolError(f"Tool '{tool_name}' is not in the allowlist")

        # Get tool implementation (mock for now — returns placeholder data)
        tool = cls.TOOLS[tool_name]

        # Execute the tool (mock implementation)
        return cls._execute_tool(tool_name, arguments)

    @classmethod
    def _execute_tool(cls, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool with the given arguments (mock implementation)."""
        if tool_name == "status.read":
            return {
                "component": arguments.get("component", "engine"),
                "status": "running",
                "last_heartbeat": "2026-10-16T04:14:00Z",
            }

        elif tool_name == "ledger.read":
            limit = arguments.get("limit", 10)
            return {
                "records": [
                    {
                        "seq": i,
                        "timestamp": "2026-10-16T04:14:00Z",
                        "event": "test",
                    }
                    for i in range(1, min(limit, 5) + 1)
                ],
                "count": min(limit, 5),
            }

        elif tool_name == "registry.read":
            agent_id = arguments.get("agent_id")
            if agent_id:
                return {
                    "agent_id": agent_id,
                    "role": "Test Agent",
                    "maturity": "REGISTERED",
                    "enabled": True,
                }
            else:
                return {
                    "agents": [
                        {"agent_id": "agent.chief-orchestrator", "enabled": True},
                        {"agent_id": "agent.reality-forensics", "enabled": True},
                    ],
                    "count": 2,
                }

        elif tool_name == "missions.read":
            status = arguments.get("status", "QUEUED")
            return {
                "missions": [
                    {
                        "id": f"DM-00000{i}",
                        "status": status,
                        "title": "Test mission",
                    }
                    for i in range(1, 4)
                ],
                "count": 3,
            }

        elif tool_name == "agents.summarize":
            return {
                "agents": {
                    "agent.chief-orchestrator": {
                        "enabled": True,
                        "maturity": "REGISTERED",
                    },
                    "agent.reality-forensics": {
                        "enabled": True,
                        "maturity": "REGISTERED",
                    },
                },
            }

        elif tool_name == "route.request":
            if arguments.get("action") != "TRIAGE":
                raise DeniedToolError("route.request only allows TRIAGE action")
            missions = arguments.get("missions", [])
            return {
                "action": "TRIAGE",
                "missions": missions,
                "result": "queued for processing",
            }

        elif tool_name == "action.propose":
            action = arguments.get("action")
            if action not in ["SUBMIT", "CANCEL"]:
                raise DeniedToolError("action.propose only allows SUBMIT or CANCEL")
            return {
                "action": action,
                "mission_id": arguments.get("mission_id"),
                "proposed": True,
            }

        elif tool_name == "gate.request":
            action = arguments.get("action")
            summary = arguments.get("summary_fa")
            return {
                "action": action,
                "summary": summary,
                "proposed": True,
            }

        else:
            # Should never reach here due to allowlist check
            raise InvalidToolError(f"Unknown tool: {tool_name}")

    @classmethod
    def validate_tool_call(
        cls,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> bool:
        """Validate a tool call before executing."""
        if tool_name not in cls.ALLOWED_TOOLS:
            return False

        tool = cls.TOOLS.get(tool_name)
        if not tool:
            return False

        params = tool.get("parameters", {}).get("properties", {})
        required = tool.get("parameters", {}).get("required", [])

        # Check required parameters
        for req in required:
            if req not in arguments:
                return False

        # Check argument types (basic validation)
        for key, value in arguments.items():
            param_schema = params.get(key)
            if param_schema:
                param_type = param_schema.get("type")
                if param_type and not isinstance(value, type_mapping.get(param_type)):
                    return False

        return True


# Basic type mapping for validation
type_mapping = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict,
}
