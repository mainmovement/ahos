"use client";

/**
 * COBE lifecycle.
 *
 * Contract (asserted in `tests/instance.test.tsx`):
 *  - `createGlobe` is called EXACTLY ONCE per mounted component, no matter how often props change.
 *  - Prop changes reach COBE through `globe.update()` via refs — never by recreating the instance.
 *  - Rotation is driven by OUR requestAnimationFrame loop (time-based, dt-scaled), never by COBE's
 *    internal loop, so pausing for hidden tabs / off-screen elements / reduced motion is exact.
 *  - The instance is destroyed on unmount (safe under React StrictMode's double mount).
 *  - A dev-only counter is exposed on `window.__ahosGlobeDev`; tests import
 *    `getGlobeInstanceCount()` directly.
 */

import createGlobe, { type COBEOptions, type Globe } from "cobe";
import { useCallback, useEffect, useRef, useState } from "react";
import type { GlobeMode, GlobeQuality } from "../../types/globe";
import type { COBEColour } from "../../lib/palette";
import { GLOBE_PALETTE } from "../../lib/palette";

/** mapSamples per quality preset (brief: low 6000, medium 12000, high 20000). */
export const MAP_SAMPLES: Record<GlobeQuality, number> = { low: 6000, medium: 12000, high: 20000 };

/** Device pixel ratio ceiling — the brief caps it at 1.5 for 8 GB machines with integrated graphics. */
export const MAX_DPR = 1.5;

let liveInstances = 0;

/** Live COBE instances. Dev tooling; the test suite asserts this stays at 1 across prop updates. */
export function getGlobeInstanceCount(): number {
  return liveInstances;
}

/** Test seam: resets the counter between cases. */
export function resetGlobeInstanceCount(): void {
  liveInstances = 0;
}

type DevApi = {
  instances: () => number;
  setPhi: (radians: number) => void;
  freeze: (frozen: boolean) => void;
};

declare global {
  interface Window {
    /** Dev-only handle used by scripts/shoot.mjs and manual inspection. */
    __ahosGlobeDev?: DevApi;
  }
}

/** Cheap capability probe; guarded so it is safe during SSR. */
export function webglAvailable(): boolean {
  if (typeof document === "undefined") return false;
  try {
    const probe = document.createElement("canvas");
    return Boolean(probe.getContext("webgl2") ?? probe.getContext("webgl"));
  } catch {
    return false;
  }
}

export type UseGlobeCanvasArgs = {
  /** Wrapper that owns the canvas (COBE inserts one extra relative wrapper inside it). */
  hostRef: React.RefObject<HTMLDivElement | null>;
  canvasRef: React.RefObject<HTMLCanvasElement | null>;
  /** Square stage size in CSS px. */
  size: number;
  quality: GlobeQuality;
  mode: GlobeMode;
  /** True while motion is allowed: drives the longitude spin. */
  animate: boolean;
  /**
   * True while the canvas must keep being repainted. COBE is created without
   * `preserveDrawingBuffer`, so a canvas that stops drawing is cleared by the compositor and the
   * globe would vanish. We therefore keep drawing whenever the dial is on screen, and only freeze
   * the *rotation* when motion is off (reduced motion, hovered marker, frozen debug mode).
   */
  rendering: boolean;
  /** Radians per second for the longitude spin; 0 freezes the rotation. */
  spinRate: number;
  /** Tilt in radians (kept small: the dial must stay legible). */
  theta: number;
  /** True while a marker is hovered/focused: the dial holds still so the tooltip can be read. */
  hold: boolean;
  /** Called after every drawn frame with the rotation used, so overlays can follow. */
  onFrame: (phi: number, theta: number, timeMs: number) => void;
  /** True when any node needs attention — only affects COBE's glow strength. */
  alert?: boolean;
};

export type UseGlobeCanvasResult = {
  /** FALSE means "render the flat SVG fallback instead". */
  supported: boolean;
  /** Rotation in radians, readable at any time (used to seed overlays). */
  phiRef: React.RefObject<number>;
  /** Ask for one extra overlay pass (resize, prop change, mode switch). */
  redraw: () => void;
};

export function useGlobeCanvas(args: UseGlobeCanvasArgs): UseGlobeCanvasResult {
  const {
    hostRef,
    canvasRef,
    size,
    quality,
    mode,
    animate,
    rendering,
    spinRate,
    theta,
    hold,
    onFrame,
    alert,
  } = args;
  const [supported, setSupported] = useState(true);
  const globeRef = useRef<Globe | null>(null);
  const phiRef = useRef<number>(0);
  const lastRef = useRef<number>(0);
  const frozenRef = useRef(false);
  const spinRef = useRef(spinRate);
  const thetaRef = useRef(theta);
  const holdRef = useRef(hold);
  const frameRef = useRef(onFrame);
  const alertRef = useRef(Boolean(alert));
  const animateRef = useRef(animate);
  const modeRef = useRef(mode);
  const sizeRef = useRef(size);
  const qualityRef = useRef(quality);

  // Latest values for the loop, refreshed after every render.
  useEffect(() => {
    spinRef.current = spinRate;
    thetaRef.current = theta;
    holdRef.current = hold;
    frameRef.current = onFrame;
    alertRef.current = Boolean(alert);
    animateRef.current = animate;
    modeRef.current = mode;
  });

  /**
   * Applies every input COBE can be re-configured with, without recreating the instance. This runs
   * on prop changes and on every resize, so the globe is created exactly once for the component's
   * whole life — including when the container is resized or the quality preset changes.
   */
  const apply = useCallback(() => {
    const globe = globeRef.current;
    if (!globe) return;
    sizeRef.current = size;
    qualityRef.current = quality;
    globe.update({
      width: size,
      height: size,
      mapSamples: MAP_SAMPLES[quality],
      diffuse: quality === "low" ? 0.95 : 1.15,
      glowColor: alert ? GLOBE_PALETTE.glowColorAlert : GLOBE_PALETTE.glowColor,
    });
    frameRef.current(phiRef.current, thetaRef.current, performance.now());
  }, [size, quality, alert]);

  useEffect(() => {
    apply();
  }, [apply]);

  const redraw = useCallback(() => {
    frameRef.current(phiRef.current, thetaRef.current, performance.now());
  }, []);

  // Created once, on mount. `size`/`quality` changes go through update(), never a new instance.
  useEffect(() => {
    if (!webglAvailable()) {
      setSupported(false);
      return;
    }
    const canvas = canvasRef.current;
    const host = hostRef.current;
    if (!canvas || !host) return;

    const dpr = Math.min(window.devicePixelRatio || 1, MAX_DPR);
    const options: COBEOptions = {
      devicePixelRatio: dpr,
      width: size,
      height: size,
      phi: phiRef.current,
      theta: thetaRef.current,
      dark: 1,
      diffuse: quality === "low" ? 0.95 : 1.15,
      scale: 1,
      mapSamples: MAP_SAMPLES[quality],
      mapBrightness: 3.8,
      mapBaseBrightness: 0,
      baseColor: GLOBE_PALETTE.baseColor as COBEColour,
      markerColor: GLOBE_PALETTE.markerColor as COBEColour,
      glowColor: alertRef.current ? GLOBE_PALETTE.glowColorAlert : GLOBE_PALETTE.glowColor,
      opacity: 1,
      offset: [0, 0],
    };

    const globe = createGlobe(canvas, options);
    globeRef.current = globe;
    const wrapper = canvas.parentElement === host ? null : canvas.parentElement;
    liveInstances += 1;

    const context = canvas.getContext("webgl2") ?? canvas.getContext("webgl");
    if (!context) {
      // COBE returned its no-op fallback: hand over to the flat SVG renderer.
      globe.destroy();
      liveInstances -= 1;
      globeRef.current = null;
      setSupported(false);
      return;
    }

    if (process.env.NODE_ENV !== "production") {
      window.__ahosGlobeDev = {
        instances: () => liveInstances,
        setPhi: (radians: number) => {
          phiRef.current = radians;
          globe.update({ phi: radians, theta: thetaRef.current });
          frameRef.current(radians, thetaRef.current, performance.now());
        },
        freeze: (frozen: boolean) => {
          frozenRef.current = frozen;
        },
      };
    }

    redraw();

    return () => {
      globe.destroy();
      liveInstances -= 1;
      globeRef.current = null;
      // COBE wraps the canvas in its own relative div and does not undo that on destroy:
      // unwrap so a StrictMode remount cannot stack wrappers.
      if (canvas.parentElement !== host) {
        host.appendChild(canvas);
      }
      if (wrapper && wrapper.parentElement === host && wrapper.childNodes.length === 0) {
        wrapper.remove();
      }
    };
    // Mount-only on purpose: size/quality/alert changes are applied through update() above.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [canvasRef, hostRef, redraw]);

  // The draw loop. Runs while the dial is on screen and in globe mode; the rotation inside it only
  // advances when motion is allowed, so reduced motion freezes the dial without blanking it.
  useEffect(() => {
    if (!rendering || mode !== "globe" || !supported) {
      redraw();
      return;
    }
    let raf = requestAnimationFrame(function step(time: number) {
      raf = requestAnimationFrame(step);
      const globe = globeRef.current;
      const last = lastRef.current === 0 ? time : lastRef.current;
      const dt = Math.min(0.1, Math.max(0, (time - last) / 1000));
      lastRef.current = time;
      if (!globe) return;
      if (animateRef.current && !holdRef.current && !frozenRef.current) {
        phiRef.current += spinRef.current * dt;
      }
      globe.update({ phi: phiRef.current, theta: thetaRef.current });
      frameRef.current(phiRef.current, thetaRef.current, time);
    });
    return () => {
      cancelAnimationFrame(raf);
      lastRef.current = 0;
    };
  }, [rendering, mode, redraw, supported]);

  return { supported, phiRef, redraw };
}
