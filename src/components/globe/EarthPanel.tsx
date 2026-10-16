"use client";
import {
  Component,
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import dynamic from "next/dynamic";
import { ArrowUpLeft, Crosshair, Layers3, MapPin, Minus, Pause, Play, Plus, RotateCcw, Sun, X } from "lucide-react";
import type { Language, Quality } from "../../lib/navigation";
import type { CountryCollection } from "../../lib/geography";
import { solarPosition } from "../../lib/solar";
import { DataCard } from "../cards/DataCard";
import { EarthFallback } from "./EarthFallback";
import type { GlobeOptions } from "./GlobeScene";
const GlobeScene = dynamic(() => import("./GlobeScene"), {
  ssr: false,
  loading: () => (
    <div className="dc-globe-loading" role="status">
      INITIALIZING EARTH…
    </div>
  ),
});
class GlobeBoundary extends Component<
  { children: ReactNode; fallback: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? this.props.fallback : this.props.children;
  }
}
export function EarthPanel({
  language,
  quality = "balanced",
}: {
  language: Language;
  quality?: Quality;
}) {
  const fa = language === "fa";
  const [countries, setCountries] = useState<CountryCollection | null>(null);
  const [failed, setFailed] = useState(false);
  const [ready, setReady] = useState(false);
  const [paused, setPaused] = useState(false);
  const [reduced, setReduced] = useState(false);
  const [view, setView] = useState<"global" | "iran">("global");
  const [zoom, setZoom] = useState(0);
  const [reset, setReset] = useState(0);
  const [layers, setLayers] = useState(false);
  const [atmosphere, setAtmosphere] = useState(true);
  const [markers, setMarkers] = useState(true);
  const [labels, setLabels] = useState(true);
  const [date, setDate] = useState<Date | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    fetch("/geo/countries.geojson", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error("Map unavailable");
        return response.json();
      })
      .then((data: CountryCollection) => {
        if (data.type !== "FeatureCollection" || !Array.isArray(data.features))
          throw new Error("Invalid map");
        setCountries(data);
      })
      .catch((error) => {
        if (error.name !== "AbortError") setFailed(true);
      });
    return () => controller.abort();
  }, []);
  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const sync = () => setReduced(media.matches);
    const raf = requestAnimationFrame(sync);
    media.addEventListener("change", sync);
    const tick = () => {
      if (!document.hidden) setDate(new Date());
    };
    const timer = setInterval(tick, 30000);
    const initial = requestAnimationFrame(tick);
    return () => {
      cancelAnimationFrame(raf);
      cancelAnimationFrame(initial);
      media.removeEventListener("change", sync);
      clearInterval(timer);
    };
  }, []);
  const onIran = useCallback(() => setView("iran"), []);
  const onFailure = useCallback(() => setFailed(true), []);
  const onReady = useCallback(() => setReady(true), []);
  const options = useMemo<GlobeOptions>(
    () => ({
      paused,
      atmosphere,
      markers,
      labels,
      view,
      zoom,
      reset,
      language,
      reducedMotion: reduced,
    }),
    [paused, atmosphere, markers, labels, view, zoom, reset, language, reduced],
  );
  const sun = date ? solarPosition(date) : null;
  const fallback = (
    <EarthFallback countries={countries} language={language} onIran={onIran} />
  );
  return (
    <DataCard
      title={fa ? "زمین و هوشمندی جهانی" : "Earth & global intelligence"}
      icon="nav/digital-world"
      language={language}
      className="dc-earth-panel"
      action={
        <span className="dc-earth-header-note">
          {fa
            ? "جغرافیای محلی · بدون شبکهٔ زنده"
            : "LOCAL GEOGRAPHY · NO LIVE FEED"}
        </span>
      }
    >
      <div className="dc-earth-stage">
        <div className="dc-earth-corner">
          <span className="dc-earth-eyebrow">A WORLD OF PERSPECTIVE</span>
          <h3>{fa ? "جهان، در یک نگاه" : "A world, in perspective"}</h3>
          <p>
            {fa
              ? "مرزها واقعی؛ داده‌های بازار نمایشی"
              : "Real geography. Demonstration market data."}
          </p>
        </div>
        <div className="dc-earth-coordinates" dir="ltr">
          <span>FOCUS / {view === "iran" ? "IRAN" : "GLOBAL"}</span>
          <strong>{view === "iran" ? "32.40° N" : "35.68° N"}</strong>
          <span>{view === "iran" ? "53.70° E" : "51.38° E"}</span>
        </div>
        {failed ? (
          fallback
        ) : countries ? (
          <GlobeBoundary fallback={fallback}>
            <GlobeScene
              countries={countries}
              quality={quality}
              options={options}
              onIran={onIran}
              onFailure={onFailure}
              onReady={onReady}
            />
          </GlobeBoundary>
        ) : (
          <div className="dc-globe-loading" role="status">
            {fa ? "بارگذاری نقشهٔ محلی…" : "Loading local geography…"}
          </div>
        )}
        <div className="dc-earth-focus">
          <button
            onClick={onIran}
            className={view === "iran" ? "is-active" : ""}
          >
            <MapPin size={13} />
            {fa ? "ایران" : "IRAN"}
            <ArrowUpLeft size={11} />
          </button>
          {view === "iran" && (
            <button
              onClick={() => {
                setView("global");
                setZoom(0);
                setReset((value) => value + 1);
              }}
            >
              {fa ? "بازگشت به جهان" : "Back to global"}
            </button>
          )}
        </div>
        {view === "iran" && (
          <section
            className="dc-iran-detail"
            aria-label={fa ? "اطلاعات ایران" : "Iran information"}
          >
            <header>
              <h4>{fa ? "ایران · تهران" : "IRAN · TEHRAN"}</h4>
              <button
                className="ah-icon-button"
                onClick={() => setView("global")}
                aria-label={
                  fa ? "بستن اطلاعات ایران" : "Close Iran information"
                }
              >
                <X size={13} />
              </button>
            </header>
            <bdi>35.6892° N / 51.3890° E</bdi>
            <p>
              {fa
                ? "مرز تعمیم‌یافتهٔ Natural Earth. نور شهرها تزئینی است و فعالیت اقتصادی را نشان نمی‌دهد."
                : "Generalized Natural Earth boundary. Stylized city lights do not measure economic activity."}
            </p>
            <span className="dc-status">DEMO</span>
          </section>
        )}
        <div className="dc-globe-controls">
          <button
            aria-label={fa ? "کاهش بزرگ‌نمایی" : "Zoom out"}
            disabled={!ready || failed}
            onClick={() => setZoom((value) => Math.max(-8, value - 1))}
          >
            <Minus size={15} />
          </button>
          <button
            aria-label={fa ? "افزایش بزرگ‌نمایی" : "Zoom in"}
            disabled={!ready || failed}
            onClick={() => setZoom((value) => Math.min(8, value + 1))}
          >
            <Plus size={15} />
          </button>
          <span />
          <button
            aria-label={
              fa
                ? paused
                  ? "ادامهٔ چرخش"
                  : "توقف چرخش"
                : paused
                  ? "Resume rotation"
                  : "Pause rotation"
            }
            aria-pressed={paused}
            disabled={failed || reduced}
            onClick={() => setPaused(!paused)}
          >
            {paused || reduced ? <Play size={13} /> : <Pause size={13} />}
          </button>
          <button
            aria-label={fa ? "بازنشانی نما" : "Reset view"}
            disabled={failed}
            onClick={() => {
              setView("global");
              setZoom(0);
              setReset((value) => value + 1);
            }}
          >
            <RotateCcw size={14} />
          </button>
          <button
            aria-label={fa ? "لایه‌های زمین" : "Earth layers"}
            aria-expanded={layers}
            disabled={failed}
            onClick={() => setLayers(!layers)}
          >
            <Layers3 size={15} />
          </button>
        </div>
        {layers && (
          <div className="dc-earth-layers">
            <label>
              <input
                type="checkbox"
                checked={labels}
                onChange={(event) => setLabels(event.target.checked)}
              />
              {fa ? "برچسب شهرها" : "City labels"}
            </label>
            <label>
              <input
                type="checkbox"
                checked={atmosphere}
                disabled={quality === "low"}
                onChange={(event) => setAtmosphere(event.target.checked)}
              />
              {fa ? "درخشش جو" : "Atmosphere"}
              {quality === "low" && <small>LOW</small>}
            </label>
            <label>
              <input
                type="checkbox"
                checked={markers}
                onChange={(event) => setMarkers(event.target.checked)}
              />
              {fa ? "نشانگرها" : "Markers"}
            </label>
          </div>
        )}
        <div className="dc-earth-legend">
          <span>
            <Sun size={11} />
            {fa ? "مرز روز و شب: زمان دستگاه" : "DAY / NIGHT · DEVICE TIME"}
          </span>
          <bdi>
            {sun
              ? `SUN ${sun.latitude.toFixed(1)}° / ${sun.longitude.toFixed(1)}°`
              : "SUN —"}
          </bdi>
          <span>
            <Crosshair size={11} />
            {fa ? "بکشید تا بچرخد" : "DRAG TO ROTATE"}
          </span>
        </div>
      </div>
    </DataCard>
  );
}
