"use client";

import { forwardRef, useEffect, useImperativeHandle, useRef, type ReactNode } from "react";
import type { FinancialCenter } from "@/lib/api/types";
import type { QualityBudget } from "@/lib/settings/types";
import { createGlobeScene, type GlobeLabel, type GlobeLayers, type GlobeScene } from "./scene";

export interface GlobeHandle {
  flyTo(target: "iran" | "global"): void;
  zoom(factor: number): void;
}

export interface RenderedLabel extends GlobeLabel {
  node: ReactNode;
}

export interface GlobeCanvasProps {
  budget: QualityBudget;
  initialView: "global" | "iran";
  reducedMotion: boolean;
  autoRotate: boolean;
  layers: GlobeLayers;
  centers: FinancialCenter[];
  links: { from: string; to: string }[];
  labels: RenderedLabel[];
  ariaLabel: string;
  onIranClick: () => void;
  onIranHover: (hover: boolean) => void;
  onRenderingChange: (rendering: boolean) => void;
  onTexturesReady: () => void;
  onError: (err: unknown) => void;
}

/** React wrapper around the framework-free scene. Imported client-only via next/dynamic. */
const GlobeCanvas = forwardRef<GlobeHandle, GlobeCanvasProps>(function GlobeCanvas(props, ref) {
  const canvasHostRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<GlobeScene | null>(null);
  const labelEls = useRef<(HTMLDivElement | null)[]>([]);
  const latest = useRef(props);
  const { budget, layers, autoRotate, reducedMotion } = props;

  useEffect(() => {
    latest.current = props;
  });

  useImperativeHandle(
    ref,
    () => ({
      flyTo: (target) => sceneRef.current?.flyTo(target),
      zoom: (factor) => sceneRef.current?.zoom(factor),
    }),
    [],
  );

  // (Re)build the scene when the quality budget changes; dispose on unmount.
  useEffect(() => {
    const host = canvasHostRef.current;
    if (!host) return;
    const p = latest.current;
    let scene: GlobeScene | null = null;
    try {
      scene = createGlobeScene(host, {
        budget,
        initialView: p.initialView,
        reducedMotion: p.reducedMotion,
        autoRotate: p.autoRotate,
        layers: p.layers,
        centers: p.centers,
        links: p.links,
        ariaLabel: p.ariaLabel,
        getLabels: () => latest.current.labels,
        getLabelEls: () => labelEls.current,
        onIranClick: () => latest.current.onIranClick(),
        onIranHover: (h) => latest.current.onIranHover(h),
        onRenderingChange: (r) => latest.current.onRenderingChange(r),
        onTexturesReady: () => latest.current.onTexturesReady(),
        onError: (e) => latest.current.onError(e),
      });
      sceneRef.current = scene;
    } catch (err) {
      p.onError(err);
    }
    return () => {
      scene?.dispose();
      sceneRef.current = null;
    };
  }, [budget]);

  useEffect(() => {
    sceneRef.current?.setLayers(layers);
  }, [layers]);
  useEffect(() => {
    sceneRef.current?.setAutoRotate(autoRotate);
  }, [autoRotate]);
  useEffect(() => {
    sceneRef.current?.setReducedMotion(reducedMotion);
  }, [reducedMotion]);

  return (
    <div className="absolute inset-0 overflow-hidden">
      <div ref={canvasHostRef} className="absolute inset-0" />
      <div className="pointer-events-none absolute inset-0" style={{ display: layers.labels ? undefined : "none" }}>
        {props.labels.map((lb, i) => (
          <div
            key={lb.id}
            ref={(el) => {
              labelEls.current[i] = el;
            }}
            className="absolute left-0 top-0 will-change-transform"
            style={{ visibility: "hidden" }}
          >
            <div className="-translate-x-1/2 -translate-y-1/2">{lb.node}</div>
          </div>
        ))}
      </div>
    </div>
  );
});

export default GlobeCanvas;
