import type { ReactNode } from "react";
import { AlertTriangle, Inbox, Loader2 } from "lucide-react";

export function PageHeader({ eyebrow, title, description, right }: { eyebrow?: string; title: string; description?: string; right?: ReactNode }) {
  return (
    <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div>
        {eyebrow && <p className="mb-2 text-xs font-medium uppercase tracking-[0.25em] text-cyan-300">{eyebrow}</p>}
        <h1 className="font-display text-2xl font-bold text-white sm:text-3xl">{title}</h1>
        {description && <p className="mt-2 max-w-2xl text-sm text-slate-400">{description}</p>}
      </div>
      {right}
    </div>
  );
}

export function EmptyState({ title = "Nothing here yet", description = "No data matches the current view.", icon }: { title?: string; description?: string; icon?: ReactNode }) {
  return (
    <div className="glass noise-border flex flex-col items-center justify-center gap-3 rounded-2xl px-6 py-16 text-center">
      <div className="grid h-12 w-12 place-items-center rounded-full border border-white/10 bg-white/5 text-slate-400">
        {icon ?? <Inbox size={20} />}
      </div>
      <h3 className="font-display text-base font-semibold text-slate-100">{title}</h3>
      <p className="max-w-sm text-sm text-slate-400">{description}</p>
    </div>
  );
}

export function ErrorState({ title = "Something went wrong", description = "AHOS could not load this data. Please retry shortly." }: { title?: string; description?: string }) {
  return (
    <div className="glass noise-border flex flex-col items-center justify-center gap-3 rounded-2xl border-rose-500/20 px-6 py-16 text-center">
      <div className="grid h-12 w-12 place-items-center rounded-full border border-rose-400/30 bg-rose-400/10 text-rose-300">
        <AlertTriangle size={20} />
      </div>
      <h3 className="font-display text-base font-semibold text-rose-200">{title}</h3>
      <p className="max-w-sm text-sm text-slate-400">{description}</p>
    </div>
  );
}

export function LoadingState({ label = "Loading intelligence..." }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-2xl px-6 py-16 text-center text-slate-400">
      <Loader2 className="animate-spin text-cyan-300" size={22} />
      <p className="text-sm">{label}</p>
    </div>
  );
}

export function KpiCard({ label, value, icon, sub, tone = "cyan" }: { label: string; value: ReactNode; icon?: ReactNode; sub?: ReactNode; tone?: "cyan" | "violet" | "gold" | "rose" | "emerald" }) {
  const toneClasses: Record<string, string> = {
    cyan: "text-cyan-300 border-cyan-400/20 bg-cyan-400/5",
    violet: "text-violet-300 border-violet-400/20 bg-violet-400/5",
    gold: "text-amber-300 border-amber-400/20 bg-amber-400/5",
    rose: "text-rose-300 border-rose-400/20 bg-rose-400/5",
    emerald: "text-emerald-300 border-emerald-400/20 bg-emerald-400/5",
  };
  return (
    <div className="glass noise-border rounded-2xl p-5">
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-wider text-slate-400">{label}</span>
        {icon && <div className={`grid h-8 w-8 place-items-center rounded-lg border ${toneClasses[tone]}`}>{icon}</div>}
      </div>
      <div className="mt-3 font-display text-2xl font-bold text-white">{value}</div>
      {sub && <div className="mt-1 text-xs text-slate-500">{sub}</div>}
    </div>
  );
}
