import type { ReactNode } from "react";
import { tr } from "@/src/lib/i18n";
import type { ChipStatus } from "@/src/features/trade-venue/logic/model";
import { TruthChip } from "@/src/components/truth/TruthChip";
import { Cell, Details, HighlightList, PageFrame, type FrameProps } from "@/src/features/missions-b2/components/PageFrame";
import { MISSING, buildMissionMap, capHighlights, formatNum, parseFlag, parsePageState, redact, tehranStamp, violationOf, type PageState } from "@/src/features/missions-b2/lib/model";
import { MISSIONS_STATUS_PATH, readMissionsStatus } from "@/src/features/missions-b2/lib/data.server";
import { readLauncherStatusOneline, readLauncherVerifyReceipt, readServedCommit } from "@/src/lib/launcher-verify";
import { SOAK_STATUS_PATH, loadContract3, readHealth, readLessons, readPortable, readReplay } from "../lib/data.server";
import { RealOilGoldPanel } from "@/src/features/real-paper/components/RealOilGoldPanel";
import { loadSoakLedger } from "@/src/features/real-paper/lib/data.server";
import { lessonHighlights, normalizeLesson, oilGoldHighlights, portableHighlights, resolveRamGuardState, toMission } from "../lib/model";

type Params = Record<string, string | string[] | undefined>;
const t = (k: string) => tr("fa", `missionsB3.${k}`);
const t2 = (k: string) => tr("fa", `missionsB2.${k}`);

interface Ctx { state: PageState; forceDemo: boolean; forceViolation: boolean; details: boolean; nowMs: number }
function ctxOf(p: Params): Ctx {
  return { state: parsePageState(p.state), forceDemo: parseFlag(p.demo), forceViolation: parseFlag(p.violation), details: parseFlag(p.details), nowMs: Date.now() };
}
const BLOCK: Record<Exclude<PageState, "ready">, ChipStatus> = { empty: "EMPTY", error: "ERROR", unavailable: "UNAVAILABLE", loading: "LOADING", stale: "STALE" };

interface Base { mode: string; real: boolean; generatedAt: string | null; demo: boolean; source: string; status: ChipStatus }
function frame(pageId: string, c: Ctx, b: Base | null, extra: { empty: boolean; note?: string | null }): Omit<FrameProps, "children"> {
  const violation = c.forceViolation ? violationOf("LIVE", true) : b ? violationOf(b.mode, b.real) : null;
  let block: FrameProps["block"] = null;
  let status: ChipStatus = b?.status ?? "UNAVAILABLE";
  if (c.state !== "ready") { block = { state: BLOCK[c.state] }; status = BLOCK[c.state]; }
  else if (!b) block = { state: "UNAVAILABLE", bodyFa: t2("ui.noSource") };
  else if (extra.empty) { block = { state: "EMPTY", bodyFa: t2("ui.noData") }; status = "EMPTY"; }
  return {
    pageId, title: t(`page.${pageId}.title`), subtitle: t(`page.${pageId}.sub`), status, demo: !!b?.demo,
    sourceText: b?.source ?? MISSING, generatedAt: b?.generatedAt ?? null, violation, block,
    note: extra.note ?? (b?.demo ? t2("ui.demoNote") : null),
  };
}
const demoBase = (c: { executionMode: string | null; realTrading: boolean | null; source: string | null; generatedAt: string | null }): Base =>
  ({ mode: c.executionMode ?? "UNKNOWN", real: c.realTrading ?? true, generatedAt: c.generatedAt, demo: true, source: c.source ?? "EXAMPLE_CONTRACT_DEMO", status: "DEMO" });

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
function Kpi({ k, v, chip }: { k: string; v: string; chip?: ChipStatus }) {
  return <div className="mb-kpi"><span className="mb-kpi__k">{k}</span><span className="mb-kpi__v" dir="auto">{v}</span>{chip ? <TruthChip status={chip} size="sm" /> : null}</div>;
}

/* ---------------------------------------------------------- health monitor -- */
export async function HealthMonitorPage({ params }: { params: Params }) {
  const c = ctxOf(params);
  const real = c.forceDemo ? null : await readHealth(c.nowMs);
  const launcherReceipt = c.forceDemo ? null : readLauncherVerifyReceipt();
  const contract = loadContract3();
  const demoSnap = contract?.healthMonitor ?? null;
  const snap = real?.snapshot ?? demoSnap;
  const isDemo = !real;
  const base: Base | null = real ? { mode: real.mode, real: real.real, generatedAt: real.snapshot.generatedAt, demo: false, source: real.snapshot.source ?? SOAK_STATUS_PATH, status: real.status } : demoSnap && contract ? demoBase(contract) : null;
  const hl = real ? real.highlights : demoSnap ? demoSnap.services.map((s) => ({ id: s.name, title: s.name, detail: null, status: "DEMO" as ChipStatus })) : [];
  const cap = capHighlights(hl);
  const servedFile = c.forceDemo ? null : readServedCommit();
  const verifyServed = launcherReceipt?.map.served_commit ?? null;
  const servedShort = (servedFile ?? verifyServed)?.slice(0, 7) ?? null;
  const servedMismatch = Boolean(servedFile && verifyServed && servedFile !== verifyServed);
  const verifyArena = launcherReceipt?.map["arena:3200"];
  const arenaLive = snap?.services.some((s) => s.name.includes("3200") && s.status === "LIVE");
  const staleVerify = Boolean(verifyArena && verifyArena !== "OK" && arenaLive);
  const healthNote = real
    ? [
        t("ui.soakNote"),
        servedShort ? `build ${servedShort}` : null,
        launcherReceipt?.map.telegram_state ? `telegram ${launcherReceipt.map.telegram_state}` : null,
        servedMismatch ? "CONFLICT served_commit vs verify" : null,
        staleVerify ? `verify stale (arena was ${verifyArena})` : null,
      ]
        .filter(Boolean)
        .join(" · ")
    : undefined;
  const f = frame("health-monitor", c, base, { empty: !!snap && hl.length === 0, note: healthNote });
  return (
    <PageFrame {...f}>
      {snap ? (
        <>
          <HighlightList items={cap.shown} hidden={cap.hidden} empty={t2("ui.noData")} />
          <Details open={c.details} meta={t("health.detailsMeta")}>
            <div className="mb-sec">
              <h3 className="mb-h2">{t("health.services")}</h3>
              <Table heads={[t2("col.title"), t2("col.status"), t("health.heartbeat")]}>
                {snap.services.map((s) => (
                  <tr key={s.name}><td dir="auto">{s.name}</td><td><TruthChip status={isDemo ? "DEMO" : s.status} size="sm" /></td><td dir="ltr" className="tv-mono"><Cell v={s.lastHeartbeat ? tehranStamp(s.lastHeartbeat) : null} /></td></tr>
                ))}
              </Table>
            </div>
            <div className="mb-kpis mb-sec">
              <Kpi k={t("health.run")} v={snap.soak.currentRun ?? MISSING} />
              <Kpi k={t("health.elapsed")} v={formatNum(snap.soak.elapsedHours)} />
              <Kpi k={t("health.target")} v={formatNum(snap.soak.targetHours)} />
              <Kpi k={t("health.restarts")} v={formatNum(snap.soak.restarts)} />
              <Kpi k={t("health.ram")} v={resolveRamGuardState(snap) === "UNKNOWN" ? t("ui.unknown") : resolveRamGuardState(snap)} chip={resolveRamGuardState(snap) === "UNKNOWN" ? "UNKNOWN" : undefined} />
              <Kpi k={t2("col.lastError")} v={redact(snap.soak.lastError) || MISSING} />
            </div>
            <div className="mb-sec">
              <h3 className="mb-h2">{t("health.faults")}</h3>
              {snap.faults.length === 0 ? <p className="mb-empty">{t("health.noFaults")}</p> : (
                <Table heads={["ID", t("health.faultType"), t("health.target2"), t("health.expected"), t("health.observed")]}>
                  {snap.faults.map((x) => (
                    <tr key={x.id}><td dir="ltr" className="tv-mono">{x.id}</td><td dir="auto">{x.faultType}</td><td dir="auto">{x.targetService}</td><td dir="auto">{x.expected}</td><td dir="auto"><Cell v={x.observed} /></td></tr>
                  ))}
                </Table>
              )}
            </div>
            {real && launcherReceipt ? (
              <p className="mb-hl__detail" dir="ltr">
                served_commit={launcherReceipt.map.served_commit ?? MISSING} · /api/ops/stack
              </p>
            ) : null}
          </Details>
        </>
      ) : null}
    </PageFrame>
  );
}

/* ------------------------------------------------------------------ lessons - */
export async function LessonsPage({ params }: { params: Params }) {
  const c = ctxOf(params);
  const contract = loadContract3();
  const realLessons = c.forceDemo ? null : readLessons();
  const snap = realLessons ?? contract?.lessons ?? null;
  const demoMode = snap ? snap.demo : true;
  const base: Base | null = snap
    ? realLessons
      ? { mode: "PAPER_ONLY", real: false, generatedAt: snap.generatedAt, demo: false, source: snap.source ?? "M49 lessons_snapshot.json", status: snap.lessons.length ? "PARTIAL" : "UNKNOWN" }
      : contract
        ? demoBase(contract)
        : null
    : null;
  const hl = snap ? lessonHighlights(snap.lessons, demoMode) : [];
  const cap = capHighlights(hl);
  const f = frame("lessons", c, base, { empty: !!snap && hl.length === 0 });
  return (
    <PageFrame {...f}>
      {snap ? (
        <>
          <p className="mb-note" data-mb-rule="">{t("lessons.rule")}</p>
          <HighlightList items={cap.shown} hidden={cap.hidden} empty={t2("ui.noData")} />
          <Details open={c.details} meta={t("lessons.detailsMeta")}>
            <Table heads={["ID", t2("col.market"), t("lessons.mistake"), t("lessons.lesson"), t2("col.reason"), t2("col.unseen")]}>
              {snap.lessons.map(normalizeLesson).map((l) => (
                <tr key={l.id}>
                  <td dir="ltr" className="tv-mono">{l.id}</td><td dir="ltr">{l.market}</td><td dir="auto">{redact(l.mistake)}</td><td dir="auto">{redact(l.lesson)}</td><td dir="auto">{redact(l.reason)}</td>
                  <td dir="ltr">{l.unseenTest ? l.unseenTest.result : "NOT_RUN"}</td>
                </tr>
              ))}
            </Table>
          </Details>
        </>
      ) : null}
    </PageFrame>
  );
}

/* ----------------------------------------------------------------- workroom - */
export async function WorkroomPage({ params }: { params: Params }) {
  const c = ctxOf(params);
  const real = c.forceDemo ? null : readMissionsStatus();
  const contract = loadContract3();
  const demoSnap = contract?.workroom ?? null;
  const missions = real ? real.parsed.missions : demoSnap ? demoSnap.missions.map(toMission) : [];
  const isDemo = !real;
  const base: Base | null = real
    ? {
        mode: "PAPER_ONLY",
        real: false,
        generatedAt: real.generatedAt,
        demo: false,
        source: real.soakFallback ? "soak_status.json · last_tier_gate" : MISSIONS_STATUS_PATH.replace(/^.*[\\/]ahos_assets[\\/]/, "ahos_assets/"),
        status: real.conflict ? "CONFLICT" : "PARTIAL",
      }
    : demoSnap && contract ? demoBase(contract) : null;
  const m = buildMissionMap(missions, isDemo);
  const cap = capHighlights(m.highlights);
  const f = frame("workroom", c, base, { empty: !!base && missions.length === 0, note: real ? (real.conflict ? t("workroom.conflict") : t2("ui.readOnlyFile")) : undefined });
  return (
    <PageFrame {...f}>
      {base ? (
        <>
          {m.counts ? (
            <div className="mb-kpis" data-mb-counts="">
              <Kpi k="DONE" v={String(m.counts.done)} /><Kpi k="PARTIAL" v={String(m.counts.partial)} /><Kpi k="NOT STARTED" v={String(m.counts.notStarted)} /><Kpi k="BLOCKED_OWNER" v={String(m.counts.blockedOwner)} />
            </div>
          ) : null}
          <HighlightList items={cap.shown} hidden={cap.hidden} empty={t2("ui.noData")} />
          <Details open={c.details} meta={t("workroom.detailsMeta")}>
            <div className="mb-sec">
              <h3 className="mb-h2">{t("workroom.agents")}</h3>
              {isDemo && demoSnap ? (
                <Table heads={[t2("col.title"), t("workroom.role"), t2("col.status")]}>
                  {demoSnap.agents.map((a) => <tr key={a.name}><td dir="auto">{a.name}</td><td dir="auto">{a.role}</td><td><TruthChip status="DEMO" size="sm" /></td></tr>)}
                </Table>
              ) : <p className="mb-empty">{t("workroom.noAgents")}</p>}
            </div>
            <Table heads={["ID", t2("col.title"), t2("col.state"), t2("col.evidence"), t2("col.caveat")]}>
              {missions.map((x) => (
                <tr key={x.id}><td dir="ltr" className="tv-mono">{x.id}</td><td dir="auto">{redact(x.title)}</td><td dir="ltr">{x.state}{x.blockedOwner ? " | BLOCKED_OWNER" : ""}</td><td dir="auto"><Cell v={x.evidence ? redact(x.evidence).slice(0, 160) : null} /></td><td dir="auto"><Cell v={x.caveat ? redact(x.caveat).slice(0, 160) : null} /></td></tr>
              ))}
            </Table>
          </Details>
        </>
      ) : null}
    </PageFrame>
  );
}

/* ----------------------------------------------------------------- portable - */
export async function PortablePage({ params }: { params: Params }) {
  const c = ctxOf(params);
  const contract = loadContract3();
  const realPortable = c.forceDemo ? null : readPortable(c.nowMs);
  const snap = realPortable ?? contract?.portable ?? null;
  const demoMode = snap ? !realPortable : true;
  const base: Base | null = snap
    ? realPortable
      ? { mode: "PAPER_ONLY", real: false, generatedAt: snap.generatedAt, demo: false, source: snap.source ?? "AHOS_Launcher", status: "PARTIAL" }
      : contract
        ? demoBase(contract)
        : null
    : null;
  const hl = snap ? portableHighlights(snap, demoMode) : [];
  const cap = capHighlights(hl);
  const served = c.forceDemo ? null : readServedCommit();
  const stackLine = c.forceDemo ? null : readLauncherStatusOneline();
  const f = frame("portable", c, base, {
    empty: !!snap && hl.length === 0,
    note: realPortable && served ? `served_commit ${served.slice(0, 7)} · PAPER_ONLY` : undefined,
  });
  return (
    <PageFrame {...f}>
      {snap ? (
        <>
          <p className="mb-note">{t("portable.tierRule")}</p>
          <HighlightList items={cap.shown} hidden={cap.hidden} empty={t2("ui.noData")} />
          <Details open={c.details} meta={t("portable.detailsMeta")}>
            <div className="mb-kpis mb-sec">
              <Kpi k={t("portable.version")} v={snap.packageVersion ?? MISSING} />
              <Kpi k={t("portable.build")} v={tehranStamp(snap.buildTime)} />
              <Kpi k="RAM (GB)" v={formatNum(snap.hardware.ramGb)} />
              <Kpi k="CPU" v={snap.hardware.cpu ?? MISSING} />
              <Kpi k="GPU" v={snap.hardware.gpu ?? MISSING} />
              <Kpi k={t("portable.heavy")} v={snap.hardware.heavyFeaturesAllowed === null ? t("ui.unknown") : String(snap.hardware.heavyFeaturesAllowed)} chip={snap.hardware.heavyFeaturesAllowed === null ? "UNKNOWN" : undefined} />
            </div>
            <Table heads={[t("portable.item"), t2("col.state")]}>
              {Object.entries(snap.checklist).map(([k, v]) => <tr key={k}><td dir="ltr">{k}</td><td dir="ltr">{v}</td></tr>)}
            </Table>
            {realPortable && stackLine ? <p className="mb-hl__detail" dir="ltr">{stackLine}</p> : null}
          </Details>
        </>
      ) : null}
    </PageFrame>
  );
}

/* ----------------------------------------------------------------- oil / gold */
export async function OilGoldPage({ params }: { params: Params }) {
  const c = ctxOf(params);
  const contract = loadContract3();
  const snap = contract?.oilGold ?? null;
  const replay = c.forceDemo ? null : readReplay();
  const ledger = c.forceDemo ? null : loadSoakLedger(c.nowMs);
  const realLive = ledger && ledger.state === "ok" ? ledger.value : null;
  const realOn = [realLive, replay].some((x) => x !== null);
  const base: Base | null = snap && contract
    ? realOn ? { mode: "PAPER_ONLY", real: false, generatedAt: realLive?.lastCycleIso ?? null, demo: false, source: "reports/grok/M13_SOAK/soak_status.json (LIVE) + ahos_replay/results.md (REPLAY_NOT_LIVE)", status: realLive?.status === "STALE" ? "STALE" : "PARTIAL" } : demoBase(contract)
    : null;
  let hl = snap ? oilGoldHighlights(snap, replay, !realOn) : [];
  if (realOn) hl = hl.map((h) => (h.id === "live" ? { ...h, title: "gold soak (live) | oil: no live track", detail: realLive ? `gold equity ${realLive.equityUsd ?? "-"} | cycle ${realLive.cycle ?? "-"}` : null, status: realLive ? realLive.status : "UNKNOWN", tag: "PAPER_ONLY" } : h));
  const cap = capHighlights(hl);
  const f = frame("oil-gold", c, base, { empty: !!snap && hl.length === 0, note: replay ? t("oilGold.replayNote") : undefined });
  return (
    <PageFrame {...f}>
      {snap ? (
        <>
          <p className="mb-note" data-mb-edge="" lang="en" dir="ltr">no proven edge yet &mdash; {t("oilGold.edgeFa")}</p>
          <HighlightList items={cap.shown} hidden={cap.hidden} empty={t2("ui.noData")} />
          {realOn ? <RealOilGoldPanel nowMs={c.nowMs} /> : null}
          {!realOn ? (
          <Details open={c.details} meta={t("oilGold.detailsMeta")}>
            <div className="mb-kpis mb-sec">
              <Kpi k={t("oilGold.liveOil")} v={replay ? MISSING : formatNum(snap.live.oil)} chip="UNKNOWN" />
              <Kpi k={t("oilGold.liveGold")} v={replay ? MISSING : formatNum(snap.live.gold)} chip="UNKNOWN" />
              <Kpi k={t("oilGold.oos")} v={snap.evidence.outOfSamplePeriod ?? MISSING} />
              <Kpi k={t("oilGold.sample")} v={formatNum(snap.evidence.sampleSize)} />
              <Kpi k={t("oilGold.cost")} v={snap.evidence.costModel ?? MISSING} />
            </div>
            <div className="mb-sec">
              <h3 className="mb-h2">{t("oilGold.replay")}</h3>
              {replay ? (
                <ul className="mb-links" data-mb-replay="">
                  {replay.lines.map((l, i) => <li key={i} className="mb-link" dir="auto">{l}</li>)}
                </ul>
              ) : <p className="mb-empty">{t("oilGold.noReplay")}</p>}
            </div>
          </Details>
          ) : null}
        </>
      ) : null}
    </PageFrame>
  );
}
