"use client";

import { useCallback, useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import dynamic from "next/dynamic";
import {
  Clock3,
  Cloudy,
  Crosshair,
  Globe2,
  Layers,
  MapPin,
  Minus,
  Pause,
  Play,
  Plus,
  RotateCcw,
  Sun,
  Sunrise,
  Sunset,
  Tag,
  Undo2,
  Waypoints,
  X,
} from "lucide-react";
import type { DataMeta, EarthOverview } from "@/lib/api/types";
import { useI18n } from "@/lib/i18n";
import { useFormat } from "@/lib/format";
import { useSettings } from "@/lib/settings/provider";
import { useSound } from "@/lib/audio/use-sound";
import { useNow, useNowMinute } from "@/lib/time/now";
import { EXCHANGES, formatCountdown, sessionState } from "@/lib/time/sessions";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Chip } from "@/components/ui/chip";
import { Delta, Num, TimeAgo } from "@/components/ui/primitives";
import { Segmented } from "@/components/ui/segmented";
import { StatusChip } from "@/components/ui/status";
import { Tip } from "@/components/ui/tooltip";
import { CardFooter } from "@/components/cards/data-card";
import { GLOBE_EVENT, type GlobeCommand } from "@/components/layout/palette-context";
import type { GlobeHandle, RenderedLabel } from "./globe-canvas";
import { GlobeFallback2D } from "./globe-fallback";
import type { GlobeLayers } from "./scene";
import { TEHRAN } from "./scene-constants";
import { computeSunInfo } from "./sun";

const GlobeCanvas = dynamic(() => import("./globe-canvas"), { ssr: false });

/* WebGL capability as an external store (null during SSR). */
const subscribeNoop = () => () => {};
let webglCache: boolean | null = null;
function getWebGL(): boolean {
  if (webglCache === null) {
    try {
      const c = document.createElement("canvas");
      webglCache = !!(c.getContext("webgl2") || c.getContext("webgl"));
    } catch {
      webglCache = false;
    }
  }
  return webglCache;
}
const useWebGL = () => useSyncExternalStore(subscribeNoop, getWebGL, () => null);

export interface GlobeHeroProps {
  earth: EarthOverview;
  meta: DataMeta;
  variant?: "hero" | "full";
  initialFocus?: "global" | "iran";
  className?: string;
}

export function GlobeHero({ earth, meta, variant = "hero", initialFocus = "global", className }: GlobeHeroProps) {
  const { t, l, tx, dir } = useI18n();
  const f = useFormat();
  const { budget, reducedMotion, settings } = useSettings();
  const play = useSound();
  const webgl = useWebGL();
  const minute = useNowMinute();
  const now = useNow();

  const [mode, setMode] = useState<"3d" | "2d">("3d");
  const [layers, setLayers] = useState<GlobeLayers>({ labels: true, atmosphere: true, markers: true, links: true });
  const [autoRotate, setAutoRotate] = useState(true);
  const [focus, setFocus] = useState<"global" | "iran">(initialFocus);
  const [ready, setReady] = useState(false);
  const [failed, setFailed] = useState(false);
  const [hoverIran, setHoverIran] = useState(false);
  const globeRef = useRef<GlobeHandle>(null);

  const use3d = webgl === true && !failed && mode === "3d";
  const sun = useMemo(() => (minute === null ? null : computeSunInfo(minute)), [minute]);

  const flyIran = useCallback(() => {
    setFocus("iran");
    globeRef.current?.flyTo("iran");
    play("whoosh");
  }, [play]);
  const backGlobal = useCallback(() => {
    setFocus("global");
    globeRef.current?.flyTo("global");
    play("whoosh");
  }, [play]);

  // Command bus (palette / chat).
  useEffect(() => {
    const onCmd = (e: Event) => {
      const cmd = (e as CustomEvent<GlobeCommand>).detail;
      if (cmd === "fly-iran") flyIran();
      else backGlobal();
    };
    window.addEventListener(GLOBE_EVENT, onCmd);
    return () => window.removeEventListener(GLOBE_EVENT, onCmd);
  }, [flyIran, backGlobal]);

  const toggleLayer = (k: keyof GlobeLayers) => {
    setLayers((prev) => ({ ...prev, [k]: !prev[k] }));
    play("tick");
  };

  const labels: RenderedLabel[] = useMemo(() => {
    const list: RenderedLabel[] = [
      {
        id: "iran",
        lat: 33.2,
        lng: 54.6,
        kind: "iran",
        node: (
          <button
            type="button"
            onClick={flyIran}
            className="pointer-events-auto group flex items-center gap-1.5 rounded-full border border-gold-300/60 bg-ink-950/75 py-0.5 pe-2.5 ps-1.5 text-2xs font-bold text-gold-100 shadow-[0_0_18px_rgb(230_191_95/0.55)] backdrop-blur-sm transition-transform hover:scale-105"
            aria-label={`${t.globe.iranTitle} — ${t.globe.flyIran}`}
          >
            <span aria-hidden className="relative flex size-2">
              <span className="absolute inset-0 rounded-full bg-gold-300 animate-ping-slow motion-off:hidden" />
              <span className="relative size-2 rounded-full bg-gold-200" />
            </span>
            {t.globe.iranTitle}
            <span className="text-3xs font-medium tracking-widest text-gold-300/80" dir="ltr">
              IRAN
            </span>
          </button>
        ),
      },
    ];
    const ordered = [...earth.centers].sort((a, b) => a.tier - b.tier);
    for (const c of ordered) {
      if (c.id === "tehran") {
        if (focus === "iran")
          list.push({
            id: c.id,
            lat: c.lat,
            lng: c.lng,
            kind: "center",
            node: <span className="whitespace-nowrap rounded-full bg-ink-950/70 px-1.5 py-px text-3xs font-semibold text-gold-100 ring-1 ring-gold-400/40">{l(c.name)}</span>,
          });
        continue;
      }
      if (c.tier > 2) continue;
      list.push({
        id: c.id,
        lat: c.lat,
        lng: c.lng,
        kind: "center",
        node: (
          <span className="flex translate-y-3 items-center gap-1 whitespace-nowrap rounded-full bg-ink-950/65 px-1.5 py-px text-3xs text-fg-2 ring-1 ring-data-400/25 backdrop-blur-[2px]">
            {l(c.name)}
            {c.tier === 1 && c.indexChange !== null && <Delta value={c.indexChange} size="xs" className="text-3xs" />}
          </span>
        ),
      });
    }
    if (sun) {
      list.push({
        id: "sun",
        lat: sun.subsolarLat,
        lng: sun.subsolarLng,
        kind: "sun",
        node: (
          <span className="flex items-center gap-1 whitespace-nowrap text-3xs text-gold-200">
            <Sun aria-hidden className="size-3.5 text-[#ffd678] drop-shadow-[0_0_6px_#ffd678]" />
            {t.globe.subsolar}
          </span>
        ),
      });
    }
    return list;
  }, [earth.centers, focus, flyIran, l, sun, t]);

  const tse = minute === null ? null : sessionState(EXCHANGES.find((e) => e.id === "tse-ir")!, new Date(minute));
  const stageH = variant === "full" ? "h-[min(70vh,720px)] min-h-[520px]" : "h-[440px] @6xl:h-[470px]";
  const tipSide = dir === "rtl" ? "left" : "right";

  return (
    <section aria-labelledby="globe-title" className={cn("glass gold-border relative isolate flex min-w-0 flex-col overflow-hidden", className)}>
      <div className={cn("relative overflow-hidden rounded-t-[var(--radius-lg)]", stageH)}>
        {/* backdrop */}
        <div aria-hidden className="absolute inset-0 bg-[radial-gradient(60%_70%_at_50%_50%,rgb(37_58_94/0.45),transparent_70%)]" />
        <div aria-hidden className="absolute inset-0 bg-[radial-gradient(35%_45%_at_50%_52%,rgb(230_191_95/0.10),transparent_70%)]" />

        {webgl === null ? null : use3d ? (
          <GlobeCanvas
            ref={globeRef}
            budget={budget}
            initialView={focus}
            reducedMotion={reducedMotion}
            autoRotate={autoRotate}
            layers={layers}
            centers={earth.centers}
            links={earth.links}
            labels={labels}
            ariaLabel={t.globe.canvasLabel}
            onIranClick={flyIran}
            onIranHover={setHoverIran}
            onRenderingChange={() => undefined}
            onTexturesReady={() => setReady(true)}
            onError={(err) => {
              console.error("[globe]", err);
              setFailed(true);
            }}
          />
        ) : (
          <GlobeFallback2D centers={earth.centers} focusIran={focus === "iran"} nowMs={minute} onIranClick={flyIran} showLabels={layers.labels} showMarkers={layers.markers} />
        )}

        {/* loading veil */}
        {use3d && !ready && (
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center gap-3" role="status">
            <span className="size-10 rounded-full border-2 border-gold-400/20 border-t-gold-300 animate-spin" />
            <span className="text-2xs text-fg-3">{t.globe.loading}</span>
          </div>
        )}

        {/* HUD: title (top-start) */}
        <div className="pointer-events-none absolute start-4 top-3.5 max-w-[46%]">
          <div className="flex items-center gap-2">
            <Globe2 aria-hidden className="size-4 text-gold-300" />
            <h2 id="globe-title" className="text-sm font-semibold text-fg-1">
              {t.globe.title}
            </h2>
            <Chip tone="gold" icon={Sun} className="pointer-events-auto">
              {t.globe.computedLocally}
            </Chip>
          </div>
          <p className="mt-0.5 text-2xs text-fg-3">{t.globe.subtitle}</p>
          {(webgl === false || failed) && <p className="mt-1 text-2xs text-warn">{t.globe.fallback}</p>}
        </div>

        {/* HUD: layers + mode (top-end) */}
        <div className="absolute end-3 top-3 flex items-center gap-1.5">
          <div role="group" aria-label={t.globe.layers} className="glass-strong flex items-center gap-0.5 rounded-[var(--radius-md)] p-0.5">
            <Layers aria-hidden className="mx-1 size-3.5 text-fg-4" />
            {(
              [
                ["labels", Tag, t.globe.layerLabels],
                ["atmosphere", Cloudy, t.globe.layerAtmosphere],
                ["markers", MapPin, t.globe.layerMarkers],
                ["links", Waypoints, t.globe.layerLinks],
              ] as const
            ).map(([k, Icon, label]) => (
              <Tip key={k} content={label} side="bottom">
                <Button variant={layers[k] ? "active" : "ghost"} size="icon-xs" aria-pressed={layers[k]} aria-label={label} onClick={() => toggleLayer(k)} disabled={k === "atmosphere" && !use3d}>
                  <Icon aria-hidden />
                </Button>
              </Tip>
            ))}
          </div>
          <Segmented
            label={tx("حالت نمایش", "View mode")}
            size="xs"
            value={use3d ? "3d" : "2d"}
            onChange={(v) => {
              setMode(v);
              setReady(false);
              play("tick");
            }}
            options={[
              { value: "3d", label: t.globe.view3d, title: t.globe.view3d },
              { value: "2d", label: t.globe.view2d, title: t.globe.view2d },
            ]}
            className="glass-strong"
          />
        </div>

        {/* HUD: controls (bottom-start) */}
        <div className="absolute bottom-3 start-3 flex items-center gap-1.5">
          <div className="glass-strong flex items-center gap-0.5 rounded-[var(--radius-md)] p-0.5" role="toolbar" aria-label={tx("کنترل‌های کره", "Globe controls")}>
            <Tip content={autoRotate ? t.globe.pause : t.globe.resume} side="top">
              <Button variant="ghost" size="icon-sm" aria-pressed={!autoRotate} aria-label={autoRotate ? t.globe.pause : t.globe.resume} onClick={() => setAutoRotate((a) => !a)} disabled={!use3d || reducedMotion}>
                {autoRotate && !reducedMotion ? <Pause aria-hidden /> : <Play aria-hidden />}
              </Button>
            </Tip>
            <Tip content={t.globe.zoomIn} side="top">
              <Button variant="ghost" size="icon-sm" aria-label={t.globe.zoomIn} onClick={() => globeRef.current?.zoom(0.78)} disabled={!use3d}>
                <Plus aria-hidden />
              </Button>
            </Tip>
            <Tip content={t.globe.zoomOut} side="top">
              <Button variant="ghost" size="icon-sm" aria-label={t.globe.zoomOut} onClick={() => globeRef.current?.zoom(1.28)} disabled={!use3d}>
                <Minus aria-hidden />
              </Button>
            </Tip>
            <Tip content={t.globe.reset} side="top">
              <Button variant="ghost" size="icon-sm" aria-label={t.globe.reset} onClick={backGlobal}>
                <RotateCcw aria-hidden />
              </Button>
            </Tip>
          </div>
          {focus === "iran" ? (
            <Button variant="outline" size="sm" onClick={backGlobal} className="glass-strong">
              <Undo2 aria-hidden className="rtl:-scale-x-100" />
              {t.globe.backGlobal}
            </Button>
          ) : (
            <Button variant="gold" size="sm" onClick={flyIran}>
              <Crosshair aria-hidden />
              {t.globe.flyIran}
            </Button>
          )}
        </div>

        {/* HUD: sun info (bottom-end) */}
        {focus !== "iran" && sun && (
          <div className="glass-strong absolute bottom-3 end-3 hidden w-[230px] rounded-[var(--radius-md)] p-2.5 text-2xs @2xl:block">
            <div className="mb-1.5 flex items-center gap-1.5 text-fg-2">
              <Sun aria-hidden className="size-3.5 text-[#ffd678]" />
              <span className="font-semibold">{t.globe.tehranSun}</span>
              <Chip tone={sun.isDayInTehran ? "gold" : "slate"} className="ms-auto">
                {sun.isDayInTehran ? t.globe.day : t.globe.night}
              </Chip>
            </div>
            <dl className="grid grid-cols-2 gap-x-3 gap-y-1">
              <dt className="text-fg-4">{t.globe.elevation}</dt>
              <dd className="text-end">
                <Num className="text-fg-1">{f.num(sun.tehranElevation, 1)}°</Num>
              </dd>
              <dt className="flex items-center gap-1 text-fg-4">
                <Sunrise aria-hidden className="size-3" />
                {t.globe.sunrise}
              </dt>
              <dd className="text-end">
                <Num className="text-fg-1">{f.time(sun.sunrise, { timeZone: "Asia/Tehran" })}</Num>
              </dd>
              <dt className="flex items-center gap-1 text-fg-4">
                <Sunset aria-hidden className="size-3" />
                {t.globe.sunset}
              </dt>
              <dd className="text-end">
                <Num className="text-fg-1">{f.time(sun.sunset, { timeZone: "Asia/Tehran" })}</Num>
              </dd>
              <dt className="text-fg-4">{t.globe.subsolar}</dt>
              <dd className="text-end">
                <Num className="text-fg-2">
                  {f.num(Math.abs(sun.subsolarLat), 1)}°{sun.subsolarLat >= 0 ? "N" : "S"} {f.num(Math.abs(sun.subsolarLng), 1)}°{sun.subsolarLng >= 0 ? "E" : "W"}
                </Num>
              </dd>
            </dl>
          </div>
        )}

        {/* Iran panel (end side) */}
        {focus === "iran" && (
          <aside aria-label={t.globe.iranTitle} className="glass-strong gold-border absolute bottom-3 end-3 top-14 flex w-[290px] max-w-[calc(100%-1.5rem)] flex-col overflow-hidden rounded-[var(--radius-lg)] animate-rise-in">
            <header className="flex items-start gap-2 border-b border-[var(--line-hairline)] px-3 py-2.5">
              <span aria-hidden className="mt-0.5 flex size-7 items-center justify-center rounded-full border border-gold-300/50 bg-gold-400/10 text-gold-200 shadow-[var(--shadow-glow-sm)]">
                <MapPin className="size-3.5" />
              </span>
              <div className="min-w-0 flex-1">
                <h3 className="text-sm font-bold text-gold-100">{t.globe.iranTitle}</h3>
                <p className="text-3xs text-fg-4">{t.globe.iranSubtitle}</p>
              </div>
              <Tip content={t.globe.backGlobal} side={tipSide}>
                <Button variant="ghost" size="icon-xs" aria-label={t.globe.backGlobal} onClick={backGlobal}>
                  <X aria-hidden />
                </Button>
              </Tip>
            </header>
            <div className="min-h-0 flex-1 space-y-2.5 overflow-y-auto p-3 text-2xs">
              <div className="grid grid-cols-2 gap-2">
                <div className="rounded-[var(--radius-md)] border border-[var(--line-subtle)] bg-white/[0.02] p-2">
                  <div className="flex items-center gap-1 text-3xs text-fg-4">
                    <Clock3 aria-hidden className="size-3" />
                    {t.globe.localTime}
                  </div>
                  <Num className="mt-0.5 text-base font-semibold text-gold-100">
                    <span suppressHydrationWarning>{now ? f.time(now, { seconds: true, timeZone: "Asia/Tehran" }) : "--:--:--"}</span>
                  </Num>
                  <div className="text-3xs text-fg-5">{now ? f.date(now, { timeZone: "Asia/Tehran", withYear: true }) : ""}</div>
                </div>
                <div className="rounded-[var(--radius-md)] border border-[var(--line-subtle)] bg-white/[0.02] p-2">
                  <div className="text-3xs text-fg-4">{tx("بورس تهران", "Tehran SE")}</div>
                  {tse && (
                    <>
                      <Chip tone={tse.open ? "up" : "slate"} className="mt-1">
                        {tse.open ? t.topbar.open : t.topbar.closed}
                      </Chip>
                      <div className="mt-1 text-3xs text-fg-5">{tse.open ? t.topbar.closesIn(f.digits(formatCountdown(tse.minutesToChange))) : t.topbar.opensIn(f.digits(formatCountdown(tse.minutesToChange)))}</div>
                    </>
                  )}
                </div>
              </div>
              {sun && (
                <div className="flex items-center justify-between rounded-[var(--radius-md)] border border-[var(--line-subtle)] bg-white/[0.02] px-2 py-1.5">
                  <span className="flex items-center gap-1 text-fg-3">
                    <Sunrise aria-hidden className="size-3 text-[#ffd678]" />
                    <Num>{f.time(sun.sunrise, { timeZone: "Asia/Tehran" })}</Num>
                  </span>
                  <span className="text-fg-4">
                    {t.globe.elevation} <Num className="text-fg-1">{f.num(sun.tehranElevation, 1)}°</Num>
                  </span>
                  <span className="flex items-center gap-1 text-fg-3">
                    <Sunset aria-hidden className="size-3 text-warn" />
                    <Num>{f.time(sun.sunset, { timeZone: "Asia/Tehran" })}</Num>
                  </span>
                </div>
              )}
              <p className="text-3xs leading-relaxed text-fg-4">{l(earth.iran.summary)}</p>
              <ul className="space-y-1.5">
                {earth.iran.indicators.map((ind) => (
                  <li key={ind.id} className="rounded-[var(--radius-md)] border border-[var(--line-subtle)] bg-white/[0.02] px-2 py-1.5">
                    <div className="flex items-center justify-between gap-2">
                      <span className="truncate text-fg-2">{l(ind.label)}</span>
                      <StatusChip status={ind.status} />
                    </div>
                    <div className="mt-0.5 flex items-baseline justify-between gap-2">
                      <span className="flex items-baseline gap-1">
                        <Num className={cn("text-sm font-semibold", ind.value === null ? "text-fg-4" : "text-fg-1")}>{f.num(ind.value, ind.decimals)}</Num>
                        <span className="text-3xs text-fg-4">{ind.value === null ? "" : l(ind.unit)}</span>
                      </span>
                      <Delta value={ind.change} size="xs" />
                    </div>
                    <div className="mt-0.5 flex items-center justify-between text-3xs text-fg-5">
                      <bdi>{ind.source}</bdi>
                      <TimeAgo iso={ind.retrievedAt} />
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </aside>
        )}

        {/* hover hint */}
        {hoverIran && focus !== "iran" && (
          <div className="pointer-events-none absolute left-1/2 top-14 -translate-x-1/2 rounded-full border border-gold-400/40 bg-ink-950/80 px-3 py-1 text-2xs text-gold-100 shadow-[var(--shadow-glow-sm)]">
            {t.globe.flyIran}
          </div>
        )}

        {/* legend */}
        <div className="pointer-events-none absolute bottom-3 left-1/2 hidden -translate-x-1/2 items-center gap-3 rounded-full bg-ink-950/50 px-3 py-1 text-3xs text-fg-4 backdrop-blur-sm @4xl:flex">
          <span className="flex items-center gap-1">
            <span aria-hidden className="h-0.5 w-4 rounded bg-gold-300 shadow-[0_0_6px_var(--color-gold-300)]" />
            {t.globe.iranTitle}
          </span>
          <span className="flex items-center gap-1">
            <span aria-hidden className="size-1.5 rounded-full bg-data-400" />
            {tx("مراکز مالی", "Financial hubs")}
          </span>
          <span className="flex items-center gap-1">
            <span aria-hidden className="h-px w-4 border-t border-dashed border-data-400" />
            {t.globe.layerLinks}
          </span>
          <span className="hidden items-center gap-1 @6xl:flex" dir="ltr">
            <span className="mono text-fg-5">
              {settings.quality.toUpperCase()} · {budget.textureSize / 1024}K · {budget.fpsCap}fps{budget.bloom ? " · bloom" : ""}
            </span>
          </span>
        </div>
      </div>
      <CardFooter meta={meta} extra={<span className="hidden shrink-0 items-center gap-1 text-fg-4 @3xl:flex"><Sun aria-hidden className="size-3 text-[#ffd678]" />{tx("خورشید: محاسبه محلی (NOAA)", "Sun: computed locally (NOAA)")}</span>} />
    </section>
  );
}

export { TEHRAN };
