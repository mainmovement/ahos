import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

type Tone = "cyan" | "violet" | "magenta" | "gold" | "danger" | "good" | "neutral";

const toneClasses: Record<Tone, string> = {
  cyan: "bg-cyan-400/10 text-cyan-300 border-cyan-400/30",
  violet: "bg-violet-400/10 text-violet-300 border-violet-400/30",
  magenta: "bg-pink-400/10 text-pink-300 border-pink-400/30",
  gold: "bg-amber-400/10 text-amber-300 border-amber-400/30",
  danger: "bg-rose-500/10 text-rose-300 border-rose-500/30",
  good: "bg-emerald-400/10 text-emerald-300 border-emerald-400/30",
  neutral: "bg-white/5 text-slate-300 border-white/15",
};

export function Badge({ children, tone = "neutral", className, icon }: { children: ReactNode; tone?: Tone; className?: string; icon?: ReactNode }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium uppercase tracking-wider",
        toneClasses[tone],
        className
      )}
    >
      {icon}
      {children}
    </span>
  );
}

export function decisionTone(decision: string): Tone {
  switch (decision) {
    case "strong_buy":
      return "good";
    case "watch":
      return "cyan";
    case "reject":
      return "danger";
    case "skip":
      return "neutral";
    default:
      return "gold";
  }
}

export function riskTone(level: string): Tone {
  switch (level) {
    case "low":
      return "good";
    case "medium":
      return "gold";
    case "high":
      return "danger";
    case "critical":
      return "danger";
    default:
      return "neutral";
  }
}
