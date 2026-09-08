"use client";

import { RevealCard } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

const phases = [
  { phase: "01", title: "Token Discovery Intelligence", desc: "Find emerging token opportunities across pre-launch, new, and hidden existing candidates.", status: "Active" },
  { phase: "02", title: "Advanced Paper Trading", desc: "Position management, advanced exits, portfolio simulation, performance analytics.", status: "Active" },
  { phase: "03", title: "Automated Token Trading", desc: "Execute real trades only after the system is fully proven.", status: "Planned" },
  { phase: "04", title: "Automated Crypto Trading", desc: "Expand from token discovery into broader crypto markets.", status: "Planned" },
  { phase: "05", title: "Advanced Chart Intelligence", desc: "Deep technical analysis across timeframes and instruments.", status: "Future" },
  { phase: "06", title: "Gold Intelligence", desc: "Extend the council architecture to commodities.", status: "Future" },
  { phase: "07", title: "Forex Intelligence", desc: "Extend the council architecture to currency markets.", status: "Future" },
];

const statusTone: Record<string, "good" | "cyan" | "neutral"> = { Active: "good", Planned: "cyan", Future: "neutral" };

export function Roadmap() {
  return (
    <section id="roadmap" className="relative py-32">
      <div className="mx-auto max-w-7xl px-6">
        <RevealCard>
          <span className="text-xs font-medium uppercase tracking-[0.3em] text-cyan-300">Section 51 — Roadmap</span>
          <h2 className="mt-4 max-w-2xl font-display text-4xl font-bold leading-tight text-white sm:text-5xl">
            Foundation first. <span className="text-gradient">Expansion second.</span>
          </h2>
          <p className="mt-5 max-w-2xl text-slate-300">
            No future phase is allowed to leave Phase 1 unstable. Seed → Root → Tree → Forest → Ecosystem.
          </p>
        </RevealCard>

        <div className="relative mt-14 space-y-4">
          <div className="absolute left-6 top-2 bottom-2 hidden w-px bg-gradient-to-b from-cyan-300/50 via-violet-400/30 to-transparent sm:block" />
          {phases.map((p, i) => (
            <RevealCard key={p.phase} delay={i * 0.05}>
              <div className="glass noise-border relative rounded-2xl p-5 pl-6 sm:pl-16">
                <div className="absolute left-4 top-1/2 hidden h-4 w-4 -translate-y-1/2 rounded-full border-2 border-cyan-300 bg-void sm:block" />
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <span className="font-mono text-xs text-slate-500">PHASE {p.phase}</span>
                    <h3 className="mt-1 font-display text-lg font-semibold text-white">{p.title}</h3>
                    <p className="mt-1 max-w-xl text-sm text-slate-400">{p.desc}</p>
                  </div>
                  <Badge tone={statusTone[p.status]}>{p.status}</Badge>
                </div>
              </div>
            </RevealCard>
          ))}
        </div>
      </div>
    </section>
  );
}
