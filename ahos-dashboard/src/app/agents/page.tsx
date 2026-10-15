import type { Metadata } from "next";
import { getAgents } from "@/lib/api/agents";
import { AgentsView } from "@/components/views/agents-view";

export const metadata: Metadata = { title: "مرکز عامل‌ها · Agent Center" };

export default async function AgentsPage({ searchParams }: { searchParams: Promise<{ agent?: string }> }) {
  const [{ agent }, agents] = await Promise.all([searchParams, getAgents()]);
  return <AgentsView agents={agents} initialAgent={agent} />;
}
