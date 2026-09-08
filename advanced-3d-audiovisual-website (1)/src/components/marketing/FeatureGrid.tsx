"use client";

import { motion } from "framer-motion";
import { ShieldBan, Bot, GitBranch, RefreshCw, Send, FlaskConical } from "lucide-react";
import { RevealCard } from "@/components/ui/Card";
import { useAudio } from "@/components/system/AudioProvider";

const features = [
  { icon: ShieldBan, title: "Security Risk Gate", desc: "High opportunity + critical security risk always equals REJECT. Risk overrides greed — no exceptions.", tone: "text-rose-300", bg: "bg-rose-400/10 border-rose-400/30" },
  { icon: FlaskConical, title: "Paper Trading Engine", desc: "Every opportunity gets a hypothetical position with entry, stop, targets and full lifecycle monitoring.", tone: "text-cyan-300", bg: "bg-cyan-400/10 border-cyan-400/30" },
  { icon: RefreshCw, title: "Win / Loss / Skip Learning", desc: "Every outcome — including a correct SKIP — is post-mortemed and fed back into the system.", tone: "text-violet-300", bg: "bg-violet-400/10 border-violet-400/30" },
  { icon: Send, title: "Telegram Companion", desc: "Ask 'What's today's best opportunity?' and get an evidence-backed answer, plus real-time alerts.", tone: "text-sky-300", bg: "bg-sky-400/10 border-sky-400/30" },
  { icon: Bot, title: "n8n Agent Orchestration", desc: "Discovery, scoring, and reporting workflows run as modular automated agents — no VPS required.", tone: "text-amber-300", bg: "bg-amber-400/10 border-amber-400/30" },
  { icon: GitBranch, title: "GitHub-Native Workflow", desc: "Every change is proposed, reviewed, tested and documented directly inside the repository.", tone: "text-slate-200", bg: "bg-white/5 border-white/20" },
];

export function FeatureGrid() {
  const { play } = useAudio();
  return (
    <section className="relative py-32">
      <div className="mx-auto max-w-7xl px-6">
        <RevealCard>
          <span className="text-xs font-medium uppercase tracking-[0.3em] text-violet-300">System Capabilities</span>
          <h2 className="mt-4 max-w-2xl font-display text-4xl font-bold leading-tight text-white sm:text-5xl">
            Built for evidence. <span className="text-gradient">Hardened against illusion.</span>
          </h2>
        </RevealCard>

        <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f, i) => (
            <RevealCard key={f.title} delay={i * 0.05}>
              <motion.div
                data-cursor-interactive
                onMouseEnter={() => play.hover()}
                whileHover={{ y: -6 }}
                className="glass noise-border h-full rounded-2xl p-6"
              >
                <div className={`grid h-11 w-11 place-items-center rounded-xl border ${f.bg} ${f.tone}`}>
                  <f.icon size={20} />
                </div>
                <h3 className="mt-5 font-display text-lg font-semibold text-white">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-400">{f.desc}</p>
              </motion.div>
            </RevealCard>
          ))}
        </div>
      </div>
    </section>
  );
}
