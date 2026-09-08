"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Volume2, VolumeX, Menu, X } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useAudio } from "@/components/system/AudioProvider";

const links = [
  { href: "#philosophy", label: "Philosophy" },
  { href: "#council", label: "AI Council" },
  { href: "#pipeline", label: "Pipeline" },
  { href: "#stats", label: "Live Intel" },
  { href: "#roadmap", label: "Roadmap" },
];

export function MarketingNav() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const { muted, toggleMuted, play } = useAudio();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <motion.header
      initial={{ y: -80, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
      className={`fixed inset-x-0 top-0 z-50 transition-all duration-300 ${scrolled ? "backdrop-blur-xl" : ""}`}
    >
      <div className={`mx-auto flex max-w-7xl items-center justify-between px-6 py-4 transition-all ${scrolled ? "" : ""}`}>
        <a href="#top" data-cursor-interactive className="flex items-center gap-2.5" onClick={() => play.nav()}>
          <span className="relative flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-300 to-violet-500">
            <span className="absolute inset-0 rounded-lg bg-cyan-300 blur-md opacity-40" />
            <span className="relative font-display text-sm font-bold text-slate-950">A</span>
          </span>
          <span className="font-display text-lg font-bold tracking-wide text-white">
            AHOS<span className="text-cyan-300">.</span>
          </span>
        </a>

        <nav className="hidden items-center gap-8 lg:flex">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              data-cursor-interactive
              onMouseEnter={() => play.hover()}
              onClick={() => play.nav()}
              className="text-sm text-slate-300 transition-colors hover:text-cyan-300"
            >
              {l.label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <button
            data-cursor-interactive
            onClick={toggleMuted}
            aria-label={muted ? "Unmute interface sounds" : "Mute interface sounds"}
            className="grid h-9 w-9 place-items-center rounded-full border border-white/15 text-slate-300 transition-colors hover:border-cyan-300/60 hover:text-cyan-300"
          >
            {muted ? <VolumeX size={16} /> : <Volume2 size={16} />}
          </button>
          <div className="hidden sm:block">
            <Button href="/dashboard" size="sm">
              Enter Dashboard
            </Button>
          </div>
          <button
            data-cursor-interactive
            className="grid h-9 w-9 place-items-center rounded-full border border-white/15 text-slate-200 lg:hidden"
            onClick={() => setOpen((v) => !v)}
            aria-label="Toggle menu"
          >
            {open ? <X size={16} /> : <Menu size={16} />}
          </button>
        </div>
      </div>

      {open && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          className="glass-strong mx-4 mb-4 rounded-2xl p-4 lg:hidden"
        >
          <div className="flex flex-col gap-3">
            {links.map((l) => (
              <a key={l.href} href={l.href} onClick={() => setOpen(false)} className="py-1 text-sm text-slate-200">
                {l.label}
              </a>
            ))}
            <Button href="/dashboard" size="sm" className="mt-2 w-full">
              Enter Dashboard
            </Button>
          </div>
        </motion.div>
      )}
    </motion.header>
  );
}
