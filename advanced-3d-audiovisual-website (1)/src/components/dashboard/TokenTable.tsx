"use client";

import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { Badge, decisionTone } from "@/components/ui/Badge";
import { EmptyState } from "@/components/dashboard/Shared";
import { formatUsd, formatPercent } from "@/lib/utils";
import { useAudio } from "@/components/system/AudioProvider";

type Row = {
  token: {
    id: number; name: string; symbol: string; chain: string; status: string; narrative: string | null;
    logoEmoji: string | null; priceUsd: string | null; priceChange24h: string | null; marketCapUsd: string | null;
    liquidityUsd: string | null; holders: number | null;
  };
  score: { opportunityScore: number; securityScore: number; confidence: number; councilDecision: string } | null;
};

const statusLabel: Record<string, string> = { pre_launch: "Pre-Launch", new: "New", existing: "Existing" };

export function TokenTable({ rows }: { rows: Row[] }) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<string>("all");
  const { play } = useAudio();

  const chains = useMemo(() => Array.from(new Set(rows.map((r) => r.token.chain))), [rows]);
  const [chain, setChain] = useState<string>("all");

  const filtered = rows.filter((r) => {
    const matchesQuery =
      query.trim() === "" ||
      r.token.name.toLowerCase().includes(query.toLowerCase()) ||
      r.token.symbol.toLowerCase().includes(query.toLowerCase());
    const matchesStatus = status === "all" || r.token.status === status;
    const matchesChain = chain === "all" || r.token.chain === chain;
    return matchesQuery && matchesStatus && matchesChain;
  });

  return (
    <div>
      <div className="mb-5 flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[220px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={15} />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by name or symbol..."
            className="w-full rounded-full border border-white/10 bg-white/[0.03] py-2.5 pl-9 pr-4 text-sm text-slate-200 outline-none placeholder:text-slate-500 focus:border-cyan-300/50"
          />
        </div>
        <select
          data-cursor-interactive
          value={status}
          onChange={(e) => {
            setStatus(e.target.value);
            play.click();
          }}
          className="rounded-full border border-white/10 bg-white/[0.03] px-4 py-2.5 text-sm text-slate-200 outline-none focus:border-cyan-300/50"
        >
          <option value="all">All Statuses</option>
          <option value="pre_launch">Pre-Launch</option>
          <option value="new">Newly Launched</option>
          <option value="existing">Existing</option>
        </select>
        <select
          data-cursor-interactive
          value={chain}
          onChange={(e) => {
            setChain(e.target.value);
            play.click();
          }}
          className="rounded-full border border-white/10 bg-white/[0.03] px-4 py-2.5 text-sm text-slate-200 outline-none focus:border-cyan-300/50"
        >
          <option value="all">All Chains</option>
          {chains.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      {filtered.length === 0 ? (
        <EmptyState title="No tokens match your filters" description="Try clearing the search or selecting a different chain / status." />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {filtered.map(({ token, score }) => (
            <a
              key={token.id}
              href={`/dashboard/tokens/${token.id}`}
              data-cursor-interactive
              onMouseEnter={() => play.hover()}
              className="glass noise-border group flex flex-col rounded-2xl p-5 transition-transform hover:-translate-y-1"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <span className="text-2xl">{token.logoEmoji}</span>
                  <div>
                    <div className="font-display text-sm font-semibold text-white group-hover:text-cyan-300">{token.name}</div>
                    <div className="text-xs text-slate-500">${token.symbol} · {token.chain}</div>
                  </div>
                </div>
                {score && <span className="font-display text-xl font-bold text-cyan-300">{score.opportunityScore}</span>}
              </div>

              <div className="mt-4 flex flex-wrap items-center gap-1.5">
                <Badge tone="neutral">{statusLabel[token.status]}</Badge>
                {token.narrative && <Badge tone="violet">{token.narrative}</Badge>}
                {score && <Badge tone={decisionTone(score.councilDecision)}>{score.councilDecision.replace("_", " ")}</Badge>}
              </div>

              <div className="mt-4 grid grid-cols-3 gap-2 border-t border-white/8 pt-4 text-xs">
                <div>
                  <div className="text-slate-500">Price</div>
                  <div className="mt-0.5 font-mono text-slate-200">{formatUsd(token.priceUsd)}</div>
                </div>
                <div>
                  <div className="text-slate-500">24h</div>
                  <div className={`mt-0.5 font-mono ${Number(token.priceChange24h) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                    {formatPercent(token.priceChange24h)}
                  </div>
                </div>
                <div>
                  <div className="text-slate-500">Liquidity</div>
                  <div className="mt-0.5 font-mono text-slate-200">{formatUsd(token.liquidityUsd, { compact: true })}</div>
                </div>
              </div>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
