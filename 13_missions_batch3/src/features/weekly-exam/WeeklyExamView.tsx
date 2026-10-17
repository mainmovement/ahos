// FILE: 13_missions_batch3/src/features/weekly-exam/WeeklyExamView.tsx
"use client";
import { useState } from "react";
import { Shell } from "@/components/shell/Shell";
import { StateBlock } from "@/components/truth/StateBlock";
import { DetailsDrawer } from "@/components/truth/DetailsDrawer";
import { DataTable, type Column } from "@/components/truth/DataTable";
import { TruthChip } from "@/components/truth/TruthChip";
import { getSnapshot } from "@/adapters/weekly-exam";
import { useSnapshot } from "@/lib/useSnapshot";
import { useFlags } from "@/lib/useFlags";
import { nonDemo, resolveViewState, sampleAdequate, truthFromSnapshot } from "@/lib/stats";
import { dash, faNum } from "@/lib/format";
import type { ExamState, TriState, WeeklyExamItem, WeeklyExamRun } from "@/contract/types";

const TRI_LABEL: Record<TriState, string> = { yes: "بله", no: "خیر", UNKNOWN: "نامشخص" };

/** Neutral state chip — never green, never a pass/fail verdict. */
function ExamStateChip({ state }: { state: ExamState }) {
  const cls =
    state === "NOT_RUN" || state === "UNKNOWN" ? "ah-chip ah-chip-unknown" : "ah-chip ah-chip-info";
  return <span className={cls} data-exam-state={state}>{state}</span>;
}

/** «آزمون هفتگی هوش» (M50) — descriptive only. No ranking, no leaderboard. */
export function WeeklyExamView() {
  const flags = useFlags();
  const { phase, data } = useSnapshot(getSnapshot);
  const [open, setOpen] = useState(false);
  const [fState, setFState] = useState<string>("ALL");

  const runs = data?.runs ?? [];
  const view = resolveViewState(phase, data, runs.length, flags.state);
  const truth = data ? truthFromSnapshot(data, runs) : "UNKNOWN";
  const minSample = data?.minSampleSize ?? 1;
  const counted = nonDemo(runs);

  const recent = [...runs]
    .sort((a, b) => (b.week ?? b.id).localeCompare(a.week ?? a.id))
    .slice(0, 7);
  const lastRun = recent[0] ?? null;

  const filtered = runs.filter((r) => fState === "ALL" || r.state === fState);

  const runColumns: Column<WeeklyExamRun>[] = [
    { key: "id", header: "شناسه", render: (r) => <code>{r.id}</code> },
    { key: "week", header: "هفته (تهران)", render: (r) => dash(r.week) },
    { key: "items", header: "تعداد موارد", render: (r) => (r.itemsCount === null ? "—" : faNum(r.itemsCount)) },
    { key: "answered", header: "پاسخ‌داده", render: (r) => (r.answeredCount === null ? "—" : faNum(r.answeredCount)) },
    { key: "evidence", header: "با شواهد", render: (r) => (r.withEvidenceCount === null ? "—" : faNum(r.withEvidenceCount)) },
    { key: "state", header: "وضعیت", render: (r) => <ExamStateChip state={r.state} /> },
    {
      key: "sample",
      header: "نمونه",
      render: (r) =>
        r.itemsCount === null ? (
          <span className="ah-muted">—</span>
        ) : sampleAdequate(r.itemsCount, minSample) ? (
          <span className="ah-cyan">کافی</span>
        ) : (
          <span className="ah-chip ah-chip-unknown">نمونه ناکافی</span>
        ),
    },
    { key: "summary", header: "خلاصه عددی", render: (r) => dash(r.resultSummary) },
    { key: "demo", header: "DEMO", render: (r) => (r.demo ? <TruthChip status="DEMO" /> : <span className="ah-muted">—</span>) },
  ];

  const itemColumns: Column<WeeklyExamItem>[] = [
    { key: "id", header: "شناسه مورد", render: (r) => <code>{r.id}</code> },
    { key: "topic", header: "موضوع", render: (r) => r.topic },
    { key: "answered", header: "پاسخ", render: (r) => TRI_LABEL[r.answered] },
    { key: "evidence", header: "شواهد", render: (r) => TRI_LABEL[r.evidence] },
    { key: "review", header: "وضعیت بازبینی", render: (r) => dash(r.reviewState) },
    { key: "demo", header: "DEMO", render: (r) => (r.demo ? <TruthChip status="DEMO" /> : <span className="ah-muted">—</span>) },
  ];

  return (
    <Shell
      title="آزمون هفتگی هوش"
      truth={flags.demo ? "DEMO" : truth}
      source={data?.source ?? null}
      lastRead={data?.generatedAt ?? null}
      rowCount={runs.length}
      snapshot={data}
    >
      <p className="ah-honest">آزمون توصیفی است، نه اثبات توانایی</p>

      {view !== "OK" ? (
        <StateBlock state={view} />
      ) : (
        <div className="flex flex-col gap-3">
          {lastRun ? (
            <section className="ah-panel ah-panel-gold">
              <h2>آخرین آزمون</h2>
              <div className="flex flex-wrap items-center gap-2" style={{ marginTop: 8 }}>
                <code>{lastRun.id}</code>
                <span className="ah-chip ah-chip-muted">هفته {dash(lastRun.week)}</span>
                <ExamStateChip state={lastRun.state} />
                {lastRun.demo ? <TruthChip status="DEMO" /> : null}
                {lastRun.itemsCount !== null && !sampleAdequate(lastRun.itemsCount, minSample) ? (
                  <span className="ah-chip ah-chip-unknown">نمونه ناکافی</span>
                ) : null}
              </div>
              <p style={{ marginTop: 8 }}>
                {dash(lastRun.resultSummary)}
                <span className="ah-muted"> · بدون امتیاز و بدون رتبه‌بندی</span>
              </p>
            </section>
          ) : null}

          <section className="ah-panel">
            <h2>اجراهای اخیر (حداکثر ۷ مورد)</h2>
            <ul className="flex flex-col gap-2" style={{ listStyle: "none", margin: 0, padding: 0 }}>
              {recent.map((run) => (
                <li key={run.id} className="ah-panel" style={{ background: "transparent" }}>
                  <div className="flex flex-wrap items-center gap-2">
                    <code>{run.id}</code>
                    <span className="ah-chip ah-chip-muted">هفته {dash(run.week)}</span>
                    <ExamStateChip state={run.state} />
                    {run.demo ? <TruthChip status="DEMO" /> : null}
                    {run.itemsCount !== null && !sampleAdequate(run.itemsCount, minSample) ? (
                      <span className="ah-chip ah-chip-unknown">نمونه ناکافی</span>
                    ) : null}
                  </div>
                  <div style={{ fontSize: 15, marginTop: 6 }}>{dash(run.resultSummary)}</div>
                </li>
              ))}
            </ul>
            <p className="ah-muted" style={{ marginTop: 8, fontSize: 13 }}>
              اجراهای غیر-DEMO در شمارش‌ها: {faNum(counted.length)} · حداقل اندازه نمونه برای توصیف: {faNum(minSample)}
            </p>
          </section>

          <DetailsDrawer open={open} onToggle={() => setOpen((o) => !o)}>
            <div className="flex flex-wrap items-center gap-2" style={{ marginBottom: 12 }}>
              <label className="ah-muted" htmlFor="we-state">وضعیت اجرا</label>
              <select id="we-state" className="ah-select" value={fState} onChange={(e) => setFState(e.target.value)}>
                <option value="ALL">همه</option>
                <option value="SCHEDULED">SCHEDULED</option>
                <option value="RAN">RAN</option>
                <option value="PARTIAL">PARTIAL</option>
                <option value="NOT_RUN">NOT_RUN</option>
                <option value="UNKNOWN">UNKNOWN</option>
              </select>
            </div>
            <DataTable columns={runColumns} rows={filtered} rowKey={(r) => r.id} />
            <h3 style={{ marginTop: 16 }}>موارد آزمون</h3>
            {filtered.map((run) => (
              <div key={`items-${run.id}`} style={{ marginTop: 12 }}>
                <p className="ah-muted" style={{ fontSize: 13 }}>
                  {run.id} · هفته {dash(run.week)}
                </p>
                {run.items.length === 0 ? (
                  <p className="ah-muted">—</p>
                ) : (
                  <DataTable columns={itemColumns} rows={run.items} rowKey={(r) => r.id} />
                )}
              </div>
            ))}
          </DetailsDrawer>
        </div>
      )}
    </Shell>
  );
}
