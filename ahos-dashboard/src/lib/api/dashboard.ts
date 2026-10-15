import type { DataEnvelope, Kpi } from "./types";
import { fromMock, label } from "./_envelope";
import { mockKpis } from "@/mock/kpis";

/** Command Center KPI row. Real source: Python canonical read model aggregates. */
export async function getKpis(): Promise<DataEnvelope<Kpi[]>> {
  return fromMock(mockKpis(), "kpis", label("خلاصه خط لوله (نمایشی)", "Pipeline summary (demo)"), 24, 120);
}

/** Sidebar badge counts. Real source: aggregate counters from the read model. */
export async function getNavBadges(): Promise<DataEnvelope<Record<string, number>>> {
  return fromMock(
    { opportunities: 21, tokens: 6, news: 8, security: 4, university: 2, agents: 25, paperTrading: 5, errors: 6 },
    "nav-badges",
    label("شمارنده‌های نمایشی", "Demo counters"),
    30,
    120,
  );
}
