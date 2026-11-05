"use client";

import Link from "next/link";
import type { ComponentType, ReactNode } from "react";
import { useLocale } from "@/components/providers/locale-provider";
import { StatusBadge } from "@/components/status/status-badge";
import type { DataStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

/**
 * Floating HUD card over the command stage. The English uppercase header is
 * deliberate avionics-style chrome (tooltip carries the localized title).
 */
export function HudCard({
  icon: Icon,
  title,
  titleFa,
  badge,
  actionHref,
  children,
  className,
}: {
  icon: ComponentType<{ className?: string }>;
  title: string;
  titleFa: string;
  badge?: ReactNode;
  actionHref?: string;
  children: ReactNode;
  className?: string;
}) {
  const { dict } = useLocale();
  return (
    <section
      aria-label={titleFa}
      title={titleFa}
      className={cn(
        "hud-card hud-cut overflow-hidden rounded-2xl border border-border/80 shadow-panel",
        className,
      )}
    >
      <header className="flex items-center gap-2 border-b border-border/60 px-3.5 py-2.5">
        <Icon className="size-3.5 shrink-0 text-primary" aria-hidden />
        <h3 className="min-w-0 flex-1 truncate font-latin text-[9px] font-extrabold uppercase tracking-[0.06em] text-foreground/90" dir="ltr">
          {title}
        </h3>
        {badge}
        {actionHref ? (
          <Link
            href={actionHref}
            className="shrink-0 rounded-lg px-1.5 py-0.5 text-[10px] font-bold text-primary/90 transition-colors hover:bg-primary/10"
          >
            {dict.common.viewAll} ›
          </Link>
        ) : null}
      </header>
      <div className="relative px-3.5 py-3">{children}</div>
    </section>
  );
}

export function HudStatusChip({ status }: { status: DataStatus }) {
  return <StatusBadge status={status} size="sm" />;
}

