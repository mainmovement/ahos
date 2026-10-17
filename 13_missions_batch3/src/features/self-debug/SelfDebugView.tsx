// FILE: 13_missions_batch3/src/features/self-debug/SelfDebugView.tsx
"use client";
import { useState } from "react";
import { Shell } from "@/components/shell/Shell";
import { StateBlock } from "@/components/truth/StateBlock";
import { DetailsDrawer } from "@/components/truth/DetailsDrawer";
import { DataTable, type Column } from "@/components/truth/DataTable";
import { TruthChip } from "@/components/truth/TruthChip";
import { getSnapshot } from "@/adapters/self-debug";
import { useSnapshot } from "@/lib/useSnapshot";
import { useFlags } from "@/lib/useFlags";
import { nonDemo, resolveViewState, truthFromSnapshot } from "@/lib/stats";
import { ageLabel, clamp, dash, faNum, median, tehranDateTime } from "@/lib/format";
import type { SelfDebugIncident } from "@/contract/types";

/** «خطایابی خودکار» (M46) — READ-ONLY. No restart, no patch, no apply-fix. */
export function SelfDebugView() {
  const flags = useFlags();
  const { phase, data } = useSnapshot(getSnapshot);
  const [open, setOpen] = useState(false);
  const [fStatus, setFStatus] = useState<string>("ALL");
  const [openIncident, setOpenIncident] = useState<string | null>(null);

  const incidents = data?.incidents ?? [];
  const view = resolveViewState(phase, data, incidents.length, flags.state);
  const truth = data ? truthFromSnapshot(data, incidents) : "UNKNOWN";
  const counted = nonDemo(incidents);

  const openCount = counted.filter((i) => i.status === "OPEN").length;
  const diagnosedCount = counted.filter((i) => i.status === "DIAGNOSED").length;
  const ages = counted
    .filter((i) => i.status === "OPEN" && i.time && data?.generatedAt)
    .map((i) => new Date(data!.generatedAt!).getTime() - new Date(i.time!).getTime())
    .filter((ms) => ms >= 0);
  const medianHours = (() => {
    const m = median(ages.map((ms) => ms / 3600000));
    return m === null ? "—" : `${faNum(Math.round(m))} ساعت`;
  })();

  const recent = [...incidents]
    .sort((a, b) => (b.time ?? "").localeCompare(a.time ?? ""))
    .slice(0, 7);

  const filtered = incidents.filter((i) => fStatus === "ALL" || i.status === fStatus);

  const columns: Column<SelfDebugIncident>[] = [
    { key: "id", header: "شناسه", render: (r) => <code>{r.id}</code> },
    { key: "time", header: "زمان", render: (r) => tehranDateTime(r.time) },
    { key: "component", header: "مؤلفه", render: (r) => r.component },
    { key: "sig", header: "امضای خطا (redacted)", render: (r) => clamp(r.errorSignature, 120) },
    { key: "status", header: "وضعیت", render: (r) => <span className="ah-chip ah-chip-muted">{r.status}</span> },
    {
      key: "evidence",
      header: "شواهد",
      render: (r) =>
        r.evidencePath ? (
          <span className="ah-cyan">{r.evidencePath}</span>
        ) : (
          <span className="ah-muted">بدون شواهد</span>
        ),
    },
    {
      key: "detail",
      header: "جزئیات",
      render: (r) => (
        <button
          type="button"
          className="ah-btn ah-btn-ghost"
          onClick={() => setOpenIncident((cur) => (cur === r.id ? null : r.id))}
          aria-expanded={openIncident === r.id}
        >
          {openIncident === r.id ? "بستن" : "جزئیات"}
        </button>
      ),
    },
  ];

  return (
    <Shell
      title="خطایابی خودکار"
      truth={flags.demo ? "DEMO" : truth}
      source={data?.source ?? null}
      lastRead={data?.generatedAt ?? null}
      rowCount={incidents.length}
      snapshot={data}
    >
      <p className="ah-honest">فقط نمایش؛ اقدام در جای دیگر</p>

      {view !== "OK" ? (
        <StateBlock state={view} />
      ) : (
        <div className="flex flex-col gap-3">
          <section className="ah-panel">
            <h2>خلاصه (بدون ردیف‌های DEMO)</h2>
            <div className="flex flex-wrap gap-2" style={{ marginTop: 8 }}>
              <span className="ah-chip ah-chip-info" data-count="open">باز: {faNum(openCount)}</span>
              <span className="ah-chip ah-chip-info" data-count="diagnosed">تشخیص‌داده: {faNum(diagnosedCount)}</span>
              <span className="ah-chip ah-chip-muted">میانه سن موارد باز: {medianHours}</span>
            </div>
          </section>

          <section className="ah-panel">
            <h2>رخدادهای اخیر (حداکثر ۷ مورد)</h2>
            <ul className="flex flex-col gap-2" style={{ listStyle: "none", margin: 0, padding: 0 }}>
              {recent.map((inc) => (
                <li key={inc.id} className="ah-panel" style={{ background: "transparent" }}>
                  <div className="flex flex-wrap items-center gap-2">
                    <code>{inc.id}</code>
                    <strong>{inc.component}</strong>
                    <span className="ah-chip ah-chip-muted">{inc.status}</span>
                    {inc.demo ? <TruthChip status="DEMO" /> : null}
                    <span className="ah-muted">{tehranDateTime(inc.time)}</span>
                  </div>
                  <div style={{ fontSize: 15, marginTop: 6 }}>
                    {clamp(inc.errorSignature, 120)}
                  </div>
                  <div style={{ fontSize: 15, marginTop: 4 }}>
                    <span className="ah-muted">تشخیص: {dash(inc.diagnosisNote)}</span>
                    <span className="ah-muted"> · شواهد: </span>
                    {inc.evidencePath ? (
                      <span className="ah-cyan">{inc.evidencePath}</span>
                    ) : (
                      <span className="ah-muted">بدون شواهد</span>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </section>

          <DetailsDrawer open={open} onToggle={() => setOpen((o) => !o)}>
            <div className="flex flex-wrap items-center gap-2" style={{ marginBottom: 12 }}>
              <label className="ah-muted" htmlFor="sd-status">وضعیت</label>
              <select id="sd-status" className="ah-select" value={fStatus} onChange={(e) => setFStatus(e.target.value)}>
                <option value="ALL">همه</option>
                <option value="OPEN">OPEN</option>
                <option value="DIAGNOSED">DIAGNOSED</option>
                <option value="CLOSED">CLOSED</option>
                <option value="UNKNOWN">UNKNOWN</option>
              </select>
            </div>
            <DataTable columns={columns} rows={filtered} rowKey={(r) => r.id} />
            {filtered
              .filter((r) => r.id === openIncident)
              .map((r) => (
                <div key={`detail-${r.id}`} className="ah-drawer" style={{ marginTop: 12 }}>
                  <h3>خط زمانی {r.id}</h3>
                  <ul style={{ fontSize: 15 }}>
                    {r.timeline.length === 0 ? (
                      <li className="ah-muted">—</li>
                    ) : (
                      r.timeline.map((ev, idx) => (
                        <li key={`${r.id}-tl-${idx}`}>
                          {tehranDateTime(ev.time)} · {ev.event} · <span className="ah-muted">{dash(ev.source)}</span>
                        </li>
                      ))
                    )}
                  </ul>
                  <h3 style={{ marginTop: 12 }}>گزیده گزارش (redacted)</h3>
                  {r.logExcerpt.length === 0 ? (
                    <p className="ah-muted">—</p>
                  ) : (
                    r.logExcerpt.map((line, idx) => (
                      <p key={`${r.id}-log-${idx}`} style={{ fontSize: 13 }} className="ah-muted">
                        {clamp(line, 200)}
                      </p>
                    ))
                  )}
                  <p className="ah-muted" style={{ fontSize: 13, marginTop: 8 }}>
                    سن از آخرین خوانش: {ageLabel(r.time, data?.generatedAt ?? null)}
                  </p>
                </div>
              ))}
          </DetailsDrawer>
        </div>
      )}
    </Shell>
  );
}
