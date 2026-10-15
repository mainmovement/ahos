"use client";

import type { ComponentType, ReactNode, SVGProps } from "react";
import { FlaskConical } from "lucide-react";
import { useI18n } from "@/lib/i18n";
import { cn } from "@/lib/utils";

/** Page heading row: icon, title, subtitle, actions, and a demo-data notice. */
export function PageHeader({
  title,
  subtitle,
  icon: Icon,
  actions,
  className,
  demo = true,
}: {
  title: string;
  subtitle?: string;
  icon?: ComponentType<SVGProps<SVGSVGElement>>;
  actions?: ReactNode;
  className?: string;
  demo?: boolean;
}) {
  const { t } = useI18n();
  return (
    <div className={cn("flex flex-wrap items-end justify-between gap-3", className)}>
      <div className="flex min-w-0 items-center gap-3">
        {Icon && (
          <span aria-hidden className="relative flex size-10 shrink-0 items-center justify-center rounded-[var(--radius-lg)] border border-gold-400/25 bg-gradient-to-b from-gold-400/15 to-gold-400/[0.02] text-gold-300 shadow-[var(--shadow-glow-sm)]">
            <Icon className="size-5" />
          </span>
        )}
        <div className="min-w-0">
          <h1 className="truncate text-xl font-bold leading-tight text-fg-1">{title}</h1>
          {subtitle && <p className="mt-0.5 truncate text-xs text-fg-3">{subtitle}</p>}
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        {actions}
        {demo && (
          <span className="inline-flex h-7 items-center gap-1.5 rounded-full border border-dashed border-status-demo/40 bg-status-demo/[0.05] px-2.5 text-3xs text-status-demo" title={t.common.demoTitle}>
            <FlaskConical aria-hidden className="size-3" />
            {t.app.demoBuild}
          </span>
        )}
      </div>
    </div>
  );
}

/** Standard page padding/grid wrapper. */
export function PageBody({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("mx-auto flex w-full max-w-[1680px] flex-col gap-4 p-4 animate-fade-in", className)}>{children}</div>;
}
