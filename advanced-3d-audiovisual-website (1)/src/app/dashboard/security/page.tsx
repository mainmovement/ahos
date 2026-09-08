import { listSecurityChecks } from "@/lib/queries";
import { PageHeader, KpiCard } from "@/components/dashboard/Shared";
import { Card } from "@/components/ui/Card";
import { Badge, riskTone } from "@/components/ui/Badge";
import { timeAgo } from "@/lib/utils";
import { ShieldCheck, ShieldAlert, ShieldX, CircleCheck, CircleX } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function SecurityPage() {
  const rows = await listSecurityChecks();
  const critical = rows.filter((r) => r.security.riskLevel === "critical").length;
  const high = rows.filter((r) => r.security.riskLevel === "high").length;
  const clean = rows.filter((r) => r.security.riskLevel === "low").length;

  return (
    <div>
      <PageHeader
        eyebrow="Team 04 — Risk Gate"
        title="Security Intelligence"
        description="High opportunity + critical security risk always equals REJECT. This layer can override the entire council."
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <KpiCard label="Clean (Low Risk)" value={clean} icon={<ShieldCheck size={16} />} tone="emerald" />
        <KpiCard label="High Risk" value={high} icon={<ShieldAlert size={16} />} tone="gold" />
        <KpiCard label="Critical (Auto-Reject)" value={critical} icon={<ShieldX size={16} />} tone="rose" />
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        {rows.map(({ security, token }) => (
          <Card key={security.id} className={security.riskLevel === "critical" ? "border-rose-500/30" : ""}>
            <div className="flex items-center justify-between gap-3">
              <a href={`/dashboard/tokens/${token.id}`} data-cursor-interactive className="flex items-center gap-2.5">
                <span className="text-xl">{token.logoEmoji}</span>
                <div>
                  <div className="font-display text-sm font-semibold text-white">{token.name}</div>
                  <div className="text-xs text-slate-500">${token.symbol} · {token.chain}</div>
                </div>
              </a>
              <Badge tone={riskTone(security.riskLevel)}>{security.riskLevel} risk</Badge>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-2 text-xs sm:grid-cols-3">
              {[
                ["Honeypot", security.honeypot],
                ["Mint Authority", security.mintAuthority],
                ["Freeze Authority", security.freezeAuthority],
                ["Renounced", security.ownershipRenounced],
                ["LP Locked", security.liquidityLocked],
                ["Rug History", security.deployerRugHistory],
              ].map(([label, val]) => (
                <div key={label as string} className="flex items-center justify-between rounded-lg border border-white/8 bg-white/[0.02] px-2.5 py-1.5">
                  <span className="text-slate-400">{label}</span>
                  {label === "Renounced" || label === "LP Locked"
                    ? val ? <CircleCheck className="text-emerald-400" size={14} /> : <CircleX className="text-rose-400" size={14} />
                    : val ? <CircleX className="text-rose-400" size={14} /> : <CircleCheck className="text-emerald-400" size={14} />}
                </div>
              ))}
            </div>

            {(security.flags?.length ?? 0) > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {security.flags!.map((f, i) => <Badge key={i} tone="danger">{f}</Badge>)}
              </div>
            )}
            <p className="mt-3 text-xs text-slate-500">{security.notes}</p>
            <p className="mt-2 text-[10px] uppercase tracking-wider text-slate-600">Checked {timeAgo(security.checkedAt)}</p>
          </Card>
        ))}
      </div>
    </div>
  );
}
