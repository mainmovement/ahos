"use client";

import type { ComponentType, ReactNode, SVGProps } from "react";
import { Clock, Database } from "lucide-react";
import type { DataMeta } from "@/lib/api/types";
import { useI18n } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import { MetaStatusChip, StatusChip } from "@/components/ui/status";
import { TimeAgo } from "@/components/ui/primitives";
import { Tip } from "@/components/ui/tooltip";

export interface DataCardProps {
  title: string;
  subtitle?: string;
  icon?: ComponentType<SVGProps<SVGSVGElement>>;
  /** Envelope metadata → footer (source · retrieved-at · status chip). */
  meta?: DataMeta;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
  /** Extra footer content rendered before the provenance block. */
  footerExtra?: ReactNode;
  /** Hide the footer entirely (only for nested cards that inherit provenance). */
  bare?: boolean;
  as?: "section" | "article" | "div";
  id?: string;
  highlight?: boolean;
}

/**
 * The AHOS card: frosted glass, gold gradient hairline, title row with a DEMO
 * chip for mock payloads, and a provenance footer on every card.
 */
export function DataCard({ title, subtitle, icon: Icon, meta, actions, children, className, bodyClassName, footerExtra, bare, as = "section", id, highlight }: DataCardProps) {
  const Comp = as;
  const headingId = id ? `${id}-title` : undefined;
  return (
    <Comp id={id} aria-labelledby={headingId} className={cn("glass gold-border card-sheen flex min-w-0 flex-col", highlight && "shadow-[var(--shadow-glow-md)]", className)}>
      <header className="flex flex-wrap items-start gap-x-2.5 gap-y-1.5 px-3.5 pb-2 pt-3">
        {Icon && (
          <span aria-hidden className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-[var(--radius-sm)] border border-gold-400/20 bg-gold-400/[0.07] text-gold-300 shadow-[inset_0_1px_0_rgb(255_255_255/0.06)]">
            <Icon className="size-3.5" />
          </span>
        )}
        <div className="min-w-[8.5rem] flex-1">
          <h2 id={headingId} className="truncate text-sm font-semibold leading-tight text-fg-1">
            {title}
          </h2>
          {subtitle && <p className="mt-0.5 truncate text-2xs text-fg-4">{subtitle}</p>}
        </div>
        <div className="ms-auto flex shrink-0 flex-wrap items-center justify-end gap-1.5">
          {actions}
          {meta?.isMock && <StatusChip status="DEMO" />}
        </div>
      </header>
      <div className={cn("min-h-0 flex-1 px-3.5 pb-3", bodyClassName)}>{children}</div>
      {!bare && (meta || footerExtra) && <CardFooter meta={meta} extra={footerExtra} />}
    </Comp>
  );
}

export function CardFooter({ meta, extra, compact }: { meta?: DataMeta; extra?: ReactNode; compact?: boolean }) {
  const { t, l } = useI18n();
  return (
    <footer className={cn("flex min-w-0 items-center gap-2 border-t border-[var(--line-subtle)] text-3xs text-fg-4", compact ? "px-2.5 py-1.5" : "px-3.5 py-2")}>
      {extra}
      {meta && (
        <>
          <Tip content={`${t.common.source}: ${l(meta.sourceLabel)} (${meta.source})`}>
            <span tabIndex={0} className="flex min-w-0 items-center gap-1 truncate">
              <Database aria-hidden className="size-3 shrink-0 text-fg-5" />
              <span className="sr-only">{t.common.source}:</span>
              <span className="truncate">{l(meta.sourceLabel)}</span>
            </span>
          </Tip>
          <span className="flex shrink-0 items-center gap-1">
            <Clock aria-hidden className="size-3 text-fg-5" />
            <span className="sr-only">{t.common.retrievedAt}:</span>
            <TimeAgo iso={meta.retrievedAt} />
          </span>
          <span className="ms-auto shrink-0">
            <MetaStatusChip meta={meta} />
          </span>
        </>
      )}
    </footer>
  );
}

/** Section heading used inside pages (between card rows). */
export function SectionTitle({ children, hint, className, actions }: { children: ReactNode; hint?: string; className?: string; actions?: ReactNode }) {
  return (
    <div className={cn("flex items-end justify-between gap-3", className)}>
      <div className="flex items-center gap-2">
        <span aria-hidden className="h-3 w-[3px] rounded-full bg-[image:var(--gradient-gold)] shadow-[var(--shadow-glow-sm)]" />
        <h2 className="text-sm font-semibold text-fg-1">{children}</h2>
        {hint && <span className="text-2xs text-fg-4">{hint}</span>}
      </div>
      {actions}
    </div>
  );
}
