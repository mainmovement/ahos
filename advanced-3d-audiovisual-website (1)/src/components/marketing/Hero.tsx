"use client";

import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import { ArrowRight, PlayCircle, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/Button";

const HeroScene = dynamic(() => import("@/components/three/HeroScene").then((m) => m.HeroScene), {
  ssr: false,
});

const tickerItems = [
  "TOKEN DISCOVERY", "SECURITY RISK GATE", "AI EXPERT COUNCIL — 10 TEAMS", "ON-CHAIN INTELLIGENCE",
  "SOCIAL & NARRATIVE ANALYSIS", "PAPER TRADING ENGINE", "SELF-LEARNING LOOP", "EVIDENCE BEFORE DECISION",
];

export function Hero() {
  return (
    <section id="top" className="relative flex min-h-[100svh] items-center overflow-hidden pt-24">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_50%_20%,rgba(139,123,255,0.16),transparent_60%),radial-gradient(ellipse_at_80%_80%,rgba(53,240,208,0.12),transparent_55%)]" />
      <HeroScene />
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-transparent via-void/10 to-void" />

      <div className="relative z-10 mx-auto grid w-full max-w-7xl gap-10 px-6">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
          className="max-w-3xl"
        >
          <span className="inline-flex items-center gap-2 rounded-full border border-cyan-300/30 bg-cyan-300/5 px-3.5 py-1.5 text-[11px] font-medium uppercase tracking-[0.2em] text-cyan-300">
            <span className="h-1.5 w-1.5 animate-pulse-glow rounded-full bg-cyan-300" />
            Artificial Hybrid Opportunity Scoring System
          </span>

          <h1 className="mt-6 font-display text-[clamp(2.6rem,7vw,5.5rem)] font-bold leading-[0.98] tracking-tight text-white">
            The intelligence
            <br />
            that finds the
            <br />
            <span className="text-gradient">opportunity first.</span>
          </h1>

          <p className="mt-6 max-w-xl text-base leading-relaxed text-slate-300 sm:text-lg">
            AHOS is not a trading bot. It is a council of ten specialized intelligence teams that
            discover, interrogate, and verify emerging token opportunities — separating real signal
            from scams, rumors, and manufactured hype, before deciding anything.
          </p>

          <div className="mt-9 flex flex-wrap items-center gap-4">
            <Button href="/dashboard" size="lg" icon={<PlayCircle size={18} />} iconRight={<ArrowRight size={18} />}>
              Enter the Dashboard
            </Button>
            <Button href="#philosophy" variant="secondary" size="lg">
              Explore the Philosophy
            </Button>
          </div>

          <div className="mt-12 grid max-w-lg grid-cols-3 gap-6 border-t border-white/10 pt-6">
            {[
              ["10", "Expert Teams"],
              ["24/7", "Discovery Loop"],
              ["$0", "Infrastructure Budget"],
            ].map(([value, label]) => (
              <div key={label}>
                <div className="font-display text-2xl font-bold text-white">{value}</div>
                <div className="text-xs text-slate-400">{label}</div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      <div className="absolute inset-x-0 bottom-0 z-10 border-y border-white/10 bg-black/30 py-3 backdrop-blur-sm">
        <div className="flex overflow-hidden">
          <div className="flex shrink-0 animate-marquee gap-10 whitespace-nowrap pr-10">
            {[...tickerItems, ...tickerItems].map((item, i) => (
              <span key={i} className="flex items-center gap-2 text-xs font-medium uppercase tracking-widest text-slate-400">
                <span className="h-1 w-1 rounded-full bg-cyan-300" />
                {item}
              </span>
            ))}
          </div>
        </div>
      </div>

      <motion.a
        href="#philosophy"
        animate={{ y: [0, 8, 0] }}
        transition={{ duration: 1.8, repeat: Infinity }}
        className="absolute bottom-16 left-1/2 z-10 hidden -translate-x-1/2 text-slate-400 sm:block"
        aria-label="Scroll down"
      >
        <ChevronDown size={22} />
      </motion.a>
    </section>
  );
}
