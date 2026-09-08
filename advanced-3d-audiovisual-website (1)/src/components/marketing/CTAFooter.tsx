"use client";

import { ArrowRight, GitBranch } from "lucide-react";
import { RevealCard } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

export function CTAFooter() {
  return (
    <>
      <section className="relative py-32">
        <div className="mx-auto max-w-5xl px-6 text-center">
          <RevealCard>
            <div className="glass-strong noise-border relative overflow-hidden rounded-[2rem] p-12 sm:p-20">
              <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_50%_0%,rgba(53,240,208,0.18),transparent_60%)]" />
              <span className="text-xs font-medium uppercase tracking-[0.3em] text-cyan-300">Evidence Before Decision</span>
              <h2 className="mx-auto mt-5 max-w-2xl font-display text-4xl font-bold leading-tight text-white sm:text-5xl">
                Stop chasing pumps. <span className="text-gradient">Start reading evidence.</span>
              </h2>
              <p className="mx-auto mt-5 max-w-xl text-slate-300">
                Step into the AHOS dashboard — live opportunity scores, a ten-team AI council,
                a security risk gate, and a fully transparent paper trading engine.
              </p>
              <div className="mt-9 flex flex-wrap items-center justify-center gap-4">
                <Button href="/dashboard" size="lg" iconRight={<ArrowRight size={18} />}>
                  Enter the Dashboard
                </Button>
                <Button href="/dashboard/system" variant="secondary" size="lg">
                  View System Status
                </Button>
              </div>
            </div>
          </RevealCard>
        </div>
      </section>

      <footer className="relative border-t border-white/10 py-12">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-6 px-6 sm:flex-row">
          <div className="flex items-center gap-2.5">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-cyan-300 to-violet-500 font-display text-xs font-bold text-slate-950">
              A
            </span>
            <span className="font-display text-sm font-semibold text-white">AHOS</span>
            <span className="text-xs text-slate-500">— Artificial Hybrid Opportunity Scoring System</span>
          </div>
          <div className="flex items-center gap-6 text-xs text-slate-400">
            <a href="https://github.com" target="_blank" rel="noreferrer" data-cursor-interactive className="flex items-center gap-1.5 hover:text-cyan-300">
              <GitBranch size={14} /> Repository
            </a>
            <span>Single-user system · $0 infrastructure budget · Local-first</span>
          </div>
        </div>
      </footer>
    </>
  );
}
