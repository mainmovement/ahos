import type { AgentEvent, AgentsOverview, DataEnvelope } from "./types";
import { fromMock, label } from "./_envelope";
import { mockAgentActivity, mockAgents } from "@/mock/agents";

/** Agent roster. Real source: agent registry (AGENT_REGISTRY_MODEL.md) + runtime heartbeats. */
export async function getAgents(): Promise<DataEnvelope<AgentsOverview>> {
  return fromMock(mockAgents(), "agents", label("فهرست عامل‌ها (نمایشی)", "Agent roster (demo)"), 30, 120);
}

/** Recent agent events. Real source: runtime event log / audit trail. */
export async function getAgentActivity(): Promise<DataEnvelope<AgentEvent[]>> {
  return fromMock(mockAgentActivity(), "agent-activity", label("رویدادهای عامل (نمایشی)", "Agent events (demo)"), 15, 60);
}
