"use client";

import { useState, type ReactNode } from "react";
import { ArrowDownRight, ArrowUpRight, Check, Copy, Minus } from "lucide-react";
import { useFormat } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { useNow } from "@/lib/time/now";
import { cn } from "@/lib/utils";
import { Tip } from "./tooltip";

const ARABIC_SCRIPT = /[\u0600-\u06FF]/;

/**
 * Numeric text: direction-isolated, tabular figures (prevents bidi reordering
 * of +/−/%). Pure numbers render LTR; values that contain Persian words
 * (e.g. "18.4 میلیون") render RTL so they read naturally.
 */
export function Num({ children, className, title }: { children: ReactNode; className?: string; title?: string }) {
  const dir = typeof children === "string" && ARABIC_SCRIPT.test(children) ? "rtl" : "ltr";
  return (
    <span dir={dir} title={title} className={cn("num inline-block", className)}>
      {children}
    </span>
  );
}

/** Delta with arrow SHAPE + sign — never colour-only. `value` is a percent. */
export function Delta({ value, decimals = 2, polarity = "up-good", className, size = "sm" }: { value: number | null | undefined; decimals?: number; polarity?: "up-good" | "down-good" | "neutral"; className?: string; size?: "xs" | "sm" | "md" }) {
  const f = useFormat();
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return <Num className={cn("text-fg-4", className)}>—</Num>;
  }
  const up = value > 0;
  const flat = value === 0;
  const good = polarity === "neutral" ? null : polarity === "up-good" ? up : !up;
  const tone = flat ? "text-fg-3" : polarity === "neutral" ? (up ? "text-up" : "text-down") : good ? "text-up" : "text-down";
  const Icon = flat ? Minus : up ? ArrowUpRight : ArrowDownRight;
  return (
    <span dir="ltr" className={cn("num inline-flex items-center gap-0.5 font-medium", tone, size === "xs" ? "text-2xs" : size === "md" ? "text-sm" : "text-xs", className)}>
      <Icon aria-hidden className={size === "md" ? "size-3.5" : "size-3"} strokeWidth={2.5} />
      {f.pct(value, decimals)}
    </span>
  );
}

export function TimeAgo({ iso, className, withTitle = true }: { iso: string | null | undefined; className?: string; withTitle?: boolean }) {
  const f = useFormat();
  const now = useNow();
  const text = f.ago(iso, now);
  return (
    <time dateTime={iso ?? undefined} title={withTitle && iso ? f.dateTime(iso) : undefined} className={cn("num", className)} suppressHydrationWarning>
      {text}
    </time>
  );
}

export function Kbd({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <kbd dir="ltr" className={cn("inline-flex h-[18px] min-w-[18px] items-center justify-center rounded-[var(--radius-xs)] border border-white/10 bg-white/[0.04] px-1 font-sans text-3xs font-medium text-fg-3", className)}>
      {children}
    </kbd>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div aria-hidden className={cn("shimmer rounded-[var(--radius-sm)]", className)} />;
}

export function Hairline({ className, vertical }: { className?: string; vertical?: boolean }) {
  return <div aria-hidden className={cn(vertical ? "hairline-y" : "hairline-x", className)} />;
}

/** Horizontal meter with explicit numeric label (not colour-only). */
export function Meter({ value, max = 1, tone = "gold", label, className, height = 4 }: { value: number | null; max?: number; tone?: "gold" | "data" | "up" | "down" | "warn"; label?: string; className?: string; height?: number }) {
  const pct = value === null ? 0 : Math.max(0, Math.min(100, (value / max) * 100));
  const bg = {
    gold: "bg-[image:var(--gradient-gold)]",
    data: "bg-data-400",
    up: "bg-up",
    down: "bg-down",
    warn: "bg-warn",
  }[tone];
  return (
    <div
      role="meter"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={max}
      aria-valuenow={value ?? undefined}
      className={cn("relative w-full overflow-hidden rounded-full bg-white/[0.06]", className)}
      style={{ height }}
    >
      {value === null ? (
        <div className="absolute inset-0 bg-[repeating-linear-gradient(135deg,rgb(167_139_250/0.25)_0_4px,transparent_4px_8px)]" />
      ) : (
        <div className={cn("absolute inset-y-0 start-0 rounded-full transition-[width] duration-[var(--dur-slow)]", bg)} style={{ width: `${pct}%` }} />
      )}
    </div>
  );
}

export function CopyButton({ value, className }: { value: string; className?: string }) {
  const { t } = useI18n();
  const [copied, setCopied] = useState(false);
  return (
    <Tip content={copied ? t.common.copied : t.common.copy}>
      <button
        type="button"
        aria-label={t.common.copy}
        className={cn("inline-flex size-6 items-center justify-center rounded-[var(--radius-xs)] text-fg-3 transition-colors hover:bg-[var(--surface-hover)] hover:text-gold-200", className)}
        onClick={() => {
          void navigator.clipboard?.writeText(value).then(() => {
            setCopied(true);
            window.setTimeout(() => setCopied(false), 1400);
          });
        }}
      >
        {copied ? <Check className="size-3.5 text-up" /> : <Copy className="size-3.5" />}
      </button>
    </Tip>
  );
}

export function EmptyState({ icon, title, hint, className }: { icon?: ReactNode; title: string; hint?: string; className?: string }) {
  return (
    <div className={cn("flex flex-col items-center justify-center gap-2 py-8 text-center", className)}>
      {icon && <div className="text-fg-4 [&_svg]:size-6">{icon}</div>}
      <p className="text-sm text-fg-2">{title}</p>
      {hint && <p className="max-w-xs text-xs text-fg-4">{hint}</p>}
    </div>
  );
}

/** Unknown value placeholder: shows "—" with an accessible explanation. */
export function UnknownValue({ className }: { className?: string }) {
  const { t } = useI18n();
  return (
    <span className={cn("text-fg-4", className)} title={t.common.unknownValue} aria-label={t.common.unknownValue}>
      —
    </span>
  );
}
