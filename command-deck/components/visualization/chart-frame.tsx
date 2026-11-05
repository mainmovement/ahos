"use client";

import type { ReactNode } from "react";
import { useLocale } from "@/components/providers/locale-provider";
import { useSettings } from "@/components/providers/settings-provider";
import { StatusBadge } from "@/components/status/status-badge";
import type { DataStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

/**
 * Chart container: title + status, an unavoidable SAMPLE watermark for sample
 * data, an accessible summary, and an optional tabular data alternative.
 */
export function ChartFrame({
  title,
  summary,
  status,
  children,
  table,
  heightClass = "h-64",
  className,
}: {
  title: string;
  summary: string;
  status: DataStatus;
  children: ReactNode;
  table?: ReactNode;
  heightClass?: string;
  className?: string;
}) {
  const { dict } = useLocale();
  const { prefs } = useSettings();
  const watermark = prefs.chartWatermark && (status === "SAMPLE" || status === "UNVERIFIED" || status === "STALE");

  return (
    <figure className={cn("panel relative overflow-hidden", className)}>
      <div className="flex items-start justify-between gap-2 panel-pad pb-0">
        <figcaption className="min-w-0">
          <span className="block truncate text-sm font-bold">{title}</span>
          <span className="mt-0.5 block text-[11px] leading-relaxed text-muted-foreground">{summary}</span>
        </figcaption>
        <StatusBadge status={status} size="sm" />
      </div>

      <div className={cn("relative panel-pad pt-3", heightClass)}>
        {watermark ? (
          <div aria-hidden className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center overflow-hidden">
            <div className="watermark-stripes absolute inset-0" />
            <span className="-rotate-12 select-none whitespace-nowrap text-4xl font-extrabold tracking-[0.35em] text-foreground/[0.05]" dir="ltr">
              {dict.common.sample} · {dict.common.sample}
            </span>
          </div>
        ) : null}
        <div dir="ltr" className="relative h-full">
          {children}
        </div>
      </div>

      {table ? (
        <details className="border-t border-border/60 px-4 py-2">
          <summary className="cursor-pointer select-none text-[11px] font-semibold text-muted-foreground transition-colors hover:text-foreground">
            {dict.common.viewDataTable}
          </summary>
          <div className="mt-2 max-h-56 overflow-auto rounded-lg border border-border/60" dir="ltr">
            {table}
          </div>
        </details>
      ) : null}
    </figure>
  );
}
