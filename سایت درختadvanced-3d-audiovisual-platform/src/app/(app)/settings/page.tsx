import { PageHeader } from "@/components/page-header";
import { SettingsForm } from "@/components/settings-form";
import { loadSettings } from "@/lib/queries";

export const dynamic = "force-dynamic";

export default async function SettingsPage() {
  const rows = await loadSettings();
  const workspace = (rows.find((r) => r.key === "workspace")?.value ?? {}) as Record<string, unknown>;
  return (
    <div>
      <PageHeader
        kicker="Settings"
        title="Single user. Zero budget. Local first."
        lede="Windows laptop, PowerShell, local Python later, local Postgres now. No provider owns the architecture."
      />
      <SettingsForm initial={workspace} />
    </div>
  );
}
