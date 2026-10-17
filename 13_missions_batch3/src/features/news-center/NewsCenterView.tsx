// FILE: 13_missions_batch3/src/features/news-center/NewsCenterView.tsx
"use client";
import { useState } from "react";
import { Shell } from "@/components/shell/Shell";
import { StateBlock } from "@/components/truth/StateBlock";
import { DetailsDrawer } from "@/components/truth/DetailsDrawer";
import { DataTable, type Column } from "@/components/truth/DataTable";
import { TruthChip } from "@/components/truth/TruthChip";
import { getSnapshot } from "@/adapters/news-center";
import { useSnapshot } from "@/lib/useSnapshot";
import { useFlags } from "@/lib/useFlags";
import { newsFreshness, nonDemo, resolveViewState, truthFromSnapshot } from "@/lib/stats";
import { dash, faNum, tehranDateTime } from "@/lib/format";
import type { Freshness, NewsItem, NewsTopic } from "@/contract/types";

const TOPIC_LABEL: Record<NewsTopic, string> = {
  Oil: "نفت",
  Gold: "طلا",
  Macro: "کلان",
  Other: "سایر",
};

const CONNECTED: NewsTopic[] = ["Oil", "Gold"];

function FreshnessChip({ value }: { value: Freshness }) {
  const cls =
    value === "LIVE"
      ? "ah-chip ah-chip-live"
      : value === "STALE"
        ? "ah-chip ah-chip-stale"
        : "ah-chip ah-chip-unknown";
  return <span className={cls} data-freshness={value}>{value}</span>;
}

/** «مرکز اخبار آرام» (M18.N) — information desk, never a trading signal. */
export function NewsCenterView() {
  const flags = useFlags();
  const { phase, data } = useSnapshot(getSnapshot);
  const [open, setOpen] = useState(false);
  const [fTopic, setFTopic] = useState<string>("ALL");
  const [fFresh, setFFresh] = useState<string>("ALL");

  const items = data?.items ?? [];
  const view = resolveViewState(phase, data, items.length, flags.state);
  const truth = data ? truthFromSnapshot(data, items) : "UNKNOWN";
  const counted = nonDemo(items);
  const staleAfter = data?.staleAfterMinutes ?? 30;

  const freshnessOf = (item: NewsItem): Freshness =>
    newsFreshness(item, data?.generatedAt ?? null, staleAfter);

  // Items without a timestamp can never be silently dropped from the calm
  // feed — slots are reserved for them and they render with UNKNOWN.
  const withTime = items
    .filter((i) => i.time)
    .sort((a, b) => (b.time ?? "").localeCompare(a.time ?? ""));
  const noTime = items.filter((i) => !i.time);
  const headlines = [
    ...withTime.slice(0, Math.max(0, 7 - noTime.length)),
    ...noTime,
  ].slice(0, 7);

  const filtered = items.filter((item) => {
    const fresh = freshnessOf(item);
    return (fTopic === "ALL" || item.topic === fTopic) && (fFresh === "ALL" || fresh === fFresh);
  });

  const columns: Column<NewsItem>[] = [
    { key: "id", header: "شناسه", render: (r) => <code>{r.id}</code> },
    { key: "time", header: "زمان", render: (r) => tehranDateTime(r.time) },
    { key: "source", header: "منبع", render: (r) => dash(r.sourceName) },
    {
      key: "topic",
      header: "موضوع",
      render: (r) => (
        <span className="flex flex-wrap items-center gap-2">
          <span className="ah-chip ah-chip-muted">{TOPIC_LABEL[r.topic]}</span>
          {CONNECTED.includes(r.topic) ? (
            <span className="ah-chip ah-chip-info">متصل</span>
          ) : (
            <span className="ah-chip ah-chip-unknown">PLANNED · متصل نیست</span>
          )}
        </span>
      ),
    },
    { key: "summary", header: "خلاصه", render: (r) => r.summary },
    { key: "fresh", header: "تازگی", render: (r) => <FreshnessChip value={freshnessOf(r)} /> },
    { key: "rel", header: "اعتبار منبع", render: (r) => r.reliability ?? "نامشخص" },
    { key: "demo", header: "DEMO", render: (r) => (r.demo ? <TruthChip status="DEMO" /> : <span className="ah-muted">—</span>) },
  ];

  return (
    <Shell
      title="مرکز اخبار آرام"
      truth={flags.demo ? "DEMO" : truth}
      source={data?.source ?? null}
      lastRead={data?.generatedAt ?? null}
      rowCount={items.length}
      snapshot={data}
    >
      <p className="ah-honest">اخبار اطلاعاتی است، نه سیگنال معاملاتی</p>

      {view !== "OK" ? (
        <StateBlock state={view} />
      ) : (
        <div className="flex flex-col gap-3">
          <section className="ah-panel">
            <h2>خبرهای آرام (حداکثر ۷ مورد)</h2>
            <ul className="flex flex-col gap-2" style={{ listStyle: "none", margin: 0, padding: 0 }}>
              {headlines.map((item) => {
                const fresh = freshnessOf(item);
                return (
                  <li key={item.id} className="ah-panel" style={{ background: "transparent" }}>
                    <div className="flex flex-wrap items-center gap-2">
                      <FreshnessChip value={fresh} />
                      <span className="ah-chip ah-chip-muted">{TOPIC_LABEL[item.topic]}</span>
                      {CONNECTED.includes(item.topic) ? (
                        <span className="ah-chip ah-chip-info">متصل</span>
                      ) : (
                        <span className="ah-chip ah-chip-unknown">PLANNED · متصل نیست</span>
                      )}
                      {item.demo ? <TruthChip status="DEMO" /> : null}
                      <span className="ah-muted">{tehranDateTime(item.time)}</span>
                    </div>
                    <div style={{ fontSize: 15, marginTop: 6 }}>{item.summary}</div>
                    <div className="ah-muted" style={{ fontSize: 13, marginTop: 4 }}>
                      {dash(item.sourceName)} · اعتبار منبع: {item.reliability ?? "نامشخص"}
                    </div>
                  </li>
                );
              })}
            </ul>
            <p className="ah-muted" style={{ marginTop: 8, fontSize: 13 }}>
              خبرهای غیر-DEMO در شمارش‌ها: {faNum(counted.length)} · فقط نفت و طلا متصل هستند؛ موضوع‌های دیگر PLANNED هستند.
            </p>
          </section>

          <DetailsDrawer open={open} onToggle={() => setOpen((o) => !o)}>
            <div className="flex flex-wrap items-center gap-2" style={{ marginBottom: 12 }}>
              <label className="ah-muted" htmlFor="nc-topic">موضوع</label>
              <select id="nc-topic" className="ah-select" value={fTopic} onChange={(e) => setFTopic(e.target.value)}>
                <option value="ALL">همه</option>
                <option value="Oil">نفت</option>
                <option value="Gold">طلا</option>
                <option value="Macro">کلان</option>
                <option value="Other">سایر</option>
              </select>
              <label className="ah-muted" htmlFor="nc-fresh">تازگی</label>
              <select id="nc-fresh" className="ah-select" value={fFresh} onChange={(e) => setFFresh(e.target.value)}>
                <option value="ALL">همه</option>
                <option value="LIVE">LIVE</option>
                <option value="STALE">STALE</option>
                <option value="UNKNOWN">UNKNOWN</option>
              </select>
            </div>
            <DataTable columns={columns} rows={filtered} rowKey={(r) => r.id} />
          </DetailsDrawer>
        </div>
      )}
    </Shell>
  );
}
