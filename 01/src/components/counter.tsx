"use client";

import { useEffect, useRef, useState } from "react";
import { fmtCompact, fmtInt, fmtPct, fmtUsd, type LocaleHint } from "@/lib/format";

type Format = "int" | "compact" | "usd" | "pct" | "pctPlain";

function format(locale: LocaleHint, fmt: Format, v: number): string {
  switch (fmt) {
    case "int": return fmtInt(locale, Math.round(v));
    case "compact": return fmtCompact(locale, v);
    case "usd": return fmtUsd(locale, v);
    case "pct": return fmtPct(locale, v, true);
    case "pctPlain": return fmtPct(locale, v, false);
  }
}

export default function Counter({
  value, locale, format: fmt = "int", duration = 1300, className,
}: {
  value: number; locale: LocaleHint; format?: Format; duration?: number; className?: string;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const [v, setV] = useState(0);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let raf = 0;
    const io = new IntersectionObserver(
      (entries) => {
        if (!entries[0].isIntersecting) return;
        io.disconnect();
        const t0 = performance.now();
        const tick = (t: number) => {
          const p = Math.min(1, (t - t0) / duration);
          setV(value * (1 - Math.pow(1 - p, 3)));
          if (p < 1) raf = requestAnimationFrame(tick);
        };
        raf = requestAnimationFrame(tick);
      },
      { threshold: 0.5 },
    );
    io.observe(el);
    return () => { io.disconnect(); cancelAnimationFrame(raf); };
  }, [value, duration]);

  return (
    <span ref={ref} className={className}>
      {format(locale, fmt, v)}
    </span>
  );
}
