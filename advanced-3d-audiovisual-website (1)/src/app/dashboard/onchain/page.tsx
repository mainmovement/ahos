import { listOnchainEvents } from "@/lib/queries";
import { PageHeader } from "@/components/dashboard/Shared";
import { Card } from "@/components/ui/Card";
import { formatUsd, timeAgo } from "@/lib/utils";
import { ArrowUpRight, Wallet } from "lucide-react";

export const dynamic = "force-dynamic";

const eventColor: Record<string, string> = {
  whale_accumulation: "text-emerald-300 border-emerald-400/30 bg-emerald-400/5",
  liquidity_add: "text-cyan-300 border-cyan-400/30 bg-cyan-400/5",
  large_transfer: "text-amber-300 border-amber-400/30 bg-amber-400/5",
  deployer_transfer: "text-rose-300 border-rose-400/30 bg-rose-400/5",
  contract_upgrade: "text-violet-300 border-violet-400/30 bg-violet-400/5",
  holder_growth: "text-cyan-300 border-cyan-400/30 bg-cyan-400/5",
};

export default async function OnChainPage() {
  const rows = await listOnchainEvents();

  return (
    <div>
      <PageHeader
        eyebrow="Team 03"
        title="On-Chain Intelligence"
        description="Wallet behavior, whale accumulation, and deployer activity — the ground truth beneath the narrative."
      />

      <Card>
        <div className="relative space-y-4 pl-6">
          <div className="absolute bottom-2 left-[7px] top-2 w-px bg-gradient-to-b from-cyan-300/40 via-white/10 to-transparent" />
          {rows.map(({ event, token }) => (
            <div key={event.id} className="relative">
              <span className={`absolute -left-6 top-1.5 h-3 w-3 rounded-full border-2 ${eventColor[event.eventType] ?? "border-white/30"} bg-void`} />
              <div className={`rounded-xl border p-4 ${eventColor[event.eventType] ?? "border-white/10 bg-white/[0.02]"}`}>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <a href={`/dashboard/tokens/${token.id}`} data-cursor-interactive className="flex items-center gap-2 text-sm font-semibold text-slate-100">
                    <span>{token.logoEmoji}</span> {token.name} <span className="text-slate-500">${token.symbol}</span>
                  </a>
                  <span className="flex items-center gap-1 font-mono text-xs">
                    <ArrowUpRight size={12} /> {formatUsd(event.amountUsd, { compact: true })}
                  </span>
                </div>
                <p className="mt-2 text-sm text-slate-300">{event.description}</p>
                <div className="mt-2 flex items-center gap-3 text-[11px] text-slate-500">
                  <span className="flex items-center gap-1 font-mono"><Wallet size={11} /> {event.walletAddress}</span>
                  <span>{timeAgo(event.occurredAt)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
