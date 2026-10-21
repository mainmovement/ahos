import { tr } from "@/src/lib/i18n";
import type { ChipStatus } from "@/src/features/trade-venue/logic/model";
import { TruthChip } from "@/src/components/truth/TruthChip";
import { Cell, Details, HighlightList, PageFrame, type FrameProps } from "./PageFrame";
import {
  MISSING, buildMessageHub, buildMissionMap, buildResearch, buildSelfEval, capHighlights, demoize, formatNum, freshness,
  ideaFromContract, ideaHighlights, ideasFromShelfFile, one, parseFlag, parsePageState, parsePeriod, redact, tehranStamp,
  violationOf, ageHours, bridgeStatus, deliveryStatus, type Highlight, type IdeaRow, type PageState,
} from "../lib/model";
import { IDEA_SHELF_PATH, MISSIONS_STATUS_PATH, loadContract, readIdeaShelf, readMessageHub, readMissionsStatus, readResearchReplay, readSelfEvaluation } from "../lib/data.server";

type Params = Record<string, string | string[] | undefined>;
const t = (k: string) => tr("fa", `missionsB2.${k}`);

interface Ctx {
  state: PageState;
  forceDemo: boolean;
  forceViolation: boolean;
  details: boolean;
  nowMs: number;
}
function ctxOf(params: Params): Ctx {
  return {
    state: parsePageState(params.state),
    forceDemo: parseFlag(params.demo),
    forceViolation: parseFlag(params.violation),
    details: parseFlag(params.details),
    nowMs: Date.now(),
  };
}
const BLOCK: Record<Exclude<PageState, "ready">, ChipStatus> = {
  empty: "EMPTY", error: "ERROR", unavailable: "UNAVAILABLE", loading: "LOADING", stale: "STALE",
};

interface Base {
  mode: string;
  real: boolean;
  generatedAt: string | null;
  demo: boolean;
  source: string;
  status: ChipStatus;
}
function frame(pageId: string, c: Ctx, b: Base | null, extra: { empty: boolean; note?: string | null; emptyBody?: string }): Omit<FrameProps, "children"> {
  const violation = c.forceViolation ? violationOf("LIVE", true) : b ? violationOf(b.mode, b.real) : null;
  let block: FrameProps["block"] = null;
  let status: ChipStatus = b?.status ?? "UNAVAILABLE";
  if (c.state !== "ready") {
    block = { state: BLOCK[c.state] };
    status = BLOCK[c.state];
  } else if (!b) {
    block = { state: "UNAVAILABLE", bodyFa: t("ui.noSource") };
  } else if (extra.empty) {
    block = { state: "EMPTY", bodyFa: extra.emptyBody };
    status = "EMPTY";
  }
  return {
    pageId,
    title: t(`page.${pageId}.title`),
    subtitle: t(`page.${pageId}.sub`),
    status,
    demo: !!b?.demo,
    sourceText: b?.source ?? MISSING,
    generatedAt: b?.generatedAt ?? null,
    violation: c.forceViolation ? violation : violation,
    block,
    note: extra.note ?? (b?.demo ? t("ui.demoNote") : null),
  };
}

function Table({ heads, children }: { heads: string[]; children: React.ReactNode }) {
  return (
    <div className="mb-tablewrap">
      <table className="tv-table tv-table--dense">
        <thead><tr>{heads.map((h) => <th key={h} scope="col">{h}</th>)}</tr></thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}

/* ------------------------------------------------------------ message hub -- */
export async function MessageHubPage({ params }: { params: Params }) {
  const c = ctxOf(params);
  const realHub = c.forceDemo ? null : readMessageHub();
  const snap = realHub ?? loadContract()?.messageHub ?? null;
  const demoMode = snap ? (realHub ? false : snap.demo !== false) : true;
  const base: Base | null = snap
    ? realHub
      ? { mode: snap.executionMode, real: snap.realTrading, generatedAt: snap.generatedAt, demo: false, source: snap.source, status: "PARTIAL" }
      : { mode: snap.executionMode, real: snap.realTrading, generatedAt: snap.generatedAt, demo: true, source: snap.source, status: "DEMO" }
    : null;
  const v = snap ? buildMessageHub(snap, demoMode) : null;
  const cap = v ? capHighlights(v.highlights) : { shown: [], hidden: 0 };
  const f = frame("message-hub", c, base, { empty: !!v && v.highlights.length === 0, emptyBody: t("ui.noData") });
  return (
    <PageFrame {...f}>
      {v ? (
        <>
          {v.telegramBlockedOwner ? <p className="mb-note" data-mb-owner-gate="">{t("messageHub.ownerGate")}</p> : null}
          <HighlightList items={cap.shown} hidden={cap.hidden} empty={t("ui.noData")} />
          <Details open={c.details} meta={t("messageHub.detailsMeta")}>
            <div className="mb-sec">
              <h3 className="mb-h2">{t("messageHub.channels")}</h3>
              <Table heads={[t("col.channel"), t("col.status"), t("col.lastMessage"), t("col.queue"), t("col.lastError")]}>
                {v.snapshot.channels.map((ch) => (
                  <tr key={ch.channel}>
                    <td dir="ltr">{ch.channel}</td>
                    <td><TruthChip status={demoize(ch.status, demoMode)} size="sm" /></td>
                    <td dir="ltr" className="tv-mono"><Cell v={ch.lastMessageTime ? tehranStamp(ch.lastMessageTime) : null} /></td>
                    <td className="tv-num"><Cell v={ch.queueDepth === null ? null : formatNum(ch.queueDepth)} /></td>
                    <td><Cell v={redact(ch.lastError)} /></td>
                  </tr>
                ))}
              </Table>
            </div>
            <div className="mb-sec">
              <h3 className="mb-h2">Telegram / {t("messageHub.nightly")}</h3>
              <div className="mb-grid2">
                <div className="mb-kpi"><span className="mb-kpi__k">Telegram</span><span className="mb-kpi__v" dir="ltr">{v.snapshot.telegram.bridgeState}</span><TruthChip status={demoize(bridgeStatus(v.snapshot.telegram.bridgeState), demoMode)} size="sm" /></div>
                <div className="mb-kpi"><span className="mb-kpi__k">{t("messageHub.nightly")}</span><span className="mb-kpi__v" dir="ltr">{v.snapshot.nightlyReport.deliveryState}</span><TruthChip status={demoize(deliveryStatus(v.snapshot.nightlyReport.deliveryState), demoMode)} size="sm" />
                  <span className="mb-hl__detail" dir="ltr">{tehranStamp(v.snapshot.nightlyReport.lastReportTime)} | {redact(v.snapshot.nightlyReport.evidenceLink)}</span></div>
              </div>
            </div>
            <div className="mb-sec">
              <h3 className="mb-h2">{t("messageHub.gate")}</h3>
              <p className="mb-hl__detail">{t("messageHub.gateNote")}</p>
              <Table heads={["ID", t("col.title"), t("col.requestedBy"), t("col.age"), t("col.status")]}>
                {v.snapshot.humanGateInbox.map((g) => (
                  <tr key={g.id}><td dir="ltr" className="tv-mono">{g.id}</td><td dir="auto">{redact(g.title)}</td><td dir="auto">{g.requestedByAgent}</td><td dir="ltr">{g.age}</td><td><TruthChip status={demoize(g.state, demoMode)} size="sm" /></td></tr>
                ))}
              </Table>
            </div>
            <div className="mb-sec">
              <h3 className="mb-h2">{t("messageHub.log")}</h3>
              <Table heads={[t("col.time"), t("col.direction"), t("col.channel"), t("col.summary"), t("col.delivery")]}>
                {v.snapshot.messageLog.map((m, i) => (
                  <tr key={i}><td dir="ltr" className="tv-mono">{tehranStamp(m.time)}</td><td dir="ltr">{m.direction}</td><td dir="ltr">{m.channel}</td><td dir="auto">{redact(m.summary).slice(0, 120)}</td><td><TruthChip status={demoize(deliveryStatus(m.deliveryState), demoMode)} size="sm" /></td></tr>
                ))}
              </Table>
            </div>
          </Details>
        </>
      ) : null}
    </PageFrame>
  );
}

/* --------------------------------------------------------- self evaluation - */
export async function SelfEvaluationPage({ params }: { params: Params }) {
  const c = ctxOf(params);
  const realEval = c.forceDemo ? null : readSelfEvaluation();
  const snap = realEval ?? loadContract()?.selfEvaluation ?? null;
  const period = parsePeriod(params.period);
  const demoMode = snap ? (realEval ? false : snap.demo !== false) : true;
  const base: Base | null = snap
    ? realEval
      ? { mode: snap.executionMode, real: snap.realTrading, generatedAt: snap.generatedAt, demo: false, source: snap.source, status: "PARTIAL" }
      : { mode: snap.executionMode, real: snap.realTrading, generatedAt: snap.generatedAt, demo: true, source: snap.source, status: "DEMO" }
    : null;
  const v = snap ? buildSelfEval(snap, period, demoMode) : null;
  const cap = v ? capHighlights(v.highlights) : { shown: [], hidden: 0 };
  const f = frame("self-evaluation", c, base, { empty: !!v && !v.scorecard, emptyBody: t("ui.noData") });
  const sc = v?.scorecard;
  const q = (p: string) => `?period=${p}${c.details ? "&details=1" : ""}`;
  return (
    <PageFrame {...f}>
      {v ? (
        <>
          <nav className="mb-links" aria-label={t("selfEvaluation.period")}>
            {(["week", "month"] as const).map((p) => (
              <a key={p} className="mb-link" href={q(p)} aria-current={p === period ? "page" : undefined}>{t(`selfEvaluation.${p}`)}</a>
            ))}
          </nav>
          <HighlightList items={cap.shown} hidden={cap.hidden} empty={t("ui.noData")} />
          <Details open={c.details} meta={t("selfEvaluation.detailsMeta")}>
            {sc ? (
              <>
                <div className="mb-kpis mb-sec">
                  {([
                    ["decisionsReviewed", sc.decisionsReviewed], ["decisionsWithEvidence", sc.decisionsWithEvidence],
                    ["decisionsWithUnseenCheck", sc.decisionsWithUnseenCheck], ["unresolvedItems", sc.unresolvedItems],
                  ] as const).map(([k, val]) => (
                    <div key={k} className="mb-kpi"><span className="mb-kpi__k">{t(`selfEvaluation.${k}`)}</span><span className="mb-kpi__v" dir="ltr">{formatNum(val)}</span><TruthChip status={demoMode ? "DEMO" : "PARTIAL"} size="sm" /></div>
                  ))}
                </div>
                <p className="mb-hl__detail">{t("selfEvaluation.calibration")}: <Cell v={redact(sc.calibrationNote)} /></p>
                <Table heads={["ID", t("col.market"), t("col.rationale"), t("selfEvaluation.outcome"), t("col.review")]}>
                  {sc.allDecisions.map((d) => (
                    <tr key={d.id}><td dir="ltr" className="tv-mono">{d.id}</td><td dir="auto">{redact(d.market)}</td><td dir="auto">{redact(d.rationaleSummary)}</td><td dir="ltr">{d.outcomeKnown}</td><td dir="ltr">{d.reviewState}</td></tr>
                  ))}
                </Table>
              </>
            ) : <p className="mb-empty">{t("ui.noData")}</p>}
          </Details>
        </>
      ) : null}
    </PageFrame>
  );
}

/* ------------------------------------------------------------- idea shelf -- */
export async function IdeaShelfPage({ params }: { params: Params }) {
  const c = ctxOf(params);
  const real = c.forceDemo ? null : readIdeaShelf();
  const realRows = real ? ideasFromShelfFile(real.raw) : null;
  let base: Base | null = null;
  let rows: IdeaRow[] = [];
  let prov: ChipStatus = "DEMO";
  if (realRows) {
    prov = freshness("file", real!.mtimeIso, c.nowMs);
    base = { mode: "PAPER_ONLY", real: false, generatedAt: real!.mtimeIso, demo: false, source: `config/idea_shelf.json (${t("ui.readOnlyFile")})`, status: prov };
    rows = realRows;
  } else {
    const snap = loadContract()?.ideaShelf ?? null;
    if (snap) {
      base = { mode: snap.executionMode, real: snap.realTrading, generatedAt: snap.generatedAt, demo: true, source: snap.source, status: "DEMO" };
      rows = snap.ideas.map(ideaFromContract);
    }
  }
  const cap = capHighlights(ideaHighlights(rows, prov));
  const f = frame("idea-shelf", c, base, { empty: !!base && rows.length === 0, emptyBody: t("ui.noData"), note: base?.demo ? t("ui.demoNote") : t("ideaShelf.realNote") });
  const demo = !!base?.demo;
  return (
    <PageFrame {...f}>
      <HighlightList items={cap.shown} hidden={cap.hidden} empty={t("ui.noData")} />
      <Details open={c.details} meta={`${rows.length}`}>
        <Table heads={["ID", t("col.title"), t("col.origin"), t("col.lifecycle"), "tier", t("col.minRam"), t("col.reason"), "flags", t("col.unseen")]}>
          {rows.map((r) => (
            <tr key={r.id}>
              <td dir="ltr" className="tv-mono">{r.id}</td>
              <td dir="auto">{r.title}</td>
              <td dir="ltr"><Cell v={r.origin} /></td>
              <td dir="ltr">{r.lifecycle === "REJECTED" ? <TruthChip status="REJECTED" size="sm" /> : <Cell v={r.lifecycle === "UNKNOWN" ? null : r.lifecycle} />}</td>
              <td dir="ltr"><Cell v={r.tier} /></td>
              <td dir="ltr"><Cell v={r.minRam} /></td>
              <td dir="auto"><Cell v={r.reason} /></td>
              <td dir="ltr"><Cell v={r.flags.join(", ")} /></td>
              <td dir="ltr">{r.unseen ? `${r.unseen.result}${demo ? " (DEMO)" : ""}` : <Cell v={null} />}</td>
            </tr>
          ))}
        </Table>
      </Details>
    </PageFrame>
  );
}

/* ----------------------------------------------------- research institute -- */
export async function ResearchInstitutePage({ params }: { params: Params }) {
  const c = ctxOf(params);
  const realResearch = c.forceDemo ? null : readResearchReplay();
  const snap = realResearch ?? loadContract()?.researchInstitute ?? null;
  const demoMode = snap ? !realResearch : true;
  const base: Base | null = snap
    ? realResearch
      ? { mode: snap.executionMode, real: snap.realTrading, generatedAt: snap.generatedAt, demo: false, source: snap.source ?? "ahos_replay/results.md", status: "PARTIAL" }
      : { mode: snap.executionMode, real: snap.realTrading, generatedAt: snap.generatedAt, demo: true, source: snap.source, status: "DEMO" }
    : null;
  const v = snap ? buildResearch(snap, demoMode) : null;
  const cap = v ? capHighlights(v.highlights) : { shown: [], hidden: 0 };
  const f = frame("research-institute", c, base, { empty: !!v && v.hypotheses.length === 0, emptyBody: t("ui.noData") });
  return (
    <PageFrame {...f}>
      {v ? (
        <>
          <p className="mb-note">{realResearch ? "REPLAY_NOT_LIVE · " : ""}{t("researchInstitute.inSampleRule")}</p>
          <HighlightList items={cap.shown} hidden={cap.hidden} empty={t("ui.noData")} />
          <Details open={c.details} meta={`${v.hypotheses.length}`}>
            <div className="mb-kpis mb-sec">
              <div className="mb-kpi"><span className="mb-kpi__k">{t("researchInstitute.examined")}</span><span className="mb-kpi__v" dir="ltr">{formatNum(v.exam?.itemsExamined)}</span><TruthChip status={demoMode ? "DEMO" : "PARTIAL"} size="sm" /></div>
              <div className="mb-kpi"><span className="mb-kpi__k">{t("researchInstitute.passedUnseen")}</span><span className="mb-kpi__v" dir="ltr">{formatNum(v.passedUnseen)}</span><span className="mb-hl__detail">{t("researchInstitute.passedRule")}</span></div>
              <div className="mb-kpi"><span className="mb-kpi__k">{t("researchInstitute.lastExam")}</span><span className="mb-kpi__v mb-kpi__v--sm" dir="ltr">{tehranStamp(v.exam?.lastExamTime)}</span></div>
            </div>
            <Table heads={["ID", t("col.statement"), t("col.source"), t("col.market"), t("col.status"), t("researchInstitute.inSample"), t("col.unseen")]}>
              {v.hypotheses.map((h) => (
                <tr key={h.id}>
                  <td dir="ltr" className="tv-mono">{h.id}</td>
                  <td dir="auto">{redact(h.statement)}</td>
                  <td dir="ltr">{h.source}</td>
                  <td dir="auto">{h.market}</td>
                  <td dir="ltr">{h.status === "REJECTED" ? <TruthChip status="REJECTED" size="sm" /> : h.status}</td>
                  <td dir="auto">{h.inSampleResult ? <span className="mb-struck">{redact(h.inSampleResult.note)}</span> : <Cell v={null} />} {h.inSampleResult ? <span className="mb-tag">{t("researchInstitute.invalid")}</span> : null}</td>
                  <td dir="ltr">{h.unseenTest ? `${h.unseenTest.result} / n=${formatNum(h.unseenTest.sampleSize)} / ${t("researchInstitute.cost")}: ${h.unseenTest.costModelPresent === null ? MISSING : h.unseenTest.costModelPresent ? "yes" : "no"}` : <Cell v={null} />}</td>
                </tr>
              ))}
            </Table>
          </Details>
        </>
      ) : null}
    </PageFrame>
  );
}

/* ------------------------------------------------------------ mission map -- */
export async function MissionMapPage({ params }: { params: Params }) {
  const c = ctxOf(params);
  const real = c.forceDemo ? null : readMissionsStatus();
  let base: Base | null = null;
  let missions: import("../contract/types").Mission[] = [];
  let demo = false;
  let note: string | null = null;
  if (real) {
    const st = real.conflict ? "CONFLICT" : freshness("file", real.generatedAt, c.nowMs);
    const src = real.soakFallback
      ? "soak_status.json · last_tier_gate (MISSIONS_STATUS.md missing)"
      : `MISSIONS_STATUS.md (${t("ui.readOnlyFile")})`;
    base = { mode: "PAPER_ONLY", real: false, generatedAt: real.generatedAt, demo: false, source: src, status: st };
    missions = real.parsed.missions;
    note = real.conflict ? t("missionMap.conflict") : real.soakFallback ? "فقط open_questions و tier_gate از M13 (نه چک‌لیست کامل)" : t("missionMap.realNote");
  } else {
    const snap = loadContract()?.missionMap ?? null;
    if (snap) {
      demo = true;
      base = { mode: snap.executionMode, real: snap.realTrading, generatedAt: snap.generatedAt, demo: true, source: snap.source, status: "DEMO" };
      missions = snap.missions;
    }
  }
  const mm = buildMissionMap(missions, demo);
  const cap = capHighlights(mm.highlights);
  const f = frame("mission-map", c, base, { empty: !!base && missions.length === 0, emptyBody: t("ui.noData"), note });
  const age = base?.generatedAt ? ageHours(base.generatedAt, c.nowMs) : null;
  return (
    <PageFrame {...f}>
      {mm.counts ? (
        <div className="mb-kpis" data-mb-counts="">
          <div className="mb-kpi"><span className="mb-kpi__k">DONE</span><span className="mb-kpi__v" dir="ltr">{mm.counts.done}</span></div>
          <div className="mb-kpi"><span className="mb-kpi__k">PARTIAL</span><span className="mb-kpi__v" dir="ltr">{mm.counts.partial}</span></div>
          <div className="mb-kpi"><span className="mb-kpi__k">NOT_STARTED</span><span className="mb-kpi__v" dir="ltr">{mm.counts.notStarted}</span></div>
          <div className="mb-kpi"><span className="mb-kpi__k">BLOCKED_OWNER</span><span className="mb-kpi__v" dir="ltr">{mm.counts.blockedOwner}</span></div>
          <div className="mb-kpi"><span className="mb-kpi__k">{t("ui.age")}</span><span className="mb-kpi__v" dir="ltr">{age === null ? MISSING : `${age}h`}</span></div>
        </div>
      ) : null}
      <HighlightList items={cap.shown} hidden={cap.hidden} empty={t("ui.noData")} />
      <Details open={c.details} meta={`${missions.length}`}>
        <Table heads={["ID", t("col.title"), t("col.group"), t("col.state"), t("col.evidence"), t("col.caveat")]}>
          {missions.map((m) => (
            <tr key={m.id}>
              <td dir="ltr" className="tv-mono">{m.id}</td>
              <td dir="auto">{redact(m.title)}</td>
              <td dir="ltr">{m.group}</td>
              <td dir="ltr">{m.state}{m.blockedOwner ? " / BLOCKED_OWNER" : ""}</td>
              <td dir="ltr"><Cell v={redact(m.evidence)} /></td>
              <td dir="auto"><Cell v={redact(m.caveat)} /></td>
            </tr>
          ))}
        </Table>
      </Details>
    </PageFrame>
  );
}

export { IDEA_SHELF_PATH, MISSIONS_STATUS_PATH };
export type { Highlight };
