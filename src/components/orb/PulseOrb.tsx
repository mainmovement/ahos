"use client";
import "./cobe/cobe.css";
import { useEffect, useMemo, useRef, useState } from "react";
import { AhosGlobe } from "./cobe/components/ahos-globe";
import { referenceCities } from "../../lib/geography";
import { demoGateCounts } from "./orbDemo";
import type { Freshness as ContractFreshness } from "../../types/contract";
import type { OrbMarker, OrbMode, PulseOrbProps } from "../../types/orb";
import type { Department, Freshness, Gate, Health, MarketNode } from "./cobe/types/globe";

const MODES: readonly OrbMode[] = ["calm", "breach", "map"];
const MODE_LABEL: Record<OrbMode, { fa: string; en: string }> = {
  calm: { fa: "آرام", en: "Calm" },
  breach: { fa: "نقض", en: "Breach" },
  map: { fa: "نقشه", en: "Map" },
};
const TRUTH_LABEL: Record<ContractFreshness, { fa: string; en: string }> = {
  LIVE: { fa: "زنده", en: "LIVE" },
  STALE: { fa: "کهنه", en: "STALE" },
  UNKNOWN: { fa: "نامشخص", en: "UNKNOWN" },
  DEMO: { fa: "نمایشی", en: "DEMO" },
};

/**
 * Hero orb adapter: PulseOrbProps -> COBE globe (AhosGlobe).
 *  - markers default to geographic reference hubs (NOT Arena markets). They are labelled DEMO in a demo
 *    workspace and UNKNOWN otherwise, never LIVE, because no per-market feed exists.
 *  - gate counts come from props; in a DEMO workspace without props they are DEMO sample counts; otherwise
 *    they are unknown and the gate prints UNKNOWN (never 0%).
 *  - the PAPER ONLY pill and the data/gate truth chips are always rendered.
 */
export default function PulseOrb({
  health,
  departments,
  gate,
  calm,
  language = "fa",
  mode: modeProp,
  markers,
  gateCounts,
  devToggle,
  onModeChange,
}: PulseOrbProps) {
  const [localMode, setLocalMode] = useState<OrbMode | null>(null);
  const stageRef = useRef<HTMLDivElement | null>(null);
  const [fitHeight, setFitHeight] = useState<number | null>(null);

  // Fit the stage to the first fold: viewport height minus where the stage starts (document-relative, so
  // scrolling does not change it). The globe is centred inside the stage by the frame.
  useEffect(() => {
    const el = stageRef.current;
    if (!el) return;
    const measure = () => {
      const top = el.getBoundingClientRect().top + window.scrollY;
      setFitHeight(Math.round(Math.min(860, Math.max(520, window.innerHeight - top - 12))));
    };
    measure();
    const raf = window.requestAnimationFrame(measure);
    window.addEventListener("resize", measure);
    return () => {
      window.cancelAnimationFrame(raf);
      window.removeEventListener("resize", measure);
    };
  }, []);
  const mode: OrbMode = localMode ?? modeProp ?? "calm";
  const demo = health.demo === true || health.freshness === "DEMO";
  const showToggle = devToggle ?? demo;
  const fa = language === "fa";
  void gate;

  const nodeFreshness: Freshness = demo ? "DEMO" : "UNKNOWN";
  const nodes = useMemo<MarketNode[]>(() => {
    const source: OrbMarker[] =
      markers ??
      referenceCities.map((c) => ({
        id: c.name,
        nameFa: c.fa,
        nameEn: c.name,
        lat: c.lat,
        lng: c.lng,
        freshness: nodeFreshness,
        asOf: demo ? health.asOf : null,
      }));
    return source.map((m) => ({ ...m }));
  }, [markers, nodeFreshness, demo, health.asOf]);

  const deps = useMemo<Department[]>(
    () =>
      departments.map((d) => ({
        id: d.id,
        nameFa: d.name.value?.fa ?? "",
        freshness: d.health.freshness,
        needsAttention: d.health.value !== null && d.health.value !== "OK",
      })),
    [departments],
  );

  const counts = gateCounts ?? (demo ? demoGateCounts(mode) : { absorbed: null, dissipated: null });
  const absorbed = counts.absorbed ?? 0;
  const dissipated = counts.dissipated ?? 0;
  const gateKnown = absorbed + dissipated > 0;
  const gateData: Gate = {
    absorbed,
    dissipated,
    ...(typeof counts.strictness === "number" ? { strictness: counts.strictness } : {}),
  };
  const gateTruth: ContractFreshness = gateKnown ? (counts.freshness ?? health.freshness) : "UNKNOWN";
  const dataTruth: ContractFreshness = health.freshness;

  const cycle = health.cycleMs.value;
  const hb: Health = {
    bpm: cycle ? 60000 / cycle : 0,
    jitterMs: 0,
    stale: health.cycleMs.freshness === "STALE" || health.cycleMs.freshness === "UNKNOWN",
  };

  const pick = (m: OrbMode) => {
    setLocalMode(m);
    onModeChange?.(m);
  };
  const label = (f: ContractFreshness) => TRUTH_LABEL[f][language];

  return (
    <div ref={stageRef} className="ahos-orb-stage" style={fitHeight ? { height: fitHeight } : undefined} data-orb="cobe" data-mode={mode} data-demo={demo ? "true" : "false"}>
      <AhosGlobe
        markets={nodes}
        signals={[]}
        gate={gateData}
        health={hb}
        departments={deps}
        calm={calm || mode === "calm"}
        mode={mode === "map" ? "map" : "globe"}
        lang={language}
      />
      <div className="ahos-orb-pills" dir="ltr">
        <span className="ahos-orb-pill" data-kind="paper" data-testid="orb-paper-only">
          {fa ? "فقط کاغذی · PAPER ONLY" : "PAPER ONLY"}
        </span>
        <span className="ahos-orb-pill" data-kind="truth" data-truth={dataTruth} data-testid="orb-truth-data">
          {fa ? `داده: ${label(dataTruth)}` : `DATA: ${label(dataTruth)}`}
        </span>
        <span className="ahos-orb-pill" data-kind="truth" data-truth={gateTruth} data-testid="orb-truth-gate">
          {fa ? `گیت: ${label(gateTruth)}` : `GATE: ${label(gateTruth)}`}
        </span>
      </div>
      {showToggle ? (
        <div className="ahos-orb-devtoggle" role="group" aria-label={fa ? "حالت نمایش (فقط دمو)" : "Orb mode (DEMO only)"} dir="ltr">
          <span className="ahos-orb-devtag">DEMO</span>
          {MODES.map((m) => (
            <button
              key={m}
              type="button"
              data-testid={`orb-mode-${m}`}
              aria-pressed={mode === m}
              onClick={() => pick(m)}
            >
              {MODE_LABEL[m][language]}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}