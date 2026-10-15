"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { geoCircle, geoEquirectangular, geoGraticule10, geoNaturalEarth1, geoPath } from "d3-geo";
import type { FeatureCollection, Geometry } from "geojson";
import type { FinancialCenter } from "@/lib/api/types";
import { antisolarPoint, sunPosition } from "@/lib/astro/solar";
import { useI18n } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import { loadCountries, loadIran, type IranFeature } from "./geo-data";
import { TEHRAN } from "./scene-constants";

interface Props {
  centers: FinancialCenter[];
  focusIran: boolean;
  nowMs: number | null;
  onIranClick: () => void;
  showLabels: boolean;
  showMarkers: boolean;
  className?: string;
}

function useElementSize<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [size, setSize] = useState({ w: 0, h: 0 });
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => {
      if (!entry) return;
      const { width, height } = entry.contentRect;
      setSize({ w: Math.round(width), h: Math.round(height) });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return [ref, size] as const;
}

/**
 * 2D fallback map (SVG + d3-geo) used when WebGL is unavailable or chosen by
 * the user. Same truth as the 3D view: night hemisphere = geoCircle(90°)
 * around the antisolar point computed from the real clock.
 */
/** Greedy screen-space label culling (tier order = priority). */
function cullLabels<T extends { c: FinancialCenter; xy: [number, number] | null }>(items: T[], text: (c: FinancialCenter) => string): T[] {
  const placed: { x0: number; x1: number; y0: number; y1: number }[] = [];
  return [...items]
    .sort((a, b) => (a.c.id === "tehran" ? -1 : b.c.id === "tehran" ? 1 : a.c.tier - b.c.tier))
    .filter((it) => {
      if (!it.xy) return false;
      const w = text(it.c).length * 6 + 14;
      const r = { x0: it.xy[0] - w / 2, x1: it.xy[0] + w / 2, y0: it.xy[1] + 6, y1: it.xy[1] + 22 };
      if (placed.some((p) => p.x0 < r.x1 && p.x1 > r.x0 && p.y0 < r.y1 && p.y1 > r.y0)) return false;
      placed.push(r);
      return true;
    });
}

export function GlobeFallback2D({ centers, focusIran, nowMs, onIranClick, showLabels, showMarkers, className }: Props) {
  const { l, t } = useI18n();
  const [ref, { w, h }] = useElementSize<HTMLDivElement>();
  const [geo, setGeo] = useState<{ countries: FeatureCollection<Geometry>; iran: IranFeature } | null>(null);

  useEffect(() => {
    let alive = true;
    void Promise.all([loadCountries(), loadIran()]).then(([countries, iran]) => {
      if (alive) setGeo({ countries, iran });
    });
    return () => {
      alive = false;
    };
  }, []);

  const model = useMemo(() => {
    if (!geo || w < 10 || h < 10) return null;
    const pad = 18;
    const projection = focusIran
      ? geoEquirectangular().fitExtent(
          [
            [pad + 40, pad + 30],
            [w - pad - 40, h - pad - 30],
          ],
          geo.iran,
        )
      : geoNaturalEarth1().fitExtent(
          [
            [pad, pad],
            [w - pad, h - pad],
          ],
          { type: "Sphere" },
        );
    const path = geoPath(projection);
    const date = new Date(nowMs ?? 0);
    const anti = antisolarPoint(date);
    const sun = sunPosition(date);
    const nightLayers = nowMs === null ? [] : [108, 102, 96, 90].map((r) => path(geoCircle().center([anti.lng, anti.lat]).radius(r)()) ?? "");
    const project = (lat: number, lng: number) => projection([lng, lat]);
    return {
      sphere: path({ type: "Sphere" }) ?? "",
      graticule: path(geoGraticule10()) ?? "",
      countries: path(geo.countries) ?? "",
      iran: path(geo.iran) ?? "",
      nightLayers,
      sunXY: nowMs === null ? null : project(sun.subsolarLat, sun.subsolarLng),
      tehranXY: project(TEHRAN.lat, TEHRAN.lng),
      centers: centers.map((c) => ({ c, xy: project(c.lat, c.lng) })),
    };
  }, [geo, w, h, focusIran, nowMs, centers]);

  return (
    <div ref={ref} className={cn("absolute inset-0", className)}>
      {model && (
        <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} role="img" aria-label={t.globe.fallbackShort} className="absolute inset-0">
          <defs>
            <radialGradient id="fb-ocean" cx="50%" cy="45%" r="70%">
              <stop offset="0%" stopColor="#0c1f40" />
              <stop offset="100%" stopColor="#050c1a" />
            </radialGradient>
            <filter id="fb-glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="b" />
              <feMerge>
                <feMergeNode in="b" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <path d={model.sphere} fill="url(#fb-ocean)" stroke="rgb(230 191 95 / 0.35)" strokeWidth={0.8} />
          <path d={model.graticule} fill="none" stroke="rgb(230 191 95 / 0.07)" strokeWidth={0.6} />
          <path d={model.countries} fill="#1b2536" stroke="rgb(240 210 126 / 0.28)" strokeWidth={0.5} />
          {model.nightLayers.map((d, i) => (
            <path key={i} d={d} fill={`rgb(1 3 9 / ${[0.12, 0.14, 0.18, 0.42][i]})`} />
          ))}
          <path
            d={model.iran}
            fill="rgb(230 191 95 / 0.22)"
            stroke="#f7e3a1"
            strokeWidth={focusIran ? 1.6 : 1.1}
            filter="url(#fb-glow)"
            className="cursor-pointer transition-[fill] hover:fill-[rgb(230_191_95/0.36)]"
            onClick={onIranClick}
            role="button"
            aria-label={t.globe.flyIran}
            tabIndex={0}
            onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onIranClick()}
          />
          {model.tehranXY && (
            <g transform={`translate(${model.tehranXY[0]} ${model.tehranXY[1]})`}>
              <circle r={9} fill="none" stroke="#f7e3a1" strokeOpacity={0.7} className="origin-center animate-ping-slow motion-off:hidden" />
              <circle r={3.2} fill="#f7e3a1" filter="url(#fb-glow)" />
            </g>
          )}
          {showMarkers &&
            model.centers
              .filter((x) => x.xy && x.c.id !== "tehran")
              .map(({ c, xy }) => <circle key={c.id} cx={xy![0]} cy={xy![1]} r={c.tier === 1 ? 2.6 : 1.8} fill="var(--color-data-400)" opacity={0.9} />)}
          {model.sunXY && (
            <g transform={`translate(${model.sunXY[0]} ${model.sunXY[1]})`}>
              <circle r={10} fill="rgb(255 214 120 / 0.18)" />
              <circle r={4} fill="#ffd678" />
            </g>
          )}
        </svg>
      )}
      {model && showLabels && (
        <div className="pointer-events-none absolute inset-0">
          {cullLabels(model.centers.filter((x) => x.xy && x.c.tier <= 2), (c) => l(c.name)).map(({ c, xy }) => (
              <span
                key={c.id}
                className={cn("absolute -translate-x-1/2 translate-y-2 whitespace-nowrap rounded-full px-1.5 text-3xs", c.id === "tehran" ? "bg-gold-400/15 font-semibold text-gold-100" : "text-fg-3")}
                style={{ left: xy![0], top: xy![1] }}
              >
                {l(c.name)}
              </span>
            ))}
        </div>
      )}
    </div>
  );
}
