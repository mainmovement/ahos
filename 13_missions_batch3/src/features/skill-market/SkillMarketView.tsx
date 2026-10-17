// FILE: 13_missions_batch3/src/features/skill-market/SkillMarketView.tsx
"use client";
import { useState } from "react";
import { Shell } from "@/components/shell/Shell";
import { StateBlock } from "@/components/truth/StateBlock";
import { DetailsDrawer } from "@/components/truth/DetailsDrawer";
import { DataTable, type Column } from "@/components/truth/DataTable";
import { TruthChip } from "@/components/truth/TruthChip";
import { getSnapshot } from "@/adapters/skill-market";
import { useSnapshot } from "@/lib/useSnapshot";
import { useFlags } from "@/lib/useFlags";
import { effectiveReview, nonDemo, resolveViewState, truthFromSnapshot } from "@/lib/stats";
import { dash, faNum } from "@/lib/format";
import type { SkillKind, SkillMarketEntry } from "@/contract/types";

const KIND_LABEL: Record<SkillKind, string> = { skill: "مهارت", plugin: "افزونه" };

/** «بازار مهارت و افزونه» (M52) — catalog display only. Nothing is installable. */
export function SkillMarketView() {
  const flags = useFlags();
  const { phase, data } = useSnapshot(getSnapshot);
  const [open, setOpen] = useState(false);
  const [fKind, setFKind] = useState<string>("ALL");
  const [fReview, setFReview] = useState<string>("ALL");

  const entries = data?.entries ?? [];
  const view = resolveViewState(phase, data, entries.length, flags.state);
  const truth = data ? truthFromSnapshot(data, entries) : "UNKNOWN";
  const counted = nonDemo(entries);

  const highlights = entries.slice(0, 7);
  const filtered = entries.filter((e) => {
    const eff = effectiveReview(e).state;
    return (fKind === "ALL" || e.kind === fKind) && (fReview === "ALL" || eff === fReview);
  });

  const columns: Column<SkillMarketEntry>[] = [
    { key: "id", header: "شناسه", render: (r) => <code>{r.id}</code> },
    { key: "name", header: "نام", render: (r) => r.name },
    { key: "kind", header: "نوع", render: (r) => KIND_LABEL[r.kind] },
    { key: "version", header: "نسخه", render: (r) => dash(r.version) },
    { key: "source", header: "منبع", render: (r) => dash(r.source) },
    { key: "install", header: "وضعیت نصب (نمایشی)", render: (r) => <span className="ah-chip ah-chip-muted">{r.installState}</span> },
    {
      key: "perms",
      header: "مجوزهای درخواستی",
      render: (r) =>
        r.permissions.length === 0 ? (
          <span className="ah-muted">—</span>
        ) : (
          <ul style={{ margin: 0, paddingInlineStart: 18 }}>
            {r.permissions.map((p) => (
              <li key={p}>{p}</li>
            ))}
          </ul>
        ),
    },
    {
      key: "review",
      header: "بازبینی",
      render: (r) => {
        const eff = effectiveReview(r);
        return (
          <span className="flex flex-wrap items-center gap-2">
            <span className="ah-chip ah-chip-muted">{eff.state}</span>
            {eff.note ? <span className="ah-chip ah-chip-unknown">{eff.note}</span> : null}
          </span>
        );
      },
    },
    { key: "reason", header: "دلیل", render: (r) => dash(r.reason) },
    { key: "demo", header: "DEMO", render: (r) => (r.demo ? <TruthChip status="DEMO" /> : <span className="ah-muted">—</span>) },
    {
      key: "copy",
      header: "شناسه",
      render: (r) => (
        <button
          type="button"
          className="ah-btn ah-btn-ghost"
          onClick={() => {
            if (typeof navigator !== "undefined" && navigator.clipboard) {
              void navigator.clipboard.writeText(r.id);
            }
          }}
        >
          کپی شناسه
        </button>
      ),
    },
  ];

  return (
    <Shell
      title="بازار مهارت و افزونه"
      truth={flags.demo ? "DEMO" : truth}
      source={data?.source ?? null}
      lastRead={data?.generatedAt ?? null}
      rowCount={entries.length}
      snapshot={data}
    >
      <p className="ah-honest">کاتالوگ نمایشی است؛ نصب در این صفحه ممکن نیست</p>

      {view !== "OK" ? (
        <StateBlock state={view} />
      ) : (
        <div className="flex flex-col gap-3">
          <section className="ah-panel">
            <h2>شمارش‌ها (بدون ردیف‌های DEMO)</h2>
            <div className="flex flex-wrap gap-2" style={{ marginTop: 8 }}>
              <span className="ah-chip ah-chip-info" data-count="skill">مهارت: {faNum(counted.filter((e) => e.kind === "skill").length)}</span>
              <span className="ah-chip ah-chip-info" data-count="plugin">افزونه: {faNum(counted.filter((e) => e.kind === "plugin").length)}</span>
              <span className="ah-chip ah-chip-muted">کل غیر-DEMO: {faNum(counted.length)}</span>
            </div>
            <p className="ah-muted" style={{ marginTop: 8, fontSize: 13 }}>
              وضعیت‌ها فقط نمایشی هستند؛ هیچ موردی «ایمن» اعلام نمی‌شود.
            </p>
          </section>

          <section className="ah-panel">
            <h2>موارد شاخص (حداکثر ۷ مورد)</h2>
            <ul className="flex flex-col gap-2" style={{ listStyle: "none", margin: 0, padding: 0 }}>
              {highlights.map((entry) => {
                const eff = effectiveReview(entry);
                return (
                  <li key={entry.id} className="ah-panel" style={{ background: "transparent" }}>
                    <div className="flex flex-wrap items-center gap-2">
                      <code>{entry.id}</code>
                      <strong>{entry.name}</strong>
                      <span className="ah-chip ah-chip-muted">{KIND_LABEL[entry.kind]}</span>
                      <span className="ah-chip ah-chip-muted">{entry.installState}</span>
                      <span className="ah-chip ah-chip-muted">{eff.state}</span>
                      {eff.note ? <span className="ah-chip ah-chip-unknown">{eff.note}</span> : null}
                      {entry.demo ? <TruthChip status="DEMO" /> : null}
                    </div>
                    <div style={{ fontSize: 15, marginTop: 6 }}>
                      <span className="ah-muted">نسخه: {dash(entry.version)} · مجوزها: </span>
                      {entry.permissions.length === 0 ? "—" : entry.permissions.join("، ")}
                    </div>
                  </li>
                );
              })}
            </ul>
          </section>

          <DetailsDrawer open={open} onToggle={() => setOpen((o) => !o)}>
            <div className="flex flex-wrap items-center gap-2" style={{ marginBottom: 12 }}>
              <label className="ah-muted" htmlFor="sm-kind">نوع</label>
              <select id="sm-kind" className="ah-select" value={fKind} onChange={(e) => setFKind(e.target.value)}>
                <option value="ALL">همه</option>
                <option value="skill">مهارت</option>
                <option value="plugin">افزونه</option>
              </select>
              <label className="ah-muted" htmlFor="sm-review">بازبینی</label>
              <select id="sm-review" className="ah-select" value={fReview} onChange={(e) => setFReview(e.target.value)}>
                <option value="ALL">همه</option>
                <option value="UNREVIEWED">UNREVIEWED</option>
                <option value="REVIEWED">REVIEWED</option>
                <option value="REJECTED">REJECTED</option>
              </select>
            </div>
            <DataTable columns={columns} rows={filtered} rowKey={(r) => r.id} />
          </DetailsDrawer>
        </div>
      )}
    </Shell>
  );
}
