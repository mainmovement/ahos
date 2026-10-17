import type { ReactNode } from "react";
import { tr } from "@/src/lib/i18n";
import type { ChipStatus } from "@/src/features/trade-venue/logic/model";
import { TruthChip } from "@/src/components/truth/TruthChip";
import { Cell, Details, HighlightList, PageFrame, type FrameProps } from "../../missions-b2/components/PageFrame";
import { parseFlag, parsePageState, tehranStamp, violationOf, type PageState } from "../../missions-b2/lib/model";
import {
  EXAM_MIN_ITEMS, EXAM_SCHEDULE, MISSING, NIGHT_STALE_HOURS, REGISTERED, buildAgents, buildCapability, buildNightly, buildUniversity, capHighlights, clean,
  examResult, freshOf, needsOwner, num, presenceChip, proposalStatus, verdictStatus,
} from "../lib/model";
import { REGISTRY_PATH, SOAK_DIR, loadContract, readAgentRegistry, readCapabilityLab, readNightly, universityRealSourceExists } from "../lib/data.server";
import { STAGES, type SectionMeta } from "../contract/types";

type Params = Record<string, string | string[] | undefined>;
const t = (k: string) => tr("fa", `missionsB5.${k}`);
const tb2 = (k: string) => tr("fa", `missionsB2.${k}`);
const BLOCK: Record<Exclude<PageState, "ready">, ChipStatus> = { empty: "EMPTY", error: "ERROR", unavailable: "UNAVAILABLE", loading: "LOADING", stale: "STALE" };

interface Ctx { state: PageState; forceDemo: boolean; forceViolation: boolean; details: boolean; nowMs: number }
const ctxOf = (p: Params): Ctx => ({ state: parsePageState(p.state), forceDemo: parseFlag(p.demo), forceViolation: parseFlag(p.violation), details: parseFlag(p.details), nowMs: Date.now() });

interface Base { mode: string; real: boolean; generatedAt: string | null; demo: boolean; source: string; status: ChipStatus }
const baseOf = (s: SectionMeta, status: ChipStatus, label?: string): Base => ({
  mode: s.executionMode, real: s.realTrading, generatedAt: s.generatedAt, demo: s.demo, status,
  source: s.demo ? `${s.source ?? "DEMO"} (DEMO)` : `${label ?? s.source ?? MISSING} (${t("ui.realFile")})`,
});

function frame(pageId: string, c: Ctx, b: Base | null, extra: { empty: boolean; emptyBody?: string; note?: string | null }): Omit<FrameProps, "children"> {
  const violation = c.forceViolation ? violationOf("LIVE", true) : b ? violationOf(b.mode, b.real) : null;
  let block: FrameProps["block"] = null;
  let status: ChipStatus = b?.status ?? "UNAVAILABLE";
  if (c.state !== "ready") { block = { state: BLOCK[c.state] }; status = BLOCK[c.state]; }
  else if (!b) block = { state: "UNAVAILABLE", bodyFa: tb2("ui.noSource") };
  else if (extra.empty) { block = { state: "EMPTY", bodyFa: extra.emptyBody }; status = "EMPTY"; }
  return {
    pageId, title: t(`page.${pageId}.title`), subtitle: t(`page.${pageId}.sub`), status, demo: !!b?.demo, sourceText: b?.source ?? MISSING,
    generatedAt: b?.generatedAt ?? null, violation, block, note: extra.note ?? (b?.demo ? tb2("ui.demoNote") : null),
  };
}

function Table({ heads, children }: { heads: string[]; children: ReactNode }) {
  return (
    <div className="mb-tablewrap">
      <table className="tv-table tv-table--dense">
        <thead><tr>{heads.map((h) => <th key={h} scope="col">{h}</th>)}</tr></thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}
const Kpi = ({ k, v, sm }: { k: string; v: string | number | null; sm?: boolean }) => (
  <div className="mb-kpi"><span className="mb-kpi__k">{k}</span><span className={`mb-kpi__v tv-num${sm ? " mb-kpi__v--sm" : ""}`}>{v === null ? MISSING : v}</span></div>
);
const when = (iso: string | null) => (iso ? tehranStamp(iso) : null);
const Verdict = ({ token, status }: { token: string | null; status: ChipStatus }) => (
  <><TruthChip status={status} size="sm" /> <span dir="ltr" className="tv-faint">{token ?? MISSING}</span></>
);

/* ----------------------------------------------------------- nightly report */
export async function NightlyReportPage({ params }: { params: Params }) {
  const c = ctxOf(params);
  const real = c.forceDemo ? null : readNightly();
  const snap = real ?? loadContract()?.nightlyReport ?? null;
  const v = snap ? buildNightly(snap.nights, c.nowMs, snap.demo) : null;
  const status: ChipStatus = !snap ? "UNAVAILABLE" : snap.demo ? "DEMO" : v!.latestFresh;
  const cap = v ? capHighlights(v.highlights) : { shown: [], hidden: 0 };
  const f = frame("nightly-report", c, snap ? baseOf(snap, status, "M13_SOAK") : null, { empty: !!v && v.rows.length === 0, emptyBody: tb2("ui.noData"), note: real ? t("nightlyReport.realNote") : null });
  const L = v?.latest ?? null;
  const lf = L ? freshOf(L.timestamp, c.nowMs) : "UNKNOWN";
  return (
    <PageFrame {...f}>
      {v && snap ? (
        <>
          <p className="mb-note">{t("nightlyReport.readOnly")} ({t("nightlyReport.stale")} {NIGHT_STALE_HOURS}h)</p>
          {L ? (
            <div className="mb-kpis" data-mb-counts="">
              <Kpi k={t("nightlyReport.latest")} v={L.day} sm />
              <div className="mb-kpi"><span className="mb-kpi__k">{t("nightlyReport.judge")}</span><span className="mb-kpi__v mb-kpi__v--sm"><Verdict token={L.judge} status={verdictStatus(L.judge, lf, snap.demo || L.demo)} /></span></div>
              <div className="mb-kpi"><span className="mb-kpi__k">{t("nightlyReport.reconcile")}</span><span className="mb-kpi__v mb-kpi__v--sm"><Verdict token={L.reconcile} status={verdictStatus(L.reconcile, lf, snap.demo || L.demo)} /></span></div>
              <Kpi k={t("nightlyReport.tier")} v={L.tier === null ? null : `T${L.tier}`} />
              <Kpi k={t("nightlyReport.closed")} v={num(L.closed)} />
              <Kpi k={t("nightlyReport.pnl")} v={L.pnl === null ? null : `${L.pnl} PAPER`} sm />
              <Kpi k={t("ui.age")} v={v.latestAge === null ? null : `${v.latestAge.toFixed(1)}h`} />
              {v.counts ? <Kpi k={t("nightlyReport.nights")} v={v.counts.nights} /> : null}
            </div>
          ) : null}
          <p className="mb-note">{t("nightlyReport.tierNote")}</p>
          <HighlightList items={cap.shown} hidden={cap.hidden} empty={tb2("ui.noData")} />
          <Details open={c.details} meta={t("nightlyReport.meta")}>
            <Table heads={[t("col.day"), t("col.time"), t("col.entries"), t("col.closed"), t("col.winsLosses"), t("col.pnl"), t("col.judge"), t("col.reconcile"), t("col.tier"), t("col.criteria"), t("col.signed")]}>
              {v.rows.map((n) => {
                const nf = freshOf(n.timestamp, c.nowMs);
                const d = snap.demo || n.demo;
                return (
                  <tr key={n.id}>
                    <td dir="ltr" className="tv-mono"><Cell v={n.day} /></td><td dir="ltr" className="tv-mono"><Cell v={when(n.timestamp)} /></td>
                    <td dir="ltr"><Cell v={n.entries} /></td><td dir="ltr"><Cell v={n.closed} /></td>
                    <td dir="ltr"><Cell v={n.wins === null || n.losses === null ? null : `${n.wins} / ${n.losses}`} /></td><td dir="ltr"><Cell v={n.pnl} /></td>
                    <td><Verdict token={n.judge} status={verdictStatus(n.judge, nf, d)} /></td><td><Verdict token={n.reconcile} status={verdictStatus(n.reconcile, nf, d)} /></td>
                    <td dir="ltr"><Cell v={n.tier === null ? null : `T${n.tier}`} /></td><td dir="ltr"><Cell v={n.criteria} /></td>
                    <td dir="ltr"><Cell v={n.signed === null ? null : n.signed ? "signed" : "unsigned"} /></td>
                  </tr>
                );
              })}
            </Table>
            {real ? <p className="mb-hl__detail" dir="ltr">{SOAK_DIR.replace(/[A-Za-z]:\\Users\\[^\\]+/i, "<user>")} | files=*_digest.json,*_judge.md,*_reconcile.md,*_tier_gate.md</p> : null}
          </Details>
        </>
      ) : null}
    </PageFrame>
  );
}

/* --------------------------------------------------------------- university */
export async function UniversityPage({ params }: { params: Params }) {
  const c = ctxOf(params);
  const snap = loadContract()?.university ?? null; // no real parser: config/university/sources.yaml absent on this machine
  const v = snap ? buildUniversity(snap, true) : null;
  const cap = v ? capHighlights(v.highlights) : { shown: [], hidden: 0 };
  const f = frame("university", c, snap ? baseOf(snap, "DEMO") : null, {
    empty: !!snap && snap.sources.length + snap.exams.length + snap.bank.length === 0, emptyBody: tb2("ui.noData"),
    note: universityRealSourceExists() ? t("university.fileNoParser") : t("university.noRealSource"),
  });
  return (
    <PageFrame {...f}>
      {snap && v ? (
        <>
          <div className="mb-kpis" data-mb-counts="">
            <Kpi k={t("university.sources")} v={v.counts ? v.counts.sources : null} />
            <Kpi k={t("university.exams")} v={v.counts ? v.counts.exams : null} />
            <Kpi k={t("university.schedule")} v={EXAM_SCHEDULE} sm />
          </div>
          <p className="mb-note">{t("university.confidential")} {t("university.sampleFloor")} <span dir="ltr" className="tv-mono">{EXAM_MIN_ITEMS}</span></p>
          <HighlightList items={cap.shown} hidden={cap.hidden} empty={tb2("ui.noData")} />
          <Details open={c.details} meta={t("university.meta")}>
            <h3 className="mb-h2">{t("university.hSources")}</h3>
            <Table heads={["ID", t("col.name"), t("col.domain"), t("col.category"), t("col.access"), t("col.licence"), "tos_ok", t("col.authority"), t("col.recency"), t("col.trackRecord"), t("col.citations"), t("col.score"), t("col.status")]}>
              {snap.sources.map((s) => (
                <tr key={s.id}>
                  <td dir="ltr" className="tv-mono">{s.id}</td><td dir="auto">{clean(s.name, 80)}</td><td dir="auto">{s.domain}</td><td dir="auto">{s.category}</td>
                  <td dir="ltr"><Cell v={s.access} /></td><td dir="ltr"><Cell v={s.licence} /></td><td dir="ltr"><Cell v={s.tosOk === null ? null : String(s.tosOk)} /></td>
                  <td dir="ltr"><Cell v={s.authority} /></td><td dir="ltr"><Cell v={s.recency} /></td><td dir="ltr"><Cell v={s.trackRecord} /></td><td dir="ltr"><Cell v={s.citations} /></td><td dir="ltr"><Cell v={s.score} /></td>
                  <td><TruthChip status="DEMO" size="sm" /></td>
                </tr>
              ))}
            </Table>
            <h3 className="mb-h2">{t("university.hExams")}</h3>
            <Table heads={[t("col.agent"), t("col.week"), t("col.score"), t("col.items"), "CI", t("col.hash"), t("col.retests"), t("col.status")]}>
              {snap.exams.map((e, i) => {
                const r = examResult(e);
                return (
                  <tr key={`${e.agent}-${i}`}>
                    <td dir="ltr" className="tv-mono">{e.agent}</td><td dir="ltr"><Cell v={e.week} /></td>
                    <td dir="auto">{r.sufficient ? <span dir="ltr" className="tv-num">{r.label}</span> : <span className="tv-faint">{t("university.insufficient")}</span>}</td>
                    <td dir="ltr"><Cell v={e.items} /></td><td dir="ltr"><Cell v={e.ci ? `${e.ci[0]} - ${e.ci[1]}` : null} /></td><td dir="ltr" className="tv-mono"><Cell v={e.hash} /></td>
                    <td dir="ltr"><Cell v={e.retests === null ? null : `${e.retests} / 3`} /></td><td><TruthChip status="DEMO" size="sm" /></td>
                  </tr>
                );
              })}
            </Table>
            <h3 className="mb-h2">{t("university.hBank")}</h3>
            <Table heads={[t("col.domain"), t("col.skill"), t("col.count"), t("col.status")]}>
              {snap.bank.map((b, i) => <tr key={`${b.domain}-${i}`}><td dir="auto">{b.domain}</td><td dir="auto">{b.skill}</td><td dir="ltr"><Cell v={b.count} /></td><td><TruthChip status="DEMO" size="sm" /></td></tr>)}
            </Table>
          </Details>
        </>
      ) : null}
    </PageFrame>
  );
}

/* ----------------------------------------------------------- capability lab */
function Spark({ values, label }: { values: number[]; label: string }) {
  if (values.length < 2) return null;
  const lo = Math.min(...values), hi = Math.max(...values), span = hi - lo || 1;
  const pts = values.map((x, i) => `${(i * 220) / (values.length - 1) + 4},${44 - ((x - lo) / span) * 38}`).join(" ");
  return <svg viewBox="0 0 228 48" width="228" height="48" role="img" aria-label={label}><polyline points={pts} fill="none" stroke="currentColor" strokeWidth="2" /></svg>;
}
export async function CapabilityLabPage({ params }: { params: Params }) {
  const c = ctxOf(params);
  const real = c.forceDemo ? null : readCapabilityLab();
  const snap = real ?? loadContract()?.capabilityLab ?? null;
  const v = snap ? buildCapability(snap, snap.demo) : null;
  const status: ChipStatus = !snap ? "UNAVAILABLE" : snap.demo ? "DEMO" : freshOf(snap.generatedAt, c.nowMs);
  const cap = v ? capHighlights(v.highlights) : { shown: [], hidden: 0 };
  const f = frame("capability-lab", c, snap ? baseOf(snap, status, "proposals/ + reports/benchmark_run_*") : null, {
    empty: !!snap && snap.points.length + snap.proposals.length === 0, emptyBody: tb2("ui.noData"), note: real ? t("capabilityLab.realNote") : null,
  });
  const stages = snap ? [...STAGES, ...(snap.proposals.some((p) => p.stage === "UNKNOWN") ? (["UNKNOWN"] as const) : [])] : [];
  return (
    <PageFrame {...f}>
      {snap && v ? (
        <>
          <div className="mb-kpis" data-mb-counts="">
            <Kpi k={t("capabilityLab.measurements")} v={v.counts ? v.counts.measurements : null} />
            <Kpi k={t("capabilityLab.proposals")} v={v.counts ? v.counts.proposals : null} />
            <Kpi k={t("capabilityLab.ownerGate")} v={v.counts ? v.counts.ownerGate : null} />
          </div>
          <p className="mb-note">{t("capabilityLab.repro")}</p>
          <HighlightList items={cap.shown} hidden={cap.hidden} empty={tb2("ui.noData")} />
          <Details open={c.details} meta={t("capabilityLab.meta")}>
            <h3 className="mb-h2">{t("capabilityLab.hTrend")}</h3>
            {v.lines.length === 0 ? <p className="mb-empty">{t("capabilityLab.noMeasure")}</p> : (
              <Table heads={[t("col.capability"), t("col.time"), t("col.value"), t("col.seed"), t("col.items"), t("col.delta"), t("col.trend"), t("col.status")]}>
                {v.lines.map((l) => {
                  const last = l.rows.at(-1);
                  const allDemo = snap.demo || l.rows.every((r) => r.demo);
                  return (
                    <tr key={l.name}>
                      <td dir="auto">{l.name}</td><td dir="ltr" className="tv-mono"><Cell v={when(last?.timestamp ?? null)} /></td>
                      <td dir="ltr"><Cell v={last?.value === null || last?.value === undefined ? null : `${last.value}${l.unit ? ` ${l.unit}` : ""}`} /></td>
                      <td dir="ltr"><Cell v={last?.seed ?? null} /></td><td dir="ltr"><Cell v={last?.items ?? null} /></td>
                      <td dir="ltr"><Cell v={l.delta} /></td>
                      <td dir="ltr"><Spark values={l.rows.map((r) => r.value).filter((x): x is number => x !== null)} label={l.name} /></td>
                      <td><TruthChip status={allDemo ? "DEMO" : status === "LIVE" ? "PARTIAL" : status} size="sm" /></td>
                    </tr>
                  );
                })}
              </Table>
            )}
            <h3 className="mb-h2">{t("capabilityLab.hPipeline")}</h3>
            <Table heads={[t("col.stage"), t("col.proposals")]}>
              {stages.map((s) => (
                <tr key={s}><td dir="ltr" className="tv-mono">{s}</td><td dir="ltr"><Cell v={snap.proposals.filter((p) => p.stage === s).map((p) => p.id).join(", ")} /></td></tr>
              ))}
            </Table>
            <Table heads={["ID", t("col.stage"), t("col.scope"), t("col.title"), t("col.redteam"), t("col.owner"), t("col.created"), t("col.status")]}>
              {snap.proposals.map((p) => (
                <tr key={p.id}>
                  <td dir="ltr" className="tv-mono">{p.id}</td><td dir="ltr">{p.stage}</td><td dir="ltr">{p.scope}</td><td dir="auto">{clean(p.title, 200)}</td>
                  <td dir="ltr"><Cell v={p.redteam} /></td><td dir="auto">{needsOwner(p) ? t("capabilityLab.needsOwner") : MISSING}</td>
                  <td dir="ltr" className="tv-mono"><Cell v={when(p.createdAt)} /></td>
                  <td><TruthChip status={proposalStatus(p, snap.demo || p.demo)} size="sm" /></td>
                </tr>
              ))}
            </Table>
          </Details>
        </>
      ) : null}
    </PageFrame>
  );
}

/* ------------------------------------------------------------- agent center */
export async function AgentCenterPage({ params }: { params: Params }) {
  const c = ctxOf(params);
  const real = c.forceDemo ? null : readAgentRegistry();
  const snap = real ?? loadContract()?.agentCenter ?? null;
  const v = snap ? buildAgents(snap.agents, c.nowMs, snap.demo) : null;
  const status: ChipStatus = !snap ? "UNAVAILABLE" : snap.demo ? "DEMO" : "PARTIAL"; // registered, presence not proven
  const cap = v ? capHighlights(v.highlights) : { shown: [], hidden: 0 };
  const f = frame("agent-center", c, snap ? baseOf(snap, status, "config/agent_registry.yaml") : null, { empty: !!v && v.rows.length === 0, emptyBody: tb2("ui.noData"), note: real ? t("agentCenter.realNote") : null });
  return (
    <PageFrame {...f}>
      {snap && v ? (
        <>
          <p className="mb-note">{t("agentCenter.presenceRule")}</p>
          {v.counts ? (
            <div className="mb-kpis" data-mb-counts="">
              <Kpi k={t("agentCenter.registered")} v={v.counts.registered} /><Kpi k={t("agentCenter.online")} v={v.counts.online} />
              <Kpi k={t("agentCenter.unknown")} v={v.counts.unknown} /><Kpi k="EXISTS" v={v.counts.exists} />
              <Kpi k="PARTIAL" v={v.counts.partial} /><Kpi k="PLANNED" v={v.counts.planned} /><Kpi k="MISSING" v={v.counts.missing} />
            </div>
          ) : null}
          <HighlightList items={cap.shown} hidden={cap.hidden} empty={tb2("ui.noData")} />
          <Details open={c.details} meta={t("agentCenter.meta")}>
            <Table heads={["ID", t("col.name"), t("col.registration"), t("col.registryStatus"), t("col.lane"), t("col.criticality"), t("col.runtimeFlag"), t("col.presence"), t("col.heartbeat")]}>
              {v.rows.map(({ a, presence }) => (
                <tr key={a.id}>
                  <td dir="ltr" className="tv-mono">{a.id}</td><td dir="auto">{clean(a.name, 80)}</td><td dir="ltr">{REGISTERED}</td>
                  <td dir="ltr"><Cell v={a.regStatus} /></td><td dir="ltr"><Cell v={a.lane} /></td><td dir="ltr"><Cell v={a.criticality} /></td>
                  <td dir="ltr"><Cell v={a.liveFlag === null ? null : a.liveFlag ? "live=true (declared)" : "live=false"} /></td>
                  <td><TruthChip status={presenceChip(presence, snap.demo || a.demo)} size="sm" /> <span dir="ltr" className="tv-faint">{presence}</span></td>
                  <td dir="ltr" className="tv-mono"><Cell v={when(a.heartbeat)} /></td>
                </tr>
              ))}
            </Table>
            {real ? <p className="mb-hl__detail" dir="ltr">{REGISTRY_PATH.replace(/[A-Za-z]:\\Users\\[^\\]+/i, "<user>")}</p> : null}
          </Details>
        </>
      ) : null}
    </PageFrame>
  );
}
