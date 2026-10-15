"use client";

import Link from "next/link";
import { ChartCandlestick } from "lucide-react";
import type { DataMeta, Instrument } from "@/lib/api/types";
import { useFormat } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import { Delta, Num, TimeAgo } from "@/components/ui/primitives";
import { StatusChip } from "@/components/ui/status";
import { Sparkline } from "@/components/charts/sparkline";
import { DataCard } from "./data-card";

/** Compact market-watch table with staleness per row. */
export function MarketWatchCard({ instruments, meta, title, className, limit }: { instruments: Instrument[]; meta: DataMeta; title?: string; className?: string; limit?: number }) {
  const { t, l, tx } = useI18n();
  const rows = limit ? instruments.slice(0, limit) : instruments;
  return (
    <DataCard
      title={title ?? tx("پایش بازار", "Market watch")}
      subtitle={tx("قیمت، تغییر ۲۴ساعته و تازگی هر ردیف", "Price, 24h change and per-row freshness")}
      icon={ChartCandlestick}
      meta={meta}
      className={className}
      bodyClassName="px-0 pb-0"
      actions={
        <Link href="/markets" className="text-3xs text-gold-300 hover:text-gold-100">
          {t.common.viewAll}
        </Link>
      }
    >
      <div className="max-h-[340px] overflow-auto">
        <table className="data-table">
          <caption className="sr-only">{title ?? tx("پایش بازار", "Market watch")}</caption>
          <thead>
            <tr>
              <th scope="col" className="ps-3.5">{t.common.symbol}</th>
              <th scope="col" className="num-cell">{t.common.price}</th>
              <th scope="col" className="num-cell">{t.common.change24h}</th>
              <th scope="col" className="hidden w-24 @4xl:table-cell">{t.common.trend}</th>
              <th scope="col" className="pe-3.5">{t.common.status}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((i) => (
              <MarketRow key={i.id} i={i} label={l(i.name)} />
            ))}
          </tbody>
        </table>
      </div>
    </DataCard>
  );
}

function MarketRow({ i, label }: { i: Instrument; label: string }) {
  const f = useFormat();
  return (
    <tr>
      <td className="ps-3.5">
        <Link href={`/markets?symbol=${i.id}`} className="group flex flex-col leading-tight">
          <bdi className="text-xs font-semibold text-fg-1 group-hover:text-gold-200">{i.symbol}</bdi>
          <span className="max-w-[140px] truncate text-3xs text-fg-4">{label}</span>
        </Link>
      </td>
      <td className="num-cell">
        <Num className={cn("text-xs", i.price === null ? "text-fg-4" : "text-fg-1")}>{f.num(i.price, i.decimals, i.decimals)}</Num>
        <div className="text-3xs text-fg-5" dir="ltr">
          {i.quote}
        </div>
      </td>
      <td className="num-cell">
        <Delta value={i.change24h} size="xs" />
      </td>
      <td className="hidden @4xl:table-cell">
        <Sparkline data={i.spark} height={22} area={false} color={(i.change24h ?? 0) >= 0 ? "var(--color-data-400)" : "var(--color-down)"} label={`${i.symbol} trend`} />
      </td>
      <td className="pe-3.5">
        <div className="flex flex-col items-start gap-0.5">
          <StatusChip status={i.status} />
          <TimeAgo iso={i.retrievedAt} className="text-3xs text-fg-5" />
        </div>
      </td>
    </tr>
  );
}
