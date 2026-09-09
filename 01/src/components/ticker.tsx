"use client";

import { fmtPct, fmtUsd, type LocaleHint } from "@/lib/format";
import { cx, TONE, DECISION_TONE, type Tone } from "@/lib/ui";
import type { DecisionKind } from "@/lib/engine";

export type TickerItem = {
  slug: string;
  symbol: string;
  priceUsd: number;
  change24h: number;
  decision: DecisionKind | null;
};

function Row({ items, locale }: { items: TickerItem[]; locale: LocaleHint }) {
  return (
    <div className="flex shrink-0 items-center">
      {items.map((it) => {
        const up = it.change24h >= 0;
        const tone: Tone | null = it.decision ? DECISION_TONE[it.decision] : null;
        return (
          <div key={it.slug} className="flex items-center gap-2.5 px-5 py-2">
            {tone && (
              <span className={cx("size-1.5 rounded-full", TONE[tone].dot, tone === "gold" && "a-pulse-soft")} />
            )}
            <span className="num text-xs font-bold tracking-wide text-frost/90">{it.symbol}</span>
            <span className="num text-[11px] text-mist">{fmtUsd(locale, it.priceUsd)}</span>
            <span
              className={cx(
                "num rounded-md px-1.5 py-0.5 text-[10px] font-semibold",
                up ? "bg-jade-400/10 text-jade-300" : "bg-flare/10 text-flare",
              )}
            >
              {fmtPct(locale, it.change24h)}
            </span>
          </div>
        );
      })}
    </div>
  );
}

export default function Ticker({ items, locale }: { items: TickerItem[]; locale: LocaleHint }) {
  if (!items.length) return null;
  return (
    <div className="marquee-wrap relative overflow-hidden border-y border-white/5 bg-abyss-950/60 backdrop-blur-sm">
      <div className="pointer-events-none absolute inset-y-0 start-0 z-10 w-24 bg-gradient-to-e from-abyss-950 to-transparent" />
      <div className="pointer-events-none absolute inset-y-0 end-0 z-10 w-24 bg-gradient-to-s from-abyss-950 to-transparent" />
      <div className="marquee-track" dir="ltr">
        <Row items={items} locale={locale} />
        <Row items={items} locale={locale} />
      </div>
    </div>
  );
}
