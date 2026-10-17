// FILE: 13_missions_batch3/src/components/shell/TehranClock.tsx
"use client";
import { useEffect, useState } from "react";

/**
 * Tehran wall clock (Asia/Tehran). No props. Updates once a minute; the tick
 * is presentation only and is disabled under prefers-reduced-motion by CSS.
 */
export function TehranClock() {
  const [now, setNow] = useState<Date | null>(null);

  useEffect(() => {
    setNow(new Date());
    const id = window.setInterval(() => setNow(new Date()), 60_000);
    return () => window.clearInterval(id);
  }, []);

  const fmt = (d: Date) =>
    new Intl.DateTimeFormat("fa-IR", {
      timeZone: "Asia/Tehran",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).format(d);

  const fmtDate = (d: Date) =>
    new Intl.DateTimeFormat("fa-IR", {
      timeZone: "Asia/Tehran",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).format(d);

  return (
    <span className="ah-chip ah-chip-gold" data-testid="tehran-clock" title="ساعت تهران">
      تهران {now ? fmt(now) : "—"}
      <span className="ah-muted" style={{ marginInlineStart: 8 }}>
        {now ? fmtDate(now) : "—"}
      </span>
    </span>
  );
}
