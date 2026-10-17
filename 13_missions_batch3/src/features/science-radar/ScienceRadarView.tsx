// FILE: 13_missions_batch3/src/features/science-radar/ScienceRadarView.tsx
"use client";
import { useState } from "react";
import { Shell } from "@/components/shell/Shell";
import { StateBlock } from "@/components/truth/StateBlock";
import { DetailsDrawer } from "@/components/truth/DetailsDrawer";
import { DataTable, type Column } from "@/components/truth/DataTable";
import { TruthChip } from "@/components/truth/TruthChip";
import { getSnapshot } from "@/adapters/science-radar";
import { useSnapshot } from "@/lib/useSnapshot";
import { useFlags } from "@/lib/useFlags";
import { nonDemo, resolveViewState, truthFromSnapshot } from "@/lib/stats";
import { dash, faNum, tehranDate } from "@/lib/format";
import type { RadarSourceType, ScienceRadarItem } from "@/contract/types";

const SOURCE_LABEL: Record<RadarSourceType, string> = {
  paper: "مقاله",
  repo: "مخزن",
  blog: "وبلاگ",
  university: "دانشگاه",
  agent: "عامل",
};

const SOURCE_TYPES: RadarSourceType[] = ["paper", "repo", "blog", "university", "agent"];

/** «رادار علم» (M44) — read-only display. No claims, no scores, no ranking. */
export function ScienceRadarView() {
  const flags = useFlags();
  const { phase, data } = useSnapshot(getSnapshot);
  const [open, setOpen] = useState(false);
  const [fSource, setFSource] = useState<string>("ALL");
  const [fTopic, setFTopic] = useState<string>("ALL");

  const items = data?.items ?? [];
  const view = resolveViewState(phase, data, items.length, flags.state);
  const truth = data ? truthFromSnapshot(data, items) : "UNKNOWN";
  const counted = nonDemo(items);
  const topics = Array.from(new Set(items.map((i) => i.topic)));

  // Items without a found-date stay visible (rendered with «—»), never dropped.
  const withDate = items
    .filter((i) => i.foundAt)
    .sort((a, b) => (b.foundAt ?? "").localeCompare(a.foundAt ?? ""));
  const noDate = items.filter((i) => !i.foundAt);
  const latest = [
    ...withDate.slice(0, Math.max(0, 7 - noDate.length)),
    ...noDate,
  ].slice(0, 7);

  const filtered = items.filter(
    (i) =>
      (fSource === "ALL" || i.sourceType === fSource) &&
      (fTopic === "ALL" || i.topic === fTopic),
  );

  const columns: Column<ScienceRadarItem>[] = [
    { key: "id", header: "شناسه", render: (r) => <code>{r.id}</code> },
    { key: "title", header: "عنوان", render: (r) => r.title },
    { key: "sourceType", header: "نوع منبع", render: (r) => SOURCE_LABEL[r.sourceType] },
    { key: "topic", header: "موضوع", render: (r) => r.topic },
    { key: "foundAt", header: "تاریخ یافت‌شدن", render: (r) => tehranDate(r.foundAt) },
    { key: "status", header: "وضعیت", render: (r) => <span className="ah-chip ah-chip-muted">{r.status}</span> },
    { key: "note", header: "یادداشت ارتباط", render: (r) => dash(r.relevanceNote) },
    { key: "sourceText", header: "منبع (متن ساده)", render: (r) => dash(r.sourceText) },
    { key: "demo", header: "DEMO", render: (r) => (r.demo ? <TruthChip status="DEMO" /> : <span className="ah-muted">—</span>) },
  ];

  return (
    <Shell
      title="رادار علم"
      truth={flags.demo ? "DEMO" : truth}
      source={data?.source ?? null}
      lastRead={data?.generatedAt ?? null}
      rowCount={items.length}
      snapshot={data}
    >
      <p className="ah-honest">رادار فقط یافته‌ها را نشان می‌دهد؛ ادعا نیست</p>

      {view !== "OK" ? (
        <StateBlock state={view} />
      ) : (
        <div className="flex flex-col gap-3">
          <section className="ah-panel">
            <h2>شمارش بر اساس نوع منبع (بدون ردیف‌های DEMO)</h2>
            <div className="flex flex-wrap gap-2" style={{ marginTop: 8 }}>
              {SOURCE_TYPES.map((st) => (
                <span key={st} className="ah-chip ah-chip-info" data-count={st}>
                  {SOURCE_LABEL[st]}: {faNum(counted.filter((i) => i.sourceType === st).length)}
                </span>
              ))}
              <span className="ah-chip ah-chip-muted">کل غیر-DEMO: {faNum(counted.length)}</span>
            </div>
            <p className="ah-muted" style={{ marginTop: 8, fontSize: 13 }}>
              ردیف‌های DEMO از همه شمارش‌ها حذف شده‌اند و فقط با برچسب DEMO نمایش داده می‌شوند.
            </p>
          </section>

          <section className="ah-panel">
            <h2>تازه‌ترین یافته‌ها (حداکثر ۷ مورد)</h2>
            <ul className="flex flex-col gap-2" style={{ listStyle: "none", margin: 0, padding: 0 }}>
              {latest.map((item) => (
                <li key={item.id} className="ah-panel" style={{ background: "transparent" }}>
                  <div className="flex flex-wrap items-center gap-2">
                    <code>{item.id}</code>
                    <strong>{item.title}</strong>
                    {item.demo ? <TruthChip status="DEMO" /> : null}
                    <span className="ah-chip ah-chip-muted">{SOURCE_LABEL[item.sourceType]}</span>
                    <span className="ah-chip ah-chip-muted">{item.topic}</span>
                    <span className="ah-chip ah-chip-muted">{tehranDate(item.foundAt)}</span>
                  </div>
                  <div style={{ fontSize: 15, marginTop: 6 }}>
                    <span>{dash(item.relevanceNote)}</span>
                    <span className="ah-muted"> · منبع: {dash(item.sourceText)}</span>
                  </div>
                </li>
              ))}
            </ul>
          </section>

          <DetailsDrawer open={open} onToggle={() => setOpen((o) => !o)}>
            <div className="flex flex-wrap items-center gap-2" style={{ marginBottom: 12 }}>
              <label className="ah-muted" htmlFor="sr-src">نوع منبع</label>
              <select id="sr-src" className="ah-select" value={fSource} onChange={(e) => setFSource(e.target.value)}>
                <option value="ALL">همه</option>
                {SOURCE_TYPES.map((st) => (
                  <option key={st} value={st}>{SOURCE_LABEL[st]}</option>
                ))}
              </select>
              <label className="ah-muted" htmlFor="sr-topic">موضوع</label>
              <select id="sr-topic" className="ah-select" value={fTopic} onChange={(e) => setFTopic(e.target.value)}>
                <option value="ALL">همه</option>
                {topics.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <DataTable columns={columns} rows={filtered} rowKey={(r) => r.id} />
          </DetailsDrawer>
        </div>
      )}
    </Shell>
  );
}
