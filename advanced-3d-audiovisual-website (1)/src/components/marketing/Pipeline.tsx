"use client";

import { motion } from "framer-motion";
import { RevealCard } from "@/components/ui/Card";

const steps = [
  "Discovery", "Evidence Collection", "Security Screening", "Team Analysis",
  "Cross Examination", "Contrarian Analysis", "Council Debate", "Final Scoring",
  "Confidence", "Decision",
];

const funnel = [
  { label: "Candidates Screened", value: "1,000+" },
  { label: "Investigated", value: "100" },
  { label: "Strong Candidates", value: "20" },
  { label: "High Quality", value: "5" },
  { label: "Exceptional Opportunity", value: "1" },
];

export function Pipeline() {
  return (
    <section id="pipeline" className="relative py-32">
      <div className="mx-auto max-w-7xl px-6">
        <RevealCard>
          <span className="text-xs font-medium uppercase tracking-[0.3em] text-magenta">Section 13 — Process</span>
          <h2 className="mt-4 max-w-2xl font-display text-4xl font-bold leading-tight text-white sm:text-5xl">
            No shortcuts. <span className="text-gradient">Ten gates to a decision.</span>
          </h2>
        </RevealCard>

        <RevealCard delay={0.1} className="mt-14">
          <div className="glass noise-border overflow-x-auto rounded-2xl p-6">
            <div className="flex min-w-[900px] items-center">
              {steps.map((step, i) => (
                <div key={step} className="flex flex-1 items-center">
                  <div className="flex flex-col items-center gap-2 text-center">
                    <motion.div
                      initial={{ scale: 0.6, opacity: 0 }}
                      whileInView={{ scale: 1, opacity: 1 }}
                      viewport={{ once: true }}
                      transition={{ delay: i * 0.06 }}
                      className="grid h-11 w-11 shrink-0 place-items-center rounded-full border border-cyan-300/40 bg-cyan-300/10 font-mono text-xs font-bold text-cyan-200"
                    >
                      {i + 1}
                    </motion.div>
                    <span className="w-24 text-[11px] leading-tight text-slate-300">{step}</span>
                  </div>
                  {i < steps.length - 1 && <div className="mx-1 h-px flex-1 bg-gradient-to-r from-cyan-300/40 to-violet-400/20" />}
                </div>
              ))}
            </div>
          </div>
        </RevealCard>

        <RevealCard delay={0.2} className="mt-10">
          <div className="glass-strong noise-border rounded-2xl p-8">
            <p className="mb-6 text-xs uppercase tracking-[0.25em] text-slate-400">The Golden Fruit Funnel</p>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              {funnel.map((f, i) => (
                <div key={f.label} className="flex flex-1 items-center gap-3">
                  <div className="flex-1 text-center">
                    <div className="font-display text-2xl font-bold text-gradient sm:text-3xl">{f.value}</div>
                    <div className="mt-1 text-[11px] uppercase tracking-wide text-slate-400">{f.label}</div>
                  </div>
                  {i < funnel.length - 1 && <div className="hidden h-8 w-px bg-white/10 sm:block" />}
                </div>
              ))}
            </div>
          </div>
        </RevealCard>
      </div>
    </section>
  );
}
