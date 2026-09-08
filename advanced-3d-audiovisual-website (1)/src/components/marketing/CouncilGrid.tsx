"use client";

import { motion } from "framer-motion";
import {
  Sigma, LineChart, Link2, ShieldAlert, Search, Newspaper, MessageCircle, Code2, BrainCircuit, Swords,
} from "lucide-react";
import { RevealCard } from "@/components/ui/Card";
import { useAudio } from "@/components/system/AudioProvider";

const icons: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
  sigma: Sigma, "line-chart": LineChart, link: Link2, "shield-alert": ShieldAlert, search: Search,
  newspaper: Newspaper, "message-circle": MessageCircle, code: Code2, "brain-circuit": BrainCircuit, swords: Swords,
};

const teams = [
  { code: "T01", name: "Mathematical Intelligence", focus: "Bayesian reasoning, anomaly detection, quantitative modeling.", icon: "sigma" },
  { code: "T02", name: "Crypto Market Intelligence", focus: "Tokenomics, liquidity structure, market cycles.", icon: "line-chart" },
  { code: "T03", name: "Blockchain & On-Chain", focus: "Whale tracking, smart money, holder distribution.", icon: "link" },
  { code: "T04", name: "Cybersecurity & Hacker Intel", focus: "Honeypots, exploits, red-team contract analysis.", icon: "shield-alert" },
  { code: "T05", name: "Investigative Intelligence", focus: "OSINT, entity investigation, contradiction detection.", icon: "search" },
  { code: "T06", name: "News & Journalism Intel", focus: "Source evaluation, narrative detection, verification.", icon: "newspaper" },
  { code: "T07", name: "Social & Narrative Intel", focus: "Sentiment, narrative velocity, influencer analysis.", icon: "message-circle" },
  { code: "T08", name: "Technology & Engineering", focus: "Architecture, automation, APIs, GitHub, DevOps.", icon: "code" },
  { code: "T09", name: "AI Research & Self-Evolution", focus: "Model comparison, reasoning, agent architecture.", icon: "brain-circuit" },
  { code: "T10", name: "Strategic Decision & Red-Team", focus: "Contrarian analysis, bias detection, worst-case sim.", icon: "swords" },
];

export function CouncilGrid() {
  const { play } = useAudio();
  return (
    <section id="council" className="relative py-32">
      <div className="mx-auto max-w-7xl px-6">
        <RevealCard>
          <span className="text-xs font-medium uppercase tracking-[0.3em] text-cyan-300">Section 11 — Governance</span>
          <h2 className="mt-4 max-w-2xl font-display text-4xl font-bold leading-tight text-white sm:text-5xl">
            One AI Council. <span className="text-gradient">Ten specialized minds.</span>
          </h2>
          <p className="mt-5 max-w-2xl text-slate-300">
            No single model decides. Every candidate is cross-examined by ten independent teams —
            including a dedicated red team whose only job is to prove the thesis wrong.
          </p>
        </RevealCard>

        <div className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {teams.map((team, i) => {
            const Icon = icons[team.icon];
            return (
              <RevealCard key={team.code} delay={i * 0.04}>
                <motion.div
                  data-cursor-interactive
                  onMouseEnter={() => play.hover()}
                  whileHover={{ y: -8 }}
                  className="glass noise-border group relative flex h-full flex-col rounded-2xl p-5"
                >
                  <div className="flex items-center justify-between">
                    <div className="grid h-10 w-10 place-items-center rounded-xl border border-white/10 bg-white/5 text-cyan-300 transition-colors group-hover:border-cyan-300/50 group-hover:text-cyan-200">
                      <Icon size={18} />
                    </div>
                    <span className="font-mono text-[10px] text-slate-500">{team.code}</span>
                  </div>
                  <h3 className="mt-4 font-display text-sm font-semibold leading-snug text-white">{team.name}</h3>
                  <p className="mt-2 text-xs leading-relaxed text-slate-400">{team.focus}</p>
                </motion.div>
              </RevealCard>
            );
          })}
        </div>
      </div>
    </section>
  );
}
