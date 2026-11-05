"use client";

import { ChartCandlestick } from "lucide-react";
import { useLocale } from "@/components/providers/locale-provider";
import { HudCard } from "./hud-card";
import { StatusBadge } from "@/components/status/status-badge";
import { CandleChart } from "@/components/visualization/candle-chart";
import { candlesFor } from "@/lib/data/series";

/** MARKET INTELLIGENCE — last 60 sample candles for the gold desk. */
export function MarketMiniChart({ className }: { className?: string }) {
  const { dict } = useLocale();
  const envelope = candlesFor("gold");

  if (!envelope.provenance || envelope.value === null) {
    return (
      <HudCard icon={ChartCandlestick} title="Market Intelligence" titleFa={dict.command.marketIntel} className={className}>
        <p className="py-6 text-center text-[10px] text-muted-foreground">{dict.status.NOT_MEASURED}</p>
      </HudCard>
    );
  }

  const { symbol, bars } = envelope.value;
  const recent = bars.slice(-60);

  return (
    <HudCard
      icon={ChartCandlestick}
      title="Market Intelligence"
      titleFa={dict.command.marketIntel}
      className={className}
      badge={<StatusBadge status={envelope.provenance.status} size="sm" />}
    >
      <div className="mb-1.5 flex items-baseline justify-between gap-2">
        <span className="font-mono text-[10px] font-bold tracking-wider text-foreground/90" dir="ltr">
          {symbol}
        </span>
      </div>
      <CandleChart bars={recent} height={116} />
      <p className="mt-1 text-[9px] leading-relaxed text-subtle">{dict.command.marketIntelNote}</p>
    </HudCard>
  );
}
