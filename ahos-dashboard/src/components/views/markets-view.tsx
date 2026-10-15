"use client";

import { useEffect, useMemo, useState } from "react";
import { ChartCandlestick, Search, Timer } from "lucide-react";
import type { AssetClass, Candle, DataEnvelope, DataStatus, MarketBoard } from "@/lib/api/types";
import { getCandles, type Timeframe } from "@/lib/api/markets";
import { useFormat } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { useNow } from "@/lib/time/now";
import { cn } from "@/lib/utils";
import { PageBody, PageHeader } from "@/components/layout/page-header";
import { DataCard } from "@/components/cards/data-card";
import { Notice } from "@/components/cards/blocks";
import { Delta, Num, TimeAgo } from "@/components/ui/primitives";
import { Segmented } from "@/components/ui/segmented";
import { StatusChip } from "@/components/ui/status";
import { Chip } from "@/components/ui/chip";
import { Sparkline } from "@/components/charts/sparkline";
import { CandlesChart } from "@/components/charts/charts";

type ClassFilter = "all" | AssetClass;

function ageTone(iso: string | null, now: number | null): "up" | "gold" | "warn" | "violet" {
  if (!iso) return "violet";
  if (now === null) return "gold";
  const s = (now - new Date(iso).getTime()) / 1000;
  return s < 120 ? "up" : s < 3600 ? "gold" : "warn";
}

export function MarketsView({ board, initialSymbol }: { board: DataEnvelope<MarketBoard>; initialSymbol?: string }) {
  const { t, l, tx } = useI18n();
  const f = useFormat();
  const now = useNow();
  const instruments = board.data.instruments;
  const [cls, setCls] = useState<ClassFilter>("all");
  const [q, setQ] = useState("");
  const [selected, setSelected] = useState(() => (initialSymbol && instruments.some((i) => i.id === initialSymbol && i.price !== null) ? initialSymbol : "btc"));
  const [tf, setTf] = useState<Timeframe>("1D");
  const [mode, setMode] = useState<"candles" | "line">("candles");
  const [series, setSeries] = useState<{ key: string; candles: Candle[] }>(() => ({ key: `${selected}:1D`, candles: board.data.candles[selected] ?? [] }));
  const candles = series.candles;

  // Fetch OHLC on demand (client-side API call) — skipped when the server already shipped it.
  useEffect(() => {
    const key = `${selected}:${tf}`;
    if (key === series.key) return;
    let alive = true;
    void getCandles(selected, tf).then((r) => {
      if (alive) setSeries({ key, candles: r.data });
    });
    return () => {
      alive = false;
    };
  }, [selected, tf, series.key]);

  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return instruments.filter((i) => (cls === "all" || i.assetClass === cls) && (!needle || i.symbol.toLowerCase().includes(needle) || i.name.fa.includes(needle) || i.name.en.toLowerCase().includes(needle)));
  }, [instruments, cls, q]);

  const counts = useMemo(() => {
    const c: Record<DataStatus, number> = { LIVE: 0, STALE: 0, UNKNOWN: 0, UNAVAILABLE: 0, DEMO: 0 };
    instruments.forEach((i) => c[i.status]++);
    return c;
  }, [instruments]);

  const inst = instruments.find((i) => i.id === selected);
  const classes: { value: ClassFilter; label: string }[] = [
    { value: "all", label: t.common.all },
    { value: "crypto", label: tx("رمزارز", "Crypto") },
    { value: "fx", label: tx("ارز", "FX") },
    { value: "commodity", label: tx("کالا", "Commodities") },
    { value: "index", label: tx("شاخص", "Indices") },
    { value: "iran", label: tx("ایران", "Iran") },
    { value: "rate", label: tx("نرخ بهره", "Rates") },
  ];

  return (
    <PageBody>
      <PageHeader title={t.nav.items.markets} subtitle={tx("جدول چنددارایی با وضعیت تازگی هر ردیف، نمودار کندل و خطی", "Multi-asset board with per-row freshness, candlestick and line charts")} icon={ChartCandlestick} />

      <Notice icon={<Timer />} tone="info">
        {tx(
          "هر ردیف وضعیت و سن داده خود را دارد. در نسخه نمایشی هیچ ردیفی «زنده» نیست؛ ردیف‌های کهنه (STALE)، نامعلوم (UNKNOWN) و ناموجود (UNAVAILABLE) عمداً برای نمایش رفتار رابط شبیه‌سازی شده‌اند.",
          "Each row carries its own status and age. Nothing is LIVE in the demo build; STALE, UNKNOWN and UNAVAILABLE rows are simulated on purpose to show how the UI behaves.",
        )}
        <div className="mt-1.5 flex flex-wrap gap-1.5">
          {(Object.keys(counts) as DataStatus[])
            .filter((k) => counts[k] > 0)
            .map((k) => (
              <span key={k} className="inline-flex items-center gap-1">
                <StatusChip status={k} />
                <Num className="text-3xs text-fg-3">×{f.num(counts[k], 0)}</Num>
              </span>
            ))}
        </div>
      </Notice>

      <DataCard
        title={inst ? `${inst.symbol} · ${l(inst.name)}` : tx("نمودار", "Chart")}
        subtitle={tx("کندل‌ها نمایشی‌اند — ابزار بزرگ‌نمایی با چرخ ماوس", "Demo candles — zoom with mouse wheel")}
        icon={ChartCandlestick}
        meta={board.meta}
        actions={
          <div className="flex items-center gap-1.5">
            <Segmented label={tx("بازه زمانی", "Timeframe")} size="xs" value={tf} onChange={setTf} options={(["1H", "4H", "1D"] as Timeframe[]).map((v) => ({ value: v, label: <span dir="ltr">{v}</span> }))} />
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
          </div>
        }
      >
        {inst && (
          <div className="mb-2 flex flex-wrap items-center gap-x-5 gap-y-1">
            <Num className="text-2xl font-semibold text-fg-1">{f.num(inst.price, inst.decimals, inst.decimals)}</Num>
            <Delta value={inst.change24h} size="md" />
            <span className="text-2xs text-fg-4">
              {t.common.high} <Num className="text-fg-2">{f.num(inst.high24h, inst.decimals)}</Num>
            </span>
            <span className="text-2xs text-fg-4">
              {t.common.low} <Num className="text-fg-2">{f.num(inst.low24h, inst.decimals)}</Num>
            </span>
            <span className="text-2xs text-fg-4">
              {t.common.volume} <Num className="text-fg-2">{f.compact(inst.volume24h)}</Num>
            </span>
            <StatusChip status={inst.status} size="sm" />
          </div>
        )}
        <CandlesChart candles={candles} height={360} label={`${inst?.symbol ?? ""} ${tf}`} mode={mode} decimals={inst?.decimals ?? 2} />
      </DataCard>

      <DataCard
        title={tx("تابلوی قیمت‌ها", "Price board")}
        subtitle={tx("برای نمایش نمودار روی ردیف کلیک کنید", "Click a row to chart it")}
        icon={ChartCandlestick}
        meta={board.meta}
        bodyClassName="px-0 pb-0"
        actions={
          <label className="relative hidden @2xl:block">
            <span className="sr-only">{t.common.search}</span>
            <Search aria-hidden className="pointer-events-none absolute start-2 top-1/2 size-3.5 -translate-y-1/2 text-fg-4" />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder={t.common.search}
              className="h-7 w-44 rounded-[var(--radius-sm)] border border-[var(--line-subtle)] bg-[var(--surface-input)] pe-2 ps-7 text-xs text-fg-1 placeholder:text-fg-5 focus:border-gold-400/50 focus:outline-none"
            />
          </label>
        }
      >
        <div className="px-3.5 pb-2">
          <Segmented label={tx("طبقه دارایی", "Asset class")} value={cls} onChange={setCls} options={classes} />
        </div>
        <div className="max-h-[560px] overflow-auto">
          <table className="data-table">
            <caption className="sr-only">{tx("تابلوی قیمت‌ها", "Price board")}</caption>
            <thead>
              <tr>
                <th scope="col" className="ps-3.5">{t.common.symbol}</th>
                <th scope="col" className="num-cell">{t.common.price}</th>
                <th scope="col" className="num-cell">{t.common.change24h}</th>
                <th scope="col" className="num-cell hidden @3xl:table-cell">{t.common.range24h}</th>
                <th scope="col" className="num-cell hidden @4xl:table-cell">{t.common.volume}</th>
                <th scope="col" className="hidden w-28 @2xl:table-cell">{t.common.trend}</th>
                <th scope="col">{t.common.status}</th>
                <th scope="col" className="pe-3.5">{tx("سن داده", "Age")}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((i) => (
                <tr
                  key={i.id}
                  data-selected={i.id === selected}
                  tabIndex={0}
                  aria-selected={i.id === selected}
                  onClick={() => i.price !== null && setSelected(i.id)}
                  onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && i.price !== null && setSelected(i.id)}
                  className={cn(i.price !== null && "cursor-pointer")}
                >
                  <td className="ps-3.5">
                    <bdi className="block text-xs font-semibold text-fg-1">{i.symbol}</bdi>
                    <span className="block max-w-[180px] truncate text-3xs text-fg-4">{l(i.name)}</span>
                  </td>
                  <td className="num-cell">
                    <Num className={cn("text-xs", i.price === null ? "text-fg-4" : "text-fg-1")}>{f.num(i.price, i.decimals, i.decimals)}</Num>
                    <span className="px-1 text-3xs text-fg-5" dir="ltr">
                      {i.quote}
                    </span>
                  </td>
                  <td className="num-cell">
                    <Delta value={i.change24h} size="xs" />
                  </td>
                  <td className="num-cell hidden @3xl:table-cell">
                    <Num className="text-3xs text-fg-3">
                      {f.num(i.low24h, i.decimals)} – {f.num(i.high24h, i.decimals)}
                    </Num>
                  </td>
                  <td className="num-cell hidden @4xl:table-cell">
                    <Num className="text-3xs text-fg-3">{f.compact(i.volume24h)}</Num>
                  </td>
                  <td className="hidden @2xl:table-cell">
                    <Sparkline data={i.spark} height={22} area={false} color={(i.change24h ?? 0) >= 0 ? "var(--color-data-400)" : "var(--color-down)"} label={`${i.symbol}`} />
                  </td>
                  <td>
                    <StatusChip status={i.status} />
                  </td>
                  <td className="pe-3.5">
                    <Chip tone={ageTone(i.retrievedAt, now)} icon={Timer}>
                      <TimeAgo iso={i.retrievedAt} withTitle={false} />
                    </Chip>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </DataCard>
    </PageBody>
  );
}
