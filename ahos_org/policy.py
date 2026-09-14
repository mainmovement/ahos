"""Canonical capability catalog and fail-closed global denies.

Capabilities are tokens. Unknown tokens are denied by the governance engine.
No capability listed here implies a live connection; Slice 1 is a policy model.
"""

from __future__ import annotations

# Operational capabilities that Slice 1 may grant on *internal* org resources
# when every other gate also passes. These never authorize AHOS access.
INTERNAL_CAPABILITIES = frozenset(
    {
        "task.propose",
        "task.inspect",
        "task.transition",
        "audit.read",
        "audit.append",
        "registry.inspect",
        "policy.inspect",
        "sandbox.execute",
        "paper.analyze",
        "evidence.record",
        "verification.review",
        "redteam.probe",
        "change.propose",
        "release.review",
        "identity.inspect",
        "security.inspect",
        "scoring.inspect",
        "calibration.inspect",
        "frontend.inspect",
        "windows.inspect",
        "integration.inspect",
        "cognitive.inspect",
        "orchestrate.plan",
    }
)

# Never ALLOW, even if an agent record lists them as allowed.
GLOBAL_DENY_CAPABILITIES = frozenset(
    {
        "ahos.connect",
        "ahos.read_source",
        "ahos.write_source",
        "ahos.read_database",
        "ahos.write_database",
        "ahos.start_runtime",
        "ahos.soak",
        "ahos.lane_a",
        "ahos.lane_b",
        "telegram.access",
        "n8n.access",
        "credentials.access",
        "provider.connect",
        "trading.live",
        "production.operate",
    }
)

KNOWN_CAPABILITIES = INTERNAL_CAPABILITIES | GLOBAL_DENY_CAPABILITIES

GLOBAL_DENY_OPERATIONS = frozenset(
    {
        "connect",
        "read_source",
        "write_source",
        "read_database",
        "write_database",
        "start_runtime",
        "soak",
        "lane_a",
        "lane_b",
        "telegram",
        "n8n",
        "credentials",
        "live_trade",
        "production",
    }
)

KNOWN_OPERATIONS = frozenset(
    {
        "inspect",
        "append",
        "execute",
        "propose",
        "review",
        "analyze",
        "record",
        "plan",
        "transition",
        "read",
        "write",
        "delete",
        "query",
        "migrate",
        "invoke",
        "start",
        "stop",
        *GLOBAL_DENY_OPERATIONS,
    }
)

MINIMUM_MATURITY_FOR_ALLOW = 2  # IMPLEMENTED — REGISTERED/DESIGNED cannot execute
MINIMUM_MATURITY_WHEN_VERIFIED_REQUIRED = 4  # VERIFIED
