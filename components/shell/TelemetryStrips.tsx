"use client";

/**
 * M-D7 — the bottom telemetry strips: run log, gates, spend, ledger.
 *
 * Presentation only (AGENTS.md). Every value here is read from
 * `/api/command`'s snapshot — the app's own read model, served from its own
 * origin — and nothing is derived, scored or decided client-side. Where a value
 * has not arrived, or the fetch failed, the strip shows grey UNKNOWN rather than
 * a plausible substitute, because `UNKNOWN > fabricated` and a dashboard that
 * invents its own telemetry is worse than one that admits it did not load.
 *
 * Four cells, per the Dashi spec:
 *  - اجرا (run log): the engine's last cycle, its status, and the cycle count.
 *  - دروازه‌ها (gates): the snapshot's health dimensions, as TruthBadges. These
 *    are the *engine's* verdicts about itself, not a client-side re-check.
 *  - هزینه (spend): always 0. AHOS runs on free tiers and public data; the
 *    number is a constant because it is a fact about the build, and it is shown
 *    so nobody has to take "free" on faith.
 *  - دفتر (ledger): the paper positions the engine holds, and how many are open.
 *
 * Where the engine has no live cycle of its own — which is the normal state on a
 * host whose Node engine is idle and whose real runner is the Python M13 paper
 * soak — the run, gates and ledger cells present that soak's recorded state
 * instead, read from its own status file (see `soak_read_model.ts`). Those cells
 * are labelled with the soak's name and its own staleness, and they yield the
 * moment the engine cycles again. The soak is PAPER_ONLY and is presented as
 * paper: nothing here turns a fictional bankroll into a position
 * recommendation, and the tier gate is shown with its own PASS/FAIL vocabulary
 * rather than as an engine health dimension.
 *
 * The strip does not poll faster than the engine cycles: 30 s against a default
 * 70 s interval. It refreshes on mount, and a failed fetch leaves the last good
 * snapshot in place with a marker rather than blanking the strip — a stale
 * reading with its age on it is more honest than an empty box.
 */
import { useEffect, useState } from "react";

import { webApiFetch } from "@/web_api_client";
import { TruthBadge } from "@/TruthBadge";
import { faNum, faPct, faUsd, type SoakReadModel } from "@/dashboard_snapshot";

const REFRESH_MS = 30_000;
const MAX_GATE_ROWS = 5;
const MAX_LEDGER_ROWS = 4;

/**
 * The slice of the snapshot these strips read. Named fields only — the full
 * payload is larger and most of it is the stage's, not the strips'.
 */
interface CommandSlice {
  state: {
    running: boolean | null;
    cycleCount: number | null;
    lastCycleAt: string | null;
    lastCycleStatus: string | null;
    intervalSec: number | null;
    lastError: string | null;
  } | null;
  health: { dimensions: { nameFa: string; status: string; evidenceFa: string }[] } | null;
  paper:
    | {
        symbol: string | null;
        status: string | null;
        side: string | null;
        entryPrice: number | null;
        lastPrice: number | null;
      }[]
    | null;
  /**
   * The local M13 paper soak. The runner that actually cycles on this host is a
   * Python process, not the Node engine, and it writes its state to a file the
   * API reads (see `soak_read_model.ts`). Present whenever that file is there.
   */
  soak?: SoakReadModel | null;
}

interface StripData {
  slice: CommandSlice | null;
  /** Wall-clock of the fetch that produced `slice`, so its age is visible. */
  fetchedAt: Date;
  /** The last fetch failed; `slice` is whatever the previous one left behind. */
  stale: boolean;
}

const PENDING: StripData = { slice: null, fetchedAt: new Date(0), stale: false };

/** Persian digits, so the strips match the shell's numerals. */
function fa(n: number | null | undefined): string {
  if (n === null || n === undefined || !Number.isFinite(n)) return "؟";
  return n.toLocaleString("fa-IR");
}

/** How long ago an ISO timestamp was, in Persian — "۱۲ دقیقه پیش". */
function faAgo(iso: string | null): string {
  if (!iso) return "UNKNOWN";
  const then = Date.parse(iso);
  if (!Number.isFinite(then)) return "UNKNOWN";
  const mins = Math.round((Date.now() - then) / 60_000);
  if (mins < 1) return "همین حالا";
  if (mins < 60) return `${fa(mins)} دقیقه پیش`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${fa(hours)} ساعت پیش`;
  return `${fa(Math.round(hours / 24))} روز پیش`;
}

/**
 * Is the engine's own telemetry live? A running engine is; a stopped one is only
 * if its last cycle is within three of its own intervals. This is the switch that
 * decides whether the strips speak for the engine or for the soak — the soak's
 * numbers are never blended into the engine's, and the engine's are never
 * overwritten by a paper runner's while it is cycling.
 */
function engineIsFresh(state: CommandSlice["state"]): boolean {
  if (!state) return false;
  if (state.running) return true;
  const at = state.lastCycleAt ? Date.parse(state.lastCycleAt) : NaN;
  if (!Number.isFinite(at)) return false;
  const limitMs = 3 * (state.intervalSec ?? 70) * 1000;
  return Date.now() - at <= limitMs;
}

/** The market's ticker, or the market's name when the file gives no ticker. */
function soakSymbol(market: string | null): string {
  if (!market) return "؟";
  return market.toLowerCase() === "gold" ? "XAU" : market.toUpperCase();
}

export function TelemetryStrips() {
  const [data, setData] = useState<StripData>(PENDING);

  useEffect(() => {
    let cancelled = false;
    let alive = true;

    const load = async () => {
      try {
        const res = await webApiFetch("/api/command");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const slice = (await res.json()) as CommandSlice;
        if (!cancelled) setData({ slice, fetchedAt: new Date(), stale: false });
      } catch {
        // Keep the last reading and flag it. An unreachable API is not a reason
        // to erase what was true a minute ago.
        if (!cancelled) setData((prev) => ({ ...prev, stale: true, fetchedAt: new Date() }));
      }
    };

    void load();
    const timer = setInterval(() => {
      if (alive) void load();
    }, REFRESH_MS);
    return () => {
      cancelled = true;
      alive = false;
      clearInterval(timer);
    };
  }, []);

  const { slice, fetchedAt, stale } = data;
  const state = slice?.state ?? null;
  const gates = slice?.health?.dimensions ?? null;
  const papers = slice?.paper ?? null;
  const open = papers ? papers.filter((p) => p.status === "OPEN").length : null;

  // The engine's telemetry wins while it is live. Where it is not — which on a
  // host whose engine is idle is the normal state — the strips present the local
  // paper soak instead, labelled as the soak and stamped with its own staleness.
  // A STALE soak still shows, with its age on it, for the same reason a failed
  // fetch keeps its last reading: an honest old number beats an empty box.
  const soak = !engineIsFresh(state) ? slice?.soak ?? null : null;
  const soakLive = soak && soak.status !== "UNAVAILABLE" ? soak : null;
  const soakHint = soakLive
    ? `${soakLive.soak ?? "SOAK"}${soakLive.status === "STALE" ? " — کهنه" : ""}`
    : null;

  return (
    <section className="telemetry" dir="rtl" lang="fa" aria-label="نوارهای تله‌متری">
      <StripCell title="اجرا" hint={stale ? "غیر قابل دسترس — آخرین خوانت" : soakHint}>
        {soakLive && soakLive.run ? (
          <SoakRun run={soakLive.run} paperOnly={soakLive.paperOnly} />
        ) : state ? (
          <>
            <p className="telemetry__line">
              <TruthBadge state={state.running ? "VERIFIED" : "UNKNOWN"} label={state.running ? "در حال اجرا" : "متوقف"} />
              <span className="telemetry__value">{fa(state.cycleCount)} چرخه</span>
            </p>
            <p className="telemetry__line telemetry__line--muted">
              آخرین چرخه {faAgo(state.lastCycleAt)}
              {state.lastCycleStatus ? ` — ${state.lastCycleStatus}` : ""}
            </p>
            {state.lastError ? (
              <p className="telemetry__line telemetry__line--err" title={state.lastError}>
                {state.lastError.slice(0, 90)}
              </p>
            ) : null}
          </>
        ) : (
          <UnknownLine label="اطلاعاتِ اجرا" />
        )}
      </StripCell>

      <StripCell title="دروازه‌ها" hint={soakHint}>
        {soakLive && soakLive.gates ? (
          <SoakGates gates={soakLive.gates} />
        ) : gates && gates.length > 0 ? (
          <ul className="telemetry__gates">
            {gates.slice(0, MAX_GATE_ROWS).map((g) => (
              <li key={g.nameFa} className="telemetry__gate">
                <TruthBadge state={g.status} label={g.status} title={g.evidenceFa} />
                <span className="telemetry__gate-name">{g.nameFa}</span>
              </li>
            ))}
          </ul>
        ) : (
          <UnknownLine label="درگاه‌های سلامت" />
        )}
      </StripCell>

      <StripCell title="هزینه">
        {/* A constant, and shown as one: AHOS runs on free tiers and public data.
            Zero is a fact about the build, not a measurement that could go stale. */}
        <p className="telemetry__line">
          <TruthBadge state="VERIFIED" label="رایگان" />
          <span className="telemetry__value">۰</span>
        </p>
        <p className="telemetry__line telemetry__line--muted">
          منابعِ رایگان و دادهٔ عمومی — بدون سرویسِ پرداختی
        </p>
      </StripCell>

      <StripCell title="دفتر" hint={soakHint}>
        {soakLive && soakLive.ledger ? (
          <SoakLedger ledger={soakLive.ledger} />
        ) : papers && papers.length > 0 ? (
          <>
            <p className="telemetry__line">
              <TruthBadge state={open ? "VERIFIED" : "UNKNOWN"} label={open ? "موقعیت باز" : "بدون موقعیت"} />
              <span className="telemetry__value">{fa(open)} از {fa(papers.length)}</span>
            </p>
            <ul className="telemetry__ledger">
              {papers.slice(0, MAX_LEDGER_ROWS).map((p, i) => (
                <li key={`${p.symbol ?? i}-${i}`} className="telemetry__ledger-row">
                  <bdi dir="ltr" className="telemetry__sym">{p.symbol ?? "؟"}</bdi>
                  <span className="telemetry__side">{p.side ?? "؟"}</span>
                  <span className="telemetry__status">{p.status ?? "؟"}</span>
                </li>
              ))}
            </ul>
          </>
        ) : (
          <UnknownLine label="موقعیت‌های کاغذی" />
        )}
      </StripCell>

      <p className="telemetry__age" aria-hidden="true">
        {fetchedAt.getTime() > 0 ? `به‌روزرسانی ${faAgo(fetchedAt.toISOString())}` : ""}
      </p>
    </section>
  );
}

/**
 * اجرا — the soak's own run log. Its `witness_state` is the two-source verdict
 * of the last cycle, so the badge shows a real IdentityState rather than a
 * "running" the strip invented. A cycle that failed is named, not hidden.
 */
function SoakRun({ run, paperOnly }: { run: NonNullable<SoakReadModel["run"]>; paperOnly: boolean }) {
  return (
    <>
      <p className="telemetry__line">
        <TruthBadge
          state={run.witnessState}
          label={run.running ? "در حال اجرا" : "متوقف"}
          title={run.witnessReason ?? undefined}
        />
        <span className="telemetry__value">{fa(run.cyclesOk)} چرخه</span>
      </p>
      <p className="telemetry__line telemetry__line--muted">
        آخرین چرخه {faAgo(run.lastCycleAt)}
        {run.lastCycleOk !== null ? ` — ${run.lastCycleOk ? "OK" : "FAILED"}` : ""}
        {run.lastCycleDurationS !== null ? ` · ${faNum(run.lastCycleDurationS)} ثانیه` : ""}
      </p>
      <p className="telemetry__line telemetry__line--muted" title={run.witnessReason ?? undefined}>
        {paperOnly ? "کاغذی — " : ""}
        شاهد {run.witnessState ?? "؟"}
        {run.priceUsd !== null ? ` · قیمت ${faUsd(run.priceUsd)}` : ""}
        {run.cyclesFailed ? ` · ${fa(run.cyclesFailed)} چرخهٔ ناموفق` : ""}
      </p>
    </>
  );
}

/**
 * دروازه‌ها — the soak's T0→T1 gate, which is a different thing from the
 * engine's health dimensions and is never merged with them. The statuses are the
 * gate's own PASS/FAIL/UNMEASURABLE vocabulary, mapped through `badgeForState`,
 * so a criterion that passed is VERIFIED and everything else reads UNKNOWN — a
 * gate that has not passed is not a failure styled as one, and promotion is an
 * owner act the strips do not perform.
 */
function SoakGates({ gates }: { gates: NonNullable<SoakReadModel["gates"]> }) {
  const measurable =
    gates.measurableTotal !== null && gates.measurableTotal > 0
      ? gates.measurablePassed === gates.measurableTotal
        ? "PASS"
        : "FAIL"
      : "UNMEASURABLE";
  const rows = [
    {
      nameFa: `تیرِ ${gates.tier ?? "؟"}`,
      status: gates.promoted ? "PASS" : "FAIL",
      evidenceFa:
        gates.promoted === false
          ? "ارتقا یک عملِ مالکانه است — دروازه هرگز ارتقا نمی‌دهد"
          : "ارزیابیِ دروازه در دسترس نیست",
    },
    {
      nameFa: "معیارهای قابلِ سنجش",
      status: measurable,
      evidenceFa:
        gates.measurablePassed !== null && gates.measurableTotal !== null
          ? `${gates.measurablePassed} از ${gates.measurableTotal} عبور کرد`
          : "هیچ معیاری سنجیده نشد",
    },
    {
      nameFa: "غیرقابلِ اندازه‌گیری",
      status: "UNMEASURABLE",
      evidenceFa:
        gates.unmeasurableCount !== null
          ? `${gates.unmeasurableCount} معیار به‌طورِ مشخص قابلِ ارزیابی نیست — مسدود می‌کنند، نه صرف‌نظر`
          : "UNKNOWN",
    },
    {
      nameFa: "آمادگی برای بازبینیِ مالک",
      status: gates.readyForOwnerReview ? "PASS" : "FAIL",
      evidenceFa:
        gates.openQuestions.length > 0
          ? gates.openQuestions[0].slice(0, 140)
          : gates.readyForOwnerReview
            ? "آماده است"
            : "هنوز همهٔ معیارها عبور نکرده‌اند",
    },
  ];
  return (
    <ul className="telemetry__gates">
      {rows.map((g) => (
        <li key={g.nameFa} className="telemetry__gate">
          <TruthBadge state={g.status} label={g.status} title={g.evidenceFa} />
          <span className="telemetry__gate-name">{g.nameFa}</span>
        </li>
      ))}
    </ul>
  );
}

/**
 * دفتر — the soak's paper position. One instrument, fictional bankroll, real
 * corroborated price; the line carries the breaker's drawdown and exposure
 * because those are the limits the runner is actually holding itself to.
 */
function SoakLedger({ ledger }: { ledger: NonNullable<SoakReadModel["ledger"]> }) {
  return (
    <>
      <p className="telemetry__line">
        <TruthBadge
          state={ledger.positionOpen ? "VERIFIED" : "UNKNOWN"}
          label={ledger.positionOpen ? "موقعیت باز" : "بدون موقعیت"}
        />
        <span className="telemetry__value">{fa(ledger.closedTrades)} معاملهٔ بسته</span>
      </p>
      <ul className="telemetry__ledger">
        <li className="telemetry__ledger-row">
          <bdi dir="ltr" className="telemetry__sym">{soakSymbol(ledger.market)}</bdi>
          <span className="telemetry__side">{ledger.positionOpen ? "باز" : "بسته"}</span>
          <span className="telemetry__status">
            {ledger.openUnpriced ? "بدون قیمت" : `${faNum(ledger.lastPrice)} دلار`}
          </span>
        </li>
      </ul>
      <p className="telemetry__line telemetry__line--muted" title={ledger.witnessReason ?? undefined}>
        تراز {faUsd(ledger.equityUsd)} از {faUsd(ledger.bankrollUsd)}
        {ledger.cumulativeRealizedPnlUsd !== null ? ` · سود/زیان ${faUsd(ledger.cumulativeRealizedPnlUsd)}` : ""}
      </p>
      <p className="telemetry__line telemetry__line--muted">
        {ledger.drawdownPct !== null ? `افت ${faPct(ledger.drawdownPct)}` : ""}
        {ledger.openExposurePct !== null ? ` · مواجهه ${faPct(ledger.openExposurePct)}` : ""}
        {ledger.breakerState ? ` · بریکر ${ledger.breakerState}` : ""}
      </p>
    </>
  );
}

function StripCell({
  title,
  hint,
  children,
}: {
  title: string;
  hint?: string | null;
  children: React.ReactNode;
}) {
  return (
    <div className="telemetry__cell">
      <h3 className="telemetry__cell-title">
        {title}
        {hint ? <span className="telemetry__stale">{hint}</span> : null}
      </h3>
      {children}
    </div>
  );
}

function UnknownLine({ label }: { label: string }) {
  return (
    <p className="telemetry__line telemetry__line--muted">
      <TruthBadge state="UNKNOWN" label="UNKNOWN" />
      <span className="telemetry__value">{label} بارگذاری نشد</span>
    </p>
  );
}
