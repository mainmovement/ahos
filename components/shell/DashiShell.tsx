"use client";

/**
 * M-D5.2 — the Dashi shell: the RTL frame the stage sits in.
 *
 * This is the *new* main screen (`app/page.tsx`), built from scratch to the
 * DASHBOARD_DESIGN_SPEC layout and OWNER_DECISIONS, not a reskin of
 * `CommandCenter.tsx`. The old Command Center stays reachable at
 * `/command_center` as the real-data surface while this shell grows; nothing is
 * deleted and no evidence is lost.
 *
 * What M-D5.2 deliberately is *not*: no left canonical column, no telemetry
 * strips, no dossier. Those land in M-D6/M-D7. The shell at this step is the
 * 56px top bar (emblem, PAPER ONLY, health, tier chip) and the centred stage —
 * enough to prove the frame, the palette, the probe and the fallback, and
 * nothing more, because a half-built panel would be a placeholder pretending to
 * be a dashboard.
 *
 * Honesty rules this file obeys:
 * - PAPER ONLY is always visible (§0.2) and its pill is bound to
 *   `/api/command`'s `executionMode`; a missing or unfetchable mode renders
 *   UNKNOWN, never "paper" by default.
 * - The tier chip shows a *measured* verdict and its Persian reason; before the
 *   probe lands it says so rather than showing a tier.
 * - A lost WebGL context drops the stage to a Persian notice and a retry, and
 *   nothing else changes (M-D5.4) — the bar and the panels are DOM and survive.
 */
import { useCallback, useEffect, useState } from "react";

import { executionModeStatus } from "@/dashboard_truth";
import { webApiFetch } from "@/web_api_client";
import { TruthBadge } from "@/TruthBadge";
import { motionBudget, useStageStore } from "@/components/stage/store";
import { HARDWARE_LABELS, TIER_LABELS, type TierVerdict } from "@/components/stage/quality";
import { probeQuality, writeOverride } from "@/components/stage/quality";
import StageLazy from "@/components/stage/StageLazy";
import TierPanel from "@/components/shelf/TierPanel";

/** Rule 5: numbers shown to the owner are Persian digits. */
const faDigits = (n: number): string =>
  String(n).replace(/[0-9]/g, (c) => "۰۱۲۳۴۵۶۷۸۹"[Number(c)]);

type ModePill =
  | { kind: "ok" }
  | { kind: "violation"; fa: string }
  | { kind: "unknown"; fa: string };

const OK_PILL: ModePill = { kind: "ok" };
const FETCH_FAIL: ModePill = {
  kind: "unknown",
  fa: "حالت اجرا نامعلوم — پاسخ سامانه دریافت نشد",
};

export default function DashiShell() {
  const theme = useStageStore((s) => s.theme);
  const verdict = useStageStore((s) => s.verdict);
  const setVerdict = useStageStore((s) => s.setVerdict);
  const contextLost = useStageStore((s) => s.contextLost);
  const setContextLost = useStageStore((s) => s.setContextLost);
  const setTheme = useStageStore((s) => s.setTheme);

  const [mode, setMode] = useState<ModePill | null>(null);

  // The probe runs once on mount. Until it resolves the stage stays at the
  // store's T1 default — the ladder only ever runs down, so defaulting high is
  // the safe direction.
  useEffect(() => {
    let cancelled = false;
    void probeQuality().then((v) => {
      if (!cancelled) setVerdict(v);
    });
    return () => {
      cancelled = true;
    };
  }, [setVerdict]);

  useEffect(() => {
    let cancelled = false;
    void webApiFetch("/api/command")
      .then(async (res) => {
        if (!res.ok) return FETCH_FAIL;
        const body = (await res.json()) as {
          executionMode?: string | null;
          realTrading?: boolean | null;
        };
        switch (executionModeStatus(body.executionMode)) {
          case "VIOLATION":
            return {
              kind: "violation" as const,
              fa: "نقض — حالت زنده! PAPER ONLY نقض شده است",
            };
          case "OK":
            return OK_PILL;
          default:
            return { kind: "unknown" as const, fa: "حالت اجرا نامعلوم" };
        }
      })
      .catch(() => FETCH_FAIL)
      .then((pill) => {
        if (!cancelled) setMode(pill);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const onContextLost = useCallback(() => setContextLost(true), [setContextLost]);

  // M-D5.4: one retry re-probes rather than blindly re-mounting, because a
  // context that was lost once may be gone for the session.
  const retryStage = useCallback(() => {
    setContextLost(false);
    void probeQuality().then(setVerdict);
  }, [setContextLost, setVerdict]);

  // M-D5.5: the panel re-probes after the override is cleared, so its tier line
  // and the chip cannot disagree about the same measurement.
  const reprobe = useCallback(() => {
    void probeQuality().then(setVerdict);
  }, [setVerdict]);

  const [panelOpen, setPanelOpen] = useState(false);

  const tier = verdict?.tier ?? "T1";
  const budget = motionBudget(tier, useStageStore.getState().reducedMotion);
  // The stage is not loaded until the probe has landed. `StageLazy` pulls the
  // whole three.js/R3F bundle, and parsing it on the main thread starves
  // `requestAnimationFrame` — so a probe that runs alongside that parse measures
  // bundle-load contention, not the GPU, and reports a tier this machine does
  // not have. Probing first costs one short "measuring" state and makes the
  // number mean what the chip says it means.
  const allowStage = verdict !== null && tier !== "T0" && !contextLost;

  return (
    <div className="dashi" data-theme={theme} dir="rtl" lang="fa">
      <header className="dashi-topbar">
        {/* RTL: reading starts at the right, so the emblem leads. Spec §4. */}
        <div className="dashi-emblem" aria-hidden="true">
          <span className="dashi-emblem__mark">◉</span>
          <span className="dashi-emblem__word">AHOS</span>
        </div>

        <div className="dashi-topbar__pills">
          <span className="dashi-pill dashi-pill--paper" aria-live="polite">
            {mode === null ? (
              "در حال دریافت…"
            ) : mode.kind === "ok" ? (
              <bdi dir="ltr">● PAPER ONLY</bdi>
            ) : mode.kind === "violation" ? (
              <span className="dashi-pill--violation">{mode.fa}</span>
            ) : (
              <TruthBadge state="UNAVAILABLE" label="حالت اجرا" title={mode.fa} />
            )}
          </span>

          <TierChip verdict={verdict} onPick={setVerdict} />
        </div>

        <button
          type="button"
          className="dashi-theme"
          onClick={() => setTheme(theme === "imperial" ? "neon" : "imperial")}
          title={theme === "imperial" ? "تغییر به تم نئون" : "تغییر به تم شاهنشاهی"}
          aria-label="تغییر تم"
        >
          {theme === "imperial" ? "شاهنشاهی" : "نئون"}
        </button>

        <button
          type="button"
          className="dashi-panel-toggle"
          onClick={() => setPanelOpen((open) => !open)}
          aria-expanded={panelOpen}
          aria-controls="dashi-tier-panel"
          aria-label="پنل طبقهٔ سخت‌افزار"
          title="پنل طبقهٔ سخت‌افزار و ایده‌های در انتظارِ ارتقا"
        >
          {panelOpen ? "بستن پنل" : "سخت‌افزار"}
        </button>
      </header>

      <div className="dashi-body">
        <main className="dashi-main">
        {verdict === null ? (
          // The probe is still running. This is deliberately *not* the fallback
          // notice: nothing has failed and no measurement has been refused, the
          // tier is simply not known yet. Showing the T0 notice here would
          // claim a verdict that was never made.
          <div className="stage-fallback dashi-probing" role="status" dir="rtl" lang="fa">
            <p className="dashi-fallback__title">در حال سنجشِ توانِ گرافیکی</p>
            <p className="dashi-fallback__body">
              چند ثانیه طول می‌کشد تا طبقهٔ نمایش اندازه‌گیری شود.
            </p>
          </div>
        ) : allowStage ? (
          <StageLazy verdict={verdict} onContextLost={onContextLost} />
        ) : (
          <FallbackNotice contextLost={contextLost} tier={tier} onRetry={retryStage} />
        )}

        {/* The honest scope caption: the globe and its rings have landed, the
            telemetry strips have not. */}
        <p className="dashi-scope" dir="rtl">
          صحنهٔ رصدخانه — M-D۶.۵. گویِ نقطه‌ای، خشکی‌ها، پایانِ شب‌روزی و
          حلقه‌های زنجیره روی صحنه است؛ نوارهای تله‌متری در M-D۷ می‌آیند.
          {budget.particles === 0 && budget.rotate === 0
            ? " حالت کم‌مصرف: حرکت و ذرات خاموش است."
            : ""}
        </p>
      </main>

      {panelOpen ? (
        <TierPanel verdict={verdict} onReprobe={reprobe} />
      ) : null}
      </div>
    </div>
  );
}

/**
 * The measured tier chip (M-D5.3). Before the probe lands it names the
 * measurement as pending — never a tier — and once it lands it shows the
 * Persian tier label with the hardware class and the reason in its title.
 *
 * Clicking steps the tier down the ladder and writes the override; a click at
 * the floor clears it back to measurement.
 */
function TierChip({
  verdict,
  onPick,
}: {
  verdict: TierVerdict | null;
  onPick: (v: TierVerdict) => void;
}) {
  if (verdict === null) {
    return (
      <span className="dashi-tier dashi-tier--pending" role="status">
        در حال اندازه‌گیریِ توان…
      </span>
    );
  }
  const labels = TIER_LABELS[verdict.tier];
  const band = verdict.hardware === null ? null : HARDWARE_LABELS[verdict.hardware];
  // The hardware span states what was *measured*, never the name of the band the
  // count was clamped into. `hardwareTierSync` puts every count below 12 in the
  // T8 band, so showing a band label here would have claimed «۸ هسته» (8 cores)
  // on this machine's 4 logical cores — a hardware fact the probe never returned,
  // the same fabrication `dedicatedClass` exists to prevent. The band stays in
  // the title, where it is presented as a band. `hardwareConcurrency` counts
  // logical processors, so the span says "logical" or it overstates the machine.
  const cores =
    verdict.cores === null ? null : `${faDigits(verdict.cores)} هستهٔ منطقی`;
  const title = [
    labels.faWhy,
    verdict.reasonFa,
    cores ?? "تعداد هسته‌ها نامعلوم",
    band === null ? null : `دستهٔ ${band.fa}`,
  ]
    .filter((part) => part !== null)
    .join(" — ");
  const step = () => {
    const order = ["T0", "T1", "T2", "T3"] as const;
    const i = order.indexOf(verdict.tier);
    // At the floor, a click clears the override and goes back to measuring.
    const next = i === 0 ? null : order[i - 1];
    writeOverride(next);
    void probeQuality().then(onPick);
  };
  return (
    <button
      type="button"
      className={`dashi-tier dashi-tier--${verdict.tier.toLowerCase()}`}
      onClick={step}
      title={title}
      aria-label={`طبقهٔ نمایش: ${labels.fa}. ${verdict.reasonFa}`}
    >
      <span className="dashi-tier__hw">{cores ?? "سخت‌افزار نامعلوم"}</span>
      <span className="dashi-tier__render">{labels.fa}</span>
    </button>
  );
}

function FallbackNotice({
  contextLost,
  tier,
  onRetry,
}: {
  contextLost: boolean;
  tier: string;
  onRetry: () => void;
}) {
  return (
    <div className="dashi-fallback" role="alert" dir="rtl" lang="fa">
      {contextLost ? (
        <>
          <p className="dashi-fallback__title">صحنهٔ سه‌بعدی از دسترس خارج شد</p>
          <p className="dashi-fallback__body">
            گرافیک پاسخ نداد؛ نمایش دو‌بعدی جایگزین شد. داده‌ها از بین نرفته‌اند.
          </p>
        </>
      ) : (
        <>
          <p className="dashi-fallback__title">نمای دو‌بعدی</p>
          <p className="dashi-fallback__body">
            این ماشین WebGL ندارد یا طبقهٔ نمایش آن T0 است ({tier}). همان داده‌ها، بدون
            سه‌بعدی.
          </p>
        </>
      )}
      <button type="button" className="dashi-retry" onClick={onRetry}>
        اندازه‌گیریِ دوباره
      </button>
    </div>
  );
}
