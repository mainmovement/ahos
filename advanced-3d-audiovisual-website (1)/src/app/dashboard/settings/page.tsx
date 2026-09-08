import { getAllSettings } from "@/lib/queries";
import { PageHeader } from "@/components/dashboard/Shared";
import { SettingsForm } from "@/components/dashboard/SettingsForm";

export const dynamic = "force-dynamic";

export default async function SettingsPage() {
  const settings = await getAllSettings();

  const notifications = (settings.notifications as { minOpportunityScore: number; minConfidence: number; criticalSecurityOnly: boolean }) ?? {
    minOpportunityScore: 70, minConfidence: 60, criticalSecurityOnly: false,
  };
  const riskGate = (settings.risk_gate as { maxAcceptableRisk: string; autoRejectCritical: boolean }) ?? {
    maxAcceptableRisk: "medium", autoRejectCritical: true,
  };
  const aiProviders = (settings.ai_providers as { primary: string; fallbacks: string[] }) ?? {
    primary: "local-reasoning-engine", fallbacks: ["openai", "anthropic", "gemini"],
  };
  const budget = (settings.budget as { monthlyUsd: number; infrastructure: string }) ?? {
    monthlyUsd: 0, infrastructure: "local + free tiers only",
  };

  return (
    <div>
      <PageHeader eyebrow="Configuration" title="Settings" description="Single-user system configuration — thresholds, risk posture, providers, and budget." />
      <SettingsForm notifications={notifications} riskGate={riskGate} aiProviders={aiProviders} budget={budget} />
    </div>
  );
}
