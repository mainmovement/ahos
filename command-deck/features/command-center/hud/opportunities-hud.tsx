"use client";

import { Trophy } from "lucide-react";
import { useLocale } from "@/components/providers/locale-provider";
import { HudCard } from "./hud-card";
import { StatusBadge } from "@/components/status/status-badge";
import { SignalBadge } from "@/components/status/signal-badge";
import { DESKS } from "@/lib/data/desks";
import { navHref } from "@/lib/nav";
import { formatScore } from "@/lib/formatters/numbers";
import Link from "next/link";

/** Top sample-scored desks — ranked, linked, clearly SAMPLE. */
export function OpportunitiesHud({ className }: { className?: string }) {
  const { dict, locale } = useLocale();

  const ranked = DESKS.filter((d) => d.score.value !== null)
    .sort((a, b) => (b.score.value?.value ?? 0) - (a.score.value?.value ?? 0))
    .slice(0, 5);

  return (
    <HudCard
      icon={Trophy}
      title="Top Opportunities"
      titleFa={dict.desks.title}
      className={className}
      badge={<StatusBadge status="SAMPLE" size="sm" />}
    >
      <ol className="flex flex-col gap-1">
        {ranked.map((desk, i) => {
          const score = desk.score.value?.value ?? 0;
          const heat =
            score >= 0.6 ? "text-success" : score >= 0.55 ? "text-accent" : "text-muted-foreground";
          return (
            <li key={desk.id}>
              <Link
                href={navHref(locale, `/desks/${desk.id}`)}
                className="group flex items-center gap-2.5 rounded-xl px-1.5 py-1.5 transition-colors hover:bg-primary/[0.07]"
              >
                <span className="tnum font-latin w-5 shrink-0 text-[11px] font-extrabold text-primary/70" dir="ltr">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span className="min-w-0 flex-1 truncate text-[11px] font-bold leading-tight">{desk.name[locale]}</span>
                <SignalBadge state={desk.signal.value ?? "UNKNOWN"} size="sm" />
                <span className={`tnum font-latin w-11 shrink-0 text-end text-sm font-extrabold ${heat}`} dir="ltr">
                  {formatScore(desk.score.value?.value ?? 0, locale)}
                </span>
                <span className="sr-only">{dict.desks.score} — {dict.common.sample}</span>
              </Link>
            </li>
          );
        })}
      </ol>
      <p className="mt-1.5 border-t border-border/50 pt-2 text-[9px] leading-relaxed text-subtle">
        {dict.desks.score} · {dict.common.sample}
      </p>
    </HudCard>
  );
}
