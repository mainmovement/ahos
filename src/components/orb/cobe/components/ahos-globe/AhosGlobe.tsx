"use client";

/**
 * <AhosGlobe /> — the AHOS hero globe (one per dashboard, on purpose).
 *
 * Structure
 *   frame        → measures the available space (ResizeObserver)
 *   dial         → globe square + 26 px chrome band: department ring, gate gauge, caption pills
 *   stage        → the COBE canvas (or the flat SVG fallback) and the overlay SVG
 *   marker layer → real DOM buttons, positioned imperatively each frame
 *
 * Rendering rules
 *   - COBE is created once and updated through refs (see `useGlobeCanvas`).
 *   - All geometry is derived from the rotation COBE itself uses, so overlays land on the dots.
 *   - Motion stops when the tab is hidden, the dial is off-screen, or the user prefers reduced
 *     motion. Markers, arcs, the Iran highlight and the gate all keep rendering — nothing is faked.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ArcLayer, arcElementId } from "./ArcLayer";
import { ArcTooltip } from "./ArcTooltip";
import { DialCaptions } from "./DialCaptions";
import { FlatMap } from "./FlatMap";
import { GateArc } from "./GateArc";
import { MarkerLayer, MARKER_HIT_SIZE, type VisibleMarker } from "./MarkerLayer";
import { RingTicks } from "./RingTicks";
import { TextTable } from "./TextTable";
import { STAGE_PAD, dialSize } from "./layout";
import { useAnimationGate } from "./useAnimationGate";
import { useGlobeCanvas } from "./useGlobeCanvas";
import { IRAN_RINGS } from "../../lib/geo/mask";
import {
  latLngToCartesian,
  makeFlatProjector,
  makeGlobeProjector,
  mapRect,
  pathFromSamples,
  phiForCentre,
  project,
  ringPath,
  sampleArc,
  sampleFlatArc,
  type ArcSample,
  type ProjectPoint,
  type Projected,
} from "../../lib/geo/projection";
import { asOfText, dictionary, direction, formatPercent, localizeNumber } from "../../lib/i18n";
import { useClientClock } from "../../lib/useClientClock";
import { breath, selectMarkers, selectSignals, signalChrome } from "../../lib/style";
import type { AhosGlobeProps, MarketNode } from "../../types/globe";

/**
 * First-paint framing. `THETA` also *is* the latitude that ends up in the centre of the disc
 * (COBE's rotation maps theta to the centre latitude). 0.42 rad ≈ 24°N, spun to 51.4°E, puts
 * Tehran — the one market this product always points at — slightly above the centre, with Iran at
 * full size instead of smeared across the limb. Eleven of the fourteen demo nodes are on the near
 * side from here (including all three attention markets); Sydney, New York and São Paulo are
 * honestly off-screen.
 */
const INITIAL_LNG = 51.39;
const THETA = 0.42;
/** Calm spin: 0.003 rad per frame at 60 fps, expressed in rad/s so it is frame-rate independent. */
const CALM_SPIN = 0.003 * 60;
const ACTIVE_SPIN = 0.0055 * 60;
/** Arc altitude in sphere-radius units; keeps every arc inside the department ring. */
const ARC_HEIGHT = 0.13;
/** Tehran — the one market the product always points at. */
const TEHRAN = { lat: 35.69, lng: 51.39 };

export function AhosGlobe({
  markets,
  signals,
  gate,
  health,
  departments,
  calm = true,
  quality = "medium",
  mode = "globe",
  lang = "fa",
  onSelect,
  className,
  now: nowProp,
}: AhosGlobeProps) {
  const dict = dictionary(lang);
  const dir = direction(lang);
  const frameRef = useRef<HTMLDivElement | null>(null);
  const hostRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const glowRef = useRef<HTMLDivElement | null>(null);
  const tehranRingRef = useRef<SVGCircleElement | null>(null);
  const arcTooltipRef = useRef<HTMLDivElement | null>(null);
  const markerRefs = useRef<Map<string, HTMLButtonElement>>(new Map());
  const pathsRef = useRef<Map<string, SVGPathElement>>(new Map());
  const flashesRef = useRef<Map<string, SVGCircleElement>>(new Map());
  const iranRefs = useRef<Map<string, SVGPathElement>>(new Map());
  const arcMidRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  const [size, setSize] = useState(520);
  const [activeMarker, setActiveMarker] = useState<string | null>(null);
  const [activeArc, setActiveArc] = useState<string | null>(null);
  const [textOpen, setTextOpen] = useState(false);
  const now = useClientClock(nowProp);

  const dial = dialSize(size);
  const nodeIndex = useMemo(() => new Map(markets.map((market) => [market.id, market])), [markets]);
  const selection = useMemo(() => selectMarkers(markets, calm), [markets, calm]);
  const visibleSignals = useMemo(() => selectSignals(signals, markets), [signals, markets]);
  const attentionCount = useMemo(() => departments.filter((d) => d.needsAttention).length, [departments]);
  const anyAttention = useMemo(
    () => markets.some((market) => market.needsAttention) || attentionCount > 0,
    [markets, attentionCount],
  );
  const hasDemoData = useMemo(
    () => markets.some((market) => market.freshness === "DEMO") || departments.some((d) => d.freshness === "DEMO"),
    [markets, departments],
  );

  const visibleMarkers = useMemo<VisibleMarker[]>(() => {
    const out: VisibleMarker[] = [];
    for (const id of selection.recessed) {
      const node = nodeIndex.get(id);
      if (node) out.push({ node, state: "recessed" });
    }
    for (const id of selection.highlighted) {
      const node = nodeIndex.get(id);
      if (node) out.push({ node, state: "highlight" });
    }
    return out;
  }, [selection, nodeIndex]);

  const activeSignal = useMemo(
    () => (activeArc === null ? null : (visibleSignals.find((signal) => signal.id === activeArc) ?? null)),
    [activeArc, visibleSignals],
  );

  /* ------------------------------------------------------------- measurement */

  useEffect(() => {
    const element = frameRef.current;
    if (!element) return;
    const apply = (width: number, height: number) => {
      const usable = Math.min(width, height) - STAGE_PAD * 2 - 12;
      setSize(Math.max(220, Math.min(780, Math.floor(usable))));
    };
    const rect = element.getBoundingClientRect();
    apply(rect.width, rect.height);
    if (typeof ResizeObserver !== "function") return;
    const observer = new ResizeObserver((entries) => {
      const entry = entries[entries.length - 1];
      if (entry) apply(entry.contentRect.width, entry.contentRect.height);
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  /* ------------------------------------------------------------ animation gate */

  const isGlobeMode = mode === "globe";
  const motion = useAnimationGate(frameRef, isGlobeMode);
  const animate = motion.animate;
  // The canvas is repainted whenever it can be seen (see `useGlobeCanvas`): COBE has no
  // preserveDrawingBuffer, so a paused canvas would be cleared by the compositor.
  const rendering = isGlobeMode && !motion.hidden && !motion.offscreen;
  const spinRate = calm ? CALM_SPIN : ACTIVE_SPIN;

  const drawOverlayRef = useRef<(phi: number, theta: number, timeMs: number) => void>(() => {});

  const { supported, phiRef, redraw } = useGlobeCanvas({
    hostRef,
    canvasRef,
    size,
    quality,
    mode,
    animate,
    rendering,
    spinRate,
    theta: THETA,
    hold: activeMarker !== null || activeArc !== null,
    alert: anyAttention,
    onFrame: (phi, theta, time) => drawOverlayRef.current(phi, theta, time),
  });

  // Start with the home framing (62°E, 17°N) facing the camera.
  useEffect(() => {
    if (phiRef.current !== 0) return;
    phiRef.current = phiForCentre(INITIAL_LNG, THETA);
    redraw();
  }, [phiRef, redraw]);

  /* ----------------------------------------------------------------- drawing */

  const drawOverlay = useCallback(
    (phi: number, theta: number, timeMs: number) => {
      const layout = { width: size, height: size, scale: 1 };
      const rect = mapRect(size, size, 0.03);
      const projector: ProjectPoint = mode === "map" ? makeFlatProjector(rect) : makeGlobeProjector(phi, theta, layout);
      const pointFor = (lat: number, lng: number): Projected =>
        mode === "map" ? projector(latLngToCartesian(lat, lng)) : project(lat, lng, phi, theta, layout);

      // Golden core glow: breathes with the heartbeat, holds still when motion is not allowed.
      const glow = glowRef.current;
      if (glow) {
        const beat = breath(timeMs, health);
        glow.style.transform = `scale(${animate ? beat.scale : 1})`;
        glow.dataset.stale = health.stale ? "true" : "false";
        glow.dataset.alert = anyAttention ? "true" : "false";
        glow.dataset.mode = mode;
      }

      // Markers (DOM buttons), written with transform only.
      markerRefs.current.forEach((element, id) => {
        const node = nodeIndex.get(id);
        if (!node) return;
        const projected = pointFor(node.lat, node.lng);
        const x = STAGE_PAD + projected.x;
        const y = STAGE_PAD + projected.y;
        element.style.transform = `translate3d(${(x - MARKER_HIT_SIZE / 2).toFixed(1)}px, ${(y - MARKER_HIT_SIZE / 2).toFixed(1)}px, 0)`;
        element.style.opacity = projected.visible ? "1" : "0";
        element.style.pointerEvents = projected.visible ? "auto" : "none";
        const wantedTabIndex = projected.visible ? 0 : -1;
        if (element.tabIndex !== wantedTabIndex) element.tabIndex = wantedTabIndex;
        element.dataset.side = y < 130 ? "below" : "above";
      });

      // Iran outline (both modes) + Tehran ring.
      IRAN_RINGS.forEach((ring, index) => {
        const path = iranRefs.current.get(`iran-${index}`);
        if (!path) return;
        const d = ringPath(ring, projector, mode === "map" ? 1 : undefined);
        path.setAttribute("d", d ?? "");
        path.style.opacity = d ? "1" : "0";
      });
      const ring = tehranRingRef.current;
      if (ring) {
        const projected = pointFor(TEHRAN.lat, TEHRAN.lng);
        ring.setAttribute("cx", projected.x.toFixed(1));
        ring.setAttribute("cy", projected.y.toFixed(1));
        ring.style.opacity = projected.visible ? "1" : "0";
        // Keep the pulse visually on top of the Tehran dot even in map mode.
        ring.setAttribute("r", mode === "map" ? "6.6" : "7.2");
      }

      // Signal arcs.
      for (const signal of visibleSignals) {
        const from = nodeIndex.get(signal.fromNodeId);
        const to = nodeIndex.get(signal.toNodeId);
        if (!from || !to) continue;
        const chrome = signalChrome(signal.outcome);
        const samples: ArcSample[] =
          mode === "map"
            ? sampleFlatArc(
                { x: pointFor(from.lat, from.lng).x, y: pointFor(from.lat, from.lng).y },
                { x: pointFor(to.lat, to.lng).x, y: pointFor(to.lat, to.lng).y },
              )
            : sampleArc(from, to, projector, { height: ARC_HEIGHT });
        const cut = Math.max(2, Math.floor(samples.length * chrome.drawFraction));
        const drawn = samples.slice(0, cut);
        const split = Math.max(1, Math.floor(drawn.length * 0.5));
        const head = pathFromSamples(drawn.slice(0, split + 1));
        const tail = pathFromSamples(drawn.slice(split));
        const hit = pathFromSamples(samples);
        const headPath = pathsRef.current.get(arcElementId(signal.id, "head"));
        const tailPath = pathsRef.current.get(arcElementId(signal.id, "tail"));
        const hitPath = pathsRef.current.get(arcElementId(signal.id, "hit"));
        if (headPath) headPath.setAttribute("d", head ?? "");
        if (tailPath) tailPath.setAttribute("d", tail ?? "");
        if (hitPath) hitPath.setAttribute("d", hit ?? "");

        const flash = flashesRef.current.get(signal.id);
        if (flash) {
          const lastSample = [...samples].reverse().find((sample) => sample.visible);
          if (lastSample && chrome.flashAtGate) {
            flash.setAttribute("cx", lastSample.x.toFixed(1));
            flash.setAttribute("cy", lastSample.y.toFixed(1));
            flash.style.opacity = "1";
          } else {
            flash.style.opacity = "0";
          }
        }

        if (activeArc === signal.id) {
          const middle = samples[Math.floor(samples.length / 2)];
          if (middle) arcMidRef.current = { x: middle.x, y: middle.y };
        }
      }

      // Arc tooltip follows its arc's midpoint (clamped inside the dial).
      const tooltip = arcTooltipRef.current;
      if (tooltip) {
        const x = Math.max(70, Math.min(dial - 70, STAGE_PAD + arcMidRef.current.x));
        const y = Math.max(64, Math.min(dial - 40, STAGE_PAD + arcMidRef.current.y));
        tooltip.style.transform = `translate3d(${x.toFixed(1)}px, ${y.toFixed(1)}px, 0)`;
      }
    },
    [size, mode, nodeIndex, visibleSignals, health, animate, anyAttention, activeArc, dial],
  );
  // The loop reads the painter through a ref; refs may not be written during render, so the
  // assignment happens here and is followed by a repaint on every input the painter depends on.
  useEffect(() => {
    drawOverlayRef.current = drawOverlay;
    redraw();
  }, [redraw, drawOverlay, textOpen]);

  /* -------------------------------------------------------------------- views */

  const fallback = mode === "globe" && !supported;

  return (
    <div
      className={["ahos-frame", className].filter(Boolean).join(" ")}
      ref={frameRef}
      dir={dir}
      lang={lang}
      data-mode={mode}
      data-calm={calm ? "true" : "false"}
      data-quality={quality}
      data-animate={animate ? "true" : "false"}
      data-rendering={rendering ? "true" : "false"}
      data-offscreen={motion.offscreen ? "true" : "false"}
      data-reduced-motion={motion.reducedMotion ? "true" : "false"}
      data-hidden={motion.hidden ? "true" : "false"}
      data-fallback={fallback ? "true" : "false"}
      data-stale={health.stale ? "true" : "false"}
    >
      <div className="ahos-dial" style={{ width: dial, height: dial }}>
        <div
          className="ahos-core-glow"
          ref={glowRef}
          style={{
            width: size * 0.86,
            height: size * 0.86,
            left: (dial - size * 0.86) / 2,
            top: (dial - size * 0.86) / 2,
          }}
          aria-hidden="true"
        />

        <div className="ahos-stage" style={{ left: STAGE_PAD, top: STAGE_PAD, width: size, height: size }}>
          <div className="ahos-canvas-host" ref={hostRef}>
            <canvas
              ref={canvasRef}
              className="ahos-canvas"
              width={size}
              height={size}
              aria-label={dict.globeAria}
              role="img"
              data-dimmed={mode === "map" ? "true" : "false"}
            />
          </div>
          {fallback ? (
            <svg className="ahos-fallback" viewBox={`0 0 ${size} ${size}`} aria-hidden="true">
              <defs>
                <radialGradient id="ahos-fallback-fill" cx="50%" cy="42%" r="60%">
                  <stop offset="0%" stopColor="#161207" />
                  <stop offset="70%" stopColor="#0b0a08" />
                  <stop offset="100%" stopColor="#050507" />
                </radialGradient>
              </defs>
              <circle cx={size / 2} cy={size / 2} r={size * 0.4} fill="url(#ahos-fallback-fill)" />
              <circle
                cx={size / 2}
                cy={size / 2}
                r={size * 0.4}
                fill="none"
                stroke="rgba(212,175,55,0.35)"
                strokeWidth={1}
                strokeDasharray="1 4"
              />
            </svg>
          ) : null}
        </div>

        <svg className="ahos-overlay" width={dial} height={dial} viewBox={`0 0 ${dial} ${dial}`} aria-hidden="true">
          <g className="ahos-globe-space" transform={`translate(${STAGE_PAD} ${STAGE_PAD})`}>
            <FlatMap size={size} visible={mode === "map"} />
            {IRAN_RINGS.map((_, index) => (
              <path
                key={`iran-${index}`}
                ref={(element) => {
                  if (element) iranRefs.current.set(`iran-${index}`, element);
                  else iranRefs.current.delete(`iran-${index}`);
                }}
                className="ahos-iran-outline"
                fill="none"
                d=""
              />
            ))}
            <ArcLayer
              signals={visibleSignals}
              nodes={nodeIndex}
              lang={lang}
              dict={dict}
              activeId={activeArc}
              pathsRef={pathsRef}
              flashesRef={flashesRef}
              onActivate={setActiveArc}
              onDeactivate={() => setActiveArc(null)}
            />
            <circle
              ref={tehranRingRef}
              className="ahos-tehran-ring"
              cx={-99}
              cy={-99}
              r={7.2}
              fill="none"
              stroke="#f5d27a"
              strokeWidth={1}
              vectorEffect="non-scaling-stroke"
            />
          </g>
          <RingTicks departments={departments} size={size} />
          <GateArc gate={gate} size={size} lang={lang} cx={dial / 2} cy={dial / 2} />
          {health.stale ? (
            <g className="ahos-stale-mark">
              {/* A stopped heartbeat is drawn as a flat line, with its caption centred beneath it
                  so the label can never collide with the trace in either direction. */}
              <line
                x1={dial / 2 - 0.14 * size}
                y1={dial / 2 + size * 0.3}
                x2={dial / 2 + 0.14 * size}
                y2={dial / 2 + size * 0.3}
                stroke="#8a93a0"
                strokeWidth={1}
                strokeLinecap="round"
              />
              <text
                x={dial / 2}
                y={dial / 2 + size * 0.322}
                className="ahos-stale-label"
                textAnchor="middle"
              >
                {dict.heartbeatStale}
              </text>
            </g>
          ) : null}
        </svg>

        <MarkerLayer
          markers={visibleMarkers}
          markerRefs={markerRefs}
          lang={lang}
          dict={dict}
          now={now}
          activeId={activeMarker}
          onActivate={setActiveMarker}
          onDeactivate={() => setActiveMarker(null)}
          onSelect={(id) => {
            setActiveMarker(id);
            onSelect?.(id);
          }}
        />

        <ArcTooltip
          signal={activeSignal}
          nodes={nodeIndex}
          lang={lang}
          dict={dict}
          now={now}
          elementRef={arcTooltipRef}
        />

        <DialCaptions
          size={size}
          lang={lang}
          dict={dict}
          gate={gate}
          departmentsNeedingAttention={attentionCount}
          collapsedCount={selection.hidden.length}
          hasDemoData={hasDemoData}
          stale={health.stale}
          textViewOpen={textOpen}
          onToggleTextView={() => setTextOpen((open) => !open)}
        />

        {fallback ? (
          <span className="ahos-fallback-note" style={{ top: size * 0.62 }}>
            {dict.fallbackNotice}
          </span>
        ) : null}

        <TextTable
          markets={markets}
          signals={visibleSignals}
          departments={departments}
          gate={gate}
          health={health}
          lang={lang}
          dict={dict}
          now={now}
          open={textOpen}
        />
      </div>

      <p className="ahos-visually-hidden" data-testid="ahos-summary">
        {`${dict.tableCaption}. ${markets
          .map((market: MarketNode) => {
            const stamp = asOfText(market.asOf, now, lang);
            const change = formatPercent(market.changePct, lang);
            return `${lang === "fa" ? market.nameFa : market.nameEn}: ${dict.freshness[market.freshness]}, ${
              stamp.display ?? dict.unknownValue
            }${change ? `, ${dict.columnChange} ${change}` : ""}${
              market.needsAttention ? `, ${dict.columnAttention}` : ""
            }`;
          })
          .join(" | ")}`}
      </p>
      <p className="ahos-visually-hidden">
        {health.stale
          ? dict.heartbeatStale
          : dict.heartbeatLive(localizeNumber(health.bpm, lang), localizeNumber(health.jitterMs, lang))}
        {` · ${localizeNumber(visibleSignals.length, lang)}/${localizeNumber(signals.length, lang)} ${lang === "fa" ? "کمان" : "arcs"}`}
        {` · ${localizeNumber(selection.hidden.length, lang)} ${lang === "fa" ? "بازار پنهان" : "hidden"}`}
      </p>
    </div>
  );
}

export default AhosGlobe;
