"use client";

import { useEffect, useState } from "react";
import { formatClock, formatRelTime } from "../lib/reltime";

/**
 * Relative time that only renders after mount (no hydration mismatch).
 * A missing timestamp renders "—" and callers pair it with UNKNOWN status —
 * this component never invents a time.
 */
export function RelTime({
  iso,
  clock = false,
  className = "",
}: {
  iso: string | null;
  clock?: boolean;
  className?: string;
}) {
  const [now, setNow] = useState<number | null>(null);

  useEffect(() => {
    setNow(Date.now());
    const t = setInterval(() => setNow(Date.now()), 30_000);
    return () => clearInterval(t);
  }, []);

  if (!iso) {
    return <span className={`ah-num text-mute ${className}`}>—</span>;
  }

  return (
    <span
      className={`ah-num ${className}`}
      title={iso}
      suppressHydrationWarning
    >
      {now === null ? "…" : clock ? formatClock(iso) : formatRelTime(iso, now)}
    </span>
  );
}
