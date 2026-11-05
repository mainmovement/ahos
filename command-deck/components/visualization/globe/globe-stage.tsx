"use client";

import dynamic from "next/dynamic";
import { Component, useEffect, useMemo, useState, type ReactNode, Suspense } from "react";
import {
  Eye,
  EyeOff,
  Globe2,
  MoonStar,
  Sun as SunIcon,
  Sunrise as SunriseIcon,
  Sunset as SunsetIcon,
  Flower2,
  Leaf,
  Snowflake,
  ShieldCheck,
  Rss,
  Armchair,
  Orbit,
  Video,
  CloudSun,
  X as CloseIcon,
} from "lucide-react";
import { useLocale } from "@/components/providers/locale-provider";
import { useSettings } from "@/components/providers/settings-provider";
import { AMBIENCE } from "@/lib/visualization/ambience";
import type { AmbiencePreset, SceneView, SeasonPreset } from "@/lib/types";
import { GlobeFallback } from "./globe-fallback";
import { Button } from "@/components/ui/button";
import { Emblem } from "@/components/brand/emblem";
import { NEWS_EVENTS } from "@/lib/data/intelligence";
import { cn } from "@/lib/utils";
import { getMarketBus, type MarketSnapshot } from "@/lib/live/market-bus";
import { classifyWmo, computePortfolio, fmtPct, fmtQty, fmtUsd } from "@/lib/live/derive";
import { ROLE_ASSETS, buildRoomTexts, type RoleId } from "@/lib/live/room-texts";

const GlobeScene = dynamic(() => import("./globe-scene"), {
  ssr: false,
  loading: () => <GlobeFallback reduced={false} skeleton />,
});

const CommandRoomScene = dynamic(() => import("./command-room-scene"), {
  ssr: false,
  loading: () => <GlobeFallback reduced={false} skeleton />,
});

/** Catches runtime WebGL/three failures and drops to the 2D fallback. */
class SceneBoundary extends Component<{ onFail: () => void; children: ReactNode }, { failed: boolean }> {
  constructor(props: { onFail: () => void; children: ReactNode }) {
    super(props);
    this.state = { failed: false };
  }
  static getDerivedStateFromError() {
    return { failed: true };
  }
  override componentDidCatch() {
    this.props.onFail();
  }
  override render() {
    if (this.state.failed) return null;
    return this.props.children;
  }
}

/* ------------------------------------------------------------------ */
/* live-data hooks + floating panels                                   */

function useLiveMarket(): MarketSnapshot {
  const [snap, setSnap] = useState<MarketSnapshot>(() => getMarketBus().getSnapshot());
  useEffect(() => {
    const bus = getMarketBus();
    const unsubscribe = bus.subscribe(() => setSnap(bus.getSnapshot()));
    setSnap(bus.getSnapshot());
    return unsubscribe;
  }, []);
  return snap;
}

/** Live weather chip — real Dezful/Khuzestan conditions; no numbers when offline. */
function WeatherChip({ title, offline, live, cond }: { title: string; offline: string; live: string; cond: Record<string, string> }) {
  const snap = useLiveMarket();
  const wx = snap.weather;
  const isLive = wx.status === "live" && wx.temperature != null;
  const kind = classifyWmo(wx.code);
  return (
    <div
      data-weather-chip
      className="absolute start-3 top-12 z-10 inline-flex max-w-[70%] items-center gap-1.5 whitespace-nowrap rounded-full border border-border-strong bg-navy-950/70 px-2.5 py-1 text-[10px] font-semibold text-muted-foreground backdrop-blur-md light:bg-white/80"
    >
      <CloudSun className="size-3 shrink-0 text-sky-300" aria-hidden />
      <span className="text-foreground/90">{title}</span>
      {isLive ? (
        <>
          <span aria-hidden>·</span>
          <span className="tabular-nums text-foreground">{Math.round(wx.temperature ?? 0)}°</span>
          <span>{cond[kind]}</span>
          <span className="text-success">● {live}</span>
        </>
      ) : (
        <span className="text-amber-500">○ {offline}</span>
      )}
    </div>
  );
}

/** Role workstation panel — opened by clicking a floating chip or a desk tablet. */
function RolePanel({ role, onClose }: { role: RoleId; onClose: () => void }) {
  const snap = useLiveMarket();
  const { dict, locale } = useLocale();
  const texts = useMemo(() => buildRoomTexts(dict, locale), [dict, locale]);
  const assets = ROLE_ASSETS[role];
  const totals = computePortfolio(snap.assets);
  const tapeId = assets.find((id) => snap.assets[id].tape.length > 0);

  return (
    <div
      data-role-panel
      dir={texts.locale === "fa" ? "rtl" : "ltr"}
      className="absolute bottom-24 left-1/2 z-30 max-h-[54%] w-80 max-w-[82%] -translate-x-1/2 overflow-y-auto rounded-xl border border-border-strong bg-navy-950/92 p-3 text-xs shadow-panel backdrop-blur-md light:bg-white/97"
    >
      <div className="mb-2 flex items-center justify-between gap-2">
        <p className="text-sm font-bold text-foreground">{texts.roles[role]}</p>
        <button
          type="button"
          aria-label={texts.panel.close}
          onClick={onClose}
          className="rounded p-1 text-muted-foreground transition-colors hover:text-foreground"
        >
          <CloseIcon className="size-3.5" aria-hidden />
        </button>
      </div>

      {assets.length > 0 ? (
        <ul className="space-y-1.5">
          {assets.map((id) => {
            const q = snap.assets[id];
            return (
              <li key={id} className="flex items-center justify-between gap-2 rounded-md bg-white/5 px-2 py-1.5 light:bg-black/5">
                <span className="font-semibold text-foreground/90">{texts.market.assets[id]}</span>
                <span className="flex items-center gap-2">
                  {q.price != null ? (
                    <>
                      <span className="font-bold tabular-nums text-foreground">${fmtUsd(q.price)}</span>
                      <span className={cn("font-semibold tabular-nums", (q.change24h ?? 0) >= 0 ? "text-emerald-400" : "text-red-400")}>
                        {fmtPct(q.change24h)}
                      </span>
                    </>
                  ) : (
                    <span className="text-muted-foreground">—</span>
                  )}
                  <span
                    className={cn(
                      "size-1.5 rounded-full",
                      q.status === "live" ? "bg-emerald-400" : q.status === "stale" ? "bg-amber-400" : "bg-muted-foreground/50",
                    )}
                    title={q.source ?? undefined}
                  />
                </span>
              </li>
            );
          })}
          <li>
            {tapeId ? (
              <div className="mt-1">
                <p className="mb-1 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">{texts.market.tape}</p>
                <ul className="space-y-0.5">
                  {snap.assets[tapeId].tape.slice(0, 4).map((tick, i) => (
                    <li key={i} className="flex items-center justify-between gap-2 tabular-nums text-[10px] text-muted-foreground">
                      <span>{new Date(tick.time).toLocaleTimeString("en-GB")}</span>
                      <span className="text-foreground/80">${fmtUsd(tick.price)}</span>
                      <span>{fmtQty(tick.qty)}</span>
                      <span className={tick.buyerMaker ? "text-red-400" : "text-emerald-400"}>
                        {tick.buyerMaker ? texts.market.sell : texts.market.buy}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="mt-1 text-[10px] text-muted-foreground">{texts.panel.noTape}</p>
            )}
          </li>
        </ul>
      ) : role === "news" ? (
        snap.news.status === "live" && snap.news.items.length > 0 ? (
          <ul className="space-y-1.5">
            {snap.news.items.slice(0, 5).map((item, i) => (
              <li key={i} className="flex gap-1.5 leading-snug text-foreground/85">
                <span className="mt-1.5 size-1 shrink-0 rounded-full bg-accent/70" aria-hidden />
                {item.title}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-muted-foreground">{texts.market.offlineNews}</p>
        )
      ) : role === "liaison" ? (
        totals.totalUsd != null ? (
          <div className="space-y-1.5">
            <p className="rounded-md bg-white/5 px-2 py-1.5 light:bg-black/5">
              <span className="text-muted-foreground">{texts.market.portfolioTitle}: </span>
              <span className="font-bold tabular-nums text-accent">${fmtUsd(totals.totalUsd)}</span>
            </p>
            {totals.pnlTodayUsd != null ? (
              <p className="rounded-md bg-white/5 px-2 py-1.5 light:bg-black/5">
                <span className="text-muted-foreground">{texts.market.pnl}: </span>
                <span className={cn("font-bold tabular-nums", totals.pnlTodayUsd >= 0 ? "text-emerald-400" : "text-red-400")}>
                  {totals.pnlTodayUsd >= 0 ? "+" : "−"}${fmtUsd(Math.abs(totals.pnlTodayUsd))}
                </span>
              </p>
            ) : null}
            <p className="text-[10px] text-muted-foreground">{texts.market.demoNote}</p>
          </div>
        ) : (
          <p className="text-muted-foreground">{texts.market.notConnected}</p>
        )
      ) : (
        <p className="leading-relaxed text-muted-foreground">{texts.panel.sampleNotice}</p>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* decorative chamber layers                                           */

/** City skyline seen from the command chamber (pure SVG, no bitmaps). */
function Skyline() {
  return (
    <svg
      aria-hidden
      viewBox="0 0 1200 120"
      preserveAspectRatio="none"
      className="pointer-events-none absolute inset-x-0 bottom-0 h-[13%] w-full"
    >
      <g fill="#050912" opacity="0.85">
        <rect x="0" y="66" width="74" height="54" />
        <rect x="60" y="46" width="52" height="74" />
        <rect x="104" y="78" width="66" height="42" />
        <rect x="170" y="34" width="40" height="86" />
        <rect x="206" y="60" width="58" height="60" />
        <rect x="268" y="72" width="72" height="48" />
        <rect x="338" y="24" width="34" height="96" />
        <rect x="368" y="56" width="52" height="64" />
        <rect x="430" y="70" width="60" height="50" />
        <rect x="498" y="40" width="44" height="80" />
        <rect x="546" y="64" width="66" height="56" />
        <rect x="616" y="30" width="38" height="90" />
        <rect x="656" y="58" width="54" height="62" />
        <rect x="718" y="74" width="70" height="46" />
        <rect x="792" y="38" width="42" height="82" />
        <rect x="838" y="62" width="58" height="58" />
        <rect x="900" y="26" width="36" height="94" />
        <rect x="938" y="56" width="52" height="64" />
        <rect x="994" y="72" width="66" height="48" />
        <rect x="1064" y="42" width="44" height="78" />
        <rect x="1112" y="64" width="88" height="56" />
      </g>
      <g fill="#D4AF37" opacity="0.35">
        <circle cx="78" cy="60" r="1.1" /><circle cx="96" cy="72" r="1.1" />
        <circle cx="186" cy="52" r="1.1" /><circle cx="198" cy="70" r="1.1" />
        <circle cx="352" cy="44" r="1.1" /><circle cx="364" cy="66" r="1.1" />
        <circle cx="514" cy="58" r="1.1" /><circle cx="630" cy="48" r="1.1" />
        <circle cx="806" cy="56" r="1.1" /><circle cx="916" cy="44" r="1.1" />
        <circle cx="1082" cy="60" r="1.1" />
      </g>
      <g fill="#22D3EE" opacity="0.4">
        <circle cx="88" cy="84" r="1" /><circle cx="230" cy="80" r="1" />
        <circle cx="390" cy="76" r="1" /><circle cx="566" cy="84" r="1" />
        <circle cx="672" cy="78" r="1" /><circle cx="852" cy="82" r="1" />
        <circle cx="954" cy="76" r="1" /><circle cx="1130" cy="84" r="1" />
      </g>
    </svg>
  );
}

/** Standing operator silhouette facing the hologram. */
function OperatorFigure({ className }: { className?: string }) {
  return (
    <svg
      aria-hidden
      viewBox="0 0 140 260"
      className={cn("pointer-events-none select-none", className)}
    >
      <defs>
        <linearGradient id="op-body" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#0A1120" />
          <stop offset="100%" stopColor="#04070E" />
        </linearGradient>
        <linearGradient id="op-rim" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#22D3EE" stopOpacity="0.85" />
          <stop offset="100%" stopColor="#22D3EE" stopOpacity="0" />
        </linearGradient>
      </defs>
      <ellipse cx="70" cy="250" rx="46" ry="6" fill="#22D3EE" opacity="0.07" />
      <path
        d="M70 48 C52 52 45 60 43 74 L37 132 L31 232 L48 236 L56 168 L60 236 L84 236 L88 166 L93 232 L109 228 L103 130 L97 72 C95 58 88 52 70 48 Z"
        fill="url(#op-body)"
      />
      <ellipse cx="70" cy="27" rx="13.5" ry="15.5" fill="#060B15" />
      <path d="M43 74 L37 132 L31 232" fill="none" stroke="url(#op-rim)" strokeWidth="2" opacity="0.55" />
      <path d="M52 64 L60 96 L58 130" fill="none" stroke="#16233C" strokeWidth="1.4" opacity="0.7" />
      <path d="M88 64 L80 96 L82 130" fill="none" stroke="#16233C" strokeWidth="1.4" opacity="0.7" />
    </svg>
  );
}

/** Golden platform sigil under the hologram. */
function PlatformSigil() {
  return (
    <div
      aria-hidden
      className="pointer-events-none absolute bottom-[10%] left-1/2 -translate-x-1/2 -translate-y-1/2 opacity-90"
    >
      <div className="relative grid size-20 place-items-center sm:size-24">
        <span className="absolute inset-0 rounded-full border border-primary/30" />
        <span className="absolute inset-2 rounded-full border border-dashed border-primary/25 [animation:spin_46s_linear_infinite]" />
        <Emblem className="size-10 opacity-85 drop-shadow-[0_0_16px_rgba(212,175,55,0.6)] sm:size-12" animated={false} />
      </div>
    </div>
  );
}

/** Recent sample events — slow marquee ticker along the stage floor. */
function EventsTicker() {
  const { dict, locale } = useLocale();
  const items = NEWS_EVENTS.filter((e) => e.at !== null).slice(0, 6);
  const line = items.map((event) => event.title[locale]);
  // duplicated once for a seamless loop (decorative, aria-hidden)
  return (
    <div
      className="pointer-events-none absolute inset-x-0 bottom-0 z-[5] overflow-hidden border-t border-border/50 bg-navy-950/60 backdrop-blur-sm light:bg-white/60"
    >
      <div className="flex items-center gap-2 py-1.5">
        <span className="flex shrink-0 items-center gap-1.5 border-e border-border/60 px-3 text-[9px] font-bold uppercase tracking-[0.12em] text-primary/90">
          <Rss className="size-3" aria-hidden />
          {dict.command.eventsTicker}
        </span>
        <div className="ticker-track flex min-w-0 shrink items-center gap-8 whitespace-nowrap" aria-hidden>
          {[...line, ...line].map((title, i) => (
            <span key={i} className="flex items-center gap-2 text-[10px] text-muted-foreground">
              <span className="inline-block size-1 rounded-full bg-primary/60" />
              {title}
            </span>
          ))}
        </div>
      </div>
      <span className="sr-only">{dict.common.sample}</span>
    </div>
  );
}

function CornerBrackets() {
  const base = "pointer-events-none absolute size-5 border-primary/35";
  return (
    <div aria-hidden className="absolute inset-3">
      <span className={cn(base, "start-0 top-0 border-s-2 border-t-2")} />
      <span className={cn(base, "end-0 top-0 border-e-2 border-t-2")} />
      <span className={cn(base, "start-0 bottom-0 border-b-2 border-s-2")} />
      <span className={cn(base, "end-0 bottom-0 border-b-2 border-e-2")} />
    </div>
  );
}

/* ------------------------------------------------------------------ */

export function GlobeStage({ className }: { className?: string }) {
  const { dict, locale } = useLocale();
  const { prefs, setPref, reducedMotion, hydrated } = useSettings();
  const [webglFailed, setWebglFailed] = useState(false);
  const [focusedRole, setFocusedRole] = useState<RoleId | null>(null);

  const showScene = hydrated && prefs.sceneEnabled && !reducedMotion && !webglFailed;
  const preset: AmbiencePreset = prefs.ambience;
  const season: SeasonPreset = prefs.season ?? "spring";
  const view: SceneView = prefs.sceneView ?? "room";
  const roomTexts = useMemo(() => buildRoomTexts(dict, locale), [dict, locale]);

  useEffect(() => {
    if (focusedRole === null) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setFocusedRole(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [focusedRole]);

  const ambienceOptions: Array<{ id: AmbiencePreset; label: string; icon: typeof MoonStar }> = [
    { id: "dawn", label: dict.command.ambienceDawn, icon: SunriseIcon },
    { id: "day", label: dict.command.ambienceDay, icon: SunIcon },
    { id: "dusk", label: dict.command.ambienceDusk, icon: SunsetIcon },
    { id: "night", label: dict.command.ambienceNight, icon: MoonStar },
  ];
  const seasons: Array<{ id: SeasonPreset; label: string; icon: typeof Flower2 }> = [
    { id: "spring", label: dict.command.seasonSpring, icon: Flower2 },
    { id: "summer", label: dict.command.seasonSummer, icon: SunIcon },
    { id: "autumn", label: dict.command.seasonAutumn, icon: Leaf },
    { id: "winter", label: dict.command.seasonWinter, icon: Snowflake },
  ];
  const cycleSeason = () => {
    const idx = seasons.findIndex((s) => s.id === season);
    setPref("season", seasons[(idx + 1) % seasons.length].id);
  };
  const SeasonIcon = (seasons.find((s) => s.id === season) ?? seasons[0]).icon;

  const viewOptions: Array<{ id: SceneView; label: string; icon: typeof Orbit }> = [
    { id: "room", label: dict.command.viewRoom, icon: Armchair },
    { id: "space", label: dict.command.viewSpace, icon: Orbit },
    { id: "fpv", label: dict.command.viewFpv, icon: Video },
  ];

  return (
    <div
      data-globe-stage
      className={cn("relative overflow-hidden rounded-2xl border border-border/80 shadow-panel", className)}
    >
      {/* simulated ambience backdrop */}
      <div aria-hidden className="absolute inset-0 transition-[background] duration-700" style={{ background: AMBIENCE[preset].css }} />
      <div aria-hidden className="absolute inset-0 grid-bg opacity-60" />

      <div className="relative h-full">
        {showScene ? (
          <SceneBoundary onFail={() => setWebglFailed(true)}>
            <Suspense fallback={<GlobeFallback reduced={false} skeleton />}>
              {view === "space" ? (
                <GlobeScene preset={preset} season={season} onFail={() => setWebglFailed(true)} />
              ) : (
                <CommandRoomScene
                  preset={preset}
                  season={season}
                  view={view}
                  texts={roomTexts}
                  onRoleFocus={(role) => setFocusedRole(role)}
                  onFail={() => setWebglFailed(true)}
                />
              )}
            </Suspense>
          </SceneBoundary>
        ) : (
          <GlobeFallback reduced={reducedMotion || !hydrated} />
        )}

        {/* chamber layers (space view only — the 3D room has its own set) */}
        <div className="absolute inset-0" aria-hidden>
          {view === "space" ? (
            <>
              <Skyline />
              {showScene ? <PlatformSigil /> : null}
              <OperatorFigure className="absolute bottom-[6%] start-[4%] hidden h-[26%] opacity-90 lg:block" />
            </>
          ) : null}
          <div className="scanlines absolute inset-0" />
          <div className="vignette absolute inset-0" />
          <CornerBrackets />
        </div>

        {/* honest labeling row (honest: demonstration only) */}
        <div className="absolute inset-x-0 top-3 z-10 flex flex-wrap items-center justify-center gap-1.5 px-12">
          <span className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border border-border-strong bg-navy-950/70 px-2.5 py-1 text-[9px] font-bold text-muted-foreground backdrop-blur-md light:bg-white/80">
            <ShieldCheck className="size-3 text-success" aria-hidden />
            {dict.command.sessionChip}
          </span>
          <span className="hidden items-center gap-1.5 whitespace-nowrap rounded-full border border-border-strong bg-navy-950/70 px-2.5 py-1 text-[9px] font-semibold text-muted-foreground backdrop-blur-md md:inline-flex light:bg-white/80">
            <Globe2 className="size-3 text-accent" aria-hidden />
            {showScene ? dict.command.sceneCaption : dict.command.sceneFallbackCaption}
          </span>
          <span className="hidden whitespace-nowrap rounded-full border border-violet/40 bg-violet/10 px-2.5 py-1 text-[9px] font-semibold text-violet md:inline-flex">
            {dict.common.simulationNote}
          </span>
        </div>

        {/* live weather chip (room views only — the room has the glass wall) */}
        {showScene && view !== "space" ? (
          <WeatherChip
            title={roomTexts.weather.title}
            offline={roomTexts.weather.offline}
            live={roomTexts.weather.live}
            cond={roomTexts.weather.cond}
          />
        ) : null}

        {/* role workstation panel */}
        {focusedRole !== null && showScene && view !== "space" ? (
          <RolePanel role={focusedRole} onClose={() => setFocusedRole(null)} />
        ) : null}

        {/* FPV hint */}
        {showScene && view === "fpv" ? (
          <div className="pointer-events-none absolute inset-x-0 bottom-[72px] z-10 flex justify-center">
            <span className="rounded-full border border-border-strong bg-navy-950/70 px-3 py-1 text-[10px] font-semibold text-muted-foreground backdrop-blur-md light:bg-white/80">
              {roomTexts.hud.fpvHint}
            </span>
          </div>
        ) : null}

        {/* scene on/off + honest captions */}
        <div className="absolute end-3 top-3 z-10">
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => setPref("sceneEnabled", !prefs.sceneEnabled)}
            aria-label={dict.settings.sceneEnable}
            aria-pressed={prefs.sceneEnabled}
            className="bg-navy-950/60 backdrop-blur-sm light:bg-white/70"
          >
            {prefs.sceneEnabled ? <Eye /> : <EyeOff />}
          </Button>
        </div>
        {/* view dock — room / space / commander FPV + ambience + season */}
        <div className="absolute inset-x-0 bottom-9 z-10 flex justify-center px-24">
          <div
            role="radiogroup"
            aria-label={dict.command.ambience}
            className="flex items-center gap-0.5 rounded-full border border-border-strong bg-navy-950/70 p-1 backdrop-blur-md light:bg-white/80"
          >
            {viewOptions.map((option) => (
              <button
                key={option.id}
                type="button"
                role="radio"
                aria-checked={view === option.id}
                title={option.label}
                data-scene-view={option.id}
                onClick={() => setPref("sceneView", option.id)}
                className={cn(
                  "inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-1 text-[11px] font-semibold transition-colors",
                  view === option.id ? "bg-accent/15 text-accent" : "text-muted-foreground hover:text-foreground",
                )}
              >
                <option.icon className="size-3.5" aria-hidden />
                <span className="hidden sm:inline">{option.label}</span>
              </button>
            ))}
            <span aria-hidden className="mx-1 h-4 w-px bg-border-strong" />
            {ambienceOptions.map((option) => (
              <button
                key={option.id}
                type="button"
                role="radio"
                aria-checked={preset === option.id}
                title={option.label}
                onClick={() => setPref("ambience", option.id)}
                className={cn(
                  "inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-1 text-[11px] font-semibold transition-colors",
                  preset === option.id
                    ? "bg-primary/20 text-primary"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                <option.icon className="size-3.5" aria-hidden />
                <span className="hidden sm:inline">{option.label}</span>
              </button>
            ))}
            <span aria-hidden className="mx-1 h-4 w-px bg-border-strong" />
            <button
              type="button"
              title={`${dict.command.seasonLabel}: ${seasons.find((s) => s.id === season)?.label}`}
              onClick={cycleSeason}
              aria-label={`${dict.command.seasonLabel}: ${seasons.find((s) => s.id === season)?.label}`}
              className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-1 text-[11px] font-semibold text-accent transition-colors hover:bg-accent/10"
            >
              <SeasonIcon className="size-3.5" aria-hidden />
              <span className="hidden sm:inline">{seasons.find((s) => s.id === season)?.label}</span>
            </button>
          </div>
        </div>

        <EventsTicker />
      </div>
    </div>
  );
}
