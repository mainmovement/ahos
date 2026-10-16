"use client";

import { useSyncExternalStore } from "react";
import { formatClock, formatRelTime } from "../lib/reltime";

/**
 * Relative time that only renders after mount (no hydration mismatch).
 * A missing timestamp renders "—" and callers pair it with UNKNOWN status —
 * this component never invents a time.
 */
function subscribeMinute(callback: () => void): () => void {
  const t = setInterval(callback, 30_000);
  return () => clearInterval(t);
}
/** Stable within a 30 s window so the store snapshot does not churn. */
function nowSnapshot(): number {
  return Math.floor(Date.now() / 30_000) * 30_000;
}
function nowServerSnapshot(): null {
  return null;
}

export function RelTime({
  iso,
  clock = false,
  className = "",
}: {
  iso: string | null;
  clock?: boolean;
  className?: string;
}) {
  const now = useSyncExternalStore(subscribeMinute, nowSnapshot, nowServerSnapshot);

  if (!iso) {
    return <span className={`wh-num text-mute ${className}`}>—</span>;
  }

  return (
    <span
      className={`wh-num ${className}`}
      title={iso}
      suppressHydrationWarning
    >
      {now === null ? "…" : clock ? formatClock(iso) : formatRelTime(iso, now)}
    </span>
  );
}
