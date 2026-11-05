"use client";

import { cn } from "@/lib/utils";
import type { DataProvenance } from "@/lib/types";
import { useLocale } from "@/components/providers/locale-provider";
import { StatusBadge } from "./status-badge";
import { formatDateTime } from "@/lib/formatters/dates";
import { Fragment } from "react";

/**
 * Evidence panel — the full provenance record of one data artifact, laid out
 * as a definition list. Used on desk detail, drawers, and health pages.
 */
export function ProvenancePanel({
  provenance,
  title,
  className,
}: {
  provenance: DataProvenance;
  title?: string;
  className?: string;
}) {
  const { dict, locale } = useLocale();
  const rows: Array<{ label: string; value: React.ReactNode }> = [
    { label: dict.common.provenance, value: <StatusBadge status={provenance.status} /> },
    {
      label: dict.common.source,
      value: (
        <span className="break-all font-mono text-[11px] text-foreground/90" dir="ltr">
          {provenance.source}
        </span>
      ),
    },
    {
      label: dict.common.observedAt,
      value: provenance.observedAt ? (
        <span className="tnum">{formatDateTime(provenance.observedAt, locale)} · UTC</span>
      ) : (
        <span className="text-muted-foreground">{dict.common.valueMissing}</span>
      ),
    },
    {
      label: dict.common.reason,
      value: provenance.reason ? (
        <span>{dict.reason[provenance.reason]}</span>
      ) : (
        <span className="text-muted-foreground">{dict.common.valueMissing}</span>
      ),
    },
    {
      label: dict.common.confidence,
      value:
        provenance.confidence !== null ? (
          <span className="tnum">{Math.round(provenance.confidence * 100)}%</span>
        ) : (
          <span className="text-muted-foreground">{dict.common.valueMissing}</span>
        ),
    },
  ];
  if (provenance.note) {
    rows.push({ label: dict.common.evidence, value: <span>{provenance.note[locale]}</span> });
  }

  return (
    <div className={cn("rounded-xl border border-border/70 bg-muted/20", className)}>
      {title ? <div className="border-b border-border/60 px-3 py-2 text-xs font-bold">{title}</div> : null}
      <dl className="grid gap-x-4 gap-y-2 px-3 py-3 text-[11px] sm:grid-cols-[auto_1fr] sm:gap-y-2.5">
        {rows.map((row, i) => (
          <Fragment key={`${row.label}-${i}`}>
            <dt className="text-muted-foreground sm:min-w-24">{row.label}</dt>
            <dd className="min-w-0 leading-relaxed">{row.value}</dd>
          </Fragment>
        ))}
      </dl>
    </div>
  );
}
