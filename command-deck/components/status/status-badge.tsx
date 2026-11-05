"use client";

import type { ComponentType } from "react";
import {
  Ban,
  CircleCheck,
  CircleDashed,
  CircleMinus,
  CircleQuestionMark,
  CircleSlash,
  Clock,
  FlaskConical,
  ShieldX,
  Unplug,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { statusGlyph, statusTone, type StatusTone } from "@/lib/provenance/status";
import type { DataEnvelope, DataProvenance, DataStatus } from "@/lib/types";
import { useLocale } from "@/components/providers/locale-provider";
import { formatDateTime } from "@/lib/formatters/dates";

const GLYPHS: Record<string, ComponentType<{ className?: string }>> = {
  check: CircleCheck,
  flask: FlaskConical,
  slash: CircleSlash,
  "plug-off": Unplug,
  clock: Clock,
  help: CircleQuestionMark,
  "shield-x": ShieldX,
  ban: Ban,
  minus: CircleMinus,
  question: CircleDashed,
};

const TONE_CLASS: Record<StatusTone, string> = {
  measured: "border-accent/40 bg-accent/10 text-accent",
  sample: "border-violet/40 bg-violet/10 text-violet",
  absent: "border-border bg-muted/40 text-muted-foreground",
  disconnected: "border-dashed border-border-strong bg-muted/30 text-muted-foreground",
  stale: "border-warning/40 bg-warning/10 text-warning",
  warning: "border-warning/40 bg-warning/10 text-warning",
  danger: "border-danger/40 bg-danger/10 text-danger",
  excluded: "border-danger/50 bg-danger/5 text-danger",
  unknown: "border-border-strong bg-muted/50 text-muted-foreground",
};

/** Visible, screen-reader-friendly status label — never color-only. */
export function StatusBadge({
  status,
  className,
  size = "md",
}: {
  status: DataStatus;
  className?: string;
  size?: "sm" | "md";
}) {
  const { dict } = useLocale();
  const Glyph = GLYPHS[statusGlyph(status)] ?? CircleDashed;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border font-semibold",
        size === "sm" ? "px-1.5 py-px text-[10px]" : "px-2 py-0.5 text-[11px]",
        TONE_CLASS[statusTone(status)],
        className,
      )}
    >
      <Glyph className={size === "sm" ? "size-3" : "size-3.5"} aria-hidden />
      <span className="tnum whitespace-nowrap">{dict.status[status]}</span>
    </span>
  );
}

/** Icon-only status marker for dense spots. */
export function StatusDot({ status, className }: { status: DataStatus; className?: string }) {
  const { dict } = useLocale();
  const Glyph = GLYPHS[statusGlyph(status)] ?? CircleDashed;
  return (
    <span className={cn("inline-flex", TONE_CLASS[statusTone(status)], "rounded-full border p-0.5", className)} title={dict.status[status]}>
      <Glyph className="size-3" aria-hidden />
      <span className="sr-only">{dict.status[status]}</span>
    </span>
  );
}

/**
 * Full provenance chip: visible status label; source / observation time /
 * reason in an accessible tooltip.
 */
export function ProvenanceChip({
  envelope,
  withSource = false,
  className,
}: {
  envelope: DataEnvelope<unknown>;
  withSource?: boolean;
  className?: string;
}) {
  const { dict, locale } = useLocale();
  const p: DataProvenance = envelope.provenance;
  const tip = [
    `${dict.common.source}: ${p.source}`,
    p.observedAt ? `${dict.common.observedAt}: ${formatDateTime(p.observedAt, locale)} (UTC)` : null,
    p.reason ? `${dict.common.reason}: ${dict.reason[p.reason]}` : null,
    p.confidence !== null ? `${dict.common.confidence}: ${Math.round(p.confidence * 100)}%` : null,
    p.note ? p.note[locale] : null,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <span className={cn("group/chip inline-flex min-w-0 items-center gap-1.5", className)}>
      <span className="relative inline-flex" tabIndex={0}>
        <StatusBadge status={p.status} />
        <span
          role="tooltip"
          className="pointer-events-none absolute bottom-full start-0 z-40 mb-1.5 hidden w-max max-w-[260px] rounded-lg border border-border-strong bg-navy-900 px-2.5 py-1.5 text-[11px] leading-relaxed text-foreground shadow-panel group-focus-within/chip:block group-hover/chip:block light:bg-white"
        >
          <span className="block break-all">{tip}</span>
        </span>
      </span>
      {withSource ? (
        <span className="truncate font-mono text-[10px] text-subtle" dir="ltr">
          {p.source}
        </span>
      ) : null}
    </span>
  );
}

/** Fixed-size value slot: renders the value or an honest absence. */
export function EnvelopeValue({
  envelope,
  render,
  absenceClassName,
}: {
  envelope: DataEnvelope<unknown>;
  render: (value: unknown) => React.ReactNode;
  absenceClassName?: string;
}) {
  const { dict } = useLocale();
  if (envelope.value === null) {
    return (
      <span className={cn("inline-flex items-center gap-1.5 text-muted-foreground", absenceClassName)}>
        <span className="inline-block h-px w-4 bg-border-strong" aria-hidden />
        <span className="sr-only">{dict.status[envelope.provenance.status]}</span>
      </span>
    );
  }
  return <>{render(envelope.value)}</>;
}
