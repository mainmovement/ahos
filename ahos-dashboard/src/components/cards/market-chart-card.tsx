"use client";

import { useMemo, useState } from "react";
import { ChartNoAxesCombined } from "lucide-react";
import type { Candle, DataMeta, Instrument } from "@/lib/api/types";
import { useFormat } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { Delta, Num } from "@/components/ui/primitives";
import { Segmented } from "@/components/ui/segmented";
import { StatusChip } from "@/components/ui/status";
import { CandlesChart } from "@/components/charts/charts";
import { DataCard } from "./data-card";

/** Wide chart card with instrument tabs and candle/line toggle. */
export function MarketChartCard({ instruments, candles, meta, ids, className, height = 300 }: { instruments: Instrument[]; candles: Record<string, Candle[]>; meta: DataMeta; ids: string[]; className?: string; height?: number }) {
  const { tx, l } = useI18n();
  const f = useFormat();
  const available = useMemo(() => ids.filter((id) => candles[id]?.length), [ids, candles]);
  const [active, setActive] = useState(available[0] ?? "");
  const [mode, setMode] = useState<"candles" | "line">("candles");
  const inst = instruments.find((i) => i.id === active);
  return (
    <DataCard
      title={tx("بازار در یک نگاه", "Markets at a glance")}
      subtitle={tx("کندل روزانه · میانگین متحرک ۲۰ و ۵۰ · حجم", "Daily candles · MA20/MA50 · volume")}
      icon={ChartNoAxesCombined}
      meta={meta}
      className={className}
      actions={
        <Segmented
          label={tx("نوع نمودار", "Chart type")}
          size="xs"
          value={mode}
          onChange={setMode}
          options={[
            { value: "candles", label: tx("کندل", "Candles") },
            { value: "line", label: tx("خطی", "Line") },
          ]}
        />
      }
    >
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <Segmented
          label={tx("دارایی", "Instrument")}
          value={active}
          onChange={setActive}
          options={available.map((id) => ({ value: id, label: <bdi>{instruments.find((i) => i.id === id)?.symbol ?? id}</bdi> }))}
        />
        {inst && (
          <div className="flex items-baseline gap-2">
            <span className="text-2xs text-fg-4">{l(inst.name)}</span>
            <Num className="text-lg font-semibold text-fg-1">{f.num(inst.price, inst.decimals, inst.decimals)}</Num>
            <Delta value={inst.change24h} size="sm" />
            <StatusChip status={inst.status} />
          </div>
        )}
      </div>
      {active && <CandlesChart candles={candles[active] ?? []} height={height} label={`${inst?.symbol ?? active} — ${tx("نمودار قیمت", "price chart")}`} mode={mode} decimals={inst?.decimals ?? 2} />}
    </DataCard>
  );
}
