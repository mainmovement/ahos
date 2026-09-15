"""Read-only cognitive research agent host.

The in-process facade still classifies PROCESS_ISOLATION as not provided.
The optional IsolatedResearchRuntime places untrusted cognitive code in a
Windows spawn worker and is classified separately.
"""

from agent_org.research_host.contracts import (
    API_BOUNDARY,
    PROCESS_ISOLATION_PROVIDED,
    SAME_PROCESS_RESIDUAL,
    SAME_PROCESS_RUNTIME,
    HostAuditRecord,
    HostDecision,
    HostResult,
    OperationClass,
    ResearchAgentContext,
    RuntimeClassification,
)
from agent_org.research_host.host import ResearchAgentHost, build_research_agent_host
from agent_org.research_host.supervisor import IsolatedResearchRuntime, WorkerLifecycle

__all__ = [
    "API_BOUNDARY",
    "PROCESS_ISOLATION_PROVIDED",
    "SAME_PROCESS_RESIDUAL",
    "SAME_PROCESS_RUNTIME",
    "HostAuditRecord",
    "HostDecision",
    "HostResult",
    "OperationClass",
    "ResearchAgentContext",
    "IsolatedResearchRuntime",
    "ResearchAgentHost",
    "RuntimeClassification",
    "WorkerLifecycle",
    "build_research_agent_host",
]
