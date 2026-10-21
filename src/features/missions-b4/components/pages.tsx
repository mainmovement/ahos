import type { ReactNode } from "react";
import { tr } from "@/src/lib/i18n";
import type { ChipStatus } from "@/src/features/trade-venue/logic/model";
import { TruthChip } from "@/src/components/truth/TruthChip";
import { Cell, Details, HighlightList, PageFrame, type FrameProps } from "../../missions-b2/components/PageFrame";
import { freshness, one, parseFlag, parsePageState, tehranStamp, violationOf, type PageState } from "../../missions-b2/lib/model";
import {
  MISSING, buildNewsCenter, buildScienceRadar, buildSelfDebug, buildSkillMarket, buildWeeklyExam, capHighlights, clean,
  debugStatus, examStatus, installChip, radarStatus,
} from "../lib/model";
import { SOAK_RUNLOG_PATH, loadContract, readScienceRadarSoak, readSoakDebug, readWeeklyExamSoak } from "../lib/data.server";
import type { SelfDebugSnapshot } from "../contract/types";

type Params = Record<string, string | string[] | undefined>;
const t = (k: string) => tr("fa", `missionsB4.${k}`);
const tb2 = (k: string) => tr("fa", `missionsB2.${k}`);
const BLOCK: Record<Exclude<PageState, "ready">, ChipStatus> = { empty: "EMPTY", error: "ERROR", unavailable: "UNAVAILABLE", loading: "LOADING", stale: "STALE" };

interface Ctx { state: PageState; forceDemo: boolean; forceViolation: boolean; details: boolean; nowMs: number }
const ctxOf = (p: Params): Ctx => ({ state: parsePageState(p.state), forceDemo: parseFlag(p.demo), forceViolation: parseFlag(p.violation), details: parseFlag(p.details), nowMs: Date.now() });

interface Base { mode: string; real: boolean; generatedAt: string | null; demo: boolean; source: string; status: ChipStatus }

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
const Kpi = ({ k, v }: { k: string; v: string | number | null }) => (
  <div className="mb-kpi"><span className="mb-kpi__k">{k}</span><span className="mb-kpi__v tv-num">{v === null ? MISSING : v}</span></div>
);
const when = (iso: string | null) => (iso ? tehranStamp(iso) : null);

function demoBase(s: { executionMode: string; realTrading: boolean; generatedAt: string | null; source: string | null }): Base {
  return { mode: s.executionMode, real: s.realTrading, generatedAt: s.generatedAt, demo: true, source: `${s.source ?? "DEMO"} (DEMO)`, status: "DEMO" };
}

/* ------------------------------------------------------------ science radar */
export async function ScienceRadarPage({ params }: { params: Params }) {
  const c = ctxOf(params);
  const real = c.forceDemo ? null : readScienceRadarSoak();
  const snap = real ?? loadContract()?.scienceRadar ?? null;
  const demoMode = !real;
  const v = snap ? buildScienceRadar(snap, demoMode) : null;
  const cap = v ? capHighlights(v.highlights) : { shown: [], hidden: 0 };
  const base: Base | null = snap
    ? real
      ? { mode: snap.executionMode, real: snap.realTrading, generatedAt: snap.generatedAt, demo: false, source: snap.source ?? "M13_SOAK", status: "PARTIAL" }
      : demoBase(snap)
    : null;
  const f = frame("science-radar", c, base, {
    empty: !!v && v.rows.length === 0,
    emptyBody: tb2("ui.noData"),
    note: real ? "شاهد قیمت M13 (نه خبرنگاری زنده)" : null,
  });
  return (
    <PageFrame {...f}>
      {v && snap ? (
        <>
          <p className="mb-note">{t("scienceRadar.note")}</p>
          <HighlightList items={cap.shown} hidden={cap.hidden} empty={tb2("ui.noData")} />
          <Details open={c.details} meta={t("scienceRadar.meta")}>
            <Table heads={[t("col.title"), t("col.sourceType"), t("col.topic"), t("col.found"), t("col.relevance"), t("col.status"), t("col.sourceText")]}>
              {snap.items.map((r) => (
                <tr key={r.id}>
                  <td dir="auto">{clean(r.title)}</td><td dir="ltr">{r.sourceType}</td><td dir="auto"><Cell v={r.topic} /></td>
                  <td dir="ltr" className="tv-mono"><Cell v={when(r.foundAt)} /></td><td dir="auto"><Cell v={clean(r.relevanceNote)} /></td>
                  <td><TruthChip status={radarStatus(r.status, demoMode)} size="sm" /> <span dir="ltr" className="tv-faint">{r.status}</span></td>
                  <td dir="auto"><Cell v={clean(r.sourceText)} /></td>
                </tr>
              ))}
            </Table>
          </Details>
        </>
      ) : null}
    </PageFrame>
  );
}

/* --------------------------------------------------------------- self debug */
export async function SelfDebugPage({ params }: { params: Params }) {
  const c = ctxOf(params);
  const real = c.forceDemo ? null : readSoakDebug();
  const demoSnap = loadContract()?.selfDebug ?? null;
  let snap: SelfDebugSnapshot | null = null;
  let base: Base | null = null;
  if (real) {
    const mode = real.paperOnly === true ? "PAPER_ONLY" : "UNKNOWN";
    const gen = real.incidents.lastTs ?? null;
    snap = { kind: "selfDebug", executionMode: "PAPER_ONLY", realTrading: false, source: "soak_runlog.jsonl", generatedAt: gen, demo: false, incidents: real.incidents.incidents };
    base = { mode, real: false, generatedAt: gen, demo: false, source: `soak_runlog.jsonl (${t("ui.realFile")})`, status: freshness("file", gen, c.nowMs) };
  } else if (demoSnap) {
    snap = demoSnap;
    base = demoBase(demoSnap);
  }
  const isDemo = !!base?.demo;
  const v = snap ? buildSelfDebug(snap, isDemo) : null;
  const cap = v ? capHighlights(v.highlights) : { shown: [], hidden: 0 };
  const f = frame("self-debug", c, base, { empty: !!v && v.rows.length === 0, emptyBody: t("selfDebug.noIncident"), note: real ? t("selfDebug.realNote") : null });
  return (
    <PageFrame {...f}>
      {v && snap ? (
        <>
          <p className="mb-note">{t("selfDebug.readOnly")}</p>
          {v.counts ? (
            <div className="mb-kpis" data-mb-counts="">
              <Kpi k={t("selfDebug.total")} v={v.counts.total} /><Kpi k={t("selfDebug.open")} v={v.counts.open} />
              <Kpi k={t("selfDebug.diagnosed")} v={v.counts.diagnosed} /><Kpi k={t("selfDebug.unknown")} v={v.counts.unknown} />
            </div>
          ) : null}
          <HighlightList items={cap.shown} hidden={cap.hidden} empty={tb2("ui.noData")} />
          <Details open={c.details} meta={t("selfDebug.meta")}>
            <Table heads={["ID", t("col.time"), t("col.component"), t("col.signature"), t("col.diagnosis"), t("col.status"), t("col.evidence")]}>
              {snap.incidents.map((r) => (
                <tr key={r.id}>
                  <td dir="ltr" className="tv-mono">{r.id}</td><td dir="ltr" className="tv-mono"><Cell v={when(r.time)} /></td><td dir="ltr">{r.component}</td>
                  <td dir="auto">{clean(r.errorSignature, 120)}</td><td dir="auto"><Cell v={clean(r.diagnosisNote)} /></td>
                  <td><TruthChip status={debugStatus(r.status, isDemo)} size="sm" /> <span dir="ltr" className="tv-faint">{r.status}</span></td>
                  <td dir="ltr" className="tv-mono"><Cell v={r.evidencePath} /></td>
                </tr>
              ))}
            </Table>
            {snap.incidents.map((r) => (
              <div key={`tl-${r.id}`} className="mb-sec">
                <h3 className="mb-h2" dir="ltr">{r.id} - {t("selfDebug.timeline")}</h3>
                {r.timeline.length === 0 ? <p className="mb-empty">{MISSING}</p> : (
                  <Table heads={[t("col.time"), t("col.event"), t("col.source")]}>
                    {r.timeline.map((e, i) => <tr key={i}><td dir="ltr" className="tv-mono"><Cell v={when(e.time)} /></td><td dir="auto">{clean(e.event)}</td><td dir="ltr"><Cell v={e.source} /></td></tr>)}
                  </Table>
                )}
                {r.logExcerpt.length > 0 ? <pre className="tv-mono mb-hl__detail" dir="ltr">{r.logExcerpt.map((l) => clean(l, 200)).join("\n")}</pre> : null}
              </div>
            ))}
            {real ? <p className="mb-hl__detail" dir="ltr">{SOAK_RUNLOG_PATH.replace(/[A-Za-z]:\\Users\\[^\\]+/i, "<user>")} | rows={real.incidents.rows} skipped={real.incidents.skipped}</p> : null}
          </Details>
        </>
      ) : null}
    </PageFrame>
  );
}

/* -------------------------------------------------------------- weekly exam */
export async function WeeklyExamPage({ params }: { params: Params }) {
  const c = ctxOf(params);
  const real = c.forceDemo ? null : readWeeklyExamSoak();
  const snap = real ?? loadContract()?.weeklyExam ?? null;
  const demoMode = !real;
  const v = snap ? buildWeeklyExam(snap, demoMode) : null;
  const cap = v ? capHighlights(v.highlights) : { shown: [], hidden: 0 };
  const base: Base | null = snap
    ? real
      ? { mode: snap.executionMode, real: snap.realTrading, generatedAt: snap.generatedAt, demo: false, source: snap.source ?? "M13_SOAK tier_gate", status: "PARTIAL" }
      : demoBase(snap)
    : null;
  const f = frame("weekly-exam", c, base, { empty: !!v && v.runs.length === 0, emptyBody: tb2("ui.noData") });
  return (
    <PageFrame {...f}>
      {v && snap ? (
        <>
          <p className="mb-note">{t("weeklyExam.neutral")}</p>
          <p className="mb-note" data-mb-sample="">{v.adequate ? t("weeklyExam.sampleOk") : `${t("weeklyExam.sampleLow")} (${t("weeklyExam.min")}: ${v.minSampleSize})`}</p>
          <HighlightList items={cap.shown} hidden={cap.hidden} empty={tb2("ui.noData")} />
          <Details open={c.details} meta={t("weeklyExam.meta")}>
            <Table heads={[t("col.week"), t("col.items"), t("col.answered"), t("col.withEvidence"), t("col.summary"), t("col.status")]}>
              {v.runs.map((r) => (
                <tr key={r.id}>
                  <td dir="ltr" className="tv-mono"><Cell v={r.week} /></td><td className="tv-num"><Cell v={r.itemsCount} /></td><td className="tv-num"><Cell v={r.answeredCount} /></td>
                  <td className="tv-num"><Cell v={r.withEvidenceCount} /></td><td dir="auto"><Cell v={clean(r.resultSummary)} /></td>
                  <td><TruthChip status={examStatus(r.state, demoMode)} size="sm" /> <span dir="ltr" className="tv-faint">{r.state}</span></td>
                </tr>
              ))}
            </Table>
            {v.runs.filter((r) => r.items.length > 0).map((r) => (
              <div key={`it-${r.id}`} className="mb-sec">
                <h3 className="mb-h2" dir="ltr">{r.week ?? r.id}</h3>
                <Table heads={[t("col.topic"), t("col.answeredQ"), t("col.evidence"), t("col.review")]}>
                  {r.items.map((i) => <tr key={i.id}><td dir="auto">{clean(i.topic)}</td><td dir="ltr">{i.answered}</td><td dir="ltr">{i.evidence}</td><td dir="auto"><Cell v={i.reviewState} /></td></tr>)}
                </Table>
              </div>
            ))}
          </Details>
        </>
      ) : null}
    </PageFrame>
  );
}

/* ------------------------------------------------------------- skill market */
export async function SkillMarketPage({ params }: { params: Params }) {
  const c = ctxOf(params);
  const snap = loadContract()?.skillMarket ?? null;
  const v = snap ? buildSkillMarket(snap, true) : null;
  const cap = v ? capHighlights(v.highlights) : { shown: [], hidden: 0 };
  const f = frame("skill-market", c, snap ? demoBase(snap) : null, { empty: !!v && v.rows.length === 0, emptyBody: tb2("ui.noData") });
  return (
    <PageFrame {...f}>
      {v && snap ? (
        <>
          <p className="mb-note">{t("skillMarket.displayOnly")}</p>
          <HighlightList items={cap.shown} hidden={cap.hidden} empty={tb2("ui.noData")} />
          <Details open={c.details} meta={t("skillMarket.meta")}>
            <Table heads={[t("col.name"), t("col.kind"), t("col.version"), t("col.source"), t("col.install"), t("col.permissions"), t("col.review"), t("col.reason")]}>
              {v.rows.map(({ e, review }) => (
                <tr key={e.id}>
                  <td dir="auto">{clean(e.name, 80)}</td><td dir="ltr">{e.kind}</td><td dir="ltr" className="tv-mono"><Cell v={e.version} /></td><td dir="auto"><Cell v={clean(e.source)} /></td>
                  <td><TruthChip status={installChip(e.installState, true)} size="sm" /> <span dir="ltr" className="tv-faint">{e.installState}</span></td>
                  <td dir="auto"><Cell v={e.permissions.length ? e.permissions.map((p) => clean(p, 60)).join("، ") : null} /></td>
                  <td dir="ltr">{review.state}{review.missingReason ? <span className="tv-faint"> ({t("skillMarket.noReason")})</span> : null}</td>
                  <td dir="auto"><Cell v={clean(e.reason)} /></td>
                </tr>
              ))}
            </Table>
          </Details>
        </>
      ) : null}
    </PageFrame>
  );
}

/* -------------------------------------------------------------- news center */
export async function NewsCenterPage({ params }: { params: Params }) {
  const c = ctxOf(params);
  const snap = loadContract()?.newsCenter ?? null;
  const v = snap ? buildNewsCenter(snap, true) : null;
  const cap = v ? capHighlights(v.highlights) : { shown: [], hidden: 0 };
  const f = frame("news-center", c, snap ? demoBase(snap) : null, { empty: !!v && v.rows.length === 0, emptyBody: tb2("ui.noData") });
  return (
    <PageFrame {...f}>
      {v && snap ? (
        <>
          <p className="mb-note">{t("newsCenter.note")} ({snap.staleAfterMinutes} {t("newsCenter.minutes")})</p>
          <HighlightList items={cap.shown} hidden={cap.hidden} empty={tb2("ui.noData")} />
          <Details open={c.details} meta={t("newsCenter.meta")}>
            <Table heads={[t("col.time"), t("col.source"), t("col.topic"), t("col.summary"), t("col.reliability"), t("col.freshness")]}>
              {v.rows.map(({ n, fresh }) => (
                <tr key={n.id}>
                  <td dir="ltr" className="tv-mono"><Cell v={when(n.time)} /></td><td dir="auto"><Cell v={n.sourceName} /></td><td dir="ltr">{n.topic}</td>
                  <td dir="auto">{clean(n.summary, 120)}</td><td dir="auto"><Cell v={n.reliability} /></td>
                  <td><TruthChip status={fresh as ChipStatus} size="sm" /></td>
                </tr>
              ))}
            </Table>
          </Details>
        </>
      ) : null}
    </PageFrame>
  );
}
