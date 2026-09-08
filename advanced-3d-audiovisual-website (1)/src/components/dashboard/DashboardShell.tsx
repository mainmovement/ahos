"use client";

import { useState, type ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard, Coins, LineChart, ShieldAlert, Newspaper, MessageCircle, Link2,
  Bot, Send, Bell, FlaskConical, Activity, Settings, Menu, X, Volume2, VolumeX, ArrowLeft,
} from "lucide-react";
import { useAudio } from "@/components/system/AudioProvider";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/tokens", label: "Token Discovery", icon: Coins },
  { href: "/dashboard/market", label: "Market Intelligence", icon: LineChart },
  { href: "/dashboard/security", label: "Security", icon: ShieldAlert },
  { href: "/dashboard/news", label: "News", icon: Newspaper },
  { href: "/dashboard/social", label: "Social Intelligence", icon: MessageCircle },
  { href: "/dashboard/onchain", label: "On-Chain", icon: Link2 },
  { href: "/dashboard/ai-chat", label: "AI Chat", icon: Bot },
  { href: "/dashboard/telegram", label: "Telegram", icon: Send },
  { href: "/dashboard/alerts", label: "Alerts", icon: Bell },
  { href: "/dashboard/paper-trading", label: "Paper Trading", icon: FlaskConical },
  { href: "/dashboard/system", label: "System Status", icon: Activity },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
];

export function DashboardShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { muted, toggleMuted, play } = useAudio();

  return (
    <div className="min-h-screen bg-void">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_at_10%_0%,rgba(139,123,255,0.10),transparent_45%),radial-gradient(ellipse_at_90%_100%,rgba(53,240,208,0.08),transparent_45%)]" />

      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 flex-col border-r border-white/10 bg-panel/70 backdrop-blur-xl lg:flex">
        <SidebarContent pathname={pathname} play={play} />
      </aside>

      {/* Mobile sidebar */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40 bg-black/60 lg:hidden"
              onClick={() => setMobileOpen(false)}
            />
            <motion.aside
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: "spring", stiffness: 300, damping: 32 }}
              className="fixed inset-y-0 left-0 z-50 flex w-72 flex-col bg-panel lg:hidden"
            >
              <SidebarContent pathname={pathname} play={play} onNavigate={() => setMobileOpen(false)} />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-30 flex items-center justify-between gap-3 border-b border-white/10 bg-void/70 px-4 py-3 backdrop-blur-xl sm:px-6">
          <div className="flex items-center gap-3">
            <button
              data-cursor-interactive
              className="grid h-9 w-9 place-items-center rounded-full border border-white/15 text-slate-200 lg:hidden"
              onClick={() => setMobileOpen(true)}
              aria-label="Open menu"
            >
              <Menu size={16} />
            </button>
            <Link href="/" data-cursor-interactive onClick={() => play.nav()} className="hidden items-center gap-2 text-xs text-slate-400 hover:text-cyan-300 lg:flex">
              <ArrowLeft size={14} /> Back to site
            </Link>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden items-center gap-2 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1 text-[11px] text-emerald-300 sm:flex">
              <span className="h-1.5 w-1.5 animate-pulse-glow rounded-full bg-emerald-400" /> Live
            </span>
            <button
              data-cursor-interactive
              onClick={toggleMuted}
              aria-label={muted ? "Unmute" : "Mute"}
              className="grid h-9 w-9 place-items-center rounded-full border border-white/15 text-slate-300 hover:border-cyan-300/60 hover:text-cyan-300"
            >
              {muted ? <VolumeX size={16} /> : <Volume2 size={16} />}
            </button>
          </div>
        </header>

        <main className="relative px-4 py-6 sm:px-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}

function SidebarContent({
  pathname,
  play,
  onNavigate,
}: {
  pathname: string;
  play: ReturnType<typeof useAudio>["play"];
  onNavigate?: () => void;
}) {
  return (
    <>
      <div className="flex items-center justify-between px-5 py-5">
        <Link href="/" data-cursor-interactive onClick={() => play.nav()} className="flex items-center gap-2.5">
          <span className="relative grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-cyan-300 to-violet-500">
            <span className="font-display text-xs font-bold text-slate-950">A</span>
          </span>
          <span className="font-display text-base font-bold text-white">AHOS</span>
        </Link>
        <button data-cursor-interactive className="grid h-8 w-8 place-items-center rounded-full text-slate-400 lg:hidden" onClick={onNavigate} aria-label="Close menu">
          <X size={16} />
        </button>
      </div>
      <nav className="flex-1 space-y-1 overflow-y-auto px-3 pb-6">
        {navItems.map((item) => {
          const active = item.href === "/dashboard" ? pathname === item.href : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              data-cursor-interactive
              onClick={() => {
                play.nav();
                onNavigate?.();
              }}
              onMouseEnter={() => play.hover()}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                active ? "bg-cyan-300/10 text-cyan-200 shadow-[inset_0_0_0_1px_rgba(53,240,208,0.25)]" : "text-slate-400 hover:bg-white/5 hover:text-slate-100"
              )}
            >
              <item.icon size={17} />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="mx-3 mb-5 rounded-xl border border-white/10 bg-white/[0.03] p-4">
        <p className="text-[11px] uppercase tracking-wider text-slate-500">Budget</p>
        <p className="mt-1 font-display text-sm font-semibold text-emerald-300">$0 / month</p>
        <p className="mt-1 text-[11px] text-slate-500">Open-source & free-tier only</p>
      </div>
    </>
  );
}
